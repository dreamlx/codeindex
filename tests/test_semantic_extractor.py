"""
Tests for SemanticExtractor (TDD: RED phase)

Story 4.4: Business Semantic Extraction
Task 4.4.1: Create SemanticExtractor foundation
"""

import pytest

from codeindex.semantic_extractor import BusinessSemantic, DirectoryContext, SemanticExtractor


class TestDirectoryContext:
    """Test DirectoryContext data structure"""

    def test_directory_context_creation(self):
        """Test creating DirectoryContext with basic info"""
        context = DirectoryContext(
            path="Application/Admin/Controller",
            files=["UserController.php", "ProductController.php"],
            subdirs=["User", "Product"],
            symbols=["UserController", "ProductController", "index", "edit"],
            imports=["BaseController", "Request"]
        )

        assert context.path == "Application/Admin/Controller"
        assert len(context.files) == 2
        assert len(context.subdirs) == 2
        assert len(context.symbols) == 4
        assert "UserController" in context.symbols


class TestBusinessSemantic:
    """Test BusinessSemantic data structure"""

    def test_business_semantic_creation(self):
        """Test creating BusinessSemantic with description"""
        semantic = BusinessSemantic(
            description="后台管理系统：用户和权限管理",
            purpose="处理后台管理相关的业务逻辑",
            key_components=["用户管理", "权限控制"]
        )

        assert "后台管理" in semantic.description
        assert semantic.purpose
        assert len(semantic.key_components) == 2


class TestSemanticExtractor:
    """Test SemanticExtractor functionality"""

    @pytest.fixture
    def extractor(self):
        """Create a SemanticExtractor instance"""
        return SemanticExtractor(use_ai=False)  # Start with heuristic mode

    def test_extractor_creation(self, extractor):
        """Test creating SemanticExtractor"""
        assert extractor is not None
        assert not extractor.use_ai
        assert extractor.ai_command is None

    def test_extractor_creation_with_ai_requires_command(self):
        """Test that AI mode requires ai_command parameter"""
        with pytest.raises(ValueError, match="ai_command is required"):
            SemanticExtractor(use_ai=True)

    def test_extractor_creation_with_ai_and_command(self):
        """Test creating SemanticExtractor with AI mode"""
        extractor = SemanticExtractor(use_ai=True, ai_command="claude -p '{prompt}'")
        assert extractor.use_ai
        assert extractor.ai_command == "claude -p '{prompt}'"

    def test_extract_controller_semantic_heuristic(self, extractor):
        """
        Test extracting semantic for Controller directory (heuristic mode)

        Given: A directory context with "Controller" in path
        When: Extract semantic using heuristic rules
        Then: Should recognize it as a controller directory
        """
        context = DirectoryContext(
            path="Application/Admin/Controller",
            files=["UserController.php", "ProductController.php"],
            subdirs=[],
            symbols=["UserController", "ProductController", "index", "edit"],
            imports=["BaseController"]
        )

        semantic = extractor.extract_directory_semantic(context)

        # Should recognize "Controller" keyword
        assert semantic is not None
        assert "控制器" in semantic.description or "Controller" in semantic.description
        assert semantic.purpose is not None

    def test_extract_model_semantic_heuristic(self, extractor):
        """
        Test extracting semantic for Model directory (heuristic mode)

        Given: A directory context with "Model" in path
        When: Extract semantic using heuristic rules
        Then: Should recognize it as a model directory
        """
        context = DirectoryContext(
            path="Application/Admin/Model",
            files=["UserModel.php", "RoleModel.php"],
            subdirs=[],
            symbols=["UserModel", "RoleModel", "find", "save"],
            imports=["BaseModel"]
        )

        semantic = extractor.extract_directory_semantic(context)

        assert semantic is not None
        assert "模型" in semantic.description or "Model" in semantic.description

    def test_extract_generic_directory_semantic(self, extractor):
        """
        Test extracting semantic for generic directory (no keywords)

        Given: A directory context without special keywords
        When: Extract semantic using heuristic rules
        Then: Should provide a generic but meaningful description
        """
        context = DirectoryContext(
            path="Application/Common/Utils",
            files=["StringHelper.php", "ArrayHelper.php"],
            subdirs=[],
            symbols=["StringHelper", "ArrayHelper", "format", "parse"],
            imports=[]
        )

        semantic = extractor.extract_directory_semantic(context)

        # Should not be empty or too generic like "Module directory"
        assert semantic is not None
        assert len(semantic.description) > 10
        assert semantic.description != "Module directory"

    def test_infer_from_symbols(self, extractor):
        """
        Test inferring business semantic from symbol names

        Given: Directory with meaningful symbol names (e.g., UserController)
        When: Extract semantic
        Then: Should infer "user-related" functionality
        """
        context = DirectoryContext(
            path="Application/Admin",
            files=["UserController.php", "UserModel.php"],
            subdirs=["Controller", "Model"],
            symbols=["UserController", "UserModel", "login", "register"],
            imports=[]
        )

        semantic = extractor.extract_directory_semantic(context)

        # Should infer user-related functionality
        assert semantic is not None
        description_lower = semantic.description.lower()
        # Check for user-related keywords in any language
        assert any(keyword in description_lower for keyword in
                   ["user", "用户", "auth", "认证", "登录"])

    def test_empty_context_handling(self, extractor):
        """
        Test handling empty directory context

        Given: Directory with no files or symbols
        When: Extract semantic
        Then: Should handle gracefully and return basic description
        """
        context = DirectoryContext(
            path="Application/Empty",
            files=[],
            subdirs=[],
            symbols=[],
            imports=[]
        )

        semantic = extractor.extract_directory_semantic(context)

        # Should handle gracefully
        assert semantic is not None
        assert len(semantic.description) > 0


