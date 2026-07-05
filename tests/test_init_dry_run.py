"""Tests for ``codeindex init --dry-run`` — preview mutation targets (GH #88).

``--dry-run`` surfaces what init would create / modify, using the same
detection logic as the real init (no hardcoded bash like the SKILL Step 0 it
replaces). Exit 0 without mutating.
"""

from pathlib import Path

from click.testing import CliRunner

from codeindex.cli_config import init


class TestInitDryRun:
    def test_dry_run_creates_no_files(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "mod.py").write_text("x = 1\n")

            result = runner.invoke(init, ["--dry-run"])
            assert result.exit_code == 0, result.output

            # Nothing mutated — init's 3 targets all absent afterwards.
            assert not (proj / ".codeindex.yaml").exists()
            assert not (proj / "CLAUDE.md").exists()
            assert not (proj / ".gitignore").exists()

    def test_dry_run_lists_all_three_targets(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "mod.py").write_text("x = 1\n")

            result = runner.invoke(init, ["--dry-run"])
            assert result.exit_code == 0, result.output

            out = result.output
            assert ".codeindex.yaml" in out
            assert "CLAUDE.md" in out
            assert ".gitignore" in out
            assert "Would create" in out
            assert "Would modify" in out

    def test_dry_run_marks_existing_config_as_in_place(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "mod.py").write_text("x = 1\n")
            (proj / ".codeindex.yaml").write_text("version: 1\n")  # already exists

            result = runner.invoke(init, ["--dry-run"])
            assert result.exit_code == 0, result.output

            out = result.output
            assert ".codeindex.yaml" in out
            # Existing target must NOT be listed under "Would create".
            create_block = out.split("Would create")[1].split("Would modify")[0] if "Would create" in out else ""
            assert ".codeindex.yaml" not in create_block, (
                f"existing .codeindex.yaml should be 'in place', not 'would create'. output:\n{out}"
            )

    def test_dry_run_exit_zero_and_no_force_required(self, tmp_path, monkeypatch):
        """--dry-run previews even when .codeindex.yaml exists (no --force needed)."""
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "mod.py").write_text("x = 1\n")
            (proj / ".codeindex.yaml").write_text("version: 1\n")

            result = runner.invoke(init, ["--dry-run"])  # no --force
            assert result.exit_code == 0, result.output
