# AI Enhancement 终极方案：多轮对话 + 知识图谱

## 🎯 核心定位重新审视

### codeindex 的真正价值

**不是**: 压缩prompt、节省API成本
**是**: 为超大规模项目构建**高质量索引**，作为AI理解代码的入口

| 场景 | codeindex的职责 | AI/LLM的职责 |
|------|----------------|--------------|
| 初次理解项目 | 提供结构化概览 | 基于索引深入探索 |
| 定位具体功能 | 导航到相关模块 | 使用grep查看细节 |
| 理解架构演进 | 展示历史变更 | 分析代码diff |
| 增量更新 | 更新变更部分的索引 | 理解变更影响 |

**关键洞察**:
- ✅ 一次性投入API成本，生成**高质量**索引
- ✅ 长期收益：每次使用都节省大量探索时间
- ✅ 索引是**导航地图**，不是代码的"压缩版"

---

## 💡 终极方案：多轮对话架构

### 为什么多轮对话是最佳选择？

既然不考虑API成本，我们应该追求**最高质量**的索引生成：

| 方案 | API调用 | Prompt大小 | 生成质量 | 适用场景 |
|------|---------|-----------|----------|----------|
| 单轮压缩 | 1次 | 20-50KB | ⭐⭐⭐ | 小文件 |
| 单轮分层 | 1次 | 15-30KB | ⭐⭐⭐⭐ | 中等文件 |
| **多轮对话** | 3-5次 | <20KB/轮 | ⭐⭐⭐⭐⭐ | **所有文件** |

**优势**:
1. **无Prompt限制** - 每轮都在安全范围内
2. **逐步聚焦** - 从宏观到微观，AI有充分思考空间
3. **高质量输出** - 每轮都有明确目标，生成更精准
4. **可扩展** - 可以根据文件复杂度动态调整轮数

---

## 🏗️ 多轮对话架构设计

### 第1轮：架构扫描（Architecture Scan）

**目标**: 理解文件/目录的整体结构和职责

**Input**:
```python
# 极简prompt（只有统计信息）
prompt_round1 = f"""
## Directory: {dir_path}

### Statistics
- Files: {file_count}
- Total Symbols: {total_symbols}
  - Classes: {class_count}
  - Functions: {function_count}
  - Methods: {method_count}

### File List
{format_file_list_simple(parse_results)}
# 只有文件名和符号数，无详细信息

## Task
Based on ONLY the statistics and file names above, provide:

1. **Primary Purpose** (1-2 sentences)
   What is this module/directory responsible for?

2. **Component Categories**
   Group the files into 3-5 logical categories (e.g., "Data Access", "Business Logic", "API Controllers")

3. **Architectural Pattern**
   What design pattern is used? (MVC, Repository, Service Layer, etc.)

Output format:
# Architecture Overview
[Your analysis]
"""
```

**Output** (Round 1):
```markdown
# Architecture Overview

## Primary Purpose
This is a goods management module responsible for CRUD operations,
pricing logic, inventory control, and promotion handling.

## Component Categories
1. **Data Access** (5 files)
   - GoodsRepository, StockRepository, PriceHistoryRepository
2. **Business Logic** (3 files)
   - OperateGoods, PriceCalculator, StockManager
3. **API Controllers** (2 files)
   - GoodsController, GoodsApiController

## Architectural Pattern
Service Layer pattern with Repository for data access
```

**关键**: 这一轮AI**不需要看任何代码细节**，只基于统计信息推断架构。

---

### 第2轮：核心组件识别（Core Component Identification）

**目标**: 识别最重要的1-3个核心组件，深入分析

**Input**:
```python
# 基于第1轮的结果，选择核心文件
core_files = identify_core_files(parse_results, round1_output)
# 如：OperateGoods.class.php（符号最多，业务逻辑核心）

prompt_round2 = f"""
## Previous Analysis
{round1_output}

## Core Component: {core_files[0].name}

### Symbol Overview
{format_symbols_grouped(core_files[0])}
# 按职责分组的符号列表（CRUD、Price、Stock等）

### Top-10 Key Methods
{format_top_symbols_detail(core_files[0], limit=10)}
# 只有top-10的详细信息（签名+docstring）

## Task
For this core component, provide:

1. **Responsibilities**
   What are the main responsibilities of this class?

2. **Method Groups**
   Organize methods into functional groups with brief descriptions

3. **Key Workflows**
   Identify 2-3 most important workflows (method call chains)

4. **Dependencies**
   What other components does it depend on?
"""
```

