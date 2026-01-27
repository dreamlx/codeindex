# Story 4.3: CLI 模块拆分

**Epic**: 4 - Code Refactoring
**Story**: 4.3 - CLI Module Split
**Priority**: High
**Estimated Effort**: 10 hours
**Status**: Planning

---

## 📋 Story Overview

### 目标

将 1062 行的 `cli.py` 拆分为 5 个职责清晰的模块，每个模块 <300 lines，提升代码可维护性和可测试性。

### 背景

当前 `cli.py` 存在的问题：
- **文件过大**: 1062 lines（目标 <100 lines）
- **职责混杂**: 包含扫描、配置、符号索引、技术债务等多个领域
- **难以维护**: 13 个函数混在一个文件中
- **测试困难**: 功能耦合导致测试复杂度高

### 成功标准

- [x] cli.py 从 1062 lines 减少到 <100 lines
- [x] 创建 5 个新模块，每个职责单一
- [x] 所有 263 个现有测试通过
- [x] 所有 CLI 命令功能保持不变
- [x] 无循环导入或运行时错误
- [x] 代码质量 ≥4.5/5

---

## 🏗️ 架构设计

### 目标文件结构

```
src/codeindex/
├── cli.py              # <100 lines - 主入口和命令组
├── cli_common.py       # ~30 lines - 共享工具（console等）
├── cli_scan.py         # ~300 lines - 扫描命令
├── cli_config.py       # ~150 lines - 配置和状态命令
├── cli_symbols.py      # ~200 lines - 符号索引命令
└── cli_tech_debt.py    # ~250 lines - 技术债务命令
```

### 模块职责划分

#### 1. cli.py (<100 lines)
**职责**: 主入口和命令组织
**内容**:
- `main()` - Click 命令组
- 命令注册逻辑
- 版本信息

```python
@click.group()
def main():
    """codeindex CLI tool."""
    pass

# 注册子命令
from codeindex.cli_scan import scan, scan_all
from codeindex.cli_config import init, status, list_dirs
from codeindex.cli_symbols import index, symbols, affected
from codeindex.cli_tech_debt import tech_debt

main.add_command(scan)
main.add_command(scan_all)
main.add_command(init)
main.add_command(status)
main.add_command(list_dirs)
main.add_command(index)
main.add_command(symbols)
main.add_command(affected)
main.add_command(tech_debt)
```

#### 2. cli_common.py (~30 lines)
**职责**: 共享工具和常量
**内容**:
- `console` - rich.Console 实例
- 共享的辅助函数（如果需要）

```python
from rich.console import Console

console = Console()
```

#### 3. cli_scan.py (~300 lines)
**职责**: 代码扫描和 README 生成
**内容**:
- `scan()` - 扫描单个目录
- `scan_all()` - 扫描所有目录
- `process_with_smartwriter()` - SmartWriter 处理（从嵌套函数转为独立函数）
- `enhance_with_ai()` - AI 增强处理（从嵌套函数转为独立函数）

#### 4. cli_config.py (~150 lines)
**职责**: 配置管理和状态查询
**内容**:
- `init()` - 初始化配置文件
- `status()` - 查看索引状态
- `list_dirs()` - 列出可索引目录

#### 5. cli_symbols.py (~200 lines)
**职责**: 符号索引和依赖分析
**内容**:
- `index()` - 生成项目索引
- `symbols()` - 生成符号索引
- `affected()` - 依赖影响分析

#### 6. cli_tech_debt.py (~250 lines)
**职责**: 技术债务分析
**内容**:
- `tech_debt()` - 技术债务分析命令
- `_find_source_files()` - 查找源文件
- `_analyze_files()` - 分析文件
- `_format_and_output()` - 格式化输出

---

## 📝 Tasks Breakdown

### Task 4.3.0: 创建 BDD 特性文件和共享模块
**Estimated**: 1 hour
**Priority**: Highest（必须先完成）

**步骤**:
1. 创建 `tests/features/cli_module_split.feature`
2. 编写 BDD 场景（命令访问、注册、向后兼容）
3. 创建 `src/codeindex/cli_common.py`
4. 移动 `console` 到 cli_common.py
5. 更新 cli.py 导入 console

**验收条件**:
- [ ] BDD 特性文件包含所有关键场景
- [ ] cli_common.py 创建成功
- [ ] cli.py 导入 cli_common 无错误
- [ ] 运行 `codeindex --help` 正常

---

### Task 4.3.1: 提取 cli_tech_debt.py
**Estimated**: 2 hours
**Priority**: High（独立命令，风险最低）

