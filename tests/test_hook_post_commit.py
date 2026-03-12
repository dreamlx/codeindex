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
    """Python-side post-commit logic."""

    @patch("codeindex.cli_hooks.subprocess.run")
    def test_skips_when_no_affected_dirs(self, mock_run):
        """No affected dirs → no scan, no commit."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"level": "skip", "affected_dirs": []}',
        )
        result = run_post_commit_hook()
        assert result == 0

    @patch("codeindex.cli_hooks.Path.cwd")
    @patch("codeindex.cli_hooks.subprocess.run")
    def test_scans_affected_directories(self, mock_run, mock_cwd, tmp_path):
        """Affected dirs → codeindex scan for each."""
        # Create the README_AI.md so the check passes
        auth_dir = tmp_path / "src" / "auth"
        auth_dir.mkdir(parents=True)
        (auth_dir / "README_AI.md").write_text("# Auth\n")
        mock_cwd.return_value = tmp_path

        diff_mock = MagicMock(returncode=1, stdout="")  # has changes
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout='{"level": "minor", "affected_dirs": ["src/auth"]}',
            ),
            MagicMock(returncode=0, stdout=""),  # scan
            MagicMock(returncode=0, stdout=""),  # git add
            diff_mock,                            # git diff --cached --quiet (1 = has changes)
            MagicMock(returncode=0, stdout="abc123"),  # git rev-parse
            MagicMock(returncode=0, stdout=""),  # git commit
        ]

        run_post_commit_hook()

        # Should have called codeindex scan for the affected dir
        scan_calls = [
            c for c in mock_run.call_args_list
            if "scan" in str(c)
        ]
        assert len(scan_calls) >= 1

    @patch("codeindex.cli_hooks.subprocess.run")
    def test_no_ai_prompt_in_scan(self, mock_run):
        """Scan should use `codeindex scan`, not custom AI prompts."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"level": "minor", "affected_dirs": ["src/mod"]}',
        )

        run_post_commit_hook()

        # Check no call contains AI prompt keywords
        for call in mock_run.call_args_list:
            cmd = str(call)
            assert "PROMPT" not in cmd
            assert "Code Diff" not in cmd
