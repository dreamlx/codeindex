# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2026-02-06

### Added

- **Complete Java Language Support** (Epic 7 Complete - 11 Stories)
  - All Java language features now fully supported
  - 184 new tests (662 total passing, 3 skipped)
  - Comprehensive coverage of Java 8-17+ features

- **Advanced Java Features** (Stories 7.1.2.2-7.1.2.5)
  - Generic Bounds: `<T extends Comparable<T>>`, multiple bounds with `&`
  - Throws Declarations: `throws IOException, SQLException`
  - Lambda Expressions: `x -> x * 2`, method references `String::length`
  - Module System (Java 9+): module-info.java, requires/exports/opens
  - 70 new tests for advanced features

- **Spring Framework Route Extraction** (Story 7.2)
  - Plugin-based route extractor for Spring REST controllers
  - Supports `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`
  - Automatic path composition (class-level + method-level `@RequestMapping`)
  - Path variable support: `{id}`, `{userId}`
  - Line number tracking for navigation
  - 11 route extraction tests

- **Lombok Support** (Story 7.1.3.4)
  - Full support for Lombok annotations
  - Code generation: `@Data`, `@Getter`, `@Setter`, `@Builder`
  - Constructors: `@AllArgsConstructor`, `@NoArgsConstructor`, `@RequiredArgsConstructor`
  - Utilities: `@ToString`, `@EqualsAndHashCode`
  - Logging: `@Slf4j`, `@Log`
  - Works with JPA and Spring annotations
  - 21 Lombok tests

- **Robustness Testing** (Stories 7.1.3.2-7.1.3.3)
  - Edge Case Tests: Nested classes, complex generics, Unicode identifiers
  - Error Recovery: Syntax errors, incomplete declarations, malformed code
  - 51 tests for edge cases and error handling

### Changed

- Parser now handles complex Java scenarios (nested classes, varargs, arrays)
- Error recovery strategy: Report errors rather than extract incorrect symbols
- Enhanced annotation extraction to handle dict-format arguments

### Performance

- Parallel directory scanning (from v0.7.0): 3-4x speedup maintained
- Efficient handling of large Java projects

### Documentation

- Added `RELEASE_NOTES_v0.8.0.md` with complete Epic 7 details
- Updated README_AI.md files for src and tests directories

### Dependencies

- tree-sitter-java: 0.21.0 (no changes)
- All dependencies remain stable

## [0.7.0] - 2026-02-05

### Added

- **Java Language Support** (Epic 7: Java Language Support - MVP)
  - Complete Java parser using tree-sitter-java
  - Support for classes, interfaces, enums, records, sealed classes
  - Generic types parsing (`<T extends Comparable<T>>`)
  - Package declarations and imports (regular, static, wildcard)
  - JavaDoc comment extraction
  - 23 comprehensive Java parser tests

- **Java Annotation Extraction** (Story 7.1.2.1)
  - Full annotation parsing for Spring Framework
  - Support for marker annotations (`@Entity`)
  - Annotations with arguments (`@GetMapping("/users")`)
  - Array arguments (`@RequestMapping({"/api", "/v1"})`)
  - Named parameters (`@Column(name = "user_id")`)
  - Spring annotations: `@RestController`, `@Service`, `@Repository`, `@Entity`, `@Autowired`, etc.
  - Bean Validation: `@NotBlank`, `@Email`, `@Size`
  - JPA Lifecycle: `@PrePersist`, `@PreUpdate`
  - 11 annotation extraction tests

- **Spring Framework Test Suite** (Story 7.1.3.1)
  - Comprehensive Spring Boot project testing
  - Controller layer: REST endpoints, parameter annotations
  - Service layer: Business logic, transactional methods
  - Repository layer: JPA repositories, custom queries
  - Entity layer: JPA entities, validation, lifecycle hooks
  - Configuration layer: Spring Boot main, bean definitions
  - Real-world Spring Boot application examples
  - 19 Spring Framework tests

