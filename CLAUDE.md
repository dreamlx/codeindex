# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🧭 Claude Code 工作流指南

### 📖 理解项目架构（分析模式）

**⚠️ 重要：本项目有多层次的 README_AI.md 文件，是理解代码的最佳入口**

1. **第一步：阅读 README_AI.md（必须）**
   ```
   优先级顺序：
   1. /README_AI.md                    # 整体项目概览
   2. /src/codeindex/README_AI.md      # 核心模块架构
   3. /tests/README_AI.md              # 测试结构和覆盖
   4. /docs/README_AI.md (如果存在)    # 文档组织
   ```

2. **第二步：查看专门的索引文件**
   - `PROJECT_SYMBOLS.md` - 全局符号索引和跨文件引用
   - `CHANGELOG.md` - 版本演进和功能变更
   - `RELEASE_NOTES_*.md` - 重大版本说明

3. **避免的做法 ❌**
   - 直接用 Glob/Grep 搜索源码（低效且无结构）
   - 不看 README_AI.md 就直接读 .py 文件
   - 忽略已有的符号索引文件

### 🔍 定位具体代码（导航模式）

**使用 Serena MCP 工具进行精确导航：**

1. **查找符号定义**
   ```python
   # 使用 find_symbol 而不是 Grep
   find_symbol(name_path_pattern="AdaptiveSymbolSelector")
   find_symbol(name_path_pattern="SmartWriter/write_readme")
   ```

2. **查找符号引用**
   ```python
   # 找谁在用这个函数
   find_referencing_symbols(
       name_path="calculate_limit",
       relative_path="src/codeindex/adaptive_selector.py"
   )
   ```

3. **搜索模式匹配**
   ```python
   # 只在必要时使用 search_for_pattern
   search_for_pattern(
       substring_pattern="file_lines",
       restrict_search_to_code_files=True
   )
   ```

4. **获取符号概览**
   ```python
   # 快速了解文件结构
   get_symbols_overview(
       relative_path="src/codeindex/parser.py",
       depth=1  # 包含方法列表
   )
   ```

### 📁 项目特殊文件说明

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| `README_AI.md` | AI生成的目录文档 | 理解任何目录的架构和组件 |
| `PROJECT_SYMBOLS.md` | 全局符号索引 | 查找符号定义位置 |
| `CHANGELOG.md` | 版本变更历史 | 了解功能演进和破坏性变更 |
| `RELEASE_NOTES_*.md` | 发布说明 | 查看重大版本的详细信息 |
| `.codeindex.yaml` | 配置文件 | 理解扫描规则和AI集成 |
| `docs/planning/*.md` | Epic/Story规划 | 查看功能设计决策 |
| `docs/evaluation/*.md` | 验证报告 | 查看功能验证结果 |

### 🎯 典型场景示例

**场景1：我想理解 adaptive symbol extraction 是如何工作的**
```
1. 读取 src/codeindex/README_AI.md
   → 找到 "AdaptiveSymbolSelector" 组件说明
2. 使用 find_symbol(name_path_pattern="AdaptiveSymbolSelector")
   → 查看类定义和方法
3. 读取 docs/planning/epic2-adaptive-symbols-plan.md
   → 理解设计决策
4. 读取 tests/test_adaptive_selector.py
   → 查看使用示例和边界情况
```

**场景2：我想找到所有使用 file_lines 的地方**
```
1. 使用 search_for_pattern(substring_pattern="file_lines")
   → 获取所有引用位置
2. 使用 find_symbol 查看核心定义
3. 使用 find_referencing_symbols 查看依赖关系
```

**场景3：我想修改符号评分算法**
```
1. 读取 src/codeindex/README_AI.md
   → 找到 SymbolImportanceScorer
2. 使用 get_symbols_overview("src/codeindex/symbol_scorer.py", depth=1)
   → 查看所有评分方法
3. 读取 tests/test_symbol_scorer.py
   → 理解评分规则和测试用例
4. 使用 find_referencing_symbols 查看调用方
   → 评估修改影响范围
```

## Quick Start (常用命令)

```bash
# 🚀 生成所有目录的索引 (最常用)
codeindex scan-all --fallback

# 查看会扫描哪些目录
codeindex list-dirs

# 生成全局符号索引
codeindex symbols

# 查看索引覆盖率
codeindex status
```

## 配置说明 (.codeindex.yaml)

