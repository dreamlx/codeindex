# graph-export — codeindex → loomgraph data contract

> **Status: EXPERIMENTAL (`schema_version: 1`).** v1 adds per-symbol
> `content_hash` (GH #124, #110 gate satisfied — see Entity). A consumer
> that only knew v0 sees `content_hash` as an additive field (ignored if
> unused); loomgraph's reader warns on `schema_version > supported` but
> still imports. Fields/format may change without deprecation while
> experimental.

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
{"type":"meta","schema_version":1,"generator":"codeindex","provenance_completeness":"ast-only: ..."}
{"type":"entity","id":"app.service.AuthService","entity_type":"class","source_id":"app/service.py:8","description":"Authenticates users.","signature":"class AuthService","provenance":"ast","content_hash":"fc5e93..."}
{"type":"edge","kind":"CALLS","src":"app.service.AuthService.login","dst":"app.service.AuthService.authenticate","resolution_qualifier":"resolved","source_id":"app/service.py:15"}
{"type":"edge","kind":"CALLS","src":"app.workers.kickoff","dst":null,"resolution_qualifier":"ambiguous","candidates":["app.workers.Builder.run","app.workers.Packer.run"],"source_id":"app/workers.py:15"}
{"type":"edge","kind":"IMPORTS","src":"app.service","dst":"app.validators","dst_raw":"app.validators","resolution_qualifier":"resolved","source_id":"app/service.py:5"}
```

### Naming convention (`id`)

Entity ids are **fully-qualified and path-derived**: the module is the file
path *relative to the scan root* with the extension dropped and `/` → `.`,
then the file-local symbol name appended. So `src/loomgraph/cli/_common.py`'s
`prepare_workspace_store` becomes `src.loomgraph.cli._common.prepare_workspace_store`.

Fully-qualified is deliberate — it resolves same-name collisions across
sibling classes/modules (the spike's F-class) and makes ownership explicit.

> **src-layout caveat.** Because the module is *path*-derived, not
> *import*-derived, a `src/`-layout project carries the layout dir in the id
> (`src.loomgraph.…`, where the real Python import path is `loomgraph.…`).
> codeindex does **not** strip it in v0 — there is no robust, config-free way
> to tell a layout dir (`src/`, strip) from a genuine top package (`app/`,
> keep). A consumer that maintains its own import-path index should normalise
> the layout prefix when ingesting these ids (it knows the project layout;
> codeindex, scanning a bare tree, does not). A codeindex-side `module_root` option is a
> possible v1 addition if multiple consumers need it.

### Entity

| field | meaning |
|---|---|
| `id` | fully-qualified, path-derived name (see above), e.g. `app.service.AuthService.login` |
| `entity_type` | `class` \| `function` \| `method` |
| `source_id` | `relpath:line` |
| `description` | first line of the docstring (may be empty) |
| `signature` | parser-derived signature, e.g. `def login(self, token: str) -> bool` / `class AuthService` (GH #115). Present for ~all symbols; empty only when the parser couldn't derive one. A consumer building an embedding input should use **`signature` + `description`** rather than `description` alone — docstring-less symbols have an empty `description`, so description-only embedding leaves a coverage hole (measured ~4–15% across repos). codeindex emits the two as separate fields; the combine is the consumer's call. |
| `provenance` | `ast` (L1 structural) |
| `content_hash` | per-symbol `sha256` over a **normalized** span (`line_start:line_end` slice → per-line trailing-ws strip → BOM strip → `\n`-join), GH #124. The hash is over **content, not line numbers** — inserting a line above a symbol shifts its `source_id` but leaves `content_hash` stable, so a consumer can skip re-embedding unchanged symbols (symbol-level incremental, vs the prior file-level warm-diff). `null` for no-span entities (module / external / synthetic). Additive over v0 — unknown-field-tolerant readers ignore it. |

### Edge

| field | meaning |
|---|---|
| `kind` | `CALLS` \| `INHERITS` \| `IMPORTS` |
| `src` | resolved entity id of the caller / child class |
| `dst` | resolved entity id of the callee / parent, or `null` if not resolved |
| `dst_raw` | the original best-effort name the resolver tried (file-local). Always present; **load-bearing when `dst` is null** — it is the only record of *what* was called, so a consumer can synthesise an external stub or filter framework noise (e.g. `expect`, `Date.now`) |
| `resolution_qualifier` | `resolved` \| `ambiguous` \| `unresolved` |
| `candidates` | (ambiguous only) the entity ids the name could refer to |
| `source_id` | `relpath:line` of the call / class definition / **import statement (IMPORTS)** |

### IMPORTS edges (GH #117, #118)

`IMPORTS` is **module→module** (additive over schema_version 0, no bump),
unlike `CALLS`/`INHERITS` (entity→entity):

- **`src`** = the *importer module* id (e.g. `app.service`) — **no `entity`
  record backs it** (modules aren't entities in this entity-centric slice;
  ADR-007), same shape as a `<module>`-level `CALLS` `src`. The consumer
  materialises the container if it wants one.
- **`dst`** = the *imported module* id if a file in the scan tree maps to it,
  else `null`. Resolution is **module-level** (does that module file exist?),
  not entity-level — `from app.validators import validate` → `dst` is
  `app.validators` (the module), not `validate` (the symbol).
- **Relative imports** (`./api`, `../lib` — TS/JS) resolve against the
  importer's directory (`./api` from `web.index` → `web.api`).
- **Java intra-project** (`import com.foo.Bar`) resolves by prepending the
  Maven source root (`src/main/java` / `src/test/java`) — `com.foo.Bar` ↔
  `src.main.java.com.foo.Bar` (GH #118). Layout-specific, **not** a general
  suffix match; external Java imports (`java.util.List`) stay unresolved.
- **PHP `use`** (`use App\Service`) resolves via `\` → `.` normalisation
  (PSR-4) — `App\Service` ↔ `App.Service` (GH #118).
- **Swift / ObjC** (`import Foundation` / `#import <Foundation/...>`) are
  framework-level — mostly unresolved (the framework isn't a single file in
  the scan tree); `dst_raw` preserves the framework name.
- **`dst_raw`** = the original import string (`app.validators` / `os` /
  `./api` / `App\Service`); load-bearing when `dst` is null
  (stdlib/external/framework) so a consumer can include externals in a
  dependency graph.
- **`source_id`** = `relpath:line` of the import statement; line is filled
  for all supported languages (Python/TS via #117, Java/PHP/Swift/ObjC via
  #118 — previously `file:0` for the latter four).

`loomgraph deps` aggregates these into module-level dependency graphs;
downstream `VALID_EDGE_KINDS` already includes `IMPORTS`.

## Scope — a structural slice, not a full graph index

The export is codeindex's **structural slice** (L1+L2): real code symbols
(`class` / `function` / `method`) and their `CALLS` / `INHERITS` edges. It is
**not** a complete graph index and is **not** meant to replace a consumer's
own index.

Deliberately **not** emitted (the consumer synthesises these around the
slice during ingestion, per ADR-007):

- **file / module container nodes** — derivable from each entity's `source_id`.
  Consequence: a `<module>`-level call has a `src` (the dotted module path)
  with no backing `entity` record; that's expected, the consumer materialises
  the container if it wants one. (`entity_type: "module"` may be added in v1
  if synthesising modules proves painful downstream.)
- **external / stdlib stubs** — these are exactly where `unresolved` edges
  point (see below); the consumer decides whether to materialise stub nodes.

This matches the LoomGraph#30 GREEN field set (which contained no module/file
nodes) and keeps the codeindex/loomgraph division clean: codeindex emits the
symbol-level truth, loomgraph builds the container + external + semantic
scaffolding on top.

## Consumer contract — read these two caveats

The parser emits **file-local** names; the export runs the only cross-file
resolution pass. Two metadata mechanisms exist because that resolution and
the underlying AST extraction are lossy — **a consumer that ignores them will
draw wrong conclusions**:

1. **`resolution_qualifier`** — never treat an `unresolved` or `ambiguous`
   edge as a confirmed relationship. `unresolved` usually means external /
   stdlib or a name not in the tree (with `dst: null`); `ambiguous` means the
   name matched several entities (see `candidates`, `dst: null`). A **high
   unresolved fraction is normal** — most calls in real code go to stdlib /
   third-party / methods AST cannot statically resolve (≈59% on a real
   loomgraph round-trip). The consumer owns the dangling-edge policy: drop,
   keep as dangling, or materialise an external stub node as the `dst`.
   codeindex emits no sentinel/placeholder entity — the entity set contains
   only real code symbols. A dotted callee whose receiver is a runtime
   variable (`obj.run`, `db.exec`) resolves as `unresolved`, **not**
   `ambiguous` — the receiver's type is statically unknowable (dynamic
   dispatch), so a last-segment name match would be a guess; `ambiguous` is
   reserved for genuine same-name collisions reachable by suffix (e.g. a bare
   `run()` with multiple `.run` entities). (GH #127)
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