- **Parallel Directory Scanning** (Story 7.1.4.2)
  - ThreadPoolExecutor for concurrent directory processing
  - Configurable `parallel_workers` in `.codeindex.yaml`
  - CLI override: `--parallel N` option
  - 3-4x performance improvement for scan-all operations
  - Graceful handling of edge cases (single dir, workers > dirs)
  - 9 parallel scanning verification tests

- **JSON Output Mode** (Epic: JSON Output Integration)
  - `--output json` flag for machine-readable output
  - Structured error handling with error codes
  - ParseResult serialization with symbols, imports, metadata
  - File-level error detection via tree-sitter
  - Exit code 1 for errors, 0 for success

- **Git Hooks Configuration Support** (Story 6)
  - Full `.codeindex.yaml` configuration for post-commit hooks
  - 5 modes: `auto`, `disabled`, `async`, `sync`, `prompt`
  - Smart detection: ≤2 directories = sync, >2 = async
  - Non-blocking async mode for large projects
  - 14 comprehensive tests for hooks configuration

### Fixed

- Fixed interface extends parsing for generic types (`JpaRepository<User, Long>`)
- Fixed JSON serialization to include annotations field in Symbol
- Fixed test expectations for Symbol.to_dict() output format

### Documentation

- Added `RELEASE_NOTES_v0.7.0.md` with comprehensive release information
- Added `EPIC7_STORY_7.1.2-7.1.4_DESIGN.md` - Epic 7 design and story breakdown
- Added `EPIC7_PERFORMANCE_CORRECTION.md` - Performance analysis and pragmatic decisions
- Added `EPIC7_TEST_STRATEGY.md` - Testing approach and coverage
- Updated `CLAUDE.md` with Java support examples
- Updated `README.md` with Java language support
- Added JSON output examples to Quick Start
- Updated Git Hooks Integration Guide

### Performance

- Parallel scanning: 3-4x improvement for multi-directory projects
- Pragmatic decisions: Skipped micro-optimizations (<3% benefit)
- Memory-efficient: Per-directory processing, immediate release

### Testing

- Total: 517 tests passing, 3 skipped
- New: +39 tests (11 annotations + 19 Spring + 9 parallel)
- Coverage: Java parser, Spring Framework, parallel scanning

## [0.6.0] - 2026-02-04

### ⚠️ BREAKING CHANGES

**AI Enhancement Feature Completely Removed**

Based on real-world PHP project testing and KISS principle evaluation, the AI Enhancement feature (multi-turn dialogue, Phase 2) has been completely removed. This feature was found to:
- **Replace** SmartWriter output instead of enhancing it
- **Lose critical information**: Routes tables, complete method signatures, detailed dependencies
- **Contradict** the "code indexing for AI programming" purpose

**What's Removed:**
- ❌ `ai_enhancement` configuration section
- ❌ Multi-turn dialogue for super large files
- ❌ Phase 2 AI Enhancement in `scan-all`
- ❌ `--strategy` option in `scan` command
- ❌ `--ai-all` option in `scan-all` command
- ❌ `AIEnhancementConfig` class
- ❌ `execute_multi_turn_enhancement()` function
- ❌ `ai_enhancement.py` module (366 lines)

**What's Kept:**
- ✅ SmartWriter (fallback mode) - Core structured README generation
- ✅ Docstring Extraction (Epic 9) - Multi-language documentation normalization
- ✅ FileSizeClassifier - Used by tech_debt module (hardcoded thresholds: 5000 lines, 100 symbols)
- ✅ All 415 tests pass

**Migration Guide:**
1. Remove `ai_enhancement:` section from `.codeindex.yaml`
2. Use `codeindex scan-all` directly (no `--ai-all` needed)
3. For AI-enhanced docs: Use `codeindex scan <dir>` to invoke AI per directory

