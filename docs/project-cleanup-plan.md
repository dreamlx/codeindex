# Project Root Directory Cleanup Plan

**Created**: 2026-02-07
**Status**: 📋 Proposed
**Goal**: Improve open source project governance and professionalism

---

## 🎯 Cleanup Strategy

**Principle**: Non-breaking, backward-compatible cleanup with Git history preservation

---

## Phase 1: Immediate Cleanup (Critical) 🔴

### 1.1 Remove Build Artifacts & Cache

```bash
# Already in .gitignore, remove from git tracking
git rm -r --cached htmlcov/
git rm -r --cached .pytest_cache/
git rm -r --cached .ruff_cache/
git rm --cached .coverage
git rm --cached .DS_Store

# Commit
git commit -m "chore: remove build artifacts and cache from git tracking

- htmlcov/ (test coverage reports)
- .pytest_cache/ (pytest cache)
- .ruff_cache/ (ruff linter cache)
- .coverage (coverage data)
- .DS_Store (macOS temp file)

These are already in .gitignore but were tracked before.
"
```

### 1.2 Remove Duplicate Virtual Environment

```bash
# Keep .venv/, remove venv/ (59MB)
git rm -r venv/

git commit -m "chore: remove duplicate virtual environment

- Keep .venv/ (standard convention)
- Remove venv/ (59MB redundant)
"
```

### 1.3 Move Test Files to tests/

```bash
# Move scattered test files
git mv test_adaptive_debug.py tests/legacy/
git mv test_current_project.py tests/legacy/
git mv test_hierarchical_src.py tests/legacy/
git mv test_hierarchical.py tests/legacy/
git mv test_hierarchy_simple.py tests/legacy/
git mv test_operategoods.py tests/legacy/
git mv test_hierarchical_test/ tests/legacy/

# Create README to explain legacy tests
cat > tests/legacy/README.md << 'EOF'
# Legacy Tests

**Status**: Historical tests from early development

These tests were moved from the root directory during the v0.12.0 cleanup.
They may be outdated or superseded by tests in the main `tests/` directory.

**Action**: Review and either:
1. Integrate useful tests into main test suite
2. Delete if obsolete
EOF

git add tests/legacy/
git commit -m "chore: move legacy test files to tests/legacy/

- test_adaptive_debug.py
- test_current_project.py
- test_hierarchical*.py
- test_operategoods.py
- test_hierarchical_test/

These files cluttered the root directory and should be reviewed
for integration or removal.
"
```

### 1.4 Clean Up Temporary Files

```bash
# Remove temporary documentation
git rm CLEANUP_AND_NEXT_STEPS.md
git rm CLAUDE_CODE_INTEGRATION_UPDATE.md

# Remove experimental code (or move to scripts/)
git mv hierarchical_strategy.py scripts/legacy/
git mv PROJECT_INDEX.json scripts/legacy/

git commit -m "chore: remove temporary files and move experimental code

Removed:
- CLEANUP_AND_NEXT_STEPS.md (temporary)
- CLAUDE_CODE_INTEGRATION_UPDATE.md (temporary)

Moved to scripts/legacy/:
- hierarchical_strategy.py
- PROJECT_INDEX.json
"
```

---

## Phase 2: Organize Documentation (High Priority) 🟡

### 2.1 Move Release Notes

```bash
# Create releases directory
mkdir -p docs/releases

# Move release notes
git mv RELEASE_NOTES_v*.md docs/releases/

# Update references in CHANGELOG.md if needed
# Update ROADMAP.md references

git commit -m "docs: move release notes to docs/releases/

- Organized 11 RELEASE_NOTES_*.md files
- Cleaner root directory
- Easier to find historical release information

All references in CHANGELOG.md and ROADMAP.md updated.
"
```

### 2.2 Move Developer Guides

```bash
# Move to docs/guides/
git mv GIT_COMMIT_GUIDE.md docs/guides/git-commit-guide.md
git mv PYPI_QUICKSTART.md docs/guides/pypi-quickstart.md
git mv PACKAGE_NAMING.md docs/guides/package-naming.md

# Update CLAUDE.md references if any

git commit -m "docs: move developer guides to docs/guides/

- git-commit-guide.md (formerly GIT_COMMIT_GUIDE.md)
- pypi-quickstart.md (formerly PYPI_QUICKSTART.md)
- package-naming.md (formerly PACKAGE_NAMING.md)

Updated references in CLAUDE.md.
"
```

### 2.3 Optional: Move PROJECT_SYMBOLS.md

```bash
# Consider moving to docs/ for cleaner root
git mv PROJECT_SYMBOLS.md docs/PROJECT_SYMBOLS.md

# Update references in README.md, CLAUDE.md

git commit -m "docs: move PROJECT_SYMBOLS.md to docs/

- Cleaner root directory
- Symbols index belongs with documentation

Updated references in README.md and CLAUDE.md.
"
```

---

## Phase 3: Add Standard Files (Medium Priority) 🟢

### 3.1 Create CONTRIBUTING.md

