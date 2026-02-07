# Epic 12: Single File Parse Command (SIMPLIFIED)

**Epic ID**: 12
**Created**: 2026-02-07
**Status**: 🟢 Ready for Implementation
**Target Version**: v0.13.0
**Estimated Effort**: 2-3 days (Simplified from 3-5 days)
**Priority**: P0 (Foundational capability)

---

## 📋 Executive Summary

### Business Context

**Problem**:
- codeindex 作为 AST 解析工具，缺乏单文件解析功能
- 下游工具（如 LoomGraph）需要调用 codeindex Python API（紧耦合）
- 功能不完整：只有批量处理（scan/scan-all），没有单文件处理

**Solution**:
添加 `codeindex parse <file>` 命令，提供单文件解析能力，通过 CLI 输出 JSON 格式的 ParseResult。

**Value Proposition**:
1. **功能完整性**: AST 解析工具应该支持单文件解析（基础能力）
2. **松耦合集成**: 通过 CLI 调用，而非 Python API 依赖
3. **工具链友好**: 其他语言的工具也能调用（非 Python 独占）
4. **架构一致性**: scan（批量）+ parse（单文件）双命令设计

### Success Criteria

**功能指标**:
- [x] 支持 Python、PHP、Java 单文件解析
- [x] JSON 输出格式与 `scan --output json` 一致
- [x] 包含所有 ParseResult 字段（symbols, imports, namespace, inheritance, calls）
- [x] 自动检测文件语言
- [x] 错误处理清晰（文件不存在、语言不支持、解析失败）

**质量指标**:
- [x] 测试覆盖率 ≥ 90%
- [x] 20+ 核心测试通过
- [x] 文档完整（README + CLAUDE.md + CLI help）

---

## 🎯 Goals & Non-Goals

### In Scope (This Epic)

✅ **Core Command**:
- `codeindex parse <file>` 命令实现
- JSON 输出格式（默认，唯一输出格式）

✅ **Language Support**:
- Python (已有解析器)
- PHP (已有解析器)
- Java (已有解析器)

✅ **Features**:
- 自动语言检测
- 完整 ParseResult 输出（symbols, imports, namespace, inheritance, calls, routes）
- 框架路由提取（ThinkPHP、Spring）自动包含
- 错误处理（文件不存在、不支持的语言、解析失败）

✅ **Documentation**:
- README.md 更新
- CLAUDE.md 更新
- CLI help text

### Out of Scope (Future Work)

❌ **Console 输出格式**:
- 推迟到 v0.13.1 或 v0.14.0
- 理由：LoomGraph 只需要 JSON，Console 是"nice to have"

❌ **批量处理**:
- 使用现有 `scan-all` 命令

❌ **新语言支持**:
- TypeScript、Go、Rust → Epic 8+

❌ **高级功能**:
- 代码分析（tech-debt、complexity）
- AI 文档生成

---

## 📊 Single User Story

### Story 12.1: Parse Command with JSON Output

**User Story**:
> 作为开发者，我希望能够通过 `codeindex parse <file>` 命令解析单个源文件，并获得 JSON 格式的结构化数据，以便我的工具（如 LoomGraph）能够通过 CLI 调用而非 Python API 集成。

**Acceptance Criteria**:
1. ✅ 命令存在: `codeindex parse <file>`
2. ✅ 自动检测语言（基于文件扩展名）
3. ✅ JSON 输出包含完整 ParseResult 字段（all fields from Epic 10 + 11）
4. ✅ 错误处理清晰（文件不存在、语言不支持、解析失败）
5. ✅ 文档完整（README.md + CLAUDE.md + CLI help）

**Technical Requirements**:
- 新增 `src/codeindex/cli_parse.py` 模块 (~100 lines)
- Click 命令定义
- 复用 `parser.py` 的 `parse_file()` 函数
- 复用 `data_types.py` 的 `ParseResult.to_dict()` 方法
- 错误码：0=成功，1=文件不存在，2=语言不支持，3=解析失败

**Test Cases** (20 tests):

**Basic Functionality (5 tests)**:
- ✅ 解析 Python 文件 → JSON 输出
- ✅ 解析 PHP 文件 → JSON 输出
- ✅ 解析 Java 文件 → JSON 输出
- ✅ CLI help text 完整
- ✅ 版本信息正确

**JSON Format Validation (5 tests)**:
- ✅ JSON 包含所有必需字段（file_path, language, symbols, imports, namespace, error）
- ✅ JSON 包含可选字段（inheritances, calls, routes - 如果存在）
- ✅ symbols 字段结构正确（name, kind, signature, line_start, line_end）
- ✅ JSON 可反序列化（round-trip test）
- ✅ 与 `scan --output json` 格式一致

