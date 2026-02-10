# Epic 15: User Onboarding Enhancement

**Version**: v0.14.0
**Priority**: P0 (Must Have - User Experience)
**Status**: 📋 Planned
**Created**: 2026-02-08

---

## 🎯 Epic Goal

Enhance the first-time user experience with an intelligent, interactive setup wizard that works both for humans (interactive) and machines (non-interactive/CI).

### Success Criteria

- [ ] New users can run `codeindex init` and have a complete setup in <1 minute
- [ ] Non-interactive mode supports LoomGraph and CI/CD integration
- [ ] Smart defaults reduce manual configuration to zero
- [ ] Help system provides comprehensive configuration reference
- [ ] 95%+ users complete setup without reading documentation

---

## 📊 Problem Statement

### Current Issues

1. **Incomplete Setup** ⚠️
   - Users run `pipx install ai-codeindex` and expect it to work
   - Missing: `.codeindex.yaml`, Git Hooks, AI integration guide
   - Users don't know what's missing until they hit errors

2. **Manual Configuration Burden** 😓
   - Users must manually create `.codeindex.yaml`
   - Must manually copy examples/CLAUDE.md.template
   - Must manually run `codeindex hooks install`
   - No guidance on configuration parameters

3. **Tool Integration Complexity** 🤖
   - LoomGraph needs to call codeindex in non-interactive mode
   - CI/CD pipelines need deterministic setup
   - Current `codeindex init` requires manual input

4. **Poor Discoverability** 🔍
   - Users don't know about parallel workers, batch size, hooks modes
   - No in-CLI documentation for `.codeindex.yaml` parameters
   - Must read external docs to understand options

### User Feedback

> "I installed codeindex but don't know what to do next."
>
> "How do I configure parallel scanning? Where's the documentation?"
>
> "Can I use codeindex in CI without manual input?"

---

## 💡 Solution Design

### Story 15.1: Interactive Setup Wizard ⭐

**What**: Enhanced `codeindex init` with step-by-step wizard

**Features**:
- Auto-detect project languages (Python, PHP, Java)
- Smart defaults for include/exclude patterns
- Optional Git Hooks installation with mode selection
- Create CODEINDEX.md AI integration guide
- Optional AI CLI configuration
- Summary of what was created

**User Flow**:
```
$ codeindex init

🚀 codeindex Setup Wizard

Step 1/4: Language Detection
  ✓ Detected: python, php
  Use detected languages? [Y/n]:

Step 2/4: Git Hooks (optional)
  Install Git Hooks for auto-updates? [Y/n]: y

  Choose mode:
    1. auto (smart, recommended)
    2. disabled
    3. async (background)
    4. sync (blocking)

  Select [1-4]: 1
  ✓ Git Hooks installed (mode: auto)

Step 3/4: AI Integration
  Create CODEINDEX.md guide? [Y/n]: y
  ✓ Created CODEINDEX.md

Step 4/4: AI CLI Configuration (optional)
  Configure AI CLI? [y/N]: n
  ℹ Using --fallback mode (no AI required)

✅ Setup complete!

Created files:
  • .codeindex.yaml (configuration)
  • CODEINDEX.md (AI usage guide)
  • .git/hooks/post-commit (auto-update)

Next steps:
  1. Review .codeindex.yaml
  2. Run: codeindex scan-all --fallback
  3. Commit: git add .codeindex.yaml CODEINDEX.md
```

**Tests**: 15 tests (user flows, default values, edge cases)

---

### Story 15.2: Non-Interactive Mode 🤖

**What**: Support headless/CI/tool integration

**CLI Design**:
```bash
# Quick setup with all defaults
codeindex init --yes

# Custom non-interactive setup
codeindex init -y \
  --languages python,php,java \
  --hooks auto \
  --ai-guide yes

# CI/CD mode (quiet, no hooks)
codeindex init -y -q --hooks disabled

# Preview defaults without executing
codeindex init --show-defaults
```

**Parameters**:
- `-y, --yes`: Non-interactive mode
- `--languages TEXT`: Comma-separated language list
- `--ai-cli TEXT`: AI CLI command template
- `--hooks [auto|disabled|async|sync|prompt]`: Git Hooks mode
- `--ai-guide [yes|no]`: Create CODEINDEX.md
- `-q, --quiet`: Minimal output
- `--show-defaults`: Display defaults and exit

**LoomGraph Integration**:
```python
# loomgraph calls codeindex
subprocess.run([
    "codeindex", "init",
    "--yes", "--quiet",
    "--languages", "python,php",
    "--hooks", "auto",
])
```

**Tests**: 12 tests (all parameter combinations, LoomGraph use case, CI mode)

---

### Story 15.3: Enhanced Help System 📚

**What**: Comprehensive in-CLI documentation

