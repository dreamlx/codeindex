# 符号过载检测（Symbol Overload Detection）

## 🎯 问题识别

### 场景分析

**OperateGoods.class.php 实际数据**：
```python
# 1. tree-sitter提取
total_symbols_parsed = 57  # 所有符号

# 2. SmartWriter过滤（排除get*/set*等噪音）
filtered_symbols = 30  # 评分>阈值的符号

# 3. Adaptive Selector计算limit
file_lines = 8891
limit = 150  # mega级别文件

# 4. 最终显示
shown_symbols = min(30, 150) = 30
```

**关键问题**：
- 提取了57个符号，但只显示30个
- **被过滤的27个符号（47%）是什么？**
  - 简单getter/setter（15个）
  - 低评分方法（12个）
- **这说明什么？**
  - ✅ 代码中有大量噪音（getter/setter过多）
  - ✅ 类的职责不清晰（方法质量参差不齐）
  - ✅ **这本身就是技术债务！**

---

## 📊 符号过载的含义

### 1. 绝对数量过多

| 符号数量 | 评级 | 说明 |
|---------|------|------|
| >100 | 🔴🔴 CRITICAL | 严重的God Class |
| 50-100 | 🔴 HIGH | God Class，需要拆分 |
| 30-50 | 🟠 MEDIUM | 大类，建议重构 |
| <30 | 🟢 OK | 合理范围 |

### 2. 符号质量比例

| 过滤比例 | 评级 | 说明 |
|---------|------|------|
| >50% | 🔴 HIGH | 大量低质量符号（噪音多） |
| 30-50% | 🟠 MEDIUM | 存在较多噪音 |
| 10-30% | 🟡 LOW | 少量噪音（正常） |
| <10% | 🟢 OK | 高质量代码 |

### 3. 噪音类型分析

**OperateGoods.class.php 示例**：
```
总符号: 57
├── 简单getter (15个，26%) ← 数据类味道
├── 简单setter (5个，9%)   ← 数据类味道
├── 私有方法 (7个，12%)    ← 正常
└── 业务方法 (30个，53%)   ← 核心代码

过滤后剩余: 30 (53%)
噪音比例: 47%  ← 🔴 HIGH debt!
```

**结论**：
- 47%的符号是噪音 → 代码质量问题
- 20个getter/setter → 数据类味道
- **应该标记为技术债务**

---

## 💡 检测策略

### 方案1: 符号过载检测器

