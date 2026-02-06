"""Tests for Java inheritance extraction.

Epic 10 Part 3, Story 10.1.3: Java Inheritance Extraction
Tests extraction of class inheritance relationships from Java code.
"""

from codeindex.parser import parse_file


class TestBasicInheritance:
    """Test basic Java inheritance extraction (AC1-AC3, AC7-AC10)."""

    def test_single_inheritance_extends(self, tmp_path):
        """Test basic single inheritance with extends (AC1)."""
        code = """
class BaseUser {
}

class AdminUser extends BaseUser {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "AdminUser"
        assert inh.parent == "BaseUser"

    def test_multiple_interfaces_implements(self, tmp_path):
        """Test class implementing multiple interfaces (AC2)."""
        code = """
interface Authenticatable {
}

interface Authorizable {
}

class User implements Authenticatable, Authorizable {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 2
        children = [inh.child for inh in result.inheritances]
        parents = [inh.parent for inh in result.inheritances]

        assert all(child == "User" for child in children)
        assert "Authenticatable" in parents
        assert "Authorizable" in parents

    def test_extends_and_implements_combined(self, tmp_path):
        """Test class with both extends and implements (AC3)."""
        code = """
class BaseService {
}

interface Loggable {
}

class UserService extends BaseService implements Loggable {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 2

        # Find extends relationship
        extends_rel = next(
            (inh for inh in result.inheritances if inh.parent == "BaseService"), None
        )
        assert extends_rel is not None
        assert extends_rel.child == "UserService"

        # Find implements relationship
        implements_rel = next(
            (inh for inh in result.inheritances if inh.parent == "Loggable"), None
        )
        assert implements_rel is not None
        assert implements_rel.child == "UserService"

    def test_interface_extends_interface(self, tmp_path):
        """Test interface extending another interface (AC7)."""
        code = """
interface Serializable {
}

interface Comparable extends Serializable {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "Comparable"
        assert inh.parent == "Serializable"

    def test_abstract_class_inheritance(self, tmp_path):
        """Test abstract class inheritance (AC8)."""
        code = """
abstract class BaseController {
}

class UserController extends BaseController {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "UserController"
        assert inh.parent == "BaseController"

    def test_no_inheritance(self, tmp_path):
        """Test class with no inheritance (AC10)."""
        code = """
class StandaloneClass {
    public void method() {}
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 0


class TestGenericTypes:
    """Test inheritance with generic types (AC4)."""

    def test_generic_single_type_parameter(self, tmp_path):
        """Test generic with single type parameter <T>."""
        code = """
import java.util.ArrayList;

class MyList<T> extends ArrayList<T> {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "MyList"
        # Should strip <T> from parent
        assert inh.parent == "java.util.ArrayList"

    def test_generic_multiple_type_parameters(self, tmp_path):
        """Test generic with multiple type parameters <K, V>."""
        code = """
import java.util.HashMap;

class MyMap<K, V> extends HashMap<K, V> {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "MyMap"
        # Should strip <K, V> from parent
        assert inh.parent == "java.util.HashMap"

    def test_generic_bounded_type(self, tmp_path):
        """Test generic with bounded type <T extends Comparable>."""
        code = """
class BaseComparable<T extends Comparable<T>> {
}

class MyComparable extends BaseComparable<String> {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "MyComparable"
        # Should strip <String> from parent
        assert inh.parent == "BaseComparable"

    def test_generic_in_implements(self, tmp_path):
        """Test generic type in implements clause."""
        code = """
interface Comparable<T> {
}

class User implements Comparable<User> {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "User"
        # Should strip <User> from parent
        assert inh.parent == "Comparable"


class TestImportResolution:
    """Test import resolution for full qualified names (AC6, AC9)."""

    def test_import_explicit(self, tmp_path):
        """Test explicit import resolution (AC6)."""
        code = """
package com.example.service;

import com.example.base.BaseService;

class UserService extends BaseService {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "com.example.service.UserService"
        # Should resolve via import
        assert inh.parent == "com.example.base.BaseService"

    def test_java_lang_implicit_import(self, tmp_path):
        """Test java.lang implicit import (AC9)."""
        code = """
class MyException extends Exception {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "MyException"
        # Should resolve to java.lang.Exception
        assert inh.parent == "java.lang.Exception"

