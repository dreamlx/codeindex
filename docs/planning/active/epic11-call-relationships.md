# Epic 11: Call Relationships Extraction for LoomGraph

**Epic ID**: 11
**Created**: 2026-02-06
**Status**: 🟢 Ready for Implementation
**Target Version**: v0.13.0
**Estimated Effort**: 16-20 days (3-4 weeks)

---

## 📋 Executive Summary

### Business Value
Enhance codeindex's LoomGraph integration by extracting **function/method call relationships** across Python, Java, and PHP codebases. This enables knowledge graph construction for code understanding, navigation, and architecture visualization.

### Goals
1. ✅ Extract caller → callee relationships for all three languages
2. ✅ Resolve import aliases (e.g., `pd.read_csv` → `pandas.read_csv`)
3. ✅ Filter to project-internal calls only (exclude stdlib/external)
4. ✅ Support simple decorators as implicit calls
5. ✅ Provide structured JSON output for LoomGraph consumption

### Success Criteria
- 100-120 tests passing across all stories
- Python, Java, PHP call extraction accuracy ≥ 95%
- Alias resolution accuracy ≥ 98% (Python)
- Project-internal filtering precision ≥ 90%
- JSON output validates against schema

---

## 🎯 Data Structure Design (Final)

### Core Data Model

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CallType(Enum):
    """调用类型枚举"""
    FUNCTION = "function"           # 函数调用: calculate()
    METHOD = "method"               # 实例方法: obj.method()
    STATIC_METHOD = "static_method" # 静态方法: Class.method()
    CONSTRUCTOR = "constructor"     # 构造函数: new Class() / __init__
    DYNAMIC = "dynamic"             # 动态调用: getattr(obj, name)()

@dataclass
class Call:
    """函数/方法调用关系 (Epic 11 MVP)

    Attributes:
        caller: 调用者的完整名称（含namespace）
            Examples:
            - "myproject.service.UserService.create_user"
            - "com.example.UserController.handleRequest"

        callee: 被调用者的完整名称（含namespace），动态调用时为None
            Examples:
            - "pandas.read_csv" (alias已解析)
            - "com.example.User.<init>" (构造函数)
            - None (无法确定的动态调用)

        line_number: 调用发生的行号（1-based）

        call_type: 调用类型（5种枚举）

        arguments_count: 参数数量（尽力而为，无法确定时为None）
            - Best-effort extraction from AST
            - Includes positional and keyword arguments
            - None for dynamic calls or complex patterns

    Design Rationale:
        - Simple: Only 5 fields, easy to understand
        - Pragmatic: Optional fields for uncertain data
        - Extensible: call_type enum allows future refinement
        - Actionable: Sufficient for knowledge graph construction
    """
    caller: str
    callee: Optional[str]
    line_number: int
    call_type: CallType
    arguments_count: Optional[int] = None

    @property
    def is_dynamic(self) -> bool:
        """是否为动态调用（无法确定callee）"""
        return self.call_type == CallType.DYNAMIC

    @property
    def is_resolved(self) -> bool:
        """调用是否已解析（callee非空）"""
        return self.callee is not None

    def to_dict(self) -> dict:
        """序列化为JSON格式"""
        return {
            "caller": self.caller,
            "callee": self.callee,
            "line_number": self.line_number,
            "call_type": self.call_type.value,
            "arguments_count": self.arguments_count,
        }

    @staticmethod
    def from_dict(data: dict) -> "Call":
        """从JSON反序列化"""
        return Call(
            caller=data["caller"],
            callee=data.get("callee"),
            line_number=data["line_number"],
            call_type=CallType(data["call_type"]),
            arguments_count=data.get("arguments_count"),
        )
```

### ParseResult Extension

```python
@dataclass
class ParseResult:
    """扩展ParseResult以支持calls（Epic 11）"""
    path: Path
    language: str
    symbols: list[Symbol]
    imports: list[Import]
    inheritances: list[Inheritance]  # Epic 10
    calls: list[Call]                # Epic 11 NEW
    namespace: str
    module_docstring: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """JSON序列化"""
        return {
            "path": str(self.path),
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": [i.to_dict() for i in self.imports],
            "inheritances": [ih.to_dict() for ih in self.inheritances],
            "calls": [c.to_dict() for c in self.calls],  # NEW
            "namespace": self.namespace,
            "module_docstring": self.module_docstring,
            "error": self.error,
        }
```

---

## 📖 Story Breakdown

### Story 11.1: Python Call Extraction ⭐⭐⭐⭐⭐

**Priority**: P0 (Must Have)
**Estimated Effort**: 4-5 days
**Dependencies**: Epic 10 (Import data for alias resolution)

#### User Story
As a developer analyzing Python code,
I want to extract function/method call relationships,
So that I can understand code dependencies and build call graphs.

#### Acceptance Criteria (30-35 Tests)

##### AC1: Basic Function Calls (5 tests)
```python
# Test 1: Simple function call
def helper():
    pass

def main():
    helper()  # ✅ Extract: main → helper

# Test 2: Module function call
import math

def calculate():
    math.sqrt(16)  # ✅ Extract: calculate → math.sqrt

# Test 3: Nested function call
def outer():
    def inner():
        pass
    inner()  # ✅ Extract: outer → outer.inner

# Test 4: Chained function calls
data = load().filter().sort()
# ✅ Extract:
#   - caller → load
#   - caller → filter
#   - caller → sort

# Test 5: Function call with arguments
result = calculate(a, b, c=10)
# ✅ Extract: caller → calculate, arguments_count=3
```

##### AC2: Method Calls (6 tests)
```python
# Test 1: Instance method call
class User:
    def save(self):
        pass

def create_user():
    user = User()
    user.save()  # ✅ Extract: create_user → User.save, call_type=METHOD

# Test 2: Static method call
class Utils:
    @staticmethod
    def format_date():
        pass

def process():
    Utils.format_date()  # ✅ Extract: process → Utils.format_date, call_type=STATIC_METHOD

# Test 3: Class method call
class Config:
    @classmethod
    def load(cls):
        pass

def init():
    Config.load()  # ✅ Extract: init → Config.load, call_type=STATIC_METHOD

# Test 4: Method call on returned object
def get_service():
    return UserService()

