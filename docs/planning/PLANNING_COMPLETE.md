# 📋 Epic 3 规划完成

## ✅ 完成状态

所有规划文档已完成，可以开始敏捷实施！

### 核心文档清单

| 文档 | 位置 | 状态 | 用途 |
|------|------|------|------|
| **Epic 3 完整规划** | `docs/planning/epic3-ai-enhancement-optimization.md` | ✅ | 11个Story的完整规划（TDD/BDD） |
| **实施指南** | `docs/planning/IMPLEMENTATION_GUIDE.md` | ✅ | 逐步实施说明和工作流程 |
| **分层策略** | `docs/development/improvements/tiered-ai-enhancement-strategy.md` | ✅ | 技术方案设计 |
| **技术债务检测** | `docs/development/improvements/tech-debt-detection.md` | ✅ | 债务检测详细设计 |
| **符号过载分析** | `docs/development/improvements/symbol-overload-detection.md` | ✅ | 符号过载检测设计 |
| **问题深度分析** | `docs/development/improvements/ai-enhancement-issues.md` | ✅ | 根因分析和解决方案 |
| **快速修复指南** | `docs/development/improvements/QUICK_START.md` | ✅ | 临时解决方案 |

---

## 📊 Epic 3 概览

### 三个子Epic

| Epic | Story数 | 工作量 | 优先级 | 目标 |
|------|---------|--------|--------|------|
| **3.1 技术债务检测** | 4 | 66h (2周) | 🔥🔥🔥🔥🔥 | 识别代码质量问题 |
| **3.2 多轮对话增强** | 4 | 49h (2周) | 🔥🔥🔥🔥🔥 | 处理超大文件 |
| **3.3 层次化Prompt** | 3 | 35h (1周) | 🔥🔥🔥 | 优化中大文件 |

**总计**: 11 Stories, 150 hours (5周)

### 成功指标

| 指标 | 当前 | 目标 | 测量方式 |
|------|------|------|---------|
| AI成功率 | 50% | 90% | 成功目录 / 总目录 |
| README质量 | 6/10 | 9/10 | 用户评分 |
| 大文件成功率 | 10% | 90% | >5000行文件成功率 |
| 技术债务可见性 | 0% | 100% | 有报告的项目占比 |
| 测试覆盖率 | 75% | 90% | pytest --cov |

---

## 🎯 Epic 3.1 详细计划（第一个Sprint）

### Story分解

#### Story 3.1.1: File-level Debt Detection (1.5天)
**验收标准**：
- ✅ 检测超大文件（>5000行）→ CRITICAL
- ✅ 检测God Class（>50方法）→ CRITICAL
- ✅ 检测大文件（>2000行）→ HIGH
- ✅ 提供可执行的重构建议

**测试要求**：
- 8个单元测试
- 3个BDD场景
- 覆盖率 >90%

#### Story 3.1.2: Symbol Overload Detection (2天)
**验收标准**：
- ✅ 检测符号总数过多（>100）
- ✅ 检测噪音比例高（>50%）
- ✅ 分析噪音来源（getter/setter/private）
- ✅ 计算代码质量分数

**测试要求**：
- 12个单元测试
- 4个BDD场景
- 覆盖率 >90%

#### Story 3.1.3: Report Generation (2.5天)
**验收标准**：
- ✅ 生成完整的Markdown报告
- ✅ 包含执行摘要
- ✅ 包含严重问题详情
- ✅ 包含重构优先级列表
- ✅ 包含符号质量分析

**测试要求**：
- 10个单元测试
- 4个BDD场景
- 报告格式验证

#### Story 3.1.4: CLI Integration (2.5天)
**验收标准**：
- ✅ `codeindex tech-debt` 命令工作
- ✅ `scan-all` 集成债务检测
- ✅ README中显示质量警告
- ✅ 用户友好的输出

**测试要求**：
- 8个CLI测试
- 3个集成测试
- 端到端测试

---

## 🚀 开始实施

### Step 1: 环境准备（今天）

