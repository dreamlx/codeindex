"""Call extraction for Swift parser.

This module provides functions to extract call relationships from Swift source code.

TODO: Phase 3 implementation - call graph extraction.
"""

from tree_sitter import Tree


def extract_calls(
    tree: Tree, source_bytes: bytes, symbols: list, imports: list
) -> list:
    """Extract call relationships from Swift source code.

    TODO: Phase 3 implementation.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code as bytes
        symbols: Previously extracted symbols
        imports: Previously extracted imports

    Returns:
        Empty list (not implemented yet)
    """
    # Phase 3: Implement call graph extraction
    return []