def run():
    get_service().process()
    # ✅ Extract: run → get_service
    # ⚠️ Cannot resolve: .process() (dynamic)

# Test 5: Method call with self
class Calculator:
    def add(self, a, b):
        return self.multiply(a, 1) + b  # ✅ Extract: Calculator.add → Calculator.multiply

# Test 6: Super method call
class Child(Parent):
    def method(self):
        super().method()  # ✅ Extract: Child.method → Parent.method
```

##### AC3: Constructor Calls (4 tests)
```python
# Test 1: Direct instantiation
def create_user():
    user = User()  # ✅ Extract: create_user → User.__init__, call_type=CONSTRUCTOR

# Test 2: Constructor with arguments
user = User(name="Alice", age=30)
# ✅ Extract: caller → User.__init__, arguments_count=2

# Test 3: Nested class instantiation
class Outer:
    class Inner:
        pass

obj = Outer.Inner()  # ✅ Extract: caller → Outer.Inner.__init__

# Test 4: Constructor via factory
class Factory:
    @staticmethod
    def create():
        return Product()  # ✅ Extract: Factory.create → Product.__init__
```

##### AC4: Alias Resolution ⭐⭐⭐⭐⭐ (7 tests)
```python
# Test 1: Simple alias
import pandas as pd

def load_data():
    df = pd.read_csv("data.csv")
    # ✅ Extract: load_data → pandas.read_csv (NOT pd.read_csv)

# Test 2: From-import alias
from numpy import array as np_array

def process():
    np_array([1, 2, 3])
    # ✅ Extract: process → numpy.array

# Test 3: Multiple aliases
import pandas as pd
import numpy as np

def analyze():
    pd.DataFrame(np.zeros(10))
    # ✅ Extract:
    #   - analyze → pandas.DataFrame
    #   - analyze → numpy.zeros

# Test 4: Nested module alias
import matplotlib.pyplot as plt

def plot():
    plt.figure()
    # ✅ Extract: plot → matplotlib.pyplot.figure

# Test 5: Alias without call
import unused_module as um
# ⚠️ No call extracted (import only)

# Test 6: Relative import alias
from ..utils import helper as h

def main():
    h()  # ✅ Extract: main → <package>.utils.helper

# Test 7: Conflicting aliases (same name)
import moduleA as mod
import moduleB as mod  # Overwrites

def func():
    mod.call()  # ✅ Extract: func → moduleB.call (last wins)
```

##### AC5: Decorator Calls (Phase 1 - Simple Only) (4 tests)
```python
# Test 1: Simple decorator
@decorator
def func():
    pass
# ✅ Extract: <module> → decorator, call_type=FUNCTION, arguments_count=1

# Test 2: Multiple simple decorators
@decorator1
@decorator2
def func():
    pass
# ✅ Extract:
#   - <module> → decorator1
#   - <module> → decorator2

# Test 3: Class decorator
@singleton
class Config:
    pass
# ✅ Extract: <module> → singleton, arguments_count=1

# Test 4: Method decorator
class Service:
    @cached_property
    def data(self):
        pass
# ✅ Extract: Service → cached_property

# ⚠️ Phase 1 Exclusions (defer to Phase 2):
# - Decorator with arguments: @decorator(arg1, arg2)
# - Decorator factories: @decorator_factory()
# - Nested decorators: @outer(@inner)
```

##### AC6: Project-Internal Filtering (3 tests)
```python
# Configuration:
# project_namespaces: ["myproject"]

# Test 1: Project-internal call
# File: myproject/service.py
from myproject.utils import helper

def process():
    helper()  # ✅ Extract: myproject.service.process → myproject.utils.helper

# Test 2: External library call (SKIP)
import pandas as pd

def load():
    pd.read_csv()  # ❌ NOT extracted (pandas is external)

# Test 3: Stdlib call (SKIP)
import math

def calc():
    math.sqrt(16)  # ❌ NOT extracted (math is stdlib)
```

##### AC7: Edge Cases (6 tests)
```python
# Test 1: Lambda call
process = lambda x: helper(x)
# ⚠️ Cannot resolve: lambda → helper (skip)

# Test 2: Dynamic call via getattr
obj = get_object()
method = getattr(obj, "method_name")
method()
# ✅ Extract: caller → <dynamic>, call_type=DYNAMIC, callee=None

# Test 3: Call in list comprehension
results = [process(x) for x in items]
# ✅ Extract: caller → process

# Test 4: Call in conditional
if condition:
    func1()
else:
    func2()
# ✅ Extract: caller → func1, caller → func2

# Test 5: Recursive call
def factorial(n):
    return factorial(n-1)  # ✅ Extract: factorial → factorial

# Test 6: No calls in function
def standalone():
    x = 10
    return x
# ⚠️ No calls extracted
```

#### Technical Implementation

##### AST Traversal Strategy
```python
def _extract_python_calls(
    node: Node,
    source_bytes: bytes,
    context: str,
    alias_map: dict[str, str],
    project_namespaces: list[str]
) -> list[Call]:
    """提取Python调用关系（递归遍历AST）

    Args:
        node: tree-sitter AST节点
        source_bytes: 源代码字节
        context: 当前上下文（函数/方法/模块名称）
        alias_map: Import alias映射表（来自Epic 10）
        project_namespaces: 项目namespace列表（用于过滤）

    Returns:
        调用关系列表
    """
    calls = []

    # 处理函数调用节点
    if node.type == "call":
        call = _parse_python_call(node, source_bytes, context, alias_map)

        # 过滤：仅保留项目内调用
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    # 处理装饰器节点（Phase 1）
    if node.type in ("function_definition", "class_definition"):
        decorator_calls = _extract_decorator_calls(node, source_bytes, context)
        calls.extend(decorator_calls)

    # 递归遍历子节点
    for child in node.children:
        calls.extend(_extract_python_calls(
            child, source_bytes, context, alias_map, project_namespaces
        ))

    return calls


