# Story: Enrich Overview/Navigation Level README_AI.md

**Status**: Done
**Priority**: P1
**Target**: v0.18.0
**Effort**: S (1-2 days)
**Related**: Validation framework L2 AI scores (architecture_comprehension: 1-2/10)

---

## Problem

The `--fallback` mode generates root (overview) and module (navigation) level README_AI.md files that are too sparse for AI agents to use effectively.

### Current Output (Root Level)

```markdown
# LoomGraph

## Overview
- **Modules**: 1
- **Files**: 0        ← only counts direct files in root dir
- **Symbols**: 0      ← same issue

## Modules
- **src** - Module directory   ← meaningless description
```

### Root Cause Analysis

1. **`_generate_overview()`**: `total_files = len(parse_results)` only counts files directly in the root directory, not recursively. A project root typically has 0-3 files.

2. **`_generate_navigation()`**: Same issue — `Application/` shows 1,718 files but all 48 subdirectories are described as "Module directory".

3. **`_extract_module_description()`**: Reads the child README_AI.md and looks for "first non-empty, non-header, non-list line" — but fallback READMEs start with `## Overview` followed by list items (`- **Files**: ...`), so the heuristic never finds a description and falls back to "Module directory".

4. **No top-level symbol summary**: The overview/navigation levels don't surface any class names, making them useless for symbol navigation.

### Impact (from validation framework)

| Project | Architecture Score | Symbol Nav Score | Doc Accuracy |
|---------|-------------------|-----------------|--------------|
| php_admin | 2/10 | 5/10 | 2/10 |
| zcyl_backend | 2/10 | 4/10 | 2/10 |
| loomgraph | 1/10 | 7/10 | 1/10 |

AI evaluator feedback: "Zero symbols extracted", "No description of what the project actually contains", "Missing file listing".

---

## Solution

Three targeted improvements to `SmartWriter`, all purely programmatic (no AI needed).

### Task 1: Recursive Statistics Aggregation

**File**: `src/codeindex/smart_writer.py`
**Methods**: `_generate_overview()`, `_generate_navigation()`

**Current**:
```python
total_files = len(parse_results)         # direct files only
total_symbols = sum(len(r.symbols) for r in parse_results)
```

**Proposed**: Add a `_collect_recursive_stats()` method that reads child README_AI.md files and aggregates their counts.

```python
def _collect_recursive_stats(self, child_dirs: list[Path], output_file: str = "README_AI.md") -> dict:
    """Aggregate file/symbol counts from child README_AI.md files."""
    total_files = 0
    total_symbols = 0
    for child in child_dirs:
        readme = child / output_file
        if readme.exists():
            content = readme.read_text(errors="replace")
            # Parse "- **Files**: 42" and "- **Symbols**: 313" from overview section
            files_match = re.search(r'\*\*Files\*\*:\s*(\d+)', content)
            symbols_match = re.search(r'\*\*Symbols\*\*:\s*(\d+)', content)
            if files_match:
                total_files += int(files_match.group(1))
            if symbols_match:
                total_symbols += int(symbols_match.group(1))
    return {"files": total_files, "symbols": total_symbols}
```

**Output change**:
```markdown
## Overview
- **Modules**: 48
- **Total Files**: 1,718 (across all modules)    ← aggregated
- **Total Symbols**: 15,870                       ← aggregated
```

### Task 2: Smart Module Description

**File**: `src/codeindex/smart_writer.py`
**Method**: `_extract_module_description()`

**Current heuristic fails** because fallback READMEs have no free-text description.

**Proposed**: Extract structured info from child README_AI.md as description.

```python
def _extract_module_description(self, dir_path: Path, output_file: str = "README_AI.md") -> str:
    readme_path = dir_path / output_file
    if not readme_path.exists():
        return "Module directory"

    content = readme_path.read_text(errors="replace")

    # Strategy 1: Parse Files/Symbols/Subdirectories counts
    files_match = re.search(r'\*\*Files\*\*:\s*(\d+)', content)
    symbols_match = re.search(r'\*\*Symbols\*\*:\s*(\d+)', content)
    subdirs_match = re.search(r'\*\*Subdirectories\*\*:\s*(\d+)', content)

    # Strategy 2: Extract top class names from content
    classes = re.findall(r'\*\*class\*\*\s+`(?:class\s+)?(\w+)`', content)

    parts = []
    if files_match:
        parts.append(f"{files_match.group(1)} files")
    if symbols_match:
        parts.append(f"{symbols_match.group(1)} symbols")
    if classes:
        top_classes = classes[:5]
        parts.append(f"classes: {', '.join(top_classes)}")
        if len(classes) > 5:
            parts[-1] += f" +{len(classes)-5} more"

    return " | ".join(parts) if parts else "Module directory"
```

