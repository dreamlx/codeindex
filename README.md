# codeindex

[🇬🇧 English](README.md) | [🇨🇳 中文](README_zh.md)

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

**Enterprise-grade Code Intelligence Platform — Make AI agents understand your codebase through semantic navigation, not grep.**

codeindex generates AI-readable documentation with **two-phase pipeline**: structural indexing (AST parsing via tree-sitter) + AI-powered module descriptions. AI agents can browse README_AI.md hierarchy, see module purposes at a glance, and navigate directly to the right code — across Python, PHP, Java, TypeScript, JavaScript, Swift, and Objective-C. Designed for **enterprise environments** with intranet isolation.

**🏢 Enterprise Ready**: ✅ Intranet compatible ✅ Self-contained ✅ Version stable ✅ Data sovereignty

---

> **For LoomGraph Developers**: [`FOR_LOOMGRAPH.md`](FOR_LOOMGRAPH.md) (quick start) | [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) (full guide)

---

## Features

### Core: Code Understanding for AI Agents

- **Two-phase documentation pipeline** (v0.23.0) — Phase 1: structural README_AI.md via SmartWriter; Phase 2: AI generates one-line functional descriptions per module. AI agents can browse README_AI.md hierarchy and find the right module **without grep**.
- **Smart indexing** — Tiered documentation (overview → navigation → detailed) optimized for AI agents, ≤50KB per file
- **Auto-AI enrichment** — When `ai_command` is configured, `scan-all` automatically enables AI module descriptions. Use `--no-ai` to opt out
- **Auto-update hooks** — Post-commit hook automatically regenerates README_AI.md for changed directories. Thin wrapper pattern: `pip upgrade` auto-updates hook logic

### Parsing & Analysis