class TestSemanticExtractorWithAI:
    """Test SemanticExtractor with AI mode"""

    @pytest.fixture
    def ai_extractor(self):
        """Create AI-enabled SemanticExtractor"""
        return SemanticExtractor(use_ai=True, ai_command="claude -p '{prompt}'")

    def test_build_ai_prompt(self, ai_extractor):
        """Test AI prompt building"""
        context = DirectoryContext(
            path="Application/Admin/Controller",
            files=["UserController.php", "RoleController.php"],
            subdirs=["User", "Role"],
            symbols=["UserController", "RoleController", "index", "edit"],
            imports=["BaseController"]
        )

        prompt = ai_extractor._build_ai_prompt(context)

        # Verify prompt contains key information
        assert "Application/Admin/Controller" in prompt
        assert "UserController.php" in prompt
        assert "RoleController" in prompt
        assert "JSON" in prompt
        assert "description" in prompt
        assert "purpose" in prompt
        assert "key_components" in prompt

    def test_parse_ai_response_json_block(self, ai_extractor):
        """Test parsing AI response with JSON in code block"""
        response = '''```json
{
  "description": "后台管理控制器：用户和角色管理",
  "purpose": "处理后台管理的HTTP请求和业务逻辑",
  "key_components": ["用户管理", "角色管理", "权限控制"]
}
```'''

        semantic = ai_extractor._parse_ai_response(response)

        assert semantic.description == "后台管理控制器：用户和角色管理"
        assert semantic.purpose == "处理后台管理的HTTP请求和业务逻辑"
        assert len(semantic.key_components) == 3
        assert "用户管理" in semantic.key_components

    def test_parse_ai_response_plain_json(self, ai_extractor):
        """Test parsing AI response with plain JSON"""
        response = '''{
  "description": "用户管理模块",
  "purpose": "处理用户相关业务逻辑",
  "key_components": ["认证", "授权"]
}'''

        semantic = ai_extractor._parse_ai_response(response)

        assert semantic.description == "用户管理模块"
        assert semantic.purpose == "处理用户相关业务逻辑"
        assert len(semantic.key_components) == 2

    def test_parse_ai_response_invalid(self, ai_extractor):
        """Test parsing invalid AI response raises error"""
        response = "This is not JSON at all"

        with pytest.raises(ValueError, match="No JSON found"):
            ai_extractor._parse_ai_response(response)

    def test_parse_ai_response_missing_description(self, ai_extractor):
        """Test parsing AI response without description field"""
        response = '''{
  "purpose": "Some purpose",
  "key_components": ["A", "B"]
}'''

        with pytest.raises(ValueError, match="Missing 'description'"):
            ai_extractor._parse_ai_response(response)

    @pytest.mark.skip(reason="AI mode integration test - requires actual AI CLI")
    def test_ai_extract_admin_module(self, ai_extractor):
        """
        Test AI extraction for Admin module

        This requires actual AI CLI to be available
        """
        context = DirectoryContext(
            path="Application/Admin",
            files=["UserController.php", "RoleController.php"],
            subdirs=["Controller", "Model", "View"],
            symbols=["UserController", "RoleController", "RoleModel"],
            imports=[]
        )

        semantic = ai_extractor.extract_directory_semantic(context)

        # AI should infer deeper business meaning
        assert semantic is not None
        assert "后台" in semantic.description or "管理" in semantic.description
        assert len(semantic.key_components) >= 2


# BDD-style scenario tests
class TestBDDScenarios:
    """BDD-style scenario tests for user stories"""

    def test_scenario_php_project_index_quality(self):
        """
        Scenario: Improve PHP project index quality

        Given I have a PHP project with Admin and Retail modules
        When I generate PROJECT_INDEX.md with semantic extraction
        Then Each module should have a unique business description
        And The description should not be generic like "Business module"
        """
        extractor = SemanticExtractor(use_ai=False)

        # Admin module
        admin_context = DirectoryContext(
            path="Application/Admin",
            files=["UserController.php", "RoleController.php"],
            subdirs=["Controller", "Model"],
            symbols=["UserController", "RoleController"],
            imports=[]
        )

        admin_semantic = extractor.extract_directory_semantic(admin_context)

        # Retail module
        retail_context = DirectoryContext(
            path="Application/Retail",
            files=["ProductController.php", "CartController.php"],
            subdirs=["Controller", "Model"],
            symbols=["ProductController", "CartController"],
            imports=[]
        )

        retail_semantic = extractor.extract_directory_semantic(retail_context)

        # Assertions
        # 1. Different descriptions (differentiation)
        assert admin_semantic.description != retail_semantic.description

        # 2. Not generic
        assert admin_semantic.description != "Business module"
        assert retail_semantic.description != "Business module"

        # 3. KISS format: path + pattern + symbols
        assert "Application/Admin" in admin_semantic.description
        assert "Application/Retail" in retail_semantic.description

        # 4. Contains actual symbols (not translations)
        assert ("Role" in admin_semantic.description or "User" in admin_semantic.description)
        assert ("Product" in retail_semantic.description or "Cart" in retail_semantic.description)