**步骤**:
1. 创建 `src/codeindex/cli_tech_debt.py`
2. 移动 `tech_debt()` 及相关函数：
   - `tech_debt()`
   - `_find_source_files()`
   - `_analyze_files()`
   - `_format_and_output()`
3. 更新导入：从 cli_common 导入 console
4. 在 cli.py 中导入并注册 tech_debt 命令
5. 运行测试：`pytest tests/test_cli_tech_debt.py -v`

**验收条件**:
- [ ] cli_tech_debt.py 创建（~250 lines）
- [ ] `codeindex tech-debt --help` 可访问
- [ ] test_cli_tech_debt.py 所有测试通过
- [ ] cli.py 减少约 250 lines

**预期 cli.py 大小**: 1062 → ~810 lines

---

### Task 4.3.2: 提取 cli_config.py
**Estimated**: 2 hours
**Priority**: High

**步骤**:
1. 创建 `src/codeindex/cli_config.py`
2. 移动以下函数：
   - `init()`
   - `status()`
   - `list_dirs()`
3. 更新导入
4. 在 cli.py 中注册命令
5. 运行相关测试

**验收条件**:
- [ ] cli_config.py 创建（~150 lines）
- [ ] `codeindex init/status/list-dirs --help` 可访问
- [ ] 相关 CLI 测试通过
- [ ] cli.py 减少约 150 lines

**预期 cli.py 大小**: ~810 → ~660 lines

---

### Task 4.3.3: 提取 cli_symbols.py
**Estimated**: 2 hours
**Priority**: Medium

**步骤**:
1. 创建 `src/codeindex/cli_symbols.py`
2. 移动以下函数：
   - `index()`
   - `symbols()`
   - `affected()`
3. 更新导入
4. 在 cli.py 中注册命令
5. 运行相关测试

**验收条件**:
- [ ] cli_symbols.py 创建（~200 lines）
- [ ] `codeindex index/symbols/affected --help` 可访问
- [ ] 相关 CLI 测试通过
- [ ] cli.py 减少约 200 lines

**预期 cli.py 大小**: ~660 → ~460 lines

---

### Task 4.3.4: 提取 cli_scan.py
**Estimated**: 3 hours
**Priority**: High（核心功能，需特别谨慎）

**步骤**:
1. 创建 `src/codeindex/cli_scan.py`
2. 移动以下函数：
   - `scan()`
   - `scan_all()`
3. **处理嵌套函数**：
   - 将 `process_with_smartwriter` 转为独立函数
   - 将 `enhance_with_ai` 转为独立函数
   - 传递必要的参数（config, timeout 等）
4. 更新导入
5. 在 cli.py 中注册命令
6. **重点测试**：核心扫描功能测试

**验收条件**:
- [ ] cli_scan.py 创建（~300 lines）
- [ ] `codeindex scan/scan-all --help` 可访问
- [ ] 嵌套函数成功转换为独立函数
- [ ] 所有扫描相关测试通过
- [ ] cli.py 减少约 300 lines

**预期 cli.py 大小**: ~460 → ~160 lines

---

### Task 4.3.5: 清理和优化 cli.py
**Estimated**: 1 hour
**Priority**: Low（收尾工作）

**步骤**:
1. 删除 cli.py 中已移动的函数
2. 优化命令注册逻辑
3. 添加模块文档字符串
4. 运行完整测试套件
5. 运行代码质量检查

**验收条件**:
- [ ] cli.py 最终 <100 lines
- [ ] 只包含 main() 和命令注册
- [ ] 所有 263 测试通过
- [ ] `ruff check src/` 无错误
- [ ] 代码质量 ≥4.5/5

**最终 cli.py 大小**: <100 lines ✅

---

## 🧪 BDD Feature File

### Feature: CLI 模块拆分

```gherkin
Feature: CLI Module Split
  As a developer
  I want CLI commands organized in separate modules
  So that the code is more maintainable and testable

  Background:
    Given the codeindex CLI is installed
    And all modules are properly imported

  Scenario: Tech debt command is accessible
    When I run "codeindex tech-debt --help"
    Then the command should display help text
    And no import errors should occur

  Scenario: Config commands are accessible
    When I run "codeindex init --help"
    Then the command should display help text
    When I run "codeindex status --help"
    Then the command should display help text
    When I run "codeindex list-dirs --help"
    Then the command should display help text

  Scenario: Symbol commands are accessible
    When I run "codeindex index --help"
    Then the command should display help text
    When I run "codeindex symbols --help"
    Then the command should display help text
    When I run "codeindex affected --help"
    Then the command should display help text

  Scenario: Scan commands are accessible
    When I run "codeindex scan --help"
    Then the command should display help text
    When I run "codeindex scan-all --help"
    Then the command should display help text

  Scenario: All commands are registered with main
    When I run "codeindex --help"
    Then I should see all subcommands listed:
      | scan      |
      | scan-all  |
      | init      |
      | status    |
      | list-dirs |
      | index     |
      | symbols   |
      | affected  |
      | tech-debt |

  Scenario: Backward compatibility maintained
    Given the legacy CLI tests exist
    When I run all CLI tests
    Then all 263 tests should pass
    And no functionality should be broken

  Scenario: No circular imports
    When I import each CLI module
    Then no ImportError should occur
    And no circular dependency should exist

  Scenario: Console is shared across modules
    Given console is defined in cli_common
    When I use console in cli_tech_debt
    And I use console in cli_scan
    Then the same console instance should be used
    And output formatting should be consistent
```

