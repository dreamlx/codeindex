# Phase 1 敏捷开发规划

基于 IMPROVEMENT_ROADMAP.md 的 Phase 1 核心改进，按照敏捷开发和 GitFlow 原则进行详细规划。

---

## 📋 Phase 1 概览

### 目标
提升 codeindex 的符号选择智能性和大文件处理能力

### 范围
1. **符号重要性评分系统** - 智能选择关键符号
2. **自适应符号提取策略** - 根据文件大小动态调整

### 预期效果
- 大文件符号数：15 → 80-120（+433%-700%）
- 关键API覆盖率：70% → 95%（+36%）
- 符号选择准确性：60% → 92%（+53%）
- Token消耗增加：<20%（可控）

### 时间计划
- **开始日期**：2026-01-27（周一）
- **结束日期**：2026-01-31（周五）
- **总时长**：5个工作日

---

## 🎯 Epic 分解

### Epic 1: 智能符号选择系统
**目标**：实现基于重要性评分的符号选择机制

**价值**：
- 用户价值：找到关键API的概率从70%提升到95%
- 技术价值：建立可扩展的符号评分框架

**验收标准**：
- ✅ 评分算法准确率 ≥90%
- ✅ 关键符号覆盖率 ≥95%
- ✅ 噪音符号比例 <10%
- ✅ 性能影响 <5%

---

### Epic 2: 大文件自适应处理
**目标**：根据文件大小智能调整符号提取数量

**价值**：
- 用户价值：大文件信息完整性提升400%+
- 技术价值：自适应策略可应用于其他场景

**验收标准**：
- ✅ 大文件（>2000行）符号数 ≥80
- ✅ 小文件保持高效（10-15个符号）
- ✅ Token消耗增幅 <20%
- ✅ 配置可自定义

---

## 🏗️ Feature 分解

### Epic 1 → Features

#### Feature 1.1: 符号评分引擎
**描述**：实现多维度符号重要性评分算法

**技术设计**：
- 新文件：`src/codeindex/symbol_scorer.py`
- 核心类：`SymbolImportanceScorer`
- 评分维度：可见性、语义、文档、复杂度、命名模式

**Story 分解**：
- Story 1.1.1: 创建评分器基础架构
- Story 1.1.2: 实现可见性评分
- Story 1.1.3: 实现语义重要性评分
- Story 1.1.4: 实现文档完整性评分
- Story 1.1.5: 实现代码复杂度评分
- Story 1.1.6: 实现命名模式评分

---

#### Feature 1.2: 符号排序和筛选
**描述**：集成评分系统到现有的符号过滤流程

**技术设计**：
- 修改：`src/codeindex/smart_writer.py`
- 新增方法：`_filter_symbols_by_importance()`
- 集成点：`_generate_detailed()` 方法

**Story 分解**：
- Story 1.2.1: 集成评分器到 SmartWriter
- Story 1.2.2: 实现基于评分的排序
- Story 1.2.3: 添加评分阈值配置

---

### Epic 2 → Features

#### Feature 2.1: 自适应配置系统
**描述**：设计和实现文件大小分层配置

**技术设计**：
- 修改：`src/codeindex/config.py`
- 新增类：`AdaptiveSymbolConfig`
- 配置层级：tiny/small/medium/large/xlarge/huge

**Story 分解**：
- Story 2.1.1: 设计自适应配置数据结构
- Story 2.1.2: 实现配置加载和验证
- Story 2.1.3: 添加默认配置

---

#### Feature 2.2: 动态符号限制计算
**描述**：根据文件大小动态计算符号提取数量

**技术设计**：
- 新增函数：`calculate_adaptive_limit()`
- 考虑因素：文件行数、符号密度
- 集成点：`SmartWriter._generate_detailed()`

**Story 分解**：
- Story 2.2.1: 实现基础自适应算法
- Story 2.2.2: 添加符号密度调整
- Story 2.2.3: 集成到 SmartWriter

---

## 📝 Story 详细设计

