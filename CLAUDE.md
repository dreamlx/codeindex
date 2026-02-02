# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🧭 Claude Code 工作流指南

### 📖 理解项目架构（分析模式）

**⚠️ 重要：本项目有多层次的 README_AI.md 文件，是理解代码的最佳入口**

1. **第一步：阅读 README_AI.md（必须）**
   ```
   优先级顺序：
   1. /README_AI.md                    # 整体项目概览
   2. /src/codeindex/README_AI.md      # 核心模块架构
   3. /tests/README_AI.md              # 测试结构和覆盖
   4. /docs/README_AI.md (如果存在)    # 文档组织
   ```

2. **第二步：查看专门的索引文件**
   - `PROJECT_SYMBOLS.md` - 全局符号索引和跨文件引用
   - `CHANGELOG.md` - 版本演进和功能变更
   - `RELEASE_NOTES_*.md` - 重大版本说明

3. **避免的做法 ❌**
   - 直接用 Glob/Grep 搜索源码（低效且无结构）
   - 不看 README_AI.md 就直接读 .py 文件
   - 忽略已有的符号索引文件

### 🔍 定位具体代码（导航模式）

**使用 Serena MCP 工具进行精确导航：**

1. **查找符号定义**
   ```python
   # 使用 find_symbol 而不是 Grep
   find_symbol(name_path_pattern="AdaptiveSymbolSelector")
   find_symbol(name_path_pattern="SmartWriter/write_readme")
   ```

2. **查找符号引用**
   ```python
   # 找谁在用这个函数
   find_referencing_symbols(
       name_path="calculate_limit",
       relative_path="src/codeindex/adaptive_selector.py"
   )
   ```

3. **搜索模式匹配**
   ```python
   # 只在必要时使用 search_for_pattern
   search_for_pattern(
       substring_pattern="file_lines",
       restrict_search_to_code_files=True
   )
   ```

4. **获取符号概览**
   ```python
   # 快速了解文件结构
   get_symbols_overview(
       relative_path="src/codeindex/parser.py",
       depth=1  # 包含方法列表
   )
   ```

### 📁 项目特殊文件说明

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| `README_AI.md` | AI生成的目录文档 | 理解任何目录的架构和组件 |
| `PROJECT_SYMBOLS.md` | 全局符号索引 | 查找符号定义位置 |
| `CHANGELOG.md` | 版本变更历史 | 了解功能演进和破坏性变更 |
| `RELEASE_NOTES_*.md` | 发布说明 | 查看重大版本的详细信息 |
| `.codeindex.yaml` | 配置文件 | 理解扫描规则和AI集成 |
| `docs/planning/*.md` | Epic/Story规划 | 查看功能设计决策 |
| `docs/evaluation/*.md` | 验证报告 | 查看功能验证结果 |

### 🎯 典型场景示例

**场景1：我想理解 adaptive symbol extraction 是如何工作的**
```
1. 读取 src/codeindex/README_AI.md
   → 找到 "AdaptiveSymbolSelector" 组件说明
2. 使用 find_symbol(name_path_pattern="AdaptiveSymbolSelector")
   → 查看类定义和方法
3. 读取 docs/planning/epic2-adaptive-symbols-plan.md
   → 理解设计决策
4. 读取 tests/test_adaptive_selector.py
   → 查看使用示例和边界情况
```

**场景2：我想找到所有使用 file_lines 的地方**
```
1. 使用 search_for_pattern(substring_pattern="file_lines")
   → 获取所有引用位置
2. 使用 find_symbol 查看核心定义
3. 使用 find_referencing_symbols 查看依赖关系
```

**场景3：我想修改符号评分算法**
```
1. 读取 src/codeindex/README_AI.md
   → 找到 SymbolImportanceScorer
2. 使用 get_symbols_overview("src/codeindex/symbol_scorer.py", depth=1)
   → 查看所有评分方法
3. 读取 tests/test_symbol_scorer.py
   → 理解评分规则和测试用例
4. 使用 find_referencing_symbols 查看调用方
   → 评估修改影响范围
```

## Quick Start (常用命令)

```bash
# 🚀 生成所有目录的索引 (最常用)
codeindex scan-all --fallback

# 查看会扫描哪些目录
codeindex list-dirs

# 生成全局符号索引
codeindex symbols

# 查看索引覆盖率
codeindex status
```

## 配置说明 (.codeindex.yaml)

```yaml
# ✅ 推荐：只指定顶层目录，自动递归扫描所有子目录
include:
  - Application    # 会扫描 Application 下所有子目录
  - src            # 会扫描 src 下所有子目录

# ❌ 不推荐：逐个列出每个子目录
include:
  - Application/Admin/Controller
  - Application/Admin/Model
  - Application/Retail/Controller
  # ... 太繁琐
```

**关键行为**：
- `include` 中的目录会**递归扫描所有子目录**
- 每个有代码文件的子目录都会生成独立的 `README_AI.md`
- 文件大小限制 50KB，超出会自动截断

## Build & Development Commands

```bash
# Install (development mode)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_parser.py::test_parse_simple_function

# Lint
ruff check src/

# CLI usage (详细)
codeindex scan ./src/auth          # 扫描单个目录
codeindex scan ./src/auth --fallback  # 不使用 AI 生成
codeindex scan ./src/auth --dry-run   # 预览 prompt
codeindex init                     # 创建 .codeindex.yaml
codeindex status                   # 查看索引覆盖率
codeindex list-dirs                # 列出可索引目录
codeindex symbols                  # 生成全局符号索引
```

## Architecture

codeindex is an AI-native code indexing tool that generates `README_AI.md` files for directories by invoking external AI CLI tools.

### Core Pipeline

1. **Scanner** (`scanner.py`) - Walks directories, filters by config patterns, returns `ScanResult` with files
2. **Parser** (`parser.py`) - Uses tree-sitter to extract symbols (classes, functions, methods), imports, and docstrings from Python files
3. **Writer** (`writer.py`) - Formats parsed data into prompts, writes output files
4. **Invoker** (`invoker.py`) - Executes external AI CLI commands with the prompt, handles timeouts
5. **CLI** (`cli.py`) - Click-based entry point, orchestrates the pipeline

### Data Flow

