# Epic 7: Java Language Support

**Epic ID**: Epic 7
**Version**: v0.6.0
**Priority**: 🔥 P0 (Critical)
**Status**: 🔄 Active (2026-02-03)
**Owner**: @dreamlx

---

## 📋 Epic Overview

### Vision

Enable codeindex to index and document Java projects with the same quality as Python projects, focusing on enterprise Java ecosystems (Spring Boot, Maven, Gradle).

### Business Value

**Why Java?**
1. **Enterprise Adoption**: Java dominates enterprise software development
2. **Market Gap**: Few tools provide AI-friendly Java code indexing
3. **User Demand**: Feedback from users with large Java codebases
4. **Revenue Potential**: Enterprise users willing to pay for quality tools

**Expected Impact**:
- Unlock enterprise market segment
- 10x increase in potential user base
- Foundation for multi-language support (v0.7.0+)

### Success Criteria

- [ ] Parse 95%+ valid Java code (Java 8-21)
- [ ] Extract Spring @RestController/@RequestMapping routes with 100% accuracy
- [ ] Generate useful README_AI.md for Java modules
- [ ] Handle large Java projects (>100k LOC) in <5 minutes
- [ ] Support Maven and Gradle project structures
- [ ] Comprehensive documentation and examples

---

## 🎯 User Stories

### Core Stories

**Story 7.1: Java Parser Integration** (P0)
> As a developer with a Java project, I want codeindex to parse my Java files and extract classes, methods, and interfaces, so that I can generate AI-friendly documentation.

**Acceptance Criteria**:
- [ ] tree-sitter-java parser integrated
- [ ] Extract classes, interfaces, enums, annotations
- [ ] Extract methods with signatures and JavaDoc
- [ ] Extract fields and constants
- [ ] Extract import statements
- [ ] Handle Java 8-21 syntax (lambdas, records, sealed classes)

**Story 7.2: Spring Framework Route Extraction** (P0)
> As a Spring Boot developer, I want codeindex to extract my REST API routes with their HTTP methods, paths, and descriptions, so that I can understand my API surface at a glance.

**Acceptance Criteria**:
- [ ] Extract @RestController classes
- [ ] Parse @RequestMapping, @GetMapping, @PostMapping, etc.
- [ ] Extract path variables and request parameters
- [ ] Extract method descriptions from JavaDoc
- [ ] Generate route table in README_AI.md

**Story 7.3: Maven/Gradle Project Detection** (P1)
> As a Java developer using Maven or Gradle, I want codeindex to automatically detect my project structure and scan the right directories, so that I don't have to manually configure paths.

**Acceptance Criteria**:
- [ ] Detect pom.xml (Maven) and build.gradle (Gradle)
- [ ] Auto-configure include paths (src/main/java, src/test/java)
- [ ] Respect multi-module projects
- [ ] Exclude generated code (target/, build/)

**Story 7.4: Java Symbol Importance Scoring** (P1)
> As a Java developer, I want codeindex to prioritize important symbols (public APIs, interfaces, main classes) over implementation details, so that README_AI.md focuses on what matters.

**Acceptance Criteria**:
- [ ] Higher scores for public classes/methods
- [ ] Higher scores for interfaces and abstract classes
- [ ] Higher scores for @Component, @Service, @Controller annotations
- [ ] Lower scores for private methods and inner classes
- [ ] Lower scores for getters/setters (unless annotated)

**Story 7.5: JavaDoc Extraction and Parsing** (P2)
> As a Java developer who writes JavaDoc, I want codeindex to extract and display my documentation comments, so that the generated README includes my existing documentation.

**Acceptance Criteria**:
- [ ] Extract class-level JavaDoc
- [ ] Extract method-level JavaDoc
- [ ] Parse @param, @return, @throws tags
- [ ] Include JavaDoc in symbol descriptions
- [ ] Handle multi-line JavaDoc correctly

### Extended Stories (P2-P3)

**Story 7.6: Java-specific File Categorization** (P2)
- Detect test files (Test suffix, @Test annotation)
- Detect configuration classes (@Configuration, @SpringBootApplication)
- Detect entities (@Entity, @Table)
- Categorize in README_AI.md

**Story 7.7: Java Package Structure Analysis** (P3)
- Analyze package hierarchies
- Detect common patterns (com.example.domain, com.example.service)
- Generate package-level summaries

**Story 7.8: Lombok Support** (P3)
- Recognize Lombok annotations (@Data, @Builder)
- Document generated methods in README_AI.md
- Handle @SneakyThrows, @Cleanup, etc.

---

