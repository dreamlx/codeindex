# Epic 6: Framework-Agnostic Route Extraction

**Date**: 2026-02-02
**Version**: v0.5.0 Planning
**Priority**: High (用户反馈：ThinkPHP 路由表是杀手级功能)

---

## 🎯 目标

将当前硬编码的 ThinkPHP 路由提取，通用化为支持所有主流框架的可扩展架构。

### 用户价值

从用户反馈来看：
> "ThinkPHP 路由表 - 杀手级功能 ⭐⭐⭐⭐⭐"
> "知道 /bigwheel/small/ImmediateLotteryDraw 是入口，直接定位到方法"

**效率提升**: 无索引 10 分钟 → 有索引 即时（20x 提效）

---

## 📐 架构设计

### 核心原则

1. **框架无关** - 支持 Python/PHP/Java/Node.js/Go 的主流框架
2. **可插拔** - 每个框架一个提取器，易于扩展
3. **零配置** - 自动检测框架，无需用户配置（可选手动指定）
4. **统一接口** - 所有框架返回统一的 RouteInfo 数据结构

### 当前实现（v0.4.0）

```python
# 硬编码方式
if dir_path.name == "Controller":  # ThinkPHP specific
    routes = extract_thinkphp_routes(parse_results, module_name)
```

**问题**:
- ❌ 只支持 ThinkPHP
- ❌ 框架检测逻辑分散
- ❌ 添加新框架需要修改多处代码

### 目标架构（v0.5.0）

```python
# 可扩展架构
framework = detect_framework(root_path)
extractor = RouteExtractorRegistry.get(framework)
routes = extractor.extract(parse_results, context)
```

**优势**:
- ✅ 支持 10+ 主流框架
- ✅ 添加新框架只需实现一个类
- ✅ 框架检测集中管理

---

## 🏗️ 核心组件

### 1. RouteExtractor 抽象基类

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

@dataclass
class RouteInfo:
    """统一的路由信息（通用）"""
    url: str                    # /api/users/123
    handler: str                # UserController.getUser
    method: str = "GET"         # HTTP method (if applicable)
    file_path: str = ""         # src/controllers/user.py:42
    line_number: int = 0        # 方法行号（新增，解决 P1）
    description: str = ""       # 方法注释（新增，解决 P2）

@dataclass
class ExtractionContext:
    """提取上下文"""
    root_path: Path             # 项目根目录
    current_dir: Path           # 当前目录
    parse_results: list[ParseResult]
    framework_version: str = ""

class RouteExtractor(ABC):
    """路由提取器抽象基类"""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """框架名称"""
        pass

    @abstractmethod
    def can_extract(self, context: ExtractionContext) -> bool:
        """判断当前上下文是否适用于此框架"""
        pass

    @abstractmethod
    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """提取路由信息"""
        pass
```

### 2. Framework 检测器（增强）

```python
class FrameworkDetector:
    """统一的框架检测器"""

    # 检测规则（可扩展）
    DETECTION_RULES = {
        # PHP 框架
        "thinkphp": {
            "files": ["Application/*/Controller"],
            "composer": ["topthink/framework", "topthink/think"],
        },
        "laravel": {
            "files": ["artisan", "app/Http/Controllers"],
            "composer": ["laravel/framework"],
        },

        # Python 框架
        "django": {
            "files": ["manage.py", "*/urls.py"],
            "imports": ["django.urls"],
        },
        "fastapi": {
            "files": ["*/main.py"],
            "imports": ["fastapi"],
        },

        # Node.js 框架
        "express": {
            "files": ["package.json"],
            "npm": ["express"],
        },

        # Java 框架
        "spring": {
            "files": ["pom.xml", "src/main/java"],
            "maven": ["spring-boot-starter-web"],
        },
    }

    def detect(self, root: Path) -> str:
        """检测框架类型"""
        for framework, rules in self.DETECTION_RULES.items():
            if self._matches_rules(root, rules):
                return framework
        return "unknown"
