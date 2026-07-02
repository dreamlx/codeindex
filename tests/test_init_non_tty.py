"""Regression tests for GH #44.

``codeindex init`` (no flags) in a non-TTY environment (CI runner,
sandbox, container) used to fall through to ``click.confirm``/``prompt``,
which raise a bare ``Abort`` — the user saw a cryptic ``Aborted!`` with no
hint that ``--yes`` is the fix.

Expected (issue option 2, the safer choice — no silent behavior change):
exit with a clear, actionable error pointing at ``--yes``.
"""

from click.testing import CliRunner

from codeindex.cli_config import init


class TestInitNonTty:
    def test_non_tty_without_yes_gives_actionable_error(self, tmp_path):
        """CliRunner's stdin is not a TTY, mirroring CI/sandbox."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(init, [])

        assert result.exit_code != 0
        # Must name the fix explicitly, not the bare Click "Aborted!".
        assert "--yes" in result.output
        assert "Aborted!" not in result.output

    def test_yes_still_works_in_non_tty(self, tmp_path):
        """--yes is the documented CI path and must remain unaffected."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            from pathlib import Path

            (Path(proj) / "src").mkdir()
            (Path(proj) / "src" / "main.py").write_text("x = 1\n")
            result = runner.invoke(init, ["--yes"])

        assert result.exit_code == 0
        assert (Path(proj) / ".codeindex.yaml").exists()
