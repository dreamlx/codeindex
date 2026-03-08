"""Inheritance extraction for Swift parser.

This module provides functions to extract inheritance relationships from Swift
source code, including class inheritance, protocol inheritance, and protocol conformance.
"""

from tree_sitter import Node, Tree

from ...parser import Inheritance


def extract_inheritances(tree: Tree, source_bytes: bytes) -> list:
    """Extract inheritance relationships from Swift source code.

    Extracts:
    - Class inheritance relationships
    - Protocol inheritance relationships
    - Class/struct conformance to protocols

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code as bytes

    Returns:
        List of Inheritance objects
    """
    inheritances: list[Inheritance] = []
    root = tree.root_node

    # Process all top-level declarations
    for child in root.children:
        if child.type == "class_declaration":
            # Check if it's actually an extension (may have access modifier)
            node_text = child.text.decode("utf-8", errors="replace").strip()
            if " extension " in node_text or node_text.startswith("extension "):
                # This is an extension
                inheritances.extend(_extract_extension_inheritances(child, source_bytes))
            else:
                # Regular class
                inheritances.extend(_extract_type_inheritances(child, source_bytes))
        elif child.type in ["struct_declaration", "protocol_declaration"]:
            inheritances.extend(_extract_type_inheritances(child, source_bytes))
        # Fallback for actual extension_declaration nodes (if they exist)
        elif child.type == "extension_declaration":
            inheritances.extend(_extract_extension_inheritances(child, source_bytes))

    return inheritances


# ==================== Private Helper Functions ====================


def _extract_type_inheritances(node: Node, source_bytes: bytes) -> list:
    """Extract inheritance relationships from class/struct/protocol node.

    Args:
        node: class_declaration/struct_declaration/protocol_declaration node
        source_bytes: Source code bytes

    Returns:
        List of Inheritance objects
    """
    inheritances: list[Inheritance] = []

    # Get type name
    type_name = None
    for child in node.children:
        if child.type == "type_identifier":
            type_name = child.text.decode("utf-8", errors="replace")
            break

    if not type_name:
        return inheritances

    # Find inheritance_specifier nodes
    for child in node.children:
        if child.type == "inheritance_specifier":
            # Extract parent type from this specifier
            parent_type = _extract_parent_type_from_specifier(child, source_bytes)
            if parent_type:
                inheritance = Inheritance(
                    child=type_name,
                    parent=parent_type,
                )
                inheritances.append(inheritance)

    return inheritances


def _extract_parent_type_from_specifier(node: Node, source_bytes: bytes) -> str | None:
    """Extract parent type name from inheritance_specifier node.

    Args:
        node: inheritance_specifier node
        source_bytes: Source code bytes

    Returns:
        Parent type name or None
    """
    # Look for type_identifier in user_type structure
    for child in node.children:
        if child.type == "user_type":
            for subchild in child.children:
                if subchild.type == "type_identifier":
                    return subchild.text.decode("utf-8", errors="replace")
        # Direct type_identifier
        elif child.type == "type_identifier":
            return child.text.decode("utf-8", errors="replace")

    return None


def _extract_extension_inheritances(node: Node, source_bytes: bytes) -> list:
    """Extract inheritance relationships from extension declarations.

    Extensions can add protocol conformance to existing types.

    Args:
        node: extension_declaration node
        source_bytes: Source code bytes

    Returns:
        List of Inheritance objects
    """
    inheritances: list[Inheritance] = []

    # Get extended type name
    extended_type = None
    for child in node.children:
        if child.type in ("type_identifier", "simple_identifier", "user_type"):
            extended_type = child.text.decode("utf-8", errors="replace")
            break

    if not extended_type:
        return inheritances

    # Check for protocol conformance
    for child in node.children:
        if child.type == "inheritance_specifier":
            # Direct inheritance_specifier node
            protocol_name = child.text.decode("utf-8", errors="replace")
            inheritance = Inheritance(child=extended_type, parent=protocol_name)
            inheritances.append(inheritance)
        elif child.type == "type_inheritance_clause":
            # Fallback: nested structure
            parent_types = _extract_parent_types(child, source_bytes)

            # Create Inheritance objects for each protocol
            for parent_type in parent_types:
                inheritance = Inheritance(child=extended_type, parent=parent_type)
                inheritances.append(inheritance)

    return inheritances


def _extract_parent_types(node: Node, source_bytes: bytes) -> list[str]:
    """Extract parent type names from type_inheritance_clause.

    Args:
        node: type_inheritance_clause node
        source_bytes: Source code bytes

    Returns:
        List of parent type names
    """
    parent_types = []

    for child in node.children:
        if child.type == "type_identifier":
            parent_type = child.text.decode("utf-8", errors="replace")
            parent_types.append(parent_type)

    return parent_types
