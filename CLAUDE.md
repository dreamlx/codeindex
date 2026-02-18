# CLAUDE.md

**For**: Claude Code (claude.ai/code) when working with this repository

**Purpose**: Guide AI Code on understanding, navigating, and contributing to codeindex

---

## 🧭 Part 1: Understanding & Navigating

### 📖 How to Understand This Project

**⚠️ Start with README_AI.md files** - They are your best entry point

**Priority order**:
1. `/README_AI.md` - Project overview
2. `/src/codeindex/README_AI.md` - Core module architecture
3. `/tests/README_AI.md` - Test structure
4. Specific module README_AI.md as needed

**Secondary resources**:
- `PROJECT_SYMBOLS.md` - Global symbol index
- `CHANGELOG.md` - Version history and breaking changes
- `RELEASE_NOTES_*.md` - Major release details
- `docs/planning/*.md` - Epic/Story design decisions

**❌ Avoid**:
- Direct Glob/Grep on source code (inefficient)
- Reading .py files without context
- Ignoring existing documentation

### 🔍 How to Navigate Code

**Use Serena MCP tools** for precise navigation:

```python
# Find symbol definitions
find_symbol(name_path_pattern="AdaptiveSymbolSelector")
find_symbol(name_path_pattern="SmartWriter/write_readme")

# Find who uses a symbol
find_referencing_symbols(
    name_path="calculate_limit",
    relative_path="src/codeindex/adaptive_selector.py"
)

# Get file overview (faster than reading full file)
get_symbols_overview(
    relative_path="src/codeindex/parser.py",
    depth=1  # Include method list
)

# Pattern search (only when necessary)
search_for_pattern(
    substring_pattern="file_lines",
    restrict_search_to_code_files=True
)
```

### 📁 Project Special Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `README_AI.md` | AI-generated directory docs | Understanding any directory |
| `PROJECT_SYMBOLS.md` | Global symbol index | Finding symbol locations |
| `CHANGELOG.md` | Version history | Understanding evolution and breaking changes |
| `RELEASE_NOTES_*.md` | Release details | Detailed version information |
| `.codeindex.yaml` | Configuration | Understanding scan rules and AI integration |
| `docs/planning/*.md` | Epic/Story plans | Design decisions and rationale |
| `docs/evaluation/*.md` | Validation reports | Feature verification results |
| `CHANGELOG.md` | Version history | Understanding evolution and config changes |

### 🎯 Common Scenarios

**Scenario 1: Understand a core feature (e.g., adaptive symbol extraction)**
```
1. Read src/codeindex/README_AI.md → Find component
2. Use find_symbol(name_path_pattern="AdaptiveSymbolSelector")
3. Read docs/planning/epic*.md → Design decisions
4. Read tests/test_*.py → Usage examples
```

**Scenario 2: Modify existing code (e.g., symbol scoring)**
```
1. Read README_AI.md → Locate module
2. Use get_symbols_overview("file.py", depth=1) → View structure
3. Use find_referencing_symbols → Assess impact
4. Read tests → Understand behavior
```

---

## 🛠️ Part 2: Development Workflow

### ⚠️ CRITICAL: Always Use Virtual Environment

**Before any development work**, you MUST activate the virtual environment:

```bash
# Activate virtual environment (REQUIRED)
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Verify activation (should show .venv path)
which python3  # → /path/to/codeindex/.venv/bin/python3

# Install dependencies if needed
pip install -e ".[dev,all]"
```

**Why critical**:
- ❌ **Without venv**: pip fails on macOS (PEP 668 protection: "externally-managed-environment")
- ❌ **Without venv**: pre-push hook tests fail with `ModuleNotFoundError: No module named 'click'`
- ❌ **Without venv**: `make release` pre-release checks fail
- ✅ **With venv**: All commands work correctly

**Common symptoms of not using venv**:
- `ModuleNotFoundError: No module named 'click'`
- `ModuleNotFoundError: No module named 'pytest_bdd'`
- `error: externally-managed-environment` when running pip
- Tests fail during `git push` (pre-push hook)

