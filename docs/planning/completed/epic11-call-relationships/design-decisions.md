# Epic 11: Call Relationships - 设计决策与分析

**日期**: 2026-02-06
**状态**: 🟢 设计确认阶段
**基于**: 利益相关方反馈 + 技术分析

---

## 📋 利益相关方反馈总结

### 1. 数据结构设计
**倾向**: Simple Call对象 (MVP Phase 1)

### 2. 调用范围
**倾向**: 仅项目内调用

### 3. 开放问题答案

| 问题 | 倾向选择 | 理由 |
|------|----------|------|
| **is_internal字段** | ❌ 不需要 (MVP) | - |
| **参数数量** | ✅ 需要 (MVP) | - |
| **构造函数命名** | Option A (语言原生) | - |
| **call_type枚举** | ✅ 需要 (5种类型) | 有助于可视化时使用不同连线样式 |

**call_type建议**:
- `FUNCTION`
- `METHOD`
- `STATIC_METHOD`
- `CONSTRUCTOR`
- `DYNAMIC`

### 4. Story拆分
**倾向**: ✅ 同意语言优先策略

### 5. 技术挑战补遗

**重要发现1 - Alias处理** ⚠️:
```python
# Python示例
import pandas as pd
pd.read_csv()  # callee应该是 "pandas.read_csv" 而不是 "pd.read_csv"
```
**结论**: 必须引用Epic 10的import alias解析结果

**重要发现2 - 隐式调用（装饰器）**:
```python
@decorator
def my_function():
    pass
# 这本质上是调用 decorator(my_function)
```
**建议**: 包含在calls中

---

## 🤔 深度分析与专业建议

### 分析1: 数据结构设计的内部矛盾

**观察到的矛盾**:
- 选择了 "Simple Call对象" (最小化设计)
- 但同时要求添加 `arguments_count` 和 `call_type` (扩展字段)

**矛盾点**:
1. `arguments_count` 增加提取复杂度
2. `call_type` 枚举需要类型判断逻辑
3. 这些与"Simple"理念有冲突

**我的建议** 🎯:

采用**务实的Simple设计** - 保留核心简洁性，但添加高价值字段：

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CallType(Enum):
    """调用类型枚举"""
    FUNCTION = "function"           # 函数调用: calculate()
    METHOD = "method"               # 实例方法: obj.method()
    STATIC_METHOD = "static_method" # 静态方法: Class.method()
    CONSTRUCTOR = "constructor"     # 构造函数: new Class()
    DYNAMIC = "dynamic"             # 动态调用: getattr(obj, name)()

@dataclass
class Call:
    """函数/方法调用关系 (Epic 11 MVP)

    Design Principles:
    - Simple: 核心字段少，易于理解
    - Practical: 包含可视化和分析必需的信息
    - Extensible: 为Phase 2预留扩展空间

    Examples:
        # Python
        Call(
            caller="process_data",
            callee="pandas.read_csv",
            line_number=15,
            call_type=CallType.FUNCTION,
            arguments_count=2
        )

        # Java
        Call(
            caller="UserService.createUser",
            callee="User.<init>",
            line_number=42,
            call_type=CallType.CONSTRUCTOR,
            arguments_count=3
        )
    """
    caller: str                      # 调用者的完整名称
    callee: Optional[str]            # 被调用者的完整名称 (dynamic时可为None)
    line_number: int                 # 调用发生的行号
    call_type: CallType              # 调用类型
    arguments_count: Optional[int]   # 参数数量 (尽力而为，无法确定时为None)

    # 便利属性 (冗余但提高可用性)
    @property
    def is_dynamic(self) -> bool:
        """是否为动态调用"""
        return self.call_type == CallType.DYNAMIC

# JSON序列化支持
def call_to_dict(call: Call) -> dict:
    """将Call对象序列化为字典"""
    return {
        "caller": call.caller,
        "callee": call.callee,
        "line_number": call.line_number,
        "call_type": call.call_type.value,
        "arguments_count": call.arguments_count,
    }
