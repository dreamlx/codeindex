"""Unit tests for file size classifier (Epic 4 Story 4.2)."""

from pathlib import Path

import pytest

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol


# ============================================================================
# Tests for FileSizeClassifier
# ============================================================================


def test_classify_tiny_file():
    """Test classification of tiny file."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("tiny.py"),
        file_lines=300,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(10)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.TINY
    assert analysis.file_lines == 300
    assert analysis.symbol_count == 10
    assert not analysis.exceeds_line_threshold
    assert not analysis.exceeds_symbol_threshold


def test_classify_small_file():
    """Test classification of small file."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("small.py"),
        file_lines=800,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(15)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.SMALL


def test_classify_medium_file():
    """Test classification of medium file."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("medium.py"),
        file_lines=1500,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(25)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.MEDIUM


def test_classify_large_file():
    """Test classification of large file."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("large.php"),
        file_lines=3000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(45)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.LARGE
    assert not analysis.exceeds_line_threshold  # 3000 < 5000
    assert not analysis.exceeds_symbol_threshold  # 45 < 100


def test_classify_super_large_by_lines():
    """Test super large classification by line count."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("super_large.php"),
        file_lines=6000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(50)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.SUPER_LARGE
    assert analysis.exceeds_line_threshold is True
    assert analysis.exceeds_symbol_threshold is False
    assert analysis.reason == "excessive_lines"


def test_classify_super_large_by_symbols():
    """Test super large classification by symbol count."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("super_large.py"),
        file_lines=3000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(120)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.SUPER_LARGE
    assert analysis.exceeds_line_threshold is False
    assert analysis.exceeds_symbol_threshold is True
    assert analysis.reason == "excessive_symbols"


def test_classify_super_large_by_both():
    """Test super large classification by both criteria."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    parse_result = ParseResult(
        path=Path("huge.php"),
        file_lines=10000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(150)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.SUPER_LARGE
    assert analysis.exceeds_line_threshold is True
    assert analysis.exceeds_symbol_threshold is True
    assert analysis.reason == "excessive_lines,excessive_symbols"


def test_is_super_large_convenience_method():
    """Test is_super_large() convenience method."""
    from codeindex.file_classifier import FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    # Super large file
    pr_super = ParseResult(
        path=Path("super.py"),
        file_lines=6000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(50)],
    )
    assert classifier.is_super_large(pr_super) is True

    # Normal file
    pr_normal = ParseResult(
        path=Path("normal.py"),
        file_lines=1000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(20)],
    )
    assert classifier.is_super_large(pr_normal) is False


def test_is_large_convenience_method():
    """Test is_large() convenience method."""
    from codeindex.file_classifier import FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    # Super large is also large
    pr_super = ParseResult(
        path=Path("super.py"),
        file_lines=6000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(50)],
    )
    assert classifier.is_large(pr_super) is True

    # Large file
    pr_large = ParseResult(
        path=Path("large.py"),
        file_lines=3000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(40)],
    )
    assert classifier.is_large(pr_large) is True

    # Medium file is not large
    pr_medium = ParseResult(
        path=Path("medium.py"),
        file_lines=1500,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(25)],
    )
    assert classifier.is_large(pr_medium) is False


def test_custom_thresholds():
    """Test custom thresholds from config."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    # Override thresholds
    config.ai_enhancement.super_large_lines = 3000
    config.ai_enhancement.super_large_symbols = 80

    classifier = FileSizeClassifier(config)

    # This file would be large with default thresholds, but super large with custom
    parse_result = ParseResult(
        path=Path("test.py"),
        file_lines=3500,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(60)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.SUPER_LARGE
    assert analysis.exceeds_line_threshold is True


def test_edge_case_exactly_at_threshold():
    """Test file exactly at threshold (should not be super large)."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    # Exactly 5000 lines (threshold is > 5000)
    parse_result = ParseResult(
        path=Path("edge.py"),
        file_lines=5000,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(100)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.LARGE  # Not super large
    assert not analysis.exceeds_line_threshold
    assert not analysis.exceeds_symbol_threshold


def test_edge_case_just_over_threshold():
    """Test file just over threshold (should be super large)."""
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    config = Config.load()
    classifier = FileSizeClassifier(config)

    # 5001 lines (threshold is > 5000)
    parse_result = ParseResult(
        path=Path("edge.py"),
        file_lines=5001,
        symbols=[Symbol(f"func{i}", "function", "", "", i, i) for i in range(101)],
    )

    analysis = classifier.classify(parse_result)

    assert analysis.category == FileSizeCategory.SUPER_LARGE
    assert analysis.exceeds_line_threshold is True
    assert analysis.exceeds_symbol_threshold is True
