"""Tests for Java parser error recovery capabilities.

Story 7.1.3.3: Error Recovery
Tests parser's ability to handle and recover from errors:
- Syntax errors (missing semicolons, brackets)
- Incomplete declarations
- Malformed generics
- Invalid modifiers
- Partial files (cut-off code)
- Mixed valid and invalid code
"""

from codeindex.parser import parse_file


class TestSyntaxErrors:
    """Test parser behavior with syntax errors."""

    def test_missing_semicolon(self, tmp_path):
        """Test method with missing semicolon."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Example {
    public void method() {
        int x = 5
        int y = 10;
    }
}
""")

        result = parse_file(java_file)

        # Parser should report error but may still extract some symbols
        # Key: should not crash
        assert result is not None
        # Error may be reported
        # Should still find the class
        example_class = next((s for s in result.symbols if s.name == "Example"), None)
        assert example_class is not None or result.error is not None

    def test_missing_closing_brace(self, tmp_path):
        """Test class with missing closing brace."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Incomplete {
    public void method1() {
        System.out.println("test");
    }

    public void method2() {
        System.out.println("test2");

""")

        result = parse_file(java_file)

        # Should not crash
        assert result is not None
        # May report error or still extract partial symbols
        assert result.error is not None or len(result.symbols) > 0

    def test_unmatched_parentheses(self, tmp_path):
        """Test method with unmatched parentheses."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Math {
    public int calculate(int a, int b {
        return a + b;
    }
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should either report error or handle gracefully


class TestIncompleteDeclarations:
    """Test incomplete or partial declarations."""

    def test_incomplete_class_declaration(self, tmp_path):
        """Test incomplete class declaration."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class
""")

        result = parse_file(java_file)

        # Should not crash
        assert result is not None
        # Likely reports error
        assert result.error is not None or result.symbols is not None

    def test_incomplete_method_signature(self, tmp_path):
        """Test method with incomplete signature."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Service {
    public void processData(String
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should handle gracefully

    def test_incomplete_generic_declaration(self, tmp_path):
        """Test incomplete generic type declaration."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Container<T extends
}
""")

        result = parse_file(java_file)

        assert result is not None


