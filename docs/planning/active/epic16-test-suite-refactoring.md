# Epic 16: Test Suite Refactoring（测试套件重构）

**Version**: v0.14.1
**Priority**: P1 (Should Have - Technical Debt)
**Status**: 📋 Planning
**Created**: 2026-02-10
**Epic Type**: Technical Debt Reduction

---

## 🎯 Epic Goal

Refactor and optimize the test suite to improve maintainability, eliminate technical debt, and establish a clear organizational structure for future test development.

### Success Criteria

- [ ] All test files pass ruff linting without exclusions
- [ ] No git workarounds (`assume-unchanged`) required
- [ ] Legacy tests reviewed and cleaned up (≤5 files remaining)
- [ ] Test directory structure is clear and documented
- [ ] Test coverage maintained at ≥90% for core modules
- [ ] CI/CD pipeline runs without test-related warnings

---

## 📊 Problem Statement

### Current Issues

**🔴 P0 - Critical Issues**

1. **Legacy Test Fixture Trailing Newlines Problem** ⚠️
   - **Location**: `tests/legacy/test_hierarchical_test/level1/` and subdirectories
   - **Files**: file1.py, file2.py, file3.py, file4.py (4 files)
   - **Symptoms**:
     ```bash
     W292 [*] No newline at end of file
     --> tests/legacy/test_hierarchical_test/level1/file1.py:1:18
     ```
   - **Current Workarounds** (Technical Debt):
     - Added to ruff exclude: `tests/legacy/test_hierarchical_test/**/*.py`
     - Used `git update-index --assume-unchanged` on 4 files
   - **Root Cause**:
     - `test_hierarchy_simple.py` generates fixtures with `write_text()`
     - `write_text()` does not automatically add trailing newline
     - Tests depend on exact 17-byte file format
   - **Impact**: Blocks clean releases, requires manual intervention

**🟡 P1 - Important Issues**

2. **Unclear Purpose of Legacy Tests**
   - **Location**: `tests/legacy/` directory (7 files, 5 tests)
   - **Problems**:
     - `test_operategoods.py` - Purpose unknown, no documentation
     - `test_adaptive_debug.py` - Early debugging code
     - `test_current_project.py` - Project-specific, potentially outdated
   - **Risk**: May test deprecated functionality (hierarchical scanning)
   - **README Status**: Marked "needs review"

3. **Inconsistent Test Naming**
   - `test_config_adaptive.py` vs `test_adaptive_config.py`
   - Both test adaptive symbols configuration
   - Functional overlap, unclear responsibility split

4. **Incomplete BDD Test Coverage**
   - **Existing BDD**: 3 test files with pytest-bdd
   - **Feature files**: 8 .feature files
   - **Missing**: 5 feature files without corresponding tests:
     - `ai_helper.feature`
     - `cli_module_split.feature`
     - `file_classifier.feature`
     - `symbol_overload_detection.feature` (used by test_tech_debt_bdd.py)
     - `tech_debt_reporting.feature` (used by test_tech_debt_bdd.py)

**🟢 P2 - Optimization Opportunities**

5. **Root Directory Test File Sprawl**
   - 68 test files flat in root directory
   - Clear language categorization (Java: 12, PHP: 6, Python: 4)
   - Lacks organizational structure

6. **Inconsistent Fixture Management**
   - `conftest.py`: Shared fixtures (mock_config, symbol_scorer)
   - `fixtures/cli_parse/`: CLI-specific
   - `fixtures/java/`: Java-specific
   - `tests/legacy/test_hierarchical_test/`: Problematic fixtures
   - Missing: PHP and Python dedicated fixture directories

7. **Test Data Duplication**
   - Multiple tests use `create_mock_parse_result()`
   - Each test constructs own test data
   - Could share more fixtures

### Impact Assessment