```

### 3. 具体实现示例

#### ThinkPHP Extractor

```python
class ThinkPHPRouteExtractor(RouteExtractor):
    """ThinkPHP 路由提取器"""

    @property
    def framework_name(self) -> str:
        return "thinkphp"

    def can_extract(self, context: ExtractionContext) -> bool:
        # 只在 Controller 目录才提取
        return context.current_dir.name == "Controller"

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        routes = []
        module_name = context.current_dir.parent.name  # Admin/Agent

        for result in context.parse_results:
            for symbol in result.symbols:
                if symbol.kind != "class" or not symbol.name.endswith("Controller"):
                    continue

                controller_name = symbol.name.replace("Controller", "")

                # 提取所有 public 方法
                for method in symbol.methods:  # 假设有子符号
                    if not method.signature.startswith("public"):
                        continue

                    routes.append(RouteInfo(
                        url=f"/{module_name.lower()}/{controller_name.lower()}/{method.name}",
                        handler=f"{symbol.name}.{method.name}",
                        method="ANY",  # ThinkPHP 不区分 HTTP 方法
                        file_path=f"{result.path.name}:{method.line_start}",  # P1: 行号
                        line_number=method.line_start,
                        description=self._extract_description(method),  # P2: 注释
                    ))

        return routes

    def _extract_description(self, symbol: Symbol) -> str:
        """提取方法描述（从 docstring 或注释）"""
        if symbol.docstring:
            # 提取第一行注释（PHPDoc 格式）
            lines = symbol.docstring.strip().split('\n')
            for line in lines:
                line = line.strip().lstrip('*').strip()
                if line and not line.startswith('@'):
                    return line
        return ""
```

#### Laravel Extractor

```python
class LaravelRouteExtractor(RouteExtractor):
    """Laravel 路由提取器"""

    @property
    def framework_name(self) -> str:
        return "laravel"

    def can_extract(self, context: ExtractionContext) -> bool:
        # 在 routes/ 目录或 Controller 目录提取
        return context.current_dir.name in ("routes", "Controllers")

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        routes = []

        if context.current_dir.name == "routes":
            # 从 routes/web.php, routes/api.php 提取
            routes.extend(self._extract_from_route_files(context))
        else:
            # 从 Controller 提取（基于注解）
            routes.extend(self._extract_from_controllers(context))

        return routes

    def _extract_from_route_files(self, context: ExtractionContext) -> list[RouteInfo]:
        """解析 routes/web.php 中的路由定义"""
        # Route::get('/users', [UserController::class, 'index']);
        # 需要简单的 PHP 代码解析
        pass
```

#### Django Extractor

```python
class DjangoRouteExtractor(RouteExtractor):
    """Django 路由提取器"""

    @property
    def framework_name(self) -> str:
        return "django"

    def can_extract(self, context: ExtractionContext) -> bool:
        # urls.py 文件
        return any(result.path.name == "urls.py" for result in context.parse_results)

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        """解析 urlpatterns"""
        # urlpatterns = [
        #     path('users/', UserListView.as_view()),
        # ]
        pass
```

#### FastAPI Extractor

```python
class FastAPIRouteExtractor(RouteExtractor):
    """FastAPI 路由提取器"""

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        routes = []

        for result in context.parse_results:
            for symbol in result.symbols:
                # 查找装饰器：@app.get("/users/{id}")
                if symbol.kind == "function":
                    decorators = self._extract_decorators(symbol)
                    for decorator in decorators:
                        if decorator.startswith("app."):
                            method, url = self._parse_decorator(decorator)
                            routes.append(RouteInfo(
                                url=url,
                                handler=f"{symbol.name}",
                                method=method.upper(),
                                file_path=f"{result.path.name}:{symbol.line_start}",
                                line_number=symbol.line_start,
                                description=symbol.docstring.split('\n')[0] if symbol.docstring else "",
                            ))

        return routes
```

### 4. 注册表和自动发现

```python
class RouteExtractorRegistry:
    """路由提取器注册表"""

    _extractors: dict[str, RouteExtractor] = {}

    @classmethod
    def register(cls, extractor: RouteExtractor):
        """注册提取器"""
        cls._extractors[extractor.framework_name] = extractor

    @classmethod
    def get(cls, framework: str) -> RouteExtractor | None:
        """获取提取器"""
        return cls._extractors.get(framework)

    @classmethod
    def auto_register(cls):
        """自动注册所有提取器"""
        cls.register(ThinkPHPRouteExtractor())
        cls.register(LaravelRouteExtractor())
        cls.register(DjangoRouteExtractor())
        cls.register(FastAPIRouteExtractor())
        cls.register(SpringBootRouteExtractor())
        cls.register(ExpressRouteExtractor())

