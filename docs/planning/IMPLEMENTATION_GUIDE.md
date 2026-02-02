# Epic 3 实施指南

## 📋 文档概览

所有规划文档已完成，位于 `docs/planning/` 和 `docs/development/improvements/`：

### 核心规划文档
- ✅ `epic3-ai-enhancement-optimization.md` - 完整的Epic规划（11个Story）
- ✅ `tiered-ai-enhancement-strategy.md` - 分层策略设计
- ✅ `tech-debt-detection.md` - 技术债务检测详细设计
- ✅ `symbol-overload-detection.md` - 符号过载检测设计
- ✅ `exclude-patterns-deep-dive.md` - 符号过滤深度分析

### 诊断和分析文档
- ✅ `ai-enhancement-issues.md` - 问题深度分析
- ✅ `QUICK_START.md` - 快速修复指南
- ✅ `README.md` - 改进计划概览

---

## 🚀 敏捷实施流程

### Phase 1: Sprint Planning（本周一）

#### 1.1 创建 Sprint 1

```bash
# 创建Sprint文件夹
mkdir -p docs/sprints/sprint-1

# Sprint目标
cat > docs/sprints/sprint-1/SPRINT_GOALS.md << 'EOF'
# Sprint 1 Goals (Week 1-2)

## Sprint Objective
Complete Epic 3.1: Technical Debt Detection System

## Stories in Sprint
- [x] Story 3.1.1: File-level Debt Detection (1.5 days)
- [ ] Story 3.1.2: Symbol Overload Detection (2 days)
- [ ] Story 3.1.3: Technical Debt Report Generation (2.5 days)
- [ ] Story 3.1.4: CLI Integration (2.5 days)

## Definition of Done
- All unit tests pass (90%+ coverage)
- All BDD scenarios pass
- Code review completed
- Documentation updated
- User can run `codeindex tech-debt` and get a report

## Team Capacity
- Developer: 8 hours/day × 10 days = 80 hours
- Estimated work: 66 hours
- Buffer: 14 hours (17.5%)

## Daily Standup Schedule
- Time: 9:30 AM
- Format: What did I do? What will I do? Any blockers?
EOF
```

#### 1.2 创建Story卡片

为每个Story创建卡片文件：

```bash
# Story 3.1.1卡片
cat > docs/sprints/sprint-1/story-3.1.1-file-debt.md << 'EOF'
# Story 3.1.1: File-level Debt Detection

**Status**: 🟡 TODO → 🔵 IN PROGRESS → 🟢 DONE

## User Story
As a developer,
I want codeindex to detect super large files and God Classes,
So that I know which files need urgent refactoring.

## Acceptance Criteria
- [ ] Detect files >5000 lines as CRITICAL
- [ ] Detect classes with >50 methods as CRITICAL
- [ ] Detect files >2000 lines as HIGH
- [ ] Normal files pass without issues
- [ ] Suggestions are actionable and specific

## Tasks
- [ ] Create `DebtSeverity` enum
- [ ] Create `DebtIssue` dataclass
- [ ] Implement `TechDebtDetector` class skeleton
- [ ] Implement super large file detection
- [ ] Implement God Class detection
- [ ] Implement large file detection
- [ ] Write unit tests (90%+ coverage)
- [ ] Write BDD tests with pytest-bdd

## Test-First Approach

### Step 1: Write Failing Test (RED)
```python
def test_detect_super_large_file():
    # Arrange
    parse_result = create_mock_parse_result(file_lines=8891)
    detector = TechDebtDetector(config)

    # Act
    issues, _ = detector.analyze_file(parse_result, scorer)

    # Assert
    assert any(i.category == "super_large_file" for i in issues)
```

### Step 2: Implement Minimum Code (GREEN)
```python
class TechDebtDetector:
    def analyze_file(self, parse_result, scorer):
        issues = []
        if parse_result.file_lines > 5000:
            issues.append(DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                ...
            ))
        return issues, None
