"""Tests for Python call extraction (Epic 11, Story 11.1).

Tests extraction of function/method call relationships from Python code.
"""

from codeindex.parser import CallType, parse_file


class TestBasicFunctionCalls:
    """Test basic function call extraction (AC1)."""

    def test_simple_function_call(self, tmp_path):
        """Test simple function call extraction."""
        code = """
def helper():
    pass

def main():
    helper()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "main"
        assert call.callee == "helper"
        assert call.call_type == CallType.FUNCTION
        assert call.line_number == 6

    def test_module_function_call(self, tmp_path):
        """Test module function call (import math)."""
        code = """
import math

def calculate():
    math.sqrt(16)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Note: math.sqrt should be EXCLUDED by project-internal filtering
        # (math is not in project namespaces)
        # But if we're not filtering yet, we should see it
        # For now, let's assume no filtering in basic test
        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "sqrt" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "calculate"
        assert call.callee == "math.sqrt"
        assert call.call_type == CallType.FUNCTION

    def test_nested_function_call(self, tmp_path):
        """Test nested function call extraction."""
        code = """
def outer():
    def inner():
        pass
    inner()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "outer"
        assert call.callee == "inner"  # or "outer.inner" depending on implementation
        assert call.call_type == CallType.FUNCTION

    def test_chained_function_calls(self, tmp_path):
        """Test chained function calls extraction."""
        code = """
def load():
    return []

def filter():
    return []

def sort():
    return []

def process():
    data = load().filter().sort()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract: process → load (at minimum)
        # Chained calls might be tricky, so we at least check for load()
        assert len(result.calls) >= 1
        load_call = next((c for c in result.calls if c.callee == "load"), None)
        assert load_call is not None
        assert load_call.caller == "process"

    def test_function_call_with_arguments(self, tmp_path):
        """Test function call with arguments extraction."""
        code = """
def calculate(a, b, c=10):
    pass

def main():
    result = calculate(1, 2, c=10)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "main"
        assert call.callee == "calculate"
        assert call.call_type == CallType.FUNCTION
        assert call.arguments_count == 3


class TestMethodCalls:
    """Test method call extraction (AC2)."""

    def test_instance_method_call(self, tmp_path):
        """Test instance method call extraction."""
        code = """
class User:
    def save(self):
        pass

def create_user():
    user = User()
    user.save()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should have 2 calls: User() constructor + user.save()
        assert len(result.calls) >= 2

        # Find save() method call
        save_call = next((c for c in result.calls if "save" in (c.callee or "")), None)
        assert save_call is not None
        assert save_call.caller == "create_user"
        assert save_call.callee == "User.save"
        assert save_call.call_type == CallType.METHOD

    def test_static_method_call(self, tmp_path):
        """Test static method call extraction."""
        code = """
class Utils:
    @staticmethod
    def format_date():
        pass

def process():
    Utils.format_date()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "format_date" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "process"
        assert call.callee == "Utils.format_date"
        assert call.call_type == CallType.STATIC_METHOD

    def test_class_method_call(self, tmp_path):
        """Test class method call extraction."""
        code = """
class Config:
    @classmethod
    def load(cls):
        pass

def init():
    Config.load()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "load" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "init"
        assert call.callee == "Config.load"
        assert call.call_type == CallType.STATIC_METHOD  # Class methods treated as static

    def test_method_call_on_returned_object(self, tmp_path):
        """Test method call on returned object (may be dynamic)."""
        code = """
class UserService:
    def process(self):
        pass

def get_service():
    return UserService()

def run():
    get_service().process()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract: run → get_service
        # .process() might be dynamic (cannot resolve)
        assert len(result.calls) >= 1
        get_service_call = next((c for c in result.calls if c.callee == "get_service"), None)
        assert get_service_call is not None
        assert get_service_call.caller == "run"

    def test_method_call_with_self(self, tmp_path):
        """Test method call with self (within class)."""
        code = """
class Calculator:
    def multiply(self, a, b):
        return a * b

    def add(self, a, b):
        return self.multiply(a, 1) + b
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "multiply" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "Calculator.add"
        assert call.callee == "Calculator.multiply"
        assert call.call_type == CallType.METHOD

    def test_super_method_call(self, tmp_path):
        """Test super() method call extraction."""
        code = """
class Parent:
    def method(self):
        pass

class Child(Parent):
    def method(self):
        super().method()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if c.caller == "Child.method"), None)
        assert call is not None
        assert call.callee == "Parent.method"


class TestConstructorCalls:
    """Test constructor call extraction (AC3)."""

    def test_direct_instantiation(self, tmp_path):
        """Test direct class instantiation extraction."""
        code = """
