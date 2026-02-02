# 技术债务检测与报告

## 🔍 问题澄清：超大文件如何处理？

### 当前解析流程

```python
# src/codeindex/parser.py: parse_file()

def parse_file(path: Path) -> ParseResult:
    # 1. 一次性读取整个文件到内存
    source_bytes = path.read_bytes()  # OperateGoods.class.php = 711KB

    # 2. tree-sitter 解析（C实现，很快）
    tree = parser.parse(source_bytes)  # 返回AST

    # 3. 提取符号元数据
    for child in tree.root_node.children:
        symbols.append(_parse_function(child, source_bytes))

    # 4. 返回ParseResult
    return ParseResult(
        path=path,
        symbols=[...],      # 57个符号 × 200字节 = 11KB
        imports=[...],      # 导入信息
        file_lines=8891,
        # 注意：source_bytes不包含在ParseResult中！
    )
```

### 关键发现 ✅

**1. tree-sitter可以处理超大文件**
- C语言实现，性能极高
- 8891行PHP代码（711KB）解析时间：~50ms
- 即使10万行代码也能在1秒内完成

**2. 我们不保存完整源码**
- `ParseResult` 只包含**元数据**（符号列表、导入信息）
- 元数据很小：57个符号 × ~200字节 = **11KB**
- 完整源码（711KB）在解析后被丢弃

**3. 多轮对话只需要元数据**

```python
def ai_enhance_multi_turn(parse_results):
    # 第1轮：需要什么？
    prompt1 = f"""
    文件: {result.path.name}
    行数: {result.file_lines}        # 8891
    符号数: {len(result.symbols)}    # 57
    类: {[s.name for s in symbols if s.kind == "class"]}  # ["OperateGoods"]
    """

    # 第2轮：需要什么？
    prompt2 = f"""
    核心类: OperateGoods
    方法分组:
    - CRUD: getGoodsInfo(), updateGoodsInfo(), ...
    - 价格管理: setGoodsPrice(), getPriceHistory(), ...
    - 库存: checkStock(), updateStock(), ...
    """

    # 第3轮：合并
```

**结论**：
- ✅ 超大文件**可以一次性解析**（tree-sitter很快）
- ✅ **元数据很小**（11KB），完全可以多轮使用
- ✅ **不需要读取完整源码**来生成README

### 什么时候需要读取完整源码？

**只有这些场景**：
1. **知识图谱构建** - 分析方法调用关系（需要AST遍历）
2. **代码片段提取** - 显示具体实现代码
3. **深度分析** - 圈复杂度、代码味道检测

**这些都不是README生成的工作**！

---

## 🚨 技术债务检测与报告

### 设计思路

你说得对：**超大文件本身就是技术债务**

我们应该：
1. ✅ **检测技术债务**（扫描时自动分析）
2. ✅ **生成债务报告**（指导用户重构）
3. ✅ **仍然生成README**（解决当前问题）
4. ✅ **报告重构建议**（解决根本问题）

### 技术债务指标

#### 1. 文件级别债务

| 指标 | 阈值 | 严重性 | 说明 |
|------|------|--------|------|
| **超大文件** | >2000行 | 🔴 HIGH | 违反单一职责原则 |
| **大文件** | >1000行 | 🟠 MEDIUM | 可读性和维护性下降 |
| **巨类** | >30个方法 | 🔴 HIGH | God Class反模式 |
| **深层嵌套** | >5层目录 | 🟡 LOW | 组织结构复杂 |

#### 2. 符号级别债务

| 指标 | 阈值 | 严重性 | 说明 |
|------|------|--------|------|
| **超长方法** | >100行 | 🟠 MEDIUM | 应该拆分 |
| **参数过多** | >5个参数 | 🟡 LOW | 考虑参数对象 |
| **缺乏文档** | 无docstring | 🟡 LOW | 可维护性问题 |

#### 3. 架构级别债务

