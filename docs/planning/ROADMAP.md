# codeindex Strategic Roadmap

**Last Updated**: 2026-03-06
**Current Version**: v0.23.0
**Vision**: Universal Code Parser - Best-in-class multi-language AST parser for AI-assisted development
**Positioning**: Focused on code parsing and structured data extraction, not AI analysis

---

## 📍 Current Status (v0.21.0)

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
| **Test Architecture Migration** | v0.15.0 | ✅ YAML+Jinja2 template system |
| **Java scan-all + tech-debt fixes** | v0.15.1 | ✅ Unified extension checking |
| **CLI UX Restructuring** | v0.16.0 | ✅ Zero-AI default, --ai opt-in |
| **CLAUDE.md Injection** | v0.17.0 | ✅ AI agent auto-onboarding |
| **Docs Consolidation** | v0.17.2 | ✅ Guides 14→8, stale content fixed |
| **Init Setup Flow** | v0.17.3 | ✅ Config review → scan → hooks |
| **Enriched Overview/Navigation** | v0.18.0 | ✅ Recursive stats, smart descriptions, Key Components |
| **Real Project Validation** | v0.18.0 | ✅ 3-layer validation framework (L1/L2/L3) |
| **TypeScript/JavaScript Support** | v0.19.0 | ✅ Full TS/JS/TSX/JSX parsing |
| **Enhanced Tech-Debt Detection** | v0.20.0 | ✅ 5 dimensions, language-aware thresholds |
| **SmartWriter Modularization** | v0.20.0 | ✅ Writers package refactor |
| **Swift/Objective-C Support** | v0.21.0 | ✅ iOS/macOS parsing, .h/.m association |

### 📚 Version History

| Version | Date | Highlights |
|---------|------|------------|
| **v0.21.0** | 2026-03-06 | 🍎 Swift/Objective-C support for iOS/macOS development |
| **v0.20.0** | 2026-02-20 | 🔍 Enhanced tech-debt (5 dims) + SmartWriter modularization |
| **v0.19.0** | 2026-02-19 | 📘 TypeScript/JavaScript language support |
| **v0.18.0** | 2026-02-18 | 📊 Enriched overview/navigation README + validation framework |
| **v0.17.3** | 2026-02-13 | 🔧 Improved CLAUDE.md setup flow for AI agent onboarding |
| **v0.17.2** | 2026-02-13 | 📚 Docs audit & consolidation (14→8 guides) |
| **v0.17.1** | 2026-02-12 | 📝 README.md restructure (-76%), CHANGELOG trim (-70%) |
| **v0.17.0** | 2026-02-12 | 🤖 CLAUDE.md injection via `codeindex init` |
| **v0.16.1** | 2026-02-12 | 🐛 Fix false v0.16.0 claims in README |
| **v0.16.0** | 2026-02-12 | 🎨 CLI UX Restructuring (Epic 19) - zero-AI default |
| **v0.15.1** | 2026-02-12 | 🐛 Java scan-all fix, tech-debt hint, getter/setter scoring |
| **v0.15.0** | 2026-02-12 | 🧪 Test Architecture Migration (YAML+Jinja2 template system) |
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

1. 🌐 **Multi-Language Support** (v0.18.0+)
   - Go, Rust, C#
   - Enterprise adoption enabler
   - Foundation: Parser modularization (Epic 13 ✅)
   - Completed: Python (v0.1.0 ✅), PHP (v0.5.0 ✅), Java (v0.7.0-v0.8.0 ✅), TypeScript/JavaScript (v0.19.0 ✅)

2. 🚀 **Framework Intelligence** (v0.20.0+)
   - Express, Laravel, FastAPI, Django
   - Route extraction + business logic mapping
   - Completed: ThinkPHP (v0.5.0 ✅), Spring (v0.8.0 ✅)

3. 🤖 **Multi-Agent Onboarding** (v0.20.0+)
   - Support Cursor, Windsurf, Cline, GitHub Copilot instruction injection
   - Unified instruction template across AI coding tools
   - Foundation: CLAUDE.md injection (v0.17.0 ✅)

