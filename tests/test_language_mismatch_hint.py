"""GH #105: the language-mismatch diagnostic is a single shared helper
(`scanner.language_mismatch_hint`) so `list-dirs` AND `scan-all` surface the
same actionable message instead of a silent empty result.

The footgun: `languages: [python]` on a TS/PHP repo makes `scan-all` scan
nothing and exit 0 — indistinguishable from "done". These tests pin the helper
contract and the scan-all wiring.
"""

from pathlib import Path

from click.testing import CliRunner

from codeindex.config import Config
from codeindex.scanner import diagnose_language_mismatch, language_mismatch_hint


def _config(
    proj: Path,
    languages: list[str],
    include=("src/",),
    exclude=(),
) -> Config:
    lines = ["version: 1", "languages:"]
    lines.extend(f"  - {lang}" for lang in languages)
    lines.append("include:")
    lines.extend(f"  - {inc}" for inc in include)
    if exclude:
        lines.append("exclude:")
        lines.extend(f"  - {exc}" for exc in exclude)
    (proj / ".codeindex.yaml").write_text("\n".join(lines) + "\n")
    return Config.load(proj / ".codeindex.yaml")


class TestLanguageMismatchHint:
    def test_mismatch_with_known_candidate(self, tmp_path):
        """Files present, extension maps to a supported language not configured."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.ts").write_text("export const x = 1\n")
        config = _config(tmp_path, languages=["python"])

        hint = language_mismatch_hint(tmp_path, config)

        assert hint is not None
        assert "python" in hint  # what's configured
        assert ".ts" in hint  # what's present
        assert "typescript" in hint  # what to add

    def test_present_but_no_supported_candidate(self, tmp_path):
        """Files present but no codeindex-supported language covers them."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "notes.rst").write_text("just docs\n")
        config = _config(tmp_path, languages=["python"])

        hint = language_mismatch_hint(tmp_path, config)

        assert hint is not None
        assert "no codeindex-supported language" in hint
        assert ".rst" in hint

    def test_truly_empty_returns_none(self, tmp_path):
        """Empty include roots -> None (caller stays silent, exit 0)."""
        (tmp_path / "src").mkdir()  # empty
        config = _config(tmp_path, languages=["python"])

        assert language_mismatch_hint(tmp_path, config) is None


class TestScanAllSurfacesMismatch:
    def test_scan_all_ts_repo_python_config_is_not_silent(self, tmp_path):
        """scan-all on a TS repo with python config must name the mismatch."""
        from codeindex.cli import main

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "src").mkdir()
            (proj / "src" / "app.ts").write_text("export const x = 1\n")
            _config(proj, languages=["python"])

            result = runner.invoke(main, ["scan-all", "--root", str(proj)])

        # Not silent: the diagnostic must appear instead of a bare
        # "No indexable directories found".
        assert "typescript" in result.output, result.output
        assert ".ts" in result.output, result.output


class TestScanAllFingerprintWhenWithFilesGT0:
    """GH #175: scan-all's mismatch hint only fires at ``with_files == 0``
    (``_build_and_print_tree``). When a stray ``.py`` under an include root
    makes ``with_files > 0`` (e.g. ``src/legacy/old.py`` alongside ``src/*.ts``),
    scan-all walks the normal path and emits *no* mismatch check — so a repo
    that's mostly TS but happens to have one stray ``.py`` indexes only the
    ``.py`` and stays silent about the TS. The whole-tree fingerprint closes
    that gap (advisory only — scan-all's partial output is visible, not
    data-loss-class like graph-export's)."""

    def test_stray_py_under_src_with_ts_majority_warns(self, tmp_path):
        from codeindex.cli import main

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "src" / "legacy").mkdir(parents=True)
            (proj / "src" / "legacy" / "old.py").write_text("def old(): return 1\n")
            # majority TS under src/ — the stray .py makes with_files>0, so
            # the with_files==0 mismatch hint never fires, but the fingerprint
            # should catch the uncaptured TS.
            for i in range(12):
                (proj / "src" / f"c{i}.tsx").write_text(
                    f"export const C{i} = () => {i};\n"
                )
            _config(proj, languages=["python"])

            result = runner.invoke(main, ["scan-all", "--root", str(proj)])

        assert result.exit_code == 0, result.output
        assert "typescript" in result.output, result.output
        assert "fingerprint" in result.output.lower(), result.output


class TestDiagnosticAccuracy:
    """GH #156: ``diagnose_language_mismatch`` drove false "Add X" suggestions
    on a TS/JS repo whose non-project files were vendored reference / build
    cache / ambiguous-header — not real source. Three defects, each pinned
    here at the ``diagnose_language_mismatch`` dict level (the single source
    the hint renders from).
    """

    def test_diagnostic_respects_config_exclude(self, tmp_path):
        """D1: the diagnostic walked include roots but never consulted
        ``config.exclude``, so a user couldn't suppress a vendored reference
        dir — 43 ``.h`` under an excluded ``docs/_assets/`` still inflated the
        objc suggestion."""
        vendored = tmp_path / "src" / "vendor" / "firmware"
        vendored.mkdir(parents=True)
        (vendored / "ref.h").write_text("int x;\n")
        config = _config(tmp_path, languages=["python"], exclude=["src/vendor/**"])

        diag = diagnose_language_mismatch(tmp_path, config)

        assert ".h" not in diag["extensions_present"], diag["extensions_present"]
        assert "objc" not in diag["candidate_languages"], diag["candidate_languages"]

    def test_h_without_m_is_not_objc(self, tmp_path):
        """D2: ``.h`` is shared by C/C++/ObjC and codeindex ships no C/C++.
        A repo with ``.h`` but no ``.m`` is almost certainly C/C++ — suggesting
        objc is non-actionable (the objc grammar can't parse C++ → parse errors,
        zero entities). Require ``.m`` for objc candidacy."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "firmware.h").write_text("int x;\n")
        config = _config(tmp_path, languages=["python"])

        diag = diagnose_language_mismatch(tmp_path, config)

        # .h IS present (reported honestly), but objc must NOT be a candidate
        assert ".h" in diag["extensions_present"]
        assert "objc" not in diag["candidate_languages"], diag["candidate_languages"]

    def test_h_with_m_is_objc(self, tmp_path):
        """D2 regression guard: ``.m`` is objc's unambiguous indicator. A repo
        with ``.m`` (with or without ``.h``) still suggests objc."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.h").write_text("@interface A\n@end\n")
        (src / "app.m").write_text("@implementation A\n@end\n")
        config = _config(tmp_path, languages=["python"])

        diag = diagnose_language_mismatch(tmp_path, config)

        assert "objc" in diag["candidate_languages"], diag["candidate_languages"]

    def test_gradle_cache_dir_skipped(self, tmp_path):
        """D3: Android's ``.gradle/<hash>/.../sources/*.java`` are AGP-generated
        accessor classes (pure build cache). They leaked into the ``.java``
        count and inflated the "Add java" suggestion."""
        gen = tmp_path / "src" / ".gradle" / "abc" / "sources"
        gen.mkdir(parents=True)
        (gen / "BuildConfig.java").write_text("class BuildConfig {}\n")
        config = _config(tmp_path, languages=["python"])

        diag = diagnose_language_mismatch(tmp_path, config)

        assert ".java" not in diag["extensions_present"], diag["extensions_present"]
        assert "java" not in diag["candidate_languages"], diag["candidate_languages"]