**Rationale:**
- For Serena MCP users: Fallback mode provides more complete, faster, and information-rich output
- KISS principle: Remove complexity that doesn't add value
- Focus on core mission: Code indexing, not content generation

### Added
- **AI-Powered Docstring Extraction** (Epic 9)
  - Multi-language documentation normalization (PHP + Python)
  - Three modes: `off` (default), `hybrid` (selective AI), `all-ai` (maximum quality)
  - Batch processing: 1 AI call per file (not per symbol)
  - Cost estimation: ~$0.15 for 250 directories (hybrid mode)
  - CLI options: `--docstring-mode`, `--show-cost`
  - Comprehensive documentation (docs/guides/docstring-extraction.md)

### Changed
- `FileSizeClassifier` now uses hardcoded super_large thresholds (5000 lines, 100 symbols)
- `scan-all` command simplified: Generates SmartWriter READMEs only
- `tech_debt` module uses `classifier.super_large_lines` instead of config

### Removed
- All AI Enhancement functionality (see BREAKING CHANGES above)
- 4 test files: multi_turn_dialogue_bdd, super_large_detection_bdd
- Multi-turn related scenarios from BDD test files

### Planning
- **Epic 9: AI-Powered Docstring Extraction** (v0.6.0)
  - Created comprehensive Epic planning document (docs/planning/epic9-docstring-extraction.md)
  - 5 user stories with acceptance criteria and technical design
  - Implementation timeline (2 weeks: 2026-02-03 to 2026-02-15)
  - Cost analysis: <$1 per 250-directory scan (hybrid mode)
  - Real PHP project validation plan (251 dirs, 1926 symbols)
- **Strategic Roadmap Update**
  - Moved PHP docstring extraction to v0.6.0 (was Java in original plan)
  - Moved Java Language Support to v0.7.0 (will reuse Epic 9 AI processor)
  - Priority change rationale: User has real PHP project for immediate validation
  - Multi-language foundation planned for v0.8.0 (TypeScript, Go, Rust)

### Documentation
- **Requirements Workflow Guide** (580 lines)
  - Extracted from CLAUDE.md to separate document
  - Complete dual-track system (Planning Docs + GitHub Issues)
  - 5-step workflow with detailed examples
  - Issue templates (epic.md, feature.md, bug.md, enhancement.md)
- **CLAUDE.md Optimization** (707 → 546 lines, -23%)
  - Reduced Requirements section from 208 to 40 lines (-81%)
  - Added link to detailed requirements-workflow.md
  - Updated version to v0.5.0
  - Improved readability as quick reference
- **README.md Enhancement**
  - Added documentation navigation section
  - Categorized guides: User Guides, Developer Guides, Planning
  - Added links to new documents

### Configuration
- **PROJECT_SYMBOLS.md Control** (v0.5.0+)
  - Added `symbols.project_symbols.enabled: false` configuration
  - Recommended for large projects (>100 files)
  - Rationale: 419KB file (100K tokens) with limited value
  - Better alternatives: PROJECT_INDEX.md + README_AI.md + Serena MCP find_symbol()
  - Updated configuration.md, configuration-changelog.md, examples/.codeindex.yaml

## [0.5.0] - 2026-02-03

### Configuration Changes
✅ **No configuration file changes** - Git Hooks managed via CLI only

See: `docs/guides/configuration-changelog.md` for detailed version-by-version changes

### Documentation
- **Configuration Upgrade Guide** (442 lines)
  - Created `docs/guides/configuration-changelog.md`
  - Version-by-version configuration changes (v0.1.0 → v0.5.0)
  - Migration guides and best practices
  - Backward compatibility matrix
- **CLAUDE.md Refactoring** (1929 → 496 lines, -74%)
  - Reorganized into 4 focused parts for better usability
  - Removed verbose implementation tutorials
  - Added quick reference section
  - Improved documentation structure
- **Enhanced Configuration Guide**
  - Added "Upgrading Your Configuration" section
  - Version compatibility matrix
  - Selective feature adoption guide

