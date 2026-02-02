"""
Tests for PROJECT_INDEX.md semantic enhancement (TDD: RED phase)

Story 4.4: Business Semantic Extraction
Task 4.4.3: PROJECT_INDEX enhancement with semantic descriptions
"""


import pytest

from codeindex.cli_symbols import extract_module_purpose
from codeindex.config import Config, IndexingConfig, SemanticConfig


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure for testing"""
    # Create project structure
    root = tmp_path / "test_project"
    root.mkdir()

    # Create Admin module
    admin = root / "Application" / "Admin"
    admin_controller = admin / "Controller"
    admin_controller.mkdir(parents=True)

    # Create files
    (admin_controller / "UserController.php").write_text("""<?php
class UserController {
    public function index() {}
    public function edit() {}
}
""")

    # Create Retail module
    retail = root / "Application" / "Retail"
    retail_product = retail / "Controller"
    retail_product.mkdir(parents=True)

    (retail_product / "ProductController.php").write_text("""<?php
class ProductController {
    public function list() {}
}
""")

    return root


class TestExtractModulePurpose:
    """Test extract_module_purpose function"""

    def test_extract_purpose_with_semantic(self, temp_project):
        """
        Test extracting module purpose with semantic extraction

        Given: A PHP Controller directory with UserController
        When: Semantic extraction is enabled
        Then: Should return meaningful business description
        And: Should not return generic "{name} module"
        """
        admin_controller = temp_project / "Application" / "Admin" / "Controller"

        # Create config with semantic extraction enabled
        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(
                    enabled=True,
                    use_ai=False
                )
            )
        )

        purpose = extract_module_purpose(
            dir_path=admin_controller,
            config=config
        )

        # Should not be generic
        assert purpose != "Controller module"
        assert purpose != "Module directory"

        # Should contain meaningful keywords
        assert any(keyword in purpose for keyword in
                   ["控制器", "Controller", "用户", "User"])

    def test_extract_purpose_without_semantic(self, temp_project):
        """
        Test extracting module purpose without semantic extraction

        Given: Semantic extraction disabled
        When: Extracting module purpose
        Then: Should use old behavior (read README or return generic)
        """
        admin_controller = temp_project / "Application" / "Admin" / "Controller"

        # Create config with semantic extraction disabled
        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(enabled=False)
            )
        )

        purpose = extract_module_purpose(
            dir_path=admin_controller,
            config=config
        )

        # Without README, should return generic description
        assert "module" in purpose.lower() or "directory" in purpose.lower()

    def test_extract_purpose_from_readme_fallback(self, temp_project):
        """
        Test fallback to README extraction

        Given: A directory with README_AI.md but semantic disabled
        When: Extracting purpose
        Then: Should read from README
        """
        admin_controller = temp_project / "Application" / "Admin" / "Controller"

        # Create README with Purpose section
        readme_content = """# Controller Directory

## Purpose

Handles HTTP requests for Admin module user management

## Files
- UserController.php
"""
        (admin_controller / "README_AI.md").write_text(readme_content)

        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(enabled=False)
            )
        )

        purpose = extract_module_purpose(
            dir_path=admin_controller,
            config=config
        )

        # Should extract from README
        assert "HTTP requests" in purpose or "Admin module" in purpose


class TestProjectIndexGeneration:
    """Test full PROJECT_INDEX.md generation with semantic descriptions"""

    def test_project_index_with_semantic(self, temp_project):
        """
        Test PROJECT_INDEX.md includes semantic descriptions

        Given: A project with Admin and Retail modules
        And: Semantic extraction is enabled
        When: Generating PROJECT_INDEX.md
        Then: Admin and Retail should have different, meaningful descriptions
        And: Descriptions should not be generic like "Business module"
        """
        # Create README_AI.md files (simulating previous scan)
        admin_controller = temp_project / "Application" / "Admin" / "Controller"
        (admin_controller / "README_AI.md").write_text("# Admin Controller\nSome content")

        retail_controller = temp_project / "Application" / "Retail" / "Controller"
        (retail_controller / "README_AI.md").write_text("# Retail Controller\nSome content")

        # Create config
        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(
                    enabled=True,
                    use_ai=False
                )
            )
        )

        # Extract purposes for both
        admin_purpose = extract_module_purpose(admin_controller, config)
        retail_purpose = extract_module_purpose(retail_controller, config)

        # Assertions
        assert admin_purpose != retail_purpose  # Should be different
        assert admin_purpose != "Controller module"
        assert retail_purpose != "Controller module"

        # Admin should have user-related keywords
        assert any(keyword in admin_purpose for keyword in
                   ["用户", "User", "控制器", "Controller"])

        # Retail should have product-related keywords
        assert any(keyword in retail_purpose for keyword in
                   ["商品", "Product", "控制器", "Controller"])


class TestBDDProjectIndex:
    """BDD-style tests for PROJECT_INDEX enhancement"""

    def test_scenario_php_project_index_quality(self, temp_project):
        """
        Scenario: Generate PROJECT_INDEX.md with high quality descriptions

        Given I have a PHP project with multiple modules
        And Each module has been scanned (has README_AI.md)
        When I generate PROJECT_INDEX.md with semantic extraction
        Then Each module should have a unique business description
        And No module should show generic descriptions like "Business module"
        """
        # Setup: Create README files
        modules = [
            temp_project / "Application" / "Admin" / "Controller",
            temp_project / "Application" / "Retail" / "Controller",
        ]

        for module_dir in modules:
            (module_dir / "README_AI.md").write_text(
                f"# {module_dir.name}\nModule content"
            )

        # Configure with semantic extraction
        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(
                    enabled=True,
                    use_ai=False
                )
            )
        )

        # Extract purposes
        purposes = [extract_module_purpose(m, config) for m in modules]

        # All purposes should be different
        assert len(set(purposes)) == len(purposes)

        # No generic descriptions
        for purpose in purposes:
            assert purpose != "Business module"
            assert purpose != "Module directory"
            assert "module" not in purpose.lower() or any(
                keyword in purpose.lower()
                for keyword in ["控制器", "controller", "用户", "user", "商品", "product"]
            )