```

**理由**:
1. ✅ **保持Simple**: 只有5个核心字段
2. ✅ **支持可视化**: `call_type` 提供连线样式区分
3. ✅ **尽力而为**: `arguments_count` 设为Optional，能提取就提取，不能则为None
4. ✅ **易于实现**: 所有信息都可以从AST直接获取，无需复杂推理
5. ✅ **向后兼容**: 为Phase 2扩展预留空间

**实现复杂度评估**:
- `call_type` 判断: ⭐⭐ (中低，基于AST节点类型即可)
- `arguments_count` 提取: ⭐⭐ (中低，遍历arguments列表即可)
- 总体复杂度增加: +15% (可接受)

---

### 分析2: "仅项目内调用"的实现机制

**问题**: 如何判断调用是否"项目内"？

**场景分析**:

```python
# Scenario 1: 标准库调用 (应该过滤)
import sys
sys.exit()  # callee = "sys.exit" → 外部，过滤

# Scenario 2: 第三方库调用 (应该过滤)
import pandas as pd
pd.read_csv()  # callee = "pandas.read_csv" → 外部，过滤

# Scenario 3: 项目内模块调用 (应该保留)
from myproject.utils import calculate
calculate()  # callee = "myproject.utils.calculate" → 项目内，保留

# Scenario 4: 同文件内调用 (应该保留)
def helper():
    pass

def main():
    helper()  # callee = "helper" → 项目内，保留
```

**实现策略**:

#### Option A: 基于namespace前缀过滤

```python
def is_project_call(callee: str, project_namespaces: list[str]) -> bool:
    """判断调用是否属于项目内

    Args:
        callee: 被调用者的完整名称
        project_namespaces: 项目的namespace列表

    Returns:
        True if project internal call

    Examples:
        >>> is_project_call("myproject.utils.calculate", ["myproject"])
        True
        >>> is_project_call("pandas.read_csv", ["myproject"])
        False
        >>> is_project_call("calculate", ["myproject"])  # 同文件内，无namespace
        True
    """
    # 无namespace的调用视为项目内（同文件调用）
    if not callee or "." not in callee:
        return True

    # 检查是否匹配项目namespace
    for ns in project_namespaces:
        if callee.startswith(ns + "."):
            return True

    return False
```

**配置示例**:
```yaml
# .codeindex.yaml
call_extraction:
  enabled: true
  project_namespaces:
    - "com.example"       # Java项目
    - "myproject"         # Python项目
    - "App\\Services"     # PHP项目 (Laravel)

  # 高级过滤选项（可选）
  include_stdlib: false   # 排除标准库
  include_external: false # 排除第三方库
```

#### Option B: 基于文件路径过滤

```python
def is_project_call(callee: str, parsed_files: set[Path]) -> bool:
    """基于已解析文件判断是否项目内调用"""
    # 如果callee定义在已解析的文件中，则为项目内
    # 需要维护全局symbol索引 (Symbol -> File映射)
    return callee in global_symbol_index
```

**优缺点对比**:

| 方案 | 优点 | 缺点 |
|------|------|------|
| Option A (namespace) | 简单、高效、可配置 | 需要用户配置namespace |
| Option B (文件路径) | 自动判断、无需配置 | 需要维护全局索引，复杂度高 |

**我的建议** 🎯:

**采用Option A (namespace前缀过滤) + 自动检测**:

1. **自动检测项目namespace** (智能默认值):
   ```python
   def detect_project_namespaces(scan_dirs: list[Path]) -> list[str]:
       """自动检测项目的主要namespace"""
       namespaces = set()
       for dir_path in scan_dirs:
           for file in dir_path.rglob("*.py"):
               result = parse_file(file)
               if result.namespace:
                   # 提取顶级namespace
                   top_ns = result.namespace.split('.')[0]
                   namespaces.add(top_ns)
       return list(namespaces)
   ```

2. **用户可覆盖配置**:
   ```yaml
   call_extraction:
     project_namespaces: auto  # 自动检测
     # 或手动指定
     # project_namespaces:
     #   - "com.example"
     #   - "myproject"
   ```

3. **过滤逻辑**:
   ```python
   # 在_extract_calls中应用过滤
   calls = []
   for call_site in all_call_sites:
       if is_project_call(call_site.callee, project_namespaces):
           calls.append(call_site)
   return calls
   ```

**理由**:
- ✅ 简单高效
- ✅ 用户体验好（自动检测 + 可覆盖）
- ✅ 实现成本低
- ✅ 符合用户"仅项目内调用"的需求

---

### 分析3: Alias处理机制 (关键技术点)

**问题重要性**: ⭐⭐⭐⭐⭐ (最高优先级)

用户指出的问题非常关键：

```python
# Epic 10已提取的import信息
Import(module="pandas", names=[], alias="pd")