```

### Step 3: Refactor (REFACTOR)
- Extract magic numbers to constants
- Add docstrings
- Improve naming

## BDD Scenarios
```gherkin
Feature: File-level Technical Debt Detection
  Scenario: Detect super large file
    Given a PHP file with 8891 lines
    When I run codeindex scan
    Then it should report a CRITICAL issue
```

## Definition of Done
- [x] All tests pass (both TDD and BDD)
- [x] Code coverage ≥ 90%
- [x] Code review approved
- [x] Documentation updated
- [x] Integrated with main codebase

## Estimate
12 hours (1.5 days)

## Actual Time
_To be filled after completion_

## Notes
_Add any learnings, blockers, or decisions here_
EOF
```

---

### Phase 2: TDD/BDD 开发循环

#### 2.1 TDD Red-Green-Refactor

**每个功能都遵循：**

```python
# ========== RED: 写失败的测试 ==========
# tests/test_tech_debt_detector.py

def test_detect_super_large_file():
    """Should detect files >5000 lines as CRITICAL"""
    # Arrange
    parse_result = create_mock_parse_result(file_lines=8891, symbols=57)
    detector = TechDebtDetector(config)

    # Act
    issues, _ = detector.analyze_file(parse_result, scorer)

    # Assert
    critical = [i for i in issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical) >= 1
    assert any(i.category == "super_large_file" for i in critical)

# 运行测试
pytest tests/test_tech_debt_detector.py::test_detect_super_large_file -v
# 预期：FAILED (因为还没实现)


# ========== GREEN: 实现最小代码使测试通过 ==========
# src/codeindex/tech_debt.py

from enum import Enum
from dataclasses import dataclass

class DebtSeverity(Enum):
    CRITICAL = "🔴🔴 CRITICAL"
    HIGH = "🔴 HIGH"
    MEDIUM = "🟠 MEDIUM"
    LOW = "🟡 LOW"

@dataclass
class DebtIssue:
    severity: DebtSeverity
    category: str
    file_path: Path
    metric_value: float
    threshold: float
    description: str
    suggestion: str

class TechDebtDetector:
    def __init__(self, config):
        self.config = config

    def analyze_file(self, parse_result, scorer):
        issues = []

        # 检测超大文件
        if parse_result.file_lines > 5000:
            issues.append(DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=parse_result.path,
                metric_value=parse_result.file_lines,
                threshold=5000,
                description=f"Extremely large file ({parse_result.file_lines} lines)",
                suggestion="URGENT: Split into smaller files"
            ))

        return issues, None

# 运行测试
pytest tests/test_tech_debt_detector.py::test_detect_super_large_file -v
# 预期：PASSED ✅


# ========== REFACTOR: 重构优化 ==========
# 提取常量
SUPER_LARGE_FILE_THRESHOLD = 5000

# 提取方法
def _detect_file_size_issues(self, parse_result):
    issues = []
    if parse_result.file_lines > SUPER_LARGE_FILE_THRESHOLD:
        issues.append(self._create_super_large_file_issue(parse_result))
    return issues

# 运行所有测试确保重构没有破坏功能
pytest tests/test_tech_debt_detector.py -v
```

#### 2.2 BDD Given-When-Then

**使用 pytest-bdd：**

```python
# tests/features/tech_debt.feature

Feature: File-level Technical Debt Detection
  As a developer
  I want to detect large files automatically
  So that I can prioritize refactoring

  Scenario: Detect super large file
    Given a PHP file with 8891 lines
    When I run technical debt analysis
    Then it should report a CRITICAL severity issue
    And the category should be "super_large_file"
    And the description should mention "8891 lines"

  Scenario: Normal file passes
    Given a PHP file with 300 lines
    When I run technical debt analysis
    Then no critical issues should be reported


# tests/test_tech_debt_bdd.py

from pytest_bdd import scenarios, given, when, then, parsers

scenarios('features/tech_debt.feature')

@given(parsers.parse('a PHP file with {lines:d} lines'))
def php_file_with_lines(lines):
    return create_mock_parse_result(file_lines=lines)

@when('I run technical debt analysis')
def run_analysis(php_file_with_lines):
    detector = TechDebtDetector(Config.load())
    issues, _ = detector.analyze_file(php_file_with_lines, SymbolImportanceScorer())
    return issues

@then('it should report a CRITICAL severity issue')
def check_critical_issue(run_analysis):
    issues = run_analysis
    critical = [i for i in issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical) >= 1

@then(parsers.parse('the category should be "{category}"'))
def check_category(run_analysis, category):
    issues = run_analysis
    assert any(i.category == category for i in issues)

# 运行BDD测试
pytest tests/test_tech_debt_bdd.py --gherkin-terminal-reporter
```

