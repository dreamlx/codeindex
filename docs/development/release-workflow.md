# Release Workflow

**Guide for releasing new versions of codeindex**

---

## 🎯 Quick Start

```bash
# Complete release workflow (automated)
make release VERSION=0.13.0
```

That's it! The rest is automated via GitHub Actions.

---

## 📋 Release Checklist

### Pre-Release (Manual)

- [ ] 1. **Complete Epic/Stories**
  - All tests passing (100%)
  - Zero regressions
  - Documentation complete

- [ ] 2. **Prepare Documentation**
  - Update `ROADMAP.md`
    - Move epic from "Active" to "Completed"
    - Update current version
    - Add version history entry
  - Update `CHANGELOG.md`
    - Add new version section
    - Document all changes
  - Create `RELEASE_NOTES_vX.X.X.md`
    - Feature highlights
    - Technical details
    - Migration guide (if needed)

- [ ] 3. **Commit Documentation**
  ```bash
  git add docs/planning/ROADMAP.md CHANGELOG.md RELEASE_NOTES_v0.13.0.md
  git commit -m "docs: prepare v0.13.0 release documentation"
  ```

- [ ] 4. **Merge to Master**
  ```bash
  git checkout master
  git merge develop --no-ff -m "Merge develop to master for v0.13.0 release"
  ```

### Release (Automated)

- [ ] 5. **Run Release Command**
  ```bash
  make release VERSION=0.13.0
  ```

  This command will:
  - ✅ Run pre-release checks (tests, lint, version files)
  - ✅ Update version in `pyproject.toml`
  - ✅ Commit version bump
  - ✅ Create Git tag `v0.13.0`
  - ✅ Push to `origin/master`
  - ✅ Push tag to `origin/v0.13.0`

### Post-Release (Automated via GitHub Actions)

- [ ] 6. **GitHub Actions Workflow** (triggered by tag push)
  - ✅ Run tests on Python 3.10, 3.11, 3.12
  - ✅ Build distribution packages (wheel + sdist)
  - ✅ Check distribution with twine
  - ✅ Publish to PyPI (via Trusted Publisher)
  - ✅ Create GitHub Release with:
    - Release notes from `RELEASE_NOTES_vX.X.X.md`
    - Distribution files attached
    - Automatic changelog extraction

- [ ] 7. **Verify Release**
  - Check PyPI: https://pypi.org/project/ai-codeindex/
  - Check GitHub Release: https://github.com/yourusername/codeindex/releases
  - Test installation: `pip install --upgrade ai-codeindex==0.13.0`

---

## 🔧 Makefile Commands

### Development

```bash
make help                  # Show all available commands
make install              # Install package (editable mode)
make install-dev          # Install with dev dependencies
make install-hooks        # Install Git hooks (pre-push)
make test                 # Run all tests
make test-fast            # Run tests without coverage (quick)
make test-cov             # Run tests with coverage report
make lint                 # Run linter (ruff)
make lint-fix             # Auto-fix lint issues
make clean                # Clean build artifacts
```

### Release

```bash
make release VERSION=0.13.0        # Full release workflow (recommended)
make bump-version VERSION=0.13.0   # Update version only (manual workflow)
make check-version                 # Verify version consistency
make build                         # Build distribution packages
make check-dist                    # Build and check with twine
make status                        # Show git and version status
```

### CI Helpers

```bash
make ci-install           # Install dependencies for CI
make ci-test              # Run tests in CI mode
make ci-build             # Build and check for CI
```

---

## 🔄 Release Workflow Details

### Option 1: Automated (Recommended)

**Single command release**:

```bash
# On master branch, with clean working directory
make release VERSION=0.13.0
```

**What happens**:
1. Pre-release checks:
   - Working directory is clean
   - On master branch
   - All tests pass
   - No lint errors
   - `RELEASE_NOTES_v0.13.0.md` exists

2. Version bump:
   - Updates `pyproject.toml`
   - Commits: "chore: bump version to 0.13.0"

3. Git operations:
   - Creates tag: `v0.13.0`
   - Pushes to origin: `master` + `v0.13.0`

4. GitHub Actions (triggered by tag):
   - Runs CI tests
   - Builds packages
   - Publishes to PyPI
   - Creates GitHub Release

### Option 2: Manual (Fine-grained control)

**Step-by-step release**:

