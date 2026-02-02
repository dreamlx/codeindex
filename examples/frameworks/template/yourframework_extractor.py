"""YourFramework route extractor template.

Copy this file to src/codeindex/extractors/yourframework.py and customize.

YourFramework routing convention:
- URL pattern: TODO - describe your framework's URL pattern
- Example: TODO - provide example URL → Controller mapping
- Directory structure: TODO - describe where controllers live
"""

from ..framework_detect import RouteInfo
from ..route_extractor import ExtractionContext, RouteExtractor


class YourFrameworkRouteExtractor(RouteExtractor):
    """
    Route extractor for YourFramework.

    YourFramework uses [convention/decorator/explicit]-based routing where:
    - TODO: Describe routing mechanism
    - Controllers are in [directory name]/ directory
    - URL pattern: TODO
    - Only [public/decorated/registered] methods are routes
    - TODO: Any exclusion rules
    """

    @property
    def framework_name(self) -> str:
        """Return framework name."""
        # TODO: Update framework identifier (lowercase, no spaces)
        return "yourframework"

    def can_extract(self, context: ExtractionContext) -> bool:
        """
        Check if routes should be extracted from this directory.

        Routes are extracted only from [target directories].

        Args:
            context: Extraction context

        Returns:
            True if current directory matches extraction criteria
        """
        # TODO: Implement directory detection logic
        # Examples:
        #   return context.current_dir.name == "controllers"
        #   return context.current_dir.name == "views"
        #   return "Controller" in context.current_dir.name
        #   return (context.current_dir / "routes.php").exists()
        return context.current_dir.name == "controllers"

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """
        Extract routes from YourFramework controllers.

        Args:
            context: Extraction context with parse results

        Returns:
            List of RouteInfo objects for each route
        """
        routes = []

        for result in context.parse_results:
            # Skip files with parse errors
            if result.error:
                continue

            # TODO: Find controller class
            # Example logic:
            controller_class = None
            for symbol in result.symbols:
                if symbol.kind == "class" and symbol.name.endswith("Controller"):
                    controller_class = symbol.name
                    break

            if not controller_class:
                continue

            # TODO: Extract controller name for URL building
            # Example: UserController → "user"
            controller_name = controller_class.replace("Controller", "").lower()

            # TODO: Find route methods/actions
            for symbol in result.symbols:
                if symbol.kind != "method":
                    continue

                # TODO: Apply framework-specific filtering
                # Examples:
                #   - Skip private methods
                #   - Skip magic methods
                #   - Check for specific decorators
                #   - Check method visibility
                method_name = symbol.name.split("::")[-1]

                # Skip private/internal methods
                if method_name.startswith("_"):
                    continue

                # TODO: Build route URL based on framework convention
                # Examples:
                #   url = f"/{controller_name}/{method_name}"
                #   url = f"/api/{controller_name}/{method_name}"
                #   url = f"/{module}/{controller_name}/{method_name}"
                url = f"/{controller_name}/{method_name}"

                # Create RouteInfo
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

        # TODO: Optional - customize description extraction
        # Examples:
        #   - Extract only first line
        #   - Remove specific annotations
        #   - Parse structured docstrings

        # Limit length for table display (REQUIRED)
        if len(description) > 60:
            return description[:60] + "..."

        return description


# TODO: After implementation:
# 1. Copy this file to: src/codeindex/extractors/yourframework.py
# 2. Update imports (remove .. if needed)
# 3. Add to src/codeindex/extractors/__init__.py:
#    from .yourframework import YourFrameworkRouteExtractor
#    __all__ = [..., "YourFrameworkRouteExtractor"]
# 4. Run tests: pytest tests/extractors/test_yourframework.py -v
# 5. Test integration: codeindex scan /path/to/your/controllers
