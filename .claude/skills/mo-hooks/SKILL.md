---
name: mo-hooks
description: Set up codeindex Git hooks for automatic README_AI.md updates on commit. Use when user wants auto-updating documentation, git hook setup for codeindex, or automatic index refresh when code changes. Triggered by "set up auto-update", "install hooks", "auto-update README_AI.md", "keep docs in sync".
---

# mo-hooks - Auto-Update Hooks Setup

Set up Git hooks so README_AI.md files automatically update when code changes are committed.

## How It Works

When a developer commits code changes:
1. **post-commit hook** detects which directories were affected
2. `codeindex affected --json` analyzes the change scope
3. `codeindex scan` regenerates README_AI.md for affected directories
4. Updated README_AI.md files are auto-committed

This keeps documentation always in sync with code — zero manual effort.

## Prerequisites

```bash
# 1. codeindex must be installed
which codeindex || echo "Not installed. Run: pip install ai-codeindex"

# 2. Project must be a git repository
git rev-parse --is-inside-work-tree

# 3. Project must have codeindex config
cat .codeindex.yaml 2>/dev/null || codeindex init
```

## Setup Workflow

### Step 1: Check Current Hook Status

```bash
codeindex hooks status
```

This shows which hooks are installed (pre-commit, post-commit, pre-push).

### Step 2: Install Post-Commit Hook

```bash
# Install just the post-commit hook (recommended)
codeindex hooks install post-commit

# Or install all hooks
codeindex hooks install --all
```

If a custom post-commit hook already exists, it will be backed up automatically.

### Step 3: Configure Hook Behavior

Edit `.codeindex.yaml` to add/adjust the hooks section:

```yaml
# Git Hooks configuration
hooks:
  post_commit:
    enabled: true
    mode: auto          # auto | sync | async | prompt | disabled
    max_dirs_sync: 2    # Threshold for sync vs async (auto mode)
```

**Modes explained:**

| Mode | Behavior |
|------|----------|
| `auto` | Smart: sync for small changes (<=2 dirs), async for large |
| `sync` | Always wait for update to complete before returning |
| `async` | Always run in background (non-blocking) |
| `prompt` | Show notification but don't auto-update. User runs `codeindex affected --update` manually |
| `disabled` | Hook installed but inactive |

### Step 4: Verify Setup

```bash
# Check hook is installed
codeindex hooks status

# Make a test change and commit
echo "# test" >> some_file.py
git add some_file.py
git commit -m "test: verify auto-update hook"

# Check if README_AI.md was updated
git log --oneline -2
# Should see: "docs: auto-update README_AI.md for <hash>"
```

### Step 5: Generate Initial Index (if not done)

The hook only updates existing README_AI.md files. Generate the initial index first:

```bash
codeindex scan-all
git add -A && git commit -m "docs: initial README_AI.md generation"
```

## Example Session

```
User: Set up auto-updating docs for this project

Claude: I'll set up the codeindex post-commit hook so README_AI.md
files stay in sync with code changes.

> codeindex hooks status
  ○ pre-commit: not installed
  ○ post-commit: not installed
  ○ pre-push: not installed

> codeindex hooks install post-commit
  ✓ post-commit: installed

Let me also make sure the hooks config is in .codeindex.yaml...

> cat .codeindex.yaml
[checks for hooks section]

Done! Post-commit hook installed. Now when you commit code changes:
- README_AI.md files auto-update for affected directories
- Updates are committed automatically
- Doc-only commits are skipped (no infinite loops)
```

## Uninstalling

```bash
# Remove post-commit hook (restores backup if exists)
codeindex hooks uninstall post-commit

# Remove all codeindex hooks
codeindex hooks uninstall --all
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Hook not triggering | Check `codeindex hooks status` — must show "installed" |
| Infinite commit loop | Should not happen — hook skips doc-only commits. If it does, run `codeindex hooks uninstall post-commit` |
| Hook too slow | Set `mode: async` in .codeindex.yaml hooks config |
| Want manual control | Set `mode: prompt` — shows notification, you decide when to update |
| Virtual env not found | Ensure `.venv/` or `venv/` exists at project root |

## Advanced: CLAUDE.md Integration

Add this to your project's CLAUDE.md to teach AI agents about the auto-update:

```markdown
## Documentation Auto-Updates

This project uses codeindex with post-commit hooks.
README_AI.md files auto-update when code changes.

- **Read README_AI.md first** before exploring source code
- After modifying code, README_AI.md updates on next commit
- To manually update: `codeindex scan ./path/to/dir`
- To check coverage: `codeindex status`
```
