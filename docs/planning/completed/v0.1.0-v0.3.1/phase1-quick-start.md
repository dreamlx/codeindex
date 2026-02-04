# Phase 1 快速开始

立即开始 Phase 1 开发的快速指南。

---

## 🚀 5分钟快速开始

### 1. 初始化 develop 分支

```bash
cd /Users/dreamlinx/Dropbox/Projects/codeindex

# 确保在最新的 main
git checkout main
git pull origin main

# 创建 develop 分支
git checkout -b develop
git push -u origin develop

echo "✅ develop 分支已创建"
```

### 2. 开始第一个 Story

```bash
# 创建 feature 分支
git checkout -b feature/symbol-scorer-base

# 创建文件
touch src/codeindex/symbol_scorer.py
touch tests/test_symbol_scorer.py

echo "✅ 准备就绪，开始 TDD！"
```

### 3. TDD 第一个循环

**Red（编写测试）**：

```python
# tests/test_symbol_scorer.py
import pytest
from codeindex.symbol_scorer import SymbolImportanceScorer

def test_scorer_initialization():
    """测试评分器初始化"""
    scorer = SymbolImportanceScorer()
    assert scorer is not None
```

运行测试（应该失败）：
```bash
pytest tests/test_symbol_scorer.py -v
# ❌ ImportError: cannot import name 'SymbolImportanceScorer'
```

**Green（实现功能）**：

```python
# src/codeindex/symbol_scorer.py
"""Symbol importance scoring system."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ScoringContext:
    """Scoring context for symbols."""
    framework: str = "unknown"
    file_type: str = "unknown"
    total_symbols: int = 0

class SymbolImportanceScorer:
    """Score symbols by importance."""

    def __init__(self, context: Optional[ScoringContext] = None):
        self.context = context or ScoringContext()
```

运行测试（应该通过）：
```bash
pytest tests/test_symbol_scorer.py -v
# ✅ test_scorer_initialization PASSED
```

**Refactor（优化代码）**：

```bash
ruff format src/codeindex/symbol_scorer.py tests/test_symbol_scorer.py
ruff check src/codeindex/symbol_scorer.py tests/test_symbol_scorer.py
```

### 4. 提交代码

```bash
git add src/codeindex/symbol_scorer.py tests/test_symbol_scorer.py

git commit -m "feat(scorer): initial symbol scorer structure

- Create SymbolImportanceScorer class
- Add ScoringContext dataclass
- Add initial test

Tests: 1/1 passing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push -u origin feature/symbol-scorer-base

echo "✅ 第一个提交完成！"
```

---

## 📋 每日工作流程

### 早上开始工作

```bash
# 1. 更新代码
git checkout develop
git pull origin develop

# 2. 查看今天的 Story
cat docs/planning/phase1-agile-plan.md | grep "Day 1"

# 3. 创建或切换到 feature 分支
git checkout feature/symbol-scorer-base
# 或创建新分支
git checkout -b feature/scorer-visibility

# 4. 查看 Story 详情
cat docs/planning/phase1-story-cards.md | grep -A 50 "Story 1.1.1"
```

### TDD 开发循环

```bash
# Red: 编写测试
vim tests/test_symbol_scorer.py
pytest tests/test_symbol_scorer.py -v  # 应该失败 ❌

# Green: 实现功能
vim src/codeindex/symbol_scorer.py
pytest tests/test_symbol_scorer.py -v  # 应该通过 ✅

# Refactor: 优化代码
ruff format src/codeindex/symbol_scorer.py
ruff check src/codeindex/symbol_scorer.py
pytest tests/test_symbol_scorer.py -v  # 确保仍通过 ✅

# 提交
git add .
git commit -m "feat(scorer): <message>"
git push
```

### 完成 Story

