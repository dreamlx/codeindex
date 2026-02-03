# Epic 4: 代码重构优化 (Code Refactoring)

**Epic ID**: Epic 4
**创建日期**: 2026-01-27
**优先级**: 高
**状态**: 规划中
**估算**: 2-3天

---

## 📋 Epic 概述

对 Epic 3.1 和 3.2 实现的代码进行重构优化，消除代码重复，改善模块组织，提升可维护性。

### 业务价值

- 降低维护成本
- 减少 bug 风险
- 提升代码可读性
- 为未来功能扩展打基础

### 成功标准

- ✅ 所有243个现有测试保持通过
- ✅ 消除 cli.py 中50+行代码重复
- ✅ cli.py 代码行数减少至少30%
- ✅ 新增的重构测试全部通过
- ✅ 代码质量评分从4/5提升到5/5

---

## 📊 Stories 分解

### Story 4.1: 提取 AI Enhancement 辅助模块 (P0)

**优先级**: P0 (最高)
**工作量**: 4小时
**依赖**: 无
**标签**: refactoring, code-duplication

#### 用户故事

```gherkin
作为一个开发者
我希望 multi-turn 执行逻辑被提取为独立函数
这样我可以在多处复用而不产生代码重复
```

#### 验收标准

- [ ] 创建 `src/codeindex/ai_helper.py` 模块
- [ ] 实现 `aggregate_parse_results()` 函数
- [ ] 实现 `execute_multi_turn_enhancement()` 函数
- [ ] scan 命令使用新函数
- [ ] scan-all 命令使用新函数
- [ ] 删除原有重复代码
- [ ] 所有现有测试通过
- [ ] 新增集成测试覆盖新函数

#### Tasks

##### Task 4.1.1: 编写 BDD Feature 文件
- 创建 `tests/features/ai_helper.feature`
- 定义 aggregate_parse_results 的 scenarios
- 定义 execute_multi_turn_enhancement 的 scenarios

##### Task 4.1.2: 实现 aggregate_parse_results (TDD)
- 编写单元测试（红灯）
- 实现函数（绿灯）
- 重构优化

##### Task 4.1.3: 实现 execute_multi_turn_enhancement (TDD)
- 编写单元测试（红灯）
- 实现函数（绿灯）
- 重构优化

##### Task 4.1.4: 重构 scan 命令
- 替换 lines 109-185 为新函数调用
- 运行测试验证
- 删除旧代码

##### Task 4.1.5: 重构 scan-all 命令
- 替换 enhance_with_ai 中的逻辑
- 运行测试验证
- 删除旧代码

##### Task 4.1.6: 集成测试
- 编写 BDD step definitions
- 运行所有 scenarios
- 验证端到端流程

---

### Story 4.2: 统一文件大小分类系统 (P1)

**优先级**: P1 (高)
**工作量**: 6小时
**依赖**: 无
**标签**: refactoring, consistency

#### 用户故事

```gherkin
作为一个开发者
我希望文件大小检测逻辑在所有模块中保持一致
这样我可以统一配置和维护阈值
```

#### 验收标准

- [ ] 创建 `src/codeindex/file_classifier.py` 模块
- [ ] 实现 `FileSizeClassifier` 类
- [ ] 支持配置化的阈值
- [ ] tech_debt 模块使用新分类器
- [ ] ai_enhancement 模块使用新分类器
- [ ] 删除硬编码常量
- [ ] 所有现有测试通过
- [ ] 新增分类器测试

#### Tasks

##### Task 4.2.1: 编写 BDD Feature 文件
- 创建 `tests/features/file_classifier.feature`
- 定义文件大小分类 scenarios
- 定义配置化阈值 scenarios

##### Task 4.2.2: 实现 FileSizeClassifier (TDD)
- 编写单元测试（红灯）
- 实现分类逻辑（绿灯）
- 重构优化

##### Task 4.2.3: 集成到 tech_debt 模块
- 替换硬编码常量
- 更新相关测试
- 验证功能一致性

##### Task 4.2.4: 集成到 ai_enhancement 模块
- 替换现有检测逻辑
- 更新相关测试
- 验证功能一致性

##### Task 4.2.5: BDD 集成测试
- 编写 step definitions
- 运行所有 scenarios
- 验证配置化工作正常

---

### Story 4.3: 拆分 CLI 模块 (P2)

