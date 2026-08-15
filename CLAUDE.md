# CLAUDE.md

**For**: Claude Code working with this repository
**Version**: v0.25.0 (in progress)

> **Distribution** (ADR-006): codeindex ships as two artifacts — the
> `ai-codeindex` CLI (PyPI, `pipx install ai-codeindex`) and the
> `dreamlx/codeindex-claude` Claude Code plugin (skills + hooks). The CLI
> wheel must never mutate `~/.claude/*` at install time. End users install
> via pipx; Claude Code users add the plugin.

> **Product positioning (2026-07, ADR-009)**: codeindex is the **parser engine** for
> [LoomGraph](https://github.com/dreamlx/LoomGraph) — the "see" layer (tree-sitter AST →
> structural slice → `graph-export` NDJSON). LoomGraph is the **user-facing product** (the
> "think + remember" layer: SQLite + sqlite-vec graph store, vector retrieval, MCP server,
> `impact`/`deps`/`topology`, skills). End users install LoomGraph (`pipx install loomgraph`),
> which pulls `ai-codeindex` as a dependency; `loomgraph index` runs the full pipeline
> (graph-export → embed → inject) — users never operate codeindex directly. codeindex is
> also usable standalone for `README_AI.md` navigation indexes without the graph layer.
> **Two repos, one product from the user's view.** Methodology role (the "see" instance of
> the agent-native middleware thesis) is decoupled from product form.

---

## Part 1: Understanding & Navigating

### Code Navigation Priority

1. `/README_AI.md` → Project overview
2. Serena `find_symbol()` → Precise symbol location
3. `/src/codeindex/README_AI.md` → Core module details
4. Serena `find_referencing_symbols()` → Call relationships

### Key Files

| File | Purpose |
|------|---------|
| `README_AI.md` | AI-generated directory docs |
| `PROJECT_SYMBOLS.md` | Global symbol index |
| `.codeindex.yaml` | Scan configuration |
| `CHANGELOG.md` | Version history |
| `docs/planning/*.md` | Epic/Story design decisions |
| `docs/architecture/design-philosophy.md` | Core design principles |

### Serena MCP Quick Reference

```python
find_symbol(name_path_pattern="SmartWriter/write_readme")
find_referencing_symbols(name_path="calculate_limit", relative_path="src/codeindex/adaptive_selector.py")
get_symbols_overview(relative_path="src/codeindex/parser.py", depth=1)
```

---

## Part 2: Development Workflow

### Virtual Environment (REQUIRED)

```bash
source .venv/bin/activate
which python3  # Must show .venv path
pip install -e ".[dev,all]"
```

Without venv: pip fails (PEP 668), pre-push hooks fail (`ModuleNotFoundError`), `make release` fails.

### Quick Start Commands

```bash
# Development
pytest -m "not slow"               # Fast tests only (~2s, daily use)
pytest -v                          # Full test suite (~7s, before PR)
ruff check src/                    # Lint
pytest --cov=src/codeindex         # Coverage

# codeindex usage
codeindex scan-all                 # Generate all indexes (structural)
codeindex scan-all --ai            # + AI enrichment; ok results cached, only new/failed dirs hit AI
codeindex scan-all --ai --retry-all # Force re-enrich every dir, ignoring cache
codeindex parse src/myfile.py      # Parse single file
codeindex symbols                  # Global symbol index
codeindex tech-debt ./src          # Code quality analysis
codeindex hooks status             # Git hooks status
```

### Commit Message Format

```
feat(scope): add new feature
fix(scope): fix bug
docs(scope): update documentation
test(scope): add tests
refactor(scope): refactor code
```

### Documentation Update Rules

| Change Type | Documents to Update |
|-------------|---------------------|
| New feature | CHANGELOG.md, README.md, relevant README_AI.md |
| Bug fix | CHANGELOG.md |
| Config change | .codeindex.yaml example, CHANGELOG.md |
| Major release | CHANGELOG.md, docs/releases/RELEASE_NOTES_vX.X.X.md |

**CHANGELOG vs RELEASE_NOTES policy**: `CHANGELOG.md` is the mandatory,
complete, every-release ledger (terse, categorized — the "what changed"
lookup). `docs/releases/RELEASE_NOTES_vX.Y.Z.md` is **optional**, written only
for a major / breaking / announced release — a curated narrative + migration
guide that doubles as the public announcement. A patch or routine minor needs
no RELEASE_NOTES; writing one per version is ceremony. The pre-release gate
(`scripts/pre_release_check.sh`) enforces CHANGELOG and only *warns* on a
missing RELEASE_NOTES.

After code changes: `codeindex scan-all`

### Epic Completion Workflow

1. Update `docs/planning/ROADMAP.md` (version + epic status)
2. Archive: `docs/planning/active/ → docs/planning/completed/`
3. Update `docs/planning/README.md` index

---

## Part 2.5: Design Philosophy

Read `docs/architecture/design-philosophy.md` when:
- Adding new language support
- Implementing features involving ParseResult
- Making architectural decisions (AI vs programmatic, parallelization)

**Core principles**:
- We extract structure (What), AI understands semantics (Why)
- 3 layers: Structure Extraction (tree-sitter) → Automated Analysis → AI Enhancement
- AI invocation is the bottleneck (99%), not parsing
- ThreadPool for all languages (I/O bound)

---

## Part 3: Architecture Reference

### Two-Repo Architecture

> codeindex **sees** (AST parsing → structural slice), LoomGraph **thinks + remembers**
> (graph store + vector retrieval + query/MCP)