```bash
# 1. 运行所有测试
pytest tests/test_symbol_scorer.py -v --cov=src/codeindex/symbol_scorer.py

# 2. 检查覆盖率
# Coverage: 95% ✅

# 3. Lint 检查
ruff check src/
ruff format src/

# 4. 合并到 develop
git checkout develop
git pull origin develop
git merge --no-ff feature/symbol-scorer-base
git push origin develop

# 5. 删除 feature 分支
git branch -d feature/symbol-scorer-base
git push origin --delete feature/symbol-scorer-base

echo "✅ Story 完成！"
```

### 晚上下班

```bash
# 1. 提交当前进度
git add .
git commit -m "wip: <progress description>"
git push

# 2. 更新 Story 状态
# 在 docs/planning/phase1-agile-plan.md 更新进度

# 3. 准备明天的工作
# 查看明天的 Story
```

---

## 📅 5天冲刺计划

### Day 1 (周一): 评分器基础 ⭐

**目标**: 完成评分器基础架构和核心评分维度

**任务清单**:
- [ ] 9:00-12:00: Story 1.1.1 - 评分器基础架构
  ```bash
  git checkout -b feature/symbol-scorer-base
  # TDD 实现 SymbolImportanceScorer 基础
  ```

- [ ] 13:00-15:00: Story 1.1.2 - 可见性评分
  ```bash
  git checkout develop
  git merge --no-ff feature/symbol-scorer-base
  git checkout -b feature/scorer-visibility
  # TDD 实现 _score_visibility()
  ```

- [ ] 15:00-18:00: Story 1.1.3 - 语义评分（部分）
  ```bash
  git checkout develop
  git merge --no-ff feature/scorer-visibility
  git checkout -b feature/scorer-semantics
  # TDD 实现 _score_semantics()
  ```

**下班检查**:
- [ ] 至少 2 个 Story 完成并合并到 develop
- [ ] 所有测试通过
- [ ] 代码已推送

---

### Day 2 (周二): 完成评分系统 ⭐⭐

**目标**: 完成所有评分维度

**任务清单**:
- [ ] 9:00-12:00: Story 1.1.3 完成 + Story 1.1.4
- [ ] 13:00-15:00: Story 1.1.5
- [ ] 15:00-18:00: Story 1.1.6

**下班检查**:
- [ ] 评分系统所有维度完成
- [ ] 端到端评分测试通过
- [ ] 所有 feature 合并到 develop

---

### Day 3 (周三): 集成 + 自适应配置 ⭐⭐

**目标**: 集成评分器，设计自适应配置

**任务清单**:
- [ ] 9:00-12:00: Story 1.2.1 - 集成评分器到 SmartWriter
- [ ] 13:00-16:00: Story 2.1.1 - 自适应配置设计
- [ ] 16:00-18:00: Story 2.1.2 - 配置加载

**下班检查**:
- [ ] SmartWriter 使用评分系统
- [ ] 自适应配置完成
- [ ] 集成测试通过

---

### Day 4 (周四): 自适应实现 ⭐⭐

**目标**: 实现自适应算法

**任务清单**:
- [ ] 9:00-11:00: Story 2.2.1 - 自适应算法
- [ ] 11:00-14:00: Story 2.2.2 - 密度调整
- [ ] 14:00-18:00: Story 2.2.3 - 集成到 SmartWriter

**下班检查**:
- [ ] 自适应算法完成
- [ ] SmartWriter 支持自适应
- [ ] 端到端测试通过

---

### Day 5 (周五): 验证和发布 ⭐⭐⭐

**目标**: 测试、文档、发布

**任务清单**:
- [ ] 9:00-11:00: 真实项目测试
  ```bash
  # 用 PHP 支付项目验证
  codeindex scan /path/to/php_project
  # 对比改进前后效果
  ```

- [ ] 11:00-13:00: 性能测试
  ```bash
  pytest tests/ --benchmark
  # 确保性能影响 <5%
  ```

- [ ] 14:00-16:00: 更新文档
  ```bash
  vim CHANGELOG.md
  vim README.md
  vim docs/evaluation/before-after.md
  ```

- [ ] 16:00-18:00: 发布流程
  ```bash
  # 创建 release 分支
  git checkout -b release/v1.1.0
  # 更新版本号
  # 合并到 main
  git tag v1.1.0
  git push origin v1.1.0
  ```

