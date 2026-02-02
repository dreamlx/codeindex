"""Integration tests for SmartWriter with route extractors (Epic 6, Task 2.4)."""

from pathlib import Path

from codeindex.config import IndexingConfig
from codeindex.extractors.thinkphp import ThinkPHPRouteExtractor
from codeindex.parser import ParseResult, Symbol
from codeindex.route_registry import RouteExtractorRegistry
from codeindex.smart_writer import SmartWriter


class TestSmartWriterRouteIntegration:
    """Test SmartWriter integration with route extractors."""

    def test_smart_writer_uses_registry(self):
        """SmartWriter should use route registry for route extraction."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        # Verify writer has a route registry
        assert hasattr(writer, "route_registry")
        assert isinstance(writer.route_registry, RouteExtractorRegistry)

    def test_smart_writer_has_thinkphp_extractor_registered(self):
        """SmartWriter should have ThinkPHP extractor registered by default."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        # Verify ThinkPHP extractor is registered
        extractor = writer.route_registry.get("thinkphp")
        assert extractor is not None
        assert isinstance(extractor, ThinkPHPRouteExtractor)

    def test_generate_detailed_readme_with_routes_via_registry(self, tmp_path):
        """Should generate route table using registry and extractors."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        # Create test directory structure (Controller directory for ThinkPHP)
        controller_dir = tmp_path / "Application" / "Admin" / "Controller"
        controller_dir.mkdir(parents=True)

        # Create parse results with controller
        parse_results = [
            ParseResult(
                path=Path("UserController.php"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController",
                        line_start=5,
                        line_end=200,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="public function index()",
                        line_start=20,
                        line_end=40,
                    ),
                    Symbol(
                        name="profile",
                        kind="method",
                        signature="public function profile()",
                        line_start=50,
                        line_end=70,
                    ),
                ],
            )
        ]

        # Act
        content = writer._generate_detailed(
            dir_path=controller_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Assert: Route table should be generated
        assert "## Routes (ThinkPHP)" in content
        assert "/admin/user/index" in content
        assert "/admin/user/profile" in content
        assert "UserController.php:20" in content
        assert "UserController.php:50" in content

    def test_generate_detailed_readme_without_routes_for_non_controller_dir(
        self, tmp_path
    ):
        """Should not generate route table for non-Controller directories."""
        # Arrange
        config = IndexingConfig()
        writer = SmartWriter(config)

        # Model directory (not Controller)
        model_dir = tmp_path / "Application" / "Admin" / "Model"
        model_dir.mkdir(parents=True)

        # Create parse results
        parse_results = [
            ParseResult(
                path=Path("UserModel.php"),
                symbols=[
                    Symbol(
                        name="UserModel",
                        kind="class",
                        signature="class UserModel",
                        line_start=5,
                        line_end=100,
                    ),
                ],
            )
        ]

        # Act
        content = writer._generate_detailed(
            dir_path=model_dir,
            parse_results=parse_results,
            child_dirs=[],
        )

        # Assert: No route table
        assert "## Routes" not in content

    def test_registry_supports_multiple_frameworks(self):
        """Registry should support multiple framework extractors."""
        config = IndexingConfig()
        writer = SmartWriter(config)

        # Verify multiple frameworks can be registered
        frameworks = writer.route_registry.list_frameworks()
        assert "thinkphp" in frameworks
        # Future: assert "laravel" in frameworks
        # Future: assert "fastapi" in frameworks
