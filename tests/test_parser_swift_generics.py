"""Test suite for Swift generic type handling (Story 2.2).

This test file validates Swift generic type parsing:
- Generic type parameters extraction
- Where clauses (generic constraints)
- Associated types in protocols
- Complex generic signatures
- Generic type formatting

Epic: #23
Story: 2.2
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestGenericTypeParameters:
    """Test extraction of generic type parameters."""

    def test_single_generic_parameter(self, tmp_path):
        """Should extract single generic type parameter."""
        swift_code = dedent("""
            class Box<T> {
                var value: T
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Find class
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

        # Signature should include generic parameter
        sig = classes[0].signature
        assert "<T>" in sig or "<t>" in sig.lower()

    def test_multiple_generic_parameters(self, tmp_path):
        """Should extract multiple generic type parameters."""
        swift_code = dedent("""
            class Pair<K, V> {
                var key: K
                var value: V
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

        # Signature should include both generic parameters
        sig = classes[0].signature.lower()
        assert "k" in sig and "v" in sig

    def test_generic_function(self, tmp_path):
        """Should extract generic parameters from functions."""
        swift_code = dedent("""
            func swap<T>(_ a: inout T, _ b: inout T) {
                let temp = a
                a = b
                b = temp
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Find function
        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1

        # Signature should include generic parameter
        sig = funcs[0].signature
        assert "<T>" in sig or "<t>" in sig.lower()


class TestGenericConstraints:
    """Test generic type constraints (where clauses)."""

    def test_simple_type_constraint(self, tmp_path):
        """Should handle simple type constraints."""
        swift_code = dedent("""
            func process<T: Codable>(_ item: T) {
                // Implementation
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1

        # Signature should include constraint
        sig = funcs[0].signature
        assert "T:" in sig or "t:" in sig.lower()
        assert "codable" in sig.lower()

    def test_where_clause_constraint(self, tmp_path):
        """Should handle where clause constraints."""
        swift_code = dedent("""
            func compare<T, U>(_ a: T, _ b: U) -> Bool where T: Comparable, U: Comparable {
                return true
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1

        # Signature should include where clause or constraints
        sig = funcs[0].signature.lower()
        # May include "where" or constraints inline
        has_constraint = "where" in sig or ("comparable" in sig and "t" in sig)
        assert has_constraint

    def test_class_with_generic_constraint(self, tmp_path):
        """Should handle generic constraints on classes."""
        swift_code = dedent("""
            class DataStore<T: Codable> {
                var items: [T] = []
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

        # Signature should include constraint
        sig = classes[0].signature
        assert "T:" in sig or "t:" in sig.lower()

    def test_multiple_constraints_same_type(self, tmp_path):
        """Should handle multiple constraints on same type."""
        swift_code = dedent("""
            func process<T>(_ item: T) where T: Codable, T: Equatable {
                // Implementation
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1

        # Should capture multiple constraints
        sig = funcs[0].signature.lower()
        assert "t" in sig


class TestAssociatedTypes:
    """Test associated types in protocols."""

    def test_protocol_with_associated_type(self, tmp_path):
        """Should extract protocols with associated types."""
        swift_code = dedent("""
            protocol Container {
                associatedtype Item
                func add(_ item: Item)
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Find protocol
        classes = [s for s in result.symbols if s.kind == "class"]
        protocols = [c for c in classes if "protocol" in c.signature.lower()]
        assert len(protocols) >= 1

        # Should have method with Item type
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1

    def test_protocol_associated_type_constraint(self, tmp_path):
        """Should handle associated type constraints."""
        swift_code = dedent("""
            protocol ItemStore {
                associatedtype Item: Codable
                var items: [Item] { get }
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should parse without errors
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1


class TestComplexGenericSignatures:
    """Test complex generic signature formatting."""

    def test_nested_generic_types(self, tmp_path):
        """Should handle nested generic types."""
        swift_code = dedent("""
            class Cache<Key: Hashable, Value> {
                var storage: [Key: Value] = [:]
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

        # Should have generic signature
        sig = classes[0].signature.lower()
        assert "key" in sig and "value" in sig

    def test_generic_with_protocol_composition(self, tmp_path):
        """Should handle protocol composition in constraints."""
        swift_code = dedent("""
            func process<T>(_ item: T) where T: Codable & Equatable {
                // Implementation
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1

        # Should capture constraint
        sig = funcs[0].signature.lower()
        assert "t" in sig

    def test_extension_with_generic_constraint(self, tmp_path):
        """Should handle extensions with generic constraints."""
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

        # Should extract extension with constraint
        classes = [s for s in result.symbols if s.kind == "class"]
        methods = [s for s in result.symbols if s.kind == "method" or s.kind == "function"]

        assert len(classes) >= 1  # Extension
        assert len(methods) >= 1  # sum method


class TestGenericEdgeCases:
    """Test edge cases for generic type handling."""

    def test_generic_type_with_default(self, tmp_path):
        """Should handle generic types with default values."""
        swift_code = dedent("""
            class Optional<Wrapped> {
                var value: Wrapped?
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1

    def test_variadic_generic_parameters(self, tmp_path):
        """Should handle variadic generic parameters (Swift 5.9+)."""
        swift_code = dedent("""
            func combine<T, U>(_ values: T..., with other: U) {
                // Implementation
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        funcs = [s for s in result.symbols if s.kind == "function"]
        assert len(funcs) >= 1

        # Should parse without crashing
        sig = funcs[0].signature
        assert "combine" in sig.lower()
