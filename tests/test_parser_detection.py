"""Tests for parser installation detection (Epic 19 Story 19.4).

Checks that the init wizard detects installed/missing tree-sitter parsers
and provides guidance for installation.
"""

from codeindex.init_wizard import check_parser_installed, get_parser_install_guidance


class TestCheckParserInstalled:
    """Tests for check_parser_installed function."""

    def test_python_parser_installed(self):
        """Python parser should be detected as installed."""
        # tree_sitter_python is a dev dependency, should always be available
        assert check_parser_installed("python") is True

    def test_java_parser_installed(self):
        """Java parser should be detected as installed."""
        assert check_parser_installed("java") is True

    def test_php_parser_installed(self):
        """PHP parser should be detected as installed."""
        assert check_parser_installed("php") is True

    def test_unknown_language_not_installed(self):
        """Unknown language should report not installed."""
        assert check_parser_installed("cobol") is False

    def test_unsupported_language_not_installed(self):
        """Language without parser mapping should report not installed."""
        assert check_parser_installed("rust") is False


class TestParserInstallGuidance:
    """Tests for parser installation guidance."""

    def test_all_parsers_installed_no_missing(self):
        """When all parsers are installed, missing list should be empty."""
        # Python, Java, PHP are all installed in dev environment
        languages = ["python", "java", "php"]
        guidance = get_parser_install_guidance(languages)
        assert guidance["missing"] == []
        assert guidance["installed"] == languages

    def test_missing_parser_shows_install_command(self):
        """Missing parser should show install command."""
        languages = ["python", "cobol"]
        guidance = get_parser_install_guidance(languages)
        assert "cobol" in guidance["missing"]
        assert "python" in guidance["installed"]

    def test_empty_languages_no_guidance(self):
        """Empty language list should return empty guidance."""
        guidance = get_parser_install_guidance([])
        assert guidance["missing"] == []
        assert guidance["installed"] == []


class TestInitWizardPostMessage:
    """Tests for updated post-init messages (Story 19.2)."""

    def test_post_init_suggests_scan_all(self, tmp_path):
        """Post-init message should suggest scan-all (works without AI)."""
        import os

        from click.testing import CliRunner

        from codeindex.cli import main

        # Create minimal project
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        runner = CliRunner()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["init", "--yes"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0
        assert "scan-all" in result.output

    def test_post_init_mentions_ai_optional(self, tmp_path):
        """Post-init message should mention --ai as optional."""
        import os

        from click.testing import CliRunner

        from codeindex.cli import main

        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        runner = CliRunner()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["init", "--yes"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0
        # Should mention AI is optional
        output_lower = result.output.lower()
        assert "optional" in output_lower or "--ai" in result.output

    def test_generated_config_no_ai_command(self, tmp_path):
        """Generated config should NOT have active ai_command (AI is opt-in)."""
        import os

        from click.testing import CliRunner

        from codeindex.cli import main
        from codeindex.config import Config

        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        runner = CliRunner()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["init", "--yes"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0

        # Load generated config - ai_command should be empty
        config = Config.load(tmp_path / ".codeindex.yaml")
        assert config.ai_command == "", (
            f"Generated config should not have active ai_command, got: {config.ai_command!r}"
        )