**下班检查**:
- [ ] 所有测试通过
- [ ] 文档更新完成
- [ ] v1.1.0 发布成功
- [ ] 🎉 Phase 1 完成！

---

## ⚡ 常用命令速查

### 开始工作

```bash
# 早上第一件事
cd ~/Dropbox/Projects/codeindex
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# 查看今天的任务
cat docs/planning/phase1-agile-plan.md | grep "Day X"
```

### TDD 循环

```bash
# Red
vim tests/test_symbol_scorer.py
pytest tests/test_symbol_scorer.py::test_name -v

# Green
vim src/codeindex/symbol_scorer.py
pytest tests/test_symbol_scorer.py::test_name -v

# Refactor
ruff format src/codeindex/
ruff check src/codeindex/
pytest tests/test_symbol_scorer.py -v
```

### 提交

```bash
git add .
git commit -m "feat(scorer): <message>

<details>

Tests: X/X passing
Coverage: XX%

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push
```

### 完成 Story

```bash
# 测试
pytest tests/test_symbol_scorer.py -v --cov

# 合并
git checkout develop
git merge --no-ff feature/my-feature
git push

# 清理
git branch -d feature/my-feature
```

---

## 📊 进度跟踪

### 每日站会（自我检查）

1. **昨天完成了什么？**
   - 查看 git log
   - 更新 Story 状态

2. **今天计划做什么？**
   - 查看 Sprint 计划
   - 确定优先级

3. **有什么阻碍吗？**
   - 技术难题
   - 需要澄清的需求

### Story 状态更新

在 `docs/planning/phase1-agile-plan.md` 更新：

```markdown
| Story | 状态 | 负责人 | 完成日期 |
|-------|------|--------|---------|
| 1.1.1 评分器基础 | ✅ 已完成 | You | 2026-01-27 |
| 1.1.2 可见性评分 | 🏗️ 进行中 | You | - |
| 1.1.3 语义评分 | 📝 待开始 | TBD | - |
```

---

## ✅ 每日检查清单

### 开始工作

- [ ] 拉取最新代码
- [ ] 查看今天的 Story
- [ ] 创建 feature 分支

### 开发过程

- [ ] TDD：先写测试
- [ ] 测试通过
- [ ] 代码格式化
- [ ] Lint 检查通过
- [ ] 定期提交

### 完成 Story

- [ ] 所有测试通过
- [ ] 覆盖率 ≥90%
- [ ] 合并到 develop
- [ ] 删除 feature 分支
- [ ] 更新 Story 状态

---

## 🔗 快速链接

- **规划文档**: [phase1-agile-plan.md](phase1-agile-plan.md)
- **Story 卡片**: [phase1-story-cards.md](phase1-story-cards.md)
- **Git 工作流**: [../development/gitflow-workflow.md](../development/gitflow-workflow.md)
- **改进路线图**: [improvement-roadmap.md](improvement-roadmap.md)

---

## 🎯 成功标准

### 必达目标

- [ ] 大文件符号数 ≥ 80
- [ ] 关键API覆盖率 ≥ 90%
- [ ] 噪音符号 < 15%
- [ ] Token增幅 < 20%
- [ ] 测试覆盖率 ≥ 90%
- [ ] 所有测试通过

### 质量目标

- [ ] 无 P0/P1 Bug
- [ ] PHP 项目验证通过
- [ ] 性能影响 <5%
- [ ] 文档完整

---

## 💬 遇到问题？

### 技术问题

1. 查看 Story 卡片的详细说明
2. 参考 `IMPROVEMENT_ROADMAP.md` 的实现细节
3. 查看相关测试用例

### 流程问题

1. 参考 `gitflow-workflow.md`
2. 检查提交规范
3. 查看最佳实践

---

**准备好了吗？让我们开始 Phase 1！** 🚀

```bash
# 第一步：初始化 develop
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop

# 第二步：开始第一个 Story
git checkout -b feature/symbol-scorer-base

# 开始 TDD！
```
