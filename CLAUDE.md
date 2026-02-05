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

### Core Design Philosophy

**"ParseResult is a programmable data structure, not just text for AI"**

codeindex's core value proposition:
1. **Extract structured, programmable code information** (our role)
2. **Support multiple automated analyses** (route extraction, symbol scoring, dependency analysis)
3. **Provide AI enhancement** (AI understands semantics, writes documentation)

**Key principle**: We extract structure (What), AI understands semantics (Why)

---

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Structure Extraction (tree-sitter)        │
│  - Parse source code to AST                         │
│  - Extract symbols, signatures, annotations         │
│  - Build ParseResult (programmable data structure)  │
│  - Languages: Python, PHP, Java (future: Go, Rust) │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│  Layer 2: Automated Analysis (programmatic)         │
│  - Route extraction (Spring/ThinkPHP/Laravel)       │
│  - Symbol scoring (importance ranking)              │
│  - Dependency analysis (import graphs)              │
│  - Technical debt detection                         │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│  Layer 3: AI Enhancement (semantic understanding)   │
│  - Understand business intent                       │
│  - Summarize architecture and design patterns       │
│  - Write README documentation                       │
│  - Extract and normalize docstrings                 │
└─────────────────────────────────────────────────────┘
```

---

### ParseResult Multi-Purpose Design

**Data Structure**:
```python
@dataclass
class ParseResult:
    symbols: list[Symbol]      # Classes, functions, methods
    imports: list[Import]      # Import statements
    namespace: str             # Package name/namespace
    annotations: list          # Decorators/annotations (Java/Python)
```

**Usage 1: Format for AI** → Generate README_AI.md
**Usage 2: Route extraction** → Programmatically traverse symbols/annotations (Story 7.2)
**Usage 3: Symbol scoring** → Rank importance based on annotations (Story 7.4)
**Usage 4: Fallback mode** → Generate README without AI
**Usage 5: Global symbol index** → PROJECT_SYMBOLS.md
**Usage 6: Dependency analysis** → Analyze import relationships

**Critical insight**: ParseResult is not just for AI consumption—it's a programmable data structure for automated analysis.

---

### Performance Architecture

#### The Real Bottleneck: AI Invocation (not tree-sitter)

**Time breakdown**:
```
Directory scan:       0.05s (10 files)
tree-sitter parsing:  0.1s  (10 files, ThreadPool)
Format prompt:        0.01s
AI invocation:        10s   ← 99% of time!
Write file:           0.01s

Total: ~10s
```

**Key insights**:
1. ✅ **tree-sitter is fast** - even large Java files parse in milliseconds
2. ✅ **AI invocation is slow** - I/O bound, waiting for network/process response
3. ✅ **ThreadPool is sufficient** - I/O operations not limited by Python GIL
4. ❌ **ProcessPool NOT needed** - AI invocation is I/O bound, not CPU bound

---

### Parallelization Strategy

**Current implementation**: `src/codeindex/parallel.py`

```python
def parse_files_parallel(files, config):
    """Use ThreadPoolExecutor for parallel parsing"""
    with ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
        # Parse files in parallel (tree-sitter fast, no bottleneck)
        results = list(executor.map(parse_file, files))
```

**Why ThreadPool instead of ProcessPool?**
1. ✅ tree-sitter parsing is fast (milliseconds), not a bottleneck
2. ✅ AI invocation is I/O bound (not limited by GIL)
3. ✅ ThreadPool starts quickly, lower memory overhead
4. ❌ ProcessPool for CPU-bound tasks, not applicable here

**Real optimization target**: Parallelize scanning multiple directories (scan-all)
```
Current: Sequential processing of 50 directories × 10s = 500s
Optimized: Parallel processing with 8 workers = 62.5s (8x faster)
```

---

### Adding New Language Support

#### ⚠️ CRITICAL: Common Misconceptions

**❌ WRONG**: "Different languages need different parallelization strategies"
- Java files are large → need ProcessPool
- Python files are small → use ThreadPool

**✅ CORRECT**: All languages use the same strategy
- AI Command handles all languages uniformly
- tree-sitter is fast for all languages
- Bottleneck is AI invocation (I/O bound)
- ThreadPool works for all languages

**Do NOT do this**:
```yaml
# ❌ WRONG design
parallel_strategy:
  python: threads
  java: processes    # Incorrect!
  go: threads
