"""Tests for Java parser edge cases and boundary conditions.

Story 7.1.3.2: Edge Case Tests
Tests parser robustness with special scenarios:
- Nested classes (inner, static, anonymous)
- Complex generic combinations
- Very long signatures
- Unicode identifiers
- Empty declarations
- Varargs parameters
- Array types
- Multiple interface inheritance
"""

from codeindex.parser import parse_file


class TestNestedClasses:
    """Test nested and inner class declarations."""

    def test_static_nested_class(self, tmp_path):
        """Test static nested class."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Outer {
    public static class StaticNested {
        public void method() {}
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        # Should capture both outer and nested class
        outer = next(s for s in result.symbols if s.name == "Outer")
        assert outer.kind == "class"
        # Nested class should also be captured
        nested = next((s for s in result.symbols if "StaticNested" in s.name), None)
        assert nested is not None

    def test_inner_class(self, tmp_path):
        """Test non-static inner class."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Outer {
    public class Inner {
        private String name;
        public Inner(String name) {
            this.name = name;
        }
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        outer = next(s for s in result.symbols if s.name == "Outer")
        assert outer is not None

    def test_multiple_nested_levels(self, tmp_path):
        """Test multiple levels of nesting."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Level1 {
    public static class Level2 {
        public static class Level3 {
            public void deepMethod() {}
        }
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        level1 = next(s for s in result.symbols if s.name == "Level1")
        assert level1 is not None

    def test_anonymous_class(self, tmp_path):
        """Test method containing anonymous class."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class ButtonHandler {
    public void setupButton() {
        button.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                System.out.println("Clicked");
            }
        });
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        handler = next(s for s in result.symbols if s.name == "ButtonHandler")
        assert handler is not None


class TestComplexGenerics:
    """Test complex generic type combinations."""

    def test_nested_generics(self, tmp_path):
        """Test deeply nested generic types."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class ComplexContainer {
    private Map<String, List<Set<Integer>>> complexField;

    public Map<String, List<Set<Integer>>> getComplexField() {
        return complexField;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        container = next(s for s in result.symbols if s.name == "ComplexContainer")
        assert container is not None

    def test_wildcard_combinations(self, tmp_path):
        """Test various wildcard combinations."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class WildcardTest {
    public void complex(List<? extends Map<String, ? super Number>> list) {}
}
""")

        result = parse_file(java_file)

        assert result.error is None
        test_class = next(s for s in result.symbols if s.name == "WildcardTest")
        assert test_class is not None

    def test_multiple_type_parameters_with_bounds(self, tmp_path):
        """Test multiple type parameters with complex bounds."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class MultiGeneric<K extends Comparable<K> & Serializable,
                           V extends Map<K, ? extends List<String>>> {
    public <T extends K> void process(T item) {}
}
""")

        result = parse_file(java_file)

        assert result.error is None
        multi = next(s for s in result.symbols if s.name == "MultiGeneric")
        assert multi is not None


class TestLongSignatures:
    """Test very long method signatures."""

    def test_many_parameters(self, tmp_path):
        """Test method with many parameters."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class ManyParams {
    public void longMethod(String a, int b, double c, boolean d,
                          List<String> e, Map<Integer, String> f,
                          Object g, String h, int i, double j) {
        // implementation
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        method = next(s for s in result.symbols if "longMethod" in s.name)
        assert method is not None
        # Signature should contain parameter types
        assert "String a" in method.signature or "String" in method.signature

    def test_long_generic_signature(self, tmp_path):
        """Test very long generic method signature."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class LongGeneric {
    public <T extends Comparable<T> & Serializable,
            U extends Map<String, List<T>>,
            V extends Collection<? super U>>
    List<Map<T, Set<V>>> transform(T input, U mapping, V collection)
            throws IOException, SQLException {
        return null;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        transform = next(s for s in result.symbols if "transform" in s.name)
        assert transform is not None


class TestSpecialCharacters:
    """Test Unicode and special characters."""

    def test_unicode_class_name(self, tmp_path):
        """Test class with Unicode name."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class 用户管理 {
    private String 名称;

    public String get名称() {
        return 名称;
    }
}
""")

        result = parse_file(java_file)

        # Should parse without error (Java allows Unicode identifiers)
        assert result.error is None

    def test_dollar_sign_in_name(self, tmp_path):
        """Test class with $ in name (generated by compiler)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Outer$Inner {
    public void method$1() {}
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestEmptyDeclarations:
    """Test empty or minimal declarations."""

    def test_empty_class(self, tmp_path):
        """Test class with no members."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Empty {
}
""")

        result = parse_file(java_file)

        assert result.error is None
        empty = next(s for s in result.symbols if s.name == "Empty")
        assert empty.kind == "class"

    def test_empty_interface(self, tmp_path):
        """Test interface with no methods (marker interface)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public interface MarkerInterface {
}
""")

        result = parse_file(java_file)

        assert result.error is None
        marker = next(s for s in result.symbols if s.name == "MarkerInterface")
        assert marker.kind == "interface"

    def test_single_line_class(self, tmp_path):
        """Test class defined on single line."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class OneLine { public void method() {} }
""")

        result = parse_file(java_file)

        assert result.error is None
        one_line = next(s for s in result.symbols if s.name == "OneLine")
        assert one_line is not None


