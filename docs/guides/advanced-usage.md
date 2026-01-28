# Advanced Usage

## Parallel Scanning

### Using scan-all (v0.1.2+, Enhanced v0.3.0)

The modern way to scan entire projects with smart AI enhancement:

```bash
# Default: Selective AI enhancement (smart and cost-effective)
codeindex scan-all

# Enhance ALL directories with AI (best quality, more time/cost)
codeindex scan-all --ai-all

# No AI, just SmartWriter (fastest, no API costs)
codeindex scan-all --no-ai

# Custom timeout per directory
codeindex scan-all --timeout 180

# Custom parallel workers
codeindex scan-all --workers 4
```

**How it works:**
1. **Phase 1**: Generate all READMEs with SmartWriter (fast, local)
2. **Phase 2**: Selectively enhance with AI based on strategy:
   - `selective` (default): Only large directories (>40KB)
   - `all`: Every directory gets AI enhancement
   - Manual `--no-ai`: Skip Phase 2 entirely

**Benefits over traditional parallel:**
- Two-phase processing prevents duplicate work
- Intelligent AI selection saves API costs
- Rate limiting prevents API throttling
- Progress tracking with Rich output

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

### Fallback Mode in Parallel

Generate docs without AI for all directories:

```bash
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {} --fallback
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

### Watch Mode (Future)

```bash
# Future feature: watch and auto-regenerate
codeindex watch ./src
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

### Analyze Affected Directories

Find which directories need updates after code changes:

```bash
# Analyze recent changes
codeindex affected --since HEAD~5 --until HEAD

# JSON output for scripting
codeindex affected --json

# Check specific commit range
codeindex affected --since abc123 --until def456

# Use in CI/CD
codeindex affected --json | jq '.directories[]' | xargs -I {} codeindex scan {}
```

**Use cases:**
- Incremental documentation updates
- CI/CD integration
- Pre-commit hooks
- Change impact analysis

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
  echo "❌ Found $CRITICAL critical technical debt issues"
  jq '.files[].issues[] | select(.severity == "CRITICAL")' debt.json
  exit 1
fi

echo "✅ No critical technical debt issues"
```

### Quality Gates

Set thresholds for acceptable debt:

```bash
# Check average quality score
AVG_QUALITY=$(jq '[.files[].quality_score] | add / length' debt.json)

if (( $(echo "$AVG_QUALITY < 70" | bc -l) )); then
  echo "❌ Average quality score $AVG_QUALITY below threshold (70)"
  exit 1
fi
```

## Multi-turn Dialogue for Super Large Files (v0.3.0+)

### Automatic Detection

For files >5000 lines or >100 symbols, use multi-turn dialogue:

```bash
# Auto-detect and use multi-turn when needed
codeindex scan ./huge-file --strategy auto

# Force multi-turn dialogue
codeindex scan ./huge-file --strategy multi_turn

# Force standard enhancement (single AI call)
codeindex scan ./huge-file --strategy standard
```

### How Multi-turn Works

**Three-round dialogue for better quality:**

1. **Round 1: Architecture Overview** (10-20 lines)
   - High-level architecture
   - Main responsibilities
   - Key design patterns

2. **Round 2: Core Component Analysis** (30-60 lines)
   - Detailed component breakdown
   - Symbol grouping by responsibility
   - Integration points

3. **Round 3: Final README Synthesis** (100+ lines)
   - Complete documentation
   - Combines rounds 1 + 2
   - Usage examples and patterns

**Benefits:**
- Better quality for huge files
- Avoids AI context limits
- Focused analysis per round
- Graceful fallback on failure

### Configuration

Configure multi-turn thresholds:

```yaml
# .codeindex.yaml
multi_turn:
  enabled: true
  line_threshold: 5000      # >5000 lines triggers multi-turn
  symbol_threshold: 100     # >100 symbols triggers multi-turn
  timeout_per_round: 120    # Timeout for each round
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
        run: pipx install codeindex

      - name: Install Claude CLI
        run: |
          # Install your AI CLI here
          npm install -g @anthropic-ai/claude-cli

      - name: Generate indexes
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          codeindex init
          codeindex list-dirs | xargs -P 4 -I {} codeindex scan {} --fallback

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
    - pip install codeindex
    - codeindex list-dirs | xargs -P 4 -I {} codeindex scan {} --fallback
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

### JSON Output (Future)

```bash
# Future feature: structured output
codeindex scan ./src --format json > index.json
```

## Pre-commit Hooks

Automatically regenerate indexes on commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: codeindex
        name: Update code indexes
        entry: bash -c 'git diff --cached --name-only | xargs -n1 dirname | sort -u | xargs -I {} codeindex scan {} --fallback'
        language: system
        pass_filenames: false
```

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
  xargs -I {} sh -c 'cd {} && codeindex list-dirs | xargs -P 4 -I @ codeindex scan @'
```

## Debugging

### Verbose Output

```bash
# Future feature: verbose logging
codeindex scan ./src --verbose
```

### Dry Run with Output

Preview generated prompt:

```bash
codeindex scan ./src --dry-run > prompt.txt
cat prompt.txt
```

### Check Configuration

```bash
# Future feature: validate config
codeindex validate-config
```

## Integration with Other Tools

### Use with MCP Servers

```bash
# Index repo for Claude Code
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {} --fallback

# Now use with Claude Code skill
claude /sc:arch-query "Where is authentication implemented?"
```

### Export to Other Formats

```bash
# Future feature: export to different formats
codeindex export --format markdown > full-index.md
codeindex export --format json > index.json
codeindex export --format html > index.html
```

## Tips & Tricks

### 1. Speed up with Fallback First

```bash
# Generate basic docs first (fast)
codeindex list-dirs | xargs -P 8 -I {} codeindex scan {} --fallback

# Then enhance with AI selectively
codeindex scan ./src/core  # AI-enhanced
```

### 2. Use Cache (Future Feature)

```bash
codeindex scan ./src --use-cache
```

### 3. Parallel + Dry Run

Preview prompts for all directories:

```bash
codeindex list-dirs | xargs -I {} sh -c 'echo "=== {} ===" && codeindex scan {} --dry-run'
```

### 4. Conditional Scanning

Only scan if README_AI.md is missing:

```bash
for dir in $(codeindex list-dirs); do
  if [ ! -f "$dir/README_AI.md" ]; then
    codeindex scan "$dir"
  fi
done
```

### 5. Custom AI Per Directory

```bash
# Use different AI for different modules
codeindex scan ./src/ml --ai-command 'claude -p "{prompt}"'
codeindex scan ./src/api --ai-command 'gpt4 "{prompt}"'
```