def _parse_python_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    alias_map: dict[str, str]
) -> Optional[Call]:
    """解析单个Python调用节点

    Call node structure:
        (call
          function: (identifier) "helper"
          arguments: (argument_list))

    OR:
        (call
          function: (attribute
                      object: (identifier) "obj"
                      attribute: (identifier) "method")
          arguments: (argument_list))
    """
    # 提取callee名称
    func_node = node.child_by_field_name("function")
    if not func_node:
        return None

    callee_raw = extract_call_name(func_node, source_bytes)

    # 解析alias（关键步骤！）
    callee = resolve_alias(callee_raw, alias_map)

    # 确定调用类型
    call_type = determine_call_type(func_node, source_bytes)

    # 提取参数数量（尽力而为）
    args_node = node.child_by_field_name("arguments")
    args_count = count_arguments(args_node) if args_node else None

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=call_type,
        arguments_count=args_count
    )


def build_alias_map(imports: list[Import]) -> dict[str, str]:
    """构建alias到真实模块名的映射（来自Epic 10 Import数据）

    Examples:
        >>> imports = [
        ...     Import(module="pandas", alias="pd"),
        ...     Import(module="numpy", alias="np"),
        ...     Import(from_module="matplotlib.pyplot", alias="plt"),
        ... ]
        >>> build_alias_map(imports)
        {'pd': 'pandas', 'np': 'numpy', 'plt': 'matplotlib.pyplot'}
    """
    alias_map = {}
    for imp in imports:
        if imp.alias:
            # 优先使用from_module（更精确）
            module = imp.from_module if imp.from_module else imp.module
            alias_map[imp.alias] = module
    return alias_map


def resolve_alias(callee: str, alias_map: dict[str, str]) -> str:
    """解析callee中的alias（核心逻辑）

    Examples:
        >>> resolve_alias("pd.read_csv", {"pd": "pandas"})
        'pandas.read_csv'

        >>> resolve_alias("helper", {})
        'helper'

        >>> resolve_alias("np.array", {"np": "numpy"})
        'numpy.array'
    """
    if not callee or "." not in callee:
        return callee

    parts = callee.split(".", 1)
    prefix = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""

    if prefix in alias_map:
        real_prefix = alias_map[prefix]
        return f"{real_prefix}.{suffix}" if suffix else real_prefix

    return callee


def determine_call_type(func_node: Node, source_bytes: bytes) -> CallType:
    """确定调用类型

    Rules:
        - Constructor: User() → CONSTRUCTOR
        - Static method: Class.method() → STATIC_METHOD
        - Instance method: obj.method() → METHOD
        - Simple call: func() → FUNCTION
        - Dynamic: getattr() → DYNAMIC
    """
    if func_node.type == "identifier":
        name = extract_text(func_node, source_bytes)
        # 构造函数：首字母大写
        if name and name[0].isupper():
            return CallType.CONSTRUCTOR
        # 动态调用：getattr, setattr, eval, exec, __import__
        if name in ("getattr", "setattr", "eval", "exec", "__import__"):
            return CallType.DYNAMIC
        return CallType.FUNCTION

    elif func_node.type == "attribute":
        obj_node = func_node.child_by_field_name("object")
        if obj_node and obj_node.type == "identifier":
            obj_name = extract_text(obj_node, source_bytes)
            # 类方法调用：ClassName.method()
            if obj_name and obj_name[0].isupper():
                return CallType.STATIC_METHOD
        return CallType.METHOD

    return CallType.FUNCTION


def _extract_decorator_calls(
    node: Node,
    source_bytes: bytes,
    context: str
) -> list[Call]:
    """提取装饰器调用（Phase 1: 仅简单装饰器）

    AST structure:
        (function_definition
          (decorator
            (identifier) "cached_property")  ← Simple decorator
          name: (identifier) "data"
          ...)
    """
    calls = []

    if node.type not in ("function_definition", "class_definition"):
        return calls

    for child in node.children:
        if child.type == "decorator":
            decorator_name = extract_decorator_name(child, source_bytes)

            # Phase 1: 仅支持简单装饰器（单个identifier）
            if is_simple_decorator(child):
                calls.append(Call(
                    caller=context,
                    callee=decorator_name,
                    line_number=child.start_point[0] + 1,
                    call_type=CallType.FUNCTION,
                    arguments_count=1  # 装饰器接收1个参数（被装饰对象）
                ))

    return calls


def is_simple_decorator(decorator_node: Node) -> bool:
    """判断是否为简单装饰器（Phase 1支持）

    Simple decorators:
        @decorator         ✅
        @module.decorator  ✅

    Complex decorators (Phase 2):
        @decorator(arg1, arg2)  ❌
        @decorator()            ❌
        @outer(@inner)          ❌
    """
    # 检查decorator节点是否只有identifier或attribute子节点
    for child in decorator_node.children:
        if child.type == "call":  # 有call节点说明是复杂装饰器
            return False
    return True
```

##### Project-Internal Filtering
```python
def is_project_call(callee: Optional[str], project_namespaces: list[str]) -> bool:
    """判断调用是否属于项目内

    Rules:
        1. callee为None（动态调用）→ False
        2. callee无namespace（同文件调用）→ True
        3. callee的namespace在project_namespaces中 → True
        4. 其他 → False (外部调用)

    Examples:
        >>> is_project_call("helper", ["myproject"])
        True  # 同文件调用

        >>> is_project_call("myproject.utils.helper", ["myproject"])
        True

        >>> is_project_call("pandas.read_csv", ["myproject"])
        False  # 外部库

        >>> is_project_call(None, ["myproject"])
        False  # 动态调用
    """
    if not callee:
        return False

    # 无namespace的调用视为项目内（同文件调用）
    if "." not in callee:
        return True

    # 检查是否匹配项目namespace
    for ns in project_namespaces:
        if callee.startswith(ns + "."):
            return True

    return False


def detect_project_namespaces(scan_dirs: list[Path]) -> list[str]:
    """自动检测项目的主要namespace

    Strategy:
        1. 扫描所有Python文件
        2. 提取namespace（来自ParseResult）
        3. 统计top-level namespace频率
        4. 返回频率最高的前N个

    Examples:
        scan_dirs = [Path("src")]
        Files:
            src/myproject/service.py → namespace="myproject.service"
            src/myproject/utils.py   → namespace="myproject.utils"
            src/tests/test_*.py      → namespace="tests.*"

        Result: ["myproject", "tests"]
    """
    namespace_counts = {}

    for dir_path in scan_dirs:
        for file in dir_path.rglob("*.py"):
            result = parse_file(file)
            if result.namespace:
                top_ns = result.namespace.split('.')[0]
                namespace_counts[top_ns] = namespace_counts.get(top_ns, 0) + 1

    # 返回频率 > 5的namespace（过滤噪音）
    return [ns for ns, count in namespace_counts.items() if count > 5]
