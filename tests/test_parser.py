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


# ==================== PHP Parser Tests ====================

def test_parse_php_class_with_inheritance():
    """Test parsing PHP class with extends and implements."""
    code = '''<?php
abstract class AgentController extends BaseController implements JsonSerializable {
    public function create(): Response {
        return new Response();
    }
}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.symbols) == 2  # class + method

    class_sym = result.symbols[0]
    assert class_sym.name == "AgentController"
    assert class_sym.kind == "class"
    assert "abstract" in class_sym.signature
    assert "extends BaseController" in class_sym.signature
    assert "implements JsonSerializable" in class_sym.signature


def test_parse_php_method_visibility():
    """Test parsing PHP methods with visibility modifiers."""
    code = '''<?php
class Service {
    public function publicMethod(): void {}
    private function privateMethod(): string {}
    protected static function protectedStatic(): int {}
}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    methods = [s for s in result.symbols if s.kind == "method"]
    assert len(methods) == 3

    signatures = {s.name.split("::")[-1]: s.signature for s in methods}
    assert "public function publicMethod(): void" in signatures["publicMethod"]
    assert "private function privateMethod(): string" in signatures["privateMethod"]
    assert "protected static function protectedStatic(): int" in signatures["protectedStatic"]


def test_parse_php_properties():
    """Test parsing PHP class properties."""
    code = '''<?php
class Model {
    private $id;
    protected static $instance;
    public string $name;
    public ?int $age;
}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    props = [s for s in result.symbols if s.kind == "property"]
    assert len(props) == 4

    signatures = {s.name.split("::")[-1]: s.signature for s in props}
    assert "private $id" in signatures["$id"]
    assert "protected static $instance" in signatures["$instance"]
    assert "public string $name" in signatures["$name"]
    assert "public ?int $age" in signatures["$age"]


def test_parse_php_function():
    """Test parsing standalone PHP function."""
    code = '''<?php
function helper(string $input): array {
    return [$input];
}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.symbols) == 1
    func = result.symbols[0]
    assert func.name == "helper"
    assert func.kind == "function"
    assert "function helper(string $input): array" in func.signature


def test_parse_php_namespace():
    """Test parsing PHP namespace declaration."""
    code = '''<?php
namespace App\\Controller;

class UserController {}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert result.namespace == "App\\Controller"


def test_parse_php_use_statements():
    """Test parsing PHP use statements."""
    code = '''<?php
namespace App\\Controller;

use App\\Service\\UserService;
use App\\Model\\User as UserModel;
use Illuminate\\Http\\Request;

class TestController {}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.imports) == 3

    modules = [imp.module for imp in result.imports]
    assert "App\\Service\\UserService" in modules
    assert "App\\Model\\User" in modules
    assert "Illuminate\\Http\\Request" in modules

    # Check alias
    user_import = [imp for imp in result.imports if imp.module == "App\\Model\\User"][0]
    assert "UserModel" in user_import.names


def test_parse_php_group_use():
    """Test parsing PHP group use statements."""
    code = '''<?php
use App\\Repository\\{UserRepository, OrderRepository};

class Test {}
'''
    with tempfile.NamedTemporaryFile(mode="w", suffix=".php", delete=False) as f:
        f.write(code)
        f.flush()
        path = Path(f.name)

    result = parse_file(path)
    path.unlink()

    assert result.error is None
    assert len(result.imports) == 2

    modules = [imp.module for imp in result.imports]
    assert "App\\Repository\\UserRepository" in modules
    assert "App\\Repository\\OrderRepository" in modules
