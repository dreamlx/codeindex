# ADR 007: codeindex 保持无状态 — 持久化图谱归属 loomgraph

## 状态

已采纳 (Accepted) — 2026-06-23；已落地 (Implemented) — 2026-06-28（`GraphBuffer` IR
与 `graph-export` 随 v0.27.0 发布，验证门控见文末更新）

## 背景

`code-governance` 工作空间对 `codebase-memory-mcp`（cbm，⭐11.2k，纯 C，22-pass
pipeline，SQLite + Cypher 图谱）做竞品分析后，产出 `absorption-plan.md` 的
B1（N-pass pipeline）/ B3（SQLite + sqlite-vec 持久化图谱）两个吸收项，提议
codeindex 从当前的线性 2-phase 升级为 N-pass 架构，并引入 `GraphBuffer` 中间
表示 + 持久化 SQLite 图谱 + sqlite-vec 向量表（统一为「Phase 1」）。

讨论中暴露出该方案的两个结构性问题：

1. **三个可分离制品被捆成一个不可分的包**：

   | 制品 | 是什么 | 成本 |
   |---|---|---|
   | A. GraphBuffer（内存 IR） | parse 结果的中间表示，pass 间通信 | 低（纯内存，每 run 重建） |
   | B. 持久化 SQLite 图谱 | nodes/edges + provenance，跨 run 维护 | **高**（schema/迁移/增量/损坏恢复/并发） |
   | C. sqlite-vec 向量表 | 语义检索后端 | 中（embedding 模型 + 重建） |

   A 的全部好处（解耦 parse/write、可组合 pass、全局调用图）来自内存 IR，**不依赖
   B**。把三者捆在一起，让 codeindex 为只有 loomgraph 才消费的能力背上有状态的代价。

2. **「SQLite 作为契约格式」被混淆成「codeindex 拥有有状态的 SQLite」**。两者正交：
   codeindex 可以每次全量吐一个 write-once 的 `.db`/JSON 快照拿到 schema-as-contract
   的好处，而无需跨 run 维护一个可变 `.db`。

前置共识：**不以「追平 cbm」为目标**。cbm 是纯 C、158 语言、arXiv 论文、SLSA-3 的
超集竞品，功能上不追、也不该追。codeindex 的护城河是消费侧的 AI 导航理解力
（见 ADR-005），不是图谱后端这个 commodity 层。

## 决策

**codeindex 保持「无状态发射器」定位，不拥有任何持久化图谱状态。**

1. **codeindex 不拥有有状态的图谱写路径。** 每次运行全量产出 artifact，**不**跨 run
   维护、**不**增量回读自身图谱、**不**做损坏恢复。`~/.codeindex/*.db` 这类常驻可变
   状态不进 codeindex。

2. **L1（AST 结构）+ L2（注释规范化）升级为 `GraphBuffer` 内存 IR。** 解耦
   `parse_file()`（今天一次性提取符号/调用/继承，加能力要改 parser），让 pass 可组合，
   产出全局调用图。IR 在内存中，每 run 重建。这是纯内部重构，不引入持久化状态。

3. **codeindex 产出一个 write-once 的结构化 graph-export artifact** 作为与 loomgraph
   的数据契约。loomgraph **读** 该 artifact（进程解耦），**不** import codeindex 当库
   （见替代方案 2）。

4. **持久化与查询全部归 loomgraph**：持久化 SQLite + sqlite-vec 向量表、L3 设计文档
   LLM 抽取、跨 run 增量图谱维护、图查询（SQL / 未来 Cypher）。loomgraph 读 codeindex
   的 L1+L2 export，追加 L3，拥有整个有状态图谱。

### codeindex 明确不做的事

- ❌ 维护跨 run 的持久化图谱 DB
- ❌ 图谱增量同步 / file_hashes 状态表 / 损坏检测与恢复
- ❌ sqlite-vec 向量索引的构建与查询
- ❌ L3 设计文档的 LLM 实体抽取
- ❌ 暴露图查询接口（search_graph / trace_call_path / Cypher）

### codeindex 仍然做的事

- ✅ AST 结构提取（L1）+ 注释规范化（L2，可选 AI）
- ✅ `GraphBuffer` 内存 IR + 可组合 pass
- ✅ README_AI.md / PROJECT_SYMBOLS.md（消费侧导航产品，不变）
- ✅ write-once graph-export artifact（给 loomgraph 等工具）
- ✅ 现有 AI-enrichment 增量缓存（ok 缓存、只重跑 new/failed dir）

## 理由

1. **codeindex 没有回读自身图谱的需求。** 唯一需要回读的场景是增量索引
   （file_hashes → 跳过未变文件）。但 design-philosophy 明确：**parse 不是瓶颈，AI
   调用才是（99%）**。结构层（L1）全量重 parse 是毫秒级，增量省不下什么。真正贵的
   AI 层（enrichment / L2 规范化）**已经有增量缓存**（#94 / #97：ok 结果缓存，只有
   new/failed dir 打 AI）。codeindex 在真正贵的地方早就解决了增量，且没用任何持久化
   图谱。持久化图谱是为一个 codeindex 不存在的问题加重状态。

2. **不引进竞品最难的失败类。** cbm 最严重的两个 bug —— #557「corrupt 检测触发即
   `unlink` DB，无备份无恢复」、#516「re-index 时 ADR 数据丢失」—— 都是持久化图谱
   状态 bug。给 codeindex 加有状态写路径等于把这个失败类引进门。

3. **服务零现有用户。** ~400 个企业用户当前消费的是 README_AI.md，没人消费 SQLite
   图。有状态写路径增加发布、回归、支持面，却不服务任何现有消费。

