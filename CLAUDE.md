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

**Scenario 1: Understand adaptive symbol extraction**
```
1. Read src/codeindex/README_AI.md
   → Find "AdaptiveSymbolSelector" component
2. Use find_symbol(name_path_pattern="AdaptiveSymbolSelector")
   → View class definition and methods
3. Read docs/planning/epic2-adaptive-symbols-plan.md
   → Understand design decisions
4. Read tests/test_adaptive_selector.py
   → See usage examples and edge cases
```

**Scenario 2: Find all uses of `file_lines`**
```
1. Use search_for_pattern(substring_pattern="file_lines")
   → Get all references
2. Use find_symbol to view core definition
3. Use find_referencing_symbols for dependency analysis
```

**Scenario 3: Modify symbol scoring algorithm**
```
1. Read src/codeindex/README_AI.md
   → Find SymbolImportanceScorer
2. Use get_symbols_overview("src/codeindex/symbol_scorer.py", depth=1)
   → View all scoring methods
3. Read tests/test_symbol_scorer.py
   → Understand scoring rules
4. Use find_referencing_symbols to assess impact
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
master (production, v0.5.0-beta1)
├── develop (main development)
│   ├── feature/epic6-xxx
│   ├── feature/epic7-xxx
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

**Dual-Track System**: GitHub Issues + Planning Documents

#### Planning Documents (Long-term Vision)

**Location**: `docs/planning/`

**Structure**:
```
docs/planning/
├── ROADMAP.md                    # Strategic roadmap (1-2 years)
├── epic7-java-support.md         # Epic: Detailed design
├── story-7.1-java-parser.md      # Story: Implementation plan
└── v0.6.0-execution-plan.md      # Version: Release plan
```

**When to create**:
- **ROADMAP.md**: Major feature planning, priority decisions
- **Epic Plan**: Large feature (2+ weeks), architectural decisions
- **Story Plan**: Complex story requiring detailed design
- **Version Plan**: Release planning, feature bundling

#### GitHub Issues (Execution & Collaboration)

**When to create**:
- Each Epic → GitHub Issue (Epic label)
- Each Story → GitHub Issue (links to Epic)
- Each Bug → GitHub Issue (bug label)
- Each Task → Optional (if needs discussion)

**Labels**:
- `epic`: Major feature (Epic 7: Java Support)
- `feature`: User-facing feature
- `enhancement`: Improvement to existing feature
- `bug`: Bug fix
- `documentation`: Documentation only
- `priority:high/medium/low`: Priority

**Milestones**:
- v0.6.0 - Java Support
- v0.7.0 - Multi-language Support
- v1.0.0 - Production Ready

#### Complete Workflow

**1. Strategic Planning** (Quarterly)
```bash
# Create/Update ROADMAP.md
vim docs/planning/ROADMAP.md

# Define next 2-3 versions
# Set priorities based on user feedback
```

**2. Epic Design** (Before starting large feature)
```bash
# Create Epic plan
vim docs/planning/epic7-java-support.md

# Include:
# - User stories
# - Technical approach
# - Dependencies
# - Success criteria

# Create GitHub Issue
# Title: "Epic 7: Java Language Support"
# Label: epic, priority:high
# Link to: docs/planning/epic7-java-support.md
```

**3. Story Breakdown** (Sprint planning)
```bash
# For each story in Epic:
# 1. Create GitHub Issue
#    Title: "Story 7.1: Java Parser (tree-sitter)"
#    Label: feature
#    Milestone: v0.6.0
#    Links to: Epic 7 issue

# 2. Create detailed plan (if complex)
vim docs/planning/story-7.1-java-parser.md
```

**4. Development** (Daily)
```bash
# Create feature branch
git checkout -b feature/java-parser

# TDD development
# Commit with issue reference
git commit -m "feat(parser): add Java parser

Implements basic Java parsing with tree-sitter.

Refs #123"

