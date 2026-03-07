"""
Integration tests for codeindex post-install hooks.

Epic #25, Story #26: Post-install Hook Implementation
These tests verify end-to-end behavior of the hook.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestRealPipInstall:
    """Integration tests with real pip install."""

    def test_real_pip_install_updates_claude_md(self, tmp_path):
        """Should update CLAUDE.md after real pip install --upgrade."""
        # Setup fake home directory
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"

        # Create initial CLAUDE.md with old version
        initial_content = (
            "# My Claude Config\n\n"
            "<!-- CODEINDEX_GUIDE_START v0.21.0 -->\n"
            "Old codeindex guide\n"
            "<!-- CODEINDEX_GUIDE_END -->\n"
        )
        claude_md.write_text(initial_content)

        # Install package in development mode with fake home
        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        # Run pip install (editable mode)
        result = subprocess.run(
            ["pip", "install", "-e", "."],
            cwd=Path(__file__).parent.parent,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"pip install failed: {result.stderr}"

        # Verify CLAUDE.md was updated
        updated_content = claude_md.read_text()
        assert "<!-- CODEINDEX_GUIDE_START v0.22.2 -->" in updated_content
        assert "codeindex scan" in updated_content  # Core command present
        assert "# My Claude Config" in updated_content  # Preserved original content

        # Verify backup was created
        backups = list(claude_dir.glob("CLAUDE.md.backup.*"))
        assert len(backups) > 0
        assert initial_content in backups[0].read_text()


@pytest.mark.integration
class TestUpgradeScenario:
    """Test upgrade from old version to new version."""

    def test_upgrade_from_old_version(self, tmp_path):
        """Should correctly upgrade from v0.11.0 to v0.22.2."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"

        # Simulate v0.11.0 CLAUDE.md content
        old_content = (
            "# CodeIndex Guide\n\n"
            "<!-- CODEINDEX_GUIDE_START v0.11.0 -->\n"
            "## 📦 已安装版本\n"
            "- **当前版本**: v0.11.0\n\n"
            "### 🚀 核心命令\n"
            "```bash\n"
            "codeindex scan ./src\n"
            "```\n"
            "<!-- CODEINDEX_GUIDE_END -->\n\n"
            "# My Custom Section\n"
            "This should be preserved.\n"
        )
        claude_md.write_text(old_content)

        # Simulate upgrade (invoke post_install hook directly)
        from codeindex.hooks import post_install_update_guide

        with patch("pathlib.Path.home", return_value=fake_home):
            with patch("codeindex.hooks._is_ci_environment", return_value=False):
                with patch("importlib.metadata.version", return_value="0.22.2"):
                    post_install_update_guide()

        # Verify upgrade
        new_content = claude_md.read_text()
        assert "<!-- CODEINDEX_GUIDE_START v0.22.2 -->" in new_content
        assert "v0.11.0" not in new_content  # Old version removed
        assert "tech-debt" in new_content  # New v0.22.0+ feature
        assert "# My Custom Section" in new_content  # Custom content preserved
        assert "This should be preserved." in new_content


@pytest.mark.integration
class TestMultipleUpgrades:
    """Test multiple consecutive upgrades."""

    def test_multiple_upgrades_idempotent(self, tmp_path):
        """Multiple upgrades should be idempotent."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("# Initial\n")

        from codeindex.hooks import post_install_update_guide

        with patch("pathlib.Path.home", return_value=fake_home):
            with patch("codeindex.hooks._is_ci_environment", return_value=False):
                with patch("importlib.metadata.version", return_value="0.22.2"):
                    # Run hook 3 times (simulate multiple installs)
                    post_install_update_guide()
                    content_1 = claude_md.read_text()

                    post_install_update_guide()
                    content_2 = claude_md.read_text()

                    post_install_update_guide()
                    content_3 = claude_md.read_text()

        # All three runs should produce identical content
        assert content_1 == content_2
        assert content_2 == content_3

        # Should only have one set of markers
        assert content_3.count("CODEINDEX_GUIDE_START") == 1
        assert content_3.count("CODEINDEX_GUIDE_END") == 1


# Pytest fixtures needed for integration tests
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up any installed packages after tests."""
    yield
    # Cleanup logic if needed