```bash
# 1. 创建feature分支
git checkout develop
git pull origin develop
git checkout -b feature/epic3-ai-optimization

# 2. 安装依赖
pip install pytest-bdd pytest-cov

# 3. 创建Sprint文件夹
mkdir -p docs/sprints/sprint-1

# 4. 验证测试环境
pytest tests/ -v
# 应该看到135个测试全部通过
```

### Step 2: 第一个Story（明天开始）

```bash
# 1. 阅读Story卡片
cat docs/planning/epic3-ai-enhancement-optimization.md
# 找到Story 3.1.1的详细说明

# 2. 创建测试文件
touch tests/test_tech_debt_detector.py

# 3. 写第一个失败的测试（RED）
vim tests/test_tech_debt_detector.py

def test_detect_super_large_file():
    """Should detect files >5000 lines as CRITICAL"""
    # Arrange
    parse_result = create_mock_parse_result(file_lines=8891)
    detector = TechDebtDetector(config)

    # Act
    issues, _ = detector.analyze_file(parse_result, scorer)

    # Assert
    assert any(i.category == "super_large_file" for i in issues)

# 4. 运行测试（应该失败）
pytest tests/test_tech_debt_detector.py::test_detect_super_large_file -v
# FAILED - TechDebtDetector not found ✅ 预期失败

# 5. 实现最小代码（GREEN）
touch src/codeindex/tech_debt.py
vim src/codeindex/tech_debt.py
# 实现TechDebtDetector...

# 6. 运行测试（应该通过）
pytest tests/test_tech_debt_detector.py::test_detect_super_large_file -v
# PASSED ✅

# 7. 重复TDD循环，完成所有功能...
```

### Step 3: 每日工作流程

```bash
# 早上 9:30 - Daily Standup
# 回答三个问题：
# 1. 昨天做了什么？
# 2. 今天计划做什么？
# 3. 有什么障碍？

# 白天 - TDD/BDD 开发循环
# RED → GREEN → REFACTOR
# 重复多次

# 下午 16:30 - 提交代码
git add .
git commit -m "feat(tech-debt): implement XXX"
git push origin feature/epic3-ai-optimization

# 下午 17:00 - 更新进度
# 更新Story卡片和看板
```

---

## 📚 TDD/BDD 示例

### TDD Example

```python
# tests/test_tech_debt_detector.py

import pytest
from pathlib import Path
from codeindex.tech_debt import TechDebtDetector, DebtSeverity
from codeindex.parser import ParseResult

class TestTechDebtDetector:
    """Test technical debt detection"""

    def test_detect_super_large_file(self):
        """Should detect files >5000 lines as CRITICAL"""
        # Arrange
        parse_result = ParseResult(
            path=Path("huge.php"),
            file_lines=8891,
            symbols=[],
        )
        detector = TechDebtDetector(config)

        # Act
        issues, _ = detector.analyze_file(parse_result, scorer)

        # Assert
        critical = [i for i in issues if i.severity == DebtSeverity.CRITICAL]
        assert len(critical) >= 1
        assert any(i.category == "super_large_file" for i in critical)
        assert any(8891 in str(i.description) for i in issues)

    def test_normal_file_no_issues(self):
        """Normal files should pass without issues"""
        # Arrange
        parse_result = ParseResult(
            path=Path("normal.php"),
            file_lines=300,
            symbols=[create_mock_symbol(f"m{i}") for i in range(15)]
        )
        detector = TechDebtDetector(config)

        # Act
        issues, _ = detector.analyze_file(parse_result, scorer)

        # Assert
        size_issues = [i for i in issues if "large" in i.category]
        assert len(size_issues) == 0
```

### BDD Example

```gherkin
# tests/features/tech_debt.feature

Feature: Technical Debt Detection
  As a developer
  I want to detect technical debt automatically
  So that I can prioritize refactoring work

  Scenario: Detect super large file
    Given a PHP file with 8891 lines
    When I analyze technical debt
    Then it should report a CRITICAL issue
    And the category should be "super_large_file"
    And the suggestion should recommend splitting the file

  Scenario: Normal file passes check
    Given a PHP file with 300 lines
    When I analyze technical debt
    Then no critical issues should be reported
```

