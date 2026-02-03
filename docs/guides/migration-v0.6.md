# Migration Guide: v0.5.x → v0.6.0

## ⚠️ Breaking Change Overview

**v0.6.0 completely removes the AI Enhancement feature** (multi-turn dialogue, Phase 2 processing). This is a **breaking change** that requires configuration updates.

---

## Why Was AI Enhancement Removed?

Based on real-world PHP project testing:

**Information Loss Problem:**
- AI Enhancement **replaced** SmartWriter output instead of enhancing it
- Lost critical structured information:
  - ✗ Routes tables (ThinkPHP URL→Controller mappings)
  - ✗ Complete method signatures with parameters
  - ✗ Detailed dependency information

**Architecture Conflict:**
- Contradicts codeindex's core purpose: "code indexing for AI programming"
- For Serena MCP users: Fallback mode provides more complete and faster results

**KISS Principle:**
- Remove complexity that doesn't add sufficient value
- Focus on core mission: Structured code indexing

---

## What's Changed

### Removed Features

| Feature | Status | Replacement |
|---------|--------|-------------|
| `ai_enhancement` config | ❌ Removed | Use `scan` for AI-enhanced docs |
| Multi-turn dialogue | ❌ Removed | N/A |
| `scan-all --ai-all` | ❌ Removed | Use `scan-all` (SmartWriter only) |
| `scan --strategy` | ❌ Removed | Use `scan` (always invokes AI) |
| Phase 2 processing | ❌ Removed | N/A |
| `AIEnhancementConfig` | ❌ Removed | N/A |
| `execute_multi_turn_enhancement()` | ❌ Removed | N/A |

### What's Kept

| Feature | Status | Notes |
|---------|--------|-------|
| SmartWriter | ✅ Kept | Core structured README generation |
| Docstring Extraction | ✅ Kept | Epic 9 (v0.6.0+) |
| FileSizeClassifier | ✅ Kept | Used by tech_debt (hardcoded thresholds) |
| All 415 tests | ✅ Pass | 3 skipped |

---

## Migration Steps

### Step 1: Update Configuration File

**Remove the `ai_enhancement` section from `.codeindex.yaml`:**

```yaml
# ❌ REMOVE THIS SECTION
ai_enhancement:
  strategy: "selective"
  enabled: true
  size_threshold: 40960
  max_concurrent: 2
  rate_limit_delay: 1.0
```

**Your config should now look like:**

```yaml
version: 1
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

include:
  - src/

exclude:
  - "**/__pycache__/**"

languages:
  - python
  - php

output_file: README_AI.md

# ✅ These sections are still supported
symbols:
  adaptive_symbols:
    enabled: true

docstrings:
  mode: hybrid
  cost_limit: 1.0

incremental:
  enabled: true
```

### Step 2: Update Your Workflow

**Before (v0.5.x):**

```bash
# Two-phase processing
codeindex scan-all                # Phase 1: SmartWriter + Phase 2: AI Enhancement
codeindex scan-all --ai-all       # Enhance ALL directories
codeindex scan-all --no-ai        # SmartWriter only

# Single directory with strategy
codeindex scan ./src --strategy multi_turn
```

**After (v0.6.0):**

```bash
# SmartWriter only (fast, structured)
codeindex scan-all

# For AI-enhanced docs: Use scan per directory
codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}
codeindex list-dirs | parallel -j 4 codeindex scan {}

# Single directory (always invokes AI)
codeindex scan ./src
```

### Step 3: Verify Changes

```bash
# 1. Validate config (should not show ai_enhancement warnings)
codeindex scan-all --dry-run

# 2. Test scan-all
codeindex scan-all

# 3. Check output
ls -lh */README_AI.md
```

---

## FAQ

### Q: I relied on AI Enhancement. What should I use now?

**A:** Use `codeindex scan` per directory for AI-enhanced documentation:

```bash
# Parallel AI-enhanced scanning
codeindex list-dirs | parallel -j 4 codeindex scan {}
```

This gives you:
- ✅ AI-enhanced docs (invokes AI per directory)
- ✅ Full control over which directories get AI processing
- ✅ Parallel execution for speed