```yaml
# ✅ 推荐：只指定顶层目录，自动递归扫描所有子目录
include:
  - Application    # 会扫描 Application 下所有子目录
  - src            # 会扫描 src 下所有子目录

# ❌ 不推荐：逐个列出每个子目录
include:
  - Application/Admin/Controller
  - Application/Admin/Model
  - Application/Retail/Controller
  # ... 太繁琐
```

**关键行为**：
- `include` 中的目录会**递归扫描所有子目录**
- 每个有代码文件的子目录都会生成独立的 `README_AI.md`
- 文件大小限制 50KB，超出会自动截断

## Build & Development Commands

```bash
# Install (development mode)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_parser.py::test_parse_simple_function

# Lint
ruff check src/

# CLI usage (详细)
codeindex scan ./src/auth          # 扫描单个目录
codeindex scan ./src/auth --fallback  # 不使用 AI 生成
codeindex scan ./src/auth --dry-run   # 预览 prompt
codeindex init                     # 创建 .codeindex.yaml
codeindex status                   # 查看索引覆盖率
codeindex list-dirs                # 列出可索引目录
codeindex symbols                  # 生成全局符号索引
```

## Architecture

codeindex is an AI-native code indexing tool that generates `README_AI.md` files for directories by invoking external AI CLI tools.

### Core Pipeline

1. **Scanner** (`scanner.py`) - Walks directories, filters by config patterns, returns `ScanResult` with files
2. **Parser** (`parser.py`) - Uses tree-sitter to extract symbols (classes, functions, methods), imports, and docstrings from Python files
3. **Writer** (`writer.py`) - Formats parsed data into prompts, writes output files
4. **Invoker** (`invoker.py`) - Executes external AI CLI commands with the prompt, handles timeouts
5. **CLI** (`cli.py`) - Click-based entry point, orchestrates the pipeline

### Data Flow

```
Directory → Scanner → [files] → Parser → [ParseResult] → Writer (format) →
    Invoker (AI CLI) → Writer (write) → README_AI.md
```

### Key Types

- `ScanResult`: Contains path, files, subdirs
- `ParseResult`: Contains path, symbols, imports, module_docstring, error
- `Symbol`: name, kind (class/function/method), signature, docstring, line range
- `Import`: module, names, is_from
- `Config`: Loaded from `.codeindex.yaml`, controls AI command, include/exclude patterns, languages

### External AI CLI Integration

The tool invokes external AI CLIs via shell subprocess. The `ai_command` config uses `{prompt}` as placeholder:
```yaml
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
```

Fallback mode (`--fallback`) generates basic README without AI.

## Configuration

Config file: `.codeindex.yaml` (see `examples/.codeindex.yaml`)
- `ai_command`: Shell command template with `{prompt}` placeholder
- `include`/`exclude`: Glob patterns for directory filtering
- `languages`: Currently only `python` supported
- `output_file`: Default `README_AI.md`

## 🛠️ 开发工作流

### TDD 开发流程（必须遵守）

本项目严格遵循 TDD（测试驱动开发）：

1. **Red（写失败的测试）**
   ```bash
   # 先写测试用例
   pytest tests/test_new_feature.py -v
   # 预期结果：测试失败 ❌
   ```

2. **Green（实现最小代码使测试通过）**
   ```bash
   # 实现功能
   pytest tests/test_new_feature.py -v
   # 预期结果：测试通过 ✅
   ```

3. **Refactor（重构优化）**
   ```bash
   # 优化代码，确保测试仍然通过
   pytest  # 运行所有测试
   ruff check src/  # 代码规范检查
   ```

### GitFlow 分支策略

```
master (生产分支，v0.3.1)
├── develop (开发分支)
│   ├── feature/epic3-xxx (功能分支)
│   ├── feature/epic4-xxx (功能分支)
│   └── hotfix/xxx (紧急修复)
```

**分支使用规则：**
- `master`: 只接受来自 develop 的合并，每次合并打 tag
- `develop`: 主开发分支，功能分支合并到这里
- `feature/*`: Epic/Story 功能开发分支
- `hotfix/*`: 紧急修复分支，可直接合并到 master

**提交信息格式：**
```
feat(scope): 添加新功能
fix(scope): 修复bug
docs(scope): 文档更新
test(scope): 测试相关
refactor(scope): 重构代码
```

### 代码质量检查清单

在提交代码前必须通过：

```bash
# ✅ 1. 运行所有测试
pytest -v
# 要求：所有测试通过

# ✅ 2. 代码规范检查
ruff check src/
# 要求：无错误

# ✅ 3. 类型检查（如果使用）
mypy src/
# 要求：无类型错误

# ✅ 4. 测试覆盖率（可选）
pytest --cov=src/codeindex --cov-report=term-missing
# 推荐：核心模块 ≥ 90%，整体 ≥ 80%
```

