# 文档重组计划

当前项目根目录有 15 个 Markdown 文档，结构混乱。本文档提供清晰的重组方案。

---

## 📊 当前状态分析

### 根目录文档（15个）

| 文档 | 类型 | 状态 | 问题 |
|------|------|------|------|
| README.md | 项目主文档 | ✅ 保留 | 正确位置 |
| CHANGELOG.md | 变更日志 | ✅ 保留 | 正确位置 |
| CLAUDE.md | 工具配置 | ✅ 保留 | 正确位置 |
| README_AI.md | AI生成索引 | ✅ 保留 | 自动生成 |
| PROJECT_INDEX.md | 项目索引 | ✅ 保留 | 自动生成 |
| PROJECT_SYMBOLS.md | 符号索引 | ✅ 保留 | 自动生成 |
| **EVALUATION_FRAMEWORK.md** | 评估框架 | ⚠️ 待移动 | 应在 docs/ |
| **EXECUTIVE_SUMMARY.md** | 执行摘要 | ⚠️ 待移动 | 应在 docs/ |
| **IMPROVEMENT_PLAN.md** | 改进计划 | ⚠️ 待移动 | 应在 docs/ |
| **IMPROVEMENT_PROPOSALS.md** | 改进提案 | ⚠️ 待移动 | 应在 docs/ |
| **IMPROVEMENT_ROADMAP.md** | 改进路线图 | ⚠️ 待移动 | 应在 docs/ |
| **BEFORE_AFTER_COMPARISON.md** | 改进对比 | ⚠️ 待移动 | 应在 docs/ |
| **DOCUMENT_AGGREGATION_DESIGN.md** | 设计文档 | ⚠️ 待移动 | 应在 docs/ |
| **PARALLEL_STRATEGY_DISCUSSION.md** | 技术讨论 | ⚠️ 待移动 | 应在 docs/ |
| **PHP_PARSER_IMPROVEMENT.md** | 改进讨论 | ⚠️ 待移动 | 应在 docs/ |

### docs/ 目录结构

```
docs/
├── README.md                    # docs 目录总览
├── architecture/                # 架构相关
│   ├── adr/                    # 架构决策记录
│   │   ├── 001-use-tree-sitter-for-parsing.md
│   │   └── 002-external-ai-cli-integration.md
│   └── design/                 # 设计文档
│       └── initial-design.md
├── development/                 # 开发相关
│   └── setup.md
├── guides/                      # 使用指南
│   ├── advanced-usage.md
│   ├── configuration.md
│   ├── contributing.md
│   └── getting-started.md
└── planning/                    # 规划相关
    └── roadmap/
        ├── 2025-Q1.md
        └── dependency-graph-update.md
```

---

## 🎯 重组方案

### 方案1：按文档类型组织（推荐）

```
codeindex/
├── README.md                           # ✅ 保留：项目主文档
├── CHANGELOG.md                        # ✅ 保留：变更日志
├── CLAUDE.md                           # ✅ 保留：Claude Code 配置
├── README_AI.md                        # ✅ 保留：自动生成索引
├── PROJECT_INDEX.md                    # ✅ 保留：自动生成索引
├── PROJECT_SYMBOLS.md                  # ✅ 保留：自动生成索引
│
└── docs/
    ├── README.md                       # docs 目录总览
    │
    ├── architecture/                   # 架构和设计
    │   ├── adr/                       # 架构决策记录（ADR）
    │   │   ├── 001-use-tree-sitter-for-parsing.md
    │   │   ├── 002-external-ai-cli-integration.md
    │   │   └── 003-adaptive-symbol-extraction.md  # 新增
    │   │
    │   └── design/                     # 设计文档
    │       ├── initial-design.md
    │       ├── document-aggregation.md       # 移动：DOCUMENT_AGGREGATION_DESIGN.md
    │       └── parallel-strategy.md          # 移动：PARALLEL_STRATEGY_DISCUSSION.md
    │
    ├── development/                    # 开发相关
    │   ├── setup.md
    │   └── improvements/               # 改进相关（新增目录）
    │       ├── README.md              # 改进总览
    │       ├── php-parser.md          # 移动：PHP_PARSER_IMPROVEMENT.md
    │       └── symbol-scoring.md      # 未来的改进文档
    │
    ├── evaluation/                     # 评估相关（新增目录）
    │   ├── README.md                  # 评估总览
    │   ├── framework.md               # 移动：EVALUATION_FRAMEWORK.md
    │   ├── before-after.md            # 移动：BEFORE_AFTER_COMPARISON.md
    │   └── case-studies/              # 案例研究
    │       └── php-payment-project.md # 移动：examples/EVALUATION_CASE_STUDY.md
    │
    ├── guides/                         # 使用指南
    │   ├── getting-started.md
    │   ├── configuration.md
    │   ├── advanced-usage.md
    │   └── contributing.md
    │
    └── planning/                       # 规划和路线图
        ├── README.md                  # 规划总览
        ├── executive-summary.md       # 移动：EXECUTIVE_SUMMARY.md
        ├── improvement-plan.md        # 移动：IMPROVEMENT_PLAN.md
        ├── improvement-proposals.md   # 移动：IMPROVEMENT_PROPOSALS.md
        ├── improvement-roadmap.md     # 移动：IMPROVEMENT_ROADMAP.md
        │
        └── roadmap/                   # 历史路线图
            ├── 2025-Q1.md
            └── dependency-graph-update.md
```

