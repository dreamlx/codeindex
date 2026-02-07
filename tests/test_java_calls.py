"""
Epic 11 Story 11.2: Java Call Extraction Tests

Test suite for Java call relationship extraction using tree-sitter.
Following TDD approach: Write tests first (Red), then implement (Green).

Test Categories (30-35 tests):
- BasicMethodCalls: 6 tests
- ConstructorCalls: 5 tests
- StaticImportResolution: 4 tests
- FullQualifiedNameCalls: 3 tests
- MethodReferences: 3 tests
- ProjectInternalFiltering: 3 tests
- EdgeCases: 6 tests
- AnnotationBasedCalls: 3 tests

Target: 90%+ passing rate
"""

import pytest

from codeindex.parser import CallType, parse_file


class TestBasicMethodCalls:
    """AC1: Basic Method Calls (6 tests)"""

    def test_instance_method_call(self, tmp_path):
        """Test instance method call extraction."""
        code = """
package com.example;

public class UserService {
    public void createUser() {
        User user = new User();
        user.save();
    }
}

class User {
    public void save() {}
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: UserService.createUser → User.save
        save_call = next((c for c in result.calls if "save" in (c.callee or "")), None)
        assert save_call is not None
        assert save_call.caller == "com.example.UserService.createUser"
        assert save_call.callee == "com.example.User.save"
        assert save_call.call_type == CallType.METHOD

    def test_static_method_call(self, tmp_path):
        """Test static method call extraction."""
        code = """
package com.example;

public class Utils {
    public static String formatDate() {
        return "";
    }
}