**New Commands**:

#### 1. Enhanced `codeindex init --help`

```bash
$ codeindex init --help

Usage: codeindex init [OPTIONS]

  Initialize codeindex configuration.

  Modes:
    • Interactive (default): Step-by-step wizard
    • Non-interactive (--yes): Use defaults

Options:
  -y, --yes              Non-interactive mode
  --languages TEXT       Languages (e.g., python,php,java)
  --ai-cli TEXT          AI CLI command template
  --hooks [auto|disabled|async|sync|prompt]
                         Git Hooks mode (default: auto)
  --ai-guide [yes|no]    Create CODEINDEX.md (default: yes)
  -q, --quiet            Minimal output
  --show-defaults        Show defaults and exit
  --help-config          Show .codeindex.yaml reference
  --help                 Show this message

Examples:
  Interactive:    codeindex init
  Quick setup:    codeindex init --yes
  Custom:         codeindex init -y --languages python,php
  CI/CD:          codeindex init -y -q --hooks disabled

See also: codeindex init --help-config
```

#### 2. New `codeindex init --help-config`

```bash
$ codeindex init --help-config

📋 .codeindex.yaml Configuration Reference

File Location: /your/project/.codeindex.yaml
Format: YAML
Created by: codeindex init

─────────────────────────────────────────────────────────
Basic Settings
─────────────────────────────────────────────────────────

codeindex: 1
  # Config file version (don't change)

languages:
  - python
  - php
  - java
  # Supported: python, php, java
  # More coming: typescript, go, rust, c#

output_file: "README_AI.md"
  # Name of generated documentation files
  # Default: README_AI.md

─────────────────────────────────────────────────────────
Performance Settings ⚡
─────────────────────────────────────────────────────────

parallel_workers: 8
  # Number of concurrent workers for scanning
  # Default: CPU count (8)
  # Range: 1-32
  # Recommendation:
  #   • Small projects (<100 files): 4
  #   • Medium projects (100-1000 files): 8
  #   • Large projects (>1000 files): 16
  #   • CI/CD: 4 (conservative)

batch_size: 50
  # Files processed per batch
  # Default: 50
  # Range: 10-200
  # Trade-off:
  #   • Larger = faster but more memory
  #   • Smaller = slower but less memory
  # Recommendation:
  #   • Normal: 50
  #   • Low memory: 20
  #   • High performance: 100

─────────────────────────────────────────────────────────
Pattern Matching
─────────────────────────────────────────────────────────

include:
  - src/
  - lib/
  # Directories/patterns to scan
  # Glob patterns supported

exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/vendor/**"
  - "**/.venv/**"
  # Patterns to skip
  # Use ** for recursive matching

─────────────────────────────────────────────────────────
Git Hooks Configuration 🔄
─────────────────────────────────────────────────────────

hooks:
  post_commit:
    mode: auto
      # Modes:
      #   • auto: Smart (≤2 dirs=sync, >2=async)
      #   • disabled: No auto-updates
      #   • async: Always background
      #   • sync: Always blocking
      #   • prompt: Ask each time
      # Default: auto

    enabled: true
      # Master switch
      # Default: true

    max_dirs_sync: 2
      # Auto mode threshold
      # ≤2 dirs: synchronous (blocking)
      # >2 dirs: asynchronous (background)
      # Default: 2

    log_file: ~/.codeindex/hooks/post-commit.log
      # Hook execution log
      # Useful for debugging

─────────────────────────────────────────────────────────
AI Integration
─────────────────────────────────────────────────────────

ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
  # AI CLI command template
  # {prompt} placeholder required
  # Examples:
  #   • Claude: 'claude -p "{prompt}"'
  #   • OpenAI: 'openai chat "{prompt}" --model gpt-4'
  #   • Custom: '/path/to/ai-wrapper.sh "{prompt}"'
  # Leave empty to use --fallback mode

─────────────────────────────────────────────────────────
Advanced Settings
─────────────────────────────────────────────────────────

symbols:
  adaptive_symbols:
    enabled: true
      # Dynamic symbol extraction
      # Adjusts symbol count based on file size

    min_symbols: 5
    max_symbols: 150
      # Symbol count range

    thresholds:
      tiny: 100      # <100 lines → 5 symbols
      small: 500     # 100-500 → 15 symbols
      medium: 1500   # 500-1500 → 30 symbols
      large: 3000    # 1500-3000 → 50 symbols
      xlarge: 5000   # 3000-5000 → 80 symbols
      huge: 8000     # 5000-8000 → 120 symbols
      mega: null     # >8000 → 150 symbols

indexing:
  max_readme_size: 51200  # 50KB limit
  root_level: "overview"
  module_level: "navigation"
  leaf_level: "detailed"

─────────────────────────────────────────────────────────
Examples
─────────────────────────────────────────────────────────

High Performance Setup:
  parallel_workers: 16
  batch_size: 100

Low Memory Setup:
  parallel_workers: 4
  batch_size: 20

CI/CD Setup:
  parallel_workers: 4
  batch_size: 50
  hooks:
    post_commit:
      enabled: false

Large Monorepo:
  parallel_workers: 16
  batch_size: 100
  hooks:
    post_commit:
      mode: async  # Always background

─────────────────────────────────────────────────────────
More Help
─────────────────────────────────────────────────────────

Full documentation:
  • Configuration: docs/guides/configuration.md
  • Git Hooks: docs/guides/git-hooks-integration.md
  • Online: https://github.com/dreamlx/codeindex

Commands:
  codeindex init --show-defaults  # Preview defaults
  codeindex status                # Check setup
  codeindex hooks status          # Check Git Hooks
```

