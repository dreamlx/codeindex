"""Spring Framework route extractor.

Extracts REST routes from Spring controllers using annotations.

Spring routing via annotations:
- Controller: @RestController, @Controller
- Class-level prefix: @RequestMapping("/api/users")
- Method mappings: @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
- Example: GET /api/users/{id} -> UserController.getUser()

Epic 7, Story 7.2: Spring Framework route extraction
"""

from ..framework_detect import RouteInfo
from ..parser import ParseResult


class SpringRouteExtractor:
    """
    Route extractor for Spring Framework.

    Extracts REST API routes from Spring controllers by analyzing:
    - @RestController and @Controller annotations
    - @RequestMapping at class level (path prefix)
    - @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
    - Path variables (e.g., {id})
    """

    def extract_routes(self, result: ParseResult) -> list[RouteInfo]:
        """
        Extract route information from Spring controllers.

        Args:
            result: Parsed Java file (ParseResult)

        Returns:
            List of RouteInfo objects representing discovered routes
        """
        if result.error:
            return []

        routes = []

        # Find controller class (must have @RestController or @Controller)
        controller_class = None
        controller_prefix = ""

        for symbol in result.symbols:
            if symbol.kind != "class":
                continue

            # Check if class has controller annotation
            has_controller = any(
                a.name in ("RestController", "Controller")
                for a in symbol.annotations
            )

            if not has_controller:
                continue

            controller_class = symbol.name

            # Get controller-level @RequestMapping prefix
            for annotation in symbol.annotations:
                if annotation.name == "RequestMapping":
                    # Extract path from @RequestMapping("/api/users")
                    controller_prefix = self._extract_path_from_annotation(annotation.arguments)
                    break

            break

        if not controller_class:
            return []

        # Extract routes from mapped methods
        for symbol in result.symbols:
            if symbol.kind != "method":
                continue

            # Check if method belongs to controller
            if not symbol.name.startswith(controller_class + "."):
                continue

            # Find mapping annotation
            http_method = None
            method_path = ""

            for annotation in symbol.annotations:
                mapping_info = self._get_mapping_info(annotation.name)
                if mapping_info:
                    http_method, default_path = mapping_info
                    # Extract path from annotation arguments
                    method_path = self._extract_path_from_annotation(annotation.arguments)
                    if not method_path and default_path:
                        method_path = default_path
                    break

            if not http_method:
                continue

            # Build full path
            full_path = self._build_path(controller_prefix, method_path)

            # Build URL with HTTP method
            url = f"{http_method} {full_path}"

            # Extract method name
            method_name = symbol.name.split(".")[-1]

            routes.append(
                RouteInfo(
                    url=url,
                    controller=controller_class,
                    action=method_name,
                    method_signature=symbol.signature,
                    line_number=symbol.line_start,
                    description=symbol.docstring,
                )
            )

        return routes

    def _get_mapping_info(self, annotation_name: str) -> tuple[str, str] | None:
        """
        Get HTTP method and default path for mapping annotation.

        Args:
            annotation_name: Annotation name (e.g., "GetMapping")

        Returns:
            Tuple of (HTTP_METHOD, default_path) or None if not a mapping annotation
        """
        mappings = {
            "GetMapping": ("GET", ""),
            "PostMapping": ("POST", ""),
            "PutMapping": ("PUT", ""),
            "DeleteMapping": ("DELETE", ""),
            "PatchMapping": ("PATCH", ""),
            "RequestMapping": ("REQUEST", ""),  # Default, can be overridden
        }
        return mappings.get(annotation_name)

    def _extract_path_from_annotation(self, arguments: dict | str) -> str:
        """
        Extract path from annotation arguments.

        Args:
            arguments: Annotation arguments (dict or string)

        Returns:
            Extracted path or empty string
        """
        if not arguments:
            return ""

        # Handle dict format (from parser)
        if isinstance(arguments, dict):
            # Try common path keys
            for key in ("value", "path"):
                if key in arguments:
                    value = arguments[key]
                    if isinstance(value, str):
                        return value
                    if isinstance(value, list) and value:
                        # Array of paths, take first
                        return value[0] if isinstance(value[0], str) else ""
            return ""

        # Handle string format (legacy)
        args = arguments.strip()
        if args.startswith("(") and args.endswith(")"):
            args = args[1:-1].strip()

        # Handle value = "/path" or just "/path"
        if "value" in args or "path" in args:
            # Extract quoted string after value= or path=
            import re
            match = re.search(r'(?:value|path)\s*=\s*"([^"]+)"', args)
            if match:
                return match.group(1)

        # Handle simple case: just a quoted string
        if args.startswith('"') and args.endswith('"'):
            return args[1:-1]

        # Handle array: {"/path1", "/path2"} - take first
        if args.startswith("{"):
            import re
            match = re.search(r'"([^"]+)"', args)
            if match:
                return match.group(1)

        return ""

    def _build_path(self, prefix: str, path: str) -> str:
        """
        Build full path from controller prefix and method path.

        Args:
            prefix: Controller-level prefix
            path: Method-level path

        Returns:
            Full path with proper slashes
        """
        # Normalize paths
        prefix = prefix.rstrip("/") if prefix else ""
        path = path if path.startswith("/") else f"/{path}" if path else ""

        # Combine
        if not prefix and not path:
            return "/"
        if not prefix:
            return path
        if not path:
            return prefix

        return f"{prefix}{path}"