### Added - Epic 6, P3.1: Git Hooks Integration
- **Git Hooks Management CLI** - Comprehensive hook management system
  - `codeindex hooks install` - Install hooks with automatic backup
  - `codeindex hooks uninstall` - Uninstall with optional backup restore
  - `codeindex hooks status` - Show hook installation status
- **Pre-commit Hook** - Quality checks before commit
  - L1: Ruff lint check (auto-detects venv or system ruff)
  - L2: Debug code detection (print/breakpoint/pdb)
  - Smart file filtering (skips CLI files)
- **Post-commit Hook** - Automatic documentation updates
  - Smart change analysis (`codeindex affected`)
  - Automatic README_AI.md updates
  - Infinite loop prevention (skips doc-only commits)
- **Backup & Safety**
  - Automatic backup of existing custom hooks
  - Restore backups on uninstall
  - Timestamped backups for multiple versions
- **Integration Documentation**
  - Comprehensive user guide (docs/guides/git-hooks-integration.md)
  - Quick start, troubleshooting, FAQ
  - CI/CD integration examples

### Fixed
- Code style compliance in hierarchical.py and symbol_index.py
  - Fixed line length violations (E501)
  - Fixed unused variable (F841)
  - Fixed bare except (E722)

### Tests
- Added 19 new tests for Git Hooks management (394 total)
- All tests passing

## [0.4.0] - 2026-02-02

### Changed - Story 4.4.5: KISS Universal Description Generator ⭐
- **Complete redesign of semantic description generation** with KISS (Keep It Simple, Stupid) principles
- **Universal language support** - Works for Python, PHP, Java, Go, TypeScript, Rust, C++, and any language
- **Universal architecture support** - MVC, DDD, microservices, layered, hexagonal, game engines, compilers
- **Universal domain support** - E-commerce, gaming, DevOps, scientific computing, and any business domain
- **Zero assumptions approach** - No hardcoded business domains or translations
- **Description format**: `{path}: {count} {pattern} ({symbol_list})`
  - Example: `Admin/Controller: 36 modules (AdminJurUsers, Permission, SystemConfig, ...)`
- **Objective information only** - Lists facts, preserves original symbol names, no interpretation
- **Code simplification**: -78 lines (-17%), more powerful functionality
- **Zero maintenance cost** - No keyword mappings to maintain

### Removed - Story 4.4.5
- **Hardcoded business domain mappings** (~150 lines) - user/order/product/payment/cart/role/permission/auth
- **Architecture keyword priorities** (~80 lines)
- **`_extract_business_domain()` method** (~40 lines)
- **Complex combination logic** (~50 lines)

### Added - Story 4.4.5
- **SimpleDescriptionGenerator class** (~160 lines)
  - Path context extraction
  - Symbol pattern recognition (Controller/Service/Model/Repository/etc.)
  - Entity name extraction (removes common prefixes/suffixes)
  - Smart description formatting
- **Cross-language validation**
  - PHP project (ThinkPHP 5.0): 100+ dirs, 500+ files - ⭐⭐⭐⭐⭐
  - Python project (codeindex): 3 dirs, 52 files - ⭐⭐⭐⭐⭐

### Impact - Story 4.4.5
- **PROJECT_INDEX.md quality**: ⭐⭐ → ⭐⭐⭐⭐⭐ (+150%)
- **Admin vs Agent differentiation**: ❌ Generic → ✅ Perfect distinction
- **Business module recognition**: ❌ "Module directory" → ✅ Clear display (BigWheel, Coupon, Lottery)
- **Generic descriptions eliminated**: 100% resolved
- **Information density**: Significantly improved
- **Traceability**: Original symbol names preserved for code navigation

### Backward Compatibility
- ✅ 100% backward compatible - all existing functionality preserved
- ✅ All 299 tests passing (1 skipped)
- ✅ No configuration changes required
- ✅ Works out of the box

