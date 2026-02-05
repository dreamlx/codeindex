# Epic 7: Java Language Support - Story Breakdown

**Epic**: Epic 7 - Java Language Support
**Version Target**: v0.8.0
**Sprint Duration**: 5 weeks
**Status**: 🟢 Ready to Start

---

## 🎯 Epic Goal

Enable codeindex to scan, parse, and document Java projects with the same quality as Python/PHP support.

**Success Criteria**:
- ✅ Parse Java 8-21 syntax (classes, interfaces, enums, records, sealed classes)
- ✅ Extract Spring Framework routes (@RestController, @GetMapping, etc.)
- ✅ Extract JavaDoc comments (reuse Epic 9 AI processor)
- ✅ 90%+ test coverage
- ✅ Support real-world Spring Boot projects

---

## 📦 Feature Breakdown

### Feature 1: Java Parser Foundation (Week 1)
**Goal**: Basic Java code parsing capability

**Stories**:
- Story 7.1.1: tree-sitter-java Integration
- Story 7.1.2: Symbol Extraction (classes, methods, interfaces)
- Story 7.1.3: Import Statement Extraction
- Story 7.1.4: Java 8-21 Syntax Support

### Feature 2: Spring Framework Integration (Week 2)
**Goal**: Extract Spring Boot API routes

**Stories**:
- Story 7.2.1: Spring Route Extractor Plugin
- Story 7.2.2: @RestController and @RequestMapping
- Story 7.2.3: HTTP Method Annotations (@GetMapping, @PostMapping, etc.)
- Story 7.2.4: Route Table Generation

### Feature 3: Project Detection & Configuration (Week 3)
**Goal**: Auto-detect Java project structure

**Stories**:
- Story 7.3.1: Maven Project Detection (pom.xml)
- Story 7.3.2: Gradle Project Detection (build.gradle)
- Story 7.3.3: Auto-configure Include/Exclude Paths
- Story 7.5.1: JavaDoc Extraction (AI Integration)

### Feature 4: Intelligence & Documentation (Week 4)
**Goal**: Improve output quality

**Stories**:
- Story 7.4.1: Java Symbol Scoring Algorithm
- Story 7.4.2: Priority-based Symbol Selection
- Story 7.6.1: Java File Classification (optional)

### Feature 5: Polish & Release (Week 5)
**Goal**: Production readiness

**Stories**:
- Story 7.7.1: Documentation & Examples
- Story 7.7.2: Performance Optimization
- Story 7.7.3: E2E Testing with Real Projects

---

## 🎫 Story 7.1.1: tree-sitter-java Integration (Day 1-2)

### Story Details
**As a** developer
**I want** codeindex to parse Java source files
**So that** I can generate README_AI.md for Java projects

**Priority**: P0 (Blocker)
**Estimate**: 2 days
**Dependencies**: None

### Acceptance Criteria
1. ✅ `tree-sitter-java` dependency installed
2. ✅ Basic Java parser initialized
3. ✅ Parse simple Java class (fields + methods)
4. ✅ Parse Java interface
5. ✅ Parse Java enum
6. ✅ Handle syntax errors gracefully
7. ✅ 20+ unit tests passing

### Tasks

#### Task 7.1.1.1: Setup Dependencies (30 min)
**Type**: Configuration
**Owner**: AI

**Steps**:
1. Add `tree-sitter-java>=0.23.0` to `pyproject.toml`
2. Install dependency: `pip install tree-sitter-java`
3. Verify installation

**Acceptance**:
```python
import tree_sitter_java
print(tree_sitter_java.language())  # Should work
```

#### Task 7.1.1.2: Create Test Fixtures (1 hour)
**Type**: Test Data
**Owner**: AI

**Steps**:
1. Create `tests/fixtures/java/` directory
2. Write synthetic Java files:
   - `simple_class.java` - Basic class with fields/methods
   - `interface.java` - Interface definition
   - `enum.java` - Enum with values
   - `generic_class.java` - Generic class
   - `imports.java` - Complex import statements

**Files to Create**:
```
tests/fixtures/java/
├── simple_class.java       # public class User { fields + methods }
├── interface.java          # public interface UserService { methods }
├── enum.java              # public enum Status { ACTIVE, INACTIVE }
├── generic_class.java     # class Box<T> { T value; }
└── imports.java           # import statements test
```