**Output change**:
```markdown
## Subdirectories
- **Cashier/** - 42 files | 313 symbols | classes: Config, Door, FacePay, Goods, Login +7 more
- **Pay/** - 17 files | 89 symbols | classes: AliPay, WxPay, PayBase
- **Token/** - 1 files | 7 symbols | classes: Token
```

### Task 3: Top Symbols Summary (Overview Level Only)

**File**: `src/codeindex/smart_writer.py`
**Method**: `_generate_overview()`

Add a "Key Components" section that surfaces the most important symbols project-wide.

```python
def _collect_top_symbols(self, child_dirs: list[Path], output_file: str = "README_AI.md", limit: int = 15) -> list[tuple[str, str, str]]:
    """Collect top symbols from child READMEs. Returns (name, kind, module)."""
    symbols = []
    for child in child_dirs:
        # Walk into deeper READMEs to find actual class definitions
        for readme in child.rglob(output_file):
            content = readme.read_text(errors="replace")
            # Extract "**class** `class ClassName`" patterns
            for m in re.finditer(r'\*\*(class|function)\*\*\s+`(?:\w+\s+)?(\w+)`', content):
                kind, name = m.group(1), m.group(2)
                module = readme.parent.name
                symbols.append((name, kind, module))
    # Deduplicate, return top N
    seen = set()
    result = []
    for name, kind, module in symbols:
        if name not in seen:
            seen.add(name)
            result.append((name, kind, module))
        if len(result) >= limit:
            break
    return result
```

**Output change**:
```markdown
## Key Components

| Symbol | Type | Module |
|--------|------|--------|
| Config | class | Cashier |
| Token | class | Token |
| AliPay | class | Pay |
| ... | ... | ... |
```

---

## Non-Goals

- **Not changing detailed-level READMEs**: They already contain full symbol info and score well
- **Not adding AI generation**: All improvements are programmatic
- **Not changing scan pipeline**: `parse_results` parameter contract stays the same
- **Not changing hierarchical processing order**: Bottom-up processing already ensures child READMEs exist when parent is generated

---

## Test Plan

### Unit Tests (TDD)

```
tests/test_smart_writer_enriched.py

1. test_overview_recursive_stats
   - 3 child dirs with README_AI.md containing Files/Symbols counts
   - Verify aggregated totals in overview output

2. test_overview_recursive_stats_missing_readmes
   - Some child dirs without README_AI.md
   - Verify graceful handling, partial totals

3. test_module_description_from_readme
   - Child README_AI.md with Files/Symbols/classes
   - Verify description like "42 files | 313 symbols | classes: Config, Door"

4. test_module_description_fallback
   - Child dir without README_AI.md
   - Verify returns "Module directory"

5. test_top_symbols_collection
   - Multiple child READMEs with class definitions
   - Verify top-15 symbols extracted with correct module attribution

6. test_overview_key_components_section
   - Full overview generation with child READMEs
   - Verify "Key Components" table present in output

7. test_navigation_enriched_stats
   - Navigation level with child dirs
   - Verify aggregated stats shown
```

### Integration Test

```
8. test_real_project_enriched_overview
   - Use php_admin project fixture (or mock structure)
   - Generate overview → verify non-zero stats
   - Generate navigation → verify module descriptions ≠ "Module directory"
```

### Validation

After implementation, re-run validation framework:
```bash
python scripts/validate_real_projects.py --layer l2 --no-ai
# Verify: Files > 0, Symbols > 0 for all projects
# Then with AI:
python scripts/validate_real_projects.py --layer l2
# Target: architecture_comprehension >= 5/10
```

---

## Implementation Order

1. Write failing tests (`test_smart_writer_enriched.py`)
2. Implement `_collect_recursive_stats()` → tests pass
3. Implement improved `_extract_module_description()` → tests pass
4. Implement `_collect_top_symbols()` + overview section → tests pass
5. Run validation framework → compare against baseline
6. Save new baseline

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Regex parsing of README_AI.md is fragile | Match exact codeindex output format (we control the format) |
| `rglob(README_AI.md)` could be slow on large projects | Limit depth or cap at N files |
| Aggregated stats double-count nested dirs | Only read direct children's READMEs (1 level) |
| Top symbols table makes overview too large | Cap at 15 symbols, respect max_size truncation |

---

## Files to Modify

| File | Action | Scope |
|------|--------|-------|
| `src/codeindex/smart_writer.py` | EDIT | Add 3 methods, modify 2 existing methods |
| `tests/test_smart_writer_enriched.py` | CREATE | ~8 test cases |

**Estimated LOC**: +150 (smart_writer) + +200 (tests) = ~350 total
