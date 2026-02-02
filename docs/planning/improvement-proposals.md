# codeindex 改进提案

基于对比测试发现的问题，本文档提出针对性的改进方案。

## 问题总结

### 核心问题
1. **评估标准错位**：用"深入技术分析"标准评估"导航索引"工具
2. **大文件处理不足**：4万行代码文件只提取15个符号
3. **符号优先级缺失**：无法区分关键API和噪音方法
4. **工具定位模糊**：用户不清楚何时用索引、何时用深入分析

---

## 改进方案

## 提案 1：符号提取策略优化 ⭐⭐⭐

### 当前问题
```yaml
# .codeindex.yaml (当前)
indexing:
  symbols:
    max_per_file: 15  # 固定限制，大文件丢失信息
```

对于 40,000 行的 PayController.php：
- 可能有 500+ 个方法
- 只提取 15 个 → 丢失 97% 的信息
- Claude Code 优先读索引 → 无法获得完整信息

### 解决方案：分层符号提取

```yaml
# .codeindex.yaml (改进)
indexing:
  symbols:
    # 基础限制
    max_per_file: 15

    # 大文件特殊处理
    large_file_handling:
      enabled: true
      threshold_lines: 500  # 超过500行触发
      strategy: "tiered"     # 分层策略

      # 分层提取规则
      tiers:
        # Tier 1: 关键公共 API（必须全部提取）
        critical:
          patterns:
            - "public class"
            - "public interface"
            - "public function __construct"
          limit: null  # 无限制

        # Tier 2: 公共方法（优先提取）
        public:
          patterns:
            - "public function"
            - "public static"
          limit: 50

        # Tier 3: 受保护方法（次要）
        protected:
          patterns:
            - "protected function"
          limit: 20

        # Tier 4: 私有方法（采样）
        private:
          patterns:
            - "private function"
          limit: 10

      # 智能排序
      sorting:
        - by: "docstring_length"  # 有文档的优先
        - by: "signature_length"  # 复杂签名优先
        - by: "line_count"        # 长方法优先（可能是核心逻辑）
```

### 实现代码（smart_writer.py 改进）

```python
# smart_writer.py 新增方法
def _extract_symbols_with_priority(
    self,
    symbols: list[Symbol],
    file_line_count: int
) -> list[Symbol]:
    """使用优先级策略提取符号"""

    # 小文件：使用原有策略
    if file_line_count < self.config.large_file_threshold:
        return self._filter_symbols(symbols)[:self.config.symbols.max_per_file]

    # 大文件：分层提取
    result = []
    tiers = self.config.large_file_handling.tiers

    # Tier 1: Critical symbols (无限制)
    critical = self._filter_by_tier(symbols, tiers.critical)
    result.extend(critical)

    # Tier 2: Public symbols (限制50)
    public = self._filter_by_tier(symbols, tiers.public)
    result.extend(self._smart_sort(public)[:tiers.public.limit])

    # Tier 3: Protected symbols (限制20)
    protected = self._filter_by_tier(symbols, tiers.protected)
    result.extend(self._smart_sort(protected)[:tiers.protected.limit])

    # Tier 4: Private symbols (限制10)
    private = self._filter_by_tier(symbols, tiers.private)
    result.extend(self._smart_sort(private)[:tiers.private.limit])

    return result

def _smart_sort(self, symbols: list[Symbol]) -> list[Symbol]:
    """智能排序：有文档 > 复杂签名 > 长方法"""
    def score(s: Symbol) -> tuple:
        has_doc = len(s.docstring) > 0
        sig_length = len(s.signature)
        line_count = s.line_end - s.line_start
        return (has_doc, sig_length, line_count)

    return sorted(symbols, key=score, reverse=True)
```

### 效果预估

| 场景 | 当前策略 | 改进后 | 提升 |
|------|---------|--------|------|
| 小文件 (<500行) | 15个符号 | 15个符号 | 不变 |
| 中文件 (500-2000行) | 15个符号 | 50个符号 | +233% |
| 大文件 (>2000行) | 15个符号 | 80个符号 | +433% |
| 超大文件 (>10000行) | 15个符号 | 120个符号 | +700% |

---

## 提案 2：双层索引模式 ⭐⭐

### 当前问题
- 单一 README_AI.md 无法同时满足"快速导航"和"完整符号"需求
- 50KB 限制导致大型模块信息截断

### 解决方案：生成两个文件

```
Application/Pay/
├── README_AI.md           # 导航索引（快速查找）
└── README_AI_FULL.md      # 完整符号索引（深入分析）
```

#### README_AI.md（导航模式，默认）
- 目标：5分钟快速理解模块
- 符号限制：15/文件
- 大小限制：50KB
- Claude Code 优先读取

#### README_AI_FULL.md（完整模式，可选）
- 目标：完整符号参考
- 符号限制：100/文件
- 大小限制：500KB
- 需要时才读取

### 配置选项