---

### Phase 3: Daily Workflow

#### 每日工作流程

```bash
# ========== 早上 9:00 ==========

# 1. 拉取最新代码
git checkout develop
git pull origin develop

# 2. 切换到feature分支
git checkout feature/epic3-ai-optimization
git rebase develop

# 3. 查看今天的Story卡片
cat docs/sprints/sprint-1/story-3.1.1-file-debt.md


# ========== 9:30 Daily Standup ==========

# 回答三个问题：
# 1. 昨天做了什么？
#    - 完成了DebtSeverity enum和DebtIssue dataclass
#    - 写了3个单元测试
# 2. 今天计划做什么？
#    - 实现God Class检测
#    - 写BDD测试
# 3. 有什么障碍？
#    - 需要确认God Class的阈值（50个方法还是30个？）


# ========== 10:00 开始编码（TDD循环）==========

# Cycle 1: God Class检测
# 1. RED: 写测试
vim tests/test_tech_debt_detector.py
# 添加 test_detect_god_class()

pytest tests/test_tech_debt_detector.py::test_detect_god_class -v
# FAILED ❌

# 2. GREEN: 实现
vim src/codeindex/tech_debt.py
# 添加God Class检测逻辑

pytest tests/test_tech_debt_detector.py::test_detect_god_class -v
# PASSED ✅

# 3. REFACTOR: 优化
# 提取常量，改进命名

pytest tests/test_tech_debt_detector.py -v
# ALL PASSED ✅


# ========== 12:00 午餐 ==========


# ========== 13:00 继续编码 ==========

# Cycle 2: 大文件检测
# 重复TDD循环...


# ========== 15:00 写BDD测试 ==========

vim tests/features/tech_debt.feature
# 添加新场景

pytest tests/test_tech_debt_bdd.py --gherkin-terminal-reporter
# PASSED ✅


# ========== 16:30 提交代码 ==========

# 1. 运行完整测试套件
pytest tests/ -v --cov=src/codeindex --cov-report=term-missing

# 2. 代码规范检查
ruff check src/

# 3. 提交
git add src/codeindex/tech_debt.py tests/
git commit -m "feat(tech-debt): implement file-level debt detection

- Add DebtSeverity enum and DebtIssue dataclass
- Implement super large file detection (>5000 lines)
- Implement God Class detection (>50 methods)
- Add 8 unit tests and 3 BDD scenarios
- Test coverage: 95%

Story: 3.1.1
Tests: pytest tests/test_tech_debt_detector.py -v"

# 4. 推送
git push origin feature/epic3-ai-optimization


# ========== 17:00 更新Story卡片 ==========

# 更新进度
vim docs/sprints/sprint-1/story-3.1.1-file-debt.md

# 标记完成的任务：
# - [x] Create `DebtSeverity` enum
# - [x] Create `DebtIssue` dataclass
# - [x] Implement super large file detection
# - [x] Implement God Class detection
# - [ ] Implement large file detection (明天继续)


# ========== 17:30 下班 ==========
```

---

### Phase 4: Story 完成检查清单

#### 每个Story完成前检查：

