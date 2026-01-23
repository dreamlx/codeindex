# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
优先读取readme_ai.md理解当前文件夹下的结构

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