# 代码中的调用
pd.read_csv("data.csv")

# 错误的提取结果 ❌
Call(caller="process_data", callee="pd.read_csv")

# 正确的提取结果 ✅
Call(caller="process_data", callee="pandas.read_csv")
```

**解决方案设计**:

#### Step 1: 复用Epic 10的Import解析

```python
# Epic 10已有的数据结构
@dataclass
class Import:
    module: str          # 原始模块名 "pandas"
    names: list[str]     # 导入的具体名称 []
    is_from: bool        # 是否from import
    alias: Optional[str] # 别名 "pd"

# Epic 10的parse_file输出
class ParseResult:
    imports: list[Import]  # 已解析的import信息
```

#### Step 2: 构建Alias映射表

```python
def build_alias_map(imports: list[Import]) -> dict[str, str]:
    """构建alias到真实名称的映射

    Args:
        imports: ParseResult中的imports列表

    Returns:
        alias -> real_name 映射

    Examples:
        >>> imports = [
        ...     Import(module="pandas", alias="pd"),
        ...     Import(module="numpy", alias="np"),
        ... ]
        >>> build_alias_map(imports)
        {'pd': 'pandas', 'np': 'numpy'}
    """
    alias_map = {}

    for imp in imports:
        if imp.alias:
            # 简单别名: import pandas as pd
            alias_map[imp.alias] = imp.module

        # from import with alias: from utils import calculate as calc
        for i, name in enumerate(imp.names):
            if imp.is_from and i < len(imp.names):
                # 处理 from X import Y as Z
                # 这需要Import结构支持per-name alias
                # 暂时简化处理
                pass

    return alias_map
```

#### Step 3: 在调用提取时应用Alias解析

```python
def _extract_calls(
    node: Node,
    source_bytes: bytes,
    caller_context: str,
    alias_map: dict[str, str]  # NEW: alias映射
) -> list[Call]:
    """提取调用关系，并解析alias"""
    calls = []

    for call_node in find_call_nodes(node):
        # 提取原始callee名称
        raw_callee = extract_callee_name(call_node, source_bytes)

        # 解析alias
        resolved_callee = resolve_alias(raw_callee, alias_map)

        calls.append(Call(
            caller=caller_context,
            callee=resolved_callee,
            line_number=call_node.start_point[0] + 1,
            call_type=determine_call_type(call_node),
            arguments_count=count_arguments(call_node)
        ))

    return calls

def resolve_alias(callee: str, alias_map: dict[str, str]) -> str:
    """解析callee中的alias

    Examples:
        >>> resolve_alias("pd.read_csv", {"pd": "pandas"})
        'pandas.read_csv'
        >>> resolve_alias("np.array", {"pd": "pandas", "np": "numpy"})
        'numpy.array'
        >>> resolve_alias("local_func", {})
        'local_func'
    """
    if not callee or "." not in callee:
        return callee

    # 提取前缀（可能是alias）
    parts = callee.split(".", 1)
    prefix = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""

    # 查找alias映射
    if prefix in alias_map:
        real_prefix = alias_map[prefix]
        return f"{real_prefix}.{suffix}" if suffix else real_prefix

    return callee
```

#### Step 4: 集成到parse_file

```python
def parse_file(file_path: Path) -> ParseResult:
    """解析文件 (Epic 11扩展)"""
    # ... 现有的解析逻辑 ...

    # Epic 10: 提取imports
    imports = _extract_imports(root, source_bytes)

    # Epic 10: 提取inheritances
    inheritances = _extract_inheritances(...)

    # Epic 11: 构建alias映射
    alias_map = build_alias_map(imports)

    # Epic 11: 提取calls (使用alias_map)
    calls = _extract_calls(
        root,
        source_bytes,
        caller_context="",
        alias_map=alias_map
    )

    return ParseResult(
        symbols=symbols,
        imports=imports,
        inheritances=inheritances,
        calls=calls,  # NEW
        ...
    )
