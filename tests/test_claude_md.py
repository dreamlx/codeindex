"""
Unit tests for codeindex CLAUDE.md management.

Tests the unified marker-based injection and version checking.
"""

from unittest.mock import patch

from codeindex.claude_md import (
    MARKER_PATTERN,
    build_section,
    check_outdated,
    extract_version,
    inject,
)


class TestExtractVersion:
    """Tests for version extraction from CLAUDE.md markers."""

    def test_extract_version_from_new_marker(self, tmp_path):
        """Should extract version from new-format marker."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Test\n"
            "<!-- codeindex:start v0.23.0 -->\n"
            "Content\n"
            "<!-- codeindex:end -->\n"
        )
        assert extract_version(claude_md) == "0.23.0"

    def test_extract_version_returns_none_if_no_marker(self, tmp_path):
        """Should return None if no marker exists."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\nNo markers here")
        assert extract_version(claude_md) is None

    def test_extract_version_handles_missing_file(self, tmp_path):
        """Should return None for missing file."""
        nonexistent = tmp_path / "does_not_exist.md"
        assert extract_version(nonexistent) is None

    def test_extract_version_old_marker_without_version(self, tmp_path):
        """Should return None for old marker without version."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "<!-- codeindex:start -->\n"
            "Old content\n"
            "<!-- codeindex:end -->\n"
        )
        assert extract_version(claude_md) is None


class TestBuildSection:
    """Tests for section building."""

    def test_build_section_with_explicit_version(self):
        """Should build section with given version."""
        section = build_section("1.2.3")
        assert "<!-- codeindex:start v1.2.3 -->" in section
        assert "<!-- codeindex:end -->" in section
        assert "v1.2.3" in section

    def test_build_section_contains_quick_commands(self):
        """Should include quick commands in section."""
        section = build_section("0.23.0")
        assert "codeindex scan-all" in section
        assert "codeindex --help" in section

    def test_build_section_contains_update_hint(self):
        """Should include upgrade reminder."""
        section = build_section("0.23.0")
        assert "codeindex claude-md update" in section


class TestInject:
    """Tests for CLAUDE.md injection."""

    def test_inject_creates_new_file(self, tmp_path):
        """Should create CLAUDE.md if it doesn't exist."""
        claude_md = tmp_path / "CLAUDE.md"
        assert inject(claude_md, "0.23.0") is True
        assert claude_md.exists()

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert "<!-- codeindex:end -->" in content

    def test_inject_appends_to_existing_file(self, tmp_path):
        """Should append section to existing file without markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# My Project\n\nExisting content")

        assert inject(claude_md, "0.23.0") is True

        content = claude_md.read_text()
        assert "# My Project" in content
        assert "Existing content" in content
        assert "<!-- codeindex:start v0.23.0 -->" in content

    def test_inject_replaces_existing_section(self, tmp_path):
        """Should replace existing section between markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Header\n\n"
            "<!-- codeindex:start v0.22.0 -->\n"
            "Old content\n"
            "<!-- codeindex:end -->\n\n"
            "# Footer\n"
        )

        assert inject(claude_md, "0.23.0") is True

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert "v0.22.0" not in content
        assert "Old content" not in content
        assert "# Header" in content
        assert "# Footer" in content

    def test_inject_replaces_old_format_markers(self, tmp_path):
        """Should replace old-format markers (without version)."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Header\n\n"
            "<!-- codeindex:start -->\n"
            "Old content\n"
            "<!-- codeindex:end -->\n\n"
            "# Footer\n"
        )

        assert inject(claude_md, "0.23.0") is True

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert content.count("codeindex:start") == 1

    def test_inject_idempotent(self, tmp_path):
        """Multiple injections should produce same result."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\n")

        inject(claude_md, "0.23.0")
        content_1 = claude_md.read_text()

        inject(claude_md, "0.23.0")
        content_2 = claude_md.read_text()

        assert content_1 == content_2
        assert content_2.count("codeindex:start") == 1

    def test_inject_preserves_surrounding_content(self, tmp_path):
        """Should preserve content before and after section."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Before\nImportant\n\n"
            "<!-- codeindex:start v0.22.0 -->\n"
            "Old\n"
            "<!-- codeindex:end -->\n\n"
            "# After\nAlso important"
        )

        inject(claude_md, "0.23.0")

        content = claude_md.read_text()
        assert "# Before\nImportant" in content
        assert "# After\nAlso important" in content


class TestCheckOutdated:
    """Tests for version check."""

    def test_returns_none_if_no_claude_md(self, tmp_path):
        """Should return None if CLAUDE.md doesn't exist."""
        assert check_outdated(tmp_path) is None

    def test_returns_none_if_no_markers(self, tmp_path):
        """Should return None if no codeindex markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# No markers\n")
        assert check_outdated(tmp_path) is None

    def test_returns_none_if_up_to_date(self, tmp_path):
        """Should return None if version matches."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("<!-- codeindex:start v9.9.9 -->\n<!-- codeindex:end -->\n")

        with patch("codeindex.claude_md._get_current_version", return_value="9.9.9"):
            assert check_outdated(tmp_path) is None

    def test_returns_old_version_if_outdated(self, tmp_path):
        """Should return old version if update needed."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("<!-- codeindex:start v0.22.0 -->\n<!-- codeindex:end -->\n")

        with patch("codeindex.claude_md._get_current_version", return_value="0.23.0"):
            assert check_outdated(tmp_path) == "0.22.0"


class TestMarkerPattern:
    """Tests for marker regex pattern."""

    def test_matches_new_format(self):
        """Should match new format with version."""
        text = "<!-- codeindex:start v0.23.0 -->\ncontent\n<!-- codeindex:end -->"
        assert MARKER_PATTERN.search(text) is not None

    def test_matches_old_format(self):
        """Should match old format without version."""
        text = "<!-- codeindex:start -->\ncontent\n<!-- codeindex:end -->"
        assert MARKER_PATTERN.search(text) is not None

    def test_no_match_without_markers(self):
        """Should not match text without markers."""
        text = "# Just a regular CLAUDE.md\nNo markers here"
        assert MARKER_PATTERN.search(text) is None