**Output** (Round 2):
```markdown
# Core Component: OperateGoods

## Responsibilities
1. Goods CRUD operations with complex business rules
2. Price management with history tracking and event triggering
3. Stock validation and reservation
4. Promotion application and validation

## Method Groups

### CRUD Operations (8 methods)
- `getGoodsInfo()` - Main entry point for retrieving goods with user context
- `updateGoodsInfo()` - Atomic update with validation
- `deleteGoods()` - Soft delete with cascading effects

### Price Management (5 methods)
- `setGoodsPrice()` - **Critical workflow**: validates → records history → triggers events → clears cache
- `getGoodsPriceHistory()` - Audit trail
- `calculatePromotionPrice()` - Complex promotion logic

### Stock Control (4 methods)
- `checkStock()` - **High centrality**: called by 8 other methods
- `reserveStock()` - Transaction-safe stock reservation

## Key Workflows

### 1. Order Creation Flow
```
processOrder()
  → checkStock()
  → getGoodsStatus()
    → calculatePromotionPrice()
  → reserveStock()
```

### 2. Price Update Flow
```
setGoodsPrice()
  → validatePriceData()
  → recordPriceHistory()
  → triggerPriceChangedEvent()
  → clearRelatedCache()
```

## Dependencies
- GoodsRepository (data access)
- StockManager (stock validation)
- EventDispatcher (price change events)
- CacheManager (cache invalidation)
```

**关键**: AI现在开始关注**调用关系**和**工作流**，这是架构理解的核心。

---

### 第3轮：组件关系图谱（Component Relationship Mapping）

**目标**: 理解组件之间的协作关系

**Input**:
```python
# 提供所有组件的摘要 + 依赖关系
prompt_round3 = f"""
## Previous Analysis
{round1_output}
{round2_output}

## All Components Summary
{format_all_components_summary(parse_results)}
# 每个文件的1-2句话描述 + 依赖列表

## Import Relationships
{format_import_graph(parse_results)}
# 谁import了谁

## Task
Based on the component summaries and relationships, provide:

1. **Data Flow**
   How does data flow through this module? (e.g., Controller → Service → Repository)

2. **Critical Paths**
   What are the 2-3 most critical execution paths?

3. **Integration Points**
   How does this module interact with external systems?

4. **Architectural Concerns**
   Any circular dependencies, tight coupling, or other issues?
"""
```

**Output** (Round 3):
```markdown
# Component Relationships

## Data Flow
```
GoodsController (HTTP)
  → OperateGoods (Business Logic)
    → GoodsRepository (Data Access)
      → Database
    → CacheManager (Caching)
      → Redis
```

## Critical Paths

### 1. Goods Retrieval Path (High Traffic)
- Entry: `GoodsController::show()`
- Logic: `OperateGoods::getGoodsInfo()`
- Data: `GoodsRepository::findById()` + `CacheManager::get()`
- Note: Cache-first strategy, 95% hit rate

### 2. Price Update Path (High Impact)
- Entry: `GoodsController::updatePrice()`
- Logic: `OperateGoods::setGoodsPrice()`
- Side Effects: Event dispatch → Cache invalidation → Price history
- Caution: Non-atomic, potential race condition

## Integration Points
- **Event System**: Publishes `PriceChangedEvent`, `StockReservedEvent`
- **Cache Layer**: Redis for goods info, 5-minute TTL
- **Message Queue**: Asynchronous stock sync to warehouse system

## Architectural Concerns
⚠️ **Potential Issue**: `OperateGoods` directly depends on `CacheManager`
   - Violates single responsibility
   - Suggest: Extract caching to Repository layer
```

**关键**: 这一轮AI开始发现**架构问题**和**优化建议**。

---

### 第4轮：文档合成与精炼（Documentation Synthesis）

**目标**: 合并前3轮的结果，生成最终README

