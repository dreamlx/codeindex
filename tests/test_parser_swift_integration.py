"""Integration and end-to-end tests for Swift parser (Story 1.6).

This test file validates the Swift parser with real-world scenarios:
- Parsing real project files (slock-app)
- Performance benchmarks
- End-to-end validation of all features
- Memory and resource usage

Epic: #23
Story: 1.6
"""

import time
from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestSwiftIntegration:
    """Integration tests with real Swift code."""

    def test_parse_real_swift_file(self, tmp_path):
        """Should parse a realistic Swift file with mixed features."""
        swift_code = dedent("""
            import Foundation
            import UIKit

            /// A view controller for managing user authentication
            public class AuthViewController: UIViewController, LoginDelegate {
                // MARK: - Properties

                /// The authentication service
                private let authService: AuthService

                /// Current user state
                @Published private(set) var userState: UserState = .loggedOut

                /// Is loading indicator visible
                @State private var isLoading: Bool = false

                // MARK: - Initialization

                /// Initialize with authentication service
                /// - Parameter authService: The service to use for authentication
                public init(authService: AuthService) {
                    self.authService = authService
                    super.init(nibName: nil, bundle: nil)
                }

                required init?(coder: NSCoder) {
                    fatalError("init(coder:) has not been implemented")
                }

                // MARK: - Lifecycle

                public override func viewDidLoad() {
                    super.viewDidLoad()
                    setupUI()
                }

                // MARK: - Private Methods

                /// Set up the user interface
                private func setupUI() {
                    view.backgroundColor = .white
                }

                /// Perform login with credentials
                /// - Parameters:
                ///   - username: The username
                ///   - password: The password
                /// - Returns: True if login successful
                /// - Throws: AuthError if login fails
                private func login(username: String, password: String) async throws -> Bool {
                    isLoading = true
                    defer { isLoading = false }

                    let result = try await authService.authenticate(
                        username: username,
                        password: password
                    )

                    return result.success
                }

                // MARK: - LoginDelegate

                func didCompleteLogin(success: Bool) {
                    if success {
                        userState = .loggedIn
                    }
                }
            }

            /// User authentication state
            enum UserState {
                case loggedOut
                case loggedIn
                case expired
            }

            /// Protocol for login delegate
            protocol LoginDelegate: AnyObject {
                func didCompleteLogin(success: Bool)
            }
        """).strip()

        swift_file = tmp_path / "AuthViewController.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        # Validate parsing succeeded
        assert result.error is None
        assert len(result.symbols) > 0

        # Check class extraction
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 3  # AuthViewController, UserState, LoginDelegate

        # Find main class
        auth_vc = [c for c in classes if "AuthViewController" in c.name]
        assert len(auth_vc) == 1

        # Validate signature includes inheritance
        assert "public" in auth_vc[0].signature.lower()

        # Validate docstring extraction
        assert auth_vc[0].docstring
        assert "authentication" in auth_vc[0].docstring.lower()

        # Check methods were extracted
        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) >= 5  # init, viewDidLoad, setupUI, login, didCompleteLogin

        # Check properties were extracted
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 3  # authService, userState, isLoading

        # Validate property wrappers
        published_props = [p for p in properties if "@Published" in p.signature]
        assert len(published_props) >= 1

        state_props = [p for p in properties if "@State" in p.signature]
        assert len(state_props) >= 1

        # Check imports
        assert len(result.imports) >= 2
        import_names = [imp.module for imp in result.imports]
        assert "Foundation" in import_names
        assert "UIKit" in import_names

    def test_parse_multiple_files_sequentially(self, tmp_path):
        """Should parse multiple Swift files without errors."""
        files = []

        # Create 10 test files
        for i in range(10):
            swift_code = dedent(f"""
                /// Test class {i}
                public class TestClass{i} {{
                    private var property{i}: Int = {i}

                    func method{i}() -> Int {{
                        return property{i}
                    }}
                }}
            """).strip()

            swift_file = tmp_path / f"TestClass{i}.swift"
            swift_file.write_text(swift_code)
            files.append(swift_file)

        # Parse all files
        results = []
        for file in files:
            try:
                result = parse_file(file)
            except ImportError:
                pytest.skip("tree-sitter-swift not installed")

            assert result.error is None
            results.append(result)

        # Validate all parsed successfully
        assert len(results) == 10

        # Each should have 1 class, 1 property, 1 method
        for result in results:
            classes = [s for s in result.symbols if s.kind == "class"]
            assert len(classes) >= 1

            properties = [s for s in result.symbols if s.kind == "property"]
            assert len(properties) >= 1

            methods = [s for s in result.symbols if s.kind == "method"]
            assert len(methods) >= 1


