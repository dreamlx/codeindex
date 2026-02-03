"""Tests for CLI docstring options.

Story 9.3: Configuration & CLI (CLI commands)

Tests:
- --docstring-mode option (off|hybrid|all-ai)
- --show-cost flag for cost reporting
- CLI overrides config values
- Processor created from CLI options
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from codeindex.cli_scan import scan


class TestDocstringCLIOptions:
    """Test CLI options for docstring extraction."""

    def test_docstring_mode_option_accepted(self, tmp_path):
        """Should accept --docstring-mode option."""
        runner = CliRunner()

        # Create test directory with a Python file
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        # Create minimal config
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'echo "test"'
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan,
                [str(test_dir), "--fallback", "--docstring-mode", "hybrid"],
            )

        # Should not have CLI errors
        assert result.exit_code == 0

    def test_docstring_mode_off(self, tmp_path):
        """Should not create processor when mode is off."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'echo "test"'
include: ["."]
languages: ["python"]
""")

        with patch("codeindex.cli_scan.DocstringProcessor") as mock_processor:
            with runner.isolated_filesystem(temp_dir=tmp_path):
                result = runner.invoke(
                    scan, [str(test_dir), "--fallback", "--docstring-mode", "off"]
                )

            # Should not create processor when mode is off
            mock_processor.assert_not_called()

        assert result.exit_code == 0

    def test_docstring_mode_hybrid_creates_processor(self, tmp_path, monkeypatch):
        """Should create processor in hybrid mode."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include: ["."]
languages: ["python"]
""")

        # Change to tmp_path so Config.load() finds the config file
        monkeypatch.chdir(tmp_path)

        with patch("codeindex.cli_scan.DocstringProcessor") as mock_processor:
            with patch("codeindex.cli_scan.SmartWriter") as mock_writer:
                mock_writer_instance = MagicMock()
                mock_writer_instance.write_readme.return_value = MagicMock(
                    success=True, path=Path("test.md"), size_bytes=100, truncated=False
                )
                mock_writer.return_value = mock_writer_instance

                result = runner.invoke(
                    scan,
                    [str(test_dir), "--fallback", "--docstring-mode", "hybrid"],
                )

                # Should create processor with hybrid mode
                mock_processor.assert_called_once()
                call_args = mock_processor.call_args
                assert call_args.kwargs["mode"] == "hybrid"

        assert result.exit_code == 0

    def test_show_cost_flag(self, tmp_path):
        """Should display cost information when --show-cost is set."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include: ["."]
languages: ["python"]
""")

        with patch("codeindex.cli_scan.DocstringProcessor") as mock_processor:
            mock_processor_instance = MagicMock()
            mock_processor_instance.total_tokens = 1500
            mock_processor.return_value = mock_processor_instance

            with patch("codeindex.cli_scan.SmartWriter") as mock_writer:
                mock_writer_instance = MagicMock()
                mock_writer_instance.write_readme.return_value = MagicMock(
                    success=True, path=Path("test.md"), size_bytes=100, truncated=False
                )
                mock_writer.return_value = mock_writer_instance

                with runner.isolated_filesystem(temp_dir=tmp_path):
                    result = runner.invoke(
                        scan,
                        [
                            str(test_dir),
                            "--fallback",
                            "--docstring-mode",
                            "hybrid",
                            "--show-cost",
                        ],
                    )

                # Should show cost information in output
                assert "tokens" in result.output.lower() or "cost" in result.output.lower()

        assert result.exit_code == 0

    def test_cli_overrides_config(self, tmp_path, monkeypatch):
        """CLI --docstring-mode should override config value."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        # Config has mode=off, CLI overrides to hybrid
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include: ["."]
languages: ["python"]
docstrings:
  mode: off
""")

        # Change to tmp_path so Config.load() finds the config file
        monkeypatch.chdir(tmp_path)

        with patch("codeindex.cli_scan.DocstringProcessor") as mock_processor:
            with patch("codeindex.cli_scan.SmartWriter") as mock_writer:
                mock_writer_instance = MagicMock()
                mock_writer_instance.write_readme.return_value = MagicMock(
                    success=True, path=Path("test.md"), size_bytes=100, truncated=False
                )
                mock_writer.return_value = mock_writer_instance

                result = runner.invoke(
                    scan,
                    [str(test_dir), "--fallback", "--docstring-mode", "hybrid"],
                )

                # CLI should override config (mode=hybrid, not off)
                mock_processor.assert_called_once()
                call_args = mock_processor.call_args
                assert call_args.kwargs["mode"] == "hybrid"

        assert result.exit_code == 0

    def test_invalid_docstring_mode_rejected(self, tmp_path):
        """Should reject invalid docstring mode values."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'echo "test"'
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--docstring-mode", "invalid_mode"]
            )

        # Should have CLI error
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "invalid" in result.output.lower()

    def test_docstring_mode_all_ai(self, tmp_path, monkeypatch):
        """Should create processor in all-ai mode."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include: ["."]
languages: ["python"]
""")

        # Change to tmp_path so Config.load() finds the config file
        monkeypatch.chdir(tmp_path)

        with patch("codeindex.cli_scan.DocstringProcessor") as mock_processor:
            with patch("codeindex.cli_scan.SmartWriter") as mock_writer:
                mock_writer_instance = MagicMock()
                mock_writer_instance.write_readme.return_value = MagicMock(
                    success=True, path=Path("test.md"), size_bytes=100, truncated=False
                )
                mock_writer.return_value = mock_writer_instance

                result = runner.invoke(
                    scan,
                    [str(test_dir), "--fallback", "--docstring-mode", "all-ai"],
                )

                # Should create processor with all-ai mode
                mock_processor.assert_called_once()
                call_args = mock_processor.call_args
                assert call_args.kwargs["mode"] == "all-ai"

        assert result.exit_code == 0


class TestDocstringHelp:
    """Test CLI help text for docstring options."""

    def test_docstring_mode_help_shown(self):
        """Should show --docstring-mode in help text."""
        runner = CliRunner()
        result = runner.invoke(scan, ["--help"])

        assert "--docstring-mode" in result.output
        assert "hybrid" in result.output
        assert "all-ai" in result.output

    def test_show_cost_help_shown(self):
        """Should show --show-cost in help text."""
        runner = CliRunner()
        result = runner.invoke(scan, ["--help"])

        assert "--show-cost" in result.output
