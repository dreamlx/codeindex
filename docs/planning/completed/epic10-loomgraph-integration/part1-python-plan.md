# Epic 10: LoomGraph 集成支持 (MVP)

**版本**: v0.9.0
**状态**: 🟢 Active
**优先级**: P0 - CRITICAL
**开始时间**: 2026-02-06
**目标完成**: 2026-02-13 (1 week)

---

## 🎯 Epic 目标

为 LoomGraph 项目提供数据支持，使 codeindex 的解析结果能够被 LoomGraph 消费，并注入到 LightRAG 知识图谱中。

**核心集成链路**:
```
codeindex scan /path --output json
  ↓ parse_results.json
loomgraph embed parse_results.json
  ↓ embeddings.json
loomgraph inject parse_results.json embeddings.json
  ↓ LightRAG (PostgreSQL + Apache AGE)
```

---

## 📦 MVP 范围 (v0.9.0)

### ✅ 包含特性

1. **Inheritance 提取** (Story 10.1)
   - Python: 类继承关系（单继承、多继承）
   - PHP: extends + implements
   - Java: superclass + super_interfaces
   - 输出：`Inheritance(child, parent)` 列表

2. **Import Alias 支持** (Story 10.2)
   - Python: `import X as Y`, `from X import Y as Z`
   - PHP: `use Namespace\Class as Alias`
   - Java: 导入别名支持
   - 输出：Import 新增 `alias` 字段

3. **数据结构升级** (Story 10.3)
   - 新增 `Inheritance` 数据类
   - 扩展 `Import` 数据类（添加 `alias` 字段）
   - 扩展 `ParseResult`（添加 `inheritances` 字段）
   - JSON 序列化支持

### ❌ 不包含（未来 Epic）

- **Call 提取**（复杂度高，留待 Epic 11）
  - 函数/方法调用关系
  - 调用图谱构建

**MVP 成功标准**:
- LoomGraph 能成功导入 codeindex 输出的 JSON
- Entity 注入成功（基于 symbols）
- INHERITS 关系注入成功
- IMPORTS 关系注入成功（带 alias）

---

## 📋 Stories 分解

### Story 10.1: Inheritance 提取 (3 天)

**目标**: 从 AST 提取类继承关系

#### Story 10.1.1: Python Inheritance 提取 (1 天)

**TDD 测试用例** (`tests/test_python_inheritance.py`):

```python
def test_single_inheritance():
    """测试单继承"""
    code = """
class BaseUser:
    pass

class AdminUser(BaseUser):
    pass
"""
    result = parse_file("test.py", code)
    assert len(result.inheritances) == 1
    assert result.inheritances[0].child == "AdminUser"
    assert result.inheritances[0].parent == "BaseUser"

def test_multiple_inheritance():
    """测试多继承"""
    code = """
class AdminUser(BaseUser, PermissionMixin, Loggable):
    pass
"""
    result = parse_file("test.py", code)
    assert len(result.inheritances) == 3
    parents = [i.parent for i in result.inheritances]
    assert "BaseUser" in parents
    assert "PermissionMixin" in parents
    assert "Loggable" in parents

def test_no_inheritance():
    """测试无继承"""
    code = "class User:\n    pass"
    result = parse_file("test.py", code)
    assert len(result.inheritances) == 0

def test_nested_class_inheritance():
    """测试嵌套类继承"""
    code = """
class Outer:
    class Inner(BaseInner):
        pass
"""
    result = parse_file("test.py", code)
    assert len(result.inheritances) == 1
    assert result.inheritances[0].child == "Outer.Inner"
    assert result.inheritances[0].parent == "BaseInner"

def test_generic_inheritance():
    """测试泛型继承 (Python 3.12+)"""
    code = """
class UserList[T](List[T]):
    pass
"""
    result = parse_file("test.py", code)
    assert len(result.inheritances) == 1
    assert result.inheritances[0].parent == "List"
```

**实现步骤**:
1. 在 `parser.py` 的 `_parse_python_symbols` 中添加继承提取
2. Tree-sitter 查询 `class_definition` 的 `argument_list` 节点
3. 提取 base classes 列表
4. 为每个 base class 创建 `Inheritance` 对象

