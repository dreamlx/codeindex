# ROADMAP 更新提案 - Epic 重新分配

**日期**: 2026-02-08
**提案**: 将 Epic 20, 21, 22 从 codeindex 迁移到 LoomGraph

---

## 🎯 架构决策

### 正确的职责分离

| 项目 | 定位 | 核心功能 |
|------|------|----------|
| **codeindex** | Universal Code Parser | AST 解析 + 结构化数据提取 |
| **LoomGraph** | AI-Powered Code Intelligence | 知识图谱 + 高级 AI 分析 |

---

## 📋 Epic 重新分配

### 从 codeindex 移除 (P2 - 低优先级)

以下 Epics 不再在 codeindex 中实现：

#### ❌ Epic 20: 代码相似性搜索
- **原计划**: codeindex v0.16.0+
- **新计划**: LoomGraph v0.3.0
- **原因**: 需要向量化 + 语义检索，LoomGraph 已有 Jina + PGVector

#### ❌ Epic 21: 自动化重构建议
- **原计划**: codeindex v0.17.0+
- **新计划**: LoomGraph v0.4.0
- **原因**: 需要图谱推理 + AI 分析，LoomGraph 已有 Apache AGE + LLM

#### ❌ Epic 22: 团队协作功能
- **原计划**: codeindex v1.0.0
- **新计划**: LoomGraph v0.5.0
- **原因**: 企业功能，知识图谱共享，LoomGraph 更适合

---

## 🎯 更新后的 codeindex Roadmap

### 核心定位: Universal Code Parser

**目标**: 成为最好的多语言代码解析器和结构化数据提取工具

### 版本规划

| 版本 | 目标日期 | Epic | 功能 |
|------|---------|------|------|
| **v0.13.0** | 2026-02-08 ✅ | Epic 12, 13, 14 | 单文件解析 + Parser 重构 + Windows 支持 |
| **v0.13.1** | 2026-02-10 | Epic 10 (完成) | Windows CI 测试 |
| **v0.14.0** | 2026-03-31 | Epic 15 | TypeScript/JavaScript 支持 |
| **v0.15.0** | 2026-05-31 | Epic 16 | Go 语言支持 |
| **v0.16.0** | 2026-07-31 | Epic 17 | 框架路由扩展 (Express, Laravel, FastAPI) |
| **v0.17.0** | 2026-09-30 | Epic 19 | Rust 语言支持 |
| **v0.18.0** | 2026-11-30 | - | C# 语言支持 |
| **v1.0.0** | 2026-12-31 | - | 生产就绪 (8+ 语言) |

### v1.0.0 定义

**Must Have**:
- ✅ 8+ 语言支持 (Python, PHP, Java, TypeScript, Go, Rust, C#, C++)
- ✅ 性能: 1M+ LOC 在 <5min 内解析完成
- ✅ 稳定性: 95%+ 解析成功率
- ✅ 跨平台: Windows, macOS, Linux
- ✅ 文档完整: API 文档 + 示例 + 集成指南

**Removed** (迁移到 LoomGraph):
- ❌ AI 驱动功能 (相似性搜索、重构建议)
- ❌ 团队协作功能
- ❌ IDE 深度集成 (LSP 服务器由 LoomGraph 提供)

---

## 🎯 LoomGraph Roadmap (新增)

### 核心定位: AI-Powered Code Intelligence

**目标**: 基于知识图谱的企业级代码智能平台

### 版本规划

| 版本 | 目标日期 | Epic | 功能 |
|------|---------|------|------|
| **v0.1.0** | 2026-02-03 ✅ | - | 基础索引 + 检索 |
| **v0.2.0** | 2026-02-06 ✅ | - | LightRAG 集成 + PostgreSQL |
| **v0.3.0** | 2026-04-30 | Epic 20 | 代码相似性搜索 ⭐ |
| **v0.4.0** | 2026-06-30 | Epic 21 | 自动化重构建议 ⭐ |
| **v0.5.0** | 2026-08-31 | Epic 22 | 团队协作功能 ⭐ |
| **v0.6.0** | 2026-10-31 | Epic 18 | IDE 集成 (LSP 服务器) |
| **v1.0.0** | 2026-12-31 | - | 企业级知识图谱平台 |

---

## 📊 技术依赖关系

```
codeindex (AST Parser)
    ↓ ParseResult JSON
LoomGraph (Knowledge Graph + AI)
    ↓ Graph API
User Applications (IDE, CI/CD, Team Tools)
```

**数据流**:
1. codeindex 解析代码 → ParseResult JSON
2. LoomGraph 消费 JSON → 构建知识图谱
3. LoomGraph 提供 AI 功能 → 相似性搜索、重构建议、协作
4. 应用层调用 LoomGraph API → IDE 扩展、CI/CD 工具

---

## ✅ 优势分析

### 1️⃣ 单一职责原则

| 项目 | 职责 | 复杂度 | 依赖 |
|------|------|--------|------|
| codeindex | AST 解析 | 低 | tree-sitter only |
| LoomGraph | AI 分析 | 高 | Jina, PostgreSQL, LLM |

**结果**: 各自专注，复杂度可控

### 2️⃣ 性能优化

- codeindex: 轻量级，快速安装
- LoomGraph: 重量级，但有图数据库和向量索引

### 3️⃣ 独立演进

- codeindex 可独立发布新语言支持
- LoomGraph 可独立升级 AI 模型
- 用户可按需选择 (只用 codeindex 或 codeindex + LoomGraph)

### 4️⃣ 商业化路径

- codeindex: 开源工具，社区驱动
- LoomGraph: 企业版，SaaS 服务

---

## 📝 文档更新清单

### codeindex 更新

- [ ] `docs/planning/ROADMAP.md` - 移除 Epic 20, 21, 22
- [ ] `README.md` - 明确定位为 "Code Parser"
- [ ] `CLAUDE.md` - 更新架构说明，指向 LoomGraph

### LoomGraph 更新

- [ ] `docs/planning/ROADMAP.md` - 新增 Epic 20, 21, 22
- [ ] `README.md` - 明确定位为 "AI Code Intelligence"
- [ ] `CLAUDE.md` - 添加 AI 功能说明

### 跨项目文档

- [ ] `codeindex/README.md` - 添加 "与 LoomGraph 集成" 章节
- [ ] `LoomGraph/README.md` - 添加 "与 codeindex 集成" 章节

---

## 🚀 实施计划

### Phase 1: 文档更新 (1 天)
- 更新 codeindex ROADMAP.md
- 更新 LoomGraph ROADMAP.md
- 更新 README.md

### Phase 2: codeindex 聚焦 (继续当前计划)
- v0.13.1: 完成 Epic 10 (Windows CI)
- v0.14.0: Epic 15 (TypeScript)

### Phase 3: LoomGraph 开发 (并行)
- v0.3.0: Epic 20 (代码相似性搜索)
- v0.4.0: Epic 21 (重构建议)

---

## ✅ 决策确认

**提案**: 将 Epic 20, 21, 22 从 codeindex 迁移到 LoomGraph

**理由**:
1. ✅ 符合单一职责原则
2. ✅ 技术栈适配性更好
3. ✅ 独立演进更灵活
4. ✅ 商业化路径更清晰

**影响**:
- codeindex 保持轻量级，专注解析
- LoomGraph 承载 AI 功能，专注图谱
- 用户可按需选择工具链

**风险**: 低 (两个项目已有清晰的架构分层)

---

**结论**: ✅ **强烈建议执行此提案**
