"""Route extractor registry for framework-agnostic route extraction.

This module provides a registry to store and retrieve route extractors
for different frameworks.

Epic 6: Framework-agnostic route extraction
"""

from .route_extractor import RouteExtractor


class RouteExtractorRegistry:
    """
    Registry for route extractors.

    Stores and manages route extractors for different frameworks.
    Each extractor is registered by its framework name.

    Example:
        registry = RouteExtractorRegistry()
        registry.register(ThinkPHPRouteExtractor())
        registry.register(LaravelRouteExtractor())

        extractor = registry.get("thinkphp")
        if extractor:
            routes = extractor.extract_routes(context)
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._extractors: dict[str, RouteExtractor] = {}

    def register(self, extractor: RouteExtractor) -> None:
        """
        Register a route extractor.

        Args:
            extractor: RouteExtractor instance to register

        Note:
            If an extractor with the same framework_name already exists,
            it will be overwritten.
        """
        self._extractors[extractor.framework_name] = extractor

    def get(self, framework: str) -> RouteExtractor | None:
        """
        Get a route extractor by framework name.

        Args:
            framework: Framework name (e.g., "thinkphp", "laravel")

        Returns:
            RouteExtractor instance if found, None otherwise
        """
        return self._extractors.get(framework)

    def has_extractor(self, framework: str) -> bool:
        """
        Check if an extractor is registered for a framework.

        Args:
            framework: Framework name to check

        Returns:
            True if extractor is registered, False otherwise
        """
        return framework in self._extractors

    def list_frameworks(self) -> list[str]:
        """
        List all registered framework names.

        Returns:
            List of framework names (sorted alphabetically)
        """
        return sorted(self._extractors.keys())