**代码位置**: `src/codeindex/parser.py:_parse_python_symbols`

#### Story 10.1.2: PHP Inheritance 提取 (1 天)

**TDD 测试用例** (`tests/test_php_inheritance.py`):

```python
def test_extends():
    """测试 extends"""
    code = """<?php
class AdminUser extends BaseUser {
}
"""
    result = parse_file("test.php", code)
    assert len(result.inheritances) == 1
    assert result.inheritances[0].child == "AdminUser"
    assert result.inheritances[0].parent == "BaseUser"

def test_implements():
    """测试 implements (接口也算继承)"""
    code = """<?php
class User implements Loggable, Serializable {
}
"""
    result = parse_file("test.php", code)
    assert len(result.inheritances) == 2

def test_extends_implements():
    """测试 extends + implements"""
    code = """<?php
class AdminUser extends BaseUser implements Loggable {
}
"""
    result = parse_file("test.php", code)
    assert len(result.inheritances) == 2
    parents = [i.parent for i in result.inheritances]
    assert "BaseUser" in parents
    assert "Loggable" in parents
```

**代码位置**: `src/codeindex/parser.py:_parse_php_symbols`

#### Story 10.1.3: Java Inheritance 提取 (1 天)

**TDD 测试用例** (`tests/test_java_inheritance.py`):

```python
def test_extends():
    """测试 extends"""
    code = """
public class AdminUser extends BaseUser {
}
"""
    result = parse_file("test.java", code)
    assert len(result.inheritances) == 1
    assert result.inheritances[0].parent == "BaseUser"

def test_implements():
    """测试 implements"""
    code = """
public class User implements Serializable, Cloneable {
}
"""
    result = parse_file("test.java", code)
    assert len(result.inheritances) == 2

def test_generic_inheritance():
    """测试泛型继承"""
    code = """
public class UserList<T> extends AbstractList<T> implements List<T> {
}
"""
    result = parse_file("test.java", code)
    assert len(result.inheritances) >= 2
    parents = [i.parent for i in result.inheritances]
    assert "AbstractList" in parents
    assert "List" in parents
```

**代码位置**: `src/codeindex/parser.py:_parse_java_symbols`

---

### Story 10.2: Import Alias 支持 (2 天)

**目标**: 扩展 Import 数据类，支持 alias 字段

#### Story 10.2.1: Python Import Alias (1 天)

**TDD 测试用例** (`tests/test_python_import_alias.py`):

```python
def test_import_as():
    """测试 import X as Y"""
    code = "import numpy as np"
    result = parse_file("test.py", code)
    assert len(result.imports) == 1
    imp = result.imports[0]
    assert imp.module == "numpy"
    assert imp.is_from == False
    assert imp.alias == "np"

def test_from_import_as():
    """测试 from X import Y as Z"""
    code = "from datetime import datetime as dt"
    result = parse_file("test.py", code)
    assert len(result.imports) == 1
    imp = result.imports[0]
    assert imp.module == "datetime"
    assert imp.names == ["datetime"]
    assert imp.is_from == True
    assert imp.alias == "dt"

def test_import_no_alias():
    """测试无别名导入（向后兼容）"""
    code = "import os"
    result = parse_file("test.py", code)
    assert result.imports[0].alias is None

def test_multiple_imports_mixed():
    """测试混合导入"""
    code = """
import os
import numpy as np
from typing import Dict as DictType
"""
    result = parse_file("test.py", code)
    assert len(result.imports) == 3
    # os: no alias
    assert result.imports[0].alias is None
    # numpy as np
    assert result.imports[1].alias == "np"
    # Dict as DictType
    assert result.imports[2].alias == "DictType"
```

**实现步骤**:
1. 修改 `parser.py` 中的 `Import` 数据类
2. 在 `_parse_python_imports` 中提取 `as` 子句
3. Tree-sitter 查询 `aliased_import` 节点

**代码位置**: `src/codeindex/parser.py:_parse_python_imports`

