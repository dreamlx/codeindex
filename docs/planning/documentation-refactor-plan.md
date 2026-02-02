# Documentation Refactor Plan - Epic 6 功能说明

**Date**: 2026-02-02
**Purpose**: 让用户和 AI 都能理解和使用 Route Extraction 功能
**Target Files**: README.md, CLAUDE.md

---

## 🎯 Problem Statement

**现状问题**：
1. ✅ Epic 6 功能已完成（路由提取 + 行号 + 描述）
2. ❌ README.md **未提及**路由提取功能
3. ❌ CLAUDE.md **未说明**如何扩展框架支持
4. ❌ AI Code **不知道**如何使用此功能

**影响**：
- 用户不知道有这个"杀手级"功能
- AI 无法帮助用户扩展新框架
- 开发者不知道如何贡献新的 extractor

---

## 📝 Refactor Strategy

### 1. README.md - 用户文档

**目标受众**: 终端用户、开发者

**新增章节**：

#### 1.1 Features 部分添加

```markdown
## ✨ Features

- 🚀 **AI-Powered Documentation**: ...
- 🌳 **Tree-sitter Parsing**: ...
+ 🎯 **Framework Route Extraction** (v0.5.0+): Auto-detect and extract routes from web frameworks
+   - **ThinkPHP**: Convention-based routing with line numbers and descriptions
+   - **Laravel**: (Coming soon) Explicit route definitions
+   - **FastAPI**: (Coming soon) Decorator-based routes
+   - **Django**: (Coming soon) URL patterns
```

#### 1.2 新增专门章节

```markdown
## 🛣️ Framework Route Extraction (v0.5.0+)

codeindex automatically detects and extracts routes from supported web frameworks,
generating beautiful route tables in your `README_AI.md` files.

### Supported Frameworks

| Framework | Language | Status | Features |
|-----------|----------|--------|----------|
| ThinkPHP  | PHP      | ✅ Stable | Line numbers, descriptions, module-based routing |
| Laravel   | PHP      | 🔄 Coming | Named routes, route groups, middleware |
| FastAPI   | Python   | 🔄 Coming | Path operations, dependencies, tags |
| Django    | Python   | 🔄 Coming | URL patterns, namespaces |

### Example Output

**ThinkPHP Controller** (`Application/Admin/Controller/UserController.php`):

```php
class UserController {
    /**
     * Get user list
     */
    public function index() {
        // ...
    }
}
```

**Generated Route Table**:

| URL | Controller | Action | Location | Description |
|-----|------------|--------|----------|-------------|
| `/admin/user/index` | UserController | index | `UserController.php:20` | Get user list |

### How It Works

1. **Auto-Detection**: Scans directory structure to detect framework
2. **Symbol Extraction**: Parses controllers/views using tree-sitter
3. **Route Inference**: Applies framework-specific routing conventions
4. **Documentation**: Extracts docstrings/PHPDoc comments
5. **Table Generation**: Formats as markdown table in README_AI.md

### Configuration

No configuration needed! Just run:

```bash
codeindex scan-all
```

Routes are automatically detected when scanning Controller directories.

### Adding Custom Frameworks

See [CLAUDE.md](CLAUDE.md#framework-route-extraction) for developer guide.
```

#### 1.3 更新 Quick Start

```markdown
## 🚀 Quick Start

### 3. Scan Your Project

```bash
# Scan all directories (auto-detects routes)
codeindex scan-all

# Scan specific directory
codeindex scan ./Application/Admin/Controller
```

**For ThinkPHP projects**, codeindex will automatically:
- ✅ Detect Controller directories
- ✅ Extract routes with line numbers
- ✅ Include method descriptions from PHPDoc
- ✅ Generate route tables in README_AI.md
```

---

### 2. CLAUDE.md - AI Developer Guide

**目标受众**: Claude Code (AI Agent)、贡献者

**新增章节**：

#### 2.1 在 "Architecture" 部分后添加

