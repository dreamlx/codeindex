# codeindex Strategic Roadmap

**Last Updated**: 2026-02-07
**Current Version**: v0.12.0
**Vision**: Universal code indexing platform for AI-assisted development

---

## 📍 Current Status (v0.12.0)

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

### 📚 Version History

| Version | Date | Highlights |
|---------|------|------------|
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

1. 🔥 **Multi-Language Support** (v0.7.0 - v0.8.0)
   - Java, TypeScript, Go, Rust
   - Enterprise adoption enabler
   - Foundation: AI docstring processor (v0.6.0 ✅)

2. 🚀 **Framework Intelligence** (v0.5.0 - v0.9.0)
   - Spring, Laravel, FastAPI, Django
   - Route extraction + business logic mapping
   - Started: ThinkPHP routes (v0.5.0 ✅)

3. 📊 **Real-time Indexing** (v0.7.0+)
   - Watch mode, incremental updates
   - IDE integration (LSP)

4. 🤖 **Advanced AI Features** (v0.8.0+)
   - Code similarity search
   - Dependency impact analysis
   - Automated refactoring suggestions

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
- Release notes: `RELEASE_NOTES_v0.8.0.md`
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
- Release notes: `RELEASE_NOTES_v0.9.0.md`
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
- Release notes: `RELEASE_NOTES_v0.10.0.md`
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

### v0.13.0 - TypeScript Language Support (Target: 2026-03-31)

**Theme**: Web development ecosystem foundation

**Epic**: Epic 8 - TypeScript Support

**Key Features**:
- TypeScript/JavaScript parser (tree-sitter-typescript)
- JSDoc extraction (AI-powered)
- React component detection
- TypeScript type annotations parsing
- LoomGraph Integration (inheritance + import alias)

**Success Criteria**:
- [ ] Parse 95%+ valid TypeScript code
- [ ] Extract JSDoc comments with AI processor
- [ ] Detect React components (@Component, hooks)
- [ ] Generate useful README_AI.md for TS modules

**See**: Planning TBD

---

### v0.14.0 - Framework Intelligence Expansion (Target: 2026-04-30)

**Theme**: Framework-aware code understanding

**Key Features**:
- Express.js route extraction (TypeScript)
- Spring Boot @Service, @Repository mapping
- Business logic pattern recognition
- API endpoint dependency graph
- Cross-framework API comparison

**Success Criteria**:
- [ ] 8+ frameworks supported
- [ ] Business context extraction (auth, payment, orders)
- [ ] API documentation auto-generation

---

### v0.12.0 - Real-time & IDE Integration (Target: 2026-09-01)

**Theme**: Developer productivity

**Key Features**:
- Watch mode (--watch)
- Incremental indexing (git diff based)
- LSP server implementation
- VS Code extension
- JetBrains plugin

**Success Criteria**:
- [ ] <100ms incremental update on file change
- [ ] IDE integration with 10k+ installs
- [ ] Real-time symbol search

---

### v1.0.0 - Production Ready (Target: 2026-12-01)

**Theme**: Stability, performance, ecosystem

**Key Features**:
- Performance optimization (10x faster)
- Distributed indexing (multi-core, multi-machine)
- Plugin ecosystem (community extensions)
- Enterprise features (team collaboration, analytics)
- Comprehensive documentation

**Success Criteria**:
- [ ] 1M+ LOC projects indexed in <5min
- [ ] 100+ community plugins
- [ ] Enterprise customers

---

## 🎯 Feature Priorities Matrix

### P0 (Must Have - Blocking Release)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~Docstring AI Processor~~ | v0.6.0 ✅ | Foundation for multi-language docs |
| Java Parser | v0.7.0 | Enterprise adoption blocker |
| Spring Routes | v0.7.0 | Most popular Java framework |
| TypeScript Parser | v0.8.0 | Web development essential |

### P1 (Should Have - High Impact)

| Feature | Version | Rationale |
|---------|---------|-----------|
| Maven/Gradle Detection | v0.7.0 | Java build system integration |
| Go Parser | v0.8.0 | Cloud-native ecosystem |
| FastAPI Routes | v0.8.0 | Modern Python API framework |

### P2 (Nice to Have - Enhancement)