#### Story 10.2.2: PHP/Java Import Alias (1 天)

**PHP 示例**:
```php
use App\Models\User as UserModel;
```

**Java 示例** (Note: Java 不支持 import alias，此 Story 验证并文档化):
```java
// Java 不支持导入别名，alias 字段始终为 None
import java.util.List;
```

**测试**: `tests/test_php_import_alias.py`

---

### Story 10.3: 数据结构与序列化 (1 天)

**目标**: 定义新数据类，更新 JSON 序列化

#### Story 10.3.1: 定义 Inheritance 数据类 (0.5 天)

**代码** (`src/codeindex/parser.py`):

```python
@dataclass
class Inheritance:
    """Class inheritance information.

    Represents parent-child relationships between classes/interfaces.
    Used by LoomGraph to build INHERITS relations in knowledge graph.

    Attributes:
        child: Child class name (e.g., "AdminUser")
        parent: Parent class/interface name (e.g., "BaseUser")

    Examples:
        Python: class AdminUser(BaseUser) → Inheritance("AdminUser", "BaseUser")
        PHP: class AdminUser extends BaseUser → Inheritance("AdminUser", "BaseUser")
        Java: class AdminUser extends BaseUser → Inheritance("AdminUser", "BaseUser")
    """
    child: str
    parent: str
```

**测试** (`tests/test_dataclass_structure.py`):

```python
def test_inheritance_dataclass():
    """测试 Inheritance 数据类"""
    inh = Inheritance(child="AdminUser", parent="BaseUser")
    assert inh.child == "AdminUser"
    assert inh.parent == "BaseUser"

def test_inheritance_equality():
    """测试 Inheritance 相等性"""
    inh1 = Inheritance("AdminUser", "BaseUser")
    inh2 = Inheritance("AdminUser", "BaseUser")
    assert inh1 == inh2
```

#### Story 10.3.2: 扩展 Import 数据类 (0.5 天)

**代码** (`src/codeindex/parser.py`):

```python
@dataclass
class Import:
    """Import statement information (extended for LoomGraph).

    Attributes:
        module: Module name (e.g., "numpy", "os.path")
        names: Imported names (e.g., ["join", "exists"])
        is_from: Whether it's a "from X import Y" statement
        alias: Import alias (e.g., "np" in "import numpy as np")
                Added in v0.9.0 for LoomGraph integration

    Examples:
        import numpy as np → Import("numpy", [], False, alias="np")
        from typing import Dict as DictType → Import("typing", ["Dict"], True, alias="DictType")
        import os → Import("os", [], False, alias=None)
    """
    module: str
    names: list[str]
    is_from: bool
    alias: str | None = None  # Added in v0.9.0
```

**向后兼容性**: `alias=None` 作为默认值，现有代码无需修改

#### Story 10.3.3: 更新 ParseResult (0.25 天)

**代码** (`src/codeindex/parser.py`):

```python
@dataclass
class ParseResult:
    """Result of parsing a single file (extended for LoomGraph).

    Attributes:
        path: File path
        symbols: Extracted symbols (classes, functions, methods, etc.)
        imports: Import statements
        inheritances: Class inheritance relationships (added in v0.9.0)
        module_docstring: Module-level docstring
        namespace: Namespace (PHP only)
        error: Parse error message if any
    """
    path: Path
    symbols: list[Symbol]
    imports: list[Import]
    inheritances: list[Inheritance]  # Added in v0.9.0
    module_docstring: str | None = None
    namespace: str | None = None
    error: str | None = None
```

#### Story 10.3.4: 更新 JSON 序列化 (0.25 天)

**代码** (`src/codeindex/writer.py:_serialize_to_json`):

