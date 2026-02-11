# codeindex Strategic Roadmap

**Last Updated**: 2026-02-11
**Current Version**: v0.14.0 (+ Epic 16 test cleanup)
**Vision**: Universal Code Parser - Best-in-class multi-language AST parser for AI-assisted development
**Positioning**: Focused on code parsing and structured data extraction, not AI analysis

---

## 📍 Current Status (v0.14.0)

### ✅ Completed Capabilities

| Feature | Version | Status |
|---------|---------|--------|
| **Python Support** | v0.1.0 | ✅ Full support |
| **Adaptive Symbol Extraction** | v0.2.0 | ✅ 5-150 symbols/file |
| **Technical Debt Analysis** | v0.3.0 | ✅ Complexity metrics |
| **CLI Modularization** | v0.3.1 | ✅ 6 focused modules |
| **KISS Description Generator** | v0.4.0 | ✅ Universal patterns |
| **Git Hooks Integration** | v0.5.0 | ✅ Pre/Post-commit |
| **Framework Routes (ThinkPHP)** | v0.5.0 | ✅ Plugin architecture |
| **AI-Powered Docstring Extraction** | v0.6.0 | ✅ Universal doc processor |
| **Java Language Support (MVP)** | v0.7.0 | ✅ Parser + JavaDoc |
| **Java Language Support (Complete)** | v0.8.0 | ✅ Spring Routes + Lombok |
| **LoomGraph Integration (Python)** | v0.9.0 | ✅ Knowledge graph data |
| **LoomGraph Integration (PHP)** | v0.10.0 | ✅ Inheritance + Import Alias |
| **Lazy Loading Architecture** | v0.11.0 | ✅ Optional language parsers |
| **Call Relationships Extraction** | v0.12.0 | ✅ Python/Java/PHP calls |
| **Single File Parse Command** | v0.13.0 | ✅ CLI parse tool integration |
| **Parser Modularization** | v0.13.0 | ✅ 3622→374 lines refactoring |
| **Windows Platform Compatibility** | v0.13.0 | ✅ UTF-8 + Path optimization |
| **Interactive Setup Wizard** | v0.14.0 | ✅ Smart defaults + Auto-detection |
| **Enhanced Help System** | v0.14.0 | ✅ Configuration documentation |
| **Test Suite Refactoring** | v0.14.0+ | ✅ Legacy cleanup + 100% BDD coverage |

### 📚 Version History

| Version | Date | Highlights |
|---------|------|------------|
| **v0.14.0** | 2026-02-10 | 🎯 User Onboarding Enhancement (Interactive Wizard + Help System) |
| **v0.13.0** | 2026-02-08 | 🚀 Single File Parse + Parser Refactoring + Windows Support |
| **v0.12.0** | 2026-02-07 | 🔗 Call Relationships Extraction (Python/Java/PHP + LoomGraph) |
| **v0.11.0** | 2026-02-06 | 🏗️ Lazy Loading Architecture (Optional Language Parsers) |
| **v0.10.0** | 2026-02-06 | 🎯 PHP LoomGraph Integration (Inheritance + Import Alias) |
| **v0.9.0** | 2026-02-06 | 🔥 Python LoomGraph Integration (Inheritance + Import Alias) |
| **v0.8.0** | 2026-02-06 | 🚀 Java Complete (Spring Routes + Lombok + Advanced Features) |
| **v0.7.0** | 2026-02-05 | ☕ Java Language Support (MVP) + Spring Framework Testing |
| **v0.6.0** | 2026-02-04 | 🔥 AI-Powered Docstring Extraction, ⚠️ Removed AI Enhancement |
| **v0.5.0** | 2026-02-03 | Git Hooks Integration, Framework Routes (ThinkPHP) |
| **v0.4.0** | 2026-02-02 | KISS Universal Description Generator |
| **v0.3.1** | 2026-01-28 | CLI Module Split (6 focused modules) |
| **v0.3.0** | 2026-01-27 | Tech Debt Analysis |
| **v0.2.0** | 2025-01-15 | Adaptive Symbol Extraction (5-150 symbols) |
| **v0.1.3** | 2025-01-15 | Project Indexing (PROJECT_INDEX.md) |
| **v0.1.2** | 2025-01-14 | Parallel Scanning |
| **v0.1.0** | 2025-01-12 | Initial Release (Python support) |

**See**: `CHANGELOG.md` for detailed version notes

### 🎯 Strategic Focus Areas

**2026 Priorities** (Ranked by Impact):

1. 🔥 **Multi-Language Support** (v0.15.0 - v0.19.0)
   - TypeScript/JavaScript, Go, Rust, C#
   - Enterprise adoption enabler
   - Foundation: Parser modularization (Epic 13 ✅)
   - Completed: Python (v0.1.0 ✅), PHP (v0.5.0 ✅), Java (v0.7.0-v0.8.0 ✅)

2. 🚀 **Framework Intelligence** (v0.17.0)
   - Express, Laravel, FastAPI, Django
   - Route extraction + business logic mapping
   - Completed: ThinkPHP (v0.5.0 ✅), Spring (v0.8.0 ✅)

