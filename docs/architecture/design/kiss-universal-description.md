# KISS Universal Description Generator

**Date**: 2026-02-02
**Version**: Task 4.4.5
**Status**: Design Document

---

## 🎯 目标

实现完全通用的描述生成器，支持所有编程语言、所有项目架构，零领域知识假设。

### 产品定位

```
codeindex = 通用代码索引工具
- 支持：Python, PHP, Java, Go, TypeScript, Rust, C++...
- 支持：Web, 游戏, 编译器, DevOps, 科学计算...
- 核心：快速、可靠、语言无关、架构无关
```

### 解决的问题

基于用户反馈（PHP项目验证）：

| 问题 | 当前状态 | 目标状态 |
|------|---------|---------|
| 1. 通用描述过多 | "后台管理模块：系统管理和配置功能" | 具体列举符号 |
| 2. Admin vs Agent无区分 | 都是"用户管理相关" | 符号列表不同，自然差异化 |
| 3. 业务词不识别 | "Module directory" | 直接显示原始符号（BigWheel） |

---

## 🏗️ 架构设计

### 核心原则

**不做：** 理解业务含义、翻译术语、猜测语义
**只做：** 提取客观信息、组织展示、保持可追溯性

### 信息提取层次

所有项目都有的通用信息：

1. **路径结构** - `Admin/Controller` vs `Agent/Controller`
2. **符号名称** - `AdminJurUsersController` vs `AgentController`
3. **符号模式** - 后缀（Controller/Service）、数量
4. **文件类型** - .php / .py / .java

### 描述格式

```
格式：{路径上下文}: {数量} {符号模式} ({关键符号列举})

例子：
- "Admin/Controller: 15 controllers (AdminJurUsers, Permission, SystemConfig, ...)"
- "src/parser: 5 modules (ASTNode, Parser, TokenStream, ...)"
- "engine/renderer: 8 modules (Camera, Lighting, Material, ...)"
```

**特点：**
- ✅ 零语义理解
- ✅ 完全通用
- ✅ 信息密度高
- ✅ 可追溯
- ✅ 有差异化

---

## 🔧 核心算法

### SimpleDescriptionGenerator

```python
class SimpleDescriptionGenerator:
    """
    通用描述生成器：零假设、零语义理解
    只提取客观信息，不做主观判断
    """

    def generate(self, context: DirectoryContext) -> str:
        """
        生成描述：{路径} {模式} ({符号})

        步骤：
        1. 提取路径上下文（最后2级目录）
        2. 识别符号模式（共同后缀/前缀）
        3. 列举关键符号（排序、去重、截断）
        4. 简单拼接
        """
```

### 1. 路径上下文提取

```python
def _extract_path_context(self, path: str) -> str:
    """
    提取路径上下文（最后1-2级）

    输入：
    - "Application/Admin/Controller" → "Admin/Controller"
    - "src/codeindex" → "src/codeindex"
    - "engine/renderer/vulkan" → "renderer/vulkan"

    策略：保持原样，不解释含义
    """
```

### 2. 符号模式识别

```python
def _analyze_symbol_pattern(self, symbols: List[str]) -> str:
    """
    分析符号模式（识别共同后缀）

    通用后缀映射（语言无关）：
    - Controller/Controllers → "controllers"
    - Service/Services → "services"
    - Model/Models → "models"
    - Util/Utils/Helper → "utilities"
    - Manager/Managers → "managers"
    - Handler/Handlers → "handlers"
    - Provider/Providers → "providers"
    - Repository/Repositories → "repositories"
    - Test/Spec → "tests"
    - 无明显模式 → "modules"（默认）

    逻辑：
    1. 统计每种后缀的出现次数
    2. 如果某后缀占比 > 50%，使用该后缀
    3. 否则返回通用的 "modules"
    """
```

#### 支持的通用后缀

| 后缀 | 复数形式 | 常见于 |
|------|---------|--------|
| Controller | controllers | MVC架构、Web框架 |
| Service | services | DDD、微服务 |
| Model | models | MVC、ORM |
| Repository | repositories | DDD、数据访问层 |
| Manager | managers | 通用管理类 |
| Handler | handlers | 事件处理、中间件 |
| Provider | providers | 依赖注入、服务提供 |
| Factory | factories | 工厂模式 |
| Strategy | strategies | 策略模式 |
| Observer | observers | 观察者模式 |
| Adapter | adapters | 适配器模式 |
| Util/Helper | utilities | 工具类 |
| Test/Spec | tests | 测试文件 |

