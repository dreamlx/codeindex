# Sprint 1: Epic 6 - Framework-Agnostic Route Extraction

**Sprint Duration**: 2026-02-02 ~ 2026-02-14 (10 working days)
**Branch**: `feature/epic6-framework-routes`
**Target Release**: v0.5.0

---

## 📋 Sprint Goal

实现框架无关的路由提取系统，支持方法行号和注释提取，为用户提供"杀手级"路由表功能。

---

## 🎯 Sprint Backlog

### Week 1 (Day 1-5): MVP 核心功能

| Day | Story | Tasks | Status |
|-----|-------|-------|--------|
| **Day 1** | **P1: 方法行号** | Task 1.1: RouteInfo 增加 line_number 字段 | 🔄 |
|  |  | Task 1.2: 提取时填充行号 | 📝 |
|  |  | Task 1.3: 显示格式化（路径:行号） | 📝 |
|  |  | Task 1.4: 测试覆盖 | 📝 |
| **Day 2-3** | **Story 6.1.1-6.1.3** | Task 2.1: RouteExtractor 抽象基类 | 📝 |
|  |  | Task 2.2: RouteExtractorRegistry | 📝 |
|  |  | Task 2.3: 重构 ThinkPHP 提取器 | 📝 |
|  |  | Task 2.4: 集成到 SmartWriter | 📝 |
|  |  | Task 2.5: 测试验证（ThinkPHP 功能不变） | 📝 |
| **Day 4-5** | **P2.1: 注释提取** | Task 3.1: Parser 增强提取注释 | 📝 |
|  |  | Task 3.2: RouteInfo 增加 description | 📝 |
|  |  | Task 3.3: _extract_description() 实现 | 📝 |
|  |  | Task 3.4: 路由表显示 Description 列 | 📝 |
|  |  | Task 3.5: 多语言测试（PHP/Python） | 📝 |

**Week 1 Deliverable**: v0.5.0-beta (ThinkPHP 增强版)

### Week 2 (Day 6-10): 扩展和完善

| Day | Story | Tasks | Status |
|-----|-------|-------|--------|
| **Day 6-7** | **P3.1: Git Hooks** | Task 4.1: cli_hooks 命令模块 | 📝 |
|  |  | Task 4.2: Hook 脚本生成 | 📝 |
|  |  | Task 4.3: 配置文件集成 | 📝 |
|  |  | Task 4.4: 已有 hook 检测合并 | 📝 |
|  |  | Task 4.5: 测试验证 | 📝 |
| **Day 8-9** | **Story 6.1.4** | Task 5.1: LaravelRouteExtractor | 📝 |
|  |  | Task 5.2: FastAPIRouteExtractor | 📝 |
|  |  | Task 5.3: 框架检测增强 | 📝 |
| **Day 10** | **验证和发布** | Task 6.1: 整体测试 | 📝 |
|  |  | Task 6.2: 文档更新 | 📝 |
|  |  | Task 6.3: CHANGELOG/RELEASE_NOTES | 📝 |

**Week 2 Deliverable**: v0.5.0 (多框架支持)

---

## 🏗️ Technical Architecture

### New Files to Create

```
src/codeindex/
├── route_extractor.py          # 抽象基类和数据结构
├── route_registry.py           # 提取器注册表
├── extractors/
│   ├── __init__.py
│   ├── thinkphp.py            # ThinkPHP 提取器（重构）
│   ├── laravel.py             # Laravel 提取器（new）
│   └── fastapi.py             # FastAPI 提取器（new）
└── cli_hooks.py               # Git hooks 命令（new）

tests/
├── test_route_extractor.py    # 抽象基类测试
├── test_route_registry.py     # 注册表测试
├── test_extractors/
│   ├── test_thinkphp.py       # ThinkPHP 提取器测试
│   ├── test_laravel.py        # Laravel 提取器测试
│   └── test_fastapi.py        # FastAPI 提取器测试
└── test_cli_hooks.py          # Git hooks 命令测试
```

### Modified Files

```
src/codeindex/
├── framework_detect.py        # 增强框架检测
├── smart_writer.py            # 集成新的路由提取
├── parser.py                  # 增强注释提取（可选）
└── cli.py                     # 注册 hooks 命令组

tests/
└── test_framework_detect.py   # 更新测试
```

---

## 📝 Day 1 详细计划

### Morning (2-3 hours): P1 - 方法行号

#### Task 1.1: 数据结构扩展（TDD）

**测试先行**:
```python
# tests/test_framework_detect.py

def test_route_info_with_line_number():
    """RouteInfo 应该包含行号"""
    route = RouteInfo(
        url="/api/users",
        controller="UserController",
        action="index",
        line_number=42,
        file_path="UserController.php"
    )

    assert route.line_number == 42
    assert route.file_path == "UserController.php"

def test_route_info_location_format():
    """Location 应该格式化为 file:line"""
    route = RouteInfo(
        url="/api/users",
        controller="UserController",
        action="index",
        line_number=42,
        file_path="controllers/UserController.php"
    )

    assert route.location == "controllers/UserController.php:42"
```

**实现**:
```python
# src/codeindex/framework_detect.py

@dataclass
class RouteInfo:
    """Information about a route."""
    url: str
    controller: str
    action: str
    method_signature: str = ""
    line_number: int = 0          # ← 新增
    file_path: str = ""           # ← 修改（原来有，但扩展）
    description: str = ""         # ← 新增（为 P2 准备）

    @property
    def location(self) -> str:
        """格式化位置信息：file:line"""
        if self.line_number > 0:
            return f"{self.file_path}:{self.line_number}"
        return self.file_path
```

