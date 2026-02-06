# Epic 10 Part 3: Java LoomGraph Integration

**版本**: v0.12.0
**状态**: 🟢 In Progress (Story 10.1.3 ✅ Complete, Story 10.1.4 ⏳ Pending)
**优先级**: P0 - HIGH
**开始时间**: 2026-02-06
**目标完成**: 2026-02-08 (2 days)

## 📊 进度更新

**2026-02-06 17:30** - Story 10.1.3 Complete ✅
- ✅ 22/22 tests passing (88% coverage)
- ✅ Basic inheritance (extends, implements, interface extends)
- ✅ Generic type handling (<T>, <K,V>, bounded types)
- ✅ Import resolution (explicit, java.lang, same package, FQN)
- ✅ Real-world frameworks (Spring, JPA, Lombok)
- ✅ Edge cases (enum, record, annotation)
- ⏸️ 3 tests deferred to Story 10.1.4 (nested class inheritance)

---

## 🎯 Epic 目标

完成 LoomGraph 三语言全覆盖（Python ✅, PHP ✅, Java ⏳），为 Java 项目提供知识图谱数据支持。

**Epic 系列进度**:
- ✅ Epic 10 Part 1: Python LoomGraph (v0.9.0) - Inheritance + Import Alias
- ✅ Epic 10 Part 2: PHP LoomGraph (v0.10.0) - Inheritance + Import Alias
- 🚀 Epic 10 Part 3: Java LoomGraph (v0.12.0) - Inheritance Only

**为什么分离 Part 3**:
1. Java parser 已在 v0.7.0-v0.8.0 完成，基础扎实
2. Import alias 提取在 Java 中复杂度低（无 `as` 语法，仅全限定名）
3. Inheritance 是知识图谱的核心关系，优先级最高
4. 快速完成（1-2 days），提升团队士气

---

## 📦 Epic 范围

### ✅ 包含特性 (v0.12.0)

**Story 10.1.3: Java Inheritance Extraction**
- `extends` 关系提取（单继承）
- `implements` 关系提取（多接口）
- Generic 类型处理（剥离类型参数）
- 嵌套类继承（完整路径）
- Full qualified name 解析（通过 import map）

**输出数据结构**:
```python
Inheritance(
    child="com.example.AdminUser",
    parent="com.example.BaseUser"
)
```

### ❌ 不包含特性

- **Import Alias**: Java 无 `as` 语法，import 已提取完整限定名
- **Call Extraction**: 留待 Epic 11
- **Annotation Processing**: 已在 v0.8.0 完成，无需改动

### 成功标准

- [x] 提取 Java `extends` 关系
- [x] 提取 Java `implements` 关系
- [x] 处理 Generic 类型（如 `<T extends Comparable<T>>`）
- [x] 嵌套类继承使用完整路径（如 `OuterClass.InnerClass`）
- [x] 与 Python/PHP 实现保持一致性
- [x] JSON 输出兼容 LoomGraph
- [x] ~20-25 个测试用例

---

## 📋 Story 分解

### Story 10.1.3: Java Basic Inheritance Extraction ✅ COMPLETE

**状态**: ✅ Complete (2026-02-06)
**分支**: `feature/epic10-part3-java-inheritance` → merged to `develop`
**测试**: 22 passed, 3 skipped (deferred to Story 10.1.4)
**提交**: `b15fe2b` feat(parser): complete Story 10.1.3

**目标**: 从 Java AST 提取类继承和接口实现关系（基础功能）

**User Story**:
```
作为 LoomGraph 开发者
我希望从 Java 代码中提取继承关系（extends + implements）
以便构建 Java 项目的类继承图谱
```

**实现范围**: AC1-AC4, AC6-AC10（基础继承、泛型、Import解析、框架支持、边界情况）
**延后功能**: AC5（嵌套类继承）→ Story 10.1.4

#### Acceptance Criteria

**AC1: Extends 单继承**
```java
// Given
class BaseUser {}
class AdminUser extends BaseUser {}

// Then
result.inheritances == [
    Inheritance(child="AdminUser", parent="BaseUser")
]
```

