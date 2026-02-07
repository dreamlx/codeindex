# Release Notes v0.8.0

**Release Date**: 2026-02-06
**Version**: v0.8.0
**Codename**: Epic 7 - Java Language Support Complete

---

## 🎯 Overview

codeindex v0.8.0 delivers **complete Java language support**, enabling comprehensive parsing and documentation generation for Java projects. This release completes all 11 Stories from Epic 7, adding 184 new tests and bringing total test coverage to 662 passing tests.

---

## ✨ Major Features

### 1. Java Language Parser (Stories 7.1.2.1-7.1.2.5)

Full Java language support with tree-sitter:

**Core Structures**:
- Classes, interfaces, enums, records (Java 14+)
- Sealed classes (Java 17+)
- Nested and inner classes
- Anonymous classes

**Advanced Features**:
- **Annotations** (Story 7.1.2.1): Full extraction including Spring, JPA, Lombok
  - Marker annotations: `@Entity`
  - With arguments: `@GetMapping("/users")`
  - Array arguments: `@RequestMapping({"/api", "/v1"})`
  - Named parameters: `@Column(name = "user_id")`

- **Generic Bounds** (Story 7.1.2.2): Type parameter constraints
  - Single bound: `<T extends Comparable<T>>`
  - Multiple bounds: `<T extends A & B & C>`
  - Wildcard bounds: `<? extends Number>`, `<? super Integer>`

- **Throws Declarations** (Story 7.1.2.3): Exception handling
  - Single: `throws IOException`
  - Multiple: `throws IOException, SQLException`
  - Generic: `throws T extends Exception`

- **Lambda Expressions** (Story 7.1.2.4): Java 8+ functional programming
  - Simple lambdas: `x -> x * 2`
  - Block lambdas: `x -> { return x * 2; }`
  - Method references: `String::length`, `ArrayList::new`

- **Module System** (Story 7.1.2.5): Java 9+ JPMS
  - Module declarations
  - requires, exports, opens directives
  - Service loading (provides/uses)

**Test Coverage**: 73 tests across 5 stories

### 2. Spring Framework Integration (Stories 7.1.3.1, 7.2)

Complete Spring ecosystem support:

**Story 7.1.3.1: Spring Framework Tests**
- REST Controllers: `@RestController`, `@Controller`
- Request mappings: `@GetMapping`, `@PostMapping`, etc.
- Service layer: `@Service`, `@Transactional`
- Data layer: `@Repository`, JPA entities
- Configuration: `@Configuration`, `@Bean`
- Validation: `@NotBlank`, `@Email`, `@Size`

**Story 7.2: Spring Route Extraction Plugin**
- Automatic route extraction from controllers
- Supports all HTTP method annotations
- Path composition (class + method level)
- Path variables: `{id}`, `{userId}`
- Line number tracking for easy navigation

**Example**:
```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
```
**Extracted Route**: `GET /api/users/{id} -> UserController.getUser` (line 8)

**Test Coverage**: 30 tests (19 Spring tests + 11 route extraction)

### 3. Lombok Support (Story 7.1.3.4)

Full support for Lombok annotations:

- **Code generation**: `@Data`, `@Getter`, `@Setter`, `@Builder`
- **Constructors**: `@AllArgsConstructor`, `@NoArgsConstructor`, `@RequiredArgsConstructor`
- **Utilities**: `@ToString`, `@EqualsAndHashCode`
- **Logging**: `@Slf4j`, `@Log`
- **Integration**: Works seamlessly with JPA + Spring

**Test Coverage**: 21 tests

### 4. Robustness & Edge Cases (Stories 7.1.3.2, 7.1.3.3)

**Edge Case Tests** (27 tests):
- Nested classes (static, inner, anonymous, multi-level)
- Complex generics (nested, wildcards, multiple bounds)
- Very long signatures (many parameters)
- Unicode identifiers (Chinese class names)
- Special characters ($ in names)
- Empty declarations, array types, varargs
- Multiple interface inheritance

**Error Recovery** (24 tests):
- Syntax errors (missing semicolons, brackets)
- Incomplete declarations
- Malformed generics
- Truncated files
- Mixed valid/invalid code
- **Strategy**: Report errors rather than extracting incorrect symbols

### 5. Performance Optimization (Story 7.1.4.2)

**Parallel Directory Scanning**:
- ThreadPoolExecutor for concurrent processing
- Configurable: `parallel_workers: 8` in config
- CLI override: `codeindex scan-all --parallel 16`
- **Performance**: 3-4x speedup for scan-all operations
- Example: 50 directories: 500s → 125s

**Test Coverage**: 9 tests

---

## 📊 Statistics

### Test Coverage

