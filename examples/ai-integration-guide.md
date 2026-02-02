# AI Integration Guide: codeindex Git Hooks

**For**: AI Code CLI tools (Claude Code, Cursor, Roo Coder, Aider, etc.)
**Purpose**: Understand codeindex Git Hooks and update user project documentation
**Version**: v0.5.0-beta1

---

## 📋 Overview

**codeindex** is a code indexing tool that generates AI-friendly documentation. It provides **Git Hooks management** for automating:
- Pre-commit: Code quality checks (lint + debug code detection)
- Post-commit: Automatic README_AI.md updates

**Your task**: Update the user's project CLAUDE.md or AGENTS.md so future AI sessions understand how Git Hooks work.

---

## 🎯 What You Need to Do

### Step 1: Read User's Project Documentation

Read the user's project documentation file (in priority order):
1. `CLAUDE.md` (Claude Code convention)
2. `AGENTS.md` (alternative naming)
3. If neither exists, create `CLAUDE.md`

### Step 2: Add Git Hooks Section

Add the following section to the user's documentation file. Insert it in an appropriate location (e.g., after "Development Workflow" or near the beginning).

**Section to add**:

````markdown
## 🪝 Git Hooks (codeindex)

This project uses **codeindex Git Hooks** for automated code quality and documentation.

### Available Commands

```bash
# Check hook status
codeindex hooks status

# Install all hooks
codeindex hooks install --all

# Uninstall all hooks
codeindex hooks uninstall --all
```

### Installed Hooks

#### Pre-commit Hook

Runs **before every commit** to ensure code quality:

**L1: Lint Check**
- Runs `ruff check` on staged Python files only
- Auto-detects ruff from `.venv/bin/ruff` or system `ruff`
- Blocks commit if lint errors found

**L2: Debug Code Detection**
- Blocks `print()`, `breakpoint()`, `pdb.set_trace()` in non-CLI files
- Prevents accidental debug code from entering codebase
- Shows line numbers for violations

**If pre-commit fails**:
```bash
# Option 1: Fix the errors (recommended)
ruff check --fix src/
# Then retry commit

# Option 2: Bypass (emergency only)
git commit --no-verify -m "urgent fix"
```

#### Post-commit Hook

Runs **after every commit** to keep documentation updated:

1. Analyzes commit changes automatically
2. Updates `README_AI.md` for affected directories
3. Creates follow-up commit: `docs: auto-update README_AI.md for <hash>`
4. Prevents infinite loops (skips if only doc files changed)

**Expected behavior**:
```bash
# You commit
git commit -m "feat: add new feature"
# Pre-commit checks...
# ✓ All checks passed!

# Post-commit runs automatically
# 📝 Post-commit: Analyzing changes...
# → Updating src/README_AI.md
# ✓ Auto-commit created
```

**This is normal!** The auto-commit is expected behavior.

### For AI Code: Important Behaviors

**When committing code**:
1. **Hooks run automatically** - No action needed
2. **If lint errors**: Fix errors before retrying commit
3. **Post-commit auto-commits**: Expected, don't be alarmed
4. **Bypass hooks**: Only use `--no-verify` in emergencies

**Typical commit flow**:
```bash
git add src/myfile.py
git commit -m "feat: add feature"
# → Pre-commit runs (lint + debug check)
# → If passed: commit succeeds
# → Post-commit runs (doc update)
# → May create auto-commit
```

**Handling failures**:
```bash
# If pre-commit fails with lint errors:
1. Read error output
2. Fix issues: ruff check --fix src/
3. Re-stage: git add src/
4. Retry commit

# If stuck, check hook status:
codeindex hooks status
```

### Troubleshooting

**Hooks not running?**
```bash
# Check if installed
codeindex hooks status

# Reinstall
codeindex hooks install --all --force
```

**Hook fails with error?**
```bash
# Debug
.git/hooks/pre-commit

# View hook content
cat .git/hooks/pre-commit

# Reinstall
codeindex hooks install pre-commit --force
```

**Need to bypass temporarily?**
```bash
# Emergency only (skip all hooks)
git commit --no-verify -m "message"
```

### Documentation

- Full user guide: `docs/guides/git-hooks-integration.md` (in codeindex repo)
- For development: `docs/development/git-hooks-architecture.md` (in codeindex repo)

---
````

### Step 3: Save and Verify

After adding the section:

1. Save the updated file
2. Inform the user:
   ```
   ✅ Updated [CLAUDE.md/AGENTS.md] with Git Hooks documentation

   Future AI sessions in this project will now understand:
   - Git Hooks are installed
   - How pre-commit and post-commit work
   - Expected behaviors and troubleshooting
   ```

---

## 🧠 Understanding codeindex Git Hooks

### What is codeindex?

**codeindex** is a CLI tool that:
- Scans code directories
- Extracts symbols (classes, functions, imports)
- Generates AI-friendly `README_AI.md` files
- Provides Git Hooks for automation

### Git Hooks Architecture

```
codeindex Git Hooks
├── pre-commit
│   ├── L1: Lint Check (ruff)
│   └── L2: Debug Code Detection
├── post-commit
│   └── Auto-update README_AI.md
└── Management
    ├── install/uninstall commands
    ├── Automatic backups
    └── Status checking
```

### Hook Installation

Hooks are installed to `.git/hooks/`:
- `.git/hooks/pre-commit` - Runs before commit
- `.git/hooks/post-commit` - Runs after commit
- Marker: `# codeindex-managed hook` (identifies codeindex hooks)

### Pre-commit: Quality Gate

**Runs**: Before `git commit` completes
**Checks**:
1. Staged Python files only (not working directory)
2. Lint with `ruff check`
3. Detect debug code patterns

**Exit codes**:
- `0` - Pass, commit proceeds
- `1` - Fail, commit blocked

### Post-commit: Auto Documentation

**Runs**: After commit succeeds
**Process**:
1. Analyze commit: `codeindex affected --json`
2. Get affected directories
3. Update README_AI.md for each
4. Create follow-up commit

**Loop Prevention**:
- Checks if commit only touched doc files
- Skips if only `README_AI.md` or `PROJECT_INDEX.md` changed

---

## 💡 Common Scenarios

### Scenario 1: Normal Development

```bash
# Developer writes code
vim src/mymodule.py

# Developer commits
git commit -m "feat: add feature"

# Pre-commit runs
# ✓ Lint passed
# ✓ No debug code

# Post-commit runs
# → Updates src/README_AI.md
# → Creates auto-commit

# Result: 2 commits (original + auto-doc)
```

### Scenario 2: Lint Errors

```bash
git commit -m "feat: add feature"

# Pre-commit runs
# ✗ Lint errors found:
#   src/mymodule.py:10:1: E501 line too long

# Commit BLOCKED

# Fix errors
ruff check --fix src/
git add src/

# Retry
git commit -m "feat: add feature"
# ✓ Success
```

### Scenario 3: Debug Code Detected

```bash
git commit -m "feat: add feature"

# Pre-commit runs
# ✗ Debug code found:
#   src/mymodule.py:
#      42: print(result)

# Commit BLOCKED

# Remove print statement
vim src/mymodule.py
git add src/

# Retry
git commit -m "feat: add feature"
# ✓ Success
```

### Scenario 4: Doc-Only Commit

```bash
# Only update docs
vim docs/guide.md
git commit -m "docs: update guide"

# Pre-commit runs (no Python files, skipped)
# Post-commit runs
# ✓ Changes below threshold, skipping update

# Result: 1 commit (no auto-doc needed)
```

---

## 🔧 Integration Checklist

After reading this guide, you should:

- [ ] Understand what codeindex Git Hooks do
- [ ] Know how pre-commit and post-commit work
- [ ] Understand expected behaviors (auto-commits are normal)
- [ ] Know how to handle hook failures
- [ ] Have updated user's CLAUDE.md/AGENTS.md with the section above

---

## 📚 Additional Resources

**In codeindex repository**:
- `docs/guides/git-hooks-integration.md` - Complete user guide (526 lines)
- `docs/development/git-hooks-architecture.md` - Developer deep dive
- `RELEASE_NOTES_v0.5.0-beta1.md` - Feature overview

**Online**:
- Installation: `pip install codeindex`
- CLI help: `codeindex hooks --help`

---

## ✅ Completion

Once you've added the Git Hooks section to the user's documentation:

1. **Inform the user**:
   ```
   ✅ Added Git Hooks documentation to CLAUDE.md

   Future AI sessions will now understand how codeindex Git Hooks work.
   You can review the changes in CLAUDE.md.
   ```

2. **Future sessions**: Any AI Code reading CLAUDE.md will now know:
   - Git Hooks are active
   - How they behave
   - How to handle errors
   - When auto-commits are expected

---

**Generated**: 2026-02-02
**Version**: v0.5.0-beta1
**Purpose**: Enable AI Code to understand and document codeindex Git Hooks usage