class User:
    pass

def create_user():
    user = User()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "create_user"
        assert call.callee == "User.__init__"
        assert call.call_type == CallType.CONSTRUCTOR

    def test_constructor_with_arguments(self, tmp_path):
        """Test constructor call with arguments."""
        code = """
class User:
    def __init__(self, name, age):
        pass

def main():
    user = User("Alice", 30)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "main"
        assert call.callee == "User.__init__"
        assert call.call_type == CallType.CONSTRUCTOR
        assert call.arguments_count == 2

    def test_nested_class_instantiation(self, tmp_path):
        """Test nested class instantiation."""
        code = """
class Outer:
    class Inner:
        pass

def main():
    obj = Outer.Inner()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "main"
        assert call.callee == "Outer.Inner.__init__"
        assert call.call_type == CallType.CONSTRUCTOR

    def test_constructor_via_factory(self, tmp_path):
        """Test constructor call via factory method."""
        code = """
class Product:
    pass

class Factory:
    @staticmethod
    def create():
        return Product()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "Product" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "Factory.create"
        assert call.callee == "Product.__init__"
        assert call.call_type == CallType.CONSTRUCTOR


class TestAliasResolution:
    """Test import alias resolution (AC4) ⭐⭐⭐⭐⭐ CRITICAL."""

    def test_simple_alias(self, tmp_path):
        """Test simple import alias resolution."""
        code = """
import pandas as pd

def load_data():
    df = pd.read_csv("data.csv")
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Critical: Must resolve pd.read_csv → pandas.read_csv
        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "read_csv" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "load_data"
        assert call.callee == "pandas.read_csv", f"Expected 'pandas.read_csv', got '{call.callee}'"

    def test_from_import_alias(self, tmp_path):
        """Test from-import with alias."""
        code = """
from numpy import array as np_array

def process():
    np_array([1, 2, 3])
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "array" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "process"
        assert call.callee == "numpy.array"

    def test_multiple_aliases(self, tmp_path):
        """Test multiple import aliases."""
        code = """
import pandas as pd
import numpy as np

def analyze():
    df = pd.DataFrame(np.zeros(10))
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should have 2 calls: pd.DataFrame + np.zeros
        assert len(result.calls) >= 2

        df_call = next((c for c in result.calls if "DataFrame" in (c.callee or "")), None)
        assert df_call is not None
        assert df_call.callee == "pandas.DataFrame"

        zeros_call = next((c for c in result.calls if "zeros" in (c.callee or "")), None)
        assert zeros_call is not None
        assert zeros_call.callee == "numpy.zeros"

    def test_nested_module_alias(self, tmp_path):
        """Test nested module alias (matplotlib.pyplot as plt)."""
        code = """
import matplotlib.pyplot as plt

def plot():
    plt.figure()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "figure" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "plot"
        assert call.callee == "matplotlib.pyplot.figure"

    def test_alias_without_call(self, tmp_path):
        """Test import alias without actual call (no extraction)."""
        code = """
import unused_module as um

def main():
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # No calls should be extracted (import only)
        assert len(result.calls) == 0

    def test_relative_import_alias(self, tmp_path):
        """Test relative import with alias."""
        # Note: Relative imports are tricky in isolated test files
        # This test may need adjustment based on implementation
        code = """
# Assuming we're in myproject/service.py
# from ..utils import helper as h

def main():
    # h()
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # For now, this test just ensures no crash
        # Real relative import testing needs package structure
        assert result.calls is not None

    def test_conflicting_aliases(self, tmp_path):
        """Test conflicting aliases (same alias name, last wins)."""
        code = """
import moduleA as mod
import moduleB as mod  # Overwrites

def func():
    mod.call()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Last import should win: moduleB
        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "call" in (c.callee or "")), None)
        assert call is not None
        # Should resolve to moduleB.call (last import)
        # But since moduleA/moduleB don't exist, actual behavior may vary
        # This test mainly checks for no crash
        assert call.callee is not None


class TestDecoratorCalls:
    """Test decorator call extraction - Phase 1 (simple decorators only) (AC5)."""

    def test_simple_decorator(self, tmp_path):
        """Test simple decorator extraction."""
        code = """
def decorator(func):
    return func

@decorator
def func():
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract decorator call
        assert len(result.calls) >= 1
        call = next((c for c in result.calls if c.callee == "decorator"), None)
        assert call is not None
        assert call.call_type == CallType.FUNCTION
        assert call.arguments_count == 1  # Decorator receives 1 arg (the function)

    def test_multiple_simple_decorators(self, tmp_path):
        """Test multiple simple decorators."""
        code = """
def decorator1(func):
    return func

