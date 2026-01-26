"""Adaptive symbols configuration.

This module defines the configuration structure for adaptive symbol extraction,
which allows dynamically adjusting the number of symbols to extract based on
file size and other factors.
"""

from dataclasses import dataclass, field


@dataclass
class AdaptiveSymbolsConfig:
    """Configuration for adaptive symbol extraction.

    Adaptive symbol extraction adjusts the number of symbols to display in
    README_AI.md files based on file size, ensuring better information coverage
    for large files while keeping smaller files concise.

    Attributes:
        enabled: Whether adaptive symbol extraction is enabled. If False,
                the traditional max_per_file setting is used.
        thresholds: File size thresholds (in lines) for categorizing files.
                   Keys: tiny, small, medium, large, xlarge, huge
                   Values: Line count thresholds
        limits: Symbol count limits for each file size category.
               Keys: tiny, small, medium, large, xlarge, huge, mega
               Values: Maximum symbols to display
        min_symbols: Minimum number of symbols to display, regardless of
                    file size or other factors.
        max_symbols: Maximum number of symbols to display, regardless of
                    file size or other factors.

    Example:
        >>> config = AdaptiveSymbolsConfig(
        ...     enabled=True,
        ...     thresholds={"small": 200, "medium": 500, "large": 1000},
        ...     limits={"small": 15, "medium": 30, "large": 50},
        ... )
        >>> config.enabled
        True
        >>> config.limits["medium"]
        30

    File Size Categories:
        - tiny: < thresholds["tiny"] lines
        - small: < thresholds["small"] lines
        - medium: < thresholds["medium"] lines
        - large: < thresholds["large"] lines
        - xlarge: < thresholds["xlarge"] lines
        - huge: < thresholds["huge"] lines
        - mega: >= thresholds["huge"] lines
    """

    enabled: bool = False
    thresholds: dict[str, int] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)
    min_symbols: int = 5
    max_symbols: int = 200


# Default configuration matching the planning document
DEFAULT_ADAPTIVE_CONFIG = AdaptiveSymbolsConfig(
    enabled=False,  # Disabled by default for backward compatibility
    thresholds={
        "tiny": 100,
        "small": 200,
        "medium": 500,
        "large": 1000,
        "xlarge": 2000,
        "huge": 5000,
    },
    limits={
        "tiny": 10,
        "small": 15,
        "medium": 30,
        "large": 50,
        "xlarge": 80,
        "huge": 120,
        "mega": 150,  # For files > 5000 lines
    },
    min_symbols=5,
    max_symbols=200,
)
