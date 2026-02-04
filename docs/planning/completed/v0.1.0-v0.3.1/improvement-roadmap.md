# codeindex 改进路线图

基于评估问题分析，本文档提供**系统性、可执行**的改进方案。

---

## 🎯 改进目标

### 核心目标
1. **提升大文件信息完整性**：15个符号 → 80+个符号（+433%）
2. **优化符号选择准确性**：关键API覆盖率 70% → 95%（+36%）
3. **保持导航效率**：定位时间 <30秒（不降低）
4. **控制Token消耗**：增幅 <20%（可接受）

### 设计原则
- ✅ **不破坏核心价值**：保持"快速导航"定位
- ✅ **智能 > 数量**：重要性评分优于简单增加数量
- ✅ **自适应设计**：根据文件大小动态调整
- ✅ **向后兼容**：现有配置继续有效

---

## 📊 改进方向总览

| 改进方向 | 优先级 | 工作量 | 影响 | 状态 |
|---------|--------|--------|------|------|
| **1. 符号重要性评分** | ⭐⭐⭐ P0 | 中(3天) | 高 | 📝 设计中 |
| **2. 自适应符号提取** | ⭐⭐⭐ P0 | 低(2天) | 高 | 📝 设计中 |
| **3. 自动化评估框架** | ⭐⭐ P1 | 中(4天) | 中 | 📋 计划中 |
| **4. 双模式索引** | ⭐ P2 | 高(5天) | 中 | 💡 可选 |
| **5. 框架感知评分** | ⭐ P3 | 高(6天) | 低 | 💡 可选 |

---

## 🚀 Phase 1：核心改进（本周）

### 改进1：符号重要性评分系统 ⭐⭐⭐

#### 问题
当前无法区分关键API和噪音方法：
- `pay()` 和 `getPayType()` 同等重要
- 可能选中 `_log()` 等内部方法
- 关键业务方法可能被忽略

#### 解决方案

**多维度评分模型**：