### Story 1.1.1: 创建评分器基础架构
**优先级**: P0 (最高)
**预计工时**: 4小时
**负责人**: TBD

#### 用户故事
```
作为开发者
我希望有一个可扩展的符号评分系统
以便未来可以轻松添加新的评分维度
```

#### 验收标准
- [ ] 创建 `src/codeindex/symbol_scorer.py` 文件
- [ ] 实现 `ScoringContext` 数据类
- [ ] 实现 `SymbolImportanceScorer` 基础类
- [ ] 实现 `score()` 方法框架
- [ ] 单元测试覆盖率 ≥90%

#### TDD 测试用例

```python
# tests/test_symbol_scorer.py

def test_scorer_initialization():
    """测试评分器初始化"""
    scorer = SymbolImportanceScorer()
    assert scorer is not None
    assert scorer.context is not None

def test_score_returns_valid_range():
    """测试评分在有效范围内 (0-100)"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(name="test", kind="function", signature="def test()")

    score = scorer.score(symbol)

    assert 0 <= score <= 100

def test_score_with_context():
    """测试带上下文的评分"""
    context = ScoringContext(framework="thinkphp", file_type="controller")
    scorer = SymbolImportanceScorer(context)
    symbol = Symbol(name="pay", kind="method", signature="public function pay()")

    score = scorer.score(symbol)

    assert score > 50  # 核心方法应该得高分
```

#### Task 分解
- [ ] Task 1.1.1.1: 创建 `symbol_scorer.py` 文件
- [ ] Task 1.1.1.2: 定义 `ScoringContext` 数据类
- [ ] Task 1.1.1.3: 定义 `SymbolImportanceScorer` 类
- [ ] Task 1.1.1.4: 实现 `score()` 方法框架（返回50）
- [ ] Task 1.1.1.5: 编写基础单元测试
- [ ] Task 1.1.1.6: 代码审查和重构

#### 分支策略
```bash
# 从 develop 创建 feature 分支
git checkout develop
git pull origin develop
git checkout -b feature/symbol-scorer-base

# 开发和测试
# ...

# 完成后合并回 develop
git checkout develop
git merge --no-ff feature/symbol-scorer-base
git push origin develop
```

---

### Story 1.1.2: 实现可见性评分
**优先级**: P0
**预计工时**: 2小时
**依赖**: Story 1.1.1

#### 用户故事
```
作为用户
我希望公共API优先被索引
以便快速找到对外暴露的接口
```

#### 验收标准
- [ ] 实现 `_score_visibility()` 方法
- [ ] 公共方法得分 +20
- [ ] 受保护方法得分 +10
- [ ] 私有方法得分 +0
- [ ] 单元测试覆盖率 ≥90%

#### TDD 测试用例

```python
def test_public_method_gets_high_visibility_score():
    """测试公共方法获得高可见性分数"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(
        name="createOrder",
        kind="method",
        signature="public function createOrder()"
    )

    visibility_score = scorer._score_visibility(symbol)

    assert visibility_score == 20.0

def test_private_method_gets_low_visibility_score():
    """测试私有方法获得低可见性分数"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(
        name="_log",
        kind="method",
        signature="private function _log()"
    )

    visibility_score = scorer._score_visibility(symbol)

    assert visibility_score == 0.0

def test_python_underscore_naming():
    """测试Python下划线命名约定"""
    scorer = SymbolImportanceScorer()

    # 公共函数（无下划线）
    public = Symbol(name="process", kind="function", signature="def process()")
    assert scorer._score_visibility(public) == 15.0

    # 私有函数（单下划线）
    private = Symbol(name="_helper", kind="function", signature="def _helper()")
    assert scorer._score_visibility(private) == 5.0
```

#### Task 分解
- [ ] Task 1.1.2.1: 编写测试用例
- [ ] Task 1.1.2.2: 实现 `_score_visibility()` 方法
- [ ] Task 1.1.2.3: 处理 PHP 可见性关键字
- [ ] Task 1.1.2.4: 处理 Python 命名约定
- [ ] Task 1.1.2.5: 验证测试通过
- [ ] Task 1.1.2.6: 代码审查

