# Release Notes — v0.20.0

**Release Date**: 2026-02-20

---

## Highlights

### Enhanced Tech-Debt Detection (#20)

`codeindex tech-debt` now detects **5 dimensions** of technical debt (up from 2), with **language-aware thresholds** that differentiate between compact languages (Python, TypeScript, JavaScript) and verbose languages (PHP, Java, Go).

**New detection dimensions:**

| Dimension | Category | Thresholds | Severity |
|-----------|----------|------------|----------|
| Long method/function | `long_method` | >80 lines / >150 lines | MEDIUM / HIGH |
| Too many functions | `too_many_functions` | >15 top-level functions | MEDIUM |
| High import coupling | `high_coupling` | >8 internal imports | MEDIUM |

**Language-aware file size thresholds:**

| Language | Medium | Large | Critical |
|----------|--------|-------|----------|
| Python, TypeScript, JS | 800 | 1500 | 2500 |
| PHP, Java, Go | 1500 | 2500 | 5000 |

**God Class detection** now has a warning tier at >20 methods (MEDIUM) in addition to the critical tier at >50 methods.

**Before**: `codeindex tech-debt src/codeindex/` → 0 issues, 100.0 score
**After**: 18 issues detected, 97.0 score

### SmartWriter Modularization

The monolithic `smart_writer.py` (864 LOC) has been refactored into a clean `writers/` package:

- `writers/core.py` — Base writer and orchestration
- `writers/detailed_generator.py` — Leaf-level detailed documentation
- `writers/navigation_generator.py` — Module-level navigation docs
- `writers/overview_generator.py` — Root-level overview docs
- `writers/utils.py` — Shared utilities (grouping, filtering, formatting)

---

## Test Coverage

- **55 tech-debt tests** (25 new)
- **1208 total tests**, all passing
- New test classes: `TestLongMethodDetection`, `TestTooManyFunctionsDetection`, `TestHighCouplingDetection`, `TestLanguageAwareThresholds`, `TestGodClassWarningTier`

## Upgrade

```bash
pip install --upgrade ai-codeindex
```

No configuration changes required. Existing `.codeindex.yaml` files are fully compatible.
