# CLAUDE.md

**For**: Claude Code (claude.ai/code) when working with this repository

**Purpose**: Guide AI Code on understanding, navigating, and contributing to codeindex

---

## 1. Understanding & Navigating

### How to Understand This Project

**Start with README_AI.md files** - They are your best entry point:

1. `/README_AI.md` - Project overview
2. `/src/codeindex/README_AI.md` - Core module architecture
3. `/tests/README_AI.md` - Test structure

**Secondary resources**:
- `PROJECT_SYMBOLS.md` - Global symbol index
- `CHANGELOG.md` - Version history (single source of truth for releases)
- `docs/planning/*.md` - Epic/Story design decisions

**Avoid**: Direct Glob/Grep on source code — use Serena MCP tools or README_AI.md first.

### How to Navigate Code

**Use Serena MCP tools** for precise navigation:

```python
find_symbol(name_path_pattern="AdaptiveSymbolSelector")
find_referencing_symbols(name_path="calculate_limit", relative_path="src/codeindex/adaptive_selector.py")
get_symbols_overview(relative_path="src/codeindex/parser.py", depth=1)
search_for_pattern(substring_pattern="file_lines", restrict_search_to_code_files=True)
```

### Project Special Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `README_AI.md` | AI-generated directory docs | Understanding any directory |
| `PROJECT_SYMBOLS.md` | Global symbol index | Finding symbol locations |
| `CHANGELOG.md` | Version history (single source of truth) | Understanding evolution and breaking changes |
| `.codeindex.yaml` | Configuration | Understanding scan rules and AI integration |
| `docs/planning/*.md` | Epic/Story plans | Design decisions and rationale |
| `docs/guides/configuration-changelog.md` | Config version history | Configuration upgrades |

---

## 2. Development Workflow

### CRITICAL: Always Use Virtual Environment

```bash
source .venv/bin/activate
which python3  # Must show .venv in path
pip install -e ".[dev,all]"
```

Without venv: pip fails (PEP 668), pre-push hooks fail (`ModuleNotFoundError`), `make release` fails.

### Quick Start Commands

```bash
codeindex scan-all --fallback          # Generate all indexes
codeindex parse src/myfile.py | jq .   # Parse single file
codeindex list-dirs                    # View what will be scanned
codeindex symbols                      # Generate global symbol index
codeindex status                       # Check indexing coverage
codeindex scan-all --output json       # JSON output for tool integration
codeindex hooks status                 # Git Hooks management
```

### TDD Development Flow (Required)

This project strictly follows TDD: **Red** (write failing tests) → **Green** (minimal implementation) → **Refactor** (optimize, keep tests green).

```bash
pytest tests/test_new_feature.py -v    # Red/Green
pytest && ruff check src/              # Refactor verification
```

### GitFlow & Commits

```
master ← develop ← feature/* | hotfix/*
```

- `master`: Only merge from develop, tag each merge
- `develop`: Main development branch
- `feature/*`: Epic/Story feature branches
- `hotfix/*`: Emergency fixes

**Commit format**: `feat(scope):`, `fix(scope):`, `docs(scope):`, `test(scope):`, `refactor(scope):`

### Pre-commit Checklist

```bash
pytest -v                              # All tests pass
ruff check src/                        # Code style
pytest --cov=src/codeindex             # Coverage: core ≥90%, overall ≥80%
```

### Documentation Update Rules

| Change Type | Documents to Update |
|-------------|---------------------|
| New feature | CHANGELOG.md, README.md, relevant README_AI.md |
| Bug fix | CHANGELOG.md |
| Config change | .codeindex.yaml example, docs/guides/configuration.md, docs/guides/configuration-changelog.md |
| API change | README.md, docstrings |
| Major release | CHANGELOG.md (GitHub Release auto-extracted from CHANGELOG) |
| Architecture decision | docs/architecture/adr-xxx.md |

After code changes: `codeindex scan-all --fallback`

### Documentation Maintenance (Post-Epic)

When an Epic is completed:
1. Update `docs/planning/ROADMAP.md` (move epic Active → Completed)
2. Archive epic docs to `docs/planning/completed/`
3. Update `docs/planning/README.md`

See `docs/development/requirements-workflow.md` for full details.

### Release Flow

```
Update CHANGELOG [Unreleased] → [X.X.X] → Merge develop to master →
make release VERSION=X.X.X → CI auto-creates GitHub Release from CHANGELOG
```