#### 3. New `codeindex config` command

```bash
$ codeindex config --help

Usage: codeindex config [OPTIONS] COMMAND [ARGS]...

  Manage codeindex configuration.

Commands:
  show     Show current configuration
  edit     Open .codeindex.yaml in editor
  validate Validate configuration file
  explain  Explain configuration parameters

$ codeindex config show
📋 Current Configuration

File: /Users/dreamlinx/Projects/myproject/.codeindex.yaml
Version: 1

Languages: python, php, java
Parallel Workers: 8
Batch Size: 50
Git Hooks: enabled (mode: auto)

AI CLI: claude -p "{prompt}"
Output File: README_AI.md

Include: src/, lib/, Application/
Exclude: **/__pycache__/**, **/node_modules/**, ...

$ codeindex config explain parallel_workers

⚡ parallel_workers

What it does:
  Controls how many directories are scanned simultaneously.
  Higher = faster, but more CPU/memory usage.

Default: 8 (CPU count)
Range: 1-32

Recommendations:
  • Small projects (<100 files): 4
  • Medium projects (100-1000 files): 8
  • Large projects (>1000 files): 16
  • CI/CD environments: 4 (conservative)

Example:
  parallel_workers: 16

See also: batch_size
```

**Tests**: 8 tests (help output, explain command, edge cases)

---

### Story 15.4: Smart Defaults & Auto-Detection 🧠

**What**: Minimize manual configuration

**Features**:

1. **Language Auto-Detection**
   ```python
   def auto_detect_languages(project_root: Path) -> list[str]:
       """Detect languages from project files"""
       detected = set()

       if list(project_root.glob("**/*.py")):
           detected.add("python")
       if list(project_root.glob("**/*.php")):
           detected.add("php")
       if list(project_root.glob("**/*.java")):
           detected.add("java")

       return sorted(detected)
   ```

2. **Include Pattern Inference**
   ```python
   def get_default_include_patterns(languages: list[str]) -> list[str]:
       """Generate include patterns based on languages"""
       patterns = []

       if "python" in languages:
           patterns.extend(["src/", "lib/", "*.py"])
       if "php" in languages:
           patterns.extend(["Application/", "app/", "src/"])
       if "java" in languages:
           patterns.extend(["src/main/java/", "src/"])

       return patterns
   ```

3. **Performance Tuning**
   ```python
   def auto_tune_performance(project_size: int) -> dict:
       """Auto-tune based on project size"""
       if project_size < 100:
           return {"parallel_workers": 4, "batch_size": 20}
       elif project_size < 1000:
           return {"parallel_workers": 8, "batch_size": 50}
       else:
           return {"parallel_workers": 16, "batch_size": 100}
   ```

**Tests**: 10 tests (detection accuracy, pattern generation, performance tuning)

---

## 📋 Implementation Plan

### Phase 1: Core Interactive Wizard (Week 1)

**Files to Create/Modify**:
- `src/codeindex/cli_init.py` - Interactive wizard logic
- `src/codeindex/init_defaults.py` - Default configurations
- `src/codeindex/init_templates.py` - File templates

**Tasks**:
1. Implement language auto-detection
2. Create interactive prompt flow
3. Generate .codeindex.yaml from user input
4. Create CODEINDEX.md from template
5. Integrate Git Hooks installation

**Deliverables**:
- Working `codeindex init` interactive mode
- 15 tests passing

### Phase 2: Non-Interactive Mode (Week 1)

**Files to Modify**:
- `src/codeindex/cli_init.py` - Add non-interactive logic
- `src/codeindex/cli.py` - Add CLI parameters

**Tasks**:
1. Add `--yes` flag and all parameters
2. Implement default value resolution
3. Add `--show-defaults` command
4. Add `--quiet` mode for CI/CD

**Deliverables**:
- LoomGraph can call `codeindex init -y`
- 12 tests passing

