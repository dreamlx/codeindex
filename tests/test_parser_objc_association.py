"""Test suite for Objective-C header/implementation file association (Story 3.2).

This test file validates .h/.m file pairing and symbol merging:
- Same filename matching (MyClass.h + MyClass.m)
- Symbol merging from @interface and @implementation
- Handling missing pairs (only .h or only .m)
- Graceful degradation
- Association accuracy

Epic: #23
Story: 3.2
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestBasicAssociation:
    """Test basic .h/.m file association."""

    def test_parse_header_file_alone(self, tmp_path):
        """Should parse .h file independently."""
        header = dedent("""
            @interface Calculator : NSObject
            - (NSInteger)add:(NSInteger)a to:(NSInteger)b;
            @end
        """).strip()

        h_file = tmp_path / "Calculator.h"
        h_file.write_text(header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        assert len(result.symbols) >= 1

        # Should find the class
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "Calculator"

    def test_parse_implementation_file_alone(self, tmp_path):
        """Should parse .m file independently."""
        impl = dedent("""
            @implementation Calculator

            - (NSInteger)add:(NSInteger)a to:(NSInteger)b {
                return a + b;
            }

            @end
        """).strip()

        m_file = tmp_path / "Calculator.m"
        m_file.write_text(impl)

        try:
            result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        assert len(result.symbols) >= 1

        # Should find the implementation
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "Calculator" for c in classes)

    def test_header_and_implementation_separate_parsing(self, tmp_path):
        """Should parse .h and .m files separately without errors."""
        header = dedent("""
            @interface Person : NSObject
            @property (nonatomic, strong) NSString *name;
            - (void)greet;
            @end
        """).strip()

        impl = dedent("""
            #import "Person.h"

            @implementation Person

            - (void)greet {
                NSLog(@"Hello, %@", self.name);
            }

            @end
        """).strip()

        h_file = tmp_path / "Person.h"
        m_file = tmp_path / "Person.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            h_result = parse_file(h_file)
            m_result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Both should parse without error
        assert h_result.error is None
        assert m_result.error is None

        # Header should have property declaration
        h_props = [s for s in h_result.symbols if s.kind == "property"]
        assert len(h_props) >= 1

        # Implementation should have method definition
        m_methods = [s for s in m_result.symbols if s.kind == "method"]
        assert len(m_methods) >= 1


class TestSymbolMerging:
    """Test symbol merging between .h and .m files."""

    def test_method_declarations_vs_definitions(self, tmp_path):
        """Header has declarations, implementation has definitions."""
        header = dedent("""
            @interface Math : NSObject
            - (NSInteger)square:(NSInteger)n;
            - (NSInteger)cube:(NSInteger)n;
            @end
        """).strip()

        impl = dedent("""
            @implementation Math

            - (NSInteger)square:(NSInteger)n {
                return n * n;
            }

            - (NSInteger)cube:(NSInteger)n {
                return n * n * n;
            }

            @end
        """).strip()

        h_file = tmp_path / "Math.h"
        m_file = tmp_path / "Math.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            h_result = parse_file(h_file)
            m_result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Header should have method declarations
        h_methods = [s for s in h_result.symbols if s.kind == "method"]
        assert len(h_methods) >= 2

        # Implementation should have method definitions
        m_methods = [s for s in m_result.symbols if s.kind == "method"]
        assert len(m_methods) >= 2

        # Method names should match
        h_names = {m.name.split(".")[-1] for m in h_methods}
        m_names = {m.name.split(".")[-1] for m in m_methods}
        assert "square:" in h_names or "square" in str(h_names)
        assert "square:" in m_names or "square" in str(m_names)

    def test_properties_in_header_only(self, tmp_path):
        """Properties are typically declared in header only."""
        header = dedent("""
            @interface User : NSObject
            @property (nonatomic, copy) NSString *username;
            @property (nonatomic, assign) NSInteger age;
            @end
        """).strip()

        impl = dedent("""
            @implementation User
            @end
        """).strip()

        h_file = tmp_path / "User.h"
        m_file = tmp_path / "User.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            h_result = parse_file(h_file)
            _ = parse_file(m_file)  # Parse to ensure no errors
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Header should have properties
        h_props = [s for s in h_result.symbols if s.kind == "property"]
        assert len(h_props) >= 2

        # Implementation typically has no properties (auto-synthesized)
        # May be 0 or may have synthesized properties depending on parser


class TestMissingPairs:
    """Test handling of missing .h or .m files."""

    def test_header_without_implementation(self, tmp_path):
        """Should handle .h file without corresponding .m."""
        header = dedent("""
            @interface Protocol : NSObject
            - (void)doSomething;
            @end
        """).strip()

        h_file = tmp_path / "Protocol.h"
        h_file.write_text(header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should parse successfully even without .m
        assert result.error is None
        assert len(result.symbols) >= 1

    def test_implementation_without_header(self, tmp_path):
        """Should handle .m file without corresponding .h."""
        impl = dedent("""
            @implementation Helper

            - (void)help {
                // Helper logic
            }

            @end
        """).strip()

        m_file = tmp_path / "Helper.m"
        m_file.write_text(impl)

        try:
            result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should parse successfully even without .h
        assert result.error is None
        assert len(result.symbols) >= 1

    def test_multiple_classes_in_same_file(self, tmp_path):
        """Should handle multiple classes in same file."""
        header = dedent("""
            @interface ClassA : NSObject
            @end

            @interface ClassB : NSObject
            @end
        """).strip()

        h_file = tmp_path / "Multiple.h"
        h_file.write_text(header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find both classes
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 2

        class_names = {c.name for c in classes}
        assert "ClassA" in class_names
        assert "ClassB" in class_names


class TestEdgeCases:
    """Test edge cases for file association."""

    def test_different_class_names_in_h_and_m(self, tmp_path):
        """Should handle .h and .m with different class names."""
        header = dedent("""
            @interface PublicAPI : NSObject
            @end
        """).strip()

        impl = dedent("""
            @implementation InternalImplementation
            @end
        """).strip()

        h_file = tmp_path / "API.h"
        m_file = tmp_path / "API.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            h_result = parse_file(h_file)
            m_result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Both should parse independently
        assert h_result.error is None
        assert m_result.error is None

        # Should find different class names
        h_classes = [s.name for s in h_result.symbols if s.kind == "class"]
        m_classes = [s.name for s in m_result.symbols if s.kind == "class"]

        assert "PublicAPI" in h_classes
        assert "InternalImplementation" in m_classes

    def test_private_methods_in_implementation(self, tmp_path):
        """Implementation may have private methods not in header."""
        header = dedent("""
            @interface Calculator : NSObject
            - (NSInteger)calculate:(NSInteger)value;
            @end
        """).strip()

        impl = dedent("""
            @implementation Calculator

            - (NSInteger)calculate:(NSInteger)value {
                return [self privateHelper:value];
            }

            - (NSInteger)privateHelper:(NSInteger)n {
                return n * 2;
            }

            @end
        """).strip()

        h_file = tmp_path / "Calculator.h"
        m_file = tmp_path / "Calculator.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            h_result = parse_file(h_file)
            m_result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Header should have 1 public method
        h_methods = [s for s in h_result.symbols if s.kind == "method"]
        assert len(h_methods) >= 1

        # Implementation should have 2 methods (public + private)
        m_methods = [s for s in m_result.symbols if s.kind == "method"]
        assert len(m_methods) >= 2

    def test_import_statement_in_implementation(self, tmp_path):
        """Implementation should import header."""
        impl = dedent("""
            #import "Calculator.h"

            @implementation Calculator
            @end
        """).strip()

        m_file = tmp_path / "Calculator.m"
        m_file.write_text(impl)

        try:
            result = parse_file(m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find the import
        imports = [imp.module for imp in result.imports]
        assert any("Calculator" in imp for imp in imports)