**Error Handling (5 tests)**:
- ✅ 文件不存在 → Exit code 1
- ✅ 不支持的语言 (.txt) → Exit code 2
- ✅ 语法错误的文件 → Exit code 3 或 JSON with error field
- ✅ 权限错误 → 清晰错误信息
- ✅ 空文件 → 正常处理（symbols = []）

**Framework Features (3 tests)**:
- ✅ ThinkPHP 控制器 → routes 字段包含
- ✅ Spring Controller → routes 字段包含
- ✅ 继承类 → inheritances 字段包含

**Performance (2 tests)**:
- ✅ 小文件 (<1000 行) 解析时间 < 0.1s
- ✅ 大文件 (5000+ 行) 解析时间 < 1s

**Estimated Effort**: 2-3 天

---

## 🏗️ Technical Design

### Architecture Overview

```
┌────────────────────────────────────────────────────┐
│  CLI Layer (cli.py)                                │
│  ├── scan (目录批量) → cli_scan.py                 │
│  ├── scan-all (全局批量) → cli_scan_all.py         │
│  └── parse (单文件) → cli_parse.py ✨ NEW          │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│  Parser Layer (parser.py)                          │
│  ├── detect_language(file_path) ✅ 已存在          │
│  ├── parse_file(file_path, language) ✅ 已存在     │
│  └── ParseResult → JSON ✅ 已存在                  │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│  Output Layer (data_types.py)                      │
│  └── ParseResult.to_dict() ✅ 已存在               │
└────────────────────────────────────────────────────┘
```

### Core Implementation

**cli_parse.py** (~100 lines):
```python
import click
import json
from pathlib import Path
from codeindex.parser import detect_language, parse_file

@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def parse(file_path: str):
    """Parse a single source file and output JSON.

    Examples:
        codeindex parse src/main.py
        codeindex parse src/Controller.php | jq .
    """
    try:
        # 1. Detect language
        file_path_obj = Path(file_path)
        language = detect_language(file_path_obj)

        if language is None:
            click.echo(f"Error: Unsupported file type: {file_path_obj.suffix}", err=True)
            raise click.exceptions.Exit(2)

        # 2. Parse file (reuse existing logic)
        parse_result = parse_file(str(file_path_obj), language)

        # 3. Output JSON (reuse to_dict)
        output_data = parse_result.to_dict()
        click.echo(json.dumps(output_data, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        click.echo(f"Error: File not found: {file_path}", err=True)
        raise click.exceptions.Exit(1)
    except PermissionError:
        click.echo(f"Error: Permission denied: {file_path}", err=True)
        raise click.exceptions.Exit(1)
    except Exception as e:
        click.echo(f"Error: Failed to parse file: {e}", err=True)
        raise click.exceptions.Exit(3)
```

**cli.py** (1 line change):
```python
from codeindex.cli_parse import parse

cli.add_command(parse)  # ✨ NEW
```

### Error Handling

| Error Type | Exit Code | Message | Example |
|------------|-----------|---------|---------|
| File not found | 1 | `Error: File not found: {path}` | 路径错误 |
| Permission denied | 1 | `Error: Permission denied: {path}` | 权限不足 |
| Unsupported language | 2 | `Error: Unsupported file type: .txt` | .txt 文件 |
| Parse failure | 3 | `Error: Failed to parse file: {reason}` | 语法错误 |
| Success | 0 | (JSON output) | 正常解析 |

---

## 🧪 Testing Strategy

### Test Structure

**test_cli_parse.py** (~200 lines):
```python
import pytest
from click.testing import CliRunner
from codeindex.cli import cli
import json

class TestCliParse:
    """CLI parse command tests"""

    def setup_method(self):
        self.runner = CliRunner()

    # Basic Functionality (5 tests)
    def test_parse_python_file(self):
        """解析 Python 文件 → JSON 输出"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/simple.py'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['language'] == 'python'
        assert len(data['symbols']) > 0

    # JSON Format Validation (5 tests)
    def test_json_all_fields(self):
        """JSON 包含所有必需字段"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/simple.py'])
        data = json.loads(result.output)
        required = ['file_path', 'language', 'symbols', 'imports', 'namespace', 'error']
        for field in required:
            assert field in data

    # Error Handling (5 tests)
    def test_file_not_found(self):
        """文件不存在 → Exit code 1"""
        result = self.runner.invoke(cli, ['parse', 'nonexistent.py'])
        assert result.exit_code == 1
        assert 'File not found' in result.output

    # Framework Features (3 tests)
    def test_thinkphp_routes(self):
        """ThinkPHP 控制器 → routes 字段"""
        # ... 测试路由提取

    # Performance (2 tests)
    def test_small_file_performance(self):
        """小文件 < 0.1s"""
        # ... 性能测试
```

### Test Fixtures