```
Directory → Scanner → [files] → Parser → [ParseResult] → Writer (format) →
    Invoker (AI CLI) → Writer (write) → README_AI.md
```

### Key Types

- `ScanResult`: Contains path, files, subdirs
- `ParseResult`: Contains path, symbols, imports, module_docstring, error
- `Symbol`: name, kind (class/function/method), signature, docstring, line range
- `Import`: module, names, is_from
- `Config`: Loaded from `.codeindex.yaml`, controls AI command, include/exclude patterns, languages

### External AI CLI Integration

The tool invokes external AI CLIs via shell subprocess. The `ai_command` config uses `{prompt}` as placeholder:
```yaml
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'
```

Fallback mode (`--fallback`) generates basic README without AI.

## Configuration

Config file: `.codeindex.yaml` (see `examples/.codeindex.yaml`)
- `ai_command`: Shell command template with `{prompt}` placeholder
- `include`/`exclude`: Glob patterns for directory filtering
- `languages`: Currently only `python` supported
- `output_file`: Default `README_AI.md`

---

## 🛣️ Framework Route Extraction (v0.5.0+)

### Architecture Overview

codeindex uses a **plugin-based architecture** for framework route extraction. New frameworks can be added without modifying core code.

**Core Components**:

```
src/codeindex/
├── route_extractor.py          # Abstract base class + data structures
│   ├── RouteExtractor (ABC)    # Base class for all extractors
│   ├── ExtractionContext       # Context passed to extractors
│   └── (RouteInfo in framework_detect.py)
│
├── route_registry.py           # Extractor registration and discovery
│   └── RouteExtractorRegistry  # Auto-discovers and manages extractors
│
└── extractors/                 # Framework-specific implementations
    ├── __init__.py             # Exports all extractors
    ├── thinkphp.py            # ✅ ThinkPHP extractor (reference impl)
    ├── laravel.py             # 🔄 TODO: Laravel extractor
    └── fastapi.py             # 🔄 TODO: FastAPI extractor
```

**Data Flow**:

```
SmartWriter._generate_detailed()
    ↓
RouteExtractorRegistry.extract_routes(context)
    ↓
For each registered extractor:
    if extractor.can_extract(context):
        routes = extractor.extract_routes(context)
    ↓
_format_route_table(routes)
    ↓
README_AI.md (with route table)
```

### How to Add a New Framework Extractor

Follow this **TDD process** to add support for a new web framework:

---

#### Step 1: Create Test File First (RED)

**File**: `tests/extractors/test_myframework.py`

```python
"""Tests for MyFramework route extractor."""

from pathlib import Path

from codeindex.extractors.myframework import MyFrameworkRouteExtractor
from codeindex.parser import ParseResult, Symbol
from codeindex.route_extractor import ExtractionContext


class TestMyFrameworkRouteExtractor:
    """Test MyFramework route extractor."""

    def test_framework_name(self):
        """Should return correct framework name."""
        extractor = MyFrameworkRouteExtractor()
        assert extractor.framework_name == "myframework"

    def test_can_extract_from_controllers_directory(self):
        """Should extract only from controllers directory."""
        extractor = MyFrameworkRouteExtractor()

        # Should extract from controllers/
        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=[],
        )
        assert extractor.can_extract(context) is True

        # Should NOT extract from other directories
        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/models"),
            parse_results=[],
        )
        assert extractor.can_extract(context) is False

    def test_extract_routes_with_line_numbers(self):
        """Should extract routes with line numbers."""
        extractor = MyFrameworkRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring="Get user list",
                        line_start=10,
                        line_end=15,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert routes[0].url == "/users"
        assert routes[0].controller == "UserController"
        assert routes[0].action == "index"
        assert routes[0].line_number == 10
        assert routes[0].file_path == "UserController.py"

    def test_extract_description_from_docstring(self):
        """Should extract description from method docstring."""
        extractor = MyFrameworkRouteExtractor()

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring="Get user list with pagination",
                        line_start=10,
                        line_end=15,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert routes[0].description == "Get user list with pagination"

    def test_truncate_long_descriptions(self):
        """Should truncate descriptions longer than 60 characters."""
        extractor = MyFrameworkRouteExtractor()

        long_desc = "This is a very long description that exceeds 60 chars limit"

        parse_results = [
            ParseResult(
                path=Path("UserController.py"),
                symbols=[
                    Symbol(
                        name="UserController",
                        kind="class",
                        signature="class UserController:",
                        docstring="",
                        line_start=1,
                        line_end=50,
                    ),
                    Symbol(
                        name="index",
                        kind="method",
                        signature="def index(self, request):",
                        docstring=long_desc,
                        line_start=10,
                        line_end=15,
                    ),
                ],
            )
        ]

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=parse_results,
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 1
        assert len(routes[0].description) <= 63  # 60 + "..."
        assert routes[0].description.endswith("...")

    def test_handle_empty_file(self):
        """Should return empty list for files with no routes."""
        extractor = MyFrameworkRouteExtractor()

        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=[],
        )

        routes = extractor.extract_routes(context)

        assert len(routes) == 0

    def test_skip_private_methods(self):
        """Should skip private methods (starting with _)."""
        # Framework-specific test - implement based on your rules
        pass
```

**Run the test** (it should fail):

```bash
pytest tests/extractors/test_myframework.py -v
# Expected: ImportError or test failures ❌
```

---

#### Step 2: Create Extractor Implementation (GREEN)

**File**: `src/codeindex/extractors/myframework.py`

