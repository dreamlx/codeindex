# Release v0.7.0 Status

**Release Date**: 2026-02-04
**Status**: ✅ GitHub Released | ⏳ PyPI Pending

---

## ✅ Completed Steps

### 1. ✅ Branch Merge
```bash
✓ Merged feature/epic-json-output → master
✓ 20 commits merged successfully
```

### 2. ✅ Tests & Quality Checks
```bash
✓ 455 tests passed, 3 skipped
✓ All lint checks passed (ruff)
✓ No uncommitted changes
```

### 3. ✅ Version Bump
```bash
✓ Version: 0.6.0 → 0.7.0
✓ pyproject.toml updated
✓ src/codeindex/__init__.py updated
✓ CHANGELOG.md updated
```

### 4. ✅ Git Tag Created
```bash
✓ Tag: v0.7.0
✓ Commit: 8f0b7a5
```

### 5. ✅ Distribution Built
```bash
✓ ai_codeindex-0.7.0-py3-none-any.whl
✓ ai_codeindex-0.7.0.tar.gz
✓ twine check: PASSED
```

### 6. ✅ GitHub Push
```bash
✓ Pushed to: https://github.com/dreamlx/codeindex.git
✓ Branch: master (98df0a9 → 8f0b7a5)
✓ Tag: v0.7.0 pushed
```

---

## ⏳ Pending: PyPI Upload

### Status
PyPI credentials not configured yet. You have 3 options:

---

## 📦 Option 1: Manual PyPI Upload (Fastest)

### Step 1: Get PyPI API Token

1. Visit https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: `codeindex-release`
4. Scope: **Entire account** (or project: ai-codeindex if exists)
5. Copy the token (starts with `pypi-...`)

### Step 2: Configure ~/.pypirc

```bash
cat > ~/.pypirc <<'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
EOF

chmod 600 ~/.pypirc
```

### Step 3: Upload to PyPI

```bash
# Activate venv
source .venv/bin/activate

# Upload to PyPI (production)
twine upload dist/ai_codeindex-0.7.0*

# Or test on TestPyPI first (recommended)
twine upload --repository testpypi dist/ai_codeindex-0.7.0*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            ai-codeindex==0.7.0

# Verify version
codeindex --version
```

### Step 4: Upload to Production PyPI

```bash
twine upload dist/ai_codeindex-0.7.0*
```

**Time**: ~5 minutes

---

## 🤖 Option 2: GitHub Actions Auto-Publish (Recommended for Future)

### Why This Option?
- ✅ Automated release workflow
- ✅ No manual PyPI token management
- ✅ Integrated testing before publish
- ✅ Automatic GitHub Release creation

### Setup Steps

#### 1. Get PyPI API Token
Same as Option 1, Step 1

#### 2. Configure GitHub Secrets
```bash
# Visit: https://github.com/dreamlx/codeindex/settings/secrets/actions
# Add these secrets:
PYPI_API_TOKEN         = pypi-YOUR_TOKEN_HERE
TEST_PYPI_API_TOKEN    = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

#### 3. Workflow Already Exists!
The workflow is already in your repo:
```
.github/workflows/publish.yml
```

It will automatically:
1. Run tests on Python 3.10, 3.11, 3.12
2. Build distributions
3. Upload to TestPyPI
4. Upload to PyPI
5. Create GitHub Release

#### 4. Trigger Workflow
The workflow triggers on tag push, so **it's already running!**

Check status:
```
https://github.com/dreamlx/codeindex/actions
```

Look for workflow: **"Publish to PyPI"**

If it failed (likely due to missing secrets), you can:
1. Add secrets (Step 2)
2. Delete and recreate the tag:
   ```bash
   git tag -d v0.7.0
   git push origin :refs/tags/v0.7.0
   git tag v0.7.0 -m "Release v0.7.0"
   git push origin master --tags
   ```

**Time**: ~10 minutes (initial setup) + 5 min (workflow run)

---

## 🚫 Option 3: Skip PyPI for Now

If you want to test locally first:

```bash
# Install from local wheel
pip install dist/ai_codeindex-0.7.0-py3-none-any.whl

