# Configuration Guide

## Configuration File

codeindex uses `.codeindex.yaml` for project-specific settings.

## Full Configuration Reference

```yaml
# AI CLI command template
# {prompt} will be replaced with the generated prompt
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Timeout for AI CLI execution (seconds)
ai_timeout: 120

# Output filename
output_file: "README_AI.md"

# Languages to parse
languages:
  - python
  # Future support:
  # - typescript
  # - javascript
  # - java
  # - go

# Directories to include
include:
  - src/
  - lib/
  - app/

# Directories/patterns to exclude
exclude:
  - "**/test/**"
  - "**/tests/**"
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/dist/**"
  - "**/build/**"

# Prompt customization (optional)
prompt_template: |
  You are analyzing a code directory. Generate comprehensive documentation.

  Directory: {directory}

  Files and symbols:
  {content}

  Generate a README_AI.md with:
  1. Overview of the directory's purpose
  2. Key components and their relationships
  3. Important functions/classes with brief descriptions
  4. Usage examples if applicable

# Parallel processing
parallel_workers: 8
batch_size: 50

# Smart indexing (tiered documentation)
indexing:
  max_readme_size: 51200     # 50KB limit per README
  root_level: "overview"
  module_level: "navigation"
  leaf_level: "detailed"

# Adaptive symbol extraction (v0.2.0+)
symbols:
  adaptive_symbols:
    enabled: true            # Enable dynamic symbol limits
    min_symbols: 5           # Minimum for tiny files
    max_symbols: 150         # Maximum for huge files
    thresholds:              # File size thresholds (lines)
      tiny: 100
      small: 500
      medium: 1500
      large: 3000
      xlarge: 5000
      huge: 8000
      mega: null             # >8000 lines
    limits:                  # Symbol limits per category
      tiny: 5
      small: 15
      medium: 30
      large: 50
      xlarge: 80
      huge: 120
      mega: 150

  # Global symbol index (v0.5.0+)
  project_symbols:
    enabled: false           # Disable PROJECT_SYMBOLS.md generation
                             # RECOMMENDED for large projects (>100 files)
                             # Reasons:
                             #   - Can become very large (>400KB for 250+ dirs)
                             #   - Limited value for AI-assisted development
                             #   - Better alternatives exist:
                             #     * PROJECT_INDEX.md (module navigation)
                             #     * README_AI.md (directory symbols)
                             #     * Serena MCP find_symbol() (precise lookup)

# AI Enhancement for scan-all (v0.3.0+)
ai_enhancement:
  strategy: "selective"      # "selective" | "all"
  enabled: true
  size_threshold: 40960      # >40KB triggers AI enhancement
  max_concurrent: 2          # Max parallel AI calls
  rate_limit_delay: 1.0      # Seconds between AI calls

# Incremental updates (v0.1.2+)
incremental:
  enabled: true
  thresholds:
    skip_lines: 5            # <5 lines changed → skip
    current_only: 50         # <50 lines → update current dir only
    suggest_full: 200        # >200 lines → suggest full scan

# Technical debt thresholds (v0.3.0+)
tech_debt:
  file_size:
    large_threshold: 2000    # Lines for "large file" warning
    super_large_threshold: 5000  # Lines for "super large file" critical
  god_class:
    method_threshold: 50     # Methods for "god class" detection
  symbol_overload:
    total_threshold: 100     # Total symbols threshold
    noise_ratio: 0.5         # >50% low-quality symbols
  complexity:
    cyclomatic_threshold: 10
    cognitive_threshold: 15
    nesting_threshold: 4
```

## AI CLI Examples

### Claude CLI

```yaml
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
```

### OpenAI (hypothetical)

```yaml
ai_command: 'openai chat "{prompt}" --model gpt-4'
```

### Custom script

```yaml
ai_command: '/path/to/my-ai-wrapper.sh "{prompt}"'
```

## Include/Exclude Patterns

Patterns use glob syntax:

- `*` - Match any characters except `/`
- `**` - Match any characters including `/`
- `?` - Match single character
- `[abc]` - Match any character in brackets
- `{a,b}` - Match either `a` or `b`

### Examples

```yaml
# Include only specific directories
include:
  - src/core/**
  - src/api/**

# Exclude test and generated files
exclude:
  - "**/*_test.py"
  - "**/*_generated.py"
  - "**/migrations/**"
```

## Language Configuration

Currently supported:
- `python` - Full support with tree-sitter

Coming soon:
- `typescript` / `javascript`
- `java`
- `go`
- `rust`

