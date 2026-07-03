"""Tests for ``codeindex hooks rerun`` — the user-facing post-commit escape
hatch (GH #89).

``hooks run`` is the hidden internal command the shell hook script delegates
to (GH #34). ``hooks rerun`` is its visible counterpart: a documented escape
hatch for when the post-commit hook didn't fire on a commit (doc-only commit
skipped by the shell wrapper's loop guard, a historical stale README from
before the #84 merge-commit fix, or retroactive populate after flipping
``enabled: false → true``). It calls the same Python logic (``run_post_commit_hook``)
directly, so it bypasses the shell wrapper's doc-only loop guard.
"""

import re

from click.testing import CliRunner

from codeindex.cli_hooks import hooks

# Click's --help lists subcommands under a "Commands:" header, each as an
# indented line "<name>  <help>". Grab the name column of that block (same
# extraction as tests/test_hooks_run_hidden.py, GH #34).
_COMMANDS_BLOCK = re.compile(
    r"Commands:\n((?:[ \t]+\S.*\n?)+)", re.MULTILINE
)


def _advertised(help_text: str) -> list[str]:
    m = _COMMANDS_BLOCK.search(help_text)
    if not m:
        return []
    return [ln.strip().split()[0] for ln in m.group(1).splitlines() if ln.strip()]


class TestHooksRerun:
    def test_rerun_advertised_in_help(self):
        """GH #89: ``rerun`` is the user escape hatch and must be visible in
        ``hooks --help`` (unlike the hidden ``run``)."""
        result = CliRunner().invoke(hooks, ["--help"])
        assert result.exit_code == 0
        advertised = _advertised(result.output)
        assert "rerun" in advertised, (
            f"`hooks rerun` is the user-facing escape hatch and must be "
            f"advertised in `hooks --help`. Advertised: {advertised}"
        )

    def test_run_still_hidden(self):
        """``run`` stays hidden (#34 — shell contract); ``rerun`` is the
        user-facing one. Both coexist: run=internal/hidden, rerun=user/visible."""
        result = CliRunner().invoke(hooks, ["--help"])
        advertised = _advertised(result.output)
        assert "run" not in advertised, (
            f"`hooks run` stays hidden (shell-internal, GH #34); the user "
            f"surface is `rerun`. Advertised: {advertised}"
        )

    def test_rerun_post_commit_calls_run_post_commit_hook(self, tmp_path, monkeypatch):
        """``rerun post-commit`` delegates to ``run_post_commit_hook`` (the
        Python logic), not via the shell wrapper — so the shell's doc-only
        loop guard is bypassed by construction."""
        import os

        called: list[int] = []

        def fake_run() -> int:
            called.append(1)
            return 0

        from codeindex import cli_hooks

        monkeypatch.setattr(cli_hooks, "run_post_commit_hook", fake_run)

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = CliRunner().invoke(hooks, ["rerun", "post-commit"])
        finally:
            os.chdir(original)
        assert result.exit_code == 0, result.output
        assert called == [1], "rerun post-commit must call run_post_commit_hook"

    def test_rerun_unknown_hook_is_handled(self, tmp_path):
        """Unknown hook name prints a message, exits 0 (mirrors `run`)."""
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = CliRunner().invoke(hooks, ["rerun", "pre-push"])
        finally:
            os.chdir(original)
        assert "No run handler" in result.output
        assert result.exit_code == 0
