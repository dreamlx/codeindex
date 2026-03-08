"""Inheritance extraction for Java parser.

This module provides functions to extract class and interface inheritance
relationships from Java source code using tree-sitter.
"""

from tree_sitter import Tree

from ...parser import Inheritance
from .imports import build_import_map
from .symbols import _parse_java_class, _parse_java_interface


def extract_inheritances(
    tree: Tree,
    source_bytes: bytes,
    namespace: str = "",
    import_map: dict[str, str] | None = None
) -> list[Inheritance]:
    """Extract class inheritance relationships from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes
        namespace: Package namespace (optional)
        import_map: Mapping of short class names to full qualified names

    Returns:
        List of Inheritance objects
    """
    inheritances = []
    root = tree.root_node

    if import_map is None:
        import_map = build_import_map(root, source_bytes)

    # Extract inheritances from type declarations
    for child in root.children:
        if child.type == "class_declaration":
            _parse_java_class(child, source_bytes, namespace, import_map, inheritances)
        elif child.type == "interface_declaration":
            _parse_java_interface(child, source_bytes, namespace, import_map, inheritances)

    return inheritances


def extract_package(tree: Tree, source_bytes: bytes) -> str:
    """Extract Java package declaration.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        Package name or empty string
    """
    from ..utils import get_node_text

    root = tree.root_node

    for child in root.children:
        if child.type == "package_declaration":
            for pkg_child in child.children:
                if pkg_child.type == "scoped_identifier" or pkg_child.type == "identifier":
                    return get_node_text(pkg_child, source_bytes)

    return ""