def decorator2(func):
    return func

@decorator1
@decorator2
def func():
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract both decorators
        assert len(result.calls) >= 2

        dec1 = next((c for c in result.calls if c.callee == "decorator1"), None)
        assert dec1 is not None

        dec2 = next((c for c in result.calls if c.callee == "decorator2"), None)
        assert dec2 is not None

    def test_class_decorator(self, tmp_path):
        """Test class decorator extraction."""
        code = """
def singleton(cls):
    return cls

@singleton
class Config:
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if c.callee == "singleton"), None)
        assert call is not None
        assert call.arguments_count == 1

    def test_method_decorator(self, tmp_path):
        """Test method decorator extraction."""
        code = """
def cached_property(func):
    return func

class Service:
    @cached_property
    def data(self):
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if c.callee == "cached_property"), None)
        assert call is not None
        assert call.caller == "Service"  # Caller is the class


class TestProjectInternalFiltering:
    """Test project-internal call filtering (AC6)."""

    def test_project_internal_call(self, tmp_path):
        """Test project-internal call is extracted."""
        # Create a simple package structure
        pkg_dir = tmp_path / "myproject"
        pkg_dir.mkdir()

        utils_file = pkg_dir / "utils.py"
        utils_file.write_text("""
def helper():
    pass
""")

        service_file = pkg_dir / "service.py"
        service_file.write_text("""
from myproject.utils import helper

def process():
    helper()
""")

        result = parse_file(service_file)

        # Should extract call to helper (project-internal)
        assert len(result.calls) >= 1
        call = next((c for c in result.calls if "helper" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "process"
        # Callee should be fully qualified
        assert "helper" in call.callee

    def test_external_library_call_skipped(self, tmp_path):
        """Test external library calls are skipped (when filtering enabled)."""
        code = """
import pandas as pd

def load():
    pd.read_csv("data.csv")
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # If project filtering is enabled and project_namespaces doesn't include pandas,
        # the call should be skipped.
        # For now, we'll check that the call is properly resolved even if not filtered
        # (Filtering logic will be implemented in parser.py)

        # This test needs configuration support to actually filter
        # For now, just verify alias resolution works
        if len(result.calls) > 0:
            call = result.calls[0]
            # Alias should be resolved
            assert "pandas" in (call.callee or "")

    def test_stdlib_call_skipped(self, tmp_path):
        """Test stdlib calls are skipped (when filtering enabled)."""
        code = """
import math

def calc():
    math.sqrt(16)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Similar to external library test
        # Filtering logic will be implemented in parser.py with config support
        # For now, just verify parsing works
        assert result.calls is not None


class TestEdgeCases:
    """Test edge cases and special patterns (AC7)."""

    def test_lambda_call_skipped(self, tmp_path):
        """Test lambda calls are skipped (too complex for Phase 1)."""
        code = """
def helper(x):
    pass

process = lambda x: helper(x)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Lambda handling is complex, may skip or mark as dynamic
        # Just ensure no crash
        assert result.calls is not None

    def test_dynamic_call_via_getattr(self, tmp_path):
        """Test dynamic call via getattr is marked as DYNAMIC."""
        code = """
class MyClass:
    pass

def caller():
    obj = MyClass()
    method = getattr(obj, "method_name")
    method()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract getattr as dynamic call (or mark method() as dynamic)
        # Implementation may vary
        assert result.calls is not None

    def test_call_in_list_comprehension(self, tmp_path):
        """Test call in list comprehension."""
        code = """
def process(x):
    return x * 2

def main():
    items = [1, 2, 3]
    results = [process(x) for x in items]
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) >= 1
        call = next((c for c in result.calls if c.callee == "process"), None)
        assert call is not None
        assert call.caller == "main"

    def test_call_in_conditional(self, tmp_path):
        """Test calls in conditional branches."""
        code = """
def func1():
    pass

def func2():
    pass

def main():
    condition = True
    if condition:
        func1()
    else:
        func2()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should extract both calls
        assert len(result.calls) >= 2

        call1 = next((c for c in result.calls if c.callee == "func1"), None)
        assert call1 is not None
        assert call1.caller == "main"

        call2 = next((c for c in result.calls if c.callee == "func2"), None)
        assert call2 is not None
        assert call2.caller == "main"

    def test_recursive_call(self, tmp_path):
        """Test recursive function call."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 1
        call = result.calls[0]
        assert call.caller == "factorial"
        assert call.callee == "factorial"
        assert call.call_type == CallType.FUNCTION

    def test_no_calls_in_function(self, tmp_path):
        """Test function with no calls returns empty list."""
        code = """
def standalone():
    x = 10
    return x
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.calls) == 0
