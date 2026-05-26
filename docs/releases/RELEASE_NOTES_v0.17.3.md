# Release Notes: v0.17.3

**Release Date**: 2026-02-13

## Summary

Improved the CLAUDE.md template and post-init message to ensure AI agents properly configure `.codeindex.yaml` before scanning. Added Epic 19 planning doc for future multi-agent tool support.

## Changes

### CLAUDE.md Template Improved
- Added **first-time setup instructions** to the injected CLAUDE.md section
- AI agents now know to: (1) review `.codeindex.yaml` config, (2) run `scan-all`, (3) optionally install hooks
- Ensures the config review step is not skipped

### Post-init Message Updated
- Step 1 now says "Review .codeindex.yaml" — guiding AI to verify include/exclude patterns before scanning
- Clearer, more actionable next steps output

### Epic 19: Multi-Agent Onboarding (Planning)
- Added `docs/planning/active/epic19-multi-agent-onboarding.md`
- Plans for supporting Cursor, Windsurf, Cline, GitHub Copilot instruction injection
- Documents the complete user onboarding flow for future reference

## Upgrade

```bash
pip install --upgrade ai-codeindex[all]
```

No breaking changes. Existing `.codeindex.yaml` files and CLAUDE.md injections continue to work.
