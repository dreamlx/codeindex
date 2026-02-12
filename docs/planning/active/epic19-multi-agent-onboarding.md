# Epic 19: Multi-Agent Onboarding Flow

**Status**: Planning
**Priority**: P2
**Target**: v0.19.0+

---

## Background

codeindex currently integrates with Claude Code through CLAUDE.md injection. The onboarding flow is:

```
1. pip install ai-codeindex[all]
2. codeindex init --yes
   → .codeindex.yaml  (auto-detected config)
   → CLAUDE.md        (setup instructions for AI agent)
   → CODEINDEX.md     (command reference)
3. AI agent reads CLAUDE.md → reviews config → runs scan-all
4. Ongoing: hooks auto-update or AI agent runs scan on demand
```

This flow works for Claude Code, but the market has multiple AI coding tools (Cursor, Windsurf, Cline, GitHub Copilot, etc.) that each have different mechanisms for reading project instructions.

---

## Goal

Make the onboarding flow work across all major AI coding tools, not just Claude Code.

---

## Current Architecture

### Instruction Injection Points

| Tool | Instruction File | How It's Read |
|------|-----------------|---------------|
| Claude Code | `CLAUDE.md` | Auto-loaded at session start |
| Cursor | `.cursorrules` | Auto-loaded at session start |
| Windsurf | `.windsurfrules` | Auto-loaded at session start |
| Cline | `.clinerules` | Auto-loaded at session start |
| GitHub Copilot | `.github/copilot-instructions.md` | Auto-loaded |
| Generic | `AGENTS.md` | Convention (Codex, etc.) |

### Current Implementation

- `init_wizard.py` has `CLAUDE_MD_SECTION` constant with codeindex instructions
- `inject_claude_md()` handles idempotent injection between `<!-- codeindex:start -->` markers
- Only targets `CLAUDE.md`

---

## Proposed Design

### Story 19.1: Multi-Agent Instruction Injection

**Goal**: `codeindex init` detects which AI tools are in use and injects instructions into the appropriate files.

**Detection logic**:
```python
def detect_ai_tools(project_dir: Path) -> list[str]:
    """Detect which AI coding tools are configured."""
    tools = []
    if (project_dir / "CLAUDE.md").exists() or shutil.which("claude"):
        tools.append("claude")
    if (project_dir / ".cursorrules").exists():
        tools.append("cursor")
    if (project_dir / ".windsurfrules").exists():
        tools.append("windsurf")
    if (project_dir / ".clinerules").exists():
        tools.append("cline")
    if (project_dir / ".github/copilot-instructions.md").exists():
        tools.append("copilot")
    return tools or ["claude"]  # Default to Claude
```

**Injection**: Same content (`CLAUDE_MD_SECTION`), injected into each tool's instruction file using the same marker-based idempotent approach.

**Wizard change**: Step 5 becomes "AI agent integration" → auto-detects tools, asks user to confirm.

### Story 19.2: Unified Instruction Template

**Goal**: Single instruction template that works across all AI tools.

Current `CLAUDE_MD_SECTION` is already tool-agnostic (no Claude-specific instructions). Just needs:
- Rename constant to `AGENT_INSTRUCTION_SECTION`
- Ensure language is generic ("AI agent" not "Claude Code")

### Story 19.3: CODEINDEX.md Consolidation

**Goal**: Evaluate whether CODEINDEX.md is still needed.

**Analysis**:
- CODEINDEX.md (105 lines) overlaps with CLAUDE.md injection content
- If instructions are injected into each tool's file, CODEINDEX.md becomes redundant
- **Decision**: Keep as fallback for tools without a standard instruction file, but make creation optional (already is)

### Story 19.4: Agent-Specific Optimizations (Future)

Different agents may benefit from different instruction styles:
- Cursor: May need `.cursorrules` format (plain text, no markdown headers)
- Copilot: May need specific formatting for `.github/copilot-instructions.md`
- Custom prompt templates per tool

---

## Reference: Current Onboarding Flow (v0.17.2)

### Complete User Journey

```
Step 1: Installation
  pip install ai-codeindex[all]

Step 2: Initialization (in AI coding tool)
  User tells AI: "initialize codeindex"
  AI executes: codeindex init --yes

  Output:
    ✓ Created: .codeindex.yaml     (auto-detected languages, dirs, performance)
    ✓ Created: CODEINDEX.md        (command reference for AI agents)
    ✓ Injected: CLAUDE.md          (setup instructions for AI agent)

    Next steps:
      1. Review .codeindex.yaml    → Verify include/exclude patterns
      2. codeindex scan-all        → Generate documentation indexes
      3. codeindex status          → Check coverage

Step 3: AI Agent Completes Setup
  AI reads CLAUDE.md (or post-init output) and:
    → Reviews .codeindex.yaml, adjusts include/exclude for project structure
    → Runs codeindex scan-all to generate initial README_AI.md indexes
    → Runs codeindex status to verify coverage
    → Optionally: codeindex hooks install post-commit

Step 4: Ongoing Usage (future sessions)
  AI reads CLAUDE.md at session start → knows to:
    → Read README_AI.md before exploring source code
    → Run codeindex scan <dir> if docs are outdated
    → Check codeindex status for coverage gaps

  If hooks installed:
    → Every git commit auto-updates affected README_AI.md files
    → Hook skips doc-only commits (no infinite loop)
    → Hook only updates already-indexed directories
```

### Key Design Decisions

1. **CLAUDE.md is the bridge**: AI agents read it at session start, it contains actionable instructions
2. **init does NOT auto-scan**: Config review should happen first (AI may need to adjust include/exclude)
3. **Hooks default to OFF**: Conservative — user or AI must explicitly enable
4. **Post-init output is for current session**: AI sees it immediately after running init
5. **CLAUDE.md instructions are for future sessions**: Persisted, read on every session start

### Files Involved

| File | Role |
|------|------|
| `src/codeindex/init_wizard.py` | Wizard logic, `CLAUDE_MD_SECTION` template, `inject_claude_md()` |
| `src/codeindex/cli_config.py` | `init` command, `_print_post_init_message()` |
| `src/codeindex/cli_hooks.py` | Hook install/uninstall/status commands |
| `.codeindex.yaml` | Project config (languages, include/exclude, hooks) |

---

## Scope Boundaries

**In scope**:
- Multi-tool instruction injection
- Detection of AI coding tools
- Unified instruction template

**Out of scope**:
- MCP server for codeindex (separate epic)
- AI-powered config optimization (init wizard auto-detection is sufficient)
- Tool-specific features beyond instruction injection

---

## Dependencies

- None (builds on existing init wizard infrastructure)

---

**Created**: 2026-02-13
**Author**: Planning phase