## 🏗️ Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                 Java Support Architecture                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐      ┌────────────────────────┐  │
│  │  Language        │      │  Framework             │  │
│  │  Detection       │─────▶│  Detection             │  │
│  │  (pom.xml/       │      │  (Spring annotations)  │  │
│  │   build.gradle)  │      └────────────────────────┘  │
│  └──────────────────┘                │                  │
│           │                           │                  │
│           ▼                           ▼                  │
│  ┌──────────────────┐      ┌────────────────────────┐  │
│  │  Java Parser     │      │  Spring Route          │  │
│  │  (tree-sitter)   │─────▶│  Extractor             │  │
│  │                  │      │  (plugin)              │  │
│  └──────────────────┘      └────────────────────────┘  │
│           │                           │                  │
│           ▼                           ▼                  │
│  ┌──────────────────┐      ┌────────────────────────┐  │
│  │  Symbol          │      │  Route Table           │  │
│  │  Extraction      │      │  Generation            │  │
│  └──────────────────┘      └────────────────────────┘  │
│           │                           │                  │
│           └───────────┬───────────────┘                  │
│                       ▼                                  │
│            ┌────────────────────┐                        │
│            │  README_AI.md      │                        │
│            │  Generation        │                        │
│            └────────────────────┘                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Component Design

#### 1. Java Parser (`parsers/java_parser.py`)

**Responsibilities**:
- Use tree-sitter-java to parse Java source files
- Extract symbols (classes, methods, fields, imports)
- Extract JavaDoc comments
- Handle Java-specific syntax (generics, annotations, lambdas)

**Key Methods**:
```python
class JavaParser:
    def parse_file(self, file_path: Path) -> ParseResult:
        """Parse a Java file and return symbols."""

    def extract_class(self, node) -> Symbol:
        """Extract class/interface/enum definition."""

    def extract_method(self, node) -> Symbol:
        """Extract method with signature and JavaDoc."""

    def extract_javadoc(self, node) -> str:
        """Extract and clean JavaDoc comment."""

    def parse_annotations(self, node) -> list[str]:
        """Extract annotation names."""
```

**Dependencies**:
- tree-sitter-java (install via pip)
- Base Parser abstraction (refactor from parser.py)

#### 2. Spring Route Extractor (`extractors/spring.py`)

**Responsibilities**:
- Detect Spring @RestController classes
- Extract @RequestMapping and shorthand mappings
- Build route URLs from class + method mappings
- Extract request/response information

**Key Methods**:
```python
class SpringRouteExtractor(RouteExtractor):
    @property
    def framework_name(self) -> str:
        return "spring"

    def can_extract(self, context: ExtractionContext) -> bool:
        """Detect Spring controllers."""

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """Extract REST API routes."""

    def parse_mapping_annotation(self, symbol) -> RouteInfo:
        """Parse @GetMapping, @PostMapping, etc."""
```

**Annotation Handling**:
- `@RestController` + `@RequestMapping("/api")`
- `@GetMapping("/users")` → GET /api/users
- `@PostMapping("/users")` → POST /api/users
- `@PathVariable`, `@RequestParam` extraction

#### 3. Project Detection (`project_detectors/java_detector.py`)

**Responsibilities**:
- Detect Maven projects (pom.xml)
- Detect Gradle projects (build.gradle, build.gradle.kts)
- Auto-configure include/exclude paths
- Detect multi-module projects

**Key Methods**:
```python
class JavaProjectDetector:
    def detect(self, root_path: Path) -> ProjectInfo:
        """Detect Java project type and structure."""

    def find_source_directories(self, root_path: Path) -> list[Path]:
        """Find src/main/java, src/test/java."""

    def detect_dependencies(self, root_path: Path) -> list[str]:
        """Extract dependencies from pom.xml/build.gradle."""
```

**Auto-configuration**:
```yaml
# Auto-generated for Maven project
include:
  - src/main/java
  - src/test/java
exclude:
  - "**/target/**"
  - "**/*.class"
languages:
  - java
```

#### 4. Java Symbol Scorer (`scorers/java_scorer.py`)

**Responsibilities**:
- Score Java symbols based on visibility, annotations, patterns
- Prioritize public APIs and framework components
- Demote boilerplate code (getters/setters)

**Scoring Rules**:
```python
# Visibility
public class/method:     +10
protected:               +5
package-private:         +2
private:                 +0

# Annotations (Spring)
@RestController:         +20
@Service:                +15
@Component:              +15
@Entity:                 +10
@Configuration:          +10

# Type
interface:               +10
abstract class:          +8
enum:                    +5
class:                   +3

# Patterns
main() method:           +20
Getters/setters:         -5 (unless @JsonProperty)
toString/equals/hashCode: -3
```

---

## 📝 Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goal**: Basic Java parsing working

**Tasks**:
1. **Refactor Parser Abstraction** (Story Setup)
   - Extract language-agnostic base class from parser.py
   - Create LanguageParser protocol
   - Update Config to support multiple languages