#### Task 7.1.1.3: Write TDD Tests (RED phase) (2 hours)
**Type**: Testing
**Owner**: AI

**Test File**: `tests/test_java_parser.py`

**Tests to Write**:
```python
# RED phase - these tests will FAIL initially

def test_parse_java_simple_class():
    """Test parsing basic Java class"""
    code = Path("tests/fixtures/java/simple_class.java").read_text()
    result = parse_java_file("test.java", code)

    assert result.success
    assert len(result.symbols) > 0
    assert result.symbols[0].name == "User"
    assert result.symbols[0].kind == "class"

def test_parse_java_interface():
    """Test parsing Java interface"""
    code = Path("tests/fixtures/java/interface.java").read_text()
    result = parse_java_file("test.java", code)

    assert result.symbols[0].kind == "interface"

def test_parse_java_enum():
    """Test parsing Java enum"""
    code = Path("tests/fixtures/java/enum.java").read_text()
    result = parse_java_file("test.java", code)

    assert result.symbols[0].kind == "enum"

def test_extract_java_imports():
    """Test extracting import statements"""
    code = Path("tests/fixtures/java/imports.java").read_text()
    result = parse_java_file("test.java", code)

    assert len(result.imports) > 0
    assert any(imp.module == "java.util.List" for imp in result.imports)

def test_parse_java_methods():
    """Test extracting method signatures"""
    code = Path("tests/fixtures/java/simple_class.java").read_text()
    result = parse_java_file("test.java", code)

    class_symbol = result.symbols[0]
    methods = [s for s in result.symbols if s.kind == "method"]
    assert len(methods) > 0

def test_parse_java_syntax_error():
    """Test handling Java syntax errors"""
    code = "public class Invalid { // missing closing brace"
    result = parse_java_file("test.java", code)

    assert result.error is not None
    assert "syntax" in result.error.lower() or result.has_error

def test_java_file_extension_detection():
    """Test Java file is recognized"""
    assert is_java_file("Test.java")
    assert not is_java_file("test.py")
```

**Expected Result**: All tests FAIL ❌ (RED phase)

#### Task 7.1.1.4: Implement Java Parser (GREEN phase) (4 hours)
**Type**: Implementation
**Owner**: AI

**Files to Create/Modify**:

**1. `src/codeindex/parsers/java_parser.py`** (NEW)
```python
"""Java language parser using tree-sitter."""

from tree_sitter import Language, Parser
import tree_sitter_java
from pathlib import Path
from typing import List

from codeindex.models import ParseResult, Symbol, Import


def get_java_parser() -> Parser:
    """Initialize Java parser."""
    parser = Parser()
    parser.set_language(tree_sitter_java.language())
    return parser


def parse_java_file(path: str, content: str) -> ParseResult:
    """
    Parse Java source file.

    Args:
        path: File path (for error reporting)
        content: Java source code

    Returns:
        ParseResult with symbols and imports
    """
    parser = get_java_parser()
    tree = parser.parse(bytes(content, "utf8"))

    # Check for syntax errors
    has_error = tree.root_node.has_error

    # Extract symbols
    symbols = _extract_symbols(tree.root_node, content)

    # Extract imports
    imports = _extract_imports(tree.root_node, content)

    # Extract module docstring (class-level JavaDoc)
    module_docstring = _extract_module_docstring(tree.root_node, content)

    return ParseResult(
        path=path,
        symbols=symbols,
        imports=imports,
        module_docstring=module_docstring,
        file_lines=len(content.splitlines()),
        error="Syntax error detected" if has_error else None
    )


def _extract_symbols(node, content: str) -> List[Symbol]:
    """Extract classes, interfaces, enums, methods from AST."""
    symbols = []

    # Traverse AST looking for:
    # - class_declaration
    # - interface_declaration
    # - enum_declaration
    # - method_declaration

    # TODO: Implement tree-sitter traversal

    return symbols


def _extract_imports(node, content: str) -> List[Import]:
    """Extract import statements."""
    imports = []

    # Look for import_declaration nodes

    # TODO: Implement import extraction

    return imports


def _extract_module_docstring(node, content: str) -> str:
    """Extract top-level JavaDoc comment."""
    # TODO: Extract first /** */ comment
    return ""


def is_java_file(path: str) -> bool:
    """Check if file is Java source."""
    return path.endswith('.java')
```

