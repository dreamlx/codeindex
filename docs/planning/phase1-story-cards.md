# Phase 1 Story Cards

每个 Story 的详细卡片，包含验收标准、测试用例和 Task 清单。

---

## 📋 Story 1.1.1: 创建评分器基础架构

### Story Card

```
ID: STORY-1.1.1
Title: 创建评分器基础架构
Epic: 智能符号选择系统
Priority: P0 (最高)
Points: 3
Status: 📝 待开始
```

### User Story

```
作为开发者
我希望有一个可扩展的符号评分系统
以便未来可以轻松添加新的评分维度
```

### Acceptance Criteria

- [ ] AC1: 创建 `src/codeindex/symbol_scorer.py` 文件
- [ ] AC2: 实现 `ScoringContext` 数据类，包含 framework、file_type、total_symbols 字段
- [ ] AC3: 实现 `SymbolImportanceScorer` 类，包含 `__init__` 和 `score` 方法
- [ ] AC4: `score()` 方法返回 0-100 之间的浮点数
- [ ] AC5: 单元测试覆盖率 ≥90%
- [ ] AC6: 所有测试通过（pytest）
- [ ] AC7: Lint 检查通过（ruff check）

### Test Cases (TDD)

```python
# tests/test_symbol_scorer.py

import pytest
from pathlib import Path
from codeindex.parser import Symbol
from codeindex.symbol_scorer import SymbolImportanceScorer, ScoringContext


class TestSymbolScorerBase:
    """测试符号评分器基础功能"""

    def test_scorer_initialization_without_context(self):
        """测试无上下文初始化"""
        scorer = SymbolImportanceScorer()

        assert scorer is not None
        assert scorer.context is not None
        assert scorer.context.framework == "unknown"
        assert scorer.context.file_type == "unknown"

    def test_scorer_initialization_with_context(self):
        """测试带上下文初始化"""
        context = ScoringContext(
            framework="thinkphp",
            file_type="controller",
            total_symbols=100
        )
        scorer = SymbolImportanceScorer(context)

        assert scorer.context.framework == "thinkphp"
        assert scorer.context.file_type == "controller"
        assert scorer.context.total_symbols == 100

    def test_score_returns_valid_range(self):
        """测试评分在有效范围内 (0-100)"""
        scorer = SymbolImportanceScorer()
        symbol = Symbol(
            name="test_function",
            kind="function",
            signature="def test_function()",
            docstring="",
            line_start=1,
            line_end=10
        )

        score = scorer.score(symbol)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_score_is_consistent(self):
        """测试相同符号的评分一致性"""
        scorer = SymbolImportanceScorer()
        symbol = Symbol(
            name="process",
            kind="function",
            signature="def process()",
            docstring="Process data",
            line_start=1,
            line_end=50
        )

        score1 = scorer.score(symbol)
        score2 = scorer.score(symbol)

        assert score1 == score2

    def test_different_symbols_different_scores(self):
        """测试不同符号应该有不同评分"""
        scorer = SymbolImportanceScorer()

        important = Symbol(
            name="pay",
            kind="method",
            signature="public function pay()",
            docstring="Process payment",
            line_start=1,
            line_end=100
        )

        trivial = Symbol(
            name="getPayType",
            kind="method",
            signature="public function getPayType()",
            docstring="",
            line_start=1,
            line_end=3
        )

        score_important = scorer.score(important)
        score_trivial = scorer.score(trivial)

        assert score_important > score_trivial
```

### Task Checklist

- [ ] **Task 1.1.1.1**: 创建文件和基础结构 (30min)
  ```bash
  touch src/codeindex/symbol_scorer.py
  # 添加文件头注释、导入语句
  ```

- [ ] **Task 1.1.1.2**: 定义 `ScoringContext` 数据类 (15min)
  ```python
  @dataclass
  class ScoringContext:
      framework: str = "unknown"
      file_type: str = "unknown"
      total_symbols: int = 0
  ```

- [ ] **Task 1.1.1.3**: 定义 `SymbolImportanceScorer` 类 (30min)
  ```python
  class SymbolImportanceScorer:
      def __init__(self, context: Optional[ScoringContext] = None):
          self.context = context or ScoringContext()
  ```

- [ ] **Task 1.1.1.4**: 实现 `score()` 方法框架 (45min)
  ```python
  def score(self, symbol: Symbol) -> float:
      """返回 0-100 之间的评分"""
      return 50.0  # 临时返回中间值
  ```

- [ ] **Task 1.1.1.5**: 编写单元测试 (1.5hr)
  - 创建 `tests/test_symbol_scorer.py`
  - 实现上述 5 个测试用例
  - 运行测试确保通过

- [ ] **Task 1.1.1.6**: 代码审查和重构 (30min)
  - 运行 `ruff check src/codeindex/symbol_scorer.py`
  - 运行 `ruff format src/codeindex/symbol_scorer.py`
  - 添加完整的 docstring
  - 检查类型提示

### Definition of Done