#### 分支策略
```bash
git checkout develop
git checkout -b feature/scorer-visibility

# TDD 循环：Red → Green → Refactor
# ...

git checkout develop
git merge --no-ff feature/scorer-visibility
```

---

### Story 1.1.3: 实现语义重要性评分
**优先级**: P0
**预计工时**: 3小时
**依赖**: Story 1.1.1

#### 用户故事
```
作为用户
我希望关键业务方法（如pay、createOrder）优先显示
以便快速定位核心功能
```

#### 验收标准
- [ ] 实现 `_score_semantics()` 方法
- [ ] 定义核心关键词列表（CRITICAL_KEYWORDS）
- [ ] 核心关键词匹配得分 +25
- [ ] 次要关键词匹配得分 +15
- [ ] 单元测试覆盖率 ≥90%

#### TDD 测试用例

```python
def test_critical_keyword_gets_high_semantic_score():
    """测试核心关键词获得高语义分数"""
    scorer = SymbolImportanceScorer()

    critical_symbols = [
        Symbol(name="pay", kind="method", signature="public function pay()"),
        Symbol(name="createOrder", kind="method", signature="public function createOrder()"),
        Symbol(name="handleNotify", kind="method", signature="public function handleNotify()"),
    ]

    for symbol in critical_symbols:
        score = scorer._score_semantics(symbol)
        assert score == 25.0, f"{symbol.name} should get 25.0"

def test_secondary_keyword_gets_medium_semantic_score():
    """测试次要关键词获得中等语义分数"""
    scorer = SymbolImportanceScorer()

    secondary_symbols = [
        Symbol(name="findUser", kind="method", signature="public function findUser()"),
        Symbol(name="searchProducts", kind="method", signature="public function searchProducts()"),
    ]

    for symbol in secondary_symbols:
        score = scorer._score_semantics(symbol)
        assert score == 15.0

def test_generic_method_gets_low_semantic_score():
    """测试普通方法获得低语义分数"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(name="helper", kind="method", signature="public function helper()")

    score = scorer._score_semantics(symbol)

    assert score == 5.0
```

#### Task 分解
- [ ] Task 1.1.3.1: 编写测试用例
- [ ] Task 1.1.3.2: 定义 CRITICAL_KEYWORDS 列表
- [ ] Task 1.1.3.3: 定义 SECONDARY_KEYWORDS 列表
- [ ] Task 1.1.3.4: 实现 `_score_semantics()` 方法
- [ ] Task 1.1.3.5: 验证测试通过
- [ ] Task 1.1.3.6: 代码审查

---

### Story 1.1.4: 实现文档完整性评分
**优先级**: P1
**预计工时**: 2小时
**依赖**: Story 1.1.1

#### 用户故事
```
作为用户
我希望有文档的方法优先显示
以便快速理解方法用途
```

#### 验收标准
- [ ] 实现 `_score_documentation()` 方法
- [ ] 详细文档（>200字符）得分 +15
- [ ] 简短文档（>50字符）得分 +10
- [ ] 最小文档得分 +5
- [ ] 无文档得分 +0

#### TDD 测试用例

```python
def test_detailed_documentation_gets_high_score():
    """测试详细文档获得高分"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(
        name="pay",
        kind="method",
        signature="public function pay()",
        docstring="This is a very detailed documentation that explains the payment processing flow, including validation, third-party integration, callback handling, and error recovery mechanisms. It provides comprehensive guidance for developers."
    )

    score = scorer._score_documentation(symbol)

    assert score == 15.0

def test_no_documentation_gets_zero_score():
    """测试无文档获得零分"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(
        name="helper",
        kind="method",
        signature="public function helper()",
        docstring=""
    )

    score = scorer._score_documentation(symbol)

    assert score == 0.0
```

---

### Story 1.1.5: 实现代码复杂度评分
**优先级**: P1
**预计工时**: 2小时
**依赖**: Story 1.1.1