# 初始化时自动注册
RouteExtractorRegistry.auto_register()
```

### 5. 统一调用接口

```python
# smart_writer.py 中的使用
def _generate_route_table(self, context: ExtractionContext) -> list[str]:
    """生成路由表（框架无关）"""

    # 1. 检测框架
    framework = detect_framework(context.root_path)

    # 2. 获取对应提取器
    extractor = RouteExtractorRegistry.get(framework)
    if not extractor:
        return []  # 不支持的框架，跳过

    # 3. 判断是否应该提取
    if not extractor.can_extract(context):
        return []

    # 4. 提取路由
    routes = extractor.extract_routes(context)
    if not routes:
        return []

    # 5. 格式化输出（统一格式）
    lines = [
        f"## Routes ({framework.title()})",
        "",
        "| URL | Handler | Method | Location | Description |",
        "|-----|---------|--------|----------|-------------|",
    ]

    for route in routes[:50]:  # 限制显示数量
        lines.append(
            f"| `{route.url}` | {route.handler} | {route.method} | "
            f"`{route.file_path}` | {route.description} |"
        )

    if len(routes) > 50:
        lines.append(f"| ... | _{len(routes) - 50} more routes_ | | | |")

    return lines
```

---

## 📊 支持的框架矩阵

### Phase 1 (v0.5.0) - Core Frameworks

| 框架 | 语言 | 提取难度 | 优先级 | 状态 |
|------|------|---------|--------|------|
| ThinkPHP | PHP | 低（已实现） | P0 | ✅ Done |
| Laravel | PHP | 中 | P1 | 🔄 Planned |
| Django | Python | 中 | P1 | 🔄 Planned |
| FastAPI | Python | 低 | P1 | 🔄 Planned |

### Phase 2 (v0.6.0) - Extended Support

| 框架 | 语言 | 提取难度 | 优先级 | 状态 |
|------|------|---------|--------|------|
| Spring Boot | Java | 中 | P2 | 📝 Future |
| Express | Node.js | 中 | P2 | 📝 Future |
| Flask | Python | 低 | P2 | 📝 Future |
| Gin | Go | 低 | P3 | 📝 Future |
| Symfony | PHP | 高 | P3 | 📝 Future |

---

## 🎯 解决 P1: 方法行号

### 当前问题

```markdown
- `public function ImmediateLotteryDraw($info)`
  ↓ 还需要 grep 找行号
grep -n "ImmediateLotteryDraw" SmallController.php
```

### 解决方案

```python
# RouteInfo 增加 line_number 字段
@dataclass
class RouteInfo:
    url: str
    handler: str
    method: str = "GET"
    line_number: int = 0  # ← 新增
    file_path: str = ""

# 提取时直接使用 symbol.line_start
routes.append(RouteInfo(
    url=f"/{module_name.lower()}/{controller_name}/{method.name}",
    handler=f"{symbol.name}.{method.name}",
    line_number=symbol.line_start,  # ← Parser 已经有了
    file_path=f"{result.path.name}:{symbol.line_start}",
))

# 显示时包含行号
| URL | Handler | Location |
|-----|---------|----------|
| `/bigwheel/small/ImmediateLotteryDraw` | SmallController.ImmediateLotteryDraw | `SmallController.php:1691` |
```

**收益**: 直接 `vim SmallController.php +1691` 跳转，省去 grep 步骤。

---

## 🎯 解决 P2: 提取注释/PHPDoc

### 分层方案

#### Layer 1: 直接提取（无需 AI，立即实现）

```python
def _extract_description(self, symbol: Symbol) -> str:
    """
    提取方法描述（从 docstring）

    支持：
    - Python: """docstring"""
    - PHP: /** PHPDoc */
    - Java: /** JavaDoc */
    - TypeScript: /** JSDoc */
    """
    if not symbol.docstring:
        return ""

    # 提取第一行有效注释
    lines = symbol.docstring.strip().split('\n')
    for line in lines:
        # 清理格式标记（*, //, #）
        cleaned = line.strip().lstrip('*').lstrip('/').lstrip('#').strip()

        # 跳过注解行（@param, @return）
        if cleaned and not cleaned.startswith('@'):
            # 限制长度
            return cleaned[:60] + "..." if len(cleaned) > 60 else cleaned

    return ""
```

**PHP 示例**:
```php
/**
 * 幸运抽奖  ← 提取这一行
 * @param $info
 * @return array
 */
public function ImmediateLotteryDraw($info)
```

**输出**:
```markdown
| URL | Handler | Description |
|-----|---------|-------------|
| `/bigwheel/small/ImmediateLotteryDraw` | SmallController.ImmediateLotteryDraw | 幸运抽奖 |
```

**收益**: 不看代码就知道方法用途，信息密度大幅提升。

#### Layer 2: AI 增强（可选，v0.6.0+）

```python
# .codeindex.yaml
indexing:
  routes:
    enhance_description: true  # 可选：启用 AI 增强
    ai_model: "claude-haiku"   # 使用最便宜的模型