4. **「薄」是核心美德。** ADR-005（导航契约）/ ADR-006（分发拆分）一脉相承：codeindex
   是 editor-agnostic 的薄引擎。持久化图谱（schema 版本化、迁移、vec0 扩展、`.db`
   生命周期）是一次结构性膨胀，与「只做 AST + AI 注释规范化」冲突。

5. **好处归 loomgraph，代价不该压 codeindex。** 持久化图谱的好处（全局查询、
   向量 + 结构 JOIN、「语义相似且调用 redis 的函数」）消费方是 loomgraph（语义检索是
   loomgraph 的能力轴）。代价（状态、schema、增量、恢复）若压在 codeindex 上即是错配。
   状态应与消费/推理方同处。

6. **格式与所有权正交。** 用 SQLite 当**导出格式**（schema-as-contract，比 CLI JSON
   稳定）不要求 codeindex **维护**一个有状态 `.db`。codeindex 吐 write-once 快照即可
   两全。

## 验证门控

`GraphBuffer` 内存 IR 因有**独立的内部解耦价值**（解耦 parse/write，与消费侧 thesis
无关），可不等 spike 推进。

但 **graph-export artifact 作为常驻契约**之前，需 loomgraph 侧先跑 time-boxed 消费
spike 出 GREEN（对照 `先验证再造基建` 红黄绿卡）：

> 同一 fixture，agent 用 README_AI.md vs 用 loomgraph 的图谱查询，哪个让 agent 理解
> 得更快 / 更省 token / 更准（消费侧三轴，对照 baseline）。

GREEN → 固化 export schema 与 loomgraph 消费链；YELLOW → 只留真正有用的字段；
RED → 重想，export 不固化为常驻契约。在 spike 出 GREEN 前，不把 export schema 当
稳定契约对外承诺。

### 门控结果（2026-06-28 更新）

LoomGraph#30 消费 spike 已跑，verdict **🟡 YELLOW**：证实了下游确实需要这份 export
artifact，但**只**为"产出制品"背书，**未**为内部 render-flip（#101 Phase 2）背书——
二者架构独立（export 需要 buffer 被*填充*，不是渲染路径被*翻转*）。据此：

- `GraphBuffer` IR（#101）+ `graph-export`（#102）随 **v0.27.0 发布**；`GraphBuffer`
  以 dormant（未接入 `scan-all`）状态随车。
- 遵循 YELLOW = "只留真正有用的字段"：export 以 **experimental `schema_version: 0`**
  发布——字段/格式在 0 版本期间可无 deprecation 变更，**尚未**作为稳定契约对外承诺。
  每条边带 `resolution_qualifier`、meta 带 `provenance_completeness`，如实标注有损性。
- render-flip 延后，issue #101 作为 tracker 保持 open。

契约现状规格见 [graph-export.md](../../guides/graph-export.md)；下游消费与集成路径见
[loomgraph-integration.md](../../guides/loomgraph-integration.md)。

## 替代方案（已否决）

### 方案 1：codeindex 拥有持久化 SQLite 图谱（cbm 模型，absorption-plan 原 B3）

- ❌ 引入跨 run 有状态（schema/迁移/增量/损坏恢复/并发），违反「薄」
- ❌ 引进 cbm 最严重的失败类（#557 / #516 数据丢失）
- ❌ 好处的消费方是 loomgraph，代价压错地方

### 方案 2：loomgraph import codeindex 当库（讨论中的决策 b）

- ❌ 把两个 repo 在代码层绑死，迭代节奏耦合
- ❌ 失去进程隔离与清晰契约
- ✅ 采用决策 a：loomgraph 读 codeindex 吐的 export artifact（进程解耦）

### 方案 3：三层（L1+L2+L3）全放 codeindex 一个工具

- ❌ L3 的 LLM 实体抽取是 AI 推断，违反 codeindex「结构索引层无 AI 依赖」约束
- ❌ 详见 `code-governance/notes/codeindex-loomgraph-division.md`

## 影响范围

### codeindex repo

- 新增 `GraphBuffer` 内存 IR + 可组合 pass（内部重构，不改对外行为）
- 新增 write-once graph-export artifact（schema 待 spike 后固化）
- README_AI.md / PROJECT_SYMBOLS.md / AI-enrichment 增量缓存：**不变**
- **不**新增任何持久化 `.db` 写路径

### loomgraph repo（跨 repo，需镜像 ADR）

- loomgraph 接手持久化 SQLite + sqlite-vec（替换 LightRAG，见
  `code-governance/notes/sqlite-vec-vs-lightrag.md`）
- 读 codeindex export → 追加 L3 → 拥有有状态图谱
- 需在 loomgraph repo 写镜像 ADR 记录这一接手

## 相关 ADR

- ADR 001: 用 tree-sitter 做解析（L1 结构提取的基础）
- ADR 002: 外部 AI CLI 集成（L2 的 AI 规范化走外部 CLI）
- ADR 005: 导航契约与 README 大小上限（codeindex 价值在消费侧的确立）
- ADR 006: 分发架构拆分（「薄引擎 + 薄触达层」范式的同源决策）

## 参考资料

- `code-governance/absorption-plan.md`（B1 / B3 吸收项）
- `code-governance/notes/three-layer-architecture.md`（三层 provenance 模型）
- `code-governance/notes/codeindex-loomgraph-division.md`（L1+L2 vs L3 分工）
- `code-governance/notes/sqlite-vec-vs-lightrag.md`（loomgraph 后端替换论证）
- `code-governance/notes/codebase-memory-mcp.md`（cbm 竞品分析，#557 / #516 失败类）

---

**决策人**: dreamlinx
**日期**: 2026-06-23
**状态**: 已采纳
