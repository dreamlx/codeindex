"""ThinkPHP route extractor.

Extracts routes from ThinkPHP framework controllers using convention-based routing.

ThinkPHP routing convention:
- URL: /module/controller/action
- Example: /admin/index/home -> Admin\\Controller\\IndexController::home()

Epic 6: Framework-agnostic route extraction
"""

from ..framework_detect import RouteInfo
from ..route_extractor import ExtractionContext, RouteExtractor


class ThinkPHPRouteExtractor(RouteExtractor):
    """
    Route extractor for ThinkPHP framework.

    ThinkPHP uses convention-based routing where:
    - Controllers are in Application/{Module}/Controller/ directories
    - URL pattern: /{module}/{controller}/{action}
    - Only public methods are routes
    - Magic methods (__construct, __call, etc.) are excluded
    - Internal methods (starting with _) are excluded
    """

    @property
    def framework_name(self) -> str:
        """Return framework name."""
        return "thinkphp"

    def can_extract(self, context: ExtractionContext) -> bool:
        """
        Check if routes should be extracted from this directory.

        Routes are extracted only from Controller directories.

        Args:
            context: Extraction context

        Returns:
            True if current directory is a Controller directory
        """
        return context.current_dir.name == "Controller"

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """
        Extract routes from ThinkPHP controllers.

        Args:
            context: Extraction context with parse results

        Returns:
            List of RouteInfo objects for each public method in controllers
        """
        routes = []

        # Get module name from directory structure
        # e.g., /Application/Admin/Controller -> module = "Admin"
        module_name = context.current_dir.parent.name

        for result in context.parse_results:
            if result.error:
                continue

            # Find controller class
            controller_class = None
            for symbol in result.symbols:
                if symbol.kind == "class" and symbol.name.endswith("Controller"):
                    controller_class = symbol.name
                    break

            if not controller_class:
                continue

            # Extract controller name (remove "Controller" suffix)
            controller_name = controller_class.replace("Controller", "").lower()

            # Find public methods (actions)
            for symbol in result.symbols:
                if symbol.kind != "method":
                    continue

                # Only public methods are routes
                if "public" not in symbol.signature.lower():
                    continue

                # Skip magic methods and internal methods
                method_name = symbol.name.split("::")[-1]
                if method_name.startswith("_") or method_name.startswith("__"):
                    continue

                # Build route URL: /module/controller/action
                url = f"/{module_name.lower()}/{controller_name}/{method_name}"

                routes.append(
                    RouteInfo(
                        url=url,
                        controller=controller_class,
                        action=method_name,
                        method_signature=symbol.signature,
                        line_number=symbol.line_start,
                        file_path=result.path.name,
                        description=self._extract_description(symbol),
                    )
                )

        return routes

    def _extract_description(self, symbol) -> str:
        """
        Extract description from symbol docstring.

        Limits description to 60 characters for table display.

        Args:
            symbol: Symbol with docstring

        Returns:
            Cleaned description (max 60 chars + "...")
        """
        if not symbol.docstring:
            return ""

        description = symbol.docstring.strip()

        # Limit length for table display
        if len(description) > 60:
            return description[:60] + "..."

        return description