```

**场景**:
- 没有注释的代码 → AI 生成简短说明
- 中文注释 → AI 翻译（可选）
- 复杂注释 → AI 总结成一行

**成本**: 每个方法 ~$0.001，100 个方法 ~$0.10

---

## 🎯 解决 P3: 增量更新（Git Hooks）

### 问题

当前：修改一个文件 → 需要 `codeindex scan-all` 整个项目（慢）

### 方案设计

#### Phase 1: 基于 mtime 的简单增量

```python
class IncrementalUpdater:
    """增量更新器"""

    def __init__(self, root: Path):
        self.root = root
        self.index_file = root / ".codeindex" / "index.json"

    def detect_changes(self) -> list[Path]:
        """检测修改的目录"""
        index = self._load_index()
        changed_dirs = []

        for dir_path, last_mtime in index.items():
            current_mtime = self._get_dir_mtime(Path(dir_path))
            if current_mtime > last_mtime:
                changed_dirs.append(Path(dir_path))

        return changed_dirs

    def update(self):
        """增量更新"""
        changed_dirs = self.detect_changes()

        for dir_path in changed_dirs:
            # 只更新这个目录
            subprocess.run(["codeindex", "scan", str(dir_path)])

        self._update_index()

# CLI 命令
@click.command()
def update():
    """Incremental update based on file changes"""
    updater = IncrementalUpdater(Path.cwd())
    updater.update()
```

#### Phase 2: Git Hook 集成

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 检测 staged 的代码文件
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|php|java|ts)$')

if [ -n "$STAGED_FILES" ]; then
    echo "📝 Updating codeindex for modified files..."

    # 提取受影响的目录（去重）
    DIRS=$(dirname "$STAGED_FILES" | sort -u)

    # 只更新这些目录
    for dir in $DIRS; do
        codeindex scan "$dir" --quiet
    done

    # 自动 stage 更新的 README_AI.md
    git add '**/README_AI.md'
fi
```

**安装**:
```bash
codeindex install-hooks  # 一键安装 git hooks
```

**配置**:
```yaml
# .codeindex.yaml
indexing:
  auto_update:
    enabled: true
    trigger: pre-commit  # 或 post-commit, pre-push, manual
    quiet: true  # 静默更新，不打扰提交流程
```

#### Phase 3: 智能依赖分析（v0.7.0+）

```python
# 分析文件依赖关系
# 修改 A.py → 影响 B.py（import A）→ 更新 B 所在目录的 README
```

---

## 📈 实施计划

### Story 6.1: 可扩展路由提取框架（5天）

**任务**:
1. 设计 `RouteExtractor` 抽象基类
2. 实现 `RouteExtractorRegistry`
3. 重构现有 ThinkPHP 提取器为新架构
4. 更新 `smart_writer.py` 使用新接口
5. 测试：确保 ThinkPHP 功能不变

**验收标准**:
- ✅ ThinkPHP 路由表功能完全保留
- ✅ 新架构通过 20+ 单元测试
- ✅ 代码覆盖率 ≥ 90%

### Story 6.2: P1 - 方法行号（1天）

**任务**:
1. `RouteInfo` 增加 `line_number` 字段
2. 提取时填充行号
3. 显示时包含文件路径和行号格式化
4. 更新测试

**验收标准**:
- ✅ 路由表显示 `SmallController.php:1691`
- ✅ 可以直接 `vim +1691` 跳转

### Story 6.3: P2 - 注释提取（2天）

**任务**:
1. Parser 增强：提取 PHPDoc/JSDoc
2. `RouteInfo` 增加 `description` 字段
3. 实现 `_extract_description()` 通用逻辑
4. 路由表显示 Description 列
5. 测试多语言注释格式

**验收标准**:
- ✅ PHP: /** */ 注释提取
- ✅ Python: """docstring""" 提取
- ✅ Java/TypeScript: /** */ 提取
- ✅ 路由表显示一行简短描述

### Story 6.4: Laravel/Django 支持（5天）

**任务**:
1. 实现 `LaravelRouteExtractor`
2. 实现 `DjangoRouteExtractor`
3. 实现 `FastAPIRouteExtractor`
4. 框架检测增强
5. 测试项目验证

