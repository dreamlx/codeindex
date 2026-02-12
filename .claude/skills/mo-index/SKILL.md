---
name: mo-index
description: Generate AI-friendly code index using codeindex tool. Use when user wants to index a project, generate README_AI.md files, create code documentation, or make codebase searchable. Triggered by "index this project", "generate code index", "create documentation", "scan codebase".
---

# mo-index - Repository Indexing

Generate AI-friendly index files (README_AI.md) for codebases using codeindex.

## Prerequisites Check

First, verify codeindex is available:

```bash
which codeindex || echo "Not installed. Run: pip install ai-codeindex"
```

## Workflow

### Step 1: Initialize (if needed)

```bash
# Check for config
cat .codeindex.yaml 2>/dev/null || codeindex init
```

### Step 2: Review Configuration

```bash
cat .codeindex.yaml
```

Key settings to verify:
- `languages` - Detected programming languages (python, java, php)
- `include` - Directories to scan
- `exclude` - Patterns to skip

### Step 3: Preview Indexable Directories

```bash
codeindex list-dirs
```

### Step 4: Index Directories

**All directories (recommended - structural documentation, works immediately):**
```bash
codeindex scan-all
```

**Single directory:**
```bash
codeindex scan ./src/module
```

**AI-enhanced mode (requires ai_command in config):**
```bash
codeindex scan-all --ai
codeindex scan ./src/module --ai --dry-run  # Preview AI prompt
```

### Step 5: Generate Project Index

```bash
codeindex index
```

Creates `PROJECT_INDEX.md` with module overview.

### Step 6: Verify Coverage

```bash
codeindex status
```

### Step 7 (Optional): Set Up Auto-Updates

```bash
codeindex hooks install post-commit
```

This installs a post-commit hook that auto-updates README_AI.md when code changes.

## Example Session

```
User: Index this project

Claude: I'll help you index this project. Let me check the setup first.

> codeindex status
Indexed: 0/3 (0%)
Not indexed: src/, tests/, examples/

> codeindex scan-all
✓ Created: src/codeindex/README_AI.md
✓ Created: tests/README_AI.md
✓ Created: examples/README_AI.md

> codeindex index
✓ Created: PROJECT_INDEX.md

Done! Your project is now indexed:
- 3 directory indexes (README_AI.md)
- 1 project index (PROJECT_INDEX.md)
- Coverage: 100%
```

## Scan Modes

| Mode | Command | Description |
|------|---------|-------------|
| Structural (default) | `codeindex scan-all` | Fast, no AI needed, works immediately |
| AI-enhanced | `codeindex scan-all --ai` | Richer docs, requires ai_command config |

## Configuration Reference

`.codeindex.yaml` example:

```yaml
version: 1

# Optional: AI CLI command (only needed for --ai mode)
# ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

languages:
  - python

include:
  - src/
  - lib/

exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"

output_file: README_AI.md

# Optional: Auto-update hooks
hooks:
  post_commit:
    enabled: true
    mode: auto  # auto | sync | async | prompt | disabled
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| AI CLI timeout | `codeindex scan ./dir --ai --timeout 180` |
| AI not configured | Use `codeindex scan-all` (structural mode, no AI needed) |
| Debug AI prompt | `codeindex scan ./dir --ai --dry-run` |
| Missing parser | `pip install ai-codeindex[java]` (or python, php) |

## Post-Indexing Recommendations

1. Commit README_AI.md files to git for team sharing
2. Set up git hooks for auto-updates: `codeindex hooks install post-commit`
3. Add to CLAUDE.md: "Read README_AI.md before modifying code"
