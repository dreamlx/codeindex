"""Tests for level-specific generator classes."""

from pathlib import Path

from codeindex.config import GroupingConfig, IndexingConfig, SymbolsConfig
from codeindex.parser import Import, ParseResult, Symbol
from codeindex.writers.detailed_generator import DetailedGenerator
from codeindex.writers.navigation_generator import NavigationGenerator
from codeindex.writers.overview_generator import OverviewGenerator


def _make_result(
    filename: str,
    symbols=None,
    imports=None,
    file_lines=100,
    module_docstring="",
    error=None,
    namespace=None,
) -> ParseResult:
    return ParseResult(
        path=Path(f"/test/{filename}"),
        symbols=symbols or [],
        imports=imports or [],
        module_docstring=module_docstring,
        error=error,
        file_lines=file_lines,
        namespace=namespace,
    )


# --- OverviewGenerator ---


class TestOverviewGenerator:
    def test_generates_overview_content(self, tmp_path):
        config = IndexingConfig()
        gen = OverviewGenerator(config)

        child1 = tmp_path / "module1"
        child2 = tmp_path / "module2"
        child1.mkdir()
        child2.mkdir()
        (child1 / "README_AI.md").write_text(
            "# mod1\n- **Files**: 3\n- **Symbols**: 10\n"
        )
        (child2 / "README_AI.md").write_text(
            "# mod2\n- **Files**: 5\n- **Symbols**: 20\n"
        )

        content = gen.generate(tmp_path, [], [child1, child2])

        assert "overview" in content
        assert "Module Structure" in content
        assert "module1" in content
        assert "module2" in content
        assert "Modules" in content  # Modules section header

    def test_includes_stats(self, tmp_path):
        config = IndexingConfig()
        gen = OverviewGenerator(config)

        child = tmp_path / "mod"
        child.mkdir()
        (child / "README_AI.md").write_text(
            "# mod\n- **Files**: 7\n- **Symbols**: 42\n"
        )

        content = gen.generate(tmp_path, [], [child])
        assert "**Modules**: 1" in content

    def test_includes_key_components(self, tmp_path):
        config = IndexingConfig()
        gen = OverviewGenerator(config)

        child = tmp_path / "mod"
        child.mkdir()
        (child / "README_AI.md").write_text(
            "**class** `MyService`\n**function** `helper`\n"
        )

        content = gen.generate(tmp_path, [], [child])
        assert "Key Components" in content
        assert "MyService" in content

    def test_no_children_minimal_output(self, tmp_path):
        config = IndexingConfig()
        gen = OverviewGenerator(config)
        content = gen.generate(tmp_path, [], [])
        assert "overview" in content
        # No Module Structure section if no children
        assert "Module Structure" not in content


# --- NavigationGenerator ---


class TestNavigationGenerator:
    def test_generates_navigation_content(self, tmp_path):
        config = IndexingConfig()
        gen = NavigationGenerator(config)

        symbols = [
            Symbol(name="UserController", kind="class", signature="class UserController"),
            Symbol(name="UserController::index", kind="method", signature="public function index()"),
        ]
        results = [_make_result("UserController.php", symbols)]

        content = gen.generate(tmp_path, results, [])
        assert "navigation" in content
        assert "Files" in content
        assert "UserController" in content

    def test_includes_subdirectories(self, tmp_path):
        config = IndexingConfig()
        gen = NavigationGenerator(config)

        child = tmp_path / "sub"
        child.mkdir()
        (child / "README_AI.md").write_text("# sub\n- **Files**: 2\n")

        content = gen.generate(tmp_path, [], [child])
        assert "Subdirectories" in content
        assert "sub" in content

    def test_grouped_files(self):
        config = IndexingConfig(
            grouping=GroupingConfig(
                enabled=True,
                by="suffix",
                patterns={"Controller": "HTTP handlers"},
            )
        )
        gen = NavigationGenerator(config)

        results = [
            _make_result("UserController.php", [
                Symbol(name="UserController", kind="class", signature="class UserController"),
            ]),
            _make_result("Helper.php", [
                Symbol(name="helper", kind="function", signature="function helper()"),
            ]),
        ]

        content = gen.generate(Path("/test"), results, [])
        assert "Controller" in content


# --- DetailedGenerator ---


class TestDetailedGenerator:
    def _make_generator(self, config=None):
        from codeindex.adaptive_selector import AdaptiveSymbolSelector
        from codeindex.route_registry import RouteExtractorRegistry

        config = config or IndexingConfig()
        selector = AdaptiveSymbolSelector(config.symbols.adaptive_symbols)
        registry = RouteExtractorRegistry()
        return DetailedGenerator(config, selector, registry)

    def test_generates_detailed_content(self, tmp_path):
        gen = self._make_generator()

        symbols = [
            Symbol(
                name="UserService", kind="class",
                signature="class UserService extends BaseService",
                docstring="Handles user logic",
            ),
            Symbol(
                name="UserService::create", kind="method",
                signature="public function create(array $data): User",
            ),
        ]
        results = [_make_result("UserService.php", symbols, [
            Import(module="App\\Repository\\UserRepo", names=[], is_from=False),
        ])]

        content = gen.generate(tmp_path, results, [])
        assert "detailed" in content
        assert "UserService" in content
        assert "public function create" in content
        assert "Dependencies" in content

    def test_shows_module_docstring(self):
        gen = self._make_generator()
        results = [_make_result("mod.py", module_docstring="This module does X")]
        content = gen.generate(Path("/test"), results, [])
        assert "This module does X" in content

    def test_shows_parse_error(self):
        gen = self._make_generator()
        results = [_make_result("bad.py", error="Syntax error")]
        content = gen.generate(Path("/test"), results, [])
        assert "Parse error" in content

    def test_shows_namespace(self):
        gen = self._make_generator()
        results = [_make_result("Foo.php", namespace="App\\Models")]
        content = gen.generate(Path("/test"), results, [])
        assert "App\\Models" in content

    def test_symbol_filtering(self):
        config = IndexingConfig(
            symbols=SymbolsConfig(exclude_patterns=["get*"])
        )
        gen = self._make_generator(config)

        symbols = [
            Symbol(name="create", kind="function", signature="def create()"),
            Symbol(name="getName", kind="function", signature="def getName()"),
        ]
        results = [_make_result("mod.py", symbols)]
        content = gen.generate(Path("/test"), results, [])
        assert "create" in content
        assert "getName" not in content

    def test_subdirectory_links(self, tmp_path):
        gen = self._make_generator()
        child = tmp_path / "sub"
        child.mkdir()
        content = gen.generate(tmp_path, [], [child])
        assert "sub/" in content
        assert "README_AI.md" in content

    def test_dependencies_section(self):
        gen = self._make_generator()
        results = [_make_result("mod.py", imports=[
            Import(module="os", names=[], is_from=False),
            Import(module="sys", names=[], is_from=False),
        ])]
        content = gen.generate(Path("/test"), results, [])
        assert "Dependencies" in content
        assert "os" in content
        assert "sys" in content

    def test_symbol_grouping_by_kind(self):
        gen = self._make_generator()
        symbols = [
            Symbol(name="MyClass", kind="class", signature="class MyClass"),
            Symbol(name="helper", kind="function", signature="def helper()"),
            Symbol(name="MyClass::method", kind="method", signature="def method()"),
            Symbol(name="MyClass::prop", kind="property", signature="prop: int"),
        ]
        results = [_make_result("mod.py", symbols)]
        content = gen.generate(Path("/test"), results, [])
        assert "**class**" in content
        assert "**Methods:**" in content
        assert "**Functions:**" in content
        assert "**Properties:**" in content