4. 🔥 ~~CLI UX & Quality~~ (v0.16.0 ✅)
   - Zero-AI-required default experience
   - Java project quality improvements

5. 🔗 **Tool Integration** (v0.13.0+ ✅)
   - Single file parsing, JSON output, LoomGraph integration

---

## 🗓️ Version Roadmap

### Completed Versions (v0.6.0 - v0.18.0)

<details>
<summary>Click to expand completed version details</summary>

#### v0.6.0 - AI-Powered Docstring Extraction ✅ (Released: 2026-02-04)
- AI-powered docstring processor (hybrid + all-AI modes)
- PHP docstring extraction (PHPDoc, inline comments, mixed language)
- **Epic 9** | Tests: 415 passing

#### v0.7.0 - Java Language Support (MVP) ✅ (Released: 2026-02-05)
- Java parser (tree-sitter-java), Spring annotations, JavaDoc
- **Epic 7 Part 1** | Tests: 478 passing

#### v0.8.0 - Java Language Support (Complete) ✅ (Released: 2026-02-06)
- Advanced Java (generics, lambdas, modules), Spring routes, Lombok
- **Epic 7 Part 2** | Tests: 662 passing

#### v0.9.0 - LoomGraph Integration (Python) ✅ (Released: 2026-02-06)
- Python inheritance + import alias extraction, JSON format
- **Epic 10 Part 1** | Tests: 729 passing

#### v0.10.0 - LoomGraph Integration (PHP) ✅ (Released: 2026-02-06)
- PHP inheritance + import alias extraction
- **Epic 10 Part 2** | Tests: 777 passing

#### v0.11.0 - Lazy Loading Architecture ✅ (Released: 2026-02-06)
- Optional language parsers, lazy loading, parser caching
- Tests: 783 passing

#### v0.12.0 - Call Relationships Extraction ✅ (Released: 2026-02-07)
- Python/Java/PHP call extraction with alias/namespace resolution
- **Epic 11** | Tests: 98 new, total passing

#### v0.13.0 - Tool Integration & Platform Support ✅ (Released: 2026-02-08)
- Single file parse, parser modularization, Windows compatibility
- **Epics 12, 13, 14** | Tests: 944 passing

#### v0.14.0 - User Onboarding Enhancement ✅ (Released: 2026-02-10)
- Interactive setup wizard, enhanced help system
- **Epic 15** | Tests: 977 passing

#### v0.15.0 - Test Architecture Migration ✅ (Released: 2026-02-12)
- YAML spec + Jinja2 template test generation system
- Migrated Python/PHP/Java inheritance tests to template system
- Removed legacy test directories, 11K+ lines cleaned up
- **Epic 18** | Tests: 991 passing

#### v0.15.1 - Bug Fixes ✅ (Released: 2026-02-12)
- Fixed scan-all missing Java files (unified extension checking)
- Added tech-debt hint for Java recursive scanning
- Fixed getter/setter false positives in Java symbol scoring
- Tests: 991 passing

#### v0.16.0 - CLI UX Restructuring ✅ (Released: 2026-02-12)
- Reversed scan defaults: structural mode is default, `--ai` is opt-in
- Deprecated `--fallback` flag (no-op with warning)
- Skip pass-through directories in scan-all (31% fewer redundant READMEs)
- Java auto-recursive tech-debt, language-aware noise analysis
- **Epic 19** | Tests: 1049 passing

#### v0.17.0 - CLAUDE.md Injection ✅ (Released: 2026-02-12)
- `codeindex init` injects instructions into CLAUDE.md automatically
- Idempotent updates via HTML comment markers
- AI agents auto-discover codeindex on session start
- Tests: 1049 passing

