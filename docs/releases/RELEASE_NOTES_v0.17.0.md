# Release Notes - v0.17.0

**Release Date**: 2026-02-12
**Theme**: CLAUDE.md Injection — Closing the AI Awareness Gap

---

## Overview

v0.17.0 adds automatic CLAUDE.md injection to `codeindex init`, solving the "awareness gap" where Claude Code had no way to discover that a project uses codeindex. Now, when you run `codeindex init`, it injects a small directive section into the project's `CLAUDE.md` so Claude Code automatically reads README_AI.md files on every startup.

---

## Major Changes

### CLAUDE.md Injection via `codeindex init`

**Problem**: Git hooks keep README_AI.md fresh and CODEINDEX.md has the command reference, but Claude Code never reads either file because it only auto-reads `CLAUDE.md` at startup.

**Solution**: `codeindex init` now injects a codeindex section into `CLAUDE.md`:

```markdown
<!-- codeindex:start -->
## codeindex

This project uses codeindex for AI-friendly code documentation.

- **Always read README_AI.md** before exploring source code in any directory
- If README_AI.md is missing or outdated, run: `codeindex scan <dir>`
- Check documentation coverage: `codeindex status`
- Full command reference: see CODEINDEX.md
<!-- codeindex:end -->
```

**Behavior**:
- **New project** (no CLAUDE.md): Creates the file with just the codeindex section
- **Existing project**: Prepends the section, preserving all existing content
- **Re-run**: Idempotent — replaces content between markers, never duplicates
- **Interactive mode**: Asks "Inject codeindex instructions into CLAUDE.md?" (default: yes)
- **Non-interactive mode** (`--yes`): Injects by default (safe — it's just markdown)

### Wizard Step Renumbering

The interactive wizard now has 6 steps (was 5):
1. Detect languages
2. Detect frameworks
3. Analyze project structure
4. Calculate performance settings
5. **AI agent integration** (NEW — CLAUDE.md injection)
6. Optional features (hooks, CODEINDEX.md, AI CLI)

---

## Files Changed

| File | Change |
|------|--------|
| `src/codeindex/init_wizard.py` | Added constants, `inject_claude_md()`, `has_claude_md_injection()`, updated `WizardResult`, renumbered wizard steps |
| `src/codeindex/cli_config.py` | Added inject calls in both interactive and `--yes` modes |
| `tests/test_claude_md_injection.py` | 12 new unit tests |
| `tests/test_init_wizard_bdd.py` | 4 new BDD scenarios + step definitions |
| `tests/features/init_wizard.feature` | 4 new CLAUDE.md injection scenarios |

---

## Test Coverage

- **12 unit tests** for `inject_claude_md()` and `has_claude_md_injection()`
- **4 BDD scenarios**: create, prepend, idempotent, skip
- **Full suite**: 1049 tests pass, 0 failures
