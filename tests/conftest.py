"""Shared test fixtures and utilities for codeindex tests."""

from pathlib import Path

import pytest

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol
from codeindex.symbol_scorer import SymbolImportanceScorer


def create_mock_symbol(
    name: str = "test_function",
    kind: str = "function",
    signature: str = "def test_function():",
    docstring: str = "A test function",
    line_start: int = 1,
    line_end: int = 10,
) -> Symbol:
    """Create a mock Symbol for testing.

    Args:
        name: Symbol name
        kind: Symbol kind (function, class, method)
        signature: Symbol signature
        docstring: Symbol docstring
        line_start: Starting line number
        line_end: Ending line number

    Returns:
        A Symbol instance
    """
    return Symbol(
        name=name,
        kind=kind,
        signature=signature,
        docstring=docstring,
        line_start=line_start,
        line_end=line_end,
    )


def create_mock_parse_result(
    file_path: str = "test.php",
    file_lines: int = 300,
    symbol_count: int = 15,
    class_name: str | None = None,
    methods_per_class: int = 0,
) -> ParseResult:
    """Create a mock ParseResult for testing.

    Args:
        file_path: Path to the file
        file_lines: Number of lines in the file
        symbol_count: Number of symbols to create (if not creating a class)
        class_name: Optional class name (for God Class testing)
        methods_per_class: Number of methods in the class

    Returns:
        A ParseResult instance

    Examples:
        >>> # Normal file
        >>> result = create_mock_parse_result(file_lines=300, symbol_count=15)

        >>> # God Class file
        >>> result = create_mock_parse_result(
        ...     file_lines=2000,
        ...     class_name="OperateGoods",
        ...     methods_per_class=57
        ... )
    """
    symbols = []

    if class_name and methods_per_class > 0:
        # Create God Class scenario with methods
        for i in range(methods_per_class):
            symbols.append(
                Symbol(
                    name=f"{class_name}::method{i}",
                    kind="method",
                    signature=f"public function method{i}()",
                    docstring="",
                    line_start=i * 10,
                    line_end=i * 10 + 5,
                )
            )
    else:
        # Create normal symbols (functions)
        for i in range(symbol_count):
            symbols.append(
                Symbol(
                    name=f"function{i}",
                    kind="function",
                    signature=f"function function{i}()",
                    docstring="A normal function",
                    line_start=i * 20,
                    line_end=i * 20 + 15,
                )
            )

    return ParseResult(
        path=Path(file_path),
        file_lines=file_lines,
        symbols=symbols,
        imports=[],
        module_docstring="",
    )


@pytest.fixture
def mock_config():
    """Fixture providing a Config instance."""
    return Config.load()


@pytest.fixture
def symbol_scorer(mock_config):
    """Fixture providing a SymbolImportanceScorer instance."""
    return SymbolImportanceScorer(mock_config)
