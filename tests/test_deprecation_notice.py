"""B3 (Epic #47 / ADR-006): deprecated CLI subcommands print a notice to
stderr, suppressible via CODEINDEX_NO_DEPRECATION_WARNINGS.
"""

from click.testing import CliRunner

from codeindex.cli_claude_md import claude_md
from codeindex.cli_common import print_deprecation_notice
from codeindex.cli_hooks import hooks


class TestPrintDeprecationNotice:
    def test_prints_by_default(self, capsys):
        print_deprecation_notice("`foo`", "use bar instead")
        err = capsys.readouterr().err
        assert "deprecated" in err
        assert "v1.0" in err
        assert "use bar instead" in err

    def test_suppressed_by_env(self, capsys, monkeypatch):
        monkeypatch.setenv("CODEINDEX_NO_DEPRECATION_WARNINGS", "1")
        print_deprecation_notice("`foo`", "use bar instead")
        assert capsys.readouterr().err == ""


class TestSubcommandNotices:
    def test_claude_md_update_warns(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(claude_md, ["update"])
            assert "deprecated" in result.stderr

    def test_claude_md_update_suppressed(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                claude_md, ["update"],
                env={"CODEINDEX_NO_DEPRECATION_WARNINGS": "1"},
            )
            assert "deprecated" not in result.stderr

    def test_hooks_install_warns(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(hooks, ["install", "post-commit"])
            assert "deprecated" in result.stderr
