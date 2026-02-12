# Epic 19: CLI UX Restructuring + Java Improvements

**Version**: v0.16.0
**Priority**: P0 (Blocking - affects all new users)
**Status**: Planning
**Created**: 2026-02-12
**Source**: User feedback from zcyl-backend Java microservice project

---

## Background

### Problem Statement

codeindex has two distinct value propositions:
1. **Code Parser** (core): Structural extraction of symbols, inheritance, calls, imports, docstrings
2. **AI Doc Generator** (optional): AI reads code and writes human-friendly documentation

However, the current CLI design implies AI is **required** for normal usage:
- `codeindex scan dir/` defaults to AI mode (fails without `ai_command`)
- `--fallback` is the structural mode, but the name implies "degraded/inferior"
- `codeindex init` prompts for AI CLI configuration as if it's mandatory
- Post-init message suggests `scan-all` which requires AI

Additionally, real-world Java project testing revealed:
- `scan-all` generates redundant README_AI.md in Java intermediate directories (31% waste)
- `tech-debt` requires manual `--recursive` for Java deep package structures
- `tech-debt` noise analysis falsely flags Java getter/setter as "low quality"

### Historical Context

```
v0.1.0  Structural output only → users said "not human-friendly"
v0.3.0  Added AI Enhancement (AI reads code, writes docs)
v0.6.0  Removed AI Enhancement, added AI Docstring Extraction
v0.15.1 Current: codeindex = structural parser + docstring extraction
        AI is only needed when code comments are poor quality
```

The product has evolved, but the CLI defaults haven't caught up.

### Design Principle

```
Layer 1 (core):     Structure extraction (symbols, inheritance, calls, imports)  ← No AI
Layer 2 (enhanced): Comment extraction (docstring/PHPDoc/JavaDoc)               ← No AI
Layer 3 (optional): AI reads code → supplements missing comments                ← AI CLI
Layer 4 (external): Cross-module understanding, semantic search                 ← LoomGraph
```

**Layer 1+2 covers 80%+ of use cases.** Layer 3 is only needed for poorly-documented code.

---

## Goals

1. **Default mode requires zero AI** — `codeindex scan-all` works out of the box
2. **AI enhancement is opt-in** — `--ai` flag when you want richer documentation
3. **Clear messaging** — help text, README, and init wizard reflect the actual value hierarchy
4. **Parser guidance** — `init` detects missing parsers and guides installation
5. **Java project quality** — no redundant READMEs, smart defaults, accurate tech-debt
6. **Backward compatible** — `--fallback` kept as deprecated no-op with warning

---

## Scope

### In Scope

| Change | Files | Description |
|--------|-------|-------------|
| Reverse scan default | `cli_scan.py` | Default = structural, `--ai` = AI-enhanced |
| Deprecate `--fallback` | `cli_scan.py` | Keep as no-op with deprecation warning |
| `--dry-run` with `--ai` only | `cli_scan.py` | Only meaningful when AI is invoked |
| Update init wizard | `cli_config.py`, `init_wizard.py` | AI config clearly optional |
| Parser detection in init | `init_wizard.py` | Check installed parsers, guide installation |
| Update help text | All CLI modules | Rewrite descriptions to reflect new defaults |
| Update README Quick Start | `README.md` | New user flow without AI dependency |
| Skip pass-through directories | `scanner.py` or `cli_scan.py` | Skip dirs with single subdir and no code files |
| Java auto-recursive tech-debt | `cli_tech_debt.py` | Auto `--recursive` when Java configured |
| Language-aware noise analysis | `tech_debt.py` | Java getter/setter not counted as noise |
| CHANGELOG entry | `CHANGELOG.md` | Breaking change documentation |

### Out of Scope (Separate Epics)

- Changing PyPI default dependencies (extras mechanism stays as-is)
- New language support (TypeScript/Go)
- LoomGraph integration changes

---

## Stories

### Story 19.1: Reverse scan/scan-all Default Behavior

**As a** new user,
**I want** `codeindex scan-all` to work without AI configuration,
**So that** I can get structural documentation immediately after init.