```

**技术依赖**:
- ✅ Epic 10的Import数据结构 (已完成)
- ✅ Epic 10的import解析逻辑 (已完成)
- ⚠️ 需要确保Import.alias字段已正确提取 (验证Epic 10实现)

**实现优先级**: P0 (最高)
**实现时机**: Story 11.1 (Python) 开始就必须包含

---

### 分析4: 隐式调用（装饰器）处理

**用户建议**: 包含在calls中

**场景分析**:

```python
# Scenario 1: 简单装饰器
@decorator
def my_function():
    pass

# 等价于: my_function = decorator(my_function)
# 应该提取为: Call(caller="<module>", callee="decorator", call_type=FUNCTION)

# Scenario 2: 带参数的装饰器
@decorator(arg1, arg2)
def my_function():
    pass

# 等价于: my_function = decorator(arg1, arg2)(my_function)
# 两个调用:
#   Call(caller="<module>", callee="decorator", arguments_count=2)
#   Call(caller="<module>", callee="<decorator_result>", call_type=DYNAMIC)

# Scenario 3: 多重装饰器
@decorator1
@decorator2
def my_function():
    pass

# 等价于: my_function = decorator1(decorator2(my_function))
# 两个调用: decorator2(my_function), decorator1(...)

# Scenario 4: 类装饰器
@dataclass
class User:
    name: str

# Call(caller="<module>", callee="dataclasses.dataclass", call_type=FUNCTION)
```

**实现复杂度评估**:

| 场景 | 复杂度 | AST节点 | 实现难度 |
|------|--------|---------|----------|
| 简单装饰器 | ⭐⭐ | `decorator` | 低 |
| 带参装饰器 | ⭐⭐⭐⭐ | `decorator` + `call` | 高 |
| 多重装饰器 | ⭐⭐⭐ | 多个`decorator` | 中 |
| 类装饰器 | ⭐⭐ | `decorator` on class | 低 |

**我的建议** 🎯:

**两阶段实现**:

**Phase 1 (MVP - Story 11.1)**: 支持简单装饰器
```python
# 只处理无参装饰器
@decorator
def func():
    pass

# 提取为:
Call(
    caller="<module>",  # 或当前类名
    callee="decorator",
    line_number=装饰器所在行,
    call_type=CallType.FUNCTION,
    arguments_count=1  # 被装饰函数作为参数
)
```

**Phase 2 (Enhancement)**: 支持复杂装饰器
- 带参数装饰器
- 多重装饰器链
- 装饰器工厂模式

**理由**:
1. ✅ **MVP可行**: 简单装饰器容易实现，价值高
2. ✅ **增量扩展**: 复杂装饰器可以Phase 2添加
3. ⚠️ **复杂度管理**: 避免MVP阶段过度复杂化
4. ✅ **用户价值**: 常见装饰器（@property, @staticmethod, @dataclass）都是简单形式

**实现示例** (Python):
```python
def _extract_decorator_calls(
    node: Node,
    source_bytes: bytes,
    context: str
) -> list[Call]:
    """提取装饰器调用 (Phase 1: 简单装饰器)"""
    calls = []

    # 查找function_definition或class_definition节点
    if node.type in ("function_definition", "class_definition"):
        # 获取decorators
        for child in node.children:
            if child.type == "decorator":
                decorator_name = extract_decorator_name(child, source_bytes)

                # 只处理简单装饰器（@name形式）
                if is_simple_decorator(child):
                    calls.append(Call(
                        caller=context,
                        callee=decorator_name,
                        line_number=child.start_point[0] + 1,
                        call_type=CallType.FUNCTION,
                        arguments_count=1  # 被装饰函数
                    ))

    return calls