**Input**:
```python
prompt_round4 = f"""
## Context
You have analyzed this module through 3 rounds:

### Round 1: Architecture Overview
{round1_output}

### Round 2: Core Component Analysis
{round2_output}

### Round 3: Component Relationships
{round3_output}

## Task
Synthesize a final README_AI.md that:

1. Starts with a clear **Purpose** statement
2. Describes the **Architecture** (pattern, layers, data flow)
3. Lists **Key Components** with their roles
4. Documents **Critical Workflows** (2-3 most important)
5. Shows **Dependencies** (what this module consumes/provides)
6. Includes **Gotchas** (performance notes, known issues)

Requirements:
- Use markdown tables for structured data
- Keep it concise (50-100 lines)
- Focus on WHAT and WHY, not HOW
- Assume the reader is a new developer onboarding
"""
```

**Output** (Final README):
```markdown
# README_AI.md - Goods Management Module

## Purpose
This module handles all goods-related operations including CRUD, pricing,
inventory management, and promotion logic. It serves as the core business
layer for the e-commerce platform's product catalog.

## Architecture

**Pattern**: Service Layer with Repository

```
┌─────────────────────────────────────────┐
│  GoodsController (HTTP API)             │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  OperateGoods (Business Logic)          │
│  - Price management                     │
│  - Stock validation                     │
│  - Promotion application                │
└─────┬───────────────────┬───────────────┘
      │                   │
      ▼                   ▼
┌─────────────┐     ┌─────────────┐
│ Repository  │     │ CacheManager│
│ (Data)      │     │ (Redis)     │
└─────────────┘     └─────────────┘
```

## Key Components

| Component | Responsibility | Key Methods |
|-----------|----------------|-------------|
| **OperateGoods** | Core business logic | `getGoodsInfo()`, `setGoodsPrice()` |
| GoodsRepository | Data persistence | `findById()`, `update()` |
| StockManager | Inventory control | `checkStock()`, `reserveStock()` |
| PriceCalculator | Promotion logic | `calculatePromotionPrice()` |

## Critical Workflows

### 1. Goods Retrieval (High Traffic, Cache-First)
```
HTTP Request → GoodsController::show()
  → CacheManager::get() (95% hit rate)
  → OperateGoods::getGoodsInfo()
    → GoodsRepository::findById()
```

### 2. Price Update (High Impact, Eventual Consistency)
```
HTTP Request → GoodsController::updatePrice()
  → OperateGoods::setGoodsPrice()
    → Validate price range
    → Record price history
    → Trigger PriceChangedEvent
    → Clear cache (async)
```

**⚠️ Note**: Price updates are not atomic. Brief inconsistency possible during cache invalidation.

## Dependencies

### Consumes
- GoodsRepository (data access)
- EventDispatcher (for price/stock events)
- CacheManager (Redis caching)

### Provides
- RESTful API for goods management
- Events: `PriceChangedEvent`, `StockReservedEvent`
- Cached goods data (5-min TTL)

## Gotchas

### Performance
- **Cache Strategy**: Cache-first with 5-minute TTL. Cold cache can cause DB load spike.
- **Stock Check**: `checkStock()` is called frequently. Consider moving to read-replica.

### Known Issues
- ⚠️ **Race Condition**: Concurrent price updates may cause history inconsistency
- ⚠️ **Tight Coupling**: OperateGoods directly depends on CacheManager (should be in Repository)

### Future Improvements
- [ ] Extract caching logic to Repository layer
- [ ] Add optimistic locking for price updates
- [ ] Implement stock reservation expiry mechanism
```

**关键**: 最终文档包含了：
- ✅ 清晰的架构图
- ✅ 关键工作流
- ✅ 性能注意事项
- ✅ 已知问题和改进建议

这是**单轮对话无法达到的质量**！

---

## 🔧 实现架构

### 核心接口设计