**Acceptance Criteria**:
- [ ] `codeindex scan dir/` generates structural README_AI.md (no AI required)
- [ ] `codeindex scan dir/ --ai` invokes AI CLI for enhanced documentation
- [ ] `codeindex scan-all` generates all README_AI.md files without AI
- [ ] `codeindex scan-all --ai` invokes AI for all directories
- [ ] `--fallback` is accepted but prints deprecation warning, behaves same as default
- [ ] `--dry-run` only works with `--ai` (prints error otherwise)
- [ ] `--ai` without configured `ai_command` gives clear error message
- [ ] All existing tests updated to reflect new defaults

**Implementation Notes**:

```python
# cli_scan.py - scan command changes

# NEW flag
@click.option("--ai", is_flag=True, help="Enable AI-enhanced documentation (requires ai_command in config)")

# DEPRECATED flag (keep for backward compat)
@click.option("--fallback", is_flag=True, hidden=True, help="[Deprecated] Structural mode is now the default")

# Logic:
# if --fallback: print deprecation warning
# if --ai: use AI CLI (current default behavior)
# else: structural mode (current --fallback behavior)
```

**Tests**:
- scan without --ai generates structural output
- scan with --ai invokes AI CLI
- scan with --fallback prints deprecation warning
- scan-all without --ai generates structural output
- --dry-run without --ai prints error
- --ai without ai_command prints clear error

---

### Story 19.2: Update Init Wizard and Post-Init Flow

**As a** new user,
**I want** `codeindex init` to lead me to immediate value,
**So that** I can see results within 1 minute of installing.

**Acceptance Criteria**:
- [ ] AI CLI configuration step clearly marked as "Optional Enhancement"
- [ ] Non-interactive mode (`--yes`) skips AI config entirely
- [ ] Post-init message suggests `codeindex scan-all` (works immediately)
- [ ] Optional next step mentions `--ai` for enhanced docs
- [ ] Generated `.codeindex.yaml` has `ai_command` commented out or in optional section

**Post-init output**:
```
✓ Setup complete!

Created: .codeindex.yaml

Next steps:
  1. codeindex scan-all          → Generate structural documentation
  2. codeindex status            → Check coverage

Optional: AI-enhanced documentation
  Edit .codeindex.yaml to set ai_command, then:
  codeindex scan-all --ai        → AI-enhanced documentation
```

---

### Story 19.3: Update Help Text and Documentation

**As a** user reading help text or README,
**I want** to understand that codeindex works without AI,
**So that** I'm not blocked by AI CLI configuration.

**Acceptance Criteria**:
- [ ] `codeindex --help` top-level description reflects parser-first positioning
- [ ] `codeindex scan --help` clearly shows structural is default, AI is optional
- [ ] README.md Quick Start rewritten: install → init → scan-all (no AI step)
- [ ] README.md has separate "AI Enhancement" section (optional)

**README Quick Start (new)**:
```markdown
## Quick Start

### 1. Install
pip install ai-codeindex[all]

### 2. Initialize
cd /your/project
codeindex init

### 3. Generate Documentation
codeindex scan-all
# → Generates README_AI.md in every source directory

### 4. (Optional) AI Enhancement
# For richer documentation, configure AI in .codeindex.yaml:
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
# Then:
codeindex scan-all --ai
```

---

### Story 19.4: Parser Installation Detection and Guidance

**As a** new user who installed `pip install ai-codeindex`,
**I want** `codeindex init` to detect missing language parsers and guide me to install them,
**So that** I don't hit confusing errors when I run `scan-all`.

**Problem**: `pip install ai-codeindex` (without extras) installs zero language parsers.
User runs `codeindex scan-all` → fails with "tree-sitter-python not found".

**Acceptance Criteria**:
- [ ] `codeindex init` checks which `tree-sitter-*` parsers are installed
- [ ] Cross-references with detected project languages (e.g., found `.java` files)
- [ ] If project has files for a language but parser is missing → clear warning + install command
- [ ] Non-interactive mode (`--yes`) prints warnings but doesn't block
- [ ] If zero parsers installed → prominent warning with install command

**Init output example**:
```
Detecting project languages...
  Found: .py (142 files), .java (87 files), .php (23 files)

Checking installed parsers...
  ✓ Python parser installed
  ✗ Java parser NOT installed
  ✗ PHP parser NOT installed

⚠ Missing parsers for detected languages!
  Install with: pip install ai-codeindex[java,php]
  Or install all: pip install ai-codeindex[all]
```

**Implementation Notes**:

```python
def check_parser_installed(language: str) -> bool:
    """Check if tree-sitter parser for language is importable."""
    import_map = {
        "python": "tree_sitter_python",
        "php": "tree_sitter_php",
        "java": "tree_sitter_java",
    }
    try:
        __import__(import_map[language])
        return True
    except ImportError:
        return False
```

**Tests**:
- init with all parsers installed → no warning
- init with missing parser for detected language → warning + install command
- init with zero parsers → prominent warning
- non-interactive mode prints warnings but completes

---

### Story 19.5: Skip Pass-Through Directories in scan-all

**As a** Java developer,
**I want** `codeindex scan-all` to skip intermediate directories that have no code files,
**So that** I don't get 20+ redundant README_AI.md files in my Maven project.

**Problem**: Maven standard directory structure `src/main/java/com/zcyl/...` generates
README_AI.md at every level. 31% of generated files are redundant pass-throughs
with content identical to their child directory.

**Approach**: Universal rule (not Java-specific) — skip any directory that:
1. Has no code files of its own (only subdirectories)
2. Has exactly one subdirectory (pure pass-through)

This handles Java `src/main/java/com/zcyl/` as well as any language with deep nesting.

**Acceptance Criteria**:
- [ ] `find_all_directories` skips directories with single subdir and zero code files
- [ ] Java `src/`, `main/`, `com/`, `com/zcyl/` are correctly skipped
- [ ] Directories with code files are never skipped (even if they have one subdir)
- [ ] Directories with multiple subdirs are never skipped (navigation value)
- [ ] `list-dirs` output reflects the filtering
- [ ] Existing Python/PHP projects unaffected (they rarely have deep pass-throughs)

**Example** (zcyl-gateway-core):
```
Before (v0.15.1): 6 directories indexed
  zcyl-gateway-core/src/                          ← skip (pass-through)
  zcyl-gateway-core/src/main/                     ← skip (pass-through)
  zcyl-gateway-core/src/main/java/                ← skip (pass-through)
  zcyl-gateway-core/src/main/java/com/            ← skip (pass-through)
  zcyl-gateway-core/src/main/java/com/zcyl/       ← skip (pass-through)
  zcyl-gateway-core/src/main/java/com/zcyl/gateway/  ← KEEP (has code files)

After: 1 directory indexed (the one with actual code)
```

**Implementation Notes**:

```python
# In scanner.py find_all_directories, after collecting dirs_to_index:
def is_pass_through(dir_path: Path, config: Config) -> bool:
    """Check if directory is a pass-through (no code files, single subdir)."""
    supported_exts = get_language_extensions(config.languages)

    subdirs = [item for item in dir_path.iterdir()
               if item.is_dir() and not should_exclude(item, config.exclude, root)]
    code_files = [item for item in dir_path.iterdir()
                  if item.is_file() and item.suffix in supported_exts]

    return len(code_files) == 0 and len(subdirs) == 1
```

**Tests**:
- Java Maven structure: skip src/main/java/com/zcyl/, keep leaf with code
- Directory with code files + single subdir → NOT skipped
- Directory with zero code files + multiple subdirs → NOT skipped (navigation)
- Directory with zero code files + single subdir → skipped
- Python flat structure → no directories skipped (all have .py files)

---

### Story 19.6: Java-Aware tech-debt Defaults

**As a** Java developer,
**I want** `codeindex tech-debt` to work correctly for Java projects without extra flags,
**So that** I get accurate technical debt analysis without workarounds.

**Two sub-tasks**:

#### 19.6a: Auto-recursive for Java

**Problem**: `tech-debt ./src` returns "0 files analyzed" for Java projects because
Java files are nested deep in `src/main/java/com/...`. User must add `--recursive`.

**Fix**: When `languages` in config includes `java`, auto-enable recursive scanning.

**Acceptance Criteria**:
- [ ] `tech-debt` auto-enables recursive when Java is in configured languages
- [ ] Explicit `--recursive` flag still works (no change)
- [ ] Non-Java projects unaffected (default remains non-recursive)
- [ ] Remove the v0.15.1 hint message (no longer needed)

#### 19.6b: Language-Aware Noise Analysis

**Problem**: `tech-debt` counts Java getter/setter as "noise symbols", producing
false HIGH severity issues. In zcyl-backend, 9/9 HIGH issues were all false positives
(standard Java getters/setters misclassified as low-quality).