3. 📊 **Cross-Platform Support** (v0.13.1+)
   - Windows, macOS, Linux compatibility
   - CI/CD automation across platforms
   - Foundation: Windows compatibility (Epic 14 ✅)

4. 🔗 **Tool Integration** (v0.13.0+)
   - Single file parsing for tool chains
   - JSON output for downstream tools
   - LoomGraph integration (knowledge graph)
   - Completed: parse command (Epic 12 ✅)

---

## 🗓️ Version Roadmap

### v0.6.0 - AI-Powered Docstring Extraction ✅ (Released: 2026-02-04)

**Theme**: Universal documentation comment understanding with AI

**Epic**: Epic 9 - AI-Powered Docstring Extraction

**⚠️ BREAKING CHANGE**: AI Enhancement feature removed (see `docs/guides/migration-v0.6.md`)

**What Was Delivered**:
- ✅ AI-powered docstring processor (hybrid + all-AI modes)
- ✅ PHP docstring extraction (PHPDoc, inline comments, mixed language)
- ✅ Configuration & CLI options (`--docstring-mode`, `--show-cost`)
- ✅ Cost optimization (batch processing, <$1 per 250 dirs)
- ✅ Breaking change: Removed AI Enhancement (multi-turn dialogue)

**Success Criteria** (All Achieved):
- [x] Extract docstrings from 80%+ of PHP methods ✅
- [x] AI cost <$1 per 250-directory scan (hybrid mode) ✅ (~$0.15)
- [x] Quality: ⭐⭐ → ⭐⭐⭐⭐⭐ (README_AI.md descriptions) ✅
- [x] Universal architecture reusable for Java/TypeScript/Go ✅

**Technical Approach**:
- **NO traditional parsers** (PHPDocParser, JavaDocParser) - KISS principle
- **AI understands all formats** naturally (structured, unstructured, mixed language)
- **Batch processing** (1 AI call per file, not per comment)
- **Hybrid mode** (simple extraction + selective AI for cost efficiency)

**Tests**: 415 passing, 3 skipped
**Files Changed**: 32 files, 3445 insertions, 2586 deletions

**Documentation**:
- User guide: `docs/guides/docstring-extraction.md`
- Migration guide: `docs/guides/migration-v0.6.md`
- Epic plan: `docs/planning/epic9-docstring-extraction.md`

---

### v0.7.0 - Java Language Support (MVP) ✅ (Released: 2026-02-05)

**Theme**: Enterprise Java ecosystem foundation

**Epic**: Epic 7 - Java Language Support (Part 1: MVP)

**Foundation**: Builds on Epic 9 AI docstring processor (v0.6.0)

**What Was Delivered**:
- ✅ Java parser using tree-sitter-java
- ✅ Support for classes, interfaces, enums, records, sealed classes
- ✅ Generic types parsing (`<T extends Comparable<T>>`)
- ✅ Package declarations and imports (regular, static, wildcard)
- ✅ JavaDoc comment extraction (AI-powered)
- ✅ Full annotation parsing for Spring Framework
- ✅ Spring Framework comprehensive test suite (19 tests)

**Success Criteria** (All Achieved):
- [x] Parse 95%+ valid Java code ✅
- [x] Extract Spring annotations with full metadata ✅
- [x] Handle Spring Boot projects efficiently ✅
- [x] Generate useful README_AI.md for Java modules ✅
- [x] Reuse AI docstring processor from Epic 9 ✅

**Tests**: 478 passing (23 Java parser + 11 annotation + 19 Spring = 53 new tests)

**Documentation**:
- Epic plan: `docs/planning/epic7-java-support.md`
- Updated README_AI.md files

**See**: CHANGELOG.md v0.7.0 entry

---

### v0.8.0 - Java Language Support (Complete) ✅ (Released: 2026-02-06)

**Theme**: Complete Java ecosystem support

**Epic**: Epic 7 - Java Language Support (Part 2: Advanced Features + Routes)

**What Was Delivered**:
- ✅ Advanced Java Features (70 new tests)
  - Generic Bounds: `<T extends Comparable<T>>`, multiple bounds with `&`
  - Throws Declarations: `throws IOException, SQLException`
  - Lambda Expressions: `x -> x * 2`, method references `String::length`
  - Module System (Java 9+): module-info.java, requires/exports/opens

- ✅ Spring Framework Route Extraction (11 tests)
  - Plugin-based route extractor for Spring REST controllers
  - Supports all HTTP methods: @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
  - Automatic path composition (class-level + method-level @RequestMapping)
  - Path variable support: {id}, {userId}
  - Line number tracking for navigation

- ✅ Lombok Support (21 tests)
  - Full support for Lombok annotations
  - Code generation: @Data, @Getter, @Setter, @Builder
  - Constructors: @AllArgsConstructor, @NoArgsConstructor, @RequiredArgsConstructor
  - Utilities: @ToString, @EqualsAndHashCode
  - Logging: @Slf4j, @Log

- ✅ Robustness Testing (51 tests)
  - Edge cases: Nested classes, complex generics, Unicode identifiers
  - Error recovery: Syntax errors, incomplete declarations, malformed code