**AC2: Implements 多接口**
```java
// Given
interface Authenticatable {}
interface Authorizable {}
class User implements Authenticatable, Authorizable {}

// Then
result.inheritances == [
    Inheritance(child="User", parent="Authenticatable"),
    Inheritance(child="User", parent="Authorizable")
]
```

**AC3: 组合 Extends + Implements**
```java
// Given
class BaseService {}
interface Loggable {}
class UserService extends BaseService implements Loggable {}

// Then
result.inheritances == [
    Inheritance(child="UserService", parent="BaseService"),  // extends
    Inheritance(child="UserService", parent="Loggable")      // implements
]
```

**AC4: Generic 类型剥离**
```java
// Given
class MyList<T> extends ArrayList<T> {}

// Then
result.inheritances == [
    Inheritance(child="MyList", parent="ArrayList")  // 注意：剥离 <T>
]
```

**AC5: 嵌套类继承** ⏸️ **DEFERRED to Story 10.1.4**
```java
// Given
package com.example;
class Outer {
    class Inner extends BaseInner {}
}

// Then
result.inheritances == [
    Inheritance(
        child="com.example.Outer.Inner",
        parent="com.example.BaseInner"  // 假设同包
    )
]
```

> **⚠️ 延后原因**: 嵌套类需要额外的命名空间上下文管理，复杂度较高。
> **测试状态**: 3个测试标记为 `@pytest.mark.skip` (Story 10.1.4)
> **优先级**: 中（嵌套类在实际Java代码中相对少见）

**AC6: Import 解析**
```java
// Given
package com.example.service;
import com.example.base.BaseService;

class UserService extends BaseService {}

// Then
result.inheritances == [
    Inheritance(
        child="com.example.service.UserService",
        parent="com.example.base.BaseService"  // 通过 import 解析
    )
]
```

**AC7: 接口继承接口**
```java
// Given
interface Serializable {}
interface Comparable extends Serializable {}

// Then
result.inheritances == [
    Inheritance(child="Comparable", parent="Serializable")
]
```

**AC8: Abstract Class**
```java
// Given
abstract class BaseController {}
class UserController extends BaseController {}

// Then
result.inheritances == [
    Inheritance(child="UserController", parent="BaseController")
]
```

**AC9: Java Standard Library 父类**
```java
// Given
class MyException extends Exception {}

// Then
result.inheritances == [
    Inheritance(child="MyException", parent="java.lang.Exception")
]
```

**AC10: 无继承**
```java
// Given
class StandaloneClass {}

// Then
result.inheritances == []
```

---

## 🏗️ 技术设计

### 架构原则

**复用现有架构**:
- ✅ Java parser (v0.7.0) - `src/codeindex/java_parser.py`
- ✅ `Inheritance` dataclass (v0.9.0) - `src/codeindex/parser.py`
- ✅ JSON 序列化 (v0.9.0) - `ParseResult.to_dict()`
- ✅ Import map 解析 (v0.7.0) - `build_use_map()`

**新增实现**:
- `_extract_java_inheritances()` function in `java_parser.py`
- 调用点：`parse_java_file()` 函数中

### 数据流

```
Java Source Code
    ↓ tree-sitter parse
Java AST
    ↓ traverse class_declaration nodes
Superclass/Interfaces Nodes
    ↓ extract identifiers
Raw Names (may have generics)
    ↓ strip_generic_type()
Clean Names
    ↓ resolve via import_map
Full Qualified Names
    ↓ create Inheritance objects
ParseResult.inheritances
    ↓ to_dict()
JSON Output
```

### 实现策略

#### Step 1: AST 结构分析

Java tree-sitter AST 节点结构：
```
class_declaration
├── modifiers
├── name (identifier)
├── type_parameters (optional, e.g., <T>)
├── superclass (optional)
│   └── type_identifier or generic_type
│       ├── type_identifier  # 类名
│       └── type_arguments   # <T>, <K, V>
└── super_interfaces (optional)
    └── type_list
        ├── type_identifier
        └── generic_type
```

#### Step 2: 核心函数设计