| 指标 | 阈值 | 严重性 | 说明 |
|------|------|--------|------|
| **职责混乱** | 多种职责模式 | 🟠 MEDIUM | 缺乏清晰架构 |
| **getter/setter过多** | >30% | 🟡 LOW | 数据类味道 |

---

## 💻 实现设计

### 1. 债务检测器

```python
# src/codeindex/tech_debt.py

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class DebtSeverity(Enum):
    LOW = "🟡 LOW"
    MEDIUM = "🟠 MEDIUM"
    HIGH = "🔴 HIGH"
    CRITICAL = "🔴🔴 CRITICAL"

@dataclass
class DebtIssue:
    """单个技术债务问题"""
    severity: DebtSeverity
    category: str           # "file_size" | "god_class" | "long_method" | ...
    file_path: Path
    symbol_name: str = ""   # 如果是符号级别问题
    metric_value: float = 0 # 实际值（如2000行）
    threshold: float = 0    # 阈值（如1000行）
    description: str = ""
    suggestion: str = ""

@dataclass
class TechDebtReport:
    """技术债务总报告"""
    project_path: Path
    total_files: int
    total_issues: int
    issues_by_severity: dict[DebtSeverity, int]
    issues: list[DebtIssue]

    def get_critical_issues(self) -> list[DebtIssue]:
        """获取严重问题"""
        return [i for i in self.issues
                if i.severity in (DebtSeverity.HIGH, DebtSeverity.CRITICAL)]

    def get_refactoring_candidates(self) -> list[Path]:
        """获取需要重构的文件"""
        critical_files = set()
        for issue in self.get_critical_issues():
            critical_files.add(issue.file_path)
        return sorted(critical_files)


class TechDebtDetector:
    """技术债务检测器"""

    def __init__(self, config: Config):
        self.config = config
        self.issues = []

    def analyze_file(self, parse_result: ParseResult) -> list[DebtIssue]:
        """分析单个文件的技术债务"""
        issues = []

        # 1. 检测超大文件
        if parse_result.file_lines > 5000:
            issues.append(DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=parse_result.path,
                metric_value=parse_result.file_lines,
                threshold=5000,
                description=f"Extremely large file ({parse_result.file_lines} lines)",
                suggestion=(
                    "URGENT: This file is too large to maintain effectively.\n"
                    "Suggested approach:\n"
                    "1. Identify logical groupings of methods\n"
                    "2. Extract into separate classes (Strategy/Service pattern)\n"
                    "3. Example: If this is a Controller with 50+ methods,\n"
                    "   split into GoodsQueryController, GoodsCRUDController, etc."
                )
            ))
        elif parse_result.file_lines > 2000:
            issues.append(DebtIssue(
                severity=DebtSeverity.HIGH,
                category="large_file",
                file_path=parse_result.path,
                metric_value=parse_result.file_lines,
                threshold=2000,
                description=f"Large file ({parse_result.file_lines} lines)",
                suggestion=(
                    "Consider refactoring this file:\n"
                    "1. Look for method groups with related functionality\n"
                    "2. Extract into separate classes\n"
                    "3. Target: <500 lines per file"
                )
            ))

        # 2. 检测God Class
        method_count = sum(1 for s in parse_result.symbols if s.kind == "method")
        if method_count > 50:
            issues.append(DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="god_class",
                file_path=parse_result.path,
                metric_value=method_count,
                threshold=50,
                description=f"God Class with {method_count} methods",
                suggestion=(
                    "This class has too many responsibilities (God Class anti-pattern).\n"
                    "Refactoring strategy:\n"
                    "1. Group methods by responsibility (CRUD, validation, calculation)\n"
                    "2. Extract each group into a separate class\n"
                    "3. Use composition or delegation pattern\n"
                    "4. Target: 10-20 methods per class"
                )
            ))
        elif method_count > 30:
            issues.append(DebtIssue(
                severity=DebtSeverity.HIGH,
                category="large_class",
                file_path=parse_result.path,
                metric_value=method_count,
                threshold=30,
                description=f"Large class with {method_count} methods",
                suggestion="Consider splitting into 2-3 smaller classes"
            ))

        # 3. 检测超长方法
        for symbol in parse_result.symbols:
            if symbol.kind in ("function", "method"):
                lines = symbol.line_end - symbol.line_start + 1

                if lines > 200:
                    issues.append(DebtIssue(
                        severity=DebtSeverity.HIGH,
                        category="very_long_method",
                        file_path=parse_result.path,
                        symbol_name=symbol.name,
                        metric_value=lines,
                        threshold=200,
                        description=f"Very long method: {symbol.name}() has {lines} lines",
                        suggestion=(
                            "This method is doing too much. Consider:\n"
                            "1. Extract Helper Methods pattern\n"
                            "2. Identify distinct steps/phases\n"
                            "3. Extract each into a separate method\n"
                            "4. Target: <50 lines per method"
                        )
                    ))
                elif lines > 100:
                    issues.append(DebtIssue(
                        severity=DebtSeverity.MEDIUM,
                        category="long_method",
                        file_path=parse_result.path,
                        symbol_name=symbol.name,
                        metric_value=lines,
                        threshold=100,
                        description=f"Long method: {symbol.name}() has {lines} lines",
                        suggestion="Consider extracting helper methods"
                    ))

        # 4. 检测getter/setter过多（数据类味道）
        simple_getters_setters = sum(
            1 for s in parse_result.symbols
            if s.kind == "method" and s.name.lower().startswith(("get", "set"))
            and (s.line_end - s.line_start) < 5
        )

        if simple_getters_setters > 20:
            issues.append(DebtIssue(
                severity=DebtSeverity.MEDIUM,
                category="data_class_smell",
                file_path=parse_result.path,
                metric_value=simple_getters_setters,
                threshold=20,
                description=f"{simple_getters_setters} simple getters/setters",
                suggestion=(
                    "This class looks like a Data Class (anemic domain model).\n"
                    "Consider:\n"
                    "1. Move behavior closer to data\n"
                    "2. Replace getters with meaningful queries\n"
                    "3. Use value objects or DTOs for pure data"
                )
            ))

        # 5. 检测职责混乱
        responsibilities = _detect_responsibilities(parse_result.symbols)
        if len(responsibilities) > 5:
            issues.append(DebtIssue(
                severity=DebtSeverity.MEDIUM,
                category="mixed_responsibilities",
                file_path=parse_result.path,
                metric_value=len(responsibilities),
                threshold=5,
                description=f"Class has {len(responsibilities)} different responsibilities",
                suggestion=(
                    f"This class handles multiple concerns: {', '.join(responsibilities)}\n"
                    "Consider applying Single Responsibility Principle:\n"
                    "1. Extract each responsibility into separate classes\n"
                    "2. Use interfaces/protocols to define contracts"
                )
            ))

        return issues

    def generate_report(self, all_parse_results: list[ParseResult]) -> TechDebtReport:
        """生成完整的技术债务报告"""
        all_issues = []

        for result in all_parse_results:
            if not result.error:
                issues = self.analyze_file(result)
                all_issues.extend(issues)

        # 统计
        issues_by_severity = {
            severity: sum(1 for i in all_issues if i.severity == severity)
            for severity in DebtSeverity
        }

        return TechDebtReport(
            project_path=Path.cwd(),
            total_files=len(all_parse_results),
            total_issues=len(all_issues),
            issues_by_severity=issues_by_severity,
            issues=sorted(all_issues, key=lambda x: (x.severity.value, x.metric_value), reverse=True)
        )


def _detect_responsibilities(symbols: list[Symbol]) -> set[str]:
    """检测类的职责"""
    responsibilities = set()

    for symbol in symbols:
        if symbol.kind != "method":
            continue

        name_lower = symbol.name.lower()

        if any(k in name_lower for k in ["get", "find", "query", "list"]):
            responsibilities.add("Data Retrieval")
        if any(k in name_lower for k in ["create", "add", "insert"]):
            responsibilities.add("Data Creation")
        if any(k in name_lower for k in ["update", "set", "modify"]):
            responsibilities.add("Data Update")
        if any(k in name_lower for k in ["delete", "remove"]):
            responsibilities.add("Data Deletion")
        if any(k in name_lower for k in ["validate", "check", "verify"]):
            responsibilities.add("Validation")
        if any(k in name_lower for k in ["calculate", "compute", "process"]):
            responsibilities.add("Business Logic")
        if any(k in name_lower for k in ["export", "import", "download"]):
            responsibilities.add("Data Exchange")
        if any(k in name_lower for k in ["send", "notify", "email"]):
            responsibilities.add("Communication")

    return responsibilities
```