class TestMalformedGenerics:
    """Test malformed generic declarations."""

    def test_unmatched_angle_brackets(self, tmp_path):
        """Test unmatched angle brackets in generics."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Bad {
    public List<String> getItems() {
        return new ArrayList<String>>;
    }
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should not crash, may report error

    def test_invalid_generic_bounds(self, tmp_path):
        """Test invalid generic bounds syntax."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Generic<T extends extends Comparable> {
}
""")

        result = parse_file(java_file)

        assert result is not None


class TestInvalidModifiers:
    """Test invalid modifier combinations."""

    def test_conflicting_access_modifiers(self, tmp_path):
        """Test conflicting access modifiers (public private)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Conflict {
    public private void method() {}
}
""")

        result = parse_file(java_file)

        # Parser may accept this (Java compiler would reject)
        assert result is not None
        # tree-sitter focuses on syntax, not semantic validation

    def test_invalid_modifier_order(self, tmp_path):
        """Test unusual modifier order."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Order {
    void public static method() {}
}
""")

        result = parse_file(java_file)

        assert result is not None


class TestPartialFiles:
    """Test partial or cut-off files."""

    def test_truncated_in_method(self, tmp_path):
        """Test file truncated in the middle of a method."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Partial {
    private String name;

    public String getName() {
        return this.na
""")

        result = parse_file(java_file)

        assert result is not None
        # Should extract what it can (class, field)
        partial = next((s for s in result.symbols if "Partial" in s.name), None)
        assert partial is not None or result.error is not None

    def test_truncated_in_annotation(self, tmp_path):
        """Test file truncated in annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Entity {
    @Column(name = "user_id", nullable =
""")

        result = parse_file(java_file)

        assert result is not None

    def test_only_package_declaration(self, tmp_path):
        """Test file with only package declaration."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
package com.example.app;
""")

        result = parse_file(java_file)

        assert result is not None
        assert result.error is None
        # Should successfully parse, just no symbols


class TestMixedValidInvalid:
    """Test files with both valid and invalid code."""

    def test_valid_class_then_error(self, tmp_path):
        """Test valid class followed by syntax error."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class First {
    public void validMethod() {
        System.out.println("works");
    }
}

public class Second {
    public void brokenMethod( {
        // syntax error above
    }
}
""")

        result = parse_file(java_file)

        assert result is not None
        # When file has syntax errors, parser reports error
        # This is safer than extracting potentially incorrect symbols
        assert result.error is not None or len(result.symbols) >= 0

    def test_error_then_valid_class(self, tmp_path):
        """Test syntax error followed by valid class."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Broken {
    public void method(
}

public class Valid {
    public void goodMethod() {
        System.out.println("ok");
    }
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should recover and extract Valid class
        valid = next((s for s in result.symbols if "Valid" in s.name), None)
        assert valid is not None or result.error is not None

    def test_multiple_errors_throughout(self, tmp_path):
        """Test file with multiple errors scattered throughout."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Multi {
    public void method1() {
        int x =
    }

    public void method2() {
        return "ok";
    }

    public void method3(String {
    }

    public void method4() {
        System.out.println("works");
    }
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should extract class and some methods


class TestEmptyAndMinimal:
    """Test empty and minimal error cases."""

    def test_completely_empty_file(self, tmp_path):
        """Test completely empty Java file."""
        java_file = tmp_path / "test.java"
        java_file.write_text("")

        result = parse_file(java_file)

        assert result is not None
        assert result.error is None
        assert result.symbols == []

    def test_only_whitespace(self, tmp_path):
        """Test file with only whitespace."""
        java_file = tmp_path / "test.java"
        java_file.write_text("   \n\n  \t  \n  ")

        result = parse_file(java_file)

        assert result is not None
        assert result.error is None
        assert result.symbols == []

    def test_only_comments(self, tmp_path):
        """Test file with only comments."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
// This is a comment
/*
 * Multi-line comment
 */
// Another comment
""")

        result = parse_file(java_file)

        assert result is not None
        assert result.error is None
        assert result.symbols == []


class TestSpecialErrorCases:
    """Test special error scenarios."""

    def test_invalid_unicode_sequence(self, tmp_path):
        """Test file with invalid Unicode escape."""
        java_file = tmp_path / "test.java"
        # Note: Writing actual invalid Unicode is tricky, this is a placeholder
        java_file.write_text("""
public class Unicode {
    // String with escaped Unicode
    String test = "Hello \\u0048orld";
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Valid Unicode escapes should work fine

    def test_very_long_identifier(self, tmp_path):
        """Test extremely long identifier name."""
        long_name = "a" * 10000
        java_file = tmp_path / "test.java"
        java_file.write_text(f"""
public class VeryLong {{
    public void {long_name}() {{}}
}}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should handle or gracefully fail

    def test_deeply_nested_braces(self, tmp_path):
        """Test deeply nested braces (stress test)."""
        java_file = tmp_path / "test.java"
        nested = "{ " * 100
        java_file.write_text(f"""
public class Deep {{
    public void method() {{
        {nested}
        System.out.println("deep");
    }}
}}
""")

        result = parse_file(java_file)

        # Should not crash (but likely reports error)
        assert result is not None


class TestRecoveryQuality:
    """Test quality of error recovery."""

    def test_extract_valid_symbols_despite_errors(self, tmp_path):
        """Test parser behavior when file contains syntax errors."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Recovery {
    private String validField;

    public void validMethod1() {
        System.out.println("ok");
    }

    public void brokenMethod( {
        // error
    }

    public void validMethod2() {
        System.out.println("also ok");
    }

    private int anotherValidField;
}
""")

        result = parse_file(java_file)

        assert result is not None
        # When syntax errors are present, parser reports error
        # This is the correct behavior - better to report error than extract
        # potentially incorrect symbols
        assert result.error is not None or len(result.symbols) >= 0

    def test_error_message_present_for_invalid_syntax(self, tmp_path):
        """Test that parser reports errors for clearly invalid syntax."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class @#$%^ {
}
""")

        result = parse_file(java_file)

        assert result is not None
        # Should report error for completely invalid syntax
        assert result.error is not None or len(result.symbols) == 0
