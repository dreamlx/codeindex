# Git Hooks

This directory contains Git hook templates for codeindex.

## 📁 Structure

```
hooks/
├── README.md                         # This file
└── templates/                        # Hook templates
    ├── post-commit-v4                # Main hook with async support
    └── post-commit-update-logic.sh   # Shared update logic
```

## 🚀 Installation

### Automatic (Recommended)

Use the CLI command (coming in Story 6 full implementation):
```bash
codeindex hooks install --all
```

### Manual

```bash
# From project root
cp hooks/templates/post-commit-v4 .git/hooks/post-commit
cp hooks/templates/post-commit-update-logic.sh .git/hooks/
chmod +x .git/hooks/post-commit
chmod +x .git/hooks/post-commit-update-logic.sh
```

## ✨ Features

### v4: Async Mode (2026-02-04)

**Smart Detection**:
- ≤2 directories: Sync mode (fast, blocks ~60s)
- \>2 directories: Async mode (instant return, runs in background)

**Benefits**:
- **Non-blocking**: Continue working immediately after commit
- **Automatic**: No configuration needed
- **Safe**: Lock files prevent concurrent runs

### Usage

**No changes needed!** Just commit as usual:

```bash
git add .
git commit -m "feat: add new feature"
# ← Hook runs here

# For ≤2 dirs: Waits ~60s
# For >2 dirs: Returns immediately, updates in background
```

**Check background progress**:
```bash
# Real-time log
tail -f ~/.codeindex/hooks/post-commit.log

# Check if still running
ls ~/.codeindex/hooks/post-commit.lock
```

## 📖 Documentation

See detailed docs:
- [Async Mode Guide](../docs/development/git-hooks-async-mode.md)
- [Architecture (Story 6)](../docs/planning/active/epic-json-output.md#story-6-git-hooks-性能优化)

## 🔧 Hooks Explained

### post-commit

**Purpose**: Auto-update `README_AI.md` files after code changes

**Workflow**:
1. Analyze commit with `codeindex affected`
2. Detect number of affected directories
3. Choose mode (sync ≤2, async >2)
4. Update README files (sync or background)
5. Create auto-commit with updated docs

**Outputs**:
- Sync: Updates immediately, blocks user
- Async: Returns instantly, updates in background

### post-commit-update-logic.sh

**Purpose**: Shared update logic for both sync and async modes

**Contains**:
- Directory scanning
- AI CLI invocation
- README generation
- Git commit creation

## 🚨 Troubleshooting

### Hook not running

```bash
# Check if installed
ls -la .git/hooks/post-commit

# Check if executable
chmod +x .git/hooks/post-commit
```

### Background update stuck

```bash
# Check log
tail -50 ~/.codeindex/hooks/post-commit.log

# Check if running
ls ~/.codeindex/hooks/post-commit.lock

# Manual cleanup (if process died)
rm ~/.codeindex/hooks/post-commit.lock
rm ~/.codeindex/hooks/post-commit.pid
```

### Disable hooks temporarily

```bash
# Skip hook for one commit
git commit --no-verify -m "message"

# Disable permanently
rm .git/hooks/post-commit
```

## 🔮 Future Enhancements

Coming in Story 6 full implementation:

- [ ] Config file support (`.codeindex.yaml`)
- [ ] Manual mode selection (async/sync/prompt/disabled)
- [ ] Parallel directory processing
- [ ] Progress bars
- [ ] Log rotation

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| v4 | 2026-02-04 | Async mode, smart detection |
| v3 | 2026-01-19 | Intelligent `affected` analysis |
| v2 | 2026-01-15 | Basic post-commit hook |

---

**Current Version**: v4
**Status**: ✅ Production ready
**Story**: Epic JSON Output, Story 6 (partial)