See `docs/development/release-workflow.md` and `docs/development/QUICK_START_RELEASE.md`.

---

## 3. Design Philosophy

**Read `docs/architecture/design-philosophy.md`** before:
- Adding new language support
- Implementing features involving ParseResult or core architecture
- Making architectural decisions or discussing parallelization

**Core principles**:
- We extract structure (What), AI understands semantics (Why)
- 3 layers: Structure Extraction (tree-sitter) → Automated Analysis → AI Enhancement
- AI invocation is the bottleneck (99% of time), not parsing
- ThreadPool for all languages (I/O bound, not CPU bound)

---

## 4. Architecture Reference

### Core Pipeline

```
Directory → Scanner → [files] → Parser → [ParseResult] →
Writer (format) → Invoker (AI CLI) → Writer (write) → README_AI.md
```

| Component | File | Output |
|-----------|------|--------|
| Scanner | `scanner.py` | `ScanResult` (path, files, subdirs) |
| Parser | `parser.py` | `ParseResult` (symbols, imports, module_docstring) |
| Writer | `writer.py` | Formatted prompts, README_AI.md |
| Invoker | `invoker.py` | AI CLI execution |
| CLI | `cli.py` | Command orchestration |

**Key types**: `Symbol` (name, kind, signature, docstring, line_start, line_end), `Import` (module, names, is_from), `Config` (from `.codeindex.yaml`)

### Configuration

**File**: `.codeindex.yaml` (see `examples/.codeindex.yaml`)

```yaml
version: 1
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
include: [src/]
exclude: ["**/__pycache__/**"]
languages: [python, php, java]     # Supported languages
output_file: README_AI.md
```

When modifying config: See `docs/guides/configuration.md` | Upgrade history: `docs/guides/configuration-changelog.md`

---

## 5. Extension Development

### Adding Framework Support

Plugin-based route extraction for web frameworks (ThinkPHP, Spring, Laravel, etc.):

1. Write tests first: `tests/extractors/test_myframework.py`
2. Implement extractor: `src/codeindex/extractors/myframework.py`
3. Auto-registered via `extractors/__init__.py`

Reference: `src/codeindex/extractors/thinkphp.py`

### Git Hooks

Built-in hooks: pre-commit (lint), post-commit (auto README), pre-push (tests).

Management: `codeindex hooks install/uninstall/status` | Guide: `docs/guides/git-hooks-integration.md`

---

## 6. Common Mistakes

| Mistake | Correct Approach |
|---------|-----------------|
| Directly modify README_AI.md | Modify source docstrings, regenerate |
| Skip tests, write implementation first | Write tests first (TDD) |
| Use Glob/Grep for code exploration | Use Serena MCP tools (find_symbol, etc.) |
| Ignore README_AI.md before modifying code | Read README_AI.md first |
| Commit directly to develop/master | Create feature branch |
| Run commands without venv | Always `source .venv/bin/activate` first |

---

## 7. Quick Reference

### Key Flows

```
Environment:  source .venv/bin/activate → which python3 → Ready
Understanding: README_AI.md → find_symbol → Read source → Write tests → Implement
Feature:      feature branch → TDD → Tests pass → ruff check → Update CHANGELOG → Merge
Release:      CHANGELOG [Unreleased]→[X.X.X] → merge to master → make release VERSION=X.X.X
```

### When to Read Detailed Docs

| When you need to... | Read |
|---------------------|------|
| Release a new version | `docs/development/release-workflow.md` |
| Create a new Epic or Feature | `docs/development/requirements-workflow.md` |
| Modify `.codeindex.yaml` config | `docs/guides/configuration.md` |
| Fix or customize Git hooks | `docs/guides/git-hooks-integration.md` |
| Add a new language parser | `docs/architecture/design-philosophy.md` |
| Set up codeindex in another project | `docs/guides/claude-code-integration.md` |

---

## 8. Code Search (LoomGraph)

```bash
loomgraph search "<query>"                          # Semantic code search
loomgraph graph "<Class.method>" --direction callers # Call relationship query
loomgraph status                                    # Check service status
loomgraph index .                                   # Re-index codebase
```

Service: LightRAG API `http://117.131.45.179:3020` | Embedding `http://117.131.45.179:3002`

---

**Last Updated**: 2026-02-11
**codeindex Version**: v0.14.0
**For**: Claude Code and contributors