```markdown
## 🛣️ Framework Route Extraction (v0.5.0+)

### Architecture Overview

codeindex uses a **plugin-based architecture** for framework route extraction:

```
RouteExtractor (Abstract Base Class)
    ├── ThinkPHPRouteExtractor
    ├── LaravelRouteExtractor (TODO)
    └── FastAPIRouteExtractor (TODO)

RouteExtractorRegistry
    └── Auto-registers all extractors
```

**Key Components**:

- **`src/codeindex/route_extractor.py`**: Abstract base class and data structures
- **`src/codeindex/route_registry.py`**: Extractor registration and discovery
- **`src/codeindex/extractors/`**: Framework-specific implementations

### How to Add a New Framework Extractor

Follow this TDD process:

#### Step 1: Create Test File

**File**: `tests/extractors/test_myframework.py`

```python
from pathlib import Path
from codeindex.extractors.myframework import MyFrameworkRouteExtractor
from codeindex.parser import ParseResult, Symbol
from codeindex.route_extractor import ExtractionContext

class TestMyFrameworkRouteExtractor:
    """Test MyFramework route extractor."""

    def test_extract_routes_from_controller(self):
        """Should extract routes from MyFramework controller."""
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
        assert routes[0].action == "index"
        assert routes[0].line_number == 10
        assert routes[0].description == "Get user list"
```

#### Step 2: Create Extractor Implementation

**File**: `src/codeindex/extractors/myframework.py`

```python
"""MyFramework route extractor."""

from ..framework_detect import RouteInfo
from ..route_extractor import ExtractionContext, RouteExtractor


class MyFrameworkRouteExtractor(RouteExtractor):
    """Route extractor for MyFramework."""

    @property
    def framework_name(self) -> str:
        """Return framework name."""
        return "myframework"

    def can_extract(self, context: ExtractionContext) -> bool:
        """Check if routes should be extracted from this directory."""
        # Example: Only extract from 'controllers' directory
        return context.current_dir.name == "controllers"

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """Extract routes from MyFramework controllers."""
        routes = []

        for result in context.parse_results:
            if result.error:
                continue

            # Your framework-specific logic here
            # Extract controller class, methods, build URLs, etc.

            for symbol in result.symbols:
                if symbol.kind == "method":
                    routes.append(
                        RouteInfo(
                            url=self._build_url(symbol),
                            controller=self._get_controller_name(symbol),
                            action=symbol.name,
                            method_signature=symbol.signature,
                            line_number=symbol.line_start,
                            file_path=result.path.name,
                            description=self._extract_description(symbol),
                        )
                    )

        return routes

    def _extract_description(self, symbol) -> str:
        """Extract description from docstring."""
        if not symbol.docstring:
            return ""

        # Limit to 60 chars for table display
        description = symbol.docstring.strip()
        if len(description) > 60:
            return description[:60] + "..."

        return description
```

#### Step 3: Register Extractor

**File**: `src/codeindex/extractors/__init__.py`

```python
from .myframework import MyFrameworkRouteExtractor
from .thinkphp import ThinkPHPRouteExtractor

__all__ = [
    "MyFrameworkRouteExtractor",
    "ThinkPHPRouteExtractor",
]
```

#### Step 4: Run Tests

```bash
# TDD: RED
pytest tests/extractors/test_myframework.py -v
# Should fail initially

# TDD: GREEN
# Implement the extractor
pytest tests/extractors/test_myframework.py -v
# Should pass