```python
# src/codeindex/tech_debt.py (新增)

@dataclass
class SymbolOverloadAnalysis:
    """符号过载分析结果"""
    total_symbols: int
    filtered_symbols: int
    filter_ratio: float          # 过滤比例（0-1）
    noise_breakdown: dict        # 噪音分解
    quality_score: float         # 质量分数（0-100）

class TechDebtDetector:

    def analyze_symbol_overload(
        self,
        parse_result: ParseResult,
        scorer: SymbolImportanceScorer
    ) -> tuple[list[DebtIssue], SymbolOverloadAnalysis]:
        """分析符号过载"""

        issues = []
        total = len(parse_result.symbols)

        # === 1. 绝对数量检测 ===
        if total > 100:
            issues.append(DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="massive_symbol_count",
                file_path=parse_result.path,
                metric_value=total,
                threshold=100,
                description=f"Massive symbol count: {total} symbols",
                suggestion=(
                    "This is an extreme God Class with 100+ symbols!\n"
                    "URGENT refactoring required:\n"
                    "1. Analyze method groups using codeindex tech-debt report\n"
                    "2. Extract 5-10 separate classes based on responsibilities\n"
                    "3. Use Facade pattern to maintain backward compatibility\n"
                    "4. Target: Max 20-30 symbols per class"
                )
            ))
        elif total > 50:
            issues.append(DebtIssue(
                severity=DebtSeverity.HIGH,
                category="god_class_symbols",
                file_path=parse_result.path,
                metric_value=total,
                threshold=50,
                description=f"God Class with {total} symbols",
                suggestion=(
                    "This class has too many symbols (50+).\n"
                    "Recommended approach:\n"
                    "1. Group methods by responsibility (use tech-debt report)\n"
                    "2. Extract 2-3 service classes\n"
                    "3. Apply Single Responsibility Principle"
                )
            ))
        elif total > 30:
            issues.append(DebtIssue(
                severity=DebtSeverity.MEDIUM,
                category="large_symbol_count",
                file_path=parse_result.path,
                metric_value=total,
                threshold=30,
                description=f"Large symbol count: {total} symbols",
                suggestion="Consider splitting into 2 classes"
            ))

        # === 2. 符号质量分析 ===

        # 模拟过滤（使用评分）
        scores = [(s, scorer.score(s)) for s in parse_result.symbols]

        # 设定过滤阈值（与SmartWriter一致）
        filter_threshold = 15.0
        filtered = [s for s, score in scores if score > filter_threshold]

        filter_ratio = 1 - (len(filtered) / total) if total > 0 else 0

        # === 3. 噪音分解分析 ===
        noise_breakdown = self._analyze_noise_breakdown(parse_result.symbols, scores)

        # === 4. 质量评分 ===
        quality_score = self._calculate_quality_score(
            total, len(filtered), noise_breakdown
        )

        # === 5. 基于过滤比例的债务检测 ===
        if filter_ratio > 0.5:  # 超过50%被过滤
            issues.append(DebtIssue(
                severity=DebtSeverity.HIGH,
                category="low_quality_symbols",
                file_path=parse_result.path,
                metric_value=filter_ratio * 100,
                threshold=50,
                description=f"High noise ratio: {filter_ratio*100:.1f}% symbols are low-quality",
                suggestion=(
                    f"This file has {int(filter_ratio*total)} low-quality symbols out of {total}.\n"
                    f"Breakdown:\n"
                    f"- Simple getters/setters: {noise_breakdown.get('getters_setters', 0)}\n"
                    f"- Other noise: {noise_breakdown.get('other_noise', 0)}\n"
                    f"\n"
                    f"Recommendations:\n"
                    f"1. If many getters/setters: Consider using DTOs or value objects\n"
                    f"2. Remove dead code and unused methods\n"
                    f"3. Apply 'Tell, Don't Ask' principle to reduce getters"
                )
            ))
        elif filter_ratio > 0.3:
            issues.append(DebtIssue(
                severity=DebtSeverity.MEDIUM,
                category="moderate_noise",
                file_path=parse_result.path,
                metric_value=filter_ratio * 100,
                threshold=30,
                description=f"Moderate noise: {filter_ratio*100:.1f}% symbols filtered",
                suggestion=(
                    f"Noise breakdown:\n"
                    f"- Simple getters/setters: {noise_breakdown.get('getters_setters', 0)}\n"
                    f"Consider refactoring to reduce boilerplate code"
                )
            ))

        # 构建分析结果
        analysis = SymbolOverloadAnalysis(
            total_symbols=total,
            filtered_symbols=len(filtered),
            filter_ratio=filter_ratio,
            noise_breakdown=noise_breakdown,
            quality_score=quality_score
        )

        return issues, analysis

    def _analyze_noise_breakdown(
        self,
        symbols: list[Symbol],
        scores: list[tuple[Symbol, float]]
    ) -> dict:
        """分析噪音来源"""

        breakdown = {
            "getters_setters": 0,      # 简单getter/setter
            "private_methods": 0,       # 私有方法（低分）
            "magic_methods": 0,         # 魔术方法
            "other_noise": 0,           # 其他低分符号
        }

        filter_threshold = 15.0

        for symbol, score in scores:
            if score <= filter_threshold:
                # 这是被过滤的符号，分析原因
                name_lower = symbol.name.lower()

                if name_lower.startswith(("get", "set", "is", "has")):
                    lines = symbol.line_end - symbol.line_start + 1
                    if lines < 10:
                        breakdown["getters_setters"] += 1
                    else:
                        breakdown["other_noise"] += 1
                elif name_lower.startswith("__"):
                    breakdown["magic_methods"] += 1
                elif name_lower.startswith("_"):
                    breakdown["private_methods"] += 1
                else:
                    breakdown["other_noise"] += 1

        return breakdown

    def _calculate_quality_score(
        self,
        total: int,
        filtered: int,
        noise_breakdown: dict
    ) -> float:
        """计算代码质量分数（0-100）"""

        if total == 0:
            return 100.0

        # 基础分数：基于保留率
        retention_rate = filtered / total
        base_score = retention_rate * 100

        # 惩罚因子：噪音类型
        getter_setter_count = noise_breakdown.get("getters_setters", 0)
        if getter_setter_count > 20:
            base_score -= 20  # 严重的数据类味道
        elif getter_setter_count > 10:
            base_score -= 10

        # 惩罚因子：符号总数
        if total > 100:
            base_score -= 30
        elif total > 50:
            base_score -= 15

        return max(0.0, min(100.0, base_score))
```

### 方案2: 在README中显示警告

