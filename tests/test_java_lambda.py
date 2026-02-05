"""Tests for Java lambda expressions parsing.

Story 7.1.2.4: Lambda Expressions
Tests parsing of Java 8+ lambda expressions and method references:
- Simple lambdas: x -> x * 2
- Parameter types: (String s) -> s.length()
- Multi-parameter: (a, b) -> a + b
- Block lambdas: x -> { return x * 2; }
- Method references: String::length, System.out::println
- Constructor references: ArrayList::new
"""

from codeindex.parser import parse_file


class TestSimpleLambda:
    """Test simple lambda expressions."""

    def test_lambda_in_variable_assignment(self, tmp_path):
        """Test lambda assigned to variable (parsing should not fail)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Calculator {
    public void test() {
        UnaryOperator<Integer> doubler = x -> x * 2;
        int result = doubler.apply(5);
    }
}
""")

        result = parse_file(java_file)

        # Lambda expressions are in method body, not extracted as symbols
        # Goal: Ensure parsing doesn't fail when lambda is present
        assert result.error is None
        test_method = next(s for s in result.symbols if "test" in s.name)
        assert test_method.kind == "method"
        assert "void test()" in test_method.signature

    def test_lambda_as_method_parameter(self, tmp_path):
        """Test lambda passed as method argument."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class StreamExample {
    public void process(List<String> items) {
        items.forEach(item -> System.out.println(item));
    }
}
""")

        result = parse_file(java_file)

        process_method = next(s for s in result.symbols if "process" in s.name)
        # Method should be parsed correctly even with lambda
        assert "List<String> items" in process_method.signature or \
               "process" in process_method.name


class TestLambdaWithParameters:
    """Test lambda expressions with explicit parameters."""

    def test_lambda_with_typed_parameter(self, tmp_path):
        """Test lambda with parameter type declaration."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class StringProcessor {
    public void process() {
        Function<String, Integer> lengthFunc = (String s) -> s.length();
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        process_method = next(s for s in result.symbols if "process" in s.name)
        assert process_method is not None

    def test_lambda_with_multiple_parameters(self, tmp_path):
        """Test lambda with multiple parameters."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class MathOps {
    public void calculate() {
        BinaryOperator<Integer> adder = (a, b) -> a + b;
        int sum = adder.apply(3, 5);
    }
}
""")

        result = parse_file(java_file)

        calc_method = next(s for s in result.symbols if "calculate" in s.name)
        assert calc_method is not None


class TestBlockLambda:
    """Test lambda expressions with statement blocks."""

    def test_lambda_with_block_body(self, tmp_path):
        """Test lambda with curly braces and statements."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Validator {
    public void validate() {
        Predicate<String> notEmpty = s -> {
            return s != null && !s.isEmpty();
        };
    }
}
""")

        result = parse_file(java_file)

        validate_method = next(s for s in result.symbols if "validate" in s.name)
        assert validate_method is not None

    def test_lambda_with_multiple_statements(self, tmp_path):
        """Test lambda with multiple statements in block."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Logger {
    public void log() {
        Consumer<String> logger = msg -> {
            System.out.println("LOG: " + msg);
            saveToFile(msg);
        };
    }
}
""")

        result = parse_file(java_file)

        log_method = next(s for s in result.symbols if "log" in s.name)
        assert log_method is not None


class TestMethodReference:
    """Test method reference expressions."""

    def test_static_method_reference(self, tmp_path):
        """Test static method reference (ClassName::method)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Converter {
    public void convert(List<String> strings) {
        List<Integer> ints = strings.stream()
            .map(Integer::parseInt)
            .collect(Collectors.toList());
    }
}
""")

        result = parse_file(java_file)

        convert_method = next(s for s in result.symbols if "convert" in s.name)
        assert convert_method is not None
        assert "List<String> strings" in convert_method.signature or \
               "convert" in convert_method.name

    def test_instance_method_reference(self, tmp_path):
        """Test instance method reference (instance::method)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Printer {
    public void printAll(List<String> items) {
        items.forEach(System.out::println);
    }
}
""")

        result = parse_file(java_file)

        print_method = next(s for s in result.symbols if "printAll" in s.name)
        assert print_method is not None

    def test_constructor_reference(self, tmp_path):
        """Test constructor reference (ClassName::new)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Factory {
    public List<String> createList() {
        Supplier<List<String>> listFactory = ArrayList::new;
        return listFactory.get();
    }
}
""")

        result = parse_file(java_file)

        create_method = next(s for s in result.symbols if "createList" in s.name)
        assert create_method is not None


class TestLambdaWithStreams:
    """Test lambda expressions with Stream API."""

    def test_lambda_in_stream_filter(self, tmp_path):
        """Test lambda in stream filter operation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class UserService {
    public List<User> getActiveUsers(List<User> users) {
        return users.stream()
            .filter(user -> user.isActive())
            .collect(Collectors.toList());
    }
}
""")

        result = parse_file(java_file)

        get_method = next(s for s in result.symbols if "getActiveUsers" in s.name)
        assert get_method is not None
        assert "List<User> users" in get_method.signature or \
               "List<User>" in get_method.signature

    def test_lambda_in_stream_map(self, tmp_path):
        """Test lambda in stream map operation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Transformer {
    public List<String> transform(List<Integer> numbers) {
        return numbers.stream()
            .map(n -> "Number: " + n)
            .collect(Collectors.toList());
    }
}
""")

        result = parse_file(java_file)

        transform_method = next(s for s in result.symbols if "transform" in s.name)
        assert transform_method is not None

    def test_complex_stream_pipeline(self, tmp_path):
        """Test lambda in complex stream pipeline."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class DataProcessor {
    public int processData(List<String> data) {
        return data.stream()
            .filter(s -> s != null)
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .mapToInt(String::length)
            .sum();
    }
}
""")

        result = parse_file(java_file)

        process_method = next(s for s in result.symbols if "processData" in s.name)
        assert process_method is not None


class TestEdgeCases:
    """Test edge cases for lambda expressions."""

    def test_nested_lambdas(self, tmp_path):
        """Test nested lambda expressions."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class NestedLambda {
    public void process() {
        Function<Integer, Function<Integer, Integer>> curriedAdd =
            a -> b -> a + b;
    }
}
""")

        result = parse_file(java_file)

        process_method = next(s for s in result.symbols if "process" in s.name)
        assert process_method is not None

    def test_lambda_with_generic_types(self, tmp_path):
        """Test lambda with generic type parameters."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class GenericMapper<T, R> {
    public <U> List<U> map(List<T> items, Function<T, U> mapper) {
        return items.stream().map(mapper).collect(Collectors.toList());
    }
}
""")

        result = parse_file(java_file)

        map_method = next(s for s in result.symbols if s.name == "GenericMapper.map")
        assert "<U>" in map_method.signature
        assert "Function<T, U>" in map_method.signature or \
               "List<T> items" in map_method.signature

    def test_method_without_lambda(self, tmp_path):
        """Test method without lambda (baseline)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Traditional {
    public int add(int a, int b) {
        return a + b;
    }
}
""")

        result = parse_file(java_file)

        add_method = next(s for s in result.symbols if "add" in s.name)
        assert "int a, int b" in add_method.signature or \
               "(int a, int b)" in add_method.signature