- **Multi-language AST parsing** — Python, PHP, Java, TypeScript, JavaScript, Swift, Objective-C via tree-sitter (Go, Rust, C# planned)
- **Call relationship extraction** — Function/method call graphs across Python, Java, PHP, TypeScript, JavaScript
- **Inheritance extraction** — Class hierarchy and interface relationships
- **Framework route extraction** — ThinkPHP and Spring Boot route tables (more planned)
- **Technical debt analysis** — Detect large files, god classes, symbol overload, test smells
- **Single file parse** — `codeindex parse <file>` with JSON output for tool integration
- **Structured JSON output** — `--output json` for CI/CD, knowledge graphs, and downstream tools

### Developer Experience

- **Adaptive symbol extraction** — Dynamic 5–150 symbols per file based on size
- **CLAUDE.md injection** — `codeindex init` auto-configures Claude Code integration
- **Auto-update guide** — Post-install hook automatically updates `~/.claude/CLAUDE.md` after `pip upgrade`
- **Template-based test generation** — YAML + Jinja2 for rapid language support (88–91% time savings)
- **Parallel scanning** — Concurrent directory processing with configurable workers

---

## Use Cases

### 🏢 Enterprise Intranet (Core Scenario)

**Without external tools**: When Serena MCP or other cloud-based code intelligence tools are unavailable due to network isolation or security policies, codeindex becomes the **primary code understanding tool**.

```bash
# Enterprise developer workflow
git clone <internal-repo>
codeindex init                       # Configure project
codeindex scan-all                   # Structural + AI descriptions (auto)
# AI agent reads README_AI.md → sees module purposes → navigates directly
# No grep needed for code discovery
codeindex tech-debt src/ --output review.md  # Code quality analysis
```

**Why enterprises choose codeindex**:
- ✅ **Semantic navigation** — AI agents understand module purposes from README_AI.md hierarchy
- ✅ **Intranet compatible** — no external dependencies, fully offline
- ✅ **Self-contained** — no upstream MCP servers required
- ✅ **Version stable** — enterprise-controlled release cycle
- ✅ **Data sovereignty** — code never leaves internal network

---

### 🕸️ Knowledge Graph Integration (LoomGraph)

**For enterprise teams**: codeindex serves as the **core data source** for [LoomGraph](https://github.com/dreamlx/LoomGraph) knowledge graphs, enabling semantic code search across the organization.

```bash
# Data pipeline
codeindex scan --output json > parse_results.json
loomgraph inject parse_results.json  # Build knowledge graph
# Team can now search code using natural language
```

**Three-repo architecture**:
```
codeindex (Parse)  →  LoomGraph (Orchestrate)  →  LightRAG (Store)
   ↓ ParseResult         ↓ Embeddings              ↓ Semantic Search
   AST extraction        Knowledge Graph           Vector + Graph DB
```

Without codeindex, LoomGraph cannot function. See [LoomGraph Integration Guide](docs/guides/loomgraph-integration.md).

---

### 👤 Personal Developers (Complementary)

**With Serena MCP**: For individual developers using Claude Code + Serena MCP, codeindex provides **complementary value**:

- **codeindex** (build-time): Semantic architecture map (README_AI.md with module descriptions) + quality analysis
- **Serena** (real-time): Precise symbol navigation (`find_symbol`, `find_referencing_symbols`)

```bash
# Personal developer workflow
codeindex init                    # Setup CLAUDE.md integration
codeindex scan-all                # Structural + AI descriptions (auto)
codeindex hooks install post-commit  # Auto-update on commit
# Claude Code reads README_AI.md → understands module purpose → uses Serena for details
```

**Relationship**: codeindex provides the "map with labels," Serena provides the "GPS navigation."

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
pip install ai-codeindex[typescript]
pip install ai-codeindex[python,php]
pip install ai-codeindex[swift]
pip install ai-codeindex[ios]          # Swift + Objective-C
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
# Scan all directories
# When ai_command is configured → auto Phase 1 (structural) + Phase 2 (AI descriptions)
# Without ai_command → Phase 1 only (structural)
codeindex scan-all

# Structural only (skip AI enrichment)
codeindex scan-all --no-ai

# Scan a single directory
codeindex scan ./src/auth

# Full AI-generated README for a single directory
codeindex scan ./src/auth --ai

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
| `codeindex tech-debt ./src` | Code quality analysis (debt + test smells) | Enhanced in v0.22.0 |
| `codeindex debt-scan ./src` | Alias for tech-debt | Backward compatibility |
| `codeindex hooks install` | Git hooks for auto-update | [Git Hooks Guide](docs/guides/git-hooks-integration.md) |
| `codeindex config explain <param>` | Parameter help | [Configuration Guide](docs/guides/configuration.md) |

---

## Claude Code Integration (Personal Developers)

**For personal developers using Claude Code + Serena MCP**:

**v0.17.0**: `codeindex init` automatically injects instructions into your project's `CLAUDE.md`, so Claude Code reads `README_AI.md` files first — no manual setup required.

```bash
# One command sets everything up
codeindex init

# Claude Code will now:
# ✅ Read README_AI.md for architecture understanding
# ✅ Use Serena MCP tools for precise navigation (find_symbol, etc.)
# ✅ Apply tech-debt analysis for code quality checks
```

**For enterprise users without Serena**: README_AI.md and PROJECT_SYMBOLS.md become your **primary code navigation tools**.

For manual setup, MCP skills (`/mo:arch`, `/mo:index`), and Git hooks integration, see the [Claude Code Integration Guide](docs/guides/claude-code-integration.md).

---

## Language Support

| Language | Status | Since | Key Features |
|----------|--------|-------|-------------|
| Python | ✅ Supported | v0.1.0 | Classes, functions, methods, imports, docstrings, inheritance, calls |
| PHP | ✅ Supported | v0.5.0 | Classes (extends/implements), methods, properties, PHPDoc, inheritance, calls |
| Java | ✅ Supported | v0.7.0 | Classes, interfaces, enums, records, annotations, Spring routes, Lombok, calls |
| TypeScript/JS | ✅ Supported | v0.19.0 | Classes, interfaces, enums, type aliases, arrow functions, JSX/TSX, imports/exports, calls |
| Swift | ✅ Supported | v0.21.0 | Classes, structs, enums, protocols, extensions, methods, properties |
| Objective-C | ✅ Supported | v0.21.0 | Classes, protocols, categories, properties, methods (instance/class) |
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

## Code Quality Analysis

### tech-debt: Comprehensive Quality Analysis (Enhanced in v0.22.0)

The `tech-debt` command provides comprehensive code quality analysis, now including test smells detection:

```bash
# JSON output (for LoomGraph integration)
codeindex tech-debt ./src --format json > debt-data.json

# Markdown report (for documentation)
codeindex tech-debt ./src --format markdown > report.md

# Console output (for quick checks)
codeindex tech-debt ./src --format console

# Alias: debt-scan also works (backward compatibility)
codeindex debt-scan ./src --format json
```

**What it detects**:
- 🔴 **Super large files** (>5000 lines), **Large files** (>2000 lines)
- 🔴 **God Classes** (>50 methods)
- 🔴 **Long methods** (>80/150 lines)
- 🟡 **High coupling** (>8 internal imports)
- 🟡 **Symbol overload** (>100 symbols, high noise ratio)
- 🧪 **Test smells** (skipped tests, giant test files) — **New in v0.22.0**
- 📊 **Quality scoring** (0-100 scale per file)

**Enhanced JSON output (v0.22.0)**:
```json
{
  "timestamp": "2026-03-06T13:45:39Z",
  "summary": {
    "total_files": 97,
    "giant_files": 0,
    "giant_functions": 3,
    "test_smells": 64,
    "avg_maintainability": 9.9
  },
  "total_files": 97,
  "average_quality_score": 99.4,
  "giant_files": [],
  "giant_functions": [...],
  "test_smells": [
    {
      "path": "tests/test_example.py",
      "type": "skipped_test",
      "details": "Skipped test detected: @pytest.mark.skip at line 42",
      "line_number": 42
    }
  ],
  "file_reports": [...]
}
```

**Key features**:
- ✅ **Unified command**: Single entry point for all quality checks
- ✅ **Backward compatible**: All existing JSON fields preserved
- ✅ **LoomGraph ready**: Enhanced summary for knowledge graph integration
- ✅ **Framework-agnostic**: Detects test smells across Jest, pytest, JUnit, etc.
- ✅ **KISS design**: 90% code reuse, simple regex patterns for test detection

---

## How It Works

### Two-Phase Pipeline (v0.23.0)

```
Phase 1 (Structural):
  Directory → Scanner → Parser (tree-sitter) → SmartWriter → README_AI.md

Phase 2 (AI Enrichment, automatic when ai_command configured):
  README_AI.md → symbol names + file names → AI → one-line description → blockquote injection
```

**Phase 1: Structural generation** (always runs)
1. **Scanner** — walks directories, filters by config patterns
2. **Parser** — extracts symbols (classes, functions, imports, calls, inheritance) via tree-sitter
3. **SmartWriter** — generates tiered documentation with size limits (≤50KB)
4. **Output** — `README_AI.md` optimized for AI consumption, or JSON for tool integration

**Phase 2: AI enrichment** (auto-enabled when `ai_command` configured)
- Generates a one-line functional description for each non-leaf module
- Writes as blockquote: `> 会员等级管理、积分兑换、权益卡券`
- ~200-400 tokens per directory, 10-20x cheaper than full AI generation
- Parent directories read child descriptions for hierarchical navigation

### Before vs After: Code Navigation

```
Before (structural only):
  └── Application/
      ├── Vip/           — 48 files | 386 symbols     ← AI agent cannot determine purpose
      ├── Pay/           — 23 files | 178 symbols
      └── SmallProgramApi/ — 31 files | 245 symbols

After (structural + AI enrichment):
  └── Application/
      ├── Vip/           — 会员等级管理、积分兑换、权益卡券 | 48 files
      ├── Pay/           — 支付网关（支付宝/微信/退款） | 23 files
      └── SmallProgramApi/ — 小程序端API（登录、头像、商品） | 31 files
                             ↑ AI agent can navigate directly
```

### Three-Repo Architecture (Enterprise Knowledge Graph)

```
┌────────────────────────────────────────────────────┐
│            Enterprise Intranet Environment          │
├────────────────────────────────────────────────────┤
│                                                    │
│  📦 Code Repository (Git)                          │
│       ↓                                            │
│  🔍 codeindex (Parse Layer)                        │
│       ├── scan --output json → ParseResult         │
│       ├── README_AI.md → architecture docs         │
│       └── tech-debt → comprehensive quality scan   │
│       ↓                                            │
│  🕸️ LoomGraph (Orchestration Layer)                │
│       ├── inject ParseResult                       │
│       ├── generate embeddings                      │
│       └── build knowledge graph                    │
│       ↓                                            │
│  💾 LightRAG (Storage Layer)                       │
│       ├── PostgreSQL (graph data)                  │
│       ├── Vector DB (embeddings)                   │
│       └── Query API (semantic search)              │
│       ↓                                            │
│  💬 AI Agents (Claude Code, Internal Chat)         │
│       └── Natural language code search             │
│                                                    │
└────────────────────────────────────────────────────┘
```

**codeindex role**: Bottom layer (data collection & parsing) — the entire system depends on codeindex providing structured ParseResult data.

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

**Current version**: v0.23.0

**Recent milestones**:
- v0.23.0 — **AI-Enhanced Module Descriptions**: two-phase pipeline, auto-AI enrichment, post-commit thin wrapper
- v0.22.2 — Auto-update CLAUDE.md on `pip upgrade`, `/codeindex-update-guide` skill
- v0.22.0 — Unified tech-debt + test smells analysis
- v0.21.0 — Swift & Objective-C language support
- v0.19.0 — TypeScript/JavaScript support with call extraction

**Next**:
- Framework routes expansion: Express, Laravel, FastAPI, Django (Epic 17)
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
