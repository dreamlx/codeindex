"""Tests for Java Lombok annotation support.

Story 7.1.3.4: Lombok Support
Tests parser's ability to handle Lombok annotations:
- @Data, @Getter, @Setter
- @AllArgsConstructor, @NoArgsConstructor, @RequiredArgsConstructor
- @Builder, @ToString, @EqualsAndHashCode
- @Slf4j, @Log
- Field-level and class-level annotations
- Lombok with other annotations (JPA, Spring)
"""

from codeindex.parser import parse_file


class TestBasicLombokAnnotations:
    """Test basic Lombok annotations."""

    def test_data_annotation(self, tmp_path):
        """Test @Data annotation (generates getters, setters, toString, etc.)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Data;

@Data
public class User {
    private Long id;
    private String name;
    private String email;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        user_class = next(s for s in result.symbols if s.name == "User")
        assert user_class is not None
        # Should capture @Data annotation
        assert any(a.name == "Data" for a in user_class.annotations)

    def test_getter_setter_annotations(self, tmp_path):
        """Test @Getter and @Setter annotations."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class Person {
    private String firstName;
    private String lastName;
    private int age;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        person = next(s for s in result.symbols if s.name == "Person")
        assert person is not None
        # Should have both annotations
        assert any(a.name == "Getter" for a in person.annotations)
        assert any(a.name == "Setter" for a in person.annotations)

    def test_field_level_lombok_annotations(self, tmp_path):
        """Test Lombok annotations on individual fields."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Getter;
import lombok.Setter;

public class Product {
    @Getter @Setter
    private Long id;

    @Getter
    private String name;

    private double price;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        product = next(s for s in result.symbols if s.name == "Product")
        assert product is not None


class TestConstructorAnnotations:
    """Test Lombok constructor annotations."""

    def test_all_args_constructor(self, tmp_path):
        """Test @AllArgsConstructor annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.AllArgsConstructor;

@AllArgsConstructor
public class Book {
    private String title;
    private String author;
    private int year;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        book = next(s for s in result.symbols if s.name == "Book")
        assert any(a.name == "AllArgsConstructor" for a in book.annotations)

