"""Tests for writers.utils — pure utility functions extracted from SmartWriter."""

from pathlib import Path

from codeindex.config import GroupingConfig, IndexingConfig, SymbolsConfig
from codeindex.framework_detect import RouteInfo
from codeindex.parser import ParseResult, Symbol
from codeindex.writers.utils import (
    collect_recursive_stats,
    collect_top_symbols,
    extract_module_description,
    filter_symbols,
    format_route_table,
    get_key_symbols,
    group_files,
    truncate_content,
)


def _make_result(filename: str, symbols=None, file_lines=100) -> ParseResult:
    return ParseResult(
        path=Path(f"/test/{filename}"),
        symbols=symbols or [],
        imports=[],
        module_docstring="",
        error=None,
        file_lines=file_lines,
    )


# --- collect_recursive_stats ---


class TestCollectRecursiveStats:
    def test_reads_counts_from_readme(self, tmp_path):
        child = tmp_path / "mod1"
        child.mkdir()
        (child / "README_AI.md").write_text(
            "# mod1\n- **Files**: 5\n- **Symbols**: 42\n"
        )
        stats = collect_recursive_stats([child])
        assert stats == {"files": 5, "symbols": 42}

    def test_aggregates_multiple_children(self, tmp_path):
        for name, files, symbols in [("a", 3, 10), ("b", 7, 20)]:
            d = tmp_path / name
            d.mkdir()
            (d / "README_AI.md").write_text(
                f"# {name}\n- **Files**: {files}\n- **Symbols**: {symbols}\n"
            )
        stats = collect_recursive_stats([tmp_path / "a", tmp_path / "b"])
        assert stats == {"files": 10, "symbols": 30}

    def test_missing_readme_returns_zeros(self, tmp_path):
        child = tmp_path / "empty"
        child.mkdir()
        stats = collect_recursive_stats([child])
        assert stats == {"files": 0, "symbols": 0}

    def test_empty_children_list(self):
        stats = collect_recursive_stats([])
        assert stats == {"files": 0, "symbols": 0}


# --- extract_module_description ---


class TestExtractModuleDescription:
    def test_structured_stats(self, tmp_path):
        (tmp_path / "README_AI.md").write_text(
            "# mod\n- **Files**: 3\n- **Symbols**: 15\n"
            "**class** `MyClass`\n**class** `OtherClass`\n"
        )
        desc = extract_module_description(tmp_path)
        assert "3 files" in desc
        assert "15 symbols" in desc
        assert "MyClass" in desc

    def test_free_text_fallback(self, tmp_path):
        (tmp_path / "README_AI.md").write_text(
            "# mod\n\nThis module handles auth logic.\n"
        )
        desc = extract_module_description(tmp_path)
        assert "auth logic" in desc

    def test_no_readme_returns_default(self, tmp_path):
        desc = extract_module_description(tmp_path)
        assert desc == "Module directory"

    def test_custom_output_file(self, tmp_path):
        (tmp_path / "INDEX.md").write_text("# mod\n- **Files**: 1\n")
        desc = extract_module_description(tmp_path, output_file="INDEX.md")
        assert "1 files" in desc


# --- collect_top_symbols ---


class TestCollectTopSymbols:
    def test_collects_classes_and_functions(self, tmp_path):
        child = tmp_path / "mod"
        child.mkdir()
        (child / "README_AI.md").write_text(
            "**class** `MyClass`\n**function** `my_func`\n"
        )
        result = collect_top_symbols([child])
        names = [r[0] for r in result]
        assert "MyClass" in names
        assert "my_func" in names

    def test_respects_limit(self, tmp_path):
        child = tmp_path / "mod"
        child.mkdir()
        lines = "\n".join(f"**class** `C{i}`" for i in range(20))
        (child / "README_AI.md").write_text(lines)
        result = collect_top_symbols([child], limit=5)
        assert len(result) <= 5

    def test_deduplicates(self, tmp_path):
        for name in ["a", "b"]:
            d = tmp_path / name
            d.mkdir()
            (d / "README_AI.md").write_text("**class** `Same`\n")
        result = collect_top_symbols([tmp_path / "a", tmp_path / "b"])
        names = [r[0] for r in result]
        assert names.count("Same") == 1


# --- group_files ---