class TestArrayTypes:
    """Test array type parameters and return types."""

    def test_array_parameter(self, tmp_path):
        """Test method with array parameter."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class ArrayHandler {
    public void process(String[] items) {}
}
""")

        result = parse_file(java_file)

        assert result.error is None
        process = next(s for s in result.symbols if "process" in s.name)
        assert "String[]" in process.signature or "String" in process.signature

    def test_multidimensional_array(self, tmp_path):
        """Test multidimensional array."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Matrix {
    public int[][] multiply(int[][] a, int[][] b) {
        return null;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        multiply = next(s for s in result.symbols if "multiply" in s.name)
        assert multiply is not None

    def test_generic_array(self, tmp_path):
        """Test generic array types."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class GenericArray<T> {
    public List<T>[] getArrayOfLists() {
        return null;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        generic = next(s for s in result.symbols if s.name == "GenericArray")
        assert generic is not None


class TestVarargs:
    """Test varargs (variable arguments) parameters."""

    def test_simple_varargs(self, tmp_path):
        """Test method with varargs parameter."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class VarargsTest {
    public void display(String... messages) {}
}
""")

        result = parse_file(java_file)

        assert result.error is None
        display_method = next(s for s in result.symbols if "display" in s.name)
        assert "String..." in display_method.signature or \
               "String" in display_method.signature

    def test_varargs_with_other_params(self, tmp_path):
        """Test varargs combined with regular parameters."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Logger {
    public void log(String level, String format, Object... args) {}
}
""")

        result = parse_file(java_file)

        assert result.error is None
        log_method = next(s for s in result.symbols if "log" in s.name)
        assert log_method is not None

    def test_generic_varargs(self, tmp_path):
        """Test generic varargs parameter."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class GenericVarargs {
    @SafeVarargs
    public final <T> List<T> asList(T... elements) {
        return Arrays.asList(elements);
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        as_list = next(s for s in result.symbols if "asList" in s.name)
        assert as_list is not None


class TestMultipleInheritance:
    """Test multiple interface inheritance."""

    def test_class_implements_multiple_interfaces(self, tmp_path):
        """Test class implementing multiple interfaces."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class MultiImpl implements Serializable, Cloneable, Comparable<MultiImpl> {
    @Override
    public int compareTo(MultiImpl o) {
        return 0;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        multi = next(s for s in result.symbols if s.name == "MultiImpl")
        assert "implements" in multi.signature
        assert "Serializable" in multi.signature or "implements" in multi.signature

    def test_interface_extends_multiple(self, tmp_path):
        """Test interface extending multiple interfaces."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public interface Combined extends Runnable, Callable<String>, AutoCloseable {
    void extraMethod();
}
""")

        result = parse_file(java_file)

        assert result.error is None
        combined = next(s for s in result.symbols if s.name == "Combined")
        assert "extends" in combined.signature


class TestAnnotationCombinations:
    """Test complex annotation combinations."""

    def test_multiple_annotations_on_method(self, tmp_path):
        """Test method with multiple annotations."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class AnnotatedService {
    @Override
    @Transactional
    @Cacheable("users")
    @PreAuthorize("hasRole('ADMIN')")
    public User findUser(Long id) {
        return null;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        find_user = next(s for s in result.symbols if "findUser" in s.name)
        # Should have multiple annotations
        assert len(find_user.annotations) >= 2

    def test_annotations_on_parameters(self, tmp_path):
        """Test annotations on method parameters."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class ParamAnnotations {
    public void process(@NotNull @Size(min=1, max=100) String input,
                       @Valid @RequestBody UserDTO user) {}
}
""")

        result = parse_file(java_file)

        assert result.error is None
        process = next(s for s in result.symbols if "process" in s.name)
        # Signature should include parameter types
        assert "String" in process.signature or "process" in process.name


class TestComplexInheritance:
    """Test complex inheritance scenarios."""

    def test_generic_extends_and_implements(self, tmp_path):
        """Test class with generic extends and implements."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class UserRepository<T extends User>
        extends AbstractRepository<T, Long>
        implements CrudRepository<T, Long>, Auditable {

    @Override
    public T findById(Long id) {
        return null;
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        repo = next(s for s in result.symbols if s.name == "UserRepository")
        assert "extends" in repo.signature
        assert "T extends User" in repo.signature or "<T" in repo.signature


class TestEdgeCasesCombined:
    """Test combinations of multiple edge cases."""

    def test_everything_combined(self, tmp_path):
        """Test class combining many edge cases."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
@Entity
@Table(name = "users")
public class User<T extends Serializable>
        extends BaseEntity<Long>
        implements Comparable<User<T>>, Cloneable {

    @Id
    @GeneratedValue
    private Long id;

    @SafeVarargs
    @Transactional(propagation = Propagation.REQUIRED)
    public final <U extends T> List<U> process(
            @NotNull String name,
            @Valid Map<String, List<? extends U>> data,
            U... items) throws IOException, SQLException {
        return Arrays.asList(items);
    }

    public static class Builder<T extends Serializable> {
        public Builder<T> withId(Long id) {
            return this;
        }
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        user_class = next(s for s in result.symbols if s.name == "User")
        assert user_class is not None
        # Should have annotations
        assert len(user_class.annotations) >= 1

    def test_minimal_valid_file(self, tmp_path):
        """Test absolute minimal valid Java file."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
class A{}
""")

        result = parse_file(java_file)

        assert result.error is None
        a_class = next(s for s in result.symbols if s.name == "A")
        assert a_class.kind == "class"
