"""
Tests for SmartWriter semantic extraction integration (TDD: RED phase)

Story 4.4: Business Semantic Extraction
Task 4.4.2: Integrate SemanticExtractor into SmartWriter
"""


import pytest

from codeindex.config import IndexingConfig, SemanticConfig
from codeindex.parser import ParseResult, Symbol
from codeindex.smart_writer import SmartWriter


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory structure for testing"""
    # Create directory structure
    admin_dir = tmp_path / "Application" / "Admin"
    controller_dir = admin_dir / "Controller"
    controller_dir.mkdir(parents=True)

    # Create some PHP files
    (controller_dir / "UserController.php").write_text("""<?php
class UserController {
    public function index() {}
    public function edit() {}
}
""")

    (controller_dir / "RoleController.php").write_text("""<?php
class RoleController {
    public function index() {}
}
""")

    return tmp_path


class TestSemanticConfig:
    """Test SemanticConfig data structure"""

    def test_semantic_config_creation(self):
        """Test creating SemanticConfig with defaults"""
        config = SemanticConfig()

        assert config.enabled is True
        assert config.use_ai is False
        assert config.fallback_to_heuristic is True

    def test_semantic_config_with_ai_mode(self):
        """Test creating SemanticConfig with AI mode"""
        config = SemanticConfig(
            enabled=True,
            use_ai=True,
            fallback_to_heuristic=True
        )

        assert config.enabled
        assert config.use_ai
        assert config.fallback_to_heuristic


class TestSmartWriterSemanticIntegration:
    """Test SmartWriter with semantic extraction"""

    @pytest.fixture
    def indexing_config_with_semantic(self):
        """Create IndexingConfig with semantic extraction enabled"""
        return IndexingConfig(
            semantic=SemanticConfig(
                enabled=True,
                use_ai=False,  # Use heuristic mode for tests
                fallback_to_heuristic=True
            )
        )

    @pytest.fixture
    def indexing_config_without_semantic(self):
        """Create IndexingConfig without semantic extraction"""
        return IndexingConfig(
            semantic=SemanticConfig(enabled=False)
        )

    def test_smart_writer_with_semantic_enabled(self, indexing_config_with_semantic):
        """Test SmartWriter initializes with semantic extraction"""
        writer = SmartWriter(indexing_config_with_semantic)

        assert writer.config.semantic.enabled
        assert writer.semantic_extractor is not None
        assert not writer.semantic_extractor.use_ai

    def test_smart_writer_without_semantic(self, indexing_config_without_semantic):
        """Test SmartWriter without semantic extraction"""
        writer = SmartWriter(indexing_config_without_semantic)

        assert not writer.config.semantic.enabled
        assert writer.semantic_extractor is None

    def test_extract_module_description_with_semantic(
        self,
        temp_dir,
        indexing_config_with_semantic
    ):
        """
        Test _extract_module_description uses semantic extraction

        Given: A directory with PHP controller files
        When: Semantic extraction is enabled
        Then: Should return meaningful business description, not "Module directory"
        """
        writer = SmartWriter(indexing_config_with_semantic)

        controller_dir = temp_dir / "Application" / "Admin" / "Controller"

        # Create mock ParseResult for the directory
        parse_result = ParseResult(
            path=controller_dir,
            symbols=[
                Symbol(
                    name="UserController",
                    kind="class",
                    signature="class UserController",
                    docstring=None,
                    line_start=2,
                    line_end=5
                ),
                Symbol(
                    name="RoleController",
                    kind="class",
                    signature="class RoleController",
                    docstring=None,
                    line_start=2,
                    line_end=4
                )
            ],
            imports=[],
            module_docstring=None,
            error=None
        )

        # Call _extract_module_description
        description = writer._extract_module_description_semantic(
            dir_path=controller_dir,
            parse_result=parse_result
        )

        # Should NOT be generic "Module directory"
        assert description != "Module directory"

        # Should contain meaningful keywords
        assert any(keyword in description for keyword in
                   ["控制器", "Controller", "用户", "User", "角色", "Role"])

    def test_extract_module_description_fallback(
        self,
        temp_dir,
        indexing_config_with_semantic
    ):
        """
        Test fallback when semantic extraction is disabled

        Given: Semantic extraction disabled
        When: _extract_module_description is called
        Then: Should use old behavior (read README or return "Module directory")
        """
        config = IndexingConfig(
            semantic=SemanticConfig(enabled=False)
        )
        writer = SmartWriter(config)

        controller_dir = temp_dir / "Application" / "Admin" / "Controller"

        # Without README file, should return "Module directory"
        description = writer._extract_module_description(
            dir_path=controller_dir
        )

        assert description == "Module directory"

    def test_semantic_extraction_with_empty_directory(
        self,
        temp_dir,
        indexing_config_with_semantic
    ):
        """
        Test semantic extraction handles empty directory

        Given: An empty directory
        When: Semantic extraction is called
        Then: Should handle gracefully and return meaningful description
        """
        writer = SmartWriter(indexing_config_with_semantic)

        empty_dir = temp_dir / "EmptyModule"
        empty_dir.mkdir()

        parse_result = ParseResult(
            path=empty_dir,
            symbols=[],
            imports=[],
            module_docstring=None,
            error=None
        )

        description = writer._extract_module_description_semantic(
            dir_path=empty_dir,
            parse_result=parse_result
        )

        # Should not crash, should return something
        assert description is not None
        assert len(description) > 0


class TestBDDSemanticIntegration:
    """BDD-style tests for semantic integration user stories"""

    def test_scenario_php_project_readme_generation(self, temp_dir):
        """
        Scenario: Generate README with semantic descriptions for PHP project

        Given I have a PHP project with Admin module
        And The module has Controller and Model subdirectories
        When I generate README with semantic extraction enabled
        Then Each subdirectory should have meaningful business description
        And The descriptions should not be generic like "Module directory"
        """
        # Setup directory structure
        admin = temp_dir / "Application" / "Admin"
        controller_dir = admin / "Controller"
        model_dir = admin / "Model"
        controller_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Create files
        (controller_dir / "UserController.php").write_text("<?php class UserController {}")
        (model_dir / "UserModel.php").write_text("<?php class UserModel {}")

        # Configure with semantic extraction
        config = IndexingConfig(
            semantic=SemanticConfig(
                enabled=True,
                use_ai=False
            )
        )

        writer = SmartWriter(config)

        # Create parse results
        controller_result = ParseResult(
            path=controller_dir,
            symbols=[Symbol("UserController", "class", "class UserController", None, 1, 1)],
            imports=[],
            module_docstring=None,
            error=None
        )

        model_result = ParseResult(
            path=model_dir,
            symbols=[Symbol("UserModel", "class", "class UserModel", None, 1, 1)],
            imports=[],
            module_docstring=None,
            error=None
        )

        # Extract descriptions
        controller_desc = writer._extract_module_description_semantic(
            controller_dir, controller_result
        )
        model_desc = writer._extract_module_description_semantic(
            model_dir, model_result
        )

        # Assertions
        assert controller_desc != "Module directory"
        assert model_desc != "Module directory"
        assert controller_desc != model_desc  # Should be different

        # Controller should mention "控制器" or "Controller"
        assert "控制器" in controller_desc or "Controller" in controller_desc

        # Model should mention "模型" or "Model"
        assert "模型" in model_desc or "Model" in model_desc