**Always check before working**:
```bash
# Quick check - should show .venv in path
which python3
# ✅ Good: /Users/xxx/codeindex/.venv/bin/python3
# ❌ Bad:  /opt/homebrew/bin/python3 (system Python)
```

---

### Quick Start Commands

```bash
# 🚀 Most common: Generate all indexes
codeindex scan-all --fallback

# 📄 Parse single file (NEW in v0.13.0)
codeindex parse src/myfile.py | jq .                  # Parse Python file
codeindex parse Controller.php | jq '.symbols'       # Extract symbols only

# View what will be scanned
codeindex list-dirs

# Generate global symbol index
codeindex symbols

# Check indexing coverage
codeindex status

# 🔧 Generate JSON output (for tool integration, e.g., LoomGraph)
codeindex scan-all --output json > parse_results.json
codeindex scan ./src --output json                    # Single directory
codeindex scan ./src --output json | jq .             # View formatted JSON

# Git Hooks management
codeindex hooks status
codeindex hooks install --all
```

### TDD Development Flow (Required)

**This project strictly follows TDD**:

1. **Red** - Write failing tests
   ```bash
   pytest tests/test_new_feature.py -v
   # Expected: Tests fail ❌
   ```

2. **Green** - Minimal implementation to pass
   ```bash
   pytest tests/test_new_feature.py -v
   # Expected: Tests pass ✅
   ```

3. **Refactor** - Optimize while keeping tests green
   ```bash
   pytest  # All tests pass
   ruff check src/  # Code style check
   ```

### GitFlow Branch Strategy

```
master (production, v0.5.0)
├── develop (main development)
│   ├── feature/epic7-xxx (Java support)
│   ├── feature/epic8-xxx
│   └── hotfix/xxx
```

**Rules**:
- `master`: Only merge from develop, tag each merge
- `develop`: Main development branch
- `feature/*`: Epic/Story feature branches
- `hotfix/*`: Emergency fixes, can merge directly to master

**Commit message format**:
```
feat(scope): add new feature
fix(scope): fix bug
docs(scope): update documentation
test(scope): add tests
refactor(scope): refactor code
```

### Pre-commit Checklist

```bash
# ✅ 1. All tests pass
pytest -v

# ✅ 2. Code style check
ruff check src/

# ✅ 3. Type check (if applicable)
mypy src/

# ✅ 4. Coverage (optional)
pytest --cov=src/codeindex --cov-report=term-missing
# Recommended: Core modules ≥90%, Overall ≥80%
```

### Documentation Update Rules

| Change Type | Documents to Update |
|-------------|---------------------|
| New feature | CHANGELOG.md, README.md, relevant README_AI.md |
| Bug fix | CHANGELOG.md |
| Config change | .codeindex.yaml example, docs/guides/configuration.md, CHANGELOG.md |
| API change | README.md, docstrings |
| Major release | CHANGELOG.md, RELEASE_NOTES_vX.X.X.md |
| Architecture decision | docs/architecture/adr-xxx.md |

**After code changes, regenerate indexes**:
```bash
codeindex scan-all --fallback
# Or specific directories:
codeindex scan src/codeindex --fallback
codeindex scan tests --fallback
```

### Documentation Maintenance (Post-Epic)

**When an Epic is completed**, follow these steps to maintain docs structure:

#### 1. Update ROADMAP.md (Required)

```bash
# Update version and epic status
# See: docs/planning/ROADMAP.md
# - Current Version: vX.X.X
# - Move epic from "Active" to "Completed"
# - Update version history table
# - Add release notes
```

#### 2. Archive Epic Documents (Required)

```bash
# Move completed epic to archived location
mv docs/planning/active/epicN-name.md \
   docs/planning/completed/epicN-name/plan.md

# Add validation report (if exists)
# Add any story/task documents to same directory
```

#### 3. Update Planning Index (Required)

```bash
# Update docs/planning/README.md
# - Move epic from "Active" to "Completed" section
# - Add completion date
# - Link to archived documents
```

#### 4. Keep Active/ Clean (Important)

**Rule**: `docs/planning/active/` should ONLY contain:
- Current sprint work (in-progress epics)
- Next 1-2 planned epics (not started yet)

