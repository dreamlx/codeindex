"""Tests for _update_gitignore in cli_config."""

from codeindex.cli_config import _update_gitignore


class TestUpdateGitignore:
    def test_creates_gitignore_when_absent(self, tmp_path):
        result = _update_gitignore(tmp_path)
        assert result is True
        content = (tmp_path / ".gitignore").read_text()
        assert "README_AI.md" in content

    def test_appends_to_existing_gitignore(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("*.pyc\n__pycache__/\n")
        result = _update_gitignore(tmp_path)
        assert result is True
        content = gi.read_text()
        assert "*.pyc" in content
        assert "README_AI.md" in content

    def test_skips_when_already_present(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("README_AI.md\n")
        result = _update_gitignore(tmp_path)
        assert result is False
        assert gi.read_text().count("README_AI.md") == 1

    def test_includes_comment(self, tmp_path):
        _update_gitignore(tmp_path)
        content = (tmp_path / ".gitignore").read_text()
        assert "codeindex" in content

    def test_preserves_existing_content_without_trailing_newline(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("*.log")
        _update_gitignore(tmp_path)
        content = gi.read_text()
        assert content.startswith("*.log")
        assert "README_AI.md" in content
