# Release Notes - v0.23.1

## New: `codeindex claude-md` CLI Command

Manage the codeindex section in your project's CLAUDE.md:

```bash
codeindex claude-md update    # Inject or update codeindex section
codeindex claude-md status    # Check if section is up-to-date
```

After upgrading codeindex, a startup hint reminds you to refresh:

```
hint: CLAUDE.md has codeindex v0.22.0, current is v0.23.1. Run `codeindex claude-md update` to refresh.
```

## Template Simplified

The injected CLAUDE.md section is now 22 lines (was 130), containing only:
- Code navigation priority (README_AI.md first)
- 6 essential commands
- `codeindex --help` reference

## Bug Fixes

- Removed 181 lines of dead code in `hooks.py` (`post_install_update_guide` was never wired to pip)
- Fixed `cli_config.py` importing non-existent `install_hooks` function
