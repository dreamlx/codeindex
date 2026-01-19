---
name: mo-index
description: Generate AI-friendly code index using codeindex tool. Use when user wants to index a project, generate README_AI.md files, create code documentation, or make codebase searchable. Triggered by "index this project", "generate code index", "create documentation", "scan codebase".
---

# mo-index - Repository Indexing

Generate AI-friendly index files (README_AI.md) for codebases using codeindex.

## Prerequisites Check

First, verify codeindex is available:

```bash
which codeindex || echo "Not installed. Run: pip install codeindex"
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
- `ai_command` - Your AI CLI command (claude, openai, etc.)
- `include` - Directories to scan
- `exclude` - Patterns to skip

### Step 3: Preview Indexable Directories

```bash
codeindex list-dirs
```

### Step 4: Index Directories

**Single directory (test first):**
```bash
codeindex scan ./src/module --dry-run  # Preview
codeindex scan ./src/module            # Execute
```

**All directories (parallel):**
```bash
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
```

**Fallback mode (no AI):**
```bash
codeindex scan ./src/module --fallback
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

## Example Session

```
User: Index this project

Claude: I'll help you index this project. Let me check the setup first.

> codeindex status
Indexed: 0/3 (0%)
Not indexed: src/, tests/, examples/

> codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
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

## Configuration Reference

`.codeindex.yaml` example:

```yaml
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

include:
  - src/
  - lib/
  - tests/
  - examples/

exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"

output_file: README_AI.md
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| AI CLI timeout | `codeindex scan ./dir --timeout 180` |
| Skip AI entirely | `codeindex scan ./dir --fallback` |
| Debug prompt | `codeindex scan ./dir --dry-run` |

## Post-Indexing Recommendations

1. Commit README_AI.md files to git for team sharing
2. Set up git hooks for auto-updates
3. Add to CLAUDE.md: "Read README_AI.md before modifying code"
