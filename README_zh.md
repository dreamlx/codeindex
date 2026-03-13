# codeindex

[🇬🇧 English](README.md) | [🇨🇳 中文](README_zh.md)

[![PyPI version](https://badge.fury.io/py/ai-codeindex.svg)](https://badge.fury.io/py/ai-codeindex)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/dreamlx/codeindex/workflows/Tests/badge.svg)](https://github.com/dreamlx/codeindex/actions)

**企业级代码智能平台 — 让 AI 智能体通过语义导航理解代码库，而非 grep 搜索。**

codeindex 通过**两阶段流水线**生成 AI 可读的文档：结构化索引（tree-sitter AST 解析）+ AI 驱动的模块功能描述。AI 智能体可以浏览 README_AI.md 层级结构，一眼看到模块用途，直接导航到目标代码 — 支持 Python、PHP、Java、TypeScript、JavaScript、Swift 和 Objective-C。专为**企业内网**隔离环境设计。

**🏢 企业就绪**：✅ 内网兼容 ✅ 自包含 ✅ 版本稳定 ✅ 数据主权

---

> **LoomGraph 开发者**：[`FOR_LOOMGRAPH.md`](FOR_LOOMGRAPH.md)（快速入门）| [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md)（完整指南）

---

## 功能特性

### 核心：面向 AI 智能体的代码理解

- **两阶段文档流水线**（v0.23.0）— 阶段一：SmartWriter 生成结构化 README_AI.md；阶段二：AI 为每个模块生成一句话功能描述。AI 智能体可以浏览 README_AI.md 层级结构，**无需 grep** 即可找到目标模块。
- **智能索引** — 分层文档（概览 → 导航 → 详细），为 AI 智能体优化，每文件 ≤50KB
- **自动 AI 增强** — 配置 `ai_command` 后，`scan-all` 自动启用 AI 模块描述。使用 `--no-ai` 可关闭
- **自动更新钩子** — post-commit 钩子自动为变更目录重新生成 README_AI.md。薄封装模式：`pip upgrade` 自动更新钩子逻辑

### 解析与分析

- **多语言 AST 解析** — Python、PHP、Java、TypeScript、JavaScript、Swift、Objective-C，基于 tree-sitter（Go、Rust、C# 计划中）
- **调用关系提取** — 跨 Python、Java、PHP、TypeScript、JavaScript 的函数/方法调用图
- **继承关系提取** — 类层级和接口关系
- **框架路由提取** — ThinkPHP 和 Spring Boot 路由表（更多计划中）
- **技术债务分析** — 检测大文件、上帝类、符号过载、测试异味
- **单文件解析** — `codeindex parse <file>`，JSON 输出用于工具集成
- **结构化 JSON 输出** — `--output json` 用于 CI/CD、知识图谱和下游工具

### 开发体验

- **自适应符号提取** — 根据文件大小动态提取 5-150 个符号
- **CLAUDE.md 注入** — `codeindex init` 自动配置 Claude Code 集成
- **指南自动更新** — `pip upgrade` 后自动更新 `~/.claude/CLAUDE.md`
- **模板化测试生成** — YAML + Jinja2，快速新增语言支持（节省 88-91% 时间）
- **并行扫描** — 可配置工作线程数的并发目录处理

---

## 使用场景

### 🏢 企业内网（核心场景）

**无需外部工具**：当 Serena MCP 或其他云端代码智能工具因网络隔离或安全策略不可用时，codeindex 成为**首要代码理解工具**。

```bash
# 企业开发者工作流
git clone <内部仓库>
codeindex init                       # 配置项目
codeindex scan-all                   # 结构化 + AI 描述（自动）
# AI 智能体读取 README_AI.md → 看到模块用途 → 直接导航
# 无需 grep 搜索代码
codeindex tech-debt src/ --output review.md  # 代码质量分析
```

**企业选择 codeindex 的理由**：
- ✅ **语义导航** — AI 智能体从 README_AI.md 层级结构理解模块用途
- ✅ **内网兼容** — 无外部依赖，完全离线
- ✅ **自包含** — 不需要上游 MCP 服务器
- ✅ **版本稳定** — 企业自主控制发布周期
- ✅ **数据主权** — 代码永远不会离开内网

---

### 🕸️ 知识图谱集成（LoomGraph）

**面向企业团队**：codeindex 作为 [LoomGraph](https://github.com/dreamlx/LoomGraph) 知识图谱的**核心数据源**，实现跨组织的语义化代码搜索。

```bash
# 数据流水线
codeindex scan --output json > parse_results.json
loomgraph inject parse_results.json  # 构建知识图谱
# 团队可以使用自然语言搜索代码
```

**三仓库架构**：
```
codeindex（解析层）  →  LoomGraph（编排层）  →  LightRAG（存储层）
   ↓ ParseResult          ↓ Embeddings           ↓ 语义搜索
   AST 提取               知识图谱               向量 + 图数据库
```

没有 codeindex，LoomGraph 无法运行。详见 [LoomGraph 集成指南](docs/guides/loomgraph-integration.md)。

---

### 👤 个人开发者（互补使用）

**配合 Serena MCP**：个人开发者使用 Claude Code + Serena MCP 时，codeindex 提供**互补价值**：

- **codeindex**（构建时）：语义化架构地图（带模块描述的 README_AI.md）+ 质量分析
- **Serena**（实时）：精确符号导航（`find_symbol`、`find_referencing_symbols`）

```bash
# 个人开发者工作流
codeindex init                       # 配置 CLAUDE.md 集成
codeindex scan-all                   # 结构化 + AI 描述（自动）
codeindex hooks install post-commit  # 提交时自动更新
# Claude Code 读取 README_AI.md → 理解模块用途 → 使用 Serena 查看细节
```

**关系**：codeindex 提供"带标注的地图"，Serena 提供"GPS 导航"。

---

## 安装

codeindex 使用**延迟加载** — 语言解析器仅在需要时导入。

### 快速安装

```bash
# 所有语言（推荐）
pip install ai-codeindex[all]

# 或仅安装特定语言
pip install ai-codeindex[python]
pip install ai-codeindex[php]
pip install ai-codeindex[java]
pip install ai-codeindex[typescript]
pip install ai-codeindex[python,php]
pip install ai-codeindex[swift]
pip install ai-codeindex[ios]          # Swift + Objective-C
```

### 使用 pipx（推荐用于 CLI）

```bash
pipx install ai-codeindex[all]
```

### 从源码安装

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[all]"
```

---

## 快速开始

### 1. 初始化项目

```bash
cd /your/project
codeindex init
```

创建以下文件：
- `.codeindex.yaml` — 扫描配置（语言、包含/排除模式）
- `CLAUDE.md` — 注入 codeindex 指令，让 Claude Code 自动使用 README_AI.md
- `CODEINDEX.md` — 项目级文档索引

### 2. 扫描代码库

```bash
# 扫描所有目录
# 配置了 ai_command → 自动执行阶段一（结构化）+ 阶段二（AI 描述）
# 未配置 ai_command → 仅执行阶段一（结构化）
codeindex scan-all

# 仅结构化（跳过 AI 增强）
codeindex scan-all --no-ai

# 扫描单个目录
codeindex scan ./src/auth

# 单目录完整 AI 生成
codeindex scan ./src/auth --ai

# 预览 AI 提示词（不执行）
codeindex scan ./src/auth --ai --dry-run
```

### 3. 检查状态

```bash
codeindex status
```

```
索引状态
───────────────────────────────
✅ src/auth/
✅ src/utils/
⚠️  src/api/ (无 README_AI.md)
已索引: 2/3 (67%)
```

### 4. 生成索引

```bash
# 全局符号索引 (PROJECT_SYMBOLS.md)
codeindex symbols

# 模块概览 (PROJECT_INDEX.md)
codeindex index

# Git 变更影响分析
codeindex affected --since HEAD~5
```

### 更多命令

| 命令 | 说明 | 指南 |
|------|------|------|
| `codeindex scan --output json` | JSON 输出用于工具集成 | [JSON 输出指南](docs/guides/json-output-integration.md) |
| `codeindex parse <file>` | 解析单个文件为 JSON | [LoomGraph 集成](docs/guides/loomgraph-integration.md) |
| `codeindex tech-debt ./src` | 代码质量分析（债务 + 测试异味） | v0.22.0 增强 |
| `codeindex hooks install` | Git 钩子自动更新 | [Git Hooks 指南](docs/guides/git-hooks-integration.md) |
| `codeindex config explain <param>` | 参数帮助 | [配置指南](docs/guides/configuration.md) |

---

## Claude Code 集成（个人开发者）

**面向使用 Claude Code + Serena MCP 的个人开发者**：

`codeindex init` 自动将指令注入项目的 `CLAUDE.md`，让 Claude Code 优先读取 `README_AI.md` — 无需手动配置。

```bash
# 一条命令完成配置
codeindex init

# Claude Code 现在会：
# ✅ 优先读取 README_AI.md 理解架构
# ✅ 使用 Serena MCP 工具精确导航（find_symbol 等）
# ✅ 使用 tech-debt 分析代码质量
```

**企业用户（无 Serena）**：README_AI.md 和 PROJECT_SYMBOLS.md 成为你的**首要代码导航工具**。

手动配置、MCP Skills（`/mo:arch`、`/mo:index`）及 Git Hooks 集成，详见 [Claude Code 集成指南](docs/guides/claude-code-integration.md)。

---

## 语言支持

| 语言 | 状态 | 版本 | 主要特性 |
|------|------|------|----------|
| Python | ✅ 已支持 | v0.1.0 | 类、函数、方法、导入、文档字符串、继承、调用 |
| PHP | ✅ 已支持 | v0.5.0 | 类（继承/接口）、方法、属性、PHPDoc、调用 |
| Java | ✅ 已支持 | v0.7.0 | 类、接口、枚举、记录、注解、Spring 路由、Lombok、调用 |
| TypeScript/JS | ✅ 已支持 | v0.19.0 | 类、接口、枚举、类型别名、箭头函数、JSX/TSX、导入/导出、调用 |
| Swift | ✅ 已支持 | v0.21.0 | 类、结构体、枚举、协议、扩展、方法、属性 |
| Objective-C | ✅ 已支持 | v0.21.0 | 类、协议、类别、属性、方法（实例/类） |
| Go | 📋 计划中 | — | 包、接口、结构体方法 |
| Rust | 📋 计划中 | — | 结构体、trait、模块 |
| C# | 📋 计划中 | — | 类、接口、.NET 项目 |

**想添加新语言？** 模板化测试系统让你只需编写 YAML 规范即可贡献 — 无需 Python 知识。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 框架路由提取

| 框架 | 语言 | 状态 |
|------|------|------|
| ThinkPHP | PHP | ✅ 稳定 (v0.5.0) |
| Spring Boot | Java | ✅ 稳定 (v0.8.0) |
| Laravel | PHP | 📋 计划中 |
| FastAPI | Python | 📋 计划中 |
| Django | Python | 📋 计划中 |
| Express.js | JS/TS | 📋 计划中 |

---

## 代码质量分析

### tech-debt：综合质量分析（v0.22.0 增强）

`tech-debt` 命令提供全面的代码质量分析，包含测试异味检测：

```bash
# JSON 输出（用于 LoomGraph 集成）
codeindex tech-debt ./src --format json > debt-data.json

# Markdown 报告（用于文档）
codeindex tech-debt ./src --format markdown > report.md

# 控制台输出（快速检查）
codeindex tech-debt ./src --format console
```

**检测内容**：
- 🔴 **超大文件**（>5000 行）、**大文件**（>2000 行）
- 🔴 **上帝类**（>50 方法）
- 🔴 **超长方法**（>80/150 行）
- 🟡 **高耦合**（>8 个内部导入）
- 🟡 **符号过载**（>100 个符号、高噪音比）
- 🧪 **测试异味**（跳过的测试、超大测试文件）
- 📊 **质量评分**（每文件 0-100 分）

---

## 工作原理

### 两阶段流水线（v0.23.0）

```
阶段一（结构化）：
  目录 → 扫描器 → 解析器 (tree-sitter) → SmartWriter → README_AI.md

阶段二（AI 增强，配置 ai_command 后自动启用）：
  README_AI.md → 符号名 + 文件名 → AI → 一句话描述 → blockquote 注入
```

**阶段一：结构化生成**（始终执行）
1. **扫描器** — 遍历目录，按配置模式过滤
2. **解析器** — 通过 tree-sitter 提取符号（类、函数、导入、调用、继承）
3. **SmartWriter** — 生成分层文档，单文件 ≤50KB
4. **输出** — 为 AI 消费优化的 `README_AI.md`，或 JSON 格式供工具集成

**阶段二：AI 增强**（配置 `ai_command` 后自动启用）
- 为每个非叶子模块生成一句话功能描述
- 写入 blockquote 格式：`> 会员等级管理、积分兑换、权益卡券`
- 每目录约 200-400 tokens，比全量 AI 生成**便宜 10-20 倍**
- 父目录读取子目录描述，实现层级导航

### 前后对比：代码导航

```
之前（仅结构化）：
  └── Application/
      ├── Vip/           — 48 files | 386 symbols     ← AI 无法判断模块用途
      ├── Pay/           — 23 files | 178 symbols
      └── SmallProgramApi/ — 31 files | 245 symbols

之后（结构化 + AI 增强）：
  └── Application/
      ├── Vip/           — 会员等级管理、积分兑换、权益卡券 | 48 files
      ├── Pay/           — 支付网关（支付宝/微信/退款） | 23 files
      └── SmallProgramApi/ — 小程序端API（登录、头像、商品） | 31 files
                             ↑ AI 智能体可以直接导航
```

### 三仓库架构（企业知识图谱）

```
┌────────────────────────────────────────────────────┐
│              企业内网环境                             │
├────────────────────────────────────────────────────┤
│                                                    │
│  📦 代码仓库 (Git)                                  │
│       ↓                                            │
│  🔍 codeindex（解析层）                              │
│       ├── scan --output json → ParseResult         │
│       ├── README_AI.md → 架构文档                    │
│       └── tech-debt → 综合质量分析                    │
│       ↓                                            │
│  🕸️ LoomGraph（编排层）                              │
│       ├── 注入 ParseResult                          │
│       ├── 生成 Embeddings                           │
│       └── 构建知识图谱                               │
│       ↓                                            │
│  💾 LightRAG（存储层）                               │
│       ├── PostgreSQL（图数据）                        │
│       ├── 向量数据库（Embeddings）                    │
│       └── 查询 API（语义搜索）                        │
│       ↓                                            │
│  💬 AI 智能体 (Claude Code、内部 Chat)               │
│       └── 自然语言代码搜索                            │
│                                                    │
└────────────────────────────────────────────────────┘
```

**codeindex 角色**：底层数据采集与解析 — 整个系统依赖 codeindex 提供结构化 ParseResult 数据。

---

## 文档

### 用户指南

| 指南 | 说明 |
|------|------|
| [快速开始](docs/guides/getting-started.md) | 安装和首次扫描 |
| [配置指南](docs/guides/configuration.md) | 所有配置选项说明 |
| [高级用法](docs/guides/advanced-usage.md) | 并行扫描、自定义提示词 |
| [Git Hooks 集成](docs/guides/git-hooks-integration.md) | 自动质量检查和文档更新 |
| [Claude Code 集成](docs/guides/claude-code-integration.md) | AI 智能体配置和 MCP Skills |
| [JSON 输出集成](docs/guides/json-output-integration.md) | 机器可读输出用于工具集成 |
| [LoomGraph 集成](docs/guides/loomgraph-integration.md) | 知识图谱数据流水线 |

### 开发者指南

| 指南 | 说明 |
|------|------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 开发环境搭建、TDD 流程、代码规范 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 和贡献者快速参考 |
| [设计哲学](docs/architecture/design-philosophy.md) | 核心设计原则和架构 |
| [发布自动化](docs/development/QUICK_START_RELEASE.md) | 5 分钟自动化发布流程 |
| [多语言支持](docs/development/multi-language-support-workflow.md) | 新增语言解析器 |

### 规划

- [战略路线图](docs/planning/ROADMAP.md) — 长期愿景和优先级
- [变更日志](CHANGELOG.md) — 版本历史和重大变更

---

## 贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
git clone https://github.com/dreamlx/codeindex.git
cd codeindex
pip install -e ".[dev,all]"
make install-hooks
make test
```

### 发布流程（维护者）

```bash
make release VERSION=0.23.0
# GitHub Actions: 测试 → PyPI 发布 → GitHub Release
```

详见[发布自动化指南](docs/development/QUICK_START_RELEASE.md)。

---

## 路线图

**当前版本**：v0.23.0

**近期里程碑**：
- v0.23.0 — **AI 增强模块描述**：两阶段流水线、自动 AI 增强、post-commit 薄封装
- v0.22.2 — `pip upgrade` 自动更新 CLAUDE.md、`/codeindex-update-guide` Skill
- v0.22.0 — 统一技术债务 + 测试异味分析
- v0.21.0 — Swift 和 Objective-C 语言支持
- v0.19.0 — TypeScript/JavaScript 支持（含调用提取）

**下一步**：
- 框架路由扩展：Express、Laravel、FastAPI、Django（Epic 17）
- Go、Rust、C# 语言支持

**已迁移至 [LoomGraph](https://github.com/dreamlx/LoomGraph)**：
- 代码相似度搜索、重构建议、团队协作、IDE 集成

详见[战略路线图](docs/planning/ROADMAP.md)。

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [tree-sitter](https://tree-sitter.github.io/) — 快速增量解析
- [Claude CLI](https://github.com/anthropics/claude-cli) — AI 集成灵感
- 所有贡献者和用户

## 支持

- **问题咨询**：[GitHub Discussions](https://github.com/dreamlx/codeindex/discussions)
- **Bug 报告**：[GitHub Issues](https://github.com/dreamlx/codeindex/issues)
- **功能建议**：[GitHub Issues](https://github.com/dreamlx/codeindex/issues/new?labels=enhancement)

---

<p align="center">
  Made with ❤️ by the codeindex team
</p>
