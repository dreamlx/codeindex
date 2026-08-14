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
    parent_dir: Path | None = None,
) -> ParseResult:
    # Production scanner always emits paths under the scanned dir_path. Tests
    # that pass a real tmp_path as dir_path should also pass parent_dir=tmp_path
    # so the path matches (otherwise filters keyed on `path.parent == dir_path`
    # — e.g. NavigationGenerator's direct-children filter, GH #76 — silently
    # exclude every fixture).
    base = parent_dir if parent_dir is not None else Path("/test")
    return ParseResult(
        path=base / filename,
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
        results = [_make_result("UserController.php", symbols, parent_dir=tmp_path)]

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

    def test_stats_no_double_count_when_parse_results_is_recursive(self, tmp_path):
        # Regression for GH #45. Navigation level: cli_scan.py runs scan with
        # recursive=True, so parse_results already covers descendants. The
        # generator must NOT add child README stats on top.
        config = IndexingConfig()
        gen = NavigationGenerator(config)

        child = tmp_path / "sub"
        child.mkdir()
        (child / "README_AI.md").write_text(
            "# sub\n- **Files**: 3\n- **Symbols**: 9\n"
        )

        # Simulate scanner having returned 2 files (recursive scan would put
        # everything here — child README is just for the description path).
        results = [
            _make_result("a.py", [Symbol(name="A", kind="class", signature="class A")]),
            _make_result("b.py", [Symbol(name="b1", kind="function", signature="def b1()")]),
        ]

        content = gen.generate(tmp_path, results, [child])
        assert "- **Files**: 2" in content
        assert "- **Symbols**: 2" in content

    def test_files_section_lists_only_direct_children(self, tmp_path):
        # Regression for GH #76. Navigation-level scans are recursive (GH #45),
        # so parse_results includes descendants. The ## Files section must list
        # ONLY this dir's direct children — subdir files belong in their own
        # README_AI.md. Without this filter, agent reading dir/README_AI.md sees
        # `deep.tsx` listed flat and tries to Read `dir/deep.tsx` → 404.
        config = IndexingConfig()
        gen = NavigationGenerator(config)

        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "README_AI.md").write_text("# sub\n")

        direct = ParseResult(
            path=tmp_path / "main.tsx",
            symbols=[Symbol(name="main", kind="function", signature="function main()")],
            imports=[],
            module_docstring="",
            error=None,
            file_lines=10,
            namespace=None,
        )
        nested = ParseResult(
            path=sub / "deep.tsx",
            symbols=[Symbol(name="Deep", kind="class", signature="class Deep")],
            imports=[],
            module_docstring="",
            error=None,
            file_lines=10,
            namespace=None,
        )

        content = gen.generate(tmp_path, [direct, nested], [sub])

        # Direct child appears in ## Files
        assert "main.tsx" in content
        # Subdir file must NOT appear in ## Files (it lives in sub/, has its
        # own README; surfacing it here loses the path and misleads the agent).
        assert "deep.tsx" not in content


class TestOverviewStatsAggregateFromChildren:
    def test_overview_aggregates_when_parse_results_is_direct_only(self, tmp_path):
        # GH #45 sanity check for the asymmetric semantics: overview level
        # is scanned NON-recursively (cli_scan.py), so parse_results contains
        # only direct files. Children's totals come from their READMEs.
        config = IndexingConfig()
        gen = OverviewGenerator(config)

        child = tmp_path / "sub"
        child.mkdir()
        (child / "README_AI.md").write_text(
            "# sub\n- **Files**: 4\n- **Symbols**: 12\n"
        )

        results = [
            _make_result("x.py", [Symbol(name="X", kind="class", signature="class X")]),
        ]

        content = gen.generate(tmp_path, results, [child])
        assert "- **Files**: 5" in content  # 1 direct + 4 from child
        assert "- **Symbols**: 13" in content  # 1 direct + 12 from child


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
        (child / "README_AI.md").write_text("# sub\n")
        content = gen.generate(tmp_path, [], [child])
        assert "[sub/](sub/README_AI.md)" in content

    def test_subdirectory_without_readme_no_dead_link(self, tmp_path):
        # GH #158: skipped/unindexed child dirs have no README_AI.md —
        # emitting a link would be dead. Plain text reference instead.
        gen = self._make_generator()
        child = tmp_path / "sub"
        child.mkdir()
        content = gen.generate(tmp_path, [], [child])
        assert "- sub/" in content
        assert "README_AI.md" not in content

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
