"""Python AST parser using tree-sitter."""

from dataclasses import dataclass, field
from pathlib import Path

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
    error: str | None = None


# Initialize tree-sitter parser
PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


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


def _parse_function(node, source_bytes: bytes, class_name: str = "", decorators: list[str] | None = None) -> Symbol:
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
    Parse a Python file and extract symbols and imports.

    Args:
        path: Path to the Python file

    Returns:
        ParseResult containing symbols, imports, and docstrings
    """
    try:
        source_bytes = path.read_bytes()
    except Exception as e:
        return ParseResult(path=path, error=str(e))

    try:
        tree = _parser.parse(source_bytes)
    except Exception as e:
        return ParseResult(path=path, error=f"Parse error: {e}")

    symbols: list[Symbol] = []
    imports: list[Import] = []

    # Extract module docstring
    module_docstring = _extract_module_docstring(tree, source_bytes)

    # Walk the AST
    root = tree.root_node
    for child in root.children:
        if child.type == "function_definition":
            symbols.append(_parse_function(child, source_bytes))
        elif child.type == "class_definition":
            symbols.extend(_parse_class(child, source_bytes))
        elif child.type == "decorated_definition":
            # Handle decorated functions/classes (e.g., @click.command())
            for dec_child in child.children:
                if dec_child.type == "function_definition":
                    symbols.append(_parse_function(dec_child, source_bytes))
                elif dec_child.type == "class_definition":
                    symbols.extend(_parse_class(dec_child, source_bytes))
        elif child.type in ("import_statement", "import_from_statement"):
            imp = _parse_import(child, source_bytes)
            if imp:
                imports.append(imp)

    return ParseResult(
        path=path,
        symbols=symbols,
        imports=imports,
        module_docstring=module_docstring,
    )


def parse_directory(paths: list[Path]) -> list[ParseResult]:
    """Parse multiple files."""
    return [parse_file(p) for p in paths]