### 2. 报告生成器

```python
# src/codeindex/tech_debt_report.py

def generate_markdown_report(report: TechDebtReport) -> str:
    """生成Markdown格式的技术债务报告"""

    lines = []

    # === 标题 ===
    lines.append("# Technical Debt Report")
    lines.append(f"\n**Project**: {report.project_path}")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # === 执行摘要 ===
    lines.append("\n## Executive Summary")
    lines.append(f"\n- Total Files Analyzed: {report.total_files}")
    lines.append(f"- Total Issues Found: {report.total_issues}")

    for severity in DebtSeverity:
        count = report.issues_by_severity[severity]
        if count > 0:
            lines.append(f"- {severity.value}: {count}")

    # === 严重问题 ===
    critical = report.get_critical_issues()
    if critical:
        lines.append("\n## 🚨 Critical Issues (Requires Immediate Attention)")

        for issue in critical[:10]:  # 显示前10个
            lines.append(f"\n### {issue.severity.value} {issue.file_path.name}")
            lines.append(f"\n**Category**: {issue.category}")
            lines.append(f"**Issue**: {issue.description}")
            lines.append(f"\n**Suggestion**:")
            lines.append(f"```\n{issue.suggestion}\n```")

    # === 重构候选 ===
    candidates = report.get_refactoring_candidates()
    if candidates:
        lines.append("\n## 📋 Refactoring Priority List")
        lines.append("\nFiles that should be refactored (ordered by severity):\n")

        for i, file_path in enumerate(candidates[:20], 1):
            # 找出这个文件的所有问题
            file_issues = [iss for iss in report.issues if iss.file_path == file_path]
            issue_count = len(file_issues)

            # 计算严重性分数
            severity_score = sum(
                4 if i.severity == DebtSeverity.CRITICAL else
                3 if i.severity == DebtSeverity.HIGH else
                2 if i.severity == DebtSeverity.MEDIUM else 1
                for i in file_issues
            )

            lines.append(f"{i}. **{file_path.name}** - {issue_count} issues (severity score: {severity_score})")

            # 列出主要问题
            for issue in file_issues[:3]:
                lines.append(f"   - {issue.description}")

    # === 统计图表 ===
    lines.append("\n## 📊 Debt Distribution")

    # 按类别统计
    by_category = {}
    for issue in report.issues:
        by_category[issue.category] = by_category.get(issue.category, 0) + 1

    lines.append("\n### By Category")
    for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {category}: {count}")

    # === 改进建议 ===
    lines.append("\n## 💡 Recommended Action Plan")

    if report.issues_by_severity[DebtSeverity.CRITICAL] > 0:
        lines.append("\n### Phase 1: Critical (This Sprint)")
        lines.append("Focus on files with CRITICAL severity:")
        critical_files = [i.file_path.name for i in critical[:5]]
        for f in critical_files:
            lines.append(f"- Refactor {f}")

    if report.issues_by_severity[DebtSeverity.HIGH] > 0:
        lines.append("\n### Phase 2: High Priority (Next 2 Sprints)")
        lines.append("Address large files and God Classes")

    if report.issues_by_severity[DebtSeverity.MEDIUM] > 0:
        lines.append("\n### Phase 3: Medium Priority (Next Quarter)")
        lines.append("Improve code quality (long methods, data classes)")

    lines.append("\n## 📚 Resources")
    lines.append("\n- [Refactoring Guru](https://refactoring.guru/)")
    lines.append("- [Martin Fowler - Refactoring](https://martinfowler.com/books/refactoring.html)")
    lines.append("- [Clean Code Principles](https://clean-code-developer.com/)")

    return "\n".join(lines)


def save_report(report: TechDebtReport, output_path: Path = None):
    """保存报告到文件"""
    if output_path is None:
        output_path = Path.cwd() / "TECH_DEBT_REPORT.md"

    content = generate_markdown_report(report)
    output_path.write_text(content)

    console.print(f"[green]✓ Technical debt report saved to {output_path}[/green]")
```

