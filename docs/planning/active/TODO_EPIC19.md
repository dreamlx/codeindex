# Epic 19: CLI UX Restructuring + Java Improvements - TODO

**Status**: 🔄 In Progress
**Branch**: `feature/epic19-cli-ux-restructuring`
**Started**: 2026-02-12
**Target Version**: v0.16.0

---

## Story 19.1: Reverse scan/scan-all Default Behavior

### Tests (RED)
- [ ] **T-19.1.1** BDD feature: `tests/features/cli_scan_defaults.feature`
  - Scenario: scan without --ai generates structural output
  - Scenario: scan with --ai invokes AI CLI
  - Scenario: scan with --fallback prints deprecation warning
  - Scenario: scan-all without --ai generates structural output
  - Scenario: --dry-run without --ai prints error
  - Scenario: --ai without ai_command prints clear error
- [ ] **T-19.1.2** BDD step definitions: `tests/test_cli_scan_defaults_bdd.py`

### Implementation (GREEN)
- [ ] **I-19.1.1** `cli_scan.py`: Add `--ai` flag to `scan` command
- [ ] **I-19.1.2** `cli_scan.py`: Default `scan` to structural mode (current `--fallback` behavior)
- [ ] **I-19.1.3** `cli_scan.py`: `--ai` triggers AI mode (current default behavior)
- [ ] **I-19.1.4** `cli_scan.py`: `--fallback` becomes hidden deprecated no-op with warning
- [ ] **I-19.1.5** `cli_scan.py`: `--dry-run` only works with `--ai` (error otherwise)
- [ ] **I-19.1.6** `cli_scan.py`: `--ai` without `ai_command` gives clear error
- [ ] **I-19.1.7** `cli_scan.py`: Update `scan_all` - replace `--no-ai`/`--fallback` with `--ai`
- [ ] **I-19.1.8** Update existing tests that depend on old defaults

---

## Story 19.5: Skip Pass-Through Directories in scan-all

### Tests (RED)
- [ ] **T-19.5.1** Unit tests: `tests/test_scanner_passthrough.py`
  - test: directory with no code + single subdir → skipped
  - test: directory with code files + single subdir → NOT skipped
  - test: directory with no code + multiple subdirs → NOT skipped
  - test: Java Maven structure: skip src/main/java/com/zcyl/, keep leaf
  - test: Python flat structure → no directories skipped

### Implementation (GREEN)
- [ ] **I-19.5.1** `scanner.py`: Add `is_pass_through()` function
- [ ] **I-19.5.2** `scanner.py`: Integrate pass-through filtering in `find_all_directories`

---

## Story 19.6a: Java Auto-Recursive tech-debt

### Tests (RED)
- [ ] **T-19.6a.1** Unit tests in `tests/test_cli_tech_debt.py`
  - test: tech-debt auto-enables recursive when Java in config languages
  - test: explicit --recursive still works
  - test: non-Java projects unaffected (default non-recursive)

### Implementation (GREEN)
- [ ] **I-19.6a.1** `cli_tech_debt.py`: Auto-enable recursive for Java config
- [ ] **I-19.6a.2** `cli_tech_debt.py`: Remove v0.15.1 hint message (no longer needed)

---

## Story 19.6b: Language-Aware Noise Analysis

### Tests (RED)
- [ ] **T-19.6b.1** Unit tests: `tests/test_tech_debt_noise.py`
  - test: Java file with 10 getters/setters → noise ratio < 50%
  - test: Python file with get_xxx → still counted as noise
  - test: PHP file with getXxx → still counted as noise
- [ ] **T-19.6b.2** Symbol scorer tests in `tests/test_symbol_scorer.py`
  - test: Java getter/setter score > 30.0 threshold

### Implementation (GREEN)
- [ ] **I-19.6b.1** `tech_debt.py`: `_analyze_noise_breakdown` skip getter/setter for Java
- [ ] **I-19.6b.2** `symbol_scorer.py`: Boost Java getter/setter score above 30.0

---

## Story 19.4: Parser Installation Detection

### Tests (RED)
- [ ] **T-19.4.1** Unit tests: `tests/test_parser_detection.py`
  - test: check_parser_installed returns True for installed parser
  - test: check_parser_installed returns False for missing parser
  - test: init with all parsers → no warning
  - test: init with missing parser for detected language → warning + install command
  - test: init with zero parsers → prominent warning

### Implementation (GREEN)
- [ ] **I-19.4.1** `init_wizard.py`: Add `check_parser_installed()` function
- [ ] **I-19.4.2** `init_wizard.py`: Add parser check step to wizard
- [ ] **I-19.4.3** `cli_config.py`: Add parser check to non-interactive mode

---

## Story 19.2: Update Init Wizard and Post-Init Flow

### Tests (RED)
- [ ] **T-19.2.1** BDD scenarios in `tests/features/init_wizard.feature`
  - Scenario: AI config step clearly marked as optional
  - Scenario: Post-init suggests scan-all (works immediately)
  - Scenario: Non-interactive mode skips AI config

### Implementation (GREEN)
- [ ] **I-19.2.1** `init_wizard.py`: Mark AI config as "Optional Enhancement"
- [ ] **I-19.2.2** `cli_config.py`: Update post-init message
- [ ] **I-19.2.3** `init_wizard.py`: Update generated config to comment out ai_command

---

## Story 19.3: Update Help Text and Documentation

### Implementation
- [ ] **I-19.3.1** `cli_scan.py`: Update help text for scan/scan-all
- [ ] **I-19.3.2** `cli.py`: Update top-level --help description
- [ ] **I-19.3.3** `README.md`: Update Quick Start section
- [ ] **I-19.3.4** `CHANGELOG.md`: Add v0.16.0 entries

---

## Progress Summary

| Story | Tests | Implementation | Status |
|-------|-------|---------------|--------|
| 19.1: Reverse defaults | ⬜ | ⬜ | Not started |
| 19.5: Skip pass-through | ⬜ | ⬜ | Not started |
| 19.6a: Java auto-recursive | ⬜ | ⬜ | Not started |
| 19.6b: Noise analysis | ⬜ | ⬜ | Not started |
| 19.4: Parser detection | ⬜ | ⬜ | Not started |
| 19.2: Init wizard | ⬜ | ⬜ | Not started |
| 19.3: Help/docs | N/A | ⬜ | Not started |