    def test_no_args_constructor(self, tmp_path):
        """Test @NoArgsConstructor annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.NoArgsConstructor;

@NoArgsConstructor
public class Empty {
    private String field;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        empty = next(s for s in result.symbols if s.name == "Empty")
        assert any(a.name == "NoArgsConstructor" for a in empty.annotations)

    def test_required_args_constructor(self, tmp_path):
        """Test @RequiredArgsConstructor annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class Service {
    private final UserRepository repository;
    private final EmailService emailService;
    private String optionalField;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        service = next(s for s in result.symbols if s.name == "Service")
        assert any(a.name == "RequiredArgsConstructor" for a in service.annotations)

    def test_multiple_constructor_annotations(self, tmp_path):
        """Test multiple constructor annotations."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@AllArgsConstructor
public class Entity {
    private Long id;
    private String name;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        entity = next(s for s in result.symbols if s.name == "Entity")
        assert any(a.name == "NoArgsConstructor" for a in entity.annotations)
        assert any(a.name == "AllArgsConstructor" for a in entity.annotations)


class TestBuilderAnnotation:
    """Test @Builder annotation."""

    def test_builder_annotation(self, tmp_path):
        """Test @Builder annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Builder;

@Builder
public class UserDTO {
    private Long id;
    private String username;
    private String email;
    private boolean active;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        dto = next(s for s in result.symbols if s.name == "UserDTO")
        assert any(a.name == "Builder" for a in dto.annotations)

    def test_builder_with_data(self, tmp_path):
        """Test @Builder combined with @Data."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class Account {
    private Long accountId;
    private String accountNumber;
    private double balance;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        account = next(s for s in result.symbols if s.name == "Account")
        assert any(a.name == "Builder" for a in account.annotations)
        assert any(a.name == "Data" for a in account.annotations)


class TestUtilityAnnotations:
    """Test utility Lombok annotations."""

    def test_tostring_annotation(self, tmp_path):
        """Test @ToString annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.ToString;

@ToString
public class LogEntry {
    private String timestamp;
    private String message;
    private String level;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        log_entry = next(s for s in result.symbols if s.name == "LogEntry")
        assert any(a.name == "ToString" for a in log_entry.annotations)

    def test_equals_and_hashcode_annotation(self, tmp_path):
        """Test @EqualsAndHashCode annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.EqualsAndHashCode;

@EqualsAndHashCode
public class Identifier {
    private String id;
    private String type;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        identifier = next(s for s in result.symbols if s.name == "Identifier")
        assert any(a.name == "EqualsAndHashCode" for a in identifier.annotations)

    def test_tostring_with_exclude(self, tmp_path):
        """Test @ToString with parameters."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.ToString;

@ToString(exclude = {"password", "secret"})
public class SecureUser {
    private String username;
    private String password;
    private String secret;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        secure = next(s for s in result.symbols if s.name == "SecureUser")
        assert any(a.name == "ToString" for a in secure.annotations)


class TestLoggingAnnotations:
    """Test Lombok logging annotations."""

    def test_slf4j_annotation(self, tmp_path):
        """Test @Slf4j annotation (generates logger field)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class UserService {
    public void processUser() {
        log.info("Processing user");
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        service = next(s for s in result.symbols if s.name == "UserService")
        assert any(a.name == "Slf4j" for a in service.annotations)

    def test_log_annotation(self, tmp_path):
        """Test @Log annotation."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.extern.java.Log;

@Log
public class LegacyService {
    public void process() {
        log.info("Processing");
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        legacy = next(s for s in result.symbols if s.name == "LegacyService")
        assert any(a.name == "Log" for a in legacy.annotations)


class TestLombokWithJPA:
    """Test Lombok combined with JPA annotations."""

    def test_lombok_with_jpa_entity(self, tmp_path):
        """Test Lombok annotations combined with JPA."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import javax.persistence.*;

@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String username;

    @Column(nullable = false)
    private String email;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        user = next(s for s in result.symbols if s.name == "User")
        # Should have both JPA and Lombok annotations
        assert any(a.name == "Entity" for a in user.annotations)
        assert any(a.name == "Data" for a in user.annotations)
        assert any(a.name == "NoArgsConstructor" for a in user.annotations)


class TestLombokWithSpring:
    """Test Lombok combined with Spring annotations."""

    def test_lombok_with_spring_service(self, tmp_path):
        """Test Lombok annotations with Spring."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;

    public User createUser(UserDTO dto) {
        log.info("Creating user: {}", dto.getUsername());
        return userRepository.save(new User(dto));
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        service = next(s for s in result.symbols if s.name == "UserService")
        # Should have both Spring and Lombok annotations
        assert any(a.name == "Service" for a in service.annotations)
        assert any(a.name == "Slf4j" for a in service.annotations)
        assert any(a.name == "RequiredArgsConstructor" for a in service.annotations)

    def test_lombok_with_spring_controller(self, tmp_path):
        """Test Lombok with Spring REST controller."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        controller = next(s for s in result.symbols if s.name == "UserController")
        assert any(a.name == "RestController" for a in controller.annotations)
        assert any(a.name == "RequiredArgsConstructor" for a in controller.annotations)


class TestComplexLombokScenarios:
    """Test complex Lombok usage scenarios."""

    def test_all_lombok_annotations_combined(self, tmp_path):
        """Test class with many Lombok annotations."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.*;
import lombok.extern.slf4j.Slf4j;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@ToString(exclude = "password")
@EqualsAndHashCode(of = "id")
@Slf4j
public class CompleteUser {
    private Long id;
    private String username;
    private String email;
    private String password;
    private boolean active;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        user = next(s for s in result.symbols if s.name == "CompleteUser")
        # Should capture multiple Lombok annotations
        assert len(user.annotations) >= 5
        assert any(a.name == "Data" for a in user.annotations)
        assert any(a.name == "Builder" for a in user.annotations)

    def test_lombok_inheritance(self, tmp_path):
        """Test Lombok with class inheritance."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class Employee extends Person {
    private String employeeId;
    private String department;
    private double salary;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        employee = next(s for s in result.symbols if s.name == "Employee")
        assert any(a.name == "Data" for a in employee.annotations)
        assert any(a.name == "EqualsAndHashCode" for a in employee.annotations)
        # Should capture extends clause
        assert "extends Person" in employee.signature


class TestLombokEdgeCases:
    """Test Lombok edge cases."""

    def test_lombok_val_and_var(self, tmp_path):
        """Test Lombok val and var (local variable type inference)."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
import lombok.val;
import lombok.var;

public class TypeInference {
    public void example() {
        val name = "John";  // final String
        var count = 10;     // int (mutable)
        val list = new ArrayList<String>();
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        # Should parse successfully (val/var are method body, not symbols)
        type_inf = next(s for s in result.symbols if s.name == "TypeInference")
        assert type_inf is not None

    def test_lombok_without_imports(self, tmp_path):
        """Test Lombok annotations with fully qualified names."""
        java_file = tmp_path / "test.java"
        java_file.write_text("""
@lombok.Data
public class NoImports {
    private String field;
}
""")

        result = parse_file(java_file)

        assert result.error is None
        no_imports = next(s for s in result.symbols if s.name == "NoImports")
        # Should recognize lombok.Data
        assert any("Data" in a.name for a in no_imports.annotations)