#### Task 1.2: ThinkPHP 提取器填充行号

**测试**:
```python
def test_thinkphp_routes_include_line_numbers():
    """ThinkPHP 路由应该包含方法行号"""
    # Arrange
    parse_results = [
        ParseResult(
            path=Path("SmallController.php"),
            symbols=[
                Symbol(
                    name="SmallController",
                    kind="class",
                    signature="class SmallController",
                    line_start=10,
                    line_end=100,
                ),
                Symbol(
                    name="ImmediateLotteryDraw",
                    kind="method",
                    signature="public function ImmediateLotteryDraw($info)",
                    line_start=1691,
                    line_end=1720,
                    parent_symbol="SmallController",
                ),
            ],
        )
    ]

    # Act
    routes = extract_thinkphp_routes(parse_results, "bigwheel")

    # Assert
    assert len(routes) == 1
    assert routes[0].line_number == 1691
    assert routes[0].location == "SmallController.php:1691"
```

**实现**:
```python
# src/codeindex/framework_detect.py

def extract_thinkphp_routes(
    parse_results: list[ParseResult],
    module_name: str,
) -> list[RouteInfo]:
    """Extract routes from ThinkPHP controllers."""
    routes = []

    for result in parse_results:
        # ... 现有逻辑 ...

        for symbol in controller_methods:
            url = f"/{module_name.lower()}/{controller_name}/{method_name}"

            routes.append(RouteInfo(
                url=url,
                controller=controller_class,
                action=symbol.name,
                method_signature=symbol.signature,
                line_number=symbol.line_start,    # ← 新增
                file_path=result.path.name,       # ← 扩展
            ))

    return routes
```

#### Task 1.3: 显示格式化

**测试**:
```python
# tests/test_smart_writer.py

def test_route_table_includes_line_numbers(tmp_path):
    """路由表应该显示行号"""
    # ... setup ...

    writer = SmartWriter(config)
    lines = writer._generate_route_table(...)

    # 应该包含 Location 列
    assert "| Location |" in "\n".join(lines)
    # 应该显示 file:line 格式
    assert "SmallController.php:1691" in "\n".join(lines)
```

**实现**:
```python
# src/codeindex/smart_writer.py

def _generate_route_table(self, ...):
    """生成路由表"""
    lines = [
        "## Routes (ThinkPHP)",
        "",
        "| URL | Controller | Action | Location |",  # ← 新增 Location 列
        "|-----|------------|--------|----------|",
    ]

    for route in routes[:30]:
        lines.append(
            f"| `{route.url}` | {route.controller} | {route.action} | "
            f"`{route.location}` |"  # ← 使用 location 属性
        )

    return lines
```

### Afternoon (1-2 hours): Story 6.1 准备

#### Task 1.4: 设计验证和文档

- [ ] 验证 epic6-framework-routes.md 设计完整性
- [ ] 创建 TDD 测试框架
- [ ] 准备 Day 2 的 RouteExtractor 抽象基类设计

---

## ✅ Definition of Done (DoD)

每个 Task 完成需要满足：

1. **代码完成**
   - [ ] 功能实现完整
   - [ ] 代码符合 PEP 8（ruff check 通过）
   - [ ] 类型注解完整

2. **测试完成**
   - [ ] TDD: 测试先写
   - [ ] 单元测试覆盖率 ≥ 90%
   - [ ] 所有测试通过（299+ passed）

3. **文档完成**
   - [ ] Docstring 完整
   - [ ] CHANGELOG 更新
   - [ ] README_AI.md 自动更新

4. **提交完成**
   - [ ] Git commit 遵循规范
   - [ ] Commit message 清晰
   - [ ] Co-Authored-By: Claude

---

## 🎓 TDD Red-Green-Refactor 循环

每个功能开发遵循：

```
1. RED: 写失败的测试
   pytest tests/test_xxx.py -v
   # 预期：测试失败 ❌

2. GREEN: 实现最小代码使测试通过
   # 编写实现代码
   pytest tests/test_xxx.py -v
   # 预期：测试通过 ✅

3. REFACTOR: 优化代码
   ruff check src/
   # 预期：无错误 ✅

4. COMMIT: 提交代码
   git add ...
   git commit -m "feat(epic6): ..."
```

---

## 📊 Daily Stand-up Template

每天开始前确认：

**Yesterday:**
- ✅ 完成了什么？
- 🐛 遇到什么问题？

**Today:**
- 🎯 计划做什么？
- ⏰ 预计用时？

**Blockers:**
- ⚠️ 有什么阻碍？

---

## 🔄 Sprint Review (End of Week 1)

**验收标准**:
- [ ] ThinkPHP 路由表显示行号
- [ ] ThinkPHP 路由表显示注释
- [ ] 可扩展框架架构就绪
- [ ] 所有测试通过（300+ passed）
- [ ] 代码覆盖率 ≥ 85%
- [ ] v0.5.0-beta 可发布

---

## 🚀 Sprint Retrospective (End of Week 2)

**持续改进**:
- 😊 What went well?
- 😞 What could be improved?
- 💡 Action items for next sprint

---

**Generated**: 2026-02-02
**Sprint Master**: Claude Sonnet 4.5
**Status**: 🔄 In Progress - Day 1