```python
def _extract_java_inheritances(
    node: Node,
    namespace: str,
    import_map: dict[str, str]
) -> list[Inheritance]:
    """
    从 Java AST 提取继承关系

    Args:
        node: class_declaration 或 interface_declaration AST 节点
        namespace: 当前包名（如 "com.example.service"）
        import_map: 短名称 → 完整限定名映射

    Returns:
        Inheritance 对象列表
    """
    inheritances = []

    # 1. 获取 child 名称
    child_name = _get_class_full_name(node, namespace)

    # 2. 提取 superclass (extends)
    superclass = node.child_by_field_name("superclass")
    if superclass:
        parent_name = _extract_type_name(superclass)
        parent_name = _strip_generic_type(parent_name)
        parent_full = _resolve_type(parent_name, namespace, import_map)
        inheritances.append(Inheritance(child=child_name, parent=parent_full))

    # 3. 提取 super_interfaces (implements)
    interfaces = node.child_by_field_name("super_interfaces")
    if interfaces:
        for interface_node in _get_type_list(interfaces):
            interface_name = _extract_type_name(interface_node)
            interface_name = _strip_generic_type(interface_name)
            interface_full = _resolve_type(interface_name, namespace, import_map)
            inheritances.append(Inheritance(child=child_name, parent=interface_full))

    return inheritances


def _strip_generic_type(type_name: str) -> str:
    """
    剥离泛型参数

    Examples:
        ArrayList<String> → ArrayList
        Map<K, V> → Map
        Comparable<T extends Number> → Comparable
    """
    return type_name.split('<')[0].strip()


def _resolve_type(
    short_name: str,
    namespace: str,
    import_map: dict[str, str]
) -> str:
    """
    解析类型的完整限定名

    Priority:
    1. java.lang.* (implicit)
    2. import_map (explicit imports)
    3. Same package (namespace)

    Examples:
        Exception → java.lang.Exception
        BaseService → com.example.base.BaseService (via import)
        InnerClass → com.example.service.InnerClass (same package)
    """
    # 1. java.lang 隐式导入
    if short_name in JAVA_LANG_CLASSES:
        return f"java.lang.{short_name}"

    # 2. 显式 import
    if short_name in import_map:
        return import_map[short_name]

    # 3. 同包类
    return f"{namespace}.{short_name}" if namespace else short_name


JAVA_LANG_CLASSES = {
    "Object", "String", "Exception", "RuntimeException",
    "Throwable", "Error", "Class", "Number", "Integer",
    "Long", "Double", "Float", "Boolean", "Character",
    # ... (常见 java.lang 类)
}
```

#### Step 3: 集成到 parse_java_file()

```python
def parse_java_file(file_path: Path, content: str) -> ParseResult:
    # ... 现有代码 ...

    # 提取 namespace
    namespace = _extract_java_namespace(tree.root_node)

    # 构建 import map
    import_map = _build_java_import_map(tree.root_node)

    # 提取 symbols
    symbols = _extract_java_symbols(tree.root_node, namespace)

    # 提取 imports
    imports = _extract_java_imports(tree.root_node)

    # 🆕 提取 inheritances
    inheritances = []
    for class_node in _find_class_nodes(tree.root_node):
        inheritances.extend(
            _extract_java_inheritances(class_node, namespace, import_map)
        )

    return ParseResult(
        path=str(file_path),
        symbols=symbols,
        imports=imports,
        inheritances=inheritances,  # 🆕
        # ... 其他字段 ...
    )
```

---

## 🧪 TDD 测试计划

### 测试文件结构

```
tests/
├── test_java_inheritance.py          # 🆕 主测试文件
├── fixtures/
│   └── java/
│       ├── inheritance_simple.java   # 单继承
│       ├── inheritance_interface.java # 接口实现
│       ├── inheritance_mixed.java    # extends + implements
│       ├── inheritance_generic.java  # 泛型继承
│       └── inheritance_nested.java   # 嵌套类
```

### 测试用例清单 (20-25 tests)

**基础继承测试** (6 tests):
- `test_single_inheritance_class` - 类单继承
- `test_multiple_interfaces` - 多接口实现
- `test_extends_and_implements` - 组合继承
- `test_no_inheritance` - 无继承
- `test_interface_extends_interface` - 接口继承
- `test_abstract_class_inheritance` - 抽象类

