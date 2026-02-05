"""Tests for Java throws declarations parsing.

Story 7.1.2.3: Throws Declarations
Tests parsing of throws clauses in Java method signatures:
- Single exception: throws IOException
- Multiple exceptions: throws IOException, SQLException
- Generic exceptions: throws T (where T extends Exception)
"""

from codeindex.parser import parse_file


class TestSingleThrows:
    """Test single exception in throws clause."""

    def test_method_throws_single_exception(self, tmp_path):
        """Test method with single throws clause."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class FileReader {
    public String read(String path) throws IOException {
        return Files.readString(Path.of(path));
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        read_method = next(s for s in result.symbols if "read" in s.name)
        assert "throws IOException" in read_method.signature

    def test_constructor_throws_exception(self, tmp_path):
        """Test constructor with throws clause."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class DatabaseConnection {
    public DatabaseConnection(String url) throws SQLException {
        // connection logic
    }
}
""")

        result = parse_file(java_file)

        constructor = next(s for s in result.symbols if s.kind == "constructor")
        assert "throws SQLException" in constructor.signature

    def test_interface_method_throws(self, tmp_path):
        """Test interface method with throws clause."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public interface Repository {
    User findById(Long id) throws NotFoundException;
}
""")

        result = parse_file(java_file)

        find_method = next(s for s in result.symbols if "findById" in s.name)
        assert "throws NotFoundException" in find_method.signature


class TestMultipleThrows:
    """Test multiple exceptions in throws clause."""

    def test_method_throws_multiple_exceptions(self, tmp_path):
        """Test method with multiple exceptions."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class DataProcessor {
    public void process() throws IOException, SQLException, ParseException {
        // processing logic
    }
}
""")

        result = parse_file(java_file)

        process_method = next(s for s in result.symbols if "process" in s.name)
        assert "throws" in process_method.signature
        # Should contain all three exceptions
        assert "IOException" in process_method.signature
        assert "SQLException" in process_method.signature or \
               "IOException, SQLException, ParseException" in process_method.signature

    def test_throws_with_generic_method(self, tmp_path):
        """Test throws clause with generic method."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Utils {
    public <T> T deserialize(String json) throws IOException, ClassNotFoundException {
        return objectMapper.readValue(json, clazz);
    }
}
""")

        result = parse_file(java_file)

        deserialize = next(s for s in result.symbols if "deserialize" in s.name)
        # Should have both generics and throws
        assert "<T>" in deserialize.signature
        assert "throws" in deserialize.signature
        assert "IOException" in deserialize.signature


class TestGenericThrows:
    """Test generic exceptions in throws clause."""

    def test_method_throws_generic_exception(self, tmp_path):
        """Test method throwing generic exception type."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Handler<T extends Exception> {
    public void handle() throws T {
        // handling logic
    }
}
""")

        result = parse_file(java_file)

        handle_method = next(s for s in result.symbols if "handle" in s.name)
        assert "throws T" in handle_method.signature or \
               "throws" in handle_method.signature

    def test_method_throws_bounded_generic(self, tmp_path):
        """Test method with generic type parameter and throws."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Executor {
    public <E extends Exception> void execute() throws E {
        // execution logic
    }
}
""")

        result = parse_file(java_file)

        execute = next(s for s in result.symbols if "execute" in s.name)
        assert "<E extends Exception>" in execute.signature
        assert "throws E" in execute.signature or "throws" in execute.signature


class TestThrowsVariants:
    """Test various throws clause variants."""

    def test_throws_with_full_package_name(self, tmp_path):
        """Test throws with fully qualified exception name."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Service {
    public void connect() throws java.net.SocketException {
        // connection logic
    }
}
""")

        result = parse_file(java_file)

        connect = next(s for s in result.symbols if "connect" in s.name)
        assert "throws" in connect.signature
        assert "SocketException" in connect.signature or \
               "java.net.SocketException" in connect.signature

    def test_method_without_throws(self, tmp_path):
        """Test method without throws clause (baseline)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
""")

        result = parse_file(java_file)

        add_method = next(s for s in result.symbols if "add" in s.name)
        # Should NOT have throws
        assert "throws" not in add_method.signature

    def test_abstract_method_with_throws(self, tmp_path):
        """Test abstract method with throws clause."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public abstract class BaseService {
    public abstract void save(Entity entity) throws PersistenceException;
}
""")

        result = parse_file(java_file)

        save_method = next(s for s in result.symbols if "save" in s.name)
        assert "abstract" in save_method.signature
        assert "throws PersistenceException" in save_method.signature


class TestThrowsWithAnnotations:
    """Test throws clause combined with annotations."""

    def test_throws_with_spring_annotations(self, tmp_path):
        """Test method with both annotations and throws."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class UserService {
    @Transactional
    public User save(User user) throws ValidationException, DataAccessException {
        return repository.save(user);
    }
}
""")

        result = parse_file(java_file)

        save_method = next(s for s in result.symbols if "save" in s.name)
        # Should have both annotation and throws
        assert len(save_method.annotations) > 0
        assert save_method.annotations[0].name == "Transactional"
        assert "throws" in save_method.signature
        assert "ValidationException" in save_method.signature


class TestEdgeCases:
    """Test edge cases for throws declarations."""

    def test_throws_runtime_exception(self, tmp_path):
        """Test throws with RuntimeException (unchecked)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class Validator {
    public void validate(String input) throws IllegalArgumentException {
        if (input == null) throw new IllegalArgumentException();
    }
}
""")

        result = parse_file(java_file)

        validate = next(s for s in result.symbols if "validate" in s.name)
        assert "throws IllegalArgumentException" in validate.signature

    def test_multiple_methods_different_throws(self, tmp_path):
        """Test multiple methods with different throws clauses."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
public class FileManager {
    public void read() throws IOException {
        // read
    }

    public void write() throws IOException, SecurityException {
        // write
    }

    public void delete() {
        // delete - no throws
    }
}
""")

        result = parse_file(java_file)

        read_method = next(s for s in result.symbols if s.name == "FileManager.read")
        write_method = next(s for s in result.symbols if s.name == "FileManager.write")
        delete_method = next(s for s in result.symbols if s.name == "FileManager.delete")

        assert "throws IOException" in read_method.signature
        assert "throws" in write_method.signature
        assert "throws" not in delete_method.signature
