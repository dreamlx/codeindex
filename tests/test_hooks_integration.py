"""
Integration tests for CLAUDE.md management.

Tests end-to-end behavior of injection and version upgrades.
"""

import pytest

from codeindex.claude_md import inject


@pytest.mark.integration
class TestUpgradeScenario:
    """Test upgrade from old version to new version."""

    def test_upgrade_replaces_old_version(self, tmp_path):
        """Should correctly upgrade from old to new version."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# My Config\n\n"
            "<!-- codeindex:start v0.22.0 -->\n"
            "Old codeindex guide\n"
            "<!-- codeindex:end -->\n\n"
            "# Custom Section\nPreserved.\n"
        )

        inject(claude_md, "0.23.0")

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert "v0.22.0" not in content
        assert "# My Config" in content
        assert "# Custom Section" in content
        assert "Preserved." in content
        assert "codeindex scan-all" in content

    def test_upgrade_from_old_format_markers(self, tmp_path):
        """Should upgrade from old marker format (no version)."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Header\n\n"
            "<!-- codeindex:start -->\n"
            "Old content without version\n"
            "<!-- codeindex:end -->\n"
        )

        inject(claude_md, "0.23.0")

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert content.count("codeindex:start") == 1


@pytest.mark.integration
class TestMultipleUpgrades:
    """Test multiple consecutive upgrades."""

    def test_multiple_upgrades_idempotent(self, tmp_path):
        """Multiple upgrades should be idempotent."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Initial\n")

        inject(claude_md, "0.22.0")
        inject(claude_md, "0.23.0")
        inject(claude_md, "0.23.0")
        content = claude_md.read_text()

        assert content.count("codeindex:start") == 1
        assert content.count("codeindex:end") == 1
        assert "v0.23.0" in content
        assert "v0.22.0" not in content


@pytest.mark.integration
class TestCLICommand:
    """Test the claude-md CLI command."""

    def test_claude_md_update_command(self, tmp_path):
        """Should update CLAUDE.md via CLI."""
        from click.testing import CliRunner

        from codeindex.cli_claude_md import claude_md

        claude_md_file = tmp_path / "CLAUDE.md"
        claude_md_file.write_text("# Test\n")

        runner = CliRunner()
        result = runner.invoke(claude_md, ["update", "--project-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert "Injected" in result.output

        content = claude_md_file.read_text()
        assert "codeindex:start" in content

    def test_claude_md_status_up_to_date(self, tmp_path):
        """Should report up-to-date status."""
        from click.testing import CliRunner

        from codeindex import __version__
        from codeindex.cli_claude_md import claude_md

        claude_md_file = tmp_path / "CLAUDE.md"
        inject(claude_md_file, __version__)

        runner = CliRunner()
        result = runner.invoke(claude_md, ["status", "--project-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert "up-to-date" in result.output

    def test_claude_md_status_outdated(self, tmp_path):
        """Should report outdated status."""
        from click.testing import CliRunner

        from codeindex.cli_claude_md import claude_md

        claude_md_file = tmp_path / "CLAUDE.md"
        inject(claude_md_file, "0.1.0")

        runner = CliRunner()
        result = runner.invoke(claude_md, ["status", "--project-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert "v0.1.0" in result.output