**Success Criteria** (All Achieved):
- [x] Complete Java 8-17+ feature support ✅
- [x] Spring route extraction with 100% accuracy ✅
- [x] Lombok annotation handling ✅
- [x] Robust error recovery ✅

**Tests**: 662 passing (184 new tests), 3 skipped

**Documentation**:
- Release notes: `docs/releases/RELEASE_NOTES_v0.8.0.md`
- Updated README_AI.md files

**See**: CHANGELOG.md v0.8.0 entry

---

### v0.9.0 - LoomGraph Integration ✅ (Released: 2026-02-06)

**Theme**: Knowledge graph data extraction for AI-assisted development

**Epic**: Epic 10 - LoomGraph Integration (MVP)

**What Was Delivered**:
- ✅ Knowledge Graph Data Structures (Story 10.3)
  - `Inheritance` dataclass (child-parent relationships)
  - Extended `Import` with `alias` field
  - `ParseResult.inheritances` list
  - Full JSON serialization support

- ✅ Python Inheritance Extraction (Story 10.1.1)
  - Single inheritance: `class Child(Parent)`
  - Multiple inheritance: `class Child(Parent1, Parent2)`
  - Nested class inheritance with full paths
  - Generic type handling (strips type parameters)
  - 21 comprehensive tests

- ✅ Python Import Alias Extraction (Story 10.2.1)
  - Granular per-name import tracking
  - Module imports: `import numpy as np`
  - From imports: `from datetime import datetime as dt`
  - 19 import alias tests

- ✅ LoomGraph Integration Validation (13 tests)
  - JSON format validation
  - Real-world example: `examples/loomgraph_sample.py`
  - Sample output: `examples/loomgraph_output.json`

**Success Criteria** (All Achieved):
- [x] Extract Python inheritance relationships ✅
- [x] Extract import aliases for knowledge graphs ✅
- [x] JSON output compatible with LoomGraph ✅
- [x] Backward compatible with existing tools ✅

**Tests**: 729 passing (67 new tests), 3 skipped

**Documentation**:
- Release notes: `docs/releases/RELEASE_NOTES_v0.9.0.md`
- Epic plan: `docs/planning/epic10-loomgraph-integration.md`
- Updated README_AI.md files

**See**: CHANGELOG.md v0.9.0 entry

---

### v0.10.0 - PHP LoomGraph Integration ✅ (Released: 2026-02-06)

**Theme**: Extend knowledge graph support to PHP

**Epic**: Epic 10 Part 2 - PHP LoomGraph Integration

**What Was Delivered**:
- ✅ PHP Inheritance Extraction (Story 10.1.2)
  - Extends relationships: `class Child extends Parent`
  - Implements relationships: `class User implements Auth, Loggable`
  - Combined: `class Admin extends User implements Authorizable`
  - Namespace resolution via use_map
  - 17 comprehensive tests

- ✅ PHP Import Alias Extraction (Story 10.2.2)
  - Alias in `Import.alias` field (not `names`)
  - Group imports: `use A\{B as C, D}`
  - `names` always empty `[]` for PHP
  - 15 import alias tests

- ✅ PHP LoomGraph Integration Testing (Story 10.3)
  - 16 integration tests validating format
  - Real-world patterns (Laravel, Symfony)
  - Example: `examples/loomgraph_sample.php`
  - JSON output: `examples/loomgraph_php_output.json`

**Success Criteria** (All Achieved):
- [x] Extract PHP inheritance relationships ✅
- [x] Extract PHP import aliases ✅
- [x] JSON output compatible with LoomGraph ✅
- [x] Consistent with Python implementation ✅

**Tests**: 777 passing (48 new tests), 3 skipped

**Documentation**:
- Release notes: `docs/releases/RELEASE_NOTES_v0.10.0.md`
- Epic plans: `docs/planning/completed/epic10-loomgraph-integration/`
  - `part1-python-plan.md` (v0.9.0)
  - `part2-php-plan.md` (v0.10.0)

**Breaking Changes**: PHP Import.alias field migration (minor)

**See**: CHANGELOG.md v0.10.0 entry

---

### v0.11.0 - Lazy Loading Architecture ✅ (Released: 2026-02-06)

**Theme**: Performance optimization through optional language dependencies

**What Was Delivered**:
- ✅ Lazy loading for language parsers (only import when needed)
- ✅ Parser caching to avoid re-initialization
- ✅ Optional dependencies: `pip install ai-codeindex[python]`, `[php]`, `[java]`, `[all]`
- ✅ Helpful error messages when language parser not installed
- ✅ Reduced installation complexity (no unnecessary dependencies)

**Breaking Changes**:
- Language parsers moved to optional dependencies
- Users must reinstall with extras: `pip install --upgrade ai-codeindex[all]`

**Success Criteria** (All Achieved):
- [x] PHP projects don't require tree-sitter-java ✅
- [x] Python projects don't require tree-sitter-php ✅
- [x] Parsers loaded on-demand ✅
- [x] Backward compatible with existing code ✅

