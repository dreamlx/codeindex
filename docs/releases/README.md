# Release Notes

**Location**: Historical release notes for codeindex versions

This directory contains detailed release notes for all published versions of codeindex.

---

## Available Releases

| Version | Date | Highlights |
|---------|------|------------|
| [v0.12.0](RELEASE_NOTES_v0.12.0.md) | 2026-02-07 | Call Relationships Extraction (Python, Java) |
| [v0.10.0](RELEASE_NOTES_v0.10.0.md) | 2026-02-06 | PHP LoomGraph Integration |
| [v0.9.0](RELEASE_NOTES_v0.9.0.md) | 2026-02-06 | Python LoomGraph Integration |
| [v0.8.0](RELEASE_NOTES_v0.8.0.md) | 2026-02-06 | Java Complete (Spring Routes + Lombok) |
| [v0.7.0](RELEASE_NOTES_v0.7.0.md) | 2026-02-05 | Java Language Support (MVP) |
| [v0.5.0-beta1](RELEASE_NOTES_v0.5.0-beta1.md) | 2026-02-02 | Git Hooks Beta |
| [v0.4.0](RELEASE_NOTES_v0.4.0.md) | 2026-02-02 | KISS Universal Description Generator |
| [v0.3.2](RELEASE_NOTES_v0.3.2.md) | - | Bug fixes and improvements |
| [v0.3.1](RELEASE_NOTES_v0.3.1.md) | 2026-01-28 | CLI Module Split |
| [v0.3.0](RELEASE_NOTES_v0.3.0.md) | 2026-01-27 | Tech Debt Analysis |
| [v0.2.0](RELEASE_NOTES_v0.2.0.md) | 2025-01-15 | Adaptive Symbol Extraction |

---

## Version Naming

- **Major.Minor.Patch** (e.g., v0.12.0)
  - Major: Breaking changes (v1.0.0 when production-ready)
  - Minor: New features (backward compatible)
  - Patch: Bug fixes

- **Beta releases** (e.g., v0.5.0-beta1)
  - Pre-release versions for testing

---

## Finding Release Information

**For the latest release**:
- See [CHANGELOG.md](../../CHANGELOG.md) for summary
- See the most recent RELEASE_NOTES file for details

**For older releases**:
- Browse this directory chronologically
- Check CHANGELOG.md for version history

**For roadmap and future versions**:
- See [docs/planning/ROADMAP.md](../planning/ROADMAP.md)

---

## Release Process

When publishing a new release:

1. Update `CHANGELOG.md` with changes
2. Create `RELEASE_NOTES_vX.Y.Z.md` in this directory
3. Update this README with the new version
4. Tag the release: `git tag vX.Y.Z`
5. Push tag: `git push origin vX.Y.Z`
6. Create GitHub release (optional)

See [CLAUDE.md](../../CLAUDE.md) for detailed release workflow.

---

**Last Updated**: 2026-02-07
**Total Releases**: 11
