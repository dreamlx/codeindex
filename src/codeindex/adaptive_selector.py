"""Adaptive symbol selector for dynamic symbol limit calculation.

This module implements the core algorithm for adaptive symbol extraction,
which adjusts the number of symbols to display based on file size.
"""

from codeindex.adaptive_config import DEFAULT_ADAPTIVE_CONFIG, AdaptiveSymbolsConfig


class AdaptiveSymbolSelector:
    """Selects appropriate symbol limit based on file size.

    This selector implements a tiered approach where larger files get
    more symbols displayed, improving information coverage while keeping
    smaller files concise.

    The algorithm works in three steps:
    1. Determine file size category (tiny/small/medium/large/xlarge/huge/mega)
    2. Get configured symbol limit for that category
    3. Apply constraints (min/max symbols, total available symbols)

    Attributes:
        config: AdaptiveSymbolsConfig instance controlling the selection logic

    Example:
        >>> selector = AdaptiveSymbolSelector()
        >>> limit = selector.calculate_limit(8891, 57)  # 8891 lines, 57 symbols
        >>> print(limit)  # Returns 57 (mega category limit=150, but only 57 symbols)
        57
        >>> limit = selector.calculate_limit(500, 100)  # 500 lines, 100 symbols
        >>> print(limit)  # Returns 50 (large category limit=50)
        50
    """

    def __init__(self, config: AdaptiveSymbolsConfig | None = None):
        """Initialize selector with optional configuration.

        Args:
            config: AdaptiveSymbolsConfig instance. If None, uses DEFAULT_ADAPTIVE_CONFIG.
        """
        if config is None:
            # Use default config, creating a copy to avoid mutation
            self.config = AdaptiveSymbolsConfig(
                enabled=DEFAULT_ADAPTIVE_CONFIG.enabled,
                thresholds=DEFAULT_ADAPTIVE_CONFIG.thresholds.copy(),
                limits=DEFAULT_ADAPTIVE_CONFIG.limits.copy(),
                min_symbols=DEFAULT_ADAPTIVE_CONFIG.min_symbols,
                max_symbols=DEFAULT_ADAPTIVE_CONFIG.max_symbols,
            )
        else:
            # Merge custom config with defaults to ensure all fields are present
            self.config = AdaptiveSymbolsConfig(
                enabled=config.enabled,
                thresholds={**DEFAULT_ADAPTIVE_CONFIG.thresholds, **config.thresholds},
                limits={**DEFAULT_ADAPTIVE_CONFIG.limits, **config.limits},
                min_symbols=config.min_symbols,
                max_symbols=config.max_symbols,
            )

    def calculate_limit(self, file_lines: int, total_symbols: int) -> int:
        """Calculate appropriate symbol limit for a file.

        This is the main entry point for the adaptive selection algorithm.

        Args:
            file_lines: Number of lines in the file
            total_symbols: Total number of symbols available in the file

        Returns:
            int: Number of symbols to display (between min_symbols and max_symbols)

        Example:
            >>> selector = AdaptiveSymbolSelector()
            >>> selector.calculate_limit(100, 20)  # small file, 20 symbols
            15
            >>> selector.calculate_limit(10000, 200)  # huge file, 200 symbols
            150
        """
        # Step 1: Determine file size category
        category = self._determine_size_category(file_lines)

        # Step 2: Get configured limit for this category
        limit = self.config.limits[category]

        # Step 3: Apply constraints
        limit = self._apply_constraints(limit, total_symbols)

        return limit

    def _determine_size_category(self, lines: int) -> str:
        """Determine file size category based on line count.

        Categories are determined by comparing against configured thresholds:
        - tiny: < thresholds["tiny"] (default: <100)
        - small: < thresholds["small"] (default: 100-199)
        - medium: < thresholds["medium"] (default: 200-499)
        - large: < thresholds["large"] (default: 500-999)
        - xlarge: < thresholds["xlarge"] (default: 1000-1999)
        - huge: < thresholds["huge"] (default: 2000-4999)
        - mega: >= thresholds["huge"] (default: >=5000)

        Args:
            lines: Number of lines in the file

        Returns:
            str: Size category name

        Example:
            >>> selector = AdaptiveSymbolSelector()
            >>> selector._determine_size_category(50)
            'tiny'
            >>> selector._determine_size_category(150)
            'small'
            >>> selector._determine_size_category(8891)
            'mega'
        """
        thresholds = self.config.thresholds

        if lines < thresholds["tiny"]:
            return "tiny"
        elif lines < thresholds["small"]:
            return "small"
        elif lines < thresholds["medium"]:
            return "medium"
        elif lines < thresholds["large"]:
            return "large"
        elif lines < thresholds["xlarge"]:
            return "xlarge"
        elif lines < thresholds["huge"]:
            return "huge"
        else:
            return "mega"

    def _apply_constraints(self, limit: int, total_symbols: int) -> int:
        """Apply constraints to ensure limit is valid.

        Constraints applied:
        1. Not exceed total_symbols (can't display more symbols than available)
        2. Not less than min_symbols (only if total_symbols >= min_symbols)
        3. Not exceed max_symbols (prevent overly long README files)

        Args:
            limit: Calculated limit from category
            total_symbols: Total symbols available in the file

        Returns:
            int: Constrained limit

        Example:
            >>> selector = AdaptiveSymbolSelector()
            >>> selector._apply_constraints(50, 30)  # Want 50, but only 30 available
            30
            >>> selector._apply_constraints(250, 300)  # Want 250, but max is 200
            200
            >>> selector._apply_constraints(3, 100)  # Want 3, but min is 5
            5
            >>> selector._apply_constraints(10, 1)  # Want 10, but only 1 available
            1
        """
        # Constraint 1: Don't exceed available symbols (hard constraint)
        limit = min(limit, total_symbols)

        # Constraint 2: Respect minimum (only if we have enough symbols)
        # If total_symbols < min_symbols, we can't enforce the minimum
        if total_symbols >= self.config.min_symbols:
            limit = max(limit, self.config.min_symbols)

        # Constraint 3: Respect maximum
        limit = min(limit, self.config.max_symbols)

        return limit
