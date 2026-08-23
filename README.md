# codeindex

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

[🇬🇧 English](README.md) | [🇨🇳 中文](README_zh.md)

**codeindex is the parser engine that powers [LoomGraph](https://github.com/dreamlx/LoomGraph).** It turns any codebase into AI-readable structural artifacts — a `graph-export` NDJSON call/inheritance graph (the sole seam LoomGraph consumes) and, as a standalone by-product, `README_AI.md` navigation indexes. Stateless (ADR-007); the user-facing product is LoomGraph.

> **End users**: `pipx install loomgraph` — it pulls `ai-codeindex` automatically. You never operate codeindex directly. See the [LoomGraph integration guide](FOR_LOOMGRAPH.md).
> **Standalone users** (navigation indexes without the graph layer): see [Standalone usage](#standalone-usage-without-the-graph-layer) below.

---

## Why

AI agents in an unfamiliar codebase waste tokens grepping for the right entry point. codeindex pre-computes a structural slice (tree-sitter AST → symbols, calls, inheritance) so the agent — or the graph layer that serves the agent — starts from a known map, not from raw `grep`. The win is navigation efficiency, not capability: a measured −28% tokens / −19% wall-time on the discovery phase, but answer quality is a wash (it does not make the agent smarter — see [Benchmark](#benchmark)).

---

## Install

```bash
pipx install loomgraph          # end users: pulls ai-codeindex as a dependency
```

Standalone (navigation indexes only, no graph layer):

```bash
pipx install ai-codeindex
```

From source:

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"
```

> **Claude Code users** — also install the companion plugin for skills
> (`codeindex:arch` / `:index` / `:update-guide`):
> ```
> /plugin marketplace add dreamlx/codeindex-claude
> /plugin install codeindex@codeindex-claude
> ```

### Language parsers

Python and PHP grammars ship by default. Other languages need the matching `tree-sitter` grammar:

```bash
pipx inject ai-codeindex tree-sitter-typescript tree-sitter-java   # add to pipx env
# or pin a subset at install time:
pipx install "ai-codeindex[ios]"      # Swift + Objective-C
```

> 🇨🇳 China users: if your mirror hasn't synced the latest release, install from upstream PyPI:
> `pipx install --index-url https://pypi.org/simple/ ai-codeindex`

---

## Quick start

**LoomGraph users** (the main path):

```bash
loomgraph index .            # codeindex graph-export → embed → inject, one pipeline
loomgraph graph "UserService.login" --depth 2
loomgraph topology           # orphans / hubs + resolved_ratio trust signal
```

**Standalone** (README_AI navigation indexes only):

```bash
codeindex init               # creates .codeindex.yaml + injects CLAUDE.md section
codeindex scan-all           # structural + optional AI descriptions (auto when ai_command set)
codeindex scan-all --no-ai   # structural only
```

Full command reference: `codeindex --help`.

---

## Standalone usage (without the graph layer)

codeindex's `README_AI.md` is a tiered **navigation index** — agents browse it to find the right module, then drop to source for precise mechanism. It is *not* a knowledge graph and does not resolve cross-module relationships; for that, use LoomGraph.

**When standalone is the right fit**:
- Small / mid codebase where a graph layer is more weight than you need.
- Air-gapped intranet where you want navigation without any external service.
- Pairing with [Serena MCP](https://github.com/oraios/serena) for precise symbol queries (codeindex = the "map", Serena = the "GPS").

**When you should move to LoomGraph**:
- You need cross-module call-graph walks (callers of `authenticate()` two hops deep).
- You need change-impact analysis, topology smells, or semantic search.
- The codebase is large enough that a flat navigation index stops paying (see benchmark: on a 250-directory legacy system the token win nearly vanished — a flat index points at files but can't synthesize cross-module semantics).

`codeindex init` injects a codeindex section into your **project's** `CLAUDE.md` so Claude Code reads `README_AI.md` first (never `~/.claude` — ADR-006). `codeindex scan-all` refreshes indexes after structural changes; `README_AI.md` is a generated artifact — do not hand-edit.

---

## Benchmark

Most "AI code understanding" tools assert value. We A/B-tested ours — and published the unflattering parts.

Across **15 graded navigation questions on 3 heterogeneous real projects**, a coding agent **with** `README_AI.md` vs **without**:

- **−28% tokens, −19% wall-time** on average — agents reach the right file faster and cheaper.
- **Answer quality is a wash.** It does *not* make answers more *correct* — the win is efficiency, not capability. (An undisciplined index even hurt a few precise-mechanism questions; fixed in [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md).)
- **Smallest win on the largest codebases.** On a 250-directory legacy system the token win nearly vanished — a flat index points you to files but can't synthesize cross-module semantics. codeindex is the *navigate* layer, not the *understand-everything* layer (pair it with source-reading / [Serena](https://github.com/oraios/serena) for precise mechanism, or move to LoomGraph for cross-module graph queries).

Full data incl. the failure cases: **[2026-05 benchmark](docs/benchmark/2026-05-readme-impact.md)**. Reproduce on your own repos: **[`bench/`](bench/)** (`make setup && make run && make grade`).

> Why publish the parts that don't flatter the tool: a navigation index that quietly degrades answer quality is worse than none. Knowing *exactly* where it helps — and where to drop to source — is the point.

---

## Commands

Full reference: `codeindex --help`. Highlights:

| Command | Purpose |
|---|---|
| `codeindex scan-all` | Generate / refresh `README_AI.md` indexes (structural + optional AI) |
| `codeindex graph-export` | Emit the entities + edges NDJSON that LoomGraph consumes |
| `codeindex parse <file>` | Single-file JSON parse for tool integration |
| `codeindex symbols` | Global symbol index (`PROJECT_SYMBOLS.md`) |
| `codeindex tech-debt <dir>` | Code-quality analysis (large files, god classes, test smells) — see [guide](docs/guides/tech-debt-analysis.md) |
| `codeindex affected --since HEAD~5` | Git change-impact (affected directories) |
| `codeindex doctor` | Health/sync check (CLI, parsers, CLAUDE.md, plugin) |
| `codeindex claude-md update` | Refresh the codeindex section in your project's `CLAUDE.md` |

Each command emits JSON (`--output json`) for CI/CD and downstream tools.

---

## Language support

| Language | Status | Since |
|----------|--------|-------|
| Python | ✅ | v0.1.0 |
| PHP | ✅ | v0.5.0 |
| Java | ✅ | v0.7.0 |
| TypeScript / JS | ✅ | v0.19.0 |
| Swift | ✅ | v0.21.0 |
| Objective-C | ✅ | v0.21.0 |
| Go / Rust / C# | 📋 Planned | — |

**Framework route extraction**: ThinkPHP (PHP), Spring Boot (Java); Express, Laravel, FastAPI, Django planned.

**Want to add a language?** The template-based test system lets you contribute by writing YAML specs — no Python knowledge required. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## How it works

codeindex's documentation generation is a **two-phase pipeline** — structure is deterministic (tree-sitter, no AI), AI enrichment is an optional overlay. The `graph-export` NDJSON (the LoomGraph seam) is pure AST. Full pipeline + architecture diagrams: [`docs/architecture/design-philosophy.md`](docs/architecture/design-philosophy.md).

---

## For LoomGraph developers

If you work on LoomGraph (the user-facing product), start here: **[FOR_LOOMGRAPH.md](FOR_LOOMGRAPH.md)** — the parser-engine contract, the graph-export NDJSON seam, and the codeindex commands you'll touch.

---

## Documentation

### User guides

| Guide | Description |
|---|---|
| [Getting started](docs/guides/getting-started.md) | Installation and first scan |
| [Configuration](docs/guides/configuration.md) | All config options explained |
| [Advanced usage](docs/guides/advanced-usage.md) | Parallel scanning, custom prompts |
| [Git hooks integration](docs/guides/git-hooks-integration.md) | Automated quality checks and doc updates |
| [Claude Code integration](docs/guides/claude-code-integration.md) | AI agent setup and MCP skills |
| [JSON output integration](docs/guides/json-output-integration.md) | Machine-readable output for tools |
| [Tech-debt analysis](docs/guides/tech-debt-analysis.md) | Code-quality analysis command reference |
| [LoomGraph integration](docs/guides/loomgraph-integration.md) | The graph-export → graph-store pipeline |

### Developer & architecture

| Doc | Description |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup, TDD workflow, code style |
| [Design philosophy](docs/architecture/design-philosophy.md) | Two-phase pipeline, two-repo architecture, design principles |
| [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) | Navigation-contract disclaimer + README size cap |
| [ADR-009](docs/architecture/adr/009-codeindex-loomgraph-parser-engine.md) | codeindex = LoomGraph parser engine positioning |
| [Release automation](docs/development/QUICK_START_RELEASE.md) | 5-minute automated release workflow |

### Evidence & benchmarks

| Doc | What it shows |
|---|---|
| [2026-05 README impact benchmark](docs/benchmark/2026-05-readme-impact.md) | Agent comprehension delta WITH vs WITHOUT `README_AI.md` (15 graded questions, 3 projects). Headline: 19% faster / 28% fewer tokens on average, but quality wash on some detail questions — fix shipped (ADR-005). |
| [`bench/`](bench/) | Reproducible harness (`make setup && make run && make grade && make report`). |

---

## Contributing

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[dev,all]"
make install-hooks
make test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Maintainer release: `make release VERSION=0.X.0` (CI → tests → PyPI publish → GitHub Release).

---

## Roadmap

**Current version**: v0.40.0

**Next**: framework routes expansion (Express, Laravel, FastAPI, Django); Go, Rust, C# language support.

Code similarity search, refactoring suggestions, team collaboration, and IDE integration live in [LoomGraph](https://github.com/dreamlx/LoomGraph), not here — codeindex stays the stateless parse layer.

See [Strategic Roadmap](docs/planning/ROADMAP.md) for detailed plans.

---

## License

[MIT](LICENSE) — free, and meant to stay that way.

## Support

- **Questions**: [GitHub Discussions](https://github.com/dreamlx/codeindex/discussions)
- **Bugs / Feature requests**: [GitHub Issues](https://github.com/dreamlx/codeindex/issues)
