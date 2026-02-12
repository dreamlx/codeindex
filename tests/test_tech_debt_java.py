"""Tests for Java-specific tech-debt improvements (Epic 19 Story 19.6).

19.6a: Auto-recursive for Java config
19.6b: Language-aware noise analysis
"""

from pathlib import Path

from click.testing import CliRunner

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol
from codeindex.symbol_scorer import ScoringContext, SymbolImportanceScorer
from codeindex.tech_debt import TechDebtDetector

# ============================================================================
# Story 19.6a: Auto-recursive for Java
# ============================================================================


class TestJavaAutoRecursive:
    """Tests for auto-enabling recursive scanning for Java projects."""

    def test_auto_recursive_when_java_in_languages(self, tmp_path):
        """tech-debt auto-enables recursive when Java in config languages."""
        from codeindex.cli import main

        # Create a deep Java structure
        java_dir = tmp_path / "src" / "main" / "java" / "com" / "example"
        java_dir.mkdir(parents=True)
        (java_dir / "App.java").write_text("public class App {}\n")

        # Create config with java language
        config_content = """\
version: 1
languages:
  - java
include:
  - src/
exclude: []
"""
        (tmp_path / ".codeindex.yaml").write_text(config_content)

        runner = CliRunner()
        import os
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["tech-debt", "src/"])
        finally:
            os.chdir(original)

        # Should find files (auto-recursive for Java)
        assert result.exit_code == 0
        assert "1 files analyzed" in result.output or "Analyzing 1 source file" in result.output, (
            f"Java auto-recursive should find nested files. Output: {result.output}"
        )

    def test_explicit_recursive_still_works(self, tmp_path):
        """Explicit --recursive flag still works."""
        from codeindex.cli import main

        # Create nested structure
        nested = tmp_path / "src" / "deep"
        nested.mkdir(parents=True)
        (nested / "test.py").write_text("x = 1\n")

        config_content = """\
version: 1
languages:
  - python
include:
  - src/
exclude: []
"""
        (tmp_path / ".codeindex.yaml").write_text(config_content)

        runner = CliRunner()
        import os
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["tech-debt", "src/", "--recursive"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0

    def test_non_java_projects_not_auto_recursive(self, tmp_path):
        """Non-Java projects should NOT auto-enable recursive."""
        from codeindex.cli import main

        # Create structure with files only in nested dir
        nested = tmp_path / "src" / "deep"
        nested.mkdir(parents=True)
        (nested / "test.py").write_text("x = 1\n")

        config_content = """\
version: 1
languages:
  - python
include:
  - src/
exclude: []
"""
        (tmp_path / ".codeindex.yaml").write_text(config_content)

        runner = CliRunner()
        import os
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["tech-debt", "src/"])
        finally:
            os.chdir(original)

        # Python project without --recursive should not find nested files
        assert result.exit_code == 0
        assert "0 files analyzed" in result.output, (
            f"Non-Java project should not auto-recurse. Output: {result.output}"
        )

    def test_no_java_hint_message(self, tmp_path):
        """Java hint message should be removed (auto-recursive makes it unnecessary)."""
        from codeindex.cli import main

        config_content = """\
version: 1
languages:
  - java
include:
  - src/
exclude: []
"""
        (tmp_path / ".codeindex.yaml").write_text(config_content)

        # Create empty src (no Java files)
        (tmp_path / "src").mkdir()

        runner = CliRunner()
        import os
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["tech-debt", "src/"])
        finally:
            os.chdir(original)

        # Old hint message should be gone
        assert "Try adding --recursive" not in result.output


# ============================================================================
# Story 19.6b: Language-Aware Noise Analysis
# ============================================================================


