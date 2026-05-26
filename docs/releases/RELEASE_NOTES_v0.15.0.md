# Release Notes - v0.15.0

**Release Date**: 2026-02-12
**Theme**: Unified Test Architecture (统一测试架构)

---

## Overview

v0.15.0 migrates all inheritance tests (Python, PHP, Java) from hand-written test files to a template-based generation system. YAML specs are now the single source of truth for test definitions, with a shared Jinja2 template generating consistent pytest files across all languages.

---

## Major Changes

### Epic 18 - Test Architecture Migration

#### Template-Based Test Generation

- **YAML Specifications**: Each language has a YAML spec defining code templates and expected parse results
  - `test_generator/specs/python.yaml` — 30 templates
  - `test_generator/specs/php.yaml` — 23 templates
  - `test_generator/specs/java.yaml` — 29 templates
- **Shared Jinja2 Template**: `test_generator/templates/inheritance_test.py.j2`
- **Generator CLI**: `python test_generator/generator.py --spec <yaml> --template <j2> --output <py>`

#### Test Coverage

| Language | Legacy Tests | New Tests | Change |
|----------|-------------|-----------|--------|
| Python | 21 | 30 | +43% |
| PHP | 17 | 23 | +35% |
| Java | 25 | 29 | +16% |
| **Total** | **63** | **82** | **+30%** |

- 100% legacy test coverage preserved (63/63 scenarios)
- 19 additional advanced test scenarios added
- 0 regressions

#### New Tooling

- `test_generator/generator.py` — YAML + Jinja2 → pytest file generation
- `test_generator/scripts/analyze_legacy_tests.py` — AST-based test analysis
- `test_generator/scripts/compare_coverage.py` — Coverage regression detection
- `test_generator/scripts/compare_test_results.py` — Test result comparison
- Custom Jinja2 filters: `py_escape`, `to_var_name`, `to_code_string`

---

## How to Add/Modify Tests

**Modify**: Edit the YAML spec, regenerate:
```bash
python test_generator/generator.py \
    --spec test_generator/specs/python.yaml \
    --template test_generator/templates/inheritance_test.py.j2 \
    --output tests/test_python_inheritance.py
```

**Add new language**: Create a new YAML spec and run the generator.

See `docs/development/test-architecture.md` for full documentation.

---

## Breaking Changes

- Legacy hand-written inheritance test files replaced with generated versions
- `tests/generated/` and `tests/legacy_reference/` directories removed
- Legacy tests preserved in `backup/legacy-tests-20260211` branch
