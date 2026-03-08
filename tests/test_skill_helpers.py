"""
Unit tests for codeindex skill helpers.

Epic #25, Story #27: codeindex-update-guide Skill Implementation
Tests follow TDD Red-Green-Refactor cycle.
"""


from codeindex.skill_helpers import (
    apply_updates,
    create_backup,
    detect_codeindex_config,
    detect_loomgraph_integration,
    detect_project_languages,
    generate_language_table_diff,
    generate_suggestions,
    generate_version_diff,
    rollback_from_backup,
)


class TestDetectProjectLanguages:
    """Tests for project language detection."""

    def test_detect_python_project(self, tmp_path):
        """Should detect Python files."""
        (tmp_path / "main.py").write_text("x = 1")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        languages = detect_project_languages(tmp_path)
        assert "python" in languages

    def test_detect_swift_project(self, tmp_path):
        """Should detect Swift files."""
        (tmp_path / "App.swift").write_text("import UIKit")

        languages = detect_project_languages(tmp_path)
        assert "swift" in languages

    def test_detect_mixed_languages(self, tmp_path):
        """Should detect multiple languages."""
        (tmp_path / "main.py").write_text("x = 1")
        (tmp_path / "App.swift").write_text("import UIKit")
        (tmp_path / "Main.java").write_text("class Main {}")
        (tmp_path / "index.ts").write_text("export default {}")

        languages = detect_project_languages(tmp_path)
        assert len(languages) >= 3
        assert "python" in languages
        assert "swift" in languages
        assert "java" in languages

    def test_detect_empty_project(self, tmp_path):
        """Should return empty list for empty directory."""
        languages = detect_project_languages(tmp_path)
        assert languages == []

    def test_detect_ignores_node_modules(self, tmp_path):
        """Should ignore files in node_modules."""
        node_dir = tmp_path / "node_modules" / "pkg"
        node_dir.mkdir(parents=True)
        (node_dir / "index.js").write_text("module.exports = {}")
        # Only source files should be counted
        (tmp_path / "app.py").write_text("x = 1")

        languages = detect_project_languages(tmp_path)
        assert "python" in languages
        # JavaScript from node_modules should NOT be detected
        assert "javascript" not in languages


class TestDetectCodeindexConfig:
    """Tests for .codeindex.yaml config detection."""

    def test_detect_existing_config(self, tmp_path):
        """Should detect and parse .codeindex.yaml."""
        config_content = (
            "codeindex: 1\n"
            "languages:\n"
            "  - python\n"
            "  - php\n"
            "include:\n"
            "  - src/\n"
        )
        (tmp_path / ".codeindex.yaml").write_text(config_content)

        config = detect_codeindex_config(tmp_path)
        assert config is not None
        assert "python" in config["languages"]
        assert "php" in config["languages"]

    def test_detect_missing_config(self, tmp_path):
        """Should return None when no config exists."""
        config = detect_codeindex_config(tmp_path)
        assert config is None


class TestDetectLoomgraphIntegration:
    """Tests for LoomGraph integration detection."""

    def test_detect_loomgraph_config(self, tmp_path):
        """Should detect LoomGraph configuration."""
        (tmp_path / ".loomgraph.yaml").write_text("endpoint: http://localhost:3020")

        result = detect_loomgraph_integration(tmp_path)
        assert result is True

    def test_no_loomgraph(self, tmp_path):
        """Should return False when no LoomGraph config."""
        result = detect_loomgraph_integration(tmp_path)
        assert result is False


class TestGenerateVersionDiff:
    """Tests for version diff generation."""

    def test_version_diff_with_upgrade(self):
        """Should show version change."""
        diff = generate_version_diff("0.11.0", "0.22.2")
        assert "0.11.0" in diff
        assert "0.22.2" in diff
        assert "-" in diff or "+" in diff  # Should have diff markers

    def test_version_diff_same_version(self):
        """Should indicate no change when versions match."""
        diff = generate_version_diff("0.22.2", "0.22.2")
        assert "no change" in diff.lower() or "same" in diff.lower() or diff == ""

    def test_version_diff_format(self):
        """Should produce readable Markdown format."""
        diff = generate_version_diff("0.11.0", "0.22.2")
        # Should contain markdown formatting
        assert isinstance(diff, str)
        assert len(diff) > 0


class TestGenerateLanguageTableDiff:
    """Tests for language table diff generation."""

    def test_language_table_diff_new_languages(self):
        """Should highlight newly supported languages."""
        old_languages = ["python", "php"]
        new_languages = ["python", "php", "swift", "java"]

        diff = generate_language_table_diff(old_languages, new_languages)
        assert "swift" in diff.lower()
        assert "java" in diff.lower()

    def test_language_table_diff_no_change(self):
        """Should indicate no change when same languages."""
        languages = ["python", "php"]
        diff = generate_language_table_diff(languages, languages)
        assert "no change" in diff.lower() or diff == "" or "same" in diff.lower()