#### 用户故事
```
作为用户
我希望复杂的核心逻辑方法优先显示
以便快速定位重要实现
```

#### 验收标准
- [ ] 实现 `_score_complexity()` 方法
- [ ] 基于代码行数计算复杂度
- [ ] >100行得分 +20
- [ ] 50-100行得分 +15
- [ ] <5行得分 +0

#### TDD 测试用例

```python
def test_complex_method_gets_high_complexity_score():
    """测试复杂方法获得高复杂度分数"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(
        name="processPayment",
        kind="method",
        signature="public function processPayment()",
        line_start=100,
        line_end=250  # 150行
    )

    score = scorer._score_complexity(symbol)

    assert score == 20.0

def test_simple_method_gets_low_complexity_score():
    """测试简单方法获得低复杂度分数"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(
        name="getId",
        kind="method",
        signature="public function getId()",
        line_start=10,
        line_end=12  # 2行
    )

    score = scorer._score_complexity(symbol)

    assert score == 0.0
```

---

### Story 1.1.6: 实现命名模式评分
**优先级**: P0
**预计工时**: 2小时
**依赖**: Story 1.1.1

#### 用户故事
```
作为用户
我不希望看到大量的getter/setter方法
以便专注于核心业务逻辑
```

#### 验收标准
- [ ] 实现 `_score_naming_pattern()` 方法
- [ ] 定义噪音模式列表（NOISE_PATTERNS）
- [ ] 匹配噪音模式得分 -20
- [ ] 不匹配得分 +0

#### TDD 测试用例

```python
def test_getter_method_gets_negative_score():
    """测试getter方法获得负分"""
    scorer = SymbolImportanceScorer()

    noise_symbols = [
        Symbol(name="getPayType", kind="method", signature="public function getPayType()"),
        Symbol(name="setConfig", kind="method", signature="public function setConfig()"),
        Symbol(name="_log", kind="method", signature="private function _log()"),
    ]

    for symbol in noise_symbols:
        score = scorer._score_naming_pattern(symbol)
        assert score == -20.0, f"{symbol.name} should get -20.0"

def test_business_method_gets_zero_score():
    """测试业务方法不扣分"""
    scorer = SymbolImportanceScorer()
    symbol = Symbol(name="processOrder", kind="method", signature="public function processOrder()")

    score = scorer._score_naming_pattern(symbol)

    assert score == 0.0
```

---

### Story 1.2.1: 集成评分器到 SmartWriter
**优先级**: P0
**预计工时**: 3小时
**依赖**: Story 1.1.1-1.1.6

#### 用户故事
```
作为开发者
我希望SmartWriter使用评分系统选择符号
以便生成更智能的索引
```

#### 验收标准
- [ ] 修改 `smart_writer.py` 的 `_filter_symbols()` 方法
- [ ] 导入并使用 `SymbolImportanceScorer`
- [ ] 创建 `ScoringContext` 传递框架信息
- [ ] 集成测试通过

#### TDD 测试用例

```python
# tests/test_smart_writer.py

def test_filter_symbols_uses_importance_scoring():
    """测试符号过滤使用重要性评分"""
    config = IndexingConfig()
    writer = SmartWriter(config)

    symbols = [
        Symbol(name="pay", kind="method", signature="public function pay()"),
        Symbol(name="getPayType", kind="method", signature="public function getPayType()"),
        Symbol(name="_log", kind="method", signature="private function _log()"),
    ]

    filtered = writer._filter_symbols(symbols, Path("PayController.php"))

    # pay() 应该在前面，getter和私有方法应该被排除或排在后面
    assert filtered[0].name == "pay"
    assert "getPayType" not in [s.name for s in filtered[:5]]
```

#### Task 分解
- [ ] Task 1.2.1.1: 编写集成测试
- [ ] Task 1.2.1.2: 导入 `symbol_scorer` 模块
- [ ] Task 1.2.1.3: 修改 `_filter_symbols()` 方法
- [ ] Task 1.2.1.4: 添加框架检测逻辑
- [ ] Task 1.2.1.5: 验证集成测试通过
- [ ] Task 1.2.1.6: 端到端测试

