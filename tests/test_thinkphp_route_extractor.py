"""Tests for ThinkPHP route extraction with line numbers (Epic 6, P1, Task 1.2)."""

from pathlib import Path

from codeindex.framework_detect import extract_thinkphp_routes
from codeindex.parser import ParseResult, Symbol


class TestThinkPHPRouteLineNumbers:
    """Test ThinkPHP route extraction includes line numbers."""

    def test_extract_routes_with_line_numbers(self):
        """ThinkPHP routes should include method line numbers."""
        # Arrange: Create parse results with controller methods
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

        # Act: Extract routes
        routes = extract_thinkphp_routes(parse_results, "bigwheel")

        # Assert: Should have 2 routes with line numbers
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
        """Should extract routes from multiple controllers with line numbers."""
        # Arrange
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

        # Act
        routes = extract_thinkphp_routes(parse_results, "admin")

        # Assert
        assert len(routes) == 2

        assert routes[0].url == "/admin/index/index"
        assert routes[0].line_number == 20
        assert routes[0].location == "IndexController.php:20"

        assert routes[1].url == "/admin/user/profile"
        assert routes[1].line_number == 150
        assert routes[1].location == "UserController.php:150"

    def test_extract_routes_only_public_methods(self):
        """Should only extract public methods, not private/protected."""
        # Arrange
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

        # Act
        routes = extract_thinkphp_routes(parse_results, "test")

        # Assert: Only public method should be extracted
        assert len(routes) == 1
        assert routes[0].action == "publicMethod"
        assert routes[0].line_number == 20

    def test_extract_routes_skip_magic_methods(self):
        """Should skip magic methods like __construct, __call, etc."""
        # Arrange
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
                        name="normalMethod",
                        kind="method",
                        signature="public function normalMethod()",
                        line_start=50,
                        line_end=60,
                    ),
                ],
            )
        ]

        # Act
        routes = extract_thinkphp_routes(parse_results, "base")

        # Assert: Only normal method should be extracted
        assert len(routes) == 1
        assert routes[0].action == "normalMethod"
        assert routes[0].line_number == 50

    def test_extract_routes_no_controller_class(self):
        """Should return empty list if no controller class found."""
        # Arrange: Only has regular class, not controller
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

        # Act
        routes = extract_thinkphp_routes(parse_results, "util")

        # Assert: No routes extracted
        assert len(routes) == 0

    def test_extract_routes_with_parse_error(self):
        """Should skip files with parse errors."""
        # Arrange
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

        # Act
        routes = extract_thinkphp_routes(parse_results, "test")

        # Assert: Only valid file should produce routes
        assert len(routes) == 1
        assert routes[0].controller == "ValidController"
        assert routes[0].line_number == 20
