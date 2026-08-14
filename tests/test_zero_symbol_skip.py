"""GH #158 (proposal 2): 0-symbol directories get no README_AI.

A directory whose parse results contain no symbols and no parse errors
has no navigation value — a README would be pure `ls` noise (evidence:
``src/codeindex/templates/`` — one empty ``__init__.py``, 13-line README).
Such directories are skipped, and a stale README from an older run is
removed so it doesn't keep rotting in place.
"""

from pathlib import Path

from codeindex.cli_scan import _process_directory_with_smartwriter
from codeindex.config import Config
from codeindex.directory_tree import DirectoryTree
from codeindex.parser import ParseResult, Symbol
from codeindex.writers.utils import should_skip_readme


def _result(filename, symbols=(), error=None, parent_dir=None):
    base = parent_dir if parent_dir is not None else Path("/test")
    return ParseResult(
        path=base / filename,
        symbols=list(symbols),
        imports=[],
        module_docstring="",
        error=error,
        file_lines=10,
    )


class TestShouldSkipReadme:
    def test_zero_symbols_skips(self):
        assert should_skip_readme([_result("__init__.py")]) is True

    def test_empty_results_skips(self):
        assert should_skip_readme([]) is True

    def test_with_symbols_not_skipped(self):
        symbols = [Symbol(name="f", kind="function", signature="def f()")]
        assert should_skip_readme([_result("a.py", symbols)]) is False

    def test_parse_error_not_skipped(self):
        # Parse errors surface as "_Parse error_" in the README — diagnostic
        # value that must survive the skip rule.
        assert should_skip_readme([_result("bad.py", error="syntax error")]) is False

    def test_zero_symbols_plus_error_not_skipped(self):
        assert should_skip_readme(
            [_result("a.py"), _result("bad.py", error="syntax error")]
        ) is False


class TestScanSkipsZeroSymbolDirs:
    def _make_project(self, tmp_path):
        empty_pkg = tmp_path / "empty_pkg"
        empty_pkg.mkdir()
        (empty_pkg / "__init__.py").write_text("")
        return empty_pkg

    def test_zero_symbol_dir_gets_no_readme(self, tmp_path):
        config = Config()
        tree = DirectoryTree(tmp_path, config)
        empty_pkg = self._make_project(tmp_path)

        path, success, msg, _ = _process_directory_with_smartwriter(
            empty_pkg, tree, config
        )

        assert success is True
        assert "skip" in msg.lower()
        assert not (empty_pkg / "README_AI.md").exists()

    def test_stale_readme_removed(self, tmp_path):
        config = Config()
        empty_pkg = self._make_project(tmp_path)
        stale = empty_pkg / "README_AI.md"
        stale.write_text("# stale\n")
        tree = DirectoryTree(tmp_path, config)

        _, success, msg, _ = _process_directory_with_smartwriter(
            empty_pkg, tree, config
        )

        assert success is True
        assert "removed" in msg.lower()
        assert not stale.exists()

    def test_dir_with_symbols_still_generates(self, tmp_path):
        config = Config()
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "mod.py").write_text("def useful():\n    pass\n")
        tree = DirectoryTree(tmp_path, config)

        _, success, _, _ = _process_directory_with_smartwriter(pkg, tree, config)

        assert success is True
        assert (pkg / "README_AI.md").exists()


class TestPhase2SkipsMissingReadme:
    def test_enrichment_ignores_dir_without_readme(self, tmp_path):
        """A dir Phase 1 skipped has no README — Phase 2 must not crash or call AI."""
        from unittest.mock import MagicMock, patch

        from codeindex.cli_scan import _enrich_directories_with_ai

        # Navigation-level dir (has an indexed child) whose own README is absent
        nav = tmp_path / "nav"
        child = nav / "pkg"
        child.mkdir(parents=True)
        (child / "mod.py").write_text("def f():\n    pass\n")
        config = Config()
        tree = DirectoryTree(tmp_path, config)

        with patch("codeindex.invoker.invoke_ai", new=MagicMock()) as mock_ai:
            _enrich_directories_with_ai([nav], tree, config, quiet=True, timeout=1)

        mock_ai.assert_not_called()


class TestHubDirsNotSkipped:
    def test_zero_symbols_with_children_keeps_readme(self):
        """Overview/navigation hubs aggregate children — 0 own symbols must not skip them."""
        from codeindex.writers.utils import should_skip_readme

        results = [_result("__init__.py")]
        assert should_skip_readme(results, has_children=True) is False
        assert should_skip_readme(results) is True
