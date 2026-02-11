"""Tests for Python inheritance extraction.

Auto-generated from: test_generator/specs/python.yaml
Generator: test_generator/generator.py
Template: test_generator/templates/inheritance_test.py.j2

DO NOT EDIT MANUALLY - changes will be overwritten.
To modify tests, edit the YAML spec and regenerate.
"""


from codeindex.parser import parse_file


class TestSingleInheritance:
    """Test single inheritance extraction."""

    def test_single_inheritance_basic(self, tmp_path):
        """Basic single inheritance."""
        code = """
class BaseUser:
    pass

class AdminUser(BaseUser):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "AdminUser"
        assert result.inheritances[0].parent == "BaseUser"

    def test_single_inheritance_with_module(self, tmp_path):
        """Inheritance from external module."""
        code = """
from models import BaseModel

class User(BaseModel):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "BaseModel"

    def test_single_inheritance_qualified(self, tmp_path):
        """Inheritance with qualified name (models.BaseModel)."""
        code = """
import models

class User(models.BaseModel):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert "BaseModel" in result.inheritances[0].parent

class TestMultipleInheritance:
    """Test multiple inheritance extraction."""

    def test_multiple_inheritance_two_parents(self, tmp_path):
        """Class with two parent classes."""
        code = """
class Loggable:
    pass

class Serializable:
    pass

class User(Loggable, Serializable):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 2
        user_parents = {inh.parent for inh in user_inh}
        assert "Loggable" in user_parents
        assert "Serializable" in user_parents

    def test_multiple_inheritance_three_parents(self, tmp_path):
        """Class with three parent classes."""
        code = """
class AdminUser(BaseUser, PermissionMixin, Loggable):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        adminuser_inh = [
            inh for inh in result.inheritances if inh.child == "AdminUser"
        ]
        assert len(adminuser_inh) == 3
        adminuser_parents = {inh.parent for inh in adminuser_inh}
        assert "BaseUser" in adminuser_parents
        assert "PermissionMixin" in adminuser_parents
        assert "Loggable" in adminuser_parents

    def test_multiple_inheritance_mixed_sources(self, tmp_path):
        """Multiple inheritance from different sources."""
        code = """
from models import BaseModel
import utils

class User(BaseModel, utils.Loggable):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 2

class TestNoInheritance:
    """Test classes without inheritance."""

    def test_no_inheritance(self, tmp_path):
        """Class without parent."""
        code = """
class User:
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 0

    def test_multiple_classes_no_inheritance(self, tmp_path):
        """Multiple classes without inheritance."""
        code = """
class User:
    pass

class Post:
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 0

class TestNestedClassInheritance:
    """Test nested class inheritance."""

    def test_nested_class_inherits_external(self, tmp_path):
        """Nested class inheriting from external class."""
        code = """
class BaseInner:
    pass

class Outer:
    class Inner(BaseInner):
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        filtered_inh = [
            inh for inh in result.inheritances
            if "Inner" in inh.child
        ]
        assert len(filtered_inh) == 1
        assert filtered_inh[0].child == "Outer.Inner"
        assert filtered_inh[0].parent == "BaseInner"

    def test_nested_class_no_inheritance(self, tmp_path):
        """Nested class without inheritance."""
        code = """
class Outer:
    class Inner:
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        filtered_inh = [
            inh for inh in result.inheritances
            if "Inner" in inh.child
        ]
        assert len(filtered_inh) == 0

    def test_deeply_nested_inheritance(self, tmp_path):
        """Deeply nested class inheritance (3 levels)."""
        code = """
class Base:
    pass

class Outer:
    class Middle:
        class Inner(Base):
            pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        filtered_inh = [
            inh for inh in result.inheritances
            if "Inner" in inh.child
        ]
        assert len(filtered_inh) == 1
        assert filtered_inh[0].child == "Outer.Middle.Inner"
        assert filtered_inh[0].parent == "Base"

class TestGenericInheritance:
    """Test generic class inheritance (Python 3.12+)."""

    def test_generic_inheritance_basic(self, tmp_path):
        """Generic class inheritance (typing.Generic)."""
        code = """
from typing import Generic, TypeVar

T = TypeVar('T')

class Container(Generic[T]):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        container_inh = [
            inh for inh in result.inheritances if inh.child == "Container"
        ]
        assert len(container_inh) == 1
        assert "Generic" in container_inh[0].parent

    def test_generic_list_inheritance(self, tmp_path):
        """Inheritance from generic List."""
        code = """
from typing import List

class UserList(List[str]):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        userlist_inh = [
            inh for inh in result.inheritances if inh.child == "UserList"
        ]
        assert len(userlist_inh) == 1
        assert "List" in userlist_inh[0].parent

    def test_generic_multiple_type_params(self, tmp_path):
        """Generic with multiple type parameters."""
        code = """
from typing import Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class Cache(Generic[K, V]):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        cache_inh = [
            inh for inh in result.inheritances if inh.child == "Cache"
        ]
        assert len(cache_inh) == 1
        assert "Generic" in cache_inh[0].parent

class TestComplexScenarios:
    """Test complex inheritance scenarios."""

    def test_multiple_classes_mixed_inheritance(self, tmp_path):
        """File with multiple classes, some with inheritance."""
        code = """
class Base:
    pass

class User(Base):
    pass

class Post:
    pass

class Comment(Post):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 2
        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 1
        user_parents = {inh.parent for inh in user_inh}
        assert "Base" in user_parents
        comment_inh = [
            inh for inh in result.inheritances if inh.child == "Comment"
        ]
        assert len(comment_inh) == 1
        comment_parents = {inh.parent for inh in comment_inh}
        assert "Post" in comment_parents

    def test_inheritance_chain(self, tmp_path):
        """Inheritance chain (A -> B -> C)."""
        code = """