| Issue | Impact on Development | Impact on CI/CD | Impact on New Contributors |
|-------|----------------------|-----------------|----------------------------|
| P0: Fixture lint errors | High (blocks releases) | High (manual fixes) | High (confusing workarounds) |
| P1: Legacy test clutter | Medium (unclear purpose) | Low | High (what to trust?) |
| P1: Inconsistent naming | Low | None | Medium (which test covers what?) |
| P1: Incomplete BDD | Low | None | Medium (outdated features?) |
| P2: Flat structure | Low | None | Medium (hard to navigate) |
| P2: Fixture duplication | Low | None | Low |

---

## 💡 Solution Design

### Design Principles

1. **Minimal Disruption**: Start with critical fixes, defer structural changes
2. **Zero Regression**: All existing tests must pass after changes
3. **Documentation First**: Update README before moving files
4. **Incremental Migration**: Phased approach with validation at each step

### Three-Phase Approach

```
Phase 1 (P0)     Phase 2 (P1)      Phase 3 (P2)
  ↓                ↓                  ↓
Critical Fix → Legacy Cleanup → Structure Optimization
(30 min)       (2 days)          (1 week, optional)
  ↓                ↓                  ↓
Release       Maintainability     Scalability
Unblocked     Improved           Future-proof
```

---

## 📋 Story Breakdown

### Story 16.1: Fix Legacy Test Fixture Trailing Newlines (P0) ⭐

**Goal**: Eliminate ruff lint errors and remove git workarounds

**Acceptance Criteria**:
- [ ] All fixture files have proper trailing newlines
- [ ] `ruff check tests/` passes without exclusions
- [ ] No files marked with `git update-index --assume-unchanged`
- [ ] `pytest tests/legacy/ -v` passes (100%)
- [ ] pyproject.toml does not exclude legacy test fixtures

**Technical Approach**:

```python
# File: tests/legacy/test_hierarchy_simple.py
# Change lines 30-33 from:

(test_dir / "level1" / "file1.py").write_text("def func1(): pass")
(test_dir / "level1" / "level2a" / "file2.py").write_text("def func2(): pass")
(test_dir / "level1" / "level2b" / "file3.py").write_text("def func3(): pass")
(test_dir / "level1" / "level2a" / "level3" / "file4.py").write_text("def func4(): pass")

# To:

(test_dir / "level1" / "file1.py").write_text("def func1(): pass\n")
(test_dir / "level1" / "level2a" / "file2.py").write_text("def func2(): pass\n")
(test_dir / "level1" / "level2b" / "file3.py").write_text("def func3(): pass\n")
(test_dir / "level1" / "level2a" / "level3" / "file4.py").write_text("def func4(): pass\n")
```

**Cleanup Steps**:

```bash
# 1. Remove git assume-unchanged markers
git update-index --no-assume-unchanged \
  tests/legacy/test_hierarchical_test/level1/file1.py \
  tests/legacy/test_hierarchical_test/level1/level2a/file2.py \
  tests/legacy/test_hierarchical_test/level1/level2b/file3.py \
  tests/legacy/test_hierarchical_test/level1/level2a/level3/file4.py

# 2. Remove from ruff exclude in pyproject.toml
# Delete line: "tests/legacy/test_hierarchical_test/**/*.py"

# 3. Verify
pytest tests/legacy/test_hierarchy_simple.py -v
ruff check tests/legacy/test_hierarchical_test/
```

**Estimated Effort**: 30 minutes
**Risk**: Low (isolated change, testable)

---

### Story 16.2: Review and Clean Legacy Tests (P1)

**Goal**: Remove obsolete tests and document remaining ones

**Acceptance Criteria**:
- [ ] All legacy tests have documented purpose in README
- [ ] Obsolete tests removed (test_operategoods.py, test_adaptive_debug.py)
- [ ] Remaining tests verified as necessary
- [ ] Full test suite passes (977 tests)
- [ ] `tests/legacy/README.md` updated with review results

**Review Checklist**:

| File | Status | Action | Reason |
|------|--------|--------|--------|
| `test_operategoods.py` | ❌ Obsolete | DELETE | No documentation, purpose unknown |
| `test_adaptive_debug.py` | ❌ Obsolete | DELETE | Early debugging code, not test |
| `test_current_project.py` | ⚠️ Review | EVALUATE | Project-specific, may be outdated |
| `test_hierarchy_simple.py` | ✅ Keep | FIX | Generates fixtures (Story 16.1) |
| `test_hierarchical.py` | ✅ Keep | KEEP | Tests hierarchical scanning (2 tests) |
| `test_hierarchical_src.py` | ✅ Keep | KEEP | Tests with subdirs (2 tests) |

**Updated legacy/README.md Structure**:

```markdown
# Legacy Tests

**Last Reviewed**: 2026-02-10
**Status**: Active (maintained)

## Purpose

This directory contains tests for early hierarchical scanning functionality
that remains in use for backward compatibility.

## Active Tests

- `test_hierarchy_simple.py` - Fixture generation for hierarchical tests
- `test_hierarchical.py` - Basic hierarchical scanning (2 tests)
- `test_hierarchical_src.py` - Hierarchical with subdirectories (2 tests)

## Removed Tests (Archive)

- `test_operategoods.py` (removed 2026-02-10) - Purpose unknown
- `test_adaptive_debug.py` (removed 2026-02-10) - Early debugging code
```

**Estimated Effort**: 4 hours
**Risk**: Medium (requires understanding test purpose)

---

### Story 16.3: Unify BDD Test Coverage (P1)

**Goal**: Either implement missing BDD tests or remove unused feature files

**Acceptance Criteria**:
- [ ] All .feature files have corresponding test implementations, OR
- [ ] Unused .feature files removed with justification
- [ ] No pytest collection warnings about missing steps
- [ ] BDD tests organized in clear structure

**Current State Analysis**:

```bash
# Feature files (8 total)
tests/features/
├── tech_debt_detection.feature       → ✅ test_tech_debt_bdd.py
├── tech_debt_reporting.feature       → ✅ test_tech_debt_bdd.py
├── symbol_overload_detection.feature → ✅ test_tech_debt_bdd.py
├── help_system.feature                → ✅ test_help_system_bdd.py
├── init_wizard.feature                → ✅ test_init_wizard_bdd.py
├── ai_helper.feature                  → ❌ No implementation
├── cli_module_split.feature           → ❌ No implementation
└── file_classifier.feature            → ❌ No implementation
```

**Decision Matrix**:

| Feature File | Functionality Status | Has Non-BDD Test? | Action |
|--------------|---------------------|-------------------|--------|
| `ai_helper.feature` | Implemented | ✅ test_ai_helper.py | DELETE (covered by unit tests) |
| `cli_module_split.feature` | Completed (Epic 4) | N/A | DELETE (historical artifact) |
| `file_classifier.feature` | Implemented | ✅ test_file_classifier.py | DELETE (covered by unit tests) |

**Rationale**: These features have comprehensive unit tests. BDD adds overhead without value for internal technical features.

**Implementation**:

```bash
# Remove unused feature files
git rm tests/features/ai_helper.feature \
       tests/features/cli_module_split.feature \
       tests/features/file_classifier.feature

# Update tests/features/README.md
cat > tests/features/README.md <<EOF
# BDD Feature Files

This directory contains Gherkin feature files for user-facing functionality
that benefits from behavior-driven development.

## Guidelines

- Use BDD for user-facing features (CLI commands, configuration, workflows)
- Use unit tests for internal technical features (parsers, extractors, utilities)
- Each .feature file must have a corresponding test_*_bdd.py file

## Current Features

- \`help_system.feature\` - Configuration help system (Story 15.3)
- \`init_wizard.feature\` - Interactive setup wizard (Story 15.1)
- \`tech_debt_detection.feature\` - Technical debt analysis
- \`tech_debt_reporting.feature\` - Debt report generation
- \`symbol_overload_detection.feature\` - Symbol overload detection
EOF
```

**Estimated Effort**: 1 hour
**Risk**: Low (removing unused files)

---

### Story 16.4: Clarify Configuration Test Naming (P1)

**Goal**: Eliminate naming confusion between configuration tests

**Acceptance Criteria**:
- [ ] Test files have clear, non-overlapping names
- [ ] Each test file has documented scope in docstring
- [ ] No functional duplication
- [ ] All tests pass after renaming