**2. Update `src/codeindex/parser.py`** (MODIFY)
```python
# Add Java support to main parser

from codeindex.parsers.java_parser import parse_java_file, is_java_file

def parse_file(path: str, content: str, language: str) -> ParseResult:
    """Parse file based on language."""
    if language == "python":
        return parse_python_file(path, content)
    elif language == "php":
        return parse_php_file(path, content)
    elif language == "java":  # ← NEW
        return parse_java_file(path, content)
    else:
        raise ValueError(f"Unsupported language: {language}")
```

**3. Update `src/codeindex/language_detector.py`** (MODIFY)
```python
# Add Java detection

def detect_language(path: str) -> str:
    """Detect language from file extension."""
    if path.endswith('.py'):
        return 'python'
    elif path.endswith('.php'):
        return 'php'
    elif path.endswith('.java'):  # ← NEW
        return 'java'
    else:
        return 'unknown'
```

**Expected Result**: Tests PASS ✅ (GREEN phase)

#### Task 7.1.1.5: Refactor & Optimize (1 hour)
**Type**: Refactoring
**Owner**: AI

**Steps**:
1. Extract common tree-sitter traversal logic
2. Add type hints
3. Add docstrings
4. Optimize performance
5. Run linter: `ruff check src/`

**Expected Result**: All tests still PASS ✅, code is clean

---

## 🎫 Story 7.1.2: Symbol Extraction - Classes & Methods (Day 3)

### Story Details
**As a** developer
**I want** to extract Java class and method definitions
**So that** README_AI.md includes all important symbols

**Priority**: P0
**Estimate**: 1 day
**Dependencies**: Story 7.1.1

### Acceptance Criteria
1. ✅ Extract class name, modifiers (public, abstract, final)
2. ✅ Extract method signatures (name, params, return type)
3. ✅ Extract field definitions
4. ✅ Handle nested classes
5. ✅ Handle generic types (e.g., `List<User>`)
6. ✅ 15+ unit tests passing

### Tasks

#### Task 7.1.2.1: Create Test Fixtures (30 min)
**Files**:
- `tests/fixtures/java/class_modifiers.java` - public/abstract/final classes
- `tests/fixtures/java/nested_class.java` - Nested and inner classes
- `tests/fixtures/java/generics.java` - Generic types

#### Task 7.1.2.2: Write TDD Tests (1 hour)
**Test File**: `tests/test_java_symbols.py`

```python
def test_extract_class_modifiers():
    """Test extracting public, abstract, final modifiers"""

def test_extract_method_signature():
    """Test method name, params, return type"""

def test_extract_generic_types():
    """Test List<User>, Map<K,V> parsing"""

def test_extract_nested_class():
    """Test inner class extraction"""
```

#### Task 7.1.2.3: Implement Symbol Extraction (3 hours)
**File**: `src/codeindex/parsers/java_parser.py`

Implement `_extract_symbols()` function using tree-sitter queries.

#### Task 7.1.2.4: Integration Test (30 min)
Test with a small real Java file (e.g., from Spring PetClinic).

---

## 🎫 Story 7.1.3: Import Statement Extraction (Day 3)

### Tasks (Similar structure)
- Task 7.1.3.1: Test fixtures
- Task 7.1.3.2: TDD tests
- Task 7.1.3.3: Implementation
- Task 7.1.3.4: Validation

---

## 🎫 Story 7.1.4: Java 8-21 Syntax Support (Day 4-5)

### New Features to Support
- **Java 8**: Lambda expressions, method references
- **Java 14**: Records (`record User(String name, int age)`)
- **Java 17**: Sealed classes (`sealed class Shape permits Circle, Square`)
- **Java 21**: Pattern matching, string templates

### Tasks
- Task 7.1.4.1: Record syntax test fixtures
- Task 7.1.4.2: Sealed class test fixtures
- Task 7.1.4.3: TDD tests for modern Java
- Task 7.1.4.4: Implementation
- Task 7.1.4.5: E2E test with Java 17+ project

---

## 📋 Week 1 Checklist