```

#### Test Structure
```python
# tests/test_python_calls.py

class TestBasicFunctionCalls:
    """Basic function call extraction (AC1)"""
    def test_simple_function_call(self, tmp_path): ...
    def test_module_function_call(self, tmp_path): ...
    def test_nested_function_call(self, tmp_path): ...
    def test_chained_function_calls(self, tmp_path): ...
    def test_function_call_with_arguments(self, tmp_path): ...

class TestMethodCalls:
    """Method call extraction (AC2)"""
    def test_instance_method_call(self, tmp_path): ...
    def test_static_method_call(self, tmp_path): ...
    def test_class_method_call(self, tmp_path): ...
    def test_method_call_on_returned_object(self, tmp_path): ...
    def test_method_call_with_self(self, tmp_path): ...
    def test_super_method_call(self, tmp_path): ...

class TestConstructorCalls:
    """Constructor call extraction (AC3)"""
    def test_direct_instantiation(self, tmp_path): ...
    def test_constructor_with_arguments(self, tmp_path): ...
    def test_nested_class_instantiation(self, tmp_path): ...
    def test_constructor_via_factory(self, tmp_path): ...

class TestAliasResolution:
    """Import alias resolution (AC4) ⭐⭐⭐⭐⭐"""
    def test_simple_alias(self, tmp_path): ...
    def test_from_import_alias(self, tmp_path): ...
    def test_multiple_aliases(self, tmp_path): ...
    def test_nested_module_alias(self, tmp_path): ...
    def test_alias_without_call(self, tmp_path): ...
    def test_relative_import_alias(self, tmp_path): ...
    def test_conflicting_aliases(self, tmp_path): ...

class TestDecoratorCalls:
    """Decorator call extraction - Phase 1 only (AC5)"""
    def test_simple_decorator(self, tmp_path): ...
    def test_multiple_simple_decorators(self, tmp_path): ...
    def test_class_decorator(self, tmp_path): ...
    def test_method_decorator(self, tmp_path): ...

class TestProjectInternalFiltering:
    """Project-internal call filtering (AC6)"""
    def test_project_internal_call(self, tmp_path): ...
    def test_external_library_call_skipped(self, tmp_path): ...
    def test_stdlib_call_skipped(self, tmp_path): ...

class TestEdgeCases:
    """Edge cases and special patterns (AC7)"""
    def test_lambda_call_skipped(self, tmp_path): ...
    def test_dynamic_call_via_getattr(self, tmp_path): ...
    def test_call_in_list_comprehension(self, tmp_path): ...
    def test_call_in_conditional(self, tmp_path): ...
    def test_recursive_call(self, tmp_path): ...
    def test_no_calls_in_function(self, tmp_path): ...
```

---

### Story 11.2: Java Call Extraction ⭐⭐⭐⭐⭐

**Priority**: P0 (Must Have)
**Estimated Effort**: 4-5 days
**Dependencies**: Story 11.1 (call extraction pattern), Epic 10 (Import data)

#### User Story
As a developer analyzing Java code,
I want to extract method/constructor call relationships,
So that I can understand dependencies in Java applications.

#### Acceptance Criteria (30-35 Tests)

##### AC1: Basic Method Calls (6 tests)
```java
// Test 1: Instance method call
public class UserService {
    public void createUser() {
        User user = new User();
        user.save();  // ✅ Extract: UserService.createUser → User.save, call_type=METHOD
    }
}

// Test 2: Static method call
public class Utils {
    public static String formatDate() { }
}

public void process() {
    Utils.formatDate();  // ✅ Extract: process → Utils.formatDate, call_type=STATIC_METHOD
}

// Test 3: Method chaining
public void loadData() {
    String result = builder.setName("test")
                          .setAge(30)
                          .build();
    // ✅ Extract:
    //   - loadData → Builder.setName
    //   - loadData → Builder.setAge
    //   - loadData → Builder.build
}

// Test 4: Method call with generics
List<String> list = new ArrayList<>();
list.add("item");  // ✅ Extract: caller → ArrayList.add

// Test 5: Interface method call
public void process(Runnable task) {
    task.run();  // ✅ Extract: process → Runnable.run
}

// Test 6: Super method call
class Child extends Parent {
    @Override
    public void method() {
        super.method();  // ✅ Extract: Child.method → Parent.method
    }
}
```

##### AC2: Constructor Calls (5 tests)
```java
// Test 1: Direct instantiation
public void create() {
    User user = new User();
    // ✅ Extract: create → com.example.User.<init>, call_type=CONSTRUCTOR
}

// Test 2: Constructor with arguments
User user = new User("Alice", 30);
// ✅ Extract: caller → User.<init>, arguments_count=2

// Test 3: Anonymous class instantiation
Runnable task = new Runnable() {
    public void run() { }
};
// ✅ Extract: caller → Runnable.<init>

// Test 4: Inner class instantiation
Outer.Inner obj = new Outer().new Inner();
// ✅ Extract:
//   - caller → Outer.<init>
//   - caller → Outer.Inner.<init>

// Test 5: Generic constructor
List<String> list = new ArrayList<String>();
// ✅ Extract: caller → java.util.ArrayList.<init>
```

##### AC3: Static Import Resolution (4 tests)
```java
// Test 1: Static import method
import static java.util.Collections.sort;

public void organize() {
    sort(list);  // ✅ Extract: organize → java.util.Collections.sort
}

// Test 2: Static import wildcard
import static java.lang.Math.*;

public void calc() {
    double result = sqrt(16);
    // ✅ Extract: calc → java.lang.Math.sqrt
}

// Test 3: Static import from same package
package com.example;
import static com.example.Utils.helper;

public void process() {
    helper();  // ✅ Extract: process → com.example.Utils.helper
}

// Test 4: Ambiguous static import (resolve to first match)
import static com.example.A.method;
import static com.example.B.method;