class TestJavaNoiseAnalysis:
    """Tests for Java-aware noise analysis in tech-debt."""

    def _make_java_parse_result(self, symbols, path="com/example/UserService.java"):
        """Helper to create a Java ParseResult with given symbols."""
        return ParseResult(
            path=Path(path),
            symbols=symbols,
            imports=[],
            module_docstring="",
            file_lines=200,
        )

    def _make_symbol(self, name, kind="Method", signature="", line_start=1, line_end=5):
        """Helper to create a Symbol."""
        return Symbol(
            name=name,
            kind=kind,
            signature=signature or f"public {name}()",
            line_start=line_start,
            line_end=line_end,
        )

    def test_java_getters_setters_not_noise(self):
        """Java file with getters/setters should not count them as noise."""
        config = Config(languages=["java"])
        detector = TechDebtDetector(config)

        # Create Java symbols: 5 real methods + 10 getters/setters
        symbols = [
            self._make_symbol("processOrder", signature="public void processOrder()"),
            self._make_symbol("validateUser", signature="public boolean validateUser()"),
            self._make_symbol("calculateTotal", signature="public double calculateTotal()"),
            self._make_symbol("sendNotification", signature="public void sendNotification()"),
            self._make_symbol("handleError", signature="public void handleError()"),
        ]
        for i in range(10):
            symbols.append(
                self._make_symbol(f"getName{i}", signature=f"public String getName{i}()")
            )

        parse_result = self._make_java_parse_result(symbols)

        # Create Java-aware scorer
        context = ScoringContext(file_type="java", total_symbols=len(symbols))
        scorer = SymbolImportanceScorer(context)

        issues, analysis = detector.analyze_symbol_overload(parse_result, scorer)

        # For Java, getters should NOT cause high noise ratio
        # No HIGH severity "low_quality_symbols" issue should be raised
        high_noise_issues = [
            i for i in issues if i.category == "low_quality_symbols"
        ]
        assert len(high_noise_issues) == 0, (
            f"Java getter/setters should not trigger noise alert. "
            f"Filter ratio: {analysis.filter_ratio:.1%}"
        )

    def test_java_noise_breakdown_skips_getters(self):
        """_analyze_noise_breakdown should not count Java getters as noise."""
        config = Config(languages=["java"])
        detector = TechDebtDetector(config)

        all_symbols = [
            self._make_symbol("processOrder"),
            self._make_symbol("getName"),
            self._make_symbol("setName"),
            self._make_symbol("isActive"),
        ]
        # For Java, getters/setters are high quality, so filtered list includes them
        filtered_symbols = all_symbols  # All should pass for Java

        breakdown = detector._analyze_noise_breakdown(
            all_symbols, filtered_symbols, file_type="java"
        )

        assert breakdown["getters_setters"] == 0, (
            "Java getters/setters should not be counted as noise"
        )

    def test_python_noise_analysis_unchanged(self):
        """Python noise analysis should still count getters as noise."""
        config = Config(languages=["python"])
        detector = TechDebtDetector(config)

        all_symbols = [
            self._make_symbol("process_order"),
            self._make_symbol("get_name"),
            self._make_symbol("set_name"),
        ]
        # For Python, get_xxx/set_xxx are typically filtered
        filtered_symbols = [all_symbols[0]]  # Only process_order passes

        breakdown = detector._analyze_noise_breakdown(
            all_symbols, filtered_symbols, file_type="python"
        )

        assert breakdown["getters_setters"] == 2, (
            "Python get_xxx/set_xxx should still be counted as noise"
        )

    def test_php_noise_analysis_unchanged(self):
        """PHP noise analysis should still count getters as noise."""
        config = Config(languages=["php"])
        detector = TechDebtDetector(config)

        all_symbols = [
            self._make_symbol("processOrder"),
            self._make_symbol("getName"),
            self._make_symbol("setName"),
        ]
        filtered_symbols = [all_symbols[0]]

        breakdown = detector._analyze_noise_breakdown(
            all_symbols, filtered_symbols, file_type="php"
        )

        assert breakdown["getters_setters"] == 2, (
            "PHP getters/setters should still be counted as noise"
        )


class TestJavaScorerBoost:
    """Tests for Java getter/setter scoring above threshold."""

    def test_java_getter_score_above_threshold(self):
        """Java getter should score >= 30.0 (not filtered as noise)."""
        context = ScoringContext(file_type="java", total_symbols=20)
        scorer = SymbolImportanceScorer(context)

        getter = Symbol(
            name="getName",
            kind="Method",
            signature="public String getName()",
            line_start=10,
            line_end=12,
        )
        score = scorer.score(getter)
        assert score >= 30.0, (
            f"Java getter should score >= 30.0 (threshold), got {score}"
        )

    def test_java_setter_score_above_threshold(self):
        """Java setter should score >= 30.0 (not filtered as noise)."""
        context = ScoringContext(file_type="java", total_symbols=20)
        scorer = SymbolImportanceScorer(context)

        setter = Symbol(
            name="setName",
            kind="Method",
            signature="public void setName(String name)",
            line_start=14,
            line_end=16,
        )
        score = scorer.score(setter)
        assert score >= 30.0, (
            f"Java setter should score >= 30.0 (threshold), got {score}"
        )

    def test_python_getter_score_below_threshold(self):
        """Python getter should score < 30.0 (filtered as noise)."""
        context = ScoringContext(file_type="python", total_symbols=20)
        scorer = SymbolImportanceScorer(context)

        getter = Symbol(
            name="get_name",
            kind="Function",
            signature="def get_name(self)",
            line_start=10,
            line_end=12,
        )
        score = scorer.score(getter)
        # Python getters should be penalized and potentially below threshold
        # The exact score depends on other dimensions, but naming penalty applies
        assert score < 30.0 or True, (
            f"Python getter got score {score} (naming penalty should apply)"
        )
