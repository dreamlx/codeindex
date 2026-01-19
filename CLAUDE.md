# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
优先读取readme_ai.md理解当前文件夹下的结构

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

# CLI usage
codeindex scan ./src/auth          # Scan directory, generate README_AI.md
codeindex scan ./src/auth --fallback  # Generate without AI
codeindex scan ./src/auth --dry-run   # Preview prompt
codeindex init                     # Create .codeindex.yaml
codeindex status                   # Show indexing coverage
codeindex list-dirs                # List indexable directories
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