```markdown
## Story 3.1.1 完成检查清单

### 代码质量
- [x] 所有单元测试通过
- [x] 测试覆盖率 ≥ 90%
- [x] 所有BDD场景通过
- [x] Ruff检查无错误
- [x] 类型提示正确

### 功能完整性
- [x] 所有验收标准满足
- [x] 边界情况已测试
- [x] 错误处理完善
- [x] 日志记录充分

### 文档
- [x] Docstring完整
- [x] README更新（如需要）
- [x] CHANGELOG更新
- [x] Story卡片更新

### 集成
- [x] 与现有代码集成
- [x] 不破坏现有测试
- [x] API文档更新（如有）

### Review
- [ ] Self-review完成
- [ ] Code review请求已发送
- [ ] Review意见已处理
- [ ] 合并到develop分支

### 演示
- [ ] 准备演示材料
- [ ] 在真实项目上验证
- [ ] 截图/录屏演示
```

---

### Phase 5: Sprint Review & Retrospective

#### Sprint结束时（Week 2 Friday）

```bash
# ========== Sprint Review ==========

# 1. 演示完成的功能
python demos/demo_tech_debt_detection.py

# 2. 展示指标
cat docs/sprints/sprint-1/SPRINT_METRICS.md

# Sprint 1 Metrics:
# - Stories Completed: 4/4 (100%)
# - Story Points: 66/66 (100%)
# - Test Coverage: 92%
# - Bugs Found: 2 (已修复)
# - Velocity: 66 points/2 weeks


# ========== Sprint Retrospective ==========

# What went well?
# - TDD流程运作良好，发现了3个边界case
# - BDD测试帮助澄清了需求
# - 每日standup保持团队同步

# What could be improved?
# - 估算略有偏差（God Class检测多花了2小时）
# - 需要更早进行code review

# Action items for next sprint:
# - 每天下午3点进行peer code review
# - 复杂Story拆分更细


# ========== 准备下一个Sprint ==========

# 创建Sprint 2
mkdir -p docs/sprints/sprint-2

# 规划Epic 3.2 Stories
...
```

---

## 📊 进度跟踪工具

### 使用GitHub Project Board

```markdown
## Epic 3: AI Enhancement Optimization

### Backlog
- [ ] Story 3.1.1: File-level Debt Detection
- [ ] Story 3.1.2: Symbol Overload Detection
- [ ] Story 3.1.3: Report Generation
- [ ] Story 3.1.4: CLI Integration

### In Progress
- [x] Story 3.1.1 (Day 1-2)

### Review
-

### Done
-
```

### 使用简单的看板

```bash
# 创建看板文件
cat > docs/sprints/KANBAN.md << 'EOF'
# Sprint 1 Kanban Board

## TODO
- Story 3.1.2 (2d)
- Story 3.1.3 (2.5d)
- Story 3.1.4 (2.5d)

## IN PROGRESS
- Story 3.1.1 (1.5d) - @developer - Day 1/2

## REVIEW
-

## DONE
-

Last Updated: 2026-01-27
EOF
```

---

## ✅ 准备开始

### 现在可以开始了！

```bash
# 1. 创建feature分支
git checkout -b feature/epic3-ai-optimization

# 2. 创建Sprint 1文件夹
mkdir -p docs/sprints/sprint-1

# 3. 复制Story卡片模板
# (使用上面提供的模板)

# 4. 安装pytest-bdd（如果还没有）
pip install pytest-bdd

# 5. 开始第一个Story
echo "Starting Story 3.1.1: File-level Debt Detection"
echo "Test-first approach: Write failing test first!"

# 6. 创建测试文件
touch tests/test_tech_debt_detector.py
vim tests/test_tech_debt_detector.py
```

---

## 📚 相关资源

### 开发文档
- TDD: https://testdriven.io/
- BDD: https://cucumber.io/docs/bdd/
- pytest-bdd: https://pytest-bdd.readthedocs.io/

### 项目文档
- Epic规划: `docs/planning/epic3-ai-enhancement-optimization.md`
- 技术设计: `docs/development/improvements/`
- API文档: `docs/api/`

### 模板
- Story卡片: 见上文
- 测试模板: `tests/test_template.py`
- BDD Feature: `tests/features/template.feature`

---

**准备好了吗？Let's start with Story 3.1.1! 🚀**

记住三个原则：
1. **Test First** - 先写测试，再写实现
2. **Small Steps** - 小步前进，频繁提交
3. **Keep It Simple** - KISS原则，简单优于复杂
