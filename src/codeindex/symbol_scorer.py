"""Symbol importance scoring system.

This module provides functionality to score symbols based on their importance,
helping to prioritize which symbols should be included in README_AI.md files.
"""

from dataclasses import dataclass
from typing import Optional

from codeindex.parser import Symbol


@dataclass
class ScoringContext:
    """Scoring context for symbols.

    Attributes:
        framework: The framework being used (e.g., 'thinkphp', 'django')
        file_type: The type of file (e.g., 'controller', 'model', 'service')
        total_symbols: Total number of symbols in the file
    """

    framework: str = "unknown"
    file_type: str = "unknown"
    total_symbols: int = 0


class SymbolImportanceScorer:
    """Score symbols by importance for inclusion in documentation.

    This scorer evaluates symbols across multiple dimensions to determine
    their importance for documentation purposes. Higher scores indicate
    more important symbols that should be prioritized for inclusion.

    Attributes:
        context: Optional ScoringContext providing additional information
                about the codebase being scored
    """

    # Critical keywords indicating core business functionality
    CRITICAL_KEYWORDS = [
        "create",
        "update",
        "delete",
        "remove",
        "save",
        "insert",
        "process",
        "handle",
        "execute",
        "run",
        "pay",
        "notify",
        "callback",
        "validate",
        "sign",
        "auth",
        "login",
        "logout",
        "register",
    ]

    # Secondary keywords for query/retrieval operations
    SECONDARY_KEYWORDS = [
        "find",
        "search",
        "query",
        "list",
        "show",
        "display",
        "fetch",
        "load",
    ]

    def __init__(self, context: Optional[ScoringContext] = None):
        """Initialize the scorer with optional context.

        Args:
            context: Optional ScoringContext. If not provided, uses defaults.
        """
        self.context = context or ScoringContext()

    def _score_visibility(self, symbol: Symbol) -> float:
        """Score symbol based on its visibility.

        Public APIs should be prioritized over private implementation details.

        Scoring:
        - PHP public: 20 points (main API surface)
        - PHP protected: 10 points (inheritance API)
        - PHP private: 0 points (internal implementation)
        - Python public (no _): 15 points
        - Python private (_ or __): 5 points

        Args:
            symbol: The Symbol to score

        Returns:
            float: Visibility score (0-20)
        """
        sig_lower = symbol.signature.lower()

        # PHP visibility keywords
        if "public" in sig_lower:
            return 20.0
        elif "protected" in sig_lower:
            return 10.0
        elif "private" in sig_lower:
            return 0.0
        else:
            # Python naming conventions
            # Private/magic methods start with underscore
            if symbol.name.startswith("_"):
                return 5.0
            else:
                return 15.0

    def _score_semantics(self, symbol: Symbol) -> float:
        """Score symbol based on semantic importance of its name.

        Core business operations (pay, create, update, delete) should be
        prioritized over generic helpers or accessor methods.

        Scoring:
        - Critical keywords (pay, create, update, etc.): 25 points
        - Secondary keywords (find, search, list): 15 points
        - Generic names: 5 points

        Matching is case-insensitive.

        Args:
            symbol: The Symbol to score

        Returns:
            float: Semantic importance score (5-25)
        """
        name_lower = symbol.name.lower()

        # Check for critical keywords
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in name_lower:
                return 25.0

        # Check for secondary keywords
        for keyword in self.SECONDARY_KEYWORDS:
            if keyword in name_lower:
                return 15.0

        # Generic method
        return 5.0

    def _score_documentation(self, symbol: Symbol) -> float:
        """Score symbol based on documentation quality.

        Well-documented code is more important for understanding and
        should be prioritized in documentation.

        Scoring:
        - Comprehensive docs (>200 chars): 15 points
        - Medium docs (>50 chars): 10 points
        - Brief docs (any): 5 points
        - No docs: 0 points

        Args:
            symbol: The Symbol to score

        Returns:
            float: Documentation quality score (0-15)
        """
        if not symbol.docstring:
            return 0.0

        doc_length = len(symbol.docstring.strip())

        if doc_length > 200:
            return 15.0
        elif doc_length > 50:
            return 10.0
        elif doc_length > 0:
            return 5.0
        else:
            return 0.0

    def _score_complexity(self, symbol: Symbol) -> float:
        """Score symbol based on code complexity (measured by line count).

        Larger, more complex symbols often contain critical business logic
        and should be prioritized for documentation.

        Scoring:
        - Very large (>100 lines): 20 points
        - Large (50-100 lines): 15 points
        - Medium (20-50 lines): 10 points
        - Small (<20 lines): 5 points

        Args:
            symbol: The Symbol to score

        Returns:
            float: Complexity score (5-20)
        """
        lines = symbol.line_end - symbol.line_start + 1

        if lines > 100:
            return 20.0
        elif lines >= 50:
            return 15.0
        elif lines >= 20:
            return 10.0
        else:
            return 5.0

    def _score_naming_pattern(self, symbol: Symbol) -> float:
        """Score symbol based on naming patterns (noise detection).

        Penalize common noise patterns like getters, setters, and
        internal/magic methods that clutter documentation.

        Scoring (penalties):
        - Magic methods (__*): -20 points
        - Private methods (_*): -15 points
        - Getter/setter/checker methods (get*/set*/is*/has*): -10 points
        - Normal methods: 0 points

        Args:
            symbol: The Symbol to score

        Returns:
            float: Naming pattern score (-20 to 0)
        """
        name = symbol.name

        # Check for magic methods (highest penalty)
        if name.startswith("__"):
            return -20.0

        # Check for private methods (high penalty)
        if name.startswith("_"):
            return -15.0

        # Check for getter/setter/checker patterns (moderate penalty)
        # Java: getters/setters are standard JavaBeans convention, not noise
        file_type = getattr(self.context, "file_type", "unknown")
        if file_type != "java":
            name_lower = name.lower()
            noise_prefixes = ["get", "set", "is", "has"]
            for prefix in noise_prefixes:
                if name_lower.startswith(prefix):
                    return -10.0

        # Normal method name
        return 0.0

    def score(self, symbol: Symbol) -> float:
        """Calculate importance score for a symbol.

        Returns a score between 0-100, where higher scores indicate
        more important symbols that should be prioritized for documentation.

        Multi-dimensional scoring based on:
        - Visibility (public/private): 0-20 points
        - Semantic importance (keywords): 5-25 points
        - Documentation quality: 0-15 points
        - Code complexity: 5-20 points
        - Naming patterns (noise detection): -20-0 points

        Theoretical range: -10 to 100 (clamped to 0-100)

        Args:
            symbol: The Symbol to score

        Returns:
            float: Score between 0-100
        """
        # Start with neutral base
        score = 0.0

        # Add all scoring dimensions
        score += self._score_visibility(symbol)  # 0-20
        score += self._score_semantics(symbol)  # 5-25
        score += self._score_documentation(symbol)  # 0-15
        score += self._score_complexity(symbol)  # 5-20
        score += self._score_naming_pattern(symbol)  # -20-0

        # Ensure score stays in valid range [0, 100]
        return max(0.0, min(100.0, score))
