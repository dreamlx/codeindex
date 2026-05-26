# Release Notes - v0.23.2

## Workflow & Hooks Improvements

### Git Hooks Portability
- All hook shebangs changed from `#!/bin/zsh` to `#!/usr/bin/env bash` for cross-platform compatibility
- `hook-common.sh` now version-controlled in `scripts/hooks/` and auto-copied on install

### Hook Installation Unified
- `make install-hooks` now delegates to `codeindex hooks install --all` (single entry point)
- `HookManager._ensure_hook_common()` copies shared utilities on every hook install

### Post-commit Error Visibility
- stderr redirected to `~/.codeindex/hooks/post-commit.log` instead of `/dev/null`
- Errors are now diagnosable instead of silently swallowed

### Lint & Type Checking
- **ruff T rules**: `T201` (print) and `T100` (debugger) replace ~50 lines of regex-based debug detection in pre-commit template
- **mypy**: Added as dev dependency with baseline config; CI runs type check on core modules (informational)
- **Coverage gate**: CI enforces `--cov-fail-under=78` to prevent coverage regression