- [x] 所有测试用例通过
- [x] 代码覆盖率 ≥90%
- [x] Ruff lint 通过
- [x] 代码已格式化
- [x] Docstring 完整
- [x] PR 已审查
- [x] 已合并到 develop

### Git Workflow

```bash
# 1. 创建 feature 分支
git checkout develop
git pull origin develop
git checkout -b feature/symbol-scorer-base

# 2. TDD 循环开发
# Red: 编写测试
# Green: 实现功能
# Refactor: 优化代码

# 3. 提交
git add src/codeindex/symbol_scorer.py tests/test_symbol_scorer.py
git commit -m "feat(scorer): implement symbol scorer base architecture

- Create SymbolImportanceScorer class
- Add ScoringContext dataclass
- Implement score() method framework
- Add comprehensive unit tests (5 test cases)

Tests: 5/5 passing
Coverage: 95%

Closes #STORY-1.1.1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 4. 推送和合并
git push -u origin feature/symbol-scorer-base

# (Code Review)

git checkout develop
git merge --no-ff feature/symbol-scorer-base
git push origin develop
git branch -d feature/symbol-scorer-base
```

---

## 📋 Story 1.1.2: 实现可见性评分

### Story Card

```
ID: STORY-1.1.2
Title: 实现可见性评分
Epic: 智能符号选择系统
Priority: P0
Points: 2
Depends: STORY-1.1.1
Status: 📝 待开始
```

### User Story

```
作为用户
我希望公共API优先被索引
以便快速找到对外暴露的接口
```

### Acceptance Criteria

- [ ] AC1: 实现 `_score_visibility()` 方法
- [ ] AC2: PHP public 方法得分 +20
- [ ] AC3: PHP protected 方法得分 +10
- [ ] AC4: PHP private 方法得分 +0
- [ ] AC5: Python 公共函数（无下划线）得分 +15
- [ ] AC6: Python 私有函数（_前缀）得分 +5
- [ ] AC7: 单元测试覆盖率 ≥90%

### Test Cases (TDD)

```python
class TestVisibilityScoring:
    """测试可见性评分"""

    @pytest.fixture
    def scorer(self):
        return SymbolImportanceScorer()

    def test_php_public_method_high_score(self, scorer):
        """PHP public 方法获得高分"""
        symbol = Symbol(
            name="createOrder",
            kind="method",
            signature="public function createOrder()",
        )
        score = scorer._score_visibility(symbol)
        assert score == 20.0

    def test_php_protected_method_medium_score(self, scorer):
        """PHP protected 方法获得中等分数"""
        symbol = Symbol(
            name="validateData",
            kind="method",
            signature="protected function validateData()",
        )
        score = scorer._score_visibility(symbol)
        assert score == 10.0

    def test_php_private_method_low_score(self, scorer):
        """PHP private 方法获得低分"""
        symbol = Symbol(
            name="_log",
            kind="method",
            signature="private function _log()",
        )
        score = scorer._score_visibility(symbol)
        assert score == 0.0

    def test_python_public_function_high_score(self, scorer):
        """Python 公共函数获得高分"""
        symbol = Symbol(
            name="process_payment",
            kind="function",
            signature="def process_payment()",
        )
        score = scorer._score_visibility(symbol)
        assert score == 15.0

    def test_python_private_function_low_score(self, scorer):
        """Python 私有函数（_前缀）获得低分"""
        symbol = Symbol(
            name="_internal_helper",
            kind="function",
            signature="def _internal_helper()",
        )
        score = scorer._score_visibility(symbol)
        assert score == 5.0

    def test_python_magic_method_low_score(self, scorer):
        """Python 魔术方法（__前缀）获得低分"""
        symbol = Symbol(
            name="__init__",
            kind="method",
            signature="def __init__(self)",
        )
        score = scorer._score_visibility(symbol)
        assert score == 5.0
```

### Task Checklist

- [ ] **Task 1.1.2.1**: 编写测试用例 (45min)
  - 6个测试用例覆盖 PHP 和 Python

- [ ] **Task 1.1.2.2**: 实现 `_score_visibility()` 方法 (1hr)
  ```python
  def _score_visibility(self, symbol: Symbol) -> float:
      sig_lower = symbol.signature.lower()

      if "public" in sig_lower:
          return 20.0
      elif "protected" in sig_lower:
          return 10.0
      elif "private" in sig_lower:
          return 0.0
      else:
          # Python 命名约定
          return 15.0 if not symbol.name.startswith("_") else 5.0
  ```

- [ ] **Task 1.1.2.3**: 验证测试通过 (15min)
  ```bash
  pytest tests/test_symbol_scorer.py::TestVisibilityScoring -v
  ```

- [ ] **Task 1.1.2.4**: 代码审查和优化 (20min)

### Git Workflow

```bash
git checkout develop
git checkout -b feature/scorer-visibility

# TDD: Red → Green → Refactor

git commit -m "feat(scorer): implement visibility scoring

- Add _score_visibility() method
- Support PHP visibility keywords (public/protected/private)
- Support Python naming conventions (_prefix)
- Add 6 comprehensive test cases

Tests: 6/6 passing
Coverage: 92%

Closes #STORY-1.1.2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git checkout develop
git merge --no-ff feature/scorer-visibility
```

