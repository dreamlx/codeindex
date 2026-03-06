"""Inheritance extraction for Python parser.

This module provides functions to extract class inheritance relationships
from Python source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Inheritance
from ..utils import get_node_text


def extract_inheritances(tree: Tree, source_bytes: bytes) -> list:
    """Extract class inheritance relationships from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Inheritance objects
    """
    inheritances: list[Inheritance] = []
    root = tree.root_node

    for child in root.children:
        if child.type == "class_definition":
            _extract_class_inheritances(child, source_bytes, "", inheritances)
        elif child.type == "decorated_definition":
            for dec_child in child.children:
                if dec_child.type == "class_definition":
                    _extract_class_inheritances(dec_child, source_bytes, "", inheritances)

    return inheritances


def _extract_class_inheritances(
    node: Node,
    source_bytes: bytes,
    parent_class: str,
    inheritances: list[Inheritance],
) -> None:
    """Extract inheritances from a class definition (helper for extract_inheritances).

    Args:
        node: Tree-sitter class_definition node
        source_bytes: Source code bytes
        parent_class: Parent class name for nested classes
        inheritances: List to append Inheritance objects to
    """
    class_name = ""
    bases = []

    for child in node.children:
        if child.type == "identifier":
            class_name = get_node_text(child, source_bytes)
        elif child.type == "argument_list":
            for arg_child in child.children:
                if arg_child.type in ("identifier", "attribute", "subscript"):
                    base_text = get_node_text(arg_child, source_bytes)
                    base_name = base_text.split("[")[0] if "[" in base_text else base_text
                    bases.append(base_name)

    full_class_name = f"{parent_class}.{class_name}" if parent_class else class_name

    # Add inheritances
    for base in bases:
        inheritances.append(Inheritance(child=full_class_name, parent=base))

    # Process nested classes
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "class_definition":
                    _extract_class_inheritances(
                        block_child, source_bytes, full_class_name, inheritances
                    )
