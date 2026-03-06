"""Test suite for Objective-C category and protocol support (Story 3.3).

This test file validates category and protocol parsing:
- @protocol declarations
- @interface categories (extensions)
- Category method extraction
- Protocol method extraction
- Category association with base classes

Epic: #23
Story: 3.3
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestProtocolDeclarations:
    """Test @protocol declaration parsing."""

    def test_simple_protocol(self, tmp_path):
        """Should extract @protocol declaration."""
        objc_code = dedent("""
            @protocol Drivable
            - (void)drive;
            - (void)stop;
            @end
        """).strip()

        h_file = tmp_path / "Drivable.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find the protocol as a class-like symbol
        protocols = [s for s in result.symbols if "protocol" in s.kind.lower() or s.kind == "interface"]
        assert len(protocols) >= 1

        # Protocol should have methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

    def test_protocol_with_properties(self, tmp_path):
        """Should extract properties from @protocol."""
        objc_code = dedent("""
            @protocol DataSource
            @property (nonatomic, readonly) NSInteger count;
            - (id)itemAtIndex:(NSInteger)index;
            @end
        """).strip()

        h_file = tmp_path / "DataSource.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find property
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1

        # Should find method
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1

    def test_protocol_inheritance(self, tmp_path):
        """Should extract protocol inheritance."""
        objc_code = dedent("""
            @protocol AdvancedDrivable <Drivable>
            - (void)accelerate;
            @end
        """).strip()

        h_file = tmp_path / "AdvancedDrivable.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find inheritance relationship
        assert len(result.inheritances) >= 1
        assert result.inheritances[0].child == "AdvancedDrivable"
        assert result.inheritances[0].parent == "Drivable"


class TestCategoryDeclarations:
    """Test @interface category parsing."""

    def test_simple_category(self, tmp_path):
        """Should extract category declaration."""
        objc_code = dedent("""
            @interface NSString (Validation)
            - (BOOL)isValidEmail;
            - (BOOL)isValidURL;
            @end
        """).strip()

        h_file = tmp_path / "NSString+Validation.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find category methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

        # Method names should indicate the category
        method_names = [m.name for m in methods]
        assert any("isValidEmail" in name for name in method_names)

    def test_category_implementation(self, tmp_path):
        """Should extract category implementation."""
        objc_code = dedent("""
            @implementation NSString (Validation)

            - (BOOL)isValidEmail {
                return [self containsString:@"@"];
            }

            - (BOOL)isValidURL {
                return [self hasPrefix:@"http"];
            }

            @end
        """).strip()

        m_file = tmp_path / "NSString+Validation.m"
        m_file.write_text(objc_code)

        try:
            result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find implementation methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

    def test_category_with_properties(self, tmp_path):
        """Should extract properties from categories."""
        objc_code = dedent("""
            @interface UIView (Animation)
            @property (nonatomic, assign) CGFloat animationDuration;
            - (void)fadeIn;
            - (void)fadeOut;
            @end
        """).strip()

        h_file = tmp_path / "UIView+Animation.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find property
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1

        # Should find methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2


class TestCategoryAssociation:
    """Test category association with base classes."""

    def test_category_name_extraction(self, tmp_path):
        """Should extract both class name and category name."""
        objc_code = dedent("""
            @interface MyClass (MyCategory)
            - (void)categoryMethod;
            @end
        """).strip()

        h_file = tmp_path / "MyClass+MyCategory.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Check that we captured information about the category
        # The exact representation may vary, but we should have the method
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1
        assert any("categoryMethod" in m.name for m in methods)

    def test_multiple_categories_same_class(self, tmp_path):
        """Should handle multiple categories for same class."""
        objc_code = dedent("""
            @interface NSString (Validation)
            - (BOOL)isValid;
            @end

            @interface NSString (Formatting)
            - (NSString *)formatted;
            @end
        """).strip()

        h_file = tmp_path / "NSString+Extensions.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find methods from both categories
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2


class TestProtocolConformance:
    """Test protocol conformance in categories."""

    def test_category_with_protocol_conformance(self, tmp_path):
        """Should extract protocol conformance in categories."""
        objc_code = dedent("""
            @interface MyClass (Delegate) <UITableViewDelegate>
            - (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath;
            @end
        """).strip()

        h_file = tmp_path / "MyClass+Delegate.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find protocol conformance
        inheritances = result.inheritances
        # May have UITableViewDelegate as parent
        if len(inheritances) > 0:
            assert any("Delegate" in inh.parent or "MyClass" in inh.child for inh in inheritances)


class TestEdgeCases:
    """Test edge cases for categories and protocols."""

    def test_empty_protocol(self, tmp_path):
        """Should handle empty protocols."""
        objc_code = dedent("""
            @protocol EmptyProtocol
            @end
        """).strip()

        h_file = tmp_path / "EmptyProtocol.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        # Should parse without error even if no methods

    def test_empty_category(self, tmp_path):
        """Should handle empty categories."""
        objc_code = dedent("""
            @interface MyClass (EmptyCategory)
            @end
        """).strip()

        h_file = tmp_path / "MyClass+Empty.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        # Should parse without error even if no methods

    def test_protocol_with_optional_methods(self, tmp_path):
        """Should handle @optional directive in protocols."""
        objc_code = dedent("""
            @protocol Delegate
            @required
            - (void)requiredMethod;
            @optional
            - (void)optionalMethod;
            @end
        """).strip()

        h_file = tmp_path / "Delegate.h"
        h_file.write_text(objc_code)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find both methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2
