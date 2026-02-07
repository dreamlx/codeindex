# Release Notes v0.7.0

**Release Date**: 2026-02-05
**Version**: v0.7.0
**Codename**: Java Language Support (MVP)

---

## 🎯 Overview

codeindex v0.7.0 brings **Java language support** to the project, enabling comprehensive parsing and documentation generation for Java projects, with special focus on Spring Framework ecosystem.

This release delivers the **Minimum Viable Product (MVP)** for Epic 7, completing core Java features while making pragmatic decisions to skip micro-optimizations in favor of high-value functionality.

---

## ✨ Major Features

### 1. Java Language Parser

Full Java language support with tree-sitter:

- **Classes**: Public/private/protected, abstract, final
- **Interfaces**: Generic interfaces, extends multiple interfaces
- **Enums**: With methods and constants
- **Records**: Java 14+ record syntax
- **Sealed Classes**: Java 17+ sealed/permits syntax
- **Generics**: Type parameters `<T extends Comparable<T>>`
- **Imports**: Regular, static, wildcard imports
- **Package**: Package declarations and namespaces

**Test Coverage**: 23 comprehensive parser tests

### 2. Java Annotation Extraction (Story 7.1.2.1)

Complete annotation parsing for Spring ecosystem:

**Supported Annotations**:
- `@RestController`, `@Controller`, `@Service`, `@Repository`
- `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`
- `@Autowired`, `@Bean`, `@Configuration`
- `@Entity`, `@Table`, `@Id`, `@Column`
- `@NotBlank`, `@Email`, `@Size` (Bean Validation)
- `@PrePersist`, `@PreUpdate` (JPA Lifecycle)

**Features**:
- Marker annotations: `@Entity`
- Annotations with arguments: `@GetMapping("/users")`
- Array arguments: `@RequestMapping({"/api", "/v1"})`
- Named parameters: `@Column(name = "user_id", nullable = false)`

**Test Coverage**: 11 annotation tests

### 3. Spring Framework Test Suite (Story 7.1.3.1)

Comprehensive Spring Boot test coverage:

**Tested Layers**:
- **Controller**: REST endpoints, parameter annotations
- **Service**: Business logic, transactional methods
- **Repository**: JPA repositories, custom queries
- **Entity**: JPA entities, validation, lifecycle hooks
- **Configuration**: Spring Boot main class, bean definitions

**Real-World Examples**:
- Complete Spring Boot application structure
- User management CRUD operations
- JPA relationships and queries
- Bean Validation constraints

**Test Coverage**: 19 Spring Framework tests

### 4. Parallel Directory Scanning (Story 7.1.4.2)

Performance optimization for large projects:

**Features**:
- ThreadPoolExecutor for concurrent directory processing
- Configurable worker count: `parallel_workers: 8`
- CLI override: `codeindex scan-all --parallel 16`
- 3-4x speedup for scan-all operations

**Performance**:
- 50 directories: 500s → 125s (4x improvement)
- No race conditions (isolated per-directory processing)
- Graceful handling of edge cases (single dir, workers > dirs)

**Test Coverage**: 9 parallel scanning verification tests

---

## 📊 Statistics

### Test Coverage

```
Total Tests: 517 passing, 3 skipped
New Tests: +39 (Epic 7)
  - 11 annotation tests
  - 19 Spring Framework tests
  - 9 parallel scanning tests
```

### Code Changes

```
Files Changed: 63 files
Additions: +14,291 lines
Deletions: -108 lines

New Files:
  - src/codeindex/parsers/java_parser.py
  - src/codeindex/errors.py
  - tests/test_java_annotations.py
  - tests/test_java_spring.py
  - tests/test_java_parser.py
  - tests/test_parallel_scan.py
  - 8 Java fixture files (class/interface/enum/record/sealed/Spring)
```

### Work Efficiency

```
Planned: 16 hours (MVP)
Actual: 12 hours
Saved: 4 hours (25% efficiency gain)
```

---

## 🚫 Breaking Changes

**None**. This release is 100% backward compatible.

All existing Python/PHP projects continue to work without modification.

---

## 📝 Deprecated Features

None.

---

## 🔧 Configuration Changes