**Tests**: 783 passing (+6 new), 3 skipped

**Documentation**:
- Migration guide in CHANGELOG.md
- Updated installation instructions

**See**: CHANGELOG.md v0.11.0 entry

---

### v0.12.0 - Call Relationships Extraction ✅ (Released: 2026-02-07)

**Theme**: Complete knowledge graph foundation with call relationships

**Epic**: Epic 11 - Call Relationships Extraction

**What Was Delivered**:
- ✅ Python call extraction (Story 11.1)
  - Function/method/constructor calls
  - Import alias resolution
  - super() call resolution
  - 35 tests passing (100%)

- ✅ Java call extraction (Story 11.2)
  - Method/constructor calls
  - Package import resolution
  - super/this call resolution
  - 26 tests passing (100%)

- ✅ PHP call extraction (Story 11.3)
  - Function/method/static calls
  - Namespace resolution (use statements)
  - parent:: call resolution
  - 25 tests passing (100%)

- ✅ LoomGraph integration (Story 11.4)
  - JSON serialization for calls
  - Round-trip serialization
  - Backward compatibility
  - 12 tests passing (100%)

**Success Criteria** (All Achieved):
- [x] Extract call relationships from Python/Java/PHP ✅
- [x] Alias/namespace resolution (98%+ accuracy) ✅
- [x] Inheritance-based resolution (super/parent) ✅
- [x] Dynamic call detection ✅
- [x] JSON output compatible with LoomGraph ✅
- [x] 98 new tests passing (100% success rate) ✅

**Actual Results**:
- **Duration**: 10 days (target was 14-21 days, 50% faster)
- **Tests**: 98 tests passing, 0 failures (100% success rate)
- **Performance**: ~0.04-0.05s per file
- **Call Accuracy**: ~98% (exceeded target of 95%)

**See**:
- `docs/planning/completed/epic11-final-summary.md`
- `docs/planning/completed/epic11-story11.1-completion.md`
- `docs/planning/completed/epic11-story11.2-completion.md`
- `docs/planning/completed/epic11-story11.3-completion.md`
- `docs/development/multi-language-support-workflow.md`

---

### v0.13.0 - Tool Integration & Platform Support ✅ (Released: 2026-02-08)

**Theme**: Architectural completeness and cross-platform compatibility

**Epics**: Epic 12, 13, 14

**What Was Delivered**:

#### Epic 12: Single File Parse Command ✅
- ✅ `codeindex parse <file>` CLI command for single file parsing
- ✅ JSON output format (consistent with scan --output json)
- ✅ Multi-language support (Python, PHP, Java)
- ✅ Framework route extraction (ThinkPHP, Spring)
- ✅ Complete documentation and integration examples
- ✅ 20+ tests passing (100% success rate)

#### Epic 13: Parser Modularization ✅
- ✅ Refactored monolithic `parser.py` (3622 lines → 374 lines, -89.7%)
- ✅ Created modular `parsers/` package:
  - `BaseLanguageParser` abstract base class (138 lines)
  - `PythonParser` for Python parsing (1020 lines)
  - `PhpParser` for PHP parsing (1094 lines)
  - `JavaParser` for Java parsing (1265 lines)
  - Shared utilities in `utils.py` (53 lines)
- ✅ Benefits: Improved maintainability, enhanced extensibility, reduced technical debt
- ✅ 100% backward compatible, all 931 tests passing

#### Epic 14: Windows Platform Compatibility ✅
- ✅ UTF-8 encoding fix for cross-platform files
  - Fixed 5 files: `writer.py`, `hierarchical.py`, `config.py`, `cli_symbols.py`
  - Ensures README_AI.md files work across Windows/Linux/macOS