```python
# src/codeindex/multi_turn_enhancer.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TurnResult:
    """单轮对话结果"""
    turn_number: int
    prompt: str
    response: str
    tokens_used: int
    duration: float

@dataclass
class EnhancementContext:
    """增强上下文（跨轮共享）"""
    dir_path: Path
    parse_results: List[ParseResult]
    previous_turns: List[TurnResult]

    def get_round_output(self, turn: int) -> str:
        """获取指定轮次的输出"""
        return self.previous_turns[turn - 1].response if turn <= len(self.previous_turns) else ""

class MultiTurnEnhancer:
    """多轮对话增强器"""

    def __init__(self, config: Config):
        self.config = config
        self.ai_command = config.ai_command
        self.max_turns = 4  # 默认4轮

    def enhance(self, dir_path: Path, parse_results: List[ParseResult]) -> EnhancementResult:
        """执行多轮增强"""

        context = EnhancementContext(
            dir_path=dir_path,
            parse_results=parse_results,
            previous_turns=[]
        )

        # 执行各轮对话
        console.print(f"[cyan]Multi-turn enhancement for {dir_path.name}...[/cyan]")

        for turn in range(1, self.max_turns + 1):
            console.print(f"[dim]  Turn {turn}/{self.max_turns}...[/dim]")

            # 生成prompt
            prompt = self._generate_prompt(turn, context)

            # 调用AI
            result = invoke_ai_cli(self.ai_command, prompt, timeout=180)

            if not result.success:
                # 记录失败，但继续
                console.print(f"[yellow]  Turn {turn} failed: {result.error}[/yellow]")
                continue

            # 记录结果
            turn_result = TurnResult(
                turn_number=turn,
                prompt=prompt,
                response=clean_ai_output(result.output),
                tokens_used=len(prompt) + len(result.output),  # 粗略估算
                duration=result.duration
            )
            context.previous_turns.append(turn_result)

            console.print(f"[green]  ✓ Turn {turn} complete ({turn_result.tokens_used} tokens)[/green]")

        # 返回最后一轮的结果作为最终README
        if context.previous_turns:
            final_output = context.previous_turns[-1].response
            return EnhancementResult(
                success=True,
                output=final_output,
                metadata={
                    "turns": len(context.previous_turns),
                    "total_tokens": sum(t.tokens_used for t in context.previous_turns),
                    "total_duration": sum(t.duration for t in context.previous_turns)
                }
            )
        else:
            return EnhancementResult(success=False, error="All turns failed")

    def _generate_prompt(self, turn: int, context: EnhancementContext) -> str:
        """根据轮次生成prompt"""

        if turn == 1:
            return self._prompt_round1_architecture_scan(context)
        elif turn == 2:
            return self._prompt_round2_core_component(context)
        elif turn == 3:
            return self._prompt_round3_relationships(context)
        elif turn == 4:
            return self._prompt_round4_synthesis(context)
        else:
            raise ValueError(f"Unsupported turn: {turn}")

    def _prompt_round1_architecture_scan(self, context: EnhancementContext) -> str:
        """第1轮：架构扫描"""

        # 统计信息
        total_symbols = sum(len(r.symbols) for r in context.parse_results)
        class_count = sum(1 for r in context.parse_results for s in r.symbols if s.kind == "class")
        function_count = sum(1 for r in context.parse_results for s in r.symbols if s.kind == "function")
        method_count = total_symbols - class_count - function_count

        # 文件列表（简化）
        file_list = "\n".join([
            f"- {r.path.name} ({len(r.symbols)} symbols)"
            for r in context.parse_results
        ])

        return f"""
## Directory: {context.dir_path}

### Statistics
- Files: {len(context.parse_results)}
- Total Symbols: {total_symbols}
  - Classes: {class_count}
  - Functions: {function_count}
  - Methods: {method_count}

### File List
{file_list}

## Task
Based on ONLY the statistics and file names above, provide:

1. **Primary Purpose** (1-2 sentences)
2. **Component Categories** (3-5 logical groups)
3. **Architectural Pattern** (MVC, Repository, Service Layer, etc.)

Output format: Markdown with clear sections.
"""

    def _prompt_round2_core_component(self, context: EnhancementContext) -> str:
        """第2轮：核心组件分析"""

        round1_output = context.get_round_output(1)

        # 识别核心文件（符号最多的文件）
        core_file = max(context.parse_results, key=lambda r: len(r.symbols))

        # 分组符号
        grouped = group_symbols_by_responsibility(core_file.symbols)
        grouped_text = "\n".join([
            f"**{group}** ({len(symbols)} methods)\n" +
            "\n".join([f"  - {s.name}()" for s in symbols[:5]])  # 只列前5个
            for group, symbols in grouped.items()
        ])

        # Top-10详细信息
        scorer = SymbolImportanceScorer()
        top_symbols = sorted(
            core_file.symbols,
            key=lambda s: scorer.score(s),
            reverse=True
        )[:10]

        top_detail = "\n".join([
            f"### {s.name}()\n`{s.signature}`\n{s.docstring[:200] if s.docstring else 'No description'}..."
            for s in top_symbols
        ])

        return f"""
## Previous Analysis
{round1_output}

## Core Component: {core_file.path.name}

### Symbol Groups
{grouped_text}

### Top-10 Key Methods
{top_detail}

## Task
For this core component, provide:

1. **Responsibilities** (main responsibilities)
2. **Method Groups** (organize methods with descriptions)
3. **Key Workflows** (2-3 important method call chains)
4. **Dependencies** (what other components it needs)

Output format: Markdown with code blocks for workflows.
"""

    def _prompt_round3_relationships(self, context: EnhancementContext) -> str:
        """第3轮：组件关系"""

        round1_output = context.get_round_output(1)
        round2_output = context.get_round_output(2)

        # 所有组件摘要
        components_summary = "\n".join([
            f"- **{r.path.name}**: {len(r.symbols)} symbols"
            for r in context.parse_results
        ])

        # 导入关系
        import_graph = "\n".join([
            f"- {r.path.name} imports: {', '.join([imp.module for imp in r.imports[:5]])}"
            for r in context.parse_results if r.imports
        ])

        return f"""
## Previous Analysis

### Round 1: Architecture
{round1_output}

### Round 2: Core Component
{round2_output}

## All Components
{components_summary}

## Import Relationships
{import_graph}

## Task
Based on the component summaries and relationships:

1. **Data Flow** (how data flows through layers)
2. **Critical Paths** (2-3 most critical execution paths)
3. **Integration Points** (external system interactions)
4. **Architectural Concerns** (issues, coupling, etc.)

Output format: Use ASCII diagrams for data flow.
"""

    def _prompt_round4_synthesis(self, context: EnhancementContext) -> str:
        """第4轮：合成最终文档"""

        round1_output = context.get_round_output(1)
        round2_output = context.get_round_output(2)
        round3_output = context.get_round_output(3)

        return f"""
## Context
You have analyzed this module through 3 rounds:

### Round 1: Architecture Overview
{round1_output}

### Round 2: Core Component Analysis
{round2_output}

### Round 3: Component Relationships
{round3_output}

## Task
Synthesize a final README_AI.md:

1. **Purpose** - Clear 1-2 sentence statement
2. **Architecture** - Pattern, layers, data flow (ASCII diagram)
3. **Key Components** - Table with roles
4. **Critical Workflows** - 2-3 most important (code blocks)
5. **Dependencies** - What it consumes/provides (tables)
6. **Gotchas** - Performance notes, known issues, future improvements

Requirements:
- Markdown format
- 50-100 lines
- Focus on WHAT and WHY
- Include ⚠️ for warnings
- Include [ ] for TODOs

Start with: # README_AI.md - {context.dir_path.name}
"""
```

