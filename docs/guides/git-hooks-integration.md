# Git Hooks Integration Guide

**Version**: v0.17.2
**Feature**: Automated Git Hooks management

---

## 📋 Overview

codeindex now provides built-in Git Hooks management to automate:
- **Pre-commit**: Lint checks and debug code detection
- **Post-commit**: Automatic README_AI.md updates
- **Pre-push**: Lint and test validation before push

No manual hook creation needed - install with one command!

---

## 🚀 Quick Start

### Check Current Status

```bash
codeindex hooks status
```

Output:
```
Git Hooks Status

  ○ pre-commit: not installed
  ○ post-commit: not installed
  ○ pre-push: not installed
```

### Install All Hooks

```bash
codeindex hooks install --all
```

Output:
```
Installing Git Hooks

  ✓ pre-commit: installed
  ✓ post-commit: installed
  ✓ pre-push: installed

✓ Successfully installed 3 hook(s)
```

### Verify Installation

```bash
codeindex hooks status
```

Output:
```
Git Hooks Status

  ✓ pre-commit: installed
  ✓ post-commit: installed
  ✓ pre-push: installed

→ 3 codeindex hook(s) installed
```

---

## 📚 Commands Reference

### `codeindex hooks status`

Show status of all Git hooks.

**Output**:
- `✓ installed` - codeindex-managed hook
- `⚠ custom` - User's custom hook
- `○ not installed` - No hook

### `codeindex hooks install`

Install Git hooks.

**Options**:
- `--all` - Install all supported hooks
- `--force` - Overwrite existing codeindex hooks

**Examples**:
```bash
# Install specific hook
codeindex hooks install pre-commit

# Install all hooks
codeindex hooks install --all

# Force reinstall (overwrite existing)
codeindex hooks install --all --force
```

**Behavior**:
- Automatically backs up existing custom hooks
- Skips already-installed codeindex hooks (unless `--force`)
- Creates `.git/hooks/<hook-name>`
- Makes hooks executable

### `codeindex hooks uninstall`

Uninstall codeindex Git hooks.

**Options**:
- `--all` - Uninstall all codeindex hooks
- `--keep-backup` - Don't restore backup when uninstalling

**Examples**:
```bash
# Uninstall specific hook
codeindex hooks uninstall pre-commit

# Uninstall all hooks
codeindex hooks uninstall --all

# Uninstall but keep backup (don't restore)
codeindex hooks uninstall --all --keep-backup
```

**Behavior**:
- Only uninstalls codeindex-managed hooks
- Restores backup if it exists (unless `--keep-backup`)
- Does NOT remove custom hooks

---

## 🔧 Hook Descriptions

### Pre-commit Hook

**Purpose**: Quality checks before commit

**Checks**:
1. **L1: Ruff Lint** - Code style and quality
   - Checks only staged Python files
   - Auto-detects ruff (venv or system)
   - Provides fix suggestions

2. **L2: Debug Code Detection** - Forbid debug statements
   - Detects: `print()`, `breakpoint()`, `pdb.set_trace()`
   - Skips CLI files (legitimate print usage)
   - Shows line numbers for violations

**Exit Codes**:
- `0` - All checks passed
- `1` - Lint errors or debug code found

**Example Output**:
```
🔍 Running pre-commit checks...
   Checking files: 3 Python files

[L1] Running ruff lint...
All checks passed!
✓ Lint check passed

[L2] Checking for debug code...
✓ No debug code found

✓ All pre-commit checks passed!
```

### Post-commit Hook

**Purpose**: Automatic structural documentation updates

**Architecture** (v0.23.0+): Thin wrapper pattern
- Shell script (~30 lines): loop guard + venv activation
- Python logic via `codeindex hooks run post-commit`: all business logic
- **Upgrade path**: `pip install --upgrade ai-codeindex` automatically updates hook behavior (no need to reinstall hooks)

**Features**:
- Analyzes commit changes (`codeindex affected`)
- Runs `codeindex scan` for affected directories (structural regeneration)
- Creates follow-up commit with updates
- Avoids infinite loops (skips doc-only commits)
- No custom AI prompts — uses standard codeindex scan pipeline

**Workflow**:
```
Code Change Commit
    ↓
Shell wrapper (loop guard + venv)
    ↓
codeindex hooks run post-commit  (Python)
    ↓
codeindex affected --json → affected directories
    ↓
codeindex scan <dir> for each → structural README_AI.md update
    ↓
Auto-commit: "docs: auto-update README_AI.md for <hash>"
```

> **Note**: Post-commit hook only updates structural content. AI-generated
> module descriptions (blockquotes) are not regenerated on every commit —
> they describe module purpose which rarely changes. Run `codeindex scan-all`
> (with `ai_command` configured) to refresh AI descriptions.

### Pre-push Hook

**Purpose**: Validation before push

**Checks**:
1. **Lint check** - Runs `ruff check src/ tests/`
2. **Test suite** - Runs `pytest` (full for develop/master, quick mode for feature/fix branches)
3. **Version consistency** (master only) - Runs `scripts/check_version_consistency.py` to ensure version numbers match across all files

