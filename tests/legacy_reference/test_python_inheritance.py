"""Tests for Python inheritance extraction.

Epic 10, Story 10.1.1: Python Inheritance Extraction
Tests extraction of class inheritance relationships from Python code.
"""


from codeindex.parser import parse_file


class TestSingleInheritance:
    """Test single inheritance extraction."""

    def test_single_inheritance_basic(self, tmp_path):
        """Test basic single inheritance."""
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
        inh = result.inheritances[0]
        assert inh.child == "AdminUser"
        assert inh.parent == "BaseUser"

    def test_single_inheritance_with_module(self, tmp_path):
        """Test inheritance from external module."""
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
        """Test inheritance with qualified name."""
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
        # Should extract full qualified name
        assert "BaseModel" in result.inheritances[0].parent


class TestMultipleInheritance:
    """Test multiple inheritance extraction."""

    def test_multiple_inheritance_two_parents(self, tmp_path):
        """Test class with two parent classes."""
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

        # Should have 2 inheritance relationships
        user_inheritances = [inh for inh in result.inheritances if inh.child == "User"]
        assert len(user_inheritances) == 2

        parents = {inh.parent for inh in user_inheritances}
        assert "Loggable" in parents
        assert "Serializable" in parents

    def test_multiple_inheritance_three_parents(self, tmp_path):
        """Test class with three parent classes."""
        code = """
class AdminUser(BaseUser, PermissionMixin, Loggable):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        admin_inheritances = [inh for inh in result.inheritances if inh.child == "AdminUser"]
        assert len(admin_inheritances) == 3

        parents = {inh.parent for inh in admin_inheritances}
        assert "BaseUser" in parents
        assert "PermissionMixin" in parents
        assert "Loggable" in parents

    def test_multiple_inheritance_mixed_sources(self, tmp_path):
        """Test multiple inheritance from different sources."""
        code = """
from models import BaseModel
import utils

class User(BaseModel, utils.Loggable):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        user_inheritances = [inh for inh in result.inheritances if inh.child == "User"]
        assert len(user_inheritances) == 2


class TestNoInheritance:
    """Test classes without inheritance."""

    def test_no_inheritance(self, tmp_path):
        """Test class without parent."""
        code = """
class User:
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should have no inheritance relationships
        assert len(result.inheritances) == 0

    def test_multiple_classes_no_inheritance(self, tmp_path):
        """Test multiple classes without inheritance."""
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
        """Test nested class inheriting from external class."""
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

        inner_inheritances = [inh for inh in result.inheritances if "Inner" in inh.child]
        assert len(inner_inheritances) == 1
        assert inner_inheritances[0].child == "Outer.Inner"
        assert inner_inheritances[0].parent == "BaseInner"

    def test_nested_class_no_inheritance(self, tmp_path):
        """Test nested class without inheritance."""
        code = """
class Outer:
    class Inner:
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Nested class without inheritance
        inner_inheritances = [inh for inh in result.inheritances if "Inner" in inh.child]
        assert len(inner_inheritances) == 0

    def test_deeply_nested_inheritance(self, tmp_path):
        """Test deeply nested class inheritance."""
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

        inner_inheritances = [inh for inh in result.inheritances if "Inner" in inh.child]
        assert len(inner_inheritances) == 1
        assert inner_inheritances[0].child == "Outer.Middle.Inner"
        assert inner_inheritances[0].parent == "Base"


class TestGenericInheritance:
    """Test generic class inheritance (Python 3.12+)."""

    def test_generic_inheritance_basic(self, tmp_path):
        """Test generic class inheritance."""
        code = """
from typing import Generic, TypeVar

T = TypeVar('T')

class Container(Generic[T]):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        container_inheritances = [inh for inh in result.inheritances if inh.child == "Container"]
        assert len(container_inheritances) == 1
        assert "Generic" in container_inheritances[0].parent

    def test_generic_list_inheritance(self, tmp_path):
        """Test inheritance from generic List."""
        code = """
from typing import List

class UserList(List[str]):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        user_list_inheritances = [inh for inh in result.inheritances if inh.child == "UserList"]
        assert len(user_list_inheritances) == 1
        assert "List" in user_list_inheritances[0].parent

    def test_generic_multiple_type_params(self, tmp_path):
        """Test generic with multiple type parameters."""
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

        cache_inheritances = [inh for inh in result.inheritances if inh.child == "Cache"]
        assert len(cache_inheritances) == 1
        assert "Generic" in cache_inheritances[0].parent


class TestComplexScenarios:
    """Test complex inheritance scenarios."""

    def test_multiple_classes_mixed_inheritance(self, tmp_path):
        """Test file with multiple classes, some with inheritance."""
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

        # Should have 2 inheritance relationships (User->Base, Comment->Post)
        assert len(result.inheritances) == 2

        # Check User inheritance
        user_inh = [inh for inh in result.inheritances if inh.child == "User"]
        assert len(user_inh) == 1
        assert user_inh[0].parent == "Base"

        # Check Comment inheritance
        comment_inh = [inh for inh in result.inheritances if inh.child == "Comment"]
        assert len(comment_inh) == 1
        assert comment_inh[0].parent == "Post"

    def test_inheritance_chain(self, tmp_path):
        """Test inheritance chain."""
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

        # Should have 2 direct inheritance relationships
        assert len(result.inheritances) == 2

        # B inherits from A
        b_inh = [inh for inh in result.inheritances if inh.child == "B"]
        assert len(b_inh) == 1
        assert b_inh[0].parent == "A"

        # C inherits from B
        c_inh = [inh for inh in result.inheritances if inh.child == "C"]
        assert len(c_inh) == 1
        assert c_inh[0].parent == "B"

    def test_inheritance_with_methods(self, tmp_path):
        """Test that inheritance is extracted even with methods."""
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

        # Should still extract inheritance
        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Derived"
        assert result.inheritances[0].parent == "Base"


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_file(self, tmp_path):
        """Test empty file."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")

        result = parse_file(py_file)

        assert len(result.inheritances) == 0

    def test_no_classes(self, tmp_path):
        """Test file with no classes."""
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
        """Test inheritance extraction with comments."""
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
        """Test explicit inheritance from object (Python 2 style)."""
        code = """
class User(object):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract object as parent
        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "object"
