# Team Development Workflow Guide

> How we build codeindex — requirements, decisions, TDD, QA gates, and Claude Code patterns.
> Read this before touching the codebase. Share with your team before your first PR.

---

## 1. Mental Model: Three Rings

```
[GitHub Issue]  →  [feature/* branch]  →  [master + PyPI tag]
     ↑                    ↑                    ↑
  Requirements         TDD + hooks          CI gates
```

Every change traces back to an Issue. Every merge goes through tests. No exceptions.

---

## 2. Requirements: GitHub Issues as Contracts

### Structure of an Issue

We treat Issues as acceptance criteria, not just descriptions. Each Issue must have:

- **Goal** — one sentence, what problem this solves
- **Checklist** — `- [ ] item` format, each item is a testable behavior
- **Labels** — `bug`, `enhancement`, `P0`–`P3` priority

**Example:**
```markdown
## Goal
Users should be able to run `codeindex init` and get a clean git tree.

## Checklist
- [x] `codeindex init` adds README_AI.md to .gitignore
- [x] Idempotent: running init twice doesn't duplicate the entry
- [x] Works whether .gitignore exists or not
- [x] Includes a comment explaining what the entry is for
```

### Why this matters
The checklist becomes your test cases. When all boxes are checked (code + tests green), the Issue closes. No "definition of done" debate.

### Priority labels
| Label | Meaning |
|-------|---------|
| P0 | Blocking — fix before anything else |
| P1 | High — next sprint |
| P2 | Medium — backlog |
| P3 | Nice to have |

---

## 3. Git Workflow: trunk-based + squash-merge

```
master   ←── only via squash-merge PR from feature/*, tagged releases only
  └── feature/short-description   ←── where you work
  └── fix/short-description
```

No `develop` / `release` branches — `master` is both integration and production
branch; releases are tags. See [gitflow-workflow.md](gitflow-workflow.md) for the
full flow.

### Day-to-day commands

```bash
# Start work
git checkout master && git pull
git checkout -b feature/my-feature

# Commit (conventional format required)
git commit -m "feat(scope): add something"
git commit -m "fix(scope): correct something"
git commit -m "test(scope): add tests for something"

# Finish
git push -u origin feature/my-feature
# → open PR to master on GitHub (squash-merge when approved)
```

### Commit format: `type(scope): description`

| Type | When |
|------|------|
| `feat` | New capability |
| `fix` | Bug correction |
| `test` | Adding/fixing tests |
| `refactor` | Restructuring without behavior change |
| `docs` | Documentation only |
| `chore` | Tooling, deps, config |

**Scope** = affected module: `init`, `parser`, `hooks`, `scanner`, `cli`, etc.

Bad: `git commit -m "fix stuff"`
Good: `git commit -m "fix(hooks): handle missing .venv on pre-push"`

---

## 4. TDD: Red → Green → Refactor

### The rule
Write the failing test **before** the implementation. One behavior at a time.

```
1. Write test → run → it FAILS (red)
2. Write minimal implementation → run → it PASSES (green)
3. Refactor if needed → run → still PASSES
4. Repeat for next behavior
```

Do not batch-write tests and then batch-implement. Keeps the feedback loop tight.

### Test anatomy

```python
class TestUpdateGitignore:
    def test_creates_gitignore_when_absent(self, tmp_path):
        # Arrange
        # (tmp_path is an isolated empty directory)

        # Act
        result = _update_gitignore(tmp_path)

        # Assert
        assert result is True
        assert "README_AI.md" in (tmp_path / ".gitignore").read_text()

    def test_skips_when_already_present(self, tmp_path):
        (tmp_path / ".gitignore").write_text("README_AI.md\n")
        result = _update_gitignore(tmp_path)
        assert result is False  # idempotent
```

### Coverage floor
Current: **78% minimum**, enforced in CI. If your PR drops coverage below 78%, CI fails.

### Test speed tiers

| Command | Tests | Time | When to use |
|---------|-------|------|-------------|
| `pytest -m "not slow"` | ~1527 | ~2s | During development (default) |
| `pytest` | ~1546 | ~7s | Before opening a PR |
| `pytest --cov=src/codeindex --cov-report=term-missing` | ~1546 | ~8s | Checking coverage |

`slow` marks tests that invoke a real subprocess (CLI calls) or scan actual project files.
They run in CI but are excluded from the fast loop to keep feedback tight.

---

## 5. Git Hooks: Automated QA on Every Commit

Three hooks run automatically. You cannot commit or push without passing them.

### pre-commit (runs on `git commit`)
Checks **staged Python files only** — fast, targeted.

1. **ruff lint** — style, imports, unused vars, debug code (T100/T201 rules catch `print()` and `breakpoint()`)
2. Reports exact line numbers. Fix then re-stage.

### post-commit (runs after `git commit`)
Runs in background, non-blocking.

1. **codeindex scan** — regenerates README_AI.md for changed directories
2. Logs to `~/.codeindex/hooks/post-commit.log` (check here if indexes seem stale)

### pre-push (runs on `git push`)
Last gate before code leaves your machine.

1. **ruff lint** on full src/
2. **pytest** — feature branches get fast mode (`-x -q`), master gets full suite
3. **version consistency check** — verifies pyproject.toml version matches CHANGELOG.md

If pre-push fails, your push is blocked. Fix the issue, don't use `--no-verify`.

### Managing hooks

```bash
codeindex hooks status          # See which hooks are installed
codeindex hooks install --all   # Install all hooks (after fresh clone)
make install-hooks              # Same thing via Makefile
```

---