**优先级**: P2 (中)
**工作量**: 1-2天
**依赖**: Story 4.1, 4.2
**标签**: refactoring, modularity

#### 用户故事

```gherkin
作为一个开发者
我希望 CLI 模块按命令拆分为独立文件
这样我可以更容易地定位和维护每个命令
```

#### 验收标准

- [ ] 创建 `src/codeindex/cli/` 目录结构
- [ ] 拆分 scan 命令到 `cli/scan.py`
- [ ] 拆分 scan-all 命令到 `cli/scan_all.py`
- [ ] 拆分 tech-debt 命令到 `cli/tech_debt_cmd.py`
- [ ] 提取共享辅助函数到 `cli/helpers.py`
- [ ] 更新导入和入口点
- [ ] cli.py 代码行数 < 300行
- [ ] 所有现有测试通过

#### Tasks

##### Task 4.3.1: 设计模块结构
- 定义文件组织方案
- 规划函数迁移清单
- 识别共享依赖

##### Task 4.3.2: 创建 cli 包结构
- 创建目录和 __init__.py
- 设置入口点
- 配置导入路径

##### Task 4.3.3: 迁移 scan 命令 (TDD)
- 创建 cli/scan.py
- 迁移函数和测试
- 验证功能

##### Task 4.3.4: 迁移 scan-all 命令 (TDD)
- 创建 cli/scan_all.py
- 迁移函数和测试
- 验证功能

##### Task 4.3.5: 迁移其他命令
- 迁移 tech-debt, symbols, status, init
- 更新测试
- 验证所有命令

##### Task 4.3.6: 提取共享辅助函数
- 创建 cli/helpers.py
- 迁移共享函数
- 更新所有调用点

##### Task 4.3.7: 清理和验证
- 删除旧 cli.py（保留最小入口）
- 运行所有测试
- 验证命令行工具

---

## 🧪 测试策略

### BDD Feature 文件

#### 1. tests/features/ai_helper.feature
```gherkin
Feature: AI Enhancement Helper Functions

  Scenario: Aggregate multiple parse results
    Given multiple parse results from different files
    When I aggregate them into one
    Then the result should contain all symbols
    And the total line count should be summed

  Scenario: Execute multi-turn enhancement with auto-detection
    Given a super large file with 6000 lines
    When I execute multi-turn enhancement with auto strategy
    Then it should detect the file as super large
    And it should use multi-turn dialogue
    And it should return success with README content

  Scenario: Execute multi-turn with standard strategy override
    Given a super large file with 6000 lines
    When I execute multi-turn enhancement with standard strategy
    Then it should skip multi-turn detection
    And it should return failure
    And the caller should use standard enhancement

  Scenario: Multi-turn fallback on failure
    Given a file that causes multi-turn to fail
    When I execute multi-turn enhancement
    Then it should return failure with error message
    And the caller should fall back to standard enhancement
```

#### 2. tests/features/file_classifier.feature
```gherkin
Feature: Unified File Size Classification

  Scenario: Classify tiny file
    Given a Python file with 300 lines and 10 symbols
    When I classify the file size
    Then it should be categorized as "tiny"

  Scenario: Classify super large file by line count
    Given a PHP file with 6000 lines and 50 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And the reason should be "excessive_lines"

  Scenario: Classify super large file by symbol count
    Given a Python file with 3000 lines and 120 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And the reason should be "excessive_symbols"

  Scenario: Use custom thresholds from config
    Given custom thresholds with super_large_lines=3000
    And a file with 3500 lines
    When I classify the file size
    Then it should respect the custom threshold
    And be categorized as "super_large"

  Scenario: Tech debt module uses classifier
    Given a file for tech debt analysis
    When I analyze technical debt
    Then it should use FileSizeClassifier
    And not use hard-coded constants

  Scenario: AI enhancement module uses classifier
    Given a file for AI enhancement
    When I select enhancement strategy
    Then it should use FileSizeClassifier
    And detection should be consistent with tech debt
```

#### 3. tests/features/cli_refactoring.feature
```gherkin
Feature: CLI Module Refactoring

  Scenario: Scan command uses ai_helper
    Given a directory to scan
    When I run "codeindex scan ./path"
    Then it should use execute_multi_turn_enhancement
    And not have duplicate detection logic

  Scenario: Scan-all command uses ai_helper
    Given multiple directories to scan
    When I run "codeindex scan-all"
    Then it should use execute_multi_turn_enhancement
    And share the same logic as scan command

  Scenario: CLI commands are in separate modules
    Given the CLI package structure
    Then scan command should be in cli/scan.py
    And scan-all command should be in cli/scan_all.py
    And tech-debt command should be in cli/tech_debt_cmd.py
    And each module should be < 400 lines
```

