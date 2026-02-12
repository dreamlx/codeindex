# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.17.2] - 2026-02-13

### Changed

- **docs/guides/ audit & cleanup**: Full alignment with v0.17.1. Updated 5 guide files (git-hooks-integration, contributing, configuration, configuration-changelog, docstring-extraction) fixing stale versions, wrong URLs, outdated architecture descriptions, and missing version entries.
- **docs/guides/ consolidation**: Removed 3 redundant files (docstring-extraction.md, configuration-changelog.md, migration-v0.6.md). Moved 3 internal files to docs/internal/. Guide count reduced from 14 to 8.
- **Makefile**: Added docs review reminder to pre-release-check.

## [0.17.1] - 2026-02-12

### Changed

- **README.md full restructure**: Reduced from 1255 to 295 lines (-76%). Now a concise navigation hub linking to existing `docs/guides/` content. Removed duplicate sections, updated for v0.17.0 features, fixed stale version claims.
- **CHANGELOG.md trimmed**: Reduced from 1080 to 319 lines (-70%). Removed internal implementation details from v0.6–v0.12, fixed all comparison links (`yourusername` → `dreamlx`), added missing version links (v0.7–v0.17).

## [0.17.0] - 2026-02-12

### Added

- **CLAUDE.md injection via `codeindex init`**: The init wizard now injects a codeindex instructions section into the project's `CLAUDE.md` file, so Claude Code automatically knows to use README_AI.md files on startup. Supports creating new files, prepending to existing files, and idempotent updates via HTML comment markers (`<!-- codeindex:start/end -->`).
- **Interactive wizard Step 5/6**: New "AI agent integration" step asks whether to inject into CLAUDE.md (default: yes). Steps renumbered from 5 to 6.
- **Non-interactive mode support**: `codeindex init --yes` injects into CLAUDE.md by default (safe — it's just markdown).
- **`inject_claude_md()` and `has_claude_md_injection()`**: Public API functions in `init_wizard` module for programmatic use.

## [0.16.1] - 2026-02-12

### Fixed

- **README.md false version claims**: Removed v0.16.0 labels from unimplemented framework route extractors (Laravel, FastAPI, Django, Express.js). These are planned features, not yet released.
- **Updated roadmap**: Fixed "Latest Improvements" section to reflect actual v0.16.0 changes instead of stale v0.14.0 content.

## [0.16.0] - 2026-02-12

### Changed (Breaking)

- **`scan` default mode reversed** (Story 19.1): `codeindex scan` now generates structural documentation by default (no AI required). Use `--ai` flag to enable AI-enhanced documentation. This makes the zero-config experience work out of the box.
- **`scan-all` default mode reversed** (Story 19.1): Same change as `scan` — structural mode is now the default.
- **`--fallback` deprecated**: Flag is now a hidden no-op that prints a deprecation warning. Will be removed in a future version.
- **`--dry-run` requires `--ai`**: Since dry-run previews the AI prompt, it now requires the `--ai` flag.

### Added

- **Pass-through directory skipping** (Story 19.5): Directories with no code files and single subdirectory are automatically skipped during scanning. Avoids redundant README_AI.md in deep structures (e.g., Java Maven `src/main/java/com/...`).
- **Parser installation detection** (Story 19.4): `codeindex init` now checks which tree-sitter parsers are installed and warns about missing ones with install commands.
- **Post-init guidance** (Story 19.2): Init wizard now suggests `scan-all` as immediate next step (works without AI). AI-enhanced docs mentioned as optional.
- **Post-commit hook auto-update**: `codeindex hooks install post-commit` now generates a fully functional hook that runs `codeindex scan` for affected directories and auto-commits updated README_AI.md files.
- **mo-hooks skill**: New Claude Code skill for customers to set up auto-update hooks.

### Improved

- **Java auto-recursive tech-debt** (Story 19.6a): `codeindex tech-debt` automatically enables `--recursive` for Java projects (deep package structures). Removes the old hint message.
- **Language-aware noise analysis** (Story 19.6b): `_analyze_noise_breakdown` now skips getter/setter counting for Java files (JavaBeans convention). Python/PHP noise analysis unchanged.

### Fixed

- **Post-commit hook not updating files**: Generated hook was missing `cd "$REPO_ROOT"`, used pipe subshells causing `git add` to run in wrong context, and `set -e` caused silent failures.

## [0.15.1] - 2026-02-12

### Fixed

- **`scan-all` missing Java files** (BUG-1): Refactored `find_all_directories` and `scan_directory` to use unified `get_language_extensions()` instead of hardcoded extension checks. Adding new languages now only requires updating the `LANGUAGE_EXTENSIONS` dict.
- **`tech-debt` 0 files for Java projects** (BUG-2): Added hint suggesting `--recursive` flag when no files found and Java is configured (deep package structures).
- **Java getter/setter false positives** (IMP-1): Skip naming pattern penalty for Java files where getters/setters are standard JavaBeans convention.

## [0.15.0] - 2026-02-12

### Changed

- **Test Architecture Migration** (Epic 18)
  - Migrated all inheritance tests to template-based generation system
  - Python: 30 tests generated from `test_generator/specs/python.yaml`
  - PHP: 23 tests generated from `test_generator/specs/php.yaml`
  - Java: 29 tests generated from `test_generator/specs/java.yaml`
  - 100% legacy test coverage preserved (63/63 scenarios)
  - 19 additional advanced test scenarios added
  - Single Jinja2 template shared across all languages

### Added

- **Test Generator Tooling** (`test_generator/`)
  - `generator.py`: CLI for YAML + Jinja2 → pytest test generation
  - `specs/`: YAML specifications for Python, PHP, Java inheritance tests
  - `templates/inheritance_test.py.j2`: Shared test template
  - `scripts/`: Analysis and comparison utilities

### Removed

- Legacy hand-written inheritance test files (preserved in `backup/legacy-tests-20260211` branch)

## [0.14.0] - 2026-02-10

### Added

- **Interactive Setup Wizard** (Epic 15 - Story 15.1)
  - Enhanced `codeindex init` with intelligent, step-by-step wizard
  - Smart auto-detection (languages, frameworks, project structure)
  - Non-interactive mode for CI/CD (`--yes`, `--quiet` flags)

- **Enhanced Help System** (Epic 15 - Story 15.3)
  - `codeindex config explain <parameter>`: Detailed parameter help
  - `codeindex init --help-config`: Full configuration reference

- **Single File Parse Command** (Epic 12 - Story 12.1)
  - New `codeindex parse <file>` command for parsing individual source files
  - JSON output with structured data (symbols, imports, namespace)
  - Exit codes: 0 (success), 1 (file error), 2 (unsupported language), 3 (parse error)

### Changed

- **Parser Modularization** (Epic 13)
  - Refactored monolithic `parser.py` (3622 lines) into modular `parsers/` package
  - `BaseLanguageParser`, `PythonParser`, `PhpParser`, `JavaParser`
  - Simplified `parser.py` to 374 lines (-89.7%)

### Fixed

- **Windows Cross-Platform Compatibility**
  - UTF-8 encoding fix for cross-platform README_AI.md files
  - Windows path length optimization (relative paths instead of absolute, 40-60% shorter)

## [0.12.0] - 2026-02-07

### Added

- **Call Relationships Extraction** (Epic 11)
  - **Python**: Function, method, constructor calls with import alias and super() resolution (35 tests)
  - **Java**: Method, static, constructor calls with package import resolution (26 tests)
  - **PHP**: Function, method, static calls with namespace resolution (25 tests)
  - **LoomGraph JSON integration**: Call serialization, round-trip support, backward compatible (12 tests)
  - Unified `Call` dataclass with `CallType` enum across all languages

- **Java Inheritance Extraction** (Epic 10 Part 3)
  - `extends`, `implements`, interface inheritance, generic type handling
  - Nested class support, fully qualified name resolution, `java.lang.*` implicit imports
  - 25 tests covering all scenarios

- **Multi-Language Development Workflow** documentation (600+ lines guide)

## [0.11.0] - 2026-02-06

### Added

- **Lazy Loading for Language Parsers**: Parsers only imported when needed, with caching and helpful error messages

### Changed

- **BREAKING**: Language parsers moved to optional dependencies
  - Install: `pip install ai-codeindex[python]`, `[php]`, `[java]`, or `[all]`

### Migration

- Existing users: `pip install --upgrade ai-codeindex[all]`

## [0.10.1] - 2026-02-06

### Fixed

- **JSON Output Clean Stream**: `--output json` now produces clean JSON without progress messages

## [0.10.0] - 2026-02-06

### Added

- **PHP LoomGraph Integration** (Epic 10 Part 2)
  - PHP inheritance extraction: `extends` (single), `implements` (multiple interfaces)
  - PHP import alias extraction: `use X as Y`, group imports `use A\{B as C, D}`
  - 32 new tests (777 total)

### Changed

- **PHP Use Statement Parsing** (Breaking): Import alias now in `Import.alias` field instead of `Import.names`. `names` field is always `[]` for PHP use statements.

## [0.9.0] - 2026-02-06

### Added

- **LoomGraph Integration Support** (Epic 10 - MVP)
  - `Inheritance` dataclass (child-parent), `Import.alias` field, `ParseResult.inheritances`
  - Python inheritance extraction (single, multiple, nested class relationships)
  - Python import alias extraction (`import X as Y`, `from X import Y as Z`)
  - 67 new tests, integration validation for LoomGraph compatibility

### Changed

- **BREAKING**: Import parsing now creates separate Import objects for each imported name (enables granular alias tracking)

## [0.8.0] - 2026-02-06

### Added

- **Complete Java Language Support** (Epic 7 Complete - 11 Stories, 184 new tests)
  - Advanced features: generic bounds, throws, lambdas, module system (Java 9+)
  - **Spring Framework route extraction**: `@GetMapping`/`@PostMapping`/etc., path composition, path variables
  - **Lombok support**: `@Data`, `@Builder`, `@Getter`/`@Setter`, constructors, logging
  - Robustness: edge cases, error recovery, nested classes, Unicode identifiers

## [0.7.0] - 2026-02-05

### Added

- **Java Language Support** (Epic 7 MVP)
  - Complete parser: classes, interfaces, enums, records, sealed classes, generics
  - **Annotation extraction**: Spring, JPA, Bean Validation with full argument parsing
  - **Spring Framework test suite**: Controllers, Services, Repositories, Entities, Configuration
  - **Parallel directory scanning**: ThreadPoolExecutor, configurable workers, 3-4x speedup
  - **JSON output mode**: `--output json` for machine-readable output
  - **Git hooks configuration**: 5 modes (auto/disabled/async/sync/prompt) in `.codeindex.yaml`

## [0.6.0] - 2026-02-04

### BREAKING CHANGES

**AI Enhancement feature completely removed** — based on real-world testing and KISS principle. SmartWriter output was being replaced (not enhanced) by AI, losing routes tables and method signatures.

Removed: `ai_enhancement` config, multi-turn dialogue, `--strategy`/`--ai-all` options, `ai_enhancement.py` module.

Kept: SmartWriter (core README generation), Docstring Extraction (Epic 9), `FileSizeClassifier`, all 415 tests passing.

**Migration**: Remove `ai_enhancement:` from `.codeindex.yaml`. Use `codeindex scan <dir>` for per-directory AI docs.

### Added

- **AI-Powered Docstring Extraction** (Epic 9): Multi-language normalization (PHP + Python), three modes (off/hybrid/all-ai), batch processing, cost estimation (~$0.15/250 dirs)

## [0.5.0] - 2026-02-03

### Added

- **Git Hooks Integration** (Epic 6, P3.1)
  - `codeindex hooks install/uninstall/status` CLI commands
  - Pre-commit: ruff lint + debug code detection
  - Post-commit: automatic README_AI.md updates with `codeindex affected`
  - Backup & safety: automatic backup/restore of existing hooks

### Documentation

- Configuration upgrade guide (`docs/guides/configuration-changelog.md`, 442 lines)
- CLAUDE.md refactoring (1929 → 496 lines, -74%)

## [0.4.0] - 2026-02-02

### Changed

- **KISS Universal Description Generator** (Story 4.4.5): Complete redesign with zero-assumption, language-agnostic module descriptions. Format: `{path}: {count} {pattern} ({symbol_list})`. Eliminated all hardcoded business domain mappings.

## [0.3.1] - 2026-01-28

### Changed

- **CLI Module Split** (Story 4.3): Refactored monolithic `cli.py` into 6 focused modules (`cli.py`, `cli_common.py`, `cli_scan.py`, `cli_config.py`, `cli_symbols.py`, `cli_tech_debt.py`). 1062 → 31 lines in cli.py (-97.1%).

## [0.3.0] - 2026-01-27

### Configuration Changes
⚠️ New optional sections: `ai_enhancement.strategy`, `tech_debt.*`, multi-turn thresholds. Migration not required — all optional with sensible defaults.

### Added

- **Code Refactoring** (Epic 4): AI Helper module, File Size Classifier, 20 new unit tests
- **Multi-turn Dialogue for Super Large Files** (Epic 3.2): Three-round dialogue for files >5000 lines or >100 symbols, intelligent strategy selection, 22 BDD tests
- **Technical Debt Analysis** (Epic 3.1): Complexity metrics, symbol overload detection, console/markdown/JSON reporting, `tech-debt` CLI command, 69 new tests
- **Adaptive Symbol Extraction** (Epic 2): Dynamic 5-150 symbols per file, 7-tier classification, YAML config, 69 new tests

## [0.1.3] - 2025-01-15

### Added
- `PROJECT_INDEX.json` and `PROJECT_INDEX.md` for codebase navigation

## [0.1.2] - 2025-01-14

### Added
- Parallel scanning support with `codeindex list-dirs`
- `--dry-run` flag for prompt preview
- Status command to check indexing coverage

### Fixed
- Unicode handling in prompts
- Path resolution on Windows

## [0.1.1] - 2025-01-13

### Added
- `--fallback` mode for generating docs without AI
- Configuration validation

### Fixed
- Tree-sitter grammar installation issues
- Import parsing edge cases

## [0.1.0] - 2025-01-12

### Added
- Initial release
- Python code parsing with tree-sitter
- CLI commands: `scan`, `init`, `status`, `list-dirs`
- External AI CLI integration
- Configuration system (`.codeindex.yaml`)
- Symbol extraction (classes, functions, methods, imports)
- README_AI.md generation

[Unreleased]: https://github.com/dreamlx/codeindex/compare/v0.17.2...HEAD
[0.17.2]: https://github.com/dreamlx/codeindex/compare/v0.17.1...v0.17.2
[0.17.1]: https://github.com/dreamlx/codeindex/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/dreamlx/codeindex/compare/v0.16.1...v0.17.0
[0.16.1]: https://github.com/dreamlx/codeindex/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/dreamlx/codeindex/compare/v0.15.1...v0.16.0
[0.15.1]: https://github.com/dreamlx/codeindex/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/dreamlx/codeindex/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/dreamlx/codeindex/compare/v0.12.0...v0.14.0
[0.12.0]: https://github.com/dreamlx/codeindex/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/dreamlx/codeindex/compare/v0.10.1...v0.11.0
[0.10.1]: https://github.com/dreamlx/codeindex/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/dreamlx/codeindex/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/dreamlx/codeindex/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/dreamlx/codeindex/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/dreamlx/codeindex/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/dreamlx/codeindex/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/dreamlx/codeindex/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dreamlx/codeindex/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/dreamlx/codeindex/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/dreamlx/codeindex/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dreamlx/codeindex/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/dreamlx/codeindex/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/dreamlx/codeindex/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dreamlx/codeindex/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dreamlx/codeindex/releases/tag/v0.1.0
