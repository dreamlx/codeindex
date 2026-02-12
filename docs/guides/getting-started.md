# Getting Started with codeindex

## What is codeindex?

codeindex is a universal code parser that extracts symbols, inheritance, call relationships, and imports from Python, PHP, and Java using tree-sitter. It generates AI-friendly documentation (`README_AI.md`) and structured JSON output for AI tools, knowledge graphs, and code intelligence platforms.

## Installation

### Using pipx (Recommended)

```bash
pipx install ai-codeindex[all]
```

### Using pip

```bash
# All languages
pip install ai-codeindex[all]

# Or specific languages only
pip install ai-codeindex[python]
pip install ai-codeindex[php]
pip install ai-codeindex[java]
```

### From source

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"
```

## Quick Start

### 1. Initialize Configuration

Navigate to your project and run the setup wizard:

```bash
cd /your/project
codeindex init
```

This creates three files:
- `.codeindex.yaml` — scan configuration (languages, include/exclude patterns)
- `CLAUDE.md` — injects codeindex instructions so Claude Code uses README_AI.md automatically
- `CODEINDEX.md` — project-level documentation reference

### 2. Configure AI CLI (Optional)

For AI-enhanced documentation, edit `.codeindex.yaml`:

```yaml
# AI CLI command (optional — scanning works without this)
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Or with other AI CLIs:
# ai_command: 'openai chat "{prompt}" --model gpt-4'
# ai_command: 'gemini "{prompt}"'

include:
  - src/
  - lib/

exclude:
  - "**/test/**"
  - "**/node_modules/**"
  - "**/__pycache__/**"

languages:
  - python

output_file: "README_AI.md"
```

### 3. Scan a Directory

Generate documentation for a single directory:

```bash
# Structural documentation (default, no AI needed)
codeindex scan ./src/auth

# AI-enhanced documentation (requires ai_command in config)
codeindex scan ./src/auth --ai
```

This creates `./src/auth/README_AI.md`.

### 4. Check Status

See which directories have been indexed:

```bash
codeindex status
```

Output:
```
Indexing Status
───────────────────────────────────────
✅ src/auth/
✅ src/utils/
⚠️  src/api/ (no README_AI.md)
✅ src/db/

Indexed: 3/4 (75%)
```

### 5. Batch Scanning

Scan all directories at once:

```bash
# Structural documentation for entire project
codeindex scan-all

# AI-enhanced documentation for entire project
codeindex scan-all --ai

# Traditional parallel scanning
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
```

### 6. Symbol Indexes (v0.1.2+)

Generate project-wide indexes for navigation:

```bash
# Global symbol index (all classes/functions)
codeindex symbols

# Module overview (directory structure)
codeindex index

# Analyze changes (for incremental updates)
codeindex affected --since HEAD~5
```

### 7. Technical Debt Analysis (v0.3.0+)

Detect code quality issues:

```bash
# Analyze directory
codeindex tech-debt ./src

# Different output formats
codeindex tech-debt ./src --format markdown
codeindex tech-debt ./src --format json

# Recursive analysis
codeindex tech-debt ./src --recursive
```

## Preview Before Generation

Want to see what prompt will be sent to the AI?

```bash
codeindex scan ./src/auth --ai --dry-run
```

> **Note**: `--dry-run` requires the `--ai` flag since it previews the AI prompt.

## Next Steps

- [Configuration Guide](./configuration.md) - Deep dive into all config options
- [Advanced Usage](./advanced-usage.md) - Parallel scanning, custom prompts
- [Claude Code Integration](./claude-code-integration.md) - AI agent setup
- [Contributing](./contributing.md) - Help improve codeindex

## Troubleshooting

### "AI command failed"

Check that your AI CLI is installed and accessible:
```bash
which claude  # or your AI CLI name
```

### "No such file or directory"

Make sure you're in a project directory and have run `codeindex init`.

### "Permission denied"

Check file permissions:
```bash
chmod +x $(which codeindex)
```

## Need Help?

- [Open an issue](https://github.com/dreamlx/codeindex/issues)
- [Join discussions](https://github.com/dreamlx/codeindex/discussions)