---

## 📋 详细移动计划

### Phase 1：创建新目录结构

```bash
# 创建评估目录
mkdir -p docs/evaluation/case-studies

# 创建改进目录
mkdir -p docs/development/improvements

# 创建规划总览目录（planning 已存在）
```

### Phase 2：移动文档

#### 1. 架构设计相关 → `docs/architecture/design/`

```bash
# 文档聚合设计
mv DOCUMENT_AGGREGATION_DESIGN.md docs/architecture/design/document-aggregation.md

# 并行策略讨论
mv PARALLEL_STRATEGY_DISCUSSION.md docs/architecture/design/parallel-strategy.md
```

#### 2. 开发改进相关 → `docs/development/improvements/`

```bash
# PHP 解析器改进
mv PHP_PARSER_IMPROVEMENT.md docs/development/improvements/php-parser.md
```

#### 3. 评估相关 → `docs/evaluation/`

```bash
# 评估框架
mv EVALUATION_FRAMEWORK.md docs/evaluation/framework.md

# 改进对比
mv BEFORE_AFTER_COMPARISON.md docs/evaluation/before-after.md

# 案例研究
mv examples/EVALUATION_CASE_STUDY.md docs/evaluation/case-studies/php-payment-project.md
```

#### 4. 规划相关 → `docs/planning/`

```bash
# 执行摘要
mv EXECUTIVE_SUMMARY.md docs/planning/executive-summary.md

# 改进计划（旧版本，可能重复）
mv IMPROVEMENT_PLAN.md docs/planning/improvement-plan-old.md

# 改进提案
mv IMPROVEMENT_PROPOSALS.md docs/planning/improvement-proposals.md

# 改进路线图
mv IMPROVEMENT_ROADMAP.md docs/planning/improvement-roadmap.md
```

### Phase 3：创建目录 README

#### docs/evaluation/README.md

```markdown
# 评估体系

本目录包含 codeindex 的评估框架、对比分析和案例研究。

## 文档列表

- **[framework.md](framework.md)** - 评估框架设计
  - 导航效率评估标准
  - 与深入分析标准的对比
  - 测试用例设计

- **[before-after.md](before-after.md)** - 改进前后对比
  - 核心指标对比
  - 具体案例分析
  - 用户体验对比

- **[case-studies/](case-studies/)** - 案例研究
  - PHP 支付项目评估
  - 其他真实项目案例

## 使用指南

1. 阅读 `framework.md` 了解评估标准
2. 参考 `before-after.md` 查看改进效果
3. 查看 `case-studies/` 了解真实案例
```

#### docs/development/improvements/README.md

```markdown
# 改进和增强

本目录记录 codeindex 的改进提案、技术讨论和实施记录。

## 文档列表

- **[php-parser.md](php-parser.md)** - PHP 解析器改进
  - 命名空间支持
  - 属性解析
  - 框架感知

## 改进流程

1. 在此目录创建改进提案文档
2. 讨论和设计
3. 实施和验证
4. 归档到 ADR（如果是架构级决策）
```

#### docs/planning/README.md

