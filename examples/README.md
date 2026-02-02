# Examples Directory

This directory contains templates and guides for integrating codeindex with your projects and AI Code tools.

---

## 📋 Files Overview

### `ai-integration-guide.md` ⭐

**For**: AI Code CLI tools (Claude Code, Cursor, Roo Coder, etc.)
**Purpose**: Teach AI how to update user projects with Git Hooks documentation

**Usage**:
```
User: "Help my AI CLI understand codeindex Git Hooks"
AI: [Reads this file]
    [Understands Git Hooks]
    [Updates user's CLAUDE.md/AGENTS.md]
    ✅ Done!
```

**Why**: Your AI CLI needs to know about Git Hooks behaviors (auto-commits, lint checks) to work correctly with them.

---

### `CLAUDE.md.template`

**For**: Claude Code users
**Purpose**: Template for your project's `CLAUDE.md` to guide Claude Code

**Usage**:
```bash
cp examples/CLAUDE.md.template CLAUDE.md
# Edit project-specific sections
git add CLAUDE.md
git commit -m "docs: add Claude Code guide"
```

**Contains**:
- How to use README_AI.md files
- Serena MCP tools navigation
- Project structure explanation template

---

### `.codeindex.yaml`

**Purpose**: Example configuration file
**Usage**: Reference for configuring your project

```bash
codeindex init  # Creates .codeindex.yaml in your project
```

---

### `frameworks/`

**For**: Developers adding new framework support
**Contains**: Templates for route extractors

See: `frameworks/template/README.md`

---

## 🚀 Quick Start Guides

### For Users: Setting Up Claude Code Integration

1. **Scan your project**:
   ```bash
   codeindex scan-all --fallback
   ```

2. **Copy template**:
   ```bash
   cp examples/CLAUDE.md.template CLAUDE.md
   ```

3. **Customize**: Edit `CLAUDE.md` with your project specifics

4. **Commit**:
   ```bash
   git add CLAUDE.md **/README_AI.md
   git commit -m "docs: add Claude Code integration"
   ```

### For AI Code: Understanding Git Hooks

If user has installed Git Hooks:

1. **Read**: `examples/ai-integration-guide.md`
2. **Understand**: How Git Hooks work
3. **Update**: User's CLAUDE.md/AGENTS.md with Git Hooks section
4. **Result**: Future AI sessions know about hooks

**Example interaction**:
```
User: "Make sure my AI understands codeindex Git Hooks"

AI Code:
1. Reads examples/ai-integration-guide.md
2. Understands:
   - Pre-commit blocks bad code
   - Post-commit auto-updates docs
   - Auto-commits are normal
3. Adds Git Hooks section to user's CLAUDE.md
4. Reports: "✅ Updated CLAUDE.md with Git Hooks docs"

Future AI sessions: Automatically know how hooks work!
```

---

## 📚 Documentation Hierarchy

```
codeindex/
├── README.md                           # User overview
├── CLAUDE.md                           # Developer guide (codeindex development)
├── examples/
│   ├── README.md                       # ← This file
│   ├── ai-integration-guide.md         # AI reads this to understand Git Hooks
│   ├── CLAUDE.md.template              # Template for user projects
│   └── frameworks/                     # Developer templates
├── docs/
│   ├── guides/
│   │   ├── claude-code-integration.md  # Detailed user guide
│   │   └── git-hooks-integration.md    # Git Hooks user guide
│   └── development/
│       └── git-hooks-architecture.md   # Developer deep dive (future)
```

---

## 🤖 For AI Code: How to Use This Directory

### When user says: "Set up Claude Code integration"

1. Read `CLAUDE.md.template`
2. Create user's `CLAUDE.md` from template
3. Customize project-specific sections
4. Report success

### When user says: "Help my AI understand Git Hooks"

1. Read `ai-integration-guide.md`
2. Understand Git Hooks behaviors
3. Update user's `CLAUDE.md` or `AGENTS.md` with Git Hooks section
4. Report success

### When user says: "How do I add support for Laravel routes?"

1. Read `frameworks/template/README.md`
2. Guide user through template-based development
3. Point to reference implementation: `src/codeindex/route_extractors/thinkphp_extractor.py`

---

## 💡 Tips

### For Users

- **Always read README_AI.md first** before diving into code
- **Use templates** to speed up setup
- **Customize** templates for your project

### For AI Code

- **Templates are designed for you** to read and execute
- **ai-integration-guide.md** is self-contained (explains everything)
- **Update user docs** automatically (don't make user copy-paste)

---

**Generated**: 2026-02-02
**Updated**: v0.5.0-beta1
**Purpose**: Help users and AI Code integrate codeindex features