```
Total Tests: 662 passing, 3 skipped
Epic 7 New Tests: +184
  - 11 annotation tests
  - 13 generic bounds tests
  - 13 throws declarations tests
  - 15 lambda expression tests
  - 21 module system tests
  - 19 Spring Framework tests
  - 27 edge case tests
  - 24 error recovery tests
  - 21 Lombok support tests
  - 9 parallel scanning tests
  - 11 Spring route extraction tests
```

### Code Changes

```
Files Changed: 15 files
Additions: +3,776 lines
Deletions: -41 lines

New Files:
  - src/codeindex/extractors/spring.py (218 lines)
  - tests/test_java_generic_bounds.py (257 lines)
  - tests/test_java_throws.py (270 lines)
  - tests/test_java_lambda.py (311 lines)
  - tests/test_java_module.py (372 lines)
  - tests/test_java_edge_cases.py (550 lines)
  - tests/test_java_error_recovery.py (453 lines)
  - tests/test_java_lombok.py (534 lines)
  - tests/extractors/test_spring.py (346 lines)

Modified Files:
  - src/codeindex/parser.py (+19 lines for generics & throws)
  - src/codeindex/extractors/__init__.py (Spring export)
  - CHANGELOG.md
  - README_AI.md files
```

### Implementation Efficiency

```
Stories Completed: 11/11 (100%)
Test-to-Code Ratio: High (comprehensive coverage)
TDD Adherence: 100% (RED-GREEN-REFACTOR for all stories)
Breaking Changes: 0
Backward Compatibility: 100%
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

### No New Config Required

All Java features work out-of-the-box with existing configurations.

### Optional: Parallel Workers (from v0.7.0)

```yaml
# .codeindex.yaml (optional)
parallel_workers: 8  # Concurrent directory scanning
```

```bash
# CLI override
codeindex scan-all --parallel 16
```

---

## 🐛 Bug Fixes

No bugs fixed (Epic 7 was greenfield development).

---

## 📚 Documentation

### Updated Documents

- `CHANGELOG.md` - v0.8.0 release notes
- `README.md` - Java language support
- `src/codeindex/README_AI.md` - Parser architecture
- `tests/README_AI.md` - Test structure

### Reference Documents (in repo)

Epic 7 design and decisions:
- `RELEASE_NOTES_v0.7.0.md` - v0.7.0 details (parallel scanning)
- Git commit history for detailed story implementation

---

## 🎓 Migration Guide

### No Migration Required

Java support is automatically enabled for `.java` files.

### Using Java Support

```bash
# Scan Java project
codeindex scan ./src

# Scan Spring Boot project
codeindex scan-all --fallback

# JSON output (for tool integration)
codeindex scan ./src --output json

# Parallel scanning for large projects
codeindex scan-all --parallel 16
```

### Spring Route Extraction

```python
from codeindex.parser import parse_file
from codeindex.extractors.spring import SpringRouteExtractor

# Parse Java controller
result = parse_file("UserController.java")

# Extract routes
extractor = SpringRouteExtractor()
routes = extractor.extract_routes(result)

for route in routes:
    print(f"{route.url} -> {route.controller}.{route.action}:{route.line_number}")
    # GET /api/users/{id} -> UserController.getUser:15
```

### Configuration Example

```yaml
# .codeindex.yaml
version: 1
languages:
  - python
  - php
  - java  # Now fully supported!

include:
  - "src/**/*.java"
  - "src/**/*.py"
  - "src/**/*.php"

parallel_workers: 8  # Optional: speed up large projects
```

---

## 🚀 What's Included

### ✅ All Epic 7 Stories Complete

| Story | Feature | Tests |
|-------|---------|-------|
| 7.1.2.1 | Annotations | 11 |
| 7.1.2.2 | Generic Bounds | 13 |
| 7.1.2.3 | Throws Declarations | 13 |
| 7.1.2.4 | Lambda Expressions | 15 |
| 7.1.2.5 | Module System | 21 |
| 7.1.3.1 | Spring Framework | 19 |
| 7.1.3.2 | Edge Case Tests | 27 |
| 7.1.3.3 | Error Recovery | 24 |
| 7.1.3.4 | Lombok Support | 21 |
| 7.1.4.2 | Parallel Scanning | 9 |
| 7.2 | Spring Route Extraction | 11 |
| **Total** | **11 Stories** | **184** |

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
pip install codeindex==0.8.0
```

### From Source

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
git checkout v0.8.0
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

### v0.8.1 (Planned - Bug fixes if needed)

### v0.9.0 (Future - Epic 8)

Potential features:
- TypeScript/JavaScript support
- Go language support
- Enhanced framework plugins (Laravel, Django, FastAPI)

---

## 🎉 Thank You

Special thanks to:
- All contributors and testers
- The tree-sitter community
- Java and Spring Framework communities
- Open source maintainers

**Enjoy codeindex v0.8.0!** 🚀

---

*Released with ❤️ by the codeindex team*
