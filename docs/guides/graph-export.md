# graph-export — codeindex → loomgraph data contract

> **Status: EXPERIMENTAL (`schema_version: 0`).** Validated on Python; a
> TypeScript spot-check precedes any stable-contract promise. Fields and
> format may change without deprecation while at version 0.

`codeindex graph-export` dumps a **write-once** NDJSON graph of the codebase
for downstream consumers (loomgraph) to read. Per [ADR-007](../architecture/adr/007-codeindex-stateless-graph-ownership.md)
codeindex stays a stateless emitter: this command holds **no** persistent or
mutable state — no `.db`, no incremental sync, no vector index.

## Usage

```bash
codeindex graph-export --root . -o graph-export.ndjson
codeindex graph-export --root . -o -        # stdout
```

It does its **own clean whole-tree parse** (every source file exactly once)
and is fully decoupled from `scan-all` / README rendering — running it never
touches `README_AI.md`.

## Format

NDJSON. Line 1 is the `meta` record; then `entity` records; then `edge`
records. All records carry a `type` tag.

```jsonc
{"type":"meta","schema_version":0,"generator":"codeindex","provenance_completeness":"ast-only: ..."}
{"type":"entity","id":"app.service.AuthService","entity_type":"class","source_id":"app/service.py:8","description":"Authenticates users.","provenance":"ast"}
{"type":"edge","kind":"CALLS","src":"app.service.AuthService.login","dst":"app.service.AuthService.authenticate","resolution_qualifier":"resolved","source_id":"app/service.py:15"}
{"type":"edge","kind":"CALLS","src":"app.workers.kickoff","dst":null,"resolution_qualifier":"ambiguous","candidates":["app.workers.Builder.run","app.workers.Packer.run"],"source_id":"app/workers.py:15"}
```

### Entity

| field | meaning |
|---|---|
| `id` | module-qualified name, e.g. `app.service.AuthService.login` (module derived from file path) |
| `entity_type` | `class` \| `function` \| `method` |
| `source_id` | `relpath:line` |
| `description` | first line of the docstring (may be empty) |
| `provenance` | `ast` (L1 structural) |

### Edge

| field | meaning |
|---|---|
| `kind` | `CALLS` \| `INHERITS` |
| `src` | resolved entity id of the caller / child class |
| `dst` | resolved entity id of the callee / parent, or `null` if not resolved |
| `resolution_qualifier` | `resolved` \| `ambiguous` \| `unresolved` |
| `candidates` | (ambiguous only) the entity ids the name could refer to |
| `source_id` | `relpath:line` of the call / class definition |

## Consumer contract — read these two caveats

The parser emits **file-local** names; the export runs the only cross-file
resolution pass. Two metadata mechanisms exist because that resolution and
the underlying AST extraction are lossy — **a consumer that ignores them will
draw wrong conclusions**:

1. **`resolution_qualifier`** — never treat an `unresolved` or `ambiguous`
   edge as a confirmed relationship. `unresolved` usually means external /
   stdlib or a name not in the tree; `ambiguous` means the name matched
   several entities (see `candidates`).
2. **`provenance_completeness`** (meta) — extraction is AST-only. Dynamic
   dispatch (`getattr` / duck-typing / event handlers), reflection /
   metaclasses, and decorator wiring are **not** captured. An **absent edge
   means "not statically resolvable", not "none"** — this was the decisive
   finding of the LoomGraph#30 consumption spike.

## What this is NOT

Per ADR-007, codeindex does not own a persistent graph. No mutable `.db`,
incremental sync, corruption recovery, or `sqlite-vec` index — those, plus L3
(design-doc LLM extraction), are loomgraph's. This artifact is a one-shot
snapshot loomgraph reads (process-decoupled, decision (a)).