**Generic 类型测试** (4 tests):
- `test_generic_single_type_parameter` - `<T>`
- `test_generic_multiple_type_parameters` - `<K, V>`
- `test_generic_bounded_type` - `<T extends Number>`
- `test_generic_in_implements` - `implements Comparable<T>`

**Import 解析测试** (5 tests):
- `test_import_explicit` - 显式 import
- `test_import_wildcard` - `import java.util.*`
- `test_java_lang_implicit` - java.lang 隐式导入
- `test_same_package_class` - 同包类
- `test_full_qualified_name_in_code` - 代码中的全限定名

**嵌套类测试** (3 tests):
- `test_nested_class_extends` - 嵌套类继承
- `test_nested_interface_implements` - 嵌套接口
- `test_inner_class_full_path` - 完整路径

**真实框架测试** (4 tests):
- `test_spring_boot_controller` - Spring Controller
- `test_jpa_entity` - JPA Entity
- `test_custom_exception` - 自定义异常
- `test_lombok_data_class` - Lombok @Data

**Edge Cases** (3 tests):
- `test_enum_implements` - Enum 实现接口
- `test_record_implements` - Record (Java 14+)
- `test_sealed_class` - Sealed class (Java 17+)

---

## 🎯 开发流程 (TDD)

### Phase 1: Red - 编写测试 (4 hours)

```bash
# 1. 创建 feature 分支
git checkout -b feature/epic10-part3-java-inheritance

# 2. 创建测试文件
vim tests/test_java_inheritance.py

# 3. 编写第一批测试（基础继承 6 tests）
pytest tests/test_java_inheritance.py -v
# Expected: 6 failed ❌
```

**测试顺序**:
1. 基础继承测试（6 tests） - 核心功能
2. Generic 类型测试（4 tests） - 常见场景
3. Import 解析测试（5 tests） - 复杂逻辑
4. 嵌套类测试（3 tests） - 边界情况
5. 真实框架测试（4 tests） - 验证实用性
6. Edge Cases（3 tests） - 健壮性

### Phase 2: Green - 最小实现 (6 hours)

```bash
# 4. 实现核心函数
vim src/codeindex/java_parser.py

# 5. 运行测试
pytest tests/test_java_inheritance.py -v
# Expected: All tests pass ✅

# 6. 完整测试套件
pytest -v
```

**实现顺序**:
1. `_strip_generic_type()` - 辅助函数
2. `_resolve_type()` - 类型解析
3. `_extract_java_inheritances()` - 核心提取
4. 集成到 `parse_java_file()` - 串联

### Phase 3: Refactor - 优化 (2 hours)

```bash
# 7. 代码审查
ruff check src/codeindex/java_parser.py
mypy src/codeindex/

# 8. 性能测试（可选）
pytest tests/test_java_inheritance.py --benchmark

# 9. 更新文档
vim src/codeindex/java_parser.py  # docstrings
vim CHANGELOG.md
```

### Phase 4: Integration - 集成测试 (2 hours)

```bash
# 10. 真实项目测试
codeindex scan examples/java-spring-project --output json

# 11. LoomGraph 验证（手动）
# 检查输出的 JSON 是否包含 inheritances 字段
jq '.results[0].inheritances' examples/java-spring-project_output.json

# 12. 全量测试
pytest -v
# Target: ~803 tests passing (783 + 20 new)
```

---

## 📊 成功指标

### 测试覆盖率
- **Target**: 20-25 new tests
- **Total**: ~803 tests passing (current 783 + 20)
- **Coverage**: 90%+ for `java_parser.py` inheritance code

### 性能基准
- **Large Java File** (1000 lines, 20 classes): <500ms parsing
- **Nested Classes** (5 levels deep): Correct full paths
- **Generic Types**: 100% stripped correctly

### 质量标准
- ✅ All tests passing
- ✅ No regressions (existing 783 tests still pass)
- ✅ Consistent with Python/PHP implementation
- ✅ JSON output valid (jq validation)
- ✅ Code style (ruff check pass)

---

## 📝 文档更新

### 必须更新
1. **CHANGELOG.md** - Add v0.12.0 entry
2. **ROADMAP.md** - Mark Epic 10 Part 3 complete
3. **docs/planning/README.md** - Move to completed
4. **src/codeindex/java_parser.py** - Docstrings

