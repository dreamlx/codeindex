"""Unit tests for AI enhancement helper functions (Epic 4 Story 4.1)."""

from pathlib import Path

import pytest

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


# ============================================================================
# Tests for execute_multi_turn_enhancement() - To be implemented
# ============================================================================


def test_execute_multi_turn_with_auto_detection_super_large():
    """Test execute_multi_turn_enhancement with auto detection for super large file."""
    from unittest.mock import MagicMock, patch

    from codeindex.ai_enhancement import MultiTurnResult
    from codeindex.ai_helper import execute_multi_turn_enhancement
    from codeindex.config import Config
    from codeindex.writer import WriteResult

    # Setup
    config = Config.load()
    parse_results = [
        ParseResult(
            path=Path("large.py"),
            file_lines=6000,
            symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(120)],
        )
    ]

    # Mock multi_turn_ai_enhancement to return success
    mock_result = MultiTurnResult(
        success=True,
        final_readme="# README\nContent",
        rounds_completed=["round1", "round2", "round3"],
        error=None,
        round_outputs={},
        total_time=10.5,
        fallback_used=False,
    )

    mock_write_result = WriteResult(
        path=Path("README_AI.md"), success=True, error=""
    )

    with patch("codeindex.ai_enhancement.multi_turn_ai_enhancement", return_value=mock_result):
        with patch("codeindex.writer.write_readme", return_value=mock_write_result):
            # Execute
            success, write_result, message = execute_multi_turn_enhancement(
                dir_path=Path("/test"),
                parse_results=parse_results,
                config=config,
                timeout=120,
                strategy="auto",
                quiet=True,
            )

    # Assertions
    assert success is True
    assert write_result is not None
    assert write_result.success is True
    assert "Multi-turn complete" in message
    assert "10.5s" in message


def test_execute_multi_turn_with_explicit_strategy():
    """Test execute_multi_turn_enhancement with explicit multi_turn strategy."""
    from unittest.mock import patch

    from codeindex.ai_enhancement import MultiTurnResult
    from codeindex.ai_helper import execute_multi_turn_enhancement
    from codeindex.config import Config
    from codeindex.writer import WriteResult

    config = Config.load()
    parse_results = [
        ParseResult(
            path=Path("normal.py"),
            file_lines=2000,  # Not super large
            symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(30)],
        )
    ]

    mock_result = MultiTurnResult(
        success=True,
        final_readme="# README",
        rounds_completed=["round1", "round2", "round3"],
        error=None,
        round_outputs={},
        total_time=8.0,
        fallback_used=False,
    )

    mock_write_result = WriteResult(
        path=Path("README_AI.md"), success=True, error=""
    )

    with patch("codeindex.ai_enhancement.multi_turn_ai_enhancement", return_value=mock_result):
        with patch("codeindex.writer.write_readme", return_value=mock_write_result):
            # Execute with explicit multi_turn strategy
            success, write_result, message = execute_multi_turn_enhancement(
                dir_path=Path("/test"),
                parse_results=parse_results,
                config=config,
                timeout=120,
                strategy="multi_turn",
                quiet=True,
            )

    # Should execute multi-turn even though file is not super large
    assert success is True
    assert write_result is not None


def test_execute_multi_turn_with_standard_strategy_should_fail():
    """Test that standard strategy returns failure."""
    from codeindex.ai_helper import execute_multi_turn_enhancement
    from codeindex.config import Config

    config = Config.load()
    parse_results = [
        ParseResult(
            path=Path("large.py"),
            file_lines=6000,
            symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(120)],
        )
    ]

    # Execute with standard strategy
    success, write_result, message = execute_multi_turn_enhancement(
        dir_path=Path("/test"),
        parse_results=parse_results,
        config=config,
        timeout=120,
        strategy="standard",
        quiet=True,
    )

    # Should return failure because standard strategy skips multi-turn
    assert success is False
    assert write_result is None
    assert "Multi-turn not applicable" in message


def test_execute_multi_turn_with_multi_turn_failure():
    """Test handling of multi-turn dialogue failure."""
    from unittest.mock import patch

    from codeindex.ai_enhancement import MultiTurnResult
    from codeindex.ai_helper import execute_multi_turn_enhancement
    from codeindex.config import Config

    config = Config.load()
    parse_results = [
        ParseResult(
            path=Path("large.py"),
            file_lines=6000,
            symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(120)],
        )
    ]

    # Mock multi_turn_ai_enhancement to return failure
    mock_result = MultiTurnResult(
        success=False,
        final_readme=None,
        rounds_completed=["round1"],
        error="Round 2 failed",
        round_outputs={"round1": "..."},
        total_time=5.0,
        fallback_used=True,
    )

    with patch("codeindex.ai_enhancement.multi_turn_ai_enhancement", return_value=mock_result):
        # Execute
        success, write_result, message = execute_multi_turn_enhancement(
            dir_path=Path("/test"),
            parse_results=parse_results,
            config=config,
            timeout=120,
            strategy="auto",
            quiet=True,
        )

    # Should return failure
    assert success is False
    assert write_result is None
    assert "Multi-turn not applicable" in message
