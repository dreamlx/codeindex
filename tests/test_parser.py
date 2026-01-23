"""Tests for the Python parser."""

import tempfile
from pathlib import Path

from codeindex.parser import parse_file


def test_parse_simple_function():
    """Test parsing a simple function."""
    code = '''
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.symbols) == 1
    assert result.symbols[0].name == "hello"
    assert result.symbols[0].kind == "function"
    assert "Say hello" in result.symbols[0].docstring


def test_parse_class_with_methods():
    """Test parsing a class with methods."""
    code = '''
class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.symbols) == 3  # class + 2 methods

    class_symbol = result.symbols[0]
    assert class_symbol.name == "Calculator"
    assert class_symbol.kind == "class"
    assert "simple calculator" in class_symbol.docstring

    method_names = [s.name for s in result.symbols if s.kind == "method"]
    assert "Calculator.add" in method_names
    assert "Calculator.subtract" in method_names


def test_parse_imports():
    """Test parsing import statements."""
    code = '''
import os
import sys
from pathlib import Path
from typing import List, Optional
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.imports) == 4

    modules = [imp.module for imp in result.imports]
    assert "os" in modules
    assert "sys" in modules
    assert "pathlib" in modules
    assert "typing" in modules


def test_parse_module_docstring():
    """Test parsing module-level docstring."""
    code = '''"""
This is a module docstring.
It spans multiple lines.
"""

def foo():
    pass
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert "module docstring" in result.module_docstring


def test_parse_nonexistent_file():
    """Test parsing a file that doesn't exist."""
    path = Path("/nonexistent/file.py")
    result = parse_file(path)

    assert result.error is not None
