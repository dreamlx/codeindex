# BDD Feature Files

This directory contains Gherkin feature files for Behavior-Driven Development (BDD) testing using pytest-bdd.

## Active Feature Files

All feature files in this directory have corresponding test implementations:

### Epic 15: User Onboarding Enhancement

#### `help_system.feature` (113 lines)
**Story**: 15.3 - Enhanced Help System  
**Test file**: `tests/test_help_system_bdd.py`  
**Scenarios**: 15 scenarios covering configuration help and parameter explanations

#### `init_wizard.feature` (158 lines)
**Story**: 15.1 - Interactive Setup Wizard  
**Test file**: `tests/test_init_wizard_bdd.py`  
**Scenarios**: 18 scenarios covering wizard interaction, auto-detection, and configuration

### Epic 3: Technical Debt Detection

#### `tech_debt_detection.feature` (53 lines)
**Test file**: `tests/test_tech_debt_bdd.py`  
**Scenarios**: Tech debt detection (large files, god classes, etc.)

#### `tech_debt_reporting.feature` (50 lines)
**Test file**: `tests/test_tech_debt_bdd.py`  
**Scenarios**: Tech debt reporting formats (console, markdown, JSON)

#### `symbol_overload_detection.feature` (21 lines)
**Test file**: `tests/test_tech_debt_bdd.py`  
**Scenarios**: Symbol overload detection (too many symbols in one file)

## BDD Testing Guidelines

### When to Use BDD

Use BDD (Gherkin + pytest-bdd) for:
- **User-facing features**: Features described in Epic/Story documents
- **Business requirements**: Scenarios that stakeholders can understand
- **Acceptance criteria**: Clear given-when-then workflows

### When to Use Regular Pytest

Use regular pytest for:
- **Unit tests**: Testing individual functions/classes
- **Internal helpers**: Testing implementation details
- **Edge cases**: Testing specific code paths

### Creating New Feature Files

1. **Write feature file** in `tests/features/`:
   ```gherkin
   Feature: Feature Name
     As a [role]
     I want [feature]
     So that [benefit]

     Scenario: Scenario name
       Given [context]
       When [action]
       Then [outcome]
   ```

2. **Create test file** in `tests/`:
   ```python
   from pytest_bdd import scenarios, given, when, then
   
   scenarios("features/feature_name.feature")
   
   @given("context")
   def context_fixture():
       ...
   ```

3. **Verify coverage**:
   ```bash
   pytest tests/test_feature_name_bdd.py -v
   ```

## Removed Feature Files (Story 16.3)

The following feature files were removed as they served as planning documents but were never implemented as BDD tests. The functionality is covered by regular pytest:

- ❌ `ai_helper.feature` → covered by `test_ai_helper.py`
- ❌ `file_classifier.feature` → covered by `test_file_classifier.py`
- ❌ `cli_module_split.feature` → covered by `test_cli_*.py`

**Reason**: Avoid confusion and maintain clear separation between BDD (user stories) and unit tests (implementation details).

## Verification

Check all feature files have corresponding tests:

```bash
for feature in tests/features/*.feature; do
  name=$(basename "$feature")
  grep -l "scenarios.*$name" tests/test_*.py || echo "Missing: $name"
done
```

Expected: All features should be found ✅

## Statistics

- **Total feature files**: 5
- **Total BDD scenarios**: ~48 scenarios
- **BDD coverage**: 100% (all features have tests)
- **Test files**: 3 BDD test files

---

**Last Updated**: 2026-02-11  
**Epic**: 16 - Test Suite Refactoring  
**Story**: 16.3 - Unify BDD test coverage