---

### Story 2.1.1: 设计自适应配置数据结构
**优先级**: P0
**预计工时**: 3小时
**依赖**: 无

#### 用户故事
```
作为用户
我希望能配置不同文件大小的符号限制
以便根据项目特点调整
```

#### 验收标准
- [ ] 创建 `AdaptiveSymbolConfig` 数据类
- [ ] 定义分层阈值（tiny/small/medium/large/xlarge/huge）
- [ ] 定义每层符号限制
- [ ] 支持 YAML 配置加载

#### TDD 测试用例

```python
# tests/test_config.py

def test_adaptive_config_has_default_thresholds():
    """测试自适应配置有默认阈值"""
    config = AdaptiveSymbolConfig()

    assert config.thresholds["tiny"] == 100
    assert config.thresholds["small"] == 200
    assert config.thresholds["medium"] == 500
    assert config.thresholds["large"] == 1000
    assert config.thresholds["xlarge"] == 2000

def test_adaptive_config_has_default_limits():
    """测试自适应配置有默认限制"""
    config = AdaptiveSymbolConfig()

    assert config.limits["tiny"] == 10
    assert config.limits["small"] == 15
    assert config.limits["medium"] == 30
    assert config.limits["large"] == 50
    assert config.limits["xlarge"] == 80
    assert config.limits["huge"] == 120

def test_load_adaptive_config_from_yaml():
    """测试从YAML加载自适应配置"""
    yaml_content = """
    adaptive_symbols:
      enabled: true
      thresholds:
        large: 1500
      limits:
        large: 60
    """

    config = load_config_from_yaml(yaml_content)

    assert config.adaptive_symbols.enabled == True
    assert config.adaptive_symbols.thresholds["large"] == 1500
    assert config.adaptive_symbols.limits["large"] == 60
```

---

### Story 2.2.1: 实现基础自适应算法
**优先级**: P0
**预计工时**: 2小时
**依赖**: Story 2.1.1

#### 用户故事
```
作为系统
我需要根据文件行数自动计算符号限制
以便提供更好的信息完整性
```

#### 验收标准
- [ ] 实现 `calculate_adaptive_limit()` 函数
- [ ] 根据文件行数返回对应限制
- [ ] 支持禁用自适应（回退到固定值）
- [ ] 单元测试覆盖所有分层

#### TDD 测试用例

```python
# tests/test_adaptive.py

def test_tiny_file_gets_tiny_limit():
    """测试小文件获得小限制"""
    config = AdaptiveSymbolConfig()

    limit = calculate_adaptive_limit(
        file_lines=80,
        total_symbols=10,
        config=config
    )

    assert limit == 10

def test_huge_file_gets_huge_limit():
    """测试巨大文件获得大限制"""
    config = AdaptiveSymbolConfig()

    limit = calculate_adaptive_limit(
        file_lines=5000,
        total_symbols=500,
        config=config
    )

    assert limit == 120

def test_disabled_adaptive_returns_default():
    """测试禁用自适应返回默认值"""
    config = AdaptiveSymbolConfig(enabled=False)

    limit = calculate_adaptive_limit(
        file_lines=5000,
        total_symbols=500,
        config=config
    )

    assert limit == 15  # 默认值
```

---

## 🌳 GitFlow 分支策略

### 分支结构

```
main (生产分支)
  ↑
release/v1.1.0 (发布分支，Phase 1 完成后创建)
  ↑
develop (开发分支，Phase 1 的集成分支)
  ↑
  ├── feature/symbol-scorer-base (Story 1.1.1)
  ├── feature/scorer-visibility (Story 1.1.2)
  ├── feature/scorer-semantics (Story 1.1.3)
  ├── feature/scorer-documentation (Story 1.1.4)
  ├── feature/scorer-complexity (Story 1.1.5)
  ├── feature/scorer-naming (Story 1.1.6)
  ├── feature/integrate-scorer (Story 1.2.1)
  ├── feature/adaptive-config (Story 2.1.1)
  ├── feature/adaptive-algorithm (Story 2.2.1)
  └── feature/adaptive-integration (Story 2.2.3)
```