# TDD: REFACTOR
ruff check src/codeindex/extractors/myframework.py
pytest  # All tests should still pass
```

#### Step 5: Integration

The extractor is **automatically registered** via `RouteExtractorRegistry`.
No manual registration needed!

```python
# SmartWriter will automatically discover and use it
writer = SmartWriter(config)
# Routes will appear in README_AI.md
```

### Testing Guidelines

**Required Test Coverage**:

1. ✅ Basic route extraction
2. ✅ Line number extraction
3. ✅ Description extraction
4. ✅ Multiple routes from one file
5. ✅ Empty/no routes case
6. ✅ Error handling (malformed files)
7. ✅ can_extract() logic

**Example Test Structure**:

```python
class TestMyFrameworkRouteExtractor:
    def test_can_extract_from_controllers_directory(self):
        """Should extract only from controllers directory."""
        # ...

    def test_extract_routes_with_line_numbers(self):
        """Should include line numbers in routes."""
        # ...

    def test_extract_description_from_docstring(self):
        """Should extract description from method docstring."""
        # ...

    def test_truncate_long_descriptions(self):
        """Should truncate descriptions > 60 chars."""
        # ...

    def test_handle_empty_file(self):
        """Should return empty list for files with no routes."""
        # ...
```

### Existing Extractors Reference

**ThinkPHP Extractor**: `src/codeindex/extractors/thinkphp.py`
- Convention-based routing: `/module/controller/action`
- Detects from `Application/{Module}/Controller/` structure
- Filters public methods, excludes magic/internal methods
- See tests: `tests/extractors/test_thinkphp.py`

### Route Display Format

Routes are displayed in README_AI.md as markdown tables:

```markdown
## Routes (MyFramework)

| URL | Controller | Action | Location | Description |
|-----|------------|--------|----------|-------------|
| `/users` | UserController | index | `UserController.py:10` | Get user list |
| `/users/create` | UserController | create | `UserController.py:20` | Create new user |
```

**Table Columns**:
- **URL**: Route path
- **Controller**: Controller class name
- **Action**: Method/action name
- **Location**: `file:line` clickable location
- **Description**: From docstring (max 60 chars)

### Framework Detection

Update `src/codeindex/framework_detect.py` if needed:

```python
def detect_framework(path: Path) -> str | None:
    """Detect web framework from directory structure."""
    # Add your framework detection logic
    if (path / "myframework.conf").exists():
        return "myframework"

    # ... existing detection ...
```

### Important Notes

1. **No Manual Registration**: Extractors are auto-discovered via `__init__.py`
2. **TDD Required**: All new extractors must have tests first
3. **Description Limit**: Always truncate to 60 chars for table display
4. **Error Handling**: Always check `result.error` before processing
5. **Performance**: Keep extraction logic fast (it runs on every scan)

### Need Help?

- See examples: `src/codeindex/extractors/thinkphp.py`
- Read tests: `tests/extractors/test_thinkphp.py`
- Check base class: `src/codeindex/route_extractor.py`
```

#### 2.2 更新已有的 "Architecture" 说明

在现有的 Architecture 部分添加：

```markdown
## Architecture

### Core Pipeline

1. **Scanner** → 2. **Parser** → 3. **Writer** → 4. **Invoker** → 5. **README_AI.md**

+ **Route Extraction** (v0.5.0+):
+   - Integrated into Writer step
+   - Auto-detects framework from directory structure
+   - Extracts routes using framework-specific extractors
+   - Generates route tables in README_AI.md
```

---

## 📋 Implementation Checklist

### Phase 1: README.md 更新（面向用户）

- [ ] 在 Features 添加 Route Extraction 说明
- [ ] 新增 "Framework Route Extraction" 专门章节
  - [ ] 支持框架列表
  - [ ] 示例输出
  - [ ] 工作原理
  - [ ] 配置说明
- [ ] 更新 Quick Start 提到路由自动检测
- [ ] 添加截图或示例（可选）

### Phase 2: CLAUDE.md 更新（面向 AI）

- [ ] 新增 "Framework Route Extraction" 章节
- [ ] 架构概览图
- [ ] 完整的"如何添加新框架"教程
  - [ ] Step-by-step TDD 流程
  - [ ] 示例代码
  - [ ] 测试指南
- [ ] 已有提取器参考
- [ ] 路由显示格式说明
- [ ] 常见问题和注意事项