```bash
tests/fixtures/cli_parse/
├── simple.py          # 简单 Python 文件
├── complete.py        # 包含所有特性（继承、调用）
├── simple.php         # 简单 PHP 文件
├── Controller.php     # ThinkPHP 控制器（带路由）
├── Simple.java        # 简单 Java 文件
├── Service.java       # Spring Service（带注解）
├── broken.py          # 语法错误文件
└── unsupported.txt    # 不支持的文件类型
```

---

## 📅 Development Plan (2-3 Days)

### Day 1: TDD Core Implementation (6 hours)

**Morning (3 hours)**:
- [ ] 创建 feature 分支
- [ ] 创建测试文件 + fixtures
- [ ] 编写前 10 个失败测试（Red phase）
  - 5 基础功能 + 5 JSON 验证
- [ ] 运行测试（期望全部 FAIL）

**Afternoon (3 hours)**:
- [ ] 实现 `cli_parse.py` 核心逻辑 (~100 lines)
- [ ] 集成到 `cli.py` (1 line)
- [ ] 运行测试（期望前 10 个 PASS）
- [ ] Commit: "feat(cli): add parse command with JSON output"

---

### Day 2: Error Handling + Framework Features (6 hours)

**Morning (3 hours)**:
- [ ] 编写 5 个错误处理测试（Red phase）
- [ ] 实现错误处理逻辑
- [ ] 运行测试（期望 15 个 PASS）
- [ ] Commit: "feat(cli): add error handling for parse command"

**Afternoon (3 hours)**:
- [ ] 编写 3 个框架特性测试（ThinkPHP/Spring routes）
- [ ] 验证路由自动提取
- [ ] 编写 2 个性能测试
- [ ] 运行测试（期望 20 个 PASS）
- [ ] Commit: "test(cli): add framework and performance tests"

---

### Day 3: Documentation + Release (4 hours)

**Morning (2 hours)**:
- [ ] 更新 README.md（添加 parse 命令用法）
- [ ] 更新 CLAUDE.md（添加集成指南）
- [ ] 验证 CLI help text
- [ ] 创建集成示例脚本（`examples/loomgraph-integration.sh`）

**Afternoon (2 hours)**:
- [ ] 完整回归测试（所有语言）
- [ ] 性能基准测试
- [ ] 更新 CHANGELOG.md + ROADMAP.md
- [ ] 代码审查（ruff check）
- [ ] 创建 PR
- [ ] Commit: "docs: add parse command documentation and examples"

---

## 📊 Success Metrics

### Functional Metrics

- [x] `codeindex parse <file>` 命令可用
- [x] 20 测试通过，0 失败
- [x] 支持 Python、PHP、Java 单文件解析
- [x] JSON 输出格式完整

### Quality Metrics

- [x] 测试覆盖率 ≥ 90%
- [x] 代码审查通过（ruff check）
- [x] 文档完整（README + CLAUDE.md + CLI help）

### Performance Metrics

- [x] 小文件 (<1000 行) < 0.1s
- [x] 大文件 (5000+ 行) < 1s

### Integration Metrics

- [x] LoomGraph 集成验证（示例脚本可运行）
- [x] 与 `scan --output json` 格式一致

---

## 🔗 Related Documents

- **Design Philosophy**: Serena memory `design_philosophy`
- **Parser Architecture**: `src/codeindex/parser.py`
- **Multi-Language Workflow**: `docs/development/multi-language-support-workflow.md`

---

## 📝 Changes from Original Design

### Removed Features (Out of Scope)

1. ❌ **Console Output Format** (`--output console`)
   - Reason: LoomGraph 只需要 JSON，Console 是"nice to have"
   - Future: v0.13.1 或 v0.14.0

2. ❌ **Separate JSON Validation Story** (Story 12.2)
   - Reason: JSON 验证是核心功能的一部分，不应该独立
   - Merged: JSON 验证测试合并到 Story 12.1

3. ❌ **Separate Documentation Story** (Story 12.3)
   - Reason: 文档是开发的最后一步，不需要独立 Story
   - Merged: 文档更新作为 Story 12.1 的 Acceptance Criteria

### Simplified Scope

**Original**: 3 Stories, 38 tests, 3-5 days
**Simplified**: 1 Story, 20 tests, 2-3 days

**Impact**:
- ✅ 更聚焦核心功能（JSON 输出）
- ✅ 更快交付（2-3 天 vs 3-5 天）
- ✅ 避免过度设计（移除非必需的 Console 输出）
- ✅ TDD 更简洁（一次 Red-Green-Refactor 循环）

---

**Epic Status**: 🟢 Ready for Implementation (Simplified)
**Next Step**: Create feature branch → Start TDD (Day 1)
**Estimated Completion**: 2026-02-09 (2-3 days)