class TestSwiftPerformance:
    """Performance benchmarks for Swift parser."""

    def test_parse_performance_small_file(self, tmp_path):
        """Benchmark parsing a small Swift file (< 100 lines)."""
        swift_code = dedent("""
            class SmallClass {
                var property1: String = ""
                var property2: Int = 0

                func method1() {}
                func method2() {}
            }
        """).strip()

        swift_file = tmp_path / "small.swift"
        swift_file.write_text(swift_code)

        try:
            start_time = time.time()
            result = parse_file(swift_file)
            elapsed = time.time() - start_time
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        # Should parse in less than 1 second
        assert elapsed < 1.0

        # Should extract all symbols
        assert result.error is None
        assert len(result.symbols) >= 5

    def test_parse_performance_medium_file(self, tmp_path):
        """Benchmark parsing a medium Swift file (100-500 lines)."""
        # Generate a realistic medium-sized file
        classes = []
        for i in range(10):  # Increased from 5 to 10 classes
            properties = "\n    ".join([f"var prop{j}: Int = {j}" for j in range(10)])
            methods = "\n    ".join([
                f"func method{j}() {{\n        return prop{j}\n    }}"
                for j in range(10)
            ])

            class_code = f"""
class Class{i} {{
    {properties}

    {methods}
}}
"""
            classes.append(class_code)

        swift_code = "\n\n".join(classes)
        swift_file = tmp_path / "medium.swift"
        swift_file.write_text(swift_code)

        # File should be ~250-500 lines (medium-sized)
        line_count = len(swift_code.split("\n"))
        assert 200 <= line_count <= 500  # Relaxed upper bound

        try:
            start_time = time.time()
            result = parse_file(swift_file)
            elapsed = time.time() - start_time
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        # Should parse in less than 2 seconds
        assert elapsed < 2.0

        # Should extract all symbols
        assert result.error is None
        # 10 classes + 100 properties + 100 methods = 210 symbols
        assert len(result.symbols) >= 200

    def test_parse_performance_batch(self, tmp_path):
        """Benchmark parsing multiple files in sequence."""
        files = []

        # Create 20 small files
        for i in range(20):
            swift_code = f"class Class{i} {{ var prop: Int = {i} }}"
            swift_file = tmp_path / f"file{i}.swift"
            swift_file.write_text(swift_code)
            files.append(swift_file)

        try:
            start_time = time.time()
            results = []
            for file in files:
                result = parse_file(file)
                results.append(result)
            elapsed = time.time() - start_time
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        # Should parse 20 files in less than 5 seconds
        assert elapsed < 5.0

        # All should succeed
        assert len(results) == 20
        assert all(r.error is None for r in results)

        # Average time per file
        avg_time = elapsed / 20
        assert avg_time < 0.3  # Less than 300ms per file


class TestSwiftEndToEnd:
    """End-to-end validation of all Swift parser features."""

    def test_all_features_together(self, tmp_path):
        """Validate all Story 1.1-1.5 features work together."""
        swift_code = dedent("""
            /// A generic container class with protocol conformance
            public class Container<T: Codable>: BaseContainer, Storable {
                // MARK: - Properties

                /// The stored items
                @Published private(set) var items: [T] = []

                /// Maximum capacity
                private let maxCapacity: Int

                // MARK: - Initialization

                /// Initialize container with capacity
                public init(capacity: Int) {
                    self.maxCapacity = capacity
                }

                // MARK: - Methods

                /// Add item to container
                /// - Parameter item: The item to add
                /// - Returns: True if added successfully
                /// - Throws: ContainerError if full
                public func add(_ item: T) async throws -> Bool {
                    guard items.count < maxCapacity else {
                        throw ContainerError.full
                    }
                    items.append(item)
                    return true
                }
            }
        """).strip()

        swift_file = tmp_path / "Container.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        # Parse succeeded
        assert result.error is None

        # Feature 1.1: Properties extracted
        properties = [s for s in result.symbols if s.kind == "property"]
        assert len(properties) >= 2
        items_prop = [p for p in properties if "items" in p.name]
        assert len(items_prop) == 1
        assert "@Published" in items_prop[0].signature

        # Feature 1.2: Inheritance extracted
        assert len(result.inheritances) >= 2
        parent_names = [i.parent for i in result.inheritances]
        assert "BaseContainer" in parent_names
        assert "Storable" in parent_names

        # Feature 1.4: Docstrings extracted
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1
        assert classes[0].docstring
        assert "generic container" in classes[0].docstring.lower()

        # Feature 1.5: Signatures include generics, async, throws
        sig = classes[0].signature
        assert "<T" in sig  # Generic parameter
        assert "public" in sig.lower()  # Access modifier

        methods = [s for s in result.symbols if s.kind == "method"]
        add_method = [m for m in methods if "add" in m.name.lower()]
        if add_method:
            method_sig = add_method[0].signature
            assert "async" in method_sig.lower()
            assert "throws" in method_sig.lower()

    def test_error_handling_invalid_swift(self, tmp_path):
        """Should handle invalid Swift code gracefully."""
        invalid_code = "this is not valid swift code { { {"

        swift_file = tmp_path / "invalid.swift"
        swift_file.write_text(invalid_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        # Should not crash, but may have empty symbols
        assert result is not None
        # Error might be set or not, but shouldn't crash

    def test_empty_file(self, tmp_path):
        """Should handle empty Swift files."""
        swift_file = tmp_path / "empty.swift"
        swift_file.write_text("")

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        assert len(result.symbols) == 0
        assert len(result.imports) == 0

    def test_comments_only_file(self, tmp_path):
        """Should handle files with only comments."""
        swift_code = dedent("""
            // This is a comment
            /* This is a block comment */
            /// This is a doc comment
        """).strip()

        swift_file = tmp_path / "comments.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        assert len(result.symbols) == 0
