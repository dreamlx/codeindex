"""Tests for post-commit hook: thin wrapper + Python logic (Epic 25).

The post-commit hook should:
1. Be a thin shell wrapper calling `codeindex hooks run post-commit`
2. Python logic handles: affected dirs → codeindex scan → auto-commit
3. No custom AI prompts, no git diff injection
"""

from unittest.mock import MagicMock, patch

from codeindex.cli_hooks import (
    _generate_post_commit_script,
    generate_hook_script,
    run_post_commit_hook,
)


class TestThinWrapperScript:
    """The generated hook script should be a thin wrapper."""

    def test_calls_codeindex_hooks_run(self):
        """Hook script delegates to `codeindex hooks run post-commit`."""
        script = _generate_post_commit_script({})
        assert "codeindex hooks run post-commit" in script

    def test_no_custom_ai_prompt(self):
        """Hook script must not contain custom AI prompts."""
        script = _generate_post_commit_script({})
        assert "PROMPT" not in script
        assert "Code Diff" not in script
        assert "git diff HEAD" not in script

    def test_still_has_loop_guard(self):
        """Hook script still guards against infinite commit loops."""
        script = _generate_post_commit_script({})
        assert "README_AI.md" in script

    def test_disabled_config(self):
        """Disabled config generates exit-only script."""
        script = _generate_post_commit_script({"auto_update": False})
        assert "exit 0" in script

    def test_has_codeindex_marker(self):
        """Generated script contains codeindex marker for management."""
        script = generate_hook_script("post-commit")
        assert "codeindex-managed hook" in script


class TestRunPostCommitHook:
    """Python-side post-commit logic (tree-aware since GH #160)."""

    @staticmethod
    def _affected_json(dirs):
        import json as _json
        return _json.dumps({"level": "affected", "affected_dirs": dirs})

    @staticmethod
    def _fake_subprocess(affected_dirs, staged_changes=False):
        """Dispatch subprocess.run: affected query answered, git ops succeed."""
        def fake_run(cmd, *args, **kwargs):
            if "affected" in cmd:
                return MagicMock(returncode=0,
                                 stdout=TestRunPostCommitHook._affected_json(affected_dirs))
            if "diff" in cmd:  # git diff --cached --quiet: 1 = has changes
                return MagicMock(returncode=1 if staged_changes else 0, stdout="")
            return MagicMock(returncode=0, stdout="")
        return fake_run

    @patch("codeindex.cli_hooks.subprocess.run")
    def test_skips_when_no_affected_dirs(self, mock_run):
        """No affected dirs → no render, no commit."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"level": "skip", "affected_dirs": []}',
        )
        result = run_post_commit_hook()
        assert result == 0

    @patch("codeindex.cli_hooks.Path.cwd")
    @patch("codeindex.cli_hooks.subprocess.run")
    def test_hub_dir_renders_navigation_not_detailed(self, mock_run, mock_cwd, tmp_path):
        """GH #160 regression: a dir with indexed children must keep its
        navigation-level README — the old per-dir `codeindex scan` subprocess
        hardcoded detailed and overwrote scan-all's hierarchy."""
        (tmp_path / "src" / "auth" / "sub").mkdir(parents=True)
        (tmp_path / "src" / "auth" / "__init__.py").write_text("def a():\n    pass\n")
        (tmp_path / "src" / "auth" / "sub" / "mod.py").write_text("def b():\n    pass\n")
        mock_cwd.return_value = tmp_path
        mock_run.side_effect = self._fake_subprocess(["src/auth"])

        run_post_commit_hook()

        content = (tmp_path / "src" / "auth" / "README_AI.md").read_text()
        assert "(navigation)" in content

    @patch("codeindex.cli_hooks.Path.cwd")
    @patch("codeindex.cli_hooks.subprocess.run")
    def test_new_dir_without_readme_gets_one(self, mock_run, mock_cwd, tmp_path):
        """New dirs (no prior README) are rendered, not skipped — the old
        `readme_path.exists()` guard left freshly added source dirs unindexed."""
        pkg = tmp_path / "src" / "newpkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text("def f():\n    pass\n")
        mock_cwd.return_value = tmp_path
        mock_run.side_effect = self._fake_subprocess(["src/newpkg"])

        run_post_commit_hook()

        assert (pkg / "README_AI.md").exists()

    @patch("codeindex.cli_hooks.Path.cwd")
    @patch("codeindex.cli_hooks.subprocess.run")
    def test_zero_symbol_dir_stale_readme_removed(self, mock_run, mock_cwd, tmp_path):
        """0-symbol skip (GH #158) is inherited from the shared seam."""
        empty = tmp_path / "src" / "empty"
        empty.mkdir(parents=True)
        (empty / "__init__.py").write_text("")
        (empty / "README_AI.md").write_text("# stale\n")
        mock_cwd.return_value = tmp_path
        mock_run.side_effect = self._fake_subprocess(["src/empty"])

        run_post_commit_hook()

        assert not (empty / "README_AI.md").exists()

    @patch("codeindex.cli_hooks.Path.cwd")
    @patch("codeindex.cli_hooks.subprocess.run")
    def test_no_codeindex_scan_subprocess(self, mock_run, mock_cwd, tmp_path):
        """Rendering is in-process now — no per-dir `codeindex scan` spawn."""
        pkg = tmp_path / "src" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "mod.py").write_text("def f():\n    pass\n")
        mock_cwd.return_value = tmp_path
        mock_run.side_effect = self._fake_subprocess(["src/pkg"])

        run_post_commit_hook()

        for call in mock_run.call_args_list:
            cmd = call.args[0]
            # tmp_path itself contains "scan" (pytest dir naming) — match the
            # invocation shape, not a substring.
            assert not (cmd[0].endswith("codeindex") and len(cmd) > 1 and cmd[1] == "scan")
