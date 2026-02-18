"""Integration tests for TypeScript/JavaScript parser (Story 20.7).

Tests end-to-end parsing of fixture files and CLI integration.
"""

from pathlib import Path

from codeindex.parser import parse_file
from codeindex.scanner import LANGUAGE_EXTENSIONS, get_language_extensions

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "typescript"


class TestFixtureParsing:
    """Test parsing real fixture files end-to-end."""

    def test_parse_service_ts(self):
        """Parse service.ts fixture with full feature set."""
        result = parse_file(FIXTURES_DIR / "service.ts")
        assert result.error is None

        # Symbols
        kind_map = {}
        for s in result.symbols:
            kind_map.setdefault(s.kind, []).append(s.name)

        assert "interface" in kind_map
        assert "User" in kind_map["interface"]

        assert "enum" in kind_map
        assert "UserRole" in kind_map["enum"]

        assert "type_alias" in kind_map
        assert "UserMap" in kind_map["type_alias"]

        assert "class" in kind_map
        assert "UserService" in kind_map["class"]

        # Methods
        method_names = kind_map.get("method", [])
        assert any("getUser" in m for m in method_names)
        assert any("createUser" in m for m in method_names)
        assert any("create" in m for m in method_names)

        # Imports
        assert len(result.imports) >= 2

        # Inheritance
        assert len(result.inheritances) >= 1
        us_inh = [i for i in result.inheritances if i.child == "UserService"]
        parents = {i.parent for i in us_inh}
        assert "EventEmitter" in parents

        # Calls
        assert len(result.calls) >= 1

        # The JSDoc is attached to the User interface (not module-level)
        user_iface = next(s for s in result.symbols if s.name == "User")
        assert "User service" in user_iface.docstring

    def test_parse_component_tsx(self):
        """Parse component.tsx fixture (React TSX)."""
        result = parse_file(FIXTURES_DIR / "component.tsx")
        assert result.error is None

        names = [s.name for s in result.symbols]
        assert "Button" in names
        assert "UserList" in names

        # Imports
        react_imports = [i for i in result.imports if i.module == "react"]
        assert len(react_imports) >= 1

    def test_parse_app_js(self):
        """Parse app.js fixture (CommonJS)."""
        result = parse_file(FIXTURES_DIR / "app.js")
        assert result.error is None

        names = [s.name for s in result.symbols]
        assert "App" in names
        assert "createApp" in names

        # CommonJS imports
        express_imports = [i for i in result.imports if i.module == "express"]
        assert len(express_imports) >= 1

    def test_json_output(self):
        """ParseResult.to_dict() produces valid JSON-compatible output."""
        result = parse_file(FIXTURES_DIR / "service.ts")
        d = result.to_dict()

        assert isinstance(d["symbols"], list)
        assert isinstance(d["imports"], list)
        assert isinstance(d["inheritances"], list)
        assert isinstance(d["calls"], list)
        assert isinstance(d["file_lines"], int)
        assert d["error"] is None

        # All symbols serializable
        for sym in d["symbols"]:
            assert "name" in sym
            assert "kind" in sym
            assert "signature" in sym

        # All imports serializable
        for imp in d["imports"]:
            assert "module" in imp

        # All calls serializable
        for call in d["calls"]:
            assert "caller" in call
            assert "callee" in call
            assert "call_type" in call


class TestScannerIntegration:
    """Test scanner recognizes TypeScript/JavaScript files."""

    def test_typescript_in_language_extensions(self):
        """LANGUAGE_EXTENSIONS includes typescript."""
        assert "typescript" in LANGUAGE_EXTENSIONS
        assert ".ts" in LANGUAGE_EXTENSIONS["typescript"]
        assert ".tsx" in LANGUAGE_EXTENSIONS["typescript"]

    def test_javascript_in_language_extensions(self):
        """LANGUAGE_EXTENSIONS includes javascript."""
        assert "javascript" in LANGUAGE_EXTENSIONS
        assert ".js" in LANGUAGE_EXTENSIONS["javascript"]
        assert ".jsx" in LANGUAGE_EXTENSIONS["javascript"]

    def test_get_language_extensions_typescript(self):
        """get_language_extensions returns .ts/.tsx for typescript."""
        exts = get_language_extensions(["typescript"])
        assert ".ts" in exts
        assert ".tsx" in exts

    def test_get_language_extensions_javascript(self):
        """get_language_extensions returns .js/.jsx for javascript."""
        exts = get_language_extensions(["javascript"])
        assert ".js" in exts
        assert ".jsx" in exts

    def test_get_language_extensions_all(self):
        """get_language_extensions with all languages includes TS/JS."""
        exts = get_language_extensions(["python", "php", "java", "typescript", "javascript"])
        assert ".ts" in exts
        assert ".tsx" in exts
        assert ".js" in exts
        assert ".jsx" in exts
        assert ".py" in exts
        assert ".java" in exts