### 3. CLI 集成

```python
# src/codeindex/cli.py

@main.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None)
def tech-debt(root: Path, output: Path):
    """Analyze technical debt in the codebase"""

    config = Config.load()

    console.print("[bold]🔍 Analyzing Technical Debt...[/bold]")

    # 1. 扫描所有文件
    from .scanner import find_all_directories, scan_directory

    dirs = find_all_directories(root, config)
    all_parse_results = []

    for dir_path in dirs:
        result = scan_directory(dir_path, config)
        if result.files:
            parse_results = parse_files_parallel(result.files, config, quiet=True)
            all_parse_results.extend(parse_results)

    console.print(f"[dim]Analyzed {len(all_parse_results)} files[/dim]")

    # 2. 检测技术债务
    detector = TechDebtDetector(config)
    report = detector.generate_report(all_parse_results)

    # 3. 显示摘要
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total Issues: {report.total_issues}")
    for severity in DebtSeverity:
        count = report.issues_by_severity[severity]
        if count > 0:
            console.print(f"  {severity.value}: {count}")

    # 4. 保存报告
    save_report(report, output)

    # 5. 显示关键问题
    critical = report.get_critical_issues()
    if critical:
        console.print(f"\n[bold red]⚠️  {len(critical)} Critical Issues Found:[/bold red]")
        for issue in critical[:5]:
            console.print(f"  - {issue.file_path.name}: {issue.description}")
```

