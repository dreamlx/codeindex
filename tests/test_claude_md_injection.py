"""Unit tests for CLAUDE.md injection (inject_claude_md / has_claude_md_injection)."""

import pytest

from codeindex.init_wizard import (
    CLAUDE_MD_MARKER_END,
    CLAUDE_MD_MARKER_START,
    CLAUDE_MD_SECTION,
    has_claude_md_injection,
    inject_claude_md,
)


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory."""
    d = tmp_path / "project"
    d.mkdir()
    return d


class TestInjectClaudeMd:
    """Tests for inject_claude_md()."""

    def test_creates_file_when_missing(self, project_dir):
        """Should create CLAUDE.md when it doesn't exist."""
        result = inject_claude_md(project_dir)
        assert result == project_dir / "CLAUDE.md"
        assert result.exists()

    def test_created_file_has_section(self, project_dir):
        """Newly created file should contain the full codeindex section."""
        inject_claude_md(project_dir)
        content = (project_dir / "CLAUDE.md").read_text()
        assert CLAUDE_MD_MARKER_START in content
        assert CLAUDE_MD_MARKER_END in content
        assert "Always read README_AI.md" in content
        assert "codeindex status" in content
        assert "codeindex scan-all" in content

    def test_prepends_to_existing_file(self, project_dir):
        """Should prepend section to existing CLAUDE.md."""
        existing = "# My Project\n\nExisting content here.\n"
        (project_dir / "CLAUDE.md").write_text(existing)

        inject_claude_md(project_dir)
        content = (project_dir / "CLAUDE.md").read_text()

        # Section should come first
        marker_pos = content.index(CLAUDE_MD_MARKER_START)
        existing_pos = content.index("Existing content here.")
        assert marker_pos < existing_pos

        # Original content preserved
        assert "# My Project" in content
        assert "Existing content here." in content

    def test_idempotent_replace_between_markers(self, project_dir):
        """Re-running should replace section, not duplicate it."""
        inject_claude_md(project_dir)
        inject_claude_md(project_dir)

        content = (project_dir / "CLAUDE.md").read_text()
        assert content.count(CLAUDE_MD_MARKER_START) == 1
        assert content.count(CLAUDE_MD_MARKER_END) == 1

    def test_idempotent_preserves_surrounding_content(self, project_dir):
        """Idempotent update should preserve content around the section."""
        existing = "# My Project\n\nExisting content here.\n"
        (project_dir / "CLAUDE.md").write_text(existing)

        inject_claude_md(project_dir)
        inject_claude_md(project_dir)

        content = (project_dir / "CLAUDE.md").read_text()
        assert "Existing content here." in content
        assert content.count(CLAUDE_MD_MARKER_START) == 1

    def test_returns_path(self, project_dir):
        """Should return the Path to CLAUDE.md."""
        result = inject_claude_md(project_dir)
        assert isinstance(result, type(project_dir / "CLAUDE.md"))
        assert result.name == "CLAUDE.md"

    def test_empty_existing_file(self, project_dir):
        """Should handle empty CLAUDE.md gracefully."""
        (project_dir / "CLAUDE.md").write_text("")
        inject_claude_md(project_dir)
        content = (project_dir / "CLAUDE.md").read_text()
        assert CLAUDE_MD_MARKER_START in content

    def test_whitespace_only_file(self, project_dir):
        """Should handle whitespace-only CLAUDE.md gracefully."""
        (project_dir / "CLAUDE.md").write_text("   \n\n  \n")
        inject_claude_md(project_dir)
        content = (project_dir / "CLAUDE.md").read_text()
        assert CLAUDE_MD_MARKER_START in content


class TestHasClaudeMdInjection:
    """Tests for has_claude_md_injection()."""

    def test_returns_false_when_no_file(self, project_dir):
        """Should return False when CLAUDE.md doesn't exist."""
        assert has_claude_md_injection(project_dir) is False

    def test_returns_false_when_no_marker(self, project_dir):
        """Should return False when CLAUDE.md exists but has no marker."""
        (project_dir / "CLAUDE.md").write_text("# My Project\n\nNo markers.\n")
        assert has_claude_md_injection(project_dir) is False

    def test_returns_true_after_injection(self, project_dir):
        """Should return True after inject_claude_md() runs."""
        inject_claude_md(project_dir)
        assert has_claude_md_injection(project_dir) is True

    def test_returns_true_with_marker_in_existing(self, project_dir):
        """Should return True when marker exists in file."""
        content = f"# Project\n\n{CLAUDE_MD_SECTION}\n\nOther stuff.\n"
        (project_dir / "CLAUDE.md").write_text(content)
        assert has_claude_md_injection(project_dir) is True