# Create PR
gh pr create --title "feat: Java parser support" \
  --body "Closes #123"
```

**5. Completion**
```bash
# PR merged → Issue auto-closes
# Update ROADMAP.md status
# Document in CHANGELOG.md
```

#### Best Practices

**Planning Documents**:
- ✅ Version controlled (track evolution)
- ✅ Include design decisions and rationale
- ✅ Update status as work progresses
- ✅ Link to GitHub Issues

**GitHub Issues**:
- ✅ Clear, actionable titles
- ✅ Link to planning documents
- ✅ Use issue templates (create them)
- ✅ Reference in commits/PRs
- ✅ Close when done (via PR merge)

**Don't**:
- ❌ Duplicate content (Issue vs Planning Doc)
- ❌ Create issues for trivial tasks
- ❌ Let issues go stale (close or update)
- ❌ Forget to update ROADMAP.md

#### Issue Templates

Create `.github/ISSUE_TEMPLATE/`:

**epic.md**:
```markdown
---
name: Epic
about: Major feature requiring multiple stories
labels: epic
---

## Epic Overview
[Brief description]

## User Stories
- [ ] Story 1: [description]
- [ ] Story 2: [description]

## Planning Document
See: `docs/planning/epicN-name.md`

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

**feature.md**:
```markdown
---
name: Feature/Story
about: User-facing feature or story
labels: feature
---

## Description
[What does this feature do?]

## Epic
Part of: #N (Epic issue)

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes
[Implementation approach]
```

**Example: Java Support Workflow**

```
1. Strategic Decision (ROADMAP.md):
   - Java support is top priority for v0.6.0
   - Rationale: Large enterprise Java projects need indexing

2. Epic Planning:
   - Create docs/planning/epic7-java-support.md
   - Design: Parser, Spring Routes, Maven detection
   - Create GitHub Issue #1: "Epic 7: Java Language Support"

3. Story Breakdown:
   - Issue #2: "Story 7.1: Java Parser (tree-sitter)"
   - Issue #3: "Story 7.2: Spring Framework Routes"
   - Issue #4: "Story 7.3: Maven/Gradle Detection"
   All linked to Epic #1, Milestone v0.6.0

4. Development:
   - Branch: feature/java-parser
   - TDD: Write tests, implement
   - Commit: "feat(parser): add Java parser\n\nRefs #2"
   - PR: "feat: Java parser support\n\nCloses #2"

5. Completion:
   - PR merged → Issue #2 closes
   - Update ROADMAP.md: Story 7.1 ✅
   - Continue to Issue #3
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

### v0.5.0-beta1 (2026-02-02)
- Git Hooks integration (Epic 6, P3.1)
- Pre-commit: lint + debug detection
- Post-commit: auto README updates
- 394 tests passing

### v0.4.0 (2026-02-02)
- KISS Universal Description Generator
- Cross-language, cross-architecture support
- -78 lines, more powerful

### v0.3.1 (2026-01-28)
- CLI module split (1062 → 31 lines in cli.py)
- 6 focused modules

### v0.3.0 (2026-01-27)
- AI Enhancement module
- Multi-turn dialogue for super large files
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

## 💡 Quick Reference

**Need detailed implementation guides?**
- Framework Route Extraction: Lines 225-899 in full CLAUDE.md (ask if needed)
- Git Hooks Development: Lines 901-1738 in full CLAUDE.md (ask if needed)
- Or see dedicated documentation in `docs/guides/`

**Configuration upgrades?**
- See: `docs/guides/configuration-changelog.md`
- All versions 100% backward compatible

**Test coverage requirements?**
- Core modules: ≥90%
- Overall: ≥80%

**Before committing?**
```bash
pytest -v && ruff check src/
```

**After code changes?**
```bash
codeindex scan-all --fallback
```

---

**Last Updated**: 2026-02-03
**codeindex Version**: v0.5.0-beta1
**For**: Claude Code and contributors
