"""Multi-language AST parser using tree-sitter."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import tree_sitter_php as tsphp
import tree_sitter_python as tspython
from tree_sitter import Language, Parser


@dataclass
class Symbol:
    """Represents a code symbol (class, function, etc.)."""

    name: str
    kind: str  # class, function, method
    signature: str = ""
    docstring: str = ""
    line_start: int = 0
    line_end: int = 0


@dataclass
class Import:
    """Represents an import statement."""

    module: str
    names: list[str] = field(default_factory=list)
    is_from: bool = False


@dataclass
class ParseResult:
    """Result of parsing a file."""

    path: Path
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)
    module_docstring: str = ""
    namespace: str = ""  # PHP namespace
    error: str | None = None
    file_lines: int = 0  # Number of lines in the file


# Initialize languages
PY_LANGUAGE = Language(tspython.language())
PHP_LANGUAGE = Language(tsphp.language_php())

# Language-specific parsers
PARSERS: Dict[str, Parser] = {
    "python": Parser(PY_LANGUAGE),
    "php": Parser(PHP_LANGUAGE),
}

# File extension to language mapping
FILE_EXTENSIONS: Dict[str, str] = {
    ".py": "python",
    ".php": "php",
    ".phtml": "php",
}


def _get_node_text(node, source_bytes: bytes) -> str:
    """Extract text from a tree-sitter node."""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _extract_docstring(node, source_bytes: bytes) -> str:
    """Extract docstring from first child if it's a string."""
    if node.child_count == 0:
        return ""

    # Look for expression_statement containing string
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "expression_statement":
                    for expr_child in block_child.children:
                        if expr_child.type == "string":
                            text = _get_node_text(expr_child, source_bytes)
                            # Remove quotes
                            if text.startswith('"""') or text.startswith("'''"):
                                return text[3:-3].strip()
                            elif text.startswith('"') or text.startswith("'"):
                                return text[1:-1].strip()
                    break
            break

    return ""


def _parse_function(
    node,
    source_bytes: bytes,
    class_name: str = "",
    decorators: list[str] | None = None
) -> Symbol:
    """Parse a function definition node."""
    name = ""
    signature_parts = []

    for child in node.children:
        if child.type == "identifier":  # function name is 'identifier', not 'name'
            name = _get_node_text(child, source_bytes)
        elif child.type == "parameters":
            signature_parts.append(_get_node_text(child, source_bytes))
        elif child.type == "type":
            signature_parts.append(f" -> {_get_node_text(child, source_bytes)}")

    kind = "method" if class_name else "function"
    full_name = f"{class_name}.{name}" if class_name else name
    signature = f"def {name}{''.join(signature_parts)}"
    docstring = _extract_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind=kind,
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_class(node, source_bytes: bytes) -> list[Symbol]:
    """Parse a class definition node and its methods."""
    symbols = []
    class_name = ""
    bases = []

    for child in node.children:
        if child.type == "identifier":  # class name is 'identifier', not 'name'
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "argument_list":
            bases.append(_get_node_text(child, source_bytes))

    signature = f"class {class_name}"
    if bases:
        signature += "".join(bases)

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

    # Parse methods
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "function_definition":
                    method = _parse_function(block_child, source_bytes, class_name)
                    symbols.append(method)

    return symbols


def _parse_import(node, source_bytes: bytes) -> Import | None:
    """Parse an import statement."""
    if node.type == "import_statement":
        # import foo, bar
        names = []
        for child in node.children:
            if child.type == "dotted_name":
                names.append(_get_node_text(child, source_bytes))
            elif child.type == "aliased_import":
                for ac in child.children:
                    if ac.type == "dotted_name":
                        names.append(_get_node_text(ac, source_bytes))
                        break
        if names:
            return Import(module=names[0], names=names[1:] if len(names) > 1 else [], is_from=False)

    elif node.type == "import_from_statement":
        # from foo import bar, baz
        module = ""
        names = []
        for child in node.children:
            if child.type == "dotted_name":
                if not module:
                    module = _get_node_text(child, source_bytes)
                else:
                    names.append(_get_node_text(child, source_bytes))
            elif child.type == "relative_import":
                module = _get_node_text(child, source_bytes)
            elif child.type == "aliased_import":
                for ac in child.children:
                    if ac.type == "dotted_name":
                        names.append(_get_node_text(ac, source_bytes))
                        break
                    elif ac.type == "identifier":
                        names.append(_get_node_text(ac, source_bytes))
                        break
            elif child.type == "identifier":
                names.append(_get_node_text(child, source_bytes))

        if module:
            return Import(module=module, names=names, is_from=True)

    return None


