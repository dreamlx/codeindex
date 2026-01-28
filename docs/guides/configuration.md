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

## Migration

Upgrade old config format:

```bash
codeindex migrate-config
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