```bash
cat > CONTRIBUTING.md << 'EOF'
# Contributing to codeindex

Thank you for your interest in contributing to codeindex!

## Development Workflow

See [CLAUDE.md](CLAUDE.md) for detailed developer guide.

**Quick Start**:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Follow TDD: Write tests first, then implementation
4. Run tests: `pytest -v`
5. Run linter: `ruff check src/`
6. Commit with conventional commits: `feat(scope): description`
7. Create Pull Request

## Issue Workflow

See [docs/development/requirements-workflow.md](docs/development/requirements-workflow.md)

Use our issue templates:
- Epic: Major features (2+ weeks)
- Feature/Story: User stories
- Bug: Bug reports
- Enhancement: Improvements

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Run `ruff check` before committing

## Testing

- Write tests for all new features
- Maintain ≥90% coverage for core modules
- Use pytest fixtures for setup

## Questions?

- Read [CLAUDE.md](CLAUDE.md) - Developer guide
- Check [docs/guides/](docs/guides/) - Specific guides
- Open a discussion on GitHub

We're excited to see your contributions! 🎉
EOF

git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md

- Standard contributing guidelines for open source
- References CLAUDE.md for detailed workflow
- Explains issue templates and code style
"
```

### 3.2 Create CODE_OF_CONDUCT.md

```bash
# Use Contributor Covenant (industry standard)
cat > CODE_OF_CONDUCT.md << 'EOF'
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the project maintainers.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1.
EOF

git add CODE_OF_CONDUCT.md
git commit -m "docs: add Contributor Covenant Code of Conduct

- Standard code of conduct for open source projects
- Version 2.1 of Contributor Covenant
- Ensures inclusive and respectful community
"
```

### 3.3 Create SECURITY.md

```bash
cat > SECURITY.md << 'EOF'
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.12.x  | :white_check_mark: |
| 0.11.x  | :white_check_mark: |
| < 0.11  | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: [your-email@example.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive a response within 48 hours. We'll work with you to understand
and address the issue promptly.

## Security Best Practices

When using codeindex:
1. Never commit `.env` files with sensitive credentials
2. Review generated README_AI.md for accidentally exposed secrets
3. Use `--fallback` mode if AI CLI contains sensitive data
4. Keep dependencies updated: `pip install --upgrade ai-codeindex`

Thank you for helping keep codeindex secure!
EOF

git add SECURITY.md
git commit -m "docs: add SECURITY.md

- Define supported versions
- Provide vulnerability reporting process
- List security best practices for users
"
```

### 3.4 Add README.md to Key Directories

```bash
# examples/README.md
cat > examples/README.md << 'EOF'
# codeindex Examples

This directory contains example files and configurations for codeindex.

## Contents

- `.codeindex.yaml` - Example configuration file
- `loomgraph_*.py` - LoomGraph integration examples
- `loomgraph_*.json` - Sample JSON output
- `ai-integration-guide.md` - AI Code integration guide

## Usage

```bash
# Copy example config to your project
cp examples/.codeindex.yaml your-project/

# Customize as needed
vim your-project/.codeindex.yaml
```

See [README.md](../README.md) for full documentation.
EOF

# scripts/README.md
cat > scripts/README.md << 'EOF'
# codeindex Scripts

Utility scripts for development and maintenance.

## Contents

- `legacy/` - Experimental code from early development
- (Add other scripts here as they're created)

## Usage

Scripts are typically run from the project root:

```bash
python scripts/script_name.py
```

For development scripts, see [CLAUDE.md](../CLAUDE.md).
EOF

git add examples/README.md scripts/README.md
git commit -m "docs: add README.md to examples/ and scripts/

- Explain purpose of each directory
- Provide usage examples
- Improve project navigability
"
```

---

## Phase 4: Optional Enhancements 📋

### 4.1 Add .editorconfig

```bash
cat > .editorconfig << 'EOF'
# EditorConfig for codeindex
# https://editorconfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
EOF

git add .editorconfig
git commit -m "chore: add .editorconfig

- Consistent coding style across editors
- Python: 4 spaces, max 100 chars
- YAML: 2 spaces
"
```

### 4.2 Update .gitignore

```bash
# Add any missing patterns
cat >> .gitignore << 'EOF'

# codeindex specific
PROJECT_INDEX.json

# macOS
.DS_Store

# Coverage
.coverage
htmlcov/
.pytest_cache/

# Ruff
.ruff_cache/
EOF

git add .gitignore
git commit -m "chore: update .gitignore with missing patterns"
```

---

## Verification Checklist

After cleanup:

- [ ] Root directory has ≤15 files
- [ ] All tests in `tests/` directory
- [ ] Release notes in `docs/releases/`
- [ ] Developer guides in `docs/guides/`
- [ ] Standard files present:
  - [ ] CONTRIBUTING.md
  - [ ] CODE_OF_CONDUCT.md
  - [ ] SECURITY.md
- [ ] No build artifacts tracked in git
- [ ] Only one virtual environment (.venv/)
- [ ] All directories have README.md

---

## Expected Root Directory After Cleanup

```
codeindex/
├── .github/
├── docs/
├── examples/
├── scripts/
├── src/
├── tests/
├── .gitignore
├── .editorconfig
├── CHANGELOG.md
├── CLAUDE.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── PROJECT_SYMBOLS.md (or in docs/)
├── README.md
├── README_AI.md
├── SECURITY.md
└── uv.lock
```

**Total**: ~16 files (down from 36+)

---

## Rollback Plan

If any issues arise:

```bash
# Revert last commit
git revert HEAD

# Or reset to before cleanup
git reset --hard <commit-before-cleanup>
```

---

**Status**: 📋 Awaiting approval
**Estimated Time**: 1-2 hours
**Impact**: Low (no code changes, only organization)
**Risk**: Very low (git preserves history)
