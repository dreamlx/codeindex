"""Framework-specific route extractors.

This package contains route extractors for different frameworks.
Each extractor implements the RouteExtractor interface.
"""

from .thinkphp import ThinkPHPRouteExtractor

__all__ = ["ThinkPHPRouteExtractor"]