```python
# codeindex/symbol_scorer.py (新文件)

from dataclasses import dataclass
from typing import Optional
from .parser import Symbol

@dataclass
class ScoringContext:
    """符号评分上下文"""
    framework: str = "unknown"  # thinkphp, laravel, django, fastapi
    file_type: str = "unknown"  # controller, model, service
    total_symbols: int = 0

class SymbolImportanceScorer:
    """符号重要性评分器"""

    # 核心业务关键词（高分）
    CRITICAL_KEYWORDS = [
        "create", "update", "delete", "save", "remove",
        "process", "handle", "execute", "run",
        "pay", "order", "notify", "callback",
        "validate", "check", "verify",
        "send", "receive", "publish"
    ]

    # 噪音模式（低分）
    NOISE_PATTERNS = [
        "get", "set", "is", "has",  # Getter/Setter
        "_", "__",                   # 私有/魔术方法
        "log", "debug", "trace",     # 日志方法
        "dump", "print", "echo"      # 调试方法
    ]

    def __init__(self, context: Optional[ScoringContext] = None):
        self.context = context or ScoringContext()

    def score(self, symbol: Symbol) -> float:
        """
        计算符号重要性评分 (0-100)

        评分维度：
        - 可见性（0-20分）
        - 语义重要性（0-25分）
        - 文档完整性（0-15分）
        - 代码复杂度（0-20分）
        - 命名模式（-20-0分）
        """
        score = 50.0  # 基础分

        # 维度1：可见性（0-20分）
        score += self._score_visibility(symbol)

        # 维度2：语义重要性（0-25分）
        score += self._score_semantics(symbol)

        # 维度3：文档完整性（0-15分）
        score += self._score_documentation(symbol)

        # 维度4：代码复杂度（0-20分）
        score += self._score_complexity(symbol)

        # 维度5：命名模式（-20-0分）
        score += self._score_naming_pattern(symbol)

        # 维度6：类型加分（0-10分）
        score += self._score_symbol_type(symbol)

        return max(0.0, min(100.0, score))

    def _score_visibility(self, symbol: Symbol) -> float:
        """可见性评分"""
        sig_lower = symbol.signature.lower()

        if "public" in sig_lower:
            return 20.0
        elif "protected" in sig_lower:
            return 10.0
        elif "private" in sig_lower:
            return 0.0
        else:
            # Python 函数默认公开
            return 15.0 if not symbol.name.startswith("_") else 5.0

    def _score_semantics(self, symbol: Symbol) -> float:
        """语义重要性评分"""
        name_lower = symbol.name.lower()

        # 检查核心关键词
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in name_lower:
                return 25.0

        # 次要关键词
        secondary = ["find", "search", "list", "show", "render"]
        for keyword in secondary:
            if keyword in name_lower:
                return 15.0

        return 5.0

    def _score_documentation(self, symbol: Symbol) -> float:
        """文档完整性评分"""
        if not symbol.docstring:
            return 0.0

        doc_len = len(symbol.docstring)
        if doc_len > 200:
            return 15.0  # 详细文档
        elif doc_len > 50:
            return 10.0  # 简短文档
        else:
            return 5.0   # 最小文档

    def _score_complexity(self, symbol: Symbol) -> float:
        """代码复杂度评分"""
        lines = symbol.line_end - symbol.line_start

        if lines < 5:
            return 0.0   # 简单方法
        elif lines < 20:
            return 5.0
        elif lines < 50:
            return 10.0
        elif lines < 100:
            return 15.0
        else:
            return 20.0  # 复杂方法（可能是核心逻辑）

    def _score_naming_pattern(self, symbol: Symbol) -> float:
        """命名模式评分（可能是负分）"""
        name_lower = symbol.name.lower()

        # 检查噪音模式
        for pattern in self.NOISE_PATTERNS:
            if name_lower.startswith(pattern):
                return -20.0

        return 0.0

    def _score_symbol_type(self, symbol: Symbol) -> float:
        """符号类型加分"""
        if symbol.kind == "class":
            return 10.0  # 类定义很重要
        elif symbol.kind == "function":
            return 5.0   # 顶层函数较重要
        elif symbol.kind == "method":
            return 0.0   # 方法根据其他维度评分
        else:
            return 0.0


def rank_symbols_by_importance(
    symbols: list[Symbol],
    limit: int,
    context: Optional[ScoringContext] = None
) -> list[Symbol]:
    """
    根据重要性排序符号并返回前N个

    Args:
        symbols: 符号列表
        limit: 返回数量限制
        context: 评分上下文

    Returns:
        按重要性排序的符号列表（前limit个）
    """
    scorer = SymbolImportanceScorer(context)

    # 为每个符号计算评分
    scored_symbols = []
    for symbol in symbols:
        score = scorer.score(symbol)
        scored_symbols.append((score, symbol))

    # 按评分排序（降序）
    scored_symbols.sort(key=lambda x: x[0], reverse=True)

    # 返回前limit个符号
    return [symbol for _, symbol in scored_symbols[:limit]]
```

#### 集成到现有代码

```python
# smart_writer.py 修改

from .symbol_scorer import rank_symbols_by_importance, ScoringContext

class SmartWriter:
    def _filter_symbols(self, symbols: list[Symbol], file_path: Path) -> list[Symbol]:
        """使用重要性评分过滤符号"""

        # 创建评分上下文
        context = ScoringContext(
            framework=detect_framework(file_path.parent),
            file_type=self._detect_file_type(file_path),
            total_symbols=len(symbols)
        )

        # 使用重要性评分排序
        return rank_symbols_by_importance(
            symbols,
            limit=self.config.symbols.max_per_file,
            context=context
        )

    def _detect_file_type(self, path: Path) -> str:
        """检测文件类型"""
        name_lower = path.stem.lower()
        if "controller" in name_lower:
            return "controller"
        elif "model" in name_lower:
            return "model"
        elif "service" in name_lower:
            return "service"
        else:
            return "unknown"
```

#### 预期效果

**PayController.php (500个方法) 测试**：