---

## 📋 Story 1.1.3: 实现语义重要性评分

### Story Card

```
ID: STORY-1.1.3
Title: 实现语义重要性评分
Epic: 智能符号选择系统
Priority: P0
Points: 3
Depends: STORY-1.1.1
```

### User Story

```
作为用户
我希望关键业务方法（如pay、createOrder）优先显示
以便快速定位核心功能
```

### Acceptance Criteria

- [ ] AC1: 实现 `_score_semantics()` 方法
- [ ] AC2: 定义 CRITICAL_KEYWORDS 列表（至少15个）
- [ ] AC3: 核心关键词匹配得分 +25
- [ ] AC4: 定义 SECONDARY_KEYWORDS 列表（至少5个）
- [ ] AC5: 次要关键词匹配得分 +15
- [ ] AC6: 普通方法得分 +5
- [ ] AC7: 关键词匹配不区分大小写

### Test Cases (TDD)

```python
class TestSemanticScoring:
    """测试语义重要性评分"""

    @pytest.fixture
    def scorer(self):
        return SymbolImportanceScorer()

    @pytest.mark.parametrize("method_name,expected_score", [
        ("pay", 25.0),
        ("createOrder", 25.0),
        ("updateUser", 25.0),
        ("deleteProduct", 25.0),
        ("processPayment", 25.0),
        ("handleNotify", 25.0),
        ("validateSign", 25.0),
    ])
    def test_critical_keywords_high_score(self, scorer, method_name, expected_score):
        """核心关键词获得高分"""
        symbol = Symbol(
            name=method_name,
            kind="method",
            signature=f"public function {method_name}()"
        )
        score = scorer._score_semantics(symbol)
        assert score == expected_score

    @pytest.mark.parametrize("method_name,expected_score", [
        ("findUser", 15.0),
        ("searchProducts", 15.0),
        ("listOrders", 15.0),
        ("showDetails", 15.0),
    ])
    def test_secondary_keywords_medium_score(self, scorer, method_name, expected_score):
        """次要关键词获得中等分数"""
        symbol = Symbol(
            name=method_name,
            kind="method",
            signature=f"public function {method_name}()"
        )
        score = scorer._score_semantics(symbol)
        assert score == expected_score

    def test_generic_method_low_score(self, scorer):
        """普通方法获得低分"""
        symbol = Symbol(
            name="helper",
            kind="method",
            signature="public function helper()"
        )
        score = scorer._score_semantics(symbol)
        assert score == 5.0

    def test_case_insensitive_matching(self, scorer):
        """关键词匹配不区分大小写"""
        symbols = [
            Symbol(name="PAY", kind="method", signature="public function PAY()"),
            Symbol(name="Pay", kind="method", signature="public function Pay()"),
            Symbol(name="pay", kind="method", signature="public function pay()"),
        ]

        for symbol in symbols:
            score = scorer._score_semantics(symbol)
            assert score == 25.0
```

### Task Checklist

- [ ] **Task 1.1.3.1**: 编写测试用例 (1hr)
- [ ] **Task 1.1.3.2**: 定义 CRITICAL_KEYWORDS (30min)
- [ ] **Task 1.1.3.3**: 定义 SECONDARY_KEYWORDS (15min)
- [ ] **Task 1.1.3.4**: 实现 `_score_semantics()` (1hr)
- [ ] **Task 1.1.3.5**: 验证测试通过 (15min)

---

## 📋 更多 Story Cards...

（其他 Story Cards 遵循相同格式，包含详细的验收标准、测试用例和任务清单）

---

## 📊 Story Points 估算参考

| Points | 工作量 | 示例 |
|--------|--------|------|
| 1 | 1-2小时 | 简单配置、文档更新 |
| 2 | 2-4小时 | 单一功能实现 |
| 3 | 4-6小时 | 中等复杂度功能 |
| 5 | 1天 | 复杂功能或集成 |
| 8 | 1.5-2天 | 大型功能 |
| 13 | 3天+ | 需要拆分 |

---

## ✅ Story 完成检查清单

每个 Story 完成时，检查：

### 代码
- [ ] 所有 AC（验收标准）满足
- [ ] TDD 测试先行（Red → Green → Refactor）
- [ ] 单元测试全部通过
- [ ] 测试覆盖率 ≥90%
- [ ] Lint 检查通过
- [ ] 代码已格式化

### 文档
- [ ] Docstring 完整
- [ ] 复杂逻辑有注释
- [ ] 必要时更新 README

### 版本控制
- [ ] Commit message 符合规范
- [ ] PR 已创建和审查
- [ ] Feature 分支已合并到 develop
- [ ] 已删除 feature 分支

### 演示
- [ ] 功能可演示
- [ ] 向团队展示（可选）

---

## 🔗 相关文档

- [phase1-agile-plan.md](phase1-agile-plan.md) - Phase 1 完整规划
- [IMPROVEMENT_ROADMAP.md](improvement-roadmap.md) - 改进路线图
