"""Tests for Java generic bounds parsing.

Story 7.1.2.2: Generic Bounds
Tests parsing of generic type bounds in Java:
- Single extends bound: <T extends Comparable<T>>
- Multiple bounds: <T extends A & B & C>
- Super bound: <T super Number> (wildcards)
- Wildcard bounds: <? extends List<String>>
"""



from codeindex.parser import parse_file


class TestSingleExtendsBound:
    """Test single extends bound in generics."""

    def test_class_with_single_extends_bound(self, tmp_path):
        """Test class with single type parameter bound."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Box<T extends Comparable<T>> {
    private T value;

    public T getValue() {
        return value;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        assert len(result.symbols) > 0

        box_class = next(s for s in result.symbols if s.name == "Box")
        assert "extends Comparable" in box_class.signature
        # Should capture the full generic bound
        assert "T extends Comparable<T>" in box_class.signature

    def test_interface_with_extends_bound(self, tmp_path):
        """Test interface with type parameter bound."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public interface Repository<T extends Entity> {
    T findById(Long id);
    List<T> findAll();
}
""")

        result = parse_file(java_file)

        repository = next(s for s in result.symbols if s.name == "Repository")
        assert "T extends Entity" in repository.signature

    def test_method_with_extends_bound(self, tmp_path):
        """Test method with generic type bound."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Utils {
    public static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) > 0 ? a : b;
    }
}
""")

        result = parse_file(java_file)

        max_method = next(s for s in result.symbols if "max" in s.name)
        # Method signature should include the generic bound
        assert "T extends Comparable" in max_method.signature


class TestMultipleBounds:
    """Test multiple bounds with & operator."""

    def test_class_with_multiple_bounds(self, tmp_path):
        """Test class with multiple type bounds (T extends A & B)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Processor<T extends Serializable & Comparable<T>> {
    private T data;
}
""")

        result = parse_file(java_file)

        processor = next(s for s in result.symbols if s.name == "Processor")
        assert "T extends Serializable & Comparable" in processor.signature or \
               "T extends Serializable" in processor.signature

    def test_method_with_multiple_bounds(self, tmp_path):
        """Test method with multiple type bounds."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Sorter {
    public <T extends Comparable<T> & Serializable> void sort(List<T> list) {
        // sorting logic
    }
}
""")

        result = parse_file(java_file)

        sort_method = next(s for s in result.symbols if "sort" in s.name)
        # Should capture at least the first bound
        assert "Comparable" in sort_method.signature or \
               "T extends" in sort_method.signature


class TestWildcardBounds:
    """Test wildcard bounds (? extends/super)."""

    def test_method_with_extends_wildcard(self, tmp_path):
        """Test method parameter with wildcard extends bound."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Container {
    public void addAll(List<? extends Number> numbers) {
        // implementation
    }
}
""")

        result = parse_file(java_file)

        add_method = next(s for s in result.symbols if "addAll" in s.name)
        # Wildcard bounds appear in method parameters
        assert "? extends Number" in add_method.signature or \
               "List<? extends Number>" in add_method.signature

    def test_method_with_super_wildcard(self, tmp_path):
        """Test method parameter with wildcard super bound."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Utils {
    public void addNumbers(List<? super Integer> list) {
        list.add(42);
    }
}
""")

        result = parse_file(java_file)

        add_method = next(s for s in result.symbols if "addNumbers" in s.name)
        # Wildcard super bound in parameters
        assert "? super Integer" in add_method.signature or \
               "List<? super Integer>" in add_method.signature

    def test_return_type_with_wildcard(self, tmp_path):
        """Test return type with wildcard bound."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Factory {
    public List<? extends Product> getProducts() {
        return products;
    }
}
""")

        result = parse_file(java_file)

        get_method = next(s for s in result.symbols if "getProducts" in s.name)
        assert "? extends Product" in get_method.signature or \
               "List<? extends Product>" in get_method.signature


class TestNestedGenerics:
    """Test nested generic types with bounds."""

    def test_nested_generic_bounds(self, tmp_path):
        """Test nested generic types (e.g., List<Map<String, ? extends T>>)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class DataStore<T extends Comparable<T>> {
    private Map<String, List<T>> data;

    public List<T> get(String key) {
        return data.get(key);
    }
}
""")

        result = parse_file(java_file)

        store_class = next(s for s in result.symbols if s.name == "DataStore")
        assert "T extends Comparable" in store_class.signature

    def test_complex_nested_bounds(self, tmp_path):
        """Test complex nested generic bounds."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public interface Repository<T extends Entity<? extends Serializable>> {
    T save(T entity);
}
""")

        result = parse_file(java_file)

        repo = next(s for s in result.symbols if s.name == "Repository")
        # Should capture the extends bound even if nested generics are complex
        assert "T extends Entity" in repo.signature


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unbounded_generic(self, tmp_path):
        """Test generic without bounds (should still work)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Container<T> {
    private T value;
}
""")

        result = parse_file(java_file)

        container = next(s for s in result.symbols if s.name == "Container")
        assert "<T>" in container.signature
        # Should NOT have "extends" for unbounded generics
        assert "extends" not in container.signature or \
               container.signature.count("extends") == 0

    def test_multiple_type_parameters_with_bounds(self, tmp_path):
        """Test multiple type parameters, each with its own bounds."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Pair<K extends Comparable<K>, V extends Serializable> {
    private K key;
    private V value;
}
""")

        result = parse_file(java_file)

        pair_class = next(s for s in result.symbols if s.name == "Pair")
        # Should capture both type parameter bounds
        assert "K extends Comparable" in pair_class.signature
        assert "V extends Serializable" in pair_class.signature

    def test_raw_type_no_generics(self, tmp_path):
        """Test class without any generics (baseline)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class SimpleClass {
    private String name;
}
""")

        result = parse_file(java_file)

        simple = next(s for s in result.symbols if s.name == "SimpleClass")
        assert "<" not in simple.signature
        assert "extends" not in simple.signature or \
               "SimpleClass extends" not in simple.signature
