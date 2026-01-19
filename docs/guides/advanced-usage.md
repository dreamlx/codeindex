# Advanced Usage

## Parallel Scanning

### Using xargs

Scan multiple directories in parallel with 4 workers:

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
