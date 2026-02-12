# codeindex

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

**Universal Code Parser - Best-in-class multi-language AST parser for AI-assisted development.**

codeindex focuses on **code parsing and structured data extraction** using tree-sitter. It extracts symbols, inheritance relationships, call relationships, and imports from Python, PHP, Java (and more languages coming). Perfect for feeding structured code data to AI tools, knowledge graphs, and code intelligence platforms.

---

> **🤝 For LoomGraph Developers**: Looking to integrate codeindex for code parsing? Start here:
> - **Quick Start**: [`FOR_LOOMGRAPH.md`](FOR_LOOMGRAPH.md) (5 min read)
> - **Complete Guide**: [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) (20 min, with code examples)

---

## ✨ Features

- 🚀 **AI-Powered Documentation**: Generate comprehensive README files using Claude, GPT, or any AI CLI
- 🌳 **Tree-sitter Parsing**: Accurate symbol extraction (classes, functions, methods, imports) for Python, PHP & Java
- 📄 **Single File Parse** (v0.13.0+): Parse individual files with JSON output for loose coupling with downstream tools
- ⚡ **Parallel Scanning**: Scan multiple directories concurrently for fast indexing
- 🎯 **Smart Filtering**: Include/exclude patterns with glob support
- 🔧 **Flexible Integration**: Works with any AI CLI tool via configurable commands
- 📊 **Coverage Tracking**: Check which directories have been indexed
- 🎨 **Fallback Mode**: Generate basic documentation without AI
- 🎯 **KISS Universal Description** (v0.4.0+): Language-agnostic, zero-assumption module descriptions
- 🏗️ **Modular Architecture** (v0.3.1+): Clean, maintainable 6-module CLI design
- 🔄 **Adaptive Symbols** (v0.2.0+): Dynamic symbol extraction (5-150 per file based on size)
- 📈 **Technical Debt Analysis** (v0.3.0+): Detect code quality issues and complexity metrics
- 🔍 **Symbol Indexing** (v0.1.2+): Global symbol search and project-wide navigation
- 🧪 **Template-Based Test Generation** (v0.14.0+): AI-assisted test generation with 88-91% time savings
  - **YAML-driven specifications**: Declarative language definitions
  - **Jinja2 templating**: Automated test code generation
  - **100% quality validation**: Python syntax + language syntax checks
  - **Community-friendly**: Enable non-Python developers to contribute language support
- 🛣️ **Framework Route Extraction** (v0.5.0+): Auto-detect and extract routes from web frameworks
  - **ThinkPHP** (v0.5.0+): Convention-based routing with line numbers and PHPDoc descriptions
  - **Spring Boot** (v0.8.0+): @GetMapping, @PostMapping, REST controllers with path variables
  - **Laravel** (planned): Explicit route definitions (Epic 17)
  - **FastAPI** (planned): Decorator-based routes (Epic 17)
  - **Django** (planned): URL patterns (Epic 17)
  - **Express.js** (planned): TypeScript/JavaScript routes (Epic 17)
- 📝 **AI Docstring Extraction** (v0.4.0+, Epic 9): Multi-language documentation normalization
  - **Hybrid mode**: Selective AI processing (<$1 per 250 directories)
  - **All-AI mode**: Maximum quality for critical projects
  - **Language support**: PHP (PHPDoc + inline comments), Python (coming soon)
  - **Mixed language**: Normalize Chinese + English comments to clean English

---

## 📦 Installation

codeindex uses **lazy loading** - language parsers are only imported when needed. Install only the languages you use to keep dependencies minimal.

### Basic Installation (Core Only)

```bash
# Install core only (no language parsers)
pip install ai-codeindex
```

### Language-Specific Installation

Install only the languages you need:

```bash
# Python projects
pip install ai-codeindex[python]

# PHP projects
pip install ai-codeindex[php]

# Java projects
pip install ai-codeindex[java]

# Multiple languages
pip install ai-codeindex[python,php]

# All languages
pip install ai-codeindex[all]
```

### Using pipx (Recommended)

```bash
# All languages
pipx install ai-codeindex[all]

# Or specific languages
pipx install ai-codeindex[python,php]
```

### From Source

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"  # Development mode with all languages
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

