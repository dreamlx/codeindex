"""Tests for JSON output serialization."""

from pathlib import Path

from codeindex.parser import Import, ParseResult, Symbol


class TestSymbolSerialization:
    """Test Symbol.to_dict() method."""

    def test_symbol_to_dict_basic(self):
        """Should serialize Symbol to dict with all fields."""
        symbol = Symbol(
            name="UserService",
            kind="class",
            signature="class UserService:",
            docstring="User management service",
            line_start=10,
            line_end=50,
        )

        result = symbol.to_dict()

        assert result == {
            "name": "UserService",
            "kind": "class",
            "signature": "class UserService:",
            "docstring": "User management service",
            "line_start": 10,
            "line_end": 50,
        }

    def test_symbol_to_dict_empty_docstring(self):
        """Should handle empty docstring."""
        symbol = Symbol(
            name="my_function",
            kind="function",
            signature="def my_function():",
            docstring="",
            line_start=5,
            line_end=10,
        )

        result = symbol.to_dict()

        assert result["docstring"] == ""

    def test_symbol_to_dict_method(self):
        """Should serialize method symbol."""
        symbol = Symbol(
            name="UserService.login",
            kind="method",
            signature="def login(self, username: str) -> bool:",
            docstring="Authenticate user",
            line_start=12,
            line_end=25,
        )

        result = symbol.to_dict()

        assert result["name"] == "UserService.login"
        assert result["kind"] == "method"


class TestImportSerialization:
    """Test Import.to_dict() method."""

    def test_import_to_dict_basic(self):
        """Should serialize Import to dict."""
        imp = Import(
            module="typing",
            names=["Optional", "Dict"],
            is_from=True,
        )

        result = imp.to_dict()

        assert result == {
            "module": "typing",
            "names": ["Optional", "Dict"],
            "is_from": True,
        }

    def test_import_to_dict_no_names(self):
        """Should handle import with no names (import module)."""
        imp = Import(
            module="os",
            names=[],
            is_from=False,
        )

        result = imp.to_dict()

        assert result["module"] == "os"
        assert result["names"] == []
        assert result["is_from"] is False


class TestParseResultSerialization:
    """Test ParseResult.to_dict() method."""

    def test_parse_result_to_dict_basic(self):
        """Should serialize ParseResult to dict."""
        result = ParseResult(
            path=Path("src/user.py"),
            symbols=[
                Symbol(
                    name="UserService",
                    kind="class",
                    signature="class UserService:",
                    docstring="User management",
                    line_start=10,
                    line_end=50,
                )
            ],
            imports=[
                Import(
                    module="typing",
                    names=["Optional"],
                    is_from=True,
                )
            ],
            module_docstring="User authentication module",
            namespace="",
            error=None,
            file_lines=100,
        )

        data = result.to_dict()

        # Check top-level fields
        assert data["path"] == "src/user.py"  # Path converted to string
        assert data["module_docstring"] == "User authentication module"
        assert data["file_lines"] == 100
        assert data["error"] is None

        # Check symbols
        assert len(data["symbols"]) == 1
        assert data["symbols"][0]["name"] == "UserService"
        assert data["symbols"][0]["kind"] == "class"

        # Check imports
        assert len(data["imports"]) == 1
        assert data["imports"][0]["module"] == "typing"

    def test_parse_result_to_dict_with_error(self):
        """Should serialize ParseResult with error."""
        result = ParseResult(
            path=Path("src/broken.py"),
            symbols=[],
            imports=[],
            module_docstring="",
            error="SyntaxError at line 42: unexpected EOF",
            file_lines=0,
        )

        data = result.to_dict()

        assert data["path"] == "src/broken.py"
        assert data["error"] == "SyntaxError at line 42: unexpected EOF"
        assert data["symbols"] == []

    def test_parse_result_to_dict_empty_symbols(self):
        """Should handle empty symbols list."""
        result = ParseResult(
            path=Path("src/empty.py"),
            symbols=[],
            imports=[],
            module_docstring="Empty module",
            error=None,
            file_lines=5,
        )

        data = result.to_dict()

        assert data["symbols"] == []
        assert data["imports"] == []

    def test_parse_result_to_dict_multiple_symbols(self):
        """Should serialize multiple symbols."""
        result = ParseResult(
            path=Path("src/models.py"),
            symbols=[
                Symbol("User", "class", "class User:", "", 1, 10),
                Symbol("Post", "class", "class Post:", "", 12, 20),
                Symbol("get_user", "function", "def get_user():", "", 22, 25),
            ],
            imports=[],
            module_docstring="",
            error=None,
            file_lines=30,
        )

        data = result.to_dict()

        assert len(data["symbols"]) == 3
        assert data["symbols"][0]["name"] == "User"
        assert data["symbols"][1]["name"] == "Post"
        assert data["symbols"][2]["name"] == "get_user"

    def test_parse_result_to_dict_path_conversion(self):
        """Should convert Path to string (relative path)."""
        # Test with absolute path
        result = ParseResult(
            path=Path("/absolute/path/to/src/user.py"),
            symbols=[],
            imports=[],
            error=None,
        )

        data = result.to_dict()

        # Path should be converted to string
        assert isinstance(data["path"], str)
        # Should preserve the path as-is (absolute or relative)
        assert data["path"] == "/absolute/path/to/src/user.py"

    def test_parse_result_to_dict_php_namespace(self):
        """Should include PHP namespace if present."""
        result = ParseResult(
            path=Path("Application/Admin/Controller/UserController.php"),
            symbols=[
                Symbol("UserController", "class", "class UserController", "", 5, 50)
            ],
            imports=[],
            module_docstring="",
            namespace="Application\\Admin\\Controller",
            error=None,
            file_lines=100,
        )

        data = result.to_dict()

        assert data["namespace"] == "Application\\Admin\\Controller"


class TestJSONCompatibility:
    """Test JSON compatibility."""

    def test_json_serializable(self):
        """Should be JSON serializable."""
        import json

        result = ParseResult(
            path=Path("src/test.py"),
            symbols=[
                Symbol("TestClass", "class", "class TestClass:", "Test class", 1, 10)
            ],
            imports=[Import("os", [], False)],
            module_docstring="Test module",
            error=None,
            file_lines=20,
        )

        data = result.to_dict()

        # Should not raise exception
        json_str = json.dumps(data, ensure_ascii=False)

        # Should be able to parse back
        parsed = json.loads(json_str)

        assert parsed["path"] == "src/test.py"
        assert parsed["symbols"][0]["name"] == "TestClass"

    def test_chinese_characters_serializable(self):
        """Should handle Chinese characters in docstrings."""
        import json

        result = ParseResult(
            path=Path("src/user.py"),
            symbols=[
                Symbol(
                    "UserService",
                    "class",
                    "class UserService:",
                    "用户管理服务",
                    1,
                    10,
                )
            ],
            imports=[],
            module_docstring="用户认证模块",
            error=None,
            file_lines=20,
        )

        data = result.to_dict()

        # Should handle Chinese characters
        json_str = json.dumps(data, ensure_ascii=False)

        assert "用户管理服务" in json_str
        assert "用户认证模块" in json_str