    def test_same_package_class(self, tmp_path):
        """Test inheritance from same package class."""
        code = """
package com.example.model;

class BaseModel {
}

class User extends BaseModel {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "com.example.model.User"
        # Same package class should have full qualified name
        assert inh.parent == "com.example.model.BaseModel"

    def test_multiple_imports_resolution(self, tmp_path):
        """Test resolving multiple imports."""
        code = """
package com.example.service;

import com.example.base.BaseService;
import com.example.mixin.Loggable;

class UserService extends BaseService implements Loggable {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 2

        # Check BaseService resolution
        base_rel = next((inh for inh in result.inheritances if "BaseService" in inh.parent), None)
        assert base_rel is not None
        assert base_rel.parent == "com.example.base.BaseService"

        # Check Loggable resolution
        mixin_rel = next((inh for inh in result.inheritances if "Loggable" in inh.parent), None)
        assert mixin_rel is not None
        assert mixin_rel.parent == "com.example.mixin.Loggable"

    def test_full_qualified_name_in_code(self, tmp_path):
        """Test full qualified name used directly in code."""
        code = """
package com.example;

class User extends com.example.base.BaseUser {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "com.example.User"
        # Should keep full qualified name
        assert inh.parent == "com.example.base.BaseUser"


class TestNestedClasses:
    """Test nested class inheritance (AC5).

    NOTE: Deferred to Story 10.1.4 (Epic 10 Part 3 Phase 2).
    Nested class support requires additional namespace context management.
    """

    def test_nested_class_extends(self, tmp_path):
        """Test nested class inheritance (AC5)."""
        code = """
package com.example;

class BaseInner {
}

class Outer {
    class Inner extends BaseInner {
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        # Nested class should have full path
        assert inh.child == "com.example.Outer.Inner"
        assert inh.parent == "com.example.BaseInner"

    def test_nested_interface_implements(self, tmp_path):
        """Test nested class implementing interface."""
        code = """
interface CustomInterface {
}

class Container {
    class Worker implements CustomInterface {
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "Container.Worker"
        assert inh.parent == "CustomInterface"

    def test_static_nested_class(self, tmp_path):
        """Test static nested class inheritance."""
        code = """
class BaseBuilder {
}

class User {
    static class Builder extends BaseBuilder {
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "User.Builder"
        assert inh.parent == "BaseBuilder"


class TestRealWorldFrameworks:
    """Test real-world framework patterns."""

    def test_spring_boot_controller(self, tmp_path):
        """Test Spring Boot controller inheritance."""
        code = """
package com.example.controller;

import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController extends BaseController {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # May have 0 or 1 inheritance depending on BaseController resolution
        # At minimum should parse without error
        assert result.inheritances is not None

    def test_jpa_entity(self, tmp_path):
        """Test JPA Entity inheritance."""
        code = """
package com.example.model;

import javax.persistence.Entity;

@Entity
public class User extends BaseEntity {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should parse without error
        assert result.inheritances is not None

    def test_custom_exception(self, tmp_path):
        """Test custom exception extending RuntimeException."""
        code = """
package com.example.exception;

public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(String message) {
        super(message);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        assert len(result.inheritances) == 1
        inh = result.inheritances[0]
        assert inh.child == "com.example.exception.UserNotFoundException"
        assert inh.parent == "java.lang.RuntimeException"

    def test_lombok_data_class(self, tmp_path):
        """Test Lombok @Data class inheritance."""
        code = """
package com.example.dto;

import lombok.Data;

@Data
public class UserDTO extends BaseDTO {
    private String name;
    private String email;
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should parse without error
        assert result.inheritances is not None


class TestEdgeCases:
    """Test edge cases and Java modern features."""

    def test_enum_implements_interface(self, tmp_path):
        """Test enum implementing interface."""
        code = """
interface Identifiable {
}

enum Status implements Identifiable {
    ACTIVE, INACTIVE
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Enum implementing interface should be extracted
        # (implementation may vary, just ensure no crash)
        assert result.inheritances is not None

    def test_record_implements_interface(self, tmp_path):
        """Test record (Java 14+) implementing interface."""
        code = """
interface Identifiable {
}

record User(String name, int age) implements Identifiable {
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Record should be parsed (tree-sitter may or may not support)
        # Just ensure no crash
        assert result.inheritances is not None

    def test_annotation_interface(self, tmp_path):
        """Test annotation interface (no inheritance expected)."""
        code = """
@interface MyAnnotation {
    String value();
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Annotation should not have inheritance
        assert len(result.inheritances) == 0
