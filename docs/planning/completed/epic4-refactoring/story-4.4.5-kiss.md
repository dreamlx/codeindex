# Story 4.4.5: KISS Description Generation (通用描述生成)

**Epic**: Epic 4 - Code Quality & Usability Enhancement
**Story**: 4.4 Business Semantic Extraction
**Sub-task**: 4.4.5 KISS通用描述优化
**Created**: 2026-02-02
**Status**: In Progress

---

## 🎯 目标

基于用户PHP项目反馈，优化描述生成逻辑，采用KISS原则（Keep It Simple, Stupid），零假设、零领域知识，完全通用。

### 用户反馈的3个问题

| 问题 | 当前状态 | 期望 |
|------|---------|------|
| 1. 通用描述过多 | "后台管理模块：系统管理和配置功能" | 具体一点，有差异化 |
| 2. Admin vs Agent无区分 | 都显示"用户管理相关" | 能看出它们的不同 |
| 3. BigWheel等未识别 | "Module directory" | 至少告诉我有BigWheel |

### 根本问题

**当前架构的缺陷：**
- ❌ 硬编码业务域（user/order/product）- 只适用电商项目
- ❌ 假设特定架构（Controller/Model）- 不通用
- ❌ 优先架构关键词 → 描述千篇一律

**期望架构：**
- ✅ 零假设、零领域知识
- ✅ 支持所有语言（Python/PHP/Java/Go/TypeScript...）
- ✅ 支持所有架构（MVC/DDD/微服务/分层...）
- ✅ 支持所有领域（电商/游戏/编译器/科学计算...）

---

## 🎯 设计原则

### KISS核心思路

```
不做：理解业务含义（"这是用户管理"）
只做：提供足够信息让人类快速理解（列举符号、路径、模式）
```

### 通用信息提取

所有项目都有的客观信息：
1. **路径结构** - `Admin/Controller` vs `Agent/Controller`
2. **符号名称** - `AdminJurUsersController` vs `AgentController`
3. **符号模式** - 后缀（Controller/Service/Util）
4. **符号数量** - 15个 vs 3个
5. **文件类型** - .php / .py / .java

### 描述格式

```
格式：{路径上下文} {符号模式} ({关键符号列举})

例子：
- "Admin/Controller: 15 controllers (AdminJurUsers, UserRole, Permission, ...)"
- "Agent/Controller: 3 controllers (Agent, Commission, Withdrawal)"
- "src/parser: 5 modules (Parser, TokenStream, ASTNode, ...)"
- "engine/renderer: 8 modules (SceneGraph, Camera, Lighting, ...)"
```

---

## 🏗️ 架构设计

### 1. SimpleDescriptionGenerator（新增）

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
        pass

    def _extract_path_context(self, path: str) -> str:
        """提取路径上下文（最后1-2级）"""
        pass

    def _analyze_symbol_pattern(self, symbols: List[str]) -> str:
        """
        分析符号模式（识别共同后缀）

        通用后缀映射（语言无关）：
        - Controller/Controllers → "controllers"
        - Service/Services → "services"
        - Model/Models → "models"
        - Util/Utils/Helper → "utilities"
        - 无明显模式 → "modules/classes"
        """
        pass

    def _extract_entity_names(self, symbols: List[str]) -> List[str]:
        """
        提取实体名（去掉通用后缀）

        "AdminJurUsersController" → "AdminJurUsers"
        "UserRoleService" → "UserRole"
        """
        pass
```

### 2. 重构SemanticExtractor

```python
def _heuristic_extract(self, context: DirectoryContext) -> BusinessSemantic:
    """
    启发式提取 - KISS版本

    移除：
    - ❌ 业务域关键词（user/order/product）
    - ❌ 业务域映射（domain_mappings）
    - ❌ 架构关键词优先级

    保留：
    - ✅ 通用后缀识别（Controller/Service/Model）
    - ✅ 路径上下文
    - ✅ 符号列举
    """
    generator = SimpleDescriptionGenerator()
    description = generator.generate(context)

    return BusinessSemantic(
        description=description,
        purpose=description,
        key_components=generator._extract_entity_names(context.symbols)[:10]
    )