## 6. CI Pipeline: GitHub Actions

Runs on every push to `master` and every PR. Must pass before merge.

**Matrix**: Ubuntu + macOS × Python 3.10 / 3.11 / 3.12 = 6 combinations.

```
Jobs:
  test   → pip install + pytest --cov-fail-under=78
  lint   → ruff check src/ tests/
  mypy   → type check core modules (informational, non-blocking)
  build  → python -m build (verify package is buildable)
```

If CI is red, **do not merge**. Fix it first.

Coverage report uploads to Codecov (Ubuntu/3.11 only — avoids duplicate uploads).

---

## 7. Code Quality Rules

### Linting: ruff

Config in `pyproject.toml`:
```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "T"]
```

- `E/W` — PEP8 style
- `F` — undefined names, unused imports
- `I` — import ordering
- `N` — naming conventions
- `T` — debug code (`T201` = print, `T100` = breakpoint/pdb)

**Exceptions** (legitimate print() usage):
- `cli_*.py` — CLI output is intentional
- `scripts/*.py` — utility scripts
- `tests/**/*.py` — test assertions

Run locally: `ruff check src/ tests/` | Auto-fix: `ruff check --fix src/`

### Type checking: mypy

```bash
make typecheck
# → mypy src/codeindex/parser.py src/codeindex/scanner.py src/codeindex/config.py
```

Informational only — mypy errors don't block CI today. But new code in core modules should be typed.

---

## 8. Documentation Rules

### What gets updated on each change type

| Change | Files to update |
|--------|----------------|
| New feature | `CHANGELOG.md`, `README.md` if user-facing |
| Bug fix | `CHANGELOG.md` |
| Major release | `CHANGELOG.md` + `RELEASE_NOTES_vX.X.X.md` |

### CHANGELOG format (Keep a Changelog)

```markdown
## [0.23.2] - 2026-05-13
### Added
- `codeindex init` now adds README_AI.md to .gitignore automatically

### Changed
- Git hook shebang changed from `#!/bin/zsh` to `#!/usr/bin/env bash`
```

### README_AI.md — do not edit manually

These files are generated by `codeindex scan`. Editing them directly is wasted effort — they get overwritten on the next scan. To change what they contain, update the source docstrings.

---

## 9. Release Process

Releases go to PyPI via GitHub Actions with OIDC (no stored secrets).

```bash
# 1. Verify everything is clean
make pre-release-check VERSION=0.23.3

# 2. Bump version (updates pyproject.toml)
make bump-version VERSION=0.23.3

# 3. Update CHANGELOG.md and RELEASE_NOTES_v0.23.3.md

# 4. PR to master, merge

# 5. Create GitHub release + tag → triggers PyPI publish automatically
```

Version single source of truth: `pyproject.toml`. The consistency check script validates that CHANGELOG mentions the version.

---

## 10. Using Claude Code in This Workflow

This is where you can significantly accelerate development. Here's how we use Claude Code in practice.

### Setting up

Install Claude Code CLI, then in the project root:

```bash
codeindex init   # Injects codeindex guide into CLAUDE.md
```

This gives Claude Code project-specific context — it knows the architecture, conventions, and where to look first.

### Pattern: Issue → Branch → TDD → PR

Tell Claude Code the Issue number and let it drive:

```
"I have issue #42: codeindex scan should support .tsx files.
Create a feature branch, write failing tests first, then implement."
```

Claude Code will:
1. Read `README_AI.md` for architecture context
2. Create `feature/tsx-support` branch
3. Write tests in `tests/extractors/test_tsx.py`
4. Run tests (red)
5. Implement `src/codeindex/extractors/tsx.py`
6. Run tests (green)
7. Offer to commit with correct format

### Pattern: Architecture questions

```
"Where is symbol extraction implemented for Python files?"
```

Claude Code reads `README_AI.md` first (per CLAUDE.md rules), then uses Serena `find_symbol()` to locate exact code. Faster and more accurate than grep.

### Pattern: QA check before PR

```
"Run all QA checks and tell me if this branch is ready to PR."
```

Claude Code runs lint → tests → coverage → version check and reports what's failing with exact fix commands.

### What Claude Code does NOT replace

- Your judgment on architecture decisions
- ADR (Architecture Decision Records) — write these yourself in `docs/architecture/adr/`
- PR descriptions — write the "why" yourself; Claude writes the "what"
- Code review — Claude can suggest, but a human approves

### Things that slow Claude Code down (avoid these)

- Asking it to edit `README_AI.md` directly — it'll do it, then the next scan overwrites it
- Committing directly to `master` — hooks and CI protect it, Claude Code knows to use feature branches
- Skipping `--no-verify` to get past hooks — the hooks exist for a reason; fix the underlying issue

---

## Quick Reference

```bash
# Setup (after fresh clone)
source .venv/bin/activate
pip install -e ".[dev,all]"
make install-hooks

# Development loop
git checkout -b feature/my-feature
# write test → implement → pytest → commit

# Before PR
make lint
pytest --cov=src/codeindex
make check-version

# Check what's installed
codeindex hooks status
codeindex status
```

---

## Checklist: "Is my PR ready?"

- [ ] Tests written before implementation (TDD)
- [ ] `pytest` passes locally
- [ ] Coverage didn't drop below 78%
- [ ] `ruff check src/ tests/` is clean
- [ ] `CHANGELOG.md` updated (for features/fixes)
- [ ] Commit messages follow `type(scope): description`
- [ ] PR description explains **why**, not just what changed
- [ ] Linked to the GitHub Issue (`Closes #XX`)
