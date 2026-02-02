# Git Hooks Integration Guide

**Version**: v0.5.0-beta1
**Feature**: Automated Git Hooks management
**Epic**: 6, P3.1 - Git Hooks Integration

---

## 📋 Overview

codeindex now provides built-in Git Hooks management to automate:
- **Pre-commit**: Lint checks and debug code detection
- **Post-commit**: Automatic README_AI.md updates
- **Pre-push**: Pre-push validation (placeholder)

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

**Purpose**: Automatic documentation updates

**Features**:
- Analyzes commit changes (`codeindex affected`)
- Updates README_AI.md for affected directories
- Creates follow-up commit with updates
- Avoids infinite loops (skips doc-only commits)

**Workflow**:
```
Code Change Commit
    ↓
Post-commit Hook Triggered
    ↓
Analyze: Which directories changed?
    ↓
Update: README_AI.md files
    ↓
Auto-commit: "docs: auto-update README_AI.md for <hash>"
```

**Example Output**:
```
📝 Post-commit: Analyzing changes...
   Update level: full
   Found 2 directory(ies) to check

→ Updating src/codeindex/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

✓ Post-commit hook completed
```

### Pre-push Hook

**Purpose**: Validation before push (placeholder)

Currently a placeholder. Can be customized for:
- Running tests
- Checking CI status
- Validating commit messages
- Running security checks

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

### Disable Lint Check

Currently, hooks are not configurable via `.codeindex.yaml`.

To disable lint check, manually edit `.git/hooks/pre-commit` and comment out the L1 section.

**Future**: Configuration support in `.codeindex.yaml` (v0.6.0+)

```yaml
# Future feature
hooks:
  pre_commit:
    lint_enabled: false
    debug_check_enabled: true
  post_commit:
    auto_update: true
```

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

### Hook Versioning

Hooks are marked with `# codeindex-managed hook` comment.

To update hooks to latest version:

```bash
# Reinstall all hooks
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
A: Each developer runs `codeindex hooks install --all` after cloning the repo.

**Q: Can I disable specific checks?**
A: Currently requires manual hook editing. Configuration support coming in v0.6.0.

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

- [Epic 6 Sprint Plan](../planning/sprint1-epic6-execution.md)
- [Git Hooks UX Design](../planning/git-hooks-ux-design.md)
- [Configuration Guide](configuration.md)
- [Developer Workflow](../development/developer-workflow.md)

---

**Generated**: 2026-02-02
**Author**: Claude Sonnet 4.5
**Status**: ✅ Production Ready (v0.5.0-beta1)
