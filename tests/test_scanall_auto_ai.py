"""Tests for scan-all auto-AI enrichment behavior (Epic 25).

When ai_command is configured in .codeindex.yaml, scan-all should
automatically enable Phase 2 AI enrichment. --no-ai disables it.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from codeindex.cli import main


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def project_with_ai_command(tmp_path):
    """Project with ai_command configured."""
    config = tmp_path / ".codeindex.yaml"
    config.write_text(
        "codeindex: 1\n"
        "ai_command: 'echo test'\n"
        "languages:\n  - python\n"
        "include:\n  - src/\n"
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def main(): pass\n")
    return tmp_path


@pytest.fixture
def project_without_ai_command(tmp_path):
    """Project without ai_command configured."""
    config = tmp_path / ".codeindex.yaml"
    config.write_text(
        "codeindex: 1\n"
        "languages:\n  - python\n"
        "include:\n  - src/\n"
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def main(): pass\n")
    return tmp_path


class TestScanAllAutoAI:
    """scan-all auto-detects ai_command and enables Phase 2."""

    @patch("codeindex.cli_scan._enrich_directories_with_ai")
    @patch("codeindex.cli_scan._process_directory_with_smartwriter")
    def test_auto_enables_ai_when_ai_command_configured(
        self, mock_smartwriter, mock_enrich, cli_runner, project_with_ai_command
    ):
        """When ai_command is in config, Phase 2 runs automatically."""
        mock_smartwriter.return_value = (
            project_with_ai_command / "src", True, "ok", 100
        )
        mock_enrich.return_value = None

        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_with_ai_command)]
        )

        assert result.exit_code == 0
        mock_enrich.assert_called_once()

    @patch("codeindex.cli_scan._enrich_directories_with_ai")
    @patch("codeindex.cli_scan._process_directory_with_smartwriter")
    def test_no_ai_flag_disables_auto_enrichment(
        self, mock_smartwriter, mock_enrich, cli_runner, project_with_ai_command
    ):
        """--no-ai explicitly disables Phase 2 even with ai_command."""
        mock_smartwriter.return_value = (
            project_with_ai_command / "src", True, "ok", 100
        )

        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_with_ai_command), "--no-ai"]
        )

        assert result.exit_code == 0
        mock_enrich.assert_not_called()

    @patch("codeindex.cli_scan._enrich_directories_with_ai")
    @patch("codeindex.cli_scan._process_directory_with_smartwriter")
    def test_no_enrichment_without_ai_command(
        self, mock_smartwriter, mock_enrich, cli_runner, project_without_ai_command
    ):
        """Without ai_command in config, Phase 2 does not run."""
        mock_smartwriter.return_value = (
            project_without_ai_command / "src", True, "ok", 100
        )

        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_without_ai_command)]
        )

        assert result.exit_code == 0
        mock_enrich.assert_not_called()

    @patch("codeindex.cli_scan._enrich_directories_with_ai")
    @patch("codeindex.cli_scan._process_directory_with_smartwriter")
    def test_explicit_ai_flag_still_works(
        self, mock_smartwriter, mock_enrich, cli_runner, project_with_ai_command
    ):
        """--ai flag is backward compatible (same as auto-detect)."""
        mock_smartwriter.return_value = (
            project_with_ai_command / "src", True, "ok", 100
        )
        mock_enrich.return_value = None

        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_with_ai_command), "--ai"]
        )

        assert result.exit_code == 0
        mock_enrich.assert_called_once()

    def test_explicit_ai_without_ai_command_errors(
        self, cli_runner, project_without_ai_command
    ):
        """--ai without ai_command still gives clear error."""
        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_without_ai_command), "--ai"]
        )

        assert result.exit_code != 0
        assert "ai_command" in result.output

    @patch("codeindex.cli_scan._enrich_directories_with_ai")
    @patch("codeindex.cli_scan._process_directory_with_smartwriter")
    def test_ai_and_no_ai_mutually_exclusive(
        self, mock_smartwriter, mock_enrich, cli_runner, project_with_ai_command
    ):
        """--ai and --no-ai together should error."""
        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_with_ai_command),
                   "--ai", "--no-ai"]
        )

        assert result.exit_code != 0
        assert "mutually exclusive" in result.output.lower() or "conflict" in result.output.lower()

    @patch("codeindex.cli_scan._enrich_directories_with_ai")
    @patch("codeindex.cli_scan._process_directory_with_smartwriter")
    def test_auto_ai_shows_info_message(
        self, mock_smartwriter, mock_enrich, cli_runner, project_with_ai_command
    ):
        """When auto-detecting AI, show informational message."""
        mock_smartwriter.return_value = (
            project_with_ai_command / "src", True, "ok", 100
        )
        mock_enrich.return_value = None

        result = cli_runner.invoke(
            main, ["scan-all", "--root", str(project_with_ai_command)]
        )

        assert result.exit_code == 0
        assert "--no-ai" in result.output  # Should mention how to disable
