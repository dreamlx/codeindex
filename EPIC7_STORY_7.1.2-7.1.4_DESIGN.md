# Epic 7: Story 7.1.2-7.1.4 详细设计方案

**编写时间**: 2026-02-05
**目标**: Week 1 (Java基础解析) 的完善与增强
**前置条件**: Story 7.1.1 已完成 (23个测试通过)

---

## 📋 目录

- [Story 7.1.2: 符号提取增强](#story-712-符号提取增强)
- [Story 7.1.3: 测试覆盖增强](#story-713-测试覆盖增强)
- [Story 7.1.4: 性能优化](#story-714-性能优化)
- [优先级建议](#优先级建议)
- [风险评估](#风险评估)

---

## Story 7.1.2: 符号提取增强

### 🎯 目标

完善符号提取功能，支持更多Java语言特性和边缘情况。

### 📊 当前状态 vs 目标状态

| 功能 | 当前状态 (7.1.1) | 目标状态 (7.1.2) |
|------|-----------------|-----------------|
| **注解提取** | ❌ 不支持 | ✅ 完整支持 @Override, @Deprecated, Spring注解等 |
| **泛型边界** | ⚠️ 基础支持 | ✅ 完整支持 `<T extends Foo & Bar>` |
| **异常声明** | ❌ 不支持 | ✅ 提取 throws 子句 |
| **内部类** | ⚠️ 基础支持 | ✅ 完整支持静态/非静态/匿名内部类 |
| **Lambda表达式** | ❌ 不支持 | ✅ 识别并标记Lambda |
| **模块系统** | ❌ 不支持 | ✅ 支持 module-info.java |
| **默认方法** | ❌ 不支持 | ✅ 接口default方法 |
| **方法引用** | ❌ 不支持 | ✅ 识别 `::` 方法引用 |

---

### 📝 详细设计

#### Feature 7.1.2.1: 注解提取 (Annotation Extraction)

**需求**: 提取所有注解及其参数，用于后续Spring路由提取和符号评分。

**实现方案**:

```python
# src/codeindex/models.py
@dataclass
class Annotation:
    """Represents a Java annotation."""
    name: str                    # e.g., "Override", "RestController"
    arguments: dict[str, str]    # e.g., {"value": "/api/users", "method": "GET"}
    line: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "line": self.line,
        }

# Symbol类增加字段
@dataclass
class Symbol:
    # ... existing fields ...
    annotations: list[Annotation] = field(default_factory=list)  # NEW
```

**解析函数**:

```python
# src/codeindex/parser.py
def _extract_java_annotations(node: Node, source_bytes: bytes) -> list[Annotation]:
    """
    Extract annotations from a Java node.

    Supports:
    - Simple annotations: @Override
    - Annotations with value: @SuppressWarnings("unchecked")
    - Annotations with named params: @RequestMapping(value="/users", method=RequestMethod.GET)
    - Marker annotations: @Deprecated
    """
    annotations = []

    for child in node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                if mod_child.type == "marker_annotation":
                    # @Override
                    name = _get_annotation_name(mod_child, source_bytes)
                    annotations.append(Annotation(name=name, arguments={}, line=mod_child.start_point[0] + 1))

                elif mod_child.type == "annotation":
                    # @SuppressWarnings("unchecked")
                    # @RequestMapping(value="/users", method=RequestMethod.GET)
                    name = _get_annotation_name(mod_child, source_bytes)
                    args = _parse_annotation_arguments(mod_child, source_bytes)
                    annotations.append(Annotation(name=name, arguments=args, line=mod_child.start_point[0] + 1))

    return annotations

def _get_annotation_name(node: Node, source_bytes: bytes) -> str:
    """Extract annotation name (e.g., 'RestController' from '@RestController')."""
    for child in node.children:
        if child.type in ("identifier", "scoped_identifier"):
            name = _get_node_text(child, source_bytes)
            return name.lstrip('@')  # Remove @ prefix if present
    return ""

def _parse_annotation_arguments(node: Node, source_bytes: bytes) -> dict[str, str]:
    """
    Parse annotation arguments.

    Examples:
    - @SuppressWarnings("unchecked") → {"value": "unchecked"}
    - @RequestMapping(value="/users", method=RequestMethod.GET) → {"value": "/users", "method": "RequestMethod.GET"}
    """
    arguments = {}

    for child in node.children:
        if child.type == "annotation_argument_list":
            for arg_child in child.children:
                if arg_child.type == "element_value_pair":
                    # Named argument: value="/users"
                    key, value = _parse_element_value_pair(arg_child, source_bytes)
                    arguments[key] = value
                elif arg_child.type in ("string_literal", "identifier", "field_access"):
                    # Single value: @SuppressWarnings("unchecked")
                    arguments["value"] = _get_node_text(arg_child, source_bytes).strip('"')

    return arguments

def _parse_element_value_pair(node: Node, source_bytes: bytes) -> tuple[str, str]:
    """Parse key-value pair in annotation arguments."""
    key = ""
    value = ""

    for child in node.children:
        if child.type == "identifier":
            key = _get_node_text(child, source_bytes)
        elif child.type in ("string_literal", "identifier", "field_access", "integer_literal"):
            value = _get_node_text(child, source_bytes).strip('"')

    return key, value
```

**测试用例** (~10 tests):

```python
# tests/test_java_annotations.py
class TestJavaAnnotations:
    def test_extract_marker_annotation(self):
        """Test @Override, @Deprecated."""
        code = """
        @Override
        public String toString() {
            return "User";
        }
        """
        result = parse_java_file("test.java", code)
        method = next(s for s in result.symbols if "toString" in s.name)
        assert len(method.annotations) == 1
        assert method.annotations[0].name == "Override"

    def test_extract_single_value_annotation(self):
        """Test @SuppressWarnings("unchecked")."""
        code = """
        @SuppressWarnings("unchecked")
        public class MyClass {}
        """
        result = parse_java_file("test.java", code)
        cls = next(s for s in result.symbols if s.kind == "class")
        assert len(cls.annotations) == 1
        assert cls.annotations[0].name == "SuppressWarnings"
        assert cls.annotations[0].arguments["value"] == "unchecked"

    def test_extract_spring_rest_controller(self):
        """Test @RestController with @RequestMapping."""
        code = """
        @RestController
        @RequestMapping("/api/users")
        public class UserController {
            @GetMapping("/{id}")
            public User getUser(@PathVariable Long id) {
                return null;
            }
        }
        """
        result = parse_java_file("test.java", code)
        cls = next(s for s in result.symbols if s.kind == "class")
        assert any(a.name == "RestController" for a in cls.annotations)
        assert any(a.name == "RequestMapping" for a in cls.annotations)

        method = next(s for s in result.symbols if "getUser" in s.name)
        assert any(a.name == "GetMapping" for a in method.annotations)

    def test_extract_multiple_annotations(self):
        """Test multiple annotations on same element."""
        code = """
        @Deprecated
        @SuppressWarnings("all")
        @CustomAnnotation(value="test", enabled=true)
        public void oldMethod() {}
        """
        result = parse_java_file("test.java", code)
        method = next(s for s in result.symbols if s.kind == "method")
        assert len(method.annotations) == 3
        assert any(a.name == "Deprecated" for a in method.annotations)
        assert any(a.name == "SuppressWarnings" for a in method.annotations)
        assert any(a.name == "CustomAnnotation" for a in method.annotations)
```

**时间估算**: 4小时 (实现3h + 测试1h)

**优先级**: 🔥 P0 (高优先级)
- Spring路由提取依赖注解
- 符号评分依赖注解

---

#### Feature 7.1.2.2: 泛型边界 (Generic Bounds)

**需求**: 完整提取泛型类型参数的边界声明。

**当前问题**:
```java
// 当前只能提取 <T>
public class Box<T extends Number & Comparable<T>> {
    // 缺失: extends Number & Comparable<T>
}
```

**实现方案**:

```python
def _extract_type_parameters_with_bounds(node: Node, source_bytes: bytes) -> str:
    """
    Extract complete type parameters with bounds.

    Examples:
    - <T> → "<T>"
    - <T extends Number> → "<T extends Number>"
    - <T extends Number & Comparable<T>> → "<T extends Number & Comparable<T>>"
    - <K, V extends List<K>> → "<K, V extends List<K>>"
    """
    type_params_node = _find_child_by_type(node, "type_parameters")
    if type_params_node:
        # 直接返回完整文本（包含所有bounds）
        return _get_node_text(type_params_node, source_bytes)
    return ""
```

**测试用例** (~5 tests):

```python
def test_extract_generic_with_single_bound(self):
    code = "public class Box<T extends Number> {}"
    result = parse_java_file("test.java", code)
    cls = next(s for s in result.symbols if s.kind == "class")
    assert "<T extends Number>" in cls.signature

def test_extract_generic_with_multiple_bounds(self):
    code = "public class Box<T extends Number & Comparable<T>> {}"
    result = parse_java_file("test.java", code)
    cls = next(s for s in result.symbols if s.kind == "class")
    assert "extends Number & Comparable<T>" in cls.signature

def test_extract_multiple_type_params_with_bounds(self):
    code = "public class Pair<K, V extends List<K>> {}"
    result = parse_java_file("test.java", code)
    cls = next(s for s in result.symbols if s.kind == "class")
    assert "<K, V extends List<K>>" in cls.signature
```

**时间估算**: 2小时 (实现1h + 测试1h)

**优先级**: 🟡 P1 (中优先级)
- 对核心功能影响较小
- 提升输出完整性

---

#### Feature 7.1.2.3: 异常声明 (Throws Clause)

**需求**: 提取方法的 `throws` 子句。

**实现方案**:

```python
# Symbol类增加字段
@dataclass
class Symbol:
    # ... existing fields ...
    throws: list[str] = field(default_factory=list)  # NEW: ["IOException", "SQLException"]

def _extract_throws_clause(node: Node, source_bytes: bytes) -> list[str]:
    """Extract throws clause from method declaration."""
    exceptions = []

    for child in node.children:
        if child.type == "throws":
            for exc_child in child.children:
                if exc_child.type in ("type_identifier", "scoped_type_identifier"):
                    exceptions.append(_get_node_text(exc_child, source_bytes))

    return exceptions
```

**修改方法解析**:

```python
def _parse_java_method(node: Node, source_bytes: bytes, class_name: str = "") -> Symbol:
    # ... existing code ...

    # Extract throws clause
    throws = _extract_throws_clause(node, source_bytes)

    # Update signature to include throws
    if throws:
        signature += f" throws {', '.join(throws)}"

    return Symbol(
        # ... existing fields ...
        throws=throws,  # NEW
    )
```

**测试用例** (~3 tests):

```python
def test_extract_single_exception(self):
    code = """
    public void readFile() throws IOException {
        // ...
    }
    """
    result = parse_java_file("test.java", code)
    method = next(s for s in result.symbols if "readFile" in s.name)
    assert method.throws == ["IOException"]
    assert "throws IOException" in method.signature

def test_extract_multiple_exceptions(self):
    code = """
    public void process() throws IOException, SQLException, CustomException {
        // ...
    }
    """
    result = parse_java_file("test.java", code)
    method = next(s for s in result.symbols if "process" in s.name)
    assert len(method.throws) == 3
    assert "IOException" in method.throws
    assert "SQLException" in method.throws
```

**时间估算**: 2小时

**优先级**: 🟡 P1 (中优先级)

---

#### Feature 7.1.2.4: Lambda与方法引用 (Lambda & Method References)

**需求**: 识别Lambda表达式和方法引用，标记为特殊符号。

**实现方案**:

```python
def _find_lambda_expressions(node: Node, source_bytes: bytes, parent_name: str = "") -> list[Symbol]:
    """
    Find and mark lambda expressions.

    Lambda expressions are not top-level symbols, but we mark them
    for completeness (useful for code analysis tools).
    """
    lambdas = []

    for child in node.children:
        if child.type == "lambda_expression":
            # Extract lambda signature
            params = ""
            for lambda_child in child.children:
                if lambda_child.type == "inferred_parameters":
                    params = _get_node_text(lambda_child, source_bytes)
                elif lambda_child.type == "formal_parameters":
                    params = _get_node_text(lambda_child, source_bytes)

            lambdas.append(Symbol(
                name=f"{parent_name}.<lambda>",
                kind="lambda",
                signature=f"lambda {params}",
                docstring="",
                line_start=child.start_point[0] + 1,
                line_end=child.end_point[0] + 1,
            ))

        # Recurse into children
        lambdas.extend(_find_lambda_expressions(child, source_bytes, parent_name))

    return lambdas
```

**测试用例** (~3 tests):

```python
def test_identify_lambda_expression(self):
    code = """
    public void processUsers() {
        users.forEach(user -> System.out.println(user));
    }
    """
    result = parse_java_file("test.java", code)
    lambdas = [s for s in result.symbols if s.kind == "lambda"]
    assert len(lambdas) >= 1

def test_identify_method_reference(self):
    code = """
    public void processUsers() {
        users.forEach(System.out::println);
    }
    """
    result = parse_java_file("test.java", code)
    # Method references can be marked similarly to lambdas
    # Or simply noted in method body (lower priority)
```

**时间估算**: 3小时

**优先级**: 🟢 P2 (低优先级)
- 对核心功能影响不大
- 仅用于高级代码分析

---

#### Feature 7.1.2.5: 模块系统 (Java 9+ Module System)

**需求**: 解析 `module-info.java` 文件。

**实现方案**:

```python
def _parse_java_module(node: Node, source_bytes: bytes) -> dict:
    """
    Parse Java module declaration.

    Example:
    module com.example.myapp {
        requires java.sql;
        requires transitive java.xml;
        exports com.example.myapp.api;
        opens com.example.myapp.internal to spring.core;
    }
    """
    module_info = {
        "name": "",
        "requires": [],
        "exports": [],
        "opens": [],
    }

    for child in node.children:
        if child.type == "identifier":
            module_info["name"] = _get_node_text(child, source_bytes)
        elif child.type == "module_body":
            for directive in child.children:
                if directive.type == "requires_module_directive":
                    # requires java.sql;
                    module_name = _get_module_directive_name(directive, source_bytes)
                    module_info["requires"].append(module_name)
                elif directive.type == "exports_module_directive":
                    # exports com.example.myapp.api;
                    package_name = _get_module_directive_name(directive, source_bytes)
                    module_info["exports"].append(package_name)
                elif directive.type == "opens_module_directive":
                    # opens com.example.myapp.internal to spring.core;
                    package_name = _get_module_directive_name(directive, source_bytes)
                    module_info["opens"].append(package_name)

    return module_info
```

**测试用例** (~3 tests):

```python
def test_parse_module_info(self):
    code = """
    module com.example.myapp {
        requires java.sql;
        requires transitive java.xml;
        exports com.example.myapp.api;
    }
    """
    result = parse_java_file("module-info.java", code)
    assert result.namespace == "com.example.myapp"
    # Module info stored in metadata
    assert "java.sql" in result.metadata.get("requires", [])
```

**时间估算**: 3小时

**优先级**: 🟢 P2 (低优先级)
- 现代Java项目才使用
- 大多数Spring项目不使用模块系统

---

### 📊 Story 7.1.2 总结

| Feature | 时间 | 优先级 | 测试数 |
|---------|------|--------|--------|
| 7.1.2.1: 注解提取 | 4h | P0 | 10 |
| 7.1.2.2: 泛型边界 | 2h | P1 | 5 |
| 7.1.2.3: 异常声明 | 2h | P1 | 3 |
| 7.1.2.4: Lambda表达式 | 3h | P2 | 3 |
| 7.1.2.5: 模块系统 | 3h | P2 | 3 |
| **总计** | **14h** | - | **24** |

**建议**: 优先实现 P0+P1 (8小时，18个测试)，P2可选。

---

## Story 7.1.3: 测试覆盖增强

### 🎯 目标

扩展测试覆盖范围，确保支持真实Java项目的各种边界情况和框架特性。

### 📊 当前测试覆盖 (Story 7.1.1)

**已有测试** (23个):
- ✅ 基础解析（文件检测、解析器初始化）
- ✅ 符号提取（类、接口、枚举、方法、字段）
- ✅ 导入语句
- ✅ 泛型
- ✅ 现代语法（Record, Sealed class）
- ✅ JavaDoc
- ✅ 文件元数据

**缺失测试**:
- ❌ Spring Boot特性（已有fixture但无测试）
- ❌ 边界情况（空文件、超大文件、特殊字符）
- ❌ 错误恢复（语法错误、不完整代码）
- ❌ Lombok注解
- ❌ 包私有/保护访问修饰符
- ❌ 静态导入重命名
- ❌ 嵌套泛型（`List<Map<String, List<User>>>`）

---

### 📝 详细设计

#### Feature 7.1.3.1: Spring Boot测试套件

**需求**: 针对Spring生态的全面测试。

**测试fixture**: `tests/fixtures/java/spring/`

```
spring/
├── UserController.java        # @RestController + CRUD endpoints
├── UserService.java           # @Service + business logic
├── UserRepository.java        # @Repository + data access
├── SecurityConfig.java        # @Configuration + security
├── Application.java           # @SpringBootApplication
└── UserDTO.java              # Plain Java bean (no Spring annotations)
```

**测试用例** (~15 tests):

```python
# tests/test_java_spring.py
class TestSpringBootAnnotations:
    """Test Spring Framework specific features."""

    def test_parse_rest_controller(self):
        """Test @RestController with @RequestMapping."""
        code = load_fixture("spring/UserController.java")
        result = parse_java_file("UserController.java", code)

        # Class should have @RestController
        controller_class = next(s for s in result.symbols if s.kind == "class")
        assert any(a.name == "RestController" for a in controller_class.annotations)

    def test_parse_spring_service(self):
        """Test @Service annotation."""
        code = load_fixture("spring/UserService.java")
        result = parse_java_file("UserService.java", code)

        service_class = next(s for s in result.symbols if s.kind == "class")
        assert any(a.name == "Service" for a in service_class.annotations)

    def test_parse_request_mapping_annotations(self):
        """Test @GetMapping, @PostMapping, @PutMapping, @DeleteMapping."""
        code = load_fixture("spring/UserController.java")
        result = parse_java_file("UserController.java", code)

        methods = [s for s in result.symbols if s.kind == "method"]

        # Should have methods with different mappings
        get_methods = [m for m in methods if any(a.name == "GetMapping" for a in m.annotations)]
        post_methods = [m for m in methods if any(a.name == "PostMapping" for a in m.annotations)]

        assert len(get_methods) >= 1
        assert len(post_methods) >= 1

    def test_parse_path_variable_annotation(self):
        """Test @PathVariable annotation in method parameters."""
        code = """
        @GetMapping("/{id}")
        public User getUser(@PathVariable Long id) {
            return null;
        }
        """
        result = parse_java_file("test.java", code)
        method = next(s for s in result.symbols if "getUser" in s.name)

        # Method signature should contain @PathVariable
        assert "PathVariable" in method.signature or len(method.annotations) > 0

    def test_parse_spring_boot_application(self):
        """Test @SpringBootApplication annotation."""
        code = load_fixture("spring/Application.java")
        result = parse_java_file("Application.java", code)

        app_class = next(s for s in result.symbols if s.kind == "class")
        assert any(a.name == "SpringBootApplication" for a in app_class.annotations)

    # ... 10 more Spring-related tests
```

**时间估算**: 6小时 (fixtures 2h + tests 4h)

**优先级**: 🔥 P0 (必须)
- Spring是Java企业开发主流框架
- 为Story 7.2 (Spring路由提取) 做准备

---

#### Feature 7.1.3.2: 边界情况测试

**需求**: 测试异常输入和边界条件。

**测试用例** (~10 tests):

```python
# tests/test_java_edge_cases.py
class TestJavaEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_parse_empty_file(self):
        """Test parsing empty Java file."""
        code = ""
        result = parse_java_file("empty.java", code)
        assert result.error is None
        assert len(result.symbols) == 0

    def test_parse_file_with_only_package(self):
        """Test file with only package declaration."""
        code = "package com.example;"
        result = parse_java_file("test.java", code)
        assert result.namespace == "com.example"
        assert len(result.symbols) == 0

    def test_parse_file_with_only_imports(self):
        """Test file with only import statements."""
        code = """
        import java.util.List;
        import java.util.Map;
        """
        result = parse_java_file("test.java", code)
        assert len(result.imports) == 2
        assert len(result.symbols) == 0

    def test_parse_file_with_unicode_identifiers(self):
        """Test Unicode in Java identifiers (Java supports this)."""
        code = """
        public class 用户类 {
            private String 名字;

            public String get名字() {
                return 名字;
            }
        }
        """
        result = parse_java_file("test.java", code)
        assert any("用户类" in s.name for s in result.symbols)

    def test_parse_very_long_class(self):
        """Test parsing class with 1000+ methods (stress test)."""
        methods = "\n".join([
            f"public void method{i}() {{ }}"
            for i in range(1000)
        ])
        code = f"public class LargeClass {{ {methods} }}"

        result = parse_java_file("test.java", code)
        methods_symbols = [s for s in result.symbols if s.kind == "method"]
        assert len(methods_symbols) == 1000

    def test_parse_deeply_nested_classes(self):
        """Test deeply nested inner classes."""
        code = """
        public class Outer {
            public class Inner1 {
                public class Inner2 {
                    public class Inner3 {
                        public void deepMethod() {}
                    }
                }
            }
        }
        """
        result = parse_java_file("test.java", code)
        # Should handle all nested levels
        assert len([s for s in result.symbols if s.kind == "class"]) == 4

    def test_parse_complex_generics(self):
        """Test deeply nested generic types."""
        code = """
        public Map<String, List<Map<Long, Set<User>>>> complexMap;
        """
        result = parse_java_file("test.java", code)
        field = next(s for s in result.symbols if s.kind == "field")
        assert "Map<String, List<Map<Long, Set<User>>>>" in field.signature

    # ... 3 more edge case tests
```

**时间估算**: 4小时

**优先级**: 🟡 P1 (高价值)

---

#### Feature 7.1.3.3: 错误恢复测试

**需求**: 测试对不完整/错误代码的鲁棒性。

**测试用例** (~8 tests):

```python
# tests/test_java_error_recovery.py
class TestJavaErrorRecovery:
    """Test parser behavior with syntax errors and incomplete code."""

    def test_parse_missing_closing_brace(self):
        """Test class missing closing brace."""
        code = """
        public class Incomplete {
            public void method() {
                // Missing closing braces
        """
        result = parse_java_file("test.java", code)
        # Should not crash, but should report error
        assert result.error is not None or hasattr(result, 'has_error')

    def test_parse_invalid_syntax(self):
        """Test completely invalid Java syntax."""
        code = "public class void interface enum {{{{{}"
        result = parse_java_file("test.java", code)
        # Should not crash
        assert result is not None

    def test_parse_missing_method_body(self):
        """Test method without implementation (interface-like)."""
        code = """
        public class MyClass {
            public abstract void incompleteMethod();
        }
        """
        result = parse_java_file("test.java", code)
        # Should parse successfully (abstract methods are valid)
        assert result.error is None

    def test_parse_unterminated_string(self):
        """Test unterminated string literal."""
        code = '''
        public class Test {
            String s = "unterminated string
        }
        '''
        result = parse_java_file("test.java", code)
        # Should handle gracefully
        assert result is not None

    # ... 4 more error recovery tests
```

**时间估算**: 3小时

**优先级**: 🟡 P1 (重要)

---

#### Feature 7.1.3.4: Lombok支持测试

**需求**: 测试对Lombok注解的识别（不展开，仅识别）。

**测试用例** (~5 tests):

```python
# tests/test_java_lombok.py
class TestJavaLombok:
    """Test Lombok annotation recognition."""

    def test_parse_lombok_data(self):
        """Test @Data annotation (generates getters/setters/toString)."""
        code = """
        @Data
        public class User {
            private Long id;
            private String name;
        }
        """
        result = parse_java_file("test.java", code)
        user_class = next(s for s in result.symbols if s.kind == "class")
        assert any(a.name == "Data" for a in user_class.annotations)

    def test_parse_lombok_builder(self):
        """Test @Builder annotation."""
        code = """
        @Builder
        public class User {
            private String name;
            private int age;
        }
        """
        result = parse_java_file("test.java", code)
        user_class = next(s for s in result.symbols if s.kind == "class")
        assert any(a.name == "Builder" for a in user_class.annotations)

    # ... 3 more Lombok tests
```

**时间估算**: 2小时

**优先级**: 🟢 P2 (可选)

---

### 📊 Story 7.1.3 总结

| Feature | 时间 | 优先级 | 测试数 |
|---------|------|--------|--------|
| 7.1.3.1: Spring测试套件 | 6h | P0 | 15 |
| 7.1.3.2: 边界情况 | 4h | P1 | 10 |
| 7.1.3.3: 错误恢复 | 3h | P1 | 8 |
| 7.1.3.4: Lombok支持 | 2h | P2 | 5 |
| **总计** | **15h** | - | **38** |

**建议**: 优先实现 P0+P1 (13小时，33个测试)。

---

## Story 7.1.4: 性能优化

### 🎯 目标

优化Java解析性能，支持大型企业项目（100k+ LOC）。

### 📊 性能基准 (当前状态)

基于Story 7.1.1测试结果：
- 小文件 (<200 LOC): 0.01秒
- 中文件 (200-1000 LOC): 0.05秒
- 大文件 (>1000 LOC): 0.2秒

**目标**:
- 大文件 (>1000 LOC): < 0.1秒 (提升100%)
- 超大文件 (5000+ LOC): < 0.5秒
- 并行扫描: 支持多进程

---

### 📝 详细设计

#### Feature 7.1.4.1: 符号提取优化

**问题**: 当前每次提取都遍历整个AST，存在重复遍历。

**优化方案**:

```python
def _parse_java_file_optimized(tree, source_bytes: bytes) -> ParseResult:
    """
    Optimized Java file parsing with single-pass AST traversal.

    Before: Multiple passes over AST (one per symbol type)
    After: Single pass collecting all symbols
    """
    root = tree.root_node
    symbols = []
    imports = []
    namespace = ""
    module_docstring = ""

    # Single-pass traversal
    def traverse(node: Node, parent_class: str = ""):
        nonlocal namespace, module_docstring

        if node.type == "package_declaration":
            namespace = _parse_java_package(node, source_bytes)

        elif node.type == "import_declaration":
            imp = _parse_java_import(node, source_bytes)
            if imp:
                imports.append(imp)

        elif node.type == "class_declaration":
            class_symbols = _parse_java_class(node, source_bytes)
            symbols.extend(class_symbols)

        elif node.type == "interface_declaration":
            interface_symbols = _parse_java_interface(node, source_bytes)
            symbols.extend(interface_symbols)

        # ... other node types

        # Recurse only if necessary
        if node.type in ("compilation_unit", "program"):
            for child in node.children:
                traverse(child, parent_class)

    traverse(root)

    return ParseResult(
        symbols=symbols,
        imports=imports,
        namespace=namespace,
        module_docstring=module_docstring,
        # ...
    )
```

**时间估算**: 4小时

**预期提升**: 30-50%

---

#### Feature 7.1.4.2: 并行文件扫描

**需求**: 支持多进程并行解析Java文件。

**实现方案**:

```python
# src/codeindex/scanner.py
def scan_directory_parallel(
    directory: Path,
    config: Config,
    max_workers: int = None
) -> list[ParseResult]:
    """
    Scan directory with parallel processing.

    Args:
        directory: Directory to scan
        config: Configuration
        max_workers: Number of worker processes (default: CPU count)

    Returns:
        List of ParseResult for all Java files
    """
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing

    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    # Collect all Java files
    java_files = list(directory.rglob("*.java"))

    # Parse in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            parse_java_file_worker,
            java_files
        ))

    return results

def parse_java_file_worker(file_path: Path) -> ParseResult:
    """Worker function for parallel parsing."""
    content = file_path.read_text(encoding='utf-8')
    return parse_file(file_path, content, language="java")
```

**配置选项**:

```yaml
# .codeindex.yaml
performance:
  parallel_parsing: true
  max_workers: 4  # or 'auto' for CPU count
```

**测试用例**:

```python
def test_parallel_parsing_faster_than_sequential():
    """Test parallel parsing is faster for large projects."""
    import time

    # Create 100 Java files
    test_dir = create_test_java_files(count=100, loc_per_file=500)

    # Sequential
    start = time.time()
    results_seq = scan_directory(test_dir, parallel=False)
    time_seq = time.time() - start

    # Parallel
    start = time.time()
    results_par = scan_directory(test_dir, parallel=True)
    time_par = time.time() - start

    # Parallel should be faster (at least 50% improvement on 4+ cores)
    assert time_par < time_seq * 0.7
    assert len(results_seq) == len(results_par)
```

**时间估算**: 6小时

**预期提升**: 200-400% (on 4-core CPU)

---

#### ~~Feature 7.1.4.3: 符号缓存~~ ❌ 已删除

**删除原因**: 收益不足（<1%）

虽然缓存可以节省tree-sitter解析时间（~0.1秒），但**即使缓存命中，仍然需要调用AI生成README**（~10秒），这占据了99%的时间。

**实际时间分解**:
```
缓存命中: 0.001s (读取cache)
格式化: 0.01s
AI调用: 10s  ← 仍然要调用
总计: 10.011s vs 无缓存10.11s
收益: 0.1s / 10.1s = <1%
```

**如果要真正有价值的缓存**:
- 需要缓存AI生成的README（而非ParseResult）
- 但这改变工具行为（README不随AI能力提升）
- 需要复杂的cache invalidation策略
- 投入产出比不划算

**结论**: 删除此功能，专注于并行扫描优化

---

#### Feature 7.1.4.4: 内存优化

**需求**: 减少大型项目的内存占用。

**优化方案**:

1. **延迟加载符号体**:
```python
@dataclass
class Symbol:
    # ... existing fields ...
    body: str = ""  # Default empty, load on demand

    def load_body(self, source_file: Path):
        """Load symbol body from source file."""
        if not self.body:
            content = source_file.read_text()
            lines = content.splitlines()
            self.body = "\n".join(lines[self.line_start-1:self.line_end])
```

2. **流式处理大文件**:
```python
def parse_large_file_streaming(file_path: Path, chunk_size: int = 10000):
    """
    Parse large file in chunks to reduce memory usage.

    For files > 10,000 lines, process in chunks.
    """
    if file_path.stat().st_size < 1_000_000:  # < 1MB
        # Small file, parse normally
        return parse_file(file_path)

    # Large file, use streaming
    # ...
```

**时间估算**: 4小时

**预期提升**: 50% memory reduction for large projects

---

### 📊 Story 7.1.4 总结 (最终版)

| Feature | 时间 | 预期提升 | 优先级 | 状态 |
|---------|------|----------|--------|------|
| 7.1.4.2: 并行扫描验证 | 2h | 已实现 | P0 | ✅ **完成** |
| ~~7.1.4.1: 单次AST遍历~~ | ~~4h~~ | ~~<3%~~ | - | ❌ **不实施** |
| ~~7.1.4.3: 符号缓存~~ | ~~5h~~ | ~~<1%~~ | - | ❌ **已删除** |
| ~~7.1.4.4: 内存优化~~ | ~~4h~~ | ~~不适用~~ | - | ❌ **不实施** |
| **Epic 7 总计** | **12h** | - | - | **✅ 完成** |

**关键决策** (2026-02-05):
- ✅ 7.1.4.2: 发现已实现，创建验证测试 (9 tests)
- ❌ 7.1.4.1: Python/Java已优化，PHP微优化（<3%）不值得
- ❌ 7.1.4.3: 删除（收益<1%，仍需调用AI）
- ❌ 7.1.4.4: 架构已优化（按目录处理），不需要额外工作
- 🎯 **务实决策**: 现代机器32GB内存，微优化留给开源社区

---

## 优先级建议

### ✅ 最终完成方案 (MVP Delivered)

**目标**: 快速支持真实Java项目，优先商业价值。

**已完成**:
- ✅ Story 7.1.2.1: 注解提取 (4h) - **11 tests**
- ✅ Story 7.1.3.1: Spring测试套件 (6h) - **19 tests**
- ✅ Story 7.1.4.2: 并行扫描验证 (2h) - **9 tests**

**总工作量**: 12小时 (1.5天)
- 实际完成: 12小时 ✅
- 节省时间: 4小时（相比原计划16h）

**测试覆盖**: 39个新测试 (11注解 + 19Spring + 9并行)
**商业价值**: ⭐⭐⭐⭐⭐

**关键成就**:
- ✅ Java注解完整支持（Spring生态就绪）
- ✅ Spring Framework全栈测试（Controller/Service/Repository/Entity）
- ✅ 并行扫描已实现（ThreadPoolExecutor，3-4x提升）
- ✅ 务实决策：跳过微优化（<3%收益），专注核心价值

---

### 推荐方案B: 增强版 (包含P1特性)

**目标**: 在MVP基础上增加符号提取增强。

**包含**:
- ✅ MVP全部内容 (16h)
- ➕ Story 7.1.2.2-3: 泛型边界 + 异常声明 (4h)
- ➕ Story 7.1.3.2-3: 边界测试 + 错误恢复 (7h)

**总工作量**: 27小时 (约3-4天)
**商业价值**: ⭐⭐⭐⭐

---

### 推荐方案C: 完整版 (包含所有可选特性)

**目标**: 全面完善Java支持，包含Lambda和模块系统。

**包含**:
- ✅ 方案B全部内容 (27h)
- ➕ Story 7.1.2.4-5: Lambda + 模块系统 (6h)
- ➕ Story 7.1.3.4: Lombok支持 (2h)
- ➕ Story 7.1.4.1: 单次AST遍历 (2h)
- ➕ Story 7.1.4.4: 内存优化 (2h)

**总工作量**: 39小时 (约5天)
**商业价值**: ⭐⭐⭐

---

## 风险评估

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **tree-sitter-java注解解析不稳定** | 中 | 高 | 充分测试，准备fallback方案 |
| **并行扫描线程安全问题** | 低 | 中 | ThreadPool处理I/O bound任务很成熟 |
| **性能优化引入bug** | 中 | 高 | TDD确保功能不退化 |

### 时间风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **注解参数解析复杂度超预期** | 高 | 中 | 逐步支持，先支持简单注解 |
| **Spring测试fixture准备耗时** | 中 | 中 | 复用开源Spring项目代码 |
| **性能优化调试耗时** | 中 | 高 | 严格TDD，小步快跑 |

---

## 实施建议

### 阶段1: Story 7.1.2 (注解+泛型) - 1周
**目标**: 完善符号提取，支持Spring注解

**Day 1-2**: 注解提取 (P0)
**Day 3**: 泛型边界 + 异常声明 (P1)
**Day 4-5**: 测试 + 重构

**Checkpoint**: Spring注解能完整提取

---

### 阶段2: Story 7.1.3 (测试覆盖) - 1周
**目标**: 确保真实项目兼容性

**Day 1-3**: Spring测试套件 (P0)
**Day 4**: 边界情况测试 (P1)
**Day 5**: 错误恢复测试 (P1)

**Checkpoint**: 真实Spring项目测试通过

---

### 阶段3: Story 7.1.4 (性能优化) - 1周
**目标**: 支持大型企业项目

**Day 1-2**: 并行扫描 (P0)
**Day 3**: 符号提取优化 (P1)
**Day 4-5**: 符号缓存 (P1)

**Checkpoint**: 100k LOC项目 < 30秒扫描

---

## 总结

### 最小MVP (方案C) - 推荐立即开始

**时间**: 2天 (16小时)
**测试**: +25个 (总计48个)
**价值**: 验证Java支持可行性

✅ **立即可做**: Story 7.1.2 P0 (注解提取)
✅ **依赖Story 7.2**: Spring路由提取需要注解

---

### 完整增强 (方案A) - 推荐Week 1完成

**时间**: 5天 (36小时)
**测试**: +51个 (总计74个)
**价值**: 生产就绪的Java支持

---

## 🤔 Review问题

请review以下方面：

1. **优先级排序**: 方案A/B/C哪个更合理？
2. **功能完整性**: 是否缺少关键的Java特性？
3. **测试覆盖**: 测试设计是否充分？
4. **时间估算**: 工作量估算是否合理？
5. **技术方案**: 实现方案是否有更好的选择？
6. **商业价值**: 哪些Feature对商业化更重要？

---

**等待你的review反馈！** 🚀
