# Advanced Usage

## Parallel Scanning

### Using scan-all

The simplest way to scan entire projects:

```bash
# Structural documentation (default, no AI needed)
codeindex scan-all

# AI-enhanced documentation
codeindex scan-all --ai

# Custom timeout per directory
codeindex scan-all --timeout 180

# Custom parallel workers
codeindex scan-all --workers 4
```

### Traditional Parallel with xargs

For fine-grained control, use traditional parallel scanning:

```bash
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
```

Adjust parallelism based on your CPU:
```bash
# 8 parallel workers
codeindex list-dirs | xargs -P 8 -I {} codeindex scan {}

# Auto-detect CPU cores
codeindex list-dirs | xargs -P $(nproc) -I {} codeindex scan {}
```

### Using GNU Parallel

```bash
# Install GNU parallel
brew install parallel  # macOS
apt install parallel   # Ubuntu

# Scan with progress bar
codeindex list-dirs | parallel --bar -j 4 codeindex scan {}

# With timeout per job
codeindex list-dirs | parallel --timeout 300 -j 4 codeindex scan {}
```

## Custom Prompts

### Override Default Prompt

Create a custom prompt template in `.codeindex.yaml`:

```yaml
prompt_template: |
  Analyze this directory and generate a technical README.

  Directory: {directory}

  Code structure:
  {content}

  Requirements:
  1. Architectural overview
  2. Key design patterns used
  3. Dependencies and their purposes
  4. API surface (public classes/functions)
  5. Security considerations
  6. Performance characteristics

  Format as README.md with clear sections.
```

### Using Prompt Files

Store prompts in separate files:

```yaml
# .codeindex.yaml
prompt_file: ".codeindex/prompt.txt"
```

```
# .codeindex/prompt.txt
Analyze {directory} and generate documentation focusing on:
- API design
- Error handling patterns
- Testing approach
```

## Selective Scanning

### Scan Specific Directories

```bash
# Scan only auth and api modules
codeindex scan ./src/auth
codeindex scan ./src/api

# Or with glob
find src -maxdepth 1 -type d | xargs -I {} codeindex scan {}
```

### Filter by Pattern

```bash
# Scan only directories containing "service"
codeindex list-dirs | grep service | xargs -P 4 -I {} codeindex scan {}

# Exclude test directories
codeindex list-dirs | grep -v test | xargs -P 4 -I {} codeindex scan {}
```

## Incremental Updates

### Scan Only Changed Directories

Using git to find changed files:

```bash
# Get changed directories since last commit
git diff --name-only HEAD~1 | xargs -n1 dirname | sort -u | \
  xargs -I {} codeindex scan {}

# Since specific commit
git diff --name-only abc123 | xargs -n1 dirname | sort -u | \
  xargs -I {} codeindex scan {}
```

### Using `codeindex affected`

```bash
# Find directories affected by recent changes
codeindex affected --since HEAD~5 --until HEAD

# JSON output for scripting
codeindex affected --json

# Pipe to scan
codeindex affected --json | jq '.directories[]' | xargs -I {} codeindex scan {}
```

## Symbol Indexing (v0.1.2+)

### Generate Global Symbol Index

Create a searchable index of all classes and functions:

```bash
# Generate PROJECT_SYMBOLS.md
codeindex symbols

# Quiet mode (minimal output)
codeindex symbols --quiet

# Custom output filename
codeindex symbols --output MY_SYMBOLS.md
```

**What you get:**
- Global symbol index with file locations
- Cross-file references
- Grouped by directory
- Quick class/function lookup

### Generate Project Index

Create a module-level overview:

```bash
# Generate PROJECT_INDEX.md
codeindex index

# Custom output
codeindex index --output PROJECT_OVERVIEW.md
```

**What you get:**
- Module descriptions extracted from README_AI.md
- Entry points and CLI commands
- Directory structure overview

## Technical Debt Analysis (v0.3.0+)

### Basic Analysis

Detect code quality issues in a directory:

```bash
# Console output (default)
codeindex tech-debt ./src

# Recursive analysis
codeindex tech-debt ./src --recursive

# Quiet mode
codeindex tech-debt ./src --quiet
```

### Output Formats

```bash
# Markdown report (for documentation)
codeindex tech-debt ./src --format markdown --output debt-report.md

# JSON output (for CI/CD)
codeindex tech-debt ./src --format json --output debt.json

# Parse JSON in scripts
codeindex tech-debt ./src --format json | \
  jq '.files[] | select(.quality_score < 70)'
```

### CI/CD Integration

Fail builds on critical issues:

```bash
#!/bin/bash
# In your CI pipeline

# Analyze codebase
codeindex tech-debt ./src --format json --output debt.json

# Check for critical issues
CRITICAL=$(jq '[.files[].issues[] | select(.severity == "CRITICAL")] | length' debt.json)

if [ "$CRITICAL" -gt 0 ]; then
  echo "Found $CRITICAL critical technical debt issues"
  jq '.files[].issues[] | select(.severity == "CRITICAL")' debt.json
  exit 1
fi

echo "No critical technical debt issues"
```

