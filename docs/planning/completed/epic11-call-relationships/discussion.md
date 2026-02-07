# Epic 11: Call Relationships Extraction - 详细技术讨论

**版本**: v0.13.0 (计划)
**状态**: 🔵 Design Discussion
**优先级**: P1 - HIGH
**预计时间**: 1-2 weeks
**创建日期**: 2026-02-06

---

## 📋 目录

1. [背景与动机](#背景与动机)
2. [技术调研](#技术调研)
3. [核心设计决策](#核心设计决策)
4. [数据结构设计](#数据结构设计)
5. [技术挑战分析](#技术挑战分析)
6. [Story拆分建议](#story拆分建议)
7. [风险评估](#风险评估)
8. [开放问题讨论](#开放问题讨论)

---

## 🎯 背景与动机

### Epic系列进展

**已完成**:
- ✅ Epic 10 Part 1: Python Inheritance + Import Alias (v0.9.0)
- ✅ Epic 10 Part 2: PHP Inheritance + Import Alias (v0.10.0)
- ✅ Epic 10 Part 3: Java Inheritance (v0.12.0)

**当前目标**: Epic 11 - Call Relationships

### 为什么需要Call Relationships？

**LoomGraph知识图谱的完整性**:
```
Symbol (类/函数/方法)
    ↓
Inheritance (继承关系) ✅ 已完成
    ↓
Import (导入关系) ✅ 已完成
    ↓
Call Relationships (调用关系) ⏳ 本Epic目标
```

**应用场景**:
1. **调用图生成**: 函数/方法的调用依赖关系
2. **影响分析**: 修改某个函数会影响哪些调用方
3. **死代码检测**: 找出从未被调用的函数
4. **模块耦合分析**: 识别紧密耦合的模块
5. **重构辅助**: 安全地重命名/移动函数

---

## 🔬 技术调研

### 1. 调用关系的类型

#### Python调用类型

```python
# 1. 函数调用
def process_data():
    result = calculate(10)  # 函数调用

# 2. 方法调用
class Service:
    def run(self):
        self.helper()  # 实例方法调用
        Service.static_method()  # 类方法调用

# 3. 内置函数调用
data = list(range(10))  # 内置函数

# 4. Lambda调用
func = lambda x: x * 2
result = func(5)

# 5. 装饰器调用
@decorator
def my_function():
    pass
```

**AST节点类型** (tree-sitter-python):
- `call` - 所有调用表达式
- `attribute` - 方法调用的属性访问
- `identifier` - 函数名

#### Java调用类型

```java
// 1. 方法调用
public class Service {
    public void run() {
        helper();  // 实例方法调用
        this.helper();  // 显式this
        Service.staticMethod();  // 静态方法调用
    }
}

// 2. 构造函数调用
User user = new User();  // 构造函数

// 3. 链式调用
service.getData()
       .process()
       .save();

// 4. Lambda调用
Runnable r = () -> doSomething();
r.run();

// 5. 方法引用
list.forEach(System.out::println);
```

**AST节点类型** (tree-sitter-java):
- `method_invocation` - 方法调用
- `object_creation_expression` - 构造函数
- `method_reference` - 方法引用

#### PHP调用类型

```php
// 1. 函数调用
function processData() {
    $result = calculate(10);  // 函数调用
}

// 2. 方法调用
class Service {
    public function run() {
        $this->helper();  // 实例方法
        self::staticMethod();  // 静态方法
        Service::staticMethod();  // 完整静态调用
    }
}

// 3. 动态调用
$methodName = 'getData';
$obj->$methodName();  // 动态方法调用

// 4. 命名空间调用
use App\Services\UserService;
UserService::create();
```

**AST节点类型** (tree-sitter-php):
- `function_call_expression` - 函数调用
- `member_call_expression` - 方法调用
- `scoped_call_expression` - 静态调用

---

### 2. 现有实现参考

#### Python AST (标准库)

Python的 `ast` 模块：
```python
import ast

code = """
def foo():
    bar()
"""

tree = ast.parse(code)
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        print(node.func)  # 调用的函数
```

**优点**: 完整的AST访问
**缺点**: 仅Python，我们需要统一三语言

#### tree-sitter Call Extraction

tree-sitter查询示例：
```scheme
(call
  function: (identifier) @function.name
)

(call
  function: (attribute
    object: (identifier)
    attribute: (identifier) @method.name
  )
)
```

**优点**: 统一的查询语法
**缺点**: 需要理解每种语言的AST结构

#### Sourcetrail (参考项目)

Sourcetrail是开源的代码导航工具：
- C/C++, Java, Python支持
- 调用图、引用图
- 使用LLVM/Clang for C++, Javaparser for Java

**启发**:
- 数据结构设计 (Call -> Callee映射)
- 处理复杂场景（多态、动态调用）

---

## 🧩 核心设计决策

### 决策1: 数据结构设计 📊

#### Option A: 简单Call对象

```python
@dataclass
class Call:
    caller: str          # 调用者名称
    callee: str          # 被调用者名称
    line_number: int     # 调用位置
    call_type: str       # "function" | "method" | "static" | "constructor"
```

**优点**:
- 简单直观
- 易于理解和使用
- 类似Inheritance设计

**缺点**:
- 缺少调用上下文（参数、返回值）
- 无法区分不同的调用方式

#### Option B: 丰富的CallSite对象

```python
@dataclass
class CallSite:
    caller: str                  # 调用者
    callee: str                  # 被调用者
    line_number: int             # 行号
    call_type: CallType          # 枚举类型
    is_static: bool              # 是否静态调用
    is_internal: bool            # 是否内部调用（同文件/模块）
    receiver: Optional[str]      # 接收者（方法调用时）
    arguments_count: int         # 参数数量
```

**优点**:
- 更丰富的信息
- 支持高级分析（内外部调用区分、静态分析）

**缺点**:
- 复杂度增加
- 提取难度更高

#### Option C: 两阶段设计（推荐）

**Phase 1 (MVP)**: Simple Call对象
- 只提取基本调用关系（caller → callee）
- 快速验证可行性
- 足够支持调用图生成

**Phase 2 (Enhancement)**: 扩展属性
- 添加更多元数据（call_type, is_static等）
- 优化分析能力

**推荐理由**:
- 符合敏捷开发原则
- 降低初始复杂度
- 为未来扩展留空间

---

### 决策2: 调用范围 🎯

#### 问题: 提取哪些调用？

**Option A: 所有调用**
- 包含标准库调用（`print()`, `List.add()`, `array_map()`）
- 包含外部依赖调用（Spring框架、Laravel等）

**优点**: 完整的调用图
**缺点**: 数据量巨大，噪音多

**Option B: 仅项目内调用**
- 只提取项目代码内的调用关系
- 过滤标准库和第三方库

**优点**: 数据精简，聚焦项目代码
**缺点**: 可能丢失重要的外部依赖

**Option C: 可配置过滤（推荐）**
```yaml
call_extraction:
  include_stdlib: false      # 是否包含标准库
  include_external: false    # 是否包含外部依赖
  whitelist:                 # 白名单（特殊关注的外部库）
    - "org.springframework.*"
    - "Laravel\\*"
```

**推荐理由**:
- 灵活性最高
- 适应不同使用场景
- 用户可控

---

### 决策3: 调用解析精度 🔍

#### 问题: 如何处理动态调用？

**动态调用示例**:
```python
# Python
method_name = "process"
obj.call(method_name)  # 无法静态确定调用目标

# PHP
$method = 'getData';
$obj->$method();  # 动态方法调用

# Java (反射)
Method m = obj.getClass().getMethod("run");
m.invoke(obj);  # 反射调用
```

**Option A: 跳过动态调用**
- 只提取静态可确定的调用
- 标记为 `dynamic_call` 但不记录callee

**Option B: 尽力解析**
- 简单情况尝试推断（字面量字符串）
- 复杂情况标记为 `unknown`

**Option C: 记录调用点，不解析目标（推荐）**
```python
@dataclass
class Call:
    caller: str
    callee: Optional[str]     # 可能为None
    is_dynamic: bool          # 是否动态调用
    dynamic_expr: str         # 动态表达式（用于调试）
```

**推荐理由**:
- 保留完整信息
- 标记不确定性
- 为未来高级分析预留空间

---

## 📐 数据结构设计（最终方案）

### ParseResult扩展

```python
@dataclass
class ParseResult:
    path: Path
    symbols: list[Symbol]
    imports: list[Import]
    inheritances: list[Inheritance]  # Epic 10
    calls: list[Call]                # Epic 11 NEW
    module_docstring: str
    namespace: str
    error: Optional[str]
    file_lines: int
```

### Call数据类（Phase 1 - MVP）

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Call:
    """Represents a function/method call relationship.

    Attributes:
        caller: Name of the calling function/method (e.g., "Service.run")
        callee: Name of the called function/method (e.g., "helper")
        line_number: Line number where the call occurs
        is_dynamic: Whether this is a dynamic call (cannot be statically resolved)

    Examples:
        # Python
        Call(caller="process_data", callee="calculate", line_number=5, is_dynamic=False)

        # Java
        Call(caller="UserService.create", callee="User.<init>", line_number=12, is_dynamic=False)

        # PHP
        Call(caller="Controller::index", callee="Service::getData", line_number=8, is_dynamic=False)
    """
    caller: str
    callee: Optional[str]  # None for dynamic calls
    line_number: int
    is_dynamic: bool = False
```

### JSON输出格式

```json
{
  "calls": [
    {
      "caller": "com.example.UserService.createUser",
      "callee": "com.example.User.<init>",
      "line_number": 42,
      "is_dynamic": false
    },
    {
      "caller": "process_data",
      "callee": "calculate",
      "line_number": 15,
      "is_dynamic": false
    }
  ]
}
```

---

## 🚧 技术挑战分析

### 挑战1: 调用目标解析的复杂性 ⭐⭐⭐⭐⭐

**问题**: 确定 `callee` 的完整名称

**场景1: 方法调用需要上下文**
```python
class Service:
    def run(self):
        self.helper()  # callee应该是 "Service.helper" 还是 "helper"?
```

**解决方案**:
- 在函数/方法内部时，维护当前类/模块上下文
- callee格式: `ClassName.method_name` (方法) 或 `function_name` (函数)

**场景2: 导入的函数/类**
```python
from utils import calculate

def process():
    calculate(10)  # callee应该是 "calculate" 还是 "utils.calculate"?
```

**解决方案**:
- 使用现有的import解析机制（Epic 10已实现）
- callee格式: 使用full qualified name `utils.calculate`

**场景3: 链式调用**
```java
user.getProfile()
    .getAddress()
    .getCity();
```

**解决方案**:
- 每个调用独立记录:
  - `caller.method → User.getProfile`
  - `caller.method → Profile.getAddress`
  - `caller.method → Address.getCity`

**复杂度评估**: ⭐⭐⭐⭐⭐ (最高)
**建议**: MVP阶段可以简化为短名称，Phase 2再优化

---

### 挑战2: AST遍历性能 ⭐⭐⭐

**问题**: 大文件中的调用数量可能非常多

**示例**:
- 2000行的Service类可能有100+个方法调用
- 扫描整个项目可能产生数万个Call对象

**影响**:
- 解析时间增加
- 内存占用增加
- JSON输出文件增大

**优化策略**:
1. **流式处理**: 边解析边写入（不全部缓存）
2. **采样**: 提供 `max_calls_per_file` 配置限制
3. **按需提取**: 添加 `--extract-calls` flag，默认关闭

**复杂度评估**: ⭐⭐⭐ (中等)
**建议**: MVP阶段先不优化，Phase 2根据性能测试结果优化

---

### 挑战3: 多态和继承的调用解析 ⭐⭐⭐⭐

**问题**: 无法静态确定运行时调用的实际方法

**示例**:
```java
interface Animal {
    void speak();
}

class Dog implements Animal {
    public void speak() { System.out.println("Woof"); }
}

class Cat implements Animal {
    public void speak() { System.out.println("Meow"); }
}

public void makeSound(Animal animal) {
    animal.speak();  // 调用的是Dog.speak还是Cat.speak？
}
```

**解决方案选项**:

**Option A: 记录接口/基类方法**
```python
Call(caller="makeSound", callee="Animal.speak", is_polymorphic=True)
```

**Option B: 记录所有可能的实现**
```python
calls = [
    Call(caller="makeSound", callee="Animal.speak", is_interface=True),
    Call(caller="makeSound", callee="Dog.speak", is_possible_target=True),
    Call(caller="makeSound", callee="Cat.speak", is_possible_target=True),
]
```

**Option C: 仅记录声明的类型（推荐）**
```python
Call(caller="makeSound", callee="Animal.speak")
# Phase 2可以结合inheritance信息推断可能的实现
```

**复杂度评估**: ⭐⭐⭐⭐ (高)
**建议**: Phase 1使用Option C，Phase 2结合inheritance图谱分析

---

### 挑战4: 跨语言一致性 ⭐⭐⭐⭐

**问题**: 三种语言的调用语义和AST结构差异大

**差异示例**:

| 特性 | Python | Java | PHP |
|------|--------|------|-----|
| 静态方法调用 | `Class.method()` | `Class.method()` | `Class::method()` |
| 实例方法调用 | `obj.method()` | `obj.method()` | `$obj->method()` |
| 构造函数 | `Class()` | `new Class()` | `new Class()` |
| 链式调用 | 支持 | 支持 | 支持 |
| 动态调用 | 常见 | 反射 | 非常常见 |

**解决方案**:
- 定义统一的Call数据结构（已设计）
- 每种语言实现独立的提取函数：
  - `_extract_python_calls()`
  - `_extract_java_calls()`
  - `_extract_php_calls()`
- 统一的格式化规则（callee naming convention）

**复杂度评估**: ⭐⭐⭐⭐ (高)
**建议**: 先实现一种语言（Python），验证设计，再推广到其他语言

---

## 📑 Story拆分建议

基于技术挑战分析，建议采用**语言优先**拆分策略：

### Story 11.1: Python Call Extraction (3-4 days)

**目标**: 实现Python的调用关系提取

**Scope**:
- ✅ 函数调用提取
- ✅ 方法调用提取（实例方法、类方法、静态方法）
- ✅ 内置函数调用过滤（可配置）
- ✅ 简单的callee名称解析
- ⏸️ 动态调用标记（不解析）

**Acceptance Criteria**:
- AC1: 提取函数调用 `calculate()` → `Call(caller=..., callee="calculate")`
- AC2: 提取方法调用 `self.helper()` → `Call(callee="ClassName.helper")`
- AC3: 提取类方法调用 `ClassName.method()` → `Call(callee="ClassName.method")`
- AC4: 过滤内置函数（`print`, `len`等）通过配置
- AC5: 标记动态调用 `getattr(obj, method_name)()` → `is_dynamic=True`
- AC6: JSON输出包含 `calls` 字段

**测试**:
- 25-30个测试用例
- 覆盖各种调用类型
- 边界情况（空文件、无调用、嵌套调用）

**技术实现**:
```python
def _extract_python_calls(root: Node, source_bytes: bytes, context: str) -> list[Call]:
    """Extract function/method calls from Python AST."""
    calls = []

    # 遍历AST，查找call节点
    for node in traverse(root):
        if node.type == "call":
            callee = _resolve_callee(node, source_bytes)
            calls.append(Call(
                caller=context,
                callee=callee,
                line_number=node.start_point[0] + 1,
                is_dynamic=_is_dynamic_call(node)
            ))

    return calls
```

---

### Story 11.2: Java Call Extraction (4-5 days)

**目标**: 实现Java的调用关系提取

**Scope**:
- ✅ 方法调用提取（instance, static）
- ✅ 构造函数调用提取
- ✅ 链式调用提取
- ⏸️ 方法引用提取（简化处理）
- ⏸️ Lambda调用提取（标记但不详细解析）

**Acceptance Criteria**:
- AC1: 提取实例方法调用 `obj.method()` → `Call(callee="ClassName.method")`
- AC2: 提取静态方法调用 `ClassName.method()` → `Call(callee="ClassName.method")`
- AC3: 提取构造函数调用 `new User()` → `Call(callee="User.<init>")`
- AC4: 提取链式调用每一步
- AC5: 使用import map解析完整限定名
- AC6: 标记多态调用（接口/抽象类方法）

**测试**:
- 30-35个测试用例
- Spring框架场景（@Autowired调用）
- Builder模式（链式调用）

**技术挑战**:
- Java的方法调用需要结合import map解析
- 泛型方法调用的类型参数处理
- 内部类方法调用的上下文管理

---

### Story 11.3: PHP Call Extraction (3-4 days)

**目标**: 实现PHP的调用关系提取

**Scope**:
- ✅ 函数调用提取
- ✅ 方法调用提取（`$this->`, `self::`, `static::`, `ClassName::`）
- ✅ 命名空间调用解析
- ⏸️ 动态调用标记（`$obj->$method()`）

**Acceptance Criteria**:
- AC1: 提取函数调用 `calculate()` → `Call(callee="calculate")`
- AC2: 提取实例方法调用 `$this->helper()` → `Call(callee="ClassName::helper")`
- AC3: 提取静态方法调用 `self::method()` → `Call(callee="ClassName::method")`
- AC4: 解析命名空间调用 `UserService::create()` → `Call(callee="App\\Services\\UserService::create")`
- AC5: 标记动态调用 `$obj->$method()` → `is_dynamic=True`

**测试**:
- 25-30个测试用例
- Laravel框架场景（Eloquent调用）
- Trait方法调用

---

### Story 11.4: Integration & Optimization (2-3 days)

**目标**: 集成测试、性能优化、文档完善

**Scope**:
- ✅ 跨语言一致性验证
- ✅ 性能测试和优化
- ✅ JSON输出格式验证
- ✅ LoomGraph集成测试
- ✅ 文档和示例

**Tasks**:
1. 跨语言测试套件（对比Python/Java/PHP输出格式一致性）
2. 性能基准测试（大项目扫描时间）
3. JSON schema定义
4. 用户文档和示例
5. CLI参数优化（`--extract-calls`, `--include-stdlib`等）

---

## ⏱️ 时间估算

| Story | 预计时间 | 测试数 | 复杂度 |
|-------|----------|--------|--------|
| 11.1 Python | 3-4 days | 25-30 | ⭐⭐⭐ |
| 11.2 Java | 4-5 days | 30-35 | ⭐⭐⭐⭐ |
| 11.3 PHP | 3-4 days | 25-30 | ⭐⭐⭐ |
| 11.4 Integration | 2-3 days | 10-15 | ⭐⭐ |
| **Total** | **12-16 days** | **90-110** | ⭐⭐⭐⭐ |

**风险缓冲**: +20% → **15-19 days** (3-4 weeks)

---

## ⚠️ 风险评估

### 高风险项 🔴

1. **调用目标解析复杂度**
   - 风险: callee名称解析可能比预期复杂
   - 缓解: MVP阶段使用简化的短名称，Phase 2优化

2. **性能问题**
   - 风险: 大项目中调用关系数量爆炸
   - 缓解: 添加采样、限制、流式处理

3. **跨语言一致性**
   - 风险: 三种语言差异导致数据格式不一致
   - 缓解: 先实现一种语言验证设计，再推广

### 中风险项 🟡

1. **动态调用处理**
   - 风险: 无法准确捕获动态调用目标
   - 缓解: 标记为 `is_dynamic=True`，Phase 2改进

2. **多态调用**
   - 风险: 无法确定运行时实际调用目标
   - 缓解: 记录声明类型，Phase 2结合inheritance分析

### 低风险项 🟢

1. **AST遍历**
   - tree-sitter已经成熟，风险低

2. **数据结构设计**
   - 简单的Call对象，风险低

---

## 💬 开放问题讨论

### 问题1: 是否需要区分内部/外部调用？

**背景**:
- 内部调用: 同一模块/包内的调用
- 外部调用: 跨模块/包的调用

**Option A: 添加 `is_internal` 字段**
```python
@dataclass
class Call:
    caller: str
    callee: Optional[str]
    line_number: int
    is_dynamic: bool
    is_internal: bool  # NEW
```

**Option B: 通过callee名称判断**
- 用户自行通过callee的namespace判断

**你的意见？**

---

### 问题2: 是否支持参数数量/类型提取？

**背景**:
- 调用时的参数信息可以帮助更精确的分析

**Option A: 添加 `arguments_count`**
```python
@dataclass
class Call:
    # ...
    arguments_count: int
```

**Option B: Phase 1跳过，Phase 2再添加**

**你的意见？**

---

### 问题3: 如何处理构造函数调用？

**Java**: `new User()` → `Call(callee="User.<init>")`
**Python**: `User()` → `Call(callee="User.__init__")` or `Call(callee="User")`?
**PHP**: `new User()` → `Call(callee="User::__construct")`

**统一命名约定**:
- Option A: 使用语言原生约定（`<init>`, `__init__`, `__construct`）
- Option B: 统一使用 `<constructor>` 标记

**你的意见？**

---

### 问题4: 是否需要标记调用类型？

```python
class CallType(Enum):
    FUNCTION = "function"
    INSTANCE_METHOD = "instance_method"
    STATIC_METHOD = "static_method"
    CONSTRUCTOR = "constructor"
    DYNAMIC = "dynamic"
```

**Option A**: 添加 `call_type: CallType` 字段
**Option B**: 通过命名约定推断（`ClassName.method` = method, `function_name` = function）

**你的意见？**

---

## 📚 参考资料

### 学术论文
- "Extracting Call Graphs from Java Source Code" (IEEE)
- "Dynamic Call Graph Construction in Interpreted Languages"

### 开源项目
- **Sourcetrail**: https://github.com/CoatiSoftware/Sourcetrail
- **javaparser**: https://github.com/javaparser/javaparser
- **ast-grep**: https://github.com/ast-grep/ast-grep

### tree-sitter文档
- Query syntax: https://tree-sitter.github.io/tree-sitter/using-parsers#pattern-matching-with-queries
- Python grammar: https://github.com/tree-sitter/tree-sitter-python
- Java grammar: https://github.com/tree-sitter/tree-sitter-java

---

## 🎯 下一步行动

1. **讨论开放问题** (优先级: HIGH)
   - 确定数据结构最终设计
   - 决定MVP范围

2. **创建Epic 11设计文档** (基于讨论结果)
   - 确定Story拆分
   - 编写详细的AC

3. **原型实现** (可选)
   - Python call extraction快速原型
   - 验证技术可行性

4. **开始Story 11.1** (Python Call Extraction)
   - TDD开发流程
   - 预计3-4天完成

---

**准备讨论！** 🚀

请分享你对以下方面的想法：
1. 数据结构设计（Simple vs Rich Call对象）
2. 调用范围（所有 vs 项目内 vs 可配置）
3. 开放问题的答案
4. Story拆分是否合理
5. 任何其他关注点或建议
