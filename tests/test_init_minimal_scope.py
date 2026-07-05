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

    def test_yes_seeds_ai_section_default(self, tmp_path, monkeypatch):
        """ADR-008 (reverses GH #75's claude-CLI seed).

        ``codeindex init --yes`` now seeds an ``ai:`` section (DeepSeek direct
        API) instead of ``ai_command`` (claude CLI) — Claude mass-bans made
        the prior default unreliable. The yaml must contain the DeepSeek
        defaults and NO uncommented ``ai_command`` (CLI stays an escape hatch
        the user opts into explicitly). First-try ``scan --ai`` works once
        ``CODEINDEX_AI_API_KEY`` is set (the post-init message points at it).
        """
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "mod.py").write_text("x = 1\n")

            result = runner.invoke(init, ["--yes"])
            assert result.exit_code == 0, result.output

            yaml = (proj / ".codeindex.yaml").read_text()
            assert "ai:" in yaml and "deepseek-chat" in yaml, (
                f"init --yes must seed the `ai:` DeepSeek section (ADR-008). "
                f"yaml:\n{yaml}"
            )
            for line in yaml.splitlines():
                assert not line.strip().startswith("ai_command:"), (
                    f"init --yes must NOT seed ai_command (Claude CLI dead, "
                    f"ADR-008). line: {line!r}"
                )

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

    def test_yes_detects_typescript_javascript_projects(self, tmp_path, monkeypatch):
        """Regression for GH #73.

        ``init_wizard.LANGUAGE_EXTENSIONS`` was a stale local copy missing
        TS/JS (and still carried a "no parser yet" comment from before those
        parsers landed). On a TS-only repo, ``detect_languages()`` returned
        ``[]`` → no ``languages:`` block written → CLI runtime fell back to
        ``DEFAULT_LANGUAGES=["python"]`` → 0 files matched → ``list-dirs``
        silent empty (the user-visible symptom of #73 + #74). Fix imports
        the canonical map from ``scanner.py`` so init tracks whatever the
        runtime can actually parse.
        """
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            proj = Path(proj)
            (proj / "src").mkdir()
            (proj / "src" / "app.tsx").write_text("export const x = 1\n")
            (proj / "src" / "util.ts").write_text("export const y = 2\n")
            (proj / "src" / "legacy.js").write_text("module.exports = {}\n")

            result = runner.invoke(init, ["--yes"])
            assert result.exit_code == 0, result.output

            yaml = (proj / ".codeindex.yaml").read_text()
            assert "languages:" in yaml, (
                f"init must write a languages: block when it detects code, "
                f"otherwise runtime falls back to [python] (GH #73). yaml:\n{yaml}"
            )
            assert "typescript" in yaml, f"TS not detected (GH #73). yaml:\n{yaml}"
            assert "javascript" in yaml, f"JS not detected (GH #73). yaml:\n{yaml}"

    def test_init_language_set_covers_scanner_supported_set(self):
        """Structural lock: every language scanner.py can scan must be
        detectable by init_wizard. If they drift apart (as they did before
        GH #73), init silently produces yaml that the scanner reads as
        "scan nothing".
        """
        from codeindex.init_wizard import LANGUAGE_EXTENSIONS as INIT_EXT
        from codeindex.scanner import LANGUAGE_EXTENSIONS as SCAN_EXT

        missing = set(SCAN_EXT.keys()) - set(INIT_EXT.keys())
        assert not missing, (
            f"init_wizard.LANGUAGE_EXTENSIONS is missing languages that "
            f"scanner.py knows how to scan: {sorted(missing)}. This is the "
            f"drift class that caused GH #73 — init won't write `languages:` "
            f"for these, so the scanner falls back to DEFAULT_LANGUAGES "
            f"(`[python]`) and matches nothing on those projects."
        )
