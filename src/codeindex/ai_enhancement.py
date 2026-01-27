"""AI enhancement strategies for super large files (Epic 3.2).

This module provides intelligent file size detection and strategy selection
for optimizing AI-powered documentation generation.
"""

from dataclasses import dataclass
from typing import Literal

from codeindex.config import Config
from codeindex.parser import ParseResult

EnhancementStrategy = Literal["standard", "hierarchical", "multi_turn"]


@dataclass
class SuperLargeFileDetection:
    """Result of super large file detection."""

    is_super_large: bool
    reason: str | None  # "excessive_lines", "excessive_symbols", or combination
    recommended_strategy: EnhancementStrategy
    file_lines: int
    symbol_count: int


def is_super_large_file(parse_result: ParseResult, config: Config) -> SuperLargeFileDetection:
    """Detect if a file is super large and needs multi-turn dialogue.

    A file is considered super large if:
    - Lines > super_large_lines threshold (default 5000), OR
    - Symbols > super_large_symbols threshold (default 100)

    Args:
        parse_result: Parsed file data with symbols and line count
        config: Configuration with super_large thresholds

    Returns:
        SuperLargeFileDetection with detection result and recommended strategy
    """
    file_lines = parse_result.file_lines
    symbol_count = len(parse_result.symbols)

    # Get thresholds from config
    lines_threshold = config.ai_enhancement.super_large_lines
    symbols_threshold = config.ai_enhancement.super_large_symbols

    # Check thresholds
    exceeds_lines = file_lines > lines_threshold
    exceeds_symbols = symbol_count > symbols_threshold

    # Determine if super large
    is_super_large = exceeds_lines or exceeds_symbols

    # Build reason string
    reasons = []
    if exceeds_lines:
        reasons.append("excessive_lines")
    if exceeds_symbols:
        reasons.append("excessive_symbols")

    reason = ",".join(reasons) if reasons else None

    # Determine strategy
    if is_super_large:
        recommended_strategy = "multi_turn"
    elif file_lines > 2000 or symbol_count > 40:
        # Large but not super large
        recommended_strategy = "hierarchical"
    else:
        recommended_strategy = "standard"

    return SuperLargeFileDetection(
        is_super_large=is_super_large,
        reason=reason,
        recommended_strategy=recommended_strategy,
        file_lines=file_lines,
        symbol_count=symbol_count,
    )


def select_enhancement_strategy(
    parse_result: ParseResult,
    config: Config,
) -> EnhancementStrategy:
    """Select appropriate AI enhancement strategy based on file size.

    Strategy selection:
    - Super large (>5000 lines OR >100 symbols): multi_turn
    - Large (>2000 lines OR >40 symbols): hierarchical
    - Normal: standard

    Args:
        parse_result: Parsed file data
        config: Configuration with thresholds

    Returns:
        Enhancement strategy: "standard", "hierarchical", or "multi_turn"
    """
    detection = is_super_large_file(parse_result, config)
    return detection.recommended_strategy