### 3. 实体名提取

```python
def _extract_entity_names(self, symbols: List[str]) -> List[str]:
    """
    提取实体名（去掉通用后缀）

    输入：
    - "AdminJurUsersController" → "AdminJurUsers"
    - "UserRoleService" → "UserRole"
    - "ProductModel" → "Product"
    - "IUserRepository" → "User"
    - "AbstractBaseController" → "Base"

    策略：
    1. 去掉后缀（Controller/Service/Model等）
    2. 去掉前缀（I/Abstract/Base等）
    3. 保留核心实体名
    """
```

### 4. 描述生成

```python
def generate(self, context: DirectoryContext) -> str:
    """
    最终拼接

    逻辑：
    1. 如果无符号 → "{path} (empty directory)"
    2. 如果 ≤ 5个符号 → 全部列举
    3. 如果 > 5个符号 → 列举前5个 + "... (N total)"

    排序：字母顺序（稳定、可预测）
    """
```

---

## 📊 效果示例

### PHP MVC项目

```
输入：Admin/Controller/
符号：AdminJurUsersController, UserRoleController, PermissionController

输出："Admin/Controller: 3 controllers (AdminJurUsers, Permission, UserRole)"
```

```
输入：Agent/Controller/
符号：AgentController, CommissionController, WithdrawalController

输出："Agent/Controller: 3 controllers (Agent, Commission, Withdrawal)"
```

✅ **差异化明显**

### Python项目（codeindex）

```
输入：src/codeindex/
符号：Scanner, Parser, Writer, Invoker, SemanticExtractor

输出："src/codeindex: 29 modules (AIHelper, Config, Invoker, Parser, Scanner, ...)"
```

### Java Spring项目

```
输入：com/example/service/
符号：UserService, OrderService, ProductService

输出："service: 3 services (Order, Product, User)"
```

### 游戏引擎（C++）

```
输入：engine/renderer/
符号：SceneGraph, Camera, Lighting, Material, Shader

输出："engine/renderer: 5 modules (Camera, Lighting, Material, SceneGraph, Shader)"
```

### TypeScript前端

```
输入：src/components/
符号：UserProfile.tsx, ProductCard.tsx, OrderList.tsx

输出："src/components: 15 modules (OrderList, ProductCard, UserProfile, ...)"
```

---

## ✅ 通用性验证

### 支持的语言

| 语言 | 符号提取 | 模式识别 | 状态 |
|------|---------|---------|------|
| Python | ✅ class/function | ✅ 后缀识别 | 完全支持 |
| PHP | ✅ class/function | ✅ 后缀识别 | 完全支持 |
| Java | ✅ class/interface | ✅ 后缀识别 | 完全支持 |
| JavaScript/TypeScript | ✅ class/function | ✅ 后缀识别 | 完全支持 |
| Go | ✅ struct/func | ✅ 后缀识别 | 完全支持 |
| Rust | ✅ struct/trait/impl | ✅ 后缀识别 | 完全支持 |
| C++ | ✅ class/struct | ✅ 后缀识别 | 完全支持 |

### 支持的架构模式

| 架构 | 识别能力 | 示例 |
|------|---------|------|
| MVC | ✅ Controller/Model/View | Spring MVC, Laravel |
| DDD | ✅ Service/Repository/Entity | 领域驱动设计 |
| 分层架构 | ✅ Controller/Service/DAO | 传统分层 |
| 微服务 | ✅ Service/Handler/Provider | Spring Boot |
| 六边形架构 | ✅ Adapter/Port/Domain | 端口适配器 |
| 无特定架构 | ✅ modules（默认） | 任何项目 |

---

## 🎯 与旧方案对比

### 旧方案（硬编码领域知识）

```python
# ❌ 问题：硬编码业务域
domain_keywords = {
    "user": ["用户", "User", "用户管理"],
    "order": ["订单", "Order", "订单管理"],
    "product": ["商品", "Product", "产品"],
    # ... 只适用于电商项目
}

# ❌ 问题：做语义理解和翻译
if "User" in symbols:
    return "用户管理相关"  # 翻译丢失原始信息
```

