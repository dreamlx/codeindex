"""Tests for GH #34 — hide the internal `hooks run` subcommand from --help.

`codeindex hooks run` is invoked by the generated shell hook scripts, not by
users. Surfacing it in `hooks --help` is noise that reads like a user-facing
command. Pin it as `hidden=True` while keeping the invocation working (the
shell scripts depend on it).
"""

import re

from click.testing import CliRunner

from codeindex.cli_hooks import hooks

# Click's --help lists subcommands under a "Commands:" header, each as an
# indented line "<name>  <help>". Grab the name column of that block.
_COMMANDS_BLOCK = re.compile(
    r"Commands:\n((?:[ \t]+\S.*\n?)+)", re.MULTILINE
)


def _advertised_subcommands(help_text: str) -> list[str]:
    m = _COMMANDS_BLOCK.search(help_text)
    if not m:
        return []
    return [ln.strip().split()[0] for ln in m.group(1).splitlines() if ln.strip()]


class TestHooksRunHidden:
    def test_run_absent_from_help(self):
        result = CliRunner().invoke(hooks, ["--help"])
        assert result.exit_code == 0
        advertised = _advertised_subcommands(result.output)
        assert "run" not in advertised, (
            f"`hooks run` is internal (called by shell hook scripts) and must "
            f"not be advertised in `hooks --help`. Advertised: {advertised}"
        )

    def test_run_still_invokable(self, tmp_path):
        """The shell hook scripts call `hooks run <name>`; hiding must not
        disable it. post-commit on a bare dir exits 0 via the no-op guard."""
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = CliRunner().invoke(hooks, ["run", "post-commit"])
        finally:
            os.chdir(original)
        # Unknown-command would be exit code 2 with "No such command".
        assert "No such command" not in result.output
        assert result.exit_code in (0, 1)
