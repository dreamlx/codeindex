"""GH #74: ``codeindex list-dirs`` must not silently return empty when the
configured ``languages`` don't match the project's actual file types. Silent
empty + exit 0 is indistinguishable from "nothing to index" and is the worst
UX class (agent debugs for minutes, human gives up).

These tests cover the three meaningful outcomes:

1. **Language mismatch** — files present, but configured ``languages`` doesn't
   cover any extension that appears in the include roots. Must surface an
   actionable diagnostic to stderr and exit non-zero.
2. **Truly empty** — no files at all under include roots. Silent + exit 0 is
   acceptable (preserve backward compat; nothing to act on).
3. **Happy path** — matching files present. Print dirs to stdout, exit 0.
"""

from pathlib import Path

from click.testing import CliRunner

from codeindex.cli_config import list_dirs


def _write_config(proj: Path, languages: list[str], include: list[str] = ("src/",)) -> None:
    """Write a minimal .codeindex.yaml for the fixture."""
    lines = ["version: 1", "languages:"]
    lines.extend(f"  - {lang}" for lang in languages)
    lines.append("include:")
    lines.extend(f"  - {inc}" for inc in include)
    (proj / ".codeindex.yaml").write_text("\n".join(lines) + "\n")


class TestListDirsLanguageMismatch:
    def test_ts_files_with_python_only_config_emits_diagnostic_and_nonzero_exit(
        self, tmp_path, monkeypatch
    ):
        """The fabricOS-class case: TS-only repo, ``languages: [python]``.
        Without this fix: silent empty + exit 0. With this fix: stderr names
        the mismatch and points to the right languages.
        """
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "src").mkdir()
            (proj / "src" / "app.tsx").write_text("export const x = 1\n")
            (proj / "src" / "util.ts").write_text("export const y = 2\n")
            _write_config(proj, languages=["python"])

            result = runner.invoke(list_dirs, [])

        assert result.exit_code != 0, (
            f"GH #74: silent empty + exit 0 is the bug. Output was:\n{result.output}"
        )
        # Diagnostic must mention what languages are configured...
        assert "python" in result.output, result.output
        # ...what extensions are actually present...
        assert ".ts" in result.output or "ts " in result.output, result.output
        # ...and what to add.
        assert "typescript" in result.output, result.output

    def test_truly_empty_dir_stays_silent_exit_zero(self, tmp_path, monkeypatch):
        """When include roots have no files at all, there's nothing to act on.
        Keep the historical silent + exit 0 — adding noise here would hurt
        scripts that pipe list-dirs to check 'is there anything to index'.
        """
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "src").mkdir()  # empty
            _write_config(proj, languages=["python"])

            result = runner.invoke(list_dirs, [])

        assert result.exit_code == 0, result.output
        # No directories listed and no diagnostic noise.
        assert result.output.strip() == "", (
            f"Expected silent output, got:\n{result.output}"
        )

    def test_happy_path_python_files_with_python_config(self, tmp_path, monkeypatch):
        """Sanity: matching config produces normal output and exit 0."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "src").mkdir()
            (proj / "src" / "mod.py").write_text("def f(): pass\n")
            _write_config(proj, languages=["python"])

            result = runner.invoke(list_dirs, [])

        assert result.exit_code == 0, result.output
        assert "src" in result.output