---

## 📊 效果预测

### 对于 OperateGoods.class.php (8891行, 57符号)

| 指标 | 单轮压缩 | 单轮分层 | **多轮对话** |
|------|----------|----------|--------------|
| **API调用** | 1次 | 1次 | **4次** |
| **Prompt大小** | 100KB | 30KB | **<20KB/轮** |
| **生成质量** | ⭐⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| **包含架构图** | ❌ | ⚠️ | **✅** |
| **包含工作流** | ❌ | ⚠️ | **✅** |
| **包含已知问题** | ❌ | ❌ | **✅** |
| **成功率** | 50% | 70% | **95%** |
| **最终大小** | 51KB | 15KB | **3-5KB** |

### 总成本分析

**单次生成成本**（以Claude Sonnet为例）:
- Input: 4轮 × 20KB ≈ 80KB ≈ 20K tokens
- Output: 4轮 × 5KB ≈ 20KB ≈ 5K tokens
- 总计: ~25K tokens
- 成本: ~$0.25 USD

**长期收益**（假设团队10人，项目1年）:
- 每次查看README节省时间: 30分钟（vs 从零理解代码）
- 每月查看次数: 每人5次
- 年度节省: 10人 × 5次/月 × 12月 × 30分钟 = **1800小时**
- 价值（按$100/小时）: **$180,000 USD**

**ROI**: 180,000 / 0.25 = **720,000x** 🚀

---

## 🌐 知识图谱的定位

### codeindex 应该提供什么？

**输出格式扩展**：除了README_AI.md，还可以输出：

