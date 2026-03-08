"""Symbol extraction for PHP parser.

This module provides functions to extract symbols (classes, functions, methods, properties)
from PHP source code using tree-sitter.
"""

from tree_sitter import Tree

from ...parser import Inheritance, Symbol
from ..utils import get_node_text


def extract_symbols(tree: Tree, source_bytes: bytes) -> list:
    """Extract symbols (classes, functions, methods, properties) from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Symbol objects
    """
    symbols = []
    namespace = ""
    use_map = {}  # For tracking use statements
    inheritances = []  # For tracking inheritance relationships

    root = tree.root_node

    # First pass: Extract namespace and use statements
    for child in root.children:
        if child.type == "namespace_definition":
            namespace = _parse_namespace(child, source_bytes)
        elif child.type == "namespace_use_declaration":
            imports = _parse_use(child, source_bytes)
            # Build use map for class resolution
            for imp in imports:
                if imp.alias:
                    use_map[imp.alias] = imp.module
                else:
                    # Extract short name from module
                    short_name = imp.module.split("\\")[-1]
                    use_map[short_name] = imp.module

    # Second pass: Extract functions and classes
    for child in root.children:
        if child.type == "function_definition":
            symbol = _parse_function(child, source_bytes)
            symbols.append(symbol)
        elif child.type == "class_declaration":
            # Pass namespace, use_map, and inheritances for inheritance extraction
            class_symbols = _parse_class(
                child, source_bytes, namespace, use_map, inheritances
            )
            symbols.extend(class_symbols)

    return symbols


def _extract_docstring(node, source_bytes: bytes) -> str:
    """Extract docstring from PHPDoc/DocComment or inline comments.

    For PHP, the comment is often a sibling node (previous sibling)
    rather than a child node.

    Supports:
    - PHPDoc blocks: /** ... */
    - Inline comments: // ...
    """
    # First check children (for class-level comments)
    for child in node.children:
        if child.type == "comment":
            text = get_node_text(child, source_bytes)
            if text.startswith("/**"):
                return _parse_phpdoc_text(text)
            elif text.startswith("//"):
                # Inline comment: remove // and strip
                return text[2:].strip()

    # Check previous sibling (for method-level comments)
    if node.prev_sibling and node.prev_sibling.type == "comment":
        text = get_node_text(node.prev_sibling, source_bytes)
        if text.startswith("/**"):
            return _parse_phpdoc_text(text)
        elif text.startswith("//"):
            # Inline comment: remove // and strip
            return text[2:].strip()

    return ""


def _parse_phpdoc_text(text: str) -> str:
    """Parse PHPDoc comment text and extract description.

    Extracts the first non-annotation line(s) from PHPDoc.
    Skips @param, @return, @throws, etc.

    Args:
        text: Raw PHPDoc comment text (/** ... */)

    Returns:
        Cleaned description text
    """
    # Handle single-line PHPDoc: /** Description */
    if "\n" not in text:
        # Remove /** and */
        content = text.strip()
        if content.startswith("/**"):
            content = content[3:]
        if content.endswith("*/"):
            content = content[:-2]
        content = content.strip()
        # Skip if it's only annotations
        if content.startswith("@"):
            return ""
        return content

    # Handle multi-line PHPDoc
    lines = text.split("\n")
    description_lines = []

    for line in lines[1:-1]:  # Skip first (/**) and last (*/) lines
        line = line.strip()
        # Remove leading * and whitespace
        if line.startswith("*"):
            line = line[1:].strip()

        # Skip empty lines
        if not line:
            continue

        # Skip annotation lines (@param, @return, etc.)
        if line.startswith("@"):
            break  # Stop at first annotation

        description_lines.append(line)

    return " ".join(description_lines)


