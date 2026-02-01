"""
Integration tests for Story 4.4: Business Semantic Extraction

Tests the complete workflow:
1. SemanticExtractor extracts business semantics
2. SmartWriter uses semantic descriptions in README_AI.md
3. PROJECT_INDEX uses semantic descriptions

This validates the entire Story 4.4 implementation end-to-end.
"""


import pytest

from codeindex.cli_symbols import extract_module_purpose
from codeindex.config import Config, IndexingConfig, SemanticConfig
from codeindex.parser import ParseResult, Symbol
from codeindex.semantic_extractor import DirectoryContext, SemanticExtractor
from codeindex.smart_writer import SmartWriter


class TestStory44EndToEnd:
    """End-to-end integration tests for Story 4.4"""

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create a realistic test project structure"""
        root = tmp_path / "sample_project"
        root.mkdir()

        # Create src/auth directory (authentication module)
        auth = root / "src" / "auth"
        auth.mkdir(parents=True)

        (auth / "user_manager.py").write_text("""
class UserManager:
    def create_user(self, username, password):
        pass

    def authenticate(self, username, password):
        pass
""")

        (auth / "token_service.py").write_text("""
class TokenService:
    def generate_token(self, user_id):
        pass

    def validate_token(self, token):
        pass
""")

        # Create src/api directory (API endpoints)
        api = root / "src" / "api"
        api.mkdir(parents=True)

        (api / "product_api.py").write_text("""
class ProductAPI:
    def list_products(self):
        pass

    def get_product(self, product_id):
        pass
""")

        # Create src/models directory (data models)
        models = root / "src" / "models"
        models.mkdir(parents=True)

        (models / "user.py").write_text("""
class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username
""")

        (models / "product.py").write_text("""
class Product:
    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price