| Feature | Version | Rationale |
|---------|---------|-----------|
| JavaDoc Extraction | v0.6.0 | Better documentation quality |
| Rust Parser | v0.7.0 | Systems programming community |
| Laravel Routes | v0.8.0 | PHP framework leader |

### P3 (Future - Research)

| Feature | Version | Rationale |
|---------|---------|-----------|
| Code Similarity Search | v0.9.0+ | AI-powered feature |
| Automated Refactoring | v0.9.0+ | Advanced AI use case |
| Team Collaboration | v1.0.0 | Enterprise feature |

---

## 📊 Language Support Priority

**Ranking Criteria**: Popularity + Enterprise Adoption + Community Demand

| Rank | Language | Target Version | Status |
|------|----------|----------------|--------|
| 1 | **Python** | v0.1.0 | ✅ Complete (LoomGraph: v0.9.0) |
| 2 | **PHP** | v0.5.0 | ✅ Complete (LoomGraph: v0.10.0) |
| 3 | **Java** | v0.7.0 | ✅ Complete (LoomGraph: Planned) |
| 4 | **TypeScript/JavaScript** | v0.11.0 | 📋 Planned |
| 5 | **Go** | v0.11.0 | 📋 Planned |
| 6 | **Rust** | v0.11.0 | 📋 Planned |
| 7 | **C#** | v0.12.0 | 📋 Planned |
| 8 | **C++** | v0.12.0 | 📋 Planned |

---

## 🏗️ Framework Support Priority

**Ranking Criteria**: Usage + Route Complexity + Business Value

| Rank | Framework | Language | Target Version | Status |
|------|-----------|----------|----------------|--------|
| 1 | **ThinkPHP** | PHP | v0.5.0 | ✅ Complete |
| 2 | **Spring Boot** | Java | v0.6.0 | 🔄 In Progress |
| 3 | **FastAPI** | Python | v0.7.0 | 📋 Planned |
| 4 | **Django** | Python | v0.7.0 | 📋 Planned |
| 5 | **Express.js** | TypeScript | v0.7.0 | 📋 Planned |
| 6 | **Laravel** | PHP | v0.8.0 | 📋 Planned |
| 7 | **ASP.NET Core** | C# | v0.8.0 | 📋 Planned |
| 8 | **Gin** | Go | v0.8.0 | 📋 Planned |

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

### Active Epics (v0.13.0+ Development)

| Epic | Version | Priority | Status |
|------|---------|----------|--------|
| **Epic 8** | v0.13.0 | P0 | 📋 Planned (TypeScript Language Support) |

### Future Epics

| Epic | Version | Priority | Status |
|------|---------|----------|--------|
| **Epic 8** | v0.13.0 | P0 | 📋 Planned (TypeScript Support) |
| **Epic 6 (P3.2-P3.3)** | v0.14.0 | P1 | 📋 Planned (Laravel, FastAPI Routes) |
| **Epic 5** | v0.15.0+ | P2 | 📋 Deferred (Intelligent Branch Management) |
| **Epic 12** | v0.15.0+ | P1 | 📋 Planned (Real-time Indexing) |

**See**: Individual epic planning docs in `docs/planning/epicN-*.md`

---

## 📈 Success Metrics

### Technical Metrics

| Metric | Current (v0.5.0) | v0.6.0 Target | v1.0.0 Target |
|--------|------------------|---------------|---------------|
| **Languages Supported** | 1 (Python) | 2 (Python, Java) | 8+ |
| **Frameworks Supported** | 1 (ThinkPHP) | 2 (ThinkPHP, Spring) | 10+ |
| **Test Coverage** | 90%+ | 90%+ | 95%+ |
| **Max Project Size** | 100k LOC | 500k LOC | 5M LOC |
| **Indexing Speed** | ~1k LOC/s | ~2k LOC/s | ~10k LOC/s |

### Adoption Metrics

| Metric | Current | v0.6.0 Target | v1.0.0 Target |
|--------|---------|---------------|---------------|
| **GitHub Stars** | <100 | 500+ | 2000+ |
| **Active Users** | <10 | 100+ | 1000+ |
| **Enterprise Users** | 0 | 5+ | 50+ |
| **Contributors** | 1 | 5+ | 20+ |

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
**Next Review**: 2026-03-01 (after v0.7.0 release)
**Maintained By**: @dreamlx + community
**Last Updated**: 2026-02-04
**Current Version**: v0.6.0 (Released 2026-02-04)