```

---

## 📊 效果预期

### PHP MVC项目（用户项目）

**Before (当前):**
```
Admin/Controller/ → "后台管理模块：系统管理和配置功能"
Agent/Controller/ → "用户管理相关的控制器目录"
Retail/Marketing/ → "Module directory"
```

**After (KISS):**
```
Admin/Controller/ → "Admin/Controller: 15 controllers (AdminJurUsers, Permission, SystemConfig, UserRole, ...)"
Agent/Controller/ → "Agent/Controller: 3 controllers (Agent, Commission, Withdrawal)"
Retail/Marketing/ → "Retail/Marketing: 3 controllers (BigWheel, Coupon, Lottery)"
```

**改进：**
- ✅ 不再通用（每个描述都不同）
- ✅ Admin vs Agent 有差异（符号列表不同）
- ✅ BigWheel 被识别（直接列出）

### Python项目（codeindex自己）

```
src/codeindex/ → "src/codeindex: 29 modules (AIHelper, AdaptiveSelector, Config, Invoker, Parser, ...)"
tests/ → "tests: 25 test modules (adaptive_selector, ai_helper, config, parser, scanner, ...)"
```

### Java Spring项目

```
com/example/service/ → "service: 12 services (Order, Payment, Product, User, ...)"
com/example/repository/ → "repository: 8 repositories (Order, Product, User, ...)"
```

### 游戏引擎（C++）

```
engine/renderer/ → "engine/renderer: 12 modules (Camera, Lighting, Material, RenderPass, SceneGraph, ...)"
engine/physics/ → "engine/physics: 8 modules (Collider, ForceField, PhysicsWorld, RigidBody)"
```

---

## 🗑️ 需要删除的硬编码

### semantic_extractor.py

1. **业务域关键词映射** (lines ~150-200)
```python
# ❌ 删除
domain_keywords = {
    "user": ["用户", "User", "用户管理"],
    "order": ["订单", "Order", "订单管理"],
    "product": ["商品", "Product", "产品"],
    "payment": ["支付", "Payment", "Pay"],
    # ... 8个业务域
}
```

2. **业务域映射** (lines ~200-250)
```python
# ❌ 删除
domain_mappings = {
    "user": "用户管理",
    "order": "订单管理",
    "product": "商品管理",
    # ...
}
```

3. **架构关键词映射中的业务描述** (lines ~100-150)
```python
# ❌ 部分删除
keyword_mappings = {
    "Controller": {
        "description": "控制器目录：处理HTTP请求和业务逻辑路由",  # ❌ 太具体
        # ...
    },
    # ...
}
```

4. **_extract_business_domain()方法** (整个方法)
```python
# ❌ 删除整个方法
def _extract_business_domain(self, context: DirectoryContext) -> Optional[str]:
    # 硬编码业务域检测逻辑
    pass
```

5. **组合逻辑中的业务域优先级** (lines ~300-350)
```python
# ❌ 删除
if arch_keyword and business_domain:
    description = f"{business_domain}相关的{arch_mapping['description'].split('：')[0]}"
```

---

## 🧪 需要修正的测试

### test_semantic_extractor.py

1. **业务域检测测试** - 删除或重构
```python
# ❌ 删除（测试硬编码业务域）
def test_extract_business_domain_from_symbols():
    assert domain == "用户管理"  # 不再做业务域理解
```

2. **架构+业务组合测试** - 重构
```python
# ❌ 修改
def test_extract_controller_semantic_heuristic():
    # Before: 期望 "用户管理相关的控制器目录"
    # After: 期望 "Admin/Controller: N controllers (...)"
