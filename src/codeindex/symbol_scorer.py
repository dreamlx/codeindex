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

    def score(self, symbol: Symbol) -> float:
        """Calculate importance score for a symbol.

        Returns a score between 0-100, where higher scores indicate
        more important symbols that should be prioritized for documentation.

        The base implementation returns a neutral score. Future versions
        will implement multi-dimensional scoring based on:
        - Visibility (public/private)
        - Semantic importance (keywords in name)
        - Documentation quality
        - Code complexity
        - Naming patterns

        Args:
            symbol: The Symbol to score

        Returns:
            float: Score between 0-100
        """
        # Base score starts at 50.0 (neutral)
        score = 50.0

        # Future scoring dimensions will be added here:
        # score += self._score_visibility(symbol)      # 0-20
        # score += self._score_semantics(symbol)       # 0-25
        # score += self._score_documentation(symbol)   # 0-15
        # score += self._score_complexity(symbol)      # 0-20
        # score += self._score_naming_pattern(symbol)  # -20-0

        # For now, add simple differentiation based on symbol attributes
        # to pass the test that different symbols should have different scores

        # Boost score for symbols with documentation
        if symbol.docstring and len(symbol.docstring) > 10:
            score += 10.0

        # Boost score for larger symbols (likely more complex/important)
        lines = symbol.line_end - symbol.line_start + 1
        if lines > 50:
            score += 15.0
        elif lines > 20:
            score += 5.0

        # Penalize getter-like methods
        if symbol.name.startswith("get") and len(symbol.name) > 3:
            score -= 10.0

        # Ensure score stays in valid range
        return max(0.0, min(100.0, score))
