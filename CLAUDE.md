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
| `docs/guides/configuration-changelog.md` | Config version history | Configuration upgrades |

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

### Quick Start Commands

```bash
# 🚀 Most common: Generate all indexes
codeindex scan-all --fallback

# View what will be scanned
codeindex list-dirs

# Generate global symbol index
codeindex symbols

# Check indexing coverage
codeindex status

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
| Config change | .codeindex.yaml example, docs/guides/configuration.md, docs/guides/configuration-changelog.md |
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
languages:      # Currently: python only
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

**Upgrade guide**: `docs/guides/configuration-changelog.md`

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

### Framework Route Extraction (v0.5.0+)

**Quick overview**: Plugin-based architecture for extracting framework routes

**Architecture**:
```
src/codeindex/
├── route_extractor.py      # Base class
├── route_registry.py       # Auto-discovery
└── extractors/
    ├── thinkphp.py        # ✅ Reference implementation
    ├── laravel.py         # 🔄 TODO
    └── fastapi.py         # 🔄 TODO
```

**How to add a framework**:
1. Write tests first (`tests/extractors/test_myframework.py`)
2. Implement extractor (`src/codeindex/extractors/myframework.py`)
3. Export in `extractors/__init__.py`
4. Auto-registered!

**Detailed guide**: See `CLAUDE.md` section 🛣️ Framework Route Extraction (lines 225-899) or ask for the full guide.

**Reference**:
- Example: `src/codeindex/extractors/thinkphp.py`
- Tests: `tests/extractors/test_thinkphp.py`
- Base class: `src/codeindex/route_extractor.py`

### Git Hooks Management (v0.5.0+)

**Quick overview**: Built-in Git Hooks for code quality and auto-documentation

**Architecture**:
```
┌─────────────────────────────────────┐
│  HookManager                        │
│  ├── install()                      │
│  ├── uninstall()                    │
│  └── status()                       │
├─────────────────────────────────────┤
│  .git/hooks/                        │
│  ├── pre-commit  (lint + debug)    │
│  ├── post-commit (auto README)     │
│  └── pre-push    (placeholder)     │
└─────────────────────────────────────┘
```

**Features**:
- Marker-based detection (`# codeindex-managed hook`)
- Automatic backup of custom hooks
- Template-based script generation
- CLI management (`codeindex hooks install/uninstall/status`)

**Detailed guide**: See `CLAUDE.md` section 🪝 Git Hooks Management (lines 901-1738) or ask for the full guide.

**Reference**:
- Implementation: `src/codeindex/cli_hooks.py`
- Tests: `tests/test_cli_hooks.py`
- User guide: `docs/guides/git-hooks-integration.md`

---

## 📈 Version History (Highlights)

### v0.5.0 (2026-02-03)
- **Documentation improvements**: Configuration upgrade guide, CLAUDE.md refactoring
- **Git Hooks integration** (Epic 6, P3.1): Pre-commit lint + debug detection, post-commit auto README updates
- **ThinkPHP route extraction**: Framework plugin architecture
- 394 tests passing

### v0.4.0 (2026-02-02)
- KISS Universal Description Generator
- Cross-language, cross-architecture support
- -78 lines, more powerful

### v0.4.0 (2026-02-04)
- **BREAKING**: Removed AI Enhancement (multi-turn dialogue)
- Added AI-Powered Docstring Extraction (Epic 9)
- Simplified scan-all (SmartWriter only)
- 415 tests passing

### v0.3.1 (2026-01-28)
- CLI module split (1062 → 31 lines in cli.py)
- 6 focused modules

### v0.3.0 (2026-01-27)
- Technical debt analysis
- 283 tests passing

### v0.2.0 (2025-01-15)
- Adaptive symbol extraction (5-150 symbols/file)
- 7-tier file size classification
- 280% coverage improvement for large files

See `CHANGELOG.md` for complete history.

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

### ✅ Best Practices

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
│   │   ├── configuration-changelog.md  # Config version history
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
| **Configuration Upgrades** | `docs/guides/configuration-changelog.md` |
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

**Last Updated**: 2026-02-03
**codeindex Version**: v0.5.0
**For**: Claude Code and contributors