**When to move**:
- ✅ Move to `completed/` when epic is done
- ✅ Keep in `active/` if planned for next version
- ❌ Don't accumulate old plans in `active/`

#### 5. Example: After Epic 7 (Java Support) Completes

```bash
# Step 1: Update ROADMAP.md
vim docs/planning/ROADMAP.md
# - Current Version: v0.6.0 → v0.7.0
# - Epic 7: Active → Completed
# - Add v0.7.0 release notes

# Step 2: Archive Epic 7
mkdir -p docs/planning/completed/epic7-java-support
mv docs/planning/active/epic7-java-support.md \
   docs/planning/completed/epic7-java-support/plan.md
# Add validation report if exists

# Step 3: Update index
vim docs/planning/README.md
# Move Epic 7 from Active to Completed table

# Step 4: Commit
git add docs/
git commit -m "docs: archive Epic 7 (Java Support) for v0.7.0"
```

### Requirements & Planning Workflow

codeindex uses a **dual-track system** for requirements management:

**System**:
- **Planning Documents** (`docs/planning/*.md`) - Long-term vision, Epic/Story design
- **GitHub Issues** - Execution tracking, collaboration, task management

**Workflow Overview**:
1. **Strategic Planning** → Update `ROADMAP.md` (quarterly)
2. **Epic Design** → Create `epicN-name.md` + GitHub Issue (epic label)
3. **Story Breakdown** → Create Story issues (feature label, linked to Epic)
4. **Development** → Feature branch + TDD + commits (Refs #N)
5. **Completion** → PR merge (Closes #N) + update ROADMAP.md

**Quick Start**:
```bash
# Create Epic plan
vim docs/planning/epic7-java-support.md
gh issue create --title "Epic 7: Java Support" --label epic

# Create Story issue
gh issue create --title "Story 7.1: Java Parser" \
  --label feature --milestone v0.6.0 --body "Part of: #1"

# Development
git checkout -b feature/java-parser
# ... TDD development ...
git commit -m "feat(parser): add Java parser\n\nRefs #2"
gh pr create --title "feat: Java parser support" --body "Closes #2"
```

**Detailed Guide**: See `docs/development/requirements-workflow.md`

**Key Principles**:
- Planning docs provide context and design (version controlled)
- GitHub Issues enable collaboration and tracking (automation)
- Link everything: planning docs ↔ issues ↔ commits ↔ PRs
- Update ROADMAP.md regularly (single source of truth)

---

## 🎨 Part 2.5: Design Philosophy & Principles

**⚠️ WHEN TO READ THIS SECTION**:

You MUST read the detailed design philosophy document when:
- 🏗️ **Adding new language support** (e.g., Java, Go, TypeScript)
- 🔧 **Implementing new features** that involve ParseResult or core architecture
- 🐛 **Debugging performance issues** or considering optimization
- 🤔 **Discussing parallelization strategies** (ThreadPool vs ProcessPool)
- 💡 **Making architectural decisions** (e.g., AI vs programmatic approach)
- ❓ **Questioning existing design choices** ("Why is it designed this way?")

**Quick triggers** - Read design doc if you encounter:
- Questions about "Why not use ProcessPool for Java?"
- Confusion about ParseResult's purpose
- Debates about AI vs programmatic analysis
- Performance optimization discussions
- New language integration planning

---

### Core Principles (Quick Reference)

**Key principle**: We extract structure (What), AI understands semantics (Why)

**Architecture**: 3 layers
1. Structure Extraction (tree-sitter) → ParseResult
2. Automated Analysis (programmatic) → Routes, scoring, debt
3. AI Enhancement (semantic) → Documentation

**Performance**: AI invocation is the bottleneck (99% of time), not parsing

**Parallelization**: ThreadPool for all languages (I/O bound, not CPU bound)

---

### 📖 Full Documentation

**Read the complete design philosophy**:
- **File**: `docs/architecture/design-philosophy.md`
- **Use Read tool**: Always read this file before making architectural decisions
- **Covers**: ParseResult design, performance architecture, common pitfalls, language support

```bash
# When to read
Read(file_path="docs/architecture/design-philosophy.md")
```

---

## 🏗️ Part 3: Architecture Reference

### Core Pipeline

1. **Scanner** (`scanner.py`) - Directory walking, file filtering → `ScanResult`
2. **Parser** (`parser.py`) - Symbol extraction via tree-sitter → `ParseResult`
3. **Writer** (`writer.py`) - Format prompts, write outputs
4. **Invoker** (`invoker.py`) - Execute AI CLI, handle timeouts
5. **CLI** (`cli.py`) - Command orchestration

**Data Flow**:
```
Directory → Scanner → [files] → Parser → [ParseResult] →
Writer (format) → Invoker (AI CLI) → Writer (write) → README_AI.md
```

### Key Data Types

- `ScanResult`: path, files, subdirs
- `ParseResult`: path, symbols, imports, module_docstring, error
- `Symbol`: name, kind, signature, docstring, line_start, line_end
- `Import`: module, names, is_from
- `Config`: Loaded from `.codeindex.yaml`

### Configuration

**File**: `.codeindex.yaml` (see `examples/.codeindex.yaml`)

**Key sections**:
```yaml
version: 1
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

include:        # Directories to scan
  - src/
exclude:        # Patterns to skip
  - "**/__pycache__/**"
languages:      # Supported: python, php, java, typescript, javascript
  - python
output_file: README_AI.md

# Optional: Adaptive symbols (v0.2.0+)
symbols:
  adaptive_symbols:
    enabled: true

# Optional: AI enhancement (v0.3.0+)
ai_enhancement:
  strategy: "selective"

# Optional: Tech debt thresholds (v0.3.0+)
tech_debt:
  file_size:
    large_threshold: 2000
```

**Config help**: `codeindex config explain <parameter>`

### Build & Development

```bash
# Install (development mode)
pip install -e .
pip install -e ".[dev]"

# Run tests
pytest
pytest tests/test_parser.py::test_parse_simple_function

# Lint
ruff check src/

# CLI usage
codeindex scan ./src/auth
codeindex scan ./src/auth --fallback
codeindex scan ./src/auth --dry-run
codeindex init
codeindex status
```

---

## 🔌 Part 4: Extension Development

### Adding Framework Support

**Plugin-based route extraction** for web frameworks (ThinkPHP, Spring, Laravel, etc.)

**Quick steps**:
1. Write tests first: `tests/extractors/test_myframework.py`
2. Implement extractor: `src/codeindex/extractors/myframework.py`
3. Auto-registered via `extractors/__init__.py`

**Reference implementation**: `src/codeindex/extractors/thinkphp.py`

---

### Git Hooks Integration

**Built-in hooks** for code quality and auto-documentation

**Features**:
- pre-commit: lint + debug checks
- post-commit: auto README updates
- pre-push: test validation

**Management**: `codeindex hooks install/uninstall/status`

**User guide**: `docs/guides/git-hooks-integration.md`

---

## 📈 Version History

**Current version**: v0.18.0

For complete version history, see:
- **[CHANGELOG.md](CHANGELOG.md)** - Detailed changes for each version
- **[RELEASE_NOTES_v*.md](.)** - Major release highlights

---

## 🚨 Common Mistakes to Avoid

### ❌ Wrong Approaches

1. **Directly modify generated README_AI.md**
   - It will be overwritten
   - ✅ Correct: Modify source docstrings, regenerate

2. **Skip tests, write implementation first**
   - Violates TDD
   - ✅ Correct: Write tests first, then implement

3. **Use Glob/Grep for code exploration**
   - Inefficient, misses context
   - ✅ Correct: Use Serena MCP tools (find_symbol, etc.)

4. **Ignore README_AI.md before modifying code**
   - May miss design intent
   - ✅ Correct: Read README_AI.md first, understand architecture

5. **Commit directly to develop/master**
   - Violates GitFlow
   - ✅ Correct: Create feature branch, merge after review

6. **Run commands without activating virtual environment**
   - pre-push hooks fail with `ModuleNotFoundError`
   - pip install fails with "externally-managed-environment" error
   - `make release` pre-release checks fail
   - ✅ Correct: Always `source .venv/bin/activate` first

### ✅ Best Practices

**Environment setup flow** (do this FIRST):
```
Check current Python → source .venv/bin/activate → Verify venv active →
which python3 (check .venv in path) → Ready to work
```

**Code understanding flow**:
```
README_AI.md → find_symbol → Read source → Write tests → Implement
```

**Feature modification flow**:
```
Create feature branch → TDD development → Tests pass →
ruff check → Update CHANGELOG → Commit → Merge to develop
```

**Release flow**:
```
Merge develop to master → Run all tests → Create tag →
Generate RELEASE_NOTES → Push to GitHub
```

---

## 📚 Documentation Structure

```
codeindex/
├── README.md                       # User overview
├── CLAUDE.md                       # This file (developer guide)
├── CHANGELOG.md                    # Version history
├── RELEASE_NOTES_*.md              # Major releases
├── PROJECT_SYMBOLS.md              # Global symbol index
├── examples/
│   ├── .codeindex.yaml            # Config example
│   ├── ai-integration-guide.md    # AI Code integration
│   └── CLAUDE.md.template         # User project template
├── docs/
│   ├── guides/
│   │   ├── configuration.md       # Config reference
│   │   ├── git-hooks-integration.md   # Git Hooks user guide
│   │   └── claude-code-integration.md # Claude Code setup
│   ├── planning/
│   │   └── epic*.md               # Design decisions
│   └── evaluation/
│       └── *.md                   # Validation reports
└── src/codeindex/
    └── README_AI.md               # Core module architecture
```

---

---

## 💡 Quick Reference Card

### Most Common Commands

```bash
# Generate all indexes
codeindex scan-all --fallback

# Parse single file (NEW in v0.13.0)
codeindex parse src/myfile.py | jq .

# Check what will be scanned
codeindex list-dirs

# View indexing status
codeindex status

# Pre-commit checks
pytest -v && ruff check src/

# After code changes (regenerate docs)
codeindex scan-all --fallback
```

### Need Detailed Guides?

| Topic | Document |
|-------|----------|
| **Requirements Management** | `docs/development/requirements-workflow.md` |
| **Configuration Reference** | `docs/guides/configuration.md` |
| **Framework Route Extraction** | See CLAUDE.md Part 4 or `docs/guides/` |
| **Git Hooks Integration** | `docs/guides/git-hooks-integration.md` |
| **Claude Code Setup** | `docs/guides/claude-code-integration.md` |

### Key Principles

- **Always TDD**: Red → Green → Refactor
- **Always use Serena MCP**: find_symbol > Glob/Grep
- **Always read README_AI.md first**: Best entry point
- **Always feature branches**: Never commit to develop/master directly
- **Always reference issues**: "Refs #N" in commits, "Closes #N" in PRs

### Test Coverage Requirements

- Core modules: ≥90%
- Overall: ≥80%

### Configuration Compatibility

All versions 100% backward compatible (v0.1.0 → v0.5.0)

---

**Last Updated**: 2026-02-04
**codeindex Version**: v0.6.0
**For**: Claude Code and contributors

---

## 🔍 代码搜索 (LoomGraph)

本项目已用 LoomGraph 索引，可使用以下命令：

### 基本命令

- `loomgraph search "<查询>"` - 语义搜索代码
- `loomgraph graph "<类名.方法名>"` - 查询调用关系
- `loomgraph status` - 检查服务状态
- `loomgraph index .` - 重新索引代码库

### 使用示例

**语义搜索**：
```bash
# 搜索符号评分相关代码
loomgraph search "symbol scoring logic"

# 搜索配置管理
loomgraph search "adaptive configuration"
```

**调用关系查询**：
```bash
# 查询某个函数的调用者
loomgraph graph "Parser.parse" --direction callers

# 查询某个函数调用了什么
loomgraph graph "Parser.parse" --direction callees
```

### 注意事项

- ⚠️ 代码变更后需要重新索引
- ⚠️ 首次索引可能需要几分钟
- ⚠️ 跨文件依赖警告（如标准库）是正常现象

**服务信息**:
- LightRAG API: http://117.131.45.179:3020
- Embedding: http://117.131.45.179:3002
- Model: jinaai/jina-embeddings-v2-base-code