- ✅ Windows path length optimization (Issue #8)
  - 40-60% path length reduction using relative paths
  - Fixed `should_exclude()` function
  - Enhanced `**` glob pattern matching
  - 13 new tests added, all 944 tests passing
- ✅ Fixed existing bug: `**/__pycache__/**` pattern now works correctly

**Success Criteria** (All Achieved):
- [x] Single file parsing for Python/PHP/Java ✅
- [x] Parser modularization (resolve large file technical debt) ✅
- [x] Windows UTF-8 encoding compatibility ✅
- [x] Windows path length issue resolved ✅
- [x] No regressions (944/944 tests passing) ✅

**Tests**: 944 passing (+27 new tests), 11 skipped

**Documentation**:
- Release notes: `CHANGELOG.md` v0.13.0 entry
- Epic plans: `docs/planning/active/epic12-*.md`, `epic13-*.md`
- Analysis: `docs/development/windows-*-analysis-*.md`

**See**: CHANGELOG.md v0.13.0 entry

---

### v0.13.1 - Windows CI Testing (Target: 2026-02-10)

**Theme**: Complete Windows platform support

**Epic**: Epic 10 (完成) - Windows Platform Compatibility

**What Will Be Delivered**:
- [ ] Add GitHub Actions Windows CI workflow
- [ ] Test on actual Windows environment (Windows 10, Windows 11)
- [ ] Verify UTF-8 encoding fix on Windows
- [ ] Verify path length optimization on Windows
- [ ] Cross-platform test suite (Windows, macOS, Linux)

**Success Criteria**:
- [ ] CI runs on Windows, macOS, Linux
- [ ] All 944 tests pass on all platforms
- [ ] UTF-8 files work correctly across platforms
- [ ] Deep directory structures work on Windows

**Tests**: Existing 944 tests, verify cross-platform

**Documentation**:
- Update README with Windows CI badge
- Issue #9: Windows testing and CI

**See**: `docs/planning/active/` (TBD)

---

### v0.14.0 - User Onboarding Enhancement ✅ (Released: 2026-02-10)

**Theme**: First-time user experience and intelligent setup automation

**Epic**: Epic 15 - User Onboarding Enhancement (用户引导体验增强)

**What Was Delivered**:

#### Story 15.1: Interactive Setup Wizard ✅
- ✅ Enhanced `codeindex init` with step-by-step wizard
- ✅ Auto-detection of project languages (Python, PHP, Java only - parser-supported)
- ✅ Smart defaults for include/exclude patterns
- ✅ Auto-tuning of performance settings (parallel_workers, batch_size)
- ✅ Framework detection (Spring, ThinkPHP, Laravel)
- ✅ Optional Git Hooks installation with mode selection
- ✅ CODEINDEX.md AI integration guide generation
- ✅ Optional AI CLI configuration (Claude, ChatGPT, custom)
- ✅ Non-interactive mode with `--yes` and `--quiet` flags (CI/CD support)
- ✅ 18 BDD test scenarios, all passing

#### Story 15.3: Enhanced Help System ✅
- ✅ Comprehensive configuration parameter documentation
- ✅ Context-aware help (shows current values, validates against system resources)
- ✅ `codeindex config explain <parameter>` command
- ✅ `codeindex init --help-config` for full reference
- ✅ Rich terminal formatting with recommendations and trade-offs
- ✅ 15 BDD test scenarios, all passing

**Success Criteria** (All Achieved):
- [x] New users complete setup in <1 minute ✅
- [x] Non-interactive mode for CI/CD ✅ (`--yes --quiet` flags)
- [x] Smart defaults require zero manual configuration ✅
- [x] Help system provides comprehensive reference ✅
- [x] 33 BDD tests passing (100% success rate) ✅

**Tests**: 977 passing (33 new BDD tests), 0 failures

**Documentation**:
- Epic plan: `docs/planning/active/epic15-user-onboarding.md`
- Feature file: `tests/features/init_wizard.feature` (18 scenarios)
- Feature file: `tests/features/help_system.feature` (15 scenarios)

**Language Support Note**:
- Language detection supports Python, PHP, Java (parser-supported)
- JavaScript, TypeScript, Go, Rust, Ruby are NOT yet supported (no parsers)
- Future language support planned for v0.15.0+

**See**: CHANGELOG.md v0.14.0 entry

---

### v0.15.0 - TypeScript/JavaScript Language Support (Target: 2026-03-31)

**Theme**: Web development ecosystem foundation

**Epic**: Epic 16 - TypeScript/JavaScript Support

**Key Features**:
- TypeScript/JavaScript parser (tree-sitter-typescript)
- JSDoc extraction (AI-powered docstring processor)
- React component detection
- TypeScript type annotations parsing
- LoomGraph Integration (inheritance + import alias + calls)

**Success Criteria**:
- [ ] Parse 95%+ valid TypeScript/JavaScript code
- [ ] Extract JSDoc comments with AI processor
- [ ] Detect React components (@Component, hooks)
- [ ] Generate useful README_AI.md for TS modules
- [ ] 50+ tests passing (90%+ coverage)

**Estimated Duration**: 3-4 weeks

**See**: Planning TBD

---

### v0.16.0 - Go Language Support (Target: 2026-05-31)

**Theme**: Cloud-native ecosystem

**Epic**: Epic 17 - Go Support

**Key Features**:
- Go parser (tree-sitter-go)
- Package/Module analysis
- Interface implementation relationships
- GoDoc extraction
- LoomGraph Integration (inheritance + import alias + calls)

**Success Criteria**:
- [ ] Parse 95%+ valid Go code
- [ ] Extract GoDoc comments
- [ ] Detect interface implementations
- [ ] Generate useful README_AI.md for Go packages
- [ ] 40+ tests passing (90%+ coverage)

**Estimated Duration**: 2-3 weeks

**See**: Planning TBD

---

### v0.17.0 - Framework Intelligence Expansion (Target: 2026-07-31)

**Theme**: Framework-aware code understanding

**Epic**: Epic 18 - Framework Routes Expansion

**Key Features**:
- Express.js route extraction (TypeScript/JavaScript)
- Laravel route extraction (PHP)
- FastAPI route extraction (Python)
- Django route extraction (Python)

**Success Criteria**:
- [ ] 8+ frameworks supported (ThinkPHP, Spring, Express, Laravel, FastAPI, Django, Gin, ASP.NET)
- [ ] Consistent route extraction API
- [ ] Framework-specific documentation

**Estimated Duration**: 1-2 weeks per framework

**See**: Planning TBD

---

### v0.18.0 - Rust Language Support (Target: 2026-09-30)

**Theme**: Systems programming

**Epic**: Epic 19 - Rust Support

**Key Features**:
- Rust parser (tree-sitter-rust)
- Cargo project analysis
- Trait implementation relationships
- RustDoc extraction
- LoomGraph Integration

**Success Criteria**:
- [ ] Parse 95%+ valid Rust code
- [ ] Extract RustDoc comments
- [ ] Detect trait implementations
- [ ] 40+ tests passing

**Estimated Duration**: 2-3 weeks

---

### v0.19.0 - C# Language Support (Target: 2026-11-30)

**Theme**: .NET ecosystem

**Key Features**:
- C# parser (tree-sitter-c-sharp)
- .NET project analysis
- Interface implementation relationships
- XML documentation extraction

**Estimated Duration**: 2-3 weeks

---

### v1.0.0 - Production Ready (Target: 2026-12-31)

**Theme**: Universal Code Parser - Stability, performance, completeness

**Positioning**: Best-in-class multi-language AST parser and structured data extractor

**What v1.0.0 Means**:

**Must Have** (Core Features):
- ✅ **8+ Languages Supported** (Python, PHP, Java, TypeScript, JavaScript, Go, Rust, C#)
- ✅ **10+ Framework Routes** (ThinkPHP, Spring, Express, Laravel, FastAPI, Django, Gin, ASP.NET, etc.)
- ✅ **Complete Parse Capabilities**:
  - Symbol extraction (classes, functions, methods)
  - Call relationships extraction
  - Inheritance relationships extraction
  - Import/alias extraction
  - Docstring/comments extraction (AI-powered)
- ✅ **Performance**: 1M+ LOC projects parsed in <5min
- ✅ **Stability**: 95%+ parse success rate across all languages
- ✅ **Cross-Platform**: Windows, macOS, Linux fully supported
- ✅ **Test Coverage**: 95%+ code coverage, 2000+ tests passing
- ✅ **Documentation**: Complete API docs, integration guides, examples

**Should Have** (Quality & Integration):
- [ ] Plugin ecosystem (community language/framework parsers)
- [ ] LoomGraph integration for all languages
- [ ] Performance optimization (10x faster than v0.1.0)
- [ ] Comprehensive error handling and recovery
- [ ] Multi-core parallel parsing

**NOT Included in v1.0.0** (Moved to LoomGraph):
- ❌ AI-driven code similarity search → LoomGraph v0.3.0
- ❌ Automated refactoring suggestions → LoomGraph v0.4.0
- ❌ Team collaboration features → LoomGraph v0.5.0
- ❌ IDE deep integration (LSP server) → LoomGraph v0.6.0

**Success Criteria**:
- [ ] 8+ languages with 95%+ parse accuracy
- [ ] 1M+ LOC in <5min
- [ ] 2000+ tests passing
- [ ] Production deployments at 10+ companies
- [ ] 1000+ GitHub stars
- [ ] Active community (50+ contributors)

---

## 🎯 Feature Priorities Matrix

### P0 (Must Have - Blocking Release)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~Docstring AI Processor~~ | v0.6.0 ✅ | Foundation for multi-language docs |
| ~~Java Parser~~ | v0.7.0-v0.8.0 ✅ | Enterprise adoption blocker |
| ~~Spring Routes~~ | v0.8.0 ✅ | Most popular Java framework |
| TypeScript Parser | v0.15.0 | Web development essential |

### P1 (Should Have - High Impact)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~Maven/Gradle Detection~~ | v0.7.0 ✅ | Java build system integration |
| Go Parser | v0.16.0 | Cloud-native ecosystem |
| FastAPI Routes | v0.17.0 | Modern Python API framework |

### P2 (Nice to Have - Enhancement)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~JavaDoc Extraction~~ | v0.6.0 ✅ | Better documentation quality |
| Rust Parser | v0.18.0 | Systems programming community |
| Laravel Routes | v0.17.0 | PHP framework leader |

### ⚠️ Features Moved to LoomGraph

The following features have been **migrated to LoomGraph** for better architectural separation:

| Feature | Moved To | Rationale |
|---------|----------|-----------|
| **Code Similarity Search** | LoomGraph v0.3.0 | Requires vector embeddings + semantic search (Jina + PGVector) |
| **Automated Refactoring Suggestions** | LoomGraph v0.4.0 | Requires knowledge graph + AI analysis (Apache AGE + LLM) |
| **Team Collaboration** | LoomGraph v0.5.0 | Enterprise feature, requires graph storage + user management |
| **IDE Integration (LSP)** | LoomGraph v0.6.0 | Real-time features better suited for graph-based system |

**Reason for Migration**:
- codeindex focuses on **code parsing** (AST → structured data)
- LoomGraph focuses on **AI analysis** (structured data → knowledge graph → insights)
- Clean separation of concerns, better performance, independent evolution

---

## 📊 Language Support Priority

**Ranking Criteria**: Popularity + Enterprise Adoption + Community Demand

| Rank | Language | Target Version | Status |
|------|----------|----------------|--------|
| 1 | **Python** | v0.1.0 | ✅ Complete (Parsing + LoomGraph: v0.9.0) |
| 2 | **PHP** | v0.5.0 | ✅ Complete (Parsing + LoomGraph: v0.10.0) |
| 3 | **Java** | v0.7.0-v0.8.0 | ✅ Complete (Parsing + Spring Routes) |
| 4 | **TypeScript/JavaScript** | v0.15.0 | 📋 Planned (Epic 16) |
| 5 | **Go** | v0.16.0 | 📋 Planned (Epic 17) |
| 6 | **Rust** | v0.18.0 | 📋 Planned (Epic 19) |
| 7 | **C#** | v0.19.0 | 📋 Planned |
| 8 | **C++** | v1.0.0 | 📋 Planned |

---

## 🏗️ Framework Support Priority

**Ranking Criteria**: Usage + Route Complexity + Business Value

| Rank | Framework | Language | Target Version | Status |
|------|-----------|----------|----------------|--------|
| 1 | **ThinkPHP** | PHP | v0.5.0 | ✅ Complete (Route extraction) |
| 2 | **Spring Boot** | Java | v0.8.0 | ✅ Complete (Route extraction) |
| 3 | **FastAPI** | Python | v0.17.0 | 📋 Planned (Epic 18) |
| 4 | **Django** | Python | v0.17.0 | 📋 Planned (Epic 18) |
| 5 | **Express.js** | TypeScript | v0.17.0 | 📋 Planned (Epic 18) |
| 6 | **Laravel** | PHP | v0.17.0 | 📋 Planned (Epic 18) |
| 7 | **ASP.NET Core** | C# | v1.0.0 | 📋 Planned |
| 8 | **Gin** | Go | v1.0.0 | 📋 Planned |

---

## 🚀 Epic Overview

### Completed Epics

| Epic | Version | Summary |
|------|---------|---------|
| **Epic 2** | v0.2.0 | Adaptive Symbol Extraction (5-150 symbols) |
| **Epic 3** | v0.3.0 | Tech Debt Analysis + ~~AI Enhancement~~ (removed v0.6.0) |
| **Epic 4** | v0.3.0-v0.4.0 | Code Refactoring + KISS Description |
| **Epic 6 (P3.1)** | v0.5.0 | Git Hooks Integration |
| **Epic 9** | v0.6.0 | AI-Powered Docstring Extraction |
| **Epic 7** | v0.7.0-v0.8.0 | Java Language Support (Complete) |
| **Epic 10 (Part 1-2)** | v0.9.0-v0.10.0 | LoomGraph Integration (Python + PHP) |
| **Epic 11** | v0.12.0 | Call Relationships Extraction (Python/Java/PHP) |
| **Epic 12** | v0.13.0 | Single File Parse Command |
| **Epic 13** | v0.13.0 | Parser Modularization (3622→374 lines) |
| **Epic 14** | v0.13.0 | Windows Platform Compatibility (UTF-8 + Path) |

### Active Epics (v0.13.1+ Development)

| Epic | Version | Priority | Status |
|------|---------|----------|--------|
| **Epic 10 (Part 3)** | v0.13.1 | P0 | 🔄 In Progress (Windows CI Testing) |

### Future Epics

| Epic | Version | Priority | Status |
|------|---------|----------|--------|
| **Epic 15** | v0.14.0 | P0 | 📋 Planned (TypeScript/JavaScript Support) |
| **Epic 16** | v0.15.0 | P0 | 📋 Planned (Go Language Support) |
| **Epic 17** | v0.16.0 | P1 | 📋 Planned (Framework Routes Expansion) |
| **Epic 19** | v0.17.0 | P1 | 📋 Planned (Rust Language Support) |

### Epics Moved to LoomGraph

| Epic | LoomGraph Version | Reason |
|------|-------------------|--------|
| **Epic 20** | v0.3.0 | Code Similarity Search (requires vector embeddings) |
| **Epic 21** | v0.4.0 | Refactoring Suggestions (requires graph + AI) |
| **Epic 22** | v0.5.0 | Team Collaboration (enterprise features) |

**See**: Individual epic planning docs in `docs/planning/epicN-*.md`

---

## 📈 Success Metrics

### Technical Metrics

| Metric | Current (v0.13.0) | v0.14.0 Target | v1.0.0 Target |
|--------|-------------------|----------------|---------------|
| **Languages Supported** | 3 (Python, PHP, Java) | 4 (+ TypeScript/JS) | 8+ |
| **Frameworks Supported** | 2 (ThinkPHP, Spring) | 4 (+ Express, FastAPI) | 10+ |
| **Test Coverage** | 90%+ | 90%+ | 95%+ |
| **Max Project Size** | 500k LOC | 1M LOC | 5M LOC |
| **Indexing Speed** | ~2k LOC/s | ~5k LOC/s | ~10k LOC/s |
| **Tests Passing** | 944 | 1000+ | 2000+ |
| **Platforms Supported** | 3 (macOS, Linux, Windows) | 3 (CI validated) | 3 (Production-ready) |

### Adoption Metrics

| Metric | Current (v0.13.0) | v0.14.0 Target | v1.0.0 Target |
|--------|-------------------|----------------|---------------|
| **GitHub Stars** | <100 | 300+ | 2000+ |
| **Active Users** | <20 | 100+ | 1000+ |
| **Enterprise Users** | 1+ | 10+ | 50+ |
| **Contributors** | 1 | 5+ | 20+ |
| **Language Parsers** | 3 | 4 | 8+ |
| **Framework Extractors** | 2 | 4 | 10+ |

---

## 🔄 Iteration Principles

**Agile Approach**:
1. **Iterative**: Each version delivers working features
2. **User-Driven**: Prioritize based on user feedback
3. **Quality First**: 90%+ test coverage, comprehensive docs
4. **Backward Compatible**: No breaking changes until v2.0.0

**Release Cadence**:
- **Minor Versions** (v0.X.0): Every 4-8 weeks
- **Patch Versions** (v0.X.Y): As needed (bug fixes)
- **Major Version** (v1.0.0): When production-ready criteria met

**Feature Flags**:
- New languages/frameworks: Opt-in initially
- Experimental features: Hidden behind flags
- Deprecated features: Warn 2 versions before removal

---

## 🎯 Strategic Decisions

### Why Java First? (v0.6.0)

**Rationale**:
1. **Enterprise Adoption**: Java dominates enterprise software
2. **User Demand**: Feedback from large Java projects
3. **Market Gap**: Few tools handle Java + Spring well
4. **Revenue Potential**: Enterprise users = paid features

**Alternatives Considered**:
- TypeScript: Web-focused, smaller enterprise footprint
- Go: Growing but smaller market
- Rust: Too niche for now

**Decision**: Java first, TypeScript second (v0.7.0)

### Why Framework Routes? (v0.5.0-v0.8.0)

**Rationale**:
1. **Business Context**: Routes = API surface = business logic
2. **High Value**: Developers need API overview most
3. **Differentiator**: Most indexers don't extract routes
4. **Extensible**: Plugin architecture scales to many frameworks

### Why Defer Epic 5? (Intelligent Branch Management)

**Rationale**:
1. **Lower Priority**: Multi-language support more urgent
2. **Complexity**: Requires multi-agent orchestrator (Epic 6 full)
3. **Limited Demand**: Nice-to-have vs must-have
4. **Resource Constraint**: Focus on core indexing first

**Revisit**: After v0.8.0 when foundation is solid

---

## 📚 Documentation Roadmap

### v0.6.0 Documentation

- [ ] User Guide: Java project setup
- [ ] User Guide: Spring Framework integration
- [ ] Developer Guide: Adding new language support
- [ ] Developer Guide: Parser plugin architecture
- [ ] API Reference: Java parser API
- [ ] Tutorial: Migrating from Javadoc to codeindex

### v1.0.0 Documentation

- [ ] Complete API reference
- [ ] Architecture deep dive
- [ ] Plugin development guide
- [ ] Enterprise deployment guide
- [ ] Performance tuning guide
- [ ] Contribution guidelines

---

## 🤝 Community & Contribution

### Open Source Strategy

**Current Phase** (v0.1.0 - v0.8.0):
- Core development by maintainers
- Community feedback via GitHub Issues
- Contributions welcome (after v0.6.0)

**Future Phase** (v0.9.0+):
- Active community contributions
- Plugin ecosystem
- Bounty program for features

### Contribution Areas

**Immediate** (v0.6.0):
- Bug reports and testing
- Documentation improvements
- Framework extractor examples

**Soon** (v0.7.0+):
- New language parsers
- Framework route extractors
- Performance optimizations
- IDE integrations

---

## ❓ FAQ

**Q: Why not support Language X in v0.6.0?**
A: Strategic focus on Java (enterprise adoption). Language X may come in v0.7.0 or later.

**Q: Will v1.0.0 support all languages?**
A: No. v1.0.0 targets 8 major languages. Long tail via plugins.

**Q: Is codeindex production-ready now?**
A: For Python projects, yes. For enterprise multi-language projects, wait for v1.0.0.

**Q: Can I contribute a language parser?**
A: Yes! See CONTRIBUTING.md (after v0.6.0). Start with Epic 7 as reference.

**Q: Will there be a paid version?**
A: Core features remain open-source. Enterprise features (team collaboration, analytics) may be paid in v1.0.0+.

---

## 🔗 Related Documents

- **Epic Plans**: `docs/planning/epicN-*.md`
- **Version Execution Plans**: `docs/planning/vX.Y.Z-execution-plan.md`
- **CHANGELOG**: `CHANGELOG.md`
- **GitHub Issues**: https://github.com/dreamlx/codeindex/issues
- **GitHub Milestones**: https://github.com/dreamlx/codeindex/milestones

---

**Roadmap Status**: 🎯 Active
**Next Review**: 2026-03-31 (after v0.14.0 release)
**Maintained By**: @dreamlx + community
**Last Updated**: 2026-02-08
**Current Version**: v0.13.0 (Released 2026-02-08)