**缺陷：**
1. 只适用于电商/SaaS项目
2. 游戏引擎、编译器等无法识别
3. 需要维护大量关键词
4. 翻译损失可追溯性

### 新方案（KISS通用）

```python
# ✅ 通用：只提取模式，不理解语义
pattern = self._analyze_symbol_pattern(symbols)
# ["XxxController"] → "controllers"（通用后缀）

# ✅ 通用：保留原始符号
entities = self._extract_entity_names(symbols)
# ["AdminJurUsersController"] → ["AdminJurUsers"]（保留）

# ✅ 通用：简单拼接
return f"{path}: {count} {pattern} ({', '.join(entities)})"
# "Admin/Controller: 3 controllers (AdminJurUsers, Permission, UserRole)"
```

**优势：**
1. 完全通用（任何语言、任何架构）
2. 零维护成本
3. 保持可追溯性
4. 自然差异化

---

## 🔬 测试策略

### 单元测试

```python
# 测试路径提取
def test_extract_path_context():
    assert extract("Application/Admin/Controller") == "Admin/Controller"
    assert extract("src/codeindex") == "src/codeindex"

# 测试模式识别
def test_analyze_symbol_pattern():
    assert analyze(["UserController", "OrderController"]) == "controllers"
    assert analyze(["UserService", "OrderService"]) == "services"
    assert analyze(["User", "Order", "Product"]) == "modules"

# 测试实体提取
def test_extract_entity_names():
    assert extract(["UserController"]) == ["User"]
    assert extract(["IUserRepository"]) == ["User"]
    assert extract(["AbstractBaseService"]) == ["Base"]
```

### 集成测试（多场景）

```python
def test_php_mvc_project():
    """PHP MVC项目（用户真实场景）"""
    ...

def test_python_project():
    """Python项目（codeindex自己）"""
    ...

def test_java_spring():
    """Java Spring项目"""
    ...

def test_game_engine():
    """游戏引擎（C++）"""
    ...

def test_frontend_typescript():
    """TypeScript前端项目"""
    ...
```

---

## 📈 质量目标

| 指标 | Before | Target |
|------|--------|--------|
| 通用描述问题 | ⭐⭐ | ⭐⭐⭐⭐ |
| 差异化 | ⭐ | ⭐⭐⭐⭐ |
| 可追溯性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 通用性（语言） | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 通用性（架构） | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 维护成本 | 高（关键词维护） | 低（零维护） |

---

## 🚀 实施计划

### Phase 1: 重构现有代码

1. **删除硬编码**
   - 移除 `domain_keywords`
   - 移除 `_extract_business_domain()`
   - 移除所有领域假设

2. **实现新算法**
   - `SimpleDescriptionGenerator`
   - `_extract_path_context()`
   - `_analyze_symbol_pattern()`
   - `_extract_entity_names()`

3. **修正测试**
   - 删除期望"用户管理"等翻译的测试
   - 改为验证通用格式

### Phase 2: 验证

1. **单元测试** - 覆盖所有核心方法
2. **集成测试** - 5+种项目类型
3. **真实项目** - PHP项目 + codeindex自己

### Phase 3: 文档更新

1. 更新 `story-4.4-validation-report.md`
2. 添加使用示例
3. 记录设计决策

---

## 💡 未来扩展（可选）

### AI模式（Story 4.5+）

KISS方案作为基础，AI作为可选增强：

```python
if config.semantic.use_ai:
    # AI深度理解（用户主动启用，明示成本）
    ai_description = self._ai_extract(context)
    return ai_description
else:
    # KISS快速生成（默认，免费）
    kiss_description = SimpleDescriptionGenerator().generate(context)
    return kiss_description
```

### 用户自定义（配置文件）

```yaml
# .codeindex.yaml
indexing:
  semantic:
    # 用户可覆盖默认后缀映射
    suffix_mappings:
      Ctrl: "controllers"  # 非标准后缀
      Mgr: "managers"

    # 用户可定义路径别名
    path_aliases:
      Admin: "后台管理系统"
      Agent: "代理商平台"
```

---

## 📚 参考

- [Story 4.4 Validation Report](../evaluation/story-4.4-validation-report.md)
- [User Feedback](../evaluation/php-project-feedback.md)
- [KISS Principle](https://en.wikipedia.org/wiki/KISS_principle)

---

**Status**: Design Complete ✅
**Next**: Implementation (Task #3-5)