```python
"""MyFramework route extractor.

MyFramework routing convention:
- URL: /controller/action
- Example: /users/index -> UserController.index()
"""

from ..framework_detect import RouteInfo
from ..route_extractor import ExtractionContext, RouteExtractor


class MyFrameworkRouteExtractor(RouteExtractor):
    """
    Route extractor for MyFramework.

    MyFramework uses convention-based routing where:
    - Controllers are in controllers/ directory
    - URL pattern: /{controller}/{action}
    - Only public methods are routes
    - Methods starting with _ are excluded
    """

    @property
    def framework_name(self) -> str:
        """Return framework name."""
        return "myframework"

    def can_extract(self, context: ExtractionContext) -> bool:
        """
        Check if routes should be extracted from this directory.

        Routes are extracted only from controllers/ directories.

        Args:
            context: Extraction context

        Returns:
            True if current directory is a controllers directory
        """
        return context.current_dir.name == "controllers"

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """
        Extract routes from MyFramework controllers.

        Args:
            context: Extraction context with parse results

        Returns:
            List of RouteInfo objects for each public method in controllers
        """
        routes = []

        for result in context.parse_results:
            if result.error:
                continue

            # Find controller class
            controller_class = None
            for symbol in result.symbols:
                if symbol.kind == "class" and symbol.name.endswith("Controller"):
                    controller_class = symbol.name
                    break

            if not controller_class:
                continue

            # Extract controller name (remove "Controller" suffix)
            controller_name = controller_class.replace("Controller", "").lower()

            # Find public methods (actions)
            for symbol in result.symbols:
                if symbol.kind != "method":
                    continue

                # Skip private methods (starting with _)
                method_name = symbol.name.split("::")[-1]
                if method_name.startswith("_"):
                    continue

                # Build route URL: /controller/action
                url = f"/{controller_name}/{method_name}"

                routes.append(
                    RouteInfo(
                        url=url,
                        controller=controller_class,
                        action=method_name,
                        method_signature=symbol.signature,
                        line_number=symbol.line_start,
                        file_path=result.path.name,
                        description=self._extract_description(symbol),
                    )
                )

        return routes

    def _extract_description(self, symbol) -> str:
        """
        Extract description from symbol docstring.

        Limits description to 60 characters for table display.

        Args:
            symbol: Symbol with docstring

        Returns:
            Cleaned description (max 60 chars + "...")
        """
        if not symbol.docstring:
            return ""

        description = symbol.docstring.strip()

        # Limit length for table display
        if len(description) > 60:
            return description[:60] + "..."

        return description
```

**Run the tests** (they should pass):

```bash
pytest tests/extractors/test_myframework.py -v
# Expected: All tests pass ✅
```

---

#### Step 3: Register Extractor

**File**: `src/codeindex/extractors/__init__.py`

```python
"""Framework route extractors."""

from .myframework import MyFrameworkRouteExtractor  # ← Add this
from .thinkphp import ThinkPHPRouteExtractor

__all__ = [
    "MyFrameworkRouteExtractor",  # ← Add this
    "ThinkPHPRouteExtractor",
]
```

**That's it!** The extractor is automatically discovered and registered.

---

#### Step 4: Verify Integration

**Run all tests**:

```bash
# All tests should pass
pytest
```

**Test with real project**:

```bash
# Scan a MyFramework controller directory
codeindex scan /path/to/myframework/controllers

# Check README_AI.md for route table
cat /path/to/myframework/controllers/README_AI.md
```

Expected output:

```markdown
## Routes (MyFramework)

| URL | Controller | Action | Location | Description |
|-----|------------|--------|----------|-------------|
| `/users/index` | UserController | index | `UserController.py:10` | Get user list with pagination |
```

---

### Testing Guidelines

**Required Test Coverage** (minimum 7 tests):

1. ✅ `test_framework_name()` - Verify framework identifier
2. ✅ `test_can_extract_from_*()` - Directory detection logic
3. ✅ `test_extract_routes_with_line_numbers()` - Basic extraction
4. ✅ `test_extract_description_from_docstring()` - Description extraction
5. ✅ `test_truncate_long_descriptions()` - 60-char limit
6. ✅ `test_handle_empty_file()` - Empty/no routes case
7. ✅ `test_skip_*()` - Framework-specific filtering rules

**Test Structure Template**:

```python
class TestMyFrameworkRouteExtractor:
    """Test MyFramework route extractor."""

    # 1. Basic properties
    def test_framework_name(self): ...

    # 2. Directory detection
    def test_can_extract_from_**(self): ...

    # 3. Route extraction
    def test_extract_routes_with_line_numbers(self): ...
    def test_extract_multiple_routes(self): ...

    # 4. Description handling
    def test_extract_description_from_docstring(self): ...
    def test_truncate_long_descriptions(self): ...
    def test_handle_empty_description(self): ...

    # 5. Edge cases
    def test_handle_empty_file(self): ...
    def test_handle_parse_error(self): ...

    # 6. Framework-specific rules
    def test_skip_private_methods(self): ...
    def test_filter_magic_methods(self): ...
```

---

### Existing Extractors Reference

#### ThinkPHP Extractor

**File**: `src/codeindex/extractors/thinkphp.py`

**Routing Convention**:
- URL pattern: `/{module}/{controller}/{action}`
- Example: `/admin/user/index` → `Admin\Controller\UserController::index()`

**Directory Structure**:
```
Application/
└── Admin/                    # Module
    └── Controller/          # ← Detected by can_extract()
        └── UserController.php
```

**Key Logic**:
- Detects from `Application/{Module}/Controller/` structure
- Filters: Only `public` methods
- Excludes: Magic methods (`__*`), internal methods (`_*`)
- Description: From PHPDoc comments

**See Tests**: `tests/extractors/test_thinkphp.py` (9 tests)

---

### Route Display Format

Routes are displayed in README_AI.md as markdown tables:

```markdown
## Routes (MyFramework)

| URL | Controller | Action | Location | Description |
|-----|------------|--------|----------|-------------|
| `/users` | UserController | index | `UserController.py:10` | Get user list |
| `/users/create` | UserController | create | `UserController.py:20` | Create new user |
| `/posts` | PostController | index | `PostController.py:15` | List all posts with pagination support and filteri... |
```

**Table Columns**:

| Column | Content | Example |
|--------|---------|---------|
| **URL** | Route path | `/users/index` |
| **Controller** | Controller class name | `UserController` |
| **Action** | Method/action name | `index` |
| **Location** | Clickable `file:line` | `UserController.py:10` |
| **Description** | From docstring (max 60 chars) | `Get user list` |

**Formatting** (handled by `SmartWriter._format_route_table()`):
- Up to 30 routes displayed
- Remaining routes shown as: `| ... | _N more routes_ | | | |`
- URLs wrapped in backticks: `` `{route.url}` ``
- Locations wrapped in backticks: `` `{route.location}` ``

---

### Framework Detection (Optional)

If your framework needs custom detection logic, update:

**File**: `src/codeindex/framework_detect.py`