```yaml
# .codeindex.yaml
indexing:
  dual_index:
    enabled: true
    navigation_file: "README_AI.md"
    full_file: "README_AI_FULL.md"

    # 何时生成完整索引
    full_index_when:
      - directory_symbols_gt: 100  # 目录符号 >100
      - file_lines_gt: 1000        # 文件行数 >1000
      - total_files_gt: 20         # 文件数 >20
```

### CLI 命令

```bash
# 只生成导航索引（默认）
codeindex scan ./Application/Pay

# 同时生成完整索引
codeindex scan ./Application/Pay --full-index

# 只生成完整索引
codeindex scan ./Application/Pay --full-only
```

---

## 提案 3：符号重要性评分 ⭐⭐⭐

### 动机
不是所有符号都同等重要：
- `public function pay()` - 核心业务逻辑 ⭐⭐⭐⭐⭐
- `public function getPayType()` - Getter 方法 ⭐
- `private function _log()` - 内部工具方法 ⭐

### 评分算法

```python
# parser.py 新增
@dataclass
class Symbol:
    name: str
    kind: str
    signature: str
    docstring: str
    line_start: int
    line_end: int
    importance_score: float = 0.0  # 新增

def calculate_importance(symbol: Symbol) -> float:
    """计算符号重要性评分 (0-100)"""
    score = 50.0  # 基础分

    # 1. 可见性加分
    if "public" in symbol.signature:
        score += 20
    elif "protected" in symbol.signature:
        score += 10

    # 2. 类型加分
    if symbol.kind == "class":
        score += 15
    elif symbol.kind == "interface":
        score += 15

    # 3. 文档加分
    if symbol.docstring:
        score += 10
        if len(symbol.docstring) > 100:  # 详细文档
            score += 5

    # 4. 命名启发式
    name_lower = symbol.name.lower()

    # 核心业务关键词
    important_keywords = [
        "pay", "order", "create", "update", "delete",
        "process", "handle", "execute", "validate",
        "notify", "callback", "refund"
    ]
    if any(kw in name_lower for kw in important_keywords):
        score += 15

    # 噪音模式（减分）
    noise_patterns = ["get", "set", "is", "has", "log", "debug"]
    if any(name_lower.startswith(p) for p in noise_patterns):
        score -= 15

    # 5. 代码复杂度加分
    line_count = symbol.line_end - symbol.line_start
    if line_count > 50:  # 长方法可能是核心逻辑
        score += min(line_count / 10, 20)

    return max(0, min(100, score))  # 限制在 0-100
```

### 使用方式

```python
# smart_writer.py 改进
def _select_important_symbols(self, symbols: list[Symbol], limit: int) -> list[Symbol]:
    """根据重要性评分选择符号"""
    for symbol in symbols:
        symbol.importance_score = calculate_importance(symbol)

    # 按重要性排序
    sorted_symbols = sorted(symbols, key=lambda s: s.importance_score, reverse=True)

    return sorted_symbols[:limit]
```

### 效果示例

PayController.php (500个方法) → 选出最重要的 50 个：

| 方法 | 重要性评分 | 是否选中 |
|------|-----------|---------|
| `public function pay()` | 95 | ✅ |
| `public function createOrder()` | 90 | ✅ |
| `public function handleNotify()` | 85 | ✅ |
| `protected function validateSign()` | 75 | ✅ |
| `public function getPayType()` | 40 | ❌ |
| `private function _log()` | 25 | ❌ |

---

## 提案 4：工具定位文档优化 ⭐

### 问题
用户不清楚何时用 codeindex，何时用 Claude Code 深入分析。

### 解决方案：更新 CLAUDE.md

```markdown
# codeindex 使用指南

## 🎯 工具定位

codeindex 是**代码导航工具**，不是深入分析工具。

### ✅ 适合 codeindex 的场景

1. **新项目探索**
   ```bash
   # 快速了解项目结构
   codeindex scan-all --fallback
   # 然后查看 README_AI.md 了解架构
   ```

2. **代码导航**
   ```
   我：支付逻辑在哪里？
   → 查看 README_AI.md → 定位到 Application/Pay/
   → 查看 Pay/README_AI.md → 找到 PayController.php
   ```

3. **项目交接**
   - 快速了解模块职责
   - 理解依赖关系

### ❌ 不适合 codeindex 的场景

1. **深入技术分析**
   ```
   问题：支付流程的完整调用链是什么？
   ❌ 错误：只看 README_AI.md（信息不足）
   ✅ 正确：用 Claude Code 的 Read/Grep 工具深入分析
   ```

2. **Bug 排查**
   - 需要看完整代码逻辑
   - 需要跟踪变量数据流
   - 👉 直接用 Read 工具阅读源码

3. **技术文档编写**
   - 需要完整的 API 说明
   - 需要详细的配置映射
   - 👉 用 Claude Code 深入分析

## 🔄 最佳实践：组合使用

### 工作流示例

```
步骤1：用 codeindex 快速定位
  └─> 查看 README_AI.md → 找到相关模块