### 工作流程

#### 1. 初始化 develop 分支

```bash
# 从 main 创建 develop 分支
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop
```

#### 2. 开发单个 Story

```bash
# 从 develop 创建 feature 分支
git checkout develop
git pull origin develop
git checkout -b feature/symbol-scorer-base

# TDD 循环开发
# 1. 编写测试（Red）
# 2. 实现代码（Green）
# 3. 重构代码（Refactor）

# 提交代码
git add .
git commit -m "feat(scorer): implement symbol scorer base architecture

- Create SymbolImportanceScorer class
- Add ScoringContext dataclass
- Implement score() method framework
- Add comprehensive unit tests

Tests: 10/10 passing
Coverage: 95%

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 推送到远程
git push -u origin feature/symbol-scorer-base
```

#### 3. 合并到 develop

```bash
# 确保测试通过
pytest tests/test_symbol_scorer.py -v

# 切换到 develop
git checkout develop
git pull origin develop

# 合并 feature 分支（使用 --no-ff 保留分支历史）
git merge --no-ff feature/symbol-scorer-base

# 推送到远程
git push origin develop

# 删除已合并的 feature 分支（可选）
git branch -d feature/symbol-scorer-base
git push origin --delete feature/symbol-scorer-base
```

#### 4. Phase 1 完成后创建 release 分支

```bash
# 所有 feature 合并到 develop 后
git checkout develop
git pull origin develop

# 创建 release 分支
git checkout -b release/v1.1.0

# 更新版本号、CHANGELOG等
# ...

# 合并到 main
git checkout main
git merge --no-ff release/v1.1.0
git tag -a v1.1.0 -m "Release v1.1.0: Phase 1 improvements"
git push origin main --tags

# 合并回 develop
git checkout develop
git merge --no-ff release/v1.1.0
git push origin develop

# 删除 release 分支
git branch -d release/v1.1.0
```

---

## 📅 Sprint 计划（5天）

### Day 1 (周一): 评分器基础架构

**目标**: 完成评分器基础和核心评分维度

**任务**:
- [x] Morning: Story 1.1.1 - 评分器基础架构
- [x] Afternoon: Story 1.1.2 - 可见性评分
- [x] Evening: Story 1.1.3 - 语义评分（部分）

**交付物**:
- `symbol_scorer.py` 基础文件
- 3个评分维度实现
- 单元测试 ≥90% 覆盖

**分支**:
- `feature/symbol-scorer-base` → `develop`
- `feature/scorer-visibility` → `develop`

---

### Day 2 (周二): 完成评分系统

**目标**: 完成所有评分维度

**任务**:
- [x] Morning: Story 1.1.3 - 语义评分（完成）
- [x] Afternoon: Story 1.1.4 - 文档评分
- [x] Afternoon: Story 1.1.5 - 复杂度评分
- [x] Evening: Story 1.1.6 - 命名模式评分

**交付物**:
- 完整的评分系统
- 所有评分维度测试通过
- 端到端评分测试

**分支**:
- `feature/scorer-semantics` → `develop`
- `feature/scorer-documentation` → `develop`
- `feature/scorer-complexity` → `develop`
- `feature/scorer-naming` → `develop`

---

### Day 3 (周三): 集成评分器 + 自适应配置

**目标**: 集成评分器到 SmartWriter，设计自适应配置

**任务**:
- [x] Morning: Story 1.2.1 - 集成评分器到 SmartWriter
- [x] Afternoon: Story 2.1.1 - 自适应配置设计
- [x] Evening: Story 2.1.2 - 配置加载和验证

**交付物**:
- SmartWriter 使用评分系统
- 自适应配置数据结构
- 集成测试通过

**分支**:
- `feature/integrate-scorer` → `develop`
- `feature/adaptive-config` → `develop`

---