```

---

### 分析5: 构造函数命名约定

**用户选择**: Option A - 使用语言原生约定

**语言对比**:

| 语言 | 构造函数语法 | 原生约定 | 示例 |
|------|-------------|----------|------|
| **Java** | `new ClassName()` | `<init>` | `User.<init>` |
| **Python** | `ClassName()` | `__init__` | `User.__init__` |
| **PHP** | `new ClassName()` | `__construct` | `User::__construct` |

**我的建议** 🎯:

**同意使用语言原生约定，但需要标准化格式**:

```python
# 构造函数callee命名规则:
# Java:   "ClassName.<init>"
# Python: "ClassName.__init__"
# PHP:    "ClassName::__construct"

# 注意分隔符:
# Java/Python: "." (点号)
# PHP: "::" (双冒号)
```

**实现示例**:

```python
def format_constructor_callee(class_name: str, language: str) -> str:
    """格式化构造函数的callee名称

    Args:
        class_name: 类名（可能包含namespace）
        language: 语言类型 ("python", "java", "php")

    Returns:
        格式化的构造函数名称

    Examples:
        >>> format_constructor_callee("User", "java")
        'User.<init>'
        >>> format_constructor_callee("User", "python")
        'User.__init__'
        >>> format_constructor_callee("App\\\\User", "php")
        'App\\\\User::__construct'
    """
    if language == "java":
        return f"{class_name}.<init>"
    elif language == "python":
        return f"{class_name}.__init__"
    elif language == "php":
        return f"{class_name}::__construct"
    else:
        return f"{class_name}.<constructor>"
```

**理由**:
- ✅ **保留语言语义**: 尊重各语言的原生表示
- ✅ **开发者熟悉**: Java开发者熟悉`<init>`，Python开发者熟悉`__init__`
- ✅ **调试友好**: 清晰表明这是构造函数调用
- ✅ **LoomGraph兼容**: LoomGraph可以识别这些模式

---

## 📐 最终数据结构设计（确认版）

基于以上分析，最终设计：

### Call数据类

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CallType(Enum):
    """调用类型枚举

    用于区分不同类型的调用，支持可视化时使用不同样式。
    """
    FUNCTION = "function"           # 普通函数调用
    METHOD = "method"               # 实例方法调用
    STATIC_METHOD = "static_method" # 静态/类方法调用
    CONSTRUCTOR = "constructor"     # 构造函数调用
    DYNAMIC = "dynamic"             # 动态调用（无法静态确定目标）

@dataclass
class Call:
    """函数/方法调用关系 (Epic 11)

    Represents a function or method call in the codebase.

    Attributes:
        caller: Full name of the calling function/method
                Format: "ClassName.method_name" or "function_name"
        callee: Full name of the called function/method
                None for dynamic calls that cannot be statically resolved
                Format:
                  - Function: "function_name" or "module.function"
                  - Method: "ClassName.method_name"
                  - Constructor: "ClassName.<init>" (Java)
                                "ClassName.__init__" (Python)
                                "ClassName::__construct" (PHP)
        line_number: Line number where the call occurs
        call_type: Type of the call (FUNCTION, METHOD, etc.)
        arguments_count: Number of arguments passed to the call
                        None if cannot be determined (e.g., *args)

    Design Notes:
        - Aliases are resolved using Epic 10's import information
        - Only project-internal calls are extracted (no stdlib/external)
        - Decorators are included as FUNCTION calls (simple form only)

    Examples:
        # Python function call
        Call(
            caller="process_data",
            callee="pandas.read_csv",  # Alias "pd" resolved to "pandas"
            line_number=15,
            call_type=CallType.FUNCTION,
            arguments_count=2
        )

        # Java method call
        Call(
            caller="UserService.createUser",
            callee="UserValidator.validate",
            line_number=42,
            call_type=CallType.METHOD,
            arguments_count=1
        )

        # Python constructor call
        Call(
            caller="create_user",
            callee="User.__init__",
            line_number=23,
            call_type=CallType.CONSTRUCTOR,
            arguments_count=3
        )

        # Dynamic call
        Call(
            caller="dynamic_dispatch",
            callee=None,
            line_number=56,
            call_type=CallType.DYNAMIC,
            arguments_count=None
        )
    """
    caller: str
    callee: Optional[str]
    line_number: int
    call_type: CallType
    arguments_count: Optional[int] = None

    @property
    def is_dynamic(self) -> bool:
        """便利属性：是否为动态调用"""
        return self.call_type == CallType.DYNAMIC

    def to_dict(self) -> dict:
        """序列化为字典（JSON兼容）"""
        return {
            "caller": self.caller,
            "callee": self.callee,
            "line_number": self.line_number,
            "call_type": self.call_type.value,
            "arguments_count": self.arguments_count,
        }
```

