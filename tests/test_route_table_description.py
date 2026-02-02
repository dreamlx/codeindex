"""Tests for route table Description column (Epic 6, P2, Task 3.4)."""

from pathlib import Path

from codeindex.config import IndexingConfig
from codeindex.parser import ParseResult, Symbol
from codeindex.smart_writer import SmartWriter


class TestRouteTableDescription:
    """Test route table displays Description column."""

    def test_route_table_has_description_column(self, tmp_path):
        """Route table should have Description column header."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "Admin" / "Controller"
        controller_dir.mkdir(parents=True)

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
                        line_end=100,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="public function index()",
                        docstring="Get user list",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Should have Description column in header
        assert "| Description |" in content

    def test_route_table_displays_method_description(self, tmp_path):
        """Route table should display method description in rows."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "Admin" / "Controller"
        controller_dir.mkdir(parents=True)

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
                        line_end=100,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="public function index()",
                        docstring="Get user list",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Should display description in route row
        assert "Get user list" in content

    def test_route_table_displays_empty_description(self, tmp_path):
        """Route table should handle methods without descriptions."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "Test" / "Controller"
        controller_dir.mkdir(parents=True)

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
                        docstring="",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Should have Description column even with empty description
        assert "| Description |" in content

    def test_route_table_displays_chinese_description(self, tmp_path):
        """Route table should display Chinese descriptions correctly."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "BigWheel" / "Controller"
        controller_dir.mkdir(parents=True)

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
                        docstring="幸运抽奖",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Should display Chinese description
        assert "幸运抽奖" in content

    def test_route_table_displays_multiple_descriptions(self, tmp_path):
        """Route table should display descriptions for multiple routes."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "Admin" / "Controller"
        controller_dir.mkdir(parents=True)

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

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Should display all descriptions
        assert "Get user list" in content
        assert "Get user profile" in content
        assert "Save user data" in content

    def test_route_table_description_column_alignment(self, tmp_path):
        """Route table should have proper Description column alignment."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "Test" / "Controller"
        controller_dir.mkdir(parents=True)

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
                        name="test",
                        kind="method",
                        signature="public function test()",
                        docstring="Test method",
                        line_start=20,
                        line_end=30,
                    ),
                ],
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Verify table structure
        lines = content.split("\n")
        route_section_found = False
        for i, line in enumerate(lines):
            if "## Routes (ThinkPHP)" in line:
                route_section_found = True
                # Check header has Description column
                header = lines[i + 2]
                assert "| URL |" in header
                assert "| Controller |" in header
                assert "| Action |" in header
                assert "| Location |" in header
                assert "| Description |" in header
                # Check separator
                assert lines[i + 3].startswith("|--")
                break

        assert route_section_found, "Route section not found in output"