""")

        return root

    def test_semantic_extractor_on_auth_module(self, test_project):
        """
        Test SemanticExtractor correctly identifies auth module

        Given: An auth directory with UserManager and TokenService
        When: Semantic extraction is performed
        Then: Should identify it as authentication/user management
        """
        auth_dir = test_project / "src" / "auth"

        # Create extractor
        extractor = SemanticExtractor(use_ai=False)

        # Build context
        context = DirectoryContext(
            path=str(auth_dir),
            files=["user_manager.py", "token_service.py"],
            subdirs=[],
            symbols=[
                "UserManager", "TokenService",
                "create_user", "authenticate", "generate_token"
            ],
            imports=[]
        )

        # Extract semantic
        semantic = extractor.extract_directory_semantic(context)

        # Verify auth-related description
        description_lower = semantic.description.lower()
        assert any(keyword in description_lower for keyword in
                   ["user", "用户", "auth", "认证", "token"])
        assert semantic.description != "Module directory"

    def test_semantic_extractor_on_api_module(self, test_project):
        """
        Test SemanticExtractor correctly identifies API module

        Given: An api directory with ProductAPI
        When: Semantic extraction is performed
        Then: Should identify it as API/product-related
        """
        api_dir = test_project / "src" / "api"

        extractor = SemanticExtractor(use_ai=False)

        context = DirectoryContext(
            path=str(api_dir),
            files=["product_api.py"],
            subdirs=[],
            symbols=["ProductAPI", "list_products", "get_product"],
            imports=[]
        )

        semantic = extractor.extract_directory_semantic(context)

        # Verify API or product-related description
        description_lower = semantic.description.lower()
        assert any(keyword in description_lower for keyword in
                   ["api", "接口", "product", "商品"])

    def test_smart_writer_uses_semantic_extraction(self, test_project):
        """
        Test SmartWriter integration with semantic extraction

        Given: SmartWriter with semantic extraction enabled
        When: Extracting module description for auth directory
        Then: Should use SemanticExtractor and return meaningful description
        """
        auth_dir = test_project / "src" / "auth"

        # Create config with semantic extraction enabled
        config = IndexingConfig(
            semantic=SemanticConfig(
                enabled=True,
                use_ai=False
            )
        )

        writer = SmartWriter(config)

        # Create parse result
        parse_result = ParseResult(
            path=auth_dir,
            symbols=[
                Symbol("UserManager", "class", "class UserManager", None, 2, 8),
                Symbol("TokenService", "class", "class TokenService", None, 2, 8)
            ],
            imports=[],
            module_docstring=None,
            error=None
        )

        # Extract description
        description = writer._extract_module_description_semantic(
            auth_dir, parse_result
        )

        # Verify quality
        assert description != "Module directory"
        assert description != "auth module"
        assert len(description) >= 10  # At least 10 characters

    def test_project_index_generation_workflow(self, test_project):
        """
        Test complete PROJECT_INDEX generation workflow

        Given: A project with auth, api, and models directories
        When: Generating PROJECT_INDEX with semantic extraction
        Then: Each module should have unique, meaningful descriptions
        """
        # Create config
        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(
                    enabled=True,
                    use_ai=False
                )
            )
        )

        # Extract purposes for each module
        modules = {
            "auth": test_project / "src" / "auth",
            "api": test_project / "src" / "api",
            "models": test_project / "src" / "models"
        }

        purposes = {}
        for name, path in modules.items():
            purposes[name] = extract_module_purpose(path, config)

        # Verify all different
        assert len(set(purposes.values())) == len(purposes)

        # Verify none are generic
        for purpose in purposes.values():
            assert purpose != "Module directory"
            assert purpose not in ["auth module", "api module", "models module"]

        # Verify auth mentions authentication/user concepts
        auth_desc = purposes["auth"].lower()
        assert any(kw in auth_desc for kw in ["user", "用户", "auth", "认证", "token"])

        # Verify api mentions API concepts
        api_desc = purposes["api"].lower()
        assert any(kw in api_desc for kw in ["api", "接口", "product", "商品"])

        # Verify models mentions data/model concepts
        models_desc = purposes["models"].lower()
        assert any(kw in models_desc for kw in ["model", "模型", "data", "数据", "user", "product"])

    def test_backward_compatibility_without_semantic(self, test_project):
        """
        Test backward compatibility when semantic extraction is disabled

        Given: Semantic extraction disabled
        When: Generating descriptions
        Then: Should fall back to old behavior without errors
        """
        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(enabled=False)
            )
        )

        auth_dir = test_project / "src" / "auth"

        # Should not crash, should return generic description
        purpose = extract_module_purpose(auth_dir, config)

        # Fallback behavior
        assert purpose is not None
        assert len(purpose) > 0


class TestStory44PerformanceValidation:
    """Performance validation for Story 4.4"""

    def test_semantic_extraction_performance(self):
        """
        Test semantic extraction performance

        Should complete in reasonable time (< 100ms for heuristic mode)
        """
        import time

        extractor = SemanticExtractor(use_ai=False)

        context = DirectoryContext(
            path="Application/Admin/Controller",
            files=["UserController.php", "RoleController.php", "PermissionController.php"],
            subdirs=["User", "Role", "Permission"],
            symbols=["UserController", "RoleController", "PermissionController"] * 10,  # 30 symbols
            imports=["BaseController", "Request", "Response"]
        )

        start = time.time()
        semantic = extractor.extract_directory_semantic(context)
        elapsed = time.time() - start

        # Should be fast (heuristic mode)
        assert elapsed < 0.1  # 100ms
        assert semantic is not None

    def test_extract_module_purpose_performance(self, tmp_path):
        """
        Test extract_module_purpose performance

        Should handle directories with many files efficiently
        """
        import time

        # Create directory with many files
        test_dir = tmp_path / "large_module"
        test_dir.mkdir()

        # Create 50 Python files
        for i in range(50):
            (test_dir / f"module_{i}.py").write_text(f"class Module{i}: pass")

        config = Config(
            indexing=IndexingConfig(
                semantic=SemanticConfig(
                    enabled=True,
                    use_ai=False
                )
            )
        )

        start = time.time()
        purpose = extract_module_purpose(test_dir, config)
        elapsed = time.time() - start

        # Should complete quickly even with many files
        assert elapsed < 0.5  # 500ms
        assert purpose is not None
