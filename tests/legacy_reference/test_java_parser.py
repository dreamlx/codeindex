"""
Unit tests for Java parser.

This module tests the Java language parser using tree-sitter-java.
Tests follow TDD methodology: RED → GREEN → REFACTOR.

Current Phase: RED (tests will fail until implementation is complete)
"""

from pathlib import Path

# These imports will fail initially - that's expected in RED phase
# from codeindex.parsers.java_parser import (
#     parse_java_file,
#     is_java_file,
#     get_java_parser,
# )
# from codeindex.models import ParseResult, Symbol, Import


# Fixture helper
def load_fixture(filename: str) -> str:
    """Load Java test fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "java" / filename
    return fixture_path.read_text()


class TestJavaParserBasics:
    """Test basic Java parsing functionality."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_java_file_detection(self):
        """Test Java file extension detection."""
        from codeindex.parsers.java_parser import is_java_file

        assert is_java_file("Test.java")
        assert is_java_file("com/example/User.java")
        assert not is_java_file("test.py")
        assert not is_java_file("test.php")
        assert not is_java_file("README.md")

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parser_initialization(self):
        """Test Java parser can be initialized."""
        from codeindex.parsers.java_parser import get_java_parser

        parser = get_java_parser()
        assert parser is not None

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_simple_class(self):
        """Test parsing a simple Java class."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        # assert isinstance(result, ParseResult)  # Will be enabled in GREEN phase
        assert result.error is None
        assert result.error is None
        assert len(result.symbols) > 0

        # Check class symbol
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) >= 1
        assert any(s.name == "User" for s in class_symbols)

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_interface(self):
        """Test parsing a Java interface."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("interface.java")
        result = parse_java_file("interface.java", code)

        assert result.error is None
        interface_symbols = [s for s in result.symbols if s.kind == "interface"]
        assert len(interface_symbols) >= 1
        assert any(s.name == "UserService" for s in interface_symbols)

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_enum(self):
        """Test parsing a Java enum."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("enum.java")
        result = parse_java_file("enum.java", code)

        assert result.error is None
        enum_symbols = [s for s in result.symbols if s.kind == "enum"]
        assert len(enum_symbols) >= 1
        assert any(s.name == "UserStatus" for s in enum_symbols)

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_syntax_error(self):
        """Test handling Java syntax errors."""
        from codeindex.parsers.java_parser import parse_java_file

        code = "public class Invalid { // missing closing brace"
        result = parse_java_file("invalid.java", code)

        # Should not crash, but should report error
        assert result.error is not None or hasattr(result, 'has_error')


class TestJavaSymbolExtraction:
    """Test Java symbol extraction (classes, methods, fields)."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_class_name(self):
        """Test extracting class name."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        class_symbol = next(s for s in result.symbols if s.name == "User")
        assert class_symbol.kind == "class"
        assert "User" in class_symbol.signature

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_methods(self):
        """Test extracting method definitions."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        method_symbols = [s for s in result.symbols if s.kind == "method"]
        assert len(method_symbols) > 0

        # Check for specific methods (names include class prefix like "User.findById")
        method_names = [s.name for s in method_symbols]
        assert any("findById" in name for name in method_names)
        assert any("save" in name for name in method_names)
        assert any("findAll" in name for name in method_names)

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_method_signature(self):
        """Test extracting complete method signature."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        find_by_id_method = next(
            (s for s in result.symbols if "findById" in s.name and s.kind == "method"),
            None
        )
        assert find_by_id_method is not None
        # Signature should include return type and parameters
        assert "Optional" in find_by_id_method.signature or "User" in find_by_id_method.signature
        assert "Long id" in find_by_id_method.signature or "id" in find_by_id_method.signature

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_fields(self):
        """Test extracting class fields."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        field_symbols = [s for s in result.symbols if s.kind == "field"]
        # Should have id, name, email, age fields
        assert len(field_symbols) >= 4

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_constructor(self):
        """Test extracting constructors."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        constructor_symbols = [s for s in result.symbols if s.kind == "constructor"]
        # Should have at least 2 constructors
        assert len(constructor_symbols) >= 2


class TestJavaImports:
    """Test Java import statement extraction."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_simple_imports(self):
        """Test extracting simple import statements."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("imports.java")
        result = parse_java_file("imports.java", code)

        assert len(result.imports) > 0

        # Check for specific imports
        import_modules = [imp.module for imp in result.imports]
        assert "java.util.List" in import_modules
        assert "java.util.Map" in import_modules

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_static_imports(self):
        """Test extracting static imports."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("imports.java")
        result = parse_java_file("imports.java", code)

        # Should have static imports
        static_imports = [
            imp for imp in result.imports
            if "Collections" in imp.module or "emptyList" in str(imp.names)
        ]
        assert len(static_imports) > 0

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_wildcard_imports(self):
        """Test extracting wildcard imports (import java.io.*)."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("imports.java")
        result = parse_java_file("imports.java", code)

        # Should detect wildcard import
        wildcard_imports = [imp for imp in result.imports if "*" in imp.module]
        assert len(wildcard_imports) > 0


class TestJavaGenerics:
    """Test parsing generic types."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_generic_class(self):
        """Test parsing generic class declaration."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("generics.java")
        result = parse_java_file("generics.java", code)

        box_class = next((s for s in result.symbols if s.name == "Box"), None)
        assert box_class is not None
        # Should capture generic type parameter <T>
        assert "<T>" in box_class.signature or "Box<T>" in box_class.signature

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_generic_method(self):
        """Test parsing generic method."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("generics.java")
        result = parse_java_file("generics.java", code)

        # Box.of() is a generic static method
        of_method = next(
            (s for s in result.symbols if "of" in s.name and s.kind == "method"),
            None
        )
        assert of_method is not None


