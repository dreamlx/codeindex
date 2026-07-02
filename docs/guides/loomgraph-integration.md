# LoomGraph 集成指南

**目标读者**: LoomGraph 项目组开发者，以及任何想把 codeindex 的解析结果喂给下游知识图谱 / 检索系统的人。

---

## 🎯 架构：两仓、单向、进程解耦

```
codeindex (CLI, 无状态)          →          LoomGraph (CLI / MCP, 有状态)
   AST 解析 → 结构切片                          SQLite + sqlite-vec
   graph-export NDJSON  ────────────────▶      import-export → 知识图谱 + 向量检索 + MCP
```

- **codeindex — 解析层（无状态）**：tree-sitter 抽取 symbol / call / inheritance，产出
  **write-once 制品**。它不持有任何持久化状态——没有 `.db`、没有增量同步、没有向量索引
  （[ADR-007](../architecture/adr/007-codeindex-stateless-graph-ownership.md)）。
- **LoomGraph — 存储 + 查询层（有状态）**：用内嵌 **SQLite + sqlite-vec** 自建知识图谱
  和向量检索，提供 query CLI 与 MCP server。它是自包含的，**不再依赖 LightRAG 或任何外部
  RAG 框架 / PostgreSQL**。
- 两仓之间**唯一的数据接缝**是 codeindex 的输出制品。codeindex 不 import loomgraph，
  loomgraph 通过子进程调用 codeindex CLI（进程隔离、独立升级、错误不跨进程传播）。

### 为什么是 CLI 子进程而非 Python API

松耦合。两仓独立安装、独立发版、进程隔离；codeindex 崩溃不会拖垮 loomgraph；任何语言都能调
CLI。代价是一次子进程 + JSON/NDJSON 序列化开销，对"解析整仓"这种粒度可以忽略。

---

## 📦 安装

```bash
pipx install "ai-codeindex[all]"   # 推荐，隔离安装（含全部语言 parser）
# 或
pip install "ai-codeindex[all]"

codeindex --version
```

> ⚠️ PyPI 包名是 **`ai-codeindex`**（CLI 命令是 `codeindex`）。不要用 `matrix-codeindex` /
> `codeindex` 之类的包名安装。

**支持的语言**（7）：Python (.py) / PHP (.php .phtml) / Java (.java) /
TypeScript (.ts .tsx) / JavaScript (.js .jsx) / Swift (.swift) / Objective-C (.m .h)。

---

## 🔌 三条集成路径

按"整仓图谱 → 单文件程序化"排序。**新集成优先用路径 A。**

### 路径 A（推荐）：`graph-export` NDJSON 契约

codeindex 对整棵树做一次干净解析，产出 **write-once** 的 NDJSON 图谱制品；loomgraph 用
`import-export` 消费。这是当前的**正式数据契约**（ADR-007）。

```bash
# codeindex 侧：产出制品（自带一次全树解析，每个文件恰好解析一次，与 scan-all / README 渲染完全解耦）
codeindex graph-export --root . -o graph-export.ndjson
codeindex graph-export --root . -o -            # 输出到 stdout

# loomgraph 侧：导入到 workspace
loomgraph import-export graph-export.ndjson
loomgraph import-export graph-export.ndjson --dry-run   # 只校验 + 打印摘要，不落库
loomgraph import-export graph-export.ndjson -w myproj --clear   # 指定 workspace 并清空重建
```

制品结构（NDJSON：第 1 行 `meta`，随后 `entity`，随后 `edge`）：

```jsonc
{"type":"meta","schema_version":0,"generator":"codeindex","provenance_completeness":"ast-only: ..."}
{"type":"entity","id":"app.service.AuthService","entity_type":"class","source_id":"app/service.py:8","description":"Authenticates users.","provenance":"ast"}
{"type":"edge","kind":"CALLS","src":"app.service.AuthService.login","dst":"app.service.AuthService.authenticate","resolution_qualifier":"resolved","source_id":"app/service.py:15"}
```

**完整字段规格、命名约定、消费者契约（两条必读 caveat）见
[graph-export.md](graph-export.md)。** 集成前请务必读这两条，否则会得出错误结论：

1. **`resolution_qualifier`** —— 永远不要把 `unresolved` / `ambiguous` 边当作已确认的关系。
   解析器只产出 file-local 名字，export 做唯一一次跨文件解析；高 unresolved 比例是正常的
   （真实代码里大量调用指向 stdlib / 三方 / AST 无法静态解析的方法，实测 loomgraph 自身
   round-trip ≈59% unresolved）。`import-export` 会**保留 `resolved`/`ambiguous`、跳过
   `unresolved`**（不插占位节点，否则会在 topology 分析里造出误导性 hub）。
2. **`provenance_completeness`** —— 抽取是 AST-only。动态派发、反射 / 元类、装饰器 wiring
   **不被捕获**。**边的缺失意味着"静态不可解析"，不等于"没有"。**

**这是一个结构切片，不是完整图谱索引**：只含真实代码符号（class/function/method）及其
CALLS/INHERITS 边，不含 file/module 容器节点和外部/stdlib stub —— 这些由消费者在 ingest 时
围绕切片自行合成（ADR-007）。

### 路径 B（便捷）：`loomgraph index <repo>` 一步式

