# Tech-Debt Analysis Guide

**Command**: `codeindex tech-debt` (alias: `codeindex debt-scan`)

Comprehensive code-quality analysis: large files, god classes, symbol overload, test smells, and per-file quality scoring. Output as JSON (for LoomGraph integration), Markdown (for reports), or console (quick checks).

## Usage

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

## What it detects

- 🔴 **Super large files** (>5000 lines), **Large files** (>2000 lines)
- 🔴 **God Classes** (>50 methods)
- 🔴 **Long methods** (>80/150 lines)
- 🟡 **High coupling** (>8 internal imports)
- 🟡 **Symbol overload** (>100 symbols, high noise ratio)
- 🧪 **Test smells** (skipped tests, giant test files) — since v0.22.0
- 📊 **Quality scoring** (0-100 scale per file)

## JSON output schema (v0.22.0)

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

## Key features

- ✅ **Unified command**: Single entry point for all quality checks
- ✅ **Backward compatible**: All existing JSON fields preserved
- ✅ **LoomGraph ready**: Enhanced summary for knowledge graph integration
- ✅ **Framework-agnostic**: Detects test smells across Jest, pytest, JUnit, etc.
- ✅ **KISS design**: 90% code reuse, simple regex patterns for test detection