### Q: Will my existing README_AI.md files break?

**A:** No! Existing `README_AI.md` files are **not affected**. They will:
- Continue to work with Claude Code / Serena MCP
- Still be readable and useful
- Only get regenerated when you run `codeindex scan-all` or `codeindex scan <dir>`

### Q: What about super large files (>5000 lines)?

**A:** FileSizeClassifier still detects super large files for **tech debt analysis**:

```bash
# Tech debt detection still works
codeindex tech-debt ./src
```

But there's **no special AI processing** for super large files anymore. Use:
- SmartWriter (generates structured README with top symbols)
- Or `codeindex scan <dir>` for AI-enhanced doc

### Q: I want the old behavior back. Can I downgrade?

**A:** Yes, you can stay on v0.5.0:

```bash
# Downgrade to v0.5.0 (last version with AI Enhancement)
pip install codeindex==0.3.1
```

However, we recommend trying v0.6.0:
- **Faster**: No Phase 2 processing overhead
- **More information**: SmartWriter preserves routes, signatures, dependencies
- **Simpler**: KISS principle applied

### Q: What about Docstring Extraction (Epic 9)?

**A:** **Docstring Extraction is kept** and recommended:

```yaml
# .codeindex.yaml
docstrings:
  mode: hybrid          # Selective AI for complex docstrings
  cost_limit: 1.0       # ~$0.15 per 250 directories
```

This is **different** from AI Enhancement:
- Docstring Extraction: Normalizes mixed-language comments (e.g., Chinese + English)
- AI Enhancement: Replaced entire README (now removed)

---

## Comparison: Before vs After

### Before (v0.5.x with AI Enhancement)

```bash
codeindex scan-all
```

**Output:**
```
📝 Phase 1: SmartWriter (generates structured READMEs)
✓ Application (50KB)
✓ Admin (20KB)

🤖 Phase 2: AI Enhancement (selective strategy)
→ Checklist: 2 directories (1 overview, 1 oversize)
✓ Application: AI enhanced (50KB → 22KB)
❌ Lost: Routes table, method signatures, dependencies
```

### After (v0.6.0 without AI Enhancement)

```bash
codeindex scan-all
```

**Output:**
```
📝 Generating READMEs (SmartWriter)
✓ Application (50KB)
✓ Admin (20KB)
→ Completed: 2/2 directories
✅ Kept: Routes table, method signatures, dependencies
```

**For AI-enhanced docs:**
```bash
codeindex scan ./Application
```

**Output:**
```
🤖 Invoking AI CLI...
✓ README_AI.md generated (AI-enhanced)
```

---

## Rollback Plan

If you encounter issues after upgrading:

### Option 1: Downgrade (Recommended for Production)

```bash
pip install codeindex==0.3.1
```

### Option 2: Report Issue

Please report issues at: https://github.com/anthropics/codeindex/issues

Include:
- Your `.codeindex.yaml` configuration
- Output of `codeindex --version`
- Description of the problem

---

## Benefits of v0.6.0

1. **Information Preservation**: SmartWriter keeps all structured data
   - ✅ Routes tables (ThinkPHP, Laravel, FastAPI)
   - ✅ Complete method signatures
   - ✅ Detailed dependencies

2. **Faster Scanning**: No Phase 2 overhead
   - Before: ~2 minutes for 250 directories (Phase 1 + Phase 2)
   - After: ~30 seconds for 250 directories (Phase 1 only)

3. **Simpler Configuration**: Less complexity
   - Removed 6 config options (strategy, enabled, size_threshold, max_concurrent, rate_limit_delay, super_large thresholds)
   - Clearer user expectations

4. **Better for AI Programming**: More structured output
   - Serena MCP can parse routes, signatures, dependencies
   - Claude Code has full context without information loss

---

## Need Help?

- **Documentation**: `docs/guides/configuration.md`
- **Examples**: `examples/.codeindex.yaml`
- **Issues**: https://github.com/anthropics/codeindex/issues
- **Changelog**: `CHANGELOG.md` (v0.6.0 section)

---

**Last Updated**: 2026-02-04 (v0.6.0 release)
