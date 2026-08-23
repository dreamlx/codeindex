# For LoomGraph Developers 🤝

codeindex is the **parser engine** that powers LoomGraph. The sole seam between
the two repos is the `graph-export` NDJSON contract (ADR-009).

## One-line setup

End users install LoomGraph — it pulls `ai-codeindex` automatically, you never
operate codeindex directly:

```bash
pipx install loomgraph
loomgraph index .          # runs codeindex graph-export → embed → inject
```

## The seam: graph-export NDJSON

`codeindex graph-export` emits entities + edges (CALLS / INHERITS / IMPORTS)
as NDJSON; LoomGraph's `import-export` ingests it into the SQLite + sqlite-vec
store. codeindex stays **stateless** (ADR-007) — it never owns the graph.

```
codeindex graph-export  →  NDJSON  →  loomgraph import-export  →  SQLite + sqlite-vec
```

Full contract: [`docs/guides/graph-export.md`](docs/guides/graph-export.md)

## codeindex commands LoomGraph devs should know

| Command | When you touch it |
|---|---|
| `codeindex graph-export` | the NDJSON seam — schema/edge resolution lives here |
| `codeindex scan-all` | regenerate `README_AI.md` navigation indexes |
| `codeindex parse <file>` | single-file JSON parse, for ad-hoc inspection |
| `codeindex scan-all --ai` | AI-enriched module descriptions (orthogonal to the graph) |

LoomGraph also ships `loomgraph codeindex <cmd>` as a passthrough that runs
any codeindex command in LoomGraph's pinned environment.

## AI enrichment vs. the graph — they don't mix

LoomGraph's index is **pure AST** (entities, relations, call graph) — no LLM,
fully reproducible. `codeindex scan-all --ai` is an **orthogonal** overlay that
enriches `README_AI.md` (one-line module descriptions); LoomGraph's graph never
consumes the `--ai` enrichment. The two are independent surfaces.

- **When you need `--ai`**: unfamiliar large codebase where you want an LLM to narrate what each module does.
- **When you don't**: structural queries via LoomGraph (`find` / `graph` / `topology` / `deps`). The AST is ground truth there; LLM would add latency and hallucination risk.

## Full integration guide

[`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) —
complete JSON format, batch processing, error handling, performance notes.

## Related

- [ADR-007](docs/architecture/adr/007-codeindex-stateless-graph-ownership.md) — codeindex is stateless
- [ADR-009](docs/architecture/adr/009-codeindex-loomgraph-parser-engine.md) — parser-engine positioning
- [graph-export guide](docs/guides/graph-export.md) — the NDJSON seam contract
