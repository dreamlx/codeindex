"""POC tests for Swift parser.

This test file validates the basic Swift parsing capability.
Full test suite will be implemented in phases.

Test coverage plan:
- Phase 1: Basic symbol extraction (20+ tests)
- Phase 2: Advanced features (15+ tests)
- Phase 3: Call graph and inheritance (10+ tests)

Issue: #23
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestSwiftParserPOC:
    """POC test suite for Swift parser."""

    def test_parse_empty_file(self, tmp_path):
        """Should handle empty Swift file."""
        swift_file = tmp_path / "empty.swift"
        swift_file.write_text("")

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.path == swift_file
        assert result.error is None
        assert len(result.symbols) == 0
        assert len(result.imports) == 0

    def test_parse_simple_class(self, tmp_path):
        """Should extract simple class declaration."""
        swift_code = dedent("""
            class UserManager {
                func login() {
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
        assert len(result.symbols) >= 1

        # Find class symbol
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0].name == "UserManager"

        # Find method symbol
        method_symbols = [s for s in result.symbols if s.kind == "method"]
        assert len(method_symbols) >= 1
        assert any("login" in s.name for s in method_symbols)

    def test_parse_struct(self, tmp_path):
        """Should extract struct declaration."""
        swift_code = dedent("""
            struct User {
                var name: String
                var age: Int
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0].name == "User"

    def test_parse_enum(self, tmp_path):
        """Should extract enum declaration."""
        swift_code = dedent("""
            enum Color {
                case red
                case green
                case blue
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0].name == "Color"

    def test_parse_top_level_function(self, tmp_path):
        """Should extract top-level function."""
        swift_code = dedent("""
            func calculateSum(a: Int, b: Int) -> Int {
                return a + b
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        func_symbols = [s for s in result.symbols if s.kind == "function"]
        assert len(func_symbols) == 1
        assert func_symbols[0].name == "calculateSum"

    def test_parse_imports(self, tmp_path):
        """Should extract import statements."""
        swift_code = dedent("""
            import Foundation
            import UIKit

            class MyClass {
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        assert len(result.imports) >= 2

        import_modules = [imp.module for imp in result.imports]
        assert "Foundation" in import_modules
        assert "UIKit" in import_modules

    def test_parse_multiple_classes(self, tmp_path):
        """Should extract multiple class declarations."""
        swift_code = dedent("""
            class FirstClass {
                func methodOne() {}
            }

            class SecondClass {
                func methodTwo() {}
            }
        """).strip()

        swift_file = tmp_path / "test.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) == 2

        class_names = {s.name for s in class_symbols}
        assert "FirstClass" in class_names
        assert "SecondClass" in class_names

    def test_line_numbers(self, tmp_path):
        """Should track correct line numbers."""
        swift_code = dedent("""
            import Foundation

            class MyClass {
                func myMethod() {
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
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) == 1

        # Class should start around line 3
        assert class_symbols[0].line_start >= 3
        assert class_symbols[0].line_end >= class_symbols[0].line_start


class TestSwiftParserRealWorld:
    """Test Swift parser with real-world code patterns."""

    def test_parse_view_controller(self, tmp_path):
        """Should parse typical iOS ViewController."""
        swift_code = dedent("""
            import UIKit

            class LoginViewController: UIViewController {

                var usernameField: UITextField!
                var passwordField: UITextField!

                override func viewDidLoad() {
                    super.viewDidLoad()
                    setupUI()
                }

                func setupUI() {
                    // Setup code
                }

                @IBAction func loginButtonTapped(_ sender: UIButton) {
                    performLogin()
                }

                private func performLogin() {
                    // Login logic
                }
            }
        """).strip()

        swift_file = tmp_path / "LoginViewController.swift"
        swift_file.write_text(swift_code)

        try:
            result = parse_file(swift_file)
        except ImportError:
            pytest.skip("tree-sitter-swift not installed")

        assert result.error is None

        # Should extract class
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0].name == "LoginViewController"

        # Should extract methods (at least viewDidLoad, setupUI, performLogin)
        method_symbols = [s for s in result.symbols if s.kind == "method"]
        assert len(method_symbols) >= 3

        method_names = {s.name.split(".")[-1] for s in method_symbols}
        assert "viewDidLoad" in method_names
        assert "setupUI" in method_names