```python
# src/codeindex/exporters/graph_exporter.py

class GraphExporter:
    """导出符号关系图谱"""

    def export_to_json(self, parse_results: List[ParseResult]) -> dict:
        """导出为JSON格式（给知识图谱项目使用）"""

        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "project": str(Path.cwd()),
                "generated_at": datetime.now().isoformat(),
                "total_symbols": sum(len(r.symbols) for r in parse_results)
            }
        }

        # 添加节点
        for result in parse_results:
            for symbol in result.symbols:
                graph["nodes"].append({
                    "id": f"{result.path.name}::{symbol.name}",
                    "label": symbol.name,
                    "type": symbol.kind,
                    "file": str(result.path),
                    "line_start": symbol.line_start,
                    "line_end": symbol.line_end,
                    "signature": symbol.signature,
                    "docstring": symbol.docstring,
                    "importance_score": scorer.score(symbol)
                })

        # 添加边（调用关系）
        for result in parse_results:
            for edge in self._detect_calls(result):
                graph["edges"].append(edge)

        return graph

    def export_to_graphml(self, parse_results: List[ParseResult]) -> str:
        """导出为GraphML格式（Gephi, Neo4j可导入）"""
        # ... 生成GraphML XML

    def export_to_neo4j_cypher(self, parse_results: List[ParseResult]) -> str:
        """导出为Neo4j Cypher语句"""
        # ... 生成CREATE语句
```

### 知识图谱项目可以做什么？

**独立的"codeindex-graph"项目**：

```bash
# 读取codeindex的输出
codeindex-graph import project_graph.json

# 启动图数据库
codeindex-graph serve
# -> Neo4j数据库 at http://localhost:7474

# 可视化查询
codeindex-graph visualize "MATCH (n:Class)-[:CALLS]->(m:Method) RETURN n, m"

# 语义查询
codeindex-graph query "Find all classes that handle price calculations"
```

**职责分离**:
- **codeindex**: 解析代码 → 生成索引 → 导出结构化数据
- **codeindex-graph**: 读取数据 → 构建图 → 可视化 → 语义查询

---

## 🔄 增量更新的挑战

### 问题场景

**场景**: 修改了 OperateGoods.class.php 的一个方法

```php
// 修改前
public function setGoodsPrice($id, $price) {
    // 10行代码
}

// 修改后
public function setGoodsPrice($id, $price, $reason) {
    // 新增了 $reason 参数
    // 20行代码（增加了价格变更原因记录）
}
```

**问题**:
1. 重新运行4轮对话，成本增加
2. 如何保留未修改部分的索引？
3. 如何合并新旧索引？

### 增量更新策略

#### 策略1: 变更检测 + 局部重新生成

```python
# src/codeindex/incremental_enhancer.py

class IncrementalEnhancer:
    """增量更新增强器"""

    def detect_changes(
        self,
        old_parse_result: ParseResult,
        new_parse_result: ParseResult
    ) -> ChangeSet:
        """检测变更"""

        changes = ChangeSet()

        old_symbols = {s.name: s for s in old_parse_result.symbols}
        new_symbols = {s.name: s for s in new_parse_result.symbols}

        # 新增的符号
        added = set(new_symbols.keys()) - set(old_symbols.keys())
        changes.added_symbols = [new_symbols[name] for name in added]

        # 删除的符号
        removed = set(old_symbols.keys()) - set(new_symbols.keys())
        changes.removed_symbols = [old_symbols[name] for name in removed]

        # 修改的符号（签名或行范围变化）
        for name in set(old_symbols.keys()) & set(new_symbols.keys()):
            old_sym = old_symbols[name]
            new_sym = new_symbols[name]

            if (old_sym.signature != new_sym.signature or
                old_sym.line_start != new_sym.line_start or
                old_sym.line_end != new_sym.line_end):
                changes.modified_symbols.append((old_sym, new_sym))

        return changes

    def should_full_regenerate(self, changes: ChangeSet) -> bool:
        """判断是否需要完整重新生成"""

        total_changed = (
            len(changes.added_symbols) +
            len(changes.removed_symbols) +
            len(changes.modified_symbols)
        )

        # 如果变更超过30%，完整重新生成
        if total_changed / len(all_symbols) > 0.3:
            return True

        # 如果核心方法被修改，完整重新生成
        for old_sym, new_sym in changes.modified_symbols:
            if scorer.score(new_sym) > 70:  # 核心方法
                return True

        return False

    def incremental_update(
        self,
        old_readme: str,
        changes: ChangeSet
    ) -> str:
        """增量更新README"""

        # 简化的增量策略：只更新"Key Components"部分

        prompt = f"""
## Current README
{old_readme}

## Changes Detected

### Added Symbols
{format_symbols(changes.added_symbols)}

### Modified Symbols
{format_symbols([new for old, new in changes.modified_symbols])}

### Removed Symbols
{format_symbols(changes.removed_symbols)}

## Task
Update ONLY the relevant sections of the README to reflect these changes.

Keep:
- Purpose (unchanged)
- Architecture diagram (unless major change)
- Dependencies (unless import changed)

Update:
- Key Components table (add/modify/remove rows)
- Critical Workflows (if affected methods changed)
- Gotchas (if new issues introduced)

Output: Full updated README
"""

        result = invoke_ai_cli(self.ai_command, prompt, timeout=120)
        return clean_ai_output(result.output)
```