#### v0.17.1-v0.17.3 - Documentation & Onboarding ✅ (Released: 2026-02-13)
- README.md restructure (-76%), CHANGELOG trim (-70%)
- Docs/guides audit & consolidation (14→8 files)
- Improved CLAUDE.md template with setup flow (review config → scan → hooks)
- Tests: 1060 passing

</details>

---

#### v0.18.0 - Enriched Overview/Navigation README ✅ (Released: 2026-02-18)
- Recursive stats aggregation, smart module descriptions, Key Components table
- 2-level directory tree in overview, real project validation framework
- Tests: 1066 passing

#### v0.19.0 - TypeScript/JavaScript Language Support ✅ (Released: 2026-02-19)
- TypeScriptParser: single class handles .ts/.tsx/.js/.jsx with 3 grammar variants
- Symbol extraction: classes, functions, interfaces, enums, type aliases, arrow functions, namespaces
- Import/export: ES modules, CommonJS require, type-only, re-exports, barrel exports
- Inheritance + call graphs + React component detection + decorators
- **Epic 20** | Tests: 77 new (68 unit + 9 integration), 1143 total passing

#### v0.20.0 - Enhanced Tech-Debt Detection ✅ (Released: 2026-02-20)
- Expanded from 2 to 5 detection dimensions with language-aware thresholds
- Long method detection (>80 lines MEDIUM, >150 lines HIGH)
- Too many functions detection (>15 per file MEDIUM)
- High import coupling detection (>8 internal imports MEDIUM)
- 3-tier file size thresholds (800/1500/2500 for compact languages)
- SmartWriter modularization (864 lines → modular writers/ package)
- **Issue #20** | Tests: 25 new tech-debt tests, 55 total tech-debt tests

#### v0.21.0 - Swift/Objective-C Language Support ✅ (Released: 2026-03-06)
- Swift parser: classes, structs, enums, protocols, extensions, property wrappers, generics
- Objective-C parser: @interface/@implementation, .h/.m association (≥95% accuracy), @protocol, categories
- NS_ASSUME_NONNULL preprocessing for Apple framework macros
- Bridging header detection for mixed Swift/Objective-C projects
- Tech-debt language-specific noise thresholds (objc: 70%, swift: 60%)
- Real-world validation: slock-app (814 files, 91.5% association accuracy)
- **Epic 23** | Tests: 74 new (23 Swift + 51 Objective-C), 1422 total passing (13 skipped)

</details>

---

### v0.22.0 - Go Language Support

**Theme**: Cloud-native ecosystem

**Epic**: Epic 21 - Go Support

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

---

### v0.23.0 - Framework Intelligence Expansion

**Theme**: Framework-aware code understanding

**Epic**: Epic 24 - Framework Routes Expansion

**Key Features**:
- Express.js route extraction (TypeScript/JavaScript)
- Laravel route extraction (PHP)
- FastAPI route extraction (Python)
- Django route extraction (Python)

**Success Criteria**:
- [ ] 6+ frameworks supported (ThinkPHP, Spring, Express, Laravel, FastAPI, Django)
- [ ] Consistent route extraction API
- [ ] Framework-specific documentation

**Estimated Duration**: 1-2 weeks per framework

---

### v0.24.0 - Rust Language Support

**Theme**: Systems programming

**Epic**: Epic 25 - Rust Support

**Key Features**:
- Rust parser (tree-sitter-rust)
- Cargo project analysis
- Trait implementation relationships
- RustDoc extraction
- LoomGraph Integration

**Estimated Duration**: 2-3 weeks

---

### v0.25.0 - C# Language Support

**Theme**: .NET ecosystem

**Epic**: Epic 26 - C# Support

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
- ✅ **8+ Framework Routes** (ThinkPHP, Spring, Express, Laravel, FastAPI, Django, Gin, ASP.NET)
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

---

## 🎯 Feature Priorities Matrix

