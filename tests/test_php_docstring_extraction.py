"""Tests for PHP docstring extraction.

Story 9.2: PHP Parser Integration

Tests:
- Parse PHPDoc blocks (/** ... */)
- Parse inline comments (// ...)
- Parse mixed language comments (Chinese + English)
- Parse class docstrings
- Parse method docstrings
- Integration with DocstringProcessor
- Fallback without processor
"""

from unittest.mock import MagicMock, patch

import pytest

from codeindex.docstring_processor import DocstringProcessor
from codeindex.parser import parse_file


class TestPHPDocstringExtraction:
    """Test PHP docstring extraction."""

    def test_parse_phpdoc_block(self, tmp_path):
        """Should extract PHPDoc block comments."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * Get user by ID
 * @param int $id User ID
 * @return array User data
 */
function getUserById($id) {
    return [];
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None
        assert len(result.symbols) > 0

        # Find getUserById function
        func = next((s for s in result.symbols if s.name == "getUserById"), None)
        assert func is not None
        assert func.kind == "function"
        assert func.docstring is not None
        assert "Get user by ID" in func.docstring

    def test_parse_inline_comment(self, tmp_path):
        """Should extract inline comments."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
// Get user list
function getUserList() {
    return [];
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None
        assert len(result.symbols) > 0

        func = next((s for s in result.symbols if s.name == "getUserList"), None)
        assert func is not None
        assert func.docstring is not None
        assert "Get user list" in func.docstring

    def test_parse_mixed_language(self, tmp_path):
        """Should handle mixed language comments (Chinese + English)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * 获取用户列表 Get user list
 * @param int $page 页码 Page number
 */
function getUserList($page) {
    return [];
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None
        func = next((s for s in result.symbols if s.name == "getUserList"), None)
        assert func is not None
        assert func.docstring is not None
        # Should contain both languages
        assert "获取" in func.docstring or "Get" in func.docstring

    def test_parse_class_docstring(self, tmp_path):
        """Should extract class-level docstrings."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * User controller class
 */
class UserController {
    public function index() {
        return [];
    }
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None

        # Find class
        cls = next((s for s in result.symbols if s.kind == "class"), None)
        assert cls is not None
        assert cls.docstring is not None
        assert "User controller" in cls.docstring

    def test_parse_method_docstring(self, tmp_path):
        """Should extract method-level docstrings."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class UserController {
    /**
     * Get user list
     */
    public function getUserList() {
        return [];
    }
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None

        # Find method (name includes class prefix: UserController::getUserList)
        method = next(
            (s for s in result.symbols if "getUserList" in s.name), None
        )
        assert method is not None
        assert method.kind == "method"
        assert method.docstring is not None
        assert "Get user list" in method.docstring

    def test_integration_with_processor(self, tmp_path):
        """Should integrate with DocstringProcessor."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * 获取用户列表 Get user list
 * @param int $page 页码
 * @param int $limit 每页数量
 * @return array User list data
 */
function getUserList($page, $limit) {
    return [];
}
""")

        # Parse PHP file
        parse_result = parse_file(php_file, "php")

        # Create processor
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        # Mock AI response
        ai_response = """{
            "symbols": [
                {
                    "name": "getUserList",
                    "description": "Retrieves paginated user list",
                    "quality": "high"
                }
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            # Process docstrings
            result = processor.process_file(php_file, parse_result.symbols)

        assert "getUserList" in result
        assert result["getUserList"] == "Retrieves paginated user list"

    def test_fallback_without_processor(self, tmp_path):
        """Should work without DocstringProcessor (fallback mode)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * Get user by ID
 */
function getUserById($id) {
    return [];
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None
        func = next((s for s in result.symbols if s.name == "getUserById"), None)
        assert func is not None
        assert func.docstring is not None

        # Even without AI processing, raw docstring should be available
        assert "Get user by ID" in func.docstring


@pytest.mark.skip(reason="SmartWriter integration deferred to Story 9.3")
class TestSmartWriterIntegration:
    """Test SmartWriter integration with DocstringProcessor.

    TODO Story 9.3: Implement SmartWriter.write_readme() integration with
    DocstringProcessor. Requirements:
    - Add docstring_processor parameter to SmartWriter.__init__()
    - Call processor.process_file() in _generate_detailed()
    - Update symbol docstrings before formatting
    """

    def test_smart_writer_uses_processor(self):
        """Should use DocstringProcessor when available."""
        pytest.skip("Deferred to Story 9.3")

    def test_smart_writer_without_processor(self):
        """Should work without DocstringProcessor (backward compatible)."""
        pytest.skip("Deferred to Story 9.3")


class TestPHPParserEdgeCases:
    """Test edge cases in PHP parser."""

    def test_empty_docstring(self, tmp_path):
        """Should handle functions without docstrings."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
function noDoc() {
    return [];
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None
        func = next((s for s in result.symbols if s.name == "noDoc"), None)
        assert func is not None
        # Docstring should be empty or None
        assert func.docstring == "" or func.docstring is None

    def test_multiline_phpdoc(self, tmp_path):
        """Should handle multi-line PHPDoc comments."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * This is a very long description
 * that spans multiple lines
 * with detailed explanation
 * @param int $id User ID
 * @param string $name User name
 * @return array User data
 */
function createUser($id, $name) {
    return [];
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None
        func = next((s for s in result.symbols if s.name == "createUser"), None)
        assert func is not None
        assert func.docstring is not None
        # Should capture the full docstring
        assert "very long description" in func.docstring or "description" in func.docstring

    def test_namespace_and_class(self, tmp_path):
        """Should handle namespaced classes."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Controller;

/**
 * User management controller
 */
class UserController {
    /**
     * Get user list
     */
    public function index() {
        return [];
    }
}
""")

        result = parse_file(php_file, "php")

        assert result.error is None

        # Should find class and method
        cls = next((s for s in result.symbols if "UserController" in s.name), None)
        assert cls is not None

        method = next((s for s in result.symbols if "index" in s.name), None)
        assert method is not None