```python
def detect_framework(path: Path) -> str | None:
    """Detect web framework from directory structure."""

    # Add your framework detection
    if (path / "myframework.conf").exists():
        return "myframework"

    if (path / "config" / "myframework.yaml").exists():
        return "myframework"

    # ... existing detection ...
```

**Note**: Most extractors don't need this. The `can_extract()` method is usually sufficient.

---

### Important Implementation Notes

**1. No Manual Registration Required**

Extractors are **auto-discovered** via `RouteExtractorRegistry`:

```python
# In route_registry.py
for name, obj in inspect.getmembers(extractors_module):
    if inspect.isclass(obj) and issubclass(obj, RouteExtractor):
        # Automatically registered!
```

**2. Description Length Limit**

**Always truncate** to 60 chars:

```python
if len(description) > 60:
    return description[:60] + "..."
```

**Why?** Markdown tables break with very long text.

**3. Error Handling**

**Always check** `result.error`:

```python
for result in context.parse_results:
    if result.error:
        continue  # ← Skip files with parse errors
```

**4. Performance Considerations**

- Keep extraction logic **fast** (runs on every scan)
- Avoid heavy computation in `can_extract()`
- Don't make external API calls

**5. TDD is Required**

- **Write tests first** (RED)
- **Implement to pass** (GREEN)
- **Refactor and verify** (REFACTOR)

**6. Symbol Name Format**

Python methods may include class prefix:

```python
# symbol.name could be:
"index"                    # Simple name
"UserController::index"    # With class prefix

# Safe extraction:
method_name = symbol.name.split("::")[-1]
```

---

### Common Patterns

#### Pattern 1: Convention-Based Routing (ThinkPHP, Django)

```python
def extract_routes(self, context):
    # Build URL from directory structure + method name
    url = f"/{module}/{controller}/{action}"
```

#### Pattern 2: Decorator-Based Routing (FastAPI, Flask)

```python
# Need to parse decorators from AST
# @app.get("/users")
# def get_users():
#     ...

# Will require enhanced parser support
```

#### Pattern 3: Explicit Route Definitions (Laravel)

```python
# Parse routes/*.php files
# Route::get('/users', [UserController::class, 'index']);

# Different approach - parse route definition files
```

---

### Need Help?

**Reference Materials**:
- **Example Implementation**: `src/codeindex/extractors/thinkphp.py`
- **Example Tests**: `tests/extractors/test_thinkphp.py`
- **Base Class**: `src/codeindex/route_extractor.py`
- **Route Display**: `src/codeindex/smart_writer.py::_format_route_table()`

**Common Questions**:

**Q: How do I test my extractor?**
A: See Step 1 - write comprehensive tests first (TDD)

**Q: My framework uses decorators for routing. How do I parse them?**
A: Current parser doesn't extract decorators. You may need to enhance `parser.py` or parse raw file content.

**Q: Routes don't appear in README_AI.md. Why?**
A: Check:
1. Is `can_extract()` returning `True`?
2. Are routes being extracted? (debug with print statements)
3. Is the extractor exported in `__init__.py`?

**Q: Can I filter routes by HTTP method (GET/POST)?**
A: Yes! Add `http_method` field to `RouteInfo` and update table format.

---

## 🪝 Git Hooks Management (v0.5.0+)

### Quick Reference

codeindex provides **built-in Git Hooks management** for automating code quality checks and documentation updates.

**For detailed development guide**: See `docs/development/git-hooks-architecture.md`
**For user integration guide**: See `docs/guides/git-hooks-integration.md`

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Git Hooks System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────┐      ┌──────────────┐                   │
│  │  HookManager  │─────▶│ Hook Scripts │                   │
│  │               │      │  Generation  │                   │
│  │ - install()   │      └──────────────┘                   │
│  │ - uninstall() │                                          │
│  │ - status()    │      ┌──────────────┐                   │
│  └───────────────┘      │    Backup    │                   │
│         │               │   & Restore  │                   │
│         │               └──────────────┘                   │
│         ▼                                                    │
│  .git/hooks/                                                │
│    ├── pre-commit       (L1: lint, L2: debug detection)    │
│    ├── post-commit      (auto-update README_AI.md)         │
│    └── pre-push         (placeholder)                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

1. **Centralized Management**: `HookManager` class handles all hook operations
2. **Template-Based**: Generate hook scripts from templates, not hardcoded
3. **Safety First**: Automatic backup before overwriting custom hooks
4. **Marker-Based Detection**: Use `# codeindex-managed hook` to identify our hooks
5. **CLI Integration**: Click commands for user-friendly management

---

### Step-by-Step: Creating a Hook Management System

#### Step 1: Define Hook Status (RED)

**Test First** (`tests/test_cli_hooks.py`):

```python
"""Tests for Git Hooks CLI module."""
import os
from pathlib import Path
from unittest.mock import patch

from codeindex.cli_hooks import (
    HookManager,
    HookStatus,
    backup_existing_hook,
    detect_existing_hooks,
    generate_hook_script,
)


class TestHookManager:
    """Test HookManager class."""

    def test_init_with_repo_path(self, tmp_path):
        """Should initialize with given repository path."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        manager = HookManager(repo_path)

        assert manager.repo_path == repo_path
        assert manager.hooks_dir == repo_path / ".git" / "hooks"

    def test_get_hook_status_not_exists(self, tmp_path):
        """Should return NOT_INSTALLED when hook doesn't exist."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        manager = HookManager(repo_path)
        status = manager.get_hook_status("pre-commit")

        assert status == HookStatus.NOT_INSTALLED

    def test_get_hook_status_exists_codeindex(self, tmp_path):
        """Should return INSTALLED when codeindex hook exists."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create hook with codeindex marker
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\n# codeindex-managed hook\necho 'test'")
        hook_file.chmod(0o755)

        manager = HookManager(repo_path)
        status = manager.get_hook_status("pre-commit")

        assert status == HookStatus.INSTALLED

    def test_get_hook_status_exists_custom(self, tmp_path):
        """Should return CUSTOM when non-codeindex hook exists."""
        repo_path = tmp_path / "test_repo"
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create custom hook without codeindex marker
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("#!/bin/bash\necho 'custom hook'")
        hook_file.chmod(0o755)

        manager = HookManager(repo_path)
        status = manager.get_hook_status("pre-commit")

        assert status == HookStatus.CUSTOM
```