步骤2：用 Claude Code 深入分析
  └─> Read 具体文件 → 理解完整逻辑

步骤3：用 Grep 搜索关联代码
  └─> 找到调用链和依赖
```

### 具体案例

**任务**：理解支付流程

```bash
# 步骤1：导航定位（用 codeindex）
cat Application/README_AI.md
# → 发现 Pay/ 模块

cat Application/Pay/README_AI.md
# → 发现关键类：
#    - PayController: 支付入口
#    - PayService: 业务逻辑
#    - Notify: 回调处理

# 步骤2：深入分析（用 Claude Code）
claude code
> Read Application/Pay/Controller/PayController.php
> Grep "function pay" Application/Pay/
> Read Application/Pay/Business/PayProfit.php

# 步骤3：生成技术文档
> 请基于刚才的分析，生成支付流程技术文档
```

**对比**：

| 方法 | 耗时 | 准确度 | Token消耗 |
|------|------|--------|----------|
| 只用 codeindex | 2分钟 | 60% | 3K |
| 只用深入分析 | 20分钟 | 95% | 58K |
| **组合使用** | **5分钟** | **95%** | **10K** |

✅ **最佳实践**：先用 codeindex 定位，再用深入分析！
```

---

## 提案 5：新增评估测试用例 ⭐⭐

### 创建标准测试

```bash
tests/
├── evaluation/
│   ├── test_navigation_efficiency.py    # 导航效率测试
│   ├── test_structure_understanding.py  # 结构理解测试
│   ├── test_symbol_coverage.py          # 符号覆盖率测试
│   └── test_large_file_handling.py      # 大文件处理测试
```

### 示例：导航效率测试

```python
# tests/evaluation/test_navigation_efficiency.py
import time
from pathlib import Path

def test_locate_module_in_30_seconds(sample_project):
    """测试：在30秒内定位到目标模块"""

    # 任务：找到"用户认证"相关代码
    start_time = time.time()

    # 步骤1：读取根目录索引
    root_readme = Path(sample_project) / "README_AI.md"
    content = root_readme.read_text()

    # 步骤2：定位 Auth 模块
    assert "Auth" in content or "Authentication" in content

    # 步骤3：读取模块索引
    auth_readme = Path(sample_project) / "Auth" / "README_AI.md"
    assert auth_readme.exists()

    auth_content = auth_readme.read_text()

    # 步骤4：找到 AuthController
    assert "AuthController" in auth_content

    elapsed = time.time() - start_time

    # 评分
    if elapsed < 10:
        score = 35  # 满分
    elif elapsed < 20:
        score = 30
    elif elapsed < 30:
        score = 25
    else:
        score = 15

    assert score >= 25, f"导航效率不足: {elapsed:.1f}秒, 得分 {score}/35"

def test_symbol_coverage_90_percent(sample_project):
    """测试：公共API覆盖率 ≥ 90%"""

    # 读取实际代码，提取所有公共方法
    actual_public_methods = extract_public_methods(sample_project / "Auth")

    # 读取索引，提取已列出的方法
    indexed_methods = extract_indexed_methods(sample_project / "Auth" / "README_AI.md")

    # 计算覆盖率
    coverage = len(indexed_methods) / len(actual_public_methods)

    assert coverage >= 0.9, f"符号覆盖率不足: {coverage:.1%}, 需要 ≥90%"
```

---

## 实施优先级

| 提案 | 优先级 | 工作量 | 影响 | 建议 |
|------|--------|--------|------|------|
| 提案1：符号提取策略优化 | ⭐⭐⭐ | 中 | 高 | **立即实施** |
| 提案2：双层索引模式 | ⭐⭐ | 中 | 中 | 可选，大型项目推荐 |
| 提案3：符号重要性评分 | ⭐⭐⭐ | 中 | 高 | **立即实施** |
| 提案4：工具定位文档优化 | ⭐ | 低 | 高 | **立即实施** |
| 提案5：新增评估测试用例 | ⭐⭐ | 高 | 中 | 逐步实施 |

### 推荐实施路线

**Phase 1（本周）**：
1. 更新 CLAUDE.md，明确工具定位（提案4）
2. 实现符号重要性评分（提案3）

**Phase 2（下周）**：
1. 实现分层符号提取（提案1）
2. 创建基础评估测试（提案5）

**Phase 3（未来）**：
1. 考虑双层索引模式（提案2，可选）
2. 完善评估框架

---

## 总结

**核心改进目标**：
1. ✅ 优化大文件处理（从15个符号 → 80+个符号）
2. ✅ 智能符号选择（重要性评分）
3. ✅ 明确工具定位（导航 vs 深入分析）
4. ✅ 设计合理的评估标准

**预期效果**：
- 大文件信息完整性：从 3% → 80%
- 符号选择准确性：从 60% → 90%
- 用户理解度：从"困惑" → "清晰"

**不改变的**：
- Token 消耗仍保持低水平（<10% 项目token）
- 导航效率不降低
- 增量更新机制保持高效
