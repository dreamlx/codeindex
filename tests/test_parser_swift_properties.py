"""Test suite for Swift property and variable extraction (Story 1.1).

# ruff: noqa: T201

This test file validates Swift property extraction capability:
- Stored properties (var/let)
- Computed properties (get/set)
- Property wrappers (@Published, @State, etc.)
- Lazy properties
- Static/class properties
- Type annotations and optionals

Epic: #23
Story: 1.1
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestSwiftStoredProperties:
    """Test stored property extraction."""

    def test_simple_var_property(self, tmp_path):
        """Should extract simple var property with type."""
        swift_code = dedent("""
            class User {
                var username: String
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Find property symbols
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 1

        prop = properties[0]
        assert prop.name.endswith("username")
        assert "String" in prop.signature

    def test_let_constant_property(self, tmp_path):
        """Should extract let constant property."""
        swift_code = dedent("""
            class Config {
                let maxRetries: Int = 3
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 1
        assert properties[0].name.endswith("maxRetries")
        assert "Int" in properties[0].signature

    def test_optional_type_property(self, tmp_path):
        """Should extract optional type property."""
        swift_code = dedent("""
            class Profile {
                var email: String?
                var age: Int?
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 2

        emails = [p for p in properties if p.name.endswith("email")]
        assert len(emails) == 1
        assert "String?" in emails[0].signature

    def test_multiple_properties_in_class(self, tmp_path):
        """Should extract multiple properties from same class."""
        swift_code = dedent("""
            class Person {
                var firstName: String
                var lastName: String
                let id: UUID
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 3

        # Extract simple names without class prefix
        prop_names = {p.name.split(".")[-1] for p in properties}
        assert prop_names == {"firstName", "lastName", "id"}

    def test_properties_in_struct(self, tmp_path):
        """Should extract properties from struct."""
        swift_code = dedent("""
            struct Point {
                var x: Double
                var y: Double
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 2


class TestSwiftComputedProperties:
    """Test computed property extraction."""

    def test_computed_property_get_only(self, tmp_path):
        """Should extract computed property with getter."""
        swift_code = dedent("""
            class User {
                var firstName: String
                var lastName: String

                var fullName: String {
                    return firstName + " " + lastName
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
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 3  # firstName, lastName, fullName

        computed = [p for p in properties if p.name.endswith("fullName")]
        assert len(computed) == 1
        assert "String" in computed[0].signature

    def test_computed_property_get_set(self, tmp_path):
        """Should extract computed property with getter and setter."""
        swift_code = dedent("""
            class Temperature {
                private var celsius: Double = 0

                var fahrenheit: Double {
                    get {
                        return celsius * 9/5 + 32
                    }
                    set {
                        celsius = (newValue - 32) * 5/9
                    }
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
        properties = [s for s in result.symbols if s.kind == "property"]

        fahrenheit = [p for p in properties if p.name.endswith("fahrenheit")]
        assert len(fahrenheit) == 1


class TestSwiftPropertyWrappers:
    """Test property wrapper extraction (@Published, @State, etc.)."""

    def test_published_property_wrapper(self, tmp_path):
        """Should extract @Published property wrapper."""
        swift_code = dedent("""
            import Combine

            class ViewModel {
                @Published var isLoggedIn: Bool = false
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1

        published = [p for p in properties if p.name.endswith("isLoggedIn")]
        assert len(published) == 1
        # Should capture @Published in signature or attributes
        assert "@Published" in published[0].signature or "Published" in published[0].signature

    def test_state_property_wrapper(self, tmp_path):
        """Should extract @State property wrapper."""
        swift_code = dedent("""
            import SwiftUI

            struct LoginView {
                @State private var showAlert = false
                @State var username: String = ""
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 2

        state_props = [p for p in properties if "@State" in p.signature or "State" in p.signature]
        assert len(state_props) >= 1


class TestSwiftLazyProperties:
    """Test lazy property extraction."""

    def test_lazy_property(self, tmp_path):
        """Should extract lazy property."""
        swift_code = dedent("""
            class DataManager {
                lazy var expensiveResource = ExpensiveClass()
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1

        lazy = [p for p in properties if p.name.endswith("expensiveResource")]
        assert len(lazy) == 1
        # Should capture 'lazy' keyword
        assert "lazy" in lazy[0].signature.lower()


class TestSwiftStaticProperties:
    """Test static and class property extraction."""

    def test_static_property(self, tmp_path):
        """Should extract static property."""
        swift_code = dedent("""
            class Config {
                static let apiKey: String = "abc123"
                static var timeout: Int = 30
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 2

        # Should capture 'static' modifier
        static_props = [p for p in properties if "static" in p.signature.lower()]
        assert len(static_props) >= 1

    def test_class_property(self, tmp_path):
        """Should extract class property."""
        swift_code = dedent("""
            class Vehicle {
                class var maxSpeed: Int {
                    return 100
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
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1


class TestSwiftPropertyVisibility:
    """Test property visibility modifiers (private, public, etc.)."""

    def test_private_property(self, tmp_path):
        """Should extract private property."""
        swift_code = dedent("""
            class Account {
                private var balance: Double = 0
                public var name: String = ""
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 2

        # Should capture visibility modifiers
        private_props = [p for p in properties if "private" in p.signature.lower()]
        assert len(private_props) >= 1


class TestSwiftPropertyEdgeCases:
    """Test edge cases for property extraction."""

    def test_property_with_didset_willset(self, tmp_path):
        """Should handle property observers (didSet, willSet)."""
        swift_code = dedent("""
            class Counter {
                var count: Int = 0 {
                    didSet {
                        // Property observer logic
                    }
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
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1

    def test_property_line_numbers(self, tmp_path):
        """Should track correct line numbers for properties."""
        swift_code = dedent("""
            class MyClass {
                var prop1: String

                var prop2: Int

                var prop3: Bool
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) == 3

        # Properties should have different line numbers
        line_starts = [p.line_start for p in properties]
        assert len(set(line_starts)) == 3  # All unique