### Phase 3: 示例和模板

- [ ] 创建 `examples/frameworks/` 目录
  - [ ] `examples/frameworks/thinkphp/` - ThinkPHP 示例
  - [ ] `examples/frameworks/template/` - 新框架模板
- [ ] 示例项目结构
- [ ] 示例路由输出

### Phase 4: 其他文档

- [ ] 更新 CHANGELOG.md 记录 v0.5.0 功能
- [ ] 创建 `docs/guides/adding-framework-extractor.md` 详细教程
- [ ] 更新 API 文档（如果有）

---

## 🎯 AI Visibility Strategy

**问题**: 如何让 AI Code 知道这个功能？

**解决方案**:

### 1. CLAUDE.md 是关键

Claude Code **会主动读取** CLAUDE.md，所以：
- ✅ 在 CLAUDE.md 中详细说明架构
- ✅ 提供完整的 TDD 示例
- ✅ 明确说明"如何添加新框架"

### 2. 文件组织清晰

```
src/codeindex/extractors/
├── __init__.py          # ← AI 会看这里找所有 extractors
├── thinkphp.py          # ← 参考实现
├── laravel.py           # ← TODO (AI 可以看到缺失)
└── fastapi.py           # ← TODO
```

### 3. 代码中的文档字符串

```python
class RouteExtractor(ABC):
    """
    Abstract base class for framework route extractors.

    To add a new framework:
    1. Create a new file in src/codeindex/extractors/
    2. Subclass RouteExtractor
    3. Implement framework_name, can_extract, extract_routes
    4. Write tests in tests/extractors/
    5. Export from __init__.py

    Example:
        See src/codeindex/extractors/thinkphp.py
    """
```

### 4. README_AI.md 自动生成

当 AI 扫描 `src/codeindex/extractors/` 时，会自动生成包含架构说明的 README_AI.md

### 5. 测试文件作为示例

AI 可以通过阅读 `tests/extractors/test_thinkphp.py` 理解如何编写新的提取器测试。

---

## 💡 Best Practices for AI-Friendly Documentation

### DO ✅

1. **在 CLAUDE.md 中提供完整代码示例**（不要只说"参考 xxx"）
2. **使用 Step-by-Step 教程**（AI 擅长跟随步骤）
3. **TDD 流程明确**（AI 会严格遵循 TDD）
4. **代码中的 docstring 要详细**（AI 会读源码）
5. **文件结构要清晰**（AI 通过文件名理解用途）

### DON'T ❌

1. ❌ 只在 README 说明（AI 可能优先看 CLAUDE.md）
2. ❌ 使用模糊的说明（"类似于 xxx"）
3. ❌ 缺少代码示例（AI 需要具体代码）
4. ❌ 隐藏在多层链接中（AI 不会深度跳转）
5. ❌ 假设 AI 知道框架（要明确说明框架特性）

---

## 📅 Implementation Timeline

**建议**: 今天（Day 5）下午完成

**时间估计**:
- README.md 更新: 30-45 分钟
- CLAUDE.md 更新: 45-60 分钟
- 示例创建: 15-30 分钟
- 测试验证: 15 分钟

**总计**: ~2 小时

**Deliverable**: 完整的文档更新，为 Week 2 和未来贡献者做好准备

---

## 🎓 Success Criteria

文档更新成功的标志：

1. ✅ 用户能在 README.md 中**快速找到**路由提取功能
2. ✅ AI Code 能通过 CLAUDE.md **自主实现**新框架提取器
3. ✅ 贡献者能通过文档**独立完成** Laravel/FastAPI 提取器
4. ✅ 示例代码**可以直接运行**（复制粘贴即可）
5. ✅ 文档保持**同步更新**（代码变化 → 文档更新）

---

**Created**: 2026-02-02
**Author**: Claude Sonnet 4.5
**Status**: 📝 Proposal - Waiting for Approval
