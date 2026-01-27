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
# AI CLI command to use for generating documentation
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# List of patterns to include for scanning
include:
  - src/

# List of patterns to exclude from scanning
exclude:
  - "**/test/**"
  - "**/__pycache__/**"

# Supported languages
languages:
  - python
  - php

# Output filename
output_file: "README_AI.md"

# AI Enhancement Settings (NEW)
ai_enhancement:
  strategy: "selective"     # "selective" | "all"
  enabled: true
  size_threshold: 40960     # >40KB triggers AI enhancement

  # Parallel processing settings
  max_concurrent: 2         # Maximum parallel AI calls
  rate_limit_delay: 1.0     # Seconds between AI calls
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
# Two-phase processing with AI enhancement (NEW)
codeindex scan-all                # Uses ai_enhancement strategy from config
codeindex scan-all --ai-all       # Enhance ALL directories with AI
codeindex scan-all --no-ai        # Use SmartWriter only (no AI)

# Traditional batch processing
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
codeindex list-dirs | parallel -j 4 codeindex scan {}
```

#### AI Enhancement Strategies

| Command | Behavior | Use Case |
|---------|----------|----------|
| `scan-all` | Uses config `ai_enhancement.strategy` | Smart and efficient |
| `scan-all --ai-all` | Enhances ALL directories with AI | Best quality, more time |
| `scan-all --no-ai` | SmartWriter only | Fast, no AI costs |

**Example output with AI enhancement:**
```
📝 Phase 1: Generating READMEs (SmartWriter)...
✓ Application ( 50KB)
✓ Admin ( 20KB)
✓ api ( 15KB)
→ Phase 1 complete: 3 directories

🤖 Phase 2: AI Enhancement...
→ Checklist: 3 directories (1 overview, 2 oversize)
✓ Application: AI enhanced (50KB → 22KB)
✓ api: AI enhanced (15KB → 7KB)
→ Completed: 3 directories, 2 AI enhanced
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

### 6. Analyze Technical Debt

**NEW in v0.2.1**: Detect code quality issues and technical debt patterns.

```bash
# Analyze directory for technical debt
codeindex tech-debt ./src

# Output formats
codeindex tech-debt ./src --format console   # Human-readable (default)
codeindex tech-debt ./src --format markdown  # Documentation
codeindex tech-debt ./src --format json      # API/scripting

# Save to file
codeindex tech-debt ./src --output debt_report.md

# Recursive analysis
codeindex tech-debt ./src --recursive

# Quiet mode (minimal output)
codeindex tech-debt ./src --quiet
```

**What it detects:**
- 🔴 **Super large files** (>5000 lines) - CRITICAL
- 🟡 **Large files** (>2000 lines) - HIGH
- 🔴 **God Classes** (>50 methods) - CRITICAL
- 🟡 **Symbol overload** (>100 symbols) - CRITICAL
- 🟠 **High noise ratio** (>50% low-quality symbols) - HIGH

**Example output:**
```
══════════════════════════════════════
  Technical Debt Report
══════════════════════════════════════

Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files analyzed: 15
Issues found: 3
Quality Score: 78.3/100

Severity Breakdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: 1
HIGH: 2
MEDIUM: 0
LOW: 0

File Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 src/models/user.py (Quality: 70.0)
  🔴 CRITICAL - super_large_file
     File has 6000 lines (threshold: 5000)
     → Split into 3-5 smaller files
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

## ⚙️ Configuration Reference

### Complete `.codeindex.yaml`

```yaml
codeindex: 1

# AI CLI command (required)
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Directory patterns
include:
  - src/                # Include all subdirectories recursively
  - modules/

exclude:
  - "**/test/**"
  - "**/__pycache__/**"
  - "**/node_modules/**"

# Language support
languages:
  - python
  - php

# Output settings
output_file: "README_AI.md"
parallel_workers: 8
batch_size: 50

# Smart indexing (generates tiered documentation)
indexing:
  max_readme_size: 51200
  root_level: "overview"
  module_level: "navigation"
  leaf_level: "detailed"

# AI Enhancement (NEW - for scan-all command)
ai_enhancement:
  strategy: "selective"      # "selective" | "all"
  enabled: true
  size_threshold: 40960      # >40KB triggers AI

  # Rate limiting and concurrency
  max_concurrent: 2          # Max parallel AI calls
  rate_limit_delay: 1.0      # Delay between calls

# Incremental updates
incremental:
  enabled: true
  thresholds:
    skip_lines: 5
    current_only: 50
    suggest_full: 200
```

---

## 🤖 Claude Code Integration

codeindex generates `README_AI.md` files that are perfect for [Claude Code](https://claude.ai/code) to understand your project architecture. By adding a `CLAUDE.md` file to your project, you can guide Claude Code to use these indexes effectively.

### Why Use CLAUDE.md?

Without guidance, Claude Code might:
- ❌ Blindly search through all source files (slow and inefficient)
- ❌ Miss important architectural context
- ❌ Use Glob/Grep instead of semantic understanding

With `CLAUDE.md`, Claude Code will:
- ✅ Read `README_AI.md` files first (fast and structured)
- ✅ Understand your project architecture before diving into code
- ✅ Use Serena MCP tools for precise symbol navigation

### Quick Setup

**1. Copy the template to your project:**

```bash
# After running codeindex scan-all
cp examples/CLAUDE.md.template CLAUDE.md
```

**2. Customize the project-specific sections:**

Edit the "Project Specific Configuration" section in your `CLAUDE.md` to document your project structure, key components, and development guidelines.

**3. Commit and push:**

```bash
git add CLAUDE.md README_AI.md **/README_AI.md
git commit -m "docs: add Claude Code integration"
```

### What's Included in the Template

The template includes guidance for Claude Code to:

1. **Prioritize README_AI.md files** when understanding architecture
2. **Use Serena MCP tools** (find_symbol, find_referencing_symbols) for precise navigation
3. **Follow a structured workflow**: README → find_symbol → read source → analyze dependencies
4. **Avoid inefficient patterns** like Glob/Grep searches

### Example Workflow

After setup, when you ask Claude Code about your project:

```
❌ Without CLAUDE.md:
You: "Where is the authentication module?"
Claude: [Uses Glob to search for "auth*"]
        [Scans 50 files, wastes time]

✅ With CLAUDE.md:
You: "Where is the authentication module?"
Claude: [Reads /src/README_AI.md]
        [Reads /src/auth/README_AI.md]
        "The authentication module is in src/auth/authenticator.py:15
         with UserAuthenticator class..."
```

### Advanced Integration: MCP Skills

codeindex also includes MCP skills for Claude Code:

| Skill | Description |
|-------|-------------|
| `/mo:arch` | Query code architecture using README_AI.md indexes |
| `/mo:index` | Generate repository index with codeindex |

**Install skills:**

```bash
# Navigate to codeindex directory
cd /path/to/codeindex

# Run install script
./skills/install.sh
```

### Full Documentation

- **User Guide**: [docs/guides/claude-code-integration.md](docs/guides/claude-code-integration.md)
- **Template File**: [examples/CLAUDE.md.template](examples/CLAUDE.md.template)
- **Skills Documentation**: [skills/README.md](skills/README.md)

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