```

**Correct approach**:
```yaml
# ✅ CORRECT design
parallel_workers: 8  # Unified config for all languages
```

---

#### Checklist for Adding New Language (e.g., Go)

**Step 1: tree-sitter integration** (Required)
```python
# src/codeindex/parser.py
import tree_sitter_go as tsgo

GO_LANGUAGE = Language(tsgo.language())
PARSERS["go"] = Parser(GO_LANGUAGE)
FILE_EXTENSIONS[".go"] = "go"
```

**Step 2: Symbol extraction** (Required)
Priority:
- P0 (Must have): Classes, functions/methods, signatures, basic docstrings
- P1 (Important): Annotations/decorators, import statements, namespaces
- P2 (Optional): Generics, exceptions, lambdas, advanced features

**Reason**: P0 info sufficient for README, P1 needed for route extraction and symbol scoring

**Step 3: DO NOT add language-specific parallelization** ❌
- All languages use the same ThreadPool
- No need to distinguish by language
- AI Command handles all languages

**Step 4: Framework-specific features** (Optional)
If framework route extraction needed (e.g., Gin for Go):
- Create extractor plugin: `src/codeindex/extractors/gin_extractor.py`
- Depend on ParseResult.symbols annotations
- Follow ThinkPHP extractor plugin pattern

---

### Common Design Pitfalls

#### Pitfall 1: Over-reliance on AI ❌

**Wrong idea**: "Let AI do everything, we just pass source code"

**Problems**:
- ❌ Cannot support route extraction (needs programmatic traversal)
- ❌ Cannot support symbol scoring (needs structured data)
- ❌ Cannot support fallback mode
- ❌ Increases AI costs

**Correct approach**: We extract structure, AI understands semantics

---

#### Pitfall 2: Misidentifying bottlenecks ❌

**Wrong idea**: "Java file parsing is slow, need ProcessPool optimization"

**Reality**:
- ✅ tree-sitter is very fast (even large files are milliseconds)
- ✅ Real bottleneck is AI invocation (seconds, I/O bound)
- ✅ ThreadPool is already sufficient

**Correct optimization**: Parallelize multiple directory scanning, not single file parsing

---

#### Pitfall 3: Language-specific parallelization ❌

**Wrong idea**: "Java files large, need ProcessPool; Python files small, use ThreadPool"

**Reality**:
- ✅ AI Command handles all languages uniformly
- ✅ Bottleneck is AI invocation (not parsing)
- ✅ I/O bound tasks best served by ThreadPool

**Correct approach**: Unified ThreadPool with reasonable worker count

---

### Key Takeaways for Future Development

1. **ParseResult is multi-purpose** - Not just for AI, also for programs
2. **We extract structure, AI understands semantics** - Clear division of labor
3. **Bottleneck is AI invocation, not tree-sitter** - Don't over-optimize parsing
4. **ThreadPool works for all languages** - No need for language-specific strategies
5. **Annotation extraction is necessary** - Supports route extraction and symbol scoring

---

### Essential Reading

**Before adding new features, read**:
- Serena memory: `design_philosophy` (this document's source)
- Epic planning docs: `docs/planning/epic*.md`
- Architecture decisions: Search for "ADR-" in documentation

**When confused about design decisions**:
```python
# Read design philosophy memory
mcp__serena__read_memory(memory_file_name="design_philosophy")
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

### v0.6.0 (2026-02-04)
- **BREAKING**: Removed AI Enhancement (multi-turn dialogue)
- **Epic 9**: AI-Powered Docstring Extraction (hybrid + all-AI modes)
- PHP + Python docstring support
- Cost-effective: ~$0.15 per 250 directories
- 415 tests passing, 3 skipped

### v0.5.0 (2026-02-03)
- **Epic 6 P3.1**: Git Hooks Integration
- ThinkPHP route extraction (framework plugin architecture)
- Configuration upgrade guide
- 394 tests passing

### v0.4.0 (2026-02-02)
- KISS Universal Description Generator
- PROJECT_INDEX quality improvements
- Cross-language, cross-architecture support
- 299 tests passing

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

**Last Updated**: 2026-02-04
**codeindex Version**: v0.6.0
**For**: Claude Code and contributors
