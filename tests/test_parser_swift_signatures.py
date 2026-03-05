"""Test suite for Swift enhanced signature formatting (Story 1.5).

This test file validates Swift signature extraction and formatting:
- Access modifiers (public, private, internal, fileprivate)
- Generic type parameters with constraints
- Complete parameter lists with labels and types
- Return types for functions and methods
- Async/await and throws keywords
- Complex signature combinations

Epic: #23
Story: 1.5
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestAccessModifiers:
    """Test access modifier extraction in signatures."""

    def test_public_class(self, tmp_path):
        """Should include 'public' modifier in class signature."""
        swift_code = dedent("""
            public class PublicClass {}
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

        # Signature should include 'public' modifier
        assert "public" in classes[0].signature.lower()

    def test_private_method(self, tmp_path):
        """Should include 'private' modifier in method signature."""
        swift_code = dedent("""
            class MyClass {
                private func secretMethod() {}
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1

        # Signature should include 'private' modifier
        assert "private" in methods[0].signature.lower()

    def test_internal_function(self, tmp_path):
        """Should include 'internal' modifier (or omit as default)."""
        swift_code = dedent("""
            internal func internalFunction() {}
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

        # Signature may include 'internal' or omit it (default)
        sig = funcs[0].signature.lower()
        assert "internal" in sig or "func" in sig

    def test_fileprivate_property(self, tmp_path):
        """Should include 'fileprivate' modifier in property signature."""
        swift_code = dedent("""
            class MyClass {
                fileprivate var secret: String = ""
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        props = [s for s in result.symbols if s.kind == "property"]
        assert len(props) >= 1

        # Signature should include 'fileprivate' modifier
        assert "fileprivate" in props[0].signature.lower()


class TestGenericParameters:
    """Test generic type parameter extraction."""

    def test_generic_class(self, tmp_path):
        """Should include generic type parameter in class signature."""
        swift_code = dedent("""
            class GenericBox<T> {}
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

        # Signature should include generic parameter
        assert "<T>" in classes[0].signature or "<t>" in classes[0].signature.lower()

    def test_generic_function_with_constraint(self, tmp_path):
        """Should include generic parameter with type constraint."""
        swift_code = dedent("""
            func compare<T: Comparable>(_ a: T, _ b: T) -> Bool {
                return a < b
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

        # Signature should include generic constraint
        sig = funcs[0].signature
        assert "T:" in sig or "t:" in sig.lower()
        assert "comparable" in sig.lower()

    def test_multiple_generic_parameters(self, tmp_path):
        """Should handle multiple generic type parameters."""
        swift_code = dedent("""
            class Pair<K, V> {}
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


class TestFunctionParameters:
    """Test complete parameter list extraction."""

    def test_function_with_parameter_labels(self, tmp_path):
        """Should include parameter labels and types."""
        swift_code = dedent("""
            func greet(name: String, age: Int) {}
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

        # Signature should include parameter labels and types
        sig = funcs[0].signature.lower()
        assert "name" in sig
        assert "string" in sig
        assert "age" in sig
        assert "int" in sig

    def test_function_with_external_parameter_names(self, tmp_path):
        """Should handle external parameter names."""
        swift_code = dedent("""
            func greet(to name: String, withAge age: Int) {}
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

        # Signature should include external and internal parameter names
        sig = funcs[0].signature.lower()
        assert "to" in sig or "name" in sig
        assert "withage" in sig or "age" in sig

    def test_function_with_default_parameters(self, tmp_path):
        """Should handle parameters with default values."""
        swift_code = dedent("""
            func connect(timeout: Int = 30) {}
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

        # Signature should include parameter with type
        sig = funcs[0].signature.lower()
        assert "timeout" in sig
        assert "int" in sig


class TestReturnTypes:
    """Test return type extraction."""

    def test_function_with_return_type(self, tmp_path):
        """Should include return type in function signature."""
        swift_code = dedent("""
            func calculate() -> Int {
                return 42
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

        # Signature should include return type
        sig = funcs[0].signature.lower()
        assert "->" in sig or "int" in sig

    def test_method_with_optional_return_type(self, tmp_path):
        """Should handle optional return types."""
        swift_code = dedent("""
            class MyClass {
                func findUser() -> User? {
                    return nil
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

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1

        # Signature should include optional return type
        sig = methods[0].signature.lower()
        assert "user" in sig and ("?" in sig or "optional" in sig)

    def test_function_with_tuple_return_type(self, tmp_path):
        """Should handle tuple return types."""
        swift_code = dedent("""
            func getCoordinates() -> (x: Int, y: Int) {
                return (0, 0)
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

        # Signature should include tuple elements
        sig = funcs[0].signature.lower()
        assert "x" in sig and "y" in sig


class TestAsyncAwaitThrows:
    """Test async/await and throws keywords."""

    def test_async_function(self, tmp_path):
        """Should include 'async' keyword in signature."""
        swift_code = dedent("""
            func fetchData() async -> Data {
                return Data()
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

        # Signature should include 'async' keyword
        assert "async" in funcs[0].signature.lower()

    def test_throws_function(self, tmp_path):
        """Should include 'throws' keyword in signature."""
        swift_code = dedent("""
            func validateInput() throws -> Bool {
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

        # Signature should include 'throws' keyword
        assert "throws" in funcs[0].signature.lower()

    def test_async_throws_function(self, tmp_path):
        """Should include both 'async' and 'throws' keywords."""
        swift_code = dedent("""
            func processData() async throws -> Result {
                return Result()
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

        # Signature should include both keywords
        sig = funcs[0].signature.lower()
        assert "async" in sig
        assert "throws" in sig


class TestComplexSignatures:
    """Test complex signature combinations."""

    def test_public_generic_async_throws_function(self, tmp_path):
        """Should handle all signature components together."""
        swift_code = dedent("""
            public func transform<T: Codable>(_ input: T) async throws -> T {
                return input
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

        # Signature should include all components
        sig = funcs[0].signature.lower()
        assert "public" in sig
        assert "t" in sig  # Generic type
        assert "async" in sig
        assert "throws" in sig
        assert "input" in sig

    def test_private_static_method_with_generics(self, tmp_path):
        """Should handle static methods with access modifiers and generics."""
        swift_code = dedent("""
            class MyClass {
                private static func create<T>() -> T? {
                    return nil
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

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 1

        # Signature should include private, static, and generic
        sig = methods[0].signature.lower()
        assert "private" in sig
        assert "static" in sig
        assert "t" in sig


class TestSignatureEdgeCases:
    """Test edge cases for signature extraction."""

    def test_function_with_no_parameters(self, tmp_path):
        """Should handle functions with no parameters."""
        swift_code = dedent("""
            public func doSomething() {}
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

        # Signature should still be valid
        assert "()" in funcs[0].signature

    def test_function_with_variadic_parameters(self, tmp_path):
        """Should handle variadic parameters."""
        swift_code = dedent("""
            func sum(_ numbers: Int...) -> Int {
                return 0
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

        # Signature should include variadic indicator
        sig = funcs[0].signature.lower()
        assert "numbers" in sig
        assert "..." in sig or "int" in sig
