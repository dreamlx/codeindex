# Release Notes - v0.25.0

**Release Date**: 2026-05-26
**Theme**: Distribution split — codeindex is now a `pipx`-installed CLI plus an optional Claude Code plugin

---

## 📊 Overview

v0.25.0 is a **distribution** release. No parser or output changes — instead, codeindex stops trying to be both a Python CLI *and* a Claude Code integration bundle in one wheel. It splits cleanly into two artifacts:

- **`ai-codeindex`** (PyPI) — the CLI. Install with `pipx`. Zero Claude Code coupling; works the same in Cursor / Continue / a bare terminal.
- **`dreamlx/codeindex-claude`** (GitHub) — a Claude Code **plugin** bundling the four skills + a prerequisite-check hook. Install via `/plugin install`.

Rationale and the full decision record: [ADR-006](../architecture/adr/006-distribution-architecture-split.md). This continues the retreat from install-time magic begun in [ADR-004](../architecture/adr/004-automatic-claude-md-update.md).

**Breaking changes**: none. Deprecations only (removal in v1.0).
**Test coverage**: full suite green (1574+ tests).

---

## ✨ What's New

### 1. `pipx install ai-codeindex` is the recommended path

codeindex is a CLI tool, so it belongs in an isolated per-tool environment:

```bash
pipx install ai-codeindex
```

`pip install --user ai-codeindex` still works as a fallback. Parser extras can be added with `pipx inject ai-codeindex tree-sitter-<lang>` or pinned at install time (`pipx install "ai-codeindex[python]"`).

### 2. Claude Code plugin

The four skills now ship as a proper plugin instead of a copy-script:

```
/plugin marketplace add dreamlx/codeindex-claude
/plugin install codeindex@codeindex-claude
```

| Skill | Trigger |
|-------|---------|
| `codeindex:arch` | "where is X", "how does module Y work", architecture questions |
| `codeindex:index` | "index this project", "generate README_AI.md" |
| `codeindex:hooks` | "set up auto-update", "install hooks" |
| `codeindex:update-guide` | "refresh my CLAUDE.md to latest codeindex guide" |

A SessionStart hook checks that the `codeindex` CLI is on `PATH` and prints an install hint if not.

### 3. `codeindex init` is minimal

`init` now writes only project-scoped scaffolding: `.codeindex.yaml`, a marker-based codeindex section in the project's `CLAUDE.md`, and a `.gitignore` entry for `README_AI.md`. It no longer creates `CODEINDEX.md` or installs git hooks (those are opt-in). It has never touched `~/.claude/` — a regression test now enforces that.

---

## 📦 Upgrade Guide

Pick the row that matches you.

### You used `pip install ai-codeindex` and never touched skills

```bash
pipx install ai-codeindex        # migrate to an isolated env
# (optional) pip uninstall ai-codeindex   # remove the old pip-managed copy
```

Nothing else changes. The CLI behaves identically.

### You ran `./skills/install.sh` (the old skill installer)

Your skills under `~/.claude/skills/{mo-arch,mo-hooks,mo-index}` keep working but will **not** receive updates. Switch to the plugin:

```bash
# remove the old copies (optional but recommended to avoid duplicate skills)
rm -rf ~/.claude/skills/mo-arch ~/.claude/skills/mo-hooks ~/.claude/skills/mo-index

# install the plugin
/plugin marketplace add dreamlx/codeindex-claude
/plugin install codeindex@codeindex-claude
```

Skill names change: `/mo-arch` → `codeindex:arch`, `/mo-index` → `codeindex:index`, `/mo-hooks` → `codeindex:hooks`, plus the new `codeindex:update-guide`.

### You have codeindex git hooks installed

No action required — installed hooks keep working. `codeindex hooks install` is still supported (now with a deprecation hint). Going forward, the `codeindex:hooks` plugin skill walks you through the same setup.

### You rely on `codeindex claude-md update`

Still works, now prints a deprecation notice. Two paths forward:
- **CLI-only users**: keep using it; suppress the notice with `CODEINDEX_NO_DEPRECATION_WARNINGS=1`. (Removed in v1.0.)
- **Claude Code users**: use the `codeindex:update-guide` skill from the plugin.

### 🇨🇳 China users

If your default PyPI mirror (e.g. aliyun) hasn't synced the release yet:

```bash
pipx install --index-url https://pypi.org/simple/ ai-codeindex
```

The plugin is hosted on GitHub, so it isn't affected by PyPI mirror lag.

---

## ⚠️ Deprecations (removed in v1.0)

| Deprecated | Use instead |
|------------|-------------|
| `codeindex claude-md update` / `status` | `codeindex:update-guide` skill (plugin) |
| `codeindex hooks install` | `codeindex:hooks` skill (plugin) — the underlying command still works |
| `skills/` directory + `skills/install.sh` | `/plugin install codeindex@codeindex-claude` |

All deprecated CLI commands remain fully functional in the v0.x line; the notices are advisory.

---

## 🔬 Why we made these changes

The v0.24.0 release surfaced three pain points: PyPI mirror sync delays for Chinese users, an `install.sh` skill mechanism that silently breaks under `pipx`, and a wheel trying to manage Claude Code's `~/.claude/` config (an anti-pattern — like an npm package editing VS Code settings). Splitting the artifacts fixes all three and lets the CLI serve non-Claude editors cleanly. Full reasoning: [ADR-006](../architecture/adr/006-distribution-architecture-split.md).

---

## 📋 Full Changelog

See [CHANGELOG.md](../../CHANGELOG.md) `[0.25.0]` section.