```python
def _serialize_to_json(self, result: ParseResult) -> dict:
    """Serialize ParseResult to JSON-compatible dict."""
    return {
        "path": str(result.path),
        "symbols": [
            {
                "name": s.name,
                "kind": s.kind,
                "signature": s.signature,
                "docstring": s.docstring,
                "line_start": s.line_start,
                "line_end": s.line_end,
                "annotations": [
                    {"name": a.name, "arguments": a.arguments}
                    for a in s.annotations
                ],
            }
            for s in result.symbols
        ],
        "imports": [
            {
                "module": i.module,
                "names": i.names,
                "is_from": i.is_from,
                "alias": i.alias,  # Added in v0.9.0
            }
            for i in result.imports
        ],
        "inheritances": [  # Added in v0.9.0
            {
                "child": inh.child,
                "parent": inh.parent,
            }
            for inh in result.inheritances
        ],
        "module_docstring": result.module_docstring,
        "namespace": result.namespace,
        "error": result.error,
    }
```

**测试** (`tests/test_json_serialization.py`):

```python
def test_serialize_inheritances():
    """测试 Inheritance 序列化"""
    result = ParseResult(
        path=Path("test.py"),
        symbols=[],
        imports=[],
        inheritances=[
            Inheritance("AdminUser", "BaseUser"),
            Inheritance("AdminUser", "PermissionMixin"),
        ],
    )
    json_data = serialize_to_json(result)
    assert "inheritances" in json_data
    assert len(json_data["inheritances"]) == 2
    assert json_data["inheritances"][0]["child"] == "AdminUser"
    assert json_data["inheritances"][0]["parent"] == "BaseUser"

def test_serialize_import_with_alias():
    """测试带 alias 的 Import 序列化"""
    result = ParseResult(
        path=Path("test.py"),
        symbols=[],
        imports=[Import("numpy", [], False, alias="np")],
        inheritances=[],
    )
    json_data = serialize_to_json(result)
    assert json_data["imports"][0]["alias"] == "np"
```

---

## 🧪 测试策略

### 测试覆盖目标

- **Inheritance 提取**: 60+ tests
  - Python: 25 tests
  - PHP: 20 tests
  - Java: 15 tests

- **Import Alias**: 30+ tests
  - Python: 20 tests
  - PHP: 10 tests

- **数据结构与序列化**: 15+ tests

**总计**: 105+ new tests (目标：total 770+ passing)

### TDD 流程

每个 Story 严格遵循：

1. **Red**: 编写测试用例，运行失败 ❌
2. **Green**: 最小实现，测试通过 ✅
3. **Refactor**: 优化代码，保持测试通过 ✅

### 集成测试

**测试场景** (`tests/test_loomgraph_integration.py`):

```python
def test_loomgraph_json_format():
    """测试 LoomGraph 期望的 JSON 格式"""
    code = """
import numpy as np

class AdminUser(BaseUser):
    def login(self):
        pass
"""
    result = parse_file("test.py", code)
    json_data = serialize_to_json(result)

    # 验证必需字段
    assert "symbols" in json_data
    assert "imports" in json_data
    assert "inheritances" in json_data

    # 验证 Inheritance
    assert len(json_data["inheritances"]) == 1
    assert json_data["inheritances"][0]["child"] == "AdminUser"
    assert json_data["inheritances"][0]["parent"] == "BaseUser"

    # 验证 Import alias
    assert json_data["imports"][0]["alias"] == "np"
```

---

## 📅 实施时间表

| Story | 工作量 | 开始日期 | 完成日期 |
|-------|--------|----------|----------|
| 10.1.1: Python Inheritance | 1 天 | 2026-02-06 | 2026-02-06 |
| 10.1.2: PHP Inheritance | 1 天 | 2026-02-07 | 2026-02-07 |
| 10.1.3: Java Inheritance | 1 天 | 2026-02-08 | 2026-02-08 |
| 10.2.1: Python Import Alias | 1 天 | 2026-02-09 | 2026-02-09 |
| 10.2.2: PHP/Java Import Alias | 1 天 | 2026-02-10 | 2026-02-10 |
| 10.3: 数据结构与序列化 | 1 天 | 2026-02-11 | 2026-02-11 |
| **集成测试与文档** | 1 天 | 2026-02-12 | 2026-02-12 |
| **Buffer** | 1 天 | 2026-02-13 | 2026-02-13 |

**总工程量**: 7 天（含 buffer）

---

## 🔄 GitFlow 分支策略