**Run Tests** (should FAIL ❌):
```bash
pytest tests/test_cli_hooks.py -v
# NameError: name 'HookStatus' is not defined
```

#### Step 2: Implement HookManager (GREEN)

**Implementation** (`src/codeindex/cli_hooks.py`):

```python
"""Git Hooks management module for codeindex.

Epic 6, P3.1: Automate Git Hooks installation and management.

This module provides:
- HookManager: Manage Git hooks installation/uninstall
- Hook script generation with templates
- Backup and restore existing hooks
- Detect and merge with existing hooks
"""

import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import click

from .cli_common import console


class HookStatus(Enum):
    """Status of a Git hook."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"  # codeindex-managed
    CUSTOM = "custom"  # User's custom hook


class HookManager:
    """Manage Git hooks for codeindex."""

    CODEINDEX_MARKER = "# codeindex-managed hook"
    SUPPORTED_HOOKS = ["pre-commit", "post-commit", "pre-push"]

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize HookManager.

        Args:
            repo_path: Path to Git repository. If None, uses current directory.
        """
        if repo_path is None:
            repo_path = self._find_git_repo()

        self.repo_path = Path(repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"

        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        # Create hooks directory if it doesn't exist
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def _find_git_repo(self) -> Path:
        """Find git repository by walking up directory tree."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        raise ValueError("Not in a git repository")

    def get_hook_status(self, hook_name: str) -> HookStatus:
        """
        Get status of a hook.

        Args:
            hook_name: Name of hook (e.g., "pre-commit")

        Returns:
            HookStatus indicating current state
        """
        hook_file = self.hooks_dir / hook_name

        if not hook_file.exists():
            return HookStatus.NOT_INSTALLED

        content = hook_file.read_text()
        if self.CODEINDEX_MARKER in content:
            return HookStatus.INSTALLED

        return HookStatus.CUSTOM

    def install_hook(
        self, hook_name: str, backup: bool = True, force: bool = False
    ) -> bool:
        """
        Install a hook.

        Args:
            hook_name: Name of hook to install
            backup: Whether to backup existing hook
            force: Overwrite existing codeindex hook

        Returns:
            True if successful
        """
        hook_file = self.hooks_dir / hook_name
        status = self.get_hook_status(hook_name)

        # Skip if already installed (unless force)
        if status == HookStatus.INSTALLED and not force:
            return False

        # Backup existing custom hook
        if status == HookStatus.CUSTOM and backup:
            backup_existing_hook(hook_file)

        # Generate and write hook script
        script = generate_hook_script(hook_name)
        hook_file.write_text(script)
        hook_file.chmod(0o755)

        return True

    def uninstall_hook(
        self, hook_name: str, restore_backup: bool = True
    ) -> bool:
        """
        Uninstall a hook.

        Args:
            hook_name: Name of hook to uninstall
            restore_backup: Whether to restore backup

        Returns:
            True if successful
        """
        hook_file = self.hooks_dir / hook_name
        status = self.get_hook_status(hook_name)

        # Only uninstall codeindex hooks
        if status != HookStatus.INSTALLED:
            return False

        # Remove hook file
        hook_file.unlink()

        # Restore backup if exists
        if restore_backup:
            backup_file = self.hooks_dir / f"{hook_name}.backup"
            if backup_file.exists():
                shutil.move(backup_file, hook_file)
                hook_file.chmod(0o755)

        return True

    def list_all_hooks(self) -> dict:
        """
        List status of all supported hooks.

        Returns:
            Dict mapping hook name to HookStatus
        """
        return {
            hook: self.get_hook_status(hook) for hook in self.SUPPORTED_HOOKS
        }
```

**Run Tests** (should PASS ✅):
```bash
pytest tests/test_cli_hooks.py -v
# test_init_with_repo_path PASSED
# test_get_hook_status_not_exists PASSED
# test_get_hook_status_exists_codeindex PASSED
# test_get_hook_status_exists_custom PASSED
```

#### Step 3: Generate Hook Scripts

**Hook scripts are shell scripts**. Use template approach:

```python
def generate_hook_script(
    hook_name: str, config: Optional[dict] = None
) -> str:
    """
    Generate hook script content.

    Args:
        hook_name: Name of hook (e.g., "pre-commit")
        config: Optional configuration for customization

    Returns:
        Hook script as string
    """
    config = config or {}

    if hook_name == "pre-commit":
        return _generate_pre_commit_script(config)
    elif hook_name == "post-commit":
        return _generate_post_commit_script(config)
    elif hook_name == "pre-push":
        return _generate_pre_push_script(config)
    else:
        raise ValueError(f"Unsupported hook: {hook_name}")


def _generate_pre_commit_script(config: dict) -> str:
    """Generate pre-commit hook script."""
    lint_enabled = config.get("lint_enabled", True)

    script = """#!/bin/zsh
# codeindex-managed hook
# Pre-commit hook for codeindex
# L1: Lint check (ruff)
# L2: Forbid debug code (print/breakpoint)

set -e

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[0;33m'
NC='\\033[0m' # No Color

# Try to activate virtual environment if exists
REPO_ROOT=$(git rev-parse --show-toplevel)
if [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
elif [ -f "$REPO_ROOT/venv/bin/activate" ]; then
    source "$REPO_ROOT/venv/bin/activate"
fi

echo "🔍 Running pre-commit checks..."

# Get staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    echo "${GREEN}✓ No Python files to check${NC}"
    exit 0
fi

echo "   Checking files: $(echo $STAGED_PY_FILES | wc -w | tr -d ' ') Python files"
"""

    if lint_enabled:
        script += """
# ============================================
# L1: Ruff lint check
# ============================================
echo "\\n${YELLOW}[L1] Running ruff lint...${NC}"

# Try venv ruff first, then system ruff
RUFF_CMD=""
if [ -f "$REPO_ROOT/.venv/bin/ruff" ]; then
    RUFF_CMD="$REPO_ROOT/.venv/bin/ruff"
elif command -v ruff &> /dev/null; then
    RUFF_CMD="ruff"
else
    echo "${RED}✗ ruff not found. Install with: pip install ruff${NC}"
    exit 1
fi

# Check only staged files
STAGED_FILES_ARRAY=()
while IFS= read -r file; do
    if [ -f "$file" ]; then
        STAGED_FILES_ARRAY+=("$file")
    fi
done < <(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$' || true)

if [ ${#STAGED_FILES_ARRAY[@]} -eq 0 ]; then
    echo "${GREEN}✓ No files to lint${NC}"
else
    if ! $RUFF_CMD check "${STAGED_FILES_ARRAY[@]}"; then
        echo "\\n${RED}✗ Lint errors found. Fix them before committing.${NC}"
        echo "   Run: ruff check --fix src/"
        exit 1
    fi
    echo "${GREEN}✓ Lint check passed${NC}"
fi
"""

    script += """
# ============================================
# L2: Debug code detection
# ============================================
echo "\\n${YELLOW}[L2] Checking for debug code...${NC}"

DEBUG_PATTERNS=(
    'print\\s*\\('           # print() statements
    'breakpoint\\s*\\('      # breakpoint() calls
    'pdb\\.set_trace\\s*\\('  # pdb debugger
    'import\\s+pdb'         # pdb import
    'from\\s+pdb\\s+import'  # from pdb import
)

FOUND_DEBUG=0
for file in $STAGED_PY_FILES; do
    # Skip CLI files and modules that use print() for legitimate output
    if [[ "$file" == *"/cli"* ]] || [[ "$file" == *"/cli_"* ]] || \\
       [[ "$file" == *"hierarchical.py"* ]] || \\
       [[ "$file" == *"directory_tree.py"* ]] || \\
       [[ "$file" == *"adaptive_selector.py"* ]]; then
        continue
    fi

    # Get only staged content (not working directory)
    STAGED_CONTENT=$(git show ":$file" 2>/dev/null || true)

    if [ -z "$STAGED_CONTENT" ]; then
        continue
    fi

    for pattern in $DEBUG_PATTERNS; do
        # Find matches with line numbers
        MATCHES=$(echo "$STAGED_CONTENT" | grep -n -E "$pattern" || true)
        if [ -n "$MATCHES" ]; then
            if [ $FOUND_DEBUG -eq 0 ]; then
                echo "${RED}✗ Debug code found:${NC}"
                FOUND_DEBUG=1
            fi
            echo "   ${file}:"
            echo "$MATCHES" | while read line; do
                echo "      $line"
            done
        fi
    done
done

if [ $FOUND_DEBUG -eq 1 ]; then
    echo "\\n${RED}✗ Remove debug code before committing.${NC}"
    echo "   Tip: Use logging module instead of print()"
    exit 1
fi

echo "${GREEN}✓ No debug code found${NC}"

echo "\\n${GREEN}✓ All pre-commit checks passed!${NC}"
exit 0
"""

    return script
```

#### Step 4: Add CLI Commands

**Register commands** (`src/codeindex/cli.py`):

```python
from .cli_hooks import hooks

main.add_command(hooks)
```

**CLI commands** (`src/codeindex/cli_hooks.py`):

```python
@click.group()
def hooks():
    """Manage Git hooks for codeindex."""
    pass


@hooks.command()
@click.option(
    "--all",
    "install_all",
    is_flag=True,
    help="Install all supported hooks",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing codeindex hooks",
)
@click.argument("hook_name", required=False)
def install(hook_name: Optional[str], install_all: bool, force: bool):
    """Install Git hooks for codeindex."""
    try:
        manager = HookManager()

        # Determine hooks to install
        if install_all:
            hooks_to_install = manager.SUPPORTED_HOOKS
        elif hook_name:
            hooks_to_install = [hook_name]
        else:
            console.print(
                "[yellow]Usage:[/yellow] codeindex hooks install <hook-name> or --all"
            )
            raise click.Abort()

        console.print("\n[bold]Installing Git Hooks[/bold]\n")

        installed_count = 0
        backed_up = []

        for hook in hooks_to_install:
            status = manager.get_hook_status(hook)

            if status == HookStatus.INSTALLED and not force:
                console.print(f"  [dim]→ {hook}: already installed (use --force to reinstall)[/dim]")
                continue

            if status == HookStatus.CUSTOM:
                backed_up.append(f"{hook} → {hook}.backup")

            result = manager.install_hook(hook, backup=True, force=force)

            if result:
                console.print(f"  [green]✓[/green] {hook}: installed")
                installed_count += 1

        console.print()

        if backed_up:
            console.print("[yellow]Backups created:[/yellow]")
            for backup in backed_up:
                console.print(f"  {backup}")
            console.print()

        console.print(
            f"[green]✓[/green] Successfully installed {installed_count} hook(s)\n"
        )

    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}", style="red")
        raise click.Abort()


@hooks.command()
def status():
    """Show status of Git hooks."""
    try:
        manager = HookManager()
        statuses = manager.list_all_hooks()

        console.print("\n[bold]Git Hooks Status[/bold]\n")

        # Status indicators
        status_icons = {
            HookStatus.INSTALLED: "[green]✓[/green]",
            HookStatus.CUSTOM: "[yellow]⚠[/yellow]",
            HookStatus.NOT_INSTALLED: "[dim]○[/dim]",
        }

        status_labels = {
            HookStatus.INSTALLED: "[green]installed[/green]",
            HookStatus.CUSTOM: "[yellow]custom[/yellow]",
            HookStatus.NOT_INSTALLED: "[dim]not installed[/dim]",
        }

        for hook_name in manager.SUPPORTED_HOOKS:
            status = statuses[hook_name]
            icon = status_icons[status]
            label = status_labels[status]
            console.print(f"  {icon} {hook_name}: {label}")

        console.print()

        installed_count = sum(
            1 for s in statuses.values() if s == HookStatus.INSTALLED
        )
        if installed_count > 0:
            console.print(f"→ {installed_count} codeindex hook(s) installed\n")

    except ValueError as e:
        console.print(f"[red]✗[/red] Error: {e}", style="red")
        raise click.Abort()
```

#### Step 5: Verify Integration

**Test the CLI**:

```bash
# Check status
codeindex hooks status
# Output:
#   ○ pre-commit: not installed
#   ○ post-commit: not installed
#   ○ pre-push: not installed

# Install all hooks
codeindex hooks install --all
# Output:
#   ✓ pre-commit: installed
#   ✓ post-commit: installed
#   ✓ pre-push: installed
#   ✓ Successfully installed 3 hook(s)

# Check status again
codeindex hooks status
# Output:
#   ✓ pre-commit: installed
#   ✓ post-commit: installed
#   ✓ pre-push: installed
#   → 3 codeindex hook(s) installed
```

---

### Testing Strategy

**Required Tests (Minimum 15 tests)**:

1. **HookManager Tests** (10 tests):
   - `test_init_with_repo_path` - Initialize with path
   - `test_init_detects_git_repo` - Auto-detect repo
   - `test_get_hook_status_not_exists` - Hook doesn't exist
   - `test_get_hook_status_exists_codeindex` - Codeindex hook exists
   - `test_get_hook_status_exists_custom` - Custom hook exists
   - `test_install_hook` - Install new hook
   - `test_install_hook_with_backup` - Backup existing hook
   - `test_uninstall_hook` - Uninstall hook
   - `test_uninstall_hook_restores_backup` - Restore backup
   - `test_list_all_hooks_status` - List all hooks

2. **Hook Generation Tests** (3 tests):
   - `test_generate_pre_commit_hook` - Generate pre-commit
   - `test_generate_post_commit_hook` - Generate post-commit
   - `test_generate_hook_with_config` - Customize with config

3. **Backup & Restore Tests** (2 tests):
   - `test_backup_existing_hook` - Create backup
   - `test_backup_with_existing_backup` - Handle existing backup

4. **Detection Tests** (2 tests):
   - `test_detect_existing_hooks` - Detect all hooks
   - `test_detect_ignores_samples` - Ignore .sample files

**Test Example** (`tests/test_cli_hooks.py`):

```python
def test_install_hook_with_backup(self, tmp_path):
    """Should backup existing custom hook before installing."""
    repo_path = tmp_path / "test_repo"
    hooks_dir = repo_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)

    # Create existing custom hook
    hook_file = hooks_dir / "pre-commit"
    hook_file.write_text("#!/bin/bash\necho 'old hook'")

    manager = HookManager(repo_path)
    result = manager.install_hook("pre-commit", backup=True)

    assert result is True
    assert (hooks_dir / "pre-commit.backup").exists()
    assert (hooks_dir / "pre-commit").exists()
```

---

### Key Implementation Patterns

#### Pattern 1: Marker-Based Detection

Use a unique marker to identify managed hooks:

```python
CODEINDEX_MARKER = "# codeindex-managed hook"

def get_hook_status(self, hook_name: str) -> HookStatus:
    hook_file = self.hooks_dir / hook_name
    if not hook_file.exists():
        return HookStatus.NOT_INSTALLED

    content = hook_file.read_text()
    if self.CODEINDEX_MARKER in content:
        return HookStatus.INSTALLED  # ← Our hook

    return HookStatus.CUSTOM  # ← User's custom hook
```

**Why?** Allows distinguishing our hooks from user's custom hooks.

#### Pattern 2: Automatic Backup

Always backup before overwriting:

```python
def backup_existing_hook(hook_file: Path) -> Path:
    """Create timestamped backup of existing hook."""
    backup_path = hook_file.with_suffix(".backup")

    # If backup exists, add timestamp
    if backup_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = hook_file.parent / f"{hook_file.name}.backup.{timestamp}"

    shutil.copy2(hook_file, backup_path)
    return backup_path
```

**Why?** User's custom hooks are precious, never lose them.

#### Pattern 3: Template-Based Generation

Generate scripts from templates, not hardcoded:

```python
def generate_hook_script(hook_name: str, config: dict = None) -> str:
    if hook_name == "pre-commit":
        return _generate_pre_commit_script(config)
    elif hook_name == "post-commit":
        return _generate_post_commit_script(config)
    # ...
```

**Why?** Easy to customize, test, and maintain.

#### Pattern 4: Shell Script Best Practices

**Set error handling**:
```bash
set -e  # Exit on error
```

**Use colors**:
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'  # No Color
echo "${GREEN}✓ Success${NC}"
```

**Activate venv if exists**:
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
if [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    source "$REPO_ROOT/.venv/bin/activate"
fi
```

---

### Common Pitfalls

**❌ Problem 1: Hook not executable**

Hooks must be executable (+x permission):

```python
# ✅ Correct
hook_file.write_text(script)
hook_file.chmod(0o755)  # ← Make executable
```

**❌ Problem 2: Infinite loop (post-commit)**

Post-commit hook can trigger itself:

```bash
# ✅ Prevent loop
LAST_COMMIT_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD)
NON_DOC_FILES=$(echo "$LAST_COMMIT_FILES" | \
    grep -v "README_AI.md" | grep -v "PROJECT_INDEX.md" || true)
if [ -z "$NON_DOC_FILES" ]; then
    exit 0  # Only doc files changed, skip
fi
```

**❌ Problem 3: Detecting staged vs working files**

Only check staged content, not working directory:

```bash
# ✅ Get staged content only
STAGED_CONTENT=$(git show ":$file" 2>/dev/null || true)
```

**❌ Problem 4: Long lines in shell scripts**

Ruff checks Python files for line length, but shell scripts too:

```bash
# ❌ Too long (>100 chars)
LEVEL=$(echo "$ANALYSIS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('level', 'skip'))")

# ✅ Split with line continuation
LEVEL=$(echo "$ANALYSIS" | python3 -c \
    "import sys, json; print(json.load(sys.stdin).get('level', 'skip'))" \
    2>/dev/null || echo "skip")
```

---

### Q&A

**Q: Why use shell scripts instead of Python?**
A: Git hooks must be shell scripts (no .py extension). Shell scripts are standard.

**Q: How to test shell scripts?**
A: Test the Python code that generates them. Don't test shell syntax.

**Q: Can users customize hooks?**
A: Future: support `.codeindex.yaml` configuration. Current: edit `.git/hooks/pre-commit` manually.

**Q: What if user has existing hooks?**
A: We detect them (`HookStatus.CUSTOM`) and create automatic backups.

**Q: How to handle multiple hooks managers?**
A: Our marker (`# codeindex-managed hook`) ensures we only manage our own hooks. Other tools use their own markers.

