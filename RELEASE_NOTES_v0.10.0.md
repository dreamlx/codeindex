# Release Notes - v0.10.0

**Release Date**: 2026-02-06
**Epic**: Epic 10 Part 2 - PHP LoomGraph Integration
**Status**: ✅ MVP Complete

---

## 📊 Overview

codeindex v0.10.0 extends **LoomGraph knowledge graph integration** to PHP, matching the Python support added in v0.9.0. This release enables PHP projects to benefit from advanced code relationship analysis through inheritance and import alias extraction.

**Key Metrics**:
- **Test Coverage**: 777 passing tests (+48 from v0.9.0), 3 skipped
- **New Features**: PHP inheritance, PHP import aliases, integration validation
- **Breaking Changes**: PHP Import alias field migration (minor)
- **Languages**: Python ✅, PHP ✅ (Java partial)

---

## ✨ What's New

### 1. PHP Inheritance Extraction (Story 10.1.2)

**Capabilities**:
- `extends` single class inheritance
- `implements` multiple interface implementation
- Combined extends + implements patterns
- Namespace resolution with `use` statement mapping

**Example**:
```php
namespace App\Models;

use App\Base\Model;
use Illuminate\Contracts\Auth\Authenticatable;

class User extends Model implements Authenticatable {
    // ...
}
```

**Output**:
```json
{
  "inheritances": [
    {"child": "App\\Models\\User", "parent": "App\\Base\\Model"},
    {"child": "App\\Models\\User", "parent": "Illuminate\\Contracts\\Auth\\Authenticatable"}
  ]
}
```

**Real-World Patterns Supported**:
- Laravel Eloquent Models (`extends Model implements Authenticatable`)
- Symfony Controllers (`extends AbstractController`)
- Abstract classes and final classes
- Multi-level inheritance chains

**Tests**: 17 comprehensive tests covering all PHP inheritance scenarios

---

### 2. PHP Import Alias Extraction (Story 10.2.2)

**Capabilities**:
- Simple aliases: `use App\Service\UserService as US;`
- Group imports: `use App\{UserRepo as UR, OrderRepo};`
- Mixed aliased/non-aliased in group imports
- Namespace-aware resolution

**Key Design Decision**:
```php
// PHP use imports WHOLE class (not specific members like Python)
use App\Service\UserService as US;

// Output:
{
  "module": "App\\Service\\UserService",
  "names": [],        // Always empty for PHP
  "alias": "US",      // Alias in alias field
  "is_from": true
}
```

**Consistency with Python**:
- Both languages use `Import.alias` field
- PHP: `names=[]` (imports whole class)
- Python: `names=["specific_name"]` (can import members)

**Tests**: 15 tests covering all PHP use statement patterns

---

### 3. Integration Testing (Story 10.3)

**Example Files**:
- **`examples/loomgraph_sample.php`** (254 lines)
  - Demonstrates all LoomGraph features for PHP
  - Laravel/Symfony real-world patterns
  - Multiple inheritance patterns
  - Group imports with aliases

- **`examples/loomgraph_php_output.json`**
  - Sample JSON export showing complete structure
  - 22 symbols, 5 imports, 4 inheritances
  - Ready for LoomGraph consumption

**Integration Tests**: 16 tests validating:
- JSON format completeness (all required fields)
- Real-world framework patterns (Laravel, Symfony)
- Edge cases (no inheritance, no imports, empty files)
- Sample file parsing and validation

---

## 🔄 Breaking Changes

### PHP Import Alias Field Migration

**Previous** (v0.9.0 - temporary adaptation):
```python
# Alias was stored in names field
import.module = "App\\Service\\UserService"
import.names = ["US"]  # ❌ Incorrect
```

**Current** (v0.10.0):
```python
# Alias is in alias field
import.module = "App\\Service\\UserService"
import.names = []      # ✅ Correct (PHP imports whole class)
import.alias = "US"    # ✅ Correct
```

**Impact**: Low - Only affects PHP import parsing
**Migration**: Check `import.alias` instead of `import.names[0]`

---

## 📈 Improvements

### Code Quality
- All tests passing: 777 (up from 729)
- No new tech debt introduced
- Consistent Python/PHP API design

### Documentation
- Example files for both Python and PHP
- JSON output samples for reference
- Comprehensive test coverage as documentation

---

## 🐛 Bug Fixes

### PHP Reserved Keyword in Tests
- **Issue**: Tests failed using `OR` as alias (`use X as OR`)
- **Cause**: `OR` is PHP reserved keyword (logical OR operator)
- **Fix**: Tree-sitter correctly identifies as syntax error; updated tests to use valid identifiers
- **Impact**: Test reliability improved

---

## 📦 Installation

```bash
pip install ai-codeindex==0.10.0
```

Or upgrade:
```bash
pip install --upgrade ai-codeindex
```

---

## 🚀 Usage Examples

### Generate JSON for LoomGraph (PHP)

```bash
# Scan single PHP file
codeindex scan ./src/Models/User.php --output json

# Scan entire PHP project
codeindex scan-all --output json > loomgraph_data.json
```

**Output includes**:
- `symbols`: Classes, methods, functions with signatures
- `imports`: Use statements with alias resolution
- `inheritances`: Extends and implements relationships
- `namespace`: PHP namespace declaration

### Integration with LoomGraph

The JSON output can be directly consumed by LoomGraph for:
- Code dependency analysis
- Inheritance graph visualization
- Import relationship mapping
- Architecture understanding

---

## 📊 Statistics

### Test Coverage
- **Total Tests**: 777 passing, 3 skipped
- **New Tests**: +48 tests
  - PHP Inheritance: 17 tests
  - PHP Import Alias: 15 tests
  - Integration Testing: 16 tests

### Code Changes
- **Files Modified**: 5
- **Lines Added**: ~1,300
- **New Features**: 3 major (PHP inheritance, import alias, integration)

---

## 🔮 What's Next

### Epic 10 Part 3: Java LoomGraph Integration
- Java inheritance extraction (extends, implements)
- Java import alias extraction
- Generic type handling
- Annotation-based relationship analysis

### Epic 11: Call Relationship Extraction
- Function/method call graph extraction
- Cross-file call tracking
- Framework-specific call patterns

---

## 🙏 Acknowledgments

This release completes the MVP for multi-language LoomGraph integration, extending knowledge graph capabilities to both Python and PHP ecosystems.

**Development Approach**:
- Strict TDD (Test-Driven Development)
- Incremental story-based delivery
- Comprehensive integration validation

---

## 📚 Resources

- **CHANGELOG**: See `CHANGELOG.md` for detailed changes
- **Examples**: `examples/loomgraph_sample.php`, `examples/loomgraph_php_output.json`
- **Planning**: `docs/planning/active/epic10-part2-php-loomgraph.md`
- **Tests**: `tests/test_php_inheritance.py`, `tests/test_php_import_alias.py`, `tests/test_php_loomgraph_integration.py`

---

**Version**: 0.10.0
**Previous Version**: 0.9.0
**Release Date**: 2026-02-06
**Epic**: Epic 10 Part 2 (Complete)
