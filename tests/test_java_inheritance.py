"""Tests for Java inheritance extraction.

Auto-generated from: test_generator/specs/java.yaml
Generator: test_generator/generator.py
Template: test_generator/templates/inheritance_test.py.j2

DO NOT EDIT MANUALLY - changes will be overwritten.
To modify tests, edit the YAML spec and regenerate.
"""


from codeindex.parser import parse_file


class TestBasicInheritance:
    """Test basic Java inheritance extraction."""

    def test_single_inheritance_extends(self, tmp_path):
        """Basic single inheritance with extends."""
        code = """
class BaseUser {
}

class AdminUser extends BaseUser {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "AdminUser"
        assert result.inheritances[0].parent == "BaseUser"

    def test_multiple_interfaces_implements(self, tmp_path):
        """Class implementing multiple interfaces."""
        code = """
interface Authenticatable {
}

interface Authorizable {
}

class User implements Authenticatable, Authorizable {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 2
        user_parents = {inh.parent for inh in user_inh}
        assert "Authenticatable" in user_parents
        assert "Authorizable" in user_parents

    def test_extends_and_implements_combined(self, tmp_path):
        """Class with both extends and implements."""
        code = """
class BaseService {
}

interface Loggable {
}

class UserService extends BaseService implements Loggable {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        userservice_inh = [
            inh for inh in result.inheritances if inh.child == "UserService"
        ]
        assert len(userservice_inh) == 2
        userservice_parents = {inh.parent for inh in userservice_inh}
        assert "BaseService" in userservice_parents
        assert "Loggable" in userservice_parents

    def test_interface_extends_interface(self, tmp_path):
        """Interface extending another interface."""
        code = """
interface Serializable {
}

interface Comparable extends Serializable {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Comparable"
        assert result.inheritances[0].parent == "Serializable"

    def test_abstract_class_inheritance(self, tmp_path):
        """Abstract class inheritance."""
        code = """
abstract class BaseController {
}

class UserController extends BaseController {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "UserController"
        assert result.inheritances[0].parent == "BaseController"

    def test_no_inheritance(self, tmp_path):
        """Class with no inheritance."""
        code = """
class StandaloneClass {
    public void method() {}
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0

class TestGenericTypes:
    """Test inheritance with generic types."""

    def test_generic_single_type_parameter(self, tmp_path):
        """Generic with single type parameter."""
        code = """
import java.util.ArrayList;

class MyList<T> extends ArrayList<T> {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "MyList"
        assert result.inheritances[0].parent == "java.util.ArrayList"

    def test_generic_multiple_type_parameters(self, tmp_path):
        """Generic with multiple type parameters."""
        code = """
import java.util.HashMap;

class MyMap<K, V> extends HashMap<K, V> {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "MyMap"
        assert result.inheritances[0].parent == "java.util.HashMap"

    def test_generic_bounded_type(self, tmp_path):
        """Generic with bounded type parameter."""
        code = """
class BaseComparable<T extends Comparable<T>> {
}

class MyComparable extends BaseComparable<String> {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "MyComparable"
        assert result.inheritances[0].parent == "BaseComparable"

    def test_generic_in_implements(self, tmp_path):
        """Generic type in implements clause."""
        code = """
interface Comparable<T> {
}

class User implements Comparable<User> {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "Comparable"

class TestImportResolution:
    """Test import resolution for fully qualified names."""

    def test_import_explicit(self, tmp_path):
        """Explicit import resolution."""
        code = """
package com.example.service;

import com.example.base.BaseService;

class UserService extends BaseService {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "com.example.service.UserService"
        assert result.inheritances[0].parent == "com.example.base.BaseService"

    def test_java_lang_implicit_import(self, tmp_path):
        """java.lang implicit import (Exception)."""
        code = """
class MyException extends Exception {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "MyException"
        assert result.inheritances[0].parent == "java.lang.Exception"

    def test_same_package_class(self, tmp_path):
        """Inheritance from same package class."""
        code = """
package com.example.model;

class BaseModel {
}

class User extends BaseModel {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "com.example.model.User"
        assert result.inheritances[0].parent == "com.example.model.BaseModel"

    def test_multiple_imports_resolution(self, tmp_path):
        """Resolving multiple imports."""
        code = """
package com.example.service;

import com.example.base.BaseService;
import com.example.mixin.Loggable;

class UserService extends BaseService implements Loggable {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        com_example_service_userservice_inh = [
            inh for inh in result.inheritances if inh.child == "com.example.service.UserService"
        ]
        assert len(com_example_service_userservice_inh) == 2
        com_example_service_userservice_parents = {inh.parent for inh in com_example_service_userservice_inh}
        assert "com.example.base.BaseService" in com_example_service_userservice_parents
        assert "com.example.mixin.Loggable" in com_example_service_userservice_parents