**💡 Pro Tip**: When scanning web framework directories (like `Application/Admin/Controller` for ThinkPHP), codeindex automatically:
- ✅ Detects the framework
- ✅ Extracts routes with line numbers
- ✅ Includes method descriptions from PHPDoc/docstrings
- ✅ Generates route tables in README_AI.md

### 4. Batch Processing

```bash
# Scan all directories (generates SmartWriter READMEs)
codeindex scan-all

# Traditional batch processing (for AI-enhanced docs)
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
codeindex list-dirs | parallel -j 4 codeindex scan {}
```

**Example output:**
```
📝 Generating READMEs (SmartWriter)...
✓ Application ( 50KB)
✓ Admin ( 20KB)
✓ api ( 15KB)
→ Completed: 3/3 directories
```

### 5. Generate Structured Data (JSON)

**NEW in v0.5.0**: For tool integration (e.g., LoomGraph, custom scripts, CI/CD pipelines), generate machine-readable JSON output.

```bash
# Single directory
codeindex scan ./src --output json

# Entire project
codeindex scan-all --output json > parse_results.json

# View formatted JSON
codeindex scan ./src --output json | jq .
```

**JSON Output Structure**:

```json
{
  "success": true,
  "results": [
    {
      "file": "src/parser.py",
      "symbols": [
        {
          "name": "Parser",
          "kind": "class",
          "signature": "class Parser:",
          "line_start": 15,
          "line_end": 120
        }
      ],
      "imports": [
        {"module": "pathlib", "names": ["Path"], "is_from": true}
      ],
      "error": null
    }
  ],
  "summary": {
    "total_files": 1,
    "total_symbols": 1,
    "total_imports": 1,
    "errors": 0
  }
}
```

**Error Handling**:

When errors occur, the JSON response includes structured error information:

```json
{
  "success": false,
  "error": {
    "code": "DIRECTORY_NOT_FOUND",
    "message": "Directory does not exist: /path/to/dir",
    "detail": null
  },
  "results": [],
  "summary": {
    "total_files": 0,
    "errors": 1
  }
}
```

**Use Cases**:
- 🔌 **Tool Integration**: Feed parse results to visualization tools like LoomGraph
- 🤖 **CI/CD Pipelines**: Validate code structure in automated workflows
- 📊 **Analytics**: Analyze codebase metrics across versions
- 🧪 **Testing**: Verify expected code structure in tests

### 6. Parse Single Files

**NEW in v0.13.0**: Parse individual source files for loose coupling with downstream tools.

> **💡 For LoomGraph Integration**: See complete guide at [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md)

```bash
# Parse a Python file
codeindex parse src/auth/user.py

# Parse a PHP file
codeindex parse Application/Controller/User.php

# Parse a Java file
codeindex parse src/main/java/User.java

# Pretty print with jq
codeindex parse myfile.py | jq .

# Extract specific fields
codeindex parse myfile.py | jq '.symbols[] | {name, kind}'
```

**JSON Output Structure** (single file):

```json
{
  "file_path": "src/auth/user.py",
  "language": "python",
  "symbols": [
    {
      "name": "User",
      "kind": "class",
      "signature": "class User:",
      "docstring": "User authentication model",
      "line_start": 10,
      "line_end": 50,
      "annotations": []
    }
  ],
  "imports": [
    {"module": "typing", "names": ["Dict"], "is_from": true, "alias": null}
  ],
  "namespace": "",
  "error": null
}
```

**Exit Codes**:
- `0`: Success (includes partial parse with errors)
- `1`: File not found or permission denied
- `2`: Unsupported language
- `3`: Parse error

**Integration Example** (with LoomGraph):

```bash
# Parse and pipe to downstream tool
codeindex parse myfile.py | loomgraph import --format codeindex

# Batch parse multiple files
find src/ -name "*.py" -exec codeindex parse {} \; | \
  jq -s '.' > all_symbols.json
```

**See also**:
- Quick examples: `examples/parse_integration_example.sh`
- **For LoomGraph developers**: See [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) for detailed integration guide with Python/Node.js code examples

### 7. Check Status

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

### 8. Generate Symbol Indexes (v0.1.2+)

**Global symbol index** - Find any class/function across your codebase:

```bash
# Generate PROJECT_SYMBOLS.md (global symbol index)
codeindex symbols

# Generate PROJECT_INDEX.md (module overview)
codeindex index

# Analyze git changes and affected directories
codeindex affected --since HEAD~5 --until HEAD
codeindex affected --json  # For scripting/CI
```