def _extract_module_docstring(tree, source_bytes: bytes) -> str:
    """Extract module-level docstring."""
    root = tree.root_node
    for child in root.children:
        if child.type == "expression_statement":
            for expr_child in child.children:
                if expr_child.type == "string":
                    text = _get_node_text(expr_child, source_bytes)
                    if text.startswith('"""') or text.startswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') or text.startswith("'"):
                        return text[1:-1].strip()
            break
        elif child.type not in ("comment",):
            break
    return ""


def parse_file(path: Path) -> ParseResult:
    """
    Parse a source file (Python or PHP) and extract symbols and imports.

    Args:
        path: Path to the source file

    Returns:
        ParseResult containing symbols, imports, and docstrings
    """
    try:
        source_bytes = path.read_bytes()
    except Exception as e:
        return ParseResult(path=path, error=str(e), file_lines=0)

    # Calculate file lines
    file_lines = source_bytes.count(b"\n") + (
        1 if source_bytes and not source_bytes.endswith(b"\n") else 0
    )

    # Determine language
    language = _get_language(path)
    if not language:
        return ParseResult(
            path=path, error=f"Unsupported file type: {path.suffix}", file_lines=file_lines
        )

    # Get appropriate parser
    parser = PARSERS.get(language)
    if not parser:
        return ParseResult(
            path=path, error=f"No parser for language: {language}", file_lines=file_lines
        )

    try:
        tree = parser.parse(source_bytes)
    except Exception as e:
        return ParseResult(path=path, error=f"Parse error: {e}", file_lines=file_lines)

    symbols: list[Symbol] = []
    imports: list[Import] = []
    module_docstring = ""

    # Language-specific parsing
    if language == "python":
        module_docstring = _extract_module_docstring(tree, source_bytes)
        root = tree.root_node
        for child in root.children:
            if child.type == "function_definition":
                symbols.append(_parse_function(child, source_bytes))
            elif child.type == "class_definition":
                symbols.extend(_parse_class(child, source_bytes))
            elif child.type == "decorated_definition":
                for dec_child in child.children:
                    if dec_child.type == "function_definition":
                        symbols.append(_parse_function(dec_child, source_bytes))
                    elif dec_child.type == "class_definition":
                        symbols.extend(_parse_class(dec_child, source_bytes))
            elif child.type in ("import_statement", "import_from_statement"):
                imp = _parse_import(child, source_bytes)
                if imp:
                    imports.append(imp)

    elif language == "php":
        # PHP parsing
        root = tree.root_node
        namespace = ""

        for child in root.children:
            if child.type == "namespace_definition":
                namespace = _parse_php_namespace(child, source_bytes)
            elif child.type == "namespace_use_declaration":
                use_imports = _parse_php_use(child, source_bytes)
                imports.extend(use_imports)
            elif child.type == "class_declaration":
                symbols.extend(_parse_php_class(child, source_bytes))
            elif child.type == "function_definition":
                symbols.append(_parse_php_function(child, source_bytes))
            elif child.type in ("include_expression", "require_expression"):
                imp = _parse_php_include(child, source_bytes)
                if imp:
                    imports.append(imp)

        # Extract module docstring from PHP file comments
        module_docstring = ""
        for child in root.children:
            if child.type == "comment" and child.text.startswith(b"/**"):
                module_docstring = _extract_php_docstring(child, source_bytes)
                break

        return ParseResult(
            path=path,
            symbols=symbols,
            imports=imports,
            module_docstring=module_docstring,
            namespace=namespace,
            file_lines=file_lines,
        )

    return ParseResult(
        path=path,
        symbols=symbols,
        imports=imports,
        module_docstring=module_docstring,
        file_lines=file_lines,
    )


def parse_directory(paths: list[Path]) -> list[ParseResult]:
    """Parse multiple files."""
    return [parse_file(p) for p in paths]

def _get_language(file_path: Path) -> str:
    """Determine language from file extension."""
    suffix = file_path.suffix.lower()
    return FILE_EXTENSIONS.get(suffix)

def _extract_php_docstring(node, source_bytes: bytes) -> str:
    """Extract docstring from PHPDoc/DocComment."""
    for child in node.children:
        if child.type == "comment":
            text = _get_node_text(child, source_bytes)
            # Check if it's a DocComment (/** ... */)
            if text.startswith("/**"):
                # Extract content between /** and */
                lines = text.split("\n")
                content = []
                for line in lines[1:-1]:  # Skip first and last line
                    line = line.strip()
                    if line.startswith("*"):
                        line = line[1:].strip()
                    if line:
                        content.append(line)
                return " ".join(content)
    return ""

