# Framework Route Extractor Template

This template helps you quickly add support for a new web framework to codeindex.

## Quick Start

Follow these steps to add a new framework extractor:

### Step 1: Copy Test Template

```bash
# Copy test template
cp examples/frameworks/template/test_template_extractor.py \
   tests/extractors/test_yourframework.py

# Replace "yourframework" with your framework name (lowercase)
# Example: test_laravel.py, test_fastapi.py, test_django.py
```

### Step 2: Customize Tests

Edit `tests/extractors/test_yourframework.py`:

1. Update class name: `TestYourFrameworkRouteExtractor`
2. Update import: `from codeindex.extractors.yourframework import YourFrameworkRouteExtractor`
3. Update framework name in `test_framework_name()`
4. Customize directory detection in `test_can_extract_from_target_directory()`
5. Update expected URL format in `test_extract_routes_with_line_numbers()`
6. Add framework-specific test cases

### Step 3: Run Tests (RED phase)

```bash
# Tests should fail (extractor doesn't exist yet)
pytest tests/extractors/test_yourframework.py -v
```

Expected output:
```
ImportError: No module named 'codeindex.extractors.yourframework'
```

### Step 4: Copy Extractor Template

```bash
# Copy extractor template
cp examples/frameworks/template/yourframework_extractor.py \
   src/codeindex/extractors/yourframework.py

# Replace "yourframework" with your framework name
```

### Step 5: Implement Extractor

Edit `src/codeindex/extractors/yourframework.py`:

1. Update class name: `YourFrameworkRouteExtractor`
2. Update `framework_name` property
3. Implement `can_extract()` - directory detection logic
4. Implement `extract_routes()` - route extraction logic
5. Customize `_extract_description()` if needed

**Key areas to customize** (marked with `# TODO:`):

```python
class YourFrameworkRouteExtractor(RouteExtractor):
    @property
    def framework_name(self) -> str:
        return "yourframework"  # ← Update this

    def can_extract(self, context: ExtractionContext) -> bool:
        # ← Implement directory detection
        return context.current_dir.name == "controllers"

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        # ← Implement route extraction
        for result in context.parse_results:
            # Find controllers
            # Build URLs
            # Create RouteInfo objects
```

### Step 6: Register Extractor

Edit `src/codeindex/extractors/__init__.py`:

```python
from .yourframework import YourFrameworkRouteExtractor  # Add this
from .thinkphp import ThinkPHPRouteExtractor

__all__ = [
    "YourFrameworkRouteExtractor",  # Add this
    "ThinkPHPRouteExtractor",
]
```

### Step 7: Run Tests (GREEN phase)

```bash
# All tests should pass now
pytest tests/extractors/test_yourframework.py -v
```

Expected output:
```
tests/extractors/test_yourframework.py::TestYourFrameworkRouteExtractor::test_framework_name PASSED
tests/extractors/test_yourframework.py::TestYourFrameworkRouteExtractor::test_can_extract_from_target_directory PASSED
...
======================== 8 passed in 0.05s ========================
```

### Step 8: Verify Integration

```bash
# Run all tests
pytest

# Test with real project
codeindex scan /path/to/your/framework/controllers

# Check output
cat /path/to/your/framework/controllers/README_AI.md
```

Expected output in README_AI.md:
```markdown
## Routes (YourFramework)

| URL | Controller | Action | Location | Description |
|-----|------------|--------|----------|-------------|
| `/users` | UserController | index | `UserController.py:10` | Get user list |
```

### Step 9: Clean Up and Document

1. Remove all `# TODO:` comments
2. Update docstrings with framework-specific details
3. Add more test cases for edge cases
4. Update CHANGELOG.md

## Framework-Specific Examples

### Convention-Based Routing (like ThinkPHP)

**Routing Pattern**: `/module/controller/action`

```python
def extract_routes(self, context):
    module = context.current_dir.parent.name
    controller = controller_class.replace("Controller", "").lower()
    action = method_name
    url = f"/{module}/{controller}/{action}"
```

### Decorator-Based Routing (like FastAPI, Flask)

**Routing Pattern**: Defined in decorators

```python
# @app.get("/users")
# def get_users():
#     ...

# Note: Current parser doesn't extract decorators
# You may need to enhance parser.py or parse raw file
```

### Explicit Route Definitions (like Laravel)

**Routing Pattern**: Defined in routes/*.php

```python
# Route::get('/users', [UserController::class, 'index']);

# Different approach - parse route definition files
# Not controller files
```

## Testing Checklist

Your extractor should have these tests:

- [ ] `test_framework_name()` - Correct framework identifier
- [ ] `test_can_extract_from_*()` - Directory detection
- [ ] `test_extract_routes_with_line_numbers()` - Basic extraction
- [ ] `test_extract_description_from_docstring()` - Description extraction
- [ ] `test_truncate_long_descriptions()` - 60-char limit
- [ ] `test_handle_empty_file()` - Empty/no routes
- [ ] `test_skip_private_methods()` - Filtering logic
- [ ] `test_extract_multiple_routes()` - Multiple routes per file

## Common Patterns

### Pattern 1: Filter by Method Name

```python
# Skip private methods
if method_name.startswith("_"):
    continue

# Skip magic methods
if method_name.startswith("__"):
    continue
```

### Pattern 2: Extract from Directory Structure

```python
# Get module name from parent directory
module = context.current_dir.parent.name

# Get namespace from path
namespace = str(context.current_dir.relative_to(context.root_path))
```

### Pattern 3: Parse Method Signature

```python
# Extract parameters from signature
# "def index(self, request, id=None):" → ["request", "id"]
params = extract_params_from_signature(symbol.signature)
```

## Troubleshooting

**Q: Tests pass but routes don't appear in README_AI.md**

A: Check:
1. Is `can_extract()` returning `True` for your directory?
2. Add debug print in `extract_routes()` to see if it's called
3. Is extractor exported in `__init__.py`?

**Q: `ImportError` when running tests**

A: Make sure:
1. Extractor file is in `src/codeindex/extractors/`
2. File name matches import: `yourframework.py` → `from .yourframework import`
3. Extractor is exported in `__init__.py`

**Q: How do I handle HTTP methods (GET/POST)?**

A: Current `RouteInfo` doesn't have `http_method` field. You can:
1. Add it to `RouteInfo` in `framework_detect.py`
2. Update table format in `smart_writer.py`
3. Extract from decorators or method names

## Reference Implementation

See `src/codeindex/extractors/thinkphp.py` for a complete working example:

- ✅ Convention-based routing
- ✅ Directory structure detection
- ✅ Method filtering (public only)
- ✅ PHPDoc description extraction
- ✅ Comprehensive tests (9 tests)

## Need Help?

- Read the complete guide: [CLAUDE.md](../../../CLAUDE.md#framework-route-extraction)
- Check existing extractor: `src/codeindex/extractors/thinkphp.py`
- See tests: `tests/extractors/test_thinkphp.py`

Good luck! 🚀