```bash
# 1. Pre-release checks
make test
make lint
make check-version

# 2. Update version
make bump-version VERSION=0.13.0
git add pyproject.toml
git commit -m "chore: bump version to 0.13.0"

# 3. Create tag
git tag -a v0.13.0 -m "Release v0.13.0"

# 4. Push
git push origin master
git push origin v0.13.0

# GitHub Actions will handle the rest
```

---

## 🔐 PyPI Configuration

### Trusted Publisher (OIDC)

codeindex uses PyPI's **Trusted Publisher** feature (no password needed).

**Setup** (one-time):
1. Go to https://pypi.org/manage/account/publishing/
2. Add new publisher:
   - PyPI Project Name: `ai-codeindex`
   - Owner: `yourusername`
   - Repository: `codeindex`
   - Workflow: `publish.yml`
   - Environment: (leave blank)

3. GitHub Actions will automatically publish when tag is pushed

**Security**:
- No API tokens stored
- OIDC provides short-lived credentials
- Only works from GitHub Actions on tagged commits

---

## 🪝 Git Hooks

### Pre-Push Hook

Automatically installed via:
```bash
make install-hooks
```

**What it does**:
- Runs linter (`ruff check`)
- Runs tests (`pytest`)
- Checks version consistency (master branch only)
- Prevents push if checks fail

**Skip hook** (emergency only):
```bash
git push --no-verify
```

---

## 📊 Version Management

### Version Number Format

Follow **Semantic Versioning** (https://semver.org):
- `MAJOR.MINOR.PATCH` (e.g., `0.13.0`)
- Increment:
  - `MAJOR`: Breaking changes (e.g., 1.0.0)
  - `MINOR`: New features (backward compatible)
  - `PATCH`: Bug fixes (backward compatible)

### Version Sources

| Source | Purpose |
|--------|---------|
| `pyproject.toml` | Package metadata (pip install) |
| Git tags (`v*.*.*`) | Release tracking, CI/CD trigger |
| `RELEASE_NOTES_vX.X.X.md` | Human-readable changelog |

**Single Source of Truth**: Git tags drive automation, `pyproject.toml` is updated automatically.

---

## 🚨 Troubleshooting

### "Tag already exists"

```bash
# Delete local tag
git tag -d v0.13.0

# Delete remote tag (careful!)
git push origin --delete v0.13.0

# Recreate tag
git tag -a v0.13.0 -m "Release v0.13.0"
git push origin v0.13.0
```

### "Tests failing on CI but pass locally"

- Check Python version (CI tests 3.10, 3.11, 3.12)
- Check OS differences (macOS vs Ubuntu)
- Clear cache: delete `.pytest_cache`, `__pycache__`

### "PyPI publish failed"

1. Check Trusted Publisher setup on PyPI
2. Verify GitHub Actions has correct permissions (`id-token: write`)
3. Check workflow logs: https://github.com/yourusername/codeindex/actions

### "Pre-push hook blocking"

```bash
# Fix lint errors
make lint-fix

# Run tests
make test

# Or skip hook (emergency only)
git push --no-verify
```

---

## 📝 Example: Complete Release

**Scenario**: Releasing v0.13.0 after completing Epic 12

```bash
# 1. Ensure on develop branch, all changes committed
git checkout develop
git status  # Should be clean

# 2. Prepare documentation
vim docs/planning/ROADMAP.md        # Update to v0.13.0
vim CHANGELOG.md                    # Add v0.13.0 section
vim RELEASE_NOTES_v0.13.0.md        # Create release notes

# 3. Commit documentation
git add docs/ CHANGELOG.md RELEASE_NOTES_v0.13.0.md
git commit -m "docs: prepare v0.13.0 release documentation"
git push origin develop

# 4. Merge to master
git checkout master
git merge develop --no-ff -m "Merge develop to master for v0.13.0 release"

# 5. Run automated release
make release VERSION=0.13.0

# 6. Monitor GitHub Actions
# Visit: https://github.com/yourusername/codeindex/actions

# 7. Verify release (after ~5 minutes)
# - PyPI: https://pypi.org/project/ai-codeindex/0.13.0/
# - GitHub: https://github.com/yourusername/codeindex/releases/tag/v0.13.0

# 8. Test installation
pip install --upgrade ai-codeindex==0.13.0
codeindex --version  # Should show v0.13.0

# Done! 🎉
```

---

## 🔗 Related Documentation

- [GitHub Actions Workflows](../../.github/workflows/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Last Updated**: 2026-02-07
**Workflow Version**: v1.0 (Automated release)
