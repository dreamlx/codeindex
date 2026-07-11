# ADR 009: codeindex 是 LoomGraph 的 parser engine(产品定位)

## Status

Accepted — 承接 ADR-006(distribution split)与 ADR-007(stateless graph
ownership),明确 codeindex 在两仓产品中的角色。

## Context

ADR-006 把 codeindex 拆成两 artifact(`ai-codeindex` CLI wheel +
`dreamlx/codeindex-claude` plugin)。ADR-007 确立 codeindex 对 graph
**stateless** —— 只产 NDJSON,不持有图存储。但「codeindex 本身是产品还是某个
更大产品的一部分」一直没有显式定位。

2026 年中,[LoomGraph](https://github.com/dreamlx/LoomGraph) 从「RAG over
LightRAG + PostgreSQL」重构为「SQLite + sqlite-vec 图存储 + 向量检索 + MCP
server」(no RAG framework needed)。重构后 LoomGraph 的 `loomgraph index` 直接
消费 `codeindex graph-export` 的 NDJSON 跑全 pipeline(graph-export → embed →
inject),LightRAG / PostgreSQL 从 runtime 退役。两仓之间的唯一 seam 收敛为
graph-export NDJSON contract —— 这让「谁是 user-facing product」变得清楚:
**用户操作 LoomGraph,不直接操作 codeindex**。

codeindex 的 README_AI.md navigation index 仍可独立用(不接图层的场景),但这
是次要 surface;主产品形态是「被 LoomGraph 调用的 parser engine」。

## Decision

**codeindex 是 LoomGraph 的 parser engine —— the "see" layer。**

分层:

| 仓 | 角色 | 状态 |
|------|------|------|
| **codeindex** | "see":tree-sitter AST → structural slice → `graph-export` NDJSON。**Stateless**(ADR-007)。 | 本仓 |
| **LoomGraph** | "think + remember":SQLite + sqlite-vec 图存储 + 向量检索 + MCP server + `impact`/`deps`/`topology` + skills。**Stateful。** | dreamlx/LoomGraph |

用户视角:**两个仓,一个产品**。终端用户 `pipx install loomgraph`(pulls
`ai-codeindex` 为依赖),`loomgraph index` 跑全 pipeline —— 用户从不直接操作
codeindex。codeindex 也可 standalone 用于 README_AI.md navigation index(不接
图层的场景)。

**methodology 角色(agent-native middleware thesis 的 "see" instance)与产品形态
解耦**:thesis 上 codeindex 是「把人类工具栈翻译成 agent-native middleware」三
instance(codeindex / loomgraph / IntentSpec)之一;但产品上它就是 LoomGraph
的解析后端。两层叙述不混。

## 与既有 ADR 的关系

- **ADR-006(distribution split)**:不变。仍是 CLI wheel + plugin repo 两
  artifact。ADR-009 只是在它之上加了「wheel 主要被 loomgraph 拉取」的产品定位。
- **ADR-007(stateless graph ownership)**:强化。codeindex 不持有图,正好符合
  「parser engine 只产 NDJSON」的定位 —— stateless 是 parser engine 的必要条件。
- **ADR-002 / ADR-008(AI backend)**:正交。AI enrichment 是 scan 命令的增强,
  与 graph-export(stateless NDJSON)是两条独立 surface。

## Consequences

+ 用户安装路径单一:`pipx install loomgraph` 拉全套,不需要单独装 codeindex。
+ codeindex 的发布节奏可独立于 LoomGraph(NDJSON contract 是稳定 seam),但
  breaking schema change(如 `schema_version`)需两仓协调。
+ graph-export NDJSON contract 成为**唯一**跨仓契约 —— 任何下游(不止
  LoomGraph)都从这个 contract 取数。contract 变更走 ADR(如 ADR-007 的
  stateless 决策、schema v1 的 content_hash)。
+ codeindex 文档(CLAUDE.md / README)需反映「parser engine」定位,而非把
  codeindex 当独立终端产品叙述。
- codeindex standalone 用法(README_AI.md navigation)定位降级为次要 surface,
  但不删除 —— 它仍是真实可用场景,且不接图层时无需装 LoomGraph。

## References

- [ADR-006](006-distribution-architecture-split.md)(distribution split)
- [ADR-007](007-codeindex-stateless-graph-ownership.md)(stateless graph ownership)
- CHANGELOG v0.32.0(产品定位澄清条目)
- [LoomGraph](https://github.com/dreamlx/LoomGraph)(the "think + remember" layer)
