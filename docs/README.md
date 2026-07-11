# codeindex Documentation

codeindex 文档导航。codeindex 是 [LoomGraph](https://github.com/dreamlx/LoomGraph) 的
**parser engine**(the "see" layer):tree-sitter AST → structural slice →
`graph-export` NDJSON。详见 [ADR-009](architecture/adr/009-codeindex-loomgraph-parser-engine.md)。

终端用户 `pipx install loomgraph` 即获全 pipeline(loomgraph 拉取 `ai-codeindex`
为依赖);codeindex 也可 standalone 用于 README_AI.md navigation index。

---

## 📚 按角色

### 用户(使用 codeindex / LoomGraph)

- **[Getting Started](guides/getting-started.md)** — 安装、快速上手、基础用法
- **[Configuration](guides/configuration.md)** — 全部配置项与示例
- **[Advanced Usage](guides/advanced-usage.md)** — 并行扫描、CI/CD、自定义 prompt
- **[graph-export](guides/graph-export.md)** — NDJSON graph export 用法与 schema
- **[LoomGraph Integration](guides/loomgraph-integration.md)** — 两仓数据流
- **[Claude Code Integration](guides/claude-code-integration.md)** — plugin/skills 集成
- **[Git Hooks](guides/git-hooks-integration.md)** — pre/post-commit hooks
- **[JSON Output](guides/json-output-integration.md)** — JSON 输出消费
- **[Contributing](guides/contributing.md)** — TDD workflow、代码风格

### 贡献者(开发 codeindex)

- **[Development Setup](development/setup.md)** — 本地开发环境
- **[Branch & Release Workflow](development/gitflow-workflow.md)** — trunk-based + squash-merge
- **[Test Architecture](development/test-architecture.md)** — 测试体系
- **[Pre-release Checklist](development/pre-release-checklist.md)** — 发布前检查
- **[Quick Start Release](development/QUICK_START_RELEASE.md)** — 发布速查
- **[Package Naming](development/package-naming.md)** — 命名约定
- **[GitHub Issue Quick Reference](development/github-issue-quick-reference.md)** — issue 管理
- **[Team Workflow Guide](development/team-workflow-guide.md)** — 团队协作
- **[Claude Code Adoption Guide](development/claude-code-adoption-guide.md)** / [.zh](development/claude-code-adoption-guide.zh.md)

### 架构与决策

- **[Design Philosophy](architecture/design-philosophy.md)** — 核心设计原则(3 层、What vs Why、ThreadPool)
- **ADR Index**(下表)
- **[Initial Design](architecture/design/initial-design.md)** — 原始设计文档
- **[Design: Document Aggregation](architecture/design/document-aggregation.md)**
- **[Design: KISS Universal Description](architecture/design/kiss-universal-description.md)**
- **[Design: Parallel Strategy](architecture/design/parallel-strategy.md)**

### 规划与发布

- **[ROADMAP](planning/ROADMAP.md)** — 当前方向(single source of truth)
- **[Executive Summary](planning/executive-summary.md)** — 「navigation index,非权威文档」定位论证
- **[Releases](releases/)** — 版本发布说明(major/breaking 才写,CHANGELOG 为每版 ledger)
- **[CHANGELOG](../CHANGELOG.md)** — 完整版本历史(根目录)

### 评估与基准

- **[2026-05 README Impact Benchmark](benchmark/2026-05-readme-impact.md)** — README 对 agent 理解的影响
- **[LoomGraph Efficiency Comparison](evaluation/loomgraph-efficiency-comparison.md)**
- **[Before/After](evaluation/before-after/README.md)** — 前后对比
- **[Case Study: PHP Payment Project](evaluation/case-studies/php-payment-project.md)**

---

## 🗺️ 文档结构

```
docs/
├── README.md                  # 本文件
├── guides/                    # 用户指南
├── development/               # 开发文档
├── planning/                  # ROADMAP + executive summary(无 epic/story 子目录)
├── architecture/
│   ├── design-philosophy.md   # 设计原则
│   ├── adr/                   # Architecture Decision Records(001-009)
│   └── design/                # 设计文档
├── benchmark/                 # 基准测试
├── evaluation/                # 评估与 case study
└── releases/                  # RELEASE_NOTES(major/breaking 版本)
```

---

## 📋 ADR 索引

| ADR | 标题 | 摘要 |
|-----|------|------|
| [001](architecture/adr/001-use-tree-sitter-for-parsing.md) | Use tree-sitter for parsing | tree-sitter vs AST/LSP |
| [002](architecture/adr/002-external-ai-cli-integration.md) | External AI CLI integration | 外部 CLI 作唯一 transport(被 ADR-008 部分反转) |
| [003](architecture/adr/003-add-swift-objc-support.md) | Add Swift/ObjC support | iOS/macOS 解析 |
| [004](architecture/adr/004-automatic-claude-md-update.md) | Automatic CLAUDE.md update | AI agent auto-onboarding |
| [005](architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) | Navigation disclaimer + README size cap | README_AI 是导航索引非权威文档,10KB 边界 |
| [006](architecture/adr/006-distribution-architecture-split.md) | Distribution architecture split | CLI wheel + plugin repo 拆分 |
| [007](architecture/adr/007-codeindex-stateless-graph-ownership.md) | Stateless graph ownership | codeindex 只产 NDJSON,不持图 |
| [008](architecture/adr/008-direct-http-api-ai-default.md) | Direct HTTP API 作默认 AI backend | 部分反转 ADR-002,内置 httpx client |
| [009](architecture/adr/009-codeindex-loomgraph-parser-engine.md) | codeindex 是 LoomGraph 的 parser engine | 产品定位:"see" layer,two repos one product |

---

## 🚀 我要…

- **快速上手** → [Getting Started](guides/getting-started.md)
- **配置 codeindex** → [Configuration](guides/configuration.md)
- **导出 graph NDJSON** → [graph-export guide](guides/graph-export.md)
- **给 LoomGraph 喂数据** → [LoomGraph Integration](guides/loomgraph-integration.md)
- **开发环境** → [Development Setup](development/setup.md)
- **发布新版本** → [Pre-release Checklist](development/pre-release-checklist.md)
- **看路线图** → [ROADMAP](planning/ROADMAP.md)
- **查版本历史** → [CHANGELOG](../CHANGELOG.md)
- **理解架构决策** → [ADR Index](#-adr-索引)

---

## 🤝 贡献文档

发现错别字或想改进文档?Fork → 编辑对应 `.md` → 提 PR。详见
[Contributing Guide](guides/contributing.md)。

---

## 🔗 外部资源

- [LoomGraph](https://github.com/dreamlx/LoomGraph) — the "think + remember" layer
- [tree-sitter](https://tree-sitter.github.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)

**Issues / Discussions**:[github.com/dreamlx/codeindex](https://github.com/dreamlx/codeindex)
