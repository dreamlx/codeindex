"""Unified file size classification system (Epic 4 Story 4.2).

This module provides a unified approach to file size classification,
replacing hard-coded constants in tech_debt and ai_enhancement modules.
"""

from dataclasses import dataclass
from enum import Enum

from codeindex.config import Config
from codeindex.parser import ParseResult


class FileSizeCategory(Enum):
    """File size categories for classification."""

    TINY = "tiny"  # <500 lines
    SMALL = "small"  # 500-1000 lines
    MEDIUM = "medium"  # 1000-2000 lines
    LARGE = "large"  # 2000-5000 lines (or 40-100 symbols)
    SUPER_LARGE = "super_large"  # >5000 lines OR >100 symbols


@dataclass
class FileSizeAnalysis:
    """Result of file size analysis.

    Attributes:
        category: File size category (enum)
        file_lines: Number of lines in the file
        symbol_count: Number of symbols in the file
        exceeds_line_threshold: True if file exceeds super_large_lines threshold
        exceeds_symbol_threshold: True if file exceeds super_large_symbols threshold
        reason: Human-readable reason (e.g., "excessive_lines", "excessive_symbols")
    """

    category: FileSizeCategory
    file_lines: int
    symbol_count: int
    exceeds_line_threshold: bool
    exceeds_symbol_threshold: bool
    reason: str | None = None


class FileSizeClassifier:
    """Unified file size classifier for all modules.

    This classifier provides consistent file size detection across
    tech_debt and ai_enhancement modules, using configurable thresholds.

    Example:
        >>> config = Config.load()
        >>> classifier = FileSizeClassifier(config)
        >>> analysis = classifier.classify(parse_result)
        >>> if analysis.category == FileSizeCategory.SUPER_LARGE:
        ...     # Super large file detected
    """

    def __init__(self, config: Config):
        """Initialize classifier with configuration.

        Args:
            config: Configuration containing threshold values
        """
        self.config = config
        # Super large thresholds for tech debt detection
        self.super_large_lines = 5000
        self.super_large_symbols = 100

    def classify(self, parse_result: ParseResult) -> FileSizeAnalysis:
        """Classify file size based on lines and symbol count.

        Classification rules:
        - TINY: < 500 lines
        - SMALL: 500-1000 lines
        - MEDIUM: 1000-2000 lines
        - LARGE: 2000-5000 lines (or 40-100 symbols)
        - SUPER_LARGE: > super_large_lines OR > super_large_symbols

        Args:
            parse_result: Parsed file data with lines and symbols

        Returns:
            FileSizeAnalysis with category, thresholds, and reason
        """
        file_lines = parse_result.file_lines
        symbol_count = len(parse_result.symbols)

        # Check super large thresholds
        exceeds_lines = file_lines > self.super_large_lines
        exceeds_symbols = symbol_count > self.super_large_symbols

        # Build reason string
        reasons = []
        if exceeds_lines:
            reasons.append("excessive_lines")
        if exceeds_symbols:
            reasons.append("excessive_symbols")
        reason = ",".join(reasons) if reasons else None

        # Determine category
        if exceeds_lines or exceeds_symbols:
            category = FileSizeCategory.SUPER_LARGE
        elif file_lines > 2000 or symbol_count > 40:
            category = FileSizeCategory.LARGE
        elif file_lines > 1000:
            category = FileSizeCategory.MEDIUM
        elif file_lines > 500:
            category = FileSizeCategory.SMALL
        else:
            category = FileSizeCategory.TINY

        return FileSizeAnalysis(
            category=category,
            file_lines=file_lines,
            symbol_count=symbol_count,
            exceeds_line_threshold=exceeds_lines,
            exceeds_symbol_threshold=exceeds_symbols,
            reason=reason,
        )

    def is_super_large(self, parse_result: ParseResult) -> bool:
        """Check if file is super large.

        Convenience method that returns True if category is SUPER_LARGE.

        Args:
            parse_result: Parsed file data

        Returns:
            True if file is super large, False otherwise
        """
        analysis = self.classify(parse_result)
        return analysis.category == FileSizeCategory.SUPER_LARGE

    def is_large(self, parse_result: ParseResult) -> bool:
        """Check if file is large or super large.

        Convenience method for checking if a file needs special handling.

        Args:
            parse_result: Parsed file data

        Returns:
            True if file is large or super large, False otherwise
        """
        analysis = self.classify(parse_result)
        return analysis.category in [FileSizeCategory.LARGE, FileSizeCategory.SUPER_LARGE]