---

## 🔍 风险分析

### 风险 1: 循环导入
**可能性**: Medium
**影响**: High
**缓解策略**:
- 使用 cli_common.py 作为共享层
- 严格单向依赖：cli.py → cli_*.py → cli_common.py
- 每次拆分后运行 `python -m codeindex.cli --help`

### 风险 2: Click 命令注册失败
**可能性**: Low
**影响**: High
**缓解策略**:
- 使用 `main.add_command()` 显式注册
- 写集成测试验证所有命令路径
- 测试 `codeindex <command> --help` 对所有命令

### 风险 3: 破坏现有测试
**可能性**: Medium
**影响**: High
**缓解策略**:
- 每次拆分后运行完整测试套件
- 特别关注 `tests/test_cli*.py`
- 保持函数签名和行为不变

### 风险 4: 嵌套函数丢失作用域
**可能性**: Medium
**影响**: Medium
**缓解策略**:
- 将嵌套函数转为独立函数，传递必要参数
- 仔细审查 `process_with_smartwriter` 和 `enhance_with_ai`
- 写单元测试验证独立函数行为

---

## 📊 预期成果

### 代码组织改进

| 指标 | 当前 | 目标 | 改进 |
|------|------|------|------|
| cli.py 大小 | 1062 lines | <100 lines | -91% |
| 模块数量 | 1 | 6 | +500% |
| 最大模块大小 | 1062 lines | <300 lines | -72% |
| 平均模块大小 | 1062 lines | ~180 lines | -83% |

### 代码质量提升

- **可读性**: 每个模块职责单一，更易理解
- **可维护性**: 模块隔离，修改影响范围小
- **可测试性**: 独立模块便于单元测试
- **可扩展性**: 新增命令只需创建新模块

### 测试覆盖

- 所有 263 个现有测试保持通过
- 新增 BDD 场景验证模块组织
- 集成测试确保命令可访问性

---

## 🚀 实施计划

### Phase 1: 准备阶段（1 hour）
- Task 4.3.0: 创建 BDD 特性文件和 cli_common.py

### Phase 2: 独立命令拆分（4 hours）
- Task 4.3.1: 提取 cli_tech_debt.py（最独立）
- Task 4.3.2: 提取 cli_config.py
- Task 4.3.3: 提取 cli_symbols.py

### Phase 3: 核心功能拆分（3 hours）
- Task 4.3.4: 提取 cli_scan.py（最复杂）

### Phase 4: 清理和验证（1 hour）
- Task 4.3.5: 清理和优化 cli.py

### Phase 5: 文档和发布（1 hour）
- 更新 CHANGELOG.md
- 更新 README_AI.md
- 更新 README.md

**总计**: 10 hours

---

## ✅ 定义完成 (Definition of Done)

Story 4.3 完成的标准：

- [ ] cli.py < 100 lines
- [ ] 创建 5 个新模块（cli_common, cli_scan, cli_config, cli_symbols, cli_tech_debt）
- [ ] 所有 263 个测试通过
- [ ] 所有 CLI 命令功能保持不变
- [ ] 无循环导入或运行时错误
- [ ] `ruff check` 无错误
- [ ] 代码质量 ≥4.5/5
- [ ] CHANGELOG.md 更新
- [ ] README_AI.md 重新生成
- [ ] 文档更新完成

---

## 📚 参考资料

- [Epic 4 规划文档](./epic4-refactoring-plan.md)
- [Click 文档 - Commands and Groups](https://click.palletsprojects.com/en/8.1.x/commands/)
- [Python 模块化最佳实践](https://docs.python.org/3/tutorial/modules.html)

---

**Created**: 2026-01-27
**Author**: Claude Code
**Epic**: 4 - Code Refactoring
**Status**: Planning → Ready for Development