---

## 📅 Sprint 计划

### Sprint 1: 核心重构 (Day 1-2)

**目标**: 完成 Story 4.1 和 4.2

#### Day 1 上午
- ✅ Task 4.1.1: 编写 ai_helper BDD feature
- ✅ Task 4.1.2: TDD 实现 aggregate_parse_results

#### Day 1 下午
- ✅ Task 4.1.3: TDD 实现 execute_multi_turn_enhancement
- ✅ Task 4.1.4: 重构 scan 命令

#### Day 2 上午
- ✅ Task 4.1.5: 重构 scan-all 命令
- ✅ Task 4.1.6: AI helper 集成测试
- ✅ Task 4.2.1: 编写 file_classifier BDD feature

#### Day 2 下午
- ✅ Task 4.2.2: TDD 实现 FileSizeClassifier
- ✅ Task 4.2.3-4.2.4: 集成到 tech_debt 和 ai_enhancement
- ✅ Task 4.2.5: File classifier BDD 测试

---

### Sprint 2: 模块拆分 (Day 3-4) - 可选

**目标**: 完成 Story 4.3

#### Day 3
- Task 4.3.1-4.3.2: 设计和创建 cli 包
- Task 4.3.3: 迁移 scan 命令

#### Day 4
- Task 4.3.4-4.3.7: 迁移其他命令和清理

---

## 🎯 Definition of Done (DoD)

### Story 级别 DoD

- [ ] 所有 Tasks 完成
- [ ] BDD Feature 文件编写
- [ ] BDD Scenarios 全部通过
- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有243个现有测试通过
- [ ] 代码通过 ruff 检查
- [ ] 提交信息符合规范
- [ ] README_AI.md 自动更新

### Epic 级别 DoD

- [ ] 所有 Stories 完成
- [ ] 代码重复率 < 3%
- [ ] cli.py 代码行数 < 300行（如果完成 Story 4.3）
- [ ] 代码质量评分 5/5
- [ ] 重构分析报告更新
- [ ] CHANGELOG.md 更新
- [ ] 性能无退化
- [ ] 合并到 develop 分支

---

## 📊 度量指标

### 代码度量

| 指标 | 重构前 | 目标 | 实际 |
|------|--------|------|------|
| cli.py 行数 | 1131 | <300 (Story 4.3) / ~1050 (Story 4.1) | TBD |
| 代码重复行数 | 50+ | 0 | TBD |
| 平均函数复杂度 | 8.5 | <8 | TBD |
| 测试通过率 | 100% | 100% | TBD |
| 代码覆盖率 | 85% | >85% | TBD |

### 时间跟踪

| Story | 估算 | 实际 | 偏差 |
|-------|------|------|------|
| Story 4.1 | 4h | TBD | TBD |
| Story 4.2 | 6h | TBD | TBD |
| Story 4.3 | 2d | TBD | TBD |

---

## ⚠️ 风险评估

### 风险 1: 重构破坏现有功能

**概率**: 低
**影响**: 高
**缓解措施**:
- 243个现有测试提供安全网
- 每个 Task 后运行测试
- 小步重构，频繁验证

### 风险 2: 时间估算不准确

**概率**: 中
**影响**: 中
**缓解措施**:
- Story 4.3 标记为可选
- 优先完成 Story 4.1 和 4.2
- 时间不足可推迟到下个 Sprint

### 风险 3: 测试覆盖不足

**概率**: 低
**影响**: 中
**缓解措施**:
- BDD + TDD 双重保障
- 每个函数有单元测试
- 集成测试覆盖关键路径

---

## 🔄 回顾和改进

### 回顾问题

1. 为什么会产生代码重复？
2. 如何在未来避免类似问题？
3. 重构过程中学到了什么？

### 改进措施

1. 在 PR 时进行代码重复检查
2. 每个 Epic 完成后安排重构时间
3. 建立代码质量度量仪表板

---

**计划制定**: 2026-01-27
**计划审批**: 待定
**开始日期**: 2026-01-27
**目标完成**: 2026-01-29 (Story 4.1-4.2)