## [0.3.1] - 2026-01-28

### Changed - Epic 4: CLI Module Split (Story 4.3) 🏗️
- **CLI architecture refactored** into 6 focused modules (from 1 monolithic file)
  - `cli.py` - Main entry point and command registration (31 lines, -97%)
  - `cli_common.py` - Shared utilities (console instance)
  - `cli_scan.py` - Core scanning commands (scan, scan-all)
  - `cli_config.py` - Configuration and status commands
  - `cli_symbols.py` - Symbol indexing and dependency analysis
  - `cli_tech_debt.py` - Technical debt analysis
- **Nested functions refactored** into independent helper functions with proper parameters
- **Code organization improved**: 1062 → 31 lines in cli.py (-97.1%)
- **Maintainability enhanced**: Each module has single, clear responsibility
- **No breaking changes**: All commands and options preserved
- All 263 tests passing, zero regressions

## [0.3.0] - 2026-01-27

### Configuration Changes
⚠️ **New optional configuration sections added**:
- `ai_enhancement.strategy` - AI enhancement control
- `tech_debt.*` - Technical debt thresholds
- Multi-turn dialogue thresholds (auto-detected)

**Migration**: Not required - all optional with sensible defaults
See: `docs/guides/configuration-changelog.md#v030-2026-01-27`

### Added - Epic 4: Code Refactoring (Partial) 🔧
- **AI Helper module** (`ai_helper.py`) for reusable enhancement functions
  - `aggregate_parse_results()` - Combines multiple ParseResult objects
  - `execute_multi_turn_enhancement()` - Unified multi-turn dialogue execution
- **File Size Classifier** (`file_classifier.py`) for consistent file size detection
  - `FileSizeCategory` enum with 5 classification levels
  - `FileSizeClassifier` with configurable thresholds
  - Unified detection logic across all modules
- 20 new unit tests (8 ai_helper + 12 classifier) with TDD approach
- 2 BDD feature files (16 + 22 scenarios)

### Changed - Epic 4
- **Code duplication eliminated**: ~110 lines of duplicate code removed
- **scan and scan-all commands** now use shared `execute_multi_turn_enhancement()`
- **tech_debt module** uses `FileSizeClassifier` instead of hard-coded constants
- **ai_enhancement module** uses `FileSizeClassifier` for consistent detection
- **cli.py reduced** from 1131 to 1062 lines (-69 lines, -6%)
- All thresholds now configurable via Config (no magic numbers)

### Added - Epic 3.2: Multi-turn Dialogue for Super Large Files 🚀
- **Super large file detection** with configurable thresholds (>5000 lines OR >100 symbols)
- **Three-round multi-turn dialogue** for complex file documentation:
  - Round 1: Architecture Overview (10KB prompt, 10-20 lines)
  - Round 2: Core Component Analysis (15KB prompt, 30-60 lines)
  - Round 3: Final README Synthesis (15KB prompt, 100+ lines)
- **Symbol grouping by responsibility** (CRUD, Query, Validation, Calculation, Utility)
- **Intelligent strategy selection** (auto/standard/multi_turn)
- `--strategy` CLI option for manual strategy override
- Automatic multi-turn dialogue in `scan-all` for super large files
- Graceful fallback to standard enhancement on failure
- Progress indicators and timing information
- 22 new BDD tests (13 multi-turn + 9 detection scenarios)

### Changed - Epic 3.2
- **scan command** now supports `--strategy` option with auto-detection
- **scan-all command** automatically detects and processes super large files with multi-turn dialogue
- Enhanced CLI output with round-by-round progress tracking

### Added - Epic 3.1: Technical Debt Analysis 🔍
- **Complexity analysis module** with cyclomatic, cognitive, and nesting depth metrics
- **Symbol overload detection** for classes/files with too many methods
- **Technical debt reporting** with multiple output formats:
  - Console: Rich table with emoji indicators
  - Markdown: Detailed report with metrics breakdown
  - JSON: Machine-readable format for CI/CD integration