public void run() {
    method();  // ✅ Extract: run → com.example.A.method (first wins)
}
```

##### AC4: Full Qualified Name Calls (3 tests)
```java
// Test 1: FQN in code
public void load() {
    java.util.List list = new java.util.ArrayList();
    // ✅ Extract: load → java.util.ArrayList.<init>
}

// Test 2: FQN static method
public void process() {
    java.lang.Math.sqrt(16);
    // ✅ Extract: process → java.lang.Math.sqrt
}

// Test 3: Mix FQN and import
import com.example.User;

public void create() {
    User user = new User();  // ✅ com.example.User.<init>
    com.other.Admin admin = new com.other.Admin();  // ✅ com.other.Admin.<init>
}
```

##### AC5: Method Reference (Java 8+) (3 tests)
```java
// Test 1: Static method reference
list.forEach(System.out::println);
// ✅ Extract: caller → System.out.println

// Test 2: Instance method reference
list.stream().map(String::toUpperCase);
// ✅ Extract: caller → String.toUpperCase

// Test 3: Constructor reference
Supplier<User> factory = User::new;
// ✅ Extract: caller → User.<init>
```

##### AC6: Project-Internal Filtering (3 tests)
```java
// Configuration:
// project_namespaces: ["com.example"]

// Test 1: Project-internal call
package com.example.service;
import com.example.model.User;

public class UserService {
    public void process() {
        User user = new User();
        // ✅ Extract: UserService.process → com.example.model.User.<init>
    }
}

// Test 2: External library call (SKIP)
import org.springframework.beans.factory.annotation.Autowired;
// ❌ NOT extracted (Spring is external)

// Test 3: java.lang call (SKIP)
public void calc() {
    Math.sqrt(16);  // ❌ NOT extracted (java.lang is stdlib)
}
```

##### AC7: Edge Cases (6 tests)
```java
// Test 1: Varargs call
public void process(String... args) { }
process("a", "b", "c");  // ✅ arguments_count=3

// Test 2: Lambda expression
list.forEach(item -> process(item));
// ✅ Extract: caller → process

// Test 3: Ternary operator call
String result = condition ? func1() : func2();
// ✅ Extract: caller → func1, caller → func2

// Test 4: Nested method calls
process(calculate(getData()));
// ✅ Extract: caller → getData, caller → calculate, caller → process

// Test 5: Reflection call (dynamic)
Method method = obj.getClass().getMethod("methodName");
method.invoke(obj);
// ✅ Extract: caller → <dynamic>, call_type=DYNAMIC, callee=None

// Test 6: No calls in method
public void standalone() {
    int x = 10;
    return x;
}
// ⚠️ No calls extracted
```

##### AC8: Annotation-Based Calls (3 tests)
```java
// Test 1: Spring @Autowired (skip - not a call)
@Autowired
private UserService service;
// ❌ NOT extracted (annotation, not call)

// Test 2: JUnit @Test (skip)
@Test
public void testMethod() { }
// ❌ NOT extracted

