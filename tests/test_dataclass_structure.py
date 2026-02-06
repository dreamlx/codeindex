"""Tests for data structure definitions.

Epic 10, Story 10.3: LoomGraph Integration - Data Structures
Tests for new data classes: Inheritance
Tests for extended data classes: Import (with alias)
Tests for updated ParseResult
"""

from pathlib import Path

from codeindex.parser import Import, Inheritance, ParseResult


class TestInheritanceDataclass:
    """Test Inheritance data class."""

    def test_inheritance_creation(self):
        """Test creating Inheritance instance."""
        inh = Inheritance(child="AdminUser", parent="BaseUser")
        assert inh.child == "AdminUser"
        assert inh.parent == "BaseUser"

    def test_inheritance_equality(self):
        """Test Inheritance equality."""
        inh1 = Inheritance("AdminUser", "BaseUser")
        inh2 = Inheritance("AdminUser", "BaseUser")
        assert inh1 == inh2

    def test_inheritance_to_dict(self):
        """Test Inheritance to_dict() method."""
        inh = Inheritance("AdminUser", "BaseUser")
        d = inh.to_dict()
        assert d == {"child": "AdminUser", "parent": "BaseUser"}

    def test_inheritance_different_instances(self):
        """Test different Inheritance instances."""
        inh1 = Inheritance("AdminUser", "BaseUser")
        inh2 = Inheritance("GuestUser", "BaseUser")
        assert inh1 != inh2


class TestImportWithAlias:
    """Test Import data class with alias field."""

    def test_import_with_alias(self):
        """Test Import with alias."""
        imp = Import(module="numpy", names=[], is_from=False, alias="np")
        assert imp.module == "numpy"
        assert imp.alias == "np"

    def test_import_without_alias(self):
        """Test Import without alias (backward compatibility)."""
        imp = Import(module="os", names=[], is_from=False)
        assert imp.alias is None

    def test_import_from_with_alias(self):
        """Test from-import with alias."""
        imp = Import(module="datetime", names=["datetime"], is_from=True, alias="dt")
        assert imp.alias == "dt"

    def test_import_to_dict_with_alias(self):
        """Test Import.to_dict() includes alias."""
        imp = Import(module="numpy", names=[], is_from=False, alias="np")
        d = imp.to_dict()
        assert "alias" in d
        assert d["alias"] == "np"

    def test_import_to_dict_without_alias(self):
        """Test Import.to_dict() with None alias."""
        imp = Import(module="os", names=[], is_from=False)
        d = imp.to_dict()
        assert "alias" in d
        assert d["alias"] is None


class TestParseResultWithInheritances:
    """Test ParseResult with inheritances field."""

    def test_parse_result_with_inheritances(self):
        """Test ParseResult with inheritances."""
        result = ParseResult(
            path=Path("test.py"),
            symbols=[],
            imports=[],
            inheritances=[
                Inheritance("AdminUser", "BaseUser"),
                Inheritance("AdminUser", "PermissionMixin"),
            ],
        )
        assert len(result.inheritances) == 2

    def test_parse_result_empty_inheritances(self):
        """Test ParseResult with empty inheritances (backward compatibility)."""
        result = ParseResult(
            path=Path("test.py"),
            symbols=[],
            imports=[],
        )
        assert result.inheritances == []

    def test_parse_result_to_dict_with_inheritances(self):
        """Test ParseResult.to_dict() includes inheritances."""
        result = ParseResult(
            path=Path("test.py"),
            symbols=[],
            imports=[],
            inheritances=[Inheritance("AdminUser", "BaseUser")],
        )
        d = result.to_dict()
        assert "inheritances" in d
        assert len(d["inheritances"]) == 1
        assert d["inheritances"][0] == {"child": "AdminUser", "parent": "BaseUser"}


class TestBackwardCompatibility:
    """Test backward compatibility of data structures."""

    def test_import_default_alias(self):
        """Test Import created without alias parameter."""
        imp = Import("os", [], False)
        assert imp.alias is None

    def test_parse_result_default_inheritances(self):
        """Test ParseResult created without inheritances parameter."""
        result = ParseResult(path=Path("test.py"))
        assert result.inheritances == []
        assert result.symbols == []
        assert result.imports == []