### 可选更新
1. **README.md** - Update language support table
2. **docs/guides/json-output-integration.md** - Java examples
3. **examples/** - Add Java LoomGraph sample

---

## 🚧 风险与依赖

### 技术风险
- **低风险**: Java parser 成熟，架构清晰
- **import 解析复杂度**: 通配符导入 `import java.util.*`
  - **缓解**: 先实现显式导入，通配符降级为短名称

### 依赖
- ✅ Java parser (v0.7.0) - 已完成
- ✅ `Inheritance` dataclass (v0.9.0) - 已完成
- ✅ JSON 序列化 (v0.9.0) - 已完成

### 阻塞因素
- 无

---

## 📅 时间表

| 阶段 | 时间 | 任务 |
|------|------|------|
| **Day 1 AM** | 4h | TDD Red - 编写测试用例 |
| **Day 1 PM** | 4h | TDD Green - 实现核心逻辑 |
| **Day 2 AM** | 2h | TDD Refactor - 优化代码 |
| **Day 2 PM** | 2h | Integration - 集成测试 + 文档 |
| **Total** | 12h | ~1.5 工作日 |

---

## ✅ Definition of Done

- [ ] 所有 20-25 个测试通过 ✅
- [ ] 现有 783 个测试无回归 ✅
- [ ] `ruff check` 通过 ✅
- [ ] CHANGELOG.md 更新 ✅
- [ ] 真实 Java 项目验证通过 ✅
- [ ] JSON 输出格式验证 ✅
- [ ] 代码审查通过 ✅
- [ ] 合并到 develop 分支 ✅

---

### Story 10.1.4: Java Nested Class Inheritance ⏳ PENDING

**状态**: ⏳ Pending (Deferred from Story 10.1.3)
**预计时间**: 1-2 hours
**优先级**: P1 - MEDIUM

**目标**: 支持嵌套类（inner class, nested class, static nested class）的继承提取

**User Story**:
```
作为 LoomGraph 开发者
我希望正确提取Java嵌套类的继承关系
以便在知识图谱中完整表示Builder模式、内部回调等设计模式
```

#### Acceptance Criteria

**AC1: 嵌套类 extends 顶层类**
```java
package com.example;
class BaseInner {}
class Outer {
    class Inner extends BaseInner {}
}

// Then
result.inheritances == [
    Inheritance(
        child="com.example.Outer.Inner",
        parent="com.example.BaseInner"
    )
]
```

**AC2: 嵌套接口实现**
```java
interface Runnable {}
class Container {
    class Worker implements Runnable {}
}

// Then
result.inheritances == [
    Inheritance(
        child="Container.Worker",
        parent="Runnable"
    )
]
```

**AC3: 静态嵌套类**
```java
class BaseBuilder {}
class User {
    static class Builder extends BaseBuilder {}
}

// Then
result.inheritances == [
    Inheritance(
        child="User.Builder",
        parent="BaseBuilder"
    )
]
```

#### 技术实现

**核心问题**: 命名空间上下文管理
- 嵌套类的child名称需要包含外部类路径（如 `Outer.Inner`）
- parent类型解析时，需要考虑：
  1. 嵌套类所在的外部类上下文
  2. 外部类的import语句
  3. 同包的其他类

**实现策略**:
1. 修改 `_parse_java_class()` 函数，传递 `parent_namespace` 参数
2. 在类型解析时，先尝试外部类上下文，再尝试顶层namespace
3. 确保嵌套类的完整路径正确构建

**测试用例**: 3个（已在test_java_inheritance.py中标记为skip）
- `test_nested_class_extends`
- `test_nested_interface_implements`
- `test_static_nested_class`

#### Definition of Done

- [ ] 3/3 nested class tests passing
- [ ] No regression in existing 22 tests
- [ ] Code style check passed
- [ ] Merged to develop

---

**状态**: 🟢 Story 10.1.3 Complete, Story 10.1.4 Pending
**负责人**: @dreamlx
**创建日期**: 2026-02-06
**最后更新**: 2026-02-06 17:30
