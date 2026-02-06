# Epic 10 Part 2: PHP LoomGraph Integration

**版本**: v0.10.0
**状态**: 📋 Planning
**优先级**: P1
**创建日期**: 2026-02-06
**依赖**: Epic 10 Part 1 (Python) ✅

---

## 📖 Epic 概述

### 背景

Epic 10 Part 1 已完成 Python 的 LoomGraph 集成（v0.9.0）。现在扩展到 PHP，为 PHP 项目提供同样的知识图谱支持。

### 目标

为 PHP 语言实现与 Python 相同的 LoomGraph 集成功能：
- ✅ 数据结构已就绪（Inheritance, Import.alias）
- 🔄 Story 10.1.2: PHP 继承提取
- 🔄 Story 10.2.2: PHP 导入别名提取
- 🔄 集成测试

### PHP 语法特点分析

#### 1. PHP 继承语法

**单继承 (extends)**:
```php
class AdminUser extends User {
    // ...
}
// → Inheritance(child="AdminUser", parent="User")
```

**接口实现 (implements)**:
```php
class User implements Authenticatable, Loggable {
    // ...
}
// → Inheritance(child="User", parent="Authenticatable")
// → Inheritance(child="User", parent="Loggable")
```

**组合使用**:
```php
class AdminUser extends User implements Authorizable {
    // ...
}
// → Inheritance(child="AdminUser", parent="User")
// → Inheritance(child="AdminUser", parent="Authorizable")
```

**Trait 使用 (特殊情况)**:
```php
class User {
    use Timestampable, SoftDeletes;
}
// → 决策：暂不提取 trait（非继承关系，是代码复用）
```

#### 2. PHP 导入别名语法

**简单别名**:
```php
use App\Service\UserService as US;
// → Import(module="App\\Service\\UserService", names=[], is_from=True, alias="US")
```

**无别名**:
```php
use App\Model\User;
// → Import(module="App\\Model\\User", names=[], is_from=True, alias=None)
```

**组导入（Group Imports）**:
```php
use App\Repository\{UserRepository as UR, OrderRepository};
// → Import(module="App\\Repository\\UserRepository", names=[], is_from=True, alias="UR")
// → Import(module="App\\Repository\\OrderRepository", names=[], is_from=True, alias=None)
```

---

## 🎯 Stories

### Story 10.1.2: PHP 继承提取

**优先级**: P0（核心功能）

**目标**: 提取 PHP 类的 `extends` 和 `implements` 关系

**实现要点**:

1. **修改 `_parse_php_class` 函数**:
   - 当前已解析 `extends` 和 `implements`，但未创建 Inheritance 对象
   - 需要：
     - 接收 `inheritances: list[Inheritance]` 参数
     - 为每个 extends/implements 创建 Inheritance 对象
     - 处理命名空间（完整类名）

2. **修改 `parse_file` (PHP 分支)**:
   - 初始化 `inheritances: list[Inheritance] = []`
   - 传递给 `_parse_php_class`
   - 返回 ParseResult 时包含 inheritances

3. **命名空间处理**:
   ```php
   namespace App\Models;
   use App\Base\Model;

   class User extends Model {  // 完整名: App\Models\User
   }
   // → Inheritance(child="App\\Models\\User", parent="App\\Base\\Model")
   ```

**测试用例**:
- ✅ 单继承 (extends)
- ✅ 接口实现 (implements, 单个)
- ✅ 接口实现 (implements, 多个)
- ✅ 组合 (extends + implements)
- ✅ 命名空间处理
- ✅ 抽象类继承
- ✅ Final 类（不能被继承，但可以继承）
- ✅ 嵌套类（PHP 不支持，跳过）
- ✅ Trait（暂不提取，留待未来）

**验收标准**:
- [ ] 正确提取 extends 关系
- [ ] 正确提取 implements 关系（每个接口一个 Inheritance）
- [ ] 完整类名包含命名空间
- [ ] 所有测试用例通过

---

### Story 10.2.2: PHP 导入别名提取

**优先级**: P0（核心功能）

**目标**: 粒度化提取 PHP `use` 语句的别名

**当前实现问题**:

当前 `_parse_php_use` 返回：
```php
use App\Service\UserService as US;
// → Import(module="App\\Service\\UserService", names=["US"], is_from=True)
```

**问题**：`names` 字段存的是 alias，与 Python 不一致。

**期望行为（对齐 Python）**:
```php
use App\Service\UserService as US;
// → Import(module="App\\Service\\UserService", names=[], is_from=True, alias="US")
```

**实现要点**:

1. **修改 `_parse_php_use` 函数**:
   - 将 alias 从 `names` 字段移到 `alias` 字段
   - `names` 字段保持空列表（PHP use 导入整个类，不是部分成员）
   - 每个 use 语句创建一个 Import 对象

2. **组导入处理**:
   ```php
   use App\Repository\{UserRepository as UR, OrderRepository};
   // → 2 个 Import 对象
   ```

3. **与 Python 的差异**:
   - PHP: `names=[]` (导入整个类)
   - Python: `names=["specific_name"]` (可以导入特定成员)

