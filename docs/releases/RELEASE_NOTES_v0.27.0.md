# Release Notes - v0.27.0

**Theme**: graph-export + parser robustness.

This release ships codeindex's first **write-once graph artifact** — the data
contract with loomgraph (per [ADR-007](../architecture/adr/007-codeindex-stateless-graph-ownership.md)) —
alongside the AI-retry and partial-parse robustness fixes that were sitting
unreleased on master.

> **Upgrade is safe and additive.** `graph-export` is a brand-new standalone
> command; the `GraphBuffer` IR it reuses is dormant (not wired into
> `scan-all`); and existing `scan-all` / `parse` / `symbols` output is
> unchanged. No migration, no cache flush needed.

## New: `codeindex graph-export`

A standalone command that does its own clean whole-tree parse and emits a
**write-once NDJSON** graph for downstream consumers (loomgraph):

```bash
codeindex graph-export --root . -o graph-export.ndjson
codeindex graph-export --root . -o -        # stdout
```

- **Entities** — `class` / `function` / `method`, module-qualified id,
  `source_id` (`relpath:line`), first-line description, `provenance`.
- **Edges** — `CALLS` / `INHERITS`, each carrying a `resolution_qualifier`
  (`resolved` / `ambiguous` / `unresolved`) plus `dst_raw` (the original
  name, load-bearing when `dst` is null) and `candidates` on ambiguous.
- **Meta** — `schema_version` + `provenance_completeness` flagging that AST
  extraction does not capture dynamic dispatch / reflection.

**Status: experimental (`schema_version: 0`).** The schema may change without
deprecation while at version 0; validated on Python with a TypeScript
spot-check. Full contract + consumer caveats: [docs/guides/graph-export.md](../guides/graph-export.md).

Decoupling note: the LoomGraph#30 consumption spike (verdict 🟡 YELLOW)
justified this export but **not** an internal render-flip (#101 Phase 2);
the two are architecturally independent and the flip is deferred.

## Robustness (previously unreleased on master)

- **In-run AI retry/backoff** (#97): `scan-all --ai` now retries
  *recognised-transient* failures (timeout / rate-limit / 5xx) with
  exponential backoff (scan paths use 3 attempts); permanent failures
  (e.g. misconfigured `ai_command`) still fail fast. Agent-CLI stays the
  only transport.
- **Cross-language partial-parse recovery** (#95): a single unparseable
  construct no longer zeroes a whole file's symbols. All parsers
  (python / typescript / java / php / swift / objc) now return recoverable
  symbols flagged `partial=True`, surfacing a hard error only when nothing
  is recoverable.

## Internal

- **GraphBuffer IR** (#101): a per-run in-memory IR between parse and render,
  shipped dormant (unwired) with a characterization safety net. Reused by
  `graph-export`; no user-facing behavior change.

See [CHANGELOG.md](../../CHANGELOG.md) for the full entry list.