**Current Confusion**:

```
test_adaptive_config.py        # Tests what?
test_config_adaptive.py        # Tests what?
```

**Analysis**:

```python
# test_adaptive_config.py (189 lines, 26 tests)
# - Tests AdaptiveSymbolsConfig dataclass
# - Tests threshold validation
# - Tests configuration structure

# test_config_adaptive.py (112 lines, 13 tests)
# - Tests Config.load() with adaptive symbols enabled
# - Tests YAML parsing
# - Tests integration with Config system
```

**Solution**: Rename to clarify scope

```bash
# Rename for clarity
git mv tests/test_adaptive_config.py \
       tests/test_adaptive_symbols_config.py

# Update docstring
```

```python
# tests/test_adaptive_symbols_config.py
"""
Unit tests for AdaptiveSymbolsConfig dataclass.

Tests the adaptive symbols configuration data structure,
validation logic, and threshold calculations.

Related:
- test_config_adaptive.py - Tests Config.load() integration
- test_adaptive_selector.py - Tests symbol selection logic
"""
```

```python
# tests/test_config_adaptive.py (update docstring)
"""
Integration tests for Config with adaptive symbols.

Tests loading adaptive symbols configuration from YAML files
and integration with the Config system.

Related:
- test_adaptive_symbols_config.py - Tests AdaptiveSymbolsConfig dataclass
- test_adaptive_selector.py - Tests symbol selection logic
"""
```

**Estimated Effort**: 2 hours
**Risk**: Low (rename + documentation)

---

### Story 16.5: Create Fixture Management Guidelines (P2, Optional)

**Goal**: Establish best practices for fixture organization

**Acceptance Criteria**:
- [ ] Fixtures organized by language/feature
- [ ] Shared fixtures moved to conftest.py
- [ ] Fixture reuse documented
- [ ] Guidelines published in tests/README_AI.md

**Proposed Structure**:

```
tests/fixtures/
├── python/              # Python test data
│   ├── simple.py
│   ├── inheritance.py
│   └── calls.py
├── php/                 # PHP test data
│   ├── simple.php
│   ├── inheritance.php
│   └── calls.php
├── java/                # Java test data (existing)
│   └── spring/
└── cli_parse/           # CLI test data (existing)
```

**conftest.py Enhancements**:

```python
# tests/conftest.py

@pytest.fixture
def python_simple_file(tmp_path):
    """Fixture: Simple Python file with one function."""
    file_path = tmp_path / "simple.py"
    file_path.write_text("def hello(): pass\n")
    return file_path

@pytest.fixture
def mock_parse_result():
    """Fixture: Standard mock ParseResult for testing."""
    return ParseResult(
        path=Path("test.py"),
        symbols=[
            Symbol(name="test_func", kind=SymbolKind.FUNCTION, ...)
        ],
        imports=[],
        module_docstring="Test module",
    )
```

**Guidelines Document**:

```markdown
# tests/README_AI.md

## Fixture Management

### When to Create a Fixture

1. **Reused ≥3 times** across different test files
2. **Complex setup** requiring multiple steps
3. **External dependencies** (files, network, etc.)

### Where to Put Fixtures

- **Shared fixtures** → tests/conftest.py
- **Language-specific data** → tests/fixtures/{language}/
- **Feature-specific data** → tests/fixtures/{feature}/
- **Test-specific data** → Inline in test file

### Best Practices

- Use descriptive fixture names (python_simple_file, not file1)
- Document fixture purpose in docstring
- Parameterize when testing multiple cases
- Clean up resources in finalizers
```

**Estimated Effort**: 4 hours
**Risk**: Low (additive, no breaking changes)

---

### Story 16.6: Implement Test Directory Reorganization (P2, Optional)

**Goal**: Create scalable directory structure for growing test suite

**Acceptance Criteria**:
- [ ] Tests organized by type (unit/integration/cli/bdd)
- [ ] Tests further organized by feature area
- [ ] All tests discoverable by pytest
- [ ] CI/CD pipeline updated
- [ ] Documentation reflects new structure

