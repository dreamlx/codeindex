# Release (Quick Start)

Releasing `ai-codeindex` to PyPI is one command. The mechanical steps live in
the **Makefile** (`make help` lists every target) — this doc is only the order
plus the judgment steps a Makefile can't encode.

## Steps

1. **Pre-flight** — work through [pre-release-checklist.md](pre-release-checklist.md)
   (tests green, sandbox-install the wheel with `[all]`, read the release notes
   as a user).
2. **Prep docs** — move `CHANGELOG.md` `[Unreleased]` → `[X.Y.Z]`, update
   `docs/planning/ROADMAP.md`, commit.
3. **Merge to master** — `git checkout master && git merge develop --no-ff`.
4. **Ship** — `make release VERSION=X.Y.Z`.

`make release` runs the pre-release checks, bumps the version, tags, and pushes.
GitHub Actions then tests on Python 3.10–3.12, builds, publishes to PyPI via the
trusted publisher, and cuts the GitHub Release. Monitor it under the repo's
**Actions** tab.

## Rolling back a bad tag

```bash
git tag -d vX.Y.Z                      # local
git push origin --delete vX.Y.Z        # remote
# PyPI releases can't be re-uploaded under the same version — bump to X.Y.Z+1.
```

> Why this is short: prose that re-narrates `make release` rots against the
> Makefile (the old 761-line guide was frozen at v0.9). The Makefile is the
> spec; this is the runbook around it.
