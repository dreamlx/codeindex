"""Utility functions for language parsers.

This module contains helper functions that are shared across multiple language parsers.
"""

from typing import Optional

from tree_sitter import Node


def get_node_text(node: Node, source_bytes: bytes) -> str:
    """Extract text from a tree-sitter node.

    Args:
        node: The tree-sitter node
        source_bytes: The source code as bytes

    Returns:
        The text content of the node as a string
    """
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def count_arguments(args_node: Node) -> Optional[int]:
    """Count arguments in argument_list node (best-effort).

    This function attempts to count the number of arguments in a function call.
    It works across languages by skipping syntax elements like parentheses and commas.

    Args:
        args_node: Tree-sitter argument_list node

    Returns:
        Number of arguments, or None if cannot determine
    """
    if not args_node or args_node.type != "argument_list":
        return None

    count = 0
    for child in args_node.children:
        # Count actual argument nodes (skip parentheses and commas)
        if child.type not in ("(", ")", ","):
            count += 1

    return count if count > 0 else None