```python
# tests/test_tech_debt_bdd.py

from pytest_bdd import scenarios, given, when, then, parsers

scenarios('features/tech_debt.feature')

@given(parsers.parse('a PHP file with {lines:d} lines'))
def php_file(lines):
    return ParseResult(
        path=Path("test.php"),
        file_lines=lines,
        symbols=[]
    )

@when('I analyze technical debt')
def analyze_debt(php_file):
    detector = TechDebtDetector(Config.load())
    issues, _ = detector.analyze_file(php_file, SymbolImportanceScorer())
    return issues

@then('it should report a CRITICAL issue')
def check_critical(analyze_debt):
    issues = analyze_debt
    critical = [i for i in issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical) >= 1
```

---

## 📈 进度跟踪

### 每日更新

在 `docs/sprints/sprint-1/DAILY_LOG.md` 中记录：

```markdown
# Sprint 1 Daily Log

## Day 1 (2026-01-28)
### Completed
- ✅ Created feature branch
- ✅ Setup test environment
- ✅ Implemented DebtSeverity enum
- ✅ Wrote 3 unit tests

### In Progress
- 🔵 Story 3.1.1: File-level Detection (50%)

### Blockers
- None

### Tomorrow
- Complete God Class detection
- Write BDD tests

---

## Day 2 (2026-01-29)
### Completed
- ✅ God Class detection implemented
- ✅ 5 BDD scenarios passing

### In Progress
- 🔵 Story 3.1.1: File-level Detection (90%)

### Blockers
- None

### Tomorrow
- Complete Story 3.1.1
- Start Story 3.1.2
```

---

## ✅ Definition of Done

### Story Level

每个Story完成需满足：
- [ ] 所有验收标准满足
- [ ] 所有单元测试通过（覆盖率≥90%）
- [ ] 所有BDD场景通过
- [ ] Ruff检查无错误
- [ ] Docstring完整
- [ ] Code review通过
- [ ] 在真实项目上验证
- [ ] 文档更新

### Epic Level

Epic 3完成需满足：
- [ ] 所有Story完成
- [ ] 集成测试通过
- [ ] 用户验收测试通过
- [ ] 性能基准满足
- [ ] 用户文档完整
- [ ] Release notes准备好

---

## 🎓 学习资源

### TDD
- [Test Driven Development by Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [pytest documentation](https://docs.pytest.org/)
- [Python TDD tutorial](https://testdriven.io/blog/modern-tdd/)

### BDD
- [Cucumber BDD Guide](https://cucumber.io/docs/bdd/)
- [pytest-bdd documentation](https://pytest-bdd.readthedocs.io/)
- [BDD in Action](https://www.manning.com/books/bdd-in-action)

### Agile
- [Scrum Guide](https://scrumguides.org/)
- [User Story Mapping](https://www.jpattonassociates.com/user-story-mapping/)
- [Agile Estimating and Planning](https://www.mountaingoatsoftware.com/books/agile-estimating-and-planning)

---

## 🚀 准备好了！

你现在拥有：
1. ✅ 完整的Epic规划（11个Story）
2. ✅ 详细的验收标准（BDD格式）
3. ✅ 完整的测试用例（TDD格式）
4. ✅ 逐步实施指南
5. ✅ 每日工作流程模板
6. ✅ 进度跟踪工具

**下一步**：开始 Story 3.1.1！

```bash
# 启动命令
git checkout -b feature/epic3-ai-optimization
mkdir -p docs/sprints/sprint-1
echo "Sprint 1 starts: $(date)" > docs/sprints/sprint-1/STARTED.txt

# Let's go! 🚀
pytest tests/ -v  # 确保一切就绪
```

---

**文档版本**: 1.0
**创建日期**: 2026-01-27
**状态**: ✅ READY FOR IMPLEMENTATION
**下一步**: Start Sprint 1, Story 3.1.1