**What you get:**

**PROJECT_SYMBOLS.md** provides:
- Quick class/function lookup across all files
- Cross-file references and imports
- Symbol locations with line numbers
- Grouped by directory

**PROJECT_INDEX.md** provides:
- Module overview with descriptions
- Directory structure
- Entry points and CLI commands
- Generated from README_AI.md files

**Affected analysis** helps with incremental updates:
- Shows which directories changed in git commits
- Suggests which README_AI.md files need regeneration
- JSON output for CI/CD integration

### 9. Analyze Technical Debt (v0.3.0+)

**NEW in v0.3.0**: Detect code quality issues and technical debt patterns.

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

### 10. Generate Test Suite for New Languages (v0.14.0+)

**NEW in v0.14.0**: Use the template-based test generation system to quickly add language support.

```bash
cd test_generator

# Create language specification (or copy template)
cp specs/_template.yaml specs/go.yaml
# Edit go.yaml with Go code examples

# Generate tests automatically
python generator.py \
  --spec specs/go.yaml \
  --template templates/inheritance_test.py.j2 \
  --output test_go_inheritance.py

# Validate generated code
python -m py_compile test_go_inheritance.py  # Python syntax
# Review Go code syntax manually

# Output: 500-700 lines of high-quality test code in 5 minutes!
```

**Benefits**:
- ⏱️ **88-91% faster** than manual test writing
- ✅ **100% syntax correctness** (automated validation)
- 🌍 **Language-agnostic** (just provide code examples in YAML)
- 🤝 **Community-friendly** (non-Python developers can contribute)

**Example output**:
```
✅ Loaded spec: Go (extension: .go)
✅ Loaded template: inheritance_test.py.j2
🔧 Generating Go tests...
✅ Code validation passed

✅ Generated test file:
   File: test_go_inheritance.py
   Lines: 587
   Test classes: 7
   Test methods: 22
```

See **[CONTRIBUTING_LANGUAGE_SUPPORT.md](test_generator/CONTRIBUTING_LANGUAGE_SUPPORT.md)** for complete guide.

### 11. Framework Route Extraction (v0.5.0+)

**NEW in v0.5.0**: Automatically detect and extract routes from web frameworks with line numbers and descriptions.

codeindex automatically identifies web frameworks and extracts route information when scanning Controller/View directories. Routes are displayed as beautiful markdown tables in your `README_AI.md` files.

#### Supported Frameworks

| Framework | Language | Status | Features |
|-----------|----------|--------|----------|
| **ThinkPHP** | PHP | ✅ Stable | Line numbers, PHPDoc descriptions, module-based routing |
| **Laravel** | PHP | 🔄 Coming v0.6.0 | Named routes, route groups, middleware |
| **FastAPI** | Python | 🔄 Coming v0.6.0 | Path operations, dependencies, tags |
| **Django** | Python | 🔄 Coming v0.6.0 | URL patterns, namespaces, view classes |

#### Example Output

**ThinkPHP Controller** (`Application/Admin/Controller/UserController.php`):

```php
class UserController {
    /**
     * Get user list with pagination
     */
    public function index() {
        // ...
    }

    /**
     * 创建新用户
     */
    public function create() {
        // ...
    }
}
```

**Generated Route Table** in `README_AI.md`:

```markdown
## Routes (ThinkPHP)

| URL | Controller | Action | Location | Description |
|-----|------------|--------|----------|-------------|
| `/admin/user/index` | UserController | index | `UserController.php:12` | Get user list with pagination |
| `/admin/user/create` | UserController | create | `UserController.php:20` | 创建新用户 |
```

#### How It Works

1. **Auto-Detection**: Scans directory structure to detect web frameworks
2. **Symbol Extraction**: Parses controllers/views using tree-sitter
3. **Route Inference**: Applies framework-specific routing conventions
4. **Documentation Extraction**: Extracts docstrings/PHPDoc comments
5. **Table Generation**: Formats as markdown table in README_AI.md

**Features:**
- ✅ **Line Numbers**: Clickable `file:line` locations
- ✅ **Descriptions**: From PHPDoc/docstrings (auto-truncated to 60 chars)
- ✅ **Multi-language**: Supports Chinese and English descriptions
- ✅ **Smart Filtering**: Only public methods, excludes magic methods
- ✅ **Zero Configuration**: Just scan, routes auto-appear