---

## 📊 示例报告

### 你的PHP项目预期输出

```markdown
# Technical Debt Report

**Project**: /Users/dreamlinx/Projects/php_admin-main
**Generated**: 2026-01-27 15:30:00

## Executive Summary

- Total Files Analyzed: 119
- Total Issues Found: 23
- 🔴🔴 CRITICAL: 2
- 🔴 HIGH: 5
- 🟠 MEDIUM: 10
- 🟡 LOW: 6

## 🚨 Critical Issues (Requires Immediate Attention)

### 🔴🔴 CRITICAL OperateGoods.class.php

**Category**: super_large_file
**Issue**: Extremely large file (8891 lines)

**Suggestion**:
```
URGENT: This file is too large to maintain effectively.
Suggested approach:
1. Identify logical groupings of methods
2. Extract into separate classes (Strategy/Service pattern)
3. Example: If this is a Controller with 50+ methods,
   split into GoodsQueryController, GoodsCRUDController, GoodsPriceController
```

### 🔴🔴 CRITICAL OperateGoods.class.php

**Category**: god_class
**Issue**: God Class with 57 methods

**Suggestion**:
```
This class has too many responsibilities (God Class anti-pattern).
Refactoring strategy:
1. Group methods by responsibility:
   - Retrieval (8 methods) → GoodsQueryService
   - Update (5 methods) → GoodsUpdateService
   - Validation (4 methods) → GoodsValidator
   - Calculation (8 methods) → GoodsPriceCalculator
