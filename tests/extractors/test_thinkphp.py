"""Tests for ThinkPHP route extractor (Epic 6, Task 2.3)."""

from pathlib import Path

from codeindex.extractors.thinkphp import ThinkPHPRouteExtractor
from codeindex.parser import ParseResult, Symbol
from codeindex.route_extractor import ExtractionContext


class TestThinkPHPRouteExtractor:
    """Test ThinkPHP route extractor with new architecture."""

    def test_framework_name(self):
        """ThinkPHP extractor should return 'thinkphp' as framework name."""
        extractor = ThinkPHPRouteExtractor()

        assert extractor.framework_name == "thinkphp"

    def test_can_extract_in_controller_directory(self):
        """Should extract routes in Controller directories."""
        extractor = ThinkPHPRouteExtractor()
        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Admin/Controller"),
            parse_results=[],
        )

        assert extractor.can_extract(context) is True

    def test_can_extract_in_non_controller_directory(self):
        """Should not extract routes in non-Controller directories."""
        extractor = ThinkPHPRouteExtractor()

        # Model directory
        context_model = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Admin/Model"),
            parse_results=[],
        )
        assert extractor.can_extract(context_model) is False

        # View directory
        context_view = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Admin/View"),
            parse_results=[],
        )
        assert extractor.can_extract(context_view) is False

        # Root directory
        context_root = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project"),
            parse_results=[],
        )
        assert extractor.can_extract(context_root) is False

    def test_extract_routes_with_line_numbers(self):
        """Should extract routes with line numbers from controllers."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("SmallController.php"),
                symbols=[
                    Symbol(
                        name="SmallController",
                        kind="class",
                        signature="class SmallController",
                        line_start=10,
                        line_end=2000,
                    ),
                    Symbol(
                        name="ImmediateLotteryDraw",
                        kind="method",
                        signature="public function ImmediateLotteryDraw($info)",
                        line_start=1691,
                        line_end=1720,
                    ),
                    Symbol(
                        name="activityList",
                        kind="method",
                        signature="public function activityList()",
                        line_start=234,
                        line_end=260,
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

        assert len(routes) == 2

        # Check first route
        route1 = routes[0]
        assert route1.url == "/bigwheel/small/ImmediateLotteryDraw"
        assert route1.controller == "SmallController"
        assert route1.action == "ImmediateLotteryDraw"
        assert route1.line_number == 1691
        assert route1.file_path == "SmallController.php"
        assert route1.location == "SmallController.php:1691"

        # Check second route
        route2 = routes[1]
        assert route2.url == "/bigwheel/small/activityList"
        assert route2.line_number == 234
        assert route2.location == "SmallController.php:234"

    def test_extract_routes_multiple_controllers(self):
        """Should extract routes from multiple controllers."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("IndexController.php"),
                symbols=[
                    Symbol(
                        name="IndexController",
                        kind="class",
                        signature="class IndexController",
                        line_start=5,
                        line_end=500,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="public function index()",
                        line_start=20,
                        line_end=40,
                    ),
                ],
            ),
            ParseResult(
                path=Path("UserController.php"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController",
                        line_start=5,
                        line_end=300,
                    ),
                    Symbol(
                        name="profile",
                        kind="method",
                        signature="public function profile()",
                        line_start=150,
                        line_end=180,
                    ),
                ],
            ),
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Admin/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 2
        assert routes[0].url == "/admin/index/index"
        assert routes[0].line_number == 20
        assert routes[1].url == "/admin/user/profile"
        assert routes[1].line_number == 150

    def test_extract_routes_only_public_methods(self):
        """Should only extract public methods, not private/protected."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("TestController.php"),
                symbols=[
                    Symbol(
                        name="TestController",
                        kind="class",
                        signature="class TestController",
                        line_start=5,
                        line_end=200,
                    ),
                    Symbol(
                        name="publicMethod",
                        kind="method",
                        signature="public function publicMethod()",
                        line_start=20,
                        line_end=30,
                    ),
                    Symbol(
                        name="privateMethod",
                        kind="method",
                        signature="private function privateMethod()",
                        line_start=40,
                        line_end=50,
                    ),
                    Symbol(
                        name="protectedMethod",
                        kind="method",
                        signature="protected function protectedMethod()",
                        line_start=60,
                        line_end=70,
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
        assert routes[0].action == "publicMethod"
        assert routes[0].line_number == 20

    def test_extract_routes_skip_magic_methods(self):
        """Should skip magic methods like __construct, __call."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("BaseController.php"),
                symbols=[
                    Symbol(
                        name="BaseController",
                        kind="class",
                        signature="class BaseController",
                        line_start=5,
                        line_end=200,
                    ),
                    Symbol(
                        name="__construct",
                        kind="method",
                        signature="public function __construct()",
                        line_start=10,
                        line_end=20,
                    ),
                    Symbol(
                        name="__call",
                        kind="method",
                        signature="public function __call($method, $params)",
                        line_start=30,
                        line_end=40,
                    ),
                    Symbol(
                        name="_initialize",
                        kind="method",
                        signature="public function _initialize()",
                        line_start=45,
                        line_end=55,
                    ),
                    Symbol(
                        name="normalMethod",
                        kind="method",
                        signature="public function normalMethod()",
                        line_start=60,
                        line_end=70,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Base/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        # Should only extract normalMethod, not __construct, __call, or _initialize
        assert len(routes) == 1
        assert routes[0].action == "normalMethod"

    def test_extract_routes_no_controller_class(self):
        """Should return empty list if no controller class found."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("Helper.php"),
                symbols=[
                    Symbol(
                        name="Helper",
                        kind="class",
                        signature="class Helper",
                        line_start=5,
                        line_end=100,
                    ),
                    Symbol(
                        name="format",
                        kind="method",
                        signature="public function format()",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Util/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 0

    def test_extract_routes_with_parse_error(self):
        """Should skip files with parse errors."""
        extractor = ThinkPHPRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("ErrorController.php"),
                symbols=[],
                error="Syntax error",
            ),
            ParseResult(
                path=Path("ValidController.php"),
                symbols=[
                    Symbol(
                        name="ValidController",
                        kind="class",
                        signature="class ValidController",
                        line_start=5,
                        line_end=100,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="public function index()",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            ),
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/Application/Test/Controller"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        # Should only extract from valid file
        assert len(routes) == 1
        assert routes[0].controller == "ValidController"