loomgraph 提供一个一步式命令，内部自动调用 codeindex 完成"扫描 → embedding → 建图"：

```bash
loomgraph index /path/to/repo          # 一条命令建好可查询的 workspace
loomgraph index /path/to/repo -w myproj
```

适合"我只想快速把一个仓库变成可查询的图谱"。前提是 `codeindex` 已在 PATH 中。

> 现状说明：`loomgraph index` 目前内部走的是较早的 `codeindex scan --output json` 路径，
> 尚未迁移到路径 A 的 graph-export 契约。二者产出的 workspace 内容可能有差异；需要契约级
> 保证（qualifier / provenance 元数据）时用路径 A。

### 路径 C（低层）：`codeindex parse <file>` 单文件 JSON

程序化、逐文件的解析 API，适合流式 / 增量 / 只处理个别文件的场景。**不做跨文件解析**——
输出的是 file-local 结果。

```bash
codeindex parse src/auth/user.py       # 固定输出 JSON 到 stdout
```

输出结构：

```json
{
  "file_path": "src/auth/user.py",
  "language": "python",
  "symbols": [
    {
      "name": "User.authenticate",
      "kind": "method",
      "signature": "def authenticate(self, password: str) -> bool:",
      "docstring": "Authenticate user with password",
      "line_start": 25,
      "line_end": 30,
      "annotations": [{"name": "override", "arguments": {}}]
    }
  ],
  "imports": [
    {"module": "typing", "names": ["Dict", "Optional"], "is_from": true, "alias": null}
  ],
  "namespace": "",
  "error": null
}
```

| 字段 | 说明 |
|------|------|
| `file_path` / `language` | 文件路径 / 语言标识 |
| `symbols[]` | `name`(方法带类名如 `User.authenticate`) / `kind`(class·function·method) / `signature` / `docstring` / `line_start` / `line_end` / `annotations[]` |
| `imports[]` | `module` / `names[]` / `is_from` / `alias` |
| `namespace` | 命名空间/包名（PHP/Java；Python 为空串） |
| `error` | 错误信息或 `null`。**部分解析**时 `error` 为 `null` 但结果可能不完整——见下 |

**Exit code**：`0` 成功；`1` 文件不存在 / 非文件 / 无权限；`2` 不支持的文件类型；
`3` 解析失败（`stdout` 仍是带 `error` 字段的 JSON，可能含部分符号）。

**部分解析恢复**：单个语法错误不会清零整个文件的符号（GH #95）。解析器会尽量返回可恢复的符号；
消费端应始终 `result.get("symbols", [])` 兜底，不要因 `error` 非空就丢弃全部结果。

最小 Python 封装：

```python
import json, subprocess
from pathlib import Path

def parse_file(path: Path) -> dict | None:
    r = subprocess.run(["codeindex", "parse", str(path)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode in (1, 2):        # 缺失 / 不支持 → 跳过
        return None
    return json.loads(r.stdout)       # returncode 0 或 3(部分/失败) 都返回可用 JSON
```

---

## 🔄 版本兼容

- **`parse` JSON（路径 C）**：字段只增不减，向后兼容；破坏性变更只随 MAJOR 版本发生。
- **`graph-export` NDJSON（路径 A）**：**实验中（`schema_version: 0`）**，在 0 版本期间字段/
  格式可能无 deprecation 直接变更。消费端应读 `meta.schema_version` 并对未知版本告警。

版本检查直接解析 `codeindex --version` 输出即可（格式 `codeindex, version X.Y.Z`）。

---

## 📚 FAQ

**Q: 路径 A / B / C 怎么选？**
整仓建图谱、要契约保证 → **A**（graph-export）。只想一条命令跑通、不在意底层 → **B**
（`loomgraph index`）。流式 / 增量 / 逐文件程序化处理 → **C**（`parse`）。

**Q: `graph-export` 和 `scan` 有什么区别？**
`scan` / `scan-all` 面向**人**，生成 `README_AI.md` 导航文档。`graph-export` 面向**机器**，
产出结构化图谱制品，且做一次干净全树解析（每文件一次），**不触碰 README_AI.md**。

**Q: 为什么 unresolved 边这么多？正常吗？**
正常。真实代码里大量调用指向 stdlib / 三方 / 动态派发，AST 静态解析不了。见路径 A 的两条
caveat 与 [graph-export.md](graph-export.md)。

**Q: LightRAG / PostgreSQL 还需要吗？**
不需要。LoomGraph 本地化后用内嵌 SQLite + sqlite-vec 取代，"no RAG framework needed"。

**Q: 能在 Docker / CI 里用吗？**
可以。`pip install "ai-codeindex[all]"` 后 `codeindex graph-export` / `parse` 都是无状态的
纯 CLI 调用，天然适合 CI。

---

## 🔗 相关资源

- **graph-export 契约规格**: [graph-export.md](graph-export.md)
- **无状态设计决策**: [ADR-007](../architecture/adr/007-codeindex-stateless-graph-ownership.md)
- **codeindex GitHub**: https://github.com/dreamlx/codeindex
- **PyPI**: https://pypi.org/project/ai-codeindex/
- **Issue**: https://github.com/dreamlx/codeindex/issues