**Target Structure**:

```
tests/
├── conftest.py                    # Global fixtures
├── README_AI.md                   # Test organization guide
│
├── unit/                          # Unit tests (820 tests)
│   ├── parsers/                   # Parser tests (500 tests)
│   │   ├── test_parser.py         # Base parser
│   │   ├── python/                # Python parser (50 tests)
│   │   │   ├── test_python_calls.py
│   │   │   ├── test_python_inheritance.py
│   │   │   ├── test_python_import_alias.py
│   │   │   └── test_python_docstring_description.py
│   │   ├── php/                   # PHP parser (80 tests)
│   │   │   ├── test_php_calls.py
│   │   │   ├── test_php_inheritance.py
│   │   │   ├── test_php_import_alias.py
│   │   │   ├── test_php_comment_extraction.py
│   │   │   └── test_php_docstring_extraction.py
│   │   └── java/                  # Java parser (370 tests)
│   │       ├── test_java_parser.py
│   │       ├── test_java_calls.py
│   │       ├── test_java_inheritance.py
│   │       ├── test_java_annotations.py
│   │       ├── test_java_generics.py
│   │       ├── test_java_lambda.py
│   │       ├── test_java_lombok.py
│   │       └── test_java_module.py
│   │
│   ├── extractors/                # Route extractors (150 tests)
│   │   ├── test_route_extractor.py
│   │   ├── test_thinkphp.py
│   │   └── test_spring.py
│   │
│   ├── writers/                   # Document writers (80 tests)
│   │   ├── test_smart_writer.py
│   │   ├── test_smart_writer_adaptive.py
│   │   └── test_smart_writer_docstring.py
│   │
│   ├── symbols/                   # Symbol processing (90 tests)
│   │   ├── test_adaptive_selector.py
│   │   ├── test_symbol_scorer.py
│   │   └── test_adaptive_symbols_config.py
│   │
│   └── core/                      # Core utilities (100 tests)
│       ├── test_file_classifier.py
│       ├── test_error_handling.py
│       └── test_lazy_loading.py
│
├── integration/                   # Integration tests (120 tests)
│   ├── test_json_output.py
│   ├── test_loomgraph_integration.py
│   └── test_backward_compatibility.py
│
├── cli/                           # CLI tests (37 tests)
│   ├── test_cli_parse.py
│   ├── test_cli_json.py
│   └── test_cli_hooks.py
│
├── bdd/                           # BDD tests (33 tests)
│   ├── features/
│   │   ├── help_system.feature
│   │   ├── init_wizard.feature
│   │   └── tech_debt_*.feature
│   ├── test_help_system_bdd.py
│   ├── test_init_wizard_bdd.py
│   └── test_tech_debt_bdd.py
│
├── fixtures/                      # Test data
│   ├── python/
│   ├── php/
│   ├── java/
│   └── cli_parse/
│
└── legacy/                        # Maintained legacy tests
    ├── README.md                  # Archived test documentation
    └── test_hierarchical.py
```

**Migration Script**:

```bash
#!/bin/bash
# scripts/reorganize_tests.py

import shutil
from pathlib import Path

# Define migrations
MIGRATIONS = {
    "tests/test_python_*.py": "tests/unit/parsers/python/",
    "tests/test_php_*.py": "tests/unit/parsers/php/",
    "tests/test_java_*.py": "tests/unit/parsers/java/",
    "tests/test_cli_*.py": "tests/cli/",
    "tests/*_bdd.py": "tests/bdd/",
    # ... more migrations
}

def migrate_files(dry_run=False):
    for pattern, target_dir in MIGRATIONS.items():
        # Use git mv to preserve history
        files = Path("tests").glob(pattern.replace("tests/", ""))
        for file in files:
            target = Path(target_dir) / file.name
            if dry_run:
                print(f"Would move: {file} -> {target}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file), str(target))
                print(f"Moved: {file} -> {target}")

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    migrate_files(dry_run=dry_run)
```

**Usage**:

```bash
# Preview changes
python scripts/reorganize_tests.py --dry-run

# Execute migration
python scripts/reorganize_tests.py

# Verify all tests still pass
pytest tests/ -v

# Update pytest.ini if needed
# (pytest auto-discovers tests in subdirectories)
```

**Estimated Effort**: 1 day (moving) + 1 day (validation)
**Risk**: High (affects all tests, requires careful validation)

**Rollback Plan**:

```bash
# If issues arise, rollback via git
git reset --hard HEAD~1
```

---

## 🎯 Implementation Roadmap

### Phase 1: Critical Fixes (v0.14.1) - 1 Day

**Timeline**: 2026-02-11
**Goals**: Unblock releases, eliminate workarounds

```
Day 1 (2026-02-11)
├── Morning (2h)
│   ├── Story 16.1: Fix fixture trailing newlines (30 min)
│   ├── Validation & testing (30 min)
│   └── Story 16.2: Review legacy tests (1h)
│
└── Afternoon (3h)
    ├── Story 16.2: Clean legacy tests (2h)
    ├── Story 16.3: Unify BDD coverage (1h)
    └── Release prep (commit, push, tag v0.14.1)
```

**Deliverables**:
- ✅ All tests pass ruff without exclusions
- ✅ No git workarounds required
- ✅ Legacy tests documented or removed
- ✅ BDD feature files aligned with tests

**Release**: v0.14.1 (patch release)

---

### Phase 2: Documentation & Guidelines (v0.15.0) - 2 Days

**Timeline**: 2026-02-17 - 2026-02-18 (when scheduling allows)
**Goals**: Improve maintainability for future development

```
Day 1 (2026-02-17)
├── Morning (2h)
│   └── Story 16.4: Clarify test naming (2h)
│
└── Afternoon (3h)
    └── Story 16.5: Fixture guidelines (3h)

Day 2 (2026-02-18)
├── Morning (2h)
│   └── Document test organization (2h)
│
└── Afternoon (2h)
    └── Update tests/README_AI.md (2h)
```

**Deliverables**:
- ✅ Clear test naming conventions
- ✅ Fixture management guidelines
- ✅ Test organization documentation

**Release**: Include in next feature release (v0.15.0)

---

### Phase 3: Structural Optimization (Future) - 1 Week

**Timeline**: TBD (when test suite grows >100 files)
**Goals**: Scalable structure for large test suite

**Triggers for Execution**:
- Test file count exceeds 100
- Team size grows beyond 3 developers
- Frequent complaints about test navigation
- New language support added (TypeScript, Go, Rust)

```
Week 1
├── Day 1-2: Story 16.6 preparation
│   ├── Create migration script
│   ├── Test script on copy of repository
│   └── Review with team
│
├── Day 3-4: Story 16.6 execution
│   ├── Execute migration
│   ├── Update imports if needed
│   ├── Run full test suite
│   └── Fix any issues
│
└── Day 5: Story 16.6 validation
    ├── CI/CD verification
    ├── Documentation updates
    └── Team review
```

**Deliverables**:
- ✅ Tests organized in unit/integration/cli/bdd
- ✅ Language-specific subdirectories
- ✅ Updated documentation
- ✅ CI/CD pipeline validated

---

## 📊 Success Metrics

### Quantitative Metrics

| Metric | Baseline (v0.14.0) | Target (v0.14.1) | Target (v0.15.0) |
|--------|-------------------|------------------|------------------|
| **Ruff lint errors** | 4 (excluded) | 0 | 0 |
| **Git workarounds** | 4 files | 0 files | 0 files |
| **Legacy test files** | 7 files | ≤5 files | ≤5 files |
| **Undocumented tests** | 3 files | 0 files | 0 files |
| **Unused BDD features** | 3 files | 0 files | 0 files |
| **Test pass rate** | 100% (977/977) | 100% | 100% |
| **Core module coverage** | ~90% | ≥90% | ≥90% |

### Qualitative Metrics

- [ ] New contributors can navigate test suite without guidance
- [ ] No manual steps required for clean test runs
- [ ] Test organization documented in README_AI.md
- [ ] CI/CD runs without test-related warnings
- [ ] Fixture reuse patterns established