| Repo | Role | Local Path |
|------|------|------------|
| **codeindex** | AST parsing, Symbol/Call/Inheritance extraction, `graph-export` NDJSON. **Stateless** (ADR-007). | `/Users/dreamlinx/Projects/opensource/codeindex` |
| **LoomGraph** | Graph store + vector retrieval (SQLite + sqlite-vec vec0 KNN), embedding, query/MCP. **Stateful.** | `/Users/dreamlinx/Projects/opensource/loomgraph` |

Data flow: `codeindex graph-export` → NDJSON → `loomgraph import-export` →
`SqliteGraphStore` (SQLite + sqlite-vec).

> **Note**: LightRAG is retired from the runtime. LoomGraph's local refactor
> replaced it with SQLite + sqlite-vec ("no RAG framework needed"); the old
> `codeindex scan → LoomGraph embed → LightRAG API → PostgreSQL` flow no longer
> applies. The graph-export NDJSON contract is the sole seam between the two repos.

### Core Pipeline

```
Directory → Scanner → [files] → Parser (tree-sitter) → [ParseResult]
  → SmartWriter → Writer → Invoker (AI CLI) → README_AI.md
```

### Key Data Types

- `ScanResult`: path, files, subdirs
- `ParseResult`: path, symbols, imports, module_docstring, error
- `Symbol`: name, kind, signature, docstring, line_start, line_end
- `Import`: module, names, is_from
- `Config`: Loaded from `.codeindex.yaml`

### Configuration

```yaml
version: 1
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
include: [src/]
exclude: ["**/__pycache__/**"]
languages: [python, php, java, typescript, javascript, swift, objc]
output_file: README_AI.md

symbols:
  adaptive_symbols:
    enabled: true
```

Full config: `examples/.codeindex.yaml` | Help: `codeindex config explain <param>`

---

## Part 4: Extension Development

### Adding Language/Framework Support

1. Write tests: `tests/extractors/test_myframework.py`
2. Implement: `src/codeindex/extractors/myframework.py`
3. Auto-registered via `extractors/__init__.py`

Reference: `src/codeindex/extractors/thinkphp.py`

### Git Hooks

- pre-commit: lint + debug checks
- pre-push: test validation
- post-commit: **not installed in this repo** (#166) — README_AI refresh is
  release-time, not per-commit; `scripts/release.sh` step 6.5 runs
  `scan-all` + `claude-md update` between version bump commit and tag

Management: `codeindex hooks install/uninstall/status`
Guide: `docs/guides/git-hooks-integration.md`

---

## Historical Decision Notes (non-derivable from code, kept short)

- **graph-export is Path A, independent of render-flip**: `graph-export` does its own clean tree parse per file; it does not depend on or require the README-render path being "flipped". If a future spike justifies render-flip, that's a separate decision on its own merits — don't bundle it just because graph-export shipped.
- **Enrichment quality bugs (leaf-dir punt) root cause pattern**: when `scan-all --ai` enrichment silently punts on leaf directories, first suspect is a **thin prompt** (subdir-only context fed to a prompt that claims richer input), not concurrency — enrichment runs serially, there's no parallel-worker confound. A single non-informative subdirectory can short-circuit the fallback that should otherwise pull in real content. Verify with same-repo git-stash A/B (buggy vs fixed source), and count `<!-- enrichment: ok -->` markers via `find | while read` (not `grep -rl --include`, which can silently short-circuit under BSD grep).
- **graph-export content_hash (schema v1)**: per-symbol content hash added so stale line-number anchors become detectable instead of silently rotting. loomgraph's `export_reader.py` warns (not raises) on unsupported schema versions, so this was fully backward-compatible — no `--schema-version` flag needed.

---

## Common Mistakes

1. **Directly modify README_AI.md** → It gets overwritten. Modify source docstrings instead.
2. **Skip tests** → TDD required. Write tests first.
3. **Glob/Grep for exploration** → Use Serena MCP tools.
4. **Ignore README_AI.md** → Always read it first.
5. **Commit to develop/master directly** → Use feature branches.
6. **Forget venv** → Always `source .venv/bin/activate` first.

<!-- codeindex:start v0.36.0 -->
## codeindex

This project uses [codeindex](https://github.com/dreamlx/codeindex) (v0.36.0) for AI-friendly code documentation.

### Navigation contract

`README_AI.md` is a **navigation index**, not authoritative technical documentation — orient with it ("what/where is X"), then read source via Read/Grep for precise mechanism. Cross-module flows (end-to-end chains spanning ≥2 modules) are out of scope: they live in the host repo's architecture docs / ADRs, never here. Symbol-level queries (calls/references/definitions): Serena MCP (`find_symbol`, `find_referencing_symbols`).

### Commands & escape hatches

Full reference: `codeindex --help`. The non-obvious one:

```bash
codeindex scan-all --ai --retry-all   # force re-enrich every dir, ignore cache
```

Transient AI failures (`⚠ <dir>: AI error`) → re-run `codeindex scan-all --ai`; successes restore from cache, only failures retry. Persistent → swap model in `ai_command` (`.codeindex.yaml`).

### README_AI markers

Each `README_AI.md` header carries: the navigation contract comment, a `Generated by ...` provenance line, and optionally `<!-- enrichment: ok -->` / `<!-- enrichment: failed (reason: ...) -->` (absent = structural-only, never ran `--ai`).

After upgrading codeindex, run `codeindex claude-md update` to refresh this section.

<!-- codeindex:end -->
