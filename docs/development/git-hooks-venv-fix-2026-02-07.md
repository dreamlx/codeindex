# Git Hooks Virtual Environment Fix

**Date**: 2026-02-07
**Issue**: User reported seeing ruff errors despite hooks supposedly running
**Root Cause**: pre-push hook was not activating virtual environment

---

## 🐛 Problem Discovered

### Symptoms
- User sees ruff errors when manually running commands
- Suggests hooks might not be working correctly

### Investigation
Checked all 3 Git hooks:

| Hook | Venv Activation | Shebang | Status |
|------|----------------|---------|--------|
| **pre-commit** | ✅ Lines 15-20 | `#!/bin/zsh` | ✅ OK |
| **post-commit** | ✅ Lines 26-30 | `#!/bin/zsh` | ✅ OK |
| **pre-push** | ❌ Missing! | `#!/bin/bash` | 🐛 **BROKEN** |

### Root Cause
**pre-push hook had critical flaws**:
1. ❌ No virtual environment activation
2. ❌ Directly used `command -v ruff` (system ruff, not venv)
3. ❌ Would skip checks if ruff not installed globally
4. ❌ Used bash instead of zsh (inconsistent)

---

## ✅ Solution Applied

### Changes to `.git/hooks/pre-push`

**Added virtual environment activation** (lines 17-28):
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)

if [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
elif [ -f "$REPO_ROOT/venv/bin/activate" ]; then
    source "$REPO_ROOT/venv/bin/activate"
else
    echo -e "${RED}✗ Virtual environment not found${RESET}"
    echo -e "${YELLOW}→ Create with: python3 -m venv .venv${RESET}"
    echo -e "${YELLOW}→ Install deps: pip install -e '.[dev,all]'${RESET}"
    exit 1
fi
```

**Prefer venv ruff over system** (lines 51-59):
```bash
RUFF_CMD=""
if [ -f "$REPO_ROOT/.venv/bin/ruff" ]; then
    RUFF_CMD="$REPO_ROOT/.venv/bin/ruff"
elif command -v ruff &> /dev/null; then
    RUFF_CMD="ruff"
else
    echo -e "${RED}✗ ruff not found${RESET}"
    echo -e "${YELLOW}→ Install with: pip install ruff${RESET}"
    exit 1
fi
```

**Other improvements**:
- Changed shebang to `#!/bin/zsh` for consistency
- Added `set -e` for fail-fast behavior
- Clear error messages if venv/tools not found

---

## 🧪 Verification

### Test 1: Virtual Environment Activation
```bash
$ source .venv/bin/activate
✅ Virtual environment activated

🔍 Checking tools availability:
   ruff: /path/to/.venv/bin/ruff
   pytest: /path/to/.venv/bin/pytest
   codeindex: /path/to/.venv/bin/codeindex

📦 Versions:
ruff 0.14.14
pytest 9.0.2
codeindex, version 0.12.0
```

### Test 2: All Hooks Consistency
```bash
$ grep -l "\.venv/bin/activate" .git/hooks/*
.git/hooks/pre-commit   ✅
.git/hooks/post-commit  ✅
.git/hooks/pre-push     ✅
```

---

## 📋 Best Practices Enforced

### For Developers

**Always use virtual environment**:
```bash
# Start development
cd /path/to/codeindex
source .venv/bin/activate

# Then use tools normally
ruff check src/
pytest
```

**Git hooks handle this automatically**:
- All 3 hooks now activate `.venv` automatically
- No need to manually activate before `git commit` or `git push`
- Fail-fast if venv not found (clear error message)

### For Hook Maintenance

**Required elements for each hook**:
1. ✅ Shebang: `#!/bin/zsh` (consistent)
2. ✅ Venv activation: Lines 15-30 (standardized)
3. ✅ Tool discovery: Prefer `.venv/bin/tool` over system
4. ✅ Error handling: Clear messages if tools missing
5. ✅ `set -e`: Fail-fast on errors

---

## 🔗 Related Issues

- **Line length**: Increased from 100 to 120 (commit f7aa978)
- **ruff installation**: Should use venv, not system (PEP 668)
- **User workflow**: `source .venv/bin/activate` before development

---

## 📌 Action Items

- [x] Fix pre-push hook venv activation
- [x] Test all 3 hooks consistency
- [x] Document the fix
- [ ] Consider adding hook tests to CI
- [ ] Update docs/guides/git-hooks-integration.md if needed

---

**Fixed by**: Claude Sonnet 4.5
**Commit**: (pending - `.git/hooks` not in version control)
**Documentation**: This file