**Q: Post-commit creates extra commits. Is this okay?**
A: Yes! Git supports this pattern. We prevent infinite loops by checking file types.

---

## 🛠️ 开发工作流

### TDD 开发流程（必须遵守）

本项目严格遵循 TDD（测试驱动开发）：

1. **Red（写失败的测试）**
   ```bash
   # 先写测试用例
   pytest tests/test_new_feature.py -v
   # 预期结果：测试失败 ❌
   ```

2. **Green（实现最小代码使测试通过）**
   ```bash
   # 实现功能
   pytest tests/test_new_feature.py -v
   # 预期结果：测试通过 ✅
   ```

3. **Refactor（重构优化）**
   ```bash
   # 优化代码，确保测试仍然通过
   pytest  # 运行所有测试
   ruff check src/  # 代码规范检查
   ```

### GitFlow 分支策略

```
master (生产分支，v0.3.1)
├── develop (开发分支)
│   ├── feature/epic3-xxx (功能分支)
│   ├── feature/epic4-xxx (功能分支)
│   └── hotfix/xxx (紧急修复)
```

**分支使用规则：**
- `master`: 只接受来自 develop 的合并，每次合并打 tag
- `develop`: 主开发分支，功能分支合并到这里
- `feature/*`: Epic/Story 功能开发分支
- `hotfix/*`: 紧急修复分支，可直接合并到 master

**提交信息格式：**
```
feat(scope): 添加新功能
fix(scope): 修复bug
docs(scope): 文档更新
test(scope): 测试相关
refactor(scope): 重构代码
```

### 代码质量检查清单

在提交代码前必须通过：

```bash
# ✅ 1. 运行所有测试
pytest -v
# 要求：所有测试通过

# ✅ 2. 代码规范检查
ruff check src/
# 要求：无错误

# ✅ 3. 类型检查（如果使用）
mypy src/
# 要求：无类型错误

# ✅ 4. 测试覆盖率（可选）
pytest --cov=src/codeindex --cov-report=term-missing
# 推荐：核心模块 ≥ 90%，整体 ≥ 80%
```

## 📚 文档更新规则

### 何时需要更新文档

| 变更类型 | 需要更新的文档 |
|---------|---------------|
| 新增功能 | CHANGELOG.md, README.md, 相关 README_AI.md |
| Bug修复 | CHANGELOG.md |
| 配置变更 | .codeindex.yaml 示例, docs/guides/configuration.md |
| API变更 | README.md, 相关模块的 docstring |
| 重大版本 | CHANGELOG.md, RELEASE_NOTES_vX.X.X.md |
| 架构决策 | docs/architecture/adr-xxx.md |

### 自动生成 README_AI.md

**重要：修改代码后需要重新生成索引**

```bash
# 重新生成所有 README_AI.md
codeindex scan-all --fallback

# 或只生成特定目录
codeindex scan src/codeindex --fallback
codeindex scan tests --fallback
```

## 📈 版本历史和功能演进

### v0.3.1 - CLI Module Split (2026-01-28)
- **Epic 4 Story 4.3**: CLI 架构重构
- CLI 从 1062 行拆分为 6 个专注模块（-97%）
- 每个模块单一职责：scan, config, symbols, tech-debt
- 零破坏性变更，所有 263 测试通过
- 嵌套函数重构为独立辅助函数

### v0.3.0 - AI Enhancement & Tech Debt (2026-01-27)
- **Epic 4 Stories 4.1-4.2**: 代码重构和质量改进
- AI Helper 模块：复用增强功能
- File Size Classifier：统一文件大小检测
- **Epic 3.2**: 超大文件多轮对话（>5000行或>100符号）
  - 三轮对话：架构概览 → 核心组件 → 最终合成
  - 自动检测和策略选择
- **Epic 3.1**: 技术债务分析
  - 复杂度指标（cyclomatic, cognitive, nesting）
  - God Class 检测（>50 methods）
  - 多格式输出（console/markdown/json）
- 消除 ~110 行代码重复

### v0.2.0 - Adaptive Symbols (2025-01-15)
- **Epic 2**: 自适应符号提取
- 7级文件大小分类（tiny→mega）
- 动态符号限制：5-150 个/文件（基于文件大小）
- 大文件信息覆盖率提升 280%（26% → 100%）
- YAML 配置支持
- 零破坏性变更（默认禁用）

### v0.1.3 - Project Indexing (2025-01-15)
- PROJECT_INDEX.json 和 PROJECT_INDEX.md
- 代码库导航索引
- 改进 README_AI.md 自动生成

### v0.1.2 - Parallel & Incremental (2025-01-14)
- 并行扫描支持（codeindex list-dirs）
- --dry-run 预览 prompt
- status 命令查看索引覆盖率
- 增量更新分析

### v0.1.0 - Initial Release (2025-01-12)
- Python 代码解析（tree-sitter）
- 外部 AI CLI 集成
- 符号提取（classes, functions, imports）
- README_AI.md 生成
- 基础测试套件

## 🚨 常见错误和避免方法

### ❌ 错误做法

1. **直接修改生成的 README_AI.md**
   - README_AI.md 是自动生成的，会被覆盖
   - 正确做法：修改源码的 docstring，然后重新生成

2. **跳过测试直接写实现**
   - 违反 TDD 原则
   - 正确做法：先写测试，再写实现

3. **使用 Glob/Grep 搜索代码**
   - 不精确，无法理解符号关系
   - 正确做法：使用 Serena MCP 的 find_symbol 和 find_referencing_symbols

4. **不看 README_AI.md 就修改代码**
   - 可能不理解模块的设计意图
   - 正确做法：先读 README_AI.md，理解架构再修改

5. **直接提交到 develop 或 master**
   - 违反 GitFlow 规范
   - 正确做法：创建 feature 分支，完成后合并

### ✅ 最佳实践

1. **理解代码流程**
   ```
   README_AI.md → find_symbol → 读源码 → 写测试 → 实现
   ```

2. **修改功能流程**
   ```
   创建 feature 分支 → TDD开发 → 测试通过 → ruff检查 →
   更新 CHANGELOG → 提交 → 合并到 develop
   ```

3. **发布版本流程**
   ```
   develop 合并到 master → 运行所有测试 → 创建 tag →
   生成 RELEASE_NOTES → 推送到 GitHub
   ```