## Environment Variables

Override config via environment:

```bash
export CODEINDEX_AI_COMMAND='claude -p "{prompt}"'
export CODEINDEX_TIMEOUT=180
```

Priority: ENV > `.codeindex.yaml` > defaults

## Multiple Configurations

For monorepos, use separate configs:

```
monorepo/
├── .codeindex.yaml          # Root config
├── backend/
│   └── .codeindex.yaml      # Backend-specific
└── frontend/
    └── .codeindex.yaml      # Frontend-specific
```

## Global Configuration

Create `~/.config/codeindex/config.yaml` for defaults:

```yaml
ai_command: 'claude -p "{prompt}"'
exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"
```

## Validation

Check if your config is valid:

```bash
codeindex validate-config
```

## Upgrading Your Configuration

### Check Current Version

```bash
# Check codeindex version
codeindex --version

# Check config version
grep "^version:" .codeindex.yaml
```

### Version Compatibility Matrix

| codeindex Version | Config Version | Compatible | Migration Needed? |
|-------------------|----------------|------------|-------------------|
| v0.5.0-beta1      | 1              | ✅ Yes     | No                |
| v0.4.0            | 1              | ✅ Yes     | No                |
| v0.3.0-0.3.1      | 1              | ✅ Yes     | No                |
| v0.2.0            | 1              | ✅ Yes     | No                |
| v0.1.x            | 1              | ✅ Yes     | No                |

**Bottom line**: All versions 100% backward compatible. No migration required.

### Upgrade Benefits by Version

#### From v0.1.x to v0.5.0-beta1

Optional improvements available:

1. **Adaptive Symbol Extraction** (v0.2.0)
   - Better handling of large files (26% → 100% coverage)
   - Add `symbols.adaptive_symbols` section

2. **AI Enhancement Control** (v0.3.0)
   - Fine-tune AI usage and cost
   - Add `ai_enhancement` section

3. **Tech Debt Thresholds** (v0.3.0)
   - Customize complexity detection
   - Add `tech_debt` section

4. **Git Hooks** (v0.5.0-beta1)
   - Automated code quality checks
   - No config changes - use CLI: `codeindex hooks install --all`

See: `docs/guides/configuration-changelog.md` for detailed upgrade paths

### Quick Upgrade Workflow

```bash
# 1. Backup current config
cp .codeindex.yaml .codeindex.yaml.backup

# 2. Get latest example config
cp examples/.codeindex.yaml .codeindex.yaml.new

# 3. Compare and merge
diff .codeindex.yaml .codeindex.yaml.new

# 4. Test new config
codeindex scan src/ --dry-run

# 5. Apply
mv .codeindex.yaml.new .codeindex.yaml
```

### Selective Feature Adoption

**Add only what you need**:

```yaml
# Minimal config (v0.1.0 compatible)
version: 1
ai_command: 'claude -p "{prompt}"'
include:
  - src/

# + Add adaptive symbols (recommended for large projects)
symbols:
  adaptive_symbols:
    enabled: true

# + Add AI enhancement control (cost optimization)
ai_enhancement:
  strategy: "selective"
  size_threshold: 40960

# + Add tech debt thresholds (custom rules)
tech_debt:
  file_size:
    large_threshold: 3000
```

## Migration (Future)

**Note**: Migration tools are planned for future breaking changes

Upgrade old config format:

```bash
codeindex config upgrade    # Future: auto-upgrade
codeindex config check      # Future: validate and suggest improvements
```

## Tips

1. **Start simple**: Use `codeindex init` defaults, then customize
2. **Test patterns**: Use `codeindex list-dirs` to verify include/exclude
3. **AI cost**: Shorter prompts = lower cost. Exclude unnecessary files
4. **Parallel safety**: Each directory scan is independent, safe for parallel execution

## Examples

### Python-only project

```yaml
ai_command: 'claude -p "{prompt}"'
languages:
  - python
include:
  - src/
exclude:
  - "**/test/**"
  - "**/__pycache__/**"
```

### Full-stack monorepo

```yaml
ai_command: 'claude -p "{prompt}"'
languages:
  - python
  - typescript
include:
  - backend/src/
  - frontend/src/
exclude:
  - "**/test/**"
  - "**/node_modules/**"
  - "**/dist/**"
```

### AI-free (always fallback)

```yaml
# No ai_command specified
languages:
  - python
include:
  - src/
```

Then always use:
```bash
codeindex scan . --fallback
```