"""Test template for new framework route extractor.

Copy this file to tests/extractors/test_yourframework.py and customize.
"""

from pathlib import Path

from codeindex.extractors.yourframework import YourFrameworkRouteExtractor

from codeindex.parser import ParseResult, Symbol
from codeindex.route_extractor import ExtractionContext


class TestYourFrameworkRouteExtractor:
    """Test YourFramework route extractor."""

    def test_framework_name(self):
        """Should return correct framework name."""
        extractor = YourFrameworkRouteExtractor()
        assert extractor.framework_name == "yourframework"

    def test_can_extract_from_target_directory(self):
        """Should extract only from target directory."""
        extractor = YourFrameworkRouteExtractor()

        # TODO: Update directory name based on your framework
        # Example: "controllers", "views", "handlers", etc.
        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=[],
        )
        assert extractor.can_extract(context) is True

        # Should NOT extract from other directories
        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/models"),
            parse_results=[],
        )
        assert extractor.can_extract(context) is False

    def test_extract_routes_with_line_numbers(self):
        """Should extract routes with line numbers."""
        extractor = YourFrameworkRouteExtractor()

        # TODO: Customize symbol data based on your framework
        parse_results = [
            ParseResult(
                path=Path("UserController.py"),  # or .php, .js, etc.
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring="Get user list",
                        line_start=10,
                        line_end=15,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        # TODO: Update expected values based on your routing convention
        assert len(routes) == 1
        assert routes[0].url == "/users"  # Update expected URL
        assert routes[0].controller == "UserController"
        assert routes[0].action == "index"
        assert routes[0].line_number == 10
        assert routes[0].file_path == "UserController.py"

    def test_extract_description_from_docstring(self):
        """Should extract description from method docstring."""
        extractor = YourFrameworkRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring="Get user list with pagination",
                        line_start=10,
                        line_end=15,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert routes[0].description == "Get user list with pagination"

    def test_truncate_long_descriptions(self):
        """Should truncate descriptions longer than 60 characters."""
        extractor = YourFrameworkRouteExtractor()

        long_desc = (
            "This is a very long description that definitely exceeds "
            "the 60 character limit"
        )

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring=long_desc,
                        line_start=10,
                        line_end=15,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert len(routes[0].description) <= 63  # 60 + "..."
        assert routes[0].description.endswith("...")

    def test_handle_empty_file(self):
        """Should return empty list for files with no routes."""
        extractor = YourFrameworkRouteExtractor()

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=[],
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 0

    def test_skip_private_methods(self):
        """Should skip private methods (starting with _)."""
        extractor = YourFrameworkRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring="Public method",
                        line_start=10,
                        line_end=15,
                    ),
                    Symbol(
                        name="_private",
                        kind="method",
                        signature="def _private(self):",
                        docstring="Private method",
                        line_start=20,
                        line_end=25,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        # Should only extract the public method
        assert len(routes) == 1
        assert routes[0].action == "index"

    def test_extract_multiple_routes_from_one_controller(self):
        """Should extract multiple routes from a single controller."""
        extractor = YourFrameworkRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=100,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring="List users",
                        line_start=10,
                        line_end=15,
                    ),
                    Symbol(
                        name="create",
                        kind="method",
                        signature="def create(self, request):",
                        docstring="Create user",
                        line_start=20,
                        line_end=25,
                    ),
                    Symbol(
                        name="update",
                        kind="method",
                        signature="def update(self, request, id):",
                        docstring="Update user",
                        line_start=30,
                        line_end=35,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 3
        assert [r.action for r in routes] == ["index", "create", "update"]
        assert [r.description for r in routes] == [
            "List users",
            "Create user",
            "Update user",
        ]