```python
# src/codeindex/smart_writer.py (修改)

def _generate_detailed(self, result: ParseResult, ...) -> list[str]:
    """生成详细级别README"""

    lines = []

    # === 新增：符号质量警告 ===
    total_symbols = len(result.symbols)

    if total_symbols > 50:
        lines.append("\n> ⚠️ **Code Quality Warning**")
        lines.append(f"> This file has {total_symbols} symbols, which may indicate:")
        lines.append("> - God Class anti-pattern")
        lines.append("> - Mixed responsibilities")
        lines.append("> - Consider refactoring into smaller, focused classes")
        lines.append(f"> - See `TECH_DEBT_REPORT.md` for detailed analysis")
        lines.append("")

    # 过滤符号
    symbols = self._filter_symbols(result.symbols)
    total_filtered = len(symbols)

    # 计算过滤率
    if total_symbols > 0:
        filter_ratio = 1 - (total_filtered / total_symbols)

        if filter_ratio > 0.3:  # 30%以上被过滤
            lines.append("> ⚠️ **Symbol Quality Notice**")
            lines.append(f"> - Total symbols: {total_symbols}")
            lines.append(f"> - High-quality symbols: {total_filtered}")
            lines.append(f"> - Filtered (low-quality): {total_symbols - total_filtered} ({filter_ratio*100:.1f}%)")

            if filter_ratio > 0.5:
                lines.append("> - **High noise ratio detected!** Consider code cleanup.")

            lines.append("")

    # ... 继续原有逻辑
```

### 方案3: 技术债务报告集成

```python
# 在生成TECH_DEBT_REPORT.md时包含符号分析

def generate_markdown_report(report: TechDebtReport) -> str:
    lines = []

    # ... 现有内容

    # === 新增：符号质量分析 ===
    lines.append("\n## 📊 Symbol Quality Analysis")

    # 找出所有符号过载问题
    symbol_issues = [
        i for i in report.issues
        if i.category in ("massive_symbol_count", "god_class_symbols",
                         "low_quality_symbols", "moderate_noise")
    ]

    if symbol_issues:
        lines.append("\n### Files with Symbol Quality Issues")

        # 按文件分组
        by_file = {}
        for issue in symbol_issues:
            if issue.file_path not in by_file:
                by_file[issue.file_path] = []
            by_file[issue.file_path].append(issue)

        for file_path, issues in sorted(
            by_file.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ):
            lines.append(f"\n#### {file_path.name}")

            for issue in issues:
                lines.append(f"- {issue.severity.value} {issue.description}")

            # 如果有噪音分析，显示详情
            noise_issue = next(
                (i for i in issues if "noise" in i.category.lower()),
                None
            )
            if noise_issue and noise_issue.suggestion:
                lines.append(f"\n{noise_issue.suggestion}")

    return "\n".join(lines)
```

---

## 📋 示例输出

### 1. README_AI.md 中的警告

```markdown
# README_AI.md - OperateGoods.class.php

> ⚠️ **Code Quality Warning**
> This file has 57 symbols, which may indicate:
> - God Class anti-pattern
> - Mixed responsibilities
> - Consider refactoring into smaller, focused classes
> - See `TECH_DEBT_REPORT.md` for detailed analysis

> ⚠️ **Symbol Quality Notice**
> - Total symbols: 57
> - High-quality symbols: 30
> - Filtered (low-quality): 27 (47.4%)
> - **High noise ratio detected!** Consider code cleanup.

## Purpose
商品操作控制器，负责商品的增删改查和业务逻辑处理。

## Symbol Groups

**Retrieval** (8 methods)
  - getGoodsInfo() - 获取商品详细信息
  ...
```

### 2. TECH_DEBT_REPORT.md 中的分析

```markdown
# Technical Debt Report

## 🚨 Critical Issues

### 🔴 HIGH OperateGoods.class.php

**Category**: god_class_symbols
**Issue**: God Class with 57 symbols

**Category**: low_quality_symbols
**Issue**: High noise ratio: 47.4% symbols are low-quality

**Noise Breakdown**:
- Simple getters/setters: 20 (35%)
- Private methods: 5 (9%)
- Other low-quality: 2 (3%)

**Total**: 27 low-quality symbols out of 57

**Suggestions**:
1. **Remove getters/setters**: 20 simple accessors indicate Data Class smell
   - Consider: Use DTOs for data transfer
   - Consider: Apply "Tell, Don't Ask" principle
   - Consider: Use property decorators (Python) or magic methods (PHP)

2. **Refactor God Class**: 57 symbols → 3-4 focused classes
   - GoodsQueryService (8 retrieval methods)
   - GoodsPriceService (5 price methods)
   - GoodsStockService (4 stock methods)
   - GoodsValidator (4 validation methods)

3. **Expected improvement**:
   - Symbol count: 57 → 4 classes × 10-15 symbols
   - Quality score: 52.6 → 85+
   - Noise ratio: 47% → <10%

## 📊 Symbol Quality Analysis

### Files with Symbol Quality Issues

#### OperateGoods.class.php
- 🔴 HIGH God Class with 57 symbols
- 🔴 HIGH High noise ratio: 47.4% symbols are low-quality

**Quality Score**: 52.6 / 100

**Improvement Potential**: 🔴🔴 CRITICAL
- Current: 30 high-quality symbols buried in 57 total
- After refactoring: 30 high-quality symbols in focused classes
- Maintainability gain: 300%

#### OrderController.class.php
- 🔴 HIGH God Class with 48 symbols
- 🟠 MEDIUM Moderate noise: 35% symbols filtered

**Quality Score**: 65.0 / 100
```