**测试用例**:
- ✅ 简单别名 (use X as Y)
- ✅ 无别名 (use X)
- ✅ 组导入 with 别名
- ✅ 组导入 mixed (有些有别名，有些没有)
- ✅ 命名空间导入
- ✅ 函数/常量导入 (use function X as Y)

**验收标准**:
- [ ] alias 存储在 `alias` 字段
- [ ] `names` 字段为空列表
- [ ] 组导入拆分为多个 Import 对象
- [ ] 所有测试用例通过

---

### Story 10.3: PHP LoomGraph 集成测试

**优先级**: P1（质量保证）

**目标**: 验证 PHP 输出符合 LoomGraph 格式

**测试类别**:

1. **JSON 格式验证**:
   - 包含 `inheritances` 字段
   - 包含 `alias` 字段
   - 数据类型正确

2. **真实 PHP 项目示例**:
   - Laravel 风格代码
   - Symfony 风格代码
   - 混合命名空间

3. **边界情况**:
   - 无继承的类
   - 无导入的文件
   - 复杂命名空间

**参考文件**:
- `examples/loomgraph_sample.py` (Python 示例)
- 创建 `examples/loomgraph_sample.php` (PHP 示例)

**验收标准**:
- [ ] 至少 10 个 PHP 集成测试通过
- [ ] 创建 PHP 示例文件
- [ ] 生成 JSON 输出示例

---

## 📊 实现计划

### Phase 1: Story 10.1.2 (PHP 继承提取)

**TDD 流程**:

1. **RED**: 编写测试用例
   ```bash
   tests/test_php_inheritance.py
   ```

2. **GREEN**: 修改实现
   - 修改 `_parse_php_class` 函数
   - 修改 `parse_file` (PHP 分支)

3. **REFACTOR**: 优化代码

**预计工作量**: 2-3 小时

### Phase 2: Story 10.2.2 (PHP 导入别名提取)

**TDD 流程**:

1. **RED**: 编写测试用例
   ```bash
   tests/test_php_import_alias.py
   ```

2. **GREEN**: 修改 `_parse_php_use` 函数

3. **REFACTOR**: 优化代码

**预计工作量**: 1-2 小时

### Phase 3: Story 10.3 (集成测试)

**任务**:
1. 创建 `examples/loomgraph_sample.php`
2. 创建 `tests/test_php_loomgraph_integration.py`
3. 生成 JSON 输出示例

**预计工作量**: 1 小时

---

## 🧪 测试策略

### 单元测试

- **test_php_inheritance.py**: 21+ 测试（对标 Python）
- **test_php_import_alias.py**: 19+ 测试（对标 Python）

### 集成测试

- **test_php_loomgraph_integration.py**: 10+ 测试

### 总计

预计新增测试：**50+ tests**

---

## 📝 文档更新

### 需要更新的文档

1. **CHANGELOG.md**: v0.10.0 条目
2. **README.md**: PHP LoomGraph 支持
3. **RELEASE_NOTES_v0.10.0.md**: 详细发布说明
4. **README_AI.md**: 自动更新

---

## 🎯 成功标准

### MVP 完成标准

- [ ] Story 10.1.2 完成（PHP 继承提取）
- [ ] Story 10.2.2 完成（PHP 导入别名提取）
- [ ] Story 10.3 完成（集成测试）
- [ ] 所有测试通过（预计 779+ passing）
- [ ] 文档更新完成

### 质量标准

- [ ] 测试覆盖率 ≥ 90%（PHP 继承/导入模块）
- [ ] Ruff 检查通过
- [ ] JSON 输出符合 LoomGraph 规范
- [ ] 与 Python 实现行为一致（除了语言差异）

---

## 🔮 未来工作 (Epic 10 Part 3+)

### Story 10.1.3: Java 继承提取

Java 已有 annotation 提取，继承提取相对简单：
- `extends` 单继承
- `implements` 多接口
- 泛型类型处理

### Story 10.4: Trait/Mixin 关系提取

PHP Traits 和 Python Mixins 的代码复用关系：
- 决定是否归入 Inheritance
- 或单独建立 `uses` 关系类型

### Epic 11: Call 关系提取（高优先级）

最复杂的关系类型，需要单独 Epic 规划。

---

## 📚 参考资料

### 内部文档

- `docs/planning/epic10-loomgraph-integration.md` (Part 1 - Python)
- `CHANGELOG.md` v0.9.0
- `RELEASE_NOTES_v0.9.0.md`

### 代码参考

- `src/codeindex/parser.py` (_parse_class for Python)
- `src/codeindex/parser.py` (_parse_php_class)
- `src/codeindex/parser.py` (_parse_php_use)
- `tests/test_python_inheritance.py` (测试模板)
- `tests/test_python_import_alias.py` (测试模板)

### 外部资料

- PHP tree-sitter grammar: https://github.com/tree-sitter/tree-sitter-php
- LoomGraph DATA_CONTRACT.md
- PHP PSR-4 Autoloading Standard

---

**最后更新**: 2026-02-06
**创建者**: Claude Code
**Epic Owner**: codeindex team
