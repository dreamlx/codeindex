# codeindex

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

[🇬🇧 English](README.md) | [🇨🇳 中文](README_zh.md)

**codeindex 是驱动 [LoomGraph](https://github.com/dreamlx/LoomGraph) 的 parser engine。** 它把任意代码库转成 AI 可读的结构化产物——一个 `graph-export` NDJSON 调用/继承图（LoomGraph 消费的唯一 seam），以及作为 standalone 副产品的 `README_AI.md` 导航索引。无状态（ADR-007）；面向用户的产品是 LoomGraph。

> **终端用户**：`pipx install loomgraph` —— 它会自动拉取 `ai-codeindex`，你无需直接操作 codeindex。见 [LoomGraph 集成指南](FOR_LOOMGRAPH.md)。
> **Standalone 用户**（不需要图层、仅要导航索引）：见下方 [Standalone 用法](#standalone-用法不接图层)。

---

## 为什么

AI agent 在陌生代码库里靠 grep 找入口要浪费大量 token。codeindex 预计算一个结构切片（tree-sitter AST → 符号、调用、继承），让 agent——或服务 agent 的图层——从一张已知地图出发，而不是从裸 `grep` 开始。收益是导航效率，不是能力提升：发现阶段实测 −28% token / −19% 墙钟，但答案质量打平（它不让 agent 更聪明——见 [Benchmark](#benchmark)）。

---

## 安装

```bash
pipx install loomgraph          # 终端用户：自动拉取 ai-codeindex 作为依赖
```

Standalone（仅导航索引，不接图层）：

```bash
pipx install ai-codeindex
```

从源码安装：

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"
```

> **Claude Code 用户** —— 另装配套 plugin 获取技能
> （`codeindex:arch` / `:index` / `:update-guide`）：
> ```
> /plugin marketplace add dreamlx/codeindex-claude
> /plugin install codeindex@codeindex-claude
> ```

### 语言解析器

Python 和 PHP 语法默认随包。其他语言需安装对应的 `tree-sitter` 语法：

```bash
pipx inject ai-codeindex tree-sitter-typescript tree-sitter-java   # 注入 pipx 环境
# 或安装时指定子集：
pipx install "ai-codeindex[ios]"      # Swift + Objective-C
```

> 🇨🇳 中国用户：若镜像未同步最新版，直接从上游 PyPI 安装：
> `pipx install --index-url https://pypi.org/simple/ ai-codeindex`

---

## 快速上手

**LoomGraph 用户**（主线）：

```bash
loomgraph index .            # codeindex graph-export → embed → inject，一条 pipeline
loomgraph graph "UserService.login" --depth 2
loomgraph topology           # orphans / hubs + resolved_ratio 信任信号
```

**Standalone**（仅 README_AI 导航索引）：

```bash
codeindex init               # 创建 .codeindex.yaml + 注入 CLAUDE.md 章节
codeindex scan-all           # 结构化 + 可选 AI 描述（配置 ai_command 时自动启用）
codeindex scan-all --no-ai   # 仅结构化
```

完整命令参考：`codeindex --help`。

---

## Standalone 用法（不接图层）

codeindex 的 `README_AI.md` 是分层的**导航索引**——agent 浏览它找到正确的模块，再钻进源码看精确机制。它**不是**知识图谱，不解析跨模块关系；那需要 LoomGraph。

**何时适合 standalone**：
- 小/中规模代码库，图层比你需要得更重。
- 物理隔离内网，导航不依赖任何外部服务。
- 与 [Serena MCP](https://github.com/oraios/serena) 搭配做精确符号查询（codeindex = "地图"，Serena = "GPS"）。

**何时该转 LoomGraph**：
- 需要跨模块调用图遍历（`authenticate()` 两跳深的所有 caller）。
- 需要变更影响分析、拓扑异味或语义搜索。
- 代码库大到扁平导航索引不再划算（见 benchmark：250 目录遗留系统上 token 收益几近消失——扁平索引能指给你文件，但综合不了跨模块语义）。

`codeindex init` 把 codeindex 章节注入你**项目的** `CLAUDE.md`，让 Claude Code 先读 `README_AI.md`（绝不碰 `~/.claude` —— ADR-006）。结构变更后跑 `codeindex scan-all` 刷新索引；`README_AI.md` 是生成物，不要手改。

---

## Benchmark

大多数"AI 代码理解"工具只是宣称自己有价值。我们对自己的工具做了 A/B 测试——并把那些不光彩的部分也公开了。

在 **3 个异构真实项目上的 15 道评分制导航题**中，一个 coding agent **带** `README_AI.md` 对比**不带**：

- **平均 −28% token、−19% 墙钟时间**——agent 更快、更省地抵达正确文件。
- **答案质量打平。** 它*不会*让答案更*正确*——赢的是效率，而非能力。（一个缺乏纪律的索引甚至在几道精确机制题上拖了后腿；已在 [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) 中修复。）
- **在最大的代码库上收益最小。** 在一个 250 个目录的遗留系统上，token 收益几近消失——扁平索引能指给你文件，却无法综合跨模块语义。codeindex 是*导航*层，不是*理解一切*层（精确机制请搭配源码阅读 / [Serena](https://github.com/oraios/serena)，或转 LoomGraph 做跨模块图查询）。

包含失败案例的完整数据：**[2026-05 benchmark](docs/benchmark/2026-05-readme-impact.md)**。在你自己的仓库上复现：**[`bench/`](bench/)**（`make setup && make run && make grade`）。

> 为什么要公开那些不为工具增光的部分：一个悄悄拉低答案质量的导航索引比没有更糟。知道它*确切*在哪里有帮助——以及在哪里该退回源码——才是重点。

---

## 命令

完整参考：`codeindex --help`。要点：

| 命令 | 用途 |
|---|---|
| `codeindex scan-all` | 生成 / 刷新 `README_AI.md` 索引（结构化 + 可选 AI） |
| `codeindex graph-export` | 输出 LoomGraph 消费的 entities + edges NDJSON |
| `codeindex parse <file>` | 单文件 JSON 解析，便于工具集成 |
| `codeindex symbols` | 全局符号索引（`PROJECT_SYMBOLS.md`） |
| `codeindex tech-debt <dir>` | 代码质量分析（大文件、上帝类、测试坏味）——见[指南](docs/guides/tech-debt-analysis.md) |
| `codeindex affected --since HEAD~5` | Git 变更影响（受影响目录） |
| `codeindex doctor` | 健康/同步检查（CLI、解析器、CLAUDE.md、plugin） |
| `codeindex claude-md update` | 刷新项目 `CLAUDE.md` 中的 codeindex 章节 |

每个命令都支持 `--output json` 输出，用于 CI/CD 和下游工具。

---

## 语言支持

| 语言 | 状态 | 版本 |
|------|------|------|
| Python | ✅ | v0.1.0 |
| PHP | ✅ | v0.5.0 |
| Java | ✅ | v0.7.0 |
| TypeScript / JS | ✅ | v0.19.0 |
| Swift | ✅ | v0.21.0 |
| Objective-C | ✅ | v0.21.0 |
| Go / Rust / C# | 📋 计划中 | — |

**框架路由提取**：ThinkPHP（PHP）、Spring Boot（Java）；Express、Laravel、FastAPI、Django 计划中。

**想添加一门语言？** 基于模板的测试系统让你通过写 YAML 规格来贡献——无需 Python 知识。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 工作原理

codeindex 的文档生成是**两阶段流水线**——结构化是确定性的（tree-sitter，无 AI），AI 增强是可选叠加层。`graph-export` NDJSON（LoomGraph seam）是纯 AST。完整 pipeline + 架构图见 [`docs/architecture/design-philosophy.md`](docs/architecture/design-philosophy.md)。

---

## 致 LoomGraph 开发者

如果你在开发 LoomGraph（面向用户的产品），从这里开始：**[FOR_LOOMGRAPH.md](FOR_LOOMGRAPH.md)**——parser engine 契约、graph-export NDJSON seam、你会接触到的 codeindex 命令。

---

## 文档

### 用户指南

| 指南 | 说明 |
|---|---|
| [入门](docs/guides/getting-started.md) | 安装与首次扫描 |
| [配置指南](docs/guides/configuration.md) | 所有配置项解释 |
| [高级用法](docs/guides/advanced-usage.md) | 并行扫描、自定义 prompt |
| [Git Hooks 集成](docs/guides/git-hooks-integration.md) | 自动化质量检查与文档更新 |
| [Claude Code 集成](docs/guides/claude-code-integration.md) | AI agent 设置与 MCP 技能 |
| [JSON 输出集成](docs/guides/json-output-integration.md) | 机器可读输出 |
| [技术债务分析](docs/guides/tech-debt-analysis.md) | 代码质量分析命令参考 |
| [LoomGraph 集成](docs/guides/loomgraph-integration.md) | graph-export → graph-store 数据流水线 |

### 开发者与架构

| 文档 | 说明 |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 开发环境、TDD 流程、代码风格 |
| [设计哲学](docs/architecture/design-philosophy.md) | 两阶段流水线、两仓架构、设计原则 |
| [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) | 导航契约声明 + README 体积上限 |
| [ADR-009](docs/architecture/adr/009-codeindex-loomgraph-parser-engine.md) | codeindex = LoomGraph parser engine 定位 |
| [发布自动化](docs/development/QUICK_START_RELEASE.md) | 5 分钟自动发布流程 |

### 证据与 benchmark

| 文档 | 内容 |
|---|---|
| [2026-05 README 影响 benchmark](docs/benchmark/2026-05-readme-impact.md) | 带 vs 不带 `README_AI.md` 的 agent 理解差异（15 道评分题，3 项目）。结论：平均快 19% / 省 28% token，但部分细节题质量打平——已修复（ADR-005）。 |
| [`bench/`](bench/) | 可复现的 benchmark 工具（`make setup && make run && make grade && make report`）。 |

---

## 贡献

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[dev,all]"
make install-hooks
make test
```

见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解规范。维护者发布：`make release VERSION=0.X.0`（CI → 测试 → PyPI 发布 → GitHub Release）。

---

## 路线图

**当前版本**：v0.40.0

**下一步**：框架路由扩展（Express、Laravel、FastAPI、Django）；Go、Rust、C# 语言支持。

代码相似度搜索、重构建议、团队协作、IDE 集成在 [LoomGraph](https://github.com/dreamlx/LoomGraph)，不在这里——codeindex 保持无状态解析层定位。

见 [战略路线图](docs/planning/ROADMAP.md) 了解详细计划。

---

## 许可证

[MIT](LICENSE)——免费，并会一直如此。

## 支持

- **提问**：[GitHub Discussions](https://github.com/dreamlx/codeindex/discussions)
- **Bug / 功能请求**：[GitHub Issues](https://github.com/dreamlx/codeindex/issues)