```markdown
# 规划和路线图

本目录包含 codeindex 的规划文档、改进路线图和执行摘要。

## 核心文档

- **[executive-summary.md](executive-summary.md)** - 执行摘要
  - 当前评估问题分析
  - 改进方向总览
  - 行动计划

- **[improvement-roadmap.md](improvement-roadmap.md)** - 改进路线图
  - Phase 1：核心改进（符号评分、自适应提取）
  - Phase 2：评估体系
  - Phase 3：可选增强

- **[improvement-proposals.md](improvement-proposals.md)** - 详细改进提案
  - 提案1：符号重要性评分
  - 提案2：双层索引模式
  - 提案3-5：其他改进

## 历史路线图

- [roadmap/2025-Q1.md](roadmap/2025-Q1.md)
- [roadmap/dependency-graph-update.md](roadmap/dependency-graph-update.md)

## 阅读顺序

1. **executive-summary.md** - 快速了解当前状态
2. **improvement-roadmap.md** - 了解实施计划
3. **improvement-proposals.md** - 深入技术细节
```

### Phase 4：更新引用链接

需要更新引用这些文档的地方：
- README.md
- docs/README.md
- CLAUDE.md
- 其他相关文档

---

## 🎯 重组后的目录结构

### 最终目录树

```
codeindex/
│
├── README.md                           # 项目主文档
├── CHANGELOG.md                        # 变更日志
├── CLAUDE.md                           # Claude Code 配置
├── README_AI.md                        # 自动生成（根目录索引）
├── PROJECT_INDEX.md                    # 自动生成（项目索引）
├── PROJECT_SYMBOLS.md                  # 自动生成（符号索引）
│
├── src/                                # 源代码
├── tests/                              # 测试
├── examples/                           # 示例
│
└── docs/                               # 📚 文档中心
    │
    ├── README.md                       # 文档导航
    │
    ├── architecture/                   # 🏗️ 架构和设计
    │   ├── adr/                       # 架构决策记录
    │   │   ├── 001-use-tree-sitter-for-parsing.md
    │   │   ├── 002-external-ai-cli-integration.md
    │   │   └── 003-adaptive-symbol-extraction.md
    │   │
    │   └── design/                     # 设计文档
    │       ├── initial-design.md
    │       ├── document-aggregation.md
    │       └── parallel-strategy.md
    │
    ├── development/                    # 🛠️ 开发相关
    │   ├── setup.md                   # 开发环境搭建
    │   │
    │   └── improvements/               # 改进记录
    │       ├── README.md
    │       ├── php-parser.md
    │       └── symbol-scoring.md
    │
    ├── evaluation/                     # 📊 评估体系
    │   ├── README.md                  # 评估总览
    │   ├── framework.md               # 评估框架
    │   ├── before-after.md            # 改进对比
    │   │
    │   └── case-studies/              # 案例研究
    │       └── php-payment-project.md
    │
    ├── guides/                         # 📖 使用指南
    │   ├── getting-started.md         # 快速开始
    │   ├── configuration.md           # 配置指南
    │   ├── advanced-usage.md          # 高级用法
    │   └── contributing.md            # 贡献指南
    │
    └── planning/                       # 🗺️ 规划和路线图
        ├── README.md                  # 规划总览
        ├── executive-summary.md       # 执行摘要
        ├── improvement-roadmap.md     # 改进路线图
        ├── improvement-proposals.md   # 改进提案
        │
        └── roadmap/                   # 历史路线图
            ├── 2025-Q1.md
            └── dependency-graph-update.md
```

---

## 📝 文档分类规则

### 保留在根目录的文档

**规则**：面向用户的核心文档 + 自动生成的索引

- ✅ README.md - 项目主文档
- ✅ CHANGELOG.md - 变更日志
- ✅ CLAUDE.md - 工具配置
- ✅ LICENSE - 许可证
- ✅ *_AI.md - 自动生成索引
- ✅ PROJECT_*.md - 自动生成索引

### 移动到 docs/ 的文档

**规则**：技术文档、设计文档、规划文档

#### docs/architecture/
- 架构决策记录（ADR）
- 设计文档
- 技术讨论

#### docs/development/
- 开发环境搭建
- 改进记录
- 技术实现细节

#### docs/evaluation/
- 评估框架
- 对比分析
- 案例研究

#### docs/guides/
- 使用指南
- 配置指南
- 贡献指南

#### docs/planning/
- 规划文档
- 路线图
- 改进提案

---

## 🚀 执行脚本

### 完整执行脚本

