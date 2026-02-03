"""AI enhancement helper functions (Epic 4 Story 4.1).

This module provides reusable functions for AI enhancement operations,
eliminating code duplication in scan and scan-all commands.
"""

from pathlib import Path

from codeindex.parser import ParseResult


def aggregate_parse_results(
    parse_results: list[ParseResult],
    path: Path,
) -> ParseResult:
    """Aggregate multiple parse results into one.

    Combines symbols and line counts from multiple parse results into a single
    ParseResult. This is useful for analyzing multi-file directories.

    Args:
        parse_results: List of parse results to aggregate
        path: Path for the aggregated result

    Returns:
        ParseResult with combined symbols and total line count

    Example:
        >>> pr1 = ParseResult(Path("a.py"), file_lines=100, symbols=[...])
        >>> pr2 = ParseResult(Path("b.py"), file_lines=200, symbols=[...])
        >>> aggregated = aggregate_parse_results([pr1, pr2], Path("dir"))
        >>> aggregated.file_lines
        300
    """
    all_symbols = []
    total_lines = 0

    for pr in parse_results:
        all_symbols.extend(pr.symbols)
        total_lines += pr.file_lines

    return ParseResult(
        path=path,
        file_lines=total_lines,
        symbols=all_symbols,
    )


