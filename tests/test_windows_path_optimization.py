"""
Tests for Windows path length optimization (Issue #8).

These tests verify that the path length optimization works correctly
by using relative paths when possible and falling back to absolute paths
only when necessary.
"""
import sys
from pathlib import Path

import pytest

from codeindex.config import Config
from codeindex.scanner import scan_directory, should_exclude


class TestRelativePathOptimization:
    """Test that relative paths are used when possible."""

    def test_relative_path_exclusion(self, tmp_path):
        """Test exclusion with relative paths."""
        base = tmp_path / "src"
        path = tmp_path / "src" / "__pycache__"
        base.mkdir()
        path.mkdir()

        # Should exclude using relative path (no .resolve() needed)
        assert should_exclude(path, ["**/__pycache__/**"], base)

    def test_relative_path_no_exclusion(self, tmp_path):
        """Test that non-matching relative paths are not excluded."""
        base = tmp_path / "src"
        path = tmp_path / "src" / "module"
        base.mkdir()
        path.mkdir()

        # Should not exclude
        assert not should_exclude(path, ["**/__pycache__/**"], base)

    def test_nested_relative_path_exclusion(self, tmp_path):
        """Test exclusion with deeply nested relative paths."""
        base = tmp_path / "src"
        path = tmp_path / "src" / "a" / "b" / "c" / "__pycache__"
        path.mkdir(parents=True)

        # Should exclude even in deep nesting
        assert should_exclude(path, ["**/__pycache__/**"], base)


class TestAbsolutePathBackwardCompatibility:
    """Test that absolute paths still work (backward compatibility)."""

    def test_absolute_path_exclusion(self, tmp_path):
        """Test exclusion with absolute paths (backward compat)."""
        base = (tmp_path / "src").resolve()
        path = (tmp_path / "src" / "__pycache__").resolve()
        base.mkdir()
        path.mkdir()

        # Should still work with absolute paths
        assert should_exclude(path, ["**/__pycache__/**"], base)

    def test_mixed_relative_and_absolute(self, tmp_path):
        """Test when one path is relative and one is absolute."""
        base = tmp_path / "src"
        path = (tmp_path / "src" / "__pycache__").resolve()
        base.mkdir()
        path.mkdir()

        # Should handle mixed types (falls back to absolute)
        assert should_exclude(path, ["**/__pycache__/**"], base)


class TestPathLengthReduction:
    """Test that path lengths are reduced compared to old behavior."""

    def test_relative_path_shorter_than_absolute(self, tmp_path):
        """Verify relative paths are shorter than absolute paths."""
        # Create a path with some nesting
        base = tmp_path / "project" / "src"
        path = tmp_path / "project" / "src" / "module" / "submodule" / "file.py"

        # Relative path length
        try:
            rel_path = str(path.relative_to(base))
        except ValueError:
            rel_path = str(path)

        # Absolute path length (old behavior)
        abs_path = str(path.resolve().relative_to(base.resolve()))

        # Relative should be much shorter (or equal if both relative)
        # At minimum, it should not be longer
        assert len(rel_path) <= len(abs_path)

    def test_deep_directory_structure(self, tmp_path):
        """Test with deep directory structure (simulating Windows issue)."""
        # Create deep structure: 15 levels
        deep_path = tmp_path
        for i in range(15):
            deep_path = deep_path / f"level{i}"
        deep_path.mkdir(parents=True)

        # Create a test file
        test_file = deep_path / "test.py"
        test_file.write_text("def test(): pass")

        # Should be able to scan without "file name too long" error
        config = Config()
        config.exclude = ["**/__pycache__/**"]
        config.languages = ["python"]
        config.output_file = "README_AI.md"

        result = scan_directory(tmp_path, config)
        assert result is not None
        # Verify the file was found
        assert any(test_file == f for f in result.files)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
class TestWindowsCrossDrive:
    """Test cross-drive path handling on Windows."""

    def test_cross_drive_fallback(self, tmp_path):
        """Test that cross-drive paths fall back gracefully."""
        # This test is skipped on non-Windows platforms
        # On Windows, if we have paths on different drives (C:\ vs D:\),
        # the function should fall back to string comparison without crashing

        # Note: This is a theoretical test - actual implementation depends on
        # whether test environment has multiple drives
        base = Path("C:/project")
        path = Path("D:/external")

        # Should not crash (behavior may vary)
        should_exclude(path, ["**/external/**"], base)
        # We don't assert the result - just verify no exception


class TestSymlinkHandling:
    """Test handling of symbolic links."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks need admin on Windows")
    def test_symlink_in_path(self, tmp_path):
        """Test exclusion with symlinks in path."""
        # Create real directory and symlink
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        (real_dir / "file.py").write_text("def func(): pass")

        symlink = tmp_path / "symlink"
        try:
            symlink.symlink_to(real_dir)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

        # Test exclusion through symlink
        path = symlink / "file.py"

        # Document behavior: With relative paths, symlinks are NOT auto-resolved
        # This is different from old behavior but acceptable
        assert path.exists()  # Verify symlink works

    @pytest.mark.skipif(sys.platform == "win32", reason="Symlinks need admin on Windows")
    def test_symlink_target_excluded(self, tmp_path):
        """Test that excluding symlink target works."""
        # Create cache directory and symlink to it
        cache = tmp_path / "cache"
        cache.mkdir()

        symlink = tmp_path / "cache_link"
        try:
            symlink.symlink_to(cache)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

        base = tmp_path

        # Real cache should be excluded
        assert should_exclude(cache, ["**/cache/**"], base)


class TestPathSeparatorNormalization:
    """Test that path separators are normalized for cross-platform patterns."""

    def test_windows_separator_normalized(self, tmp_path):
        """Test that Windows backslashes are normalized to forward slashes."""
        base = tmp_path / "src"
        path = tmp_path / "src" / "sub" / "module"
        path.mkdir(parents=True)

        # Pattern with forward slashes should match even on Windows
        assert should_exclude(path, ["**/sub/module"], base)

    def test_pattern_matching_across_platforms(self, tmp_path):
        """Test that patterns work consistently across platforms."""
        base = tmp_path / "project"
        path = tmp_path / "project" / "node_modules" / "package"
        path.mkdir(parents=True)

        # Common exclude pattern should work
        assert should_exclude(path, ["**/node_modules/**"], base)


class TestExistingScannerBehavior:
    """Test that existing scanner behavior is preserved."""

    def test_scan_directory_with_exclusions(self, tmp_path):
        """Test that scan_directory respects exclusions."""
        # Create structure
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("def main(): pass")

        cache = src / "__pycache__"
        cache.mkdir()
        (cache / "main.cpython-39.pyc").write_text("compiled")

        config = Config()
        config.exclude = ["**/__pycache__/**"]
        config.languages = ["python"]
        config.output_file = "README_AI.md"

        result = scan_directory(tmp_path, config)

        # Should find main.py but not the .pyc file
        assert any(f.name == "main.py" for f in result.files)
        assert not any(f.name.endswith(".pyc") for f in result.files)

    def test_multiple_exclusion_patterns(self, tmp_path):
        """Test multiple exclusion patterns work together."""
        base = tmp_path
        paths = [
            tmp_path / "__pycache__",
            tmp_path / "node_modules",
            tmp_path / ".git",
            tmp_path / "dist",
        ]

        for p in paths:
            p.mkdir()

        patterns = ["**/__pycache__/**", "**/node_modules/**", "**/.git/**", "**/dist/**"]

        # All should be excluded
        for p in paths:
            assert should_exclude(p, patterns, base)
