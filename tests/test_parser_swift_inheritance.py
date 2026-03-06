"""Test suite for Swift inheritance relationship tracking (Story 1.3).

This test file validates Swift inheritance extraction:
- Class superclass relationships
- Protocol conformances
- Multiple protocol conformances
- Generic type constraints
- Mixed inheritance scenarios

Epic: #23
Story: 1.3
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestSwiftClassInheritance:
    """Test class inheritance extraction."""

    def test_simple_class_inheritance(self, tmp_path):
        """Should extract simple class inheritance."""
        swift_code = dedent("""
            class Animal {}
            class Dog: Animal {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        assert len(result.inheritances) >= 1

        # Find Dog -> Animal inheritance
        dog_inherits = [i for i in result.inheritances if i.child == "Dog"]
        assert len(dog_inherits) == 1
        assert dog_inherits[0].parent == "Animal"

    def test_multiple_level_inheritance(self, tmp_path):
        """Should track multi-level inheritance."""
        swift_code = dedent("""
            class Animal {}
            class Mammal: Animal {}
            class Dog: Mammal {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        assert len(result.inheritances) >= 2

        # Should track both relationships
        parents = {i.parent for i in result.inheritances}
        assert "Animal" in parents
        assert "Mammal" in parents

    def test_struct_no_inheritance(self, tmp_path):
        """Should handle struct without inheritance."""
        swift_code = dedent("""
            struct Point {
                var x: Int
                var y: Int
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        # Struct with no inheritance should have no inheritance records
        struct_inherits = [i for i in result.inheritances if i.child == "Point"]
        assert len(struct_inherits) == 0


class TestSwiftProtocolConformance:
    """Test protocol conformance tracking."""

    def test_single_protocol_conformance(self, tmp_path):
        """Should track class conforming to single protocol."""
        swift_code = dedent("""
            protocol Drivable {}
            class Car: Drivable {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        assert len(result.inheritances) >= 1

        car_conforms = [i for i in result.inheritances if i.child == "Car"]
        assert len(car_conforms) == 1
        assert car_conforms[0].parent == "Drivable"

    def test_multiple_protocol_conformance(self, tmp_path):
        """Should track class conforming to multiple protocols."""
        swift_code = dedent("""
            protocol A {}
            protocol B {}
            protocol C {}

            class MyClass: A, B, C {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have 3 inheritance records for MyClass
        myclass_conforms = [i for i in result.inheritances if i.child == "MyClass"]
        assert len(myclass_conforms) == 3

        # Check all protocols are tracked
        parents = {i.parent for i in myclass_conforms}
        assert parents == {"A", "B", "C"}

    def test_struct_protocol_conformance(self, tmp_path):
        """Should track struct conforming to protocol."""
        swift_code = dedent("""
            protocol Identifiable {}
            struct User: Identifiable {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        user_conforms = [i for i in result.inheritances if i.child == "User"]
        assert len(user_conforms) == 1
        assert user_conforms[0].parent == "Identifiable"


class TestSwiftMixedInheritance:
    """Test mixed inheritance scenarios (class + protocols)."""

    def test_class_inheritance_and_protocol(self, tmp_path):
        """Should track both class inheritance and protocol conformance."""
        swift_code = dedent("""
            class UIViewController {}
            protocol Delegate {}

            class LoginVC: UIViewController, Delegate {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have 2 inheritance records
        loginvc_inherits = [i for i in result.inheritances if i.child == "LoginVC"]
        assert len(loginvc_inherits) == 2

        parents = {i.parent for i in loginvc_inherits}
        assert "UIViewController" in parents
        assert "Delegate" in parents

    def test_class_multiple_protocols(self, tmp_path):
        """Should handle class with superclass and multiple protocols."""
        swift_code = dedent("""
            class BaseView {}
            protocol A {}
            protocol B {}

            class CustomView: BaseView, A, B {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        customview_inherits = [i for i in result.inheritances if i.child == "CustomView"]
        assert len(customview_inherits) == 3

        parents = {i.parent for i in customview_inherits}
        assert parents == {"BaseView", "A", "B"}


class TestSwiftGenericConstraints:
    """Test generic type constraints in inheritance."""

    def test_generic_class_inheritance(self, tmp_path):
        """Should handle generic class with inheritance."""
        swift_code = dedent("""
            class Storage {}
            class Cache<T>: Storage {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Cache should inherit from Storage
        cache_inherits = [i for i in result.inheritances if i.child == "Cache"]
        assert len(cache_inherits) >= 1

        # Find Storage parent
        storage_parents = [i for i in cache_inherits if i.parent == "Storage"]
        assert len(storage_parents) == 1

    def test_generic_protocol_constraint(self, tmp_path):
        """Should handle generic type with protocol constraint."""
        swift_code = dedent("""
            protocol Codable {}
            class Storage {}

            class Cache<T: Codable>: Storage {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Cache should inherit from Storage (main inheritance)
        cache_inherits = [i for i in result.inheritances if i.child == "Cache"]
        assert len(cache_inherits) >= 1

        # Should find Storage inheritance
        storage_inherit = [i for i in cache_inherits if i.parent == "Storage"]
        assert len(storage_inherit) == 1


class TestSwiftInheritanceEdgeCases:
    """Test edge cases for inheritance tracking."""

    def test_empty_class_no_inheritance(self, tmp_path):
        """Should handle class with no inheritance."""
        swift_code = dedent("""
            class Standalone {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        standalone_inherits = [i for i in result.inheritances if i.child == "Standalone"]
        assert len(standalone_inherits) == 0

    def test_multiple_classes_same_file(self, tmp_path):
        """Should track inheritance for multiple classes in one file."""
        swift_code = dedent("""
            class Base {}
            class Child1: Base {}
            class Child2: Base {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should have 2 inheritance records
        base_children = [i for i in result.inheritances if i.parent == "Base"]
        assert len(base_children) == 2

        children = {i.child for i in base_children}
        assert children == {"Child1", "Child2"}

    def test_protocol_inheritance_chain(self, tmp_path):
        """Should track protocol inheritance chain."""
        swift_code = dedent("""
            protocol A {}
            protocol B: A {}
            protocol C: B {}
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should track protocol inheritance
        assert len(result.inheritances) >= 2

        # B inherits from A
        b_inherits = [i for i in result.inheritances if i.child == "B"]
        assert len(b_inherits) >= 1

        # C inherits from B
        c_inherits = [i for i in result.inheritances if i.child == "C"]
        assert len(c_inherits) >= 1