class A:
    pass

class B(A):
    pass

class C(B):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 2
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
        assert "B" in c_parents

    def test_inheritance_with_methods(self, tmp_path):
        """Inheritance extracted even with methods."""
        code = """
class Base:
    def base_method(self):
        pass

class Derived(Base):
    def derived_method(self):
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Derived"
        assert result.inheritances[0].parent == "Base"

class TestEdgeCases:
    """Test edge cases."""

    def test_empty_file(self, tmp_path):
        """Empty file."""
        code = ""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 0

    def test_no_classes(self, tmp_path):
        """File with functions only, no classes."""
        code = """
def function():
    pass

variable = 42
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 0

    def test_inheritance_with_comments(self, tmp_path):
        """Inheritance extraction with comments."""
        code = """
# Base class
class Base:
    pass

# Derived class with inheritance
class Derived(Base):  # Inherits from Base
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Derived"
        assert result.inheritances[0].parent == "Base"

    def test_inheritance_from_object(self, tmp_path):
        """Explicit inheritance from object (Python 2 style)."""
        code = """
class User(object):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "object"

class TestAdvancedInheritance:
    """Test advanced inheritance patterns."""

    def test_abstract_base_class(self, tmp_path):
        """Abstract base class with ABC."""
        code = """
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def area(self):
        return 3.14
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 2
        shape_inh = [
            inh for inh in result.inheritances if inh.child == "Shape"
        ]
        assert len(shape_inh) == 1
        assert "ABC" in shape_inh[0].parent
        circle_inh = [
            inh for inh in result.inheritances if inh.child == "Circle"
        ]
        assert len(circle_inh) == 1
        circle_parents = {inh.parent for inh in circle_inh}
        assert "Shape" in circle_parents

    def test_dataclass_inheritance(self, tmp_path):
        """Dataclass inheritance."""
        code = """
from dataclasses import dataclass

@dataclass
class Base:
    name: str

@dataclass
class Child(Base):
    age: int
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Child"
        assert result.inheritances[0].parent == "Base"

    def test_enum_inheritance(self, tmp_path):
        """Enum class inheritance."""
        code = """
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        color_inh = [
            inh for inh in result.inheritances if inh.child == "Color"
        ]
        assert len(color_inh) == 1
        assert "Enum" in color_inh[0].parent

    def test_exception_hierarchy(self, tmp_path):
        """Custom exception hierarchy."""
        code = """
class AppError(Exception):
    pass

class ValidationError(AppError):
    pass

class NotFoundError(AppError):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 3
        apperror_inh = [
            inh for inh in result.inheritances if inh.child == "AppError"
        ]
        assert len(apperror_inh) == 1
        apperror_parents = {inh.parent for inh in apperror_inh}
        assert "Exception" in apperror_parents
        validationerror_inh = [
            inh for inh in result.inheritances if inh.child == "ValidationError"
        ]
        assert len(validationerror_inh) == 1
        validationerror_parents = {inh.parent for inh in validationerror_inh}
        assert "AppError" in validationerror_parents
        notfounderror_inh = [
            inh for inh in result.inheritances if inh.child == "NotFoundError"
        ]
        assert len(notfounderror_inh) == 1
        notfounderror_parents = {inh.parent for inh in notfounderror_inh}
        assert "AppError" in notfounderror_parents

    def test_mixin_pattern(self, tmp_path):
        """Mixin pattern with multiple inheritance."""
        code = """
class TimestampMixin:
    created_at = None

class SoftDeleteMixin:
    deleted = False

class Model(TimestampMixin, SoftDeleteMixin):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        model_inh = [
            inh for inh in result.inheritances if inh.child == "Model"
        ]
        assert len(model_inh) == 2
        model_parents = {inh.parent for inh in model_inh}
        assert "TimestampMixin" in model_parents
        assert "SoftDeleteMixin" in model_parents

    def test_diamond_inheritance(self, tmp_path):
        """Diamond inheritance pattern."""
        code = """
class A:
    pass

class B(A):
    pass

class C(A):
    pass

class D(B, C):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

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

    def test_protocol_inheritance(self, tmp_path):
        """Protocol class (Python 3.8+)."""
        code = """
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None:
        ...

class Widget(Drawable):
    def draw(self) -> None:
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 2
        drawable_inh = [
            inh for inh in result.inheritances if inh.child == "Drawable"
        ]
        assert len(drawable_inh) == 1
        assert "Protocol" in drawable_inh[0].parent
        widget_inh = [
            inh for inh in result.inheritances if inh.child == "Widget"
        ]
        assert len(widget_inh) == 1
        widget_parents = {inh.parent for inh in widget_inh}
        assert "Drawable" in widget_parents

    def test_metaclass_usage(self, tmp_path):
        """Class with metaclass."""
        code = """
class Singleton(type):
    pass

class MyClass(metaclass=Singleton):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        singleton_inh = [
            inh for inh in result.inheritances if inh.child == "Singleton"
        ]
        assert len(singleton_inh) == 1
        singleton_parents = {inh.parent for inh in singleton_inh}
        assert "type" in singleton_parents

    def test_class_with_decorators(self, tmp_path):
        """Decorated class with inheritance."""
        code = """
def my_decorator(cls):
    return cls

class Base:
    pass

@my_decorator
class Child(Base):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Child"
        assert result.inheritances[0].parent == "Base"
