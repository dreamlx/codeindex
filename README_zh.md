# codeindex

[🇬🇧 English](README.md) | [🇨🇳 中文](README_zh.md)

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

**让 AI coding agent 靠阅读而非 grep 来导航你的代码库。**

codeindex 是一个**开源 CLI**，通过**两阶段流水线**把任意代码库转化为 AI 可读的导航索引（`README_AI.md`）——结构化索引（tree-sitter AST）+ 可选的一行式 AI 模块描述。Agent 浏览 README_AI.md 层级结构，看清每个模块的职责，直接跳到正确的文件——覆盖 Python、PHP、Java、TypeScript、JavaScript、Swift 和 Objective-C。可量化的收益是效率，而非魔法（见下方 benchmark）。

**完全离线运行。** 结构化索引根本不需要 AI；AI 描述使用*你自己*的本地 agent CLI（例如 `claude -p`），所以代码不会离开你的网络——适用于物理隔离的内网。MIT 许可、免费，并且会一直如此：codeindex 是开源的*导航*层；推理/检索层位于 [LoomGraph](FOR_LOOMGRAPH.md)。

---

## 它真的能帮到 agent 吗？我们做了测量。

大多数"AI 代码理解"工具只是宣称自己有价值。我们对自己的工具做了 A/B 测试——并把那些不光彩的部分也公开了。

在 **3 个异构真实项目上的 15 道评分制导航题**中，一个 coding agent **带** `README_AI.md` 对比**不带**：