#### Usage

```bash
# Routes are automatically extracted when scanning
codeindex scan-all

# Or scan specific controller directory
codeindex scan ./Application/Admin/Controller
```

No configuration needed! Routes are detected and extracted automatically.

#### For Developers

Want to add support for your favorite framework? See [CLAUDE.md](CLAUDE.md#framework-route-extraction) for the complete developer guide on creating custom route extractors.

---

## 📋 Recent Updates

**Current version**: v0.16.1

### Key Features

- 🧪 **Template-Based Test Generation** (v0.14.0): AI-assisted test generation system
  - **88-91% time savings** (11-17 hours → ~2 hours per language)
  - **YAML-driven specifications**: Declarative language definitions
  - **Jinja2 templating**: Automated test code generation
  - **100% quality validation**: TypeScript tests ready (25 methods)
  - **Community-friendly**: Enable non-Python developers to contribute
- 🔗 **Call Relationship Extraction** (v0.12.0): Function/method call graphs and dependency analysis
- 🛣️ **Framework Route Extraction**: Auto-detect routes from ThinkPHP and Spring frameworks
- 🤖 **AI Docstring Extraction**: Multi-language documentation normalization (PHP, Python)
- 🎯 **KISS Universal Descriptions**: Language-agnostic module summaries with actual symbol names
- 📊 **Technical Debt Analysis**: Detect code quality issues and complexity metrics
- 🚀 **Automated Release Workflow**: One-command releases with GitHub Actions + PyPI Trusted Publisher

### Latest Improvements (v0.16.0)

- ✅ **Structural mode default**: `scan`/`scan-all` works immediately without AI config
- ✅ **`--ai` opt-in**: AI-enhanced docs now require explicit `--ai` flag
- ✅ **Post-commit auto-update**: `codeindex hooks install post-commit` for automatic README_AI.md sync
- ✅ **Parser detection**: Init wizard warns about missing tree-sitter parsers
- ✅ **Pass-through directory skip**: Avoids redundant docs in deep Java structures
- ✅ **Java tech-debt improvements**: Auto-recursive + language-aware noise analysis

**See**: [CHANGELOG.md](CHANGELOG.md) for complete version history

---

## 📖 Documentation

### User Guides
- **[Getting Started](docs/guides/getting-started.md)** - Detailed installation and setup
- **[Configuration Guide](docs/guides/configuration.md)** - All config options explained
- **[Configuration Changelog](docs/guides/configuration-changelog.md)** - Version-by-version config changes
- **[Advanced Usage](docs/guides/advanced-usage.md)** - Parallel scanning, custom prompts
- **[Git Hooks Integration](docs/guides/git-hooks-integration.md)** - Automated code quality checks

### Developer Guides
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup, TDD workflow, code style guidelines
- **[CLAUDE.md](CLAUDE.md)** - Quick reference for Claude Code and contributors
- **[Design Philosophy](docs/architecture/design-philosophy.md)** - Core design principles and architecture
- **[Release Automation](docs/development/QUICK_START_RELEASE.md)** - 5-minute automated release workflow
- **[Multi-Language Support](docs/development/multi-language-support-workflow.md)** - Guide for adding new language support
- **[Requirements Workflow](docs/development/requirements-workflow.md)** - Planning, issues, and development process

### Planning
- **[Strategic Roadmap](docs/planning/ROADMAP.md)** - Long-term vision and priorities
- **[Changelog](CHANGELOG.md)** - Version history and breaking changes

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

# Adaptive symbol extraction (v0.2.0+)
symbols:
  adaptive_symbols:
    enabled: true           # Enable dynamic symbol limits based on file size
    min_symbols: 5          # Minimum symbols for tiny files
    max_symbols: 150        # Maximum symbols for huge files
    thresholds:             # File size thresholds (lines)
      tiny: 100             # <100 lines → 5 symbols
      small: 500            # 100-500 lines → 15 symbols
      medium: 1500          # 500-1500 lines → 30 symbols
      large: 3000           # 1500-3000 lines → 50 symbols
      xlarge: 5000          # 3000-5000 lines → 80 symbols
      huge: 8000            # 5000-8000 lines → 120 symbols
      mega: null            # >8000 lines → 150 symbols
    limits:                 # Symbol limits per category
      tiny: 5
      small: 15
      medium: 30
      large: 50
      xlarge: 80
      huge: 120
      mega: 150

# Incremental updates
incremental:
  enabled: true
  thresholds:
    skip_lines: 5
    current_only: 50
    suggest_full: 200

# Git Hooks configuration (v0.7.0+, Story 6)
hooks:
  post_commit:
    mode: auto            # auto | disabled | async | sync | prompt
    max_dirs_sync: 2      # Auto mode: ≤2 dirs = sync, >2 = async
    enabled: true         # Master switch
    log_file: ~/.codeindex/hooks/post-commit.log
```

**Hooks Modes**:
- `auto` (default): Smart detection based on project size
- `disabled`: Completely disabled
- `async`: Always non-blocking (background updates)
- `sync`: Always blocking (immediate updates)
- `prompt`: Reminder only, no auto-execution

See [Git Hooks Integration Guide](docs/guides/git-hooks-integration.md) for detailed configuration.

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

### For Git Hooks Users (v0.5.0+)

If you're using **codeindex Git Hooks**, help your AI Code CLI understand how hooks work:

**Method 1: Let AI Code read the guide** ⭐️ (Recommended)

```bash
# In your project directory, run:
codeindex docs show-ai-guide
```

Then tell your AI:
```
User: "Read the output above and update my CLAUDE.md with Git Hooks documentation"
AI Code: [Reads the guide]
         [Understands Git Hooks]
         [Updates your CLAUDE.md/AGENTS.md]
         ✅ Done!
```

**Method 2: Direct AI integration**

```
User: "Help my AI CLI understand codeindex Git Hooks"
AI Code: [User runs: codeindex docs show-ai-guide]
         [AI reads output]
         [Updates CLAUDE.md with Git Hooks section]
         ✅ Done! Future AI sessions will know about hooks.
```

**What the guide contains:**
- Complete Git Hooks functionality explanation
- Pre-commit and post-commit behaviors
- Ready-to-use section template for your CLAUDE.md
- Troubleshooting and common scenarios
- Expected behaviors (auto-commits are normal!)

**Why this matters**: Your AI CLI needs to know that post-commit will create auto-commits (normal behavior) and that lint failures will block commits (by design).

### Full Documentation

- **User Guide**: [docs/guides/claude-code-integration.md](docs/guides/claude-code-integration.md)
- **Git Hooks Guide**: [docs/guides/git-hooks-integration.md](docs/guides/git-hooks-integration.md)
- **AI Integration**: [examples/ai-integration-guide.md](examples/ai-integration-guide.md)
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

### Code Parsing & Documentation

```
Directory → Scanner → Parser (tree-sitter) → Smart Writer → README_AI.md (≤50KB)
```

1. **Scanner**: Walks directories, filters by config patterns
2. **Parser**: Extracts symbols (classes, functions, imports) using tree-sitter
3. **Smart Writer**: Generates tiered documentation with size limits
4. **Output**: Optimized `README_AI.md` for AI consumption

### Test Generation (v0.14.0+)

```
Language Spec (YAML) → Jinja2 Template → Python Generator → Test File (500-700 lines)
                ↓                                              ↓
         Code Examples                                  Validation (100%)
         Expected Results                               Python + Target Language
```

1. **YAML Specification**: Define language syntax patterns and test scenarios
2. **Jinja2 Template**: Reusable test code template
3. **Generator**: Automated test file creation with validation
4. **Output**: High-quality pytest test suite

**Key Innovation**: Separate test definition (YAML) from test implementation (Python), enabling non-Python developers to contribute language support.

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

## 🔗 Integration with LoomGraph

**codeindex** and **[LoomGraph](https://github.com/dreamlx/LoomGraph)** work together as complementary tools:

### Architecture

```
codeindex (AST Parser)
    ↓ Structured Data (JSON)
LoomGraph (Knowledge Graph + AI)
    ↓ Insights & Analysis
Applications (IDE, CI/CD, Team Tools)
```

### Division of Responsibilities

| Tool | Focus | Key Features |
|------|-------|--------------|
| **codeindex** | Code Parsing | AST extraction, symbol extraction, call/inheritance relationships, multi-language support |
| **LoomGraph** | AI Analysis | Knowledge graph, vector embeddings, semantic search, refactoring suggestions, team collaboration |

### What codeindex Provides

- ✅ **Structured code data** (symbols, calls, imports, inheritance)
- ✅ **Multi-language support** (Python, PHP, Java, TypeScript, Go, Rust, C#)
- ✅ **Framework awareness** (ThinkPHP, Spring, Laravel, FastAPI routes)
- ✅ **JSON output** for downstream tools (`codeindex parse`, `codeindex scan --output json`)

### What LoomGraph Adds

- 🔍 **Code similarity search** (vector embeddings + semantic search)
- 🤖 **Automated refactoring suggestions** (graph analysis + AI)
- 👥 **Team collaboration** (shared knowledge graphs)
- 🔌 **IDE integration** (LSP server for real-time features)

### Integration Guide

See [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) or [`FOR_LOOMGRAPH.md`](FOR_LOOMGRAPH.md) for complete integration examples.

**Quick Example**:
```bash
# Parse a file and get JSON output
codeindex parse myfile.py | jq .

# Parse all files in a directory
codeindex scan ./src --output json > parse_results.json

# LoomGraph consumes this JSON to build knowledge graph
```

### Why This Separation?

1. **Single Responsibility**: codeindex focuses on parsing, LoomGraph focuses on AI
2. **Independent Evolution**: Each tool can evolve without affecting the other
3. **Flexible Integration**: Use codeindex alone or with LoomGraph
4. **Performance**: Lightweight parser vs. heavyweight graph+AI system

---

## 🌍 Language Support

| Language       | Status          | Version | Features |
|----------------|-----------------|---------|----------|
| Python         | ✅ Supported    | v0.1.0+ | Classes, functions, methods, imports, docstrings, inheritance, calls |
| PHP            | ✅ Supported    | v0.5.0+ | Classes (extends/implements), methods (visibility, static, return types), properties, functions, inheritance, calls |
| Java           | ✅ Supported    | v0.7.0+ | Classes, interfaces, enums, records, annotations, Spring routes, Lombok, inheritance, calls |
| TypeScript/JS  | 🧪 Tests Ready  | v0.14.0 | Classes, functions, React components, JSDoc (Epic 15) - Parser implementation in progress |
| Go             | 📋 Planned      | v0.15.0 | Packages, interfaces, struct methods (Epic 16) |
| Rust           | 📋 Planned      | v0.17.0 | Structs, traits, modules (Epic 19) |
| C#             | 📋 Planned      | v0.18.0 | Classes, interfaces, .NET projects |

### 🎯 Test Architecture (v0.14.0+)

codeindex uses a **template-based test generation system** to accelerate language support development:

- **YAML Language Specifications**: Declarative syntax patterns and test scenarios
- **Jinja2 Templates**: Automated Python test code generation
- **Quality Validation**: 100% syntax correctness for both Python and target language
- **Time Savings**: 88-91% reduction (11-17 hours → ~2 hours per language)

**Current test coverage**:
- ✅ **Python**: 50+ test methods (hand-written)
- ✅ **PHP**: 30+ test methods (hand-written)
- ✅ **Java**: 60+ test methods (hand-written)
- ✅ **TypeScript**: 25 test methods (template-generated, 100% quality)

**Want to contribute a new language?** See [Contributing Language Support](#-contributing-language-support) below.

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### 🚀 Quick Start for Contributors

```bash
# Clone and install
git clone https://github.com/dreamlx/codeindex.git
cd codeindex

# Install with dev dependencies
make install-dev
# or: pip install -e ".[dev,all]"

# Install Git hooks (pre-push checks)
make install-hooks

# Run tests
make test
# or: pytest

# Lint and auto-fix
make lint-fix
# or: ruff check --fix src/

# See all available commands
make help
```

### 🌟 Contributing Language Support

**Want to add support for Go, Rust, C++, or other languages?** You don't need to know Python!

We use a **template-based test generation system** that lets you contribute by only knowing your target language:

#### Quick Start (1-3 hours total)

1. **Create YAML specification** (1-2 hours)
   ```bash
   cd test_generator/specs
   cp _template.yaml <language>.yaml
   # Fill in code examples in your language
   ```

2. **Generate tests** (5 minutes)
   ```bash
   python generator.py \
     --spec specs/<language>.yaml \
     --template templates/inheritance_test.py.j2 \
     --output test_<language>_inheritance.py
   ```

3. **Review and submit PR** (30-60 minutes)
   - Verify Python syntax: `python -m py_compile test_*.py`
   - Verify your language syntax (manual review)
   - Submit PR with both YAML and generated test file

#### What You Need

- ✅ Familiarity with target language (Go/Rust/C++/etc.)
- ✅ Ability to write code examples in that language
- ✅ 1-3 hours of time
- ❌ **NO Python knowledge required!**

#### What You'll Create

- **YAML file**: 20-30 code templates with expected parsing results
- **Test file**: Auto-generated Python tests (you just review)

#### Quality Standards

- **Minimum**: 6 test classes, 15 test methods
- **Target**: 8 test classes, 25+ test methods
- **Validation**: 100% Python syntax + 100% target language syntax

#### Examples

- **TypeScript**: See `test_generator/specs/typescript.yaml` (351 lines, 28 templates)
- **Template**: See `test_generator/specs/_template.yaml` (fully documented starter)

#### Full Guide

See **[CONTRIBUTING_LANGUAGE_SUPPORT.md](test_generator/CONTRIBUTING_LANGUAGE_SUPPORT.md)** for:
- Detailed step-by-step instructions
- YAML specification guide
- PR template and checklist
- FAQ and troubleshooting

**Current recruitment**: 🔥 Go, Rust, C++, C#, Ruby, Kotlin

### 📚 Developer Documentation

- **[Quick Start Release Guide](docs/development/QUICK_START_RELEASE.md)** - 5-minute automated release workflow
- **[Release Workflow](docs/development/release-workflow.md)** - Complete release process documentation
- **[Multi-Language Support](docs/development/multi-language-support-workflow.md)** - Guide for adding new language support
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup, TDD workflow, code style guidelines
- **[Makefile](Makefile)** - Run `make help` to see all available commands

### 🎯 Release Process (Maintainers)

```bash
# Automated one-command release
make release VERSION=0.13.0

# GitHub Actions will automatically:
# ✅ Run tests on Python 3.10, 3.11, 3.12
# ✅ Build and publish to PyPI
# ✅ Create GitHub Release

# See: docs/development/QUICK_START_RELEASE.md
```

---

## 📊 Roadmap

See [Strategic Roadmap](docs/planning/ROADMAP.md) for detailed plans.

**Completed (v0.14.0)**:
- ✅ Python, PHP, Java language support (with LoomGraph integration)
- ✅ Single file parse command (loose coupling with downstream tools)
- ✅ Parser modularization (3622→374 lines refactoring)
- ✅ Windows platform compatibility (UTF-8 + path optimization)
- ✅ Call relationships extraction (Python/Java/PHP)
- ✅ Framework routes (ThinkPHP, Spring Boot)
- ✅ Interactive Setup Wizard (`codeindex init`)

**Completed (v0.16.0)**:
- ✅ CLI UX Restructuring: structural mode default, --ai opt-in (Epic 19)
- ✅ Java improvements: auto-recursive tech-debt, noise analysis
- ✅ Post-commit hook auto-update README_AI.md
- ✅ Parser installation detection in init wizard

**Next**:
- 📋 Framework routes expansion: Express, Laravel, FastAPI, Django (Epic 17)
- 📋 Rust language support
- 📋 C# language support

**Not Included** (Moved to LoomGraph):
- ❌ Code similarity search → [LoomGraph v0.3.0](https://github.com/dreamlx/LoomGraph)
- ❌ Automated refactoring suggestions → LoomGraph v0.4.0
- ❌ Team collaboration features → LoomGraph v0.5.0
- ❌ IDE deep integration (LSP server) → LoomGraph v0.6.0

**Reason**: codeindex focuses on **code parsing** (AST → structured data), while LoomGraph focuses on **AI analysis** (structured data → knowledge graph → insights).

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

- **Questions**: [GitHub Discussions](https://github.com/dreamlx/codeindex/discussions)
- **Bugs**: [GitHub Issues](https://github.com/dreamlx/codeindex/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/dreamlx/codeindex/issues/new?labels=enhancement)

---

## ⭐ Star History

If you find codeindex useful, please star the repository to show your support!

[![Star History Chart](https://api.star-history.com/svg?repos=dreamlx/codeindex&type=Date)](https://star-history.com/#dreamlx/codeindex&Date)

---

<p align="center">
  Made with ❤️ by the codeindex team
</p>