### Quality Gates

Set thresholds for acceptable debt:

```bash
# Check average quality score
AVG_QUALITY=$(jq '[.files[].quality_score] | add / length' debt.json)

if (( $(echo "$AVG_QUALITY < 70" | bc -l) )); then
  echo "Average quality score $AVG_QUALITY below threshold (70)"
  exit 1
fi
```

## Adaptive Symbol Extraction (v0.2.0+)

### How It Works

Dynamically adjust symbol limits based on file size:

- **Tiny files** (<100 lines): 5 symbols
- **Small files** (100-500 lines): 15 symbols
- **Medium files** (500-1500 lines): 30 symbols
- **Large files** (1500-3000 lines): 50 symbols
- **XLarge files** (3000-5000 lines): 80 symbols
- **Huge files** (5000-8000 lines): 120 symbols
- **Mega files** (>8000 lines): 150 symbols

### Configuration

```yaml
# .codeindex.yaml
symbols:
  adaptive_symbols:
    enabled: true
    min_symbols: 5
    max_symbols: 150
    # Customize thresholds
    thresholds:
      small: 300       # Lower small threshold
      mega: 10000      # Higher mega threshold
```

### Benefits

- **Better coverage**: Large files get more symbols (280% improvement)
- **Efficiency**: Small files don't waste space with truncation messages
- **Flexible**: Fully configurable thresholds and limits

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/codeindex.yml
name: Update Code Index

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install codeindex
        run: pipx install ai-codeindex[all]

      - name: Generate indexes
        run: |
          codeindex init --yes
          codeindex scan-all

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add '**/README_AI.md'
          git commit -m "docs: auto-update README_AI.md files" || exit 0
          git push
```

### GitLab CI

```yaml
# .gitlab-ci.yml
update-index:
  image: python:3.11
  script:
    - pip install ai-codeindex[all]
    - codeindex scan-all
  artifacts:
    paths:
      - '**/README_AI.md'
```

## Performance Optimization

### Exclude Large Files

```yaml
# .codeindex.yaml
exclude:
  - "**/node_modules/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/*.min.js"
  - "**/generated/**"
```

### Timeout Configuration

Adjust timeout for large directories:

```yaml
ai_timeout: 300  # 5 minutes for complex codebases
```

### Limit Scanned Files

```yaml
# Custom exclude patterns
exclude:
  - "**/*_pb2.py"      # Generated protobuf
  - "**/*_generated.py"
  - "**/migrations/**"
```

## Output Customization

### Custom Output Filename

```yaml
output_file: "OVERVIEW.md"  # Instead of README_AI.md
```

### JSON Output

```bash
# Single directory
codeindex scan ./src --output json

# Entire project
codeindex scan-all --output json > parse_results.json

# Parse single file
codeindex parse myfile.py | jq .
```

## Git Hooks Integration

Automatically regenerate indexes on commit using codeindex's built-in hooks:

```bash
# Install all hooks (pre-commit + post-commit)
codeindex hooks install --all

# Or install individually
codeindex hooks install pre-commit
codeindex hooks install post-commit

# Check hook status
codeindex hooks status
```

See [Git Hooks Integration Guide](./git-hooks-integration.md) for details.

## Multi-Project Workflows

### Workspace Configuration

For monorepos with multiple languages:

```
monorepo/
├── .codeindex.yaml           # Root config
├── backend/
│   ├── .codeindex.yaml       # Python-specific
│   └── src/
├── frontend/
│   ├── .codeindex.yaml       # TypeScript-specific
│   └── src/
└── mobile/
    ├── .codeindex.yaml       # Kotlin-specific
    └── src/
```

```bash
# Scan entire monorepo
find . -name .codeindex.yaml -exec dirname {} \; | \
  xargs -I {} sh -c 'cd {} && codeindex scan-all'
```

## Debugging

### Dry Run with Output

Preview generated AI prompt:

```bash
codeindex scan ./src --ai --dry-run > prompt.txt
cat prompt.txt
```

> **Note**: `--dry-run` requires the `--ai` flag since it previews the AI prompt.

## Integration with Other Tools

### Use with Claude Code

```bash
# Index repo for Claude Code
codeindex scan-all

# Now use with Claude Code skill
claude /mo:arch "Where is authentication implemented?"
```

## Tips & Tricks

### 1. Selective AI Enhancement

```bash
# Generate structural docs for everything (fast)
codeindex scan-all

# Then enhance critical modules with AI
codeindex scan ./src/core --ai
codeindex scan ./src/auth --ai
```

### 2. Conditional Scanning

Only scan if README_AI.md is missing:

```bash
for dir in $(codeindex list-dirs); do
  if [ ! -f "$dir/README_AI.md" ]; then
    codeindex scan "$dir"
  fi
done
```

### 3. Custom AI Per Directory

```bash
# Use different AI for different modules
codeindex scan ./src/ml --ai-command 'claude -p "{prompt}"'
codeindex scan ./src/api --ai-command 'gpt4 "{prompt}"'
```
