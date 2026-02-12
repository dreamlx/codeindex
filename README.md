# codeindex

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

**Universal Code Parser — Best-in-class multi-language AST parser for AI-assisted development.**

codeindex extracts symbols, inheritance relationships, call graphs, and imports from Python, PHP, and Java using tree-sitter. Perfect for feeding structured code data to AI tools, knowledge graphs, and code intelligence platforms.

---

> **For LoomGraph Developers**: [`FOR_LOOMGRAPH.md`](FOR_LOOMGRAPH.md) (quick start) | [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) (full guide)

---

## Features

- **Multi-language AST parsing** — Python, PHP, Java via tree-sitter (TypeScript, Go, Rust, C# planned)
- **AI-powered documentation** — Generate README files using Claude, GPT, or any AI CLI
- **Single file parse** — `codeindex parse <file>` with JSON output for tool integration
- **Structured JSON output** — `--output json` for CI/CD, knowledge graphs, and downstream tools
- **Call relationship extraction** — Function/method call graphs across Python, Java, PHP
- **Inheritance extraction** — Class hierarchy and interface relationships
- **Framework route extraction** — ThinkPHP and Spring Boot route tables (more planned)
- **Technical debt analysis** — Detect large files, god classes, symbol overload
- **Smart indexing** — Tiered documentation (overview → navigation → detailed) optimized for AI agents
- **Adaptive symbol extraction** — Dynamic 5–150 symbols per file based on size
- **CLAUDE.md injection** — `codeindex init` auto-configures Claude Code integration (v0.17.0)
- **Template-based test generation** — YAML + Jinja2 for rapid language support (88–91% time savings)
- **Parallel scanning** — Concurrent directory processing with configurable workers

---

## Installation

codeindex uses **lazy loading** — language parsers are only imported when needed.

### Quick Install

```bash
# All languages (recommended)
pip install ai-codeindex[all]

# Or specific languages only
pip install ai-codeindex[python]
pip install ai-codeindex[php]
pip install ai-codeindex[java]
pip install ai-codeindex[python,php]
```

### Using pipx (Recommended for CLI use)

```bash
pipx install ai-codeindex[all]
```

### From Source

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"
```

---

## Quick Start

### 1. Initialize Your Project

```bash
cd /your/project
codeindex init
```

This creates:
- `.codeindex.yaml` — scan configuration (languages, include/exclude patterns)
- `CLAUDE.md` — injects codeindex instructions so Claude Code uses README_AI.md automatically
- `CODEINDEX.md` — project-level documentation reference

### 2. Scan Your Codebase

```bash
# Scan all directories (structural documentation, no AI needed)
codeindex scan-all

# Scan a single directory
codeindex scan ./src/auth

# AI-enhanced documentation (requires ai_command in config)
codeindex scan-all --ai

# Preview AI prompt without executing
codeindex scan ./src/auth --ai --dry-run
```

### 3. Check Status

```bash
codeindex status
```

```
Indexing Status
───────────────────────────────
✅ src/auth/
✅ src/utils/
⚠️  src/api/ (no README_AI.md)
Indexed: 2/3 (67%)
```

### 4. Generate Indexes

```bash
# Global symbol index (PROJECT_SYMBOLS.md)
codeindex symbols

# Module overview (PROJECT_INDEX.md)
codeindex index

# Git change impact analysis
codeindex affected --since HEAD~5
```

### More Commands

| Command | Description | Guide |
|---------|-------------|-------|
| `codeindex scan --output json` | JSON output for tools | [JSON Output Guide](docs/guides/json-output-integration.md) |
| `codeindex parse <file>` | Parse single file to JSON | [LoomGraph Integration](docs/guides/loomgraph-integration.md) |
| `codeindex tech-debt ./src` | Technical debt analysis | [Advanced Usage](docs/guides/advanced-usage.md) |
| `codeindex hooks install` | Git hooks for auto-update | [Git Hooks Guide](docs/guides/git-hooks-integration.md) |
| `codeindex config explain <param>` | Parameter help | [Configuration Guide](docs/guides/configuration.md) |

---

## Claude Code Integration

**v0.17.0**: `codeindex init` automatically injects instructions into your project's `CLAUDE.md`, so Claude Code reads `README_AI.md` files first — no manual setup required.

```bash
# One command sets everything up
codeindex init

# Claude Code will now:
# ✅ Read README_AI.md before searching source files
# ✅ Use structured indexes for architecture understanding
# ✅ Navigate code via Serena MCP tools (find_symbol, etc.)
```

For manual setup, MCP skills (`/mo:arch`, `/mo:index`), and Git hooks integration, see the [Claude Code Integration Guide](docs/guides/claude-code-integration.md).

---

## Language Support

| Language | Status | Since | Key Features |
|----------|--------|-------|-------------|
| Python | ✅ Supported | v0.1.0 | Classes, functions, methods, imports, docstrings, inheritance, calls |
| PHP | ✅ Supported | v0.5.0 | Classes (extends/implements), methods, properties, PHPDoc, inheritance, calls |
| Java | ✅ Supported | v0.7.0 | Classes, interfaces, enums, records, annotations, Spring routes, Lombok, calls |
| TypeScript/JS | 🧪 Tests Ready | v0.14.0 | Parser implementation in progress (Epic 15) |
| Go | 📋 Planned | — | Packages, interfaces, struct methods |
| Rust | 📋 Planned | — | Structs, traits, modules |
| C# | 📋 Planned | — | Classes, interfaces, .NET projects |

**Want to add a language?** The template-based test system lets you contribute by writing YAML specs — no Python knowledge required. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Framework Route Extraction

| Framework | Language | Status |
|-----------|----------|--------|
| ThinkPHP | PHP | ✅ Stable (v0.5.0) |
| Spring Boot | Java | ✅ Stable (v0.8.0) |
| Laravel | PHP | 📋 Planned |
| FastAPI | Python | 📋 Planned |
| Django | Python | 📋 Planned |
| Express.js | JS/TS | 📋 Planned |

---

## How It Works

```
Directory → Scanner → Parser (tree-sitter) → Smart Writer → README_AI.md
```

1. **Scanner** — walks directories, filters by config patterns
2. **Parser** — extracts symbols (classes, functions, imports, calls, inheritance) via tree-sitter
3. **Smart Writer** — generates tiered documentation with size limits (≤50KB)
4. **Output** — `README_AI.md` optimized for AI consumption, or JSON for tool integration

---

## Documentation

### User Guides

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Installation and first scan |
| [Configuration Guide](docs/guides/configuration.md) | All config options explained |
| [Advanced Usage](docs/guides/advanced-usage.md) | Parallel scanning, custom prompts |
| [Git Hooks Integration](docs/guides/git-hooks-integration.md) | Automated quality checks and doc updates |
| [Claude Code Integration](docs/guides/claude-code-integration.md) | AI agent setup and MCP skills |
| [JSON Output Integration](docs/guides/json-output-integration.md) | Machine-readable output for tools |
| [LoomGraph Integration](docs/guides/loomgraph-integration.md) | Knowledge graph data pipeline |

### Developer Guides

| Guide | Description |
|-------|-------------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup, TDD workflow, code style |
| [CLAUDE.md](CLAUDE.md) | Quick reference for Claude Code and contributors |
| [Design Philosophy](docs/architecture/design-philosophy.md) | Core design principles and architecture |
| [Release Automation](docs/development/QUICK_START_RELEASE.md) | 5-minute automated release workflow |
| [Multi-Language Support](docs/development/multi-language-support-workflow.md) | Adding new language parsers |
| [Language Support Contribution](docs/development/multi-language-support-workflow.md) | Template-based test generation for new languages |

### Planning

- [Strategic Roadmap](docs/planning/ROADMAP.md) — long-term vision and priorities
- [Changelog](CHANGELOG.md) — version history and breaking changes

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[dev,all]"
make install-hooks
make test
```

### Release Process (Maintainers)

```bash
make release VERSION=0.17.0
# GitHub Actions: tests → PyPI publish → GitHub Release
```

See [Release Automation Guide](docs/development/QUICK_START_RELEASE.md) for details.

---

## Roadmap

**Current version**: v0.17.2

**Recent milestones**:
- v0.17.0 — CLAUDE.md injection via `codeindex init`
- v0.16.0 — CLI UX restructuring (structural mode default, `--ai` opt-in)
- v0.15.0 — Template-based test architecture migration
- v0.14.0 — Interactive setup wizard, single file parse, parser modularization

**Next**:
- Framework routes expansion: Express, Laravel, FastAPI, Django (Epic 17)
- TypeScript parser implementation (Epic 15)
- Go, Rust, C# language support

**Moved to [LoomGraph](https://github.com/dreamlx/LoomGraph)**:
- Code similarity search, refactoring suggestions, team collaboration, IDE integration

See [Strategic Roadmap](docs/planning/ROADMAP.md) for detailed plans.

---

## License

MIT License — see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [tree-sitter](https://tree-sitter.github.io/) — fast, incremental parsing
- [Claude CLI](https://github.com/anthropics/claude-cli) — AI integration inspiration
- All contributors and users

## Support

- **Questions**: [GitHub Discussions](https://github.com/dreamlx/codeindex/discussions)
- **Bugs**: [GitHub Issues](https://github.com/dreamlx/codeindex/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/dreamlx/codeindex/issues/new?labels=enhancement)

---

<p align="center">
  Made with ❤️ by the codeindex team
</p>