| 方法 | 当前策略 | 评分策略 | 重要性评分 |
|------|---------|---------|-----------|
| `public function pay()` | 可能 | ✅ 必选 | 95 |
| `public function createOrder()` | 可能 | ✅ 必选 | 90 |
| `public function handleNotify()` | 可能 | ✅ 必选 | 85 |
| `protected function validateSign()` | 可能 | ✅ 选中 | 75 |
| `public function getPayType()` | ✅ 可能选中 | ❌ 不选 | 40 |
| `private function _log()` | ❌ 不选 | ❌ 不选 | 25 |

**关键API覆盖率**：70% → **95%** ✅

---

### 改进2：自适应符号提取策略 ⭐⭐⭐

#### 问题
固定的 `max_per_file=15` 对所有文件一视同仁：
- 小文件（100行）：15个符号足够
- 大文件（4000行）：15个符号远远不够

#### 解决方案

**基于文件大小的自适应策略**：

```python
# config.py 扩展

@dataclass
class AdaptiveSymbolConfig:
    """自适应符号提取配置"""
    enabled: bool = True

    # 分层阈值
    thresholds: dict[str, int] = field(default_factory=lambda: {
        "tiny": 100,      # <100行
        "small": 200,     # 100-200行
        "medium": 500,    # 200-500行
        "large": 1000,    # 500-1000行
        "xlarge": 2000,   # 1000-2000行
        "huge": 5000,     # >2000行
    })

    # 每层的符号限制
    limits: dict[str, int] = field(default_factory=lambda: {
        "tiny": 10,       # 小文件减少到10个
        "small": 15,      # 默认15个
        "medium": 30,     # 中等文件30个
        "large": 50,      # 大文件50个
        "xlarge": 80,     # 超大文件80个
        "huge": 120,      # 巨大文件120个
    })

    # 基于符号密度的调整因子
    density_adjustment: bool = True
    density_threshold: float = 0.05  # 符号/行数 > 5%


@dataclass
class IndexingConfig:
    # ... 现有配置 ...
    adaptive_symbols: AdaptiveSymbolConfig = field(default_factory=AdaptiveSymbolConfig)


# 新增函数
def calculate_adaptive_limit(
    file_lines: int,
    total_symbols: int,
    config: AdaptiveSymbolConfig
) -> int:
    """
    计算自适应符号限制

    Args:
        file_lines: 文件行数
        total_symbols: 文件中总符号数
        config: 自适应配置

    Returns:
        符号数量限制
    """
    if not config.enabled:
        return 15  # 回退到固定值

    # 根据文件大小确定基础限制
    if file_lines < config.thresholds["tiny"]:
        base_limit = config.limits["tiny"]
    elif file_lines < config.thresholds["small"]:
        base_limit = config.limits["small"]
    elif file_lines < config.thresholds["medium"]:
        base_limit = config.limits["medium"]
    elif file_lines < config.thresholds["large"]:
        base_limit = config.limits["large"]
    elif file_lines < config.thresholds["xlarge"]:
        base_limit = config.limits["xlarge"]
    else:
        base_limit = config.limits["huge"]

    # 基于符号密度调整
    if config.density_adjustment and file_lines > 0:
        density = total_symbols / file_lines
        if density > config.density_threshold:
            # 高密度文件，增加限制
            base_limit = int(base_limit * 1.5)

    return base_limit
```

#### 集成到现有代码

```python
# smart_writer.py 修改

def _generate_detailed(self, dir_path: Path, parse_results: list[ParseResult], ...):
    # ... 现有代码 ...

    for result in group_results:
        # 计算自适应限制
        file_lines = result.line_count if hasattr(result, 'line_count') else 0
        adaptive_limit = calculate_adaptive_limit(
            file_lines,
            len(result.symbols),
            self.config.adaptive_symbols
        )

        # 过滤并限制符号（使用自适应限制）
        symbols = self._filter_symbols(result.symbols)
        symbols = symbols[:adaptive_limit]  # 使用自适应限制

        # ... 现有渲染代码 ...
```

#### 配置示例