**Note**: The CLI-installed pre-push hook (`codeindex hooks install pre-push`) generates a minimal placeholder. For the full-featured pre-push template with lint+tests, see `scripts/hooks/pre-push` and copy it manually to `.git/hooks/pre-push`.

---

## 🛡️ Backup and Safety

### Automatic Backups

When installing hooks, codeindex automatically backs up existing custom hooks:

```bash
$ codeindex hooks install --all

Installing Git Hooks

  ✓ pre-commit: installed
  ✓ post-commit: installed

Backups created:
  pre-commit → pre-commit.backup
  post-commit → post-commit.backup
```

Backup location: `.git/hooks/<hook-name>.backup`

### Restore Backups

When uninstalling, backups are automatically restored:

```bash
$ codeindex hooks uninstall --all

Uninstalling Git Hooks

  ✓ pre-commit: uninstalled
  ✓ post-commit: uninstalled

Backups restored:
  pre-commit ← pre-commit.backup
  post-commit ← post-commit.backup
```

### Manual Backup Management

Backups are regular files - manage them manually:

```bash
# View backups
ls -la .git/hooks/*.backup

# Manually restore
mv .git/hooks/pre-commit.backup .git/hooks/pre-commit

# Remove backups
rm .git/hooks/*.backup
```

---

## ⚙️ Configuration

### Post-Commit Hook Configuration

**NEW in v0.7.0** (Story 6): Post-commit hooks are now fully configurable via `.codeindex.yaml`.

Add to your `.codeindex.yaml`:

```yaml
hooks:
  post_commit:
    mode: auto             # auto | disabled | async | sync | prompt
    max_dirs_sync: 2       # Auto mode threshold (≤2 = sync, >2 = async)
    enabled: true          # Master switch
    log_file: ~/.codeindex/hooks/post-commit.log
```

#### Mode Options

| Mode | Behavior | Use Case |
|------|----------|----------|
| `auto` **(default)** | Smart detection: ≤2 dirs = sync, >2 = async | Balanced UX (non-blocking for large projects) |
| `disabled` | Completely disabled | Temporary disable or CI environments |
| `async` | Always run in background (non-blocking) | Large projects, fast commits |
| `sync` | Always run synchronously (blocking) | Small projects, immediate feedback |
| `prompt` | Only show reminder, don't auto-execute | Manual control, batch updates |

#### Examples

**Disable post-commit hook**:
```yaml
hooks:
  post_commit:
    mode: disabled
    enabled: false
```

**Always async (non-blocking)**:
```yaml
hooks:
  post_commit:
    mode: async
    log_file: ~/.my-logs/post-commit.log
```

**Always sync (blocking)**:
```yaml
hooks:
  post_commit:
    mode: sync
```

**Prompt only (manual updates)**:
```yaml
hooks:
  post_commit:
    mode: prompt
```

**Custom threshold for auto mode**:
```yaml
hooks:
  post_commit:
    mode: auto
    max_dirs_sync: 5  # ≤5 dirs = sync, >5 = async
```

#### Async Mode Output

When async mode is active, you'll see:

```bash
⚡ Running in async mode (non-blocking)
   3 directories will be updated in background
   Log: ~/.codeindex/hooks/post-commit.log

   To check progress: tail -f ~/.codeindex/hooks/post-commit.log
   Or wait for completion: while [ -f ~/.codeindex/hooks/post-commit.lock ]; do sleep 1; done

✓ You can continue working. Updates will commit automatically.
```

#### Prompt Mode Output

When prompt mode is active, you'll see:

```bash
⚠️ README_AI.md updates available
   3 directories need updating
   Run: codeindex scan <affected-dirs>
```

### Pre-Commit Configuration

Pre-commit hooks are not yet configurable via `.codeindex.yaml`.

To disable lint check, manually edit `.git/hooks/pre-commit` and comment out the L1 section.

---

## 🔄 Workflow Integration

### Typical Development Workflow

```bash
# 1. Initialize project
git clone <repo>
cd <repo>

# 2. Install codeindex hooks
codeindex hooks install --all

# 3. Make changes
vim src/mymodule.py

# 4. Commit (pre-commit runs automatically)
git add src/mymodule.py
git commit -m "feat: add new feature"

   🔍 Running pre-commit checks...
   ✓ All checks passed!

# 5. Post-commit runs (updates README_AI.md)
   📝 Post-commit: Analyzing changes...
   ✓ README_AI.md updated

# 6. Push
git push
```

### CI/CD Integration

Hooks run locally, not in CI. For CI validation:

```yaml
# .github/workflows/ci.yml
- name: Run lint
  run: ruff check src/

- name: Check for debug code
  run: |
    if grep -r "print(" src/ --exclude-dir=cli*; then
      echo "Debug code found"
      exit 1
    fi
```

---

## 🚨 Troubleshooting

