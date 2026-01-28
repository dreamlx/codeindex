# Getting Started with codeindex

## What is codeindex?

codeindex is an AI-native code indexing tool that generates intelligent documentation (`README_AI.md`) for your codebase directories. It uses tree-sitter for code parsing and integrates with external AI CLIs to create comprehensive, context-aware documentation.

## Installation

### Using pipx (Recommended)

```bash
pipx install codeindex
```

### Using pip

```bash
pip install codeindex
```

### From source

```bash
git clone https://github.com/yourusername/codeindex.git
cd codeindex
pip install -e .
```

## Quick Start

### 1. Initialize Configuration

Navigate to your project and create a configuration file:

```bash
cd /your/project
codeindex init
```

This creates `.codeindex.yaml` in your project root.

### 2. Configure AI CLI

Edit `.codeindex.yaml` to set up your AI CLI command:

```yaml
# Example with Claude CLI
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Or with other AI CLIs:
# ai_command: 'opencode run "{prompt}"'
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
codeindex scan ./src/auth
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

### 5. Batch Scanning (v0.1.2+)

Scan all directories at once with two-phase processing:

```bash
# Smart batch scanning with AI enhancement
codeindex scan-all                # Uses config ai_enhancement strategy
codeindex scan-all --ai-all       # Enhance ALL directories with AI
codeindex scan-all --no-ai        # SmartWriter only (fast, no AI costs)

# Traditional parallel scanning
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
```

**Two-phase processing** (default):
1. Phase 1: Generate all READMEs with SmartWriter (fast)
2. Phase 2: Selectively enhance with AI (large directories only)

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

## No AI? Use Fallback Mode

If you don't have an AI CLI configured, you can generate basic documentation:

```bash
codeindex scan ./src/auth --fallback
```

This creates a structured overview without AI enhancement.

## Preview Before Generation

Want to see what prompt will be sent to the AI?

```bash
codeindex scan ./src/auth --dry-run
```

## Next Steps

- [Configuration Guide](./configuration.md) - Deep dive into all config options
- [Advanced Usage](./advanced-usage.md) - Parallel scanning, custom prompts
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

- Check the [FAQ](./faq.md)
- [Open an issue](https://github.com/yourusername/codeindex/issues)
- [Join discussions](https://github.com/yourusername/codeindex/discussions)