### P0 (Must Have - Blocking Release)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~Docstring AI Processor~~ | v0.6.0 ✅ | Foundation for multi-language docs |
| ~~Java Parser~~ | v0.7.0-v0.8.0 ✅ | Enterprise adoption blocker |
| ~~Spring Routes~~ | v0.8.0 ✅ | Most popular Java framework |
| ~~CLI UX Restructuring~~ | v0.16.0 ✅ | Affects all new users (zero-AI default) |
| ~~TypeScript Parser~~ | v0.19.0 ✅ | Web development essential |

### P1 (Should Have - High Impact)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~Maven/Gradle Detection~~ | v0.7.0 ✅ | Java build system integration |
| Go Parser | v0.20.0 | Cloud-native ecosystem |
| FastAPI Routes | v0.21.0 | Modern Python API framework |

### P2 (Nice to Have - Enhancement)

| Feature | Version | Rationale |
|---------|---------|-----------|
| ~~JavaDoc Extraction~~ | v0.6.0 ✅ | Better documentation quality |
| Rust Parser | v0.22.0 | Systems programming community |
| Laravel Routes | v0.21.0 | PHP framework leader |
| Multi-Agent Onboarding | v0.21.0 | Support Cursor, Windsurf, Cline, Copilot |

### ⚠️ Features Moved to LoomGraph

| Feature | Moved To | Rationale |
|---------|----------|-----------|
| **Code Similarity Search** | LoomGraph v0.3.0 | Requires vector embeddings + semantic search |
| **Automated Refactoring Suggestions** | LoomGraph v0.4.0 | Requires knowledge graph + AI analysis |
| **Team Collaboration** | LoomGraph v0.5.0 | Enterprise feature, requires graph storage |
| **IDE Integration (LSP)** | LoomGraph v0.6.0 | Real-time features better suited for graph system |

---

## 📊 Language Support Priority

**Ranking Criteria**: Popularity + Enterprise Adoption + Community Demand

| Rank | Language | Target Version | Status |
|------|----------|----------------|--------|
| 1 | **Python** | v0.1.0 | ✅ Complete (Parsing + LoomGraph: v0.9.0) |
| 2 | **PHP** | v0.5.0 | ✅ Complete (Parsing + LoomGraph: v0.10.0) |
| 3 | **Java** | v0.7.0-v0.8.0 | ✅ Complete (Parsing + Spring Routes) |
| 4 | **TypeScript/JavaScript** | v0.19.0 | ✅ Complete (Parsing + Calls: v0.19.0) |
| 5 | **Go** | v0.20.0 | 📋 Planned (Epic 21) |
| 6 | **Rust** | v0.22.0 | 📋 Planned (Epic 24) |
| 7 | **C#** | v0.23.0 | 📋 Planned (Epic 25) |
| 8 | **C++** | v1.0.0 | 📋 Planned |

---

## 🏗️ Framework Support Priority

**Ranking Criteria**: Usage + Route Complexity + Business Value

| Rank | Framework | Language | Target Version | Status |
|------|-----------|----------|----------------|--------|
| 1 | **ThinkPHP** | PHP | v0.5.0 | ✅ Complete |
| 2 | **Spring Boot** | Java | v0.8.0 | ✅ Complete |
| 3 | **FastAPI** | Python | v0.21.0 | 📋 Planned (Epic 23) |
| 4 | **Django** | Python | v0.21.0 | 📋 Planned (Epic 23) |
| 5 | **Express.js** | TypeScript | v0.21.0 | 📋 Planned (Epic 23) |
| 6 | **Laravel** | PHP | v0.21.0 | 📋 Planned (Epic 23) |
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
| **Epic 15** | v0.14.0 | User Onboarding Enhancement (Interactive Wizard) |
| **Epic 16** | v0.14.0+ | Test Suite Refactoring (BDD coverage) |
| **Epic 18** | v0.15.0 | Test Architecture Migration (YAML+Jinja2 templates) |
| **Epic 19** | v0.16.0 | CLI UX Restructuring + Java Improvements |
| **Epic 20** | v0.19.0 | TypeScript/JavaScript Support (77 tests) |

### Future Epics

