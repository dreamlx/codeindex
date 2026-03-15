# CLAUDE.md

**For**: Claude Code working with this repository
**Version**: v0.23.1

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
pytest -v                          # Run tests
ruff check src/                    # Lint
pytest --cov=src/codeindex         # Coverage

# codeindex usage
codeindex scan-all --fallback      # Generate all indexes
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
| Major release | CHANGELOG.md, RELEASE_NOTES_vX.X.X.md |

After code changes: `codeindex scan-all --fallback`

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

### Three-Repo Architecture

> codeindex **sees** (AST parsing), LoomGraph **thinks** (pipeline + skills), LightRAG **remembers** (storage + retrieval)

| Repo | Role | Local Path |
|------|------|------------|
| **codeindex** | AST parsing, Symbol/Call/Inheritance extraction | `/Users/dreamlinx/Projects/codeindex` |
| **LoomGraph** | Pipeline dispatch, Embedding, CLI/Skill | `/Users/dreamlinx/Projects/LoomGraph` |
| **LightRAG** | Graph storage, vector retrieval | `/Users/dreamlinx/Projects/LightRAG` |

Data flow: `codeindex scan` → ParseResult → `LoomGraph embed/inject` → LightRAG API → PostgreSQL

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
- post-commit: auto README updates
- pre-push: test validation

Management: `codeindex hooks install/uninstall/status`
Guide: `docs/guides/git-hooks-integration.md`

---

## Common Mistakes

1. **Directly modify README_AI.md** → It gets overwritten. Modify source docstrings instead.
2. **Skip tests** → TDD required. Write tests first.
3. **Glob/Grep for exploration** → Use Serena MCP tools.
4. **Ignore README_AI.md** → Always read it first.
5. **Commit to develop/master directly** → Use feature branches.
6. **Forget venv** → Always `source .venv/bin/activate` first.