v0.15.1 fixed the scorer (-10 penalty removed for Java), but:
1. Getter scores ~25-30 (borderline at threshold 30.0), many still filtered
2. `_analyze_noise_breakdown` always counts `get*/set*` as noise regardless of language

**Fix**: Make noise analysis language-aware.

**Acceptance Criteria**:
- [ ] `_analyze_noise_breakdown` skips getter/setter counting for Java files
- [ ] Java getter/setter get a slight score boost (ensure above 30.0 threshold)
- [ ] Java files with Lombok `@Data`/`@Getter` + manual getters still flagged (real redundancy)
- [ ] Python/PHP noise analysis unchanged
- [ ] Existing tech-debt tests updated
- [ ] New tests for Java getter/setter noise scenario

**Implementation Notes**:

```python
# tech_debt.py - _analyze_noise_breakdown
def _analyze_noise_breakdown(self, all_symbols, filtered_symbols, file_type="unknown"):
    # ...
    for symbol in all_symbols:
        if symbol.name in filtered_names:
            continue

        # Java: getter/setter is standard pattern, not noise
        if file_type == "java" and symbol.name.startswith(("get", "set", "is", "has")):
            continue  # Don't count as noise

        if symbol.name.startswith(("get", "set")) and len(symbol.name) > 3:
            breakdown["getters_setters"] += 1
        # ...

# symbol_scorer.py - boost Java getter/setter above threshold
# In _score_semantics, recognize get/set as SECONDARY_KEYWORDS for Java
# Or add a small positive bonus in _score_naming_pattern for Java getters
```

**Tests**:
- Java file with 10 getters/setters → noise ratio < 50% (no HIGH issue)
- Java file with Lombok @Data + manual getters → flagged as redundancy
- Python file with get_xxx methods → still counted as noise (unchanged)
- PHP file with getXxx methods → still counted as noise (unchanged)

---

## Breaking Changes

| Change | Before (v0.15.x) | After (v0.16.0) | Migration |
|--------|-------------------|------------------|-----------|
| `scan` default | AI mode (needs ai_command) | Structural mode (no AI) | Add `--ai` to get old behavior |
| `scan-all` default | AI mode | Structural mode | Add `--ai` to get old behavior |
| `--fallback` | Structural mode flag | Deprecated no-op | Remove from scripts, now default |
| `--dry-run` | Works standalone | Requires `--ai` | Add `--ai` when using `--dry-run` |
| `scan-all` directories | All directories with code | Skips pass-through dirs | May generate fewer README_AI.md |
| `tech-debt` Java | Non-recursive | Auto-recursive for Java | Remove `--recursive` from scripts |

---

## Estimated Effort

| Story | Effort | Notes |
|-------|--------|-------|
| 19.1: Reverse defaults | 2-3 hours | CLI changes + test updates |
| 19.2: Init wizard | 1-2 hours | Wizard flow + messages |
| 19.3: Help/README | 1-2 hours | Documentation |
| 19.4: Parser detection | 1-2 hours | Init parser check + guidance |
| 19.5: Skip pass-through dirs | 2-3 hours | Scanner logic + tests |
| 19.6a: Java auto-recursive | 0.5-1 hour | Small CLI change |
| 19.6b: Language-aware noise | 2-3 hours | Tech-debt + scorer + tests |
| **Total** | **9-15 hours** | |

---

## Success Criteria

1. **Zero-AI flow works**: `pip install` → `init` → `scan-all` → README_AI.md files (no AI needed)
2. **AI is clearly opt-in**: Only used when `--ai` flag is explicitly passed
3. **Parser guidance**: `init` detects missing parsers and tells user how to install
4. **Java quality**: No redundant READMEs, auto-recursive tech-debt, accurate noise analysis
5. **Backward compat**: Old scripts with `--fallback` still work (with warning)
6. **All tests pass**: 991+ tests green after changes

---

## Validation Plan

Test on real project: zcyl-backend (Java microservice, Maven multi-module)

| Test | Expected Result |
|------|-----------------|
| `codeindex init --yes` | Config created, parser check shown |
| `codeindex scan-all` | ~44 README_AI.md (not 64), no redundant pass-throughs |
| `codeindex list-dirs` | Leaf directories only, no src/main/java/com/ |
| `codeindex tech-debt ./zcyl-ocr` | Auto-recursive, no getter/setter false positives |
| `codeindex scan ./zcyl-gateway --ai` | AI-enhanced docs (if configured) |