- `tech-debt` CLI command for project-wide analysis:
  - `codeindex tech-debt` - Console output with summary
  - `codeindex tech-debt --format markdown` - Detailed markdown report
  - `codeindex tech-debt --format json` - JSON export
  - `codeindex tech-debt --output report.md` - Save to file
- Configurable thresholds for complexity and overload detection
- 69 new tests (30 TDD + 5 BDD complexity + 12 TDD + 2 BDD overload + 22 TDD + 5 BDD reporting + 12 CLI integration)

### Changed - Epic 3.1
- **Parser** enhanced with complexity metrics extraction
- **Symbol data models** extended with complexity scores
- CLI refactored with focused helper functions for better maintainability

### Added - Epic 2: Adaptive Symbol Extraction 🎉
⚠️ **Configuration Impact**: New `symbols.adaptive_symbols` section (disabled by default)

- **Adaptive symbol extraction** based on file size (5-150 symbols per file)
- 7-tier file size classification system (tiny/small/medium/large/xlarge/huge/mega)
- `AdaptiveSymbolsConfig` data structure for flexible configuration
- `AdaptiveSymbolSelector` with intelligent limit calculation algorithm
- `file_lines` field in ParseResult for file size tracking
- YAML configuration support for adaptive symbols settings
- 69 new tests for adaptive functionality (18+13+30+8)
- Comprehensive validation report (docs/epic2-validation-report.md)

### Changed - Epic 2
- **SmartWriter** now uses adaptive symbol limits when enabled
- **Config system** supports adaptive_symbols configuration with defaults merging
- **Symbol display** dynamically adjusts from fixed 15 to 5-150 based on file size
- Large file information coverage improved from 26% to 100% (+280%)
- Truncation messages now use filtered symbol count (bug fix)

### Added - Documentation
- Comprehensive documentation structure (docs/)
- Architecture Decision Records (ADR)
- Getting started guide
- Configuration guide
- Roadmap for 2025 Q1
- Epic 2 validation report with real-world testing results

### Changed - Structure
- Migrated design docs to docs/architecture/
- Improved project structure

### Performance
- Adaptive calculation overhead: <1%
- No regression in parsing speed
- Memory usage stable

### Backward Compatibility
- ✅ Adaptive symbols disabled by default (enabled: false)
- ✅ All existing configurations work without modification
- ✅ 66 regression tests passing

## [0.1.3] - 2025-01-15

### Added
- `PROJECT_INDEX.json` and `PROJECT_INDEX.md` for codebase navigation
- System environment reporter example
- Improved README_AI.md auto-generation

### Changed
- Documentation updates
- Version bump to 0.1.3

## [0.1.2] - 2025-01-14

### Added
- Parallel scanning support with `codeindex list-dirs`
- `--dry-run` flag for prompt preview
- Status command to check indexing coverage
- Better error handling for AI CLI failures

### Changed
- Improved CLI output formatting
- Better timeout handling (default 120s)

### Fixed
- Unicode handling in prompts
- Path resolution on Windows

## [0.1.1] - 2025-01-13

### Added
- `--fallback` mode for generating docs without AI
- Configuration validation
- Example `.codeindex.yaml` in examples/

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
- Basic test suite

### Features
- Parse Python files and extract symbols
- Generate documentation via external AI CLI
- Configurable include/exclude patterns
- Timeout and error handling
- Development mode installation

[Unreleased]: https://github.com/yourusername/codeindex/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/yourusername/codeindex/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/yourusername/codeindex/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/yourusername/codeindex/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/yourusername/codeindex/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/yourusername/codeindex/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/codeindex/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/yourusername/codeindex/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/yourusername/codeindex/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/yourusername/codeindex/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/yourusername/codeindex/releases/tag/v0.1.0