```yaml
# .codeindex.yaml

indexing:
  # 自适应符号提取
  adaptive_symbols:
    enabled: true

    # 自定义阈值（可选）
    thresholds:
      tiny: 100
      small: 200
      medium: 500
      large: 1000
      xlarge: 2000

    # 自定义限制（可选）
    limits:
      tiny: 10
      small: 15
      medium: 30
      large: 50
      xlarge: 80
      huge: 120

    # 密度调整
    density_adjustment: true
    density_threshold: 0.05
```

#### 预期效果

| 文件类型 | 行数 | 符号数 | 当前限制 | 自适应限制 | 提升 |
|---------|------|--------|---------|-----------|------|
| Helper.php | 80 | 12 | 15 | 10 | - |
| UserModel.php | 300 | 25 | 15 | 30 | +100% |
| PayController.php | 1500 | 120 | 15 | 80 | +433% |
| OrderService.php | 4000 | 500 | 15 | 120 | +700% |

**大文件信息完整性**：3% → **80%** ✅

---

### 改进3：配置优化 ⭐

#### 默认配置更新

```yaml
# DEFAULT_INDEXING 更新

DEFAULT_INDEXING = {
    "max_readme_size": 50 * 1024,  # 保持50KB

    # 自适应符号提取（新增）
    "adaptive_symbols": {
        "enabled": True,  # 默认启用
        "thresholds": {
            "tiny": 100,
            "small": 200,
            "medium": 500,
            "large": 1000,
            "xlarge": 2000,
        },
        "limits": {
            "tiny": 10,
            "small": 15,
            "medium": 30,
            "large": 50,
            "xlarge": 80,
            "huge": 120,
        },
        "density_adjustment": True,
        "density_threshold": 0.05,
    },

    "symbols": {
        "max_per_file": 15,  # 保留作为回退值
        "include_visibility": ["public", "protected"],
        "exclude_patterns": ["get*", "set*", "__*"],

        # 重要性评分（新增）
        "importance_scoring": {
            "enabled": True,  # 默认启用
            "min_score": 40,  # 最低评分阈值
        },
    },

    # ... 其他配置保持不变 ...
}
```

---

## 📋 Phase 2：评估体系（下周）

### 改进4：自动化评估框架 ⭐⭐

#### 目标
建立客观的评估标准，验证改进效果

#### 实现方案

```python
# tests/evaluation/test_navigation_efficiency.py

import pytest
import time
from pathlib import Path
from typing import Set

class NavigationEfficiencyTest:
    """导航效率评估"""

    @pytest.fixture
    def php_payment_project(self):
        """PHP 支付项目测试夹具"""
        return Path("/path/to/php_payment_project")

    def test_quick_locate_module(self, php_payment_project):
        """测试1：快速定位模块（权重：35%）"""
        start = time.time()

        # 任务：找到"支付回调处理"模块
        root_index = self._read_index(php_payment_project / "README_AI.md")

        # 验证：能否找到相关模块
        assert any(keyword in root_index for keyword in ["Pay", "NotifyApi", "Payment"])

        # 进入模块
        notify_index = self._read_index(php_payment_project / "NotifyApi" / "README_AI.md")

        # 验证：能否找到控制器
        assert "NotifyController" in notify_index

        elapsed = time.time() - start

        # 评分
        if elapsed < 10:
            score = 35
        elif elapsed < 20:
            score = 30
        elif elapsed < 30:
            score = 25
        else:
            score = 15

        assert score >= 25, f"定位耗时过长: {elapsed:.1f}秒"
        return score

    def test_symbol_coverage(self, php_payment_project):
        """测试2：符号覆盖率（权重：20%）"""
        # 提取实际的公共API
        actual_apis = self._extract_public_apis(php_payment_project)

        # 提取索引中的API
        indexed_apis = self._extract_indexed_apis(php_payment_project)

        # 计算覆盖率
        coverage = len(indexed_apis & actual_apis) / len(actual_apis)

        # 评分
        if coverage >= 0.95:
            score = 20
        elif coverage >= 0.85:
            score = 18
        elif coverage >= 0.75:
            score = 15
        else:
            score = 10

        assert coverage >= 0.85, f"覆盖率不足: {coverage:.1%}"
        return score

    def test_noise_ratio(self, php_payment_project):
        """测试3：噪音符号比例（权重：15%）"""
        indexed_symbols = self._extract_indexed_symbols(php_payment_project)

        # 识别噪音符号
        noise = [s for s in indexed_symbols if self._is_noise(s)]
        noise_ratio = len(noise) / len(indexed_symbols)

        # 评分
        if noise_ratio < 0.10:
            score = 15
        elif noise_ratio < 0.20:
            score = 12
        elif noise_ratio < 0.30:
            score = 8
        else:
            score = 0

        assert noise_ratio < 0.20, f"噪音过多: {noise_ratio:.1%}"
        return score

    def test_overall_score(self, php_payment_project):
        """综合评分"""
        scores = {
            "定位效率": self.test_quick_locate_module(php_payment_project),
            "符号覆盖": self.test_symbol_coverage(php_payment_project),
            "噪音控制": self.test_noise_ratio(php_payment_project),
        }

        total = sum(scores.values())

        print(f"\n导航效率评估报告：")
        for metric, score in scores.items():
            print(f"  {metric}: {score}分")
        print(f"  总分: {total}/70")

        assert total >= 60, f"总分不足: {total}/70"
        return total

    def _is_noise(self, symbol_name: str) -> bool:
        """判断是否为噪音符号"""
        noise_patterns = ["get", "set", "is", "has", "_", "log", "debug"]
        return any(symbol_name.lower().startswith(p) for p in noise_patterns)

    def _extract_public_apis(self, project_path: Path) -> Set[str]:
        """提取实际的公共API（从源码）"""
        # 实现省略
        pass

    def _extract_indexed_apis(self, project_path: Path) -> Set[str]:
        """提取索引中的API（从README_AI.md）"""
        # 实现省略
        pass

    def _read_index(self, path: Path) -> str:
        """读取索引文件"""
        return path.read_text(encoding="utf-8")
```