2. Use composition: OperateGoods delegates to these services
3. Target: 10-20 methods per class
```

### 🔴 HIGH OrderController.class.php

**Category**: large_file
**Issue**: Large file (7923 lines)

**Suggestion**:
```
Consider refactoring this file:
1. Look for method groups with related functionality
2. Extract into separate classes
3. Target: <500 lines per file
```

## 📋 Refactoring Priority List

Files that should be refactored (ordered by severity):

1. **OperateGoods.class.php** - 4 issues (severity score: 14)
   - Extremely large file (8891 lines)
   - God Class with 57 methods
   - Very long method: processComplexOrder() has 215 lines
   - 23 simple getters/setters

2. **OrderController.class.php** - 3 issues (severity score: 10)
   - Large file (7923 lines)
   - Large class with 48 methods
   - Very long method: calculateOrderPrice() has 180 lines

3. **GoodsModel.class.php** - 2 issues (severity score: 6)
   - Large file (5132 lines)
   - 25 simple getters/setters (Data Class smell)

## 📊 Debt Distribution

### By Category
- super_large_file: 2
- god_class: 1
- large_file: 5
- very_long_method: 6
- data_class_smell: 4
- mixed_responsibilities: 5

## 💡 Recommended Action Plan

### Phase 1: Critical (This Sprint)
Focus on files with CRITICAL severity:
- Refactor OperateGoods.class.php
  - Priority: Extract GoodsQueryService (8 retrieval methods)
  - Priority: Extract GoodsPriceCalculator (8 calculation methods)
  - Priority: Split processComplexOrder() into smaller methods

### Phase 2: High Priority (Next 2 Sprints)
Address large files and God Classes:
- OrderController.class.php - Split into OrderQueryController + OrderCRUDController
- GoodsModel.class.php - Consider using DTOs for simple data transfer

### Phase 3: Medium Priority (Next Quarter)
Improve code quality (long methods, data classes)

## 📚 Resources

- [Refactoring Guru](https://refactoring.guru/)
- [Martin Fowler - Refactoring](https://martinfowler.com/books/refactoring.html)
- [Clean Code Principles](https://clean-code-developer.com/)
```

---

## 🔄 工作流整合

### scan-all 命令集成

```bash
# 扫描时自动检测技术债务
codeindex scan-all

# 输出：
# ================================================================================
# 📝 Phase 1: Generating READMEs (SmartWriter)...
# ✓ 119/119 directories processed
#
# 🤖 Phase 2: AI Enhancement...
# ✓ 7/8 directories enhanced
# ⚠️  OperateGoods.class.php: Using multi-turn dialogue (super large file)
#
# 🔍 Phase 3: Technical Debt Analysis...
# Found 23 issues (2 critical, 5 high, 10 medium, 6 low)
#
# 📄 Reports Generated:
# - README_AI.md files: 119
# - TECH_DEBT_REPORT.md: 1
#
# ⚠️  Critical Issues:
# - OperateGoods.class.php: Extremely large file (8891 lines)
# - OperateGoods.class.php: God Class with 57 methods
#
# Run 'codeindex tech-debt' for detailed analysis.
# ================================================================================
```

### 独立命令

```bash
# 只生成技术债务报告（不重新扫描）
codeindex tech-debt --output debt-report.md

# 指定项目路径
codeindex tech-debt --root /path/to/project
```

---

## ✅ 总结

### 问题1回答：超大文件如何处理？

**答案**：
1. ✅ tree-sitter **可以快速解析**超大文件（<1秒）
2. ✅ 我们**只保存元数据**（11KB），不保存完整源码
3. ✅ 多轮对话**只需要元数据**，完全可行
4. ✅ 完整源码**只在知识图谱时需要**（另一个工具）

### 问题2回答：技术债务报告

**功能**：
- ✅ 自动检测超大文件、God Class、超长方法等
- ✅ 生成详细报告（TECH_DEBT_REPORT.md）
- ✅ 提供具体的重构建议
- ✅ 优先级排序（Critical → High → Medium → Low）
- ✅ 分阶段行动计划

**价值**：
- 帮助用户识别最需要重构的文件
- 提供具体的重构方向和示例
- 长期改善代码质量

---

需要我现在开始实施技术债务检测功能吗？还是先实施多轮对话？