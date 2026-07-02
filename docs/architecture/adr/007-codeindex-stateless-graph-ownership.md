# ADR 007: codeindex 无状态 — 持久化图谱归 loomgraph

## 状态

已采纳 (Accepted) — 2026-06-28（随 v0.27.0 `graph-export` 发布落地）

## 背景

LoomGraph#30 消费 spike（verdict 🟡 YELLOW）验证了下游确实需要 codeindex 产出一份
机读的图谱制品（entity + CALLS/INHERITS），但同时逼出一个必须先拍板的架构问题：

**谁持有持久化的代码图谱状态？**

两仓都"碰"图谱：codeindex 从 AST 抽出符号与边，loomgraph 要把它们存进可增量更新、
可向量检索、可 topology 分析的知识图谱。如果不划清所有权，可预见的失败模式：

1. **双写状态**：codeindex 若自己维护一份持久 `.db`（增量同步 / 缓存图谱），loomgraph 又
   维护一份，两份状态会漂移，且"谁是 source of truth" 永远说不清。
2. **职责错层**：codeindex 的价值在消费侧的导航与结构真值（ADR-005），不在"当一个图数据库"。
   让它长出 corruption recovery / 向量索引 / 增量 reconcile，是把 loomgraph 的活扛过来。
3. **export 与 render-flip 混淆**：spike 通过后一度想顺势把 `scan-all` 的内部渲染路径也
   翻新（#101 Phase 2 render-flip）。但 spike 解锁的是**产出制品**，不是**内部重构**——
   export 需要的是 buffer 被 *填充*，不是渲染路径被 *翻转*。二者架构独立。

## 决策

**codeindex 是无状态的图谱 emitter；持久化图谱归 loomgraph。**

1. **codeindex 只产出 write-once 制品**：`codeindex graph-export` 对整棵树做一次干净解析，
   dump 一份 NDJSON（`meta` + `entity` + `edge`）。它**不持有任何持久 / 可变状态**——
   没有 `.db`、没有增量同步、没有 corruption recovery、没有向量索引。契约规格见
   [graph-export.md](../../guides/graph-export.md)。

2. **持久化 + 语义层全部归 loomgraph**：可变 `.db`、增量同步、向量（`sqlite-vec`）索引、
   以及 L3（设计文档级 LLM 抽取）都是 loomgraph 的职责。loomgraph 读这份一次性快照，
   在其上合成容器节点（file/module）、外部 stub、语义脚手架。

3. **唯一接缝是制品**：进程解耦（decision (a)）——codeindex 不 import loomgraph，
   loomgraph 通过子进程调 codeindex CLI 拿到 NDJSON。制品是两仓之间**唯一**的数据契约。

4. **codeindex 只发结构切片，不发完整图谱**：只含真实代码符号（class/function/method）
   及其 CALLS/INHERITS 边，附 `resolution_qualifier` / `provenance_completeness` 元数据，
   如实标注 AST 抽取与跨文件解析的有损性。容器节点 / 外部 stub 由消费者合成。

## 理由

### 1. 分层：sees vs thinks+remembers

两仓模型：**codeindex sees**（AST → 结构切片），**loomgraph thinks + remembers**
（图存储 + 向量检索 + query/MCP）。持久化状态天然属于 "remembers" 侧。让 emitter 保持
无状态，是这条分层的直接推论。

### 2. 单一 source of truth

制品是 write-once 快照，不是可变状态。任何时刻"图谱现在是什么样"只有一个答案——
loomgraph 的 workspace。codeindex 每次 `graph-export` 都从源码重新生成，无历史包袱、
无 reconcile。

### 3. 无状态 = 易测、易 CI、易并发

`graph-export` 是纯函数式的 `源码树 → NDJSON`。可在 CI / Docker / 任意目录无副作用运行，
golden 测试可 diff（见 `tests/test_graph_export.py`）。若 codeindex 持有 `.db`，这些性质
全部消失。

### 4. export ≠ flip（解耦，不顺势重构）

spike 的 GREEN/YELLOW 只为"produce artifact"背书。内部 render-flip（#101 Phase 2）是
独立的、可延后的重构：export 从 `GraphBuffer` 读*已填充*的数据，不要求渲染路径先翻转。
因此 v0.27.0 只 ship export，render-flip 延后，`GraphBuffer` IR 以 dormant（未接线）状态
随车发布。

## 影响范围

- **新增**：`codeindex graph-export` 命令 + [graph-export.md](../../guides/graph-export.md) 契约文档。
- **复用**：`GraphBuffer` IR（#101）仅作已解析数据的容器被 export 复用；不 ship 任何持久 /
  可变状态。
- **延后**：`scan-all` 内部 render-flip（#101 Phase 2），issue #101 作为 tracker 保持 open。
- **下游**：loomgraph 通过 `loomgraph import-export` 消费制品，`unresolved` 边计数但跳过存储
  （不插占位节点，避免污染 topology）。集成见
  [loomgraph-integration.md](../../guides/loomgraph-integration.md)。

## 替代方案（已否决）

### 方案 1：codeindex 自持久化图谱（`.db` + 增量同步）

- ❌ 双写状态、source-of-truth 不清。
- ❌ 职责错层——把 loomgraph 的存储 / 向量 / reconcile 活扛过来。
- ❌ 摧毁无状态带来的可测 / 可 CI / 可并发性质。

### 方案 2：借 export 顺势做 render-flip（#101 Phase 2 一起上）

- ❌ 把"产出制品"和"内部重构"绑成一个大变更，风险叠加。
- ❌ spike 没为 flip 背书；export 不依赖 flip。延后是更小、更可控的路径。

### 方案 3：codeindex 直接 import loomgraph、进程内传对象

- ❌ 紧耦合，违背两仓独立发版 / 进程隔离（同 ADR-006 的引擎/触达层原则的精神）。
- ❌ 强绑 Python 环境；CLI 制品接缝对任何语言的消费者都开放。

## 相关 ADR

- ADR 005: 导航契约与 README 大小上限（codeindex 价值在消费侧——本决策的 precedent）。
- ADR 006: 分发架构拆分（CLI 引擎 vs 触达层；两仓独立发版的同源思路）。

## 参考资料

- 契约规格：[docs/guides/graph-export.md](../../guides/graph-export.md)
- 集成指南：[docs/guides/loomgraph-integration.md](../../guides/loomgraph-integration.md)
- LoomGraph#30 消费 spike（verdict 🟡 YELLOW，为 export 背书、未为 flip 背书）
- 实现：`src/codeindex/graph_export.py`、`src/codeindex/graph_buffer.py`（#101 dormant IR）

---

**决策人**: dreamlinx
**日期**: 2026-06-28
**状态**: 已采纳（v0.27.0 已落地）