---

## 🚨 Risk Assessment

### Technical Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| **Breaking tests during fix** | High | Low | Test in isolation, run full suite |
| **Deleting still-used tests** | High | Medium | Grep for references, run full suite |
| **File moves breaking imports** | High | Low (Phase 3) | Use migration script, validate |
| **CI/CD pipeline disruption** | High | Low | Test locally first, phased rollout |

### Process Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| **Scope creep (Phase 3)** | Medium | High | Phase 3 is optional, trigger-based |
| **Time overruns** | Medium | Medium | Phase 1 is time-boxed (1 day max) |
| **Team disagreement** | Low | Low | Phase 3 requires team consensus |

---

## 📚 References

### Related Documents

- **Analysis Report**: Agent output from 2026-02-10 analysis
- **Test Suite Statistics**: 977 passing tests, 87 test files
- **Ruff Configuration**: `pyproject.toml` lines 66-70
- **Pytest Configuration**: `pyproject.toml` lines 72-74

### Related Issues

- GitHub Issue #TBD: Ruff lint errors in legacy tests
- GitHub Issue #TBD: Legacy test cleanup

### Related Epics

- Epic 15: User Onboarding Enhancement (v0.14.0) - Added 33 new BDD tests
- Epic 4: Refactoring + KISS (v0.3.1-v0.4.0) - CLI modularization

---

## 💬 Decision Log

### Decision 1: Phased Approach (2026-02-10)

**Context**: Test suite has issues at multiple priority levels

**Options**:
1. Big bang refactor (all at once)
2. Phased approach (P0 → P1 → P2)
3. Ignore P2, only fix P0/P1

**Decision**: Phased approach (Option 2)

**Rationale**:
- Phase 1 unblocks releases immediately (30 min)
- Phase 2 improves maintainability (2 days)
- Phase 3 is optional, triggered by growth

**Trade-offs**:
- ✅ Lower risk (incremental validation)
- ✅ Faster value delivery (Phase 1)
- ❌ Requires multiple releases

---

### Decision 2: Delete vs Migrate Legacy Tests (2026-02-10)

**Context**: 3 legacy tests have unclear purpose

**Options**:
1. Keep all legacy tests (no action)
2. Delete suspicious tests immediately
3. Review → Document or Delete

**Decision**: Review → Document or Delete (Option 3)

**Rationale**:
- test_operategoods.py: No documentation, no references → DELETE
- test_adaptive_debug.py: Early debug code → DELETE
- test_current_project.py: Needs review, may be useful → EVALUATE

**Trade-offs**:
- ✅ Reduces clutter
- ✅ Documents decisions
- ❌ Requires careful review

---

### Decision 3: BDD Feature Files (2026-02-10)

**Context**: 3 .feature files lack corresponding tests

**Options**:
1. Implement missing BDD tests
2. Delete unused .feature files
3. Keep for future reference

**Decision**: Delete unused .feature files (Option 2)

**Rationale**:
- All have comprehensive unit test coverage
- BDD adds overhead for internal features
- Can recreate if user-facing BDD needed

**Trade-offs**:
- ✅ Eliminates confusion
- ✅ Reduces maintenance
- ❌ Loses BDD perspective (minor)

---

## 📝 Notes

### Lessons Learned

1. **Fixture Generation Pitfalls**: `write_text()` doesn't add trailing newlines automatically
2. **Technical Debt Compounds**: Small workarounds (ruff exclude, git assume-unchanged) accumulate
3. **Documentation Matters**: Unclear test purpose leads to "keep for safety" mentality

### Future Considerations

1. **Test Coverage Tracking**: Consider adding pytest-cov to CI/CD
2. **Test Performance**: Monitor test suite execution time (currently ~5.5s)
3. **Language-Specific Fixtures**: When adding new languages (TypeScript, Go), create dedicated fixture directories from the start

---

**Epic Owner**: @dreamlinx
**Last Updated**: 2026-02-10
**Status**: Ready for Sprint Planning