#### CLI 命令

```bash
# 运行评估测试
pytest tests/evaluation/ -v

# 对比改进前后
pytest tests/evaluation/ --baseline=before --compare=after

# 生成评估报告
pytest tests/evaluation/ --report=html
```

---

## 🔄 Phase 3：可选增强（未来）

### 改进5：双模式索引 ⭐（可选）

**适用场景**：大型模块（>100个符号或>20个文件）

```yaml
indexing:
  dual_mode:
    enabled: auto  # auto, always, never

    # 何时生成完整索引
    trigger_conditions:
      - total_symbols_gt: 100
      - file_count_gt: 20
      - directory_lines_gt: 5000

    # 输出文件
    quick_file: "README_AI.md"
    full_file: "README_AI_FULL.md"
```

**CLI 命令**：
```bash
# 生成完整索引
codeindex scan ./Application/Pay --full

# 查看建议
codeindex scan ./Application/Pay --suggest-full
```

### 改进6：框架感知评分 ⭐（可选）

**适用场景**：特定框架有明确的重要符号模式

```python
# framework_scorers.py (新文件)

class ThinkPHPScorer:
    """ThinkPHP 框架感知评分"""

    def adjust_score(self, symbol: Symbol, base_score: float) -> float:
        # Controller 的 public function = 路由动作（重要）
        if "Controller" in symbol.file_path and "public function" in symbol.signature:
            base_score += 20

        # Model 的 protected $table（重要）
        if "Model" in symbol.file_path and "$table" in symbol.name:
            base_score += 15

        return base_score
```

---

## 📈 预期效果总结

### 改进前 vs 改进后

| 指标 | 改进前 | 改进后 | 提升 |
|------|--------|--------|------|
| **大文件符号数** | 15 | 80-120 | **+433%-700%** |
| **关键API覆盖率** | 70% | 95% | **+36%** |
| **噪音符号比例** | 25% | <10% | **-60%** |
| **导航效率评分** | 72/100 | **92/100** | **+28%** |
| **Token消耗增加** | - | <20% | **可控** |

### 具体案例：PayController.php

| 项目 | 改进前 | 改进后 |
|------|--------|--------|
| 文件行数 | 4,000 | 4,000 |
| 总符号数 | 500 | 500 |
| 索引符号数 | 15 (3%) | 120 (24%) |
| 关键方法覆盖 | 60% | 98% |
| 噪音方法 | 5 (33%) | 2 (1.7%) |