### Hook Not Running

**Problem**: Commit succeeds but no hook output

**Solutions**:
1. Check hook exists: `ls -la .git/hooks/pre-commit`
2. Check executable: `chmod +x .git/hooks/pre-commit`
3. Verify hook: `cat .git/hooks/pre-commit`
4. Test manually: `.git/hooks/pre-commit`

### Hooks Interfere with Workflow

**Problem**: Don't want hooks to run

**Temporary Bypass**:
```bash
# Skip hooks for one commit
git commit --no-verify -m "message"
```

**Permanent Disable**:
```bash
# Uninstall all hooks
codeindex hooks uninstall --all

# Or remove specific hook
rm .git/hooks/pre-commit
```

### Hook Fails with Error

**Problem**: Hook exits with error

**Debug**:
```bash
# Run hook manually to see full error
.git/hooks/pre-commit

# Check hook content
cat .git/hooks/pre-commit

# Reinstall hook
codeindex hooks install pre-commit --force
```

### Ruff Not Found

**Problem**: `ruff not found` error

**Solutions**:
```bash
# Install ruff in project venv
pip install ruff

# Or install system-wide
brew install ruff  # macOS
```

### Post-commit Creates Infinite Loop

**Problem**: Commits keep triggering more commits

**Protection Built-in**: Post-commit hook automatically skips if commit only contains documentation files.

**Manual Fix** (if needed):
```bash
# Temporarily disable post-commit
mv .git/hooks/post-commit .git/hooks/post-commit.disabled

# Make commits
git commit -m "fix"

# Re-enable
mv .git/hooks/post-commit.disabled .git/hooks/post-commit
```

---

## 🎓 Advanced Usage

### Customizing Hooks

Hooks are generated from templates but can be manually edited:

```bash
# Edit installed hook
vim .git/hooks/pre-commit

# Add custom checks
# Example: Add mypy type checking
if command -v mypy &> /dev/null; then
    echo "Running mypy..."
    mypy src/
fi
```

**Note**: Manual edits will be lost if you reinstall with `--force`.

### Hook Architecture and Upgrades

**Thin wrapper pattern** (v0.23.0+):

Post-commit hooks use a thin shell wrapper that delegates to Python:

```
.git/hooks/post-commit (shell, ~30 lines)
    → loop guard (skip doc-only commits)
    → activate venv
    → codeindex hooks run post-commit  ← Python logic

codeindex hooks run post-commit (Python, in cli_hooks.py)
    → codeindex affected --json
    → codeindex scan <dir> for each affected dir
    → git add + git commit
```

**Upgrade behavior**:
- `pip install --upgrade ai-codeindex` → Python logic auto-updates, no hook reinstall needed
- `codeindex hooks install --force` → only needed if shell wrapper itself changes (rare)
- Hooks are marked with `# codeindex-managed hook` comment

**To update hooks to latest version**:

```bash
# Usually not needed (Python logic auto-updates via pip)
# Only if instructed by release notes:
codeindex hooks install --all --force
```

### Multiple Projects

Each Git repository has independent hooks:

```bash
# Project A
cd /path/to/project-a
codeindex hooks install --all

# Project B
cd /path/to/project-b
codeindex hooks install --all
```

---

## 📖 FAQ

**Q: Do hooks run in CI/CD?**
A: No, Git hooks run locally only. Configure separate CI checks.

**Q: Can I use codeindex hooks with other tools' hooks?**
A: Yes! codeindex backs up existing hooks and can coexist with other hook managers like pre-commit framework.

**Q: What if I already have pre-commit framework?**
A: codeindex hooks are independent. You can use both:
- pre-commit framework: Runs first (if configured)
- codeindex hooks: Runs after

**Q: How do I share hooks with my team?**
A: Each developer runs `codeindex hooks install --all` after cloning the repo. Alternatively, `codeindex init` offers to install hooks during interactive setup.

**Q: Can I disable specific checks?**
A: Pre-commit checks require manual hook editing. Post-commit hooks are fully configurable via `.codeindex.yaml` (see Configuration section above) with 5 modes: `auto`, `disabled`, `async`, `sync`, `prompt`.

**Q: What happens if I switch branches?**
A: Hooks persist across branches (stored in `.git/hooks/`, not tracked by Git).

---

## 🎉 Benefits

**Before Git Hooks Integration**:
- ❌ Manual lint checks before commit
- ❌ Debug code slips into commits
- ❌ README_AI.md becomes outdated
- ❌ Inconsistent code quality

**After Git Hooks Integration**:
- ✅ Automatic lint checks (catch errors early)
- ✅ Debug code forbidden (cleaner commits)
- ✅ README_AI.md always up-to-date
- ✅ Consistent code quality across team

---

## 🔗 Related Documentation

- [Configuration Guide](configuration.md)
- [Getting Started Guide](getting-started.md)
- [Advanced Usage](advanced-usage.md)

---

**Last Updated**: 2026-03-12
**Status**: Production Ready (v0.23.0)