2. **Implement Java Parser** (Story 7.1)
   - Install tree-sitter-java
   - Implement JavaParser class
   - Extract basic symbols (classes, methods, fields)
   - Write comprehensive tests (TDD)

3. **JavaDoc Extraction** (Story 7.5 - partial)
   - Parse JavaDoc comments
   - Extract @param, @return, @throws
   - Clean and format JavaDoc text

**Deliverable**: `codeindex scan src/ --language java` works

### Phase 2: Spring Support (Week 3)

**Goal**: Spring route extraction working

**Tasks**:
4. **Spring Route Extractor** (Story 7.2)
   - Implement SpringRouteExtractor
   - Parse @RestController annotations
   - Parse @RequestMapping and variants
   - Extract HTTP methods and paths
   - Write tests with real Spring code

5. **Route Table Generation** (Story 7.2)
   - Format routes in README_AI.md
   - Include HTTP method, path, controller, method
   - Add JavaDoc descriptions

**Deliverable**: Spring Boot project route table generated

### Phase 3: Project Integration (Week 4)

**Goal**: Maven/Gradle auto-detection

**Tasks**:
6. **Java Project Detector** (Story 7.3)
   - Detect pom.xml and build.gradle
   - Auto-configure include/exclude
   - Handle multi-module projects

7. **Java Symbol Scorer** (Story 7.4)
   - Implement scoring rules
   - Test with real Java projects
   - Tune thresholds

8. **Integration Testing** (Story 7.1-7.5)
   - Test on real Spring Boot projects
   - Test on multi-module Maven projects
   - Performance testing (100k+ LOC)

**Deliverable**: Auto-detection works end-to-end

### Phase 4: Polish & Documentation (Week 5-6)

**Goal**: Production quality

**Tasks**:
9. **Edge Cases & Bug Fixes**
   - Handle Java 21 syntax (records, sealed classes)
   - Handle Lombok annotations
   - Fix parser edge cases

10. **Documentation** (Critical)
    - User guide: Java project setup
    - Developer guide: Adding languages
    - Example Spring Boot project
    - Migration guide from JavaDoc

11. **Performance Optimization**
    - Profile parser performance
    - Optimize tree-sitter queries
    - Parallel processing for large projects

**Deliverable**: v0.6.0 release candidate

---

## 🧪 Testing Strategy

### Test Pyramid

```
         ▲
        ╱ ╲
       ╱ E2E╲         5 tests  - Full Spring Boot projects
      ╱───────╲
     ╱Integration╲    20 tests - Parser + Extractor integration
    ╱─────────────╲
   ╱  Unit Tests   ╲  100 tests - Java parser, Spring extractor
  ╱─────────────────╲
```

### Unit Tests (100+ tests)

**JavaParser** (50 tests):
- Parse classes (simple, nested, generic)
- Parse interfaces and enums
- Parse methods (static, default, overloaded)
- Parse annotations (@Override, @Deprecated, custom)
- Parse JavaDoc (class, method, field)
- Handle syntax errors gracefully
- Java 8-21 features (lambdas, records, sealed)

**SpringRouteExtractor** (30 tests):
- Extract @RestController routes
- Parse @RequestMapping variants
- Handle path variables and request params
- Combine class + method mappings
- Extract descriptions from JavaDoc
- Handle inheritance (@RequestMapping on interface)

**JavaProjectDetector** (10 tests):
- Detect Maven single-module
- Detect Maven multi-module
- Detect Gradle single/multi-module
- Auto-configure include paths
- Handle missing pom.xml/build.gradle

**JavaSymbolScorer** (10 tests):
- Score by visibility
- Score by annotation
- Score by type (interface, abstract, class)
- Demote boilerplate (getters/setters)

### Integration Tests (20 tests)

**Parser + Extractor**:
- Parse Spring Boot controller → Extract routes
- Parse Maven project → Detect structure
- Score Java symbols → Verify top symbols
- Generate README_AI.md → Verify format

### End-to-End Tests (5 tests)

**Real Projects**:
- Test on Spring Boot sample project (spring-petclinic)
- Test on multi-module Maven project
- Test on Gradle project
- Performance test (100k+ LOC project)
- Regression test (existing Python projects still work)

---

## 📊 Success Metrics

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Parser Accuracy** | 95%+ | Parse 95%+ valid Java files without errors |
| **Route Extraction Accuracy** | 100% | Extract 100% of Spring routes correctly |
| **Test Coverage** | 90%+ | Line coverage for Java-related code |
| **Performance** | <5min | Index 100k LOC Java project in <5min |

