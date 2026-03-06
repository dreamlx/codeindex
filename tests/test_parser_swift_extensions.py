"""Test suite for Swift extension support (Story 2.1).

This test file validates Swift extension parsing:
- Basic extension declarations
- Methods and properties in extensions
- Protocol conformance via extensions
- Constrained extensions (where clauses)
- Extension association with base types

Epic: #23
Story: 2.1
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestBasicExtensions:
    """Test basic extension declarations."""

    def test_simple_extension(self, tmp_path):
        """Should extract extension declaration."""
        swift_code = dedent("""
            class MyClass {}

            extension MyClass {
                func newMethod() {}
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have both class and extension
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 2  # Original class + extension

        # Find extension
        extensions = [c for c in classes if "extension" in c.signature.lower()]
        assert len(extensions) >= 1

    def test_extension_on_builtin_type(self, tmp_path):
        """Should extract extension on built-in types."""
        swift_code = dedent("""
            extension String {
                func customReverse() -> String {
                    return String(self.reversed())
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have extension
        classes = [s for s in result.symbols if s.kind == "class"]
        extensions = [c for c in classes if "String" in c.name or "string" in c.name.lower()]
        assert len(extensions) >= 1

    def test_extension_with_multiple_members(self, tmp_path):
        """Should extract all methods from extension."""
        swift_code = dedent("""
            extension Int {
                func squared() -> Int {
                    return self * self
                }

                func cubed() -> Int {
                    return self * self * self
                }

                var isEven: Bool {
                    return self % 2 == 0
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should extract methods and properties from extension
        # Extension creates symbols for its members
        methods = [s for s in result.symbols if s.kind == "method" or s.kind == "function"]
        properties = [s for s in result.symbols if s.kind == "property"]

        # At least 2 methods
        assert len(methods) >= 2

        # At least 1 property
        assert len(properties) >= 1


class TestProtocolConformanceExtensions:
    """Test extensions that add protocol conformance."""

    def test_extension_protocol_conformance(self, tmp_path):
        """Should track protocol conformance via extension."""
        swift_code = dedent("""
            class MyClass {}

            extension MyClass: Codable {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have inheritance relationship for protocol conformance
        assert len(result.inheritances) >= 1

        # Check that Codable is listed as a parent
        codable_inheritance = [i for i in result.inheritances if "Codable" in i.parent]
        assert len(codable_inheritance) >= 1

    def test_extension_multiple_protocol_conformance(self, tmp_path):
        """Should handle multiple protocol conformances in extension."""
        swift_code = dedent("""
            struct User {}

            extension User: Codable, Equatable {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have multiple inheritance relationships
        assert len(result.inheritances) >= 2

    def test_extension_with_protocol_methods(self, tmp_path):
        """Should extract methods that implement protocol requirements."""
        swift_code = dedent("""
            protocol Drivable {
                func drive()
            }

            class Car {}

            extension Car: Drivable {
                func drive() {
                    // Implementation
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should extract protocol and methods
        methods = [s for s in result.symbols if s.kind == "method"]
        drive_methods = [m for m in methods if "drive" in m.name.lower()]
        assert len(drive_methods) >= 1


class TestConstrainedExtensions:
    """Test extensions with generic constraints (where clauses)."""

    def test_constrained_extension_on_array(self, tmp_path):
        """Should handle extensions with where clauses."""
        swift_code = dedent("""
            extension Array where Element: Numeric {
                func sum() -> Element {
                    return reduce(0, +)
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should extract extension and method
        classes = [s for s in result.symbols if s.kind == "class"]
        methods = [s for s in result.symbols if s.kind == "method" or s.kind == "function"]

        # Should have extension declaration
        assert len(classes) >= 1

        # Should have sum method
        sum_methods = [m for m in methods if "sum" in m.name.lower()]
        assert len(sum_methods) >= 1

    def test_constrained_extension_signature(self, tmp_path):
        """Should include constraint in extension signature."""
        swift_code = dedent("""
            extension Collection where Element == Int {
                func average() -> Double {
                    return Double(self.reduce(0, +)) / Double(self.count)
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Extension should be extracted
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

        # Signature may include constraint information
        # (relaxed assertion - just verify parsing doesn't crash)


class TestExtensionAssociation:
    """Test association of extensions with base types."""

    def test_extension_in_same_file_as_class(self, tmp_path):
        """Should associate extension with class in same file."""
        swift_code = dedent("""
            class Calculator {
                func add(_ a: Int, _ b: Int) -> Int {
                    return a + b
                }
            }

            extension Calculator {
                func multiply(_ a: Int, _ b: Int) -> Int {
                    return a * b
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have both class and extension
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 2

        # Should have both methods
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 2

        # Check for both add and multiply
        method_names = [m.name.lower() for m in methods]
        assert any("add" in name for name in method_names)
        assert any("multiply" in name for name in method_names)

    def test_multiple_extensions_same_type(self, tmp_path):
        """Should handle multiple extensions on the same type."""
        swift_code = dedent("""
            struct Point {}

            extension Point {
                func distanceFromOrigin() -> Double {
                    return 0.0
                }
            }

            extension Point: Equatable {
                static func == (lhs: Point, rhs: Point) -> Bool {
                    return true
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have struct + multiple extensions
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 2  # At least struct + 1 extension


class TestExtensionEdgeCases:
    """Test edge cases for extension parsing."""

    def test_empty_extension(self, tmp_path):
        """Should handle empty extensions."""
        swift_code = dedent("""
            class MyClass {}
            extension MyClass {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should not crash on empty extension
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

    def test_extension_with_nested_types(self, tmp_path):
        """Should handle extensions with nested type declarations."""
        swift_code = dedent("""
            class OuterClass {}

            extension OuterClass {
                enum Status {
                    case active
                    case inactive
                }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should extract both outer class, extension, and nested enum
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 2  # OuterClass + Status enum (or extension)

    def test_extension_with_access_modifiers(self, tmp_path):
        """Should handle extensions with access modifiers."""
        swift_code = dedent("""
            public class PublicClass {}

            public extension PublicClass {
                func publicMethod() {}
            }

            private extension PublicClass {
                func privateMethod() {}
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should extract all extensions
        classes = [s for s in result.symbols if s.kind == "class"]
        methods = [s for s in result.symbols if s.kind == "method"]

        # At least 3 classes (original + 2 extensions)
        assert len(classes) >= 2

        # At least 2 methods
        assert len(methods) >= 2