class TestGenerateSuggestions:
    """Tests for personalized suggestion generation."""

    def test_suggestions_for_swift_project(self, tmp_path):
        """Should suggest Swift-specific documentation."""
        profile = {
            "languages": ["swift", "python"],
            "has_codeindex_config": True,
            "has_loomgraph": False,
            "project_path": str(tmp_path),
        }

        suggestions = generate_suggestions(profile, "0.22.2")
        assert len(suggestions) >= 2
        # Should have at least one Swift-related suggestion
        swift_suggestions = [s for s in suggestions if "swift" in s.lower()]
        assert len(swift_suggestions) >= 1

    def test_suggestions_for_loomgraph_project(self, tmp_path):
        """Should suggest LoomGraph-specific tips."""
        profile = {
            "languages": ["python"],
            "has_codeindex_config": True,
            "has_loomgraph": True,
            "project_path": str(tmp_path),
        }

        suggestions = generate_suggestions(profile, "0.22.2")
        assert len(suggestions) >= 2
        loomgraph_suggestions = [s for s in suggestions if "loomgraph" in s.lower()]
        assert len(loomgraph_suggestions) >= 1

    def test_suggestions_minimum_count(self, tmp_path):
        """Should always generate at least 2 suggestions."""
        profile = {
            "languages": ["python"],
            "has_codeindex_config": False,
            "has_loomgraph": False,
            "project_path": str(tmp_path),
        }

        suggestions = generate_suggestions(profile, "0.22.2")
        assert len(suggestions) >= 2

    def test_suggestions_include_version_update(self, tmp_path):
        """Should suggest version update when outdated."""
        profile = {
            "languages": ["python"],
            "has_codeindex_config": True,
            "has_loomgraph": False,
            "project_path": str(tmp_path),
            "current_guide_version": "0.11.0",
        }

        suggestions = generate_suggestions(profile, "0.22.2")
        version_suggestions = [s for s in suggestions if "version" in s.lower() or "update" in s.lower()]
        assert len(version_suggestions) >= 1


class TestApplyUpdates:
    """Tests for applying updates to CLAUDE.md."""

    def test_apply_all_updates(self, tmp_path):
        """Should apply all suggested updates."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Initial\n")

        updates = [
            {"section": "version", "content": "## Version: 0.22.2\n"},
            {"section": "commands", "content": "## Commands\ncodeindex scan\n"},
        ]

        success = apply_updates(claude_md, updates, select_all=True)
        assert success is True
        content = claude_md.read_text()
        assert "0.22.2" in content
        assert "codeindex scan" in content

    def test_apply_selected_updates(self, tmp_path):
        """Should apply only selected updates."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Initial\n")

        updates = [
            {"section": "version", "content": "## Version: 0.22.2\n"},
            {"section": "commands", "content": "## Commands\ncodeindex scan\n"},
        ]

        success = apply_updates(claude_md, updates, selected_indices=[0])
        assert success is True
        content = claude_md.read_text()
        assert "0.22.2" in content
        # Second update should NOT be applied
        assert "codeindex scan" not in content


class TestBackupAndRollback:
    """Tests for backup creation and rollback."""

    def test_create_backup(self, tmp_path):
        """Should create timestamped backup."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Original content")

        backup_path = create_backup(claude_md)
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "Original content"

    def test_rollback_from_backup(self, tmp_path):
        """Should restore from backup."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Original content")

        # Create backup
        backup_path = create_backup(claude_md)

        # Modify file
        claude_md.write_text("Modified content")
        assert claude_md.read_text() == "Modified content"

        # Rollback
        success = rollback_from_backup(claude_md, backup_path)
        assert success is True
        assert claude_md.read_text() == "Original content"

    def test_rollback_missing_backup(self, tmp_path):
        """Should handle missing backup gracefully."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Content")
        fake_backup = tmp_path / "nonexistent.backup"

        success = rollback_from_backup(claude_md, fake_backup)
        assert success is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_detect_languages_with_symlinks(self, tmp_path):
        """Should handle symlinks gracefully."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "main.py").write_text("x = 1")

        # Create symlink
        link = tmp_path / "link"
        try:
            link.symlink_to(real_dir)
            languages = detect_project_languages(tmp_path)
            assert "python" in languages
        except OSError:
            # Symlinks may not be supported on all platforms
            pass

    def test_apply_updates_to_nonexistent_file(self, tmp_path):
        """Should create file if it doesn't exist."""
        claude_md = tmp_path / "new_claude.md"
        updates = [{"section": "test", "content": "# Test\n"}]

        success = apply_updates(claude_md, updates, select_all=True)
        assert success is True
        assert claude_md.exists()