```

3. **通用描述测试** - 重构
```python
# ❌ 修改
def test_infer_from_symbols():
    # Before: 期望包含 "用户" 或 "User"
    # After: 期望直接列举符号 "AdminJurUsers, UserRole"
```

### test_project_index_semantic.py

1. **业务关键词断言** - 删除
```python
# ❌ 删除
assert any(keyword in admin_purpose for keyword in
           ["用户", "User", "控制器", "Controller"])
```

2. **改为结构化断言**
```python
# ✅ 新增
assert "Admin/Controller" in admin_purpose
assert "AdminJurUsers" in admin_purpose or "UserRole" in admin_purpose
assert admin_purpose != retail_purpose  # 确保差异化
```

---

## 📋 实施任务清单

### Phase 1: 清理硬编码（准备阶段）

- [ ] 查看git log，了解当前实现历史
- [ ] 识别semantic_extractor.py中的硬编码部分
- [ ] 识别需要修正的测试文件
- [ ] 创建清理计划

### Phase 2: 实现通用生成器（开发阶段）

- [ ] 实现SimpleDescriptionGenerator类
- [ ] 实现_extract_path_context()
- [ ] 实现_analyze_symbol_pattern()
- [ ] 实现_extract_entity_names()
- [ ] 实现generate()主方法

### Phase 3: 重构SemanticExtractor（重构阶段）

- [ ] 删除业务域关键词映射
- [ ] 删除_extract_business_domain()方法
- [ ] 简化_heuristic_extract()逻辑
- [ ] 使用SimpleDescriptionGenerator

### Phase 4: 修正测试（测试阶段）

- [ ] 修正test_semantic_extractor.py
- [ ] 修正test_project_index_semantic.py
- [ ] 修正test_story_4_4_integration.py
- [ ] 确保所有测试通过

### Phase 5: 验证（验证阶段）

- [ ] 在PHP项目验证
- [ ] 在codeindex项目验证
- [ ] 在模拟项目验证（Java/TypeScript）
- [ ] 更新validation report

---

## 🎯 验收标准

### 功能要求

- [ ] 描述格式：`{path}: {count} {pattern} ({symbols})`
- [ ] 路径上下文：提取最后1-2级目录
- [ ] 符号模式：识别Controller/Service/Model等通用后缀
- [ ] 符号列举：排序、去重、截断（前5个）
- [ ] 无硬编码：零业务域假设

### 质量要求

- [ ] 问题1（通用描述）：⭐⭐ → ⭐⭐⭐⭐
- [ ] 问题2（无差异化）：⭐ → ⭐⭐⭐⭐
- [ ] 问题3（BigWheel）：⭐ → ⭐⭐⭐⭐
- [ ] 通用性：在5+种项目类型测试通过
- [ ] 测试覆盖：所有测试通过
- [ ] 性能：<100ms/目录

### 向后兼容

- [ ] 配置文件格式不变
- [ ] BusinessSemantic数据结构不变
- [ ] API接口不变
- [ ] 默认行为改进但不破坏

---

## 📈 预期收益

| 指标 | Before | After | 提升 |
|------|--------|-------|------|
| 描述质量 | ⭐⭐ | ⭐⭐⭐⭐ | +100% |
| 差异化 | ⭐ | ⭐⭐⭐⭐ | +300% |
| 通用性 | ⭐⭐ (仅电商) | ⭐⭐⭐⭐⭐ (所有项目) | +150% |
| 维护成本 | 高（硬编码） | 低（通用逻辑） | -80% |
| 代码行数 | ~500 | ~300 | -40% |

---

## 🚀 下一步

1. **立即执行**：查看git log，对比当前实现
2. **识别清理目标**：列出需要删除的具体代码
3. **TDD开发**：先写测试，再实现
4. **验证**：在真实项目测试

---

**Status**: Ready to implement
**Estimated Effort**: 2.5-3.5 hours
**Priority**: P0 (用户反馈)
