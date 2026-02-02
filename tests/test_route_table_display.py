"""Tests for route table display with line numbers (Epic 6, P1, Task 1.3)."""


from codeindex.config import IndexingConfig
from codeindex.framework_detect import RouteInfo
from codeindex.smart_writer import SmartWriter


class TestRouteTableDisplay:
    """Test route table formatting with Location column."""

    def test_route_table_includes_location_column(self, tmp_path):
        """Route table should include Location column header."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        routes = [
            RouteInfo(
                url="/admin/user/index",
                controller="UserController",
                action="index",
                line_number=42,
                file_path="UserController.php",
            )
        ]

        # Act
        lines = writer._format_route_table(routes, "thinkphp")

        # Assert: Should have Location column
        header_line = next(line for line in lines if "| URL |" in line)
        assert "| Location |" in header_line

    def test_route_table_displays_file_and_line(self, tmp_path):
        """Route table should display file:line format."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        routes = [
            RouteInfo(
                url="/bigwheel/small/ImmediateLotteryDraw",
                controller="SmallController",
                action="ImmediateLotteryDraw",
                method_signature="public function ImmediateLotteryDraw($info)",
                line_number=1691,
                file_path="Application/BigWheel/Controller/SmallController.php",
            )
        ]

        # Act
        lines = writer._format_route_table(routes, "thinkphp")

        # Assert: Should display location with line number
        route_line = next(
            line
            for line in lines
            if "ImmediateLotteryDraw" in line and "|" in line
        )
        assert "SmallController.php:1691" in route_line

    def test_route_table_displays_multiple_routes_with_locations(self, tmp_path):
        """Route table should display all routes with their locations."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        routes = [
            RouteInfo(
                url="/admin/user/index",
                controller="UserController",
                action="index",
                line_number=42,
                file_path="UserController.php",
            ),
            RouteInfo(
                url="/admin/user/profile",
                controller="UserController",
                action="profile",
                line_number=150,
                file_path="UserController.php",
            ),
            RouteInfo(
                url="/admin/order/list",
                controller="OrderController",
                action="list",
                line_number=78,
                file_path="OrderController.php",
            ),
        ]

        # Act
        lines = writer._format_route_table(routes, "thinkphp")
        content = "\n".join(lines)

        # Assert: All locations should be displayed
        assert "UserController.php:42" in content
        assert "UserController.php:150" in content
        assert "OrderController.php:78" in content

    def test_route_table_handles_route_without_line_number(self, tmp_path):
        """Route table should handle routes without line numbers gracefully."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        routes = [
            RouteInfo(
                url="/admin/user/index",
                controller="UserController",
                action="index",
                line_number=0,  # No line number
                file_path="UserController.php",
            )
        ]

        # Act
        lines = writer._format_route_table(routes, "thinkphp")
        content = "\n".join(lines)

        # Assert: Should show file path only
        assert "UserController.php" in content
        # Should NOT have :0
        assert ":0" not in content

    def test_route_table_markdown_format(self, tmp_path):
        """Route table should be valid Markdown."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        routes = [
            RouteInfo(
                url="/admin/user/index",
                controller="UserController",
                action="index",
                line_number=42,
                file_path="UserController.php",
            )
        ]

        # Act
        lines = writer._format_route_table(routes, "thinkphp")

        # Assert: Valid Markdown table structure
        assert lines[0] == "## Routes (ThinkPHP)"
        assert lines[1] == ""
        # Header row
        assert lines[2].startswith("|") and lines[2].endswith("|")
        # Separator row
        assert "---" in lines[3]
        # Data row
        assert lines[4].startswith("|") and lines[4].endswith("|")

    def test_route_table_limits_routes(self, tmp_path):
        """Route table should limit display to 30 routes."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        # Create 50 routes
        routes = [
            RouteInfo(
                url=f"/admin/test/action{i}",
                controller="TestController",
                action=f"action{i}",
                line_number=i * 10,
                file_path="TestController.php",
            )
            for i in range(50)
        ]

        # Act
        lines = writer._format_route_table(routes, "thinkphp")

        # Assert: Should have approximately 30 routes + header + footer
        # Header: 4 lines (title, blank, header, separator)
        # Routes: 30 lines
        # More indicator: 1 line
        # Blank: 1 line
        assert len(lines) <= 40  # Rough check

        content = "\n".join(lines)
        assert "... |" in content or "more" in content.lower()