### Phase 3: Enhanced Help System (Week 2)

**Files to Create/Modify**:
- `src/codeindex/cli_config.py` - New config command
- `src/codeindex/help_formatter.py` - Help text formatter

**Tasks**:
1. Create comprehensive help text for `--help-config`
2. Implement `codeindex config` command group
3. Add `config show`, `config explain`
4. Format help with examples and recommendations

**Deliverables**:
- `codeindex init --help-config` shows full reference
- `codeindex config explain <param>` works
- 8 tests passing

### Phase 4: Smart Defaults (Week 2)

**Files to Create/Modify**:
- `src/codeindex/auto_detect.py` - Detection logic
- `src/codeindex/performance_tuner.py` - Auto-tuning

**Tasks**:
1. Implement language detection
2. Implement pattern inference
3. Implement performance auto-tuning
4. Add project size estimation

**Deliverables**:
- Auto-detection works for common projects
- 10 tests passing

---

## 🧪 Testing Strategy

### Unit Tests (45 tests total)

| Component | Tests | Coverage |
|-----------|-------|----------|
| Interactive wizard | 15 | User flows, defaults, edge cases |
| Non-interactive mode | 12 | All parameters, combinations |
| Help system | 8 | Output format, explain command |
| Smart defaults | 10 | Detection, inference, tuning |

### Integration Tests (5 tests)

1. End-to-end interactive setup
2. LoomGraph integration scenario
3. CI/CD pipeline scenario
4. Upgrade from v0.13.0 config
5. Multi-language project setup

### Manual Testing Checklist

- [ ] Fresh installation on clean project
- [ ] Upgrade existing project with old .codeindex.yaml
- [ ] Python-only project setup
- [ ] PHP-only project setup
- [ ] Multi-language project setup
- [ ] CI/CD in GitHub Actions
- [ ] LoomGraph integration test

---

## 📊 Success Metrics

### Quantitative

| Metric | Current | Target |
|--------|---------|--------|
| Setup time (first-time) | 5-10 min | <1 min |
| Setup completion rate | ~60% | 95%+ |
| Config questions asked | ~15 | 0 (defaults) |
| Help lookups needed | ~80% | <20% |

### Qualitative

- [ ] Users report "easy to get started"
- [ ] No confusion about configuration
- [ ] LoomGraph integration works seamlessly
- [ ] CI/CD pipelines work without manual setup

---

## 🔗 Dependencies

### Requires
- v0.13.0 (base functionality)

### Enables
- Epic 16: TypeScript Support (easier language setup)
- Epic 17: Framework Routes Expansion (auto-detection helps)
- LoomGraph integration (non-interactive mode)

---

## 📝 Documentation Updates

### Files to Update
1. `README.md` - Update Quick Start section
2. `docs/guides/configuration.md` - Add help reference
3. `CLAUDE.md` - Update init command examples
4. `examples/.codeindex.yaml` - Add comprehensive comments

### New Documentation
1. `docs/guides/first-time-setup.md` - First-time user guide
2. `docs/guides/ci-cd-integration.md` - CI/CD setup guide
3. `docs/guides/configuration-reference.md` - Full parameter reference

---

## 🚀 Release Plan

### v0.14.0 Release

**Release Date**: 2026-03-31

**Theme**: User Onboarding Enhancement

**What's Included**:
- ✅ Interactive setup wizard
- ✅ Non-interactive mode for tools/CI
- ✅ Enhanced help system with config reference
- ✅ Smart defaults and auto-detection
- ✅ CODEINDEX.md auto-creation

**Breaking Changes**: None (100% backward compatible)

**Migration Guide**: Not needed (auto-upgrades old configs)

---

## 💬 Open Questions

1. **Q**: Should we support `.codeindexrc` (JSON/TOML) in addition to YAML?
   **A**: No, keep it simple with YAML only for now

2. **Q**: Should `codeindex init` auto-run first scan?
   **A**: No, let user review config first, suggest as next step

3. **Q**: Should we detect framework (ThinkPHP, Spring) and auto-configure?
   **A**: v0.15.0+ (out of scope for this Epic)

4. **Q**: Support environment variables (CODEINDEX_WORKERS=16)?
   **A**: v0.15.0+ (nice to have, not essential)

---

## 📚 References

- [Configuration Changelog](../guides/configuration-changelog.md)
- [Git Hooks Integration](../guides/git-hooks-integration.md)
- [LoomGraph Integration](../guides/loomgraph-integration.md)
- [ROADMAP.md](../ROADMAP.md) - Epic 15 entry

---

**Epic Owner**: @dreamlx
**Target Version**: v0.14.0
**Estimated Effort**: 2 weeks
**Status**: 📋 Planned (ready to start)
