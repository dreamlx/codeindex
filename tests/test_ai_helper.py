"""Unit tests for AI enhancement helper functions (Epic 4 Story 4.1)."""

from pathlib import Path

from codeindex.parser import ParseResult, Symbol

# ============================================================================
# Tests for aggregate_parse_results()
# ============================================================================


def test_aggregate_multiple_parse_results():
    """Test aggregating multiple parse results."""
    from codeindex.ai_helper import aggregate_parse_results

    # Create test parse results
    pr1 = ParseResult(
        path=Path("file1.py"),
        file_lines=1000,
        symbols=[
            Symbol(
                name="func1",
                kind="function",
                signature="def func1()",
                docstring="",
                line_start=10,
                line_end=20,
            )
        ],
    )
    pr2 = ParseResult(
        path=Path("file2.py"),
        file_lines=2000,
        symbols=[
            Symbol(
                name="func2",
                kind="function",
                signature="def func2()",
                docstring="",
                line_start=10,
                line_end=20,
            ),
            Symbol(
                name="func3",
                kind="function",
                signature="def func3()",
                docstring="",
                line_start=30,
                line_end=40,
            ),
        ],
    )

    # Aggregate
    result = aggregate_parse_results([pr1, pr2], Path("aggregated"))

    # Assertions
    assert result.path == Path("aggregated")
    assert result.file_lines == 3000
    assert len(result.symbols) == 3
    assert result.symbols[0].name == "func1"
    assert result.symbols[1].name == "func2"
    assert result.symbols[2].name == "func3"


def test_aggregate_single_parse_result():
    """Test aggregating a single parse result."""
    from codeindex.ai_helper import aggregate_parse_results

    pr = ParseResult(
        path=Path("file1.py"),
        file_lines=1000,
        symbols=[
            Symbol(
                name="func1",
                kind="function",
                signature="def func1()",
                docstring="",
                line_start=10,
                line_end=20,
            )
        ],
    )

    result = aggregate_parse_results([pr], Path("single"))

    assert result.path == Path("single")
    assert result.file_lines == 1000
    assert len(result.symbols) == 1
    assert result.symbols[0].name == "func1"


def test_aggregate_empty_parse_results():
    """Test aggregating empty list."""
    from codeindex.ai_helper import aggregate_parse_results

    result = aggregate_parse_results([], Path("empty"))

    assert result.path == Path("empty")
    assert result.file_lines == 0
    assert len(result.symbols) == 0


def test_aggregate_preserves_symbol_order():
    """Test that aggregation preserves symbol order."""
    from codeindex.ai_helper import aggregate_parse_results

    pr1 = ParseResult(
        path=Path("file1.py"),
        file_lines=100,
        symbols=[
            Symbol("a", "function", "def a()", "", 1, 2),
            Symbol("b", "function", "def b()", "", 3, 4),
        ],
    )
    pr2 = ParseResult(
        path=Path("file2.py"),
        file_lines=200,
        symbols=[
            Symbol("c", "function", "def c()", "", 1, 2),
            Symbol("d", "function", "def d()", "", 3, 4),
        ],
    )

    result = aggregate_parse_results([pr1, pr2], Path("ordered"))

    assert [s.name for s in result.symbols] == ["a", "b", "c", "d"]