def _parse_function(node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a PHP function definition node (standalone function, not method)."""
    name = ""
    params = ""
    return_type = ""

    for child in node.children:
        if child.type == "name":
            name = get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = get_node_text(child, source_bytes)

    signature = f"function {name}{params}"
    if return_type:
        signature += f": {return_type}"

    docstring = _extract_docstring(node, source_bytes)

    return Symbol(
        name=name,
        kind="function",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_method(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP method declaration node with visibility, static, and return type."""
    name = ""
    params = ""
    return_type = ""
    visibility = ""
    is_static = False

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type == "name":
            name = get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = get_node_text(child, source_bytes)

    # Build signature: [visibility] [static] function name(params)[: return_type]
    sig_parts = []
    if visibility:
        sig_parts.append(visibility)
    if is_static:
        sig_parts.append("static")
    sig_parts.append(f"function {name}{params}")
    signature = " ".join(sig_parts)
    if return_type:
        signature += f": {return_type}"

    docstring = _extract_docstring(node, source_bytes)
    full_name = f"{class_name}::{name}"

    return Symbol(
        name=full_name,
        kind="method",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_property(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP property declaration node."""
    prop_name = ""
    visibility = ""
    is_static = False
    prop_type = ""

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            prop_type = get_node_text(child, source_bytes)
        elif child.type == "property_element":
            for prop_child in child.children:
                if prop_child.type == "variable_name":
                    prop_name = get_node_text(prop_child, source_bytes)

    # Build signature: [visibility] [static] [type] $name
    sig_parts = []
    if visibility:
        sig_parts.append(visibility)
    if is_static:
        sig_parts.append("static")
    if prop_type:
        sig_parts.append(prop_type)
    sig_parts.append(prop_name)
    signature = " ".join(sig_parts)

    full_name = f"{class_name}::{prop_name}"

    return Symbol(
        name=full_name,
        kind="property",
        signature=signature,
        docstring="",
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_class(
    node,
    source_bytes: bytes,
    namespace: str = "",
    use_map: dict[str, str] | None = None,
    inheritances: list[Inheritance] | None = None
) -> list[Symbol]:
    """Parse a PHP class definition node with extends, implements, properties and methods.

    Epic 10, Story 10.1.2: Added namespace, use_map, and inheritances parameters
    to support inheritance extraction for LoomGraph integration.

    Args:
        node: tree-sitter node for class_declaration
        source_bytes: Source code bytes
        namespace: Current namespace (e.g., "App\\Models")
        use_map: Mapping of short names to full qualified names from use statements
        inheritances: List to append Inheritance relationships to
    """
    if use_map is None:
        use_map = {}
    if inheritances is None:
        inheritances = []

    symbols = []
    class_name = ""
    extends = ""
    implements = []
    is_abstract = False
    is_final = False

    for child in node.children:
        if child.type == "name":
            class_name = get_node_text(child, source_bytes)
        elif child.type == "abstract_modifier":
            is_abstract = True
        elif child.type == "final_modifier":
            is_final = True
        elif child.type == "base_clause":
            # extends BaseClass
            for bc_child in child.children:
                if bc_child.type == "name":
                    extends = get_node_text(bc_child, source_bytes)
        elif child.type == "class_interface_clause":
            # implements Interface1, Interface2
            for ic_child in child.children:
                if ic_child.type == "name":
                    implements.append(get_node_text(ic_child, source_bytes))

    # Build full class name with namespace
    full_class_name = f"{namespace}\\{class_name}" if namespace else class_name

    # Create Inheritance objects (Epic 10, Story 10.1.2)
    if extends:
        # Resolve parent class full name using use_map
        parent_full_name = use_map.get(extends, f"{namespace}\\{extends}" if namespace else extends)
        inheritances.append(Inheritance(child=full_class_name, parent=parent_full_name))

    for interface in implements:
        # Resolve interface full name using use_map
        interface_full_name = use_map.get(
            interface, f"{namespace}\\{interface}" if namespace else interface
        )
        inheritances.append(Inheritance(child=full_class_name, parent=interface_full_name))

    # Build signature: [abstract|final] class Name [extends Base] [implements I1, I2]
    sig_parts = []
    if is_abstract:
        sig_parts.append("abstract")
    elif is_final:
        sig_parts.append("final")
    sig_parts.append(f"class {class_name}")
    if extends:
        sig_parts.append(f"extends {extends}")
    if implements:
        sig_parts.append(f"implements {', '.join(implements)}")
    signature = " ".join(sig_parts)

    docstring = _extract_docstring(node, source_bytes)

    symbols.append(
        Symbol(
            name=class_name,
            kind="class",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Parse properties and methods from declaration_list
    for child in node.children:
        if child.type == "declaration_list":
            for decl in child.children:
                if decl.type == "property_declaration":
                    prop = _parse_property(decl, source_bytes, class_name)
                    symbols.append(prop)
                elif decl.type == "method_declaration":
                    method = _parse_method(decl, source_bytes, class_name)
                    symbols.append(method)

    return symbols


def _parse_namespace(node, source_bytes: bytes) -> str:
    """Parse PHP namespace definition."""
    for child in node.children:
        if child.type == "namespace_name":
            return get_node_text(child, source_bytes)
    return ""


def _parse_use(node, source_bytes: bytes) -> list:
    """Parse PHP use statement.

    This is a minimal import structure needed for use_map construction
    in symbol extraction. Returns list of simple objects with module and alias.
    """
    from ...parser import Import

    imports = []
    base_namespace = ""

    for child in node.children:
        if child.type == "namespace_name":
            # Group import base: use App\Repository\{...}
            base_namespace = get_node_text(child, source_bytes)

        elif child.type == "namespace_use_clause":
            # Single import
            module = ""
            alias = ""

            for clause_child in child.children:
                if clause_child.type == "qualified_name":
                    module = get_node_text(clause_child, source_bytes)
                elif clause_child.type == "name" and module:
                    # This is the alias (after 'as')
                    alias = get_node_text(clause_child, source_bytes)

            if module:
                # If there's a base namespace (group import), prepend it
                if base_namespace:
                    module = f"{base_namespace}\\{module}"

                imports.append(
                    Import(
                        module=module,
                        names=[],
                        is_from=True,
                        alias=alias if alias else None,
                    )
                )

        elif child.type == "namespace_use_group":
            # Group import: {UserRepository, OrderRepository}
            for group_child in child.children:
                if group_child.type == "namespace_use_clause":
                    name = ""
                    alias = ""
                    for clause_child in group_child.children:
                        if clause_child.type == "qualified_name":
                            name = get_node_text(clause_child, source_bytes)
                        elif clause_child.type == "name":
                            if not name:
                                name = get_node_text(clause_child, source_bytes)
                            else:
                                alias = get_node_text(clause_child, source_bytes)

                    if name:
                        full_module = f"{base_namespace}\\{name}" if base_namespace else name
                        imports.append(
                            Import(
                                module=full_module,
                                names=[],
                                is_from=True,
                                alias=alias if alias else None,
                            )
                        )

    return imports
