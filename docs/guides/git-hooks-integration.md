# Git Hooks Integration Guide

**Feature**: Automated Git Hooks management

---

## 📋 Overview

codeindex provides built-in Git Hooks management to automate:
- **Pre-commit**: Lint checks (ruff, includes debug-code rules)
- **Pre-push**: Validation before push

> **Post-commit hook removed (GH #167)**: README_AI.md auto-refresh on every
> commit was retired — the per-commit frequency was wrong for a navigation
> index, and the refresh machinery (loop guards, config gating) cost more than
> it returned. README_AI refresh is now **release-time or manual**: run
> `codeindex scan-all` whenever you want fresh indexes, or (in the codeindex
> repo itself) let `scripts/release.sh` step 6.5 refresh before each tag.
> **Migration**: a leftover hook from an older install is silent (its errors
> go to `~/.codeindex/hooks/post-commit.log`) but costs one Python startup
> per commit — `codeindex hooks status` flags it, and
> `codeindex hooks uninstall post-commit` (or `uninstall --all`) removes it.

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
  ✓ pre-push: installed

✓ Successfully installed 2 hook(s)
```

### Verify Installation

```bash
codeindex hooks status
```

Output:
```
Git Hooks Status

  ✓ pre-commit: installed
  ✓ pre-push: installed

→ 2 codeindex hook(s) installed
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
# Uninstall specific hook (also works for a leftover post-commit
# installed by codeindex < 0.37 — see the migration note above)
codeindex hooks uninstall post-commit

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
   - Debug-code detection (print/breakpoint/pdb) is covered by ruff
     rules T201/T100 in the lint check

**Exit Codes**:
- `0` - All checks passed
- `1` - Lint errors found

**Example Output**:
```
🔍 Running pre-commit checks...
   Checking files: 3 Python files

[L1] Running ruff lint...
All checks passed!
✓ Lint check passed

✓ All pre-commit checks passed!
```

### Pre-push Hook

**Purpose**: Validation before push

**Checks**:
1. **Lint check** - Runs `ruff check src/ tests/`
2. **Test suite** - Runs `pytest` (full for master, quick mode for feature/fix branches)
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
  ✓ pre-push: installed

Backups created:
  pre-commit → pre-commit.backup
  pre-push → pre-push.backup
```

Backup location: `.git/hooks/<hook-name>.backup`

### Restore Backups

When uninstalling, backups are automatically restored:

```bash
$ codeindex hooks uninstall --all

Uninstalling Git Hooks

  ✓ pre-commit: uninstalled
  ✓ pre-push: uninstalled

Backups restored:
  pre-commit ← pre-commit.backup
  pre-push ← pre-push.backup
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

### Pre-Commit Configuration

Hooks are not configurable via `.codeindex.yaml`.

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

# 5. Push
git push
```

### Refreshing README_AI

README_AI.md no longer refreshes per-commit. Refresh when you want fresh
navigation (before a release, after a big refactor, or whenever):

```bash
codeindex scan-all          # structural, seconds
codeindex scan-all --ai     # + AI enrichment (cached per directory)
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
A: Hook checks require manual hook editing (see Configuration above).

**Q: What happens if I switch branches?**
A: Hooks persist across branches (stored in `.git/hooks/`, not tracked by Git).

---

## 🎉 Benefits

- ✅ Automatic lint checks (catch errors early)
- ✅ Debug code forbidden (cleaner commits)
- ✅ Consistent code quality across team
- ✅ README_AI refresh at meaningful moments, not per-commit noise

---

## 🔗 Related Documentation

- [Configuration Guide](configuration.md)
- [Getting Started Guide](getting-started.md)
- [Advanced Usage](advanced-usage.md)