By end of Week 1, you should have:

**Code**:
- [ ] `src/codeindex/parsers/java_parser.py` - 200+ lines
- [ ] `tests/test_java_parser.py` - 20+ tests
- [ ] `tests/test_java_symbols.py` - 15+ tests
- [ ] `tests/fixtures/java/*.java` - 10+ files

**Tests**:
- [ ] 50+ unit tests passing
- [ ] 0 tests failing
- [ ] Test coverage > 90% for java_parser.py

**Dependencies**:
- [ ] `tree-sitter-java>=0.23.0` in pyproject.toml
- [ ] All dependencies installed

**Documentation**:
- [ ] Docstrings for all public functions
- [ ] README updated with Java support mention

**User Validation**:
- [ ] User runs codeindex on real Java project
- [ ] User provides feedback
- [ ] Issues documented for Week 2

---

## 🔄 Development Workflow (Per Story)

### Phase 1: Planning (15 min)
1. Read story acceptance criteria
2. Review task list
3. Understand dependencies

### Phase 2: RED (TDD - 1 hour)
1. Create test fixtures
2. Write failing tests
3. Run tests: `pytest tests/test_java_parser.py -v`
4. Verify all tests FAIL ❌

### Phase 3: GREEN (Implementation - 3 hours)
1. Implement minimum code to pass tests
2. Run tests: `pytest tests/test_java_parser.py -v`
3. Fix until all tests PASS ✅

### Phase 4: REFACTOR (Optimization - 30 min)
1. Improve code quality
2. Add type hints and docstrings
3. Run linter: `ruff check src/`
4. Run tests again (should still pass)

### Phase 5: Commit (10 min)
```bash
git add .
git commit -m "feat(parser): add Java class extraction (Story 7.1.2)

- Extract class declarations with modifiers
- Extract method signatures
- Support generic types
- 15 tests passing

Refs #<epic7-issue-number>"
```

### Phase 6: User Validation (30 min)
1. Push to feature branch
2. User pulls and tests with real Java project
3. User provides feedback
4. Fix issues (back to Phase 2 if needed)

---

## 🚀 Getting Started (Next Steps)

### Step 1: Commit Planning Docs
```bash
git add EPIC7_JAVA_ROADMAP.md EPIC7_TEST_STRATEGY.md docs/planning/active/epic7-story-breakdown.md
git commit -m "docs: add Epic 7 planning documents

- EPIC7_JAVA_ROADMAP.md: 5-week implementation plan
- EPIC7_TEST_STRATEGY.md: Test strategy and fixtures
- epic7-story-breakdown.md: Detailed story breakdown"
```

### Step 2: Create Feature Branch
```bash
git checkout -b feature/epic7-java-support
git push -u origin feature/epic7-java-support
```

### Step 3: Create GitHub Issue (Optional)
```bash
gh issue create --title "Epic 7: Java Language Support" \
  --label epic \
  --milestone v0.8.0 \
  --body "See docs/planning/active/epic7-story-breakdown.md"
```

### Step 4: Start Story 7.1.1
```bash
# Create test fixtures
mkdir -p tests/fixtures/java

# Run first TDD cycle
pytest tests/test_java_parser.py -v  # Should have 0 tests initially
```

---

## 📞 Questions for User

### Q1: User Testing Frequency
**Question**: How often do you want to test during Week 1?

**Options**:
- A) After each Story (4-5 times)
- B) After each Day (5 times)
- C) After Week 1 complete (1 time)

**Recommendation**: Option A (after each Story) for faster feedback

### Q2: Test Project Selection
**Question**: Which Java project will you use for testing?

**Suggestions**:
- Spring PetClinic (recommended, ~5k LOC)
- Your own project
- Another Spring Boot project

### Q3: Communication Style
**Question**: How do you want to receive updates?

**Options**:
- A) Commit message + short summary
- B) Detailed progress report after each task
- C) Only notify when story is complete

**Recommendation**: Option A (commit + summary)

---

**Ready to start?** 🚀

Tell me to proceed, and I'll:
1. Commit planning docs
2. Create feature branch
3. Start Task 7.1.1.1 (Setup Dependencies)
4. Create test fixtures
5. Write first TDD tests

**Your command**: "开始执行" or "按计划开始"