### ParseResult扩展

```python
@dataclass
class ParseResult:
    """代码解析结果 (Epic 11扩展)"""
    path: Path
    symbols: list[Symbol]
    imports: list[Import]
    inheritances: list[Inheritance]
    calls: list[Call]              # NEW: Epic 11
    module_docstring: str
    namespace: str
    error: Optional[str]
    file_lines: int
```

### JSON输出格式

```json
{
  "path": "src/myproject/service.py",
  "namespace": "myproject.service",
  "symbols": [...],
  "imports": [...],
  "inheritances": [...],
  "calls": [
    {
      "caller": "UserService.create_user",
      "callee": "User.__init__",
      "line_number": 42,
      "call_type": "constructor",
      "arguments_count": 3
    },
    {
      "caller": "UserService.create_user",
      "callee": "UserValidator.validate",
      "line_number": 45,
      "call_type": "method",
      "arguments_count": 1
    },
    {
      "caller": "process_data",
      "callee": "pandas.read_csv",
      "line_number": 15,
      "call_type": "function",
      "arguments_count": 2
    }
  ]
}
```

---

## 🎯 配置设计

### .codeindex.yaml扩展

```yaml
# Epic 11: Call Extraction Configuration
call_extraction:
  # 是否启用调用提取
  enabled: true

  # 项目namespace配置
  project_namespaces: auto  # auto: 自动检测
  # 或手动指定:
  # project_namespaces:
  #   - "com.example"       # Java
  #   - "myproject"         # Python
  #   - "App\\Services"     # PHP

  # 高级选项
  include_decorators: true   # 是否提取装饰器调用 (Python)
  max_calls_per_file: 1000   # 单文件最大调用数限制 (防止性能问题)

  # 过滤选项
  include_stdlib: false      # 排除标准库调用
  include_external: false    # 排除第三方库调用
```

---

## 📋 修订后的Story拆分

基于最终设计，Story拆分调整：

### Story 11.1: Python Call Extraction (4-5 days)

**调整**: 增加装饰器支持，时间+1天

**Scope**:
- ✅ 函数调用提取
- ✅ 方法调用提取（实例、类、静态）
- ✅ 构造函数调用提取
- ✅ **Alias解析** (使用Epic 10 imports) ⭐ 关键
- ✅ **简单装饰器调用** (无参形式) ⭐ 新增
- ✅ `call_type` 判断
- ✅ `arguments_count` 提取（尽力而为）
- ✅ 项目内调用过滤

**Acceptance Criteria**:
- AC1: 提取函数调用，正确解析alias
- AC2: 提取方法调用，区分实例/类/静态
- AC3: 提取构造函数调用（`ClassName()`）
- AC4: 正确设置`call_type`（5种类型）
- AC5: 提取`arguments_count`（能提取时）
- AC6: 仅提取项目内调用（通过namespace过滤）
- AC7: 提取简单装饰器调用（`@decorator`）
- AC8: JSON输出格式正确

**测试**: 30-35个

---

### Story 11.2: Java Call Extraction (4-5 days)

**Scope**:
- ✅ 方法调用提取（实例、静态）
- ✅ 构造函数调用提取（`new ClassName()`）
- ✅ 链式调用提取（每一步独立记录）
- ✅ Import解析（使用Epic 10）
- ✅ `call_type` 判断
- ✅ `arguments_count` 提取
- ✅ 项目内调用过滤

**Acceptance Criteria**:
- AC1: 提取实例方法调用
- AC2: 提取静态方法调用（`ClassName.method()`）
- AC3: 提取构造函数调用（`new User()` → `User.<init>`）
- AC4: 链式调用的每一步独立提取
- AC5: 正确设置`call_type`
- AC6: 提取`arguments_count`
- AC7: 仅提取项目内调用
- AC8: JSON输出格式正确

**测试**: 30-35个

---

