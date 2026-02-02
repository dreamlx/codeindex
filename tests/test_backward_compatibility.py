"""Backward compatibility tests for Epic 6 refactoring (Task 2.5).

These tests verify that the new route extractor architecture maintains
100% compatibility with the original ThinkPHP route extraction functionality.
"""

from pathlib import Path

from codeindex.config import IndexingConfig
from codeindex.framework_detect import extract_thinkphp_routes
from codeindex.parser import ParseResult, Symbol
from codeindex.smart_writer import SmartWriter


class TestBackwardCompatibility:
    """Verify new architecture is 100% compatible with old implementation."""

    def test_extract_thinkphp_routes_still_works(self):
        """Old extract_thinkphp_routes function should still work."""
        # This tests that the legacy function in framework_detect.py
        # is not broken by the refactoring
        parse_results = [
            ParseResult(
                path=Path("UserController.php"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController",
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
            )
        ]

        routes = extract_thinkphp_routes(parse_results, "admin")

        assert len(routes) == 1
        assert routes[0].url == "/admin/user/index"
        assert routes[0].line_number == 20

    def test_smart_writer_generates_same_output_structure(self, tmp_path):
        """SmartWriter should generate same README structure as before."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        controller_dir = tmp_path / "Application" / "Admin" / "Controller"
        controller_dir.mkdir(parents=True)

        parse_results = [
            ParseResult(
                path=Path("IndexController.php"),
                symbols=[
                    Symbol(
                        name="IndexController",
                        kind="class",
                        signature="class IndexController",
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
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Should have same sections as before
        assert "## Routes (ThinkPHP)" in content
        assert "| URL |" in content
        assert "| Controller |" in content
        assert "| Action |" in content
        assert "| Location |" in content
        assert "/admin/index/index" in content

    def test_route_table_format_unchanged(self, tmp_path):
        """Route table format should be identical to original."""
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
                        line_start=5,
                        line_end=100,
                    ),
                    Symbol(
                        name="action1",
                        kind="method",
                        signature="public function action1()",
                        line_start=20,
                        line_end=30,
                    ),
                    Symbol(
                        name="action2",
                        kind="method",
                        signature="public function action2()",
                        line_start=40,
                        line_end=50,
                    ),
                ],
            )
        ]

        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Verify exact format
        lines = content.split("\n")
        route_section_found = False
        for i, line in enumerate(lines):
            if "## Routes (ThinkPHP)" in line:
                route_section_found = True
                # Check header format
                assert lines[i + 2].startswith("| URL |")
                assert "| Controller |" in lines[i + 2]
                assert "| Action |" in lines[i + 2]
                assert "| Location |" in lines[i + 2]
                # Check separator
                assert lines[i + 3].startswith("|--")
                break

        assert route_section_found, "Route section not found in output"