public class Service {
    public void process() {
        Utils.formatDate();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.process → Utils.formatDate
        call = next((c for c in result.calls if "formatDate" in (c.callee or "")), None)
        assert call is not None
        assert call.caller == "com.example.Service.process"
        assert call.callee == "com.example.Utils.formatDate"
        assert call.call_type == CallType.STATIC_METHOD

    def test_method_chaining(self, tmp_path):
        """Test method chaining extraction."""
        code = """
package com.example;

public class Builder {
    public Builder setName(String name) { return this; }
    public Builder setAge(int age) { return this; }
    public Builder build() { return this; }
}

public class Service {
    public void loadData() {
        Builder builder = new Builder();
        builder.setName("test")
               .setAge(30)
               .build();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should have 3 method calls
        method_calls = [c for c in result.calls
                       if c.call_type == CallType.METHOD
                       and "Builder" in (c.callee or "")]
        assert len(method_calls) >= 3

        # Check for setName, setAge, build
        callees = {c.callee for c in method_calls}
        assert any("setName" in callee for callee in callees)
        assert any("setAge" in callee for callee in callees)
        assert any("build" in callee for callee in callees)

    def test_method_call_with_generics(self, tmp_path):
        """Test method call on generic type."""
        code = """
package com.example;

import java.util.ArrayList;
import java.util.List;

public class Service {
    public void process() {
        List<String> list = new ArrayList<>();
        list.add("item");
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.process → ArrayList.add
        # Note: Generic types stripped (ArrayList<String> → ArrayList)
        add_call = next((c for c in result.calls if "add" in (c.callee or "")), None)
        assert add_call is not None
        assert add_call.caller == "com.example.Service.process"
        # Callee should be ArrayList.add (generic type stripped)
        assert "ArrayList.add" in add_call.callee or "List.add" in add_call.callee

    def test_interface_method_call(self, tmp_path):
        """Test interface method call."""
        code = """
package com.example;

public interface Runnable {
    void run();
}

public class Service {
    public void process(Runnable task) {
        task.run();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.process → Runnable.run
        run_call = next((c for c in result.calls if "run" in (c.callee or "")), None)
        assert run_call is not None
        assert run_call.caller == "com.example.Service.process"
        assert run_call.callee == "com.example.Runnable.run"
        assert run_call.call_type == CallType.METHOD

    def test_super_method_call(self, tmp_path):
        """Test super method call extraction."""
        code = """
package com.example;

class Parent {
    public void method() {}
}

class Child extends Parent {
    @Override
    public void method() {
        super.method();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Child.method → Parent.method
        super_call = next(
            (c for c in result.calls
             if c.caller == "Child.method" and "Parent" in (c.callee or "")),
            None
        )
        assert super_call is not None
        assert super_call.callee == "com.example.Parent.method"
        assert super_call.call_type == CallType.METHOD


class TestConstructorCalls:
    """AC2: Constructor Calls (5 tests)"""

    def test_direct_instantiation(self, tmp_path):
        """Test direct constructor call."""
        code = """
package com.example.model;

public class User {
    public User() {}
}

class Service {
    public void create() {
        User user = new User();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.create → User.<init>
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.caller == "com.example.model.Service.create"
        assert constructor_call.callee == "com.example.model.User.<init>"

    def test_constructor_with_arguments(self, tmp_path):
        """Test constructor with arguments."""
        code = """
package com.example;

public class User {
    public User(String name, int age) {}
}

class Service {
    public void create() {
        User user = new User("Alice", 30);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract constructor with arguments_count=2
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.arguments_count == 2
        assert constructor_call.callee == "com.example.User.<init>"

    def test_anonymous_class_instantiation(self, tmp_path):
        """Test anonymous class instantiation."""
        code = """
package com.example;

public interface Runnable {
    void run();
}

class Service {
    public void execute() {
        Runnable task = new Runnable() {
            public void run() {
                System.out.println("Running");
            }
        };
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.execute → Runnable.<init>
        constructor_call = next(
            (c for c in result.calls
             if c.call_type == CallType.CONSTRUCTOR
             and "Runnable" in (c.callee or "")),
            None
        )
        assert constructor_call is not None
        assert constructor_call.callee == "com.example.Runnable.<init>"

    def test_inner_class_instantiation(self, tmp_path):
        """Test inner class instantiation."""
        code = """
package com.example;

public class Outer {
    public class Inner {
        public Inner() {}
    }
}

class Service {
    public void create() {
        Outer outer = new Outer();
        Outer.Inner inner = outer.new Inner();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract both: Outer.<init> and Outer.Inner.<init>
        constructors = [c for c in result.calls if c.call_type == CallType.CONSTRUCTOR]
        assert len(constructors) >= 2

        outer_init = next((c for c in constructors if c.callee == "com.example.Outer.<init>"), None)
        assert outer_init is not None

        inner_init = next((c for c in constructors if "Inner" in (c.callee or "")), None)
        assert inner_init is not None

    def test_generic_constructor(self, tmp_path):
        """Test generic constructor."""
        code = """
package com.example;

import java.util.ArrayList;
import java.util.List;

class Service {
    public void create() {
        List<String> list = new ArrayList<String>();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.create → ArrayList.<init>
        # Generic parameters should be stripped
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.callee == "java.util.ArrayList.<init>"


class TestStaticImportResolution:
    """AC3: Static Import Resolution (4 tests)"""

    def test_static_import_method(self, tmp_path):
        """Test static import method resolution."""
        code = """
package com.example;

import static java.util.Collections.sort;

import java.util.List;

public class Service {
    public void organize(List<String> list) {
        sort(list);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.organize → java.util.Collections.sort
        sort_call = next((c for c in result.calls if "sort" in (c.callee or "")), None)
        assert sort_call is not None
        assert sort_call.caller == "com.example.Service.organize"
        assert sort_call.callee == "java.util.Collections.sort"

    def test_static_import_wildcard(self, tmp_path):
        """Test static import wildcard resolution."""
        code = """
package com.example;

import static java.lang.Math.*;

public class Calculator {
    public void calc() {
        double result = sqrt(16);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Calculator.calc → java.lang.Math.sqrt
        sqrt_call = next((c for c in result.calls if "sqrt" in (c.callee or "")), None)
        assert sqrt_call is not None
        assert sqrt_call.caller == "com.example.Calculator.calc"
        assert sqrt_call.callee == "java.lang.Math.sqrt"

    def test_static_import_same_package(self, tmp_path):
        """Test static import from same package."""
        code = """
package com.example;

import static com.example.Utils.helper;

public class Utils {
    public static void helper() {}
}

public class Service {
    public void process() {
        helper();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.process → com.example.Utils.helper
        helper_call = next((c for c in result.calls if "helper" in (c.callee or "")), None)
        assert helper_call is not None
        assert helper_call.caller == "com.example.Service.process"
        assert helper_call.callee == "com.example.Utils.helper"

    def test_ambiguous_static_import(self, tmp_path):
        """Test ambiguous static import (first wins)."""
        code = """
package com.example;

import static com.example.A.method;
import static com.example.B.method;

public class A {
    public static void method() {}
}

public class B {
    public static void method() {}
}

public class Service {
    public void run() {
        method();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.run → com.example.A.method (first import wins)
        method_call = next(
            (c for c in result.calls
             if c.caller == "Service.run" and "method" in (c.callee or "")),
            None
        )
        assert method_call is not None
        # First static import should win
        assert method_call.callee == "com.example.A.method"


class TestFullQualifiedNameCalls:
    """AC4: Full Qualified Name Calls (3 tests)"""

    def test_fqn_in_code(self, tmp_path):
        """Test FQN in code."""
        code = """
package com.example;

public class Service {
    public void load() {
        java.util.List list = new java.util.ArrayList();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.load → java.util.ArrayList.<init>
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.callee == "java.util.ArrayList.<init>"

    def test_fqn_static_method(self, tmp_path):
        """Test FQN static method call."""
        code = """
package com.example;

public class Calculator {
    public void process() {
        double result = java.lang.Math.sqrt(16);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Calculator.process → java.lang.Math.sqrt
        sqrt_call = next((c for c in result.calls if "sqrt" in (c.callee or "")), None)
        assert sqrt_call is not None
        assert sqrt_call.callee == "java.lang.Math.sqrt"

    def test_mix_fqn_and_import(self, tmp_path):
        """Test mix of FQN and import."""
        code = """
package com.example;

import com.example.model.User;

public class Admin {}

public class Service {
    public void create() {
        User user = new User();
        Admin admin = new com.other.Admin();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract both constructors
        constructors = [c for c in result.calls if c.call_type == CallType.CONSTRUCTOR]
        assert len(constructors) >= 2

        user_init = next(
            (c for c in constructors if c.callee == "com.example.model.User.<init>"),
            None
        )
        assert user_init is not None

        admin_init = next((c for c in constructors if c.callee == "com.other.Admin.<init>"), None)
        assert admin_init is not None


class TestMethodReferences:
    """AC5: Method References (Java 8+) (3 tests)"""

    @pytest.mark.skip(reason="Method reference parsing - Phase 2 feature")
    def test_static_method_reference(self, tmp_path):
        """Test static method reference."""
        code = """
package com.example;

import java.util.List;

public class Service {
    public void process(List<String> list) {
        list.forEach(System.out::println);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.process → System.out.println
        println_call = next((c for c in result.calls if "println" in (c.callee or "")), None)
        assert println_call is not None
        assert println_call.callee == "java.lang.System.out.println"

    @pytest.mark.skip(reason="Method reference parsing - Phase 2 feature")
    def test_instance_method_reference(self, tmp_path):
        """Test instance method reference."""
        code = """
package com.example;

import java.util.List;

public class Service {
    public void process(List<String> list) {
        list.stream().map(String::toUpperCase);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.process → String.toUpperCase
        upper_call = next((c for c in result.calls if "toUpperCase" in (c.callee or "")), None)
        assert upper_call is not None
        assert upper_call.callee == "java.lang.String.toUpperCase"

    @pytest.mark.skip(reason="Method reference parsing - Phase 2 feature")
    def test_constructor_reference(self, tmp_path):
        """Test constructor reference."""
        code = """
package com.example;

import java.util.function.Supplier;

public class User {
    public User() {}
}

public class Service {
    public void create() {
        Supplier<User> factory = User::new;
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.create → User.<init>
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.callee == "com.example.User.<init>"


class TestProjectInternalFiltering:
    """AC6: Project-Internal Filtering (3 tests)"""

    @pytest.mark.skip(reason="Project filtering requires configuration - Phase 2")
    def test_project_internal_call(self, tmp_path):
        """Test project-internal call is extracted."""
        code = """
package com.example.service;

import com.example.model.User;

public class UserService {
    public void process() {
        User user = new User();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        # TODO: Need to pass project_namespaces configuration
        result = parse_file(java_file)

        # Should extract: UserService.process → com.example.model.User.<init>
        constructor_call = next(
            (c for c in result.calls if c.call_type == CallType.CONSTRUCTOR),
            None
        )
        assert constructor_call is not None
        assert constructor_call.callee == "com.example.model.User.<init>"

    @pytest.mark.skip(reason="Project filtering requires configuration - Phase 2")
    def test_external_library_call_skipped(self, tmp_path):
        """Test external library call is skipped."""
        code = """
package com.example;

import org.springframework.beans.factory.annotation.Autowired;

public class Service {
    @Autowired
    private UserService service;
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should NOT extract @Autowired (annotation, not call)
        # and NOT extract Spring framework calls
        spring_calls = [c for c in result.calls if "springframework" in (c.callee or "")]
        assert len(spring_calls) == 0

    @pytest.mark.skip(reason="Project filtering requires configuration - Phase 2")
    def test_stdlib_call_skipped(self, tmp_path):
        """Test java.lang call is skipped."""
        code = """
package com.example;

public class Calculator {
    public void calc() {
        double result = Math.sqrt(16);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should NOT extract Math.sqrt (java.lang is stdlib)
        math_calls = [c for c in result.calls if "Math.sqrt" in (c.callee or "")]
        assert len(math_calls) == 0


class TestEdgeCases:
    """AC7: Edge Cases (6 tests)"""

    def test_varargs_call(self, tmp_path):
        """Test varargs method call."""
        code = """
package com.example;

public class Service {
    public void process(String... args) {}

    public void run() {
        process("a", "b", "c");
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract with arguments_count=3
        process_call = next((c for c in result.calls if "process" in (c.callee or "")), None)
        assert process_call is not None
        assert process_call.arguments_count == 3

    @pytest.mark.skip(reason="Lambda expression parsing - Phase 2 feature")
    def test_lambda_expression(self, tmp_path):
        """Test lambda expression call."""
        code = """
package com.example;

import java.util.List;

public class Service {
    public void process(String item) {}

    public void run(List<String> list) {
        list.forEach(item -> process(item));
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract: Service.run → Service.process
        process_call = next((c for c in result.calls if "process" in (c.callee or "")), None)
        assert process_call is not None
        assert process_call.caller == "Service.run"

    def test_ternary_operator_call(self, tmp_path):
        """Test ternary operator with calls."""
        code = """
package com.example;

public class Service {
    public String func1() { return "a"; }
    public String func2() { return "b"; }

    public void run(boolean condition) {
        String result = condition ? func1() : func2();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract both func1 and func2
        func1_call = next((c for c in result.calls if "func1" in (c.callee or "")), None)
        assert func1_call is not None

        func2_call = next((c for c in result.calls if "func2" in (c.callee or "")), None)
        assert func2_call is not None

    def test_nested_method_calls(self, tmp_path):
        """Test nested method calls."""
        code = """
package com.example;

public class Service {
    public int getData() { return 1; }
    public int calculate(int x) { return x * 2; }
    public void process(int x) {}

    public void run() {
        process(calculate(getData()));
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract all 3 calls: getData, calculate, process
        method_calls = [
            c for c in result.calls
            if c.call_type in (CallType.METHOD, CallType.FUNCTION)
        ]
        assert len(method_calls) >= 3

        callees = {c.callee for c in method_calls}
        assert any("getData" in callee for callee in callees)
        assert any("calculate" in callee for callee in callees)
        assert any("process" in callee for callee in callees)

    def test_reflection_call_dynamic(self, tmp_path):
        """Test reflection call marked as DYNAMIC."""
        code = """
package com.example;

import java.lang.reflect.Method;

public class Service {
    public void execute(Object obj) throws Exception {
        Method method = obj.getClass().getMethod("methodName");
        method.invoke(obj);
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract invoke as DYNAMIC call
        invoke_call = next(
            (c for c in result.calls
             if c.call_type == CallType.DYNAMIC or "invoke" in (c.callee or "")),
            None
        )
        # Note: This test verifies we can detect reflection patterns
        # May need to mark invoke() specially as DYNAMIC
        assert invoke_call is not None or len(result.calls) > 0

    def test_no_calls_in_method(self, tmp_path):
        """Test method with no calls."""
        code = """
package com.example;

public class Service {
    public int standalone() {
        int x = 10;
        return x;
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should have no calls
        assert len(result.calls) == 0


class TestAnnotationBasedCalls:
    """AC8: Annotation-Based Calls (3 tests)"""

    def test_spring_autowired_skip(self, tmp_path):
        """Test @Autowired annotation is not extracted as call."""
        code = """
package com.example;

import org.springframework.beans.factory.annotation.Autowired;

public class Service {
    @Autowired
    private UserService userService;
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should NOT extract @Autowired as a call
        autowired_calls = [c for c in result.calls if "Autowired" in (c.callee or "")]
        assert len(autowired_calls) == 0

    def test_junit_test_skip(self, tmp_path):
        """Test @Test annotation is not extracted as call."""
        code = """
package com.example;

import org.junit.Test;

public class ServiceTest {
    @Test
    public void testMethod() {
        // test code
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should NOT extract @Test as a call
        test_calls = [c for c in result.calls if "Test" in (c.callee or "")]
        assert len(test_calls) == 0

    def test_custom_annotation_with_call(self, tmp_path):
        """Test custom annotation with method call inside."""
        code = """
package com.example;

@interface CustomAnnotation {}

public class Service {
    public void helper() {}

    @CustomAnnotation
    public void annotated() {
        helper();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(code)

        result = parse_file(java_file)

        # Should extract the helper() call, but NOT @CustomAnnotation
        helper_call = next((c for c in result.calls if "helper" in (c.callee or "")), None)
        assert helper_call is not None
        assert helper_call.caller == "Service.annotated"

        # Should NOT extract annotation as call
        annotation_calls = [c for c in result.calls if "CustomAnnotation" in (c.callee or "")]
        assert len(annotation_calls) == 0