```
master (v0.8.0)
  ↓
develop (基于 master)
  ↓
feature/epic10-loomgraph-integration
  ├── feature/epic10-story10.1-inheritance
  ├── feature/epic10-story10.2-import-alias
  └── feature/epic10-story10.3-datastructure
```

**分支命名规范**:
- Epic 分支: `feature/epic10-loomgraph-integration`
- Story 分支: `feature/epic10-story10.1-inheritance`

**合并策略**:
- Story → Epic branch (squash merge)
- Epic → develop (no-ff merge)
- develop → master (release merge, tag v0.9.0)

---

## 📊 成功标准

### 技术指标

- ✅ 105+ new tests passing
- ✅ 0 breaking changes (向后兼容)
- ✅ JSON 输出包含 `inheritances` 和 `alias`
- ✅ 所有语言（Python, PHP, Java）支持 Inheritance
- ✅ Python 和 PHP 支持 Import Alias

### 集成验证

- ✅ LoomGraph 能成功解析 codeindex JSON 输出
- ✅ `loomgraph inject` 命令执行成功
- ✅ Entity 和 INHERITS 关系正确注入 LightRAG
- ✅ Import 关系包含 alias 信息

### 文档完整性

- ✅ CHANGELOG.md 更新
- ✅ README.md 更新（新特性说明）
- ✅ RELEASE_NOTES_v0.9.0.md 创建
- ✅ 代码中所有 docstring 完整

---

## 🚫 不包含（未来 Epic 11）

### Call 提取 (Epic 11: Code Relationship Graph)

**原因**: 实现复杂度高，需要独立 Epic

**计划**:
- Epic 11 专门处理 Call 提取
- 分 4 个 Story：Python, PHP, Java, 性能优化
- 预计工程量：2-3 周
- 目标版本：v0.10.0

**Call 数据结构**（未来）:
```python
@dataclass
class Call:
    """Function/method call information (planned for v0.10.0)."""
    caller: str        # "UserService.login"
    callee: str        # "db.find_user"
    line: int          # 调用行号
    is_method: bool    # 是否方法调用
```

---

## 📝 相关文档

### LoomGraph 集成文档

- `LoomGraph/docs/integration/LIGHTRAG_REQUIREMENTS.md` - LightRAG API 使用
- `LoomGraph/docs/api/DATA_CONTRACT.md` - 数据映射规则
- `LoomGraph/docs/api/CLI_DESIGN.md` - CLI 命令设计

### codeindex 参考文档

- `CHANGELOG.md` - 版本历史
- `README.md` - 用户文档
- `docs/guides/configuration.md` - 配置指南
- `src/codeindex/README_AI.md` - 模块架构

---

## 🔗 GitHub Issues

- **Epic Issue**: #TBD (Create GitHub Issue for Epic 10)
- **Milestone**: v0.9.0

---

## ✅ Definition of Done

Epic 10 完成标准：

1. **代码实现**:
   - [ ] Inheritance 提取支持 Python, PHP, Java
   - [ ] Import Alias 支持 Python, PHP
   - [ ] 数据结构扩展完成（Inheritance 数据类）
   - [ ] JSON 序列化包含新字段

2. **测试通过**:
   - [ ] 105+ new tests passing
   - [ ] Total 770+ tests passing
   - [ ] 所有 Ruff lint 检查通过
   - [ ] Pre-commit hooks 通过

3. **文档更新**:
   - [ ] CHANGELOG.md v0.9.0 条目
   - [ ] RELEASE_NOTES_v0.9.0.md 完成
   - [ ] README.md 新特性说明
   - [ ] README_AI.md 更新

4. **集成验证**:
   - [ ] LoomGraph 成功导入 JSON
   - [ ] `loomgraph inject` 测试通过
   - [ ] Entity + INHERITS 关系正确

5. **发布流程**:
   - [ ] Merge to develop
   - [ ] Merge to master
   - [ ] Create tag v0.9.0
   - [ ] Push to GitHub

---

**创建时间**: 2026-02-06
**最后更新**: 2026-02-06
**负责人**: @dreamlx + Claude Opus 4.5
