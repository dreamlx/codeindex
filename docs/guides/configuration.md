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

# Docstring extraction (v0.6.0+, Epic 9)
docstrings:
  mode: "hybrid"             # "off" | "hybrid" | "all-ai"
  ai_command: ""             # Optional, inherits from global if not specified
  cost_limit: 1.0            # Maximum cost in USD

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

## Docstring Extraction (v0.6.0+, Epic 9)

AI-powered docstring extraction for multi-language projects with mixed documentation styles.

### Why Use Docstring Extraction?

**Problem**: Many projects have inconsistent or mixed-language documentation:
- PHP projects with Chinese + English comments mixed in PHPDoc
- Legacy code with minimal or cryptic comments
- Inconsistent documentation standards across team members

**Solution**: AI normalizes all docstrings into clear, consistent English descriptions.

### Configuration

```yaml
docstrings:
  # Mode: off | hybrid | all-ai
  mode: hybrid

  # AI CLI command (optional, inherits from global if not specified)
  # ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

  # Cost limit in USD (prevents runaway costs)
  cost_limit: 1.0
```

### Modes Explained

#### `off` (Default)
- **No AI processing** - Uses raw docstrings as-is
- **Cost**: $0
- **Best for**: Projects with consistent English documentation
- **Backward compatible**: Default mode for all existing configs

#### `hybrid` (Recommended)
- **Selective AI** - Only processes complex or mixed-language docstrings
- **Cost**: <$1 for typical 250-directory projects
- **Decision logic**:
  - Simple English one-liners → No AI (free)
  - Structured docs (`@param`, `@return`) → AI processes
  - Mixed language (Chinese + English) → AI processes
  - Long/complex comments → AI processes
- **Best for**: Most projects, cost-effective quality improvement

#### `all-ai`
- **AI processes everything** - Maximum quality and consistency
- **Cost**: Higher (all docstrings processed)
- **Best for**: Critical documentation or multilingual projects
- **Use case**: High-value codebases needing professional docs

### CLI Usage

Override config mode via CLI:

```bash
# Use hybrid mode (overrides config)
codeindex scan src/ --docstring-mode hybrid

# Use all-ai mode with cost tracking
codeindex scan-all --docstring-mode all-ai --show-cost

# Disable docstring processing
codeindex scan src/ --docstring-mode off

# Show token usage and estimated cost
codeindex scan-all --docstring-mode hybrid --show-cost
```

### Cost Estimation

**Hybrid mode** (recommended):
- Typical project: 250 directories, 1926 symbols
- AI calls: ~100-200 symbols (only complex ones)
- Tokens: ~50,000 tokens
- Cost: ~$0.15 @ $3 per 1M tokens

**All-AI mode**:
- Same project: All 1926 symbols processed
- Tokens: ~500,000 tokens
- Cost: ~$1.50

**Formula**: Cost ≈ (tokens / 1,000,000) × $3

### Supported Languages

- **PHP**: PHPDoc (`/** */`), inline comments (`//`)
- **Python**: Docstrings, comments (coming soon)
- **JavaScript/TypeScript**: JSDoc (planned)

### Example Use Cases

#### PHP Project with Mixed Language Comments

**Before** (raw docstring):
```php
/**
 * 获取用户列表 Get user list
 * @param int $page 页码 Page number
 * @param int $limit 每页数量 Items per page
 * @return array 用户数据 User data
 */
function getUserList($page, $limit) { ... }
```

**After** (AI-normalized with `hybrid` mode):
```
Retrieves paginated user list with configurable page size
```

#### Legacy Code with Cryptic Comments

**Before**:
```php
// get usr
function getU($id) { ... }
```

**After** (AI-enhanced):
```
Retrieves user by ID from database
```

### Performance

- **Batch processing**: 1 AI call per file (not per symbol)
- **Parallel safe**: Works with `--parallel` option
- **Smart caching**: AI results cached during scan session
- **Graceful fallback**: If AI fails, uses raw docstrings

### Tips

1. **Start with `hybrid`**: Best cost/quality tradeoff
2. **Use `--show-cost`**: Monitor token usage during development
3. **Set `cost_limit`**: Prevents accidental overspending
4. **Test first**: Run `scan` on single directory before `scan-all`

### Integration with SmartWriter

Docstring processing happens **before** README generation:
1. Parse file → Extract raw docstrings
2. Process with AI (if mode != "off") → Get normalized descriptions
3. Generate README → Use normalized descriptions

### Backward Compatibility

- **Default mode**: `off` (no changes to existing behavior)
- **No config changes required**: Existing configs work without modification
- **Opt-in**: Only active when `mode` is set to `hybrid` or `all-ai`

## Language Configuration

Currently supported:
- `python` - Full support with tree-sitter
- `php` - Full support with PHPDoc extraction (v0.6.0+)

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
| v0.6.0            | 1              | ⚠️ Partial  | **Yes** - Remove `ai_enhancement` section |
| v0.5.0            | 1              | ✅ Yes     | No                |
| v0.4.0            | 1              | ✅ Yes     | No                |
| v0.3.0-0.3.1      | 1              | ✅ Yes     | No                |
| v0.2.0            | 1              | ✅ Yes     | No                |
| v0.1.x            | 1              | ✅ Yes     | No                |

**Breaking Change in v0.6.0**: `ai_enhancement` configuration section removed. See `docs/guides/migration-v0.6.md` for migration guide.

### Upgrade Benefits by Version

#### From v0.1.x to v0.5.0-beta1

Optional improvements available:

1. **Adaptive Symbol Extraction** (v0.2.0)
   - Better handling of large files (26% → 100% coverage)
   - Add `symbols.adaptive_symbols` section

2. **Tech Debt Thresholds** (v0.3.0)
   - Customize complexity detection
   - Add `tech_debt` section

3. **Docstring Extraction** (v0.6.0)
   - AI-powered multi-language documentation normalization
   - Add `docstrings` section

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