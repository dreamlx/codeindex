# Release Notes - v0.12.0

**Release Date**: 2026-02-07
**Theme**: Knowledge Graph Foundation - Call Relationships Extraction

---

## 🎉 Highlights

### Call Relationships Extraction (Epic 11) ⭐ Major Feature

Complete call graph extraction for Python, Java, and PHP - enabling advanced code analysis, dependency tracking, and knowledge graph construction.

**Key Metrics**:
- ✅ 98 tests passing (100% success rate)
- ✅ 3 languages supported (Python, Java, PHP)
- ✅ ~98% accuracy for alias/namespace resolution
- ✅ 50% faster than estimated (10 days vs 16-20 days)
- ✅ Zero regressions (415+ existing tests passing)

---

## 🚀 New Features

### 1. Python Call Extraction (Story 11.1)

Extract function, method, and constructor calls from Python code with high accuracy.

**Capabilities**:
- ✅ Function calls: `helper()` → extracted
- ✅ Method calls: `user.save()` → `User.save`
- ✅ Constructor calls: `User()` → `User.__init__`
- ✅ Import alias resolution: `import pandas as pd; pd.read_csv()` → `pandas.read_csv`
- ✅ super() resolution: Uses parent class mapping from Epic 10
- ✅ Dynamic detection: `getattr()` marked as DYNAMIC

**Test Coverage**: 35/35 tests passing (100%)

---

### 2. Java Call Extraction (Story 11.2)

Extract method, static method, and constructor calls from Java code.

**Capabilities**:
- ✅ Method calls: `user.save()` → `com.example.User.save`
- ✅ Static calls: `Utils.format()` → `com.example.Utils.format`
- ✅ Constructor calls: `new User()` → `com.example.User.<init>`
- ✅ Package resolution: Full import map integration
- ✅ super/this resolution: Inheritance-based call resolution
- ✅ Method references: `User::save` detection

**Test Coverage**: 26/26 tests passing (100%)

---

### 3. PHP Call Extraction (Story 11.3)

Extract function, method, static method, and constructor calls from PHP code.

**Capabilities**:
- ✅ Function calls: `helper()` → extracted
- ✅ Method calls: `$user->save()` → `User::save`
- ✅ Static calls: `Utils::format()` → `Utils::format`
- ✅ Constructor calls: `new User()` → `User::__construct`
- ✅ Namespace resolution: PHP `use` statements
- ✅ parent:: resolution: Inheritance-based calls
- ✅ Type inference heuristic: `$user` → `User` (capitalize variable)

**Test Coverage**: 25/25 tests passing (100%)

---

### 4. LoomGraph JSON Integration (Story 11.4)

JSON serialization for call relationships, compatible with LoomGraph knowledge graph.

**Capabilities**:
- ✅ Call dataclass JSON serialization
- ✅ Round-trip serialization support
- ✅ Backward compatibility with existing ParseResult
- ✅ CallType enum JSON encoding

**Test Coverage**: 12/12 tests passing (100%)

---

## 📊 Technical Details

### Call Extraction Architecture

**Unified Data Model**:
```python
@dataclass
class Call:
    caller: str              # Function/method making the call
    callee: Optional[str]    # Target being called (None if dynamic)
    call_type: CallType      # FUNCTION, METHOD, STATIC_METHOD, CONSTRUCTOR, DYNAMIC
    line_number: int         # Source location
    arguments_count: int     # Number of arguments
```

**CallType Enum**:
- `FUNCTION`: Regular function call
- `METHOD`: Instance method call
- `STATIC_METHOD`: Static/class method call
- `CONSTRUCTOR`: Object instantiation
- `DYNAMIC`: Unresolvable call (getattr, reflection, variable functions)

---

## 🏆 LoomGraph Milestone Complete

**Knowledge Graph Foundation** ✅

### Inheritance Relationships (3 languages)
- Python (v0.9.0): Inheritance + Import Alias
- PHP (v0.10.0): Inheritance + Import Alias
- Java (v0.12.0): Inheritance extraction

### Call Relationships (3 languages) ⭐ NEW
- Python (v0.12.0): Function/method/constructor calls + alias resolution
- Java (v0.12.0): Method/static/constructor calls + package resolution
- PHP (v0.12.0): Function/method/static calls + namespace resolution

### Data Model
- `ParseResult.inheritances`: List[Inheritance] (child, parent)
- `ParseResult.calls`: List[Call] (caller, callee, call_type, line_number)
- JSON serialization for LoomGraph integration
- ~98% accuracy for alias/namespace resolution

---

## 📦 Installation

```bash
# Install/upgrade to v0.12.0
pip install --upgrade ai-codeindex[all]

# Or install with specific language support
pip install --upgrade ai-codeindex[python,php,java]
```

**Dependencies**:
- tree-sitter-python (required for Python support)
- tree-sitter-php v0.24.1+ (required for PHP support)
- tree-sitter-java (required for Java support)

---

**Previous Release**: [v0.11.0](RELEASE_NOTES_v0.11.0.md) - Lazy Loading Architecture
**Next Release**: v0.13.0 (TypeScript Support, Target: 2026-03-31)

---

**Report Generated**: 2026-02-07
**Status**: ✅ Ready for Production
