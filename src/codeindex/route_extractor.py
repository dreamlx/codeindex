"""Route extraction framework for multi-framework support.

This module provides the abstract base class for route extractors and
the extraction context data structure.

Epic 6: Framework-agnostic route extraction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .framework_detect import RouteInfo
from .parser import ParseResult


@dataclass
class ExtractionContext:
    """
    Context for route extraction.

    Provides all necessary information for a route extractor to analyze
    and extract routes from code.
    """

    root_path: Path
    """Project root directory"""

    current_dir: Path
    """Current directory being analyzed"""

    parse_results: list[ParseResult]
    """Parsed code symbols from the current directory"""

    framework_version: str = ""
    """Framework version (optional, for version-specific extraction)"""


class RouteExtractor(ABC):
    """
    Abstract base class for framework-specific route extractors.

    Each framework (ThinkPHP, Laravel, Django, FastAPI, etc.) should
    implement this interface to provide route extraction capabilities.

    Example:
        class ThinkPHPRouteExtractor(RouteExtractor):
            @property
            def framework_name(self) -> str:
                return "thinkphp"

            def can_extract(self, context: ExtractionContext) -> bool:
                return context.current_dir.name == "Controller"

            def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
                # Implementation here
                return routes
    """

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """
        Return the framework name (e.g., "thinkphp", "laravel", "django").

        Returns:
            Framework identifier in lowercase
        """
        pass

    @abstractmethod
    def can_extract(self, context: ExtractionContext) -> bool:
        """
        Check if this extractor can extract routes from the given context.

        This method is called to determine if the current directory is
        relevant for this framework's route extraction.

        Args:
            context: Extraction context with directory and parse results

        Returns:
            True if this extractor should process this context
        """
        pass

    @abstractmethod
    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """
        Extract route information from the given context.

        Args:
            context: Extraction context with directory and parse results

        Returns:
            List of RouteInfo objects representing discovered routes
        """
        pass