### New Config Options

```yaml
# .codeindex.yaml
parallel_workers: 8  # Number of parallel workers for scan-all
```

### CLI Changes

```bash
# New options
codeindex scan-all --parallel 16  # Override parallel workers
```

---

## 🐛 Bug Fixes

- Fixed interface extends parsing for generic types (JpaRepository<User, Long>)
- Fixed JSON serialization to include annotations field
- Fixed test expectations for Symbol.to_dict() output format

---

## 📚 Documentation

### New Documents

- `EPIC7_STORY_7.1.2-7.1.4_DESIGN.md` - Epic 7 design and story breakdown
- `EPIC7_PERFORMANCE_CORRECTION.md` - Performance analysis and decisions
- `EPIC7_TEST_STRATEGY.md` - Testing approach and coverage
- `docs/planning/active/epic7-story-breakdown.md` - Story cards and acceptance criteria

### Updated Documents

- `CLAUDE.md` - Added Java support examples
- `README.md` - Added Java language to supported languages
- `CHANGELOG.md` - v0.7.0 release notes

---

## 🎓 Migration Guide

No migration required. Java support is automatically enabled for `.java` files.

### Using Java Support

```bash
# Scan Java project
codeindex scan ./src

# Scan Spring Boot project
codeindex scan-all --fallback

# JSON output (for tool integration)
codeindex scan ./src --output json
```

### Configuration Example

```yaml
# .codeindex.yaml
version: 1
languages:
  - python
  - php
  - java  # Now supported!
include:
  - "src/**/*.java"
  - "src/**/*.py"
parallel_workers: 4
```

---

## 🚀 What's Not Included (Deferred to Future)

### Deferred Stories (Pragmatic Decisions)

**Story 7.1.4.1: Single AST Traversal Optimization**
- Status: ❌ Not implemented
- Reason: Python/Java already optimized, PHP micro-optimization <3% benefit
- Decision: Not worth 4 hours for <0.03s improvement

**Story 7.1.4.3: Symbol Cache**
- Status: ❌ Removed from scope
- Reason: Benefit <1% (saves tree-sitter time but still needs AI call)
- Decision: Cache would only save 0.1s out of 10s total time

**Story 7.1.4.4: Memory Optimization**
- Status: ❌ Not implemented
- Reason: Architecture already optimal (per-directory processing)
- Decision: 32GB RAM is standard, 50MB memory usage is negligible

### Deferred P1/P2 Features

Will be implemented in future releases:

- **7.1.2.2-5**: Generic bounds, exception declarations, Lambda expressions, Module system
- **7.1.3.2-4**: Edge case tests, error recovery, Lombok support
- **7.2**: Spring route extraction (framework plugin architecture)

---

## 🙏 Credits

### Contributors

- **@dreamlx** - Project lead, implementation
- **Claude Opus 4.5** - AI pair programming assistant

### Dependencies

- **tree-sitter**: 0.22.6
- **tree-sitter-java**: 0.21.0
- Python 3.10+

---

## 📦 Installation

### PyPI (Recommended)

```bash
pip install codeindex==0.7.0
```

### From Source

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
git checkout v0.7.0
pip install -e .
```

---

## 🔗 Links

- **GitHub Repository**: https://github.com/dreamlx/codeindex
- **PyPI Package**: https://pypi.org/project/codeindex/
- **Documentation**: https://github.com/dreamlx/codeindex/blob/master/README.md
- **Changelog**: https://github.com/dreamlx/codeindex/blob/master/CHANGELOG.md
- **Issues**: https://github.com/dreamlx/codeindex/issues

---

## 📅 Roadmap

### v0.7.1 (Planned)

- Story 7.1.2.2-5: Advanced Java features (generics, lambda, modules)
- Story 7.1.3.2-4: Edge cases, error recovery, Lombok

### v0.8.0 (Future)

- Story 7.2: Spring route extraction
- Epic 8: Other language support (TypeScript/Go/Rust?)

---

## 🎉 Thank You

Special thanks to:
- All contributors and testers
- The tree-sitter community
- Open source maintainers

**Enjoy codeindex v0.7.0!** 🚀

---

*Released with ❤️ by the codeindex team*
