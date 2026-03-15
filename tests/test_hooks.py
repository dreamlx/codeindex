"""
Tests for legacy hooks module re-exports.

Verifies backward compatibility of imports from codeindex.hooks.
"""

from codeindex.hooks import check_outdated, extract_version, inject


class TestLegacyImports:
    """Verify hooks module re-exports work."""

    def test_extract_version_importable(self):
        """extract_version should be importable from hooks."""
        assert callable(extract_version)

    def test_inject_importable(self):
        """inject should be importable from hooks."""
        assert callable(inject)

    def test_check_outdated_importable(self):
        """check_outdated should be importable from hooks."""
        assert callable(check_outdated)
