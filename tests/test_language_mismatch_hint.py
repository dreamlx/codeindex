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
from codeindex.scanner import language_mismatch_hint


def _config(proj: Path, languages: list[str], include=("src/",)) -> Config:
    lines = ["version: 1", "languages:"]
    lines.extend(f"  - {lang}" for lang in languages)
    lines.append("include:")
    lines.extend(f"  - {inc}" for inc in include)
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