def _parse_php_function(node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a PHP function definition node (standalone function, not method)."""
    name = ""
    params = ""
    return_type = ""

    for child in node.children:
        if child.type == "name":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = _get_node_text(child, source_bytes)

    signature = f"function {name}{params}"
    if return_type:
        signature += f": {return_type}"

    docstring = _extract_php_docstring(node, source_bytes)

    return Symbol(
        name=name,
        kind="function",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_php_method(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP method declaration node with visibility, static, and return type."""
    name = ""
    params = ""
    return_type = ""
    visibility = ""
    is_static = False

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = _get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type == "name":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = _get_node_text(child, source_bytes)

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

    docstring = _extract_php_docstring(node, source_bytes)
    full_name = f"{class_name}::{name}"

    return Symbol(
        name=full_name,
        kind="method",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_php_property(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP property declaration node."""
    prop_name = ""
    visibility = ""
    is_static = False
    prop_type = ""

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = _get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            prop_type = _get_node_text(child, source_bytes)
        elif child.type == "property_element":
            for prop_child in child.children:
                if prop_child.type == "variable_name":
                    prop_name = _get_node_text(prop_child, source_bytes)

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

def _parse_php_class(node, source_bytes: bytes) -> list[Symbol]:
    """Parse a PHP class definition node with extends, implements, properties and methods."""
    symbols = []
    class_name = ""
    extends = ""
    implements = []
    is_abstract = False
    is_final = False

    for child in node.children:
        if child.type == "name":
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "abstract_modifier":
            is_abstract = True
        elif child.type == "final_modifier":
            is_final = True
        elif child.type == "base_clause":
            # extends BaseClass
            for bc_child in child.children:
                if bc_child.type == "name":
                    extends = _get_node_text(bc_child, source_bytes)
        elif child.type == "class_interface_clause":
            # implements Interface1, Interface2
            for ic_child in child.children:
                if ic_child.type == "name":
                    implements.append(_get_node_text(ic_child, source_bytes))

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

    docstring = _extract_php_docstring(node, source_bytes)

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
                    prop = _parse_php_property(decl, source_bytes, class_name)
                    symbols.append(prop)
                elif decl.type == "method_declaration":
                    method = _parse_php_method(decl, source_bytes, class_name)
                    symbols.append(method)

    return symbols

def _parse_php_include(node, source_bytes: bytes) -> Import | None:
    """Parse PHP include/require statements."""
    if node.type == "include_expression" or node.type == "require_expression":
        for child in node.children:
            if child.type == "string":
                module = _get_node_text(child, source_bytes)
                # Remove quotes
                module = module.strip('\'"')
                return Import(module=module, names=[], is_from=False)
    return None


def _parse_php_namespace(node, source_bytes: bytes) -> str:
    """Parse PHP namespace definition."""
    for child in node.children:
        if child.type == "namespace_name":
            return _get_node_text(child, source_bytes)
    return ""


def _parse_php_use(node, source_bytes: bytes) -> list[Import]:
    """
    Parse PHP use statement.

    Handles:
    - use App\\Service\\UserService;
    - use App\\Model\\User as UserModel;
    - use App\\Repository\\{UserRepository, OrderRepository};
    """
    imports = []
    base_namespace = ""

    for child in node.children:
        if child.type == "namespace_name":
            # Group import base: use App\Repository\{...}
            base_namespace = _get_node_text(child, source_bytes)

        elif child.type == "namespace_use_clause":
            # Single import
            module = ""
            alias = ""

            for clause_child in child.children:
                if clause_child.type == "qualified_name":
                    module = _get_node_text(clause_child, source_bytes)
                elif clause_child.type == "name" and module:
                    # This is the alias (after 'as')
                    alias = _get_node_text(clause_child, source_bytes)

            if module:
                # If there's a base namespace (group import), prepend it
                if base_namespace:
                    module = f"{base_namespace}\\{module}"

                imports.append(Import(
                    module=module,
                    names=[alias] if alias else [],
                    is_from=True,  # PHP use is similar to Python's from...import
                ))

        elif child.type == "namespace_use_group":
            # Group import: {UserRepository, OrderRepository}
            for group_child in child.children:
                if group_child.type == "namespace_use_clause":
                    name = ""
                    alias = ""
                    for clause_child in group_child.children:
                        if clause_child.type == "qualified_name":
                            name = _get_node_text(clause_child, source_bytes)
                        elif clause_child.type == "name":
                            if not name:
                                name = _get_node_text(clause_child, source_bytes)
                            else:
                                alias = _get_node_text(clause_child, source_bytes)

                    if name:
                        full_module = f"{base_namespace}\\{name}" if base_namespace else name
                        imports.append(Import(
                            module=full_module,
                            names=[alias] if alias else [],
                            is_from=True,
                        ))

    return imports
