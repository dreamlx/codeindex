"""B1 (Epic #47 / ADR-006): `codeindex init` produces a minimal, project-scoped
footprint — .codeindex.yaml + project CLAUDE.md + .gitignore — and never the
dropped artifacts (CODEINDEX.md) or git hooks, and never touches ~/.claude.
"""

from pathlib import Path

from click.testing import CliRunner

from codeindex.cli_config import init


class TestInitMinimalScope:
    def test_yes_creates_only_project_scoped_files(self, tmp_path, monkeypatch):
        # Point HOME at an isolated dir so we can assert ~/.claude is untouched.
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "mod.py").write_text("def f():\n    return 1\n")

            result = runner.invoke(init, ["--yes"])
            assert result.exit_code == 0, result.output

            # Created (project-scoped, middle-path B1):
            assert (proj / ".codeindex.yaml").exists()
            assert (proj / "CLAUDE.md").exists()  # project CLAUDE.md injection kept
            assert (proj / ".gitignore").exists()
            assert "README_AI.md" in (proj / ".gitignore").read_text()

            # Dropped by B1:
            assert not (proj / "CODEINDEX.md").exists(), "CODEINDEX.md should no longer be created by init"

            # Never touches user home ~/.claude:
            assert not (fake_home / ".claude").exists(), "init must not create or write ~/.claude"

    def test_yes_does_not_install_git_hooks(self, tmp_path, monkeypatch):
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            # Make it a git repo so a hook *could* be installed if init tried.
            (proj / ".git" / "hooks").mkdir(parents=True)
            (proj / "mod.py").write_text("x = 1\n")

            result = runner.invoke(init, ["--yes"])
            assert result.exit_code == 0, result.output

            # init must not write any hook into .git/hooks
            installed = list((proj / ".git" / "hooks").iterdir())
            assert installed == [], f"init should not install git hooks, found: {installed}"
