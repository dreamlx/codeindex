"""Symbol extraction for Python parser.

This module provides functions to extract symbols (classes, functions, methods)
from Python source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Inheritance, Symbol
from ..utils import get_node_text


def extract_symbols(tree: Tree, source_bytes: bytes) -> list:
    """Extract symbols (classes, functions, methods) from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Symbol objects
    """
    symbols: list[Symbol] = []
    inheritances: list[Inheritance] = []  # For nested class support
    root = tree.root_node

    for child in root.children:
        if child.type == "function_definition":
            symbols.append(_parse_function(child, source_bytes))
        elif child.type == "class_definition":
            symbols.extend(_parse_class(child, source_bytes, "", inheritances))
        elif child.type == "decorated_definition":
            for dec_child in child.children:
                if dec_child.type == "function_definition":
                    symbols.append(_parse_function(dec_child, source_bytes))
                elif dec_child.type == "class_definition":
                    symbols.extend(_parse_class(dec_child, source_bytes, "", inheritances))

    return symbols


def extract_module_docstring(tree: Tree, source_bytes: bytes) -> str:
    """Extract module-level docstring.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        Module docstring or empty string
    """
    root = tree.root_node
    for child in root.children:
        if child.type == "expression_statement":
            for expr_child in child.children:
                if expr_child.type == "string":
                    text = get_node_text(expr_child, source_bytes)
                    if text.startswith('"""') or text.startswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') or text.startswith("'"):
                        return text[1:-1].strip()
            break
        elif child.type not in ("comment",):
            break
    return ""


def _extract_docstring(node: Node, source_bytes: bytes) -> str:
    """Extract docstring from first child if it's a string.

    Args:
        node: Tree-sitter AST node
        source_bytes: Source code bytes

    Returns:
        Docstring or empty string
    """
    if node.child_count == 0:
        return ""

    # Look for expression_statement containing string
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "expression_statement":
                    for expr_child in block_child.children:
                        if expr_child.type == "string":
                            text = get_node_text(expr_child, source_bytes)
                            # Remove quotes
                            if text.startswith('"""') or text.startswith("'''"):
                                return text[3:-3].strip()
                            elif text.startswith('"') or text.startswith("'"):
                                return text[1:-1].strip()
                    break
            break

    return ""


def _parse_function(
    node: Node,
    source_bytes: bytes,
    class_name: str = "",
    decorators: list[str] | None = None,
) -> Symbol:
    """Parse a function definition node.

    Args:
        node: Tree-sitter function_definition node
        source_bytes: Source code bytes
        class_name: Parent class name (for methods)
        decorators: List of decorator names (unused currently)

    Returns:
        Symbol object representing the function/method
    """
    name = ""
    signature_parts = []

    for child in node.children:
        if child.type == "identifier":  # function name is 'identifier', not 'name'
            name = get_node_text(child, source_bytes)
        elif child.type == "parameters":
            signature_parts.append(get_node_text(child, source_bytes))
        elif child.type == "type":
            signature_parts.append(f" -> {get_node_text(child, source_bytes)}")

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


def _parse_class(
    node: Node,
    source_bytes: bytes,
    parent_class: str = "",
    inheritances: list[Inheritance] | None = None,
) -> list[Symbol]:
    """Parse a class definition node and its methods.

    Args:
        node: Tree-sitter class_definition node
        source_bytes: Source code bytes
        parent_class: Parent class name for nested classes (e.g., "Outer" for Outer.Inner)
        inheritances: List to append Inheritance objects to (Epic 10, Story 10.1.1)

    Returns:
        List of Symbol objects (class + methods)
    """
    if inheritances is None:
        inheritances = []

    symbols = []
    class_name = ""
    bases = []

    for child in node.children:
        if child.type == "identifier":  # class name is 'identifier', not 'name'
            class_name = get_node_text(child, source_bytes)
        elif child.type == "argument_list":
            # Extract base classes from argument_list
            # Format: (BaseA, BaseB, Generic[T])
            for arg_child in child.children:
                if arg_child.type in ("identifier", "attribute", "subscript"):
                    base_text = get_node_text(arg_child, source_bytes)
                    # Remove generic type parameters: List[str] -> List
                    base_name = base_text.split("[")[0] if "[" in base_text else base_text
                    bases.append(base_name)

    # Build full class name (handle nested classes)
    full_class_name = f"{parent_class}.{class_name}" if parent_class else class_name

    signature = f"class {class_name}"
    if bases:
        signature += f"({', '.join(bases)})"

    docstring = _extract_docstring(node, source_bytes)

    symbols.append(
        Symbol(
            name=full_class_name,
            kind="class",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Create Inheritance objects (Epic 10, Story 10.1.1)
    for base in bases:
        inheritances.append(Inheritance(child=full_class_name, parent=base))

    # Parse methods and nested classes
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "function_definition":
                    method = _parse_function(block_child, source_bytes, full_class_name)
                    symbols.append(method)
                elif block_child.type == "class_definition":
                    # Nested class (Epic 10, Story 10.1.1)
                    nested_symbols = _parse_class(
                        block_child, source_bytes, full_class_name, inheritances
                    )
                    symbols.extend(nested_symbols)

    return symbols