// Test 3: Custom annotation with method call inside
@CustomAnnotation
public void annotated() {
    helper();  // ✅ Extract: annotated → helper
}
```

#### Technical Implementation

```java
def _extract_java_calls(
    node: Node,
    source_bytes: bytes,
    context: str,
    import_map: dict[str, str],
    project_namespaces: list[str]
) -> list[Call]:
    """提取Java调用关系

    Key Java AST nodes:
        - method_invocation: obj.method()
        - object_creation_expression: new Class()
        - method_reference: Class::method
        - super: super.method()
    """
    calls = []

    if node.type == "method_invocation":
        call = _parse_java_method_call(node, source_bytes, context, import_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    elif node.type == "object_creation_expression":
        call = _parse_java_constructor_call(node, source_bytes, context, import_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    elif node.type == "method_reference":
        call = _parse_java_method_reference(node, source_bytes, context, import_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    # 递归子节点
    for child in node.children:
        calls.extend(_extract_java_calls(
            child, source_bytes, context, import_map, project_namespaces
        ))

    return calls


def _parse_java_method_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    import_map: dict[str, str]
) -> Optional[Call]:
    """解析Java方法调用

    AST structure:
        (method_invocation
          object: (identifier) "user"
          name: (identifier) "save"
          arguments: (argument_list))
    """
    # 提取方法名
    name_node = node.child_by_field_name("name")
    if not name_node:
        return None
    method_name = extract_text(name_node, source_bytes)

    # 提取对象名（如果有）
    obj_node = node.child_by_field_name("object")
    if obj_node:
        obj_name = extract_qualified_name(obj_node, source_bytes)
        # 解析import
        resolved_class = import_map.get(obj_name, obj_name)
        callee = f"{resolved_class}.{method_name}"
    else:
        # 无对象，可能是静态导入或同类方法
        callee = method_name

    # 提取参数
    args_node = node.child_by_field_name("arguments")
    args_count = count_java_arguments(args_node) if args_node else None

    # 确定调用类型
    call_type = determine_java_call_type(obj_node, obj_name if obj_node else None)

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=call_type,
        arguments_count=args_count
    )


def format_java_constructor_callee(class_name: str) -> str:
    """格式化Java构造函数callee

    Examples:
        >>> format_java_constructor_callee("com.example.User")
        'com.example.User.<init>'
    """
    return f"{class_name}.<init>"
```

---

### Story 11.3: PHP Call Extraction ⭐⭐⭐⭐

**Priority**: P0 (Must Have)
**Estimated Effort**: 3-4 days
**Dependencies**: Story 11.1, 11.2 (call extraction patterns)

#### User Story
As a developer analyzing PHP code,
I want to extract function/method call relationships,
So that I can understand dependencies in PHP applications.

#### Acceptance Criteria (25-30 Tests)

##### AC1: Basic Function Calls (5 tests)
```php
// Test 1: Simple function call
function helper() { }

function main() {
    helper();  // ✅ Extract: main → helper
}

// Test 2: Namespaced function call
namespace App\Utils;

function format_date() { }

namespace App\Service;
use function App\Utils\format_date;

function process() {
    format_date();  // ✅ Extract: App\Service\process → App\Utils\format_date
}

// Test 3: Global function call
function load_data() {
    var_dump($data);  // ❌ NOT extracted (built-in function)
}

// Test 4: Function call with arguments
$result = calculate($a, $b, $c);
// ✅ Extract: caller → calculate, arguments_count=3

// Test 5: Variable function call (dynamic)
$func = 'helper';
$func();  // ✅ Extract: caller → <dynamic>, call_type=DYNAMIC, callee=None
```

##### AC2: Method Calls (6 tests)
```php
// Test 1: Instance method call
class User {
    public function save() { }
}

function createUser() {
    $user = new User();
    $user->save();  // ✅ Extract: createUser → User::save, call_type=METHOD
}

// Test 2: Static method call
class Utils {
    public static function formatDate() { }
}

function process() {
    Utils::formatDate();  // ✅ Extract: process → Utils::formatDate, call_type=STATIC_METHOD
}

// Test 3: Method chaining
$result = $builder->setName('test')
                  ->setAge(30)
                  ->build();
// ✅ Extract: caller → Builder::setName, Builder::setAge, Builder::build

// Test 4: Method call with self
class Calculator {
    public function add($a, $b) {
        return $this->multiply($a, 1) + $b;
        // ✅ Extract: Calculator::add → Calculator::multiply
    }
}

// Test 5: Parent method call
class Child extends Parent {
    public function method() {
        parent::method();  // ✅ Extract: Child::method → Parent::method
    }
}

// Test 6: Variable method call (dynamic)
$method = 'getData';
$obj->$method();  // ✅ Extract: caller → <dynamic>, call_type=DYNAMIC
```

##### AC3: Constructor Calls (4 tests)
```php
// Test 1: Direct instantiation
function create() {
    $user = new User();
    // ✅ Extract: create → User::__construct, call_type=CONSTRUCTOR
}

// Test 2: Namespaced class instantiation
namespace App\Service;
use App\Model\User;

function createUser() {
    $user = new User();
    // ✅ Extract: App\Service\createUser → App\Model\User::__construct
}

// Test 3: Constructor with arguments
$user = new User('Alice', 30);
// ✅ Extract: caller → User::__construct, arguments_count=2

// Test 4: Anonymous class (PHP 7+)
$obj = new class {
    public function method() { }
};
// ⚠️ Skip (anonymous class, no meaningful callee)
```

##### AC4: Namespace Resolution (5 tests)
```php
// Test 1: Use statement
namespace App\Service;
use App\Model\User;

function process() {
    $user = new User();
    // ✅ Extract: App\Service\process → App\Model\User::__construct
}

// Test 2: Use alias
namespace App\Service;
use App\Model\User as UserModel;

function create() {
    $user = new UserModel();
    // ✅ Extract: create → App\Model\User::__construct (alias resolved)
}

// Test 3: Fully qualified name
namespace App\Service;

function load() {
    $user = new \App\Model\User();
    // ✅ Extract: load → App\Model\User::__construct
}

// Test 4: Same namespace call
namespace App\Service;

class Helper { }

class UserService {
    public function process() {
        new Helper();
        // ✅ Extract: UserService::process → App\Service\Helper::__construct
    }
}

// Test 5: Global namespace call
namespace App;

function run() {
    new \Exception('error');
    // ✅ Extract: run → Exception::__construct (global namespace)
}
```

##### AC5: Project-Internal Filtering (3 tests)
```php
// Configuration:
// project_namespaces: ["App"]

// Test 1: Project-internal call
namespace App\Service;
use App\Model\User;

function process() {
    new User();  // ✅ Extract: process → App\Model\User::__construct
}

// Test 2: External library call (SKIP)
use Symfony\Component\HttpFoundation\Request;
// ❌ NOT extracted (Symfony is external)

// Test 3: Built-in function call (SKIP)
function load() {
    json_decode($data);  // ❌ NOT extracted (built-in)
}
```

##### AC6: Edge Cases (6 tests)
```php
// Test 1: Call in closure
$func = function() {
    helper();  // ✅ Extract: <closure> → helper
};

// Test 2: Call in ternary
$result = $condition ? func1() : func2();
// ✅ Extract: caller → func1, caller → func2

// Test 3: Call in array
$handlers = [
    'create' => function() { create(); },  // ✅ Extract
];

// Test 4: Nested calls
process(calculate(getData()));
// ✅ Extract: caller → getData, calculate, process

// Test 5: Magic method call
$obj->__call('method', []);
// ⚠️ Skip magic methods

// Test 6: No calls in function
function standalone() {
    $x = 10;
    return $x;
}
// ⚠️ No calls extracted
```

#### Technical Implementation

```php
def _extract_php_calls(
    node: Node,
    source_bytes: bytes,
    context: str,
    namespace_map: dict[str, str],
    project_namespaces: list[str]
) -> list[Call]:
    """提取PHP调用关系

    Key PHP AST nodes:
        - function_call_expression: func()
        - member_call_expression: $obj->method()
        - scoped_call_expression: Class::method()
        - object_creation_expression: new Class()
    """
    calls = []

    if node.type == "function_call_expression":
        call = _parse_php_function_call(node, source_bytes, context, namespace_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    elif node.type == "member_call_expression":
        call = _parse_php_member_call(node, source_bytes, context, namespace_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    elif node.type == "scoped_call_expression":
        call = _parse_php_scoped_call(node, source_bytes, context, namespace_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    elif node.type == "object_creation_expression":
        call = _parse_php_constructor_call(node, source_bytes, context, namespace_map)
        if call and is_project_call(call.callee, project_namespaces):
            calls.append(call)

    # 递归
    for child in node.children:
        calls.extend(_extract_php_calls(
            child, source_bytes, context, namespace_map, project_namespaces
        ))

    return calls


def format_php_constructor_callee(class_name: str) -> str:
    """格式化PHP构造函数callee

    Examples:
        >>> format_php_constructor_callee("App\\Model\\User")
        'App\\Model\\User::__construct'
    """
    return f"{class_name}::__construct"
```

---

### Story 11.4: Integration & JSON Output ⭐⭐⭐

**Priority**: P1 (Important)
**Estimated Effort**: 2-3 days
**Dependencies**: Story 11.1, 11.2, 11.3

#### User Story
As a LoomGraph user,
I want to consume call relationships in JSON format,
So that I can build knowledge graphs from codeindex output.

#### Acceptance Criteria (10-15 Tests)

##### AC1: JSON Output Format (3 tests)
```json
// Test 1: Basic JSON structure
{
  "path": "src/myproject/service.py",
  "language": "python",
  "namespace": "myproject.service",
  "calls": [
    {
      "caller": "myproject.service.UserService.create_user",
      "callee": "myproject.model.User.__init__",
      "line_number": 42,
      "call_type": "constructor",
      "arguments_count": 2
    }
  ]
}

// Test 2: Multiple calls
{
  "calls": [
    {
      "caller": "process",
      "callee": "pandas.read_csv",
      "line_number": 15,
      "call_type": "function",
      "arguments_count": 1
    },
    {
      "caller": "process",
      "callee": "helper",
      "line_number": 20,
      "call_type": "function",
      "arguments_count": 0
    }
  ]
}

// Test 3: Dynamic call (callee=null)
{
  "calls": [
    {
      "caller": "dynamic_caller",
      "callee": null,
      "line_number": 30,
      "call_type": "dynamic",
      "arguments_count": null
    }
  ]
}
```

##### AC2: CLI Integration (4 tests)
```bash
# Test 1: Scan with call extraction
codeindex scan ./src --output json
# ✅ Output includes "calls" field

# Test 2: Scan-all with call extraction
codeindex scan-all --output json > results.json
# ✅ All ParseResults include "calls"

# Test 3: Configuration control
# .codeindex.yaml:
# call_extraction:
#   enabled: false
codeindex scan ./src --output json
# ✅ "calls" field is empty array []

# Test 4: Project namespace auto-detection
codeindex scan ./src --output json
# ✅ Only project-internal calls included
```

##### AC3: Backward Compatibility (2 tests)
```python
# Test 1: ParseResult without calls (old code)
result = ParseResult(
    path=Path("test.py"),
    language="python",
    symbols=[],
    imports=[],
    inheritances=[],
    namespace="",
)
# ✅ calls defaults to []

# Test 2: JSON output without call_extraction
{
  "path": "test.py",
  "symbols": [...],
  "imports": [...],
  "inheritances": [...],
  "calls": []  // ✅ Empty but present
}
```

##### AC4: Configuration Schema (3 tests)
```yaml
# Test 1: Basic configuration
call_extraction:
  enabled: true
  project_namespaces: auto  # Auto-detect

# Test 2: Manual namespaces
call_extraction:
  enabled: true
  project_namespaces:
    - myproject
    - tests
  include_decorators: true
  max_calls_per_file: 1000

# Test 3: Disabled
call_extraction:
  enabled: false
```

##### AC5: Performance Validation (3 tests)
```python
# Test 1: Large file performance (5000 lines)
# Time limit: < 2 seconds per file
result = parse_file(large_file)
# ✅ calls extracted within time limit

# Test 2: Many calls (500 calls in one file)
# Memory limit: < 100MB increase
result = parse_file(many_calls_file)
# ✅ len(result.calls) == 500

# Test 3: Parallel scanning (10 files)
results = scan_directory(ten_files)
# ✅ All files processed in parallel
# ✅ Total time < 5 seconds
```

#### Technical Implementation

##### Configuration Extension
```yaml
# .codeindex.yaml (v0.13.0+)

# Call extraction settings (Epic 11)
call_extraction:
  enabled: true                    # Enable/disable call extraction

  # Project namespace detection
  project_namespaces: auto         # auto | manual list
  # Manual override:
  # project_namespaces:
  #   - myproject
  #   - tests

  # Feature toggles
  include_decorators: true         # Include decorator calls (Python)
  include_method_references: true  # Include method references (Java)

  # Performance limits
  max_calls_per_file: 1000         # Prevent excessive memory usage

  # Filtering
  include_stdlib: false            # Exclude stdlib calls
  include_external: false          # Exclude external library calls
```

##### CLI Updates
```python
# src/codeindex/cli.py

@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", type=click.Choice(["text", "json"]), default="text")
def scan(path: str, output: str):
    """Scan directory and extract code information"""
    config = load_config()

    # Parse files
    results = parse_directory(Path(path), config)

    if output == "json":
        # Include calls in JSON output
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        # Text output (existing behavior)
        write_readme(results, config)
```

##### JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ParseResult",
  "type": "object",
  "properties": {
    "path": { "type": "string" },
    "language": { "type": "string", "enum": ["python", "java", "php"] },
    "namespace": { "type": "string" },
    "symbols": { "type": "array" },
    "imports": { "type": "array" },
    "inheritances": { "type": "array" },
    "calls": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "caller": { "type": "string" },
          "callee": { "type": ["string", "null"] },
          "line_number": { "type": "integer", "minimum": 1 },
          "call_type": {
            "type": "string",
            "enum": ["function", "method", "static_method", "constructor", "dynamic"]
          },
          "arguments_count": { "type": ["integer", "null"], "minimum": 0 }
        },
        "required": ["caller", "callee", "line_number", "call_type"]
      }
    }
  },
  "required": ["path", "language", "calls"]
}
```

---

## 🛠️ Technical Architecture

### Module Structure
```
src/codeindex/
├── parser.py                    # Core parser (add call extraction)
│   ├── _extract_python_calls()  # Story 11.1
│   ├── _extract_java_calls()    # Story 11.2
│   └── _extract_php_calls()     # Story 11.3
│
├── call_utils.py                # NEW: Call extraction utilities
│   ├── build_alias_map()
│   ├── resolve_alias()
│   ├── is_project_call()
│   ├── detect_project_namespaces()
│   ├── determine_call_type()
│   ├── count_arguments()
│   └── format_constructor_callee()
│
├── data_types.py                # Extend with Call, CallType
│
└── config.py                    # Add call_extraction config

tests/
├── test_python_calls.py         # Story 11.1 tests (30-35)
├── test_java_calls.py           # Story 11.2 tests (30-35)
├── test_php_calls.py            # Story 11.3 tests (25-30)
└── test_call_integration.py     # Story 11.4 tests (10-15)
```

### Key Algorithms

#### 1. Alias Resolution (Highest Priority)
```python
# Input: ParseResult.imports (Epic 10)
imports = [
    Import(module="pandas", alias="pd"),
    Import(module="numpy", alias="np"),
]

# Build map
alias_map = build_alias_map(imports)
# → {"pd": "pandas", "np": "numpy"}

# Resolve during call extraction
callee_raw = "pd.read_csv"
callee = resolve_alias(callee_raw, alias_map)
# → "pandas.read_csv"
```

#### 2. Project-Internal Filtering
```python
# Auto-detect project namespaces
scan_dirs = [Path("src")]
project_ns = detect_project_namespaces(scan_dirs)
# → ["myproject", "tests"]

# Filter calls
callee = "myproject.utils.helper"
is_internal = is_project_call(callee, project_ns)
# → True

callee = "pandas.read_csv"
is_internal = is_project_call(callee, project_ns)
# → False (excluded)
```

#### 3. Constructor Naming Convention
```python
# Python
format_constructor_callee("User", "python")
# → "User.__init__"

# Java
format_constructor_callee("com.example.User", "java")
# → "com.example.User.<init>"

# PHP
format_constructor_callee("App\\Model\\User", "php")
# → "App\\Model\\User::__construct"
```

---

## 📊 Testing Strategy

### Test Coverage Target
- Overall: ≥ 90% coverage
- Core extraction functions: 95%+
- Edge cases: Full coverage

### Test Distribution
```
Total: 100-120 tests

Story 11.1 (Python):  30-35 tests (30%)
Story 11.2 (Java):    30-35 tests (30%)
Story 11.3 (PHP):     25-30 tests (25%)
Story 11.4 (Integration): 10-15 tests (15%)
```

### Critical Test Areas
1. **Alias Resolution** (⭐⭐⭐⭐⭐): 7 tests in Python, 4 in Java, 5 in PHP
2. **Project Filtering**: 3 tests per language
3. **Call Type Classification**: Covered in all basic tests
4. **Constructor Naming**: 4-5 tests per language
5. **Edge Cases**: 6 tests per language

---

## ⚠️ Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Alias resolution accuracy | High | Medium | Comprehensive testing (7 tests), use Epic 10 data |
| Dynamic call noise | Medium | High | Mark as DYNAMIC, callee=None |
| Performance on large files | Medium | Low | ThreadPool, max_calls_per_file limit |
| Cross-language consistency | High | Medium | Shared call_utils module, unified data model |
| Tree-sitter AST variations | Medium | Medium | Extensive real-world test cases |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Underestimated complexity | Medium | 25% buffer included (16-20 days) |
| Blocker bugs in dependencies | Low | Epic 10 already stable |
| Scope creep (complex decorators) | High | Strict Phase 1 scope, defer to Phase 2 |

---

## 🚀 Success Metrics

### Quantitative Goals
- ✅ 100-120 tests passing
- ✅ 0 regressions in existing tests (415 tests)
- ✅ Call extraction accuracy ≥ 95% (measured on real codebases)
- ✅ Alias resolution accuracy ≥ 98% (Python)
- ✅ Project-internal filtering precision ≥ 90%
- ✅ Performance: < 2s per 5000-line file
- ✅ Memory: < 100MB increase for 500 calls/file

### Qualitative Goals
- ✅ LoomGraph can consume JSON output directly
- ✅ Documentation is clear and comprehensive
- ✅ Code is maintainable (follows existing patterns)
- ✅ Configuration is intuitive

---

## 📅 Timeline & Milestones

### Week 1 (Days 1-5): Story 11.1 (Python)
- Day 1: TDD setup, basic function call tests (Red phase)
- Day 2: Implement basic + method calls (Green phase)
- Day 3: Alias resolution implementation ⭐⭐⭐⭐⭐
- Day 4: Decorator + project filtering
- Day 5: Edge cases, refactor, all tests green

### Week 2 (Days 6-10): Story 11.2 (Java)
- Day 6: TDD setup, basic method call tests
- Day 7: Constructor + static import tests
- Day 8: Implement Java call extraction
- Day 9: Method references, edge cases
- Day 10: All Java tests passing

### Week 3 (Days 11-14): Story 11.3 (PHP)
- Day 11: TDD setup, function + method tests
- Day 12: Implement PHP call extraction
- Day 13: Namespace resolution, edge cases
- Day 14: All PHP tests passing

### Week 4 (Days 15-17): Story 11.4 (Integration)
- Day 15: JSON output, CLI integration
- Day 16: Configuration, backward compatibility
- Day 17: Performance validation, documentation

### Buffer (Days 18-20): Polish & Testing
- Day 18: Full regression testing (415 + 100 tests)
- Day 19: Documentation updates
- Day 20: Code review, merge to develop

---

## 📚 References

### Dependencies
- **Epic 10 (Inheritance)**: Import data for alias resolution, namespace context
- **tree-sitter**: AST parsing for all languages
- **Existing parser.py**: Symbol extraction patterns

### Related Documentation
- `docs/planning/epic10-part3.md`: Inheritance extraction (reference)
- `src/codeindex/parser.py`: Symbol extraction implementation
- `CLAUDE.md`: Design philosophy, TDD workflow
- `CHANGELOG.md`: Version history

### External Resources
- tree-sitter Python: https://github.com/tree-sitter/tree-sitter-python
- tree-sitter Java: https://github.com/tree-sitter/tree-sitter-java
- tree-sitter PHP: https://github.com/tree-sitter/tree-sitter-php

---

## ✅ Design Confirmation

This Epic 11 design has been confirmed with the following decisions:

**A. Data Structure**: ✅ Confirmed
- 5 fields: caller, callee, line_number, call_type, arguments_count
- Pragmatic simple design

**B. Alias Resolution**: ✅ Confirmed
- P0 priority in Story 11.1
- Use Epic 10 Import data

**C. Decorator Handling**: ✅ Confirmed
- Phase 1: Simple decorators only
- Phase 2: Complex decorators (deferred)

**D. Project-Internal Filtering**: ✅ Confirmed
- Namespace prefix auto-detection
- No is_internal field in Call object

**E. Time Estimate**: ✅ Confirmed
- 16-20 days (3-4 weeks)
- 4 stories with detailed breakdown

---

**Document Status**: ✅ Ready for Implementation
**Next Step**: Story 11.1 TDD Development (Python Call Extraction)
**Created**: 2026-02-06
**Last Updated**: 2026-02-06
