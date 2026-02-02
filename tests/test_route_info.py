"""Tests for RouteInfo data structure (Epic 6, P1: Line Numbers)."""



from codeindex.framework_detect import RouteInfo


class TestRouteInfoLineNumber:
    """Test RouteInfo with line number support."""

    def test_route_info_with_line_number(self):
        """RouteInfo should include line_number field."""
        route = RouteInfo(
            url="/api/users",
            controller="UserController",
            action="index",
            line_number=42,
            file_path="UserController.php",
        )

        assert route.line_number == 42
        assert route.file_path == "UserController.php"

    def test_route_info_with_description(self):
        """RouteInfo should include description field (for P2)."""
        route = RouteInfo(
            url="/api/users",
            controller="UserController",
            action="index",
            description="Get user list",
        )

        assert route.description == "Get user list"

    def test_route_info_location_with_line_number(self):
        """Location property should format as file:line when line_number exists."""
        route = RouteInfo(
            url="/api/users",
            controller="UserController",
            action="index",
            line_number=42,
            file_path="controllers/UserController.php",
        )

        assert route.location == "controllers/UserController.php:42"

    def test_route_info_location_without_line_number(self):
        """Location property should return file path when line_number is 0."""
        route = RouteInfo(
            url="/api/users",
            controller="UserController",
            action="index",
            line_number=0,
            file_path="controllers/UserController.php",
        )

        assert route.location == "controllers/UserController.php"

    def test_route_info_location_no_file_path(self):
        """Location property should return empty string when no file_path."""
        route = RouteInfo(
            url="/api/users",
            controller="UserController",
            action="index",
        )

        assert route.location == ""

    def test_route_info_defaults(self):
        """RouteInfo should have sensible defaults."""
        route = RouteInfo(
            url="/api/users",
            controller="UserController",
            action="index",
        )

        assert route.method_signature == ""
        assert route.line_number == 0
        assert route.file_path == ""
        assert route.description == ""

    def test_route_info_all_fields(self):
        """RouteInfo should support all fields together."""
        route = RouteInfo(
            url="/bigwheel/small/ImmediateLotteryDraw",
            controller="SmallController",
            action="ImmediateLotteryDraw",
            method_signature="public function ImmediateLotteryDraw($info)",
            line_number=1691,
            file_path="Application/BigWheel/Controller/SmallController.php",
            description="幸运抽奖",
        )

        assert route.url == "/bigwheel/small/ImmediateLotteryDraw"
        assert route.controller == "SmallController"
        assert route.action == "ImmediateLotteryDraw"
        assert route.method_signature == "public function ImmediateLotteryDraw($info)"
        assert route.line_number == 1691
        assert route.file_path == "Application/BigWheel/Controller/SmallController.php"
        assert route.description == "幸运抽奖"
        assert (
            route.location == "Application/BigWheel/Controller/SmallController.php:1691"
        )
