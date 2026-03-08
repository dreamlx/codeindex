"""Symbol extraction for TypeScript/JavaScript parser.

This module provides functions to extract symbols (classes, functions, methods,
interfaces, enums, type aliases) from TypeScript/JavaScript source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Symbol
from ..utils import get_node_text


def extract_symbols(tree: Tree, source_bytes: bytes) -> list:
    """Extract symbols from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Symbol objects
    """
    symbols = []
    root = tree.root_node

    for child in root.children:
        symbols.extend(_extract_node_symbols(child, source_bytes))

    return symbols


def extract_module_docstring(tree: Tree, source_bytes: bytes) -> str:
    """Extract module-level JSDoc comment (first comment in file).

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        Module docstring or empty string
    """
    root = tree.root_node
    if root.children:
        first = root.children[0]
        if first.type == "comment":
            text = get_node_text(first, source_bytes)
            if text.startswith("/**"):
                return text[3:-2].strip()
    return ""


def _extract_node_symbols(
    node: Node, source_bytes: bytes, class_name: str = ""
) -> list[Symbol]:
    """Extract symbols from a single AST node.

    Args:
        node: The AST node to extract from
        source_bytes: The source code as bytes
        class_name: Current class context (for nested symbols)

    Returns:
        List of Symbol objects
    """
    symbols = []

    if node.type == "function_declaration":
        sym = _parse_function_declaration(node, source_bytes)
        if sym:
            symbols.append(sym)

    elif node.type == "generator_function_declaration":
        sym = _parse_function_declaration(node, source_bytes)
        if sym:
            symbols.append(sym)

    elif node.type == "class_declaration":
        symbols.extend(_parse_class_declaration(node, source_bytes))

    elif node.type == "abstract_class_declaration":
        symbols.extend(_parse_class_declaration(node, source_bytes, abstract=True))

    elif node.type == "interface_declaration":
        sym = _parse_interface_declaration(node, source_bytes)
        if sym:
            symbols.append(sym)

    elif node.type == "enum_declaration":
        sym = _parse_enum_declaration(node, source_bytes)
        if sym:
            symbols.append(sym)

    elif node.type == "type_alias_declaration":
        sym = _parse_type_alias(node, source_bytes)
        if sym:
            symbols.append(sym)

    elif node.type == "lexical_declaration":
        symbols.extend(_parse_lexical_declaration(node, source_bytes))

    elif node.type == "export_statement":
        # Extract symbols from exported declarations
        for child in node.children:
            symbols.extend(_extract_node_symbols(child, source_bytes, class_name))

    elif node.type in ("module", "internal_module"):
        # TypeScript namespace/module
        sym = _parse_namespace(node, source_bytes)
        if sym:
            symbols.append(sym)

    elif node.type == "expression_statement":
        # Namespace declarations are wrapped in expression_statement
        for child in node.children:
            symbols.extend(_extract_node_symbols(child, source_bytes, class_name))

    return symbols


def _parse_function_declaration(
    node: Node, source_bytes: bytes
) -> Symbol | None:
    """Parse a function declaration node.

    Args:
        node: The function_declaration or generator_function_declaration node
        source_bytes: The source code as bytes

    Returns:
        Symbol object or None
    """
    name = ""
    params = ""
    is_async = False
    is_generator = False

    for child in node.children:
        if child.type == "identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = get_node_text(child, source_bytes)
        elif child.type == "async":
            is_async = True
        elif child.type == "*":
            is_generator = True

    # Also detect generator from node type
    if node.type == "generator_function_declaration":
        is_generator = True

    if not name:
        return None

    sig_parts = []
    if is_async:
        sig_parts.append("async")
    sig_parts.append("function")
    if is_generator:
        sig_parts.append("*")
    sig_parts.append(f"{name}{params}")

    # Add return type if present
    return_type = _find_type_annotation(node, source_bytes)
    if return_type:
        sig_parts.append(f": {return_type}")

    return Symbol(
        name=name,
        kind="function",
        signature=" ".join(sig_parts),
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_class_declaration(
    node: Node, source_bytes: bytes, abstract: bool = False
) -> list[Symbol]:
    """Parse a class declaration node.

    Args:
        node: The class_declaration or abstract_class_declaration node
        source_bytes: The source code as bytes
        abstract: Whether this is an abstract class

    Returns:
        List of Symbol objects (class + members)
    """
    symbols = []
    class_name = ""
    type_params = ""
    extends = ""
    implements_list = []

    for child in node.children:
        if child.type in ("type_identifier", "identifier"):
            class_name = get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = get_node_text(child, source_bytes)
        elif child.type == "class_heritage":
            extends, implements_list = _parse_class_heritage(child, source_bytes)

    if not class_name:
        return symbols

    sig_parts = []
    if abstract:
        sig_parts.append("abstract")
    sig_parts.append("class")
    sig_parts.append(class_name + type_params if type_params else class_name)
    if extends:
        sig_parts.append(f"extends {extends}")
    if implements_list:
        sig_parts.append(f"implements {', '.join(implements_list)}")

    symbols.append(Symbol(
        name=class_name,
        kind="class",
        signature=" ".join(sig_parts),
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    ))

    # Extract class body members
    for child in node.children:
        if child.type == "class_body":
            symbols.extend(_parse_class_body(child, source_bytes, class_name))

    return symbols


def _parse_class_heritage(
    node: Node, source_bytes: bytes
) -> tuple[str, list[str]]:
    """Parse class_heritage node to extract extends and implements.

    Args:
        node: The class_heritage node
        source_bytes: The source code as bytes

    Returns:
        Tuple of (extends_class, list_of_implemented_interfaces)
    """
    extends = ""
    implements_list = []

    for child in node.children:
        if child.type == "extends_clause":
            for ext_child in child.children:
                if ext_child.type in ("identifier", "type_identifier", "generic_type"):
                    extends = get_node_text(ext_child, source_bytes)
        elif child.type == "implements_clause":
            for impl_child in child.children:
                if impl_child.type in ("type_identifier", "generic_type"):
                    implements_list.append(get_node_text(impl_child, source_bytes))

    return extends, implements_list


def _parse_class_body(
    node: Node, source_bytes: bytes, class_name: str
) -> list[Symbol]:
    """Parse class body members.

    Args:
        node: The class_body node
        source_bytes: The source code as bytes
        class_name: Name of the containing class

    Returns:
        List of Symbol objects (methods, fields)
    """
    symbols = []

    for child in node.children:
        if child.type == "method_definition":
            sym = _parse_method_definition(child, source_bytes, class_name)
            if sym:
                symbols.append(sym)
        elif child.type == "public_field_definition":
            sym = _parse_field_definition(child, source_bytes, class_name)
            if sym:
                symbols.append(sym)

    return symbols


def _parse_method_definition(
    node: Node, source_bytes: bytes, class_name: str
) -> Symbol | None:
    """Parse a method definition node.

    Args:
        node: The method_definition node
        source_bytes: The source code as bytes
        class_name: Name of the containing class

    Returns:
        Symbol object or None
    """
    name = ""
    params = ""
    is_async = False
    is_static = False
    is_getter = False
    is_setter = False
    accessibility = ""

    for child in node.children:
        if child.type == "property_identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = get_node_text(child, source_bytes)
        elif child.type == "async":
            is_async = True
        elif child.type == "static":
            is_static = True
        elif child.type == "get":
            is_getter = True
        elif child.type == "set":
            is_setter = True
        elif child.type == "accessibility_modifier":
            accessibility = get_node_text(child, source_bytes)

    if not name:
        return None

    # Determine kind
    if name == "constructor":
        kind = "constructor"
    else:
        kind = "method"

    full_name = f"{class_name}.{name}"

    # Build signature
    sig_parts = []
    if accessibility:
        sig_parts.append(accessibility)
    if is_static:
        sig_parts.append("static")
    if is_async:
        sig_parts.append("async")
    if is_getter:
        sig_parts.append("get")
    if is_setter:
        sig_parts.append("set")
    sig_parts.append(f"{name}{params}")

    return_type = _find_type_annotation(node, source_bytes)
    if return_type:
        sig_parts.append(f": {return_type}")

    return Symbol(
        name=full_name,
        kind=kind,
        signature=" ".join(sig_parts),
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_field_definition(
    node: Node, source_bytes: bytes, class_name: str
) -> Symbol | None:
    """Parse a class field definition.

    Args:
        node: The public_field_definition node
        source_bytes: The source code as bytes
        class_name: Name of the containing class

    Returns:
        Symbol object or None
    """
    name = ""
    accessibility = ""

    for child in node.children:
        if child.type == "property_identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "accessibility_modifier":
            accessibility = get_node_text(child, source_bytes)

    if not name:
        return None

    full_name = f"{class_name}.{name}"

    sig_parts = []
    if accessibility:
        sig_parts.append(accessibility)
    sig_parts.append(name)

    type_ann = _find_type_annotation(node, source_bytes)
    if type_ann:
        sig_parts.append(f": {type_ann}")

    return Symbol(
        name=full_name,
        kind="field",
        signature=" ".join(sig_parts),
        docstring="",
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_interface_declaration(
    node: Node, source_bytes: bytes
) -> Symbol | None:
    """Parse an interface declaration.

    Args:
        node: The interface_declaration node
        source_bytes: The source code as bytes

    Returns:
        Symbol object or None
    """
    name = ""
    type_params = ""
    extends_list = []

    for child in node.children:
        if child.type == "type_identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = get_node_text(child, source_bytes)
        elif child.type == "extends_type_clause":
            for ext_child in child.children:
                if ext_child.type in ("type_identifier", "generic_type"):
                    extends_list.append(get_node_text(ext_child, source_bytes))

    if not name:
        return None

    sig_parts = ["interface"]
    sig_parts.append(name + type_params if type_params else name)
    if extends_list:
        sig_parts.append(f"extends {', '.join(extends_list)}")

    return Symbol(
        name=name,
        kind="interface",
        signature=" ".join(sig_parts),
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_enum_declaration(
    node: Node, source_bytes: bytes
) -> Symbol | None:
    """Parse an enum declaration.

    Args:
        node: The enum_declaration node
        source_bytes: The source code as bytes

    Returns:
        Symbol object or None
    """
    name = ""
    is_const = False

    for child in node.children:
        if child.type == "identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "const":
            is_const = True

    if not name:
        return None

    sig_parts = []
    if is_const:
        sig_parts.append("const")
    sig_parts.append("enum")
    sig_parts.append(name)

    return Symbol(
        name=name,
        kind="enum",
        signature=" ".join(sig_parts),
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_type_alias(
    node: Node, source_bytes: bytes
) -> Symbol | None:
    """Parse a type alias declaration.

    Args:
        node: The type_alias_declaration node
        source_bytes: The source code as bytes

    Returns:
        Symbol object or None
    """
    name = ""
    type_params = ""

    for child in node.children:
        if child.type == "type_identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = get_node_text(child, source_bytes)

    if not name:
        return None

    sig = f"type {name}{type_params}" if type_params else f"type {name}"

    return Symbol(
        name=name,
        kind="type_alias",
        signature=sig,
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_lexical_declaration(
    node: Node, source_bytes: bytes
) -> list[Symbol]:
    """Parse const/let/var declaration, distinguishing arrow functions from variables.

    Args:
        node: The lexical_declaration node
        source_bytes: The source code as bytes

    Returns:
        List of Symbol objects
    """
    symbols = []
    decl_keyword = ""

    for child in node.children:
        if child.type in ("const", "let", "var"):
            decl_keyword = child.type
        elif child.type == "variable_declarator":
            sym = _parse_variable_declarator(child, source_bytes, decl_keyword)
            if sym:
                symbols.append(sym)

    return symbols


def _parse_variable_declarator(
    node: Node, source_bytes: bytes, decl_keyword: str
) -> Symbol | None:
    """Parse a variable_declarator node.

    Args:
        node: The variable_declarator node
        source_bytes: The source code as bytes
        decl_keyword: The declaration keyword (const/let/var)

    Returns:
        Symbol object or None
    """
    name = ""
    value_node = None

    for child in node.children:
        if child.type == "identifier":
            name = get_node_text(child, source_bytes)
        elif child.type in ("arrow_function", "function"):
            value_node = child

    if not name:
        return None

    if value_node and value_node.type == "arrow_function":
        # Arrow function → function symbol
        params = ""
        is_async = False
        for child in value_node.children:
            if child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type == "async":
                is_async = True
            elif child.type == "identifier" and not params:
                # Single param arrow: (x) => ... or x => ...
                params = f"({get_node_text(child, source_bytes)})"

        sig_parts = [decl_keyword]
        if is_async:
            sig_parts.append("async")
        sig_parts.append(f"{name} = {params} =>")

        return_type = _find_type_annotation(node, source_bytes)
        if return_type:
            sig_parts[-1] = f"{name}: {return_type} = {params} =>"

        return Symbol(
            name=name,
            kind="function",
            signature=" ".join(sig_parts),
            docstring=_extract_jsdoc(node.parent, source_bytes) if node.parent else "",
            line_start=node.parent.start_point[0] + 1 if node.parent else node.start_point[0] + 1,
            line_end=node.parent.end_point[0] + 1 if node.parent else node.end_point[0] + 1,
        )
    else:
        # Regular variable
        sig_parts = [decl_keyword, name]
        type_ann = _find_type_annotation(node, source_bytes)
        if type_ann:
            sig_parts.append(f": {type_ann}")

        return Symbol(
            name=name,
            kind="variable",
            signature=" ".join(sig_parts),
            docstring="",
            line_start=node.parent.start_point[0] + 1 if node.parent else node.start_point[0] + 1,
            line_end=node.parent.end_point[0] + 1 if node.parent else node.end_point[0] + 1,
        )


def _parse_namespace(
    node: Node, source_bytes: bytes
) -> Symbol | None:
    """Parse a namespace/module declaration.

    Args:
        node: The module or internal_module node
        source_bytes: The source code as bytes

    Returns:
        Symbol object or None
    """
    name = ""

    for child in node.children:
        if child.type == "identifier":
            name = get_node_text(child, source_bytes)

    if not name:
        return None

    return Symbol(
        name=name,
        kind="namespace",
        signature=f"namespace {name}",
        docstring=_extract_jsdoc(node, source_bytes),
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


# ==================== Helper Functions ====================


def _find_type_annotation(node: Node, source_bytes: bytes) -> str:
    """Find type annotation child of a node.

    Args:
        node: The node to search in
        source_bytes: The source code as bytes

    Returns:
        Type annotation string or empty string
    """
    for child in node.children:
        if child.type == "type_annotation":
            # Extract the type part (skip the colon)
            for type_child in child.children:
                if type_child.type != ":":
                    return get_node_text(type_child, source_bytes)
    return ""


def _extract_jsdoc(node: Node, source_bytes: bytes) -> str:
    """Extract JSDoc comment preceding a node.

    Args:
        node: The node to extract JSDoc for
        source_bytes: The source code as bytes

    Returns:
        JSDoc string or empty string
    """
    if node is None:
        return ""

    # Check previous sibling for comment
    if hasattr(node, "prev_sibling") and node.prev_sibling:
        prev = node.prev_sibling
        if prev.type == "comment":
            text = get_node_text(prev, source_bytes)
            if text.startswith("/**"):
                return text[3:-2].strip()

    return ""
