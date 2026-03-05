r"""Test suite for Swift property wrapper detection (Story 2.3).

This test file validates Swift property wrapper parsing:
- Common SwiftUI property wrappers (@State, @Binding, @Published, @ObservedObject)
- Property wrapper parameters (@Environment(\.colorScheme))
- Property wrapper metadata in signatures
- Multiple property wrappers on same property

Epic: #23
Story: 2.3
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestCommonPropertyWrappers:
    """Test detection of common SwiftUI property wrappers."""

    def test_state_wrapper(self, tmp_path):
        """Should detect @State property wrapper."""
        swift_code = dedent("""
            class MyView {
                @State var isActive: Bool = false
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Find properties
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 1

        # Signature should include @State
        prop = properties[0]
        assert "@State" in prop.signature or "@state" in prop.signature.lower()

    def test_binding_wrapper(self, tmp_path):
        """Should detect @Binding property wrapper."""
        swift_code = dedent("""
            struct DetailView {
                @Binding var selectedItem: String
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

        # Signature should include @Binding
        assert "@Binding" in properties[0].signature

    def test_published_wrapper(self, tmp_path):
        """Should detect @Published property wrapper."""
        swift_code = dedent("""
            class ViewModel {
                @Published var count: Int = 0
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

        # Signature should include @Published
        assert "@Published" in properties[0].signature

    def test_observed_object_wrapper(self, tmp_path):
        """Should detect @ObservedObject property wrapper."""
        swift_code = dedent("""
            struct ContentView {
                @ObservedObject var viewModel: ViewModel
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

        # Signature should include @ObservedObject
        assert "@ObservedObject" in properties[0].signature


class TestParameterizedWrappers:
    """Test property wrappers with parameters."""

    def test_environment_wrapper_with_keypath(self, tmp_path):
        """Should detect @Environment with key path parameter."""
        swift_code = dedent("""
            struct MyView {
                @Environment(\\.colorScheme) var colorScheme
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

        # Signature should include @Environment with parameter
        sig = properties[0].signature
        assert "@Environment" in sig
        # Parameter may or may not be included depending on implementation
        # Just verify wrapper is detected

    def test_appstorage_wrapper_with_key(self, tmp_path):
        """Should detect @AppStorage with key parameter."""
        swift_code = dedent("""
            struct SettingsView {
                @AppStorage("username") var username: String = ""
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

        # Signature should include @AppStorage
        assert "@AppStorage" in properties[0].signature

    def test_fetchrequest_wrapper(self, tmp_path):
        """Should detect @FetchRequest wrapper with complex parameters."""
        swift_code = dedent("""
            struct TodoListView {
                @FetchRequest(
                    sortDescriptors: [SortDescriptor(\\.date)]
                ) var items: FetchedResults<TodoItem>
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

        # Signature should include @FetchRequest
        assert "@FetchRequest" in properties[0].signature


class TestMultipleWrappers:
    """Test properties with multiple attributes."""

    def test_property_with_access_modifier_and_wrapper(self, tmp_path):
        """Should handle both access modifier and property wrapper."""
        swift_code = dedent("""
            class MyClass {
                private @State var isHidden: Bool = false
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

        # Signature should include both private and @State
        sig = properties[0].signature
        assert "private" in sig.lower()
        assert "@State" in sig

    def test_multiple_properties_with_different_wrappers(self, tmp_path):
        """Should handle multiple properties with different wrappers."""
        swift_code = dedent("""
            class ViewModel {
                @Published var title: String = ""
                @Published var count: Int = 0
                @State var isLoading: Bool = false
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
        assert len(properties) >= 3

        # Count wrappers
        published_props = [p for p in properties if "@Published" in p.signature]
        state_props = [p for p in properties if "@State" in p.signature]

        assert len(published_props) >= 2
        assert len(state_props) >= 1


class TestEdgeCases:
    """Test edge cases for property wrapper detection."""

    def test_property_without_wrapper(self, tmp_path):
        """Should handle properties without wrappers."""
        swift_code = dedent("""
            class MyClass {
                var normalProperty: String = ""
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

        # Signature should not have @ symbols (except possible type annotations)
        sig = properties[0].signature
        # Should not start with @
        assert not sig.strip().startswith("@")

    def test_custom_property_wrapper(self, tmp_path):
        """Should handle custom property wrappers."""
        swift_code = dedent("""
            class MyClass {
                @UserDefault(key: "theme") var theme: String
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

        # Signature should include custom wrapper
        assert "@UserDefault" in properties[0].signature

    def test_wrapper_with_static_property(self, tmp_path):
        """Should handle wrappers on static properties."""
        swift_code = dedent("""
            class Config {
                @AppStorage("apiKey") static var apiKey: String = ""
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

        # Signature should include both @AppStorage and static
        sig = properties[0].signature
        assert "@AppStorage" in sig
        assert "static" in sig.lower()
