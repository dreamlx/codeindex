"""
Unit tests for codeindex post-install hooks.

Epic #25, Story #26: Post-install Hook Implementation
Tests follow TDD Red-Green-Refactor cycle.
"""

import os
from unittest.mock import patch

from codeindex.hooks import (
    _extract_version_from_file,
    _inject_core_guide,
    _is_ci_environment,
    post_install_update_guide,
)


class TestExtractVersion:
    """Tests for version extraction from CLAUDE.md."""

    def test_extract_version_from_valid_marker(self, tmp_path):
        """Should extract version from valid marker."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Test\n"
            "<!-- CODEINDEX_GUIDE_START v0.21.0 -->\n"
            "Content\n"
            "<!-- CODEINDEX_GUIDE_END -->\n"
        )

        version = _extract_version_from_file(claude_md)
        assert version == "0.21.0"

    def test_extract_version_returns_none_if_no_marker(self, tmp_path):
        """Should return None if no marker exists."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\nNo markers here")

        version = _extract_version_from_file(claude_md)
        assert version is None

    def test_extract_version_handles_missing_file(self, tmp_path):
        """Should return None for missing file."""
        nonexistent = tmp_path / "does_not_exist.md"

        version = _extract_version_from_file(nonexistent)
        assert version is None

    def test_extract_version_handles_malformed_marker(self, tmp_path):
        """Should return None for malformed version marker."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "<!-- CODEINDEX_GUIDE_START invalid -->\n"
        )

        version = _extract_version_from_file(claude_md)
        assert version is None


class TestInjectCoreGuide:
    """Tests for core guide injection."""

    def test_inject_core_guide_new_content(self, tmp_path):
        """Should inject guide into file without existing markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Existing content\n\nSome text")

        success = _inject_core_guide(claude_md, "0.22.2")

        assert success is True
        content = claude_md.read_text()
        assert "<!-- CODEINDEX_GUIDE_START v0.22.2 -->" in content
        assert "<!-- CODEINDEX_GUIDE_END -->" in content
        assert "# Existing content" in content

    def test_inject_core_guide_idempotent(self, tmp_path):
        """Should update existing guide content (idempotent)."""
        claude_md = tmp_path / "CLAUDE.md"
        initial_content = (
            "# Header\n"
            "<!-- CODEINDEX_GUIDE_START v0.21.0 -->\n"
            "Old guide content\n"
            "<!-- CODEINDEX_GUIDE_END -->\n"
            "# Footer\n"
        )
        claude_md.write_text(initial_content)

        # First update
        success1 = _inject_core_guide(claude_md, "0.22.2")
        assert success1 is True

        # Second update (should be idempotent)
        success2 = _inject_core_guide(claude_md, "0.22.2")
        assert success2 is True

        content = claude_md.read_text()
        # Should only have one set of markers
        assert content.count("CODEINDEX_GUIDE_START") == 1
        assert content.count("CODEINDEX_GUIDE_END") == 1
        assert "<!-- CODEINDEX_GUIDE_START v0.22.2 -->" in content

    def test_inject_core_guide_preserves_surrounding_content(self, tmp_path):
        """Should preserve content before and after guide section."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Before\nImportant content\n\n"
            "<!-- CODEINDEX_GUIDE_START v0.21.0 -->\n"
            "Old guide\n"
            "<!-- CODEINDEX_GUIDE_END -->\n\n"
            "# After\nMore important content"
        )

        _inject_core_guide(claude_md, "0.22.2")

        content = claude_md.read_text()
        assert "# Before\nImportant content" in content
        assert "# After\nMore important content" in content


class TestCIEnvironmentDetection:
    """Tests for CI environment detection."""

    def test_is_ci_environment_github_actions(self):
        """Should detect GitHub Actions environment."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_gitlab_ci(self):
        """Should detect GitLab CI environment."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_jenkins(self):
        """Should detect Jenkins environment."""
        with patch.dict(os.environ, {"JENKINS_HOME": "/var/jenkins"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_circle_ci(self):
        """Should detect CircleCI environment."""
        with patch.dict(os.environ, {"CIRCLECI": "true"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_generic_ci(self):
        """Should detect generic CI variable."""
        with patch.dict(os.environ, {"CI": "true"}):
            assert _is_ci_environment() is True

    def test_is_ci_environment_local_dev(self):
        """Should return False for local development."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear all CI-related env vars
            for key in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_HOME", "CIRCLECI"]:
                os.environ.pop(key, None)
            assert _is_ci_environment() is False


class TestPostInstallUpdateGuide:
    """Tests for main post-install hook."""

    def test_post_install_skip_if_ci_environment(self):
        """Should skip update in CI environment."""
        with patch("codeindex.hooks._is_ci_environment", return_value=True):
            with patch("codeindex.hooks._inject_core_guide") as mock_inject:
                post_install_update_guide()
                mock_inject.assert_not_called()

    def test_post_install_skip_if_no_claude_dir(self, tmp_path):
        """Should skip if ~/.claude directory does not exist."""
        with patch("codeindex.hooks._is_ci_environment", return_value=False):
            with patch("pathlib.Path.home", return_value=tmp_path):
                with patch("codeindex.hooks._inject_core_guide") as mock_inject:
                    post_install_update_guide()
                    mock_inject.assert_not_called()

    def test_post_install_creates_backup(self, tmp_path):
        """Should create backup of existing CLAUDE.md."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("Original content")

        with patch("codeindex.hooks._is_ci_environment", return_value=False):
            with patch("pathlib.Path.home", return_value=tmp_path):
                with patch("codeindex.hooks._inject_core_guide", return_value=True):
                    post_install_update_guide()

        # Check backup was created
        backups = list(claude_dir.glob("CLAUDE.md.backup.*"))
        assert len(backups) > 0
        assert backups[0].read_text() == "Original content"

    def test_post_install_handles_permission_error(self, tmp_path):
        """Should handle permission errors gracefully."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("Content")

        with patch("codeindex.hooks._is_ci_environment", return_value=False):
            with patch("pathlib.Path.home", return_value=tmp_path):
                with patch("codeindex.hooks._inject_core_guide", side_effect=PermissionError):
                    # Should not raise exception
                    post_install_update_guide()

    def test_post_install_uses_current_version(self, tmp_path):
        """Should inject guide with current package version."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("# Test")

        with patch("codeindex.hooks._is_ci_environment", return_value=False):
            with patch("pathlib.Path.home", return_value=tmp_path):
                with patch("importlib.metadata.version", return_value="0.22.2"):
                    with patch("codeindex.hooks._inject_core_guide") as mock_inject:
                        post_install_update_guide()
                        mock_inject.assert_called_once_with(claude_md, "0.22.2")
