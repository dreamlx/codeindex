"""Inheritance extraction for TypeScript/JavaScript parser.

This module provides functions to extract class and interface inheritance
relationships from TypeScript/JavaScript source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Inheritance
from ..utils import get_node_text


def extract_inheritances(tree: Tree, source_bytes: bytes) -> list:
    """Extract class/interface inheritance relationships.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Inheritance objects
    """
    inheritances = []
    root = tree.root_node

    for child in root.children:
        _extract_inheritances_from_node(child, source_bytes, inheritances)

    return inheritances


def _extract_inheritances_from_node(
    node: Node, source_bytes: bytes, inheritances: list[Inheritance]
):
    """Recursively extract inheritance from a node.

    Args:
        node: The node to extract from
        source_bytes: The source code as bytes
        inheritances: List to accumulate Inheritance objects
    """
    if node.type in ("class_declaration", "abstract_class_declaration"):
        class_name = ""
        for child in node.children:
            if child.type in ("type_identifier", "identifier"):
                class_name = get_node_text(child, source_bytes)
            elif child.type == "class_heritage" and class_name:
                extends, implements_list = _parse_class_heritage(child, source_bytes)
                if extends:
                    # Strip generic params for inheritance
                    parent = _strip_generic_type(extends)
                    inheritances.append(Inheritance(child=class_name, parent=parent))
                for impl in implements_list:
                    parent = _strip_generic_type(impl)
                    inheritances.append(Inheritance(child=class_name, parent=parent))

    elif node.type == "interface_declaration":
        iface_name = ""
        for child in node.children:
            if child.type == "type_identifier":
                iface_name = get_node_text(child, source_bytes)
            elif child.type == "extends_type_clause" and iface_name:
                for ext_child in child.children:
                    if ext_child.type in ("type_identifier", "generic_type"):
                        parent = _strip_generic_type(
                            get_node_text(ext_child, source_bytes)
                        )
                        inheritances.append(Inheritance(child=iface_name, parent=parent))

    elif node.type == "export_statement":
        for child in node.children:
            _extract_inheritances_from_node(child, source_bytes, inheritances)


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


def _strip_generic_type(type_name: str) -> str:
    """Strip generic type parameters: 'Map<string, User>' → 'Map'.

    Args:
        type_name: Type name possibly containing generic parameters

    Returns:
        Type name without generic parameters
    """
    idx = type_name.find("<")
    if idx >= 0:
        return type_name[:idx].strip()
    return type_name