```bash
#!/bin/bash

# codeindex 文档重组脚本
set -e

echo "开始文档重组..."

# 1. 创建新目录
echo "创建新目录结构..."
mkdir -p docs/evaluation/case-studies
mkdir -p docs/development/improvements

# 2. 移动架构设计文档
echo "移动架构设计文档..."
[ -f DOCUMENT_AGGREGATION_DESIGN.md ] && mv DOCUMENT_AGGREGATION_DESIGN.md docs/architecture/design/document-aggregation.md
[ -f PARALLEL_STRATEGY_DISCUSSION.md ] && mv PARALLEL_STRATEGY_DISCUSSION.md docs/architecture/design/parallel-strategy.md

# 3. 移动开发改进文档
echo "移动开发改进文档..."
[ -f PHP_PARSER_IMPROVEMENT.md ] && mv PHP_PARSER_IMPROVEMENT.md docs/development/improvements/php-parser.md

# 4. 移动评估文档
echo "移动评估文档..."
[ -f EVALUATION_FRAMEWORK.md ] && mv EVALUATION_FRAMEWORK.md docs/evaluation/framework.md
[ -f BEFORE_AFTER_COMPARISON.md ] && mv BEFORE_AFTER_COMPARISON.md docs/evaluation/before-after.md
[ -f examples/EVALUATION_CASE_STUDY.md ] && mv examples/EVALUATION_CASE_STUDY.md docs/evaluation/case-studies/php-payment-project.md

# 5. 移动规划文档
echo "移动规划文档..."
[ -f EXECUTIVE_SUMMARY.md ] && mv EXECUTIVE_SUMMARY.md docs/planning/executive-summary.md
[ -f IMPROVEMENT_PROPOSALS.md ] && mv IMPROVEMENT_PROPOSALS.md docs/planning/improvement-proposals.md
[ -f IMPROVEMENT_ROADMAP.md ] && mv IMPROVEMENT_ROADMAP.md docs/planning/improvement-roadmap.md
[ -f IMPROVEMENT_PLAN.md ] && mv IMPROVEMENT_PLAN.md docs/planning/improvement-plan-archive.md

echo "文档重组完成！"
echo ""
echo "下一步："
echo "1. 创建 docs/evaluation/README.md"
echo "2. 创建 docs/development/improvements/README.md"
echo "3. 更新 docs/planning/README.md"
echo "4. 更新根目录 README.md 的文档链接"
```

---

## 📖 更新 README.md

### 建议在主 README.md 添加文档导航

```markdown
## 📚 文档

### 快速开始
- [快速开始指南](docs/guides/getting-started.md)
- [配置指南](docs/guides/configuration.md)
- [高级用法](docs/guides/advanced-usage.md)

### 开发相关
- [开发环境搭建](docs/development/setup.md)
- [贡献指南](docs/guides/contributing.md)
- [改进记录](docs/development/improvements/)

### 规划和设计
- [改进路线图](docs/planning/improvement-roadmap.md) - **推荐阅读**
- [执行摘要](docs/planning/executive-summary.md)
- [架构设计](docs/architecture/design/)
- [评估体系](docs/evaluation/)

### 变更记录
- [CHANGELOG](CHANGELOG.md) - 版本变更历史
```

---

## ✅ 执行检查清单

- [ ] 创建新目录结构
- [ ] 移动文档文件
- [ ] 创建目录 README.md
  - [ ] docs/evaluation/README.md
  - [ ] docs/development/improvements/README.md
  - [ ] 更新 docs/planning/README.md
- [ ] 更新根目录 README.md
- [ ] 更新 docs/README.md
- [ ] 更新 CLAUDE.md 中的文档引用
- [ ] 检查所有内部链接
- [ ] 提交 git commit

---

## 🎯 预期效果

### 重组前
```
根目录：15个 MD 文档 ❌ 混乱
```

### 重组后
```
根目录：6个核心文档 ✅ 清晰
docs/：结构化文档树 ✅ 易导航
```

### 用户体验提升
- ✅ 快速找到相关文档
- ✅ 清晰的文档分类
- ✅ 完整的目录导航
- ✅ 易于维护和扩展

---

## 💬 下一步

1. **确认方案**：是否采用此重组方案？
2. **执行重组**：运行脚本或手动移动
3. **创建 README**：为各目录创建导航文档
4. **更新链接**：更新所有文档引用
5. **提交变更**：git commit

**建议立即执行，清理文档结构！**
