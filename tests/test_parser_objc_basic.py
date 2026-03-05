"""Test suite for Objective-C parser basic functionality (Story 3.1).

This test file validates Objective-C parser infrastructure:
- @interface declaration parsing
- @implementation parsing
- Method extraction (instance and class methods)
- Property extraction
- Basic type handling

Epic: #23
Story: 3.1
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestInterfaceDeclarations:
    """Test @interface declaration parsing."""

    def test_simple_interface(self, tmp_path):
        """Should extract @interface declaration as class symbol."""
        objc_code = dedent("""
            @interface MyClass : NSObject
            @end
        """).strip()

        objc_file = tmp_path / "MyClass.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find the interface
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "MyClass"
        assert "NSObject" in classes[0].signature or "MyClass" in classes[0].signature

    def test_interface_with_properties(self, tmp_path):
        """Should extract properties from @interface."""
        objc_code = dedent("""
            @interface Person : NSObject
            @property (nonatomic, strong) NSString *name;
            @property (nonatomic, assign) NSInteger age;
            @end
        """).strip()

        objc_file = tmp_path / "Person.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find properties
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 2

        prop_names = [p.name for p in properties]
        assert "name" in prop_names or "Person.name" in prop_names
        assert "age" in prop_names or "Person.age" in prop_names

    def test_interface_with_instance_methods(self, tmp_path):
        """Should extract instance methods from @interface."""
        objc_code = dedent("""
            @interface Calculator : NSObject
            - (NSInteger)add:(NSInteger)a to:(NSInteger)b;
            - (void)reset;
            @end
        """).strip()

        objc_file = tmp_path / "Calculator.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

        method_names = [m.name for m in methods]
        # Method names might be "add:to:" or "Calculator.add:to:"
        assert any("add" in name for name in method_names)
        assert any("reset" in name for name in method_names)

    def test_interface_with_class_methods(self, tmp_path):
        """Should extract class methods (+) from @interface."""
        objc_code = dedent("""
            @interface Singleton : NSObject
            + (instancetype)sharedInstance;
            + (void)configure;
            @end
        """).strip()

        objc_file = tmp_path / "Singleton.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find class methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

        # Class methods might have "+" in signature
        method_sigs = [m.signature for m in methods]
        assert any("sharedInstance" in sig for sig in method_sigs)
        assert any("configure" in sig for sig in method_sigs)


class TestImplementationParsing:
    """Test @implementation parsing."""

    def test_simple_implementation(self, tmp_path):
        """Should extract @implementation as class symbol."""
        objc_code = dedent("""
            @implementation MyClass
            @end
        """).strip()

        objc_file = tmp_path / "MyClass.m"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find the implementation
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "MyClass" for c in classes)

    def test_implementation_with_methods(self, tmp_path):
        """Should extract method implementations."""
        objc_code = dedent("""
            @implementation Calculator

            - (NSInteger)add:(NSInteger)a to:(NSInteger)b {
                return a + b;
            }

            - (void)reset {
                // Reset logic
            }

            @end
        """).strip()

        objc_file = tmp_path / "Calculator.m"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

        method_names = [m.name for m in methods]
        assert any("add" in name for name in method_names)
        assert any("reset" in name for name in method_names)

    def test_implementation_with_class_methods(self, tmp_path):
        """Should extract class method implementations (+)."""
        objc_code = dedent("""
            @implementation Singleton

            + (instancetype)sharedInstance {
                static Singleton *instance = nil;
                return instance;
            }

            @end
        """).strip()

        objc_file = tmp_path / "Singleton.m"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find class method
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1
        assert any("sharedInstance" in m.name for m in methods)


class TestImportStatements:
    """Test import/include statement parsing."""

    def test_import_foundation(self, tmp_path):
        """Should extract #import statements."""
        objc_code = dedent("""
            #import <Foundation/Foundation.h>
            #import "MyClass.h"

            @interface Test : NSObject
            @end
        """).strip()

        objc_file = tmp_path / "Test.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find imports
        assert len(result.imports) >= 1
        import_modules = [imp.module for imp in result.imports]
        # Might be "Foundation/Foundation.h" or "Foundation"
        assert any("Foundation" in mod for mod in import_modules) or \
               any("MyClass" in mod for mod in import_modules)


class TestInheritanceExtraction:
    """Test inheritance relationship extraction."""

    def test_simple_inheritance(self, tmp_path):
        """Should extract superclass relationship."""
        objc_code = dedent("""
            @interface Dog : Animal
            @end
        """).strip()

        objc_file = tmp_path / "Dog.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find inheritance relationship
        assert len(result.inheritances) >= 1
        assert result.inheritances[0].child == "Dog"
        assert result.inheritances[0].parent == "Animal"

    def test_protocol_conformance(self, tmp_path):
        """Should extract protocol conformance."""
        objc_code = dedent("""
            @interface MyView : UIView <UITableViewDelegate, UITableViewDataSource>
            @end
        """).strip()

        objc_file = tmp_path / "MyView.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find protocol conformances
        assert len(result.inheritances) >= 1
        # Should have UIView as parent and protocols
        parent_names = [inh.parent for inh in result.inheritances]
        assert "UIView" in parent_names or \
               any("Delegate" in p for p in parent_names) or \
               any("DataSource" in p for p in parent_names)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_file(self, tmp_path):
        """Should handle empty Objective-C files."""
        objc_file = tmp_path / "Empty.h"
        objc_file.write_text("")

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        assert len(result.symbols) == 0

    def test_syntax_error_handling(self, tmp_path):
        """Should handle syntax errors gracefully."""
        objc_code = "@interface BrokenClass"  # Missing @end

        objc_file = tmp_path / "Broken.h"
        objc_file.write_text(objc_code)

        try:
            result = parse_file(objc_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should either report error or return partial results
        # Exact behavior depends on tree-sitter-objc error recovery
        assert result is not None

    def test_file_extension_recognition(self, tmp_path):
        """Should recognize both .h and .m extensions."""
        header = tmp_path / "Test.h"
        header.write_text("@interface Test : NSObject\n@end")

        impl = tmp_path / "Test.m"
        impl.write_text("@implementation Test\n@end")

        try:
            header_result = parse_file(header)
            impl_result = parse_file(impl)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Both should parse without error
        assert header_result.error is None
        assert impl_result.error is None

        # Both should find the class
        assert len(header_result.symbols) >= 1
        assert len(impl_result.symbols) >= 1
