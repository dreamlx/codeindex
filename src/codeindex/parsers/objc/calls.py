"""Call extraction for Objective-C parser.

This module provides functions to extract function/method calls from Objective-C code.

Note: Call graph extraction is planned for a future story.
For now, this returns an empty list to satisfy the parser interface.
"""

from tree_sitter import Tree


def extract_calls(
    tree: Tree, source_bytes: bytes, symbols: list, imports: list
) -> list:
    """Extract function/method calls from Objective-C code.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code as bytes
        symbols: List of symbols (for context)
        imports: List of imports (for resolution)

    Returns:
        List of Call objects (empty for now)
    """
    # Call graph extraction will be implemented in a future story
    # For now, return empty list to satisfy BaseLanguageParser interface
    return []
