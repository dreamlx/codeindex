"""Tests for ThinkPHP route extractor description extraction (Epic 6, P2, Task 3.3)."""

from pathlib import Path

from codeindex.extractors.thinkphp import ThinkPHPRouteExtractor
from codeindex.parser import ParseResult, Symbol
from codeindex.route_extractor import ExtractionContext


class TestThinkPHPDescriptionExtraction:
    """Test ThinkPHP route extractor extracts descriptions from docstrings."""

    def test_extract_description_from_method_docstring(self):
        """Should extract description from method docstring."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("SmallController.php"),
                symbols=[
                    Symbol(
                        name="SmallController",
                        kind="class",
                        signature="class SmallController",
                        docstring="",
                        line_start=10,
                        line_end=100,
                    ),
                    Symbol(
                        name="ImmediateLotteryDraw",
                        kind="method",
                        signature="public function ImmediateLotteryDraw($info)",
                        docstring="幸运抽奖",  # Parser extracts this from PHPDoc
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/BigWheel/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert routes[0].description == "幸运抽奖"

    def test_extract_description_truncates_long_text(self):
        """Should truncate description to 60 characters."""
        extractor = ThinkPHPRouteExtractor()

        long_description = (
            "This is a very long description that exceeds "
            "sixty characters and should be truncated"
        )

        parse_results = [
            ParseResult(
                path=Path("TestController.php"),
                symbols=[
                    Symbol(
                        name="TestController",
                        kind="class",
                        signature="class TestController",
                        docstring="",
                        line_start=5,
                        line_end=100,
                    ),
                    Symbol(
                        name="longMethod",
                        kind="method",
                        signature="public function longMethod()",
                        docstring=long_description,
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Test/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert len(routes[0].description) <= 63  # 60 + "..."
        assert routes[0].description.endswith("...")

    def test_extract_description_empty_for_no_docstring(self):
        """Should have empty description when method has no docstring."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("TestController.php"),
                symbols=[
                    Symbol(
                        name="TestController",
                        kind="class",
                        signature="class TestController",
                        docstring="",
                        line_start=5,
                        line_end=100,
                    ),
                    Symbol(
                        name="undocumented",
                        kind="method",
                        signature="public function undocumented()",
                        docstring="",  # No docstring
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Test/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert routes[0].description == ""

    def test_extract_description_from_multiple_methods(self):
        """Should extract descriptions from multiple methods."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("UserController.php"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController",
                        docstring="",
                        line_start=5,
                        line_end=200,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="public function index()",
                        docstring="Get user list",
                        line_start=20,
                        line_end=40,
                    ),
                    Symbol(
                        name="profile",
                        kind="method",
                        signature="public function profile()",
                        docstring="Get user profile",
                        line_start=50,
                        line_end=70,
                    ),
                    Symbol(
                        name="save",
                        kind="method",
                        signature="public function save()",
                        docstring="Save user data",
                        line_start=80,
                        line_end=100,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Admin/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 3
        assert routes[0].description == "Get user list"
        assert routes[1].description == "Get user profile"
        assert routes[2].description == "Save user data"
