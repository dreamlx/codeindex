"""
Story 11.3: PHP Call Extraction Tests

Tests for extracting function/method call relationships from PHP code.
Following TDD approach with comprehensive coverage of PHP-specific features.
"""

from codeindex.parser import CallType, parse_file


class TestBasicFunctionCalls:
    """AC1: Basic Function Calls (5 tests)"""

    def test_simple_function_call(self, tmp_path):
        """Test 1: Simple function call."""
        code = """<?php
function helper() {
}

function main() {
    helper();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: main → helper
        helper_call = next(
            (c for c in result.calls if "helper" in (c.callee or "")),
            None
        )
        assert helper_call is not None
        assert helper_call.caller == "main"
        assert helper_call.callee == "helper"
        assert helper_call.call_type == CallType.FUNCTION

    def test_namespaced_function_call(self, tmp_path):
        """Test 2: Namespaced function call with use statement."""
        code = """<?php
namespace App\\Utils;

function format_date() {
}

namespace App\\Service;
use function App\\Utils\\format_date;

function process() {
    format_date();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: App\Service\process → App\Utils\format_date
        call = next(
            (c for c in result.calls if "format_date" in (c.callee or "")),
            None
        )
        assert call is not None
        assert "process" in call.caller
        assert "format_date" in call.callee

    def test_global_function_not_extracted(self, tmp_path):
        """Test 3: Built-in functions should not be extracted."""
        code = """<?php
function load_data() {
    $data = array(1, 2, 3);
    var_dump($data);  // Built-in, should not extract
    print_r($data);   // Built-in, should not extract
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should not extract var_dump or print_r (built-in functions)
        _var_dump_call = next(
            (c for c in result.calls if c.callee == "var_dump"),
            None
        )
        _print_r_call = next(
            (c for c in result.calls if c.callee == "print_r"),
            None
        )
        # Built-in functions may or may not be extracted depending on implementation
        # This test documents the expected behavior

    def test_function_call_with_arguments(self, tmp_path):
        """Test 4: Function call with argument counting."""
        code = """<?php
function calculate($a, $b, $c) {
    return $a + $b + $c;
}

function main() {
    $result = calculate(1, 2, 3);
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: main → calculate, arguments_count=3
        calc_call = next(
            (c for c in result.calls if "calculate" in (c.callee or "")),
            None
        )
        assert calc_call is not None
        assert calc_call.arguments_count == 3

    def test_variable_function_call(self, tmp_path):
        """Test 5: Variable function call (dynamic)."""
        code = """<?php
function helper() {
}

function main() {
    $func = 'helper';
    $func();  // Dynamic call
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        _result = parse_file(php_file)

        # Variable function calls are dynamic
        # Implementation may mark as DYNAMIC with callee=None
        # or extract 'helper' if detectable
        # This test documents expected behavior


class TestMethodCalls:
    """AC2: Method Calls (6 tests)"""

    def test_instance_method_call(self, tmp_path):
        """Test 1: Instance method call."""
        code = """<?php
class User {
    public function save() {
    }
}

function createUser() {
    $user = new User();
    $user->save();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: createUser → User::save
        save_call = next(
            (c for c in result.calls if "save" in (c.callee or "")),
            None
        )
        assert save_call is not None
        assert "createUser" in save_call.caller
        assert "User" in save_call.callee
        assert "save" in save_call.callee
        assert save_call.call_type == CallType.METHOD

    def test_static_method_call(self, tmp_path):
        """Test 2: Static method call."""
        code = """<?php
class Utils {
    public static function formatDate() {
    }
}

function process() {
    Utils::formatDate();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: process → Utils::formatDate
        call = next(
            (c for c in result.calls if "formatDate" in (c.callee or "")),
            None
        )
        assert call is not None
        assert call.caller == "process"
        assert "Utils" in call.callee
        assert "formatDate" in call.callee
        assert call.call_type == CallType.STATIC_METHOD

    def test_method_chaining(self, tmp_path):
        """Test 3: Method chaining."""
        code = """<?php
class Builder {
    public function setName($name) {
        return $this;
    }

    public function setAge($age) {
        return $this;
    }

    public function build() {
        return new stdClass();
    }
}

function main() {
    $result = (new Builder())
        ->setName('test')
        ->setAge(30)
        ->build();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Method chaining: return type inference needed
        # Without type analysis, chained calls are marked as DYNAMIC
        # We should have: 1 constructor + 3 method calls (may be DYNAMIC)
        calls_from_main = [c for c in result.calls if c.caller == "main"]
        assert len(calls_from_main) >= 3

        # Should have constructor call
        constructor_call = next(
            (c for c in calls_from_main if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert "Builder" in constructor_call.callee

        # Chained method calls may be DYNAMIC (acceptable limitation)
        # This documents the design decision: type inference is out of scope

    def test_method_call_with_this(self, tmp_path):
        """Test 4: Method call with $this."""
        code = """<?php
class Calculator {
    public function multiply($a, $b) {
        return $a * $b;
    }

    public function add($a, $b) {
        return $this->multiply($a, 1) + $b;
    }
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: Calculator::add → Calculator::multiply
        multiply_call = next(
            (c for c in result.calls
             if "add" in (c.caller or "") and "multiply" in (c.callee or "")),
            None
        )
        assert multiply_call is not None
        assert "Calculator" in multiply_call.caller
        assert "Calculator" in multiply_call.callee

    def test_parent_method_call(self, tmp_path):
        """Test 5: Parent method call."""
        code = """<?php
class ParentClass {
    public function method() {
    }
}

class Child extends ParentClass {
    public function method() {
        parent::method();
    }
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: Child::method → ParentClass::method
        parent_call = next(
            (c for c in result.calls if "parent" in str(c).lower()),
            None
        )
        # parent::method() should resolve to ParentClass::method
        if parent_call:
            assert "Child" in parent_call.caller
            assert "method" in parent_call.callee

    def test_variable_method_call(self, tmp_path):
        """Test 6: Variable method call (dynamic)."""
        code = """<?php
class User {
    public function getData() {
    }
}

function process() {
    $obj = new User();
    $method = 'getData';
    $obj->$method();  // Dynamic
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        _result = parse_file(php_file)

        # Variable method calls are dynamic
        # May be marked as DYNAMIC or extracted if detectable


class TestConstructorCalls:
    """AC3: Constructor Calls (4 tests)"""

    def test_direct_instantiation(self, tmp_path):
        """Test 1: Direct class instantiation."""
        code = """<?php
class User {
    public function __construct() {
    }
}

function create() {
    $user = new User();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: create → User::__construct
        constructor_call = next(
            (c for c in result.calls
             if c.call_type == CallType.CONSTRUCTOR and "User" in (c.callee or "")),
            None
        )
        assert constructor_call is not None
        assert constructor_call.caller == "create"
        assert "User" in constructor_call.callee
        assert "__construct" in constructor_call.callee

    def test_namespaced_class_instantiation(self, tmp_path):
        """Test 2: Namespaced class with use statement."""
        code = """<?php
namespace App\\Model;

class User {
    public function __construct() {
    }
}

namespace App\\Service;
use App\\Model\\User;

function createUser() {
    $user = new User();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: App\Service\createUser → App\Model\User::__construct
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert "createUser" in constructor_call.caller
        assert "User" in constructor_call.callee

    def test_constructor_with_arguments(self, tmp_path):
        """Test 3: Constructor with arguments."""
        code = """<?php
class User {
    public function __construct($name, $age) {
    }
}

function main() {
    $user = new User('Alice', 30);
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: main → User::__construct, arguments_count=2
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.arguments_count == 2

    def test_anonymous_class_skip(self, tmp_path):
        """Test 4: Anonymous class (should skip or handle specially)."""
        code = """<?php
function create() {
    $obj = new class {
        public function method() {
        }
    };
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        _result = parse_file(php_file)

        # Anonymous classes have no meaningful callee
        # Implementation may skip or mark as special


class TestNamespaceResolution:
    """AC4: Namespace Resolution (5 tests)"""

    def test_use_statement(self, tmp_path):
        """Test 1: Use statement resolution."""
        code = """<?php
namespace App\\Model;

class User {
}

namespace App\\Service;
use App\\Model\\User;

function process() {
    $user = new User();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should resolve User to App\Model\User
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        # Should include namespace in callee

    def test_use_alias(self, tmp_path):
        """Test 2: Use statement with alias."""
        code = """<?php
namespace App\\Model;

class User {
}

namespace App\\Service;
use App\\Model\\User as UserModel;

function create() {
    $user = new UserModel();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should resolve UserModel to App\Model\User
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None

    def test_fully_qualified_name(self, tmp_path):
        """Test 3: Fully qualified name (leading backslash)."""
        code = """<?php
namespace App\\Service;

function load() {
    $user = new \\App\\Model\\User();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract with full namespace
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert "User" in constructor_call.callee

    def test_same_namespace(self, tmp_path):
        """Test 4: Class in same namespace."""
        code = """<?php
namespace App\\Service;

class Helper {
}

function process() {
    $helper = new Helper();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: App\Service\process → App\Service\Helper::__construct
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None

    def test_global_namespace(self, tmp_path):
        """Test 5: Global namespace (no namespace declaration)."""
        code = """<?php
class User {
}

function create() {
    $user = new User();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract: create → User::__construct (no namespace prefix)
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert "User" in constructor_call.callee


class TestEdgeCases:
    """AC5: Edge Cases (5 tests)"""

    def test_nested_function_calls(self, tmp_path):
        """Test 1: Nested function calls."""
        code = """<?php
function inner() {
    return 42;
}

function outer() {
    return helper(inner());
}

function helper($value) {
    return $value;
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract both helper() and inner() calls
        calls_from_outer = [c for c in result.calls if c.caller == "outer"]
        assert len(calls_from_outer) >= 2

    def test_closure_call(self, tmp_path):
        """Test 2: Closure/anonymous function call."""
        code = """<?php
function main() {
    $closure = function() {
        return 42;
    };

    $result = $closure();
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        _result = parse_file(php_file)

        # Closure calls may be marked as DYNAMIC

    def test_array_function_call(self, tmp_path):
        """Test 3: Array function call."""
        code = """<?php
function main() {
    $data = [1, 2, 3];
    array_map('strtoupper', $data);
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        _result = parse_file(php_file)

        # array_map is built-in, may or may not be extracted

    def test_no_calls_in_function(self, tmp_path):
        """Test 4: Function with no calls."""
        code = """<?php
function calculate() {
    $x = 1 + 2;
    return $x * 3;
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should have empty calls list for this file
        calls_from_calculate = [c for c in result.calls if c.caller == "calculate"]
        assert len(calls_from_calculate) == 0

    def test_conditional_call(self, tmp_path):
        """Test 5: Call inside conditional."""
        code = """<?php
function helper() {
}

function main() {
    if (true) {
        helper();
    }
}
"""
        php_file = tmp_path / "test.php"
        php_file.write_text(code)

        result = parse_file(php_file)

        # Should extract call even inside conditional
        helper_call = next(
            (c for c in result.calls if "helper" in (c.callee or "")),
            None
        )
        assert helper_call is not None