---

## 🛠️ 实施计划

### Week 1：核心改进

**Day 1-2**：实现符号重要性评分
- [ ] 创建 `codeindex/symbol_scorer.py`
- [ ] 实现多维度评分算法
- [ ] 单元测试

**Day 3-4**：实现自适应符号提取
- [ ] 扩展 `config.py` 配置
- [ ] 实现 `calculate_adaptive_limit()`
- [ ] 集成到 `smart_writer.py`
- [ ] 单元测试

**Day 5**：验证和调优
- [ ] 用 PHP 支付项目验证
- [ ] 用 codeindex 自身验证
- [ ] 调整评分权重
- [ ] 更新文档

### Week 2：评估体系

**Day 6-8**：自动化评估框架
- [ ] 创建 `tests/evaluation/`
- [ ] 实现导航效率测试
- [ ] 实现符号覆盖率测试
- [ ] 实现噪音检测测试

**Day 9-10**：文档和发布
- [ ] 更新 CLAUDE.md
- [ ] 更新 README.md
- [ ] 编写迁移指南
- [ ] 发布 beta 版本

---

## 🎯 成功标准

### 必达目标（Phase 1）
- ✅ 大文件（>2000行）符号数 ≥ 80
- ✅ 关键API覆盖率 ≥ 90%
- ✅ 噪音符号比例 < 15%
- ✅ Token消耗增幅 < 20%
- ✅ 导航效率不降低

### 期望目标（Phase 2）
- ✅ 自动化评估测试通过率 100%
- ✅ PHP 支付项目评分 ≥ 90/100
- ✅ 用户反馈积极

---

## 🔧 配置兼容性

### 向后兼容

**现有配置继续有效**：
```yaml
# 旧配置（仍然有效）
indexing:
  symbols:
    max_per_file: 15
```

**新配置（可选启用）**：
```yaml
# 新配置（可选）
indexing:
  adaptive_symbols:
    enabled: true  # 覆盖 max_per_file

  symbols:
    max_per_file: 15  # 作为回退值
    importance_scoring:
      enabled: true
```

### 配置优先级

1. **adaptive_symbols.enabled=true** → 使用自适应策略
2. **adaptive_symbols.enabled=false** → 使用固定 max_per_file
3. **importance_scoring.enabled=true** → 使用重要性评分排序
4. **importance_scoring.enabled=false** → 使用原有过滤逻辑

---

## 📝 下一步行动

### 立即行动
1. ✅ 阅读本文档，确认改进方向
2. ✅ 决定是否实施 Phase 1（推荐）
3. ✅ 准备测试项目（PHP 支付项目）

### 本周任务
1. 实现符号重要性评分
2. 实现自适应符号提取
3. 验证改进效果

### 反馈收集
- 改进后的索引质量如何？
- Token 消耗是否可接受？
- 是否需要双模式索引？
- 是否需要框架感知？

---

## 💬 FAQ

**Q1: 改进后 Token 消耗会增加多少？**
A: 预计增加 <20%。大文件符号增加，但通过重要性评分减少噪音，整体可控。

**Q2: 现有配置会失效吗？**
A: 不会。新配置是可选的，现有配置继续有效。

**Q3: 如何禁用新特性？**
A: 设置 `adaptive_symbols.enabled: false` 和 `importance_scoring.enabled: false`

**Q4: 改进后索引文件会变大吗？**
A: 大文件的索引会变大，但仍控制在50KB以内（通过智能截断）。

**Q5: 何时需要完整索引（README_AI_FULL.md）？**
A: 只有大型模块（>100符号或>20文件）才建议生成完整索引。

---

## 🎉 总结

通过**符号重要性评分**和**自适应符号提取**两个核心改进：
- ✅ 大文件信息完整性提升 **400%-700%**
- ✅ 关键API覆盖率提升 **36%**
- ✅ 保持快速导航的核心价值
- ✅ Token消耗增幅可控（<20%）

**建议立即实施 Phase 1，快速见效！**
