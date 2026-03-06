"""Import extraction for Java parser.

This module provides functions to extract import statements and build import
mappings from Java source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Import
from ..utils import get_node_text


def extract_imports(tree: Tree, source_bytes: bytes) -> list[Import]:
    """Extract import statements from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Import objects
    """
    imports = []
    root = tree.root_node

    for child in root.children:
        if child.type == "import_declaration":
            java_import = _parse_java_import(child, source_bytes)
            if java_import:
                imports.append(java_import)

    return imports


def build_import_map(root: Node, source_bytes: bytes) -> dict[str, str]:
    """Build a mapping of short class names to full qualified names from imports.

    Args:
        root: The root node of the parse tree
        source_bytes: The source code as bytes

    Returns:
        Dictionary mapping short class names to full qualified names
    """
    import_map = {}

    for child in root.children:
        if child.type == "import_declaration":
            for import_child in child.children:
                if import_child.type == "scoped_identifier":
                    full_name = get_node_text(import_child, source_bytes)
                    short_name = full_name.split('.')[-1]
                    import_map[short_name] = full_name
                elif import_child.type == "identifier":
                    short_name = get_node_text(import_child, source_bytes)
                    import_map[short_name] = short_name

    return import_map


def build_static_import_map(root: Node, source_bytes: bytes) -> dict[str, str]:
    """Build mapping of statically imported method names to full qualified names.

    Args:
        root: The root node of the parse tree
        source_bytes: The source code as bytes

    Returns:
        Dictionary mapping method names to full qualified names
    """
    static_import_map = {}

    for child in root.children:
        if child.type == "import_declaration":
            is_static = False
            import_path = ""
            has_wildcard = False

            for import_child in child.children:
                if import_child.type == "static":
                    is_static = True
                elif import_child.type == "scoped_identifier":
                    import_path = get_node_text(import_child, source_bytes)
                elif import_child.type in ("asterisk", "asterisk_import"):
                    has_wildcard = True

            if is_static and import_path and has_wildcard:
                static_import_map[f"_wildcard_{import_path}"] = import_path

            elif is_static and import_path and "." in import_path:
                method_name = import_path.split(".")[-1]
                if method_name not in static_import_map:
                    static_import_map[method_name] = import_path

    return static_import_map


def resolve_static_import(
    method_name: str,
    static_import_map: dict[str, str]
) -> str | None:
    """Resolve statically imported method name to full qualified name.

    Args:
        method_name: The method name to resolve
        static_import_map: Dictionary of static imports

    Returns:
        Full qualified name or None if not found
    """
    if method_name in static_import_map:
        return static_import_map[method_name]

    for key, package in static_import_map.items():
        if key.startswith("_wildcard_"):
            return f"{package}.{method_name}"

    return None


# ==================== Private Helper Functions ====================


def _parse_java_import(node: Node, source_bytes: bytes) -> Import | None:
    """Parse a Java import statement."""
    module = ""
    is_static = False
    is_wildcard = False

    for child in node.children:
        if child.type == "scoped_identifier" or child.type == "identifier":
            module = get_node_text(child, source_bytes)
        elif child.type == "asterisk":
            is_wildcard = True
        elif child.type == "static":
            is_static = True

    if module:
        if is_wildcard:
            module = module + ".*"

        return Import(
            module=module,
            names=[],
            is_from=is_static,
        )

    return None
