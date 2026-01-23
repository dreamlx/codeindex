# codeindex

[![PyPI version](https://badge.fury.io/py/codeindex.svg)](https://badge.fury.io/py/codeindex)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/codeindex/workflows/Tests/badge.svg)](https://github.com/yourusername/codeindex/actions)

**AI-native code indexing tool for large codebases.**

codeindex automatically generates intelligent documentation (`README_AI.md`) for your directories using tree-sitter parsing and external AI CLIs. Perfect for understanding large codebases, onboarding new developers, and maintaining living documentation.

---

## ✨ Features

- 🚀 **AI-Powered Documentation**: Generate comprehensive README files using Claude, GPT, or any AI CLI
- 🌳 **Tree-sitter Parsing**: Accurate symbol extraction (classes, functions, methods, imports) for Python (more languages coming)
- ⚡ **Parallel Scanning**: Scan multiple directories concurrently for fast indexing
- 🎯 **Smart Filtering**: Include/exclude patterns with glob support
- 🔧 **Flexible Integration**: Works with any AI CLI tool via configurable commands
- 📊 **Coverage Tracking**: Check which directories have been indexed
- 🎨 **Fallback Mode**: Generate basic documentation without AI

---

## 📦 Installation

### Using pipx (Recommended)

```bash
pipx install codeindex
```

### Using pip

```bash
pip install codeindex
```

### From Source

```bash
git clone https://github.com/yourusername/codeindex.git
cd codeindex
pip install -e .
```

---

## 🚀 Quick Start

### 1. Initialize Configuration

```bash
cd /your/project
codeindex init
```

This creates `.codeindex.yaml` in your project.

### 2. Configure AI CLI

Edit `.codeindex.yaml`:

```yaml
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

include:
  - src/
exclude:
  - "**/test/**"
  - "**/__pycache__/**"

languages:
  - python
  - php

output_file: "README_AI.md"
```

**Other AI CLI examples:**
```yaml
# OpenAI
ai_command: 'openai chat "{prompt}" --model gpt-4'

# Gemini
ai_command: 'gemini "{prompt}"'

# Custom script
ai_command: '/path/to/my-ai-wrapper.sh "{prompt}"'
```

### 3. Scan a Directory

```bash
# Scan single directory
codeindex scan ./src/auth

# Preview prompt without executing
codeindex scan ./src/auth --dry-run

# Generate without AI (fallback mode)
codeindex scan ./src/auth --fallback
```

### 4. Batch Processing

```bash
# List all indexable directories
codeindex list-dirs

# Scan all directories in parallel (4 workers)
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}

# Or with GNU parallel
codeindex list-dirs | parallel -j 4 codeindex scan {}
```

### 5. Check Status

```bash
codeindex status
```

**Output:**
```
Indexing Status
───────────────────────────────────────
✅ src/auth/
✅ src/utils/
⚠️  src/api/ (no README_AI.md)
✅ src/db/

Indexed: 3/4 (75%)
```

---

## 📖 Documentation

- **[Getting Started](docs/guides/getting-started.md)** - Detailed installation and setup
- **[Configuration Guide](docs/guides/configuration.md)** - All config options explained
- **[Advanced Usage](docs/guides/advanced-usage.md)** - Parallel scanning, custom prompts
- **[Contributing](docs/guides/contributing.md)** - Development setup and guidelines
- **[Roadmap](docs/planning/roadmap/2025-Q1.md)** - Future plans and milestones
- **[Architecture](docs/architecture/)** - Design decisions and ADRs
- **[Changelog](CHANGELOG.md)** - Version history

---

## 🤖 Claude Code Integration

codeindex includes skills for [Claude Code](https://claude.ai/code) to enhance your AI-assisted development workflow.

### Install Skills

```bash
# Navigate to codeindex directory
cd /path/to/codeindex

# Run install script
./skills/install.sh
```

### Available Skills

| Command | Description |
|---------|-------------|
| `/mo:arch` | Query code architecture using README_AI.md indexes |
| `/mo:index` | Generate repository index with codeindex |

### Usage Example

After indexing your project:

```
You: /mo:arch Where is the parser implemented?

Claude: Based on README_AI.md, the parser is in src/codeindex/parser.py.
        It uses tree-sitter for AST parsing and extracts Symbol and Import...
```

### CLAUDE.md Integration

Add to your project's `CLAUDE.md`:

```markdown
Each source directory has README_AI.md - read it before modifying code to understand module structure.
```

See [skills/README.md](skills/README.md) for detailed documentation.

---

## 🎯 Use Cases

### 📚 Code Understanding
Generate comprehensive documentation for legacy codebases to help new developers onboard faster.

### 🔍 Codebase Navigation
Create structured overviews of large projects (10,000+ files) for efficient exploration.

### 🤖 AI Agent Integration
Use generated indexes with tools like Claude Code or Cursor for better code context.

### 📝 Living Documentation
Keep documentation up-to-date by regenerating README_AI.md files as code changes.

---

## 🛠️ How It Works

```
Directory → Scanner → Parser (tree-sitter) → Smart Writer → README_AI.md (≤50KB)
```

1. **Scanner**: Walks directories, filters by config patterns
2. **Parser**: Extracts symbols (classes, functions, imports) using tree-sitter
3. **Smart Writer**: Generates tiered documentation with size limits
4. **Output**: Optimized `README_AI.md` for AI consumption

---

## 📐 Smart Indexing Architecture

codeindex generates **tiered documentation** optimized for AI agents:

```
Project Root/
├── PROJECT_INDEX.md (~10KB)     # Overview level
│   └── Module list + descriptions
│
├── Module/
│   └── README_AI.md (~30KB)     # Navigation level
│       ├── Grouped files by type
│       └── Key classes summary
│
└── LeafDir/
    └── README_AI.md (≤50KB)     # Detailed level
        ├── Full symbol info
        └── Dependencies
```

### Configuration

```yaml
indexing:
  max_readme_size: 51200    # 50KB limit
  symbols:
    max_per_file: 15
    include_visibility: [public, protected]
    exclude_patterns: ["get*", "set*"]
  grouping:
    by: suffix
    patterns:
      Controller: "HTTP handlers"
      Service: "Business logic"
      Model: "Data models"
```

---

## 🤖 AI Coder Integration

### For Claude Code Users

Add this to your project's `CLAUDE.md`:

```markdown
## Code Index

This project uses codeindex for AI-friendly documentation.

### How to Read Code Index

1. **Start with overview**: Read `PROJECT_INDEX.md` or root `README_AI.md` to understand project structure
2. **Locate module**: Find the relevant module from the module list
3. **Deep dive**: Read module's `README_AI.md` for file/symbol details
4. **Read source**: Open specific files when you need implementation details

### Index Files

- `README_AI.md` - Directory-level documentation (≤50KB each)
- Each directory with source code has its own README_AI.md

### Example Workflow

Task: "Fix user authentication bug"
1. Read root README_AI.md → Find Auth/User module
2. Read Auth/README_AI.md → Find AuthService.php
3. Read AuthService.php → Understand implementation
```

### Usage Tips

- **Token efficient**: Each README is ≤50KB, suitable for LLM context
- **Progressive loading**: Start from overview, drill down as needed
- **Keep indexes updated**: Run `codeindex scan-all --fallback` after major changes

### CLAUDE.md Template

Copy the template to your project:

```bash
cp /path/to/codeindex/examples/CLAUDE.md.template your-project/CLAUDE.md
```

Or see [examples/CLAUDE.md.template](examples/CLAUDE.md.template) for the full template.

---

## 🌍 Language Support

| Language       | Status          | Parser      | Features |
|----------------|-----------------|-------------|----------|
| Python         | ✅ Supported    | tree-sitter | Classes, functions, methods, imports, docstrings |
| PHP            | ✅ Supported    | tree-sitter | Classes (extends/implements), methods (visibility, static, return types), properties, functions |
| TypeScript/JS  | 🚧 Coming Soon  | tree-sitter | - |
| Java           | 🚧 Planned      | tree-sitter | - |
| Go             | 🚧 Planned      | tree-sitter | - |
| Rust           | 🚧 Planned      | tree-sitter | - |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/guides/contributing.md) for:

- Development setup
- TDD workflow
- Code style guidelines
- How to add new languages
- Release process

### Quick Start for Contributors

```bash
# Clone and install
git clone https://github.com/yourusername/codeindex.git
cd codeindex
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check src/
ruff format src/
```

---

## 📊 Roadmap

See [2025 Q1 Roadmap](docs/planning/roadmap/2025-Q1.md) for detailed plans.

**Upcoming:**
- Multi-language support (TypeScript, Java, Go)
- MCP service integration for Claude Code
- Incremental indexing (only scan changed files)
- Performance optimizations
- Plugin system for custom AI providers

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [tree-sitter](https://tree-sitter.github.io/) - Fast, incremental parsing
- [Claude CLI](https://github.com/anthropics/claude-cli) - AI integration inspiration
- All contributors and users

---

## 📞 Support

- **Questions**: [GitHub Discussions](https://github.com/yourusername/codeindex/discussions)
- **Bugs**: [GitHub Issues](https://github.com/yourusername/codeindex/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/yourusername/codeindex/issues/new?labels=enhancement)

---

## ⭐ Star History

If you find codeindex useful, please star the repository to show your support!

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/codeindex&type=Date)](https://star-history.com/#yourusername/codeindex&Date)

---

<p align="center">
  Made with ❤️ by the codeindex team
</p>