    def test_full_qualified_name_in_code(self, tmp_path):
        """Full qualified name used directly in code."""
        code = """
package com.example;

class User extends com.example.base.BaseUser {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "com.example.User"
        assert result.inheritances[0].parent == "com.example.base.BaseUser"

class TestNestedClasses:
    """Test nested class inheritance."""

    def test_nested_class_extends(self, tmp_path):
        """Nested class inheritance."""
        code = """
package com.example;

class BaseInner {
}

class Outer {
    class Inner extends BaseInner {
    }
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "com.example.Outer.Inner"
        assert result.inheritances[0].parent == "com.example.BaseInner"

    def test_nested_interface_implements(self, tmp_path):
        """Nested class implementing interface."""
        code = """
interface CustomInterface {
}

class Container {
    class Worker implements CustomInterface {
    }
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Container.Worker"
        assert result.inheritances[0].parent == "CustomInterface"

    def test_static_nested_class(self, tmp_path):
        """Static nested class inheritance."""
        code = """
class BaseBuilder {
}

class User {
    static class Builder extends BaseBuilder {
    }
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User.Builder"
        assert result.inheritances[0].parent == "BaseBuilder"

class TestRealWorldFrameworks:
    """Test real-world framework patterns."""

    def test_spring_boot_controller(self, tmp_path):
        """Spring Boot controller inheritance."""
        code = """
package com.example.controller;

import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController extends BaseController {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert result.inheritances is not None

    def test_jpa_entity(self, tmp_path):
        """JPA Entity inheritance."""
        code = """
package com.example.model;

import javax.persistence.Entity;

@Entity
public class User extends BaseEntity {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert result.inheritances is not None

    def test_custom_exception(self, tmp_path):
        """Custom exception extending RuntimeException."""
        code = """
package com.example.exception;

public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(String message) {
        super(message);
    }
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "com.example.exception.UserNotFoundException"
        assert result.inheritances[0].parent == "java.lang.RuntimeException"

    def test_lombok_data_class(self, tmp_path):
        """Lombok @Data class inheritance."""
        code = """
package com.example.dto;

import lombok.Data;

@Data
public class UserDTO extends BaseDTO {
    private String name;
    private String email;
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert result.inheritances is not None

class TestEdgeCases:
    """Test edge cases and Java modern features."""

    def test_enum_implements_interface(self, tmp_path):
        """Enum implementing interface."""
        code = """
interface Identifiable {
}

enum Status implements Identifiable {
    ACTIVE, INACTIVE
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert result.inheritances is not None

    def test_record_implements_interface(self, tmp_path):
        """Record (Java 14+) implementing interface."""
        code = """
interface Identifiable {
}

record User(String name, int age) implements Identifiable {
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert result.inheritances is not None

    def test_annotation_interface(self, tmp_path):
        """Annotation interface (no inheritance expected)."""
        code = """
@interface MyAnnotation {
    String value();
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0

class TestAdvancedJavaInheritance:
    """Test advanced Java inheritance patterns."""

    def test_diamond_inheritance(self, tmp_path):
        """Diamond inheritance pattern via interfaces."""
        code = """
interface A {}
interface B extends A {}
interface C extends A {}
class D implements B, C {}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 4
        b_inh = [
            inh for inh in result.inheritances if inh.child == "B"
        ]
        assert len(b_inh) == 1
        b_parents = {inh.parent for inh in b_inh}
        assert "A" in b_parents
        c_inh = [
            inh for inh in result.inheritances if inh.child == "C"
        ]
        assert len(c_inh) == 1
        c_parents = {inh.parent for inh in c_inh}
        assert "A" in c_parents
        d_inh = [
            inh for inh in result.inheritances if inh.child == "D"
        ]
        assert len(d_inh) == 2
        d_parents = {inh.parent for inh in d_inh}
        assert "B" in d_parents
        assert "C" in d_parents

    def test_sealed_class(self, tmp_path):
        """Sealed class (Java 17+)."""
        code = """
sealed class Shape permits Circle, Rectangle {}
final class Circle extends Shape {}
non-sealed class Rectangle extends Shape {}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert result.inheritances is not None

    def test_wildcard_extends(self, tmp_path):
        """Wildcard extends in generic superclass."""
        code = """
import java.util.AbstractList;

class ReadOnlyList<T> extends AbstractList<T> {
    public T get(int index) { return null; }
    public int size() { return 0; }
}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "ReadOnlyList"
        assert result.inheritances[0].parent == "java.util.AbstractList"

    def test_multiple_extends_interfaces(self, tmp_path):
        """Interface extending multiple interfaces."""
        code = """
interface Readable {}
interface Writable {}

interface ReadWritable extends Readable, Writable {}
"""
        test_file = tmp_path / "test.java"
        test_file.write_text(code)

        result = parse_file(test_file)

        readwritable_inh = [
            inh for inh in result.inheritances if inh.child == "ReadWritable"
        ]
        assert len(readwritable_inh) == 2
        readwritable_parents = {inh.parent for inh in readwritable_inh}
        assert "Readable" in readwritable_parents
        assert "Writable" in readwritable_parents