### Day 4 (周四): 自适应算法实现

**目标**: 实现并集成自适应符号提取

**任务**:
- [x] Morning: Story 2.2.1 - 基础自适应算法
- [x] Afternoon: Story 2.2.2 - 符号密度调整
- [x] Evening: Story 2.2.3 - 集成到 SmartWriter

**交付物**:
- 完整的自适应算法
- SmartWriter 支持自适应
- 端到端测试通过

**分支**:
- `feature/adaptive-algorithm` → `develop`
- `feature/adaptive-integration` → `develop`

---

### Day 5 (周五): 验证和发布

**目标**: 全面测试、文档更新、准备发布

**任务**:
- [x] Morning: 真实项目测试（PHP 支付项目）
- [x] Morning: 性能测试和优化
- [x] Afternoon: 更新文档（CHANGELOG, README）
- [x] Afternoon: 创建 release 分支
- [x] Evening: 发布 v1.1.0

**交付物**:
- 真实项目验证通过
- 性能测试报告
- 更新的文档
- v1.1.0 release

**分支**:
- `release/v1.1.0` → `main`

---

## ✅ Definition of Done (DoD)

每个 Story 完成的标准：

### 代码质量
- [ ] 所有单元测试通过（pytest）
- [ ] 测试覆盖率 ≥90%
- [ ] Lint 检查通过（ruff check）
- [ ] 代码格式化（ruff format）
- [ ] 类型提示完整（mypy检查，可选）

### 功能完整性
- [ ] 验收标准全部满足
- [ ] 集成测试通过
- [ ] 无已知 Bug

### 文档
- [ ] Docstring 完整
- [ ] 内联注释清晰
- [ ] 必要时更新 README

### 版本控制
- [ ] Commit message 符合规范
- [ ] Feature 分支已合并到 develop
- [ ] 无冲突

---

## 📊 进度跟踪

### Story 完成状态

| Story | 状态 | 负责人 | 完成日期 |
|-------|------|--------|---------|
| 1.1.1 评分器基础 | 📝 待开始 | TBD | - |
| 1.1.2 可见性评分 | 📝 待开始 | TBD | - |
| 1.1.3 语义评分 | 📝 待开始 | TBD | - |
| 1.1.4 文档评分 | 📝 待开始 | TBD | - |
| 1.1.5 复杂度评分 | 📝 待开始 | TBD | - |
| 1.1.6 命名评分 | 📝 待开始 | TBD | - |
| 1.2.1 集成评分器 | 📝 待开始 | TBD | - |
| 2.1.1 自适应配置 | 📝 待开始 | TBD | - |
| 2.2.1 自适应算法 | 📝 待开始 | TBD | - |
| 2.2.3 集成自适应 | 📝 待开始 | TBD | - |

### Burndown Chart (TODO)

使用 GitHub Projects 或其他工具跟踪 burndown。

---

## 🔗 相关文档

- [IMPROVEMENT_ROADMAP.md](improvement-roadmap.md) - 完整改进路线图
- [IMPROVEMENT_PROPOSALS.md](improvement-proposals.md) - 详细技术提案
- [evaluation/before-after.md](../evaluation/before-after.md) - 改进效果对比

---

## 💬 每日站会问题

1. 昨天完成了什么？
2. 今天计划做什么？
3. 有什么阻碍吗？

---

## 🎯 Phase 1 成功标准

### 必达目标
- ✅ 大文件（>2000行）符号数 ≥ 80
- ✅ 关键API覆盖率 ≥ 90%
- ✅ 噪音符号比例 < 15%
- ✅ Token消耗增幅 < 20%
- ✅ 所有测试通过
- ✅ 代码覆盖率 ≥ 90%

### 质量目标
- ✅ 无 P0/P1 Bug
- ✅ 真实项目验证通过
- ✅ 性能无明显退化（<5%）
- ✅ 文档完整更新

---

**准备好开始 Phase 1 了吗？** 🚀

下一步：
1. 确认计划
2. 创建 develop 分支
3. 开始 Story 1.1.1