class TestGroupFiles:
    def test_groups_by_suffix(self):
        config = IndexingConfig(
            grouping=GroupingConfig(
                enabled=True,
                by="suffix",
                patterns={"Controller": "Handlers", "Service": "Logic"},
            )
        )
        results = [
            _make_result("UserController.php"),
            _make_result("OrderService.php"),
            _make_result("Helper.php"),
        ]
        grouped = group_files(results, config)
        assert "Controller" in grouped
        assert "Service" in grouped
        assert "_ungrouped" in grouped
        assert len(grouped["Controller"]) == 1
        assert len(grouped["Service"]) == 1
        assert len(grouped["_ungrouped"]) == 1

    def test_grouping_disabled(self):
        config = IndexingConfig(grouping=GroupingConfig(enabled=False))
        results = [_make_result("a.py"), _make_result("b.py")]
        grouped = group_files(results, config)
        assert "_ungrouped" in grouped
        assert len(grouped["_ungrouped"]) == 2


# --- filter_symbols ---


class TestFilterSymbols:
    def test_exclude_patterns(self):
        config = IndexingConfig(
            symbols=SymbolsConfig(exclude_patterns=["get*", "set*"])
        )
        symbols = [
            Symbol(name="create", kind="method", signature="public function create()"),
            Symbol(name="getName", kind="method", signature="public function getName()"),
            Symbol(name="setName", kind="method", signature="public function setName()"),
        ]
        filtered = filter_symbols(symbols, config)
        names = [s.name for s in filtered]
        assert "create" in names
        assert "getName" not in names
        assert "setName" not in names

    def test_visibility_filter(self):
        config = IndexingConfig(
            symbols=SymbolsConfig(include_visibility=["public"])
        )
        symbols = [
            Symbol(name="pub", kind="method", signature="public function pub()"),
            Symbol(name="priv", kind="method", signature="private function priv()"),
        ]
        filtered = filter_symbols(symbols, config)
        names = [s.name for s in filtered]
        assert "pub" in names
        assert "priv" not in names

    def test_no_visibility_marker_passes(self):
        config = IndexingConfig(
            symbols=SymbolsConfig(include_visibility=["public"])
        )
        symbols = [
            Symbol(name="func", kind="function", signature="def func()"),
        ]
        filtered = filter_symbols(symbols, config)
        assert len(filtered) == 1


# --- get_key_symbols ---


class TestGetKeySymbols:
    def test_returns_classes_and_functions(self):
        symbols = [
            Symbol(name="MyClass", kind="class", signature="class MyClass"),
            Symbol(name="helper", kind="function", signature="def helper()"),
            Symbol(name="MyClass::method", kind="method", signature="public function method()"),
            Symbol(name="private_method", kind="method", signature="private function pm()"),
        ]
        key = get_key_symbols(symbols)
        names = [s.name for s in key]
        assert "MyClass" in names
        assert "helper" in names
        assert "MyClass::method" in names  # public method
        assert "private_method" not in names  # private, not function

    def test_limits_to_five(self):
        symbols = [Symbol(name=f"C{i}", kind="class", signature=f"class C{i}") for i in range(10)]
        key = get_key_symbols(symbols)
        assert len(key) <= 5


# --- format_route_table ---


class TestFormatRouteTable:
    def test_formats_markdown_table(self):
        routes = [
            RouteInfo(url="/api/users", controller="UserController", action="index"),
            RouteInfo(url="/api/orders", controller="OrderController", action="list"),
        ]
        lines = format_route_table(routes, "thinkphp")
        text = "\n".join(lines)
        assert "ThinkPHP" in text
        assert "/api/users" in text
        assert "UserController" in text

    def test_empty_routes(self):
        assert format_route_table([], "thinkphp") == []

    def test_truncates_at_30(self):
        routes = [
            RouteInfo(url=f"/r/{i}", controller="C", action="a")
            for i in range(35)
        ]
        lines = format_route_table(routes, "thinkphp")
        text = "\n".join(lines)
        assert "more routes" in text

    def test_framework_display_names(self):
        route = [RouteInfo(url="/x", controller="C", action="a")]
        for fw, expected in [("laravel", "Laravel"), ("django", "Django"), ("fastapi", "FastAPI")]:
            lines = format_route_table(route, fw)
            assert expected in "\n".join(lines)


# --- truncate_content ---


class TestTruncateContent:
    def test_no_truncation_needed(self):
        content = "Short content"
        result, truncated = truncate_content(content, 1024)
        assert result == content
        assert not truncated

    def test_truncates_at_section_boundary(self):
        sections = "\n## Section 1\nContent1\n\n## Section 2\nContent2\n\n## Section 3\nContent3"
        result, truncated = truncate_content(sections, 60)
        assert truncated
        assert "truncated" in result.lower()

    def test_truncation_adds_notice(self):
        content = "x" * 2000
        result, truncated = truncate_content(content, 500)
        assert truncated
        assert "Content truncated" in result
