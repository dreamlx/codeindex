# Test Architecture: Template-Based Test Generation

**Since**: v0.15.0 (Epic 18)
**Last Updated**: 2026-02-12

---

## Overview

All inheritance tests for Python, PHP, and Java are generated from YAML specifications using a Jinja2 template system. This replaces the previous hand-written test approach.

**Key principle**: YAML specs are the single source of truth. Generated test files should never be edited manually.

## Architecture

```
test_generator/
├── generator.py                 # CLI tool: YAML + Jinja2 → .py
├── specs/
│   ├── python.yaml              # 30 templates, 8 test classes
│   ├── php.yaml                 # 23 templates, 7 test classes
│   └── java.yaml                # 29 templates, 7 test classes
├── templates/
│   └── inheritance_test.py.j2   # Shared template for all languages
└── scripts/
    ├── analyze_legacy_tests.py  # AST-based legacy test analyzer
    ├── compare_coverage.py      # Coverage regression detection
    └── compare_test_results.py  # Test result regression detection
```

**Generated outputs** (in `tests/`):
- `test_python_inheritance.py` — 30 tests
- `test_php_inheritance.py` — 23 tests
- `test_java_inheritance.py` — 29 tests

## YAML Spec Format

Each spec has three sections:

### 1. Language metadata

```yaml
language:
  name: Python
  extension: py
  parser_module: codeindex.parser
  parser_function: parse_file
```

### 2. Code templates

Named code snippets with expected parse results:

```yaml
code_templates:
  single_inheritance_basic:
    description: "Basic single inheritance"
    code: |
      class Base:
          pass
      class Child(Base):
          pass
    expected:
      inheritance_count: 1
      inheritances:
        - child: "Child"
          parent: "Base"
```

**Assertion types**:

| Type | Usage |
|------|-------|
| `inheritance_count` | `assert len(result.inheritances) == N` |
| `inheritances` | Exact list of `{child, parent}` pairs |
| `child_parents` | Filter by child, check parent set and count |
| `parent_contains` | `assert "X" in inh.parent` (substring match) |
| `parses_without_error` | `assert result.inheritances is not None` |
| `filter_child_contains` | Filter by substring in child name |

### 3. Test scenarios

Map test classes and methods to templates:

```yaml
test_scenarios:
  - class_name: TestSingleInheritance
    description: "Test single inheritance."
    tests:
      - method: test_basic
        template: single_inheritance_basic
```

## Regenerating Tests

```bash
# Regenerate a single language
python test_generator/generator.py \
    --spec test_generator/specs/python.yaml \
    --template test_generator/templates/inheritance_test.py.j2 \
    --output tests/test_python_inheritance.py

# Regenerate all three
for lang in python php java; do
    python test_generator/generator.py \
        --spec test_generator/specs/${lang}.yaml \
        --template test_generator/templates/inheritance_test.py.j2 \
        --output tests/test_${lang}_inheritance.py
done

# Preview without writing (dry-run)
python test_generator/generator.py \
    --spec test_generator/specs/python.yaml \
    --template test_generator/templates/inheritance_test.py.j2 \
    --dry-run
```

## Adding a New Language

1. Create `test_generator/specs/<language>.yaml` with language metadata, code templates, and test scenarios
2. Run the generator to produce `tests/test_<language>_inheritance.py`
3. Run `pytest tests/test_<language>_inheritance.py -v` to validate
4. Commit both the YAML spec and the generated test file

## Modifying Existing Tests

1. Edit the YAML spec file (never the generated `.py` file)
2. Regenerate the test file
3. Run tests to validate
4. Commit both changed files

## Custom Jinja2 Filters

The generator provides three custom filters:

| Filter | Purpose | Example |
|--------|---------|---------|
| `to_code_string` | Wraps code as triple-quoted Python string | `class Foo` → `"""\nclass Foo\n"""` |
| `py_escape` | Doubles backslashes for Python string literals | `App\Models` → `App\\Models` |
| `to_var_name` | Converts names to valid Python identifiers | `com.example.User` → `com_example_user` |

## Test Statistics

| Language | Templates | Test Methods | Legacy Coverage | Advanced Tests |
|----------|-----------|-------------|-----------------|----------------|
| Python | 30 | 30 | 21/21 (100%) | +9 new |
| PHP | 23 | 23 | 17/17 (100%) | +6 new |
| Java | 29 | 29 | 25/25 (100%) | +4 new |
| **Total** | **82** | **82** | **63/63 (100%)** | **+19 new** |
