# codeindex Skills for Claude Code

Claude Code skills that enhance your AI-assisted development workflow with codeindex.

## Directory Structure

```
skills/
├── src/                    # Skill source files (single source of truth)
│   ├── mo-arch/
│   │   └── SKILL.md
│   └── mo-index/
│       └── SKILL.md
├── README.md               # This file
├── install.sh              # Installation script
└── create.sh               # Template generator
```

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **mo-arch** | `/mo-arch` | Query code architecture using README_AI.md |
| **mo-index** | `/mo-index` | Generate repository index with codeindex |

## Quick Start

### Install to Project (Recommended)

```bash
cd /path/to/codeindex
./skills/install.sh
```

This copies skills to `.claude/skills/` which are auto-discovered when Claude Code runs in this directory.

### Install Globally

```bash
./skills/install.sh --personal
```

This copies skills to `~/.claude/skills/` for global availability.

## Usage

### /mo-arch - Architecture Query

Query code structure after indexing:

```
User: /mo-arch Where is the parser implemented?

Claude: Based on README_AI.md, the parser is in src/codeindex/parser.py.
        It uses tree-sitter for AST parsing and extracts Symbol and Import...
```

### /mo-index - Repository Indexing

Generate index for your codebase:

```
User: /mo-index

Claude: I'll help you index this project.
        First, let me check if codeindex is installed...
```

## Creating New Skills

Use the template generator:

```bash
# Create a new skill
./skills/create.sh my-feature

# Create and open in editor
./skills/create.sh my-feature --edit
```

This creates `skills/src/my-feature/SKILL.md` with a template.

### SKILL.md Format

Skills require YAML front matter:

```markdown
---
name: my-feature
description: What it does. Use when [trigger scenarios]. Triggered by "[phrases]".
---

# my-feature

Instructions for Claude...
```

**Critical**: The `description` field determines when Claude triggers the skill.

## Installation Targets

| Target | Path | Scope |
|--------|------|-------|
| Project | `.claude/skills/` | Auto-discovered in project |
| Personal | `~/.claude/skills/` | Available globally |

Project skills take precedence over personal skills with the same name.

## Prerequisites

Skills require codeindex to be installed:

```bash
pip install codeindex
# or
pip install -e /path/to/codeindex
```

## Troubleshooting

### Skills not recognized

1. Run `./install.sh` to deploy skills
2. Check `.claude/skills/<name>/SKILL.md` exists
3. Restart Claude Code session

### Commands not working

1. Verify codeindex is installed: `which codeindex`
2. Check README_AI.md files exist: `find . -name "README_AI.md"`
3. Run indexing first: `codeindex scan ./src`

### Skill not triggering

1. Check `description` field in YAML front matter
2. Description must include WHAT the skill does and WHEN to use it
3. Use specific trigger phrases that match user intent