---

## 🎯 实施计划

### Phase 1: 检测器实现（2天）

**Story 1.1**: 实现 `analyze_symbol_overload()`
- 绝对数量检测
- 过滤比例分析
- 噪音分解分析
- 质量评分计算

**Story 1.2**: 集成到 `TechDebtDetector`
- 在 `analyze_file()` 中调用
- 添加到问题列表

### Phase 2: README警告（1天）

**Story 2.1**: 修改 `SmartWriter._generate_detailed()`
- 添加符号数量警告
- 添加质量通知
- 条件显示（只在有问题时）

### Phase 3: 报告增强（1天）

**Story 3.1**: 更新 `generate_markdown_report()`
- 添加"Symbol Quality Analysis"章节
- 噪音分解展示
- 质量分数和改进建议

### Phase 4: CLI集成（0.5天）

**Story 4.1**: 在 `scan-all` 中显示警告
```bash
codeindex scan-all

# 输出：
# ⚠️  Symbol Quality Issues Found:
# - OperateGoods.class.php: 57 symbols (47% noise)
# - OrderController.class.php: 48 symbols (35% noise)
#
# Run 'codeindex tech-debt' for detailed analysis.
```

---

## 🔄 与现有功能的关系

### 与Adaptive Selector的关系

```python
# 当前流程（保持不变）
total_symbols = 57
↓
SmartWriter过滤（评分阈值）
↓
filtered_symbols = 30
↓
AdaptiveSelector.calculate_limit(file_lines=8891, total_symbols=30)
↓
limit = 150  # mega级别
↓
shown_symbols = min(30, 150) = 30
```

**新增功能**：
```python
# 在scan-all时
detector.analyze_symbol_overload(parse_result, scorer)
↓
检测：total=57, filtered=30, ratio=47%
↓
生成债务问题：
- God Class (57 symbols)
- High noise ratio (47%)
↓
在README中显示警告
在TECH_DEBT_REPORT.md中详细分析
```

**关键**：
- ✅ 不改变现有的过滤和显示逻辑
- ✅ 只是**标识和报告**这是技术债务
- ✅ 让用户知道"为什么有这么多符号被过滤"

### 与技术债务报告的关系

**扩展债务类型**：

| 债务类型 | 现有 | 新增 |
|---------|------|------|
| 文件级别 | 超大文件、大文件 | - |
| 类级别 | God Class（方法数） | God Class（符号数）✨ |
| 符号级别 | 超长方法 | - |
| **质量级别** | - | **符号噪音比例** ✨ |
| **质量级别** | - | **质量评分** ✨ |

---

## ✅ 总结

### 你的问题：tree-sitter提取符号本身oversize了，怎么处理？

**答案**：

1. **✅ 是的，应该标识为技术债务**
   - 57个符号本身就是God Class
   - 47%被过滤说明代码质量问题
   - 这是**架构问题**，不是工具问题

2. **✅ tree-sitter提取是正确的**
   - 它应该提取所有符号（完整性）
   - 不应该在解析阶段过滤
   - 过滤是SmartWriter的职责

3. **✅ 解决方案：三层处理**
   - **Layer 1**: tree-sitter提取所有符号（不变）
   - **Layer 2**: SmartWriter/AdaptiveSelector过滤和限制（不变）
   - **Layer 3**: TechDebtDetector分析和报告（新增）✨

4. **✅ 用户价值**
   - 在README中看到警告："这个类有质量问题"
   - 在TECH_DEBT_REPORT.md中看到详细分析
   - 知道应该重构哪些文件、如何重构

### 实施优先级

| 优先级 | 功能 | 工作量 | 价值 |
|-------|------|--------|------|
| 🔥🔥🔥🔥🔥 | 符号过载检测器 | 2天 | 识别代码质量问题 |
| 🔥🔥🔥🔥 | README警告 | 1天 | 即时反馈 |
| 🔥🔥🔥 | 技术债务报告增强 | 1天 | 详细分析 |

**总工作量**：4天
**总价值**：让用户理解"为什么符号这么多"，并知道如何改进

---

需要我开始实施吗？建议从"符号过载检测器"开始，这样可以先完成核心逻辑。