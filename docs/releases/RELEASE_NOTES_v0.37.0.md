# Release Notes v0.37.0

**Date**: 2026-08-15
**Type**: Minor with **BREAKING** removal

---

## TL;DR

The post-commit hook is gone. codeindex is now purely a **stateless
generator** — *when* to refresh indexes is the orchestrator's policy, not
the generator's. `loomgraph index` already re-exports on every run, and
README_AI refresh is release-time or manual. Everything else in this
release is hardening: cleaner graphs for JS/TS projects, leftover-hook
cleanup, and a docs sweep.

## Breaking: post-commit hook removed (GH #167)

**What you'll notice after upgrading**: if you had the hook installed,
every commit silently spawns a dead wrapper — its errors go to
`~/.codeindex/hooks/post-commit.log` and cost one Python startup per
commit. Nothing breaks; nothing prints.

**Migration**:

```bash
codeindex hooks status                  # flags the leftover
codeindex hooks uninstall post-commit   # (or: uninstall --all)
```

Removed with it: `hooks install post-commit`, the hidden `hooks run`,
`hooks rerun`, the `hooks.post_commit` config section
(auto/disabled/async/sync/prompt modes), and the install-time
enabled-warning. `pre-commit` / `pre-push` hooks are unchanged.

**Why**: per-commit was the wrong frequency for a navigation index, and
the refresh machinery (loop guards, config gating, mode selection) cost
more than it returned. Refresh policy belongs to whoever consumes the
indexes.

## README_AI refresh is now release-time (GH #166)

The codeindex repo itself refreshes its tracked README_AI indexes at
release time (`scripts/release.sh` step 6.5, between version bump and
tag). For your repo: run `codeindex scan-all` whenever you want fresh
navigation — before a release, after a big refactor, or whenever.

## Cleaner graphs for JS/TS projects (GH #165)

Unexcluded co-located test files were the upstream root cause of
graph-export edge pollution (a real NestJS+React monorepo: 77% of edges
from test files, all mocks unresolved). `codeindex init` now suggests
`*.spec.ts` / `*.test.ts` / `__tests__` excludes when such files exist,
and `codeindex config explain exclude` lists them — graph-export's
high-unresolved warning always told you to run it; now the answer is
actually there.

## Fixes

- Characterization tests no longer drift on local runs from fixture
  pollution (GH #135 residual).
- `hooks status` survives an unreadable leftover hook; `uninstall --all`
  removes leftovers.
- JS-test detection prunes `node_modules`/venvs and shares its
  skip-list with language detection.
- Docs sweep: no active doc, `init` output, or example still advertises
  the removed post-commit workflow.

## Upgrading

```bash
pipx upgrade ai-codeindex
codeindex hooks status   # check for the leftover, uninstall if flagged
```

LoomGraph users: nothing to do — `loomgraph index` behavior is
unchanged.