#### 策略2: 混合模式

```python
def enhance_with_incremental_mode(
    dir_path: Path,
    parse_results: List[ParseResult],
    old_readme: Optional[str] = None
) -> str:
    """混合模式增强"""

    # 如果没有旧README，使用多轮对话
    if not old_readme:
        return MultiTurnEnhancer().enhance(dir_path, parse_results)

    # 检测变更
    old_results = load_old_parse_results(dir_path)
    changes = detect_changes(old_results, parse_results)

    # 判断策略
    if should_full_regenerate(changes):
        console.print("[yellow]Major changes detected, full regeneration...[/yellow]")
        return MultiTurnEnhancer().enhance(dir_path, parse_results)
    else:
        console.print("[green]Minor changes, incremental update...[/green]")
        return IncrementalEnhancer().incremental_update(old_readme, changes)
```

**优势**:
- ✅ 小改动：1次API调用（增量更新）
- ✅ 大改动：4次API调用（完整重新生成）
- ✅ 自动判断策略

---

## 🎯 Epic 3 实施计划修订

### Epic 3.1: 多轮对话架构（2周）

| Story | 工作量 | 优先级 |
|-------|--------|--------|
| 3.1.1 MultiTurnEnhancer 核心架构 | 3天 | P0 |
| 3.1.2 Round 1-4 Prompt模板 | 2天 | P0 |
| 3.1.3 符号分组和重要性评分 | 2天 | P0 |
| 3.1.4 增量更新检测 | 2天 | P1 |
| 3.1.5 测试和验证 | 1天 | P0 |

### Epic 3.2: 知识图谱导出（1周）

| Story | 工作量 | 优先级 |
|-------|--------|--------|
| 3.2.1 GraphExporter JSON格式 | 1天 | P1 |
| 3.2.2 调用关系检测 | 2天 | P1 |
| 3.2.3 GraphML/Cypher导出 | 1天 | P2 |
| 3.2.4 CLI命令集成 | 1天 | P1 |

### Epic 3.3: 增量更新优化（2周）

| Story | 工作量 | 优先级 |
|-------|--------|--------|
| 3.3.1 变更检测算法 | 2天 | P1 |
| 3.3.2 增量prompt生成 | 2天 | P1 |
| 3.3.3 混合模式策略 | 2天 | P1 |
| 3.3.4 缓存和性能优化 | 2天 | P2 |

---

## ✅ 下一步行动

### 立即可以做的实验

1. **手动测试多轮对话**
   ```bash
   # 手动运行4轮，验证概念

   # Round 1
   claude -p "$(cat round1_prompt.txt)"

   # Round 2（基于Round 1的输出）
   claude -p "$(cat round2_prompt.txt)"

   # ...
   ```

2. **在PHP项目上验证效果**
   - 选择1个超大文件（如OperateGoods.class.php）
   - 手动执行4轮对话
   - 对比单轮vs多轮的质量差异

3. **原型实现**
   - 实现简化版MultiTurnEnhancer
   - 只实现Round 1-2（验证可行性）
   - 测试API调用和prompt生成

### 需要讨论的问题

1. **默认策略**
   - 对所有文件都用多轮对话？
   - 还是只对>5000行的文件用多轮？

2. **轮数配置**
   - 4轮是否合适？
   - 是否需要根据文件大小动态调整（2-6轮）？

3. **知识图谱优先级**
   - 是否先实施多轮对话，再考虑图谱导出？
   - 还是同时进行？

---

这个方案是否符合你的产品定位？需要我深入设计某个部分吗？