# Or install in development mode
pip install -e .

# Verify
codeindex --version
```

You can publish to PyPI later using Option 1 or 2.

---

## 📊 Release Summary

### What's New in v0.7.0

#### 🎯 JSON Output Mode
```bash
# Generate machine-readable output
codeindex scan ./src --output json
codeindex scan-all --output json > parse_results.json

# Structured error handling
# Exit code 1 for command errors, 0 for partial success
```

#### ⚙️ Git Hooks Configuration
```yaml
# .codeindex.yaml
hooks:
  post_commit:
    mode: auto  # or: async, sync, disabled, prompt
    enabled: true
    max_dirs_sync: 2
    log_file: ~/.codeindex/hooks/post-commit.log
```

**Performance**: 3 directories: 90s → <1s (async mode)

#### 📦 PyPI Package Rename
- **PyPI Package**: `ai-codeindex` (避免名称冲突)
- **GitHub Repo**: `codeindex` (保持简洁)
- **CLI Command**: `codeindex` (用户体验优先)
- **Python Import**: `import codeindex` (代码一致性)

#### 🚀 PyPI Release Infrastructure
- GitHub Actions workflow
- Automated release scripts
- Complete documentation

---

## 🔗 Links

### GitHub
- **Repository**: https://github.com/dreamlx/codeindex
- **Release**: https://github.com/dreamlx/codeindex/releases/tag/v0.7.0
- **Actions**: https://github.com/dreamlx/codeindex/actions

### PyPI (After Upload)
- **Package**: https://pypi.org/project/ai-codeindex/
- **v0.7.0**: https://pypi.org/project/ai-codeindex/0.7.0/

### TestPyPI (For Testing)
- **Package**: https://test.pypi.org/project/ai-codeindex/

---

## 🎉 Next Steps

### Immediate (Choose One)
1. **Option 1**: Configure PyPI token and upload manually (~5 min)
2. **Option 2**: Configure GitHub Actions secrets (~10 min setup)
3. **Option 3**: Skip PyPI, test locally first

### After PyPI Upload
1. ✅ Create GitHub Release with changelog
   - Visit: https://github.com/dreamlx/codeindex/releases/new
   - Tag: v0.7.0
   - Title: "Release v0.7.0: JSON Output + Hooks Config"
   - Description: Copy from CHANGELOG.md

2. ✅ Test installation
   ```bash
   pip install ai-codeindex==0.7.0
   codeindex --version
   codeindex scan --help
   ```

3. ✅ Announce release
   - Update project README if needed
   - Notify users (if any)
   - Social media (optional)

4. ✅ Clean up
   ```bash
   # Delete feature branch (already merged)
   git branch -d feature/epic-json-output
   ```

---

## 📝 Commands Reference

### Check Release Status
```bash
# Current version
codeindex --version

# Git status
git log --oneline -5
git tag -l "v0.7*"

# Check built packages
ls -lh dist/

# Check package contents
tar -tzf dist/ai_codeindex-0.7.0.tar.gz | head -20
```

### Rollback (If Needed)
```bash
# Delete tag locally and remotely
git tag -d v0.7.0
git push origin :refs/tags/v0.7.0

# Revert version commit
git revert 8f0b7a5

# Or reset to previous version
git reset --hard 98df0a9
git push origin master --force  # ⚠️ Use with caution
```

---

## 🐛 Troubleshooting

### PyPI Upload Fails (403 Forbidden)
```bash
# Check token in ~/.pypirc
cat ~/.pypirc

# Verify token format (should start with pypi-)
# Verify token has correct scope
```

### Version Already Exists on PyPI
```bash
# PyPI doesn't allow overwriting
# Need to increment version
./scripts/bump_version.sh 0.7.1
# ... repeat release process
```

### GitHub Actions Workflow Fails
```bash
# Check workflow logs
# Visit: https://github.com/dreamlx/codeindex/actions

# Common issues:
# - Missing PYPI_API_TOKEN secret
# - Network timeout
# - Test failures
```

---

**Generated**: 2026-02-04
**Author**: Claude Code
**Status**: ✅ Ready for PyPI Upload