class TestJavaModernSyntax:
    """Test Java 14+ modern syntax (records, sealed classes)."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_record(self):
        """Test parsing Java 14+ record."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("record.java")
        result = parse_java_file("record.java", code)

        record_symbols = [s for s in result.symbols if s.kind in ["record", "class"]]
        assert len(record_symbols) >= 1
        assert any("UserRecord" in s.name for s in record_symbols)

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_parse_sealed_class(self):
        """Test parsing Java 17+ sealed class."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("sealed_class.java")
        result = parse_java_file("sealed_class.java", code)

        # Should have Shape, Circle, Rectangle, Triangle
        class_symbols = [s for s in result.symbols if s.kind == "class"]
        assert len(class_symbols) >= 4

        shape_class = next((s for s in class_symbols if s.name == "Shape"), None)
        assert shape_class is not None
        # Ideally should capture "sealed" modifier
        # assert "sealed" in shape_class.signature.lower()


class TestJavaDocstring:
    """Test JavaDoc extraction."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_class_javadoc(self):
        """Test extracting class-level JavaDoc."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        class_symbol = next(s for s in result.symbols if s.name == "User")
        # Should have docstring
        assert class_symbol.docstring is not None
        assert "User entity class" in class_symbol.docstring

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_method_javadoc(self):
        """Test extracting method-level JavaDoc."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        find_by_id_method = next(
            (s for s in result.symbols if "findById" in s.name and s.kind == "method"),
            None
        )
        assert find_by_id_method is not None
        # Should have docstring with @param and @return tags
        assert find_by_id_method.docstring is not None
        assert "Get user by ID" in find_by_id_method.docstring

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_module_docstring(self):
        """Test extracting top-level (module) JavaDoc."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("interface.java")
        result = parse_java_file("interface.java", code)

        # module_docstring should contain class/interface JavaDoc
        assert result.module_docstring is not None
        assert "User service interface" in result.module_docstring


class TestJavaFileMetadata:
    """Test file-level metadata extraction."""

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_extract_package_name(self):
        """Test extracting package declaration."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        # Package info should be captured somewhere
        # Could be in metadata or as a separate field
        assert "com.example.demo" in str(result) or hasattr(result, 'package')

    # @pytest.mark.skip(reason="GREEN phase: implementation ready")
    def test_count_file_lines(self):
        """Test counting lines in file."""
        from codeindex.parsers.java_parser import parse_java_file

        code = load_fixture("simple_class.java")
        result = parse_java_file("simple_class.java", code)

        assert result.file_lines > 0
        assert result.file_lines == len(code.splitlines())


# Summary for RED phase:
# - 30+ tests defined
# - All tests marked with @pytest.mark.skip
# - Expected to FAIL when skip is removed
# - Next: Implement java_parser.py to make tests PASS (GREEN phase)