### User Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **User Satisfaction** | 4/5+ | Feedback from beta testers |
| **Documentation Quality** | Complete | All user stories have guides |
| **Bug Reports** | <10 | Bugs reported in first 2 weeks |

---

## 🚧 Risks & Mitigations

### Risk 1: tree-sitter-java Limitations

**Risk**: tree-sitter-java may not support latest Java syntax

**Probability**: Medium
**Impact**: High

**Mitigation**:
- Test with Java 8, 11, 17, 21 codebases
- Contribute fixes upstream if needed
- Graceful fallback for unsupported syntax

### Risk 2: Spring Annotation Complexity

**Risk**: Spring has many annotation variants and inheritance patterns

**Probability**: High
**Impact**: Medium

**Mitigation**:
- Start with common patterns (@RestController, @GetMapping)
- Iterative approach: v0.6.0 covers 80%, v0.7.0 covers 95%
- Document unsupported patterns

### Risk 3: Performance on Large Projects

**Risk**: Java projects can be massive (1M+ LOC)

**Probability**: High
**Impact**: High

**Mitigation**:
- Parallel processing (multiple files)
- Incremental indexing (v0.7.0)
- Performance profiling and optimization
- Set expectations (v0.6.0 target: 100k LOC)

### Risk 4: Multi-language Parser Abstraction

**Risk**: Refactoring parser.py may break existing Python support

**Probability**: Low
**Impact**: Critical

**Mitigation**:
- Comprehensive regression tests for Python
- Gradual refactoring with feature flags
- Maintain backward compatibility
- **Gate**: All Python tests must pass before Java release

---

## 📅 Timeline

### v0.6.0-alpha (Week 3)
- Basic Java parsing working
- Internal testing

### v0.6.0-beta (Week 5)
- Spring route extraction working
- Beta testers invited
- Documentation draft

### v0.6.0-rc1 (Week 6)
- All features complete
- Bug fixes from beta
- Final documentation review

### v0.6.0 (Week 7)
- Production release
- Announcement
- User onboarding

**Target Release Date**: 2026-03-15

---

## 🎓 Learning Resources

### For Implementers

**tree-sitter**:
- [tree-sitter documentation](https://tree-sitter.github.io/tree-sitter/)
- [tree-sitter-java](https://github.com/tree-sitter/tree-sitter-java)
- Query syntax and AST exploration

**Spring Framework**:
- [Spring Web MVC annotations](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html)
- @RestController, @RequestMapping variants
- Path patterns and method mappings

**Java Language**:
- Java 8-21 syntax changes
- Annotations and reflection
- JavaDoc conventions

### Example Projects

**Test Data**:
- [Spring PetClinic](https://github.com/spring-projects/spring-petclinic) - Classic Spring Boot example
- [Spring Boot Samples](https://github.com/spring-projects/spring-boot/tree/main/spring-boot-samples) - Official samples
- Real-world multi-module Maven projects

---

## 📚 Documentation Deliverables

### User Documentation

1. **Quick Start: Java Projects**
   - `docs/guides/java-quickstart.md`
   - Installation, first scan, configuration

2. **Spring Boot Integration Guide**
   - `docs/guides/spring-boot-integration.md`
   - Route extraction, best practices

3. **Java Configuration Reference**
   - `docs/guides/java-configuration.md`
   - Maven/Gradle detection, custom paths

### Developer Documentation

4. **Adding Language Support**
   - `docs/development/adding-languages.md`
   - Parser abstraction, plugin architecture
   - Use Java as reference implementation

5. **Java Parser Deep Dive**
   - `docs/development/java-parser-architecture.md`
   - tree-sitter integration, symbol extraction
   - Performance considerations

---

## ✅ Definition of Done

**Epic 7 is complete when**:

- [ ] All user stories (7.1-7.5) implemented and tested
- [ ] All acceptance criteria met
- [ ] 90%+ test coverage for Java code
- [ ] Documentation complete (user + developer)
- [ ] Performance targets met (<5min for 100k LOC)
- [ ] Beta testing complete, critical bugs fixed
- [ ] CHANGELOG.md updated
- [ ] v0.6.0 released to GitHub
- [ ] User onboarding materials ready

---

## 🔗 Related Documents

- **ROADMAP**: `docs/planning/ROADMAP.md`
- **Version Plan**: `docs/planning/v0.6.0-execution-plan.md` (TBD)
- **GitHub Epic**: Issue #TBD (to be created)
- **GitHub Milestone**: v0.6.0 - Java Support

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-03 | Epic created | @dreamlx |

---

**Epic Status**: 🔄 Active (Ready to start)
**Next Step**: Create GitHub Epic Issue + Milestone
**Owner**: @dreamlx
**Estimated Effort**: 6-7 weeks
**Target Release**: v0.6.0 (2026-03-15)
