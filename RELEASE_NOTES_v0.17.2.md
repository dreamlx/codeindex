# Release Notes: v0.17.2

**Release Date**: 2026-02-13
**Type**: Documentation cleanup

## Summary

Full audit and consolidation of `docs/guides/` to align with v0.17.x features.

## Changes

### docs/guides/ Audit (5 files updated)

- **git-hooks-integration.md**: Fixed version (v0.5.0-beta1 → v0.17.2), updated pre-push hook description from "placeholder" to actual behavior (lint + tests + version consistency), fixed stale CLI flags and dead links
- **contributing.md**: Fixed GitHub URLs (yourusername → dreamlx), updated install commands, rewrote "Adding New Languages" for modular parser architecture (v0.14.0+), updated release process to use `make release`
- **configuration.md**: Extended version compatibility matrix to v0.17.x, added config explain (v0.14.0+), fixed stale `--ai --dry-run` flags

### docs/guides/ Consolidation (14 → 8 files)

**Deleted** (redundant with existing docs):
- `docstring-extraction.md` — content already in `configuration.md`
- `configuration-changelog.md` — duplicated `CHANGELOG.md`
- `migration-v0.6.md` — one-time migration doc, 12 versions old

**Moved to `docs/internal/`** (not user-facing guides):
- `git-commit-guide.md`
- `package-naming.md`
- `pypi-quickstart.md`

### Process

- Added docs review reminder to `make pre-release-check`
