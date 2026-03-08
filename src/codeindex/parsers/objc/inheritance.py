"""Inheritance extraction for Objective-C parser.

This module provides functions to extract inheritance relationships:
- Class inheritance (superclass)
- Protocol conformance
- Protocol inheritance
"""

from tree_sitter import Tree

from ...parser import Inheritance
from ..utils import get_node_text


def extract_inheritances(tree: Tree, source_bytes: bytes) -> list:
    """Extract inheritance relationships from Objective-C code.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code as bytes

    Returns:
        List of Inheritance objects
    """
    inheritances = []
    root = tree.root_node

    for child in root.children:
        if child.type == "class_interface":
            inheritances.extend(_extract_interface_inheritance(child, source_bytes))
        elif child.type == "protocol_declaration":
            inheritances.extend(_extract_protocol_inheritance(child, source_bytes))

    return inheritances


def _extract_interface_inheritance(node, source_bytes: bytes) -> list[Inheritance]:
    """Extract inheritance from @interface.

    Args:
        node: class_interface node
        source_bytes: Source code bytes

    Returns:
        List of Inheritance objects
    """
    inheritances = []

    # Get class name (first identifier)
    class_name = None
    for child in node.children:
        if child.type == "identifier":
            class_name = get_node_text(child, source_bytes)
            break

    if not class_name:
        return inheritances

    # Extract superclass (second identifier after ':')
    found_colon = False
    for child in node.children:
        if child.type == ":":
            found_colon = True
        elif found_colon and child.type == "identifier":
            superclass = get_node_text(child, source_bytes)
            inheritances.append(
                Inheritance(child=class_name, parent=superclass)
            )
            break

    # Extract protocol conformances (from parameterized_arguments)
    for child in node.children:
        if child.type == "parameterized_arguments":
            for subchild in child.children:
                if subchild.type == "type_name":
                    # Get type_identifier from type_name
                    for type_child in subchild.children:
                        if type_child.type == "type_identifier":
                            protocol = get_node_text(type_child, source_bytes)
                            inheritances.append(
                                Inheritance(child=class_name, parent=protocol)
                            )
                            break

    return inheritances


def _extract_protocol_inheritance(node, source_bytes: bytes) -> list[Inheritance]:
    """Extract inheritance from @protocol.

    Args:
        node: protocol_declaration node
        source_bytes: Source code bytes

    Returns:
        List of Inheritance objects
    """
    inheritances = []

    # Get protocol name (first identifier)
    protocol_name = None
    for child in node.children:
        if child.type == "identifier":
            protocol_name = get_node_text(child, source_bytes)
            break

    if not protocol_name:
        return inheritances

    # Extract parent protocols from protocol_reference_list
    for child in node.children:
        if child.type == "protocol_reference_list":
            # Extract all identifiers in the list
            for subchild in child.children:
                if subchild.type == "identifier":
                    parent_protocol = get_node_text(subchild, source_bytes)
                    inheritances.append(
                        Inheritance(child=protocol_name, parent=parent_protocol)
                    )

    return inheritances