- **平均 −28% token、−19% 墙钟时间**——agent 更快、更省地抵达正确文件。
- **答案质量打平。** 它*不会*让答案更*正确*——赢的是效率，而非能力。（一个缺乏纪律的索引甚至在几道精确机制题上拖了后腿；已在 [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) 中修复。）
- **在最大的代码库上收益最小。** 在一个 250 个目录的遗留系统上，token 收益几近消失——扁平索引能指给你文件，却无法综合跨模块语义。codeindex 是*导航*层，不是*理解一切*层（精确机制请搭配源码阅读 / [Serena](https://github.com/oraios/serena)）。

包含失败案例的完整数据：**[2026-05 benchmark](docs/benchmark/2026-05-readme-impact.md)**。在你自己的仓库上复现：**[`bench/`](bench/)**（`make setup && make run && make grade`）。

> 为什么要公开那些不为工具增光的部分：一个悄悄拉低答案质量的导航索引比没有更糟。知道它*确切*在哪里有帮助——以及在哪里该退回源码——才是重点。

---

> **致 LoomGraph 开发者**：[`FOR_LOOMGRAPH.md`](FOR_LOOMGRAPH.md)（快速上手）| [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md)（完整指南）

---

## 特性

### 核心：面向 AI Agent 的代码理解

- **两阶段文档流水线**（v0.23.0）——阶段 1：通过 SmartWriter 生成结构化 README_AI.md；阶段 2：AI 为每个模块生成一行式功能描述。AI agent 可以浏览 README_AI.md 层级结构并找到正确的模块，**无需 grep**。
- **智能索引**——分层文档（概览 → 导航 → 详细），为 AI agent 优化，每个文件 ≤10KB（导航索引，而非技术文档——见 [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md)）
- **自动 AI 增强**——当配置了 `ai_command` 时，`scan-all` 会自动启用 AI 模块描述。使用 `--no-ai` 退出

### 解析与分析

- **多语言 AST 解析**——通过 tree-sitter 支持 Python、PHP、Java、TypeScript、JavaScript、Swift、Objective-C；更多语言可通过 extractor API 接入（`src/codeindex/extractors/`，社区贡献）
- **调用关系提取**——跨 Python、Java、PHP、TypeScript、JavaScript 的函数/方法调用图
- **继承关系提取**——类层级与接口关系
- **框架路由提取**——ThinkPHP 与 Spring Boot 路由表（更多计划中）
- **技术债务分析**——检测大文件、上帝类、符号过载、测试坏味
- **单文件解析**——`codeindex parse <file>`，JSON 输出，便于工具集成
- **结构化 JSON 输出**——`--output json`，用于 CI/CD、知识图谱及下游工具

### 开发者体验

- **自适应符号提取**——根据文件大小动态提取每文件 5–150 个符号
- **CLAUDE.md 注入**——`codeindex init` 把 codeindex 章节注入到你的**项目的** `CLAUDE.md`（绝不碰 `~/.claude`）
- **Claude Code 插件**——通过 [dreamlx/codeindex-claude](https://github.com/dreamlx/codeindex-claude) 提供 `codeindex:arch` / `:index` / `:hooks` / `:update-guide` 技能
- **基于模板的测试生成**——YAML + Jinja2 实现快速语言支持（节省 88–91% 时间）
- **并行扫描**——并发目录处理，worker 数可配置

---

## 使用场景

### 🏢 企业内网（核心场景）

**没有外部工具时**：当 Serena MCP 或其他基于云的代码智能工具因网络隔离或安全策略而不可用时，codeindex 成为**主力代码理解工具**。

```bash
# 企业开发者工作流
git clone <internal-repo>
codeindex init                       # 配置项目
codeindex scan-all                   # 结构化 + AI 描述（自动）
# AI agent 读取 README_AI.md → 看清模块用途 → 直接导航
# 代码发现无需 grep
codeindex tech-debt src/ --output review.md  # 代码质量分析
```

**企业为何选择 codeindex**：
- ✅ **语义导航**——AI agent 从 README_AI.md 层级结构理解模块用途
- ✅ **内网兼容**——无外部依赖，完全离线
- ✅ **自包含**——无需上游 MCP 服务器
- ✅ **版本稳定**——企业可控的发布周期
- ✅ **数据主权**——代码绝不离开内网

---

### 🕸️ 知识图谱集成（LoomGraph）

**面向企业团队**：codeindex 作为 [LoomGraph](https://github.com/dreamlx/LoomGraph) 知识图谱的**核心数据源**，支持全组织范围的语义代码搜索。

```bash
# 数据流水线
codeindex scan --output json > parse_results.json
loomgraph inject parse_results.json  # Build knowledge graph
# Team can now search code using natural language
```

**两仓库架构**：
```
codeindex (Parse)         →   LoomGraph (Store + Query)
   ↓ graph-export NDJSON        ↓ SQLite + sqlite-vec
   AST extraction               知识图谱 + 向量检索 + MCP
```

codeindex 是无状态的解析层；LoomGraph 是自包含的知识图谱（SQLite + sqlite-vec，
无需外部 RAG 框架）。没有 codeindex，LoomGraph 就无内容可索引。参见 [LoomGraph 集成指南](docs/guides/loomgraph-integration.md)。

---

### 👤 个人开发者（互补）

**搭配 Serena MCP**：对于使用 Claude Code + Serena MCP 的个人开发者，codeindex 提供**互补价值**：

- **codeindex**（构建期）：语义架构地图（带模块描述的 README_AI.md）+ 质量分析
- **Serena**（实时）：精确符号导航（`find_symbol`、`find_referencing_symbols`）

```bash
# 个人开发者工作流
codeindex init                    # 配置 CLAUDE.md 集成
codeindex scan-all                # 结构化 + AI 描述（自动）
# Claude Code 读取 README_AI.md → 理解模块用途 → 用 Serena 查细节
```

**关系**：codeindex 提供"带标注的地图"，Serena 提供"GPS 导航"。

---

## 安装

codeindex 是一个 CLI 工具——用 **pipx** 安装（隔离环境，无依赖冲突）：

```bash
pipx install ai-codeindex
```

> **Claude Code 用户**——同时安装配套插件以获得技能
> （`codeindex:arch` / `:index` / `:hooks` / `:update-guide`）：
> ```
> /plugin marketplace add dreamlx/codeindex-claude
> /plugin install codeindex@codeindex-claude
> ```
> 该插件是可选的，仅供 Claude Code 使用。CLI 在任意编辑器 / 终端中均可独立工作。参见 [dreamlx/codeindex-claude](https://github.com/dreamlx/codeindex-claude)。

### 语言解析器

codeindex 使用**惰性加载**——语言解析器仅在需要时导入。
`pipx install ai-codeindex` 默认拉取全部解析器。若想之后向 pipx 环境注入额外解析器，或安装一个子集：

```bash
pipx inject ai-codeindex tree-sitter-python tree-sitter-typescript   # add to pipx env
# or pin a subset at install time:
pipx install "ai-codeindex[python]"      # python only
pipx install "ai-codeindex[ios]"         # Swift + Objective-C
```

### pipx 的替代方案

```bash
pip install --user ai-codeindex          # if you don't have pipx
```

> **🇨🇳 中国用户**：如果你默认的镜像（如阿里云）尚未同步最新版本，可直接从上游 PyPI 安装：
> ```bash
> pipx install --index-url https://pypi.org/simple/ ai-codeindex
> ```

### 从源码安装

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"
```

---

## 快速上手

### 1. 初始化你的项目

```bash
cd /your/project
codeindex init
```

这会创建：
- `.codeindex.yaml` —— 扫描配置（语言、include/exclude 模式）
- `CLAUDE.md` —— 注入 codeindex 指令，使 Claude Code 自动使用 README_AI.md
- `CODEINDEX.md` —— 项目级文档参考

### 2. 扫描你的代码库

```bash
# 扫描所有目录
# 当配置了 ai_command 时 → 自动执行阶段 1（结构化）+ 阶段 2（AI 描述）
# 没有 ai_command 时 → 仅阶段 1（结构化）
codeindex scan-all

# 仅结构化（跳过 AI 增强）
codeindex scan-all --no-ai

# 扫描单个目录
codeindex scan ./src/auth

# 为单个目录生成完整的 AI 生成 README
codeindex scan ./src/auth --ai

# 预览 AI prompt 而不执行
codeindex scan ./src/auth --ai --dry-run
```

### 3. 查看状态

```bash
codeindex status
```

```
Indexing Status
───────────────────────────────
✅ src/auth/
✅ src/utils/
⚠️  src/api/ (no README_AI.md)
Indexed: 2/3 (67%)
```

### 4. 生成索引

```bash
# 全局符号索引（PROJECT_SYMBOLS.md）
codeindex symbols

# 模块概览（PROJECT_INDEX.md）
codeindex index

# Git 变更影响分析
codeindex affected --since HEAD~5
```

### 更多命令

| 命令 | 描述 | 指南 |
|---------|-------------|-------|
| `codeindex scan --output json` | 面向工具的 JSON 输出 | [JSON Output Guide](docs/guides/json-output-integration.md) |
| `codeindex parse <file>` | 将单文件解析为 JSON | [LoomGraph Integration](docs/guides/loomgraph-integration.md) |
| `codeindex tech-debt ./src` | 代码质量分析（技术债 + 测试坏味） | v0.22.0 增强 |
| `codeindex debt-scan ./src` | tech-debt 的别名 | 向后兼容 |
| `codeindex hooks install` | 用于自动更新的 Git hook | [Git Hooks Guide](docs/guides/git-hooks-integration.md) |
| `codeindex doctor` | 健康/同步检查（CLI、解析器、CLAUDE.md、插件） | 只读诊断 |
| `codeindex config explain <param>` | 参数帮助 | [Configuration Guide](docs/guides/configuration.md) |

---

## Claude Code 集成

**codeindex 插件**为 Claude Code 提供四个由 CLI 支撑的技能：

```
/plugin marketplace add dreamlx/codeindex-claude
/plugin install codeindex@codeindex-claude
```

| 技能 | 它的作用 |
|-------|--------------|
| `codeindex:arch` | 从 `README_AI.md` 回答架构 / "X 在哪里" 类问题 |
| `codeindex:index` | 引导你完成 `codeindex init` → `scan-all` |
| `codeindex:update-guide` | 刷新你项目 `CLAUDE.md` 中的 codeindex 章节 |

`codeindex init` 还会把 codeindex 章节注入到你项目的 `CLAUDE.md`，
使 Claude Code 优先读取 `README_AI.md` 文件。（自 v0.25.0 起，`init` 只
触碰项目范围的文件——见 [ADR-006](docs/architecture/adr/006-distribution-architecture-split.md)。）

**对于没有 Serena 的企业用户**：README_AI.md 和 PROJECT_SYMBOLS.md 成为你的**主力代码导航工具**。

> 插件技能并不取代 `codeindex claude-md` / `codeindex hooks`
> CLI 命令——而是编排它们。这些命令对仅使用 CLI 的用户（Cursor、脚本）
> 仍是一等公民；技能则在其之上叠加引导式的 Claude Code 体验。

---

## 语言支持

| 语言 | 状态 | 起始版本 | 关键特性 |
|----------|--------|-------|-------------|
| Python | ✅ 已支持 | v0.1.0 | 类、函数、方法、imports、docstring、继承、调用 |
| PHP | ✅ 已支持 | v0.5.0 | 类（extends/implements）、方法、属性、PHPDoc、继承、调用 |
| Java | ✅ 已支持 | v0.7.0 | 类、接口、枚举、record、注解、Spring 路由、Lombok、调用 |
| TypeScript/JS | ✅ 已支持 | v0.19.0 | 类、接口、枚举、类型别名、箭头函数、JSX/TSX、imports/exports、调用 |
| Swift | ✅ 已支持 | v0.21.0 | 类、结构体、枚举、协议、扩展、方法、属性 |
| Objective-C | ✅ 已支持 | v0.21.0 | 类、协议、category、属性、方法（实例/类） |
| Go | 📋 计划中 | — | 包、接口、结构体方法 |
| Rust | 📋 计划中 | — | 结构体、trait、模块 |
| C# | 📋 计划中 | — | 类、接口、.NET 项目 |

**想添加一门语言？** 基于模板的测试系统让你通过编写 YAML 规格来贡献——无需 Python 知识。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 框架路由提取

| 框架 | 语言 | 状态 |
|-----------|----------|--------|
| ThinkPHP | PHP | ✅ 稳定（v0.5.0） |
| Spring Boot | Java | ✅ 稳定（v0.8.0） |
| Laravel | PHP | 📋 计划中 |
| FastAPI | Python | 📋 计划中 |
| Django | Python | 📋 计划中 |
| Express.js | JS/TS | 📋 计划中 |

---

## 代码质量分析

### tech-debt：全面质量分析（v0.22.0 增强）

`tech-debt` 命令提供全面的代码质量分析，现在包含测试坏味检测：

```bash
# JSON 输出（用于 LoomGraph 集成）
codeindex tech-debt ./src --format json > debt-data.json

# Markdown 报告（用于文档）
codeindex tech-debt ./src --format markdown > report.md

# 控制台输出（用于快速检查）
codeindex tech-debt ./src --format console

# 别名：debt-scan 也可用（向后兼容）
codeindex debt-scan ./src --format json
```

**它能检测什么**：
- 🔴 **超大文件**（>5000 行）、**大文件**（>2000 行）
- 🔴 **上帝类**（>50 个方法）
- 🔴 **超长方法**（>80/150 行）
- 🟡 **高耦合**（>8 个内部 imports）
- 🟡 **符号过载**（>100 个符号，高噪声比）
- 🧪 **测试坏味**（被跳过的测试、巨型测试文件）—— **v0.22.0 新增**
- 📊 **质量评分**（每文件 0-100 分）

**增强的 JSON 输出（v0.22.0）**：
```json
{
  "timestamp": "2026-03-06T13:45:39Z",
  "summary": {
    "total_files": 97,
    "giant_files": 0,
    "giant_functions": 3,
    "test_smells": 64,
    "avg_maintainability": 9.9
  },
  "total_files": 97,
  "average_quality_score": 99.4,
  "giant_files": [],
  "giant_functions": [...],
  "test_smells": [
    {
      "path": "tests/test_example.py",
      "type": "skipped_test",
      "details": "Skipped test detected: @pytest.mark.skip at line 42",
      "line_number": 42
    }
  ],
  "file_reports": [...]
}
```

**关键特性**：
- ✅ **统一命令**：所有质量检查的单一入口
- ✅ **向后兼容**：保留所有现有 JSON 字段
- ✅ **LoomGraph 就绪**：增强的 summary 便于知识图谱集成
- ✅ **框架无关**：跨 Jest、pytest、JUnit 等检测测试坏味
- ✅ **KISS 设计**：90% 代码复用，用简单正则模式做测试检测

---

## 工作原理

### 两阶段流水线（v0.23.0）

```
Phase 1 (Structural):
  Directory → Scanner → Parser (tree-sitter) → SmartWriter → README_AI.md

Phase 2 (AI Enrichment, automatic when ai_command configured):
  README_AI.md → symbol names + file names → AI → one-line description → blockquote injection
```

**阶段 1：结构化生成**（始终运行）
1. **Scanner** —— 遍历目录，按配置模式过滤
2. **Parser** —— 通过 tree-sitter 提取符号（类、函数、imports、调用、继承）
3. **SmartWriter** —— 生成带大小限制的分层文档（≤50KB）
4. **Output** —— 为 AI 消费优化的 `README_AI.md`，或用于工具集成的 JSON

**阶段 2：AI 增强**（配置 `ai_command` 时自动启用）
- 为每个非叶子模块生成一行式功能描述
- 以 blockquote 形式写入：`> 会员等级管理、积分兑换、权益卡券`
- 每个目录约 200-400 token，比完整 AI 生成便宜 10-20 倍
- 父目录读取子目录描述以实现层级化导航

### 前后对比：代码导航

```
Before (structural only):
  └── Application/
      ├── Vip/           — 48 files | 386 symbols     ← AI agent cannot determine purpose
      ├── Pay/           — 23 files | 178 symbols
      └── SmallProgramApi/ — 31 files | 245 symbols

After (structural + AI enrichment):
  └── Application/
      ├── Vip/           — 会员等级管理、积分兑换、权益卡券 | 48 files
      ├── Pay/           — 支付网关（支付宝/微信/退款） | 23 files
      └── SmallProgramApi/ — 小程序端API（登录、头像、商品） | 31 files
                             ↑ AI agent can navigate directly
```

### 两仓库架构（企业知识图谱）

```
┌────────────────────────────────────────────────────┐
│            Enterprise Intranet Environment          │
├────────────────────────────────────────────────────┤
│                                                    │
│  📦 Code Repository (Git)                          │
│       ↓                                            │
│  🔍 codeindex (Parse Layer — 无状态)               │
│       ├── graph-export → NDJSON 图谱制品           │
│       ├── README_AI.md → architecture docs         │
│       └── tech-debt → comprehensive quality scan   │
│       ↓                                            │
│  🕸️ LoomGraph (Store + Query — 有状态)             │
│       ├── import-export ← codeindex NDJSON         │
│       ├── SQLite + sqlite-vec（图谱 + 向量）       │
│       ├── embeddings + KNN 语义检索                │
│       └── query CLI + MCP server                   │
│       ↓                                            │
│  💬 AI Agents (Claude Code, Internal Chat)         │
│       └── Natural language code search (MCP)       │
│                                                    │
└────────────────────────────────────────────────────┘
```

> **注**：LightRAG + PostgreSQL 已不在此流程中。LoomGraph 本地化改造后用内嵌的
> SQLite + sqlite-vec 取代（"no RAG framework needed"）。

**codeindex 角色**：底层（解析）——LoomGraph 以 codeindex 的 `graph-export` NDJSON
为唯一数据接缝；codeindex 自身保持无状态（ADR-007）。

---

## 文档

### 用户指南

| 指南 | 描述 |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | 安装与首次扫描 |
| [Configuration Guide](docs/guides/configuration.md) | 所有配置项详解 |
| [Advanced Usage](docs/guides/advanced-usage.md) | 并行扫描、自定义 prompt |
| [Git Hooks Integration](docs/guides/git-hooks-integration.md) | 自动化质量检查与文档更新 |
| [Claude Code Integration](docs/guides/claude-code-integration.md) | AI agent 配置与 MCP 技能 |
| [JSON Output Integration](docs/guides/json-output-integration.md) | 面向工具的机器可读输出 |
| [LoomGraph Integration](docs/guides/loomgraph-integration.md) | 知识图谱数据流水线 |

### 开发者指南

| 指南 | 描述 |
|-------|-------------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 开发环境搭建、TDD 工作流、代码风格 |
| [CLAUDE.md](CLAUDE.md) | 面向 Claude Code 和贡献者的快速参考 |
| [Design Philosophy](docs/architecture/design-philosophy.md) | 核心设计原则与架构 |
| [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) | 2026-05：导航契约免责声明 + 大小上限，由 benchmark 支撑 |
| [Release Automation](docs/development/QUICK_START_RELEASE.md) | 5 分钟自动化发布工作流 |
| [Multi-Language Support](docs/development/multi-language-support-workflow.md) | 添加新语言解析器 |
| [Language Support Contribution](docs/development/multi-language-support-workflow.md) | 面向新语言的基于模板的测试生成 |

### 证据与 benchmark

| 文档 | 它展示了什么 |
|---|---|
| [2026-05 README impact benchmark](docs/benchmark/2026-05-readme-impact.md) | 在 3 个异构项目上测量 agent 在带 vs 不带 `README_AI.md` 时的理解差异（15 道评分题）。要点：平均快 19% / 少 28% token，但速度收益在某些细节题上掩盖了质量下降——修复已发布（见 ADR-005）。 |
| [`bench/`](bench/) | 用于产出上述 benchmark 的可复现测试框架（Makefile + python）；在你自己环境运行：`cd bench && make setup && make run && make grade && make report`。 |

### 规划

- [Strategic Roadmap](docs/planning/ROADMAP.md) —— 长期愿景与优先级
- [Changelog](CHANGELOG.md) —— 版本历史与破坏性变更

---

## 贡献

我们欢迎贡献！指南见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[dev,all]"
make install-hooks
make test
```

### 发布流程（维护者）

```bash
make release VERSION=0.17.0
# GitHub Actions: tests → PyPI publish → GitHub Release
```

详见 [Release Automation Guide](docs/development/QUICK_START_RELEASE.md)。

---

## 路线图

**当前版本**：v0.25.0

**近期里程碑**：
- v0.23.0 —— **AI 增强的模块描述**：两阶段流水线、自动 AI 增强、post-commit 薄包装
- v0.22.2 —— `pip upgrade` 时自动更新 CLAUDE.md、`/codeindex-update-guide` 技能
- v0.22.0 —— 统一的 tech-debt + 测试坏味分析
- v0.21.0 —— Swift & Objective-C 语言支持
- v0.19.0 —— 带调用提取的 TypeScript/JavaScript 支持

**下一步**：
- 框架路由扩展：Express、Laravel、FastAPI、Django（Epic 17）
- Go、Rust、C# 语言支持

**已迁移至 [LoomGraph](https://github.com/dreamlx/LoomGraph)**：
- 代码相似度搜索、重构建议、团队协作、IDE 集成

详细规划见 [Strategic Roadmap](docs/planning/ROADMAP.md)。

---

## 许可证

MIT License —— 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [tree-sitter](https://tree-sitter.github.io/) —— 快速、增量的解析
- [Claude CLI](https://github.com/anthropics/claude-cli) —— AI 集成灵感
- 所有贡献者与用户

## 支持

- **提问**：[GitHub Discussions](https://github.com/dreamlx/codeindex/discussions)
- **Bug**：[GitHub Issues](https://github.com/dreamlx/codeindex/issues)
- **功能请求**：[GitHub Issues](https://github.com/dreamlx/codeindex/issues/new?labels=enhancement)

---

<p align="center">
  Made with ❤️ by the codeindex team
</p>