## 📚 文档更新规则

### 何时需要更新文档

| 变更类型 | 需要更新的文档 |
|---------|---------------|
| 新增功能 | CHANGELOG.md, README.md, 相关 README_AI.md |
| Bug修复 | CHANGELOG.md |
| 配置变更 | .codeindex.yaml 示例, docs/guides/configuration.md |
| API变更 | README.md, 相关模块的 docstring |
| 重大版本 | CHANGELOG.md, RELEASE_NOTES_vX.X.X.md |
| 架构决策 | docs/architecture/adr-xxx.md |

### 自动生成 README_AI.md

**重要：修改代码后需要重新生成索引**

```bash
# 重新生成所有 README_AI.md
codeindex scan-all --fallback

# 或只生成特定目录
codeindex scan src/codeindex --fallback
codeindex scan tests --fallback
```

## 📈 版本历史和功能演进

### v0.3.1 - CLI Module Split (2026-01-28)
- **Epic 4 Story 4.3**: CLI 架构重构
- CLI 从 1062 行拆分为 6 个专注模块（-97%）
- 每个模块单一职责：scan, config, symbols, tech-debt
- 零破坏性变更，所有 263 测试通过
- 嵌套函数重构为独立辅助函数

### v0.3.0 - AI Enhancement & Tech Debt (2026-01-27)
- **Epic 4 Stories 4.1-4.2**: 代码重构和质量改进
- AI Helper 模块：复用增强功能
- File Size Classifier：统一文件大小检测
- **Epic 3.2**: 超大文件多轮对话（>5000行或>100符号）
  - 三轮对话：架构概览 → 核心组件 → 最终合成
  - 自动检测和策略选择
- **Epic 3.1**: 技术债务分析
  - 复杂度指标（cyclomatic, cognitive, nesting）
  - God Class 检测（>50 methods）
  - 多格式输出（console/markdown/json）
- 消除 ~110 行代码重复

### v0.2.0 - Adaptive Symbols (2025-01-15)
- **Epic 2**: 自适应符号提取
- 7级文件大小分类（tiny→mega）
- 动态符号限制：5-150 个/文件（基于文件大小）
- 大文件信息覆盖率提升 280%（26% → 100%）
- YAML 配置支持
- 零破坏性变更（默认禁用）

### v0.1.3 - Project Indexing (2025-01-15)
- PROJECT_INDEX.json 和 PROJECT_INDEX.md
- 代码库导航索引
- 改进 README_AI.md 自动生成

### v0.1.2 - Parallel & Incremental (2025-01-14)
- 并行扫描支持（codeindex list-dirs）
- --dry-run 预览 prompt
- status 命令查看索引覆盖率
- 增量更新分析

### v0.1.0 - Initial Release (2025-01-12)
- Python 代码解析（tree-sitter）
- 外部 AI CLI 集成
- 符号提取（classes, functions, imports）
- README_AI.md 生成
- 基础测试套件

## 🚨 常见错误和避免方法

### ❌ 错误做法

1. **直接修改生成的 README_AI.md**
   - README_AI.md 是自动生成的，会被覆盖
   - 正确做法：修改源码的 docstring，然后重新生成

2. **跳过测试直接写实现**
   - 违反 TDD 原则
   - 正确做法：先写测试，再写实现

3. **使用 Glob/Grep 搜索代码**
   - 不精确，无法理解符号关系
   - 正确做法：使用 Serena MCP 的 find_symbol 和 find_referencing_symbols

4. **不看 README_AI.md 就修改代码**
   - 可能不理解模块的设计意图
   - 正确做法：先读 README_AI.md，理解架构再修改

5. **直接提交到 develop 或 master**
   - 违反 GitFlow 规范
   - 正确做法：创建 feature 分支，完成后合并

### ✅ 最佳实践

1. **理解代码流程**
   ```
   README_AI.md → find_symbol → 读源码 → 写测试 → 实现
   ```

2. **修改功能流程**
   ```
   创建 feature 分支 → TDD开发 → 测试通过 → ruff检查 →
   更新 CHANGELOG → 提交 → 合并到 develop
   ```

3. **发布版本流程**
   ```
   develop 合并到 master → 运行所有测试 → 创建 tag →
   生成 RELEASE_NOTES → 推送到 GitHub
   ```