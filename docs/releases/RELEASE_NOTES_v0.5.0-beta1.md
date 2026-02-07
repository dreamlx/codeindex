# Release Notes v0.5.0-beta1

**Release Date**: 2026-02-02
**Status**: Beta Release
**Epic**: Epic 6, P3.1 - Git Hooks Integration

---

## 🎉 What's New

### Git Hooks Management System

codeindex now provides **built-in Git Hooks management** to automate code quality checks and documentation updates!

#### Key Features

**1. One-Command Installation**
```bash
codeindex hooks install --all
```

**2. Automated Quality Checks (Pre-commit)**
- ✅ **Ruff lint** - Catch style issues before commit
- ✅ **Debug code detection** - Block print()/breakpoint() statements
- ✅ **Smart filtering** - Skips CLI files that legitimately use print()

**3. Automatic Documentation (Post-commit)**
- ✅ **Smart change analysis** - Detects which directories changed
- ✅ **Auto-update README_AI.md** - Keeps documentation in sync
- ✅ **Infinite loop prevention** - Skips doc-only commits

**4. Safety First**
- ✅ **Automatic backups** - Preserves existing custom hooks
- ✅ **Easy restore** - Uninstall restores backups automatically
- ✅ **Status visibility** - See what's installed at a glance

---

## 📦 CLI Commands

### `codeindex hooks install`

Install Git hooks with automatic backup of existing hooks.

```bash
# Install specific hook
codeindex hooks install pre-commit

# Install all hooks
codeindex hooks install --all

# Force reinstall (overwrite existing)
codeindex hooks install --all --force
```

### `codeindex hooks uninstall`

Uninstall codeindex hooks and optionally restore backups.

```bash
# Uninstall specific hook
codeindex hooks uninstall pre-commit

# Uninstall all hooks
codeindex hooks uninstall --all

# Uninstall but keep backup
codeindex hooks uninstall --all --keep-backup
```

### `codeindex hooks status`

Show status of all Git hooks.

```bash
codeindex hooks status
```

Output:
```
Git Hooks Status

  ✓ pre-commit: installed
  ✓ post-commit: installed
  ○ pre-push: not installed

→ 2 codeindex hook(s) installed
```

---

## 🔧 How It Works

### Pre-commit Hook

**Runs before every commit** to ensure code quality:

1. **L1: Lint Check**
   - Runs `ruff check` on staged Python files
   - Auto-detects ruff from venv or system
   - Provides fix suggestions

2. **L2: Debug Code Detection**
   - Blocks `print()`, `breakpoint()`, `pdb.set_trace()`
   - Skips CLI files (legitimate print usage)
   - Shows line numbers for violations

**Example Output:**
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

**Runs after every commit** to keep documentation updated:

1. Analyzes commit changes (`codeindex affected`)
2. Updates README_AI.md for affected directories
3. Creates follow-up commit automatically
4. Skips if only doc files changed (avoids loops)

**Example Output:**
```
📝 Post-commit: Analyzing changes...
   Update level: full
   Found 2 directory(ies) to check

→ Updating src/codeindex/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

✓ Post-commit hook completed
```

---

## 📖 Documentation

Comprehensive integration guide available:
- **docs/guides/git-hooks-integration.md**
  - Quick start
  - Commands reference
  - Hook descriptions
  - Backup and safety
  - Troubleshooting
  - FAQ

---

## 🧪 Testing

- **19 new tests** for Git Hooks management
- **394 total tests** - All passing
- **Test coverage**:
  - HookManager class (10 tests)
  - Hook script generation (3 tests)
  - Backup and restore (2 tests)
  - Hook detection (2 tests)
  - CLI integration (2 tests)

---

## 🐛 Bug Fixes

Fixed code style issues in existing modules:
- **hierarchical.py**: Fixed line length violations, unused variables, bare except
- **symbol_index.py**: Fixed line length violation

---

## 📈 Impact

**Before Git Hooks:**
- ❌ Manual lint checks before commit
- ❌ Debug code slips into commits
- ❌ README_AI.md becomes outdated
- ❌ Inconsistent code quality

**After Git Hooks:**
- ✅ Automatic lint checks (catch errors early)
- ✅ Debug code blocked (cleaner commits)
- ✅ README_AI.md always up-to-date
- ✅ Consistent code quality across team

---

## 🚀 Upgrade Guide

### New Users

```bash
# Install codeindex
pip install codeindex==0.5.0-beta1

# Install Git hooks
codeindex hooks install --all
```

### Existing Users

```bash
# Upgrade
pip install --upgrade codeindex==0.5.0-beta1

# Install Git hooks (optional but recommended)
codeindex hooks install --all
```

**Note**: Git hooks are **optional**. All existing functionality works without them.

---

## ⚠️ Breaking Changes

**None** - This is a purely additive release.

All existing commands and workflows remain unchanged.

---

## 🔮 What's Next

**v0.6.0 (Planned)**:
- Hook configuration via `.codeindex.yaml`
- Additional hooks (pre-push validation)
- Custom hook scripts
- Hook templates

---

## 📝 Files Changed

**New Files:**
- `src/codeindex/cli_hooks.py` (516 lines) - Git Hooks management
- `tests/test_cli_hooks.py` (272 lines) - Tests
- `docs/guides/git-hooks-integration.md` (526 lines) - Documentation

**Modified Files:**
- `src/codeindex/cli.py` - Added hooks command registration
- `src/codeindex/hierarchical.py` - Code style fixes
- `src/codeindex/symbol_index.py` - Code style fix
- `CHANGELOG.md` - Added v0.5.0-beta1 entry
- `pyproject.toml` - Version bump to 0.5.0-beta1

---

## 🙏 Credits

**Developed by**: Claude Sonnet 4.5
**Epic**: Epic 6, P3.1 - Git Hooks Integration
**Development Time**: Day 6 of Week 2 Sprint
**Tests**: 19 new tests, 394 total (100% pass rate)

---

## 📄 License

MIT License - See LICENSE file for details

---

**Generated**: 2026-02-02
**Status**: ✅ Beta Release - Ready for Testing