**验收标准**:
- ✅ Laravel 项目路由表正确
- ✅ Django 项目路由表正确
- ✅ FastAPI 项目路由表正确

### Story 6.5: P3.1 - 增量更新基础（3天）

**任务**:
1. 实现 `IncrementalUpdater` 基于 mtime
2. 添加 `codeindex update` 命令
3. 索引文件管理（.codeindex/index.json）
4. 测试：修改文件触发增量更新

**验收标准**:
- ✅ `codeindex update` 只更新修改的目录
- ✅ 比 `scan-all` 快 10x+

### Story 6.6: Git Hooks 集成（2天）

**任务**:
1. 生成 pre-commit hook 脚本
2. 添加 `codeindex install-hooks` 命令
3. 配置文件支持 auto_update 选项
4. 测试：commit 自动更新索引

**验收标准**:
- ✅ `git commit` 自动更新受影响的 README_AI.md
- ✅ 可配置启用/禁用
- ✅ 不影响提交流程（<2秒）

---

## 🎓 设计原则总结

### KISS 原则延续

就像 Story 4.4.5 的 KISS 描述生成器：
- ❌ 不要：复杂的 AI 理解
- ✅ 要：提取客观信息（路径、行号、注释）

### 通用化原则

- ❌ 不要：硬编码每个框架的规则到核心逻辑
- ✅ 要：可插拔的提取器，易于扩展

### 渐进增强原则

- Layer 1: 结构化提取（无 AI，高性能）
- Layer 2: AI 增强（可选，用户付费）

---

## 📊 预期效果

### Before (v0.4.0)

```markdown
## Routes (ThinkPHP)

| URL | Controller | Action |
|-----|------------|--------|
| `/bigwheel/small/ImmediateLotteryDraw` | SmallController | ImmediateLotteryDraw |
```

### After (v0.5.0)

```markdown
## Routes (ThinkPHP)

| URL | Handler | Method | Location | Description |
|-----|---------|--------|----------|-------------|
| `/bigwheel/small/ImmediateLotteryDraw` | SmallController.ImmediateLotteryDraw | ANY | `SmallController.php:1691` | 幸运抽奖 |
| `/bigwheel/index/activityList` | IndexController.activityList | ANY | `IndexController.php:234` | 活动列表 |
| `/bigwheel/index/addActivity` | IndexController.addActivity | ANY | `IndexController.php:456` | 添加活动 |
```

**改进**:
- ✅ 行号：直接跳转 `vim +1691`
- ✅ 描述：不看代码就知道功能
- ✅ 统一格式：所有框架一致

---

## 🚀 ROI 分析

| Feature | 实现成本 | 用户价值 | ROI |
|---------|---------|---------|-----|
| P1: 方法行号 | 1天 | 高（省去 grep 步骤） | ⭐⭐⭐⭐⭐ |
| P2: 注释提取 | 2天 | 高（不看代码知道功能） | ⭐⭐⭐⭐⭐ |
| P3.1: 增量更新 | 3天 | 中高（日常开发效率） | ⭐⭐⭐⭐ |
| Laravel/Django 支持 | 5天 | 中（扩大用户群） | ⭐⭐⭐ |
| Git Hooks | 2天 | 中（自动化体验） | ⭐⭐⭐ |

**建议优先级**: P1 → P2 → P3.1 → Git Hooks → 更多框架

---

## 📝 附录

### A. 框架路由规则对比

| 框架 | 路由定义方式 | 提取难度 |
|------|------------|---------|
| ThinkPHP | Convention: /module/controller/action | ⭐ 易 |
| Laravel | routes/web.php: Route::get() | ⭐⭐ 中 |
| Django | urls.py: urlpatterns | ⭐⭐ 中 |
| FastAPI | Decorator: @app.get() | ⭐ 易 |
| Spring Boot | Annotation: @GetMapping() | ⭐⭐⭐ 难 |
| Express | Code: app.get() | ⭐⭐ 中 |

### B. 注释格式对比

| 语言 | 注释格式 | 示例 |
|------|---------|------|
| PHP | PHPDoc | `/** 幸运抽奖 */` |
| Python | Docstring | `"""Get user info"""` |
| Java | JavaDoc | `/** Get user info */` |
| TypeScript | JSDoc | `/** Get user info */` |
| Go | Comment | `// GetUser returns user info` |

---

**Generated**: 2026-02-02
**Status**: Design Complete
**Next**: Story 6.1 Implementation (TDD)
