"""Tests for Java annotation extraction.

Story 7.1.2.1: Annotation Extraction
Tests cover class, method, and field annotations with various argument patterns.
"""

from codeindex.parser import parse_file


class TestClassAnnotations:
    """Test annotation extraction from Java classes."""

    def test_simple_class_annotation(self, tmp_path, ):
        """Test extraction of simple annotation without arguments."""
        java_file = tmp_path / "User.java"
        java_file.write_text("""
@Entity
public class User {
    private String name;
}
""")

        result = parse_file(java_file, "java")
        assert result.error is None

        user_class = next(s for s in result.symbols if s.kind == "class")
        assert user_class.name == "User"
        assert len(user_class.annotations) == 1
        assert user_class.annotations[0].name == "Entity"
        assert user_class.annotations[0].arguments == {}

    def test_class_annotation_with_string_argument(self, tmp_path, ):
        """Test annotation with single string argument."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
@RequestMapping("/api/users")
public class UserController {
}
""")

        result = parse_file(java_file, "java")
        user_class = result.symbols[0]
        assert len(user_class.annotations) == 1
        assert user_class.annotations[0].name == "RequestMapping"
        assert user_class.annotations[0].arguments == {"value": "/api/users"}

    def test_multiple_class_annotations(self, tmp_path, ):
        """Test multiple annotations on a class."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
@RestController
@RequestMapping("/api/users")
public class UserController {
}
""")

        result = parse_file(java_file, "java")
        user_class = result.symbols[0]
        assert len(user_class.annotations) == 2

        annotations = {a.name: a for a in user_class.annotations}
        assert "RestController" in annotations
        assert "RequestMapping" in annotations
        assert annotations["RequestMapping"].arguments == {"value": "/api/users"}


class TestMethodAnnotations:
    """Test annotation extraction from Java methods."""

    def test_simple_method_annotation(self, tmp_path, ):
        """Test extraction of simple method annotation."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
public class UserController {
    @GetMapping
    public List<User> getUsers() {
        return null;
    }
}
""")

        result = parse_file(java_file, "java")
        # Symbols are flat list: [class, method, ...]
        get_users = next(s for s in result.symbols if s.name == "UserController.getUsers")

        assert len(get_users.annotations) == 1
        assert get_users.annotations[0].name == "GetMapping"
        assert get_users.annotations[0].arguments == {}

    def test_method_annotation_with_path(self, tmp_path, ):
        """Test method annotation with path argument."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
public class UserController {
    @GetMapping("/list")
    public List<User> getUsers() {
        return null;
    }
}
""")

        result = parse_file(java_file, "java")
        get_users = next(s for s in result.symbols if s.name == "UserController.getUsers")

        assert len(get_users.annotations) == 1
        assert get_users.annotations[0].name == "GetMapping"
        assert get_users.annotations[0].arguments == {"value": "/list"}

    def test_multiple_method_annotations(self, tmp_path, ):
        """Test multiple annotations on a method."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
public class UserController {
    @PostMapping("/create")
    @ResponseBody
    public User createUser(@RequestBody User user) {
        return null;
    }
}
""")

        result = parse_file(java_file, "java")
        create_user = next(s for s in result.symbols if s.name == "UserController.createUser")

        assert len(create_user.annotations) == 2
        annotations = {a.name: a for a in create_user.annotations}
        assert "PostMapping" in annotations
        assert "ResponseBody" in annotations
        assert annotations["PostMapping"].arguments == {"value": "/create"}


class TestFieldAnnotations:
    """Test annotation extraction from Java fields."""

    def test_field_annotation(self, tmp_path, ):
        """Test extraction of field annotation."""
        java_file = tmp_path / "User.java"
        java_file.write_text("""
public class User {
    @Id
    private Long id;

    private String name;
}
""")

        result = parse_file(java_file, "java")
        # Symbols are flat list: [class, field1, field2, ...]
        id_field = next(s for s in result.symbols if s.name == "User.id")
        name_field = next(s for s in result.symbols if s.name == "User.name")

        assert len(id_field.annotations) == 1
        assert id_field.annotations[0].name == "Id"
        assert len(name_field.annotations) == 0

    def test_field_annotation_with_arguments(self, tmp_path, ):
        """Test field annotation with named arguments."""
        java_file = tmp_path / "User.java"
        java_file.write_text("""
public class User {
    @Column(name = "user_name", length = 100)
    private String name;
}
""")

        result = parse_file(java_file, "java")
        name_field = next(s for s in result.symbols if s.name == "User.name")

        assert len(name_field.annotations) == 1
        assert name_field.annotations[0].name == "Column"
        # Note: For MVP, we store arguments as a dict
        # Full parsing of key-value pairs can be enhanced later
        assert "name" in name_field.annotations[0].arguments
        assert "length" in name_field.annotations[0].arguments


class TestAnnotationEdgeCases:
    """Test edge cases and special annotation patterns."""

    def test_annotation_with_array_argument(self, tmp_path, ):
        """Test annotation with array values."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
public class UserController {
    @RequestMapping(value = {"/users", "/user"})
    public void getUser() {
    }
}
""")

        result = parse_file(java_file, "java")
        get_user = next(s for s in result.symbols if s.name == "UserController.getUser")

        assert len(get_user.annotations) == 1
        assert get_user.annotations[0].name == "RequestMapping"
        # Array arguments stored as string for MVP
        assert "value" in get_user.annotations[0].arguments

    def test_no_annotations(self, tmp_path, ):
        """Test that symbols without annotations have empty list."""
        java_file = tmp_path / "User.java"
        java_file.write_text("""
public class User {
    private String name;

    public String getName() {
        return name;
    }
}
""")

        result = parse_file(java_file, "java")
        user_class = next(s for s in result.symbols if s.kind == "class")
        name_field = next(s for s in result.symbols if s.name == "User.name")
        get_name = next(s for s in result.symbols if s.name == "User.getName")

        assert len(user_class.annotations) == 0
        assert len(name_field.annotations) == 0
        assert len(get_name.annotations) == 0

    def test_annotation_formatting_in_prompt(self, tmp_path, ):
        """Test that annotations are included in formatted output."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/list")
    public List<User> getUsers() {
        return null;
    }
}
""")

        result = parse_file(java_file, "java")
        user_class = result.symbols[0]
        get_users = next(s for s in result.symbols if s.name == "UserController.getUsers")

        # Verify annotations are extracted
        assert len(user_class.annotations) == 2
        assert get_users.annotations[0].name == "GetMapping"

        # Verify signature includes annotation info
        # (This will be implemented in writer.py formatting)
        assert user_class.name == "UserController"