### Story 11.3: PHP Call Extraction (3-4 days)

**Scope**:
- ✅ 函数调用提取
- ✅ 方法调用提取（`$this->`, `self::`, `static::`, `ClassName::`）
- ✅ 构造函数调用提取（`new ClassName()`）
- ✅ Namespace解析（使用Epic 10）
- ✅ `call_type` 判断
- ✅ `arguments_count` 提取
- ✅ 项目内调用过滤

**Acceptance Criteria**:
- AC1: 提取函数调用
- AC2: 提取实例方法调用（`$this->method()`）
- AC3: 提取静态方法调用（`self::`, `ClassName::`）
- AC4: 提取构造函数调用（`new User()` → `User::__construct`）
- AC5: 正确设置`call_type`
- AC6: 提取`arguments_count`
- AC7: 仅提取项目内调用
- AC8: JSON输出格式正确

**测试**: 25-30个

---

### Story 11.4: Integration & Documentation (2-3 days)

**Scope**:
- ✅ 跨语言一致性测试
- ✅ 性能测试和优化
- ✅ 自动namespace检测实现
- ✅ CLI参数优化
- ✅ JSON schema定义
- ✅ 用户文档和示例
- ✅ LoomGraph集成验证

**测试**: 10-15个（集成测试）

---

## ⏱️ 修订后时间估算

| Story | 原估算 | 修订估算 | 变化 | 原因 |
|-------|--------|----------|------|------|
| 11.1 Python | 3-4 days | **4-5 days** | +1 | 增加装饰器+alias解析 |
| 11.2 Java | 4-5 days | **4-5 days** | 0 | 保持不变 |
| 11.3 PHP | 3-4 days | **3-4 days** | 0 | 保持不变 |
| 11.4 Integration | 2-3 days | **2-3 days** | 0 | 保持不变 |
| **Total** | 12-16 days | **13-17 days** | +1 | - |

**风险缓冲**: +20% → **16-20 days (3-4 weeks)**

---

## ✅ 最终确认清单

### 设计决策

- [x] **数据结构**: Call对象包含5个字段（caller, callee, line_number, call_type, arguments_count）
- [x] **call_type枚举**: 5种类型（FUNCTION, METHOD, STATIC_METHOD, CONSTRUCTOR, DYNAMIC）
- [x] **调用范围**: 仅项目内调用，通过namespace前缀过滤
- [x] **Alias处理**: 使用Epic 10的import信息解析alias
- [x] **装饰器**: Phase 1支持简单装饰器
- [x] **构造函数命名**: 使用语言原生约定（`<init>`, `__init__`, `__construct`）
- [x] **is_internal字段**: 不添加（通过提取过程过滤）
- [x] **arguments_count**: 添加为Optional字段，尽力而为

### 技术实现

- [x] **Alias解析机制**: build_alias_map() + resolve_alias()
- [x] **项目内过滤**: is_project_call() + 自动namespace检测
- [x] **装饰器提取**: _extract_decorator_calls() (简单形式)
- [x] **构造函数格式化**: format_constructor_callee()

### 配置设计

- [x] **call_extraction配置**: enabled, project_namespaces, include_decorators
- [x] **自动检测**: project_namespaces: auto
- [x] **过滤选项**: max_calls_per_file, include_stdlib

### Story拆分

- [x] **Story 11.1**: Python (4-5 days, 30-35 tests)
- [x] **Story 11.2**: Java (4-5 days, 30-35 tests)
- [x] **Story 11.3**: PHP (3-4 days, 25-30 tests)
- [x] **Story 11.4**: Integration (2-3 days, 10-15 tests)
- [x] **总计**: 13-17 days → 16-20 days (with buffer)

---

## 🚀 下一步行动

1. **确认设计决策** ✅ (本文档)
2. **创建Epic 11正式设计文档** (基于本文档)
3. **Story 11.1详细AC编写**
4. **Python call extraction原型验证** (可选)
5. **开始TDD开发** (Story 11.1)

---

**等待最终确认！** 🎯

如果你同意以上设计，我将立即创建正式的Epic 11设计文档并开始Story 11.1的实现。

如果还有任何疑问或需要调整的地方，请随时提出！