| Epic | Version | Priority | Status |
|------|---------|----------|--------|
| **Epic 21** | v0.20.0 | P1 | 📋 Planned (Go Language Support) |
| **Epic 22** | v0.21.0 | P2 | 📋 Planned (Multi-Agent Onboarding) |
| **Epic 23** | v0.21.0 | P1 | 📋 Planned (Framework Routes Expansion) |
| **Epic 24** | v0.22.0 | P2 | 📋 Planned (Rust Language Support) |
| **Epic 25** | v0.23.0 | P2 | 📋 Planned (C# Language Support) |

### Deferred Epics

| Epic | Reason |
|------|--------|
| **Epic 6 (Full)** | Multi-Agent Orchestrator - Lower priority, revisit after core languages |
| **Windows CI** | v0.13.1 Windows CI testing - Deferred, local testing sufficient |

### Epics Moved to LoomGraph

| Epic | LoomGraph Version | Reason |
|------|-------------------|--------|
| Code Similarity Search | v0.3.0 | Requires vector embeddings |
| Refactoring Suggestions | v0.4.0 | Requires graph + AI |
| Team Collaboration | v0.5.0 | Enterprise features |

---

## 📈 Success Metrics

### Technical Metrics

| Metric | Current (v0.19.0) | Next Target (v0.20.0) | v1.0.0 Target |
|--------|-------------------|----------------------|---------------|
| **Languages Supported** | 5 (Python, PHP, Java, TS, JS) | 6 (+Go) | 8+ |
| **Frameworks Supported** | 2 (ThinkPHP, Spring) | 2 | 10+ |
| **Test Coverage** | 90%+ | 90%+ | 95%+ |
| **Tests Passing** | 1143 | 1200+ | 2000+ |
| **Max Project Size** | 500k LOC | 1M LOC | 5M LOC |
| **Platforms Supported** | macOS, Linux (Windows partial) | + Windows CI | 3 (Production-ready) |

---

## 🔄 Iteration Principles

**Agile Approach**:
1. **Iterative**: Each version delivers working features
2. **User-Driven**: Prioritize based on user feedback
3. **Quality First**: 90%+ test coverage, comprehensive docs
4. **Backward Compatible**: No breaking changes until v2.0.0

**Release Cadence**:
- **Minor Versions** (v0.X.0): Every 2-4 weeks
- **Patch Versions** (v0.X.Y): As needed (bug fixes)
- **Major Version** (v1.0.0): When production-ready criteria met

---

## 🎯 Strategic Decisions

### Why Java First? (v0.7.0)

1. **Enterprise Adoption**: Java dominates enterprise software
2. **User Demand**: Feedback from large Java projects (zcyl-backend)
3. **Market Gap**: Few tools handle Java + Spring well

### Why Framework Routes? (v0.5.0-v0.8.0)

1. **Business Context**: Routes = API surface = business logic
2. **High Value**: Developers need API overview most
3. **Differentiator**: Most indexers don't extract routes

### Why CLI UX First? (v0.16.0)

1. **New User Blocking**: Current defaults require AI config, blocking 80%+ of use cases
2. **Real Project Feedback**: Java testing (zcyl-backend) revealed 31% redundant READMEs
3. **Foundation**: Better UX benefits all future language additions

### Why TypeScript Next? (v0.19.0)

1. **Web Development**: TypeScript is #4 most popular language
2. **React Ecosystem**: Component detection adds unique value
3. **LoomGraph Synergy**: JS/TS projects benefit from knowledge graph

---

## 🔗 Related Documents

- **Epic Plans**: `docs/planning/completed/epicN-*/`
- **CHANGELOG**: `CHANGELOG.md`
- **GitHub Issues**: https://github.com/dreamlx/codeindex/issues

---

**Roadmap Status**: 🎯 Active
**Next Review**: 2026-03-31
**Maintained By**: @dreamlx
**Last Updated**: 2026-03-06
**Current Version**: v0.23.0
