# Git Commit 指南

## 📝 提交文档重组

文档已成功重组，现在可以创建 git commit。

---

## 🔍 变更概览

```bash
# 查看所有变更
git status

# 查看文档移动
git status --short
```

---

## ✅ 推荐 Commit 方案

### 方案1：一次性提交（推荐）

```bash
# 添加所有变更
git add .

# 创建提交
git commit -m "docs: reorganize documentation structure

Reorganize all documentation files into structured docs/ directory

Changes:
- Move 9 documents from root to docs/ subdirectories
  - Architecture designs → docs/architecture/design/
  - Development improvements → docs/development/improvements/
  - Evaluation docs → docs/evaluation/
  - Planning docs → docs/planning/

- Create navigation README files
  - docs/evaluation/README.md
  - docs/development/improvements/README.md
  - docs/planning/README.md

- Update documentation index
  - README.md: Add structured doc navigation
  - docs/README.md: Complete rewrite as doc center

- Add documentation guides
  - DOCUMENTATION_REORGANIZATION.md: Reorganization plan
  - DOCUMENTATION_SUMMARY.md: Summary of changes
  - GIT_COMMIT_GUIDE.md: This file

Result:
- Root directory: 8 MD files (was 15) ✅
- docs/ directory: 24 MD files with clear structure ✅
- Improved discoverability and navigation ✅

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 方案2：分步提交

```bash
# 步骤1：移动文档
git add docs/architecture/design/document-aggregation.md
git add docs/architecture/design/parallel-strategy.md
git add docs/development/improvements/php-parser.md
git add docs/evaluation/framework.md
git add docs/evaluation/before-after.md
git add docs/evaluation/case-studies/php-payment-project.md
git add docs/planning/executive-summary.md
git add docs/planning/improvement-proposals.md
git add docs/planning/improvement-roadmap.md
git add docs/planning/improvement-plan-archive.md

git commit -m "docs: move documents to appropriate directories

Move 9 documents from root to structured subdirectories:
- Architecture/design: 2 files
- Development/improvements: 1 file
- Evaluation: 3 files
- Planning: 4 files

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 步骤2：新增导航文档
git add docs/evaluation/README.md
git add docs/development/improvements/README.md
git add docs/planning/README.md

git commit -m "docs: add navigation README files for subdirectories

Create README.md files for:
- docs/evaluation/
- docs/development/improvements/
- docs/planning/

Each README provides overview and navigation for its directory.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 步骤3：更新主文档
git add README.md
git add docs/README.md

git commit -m "docs: update main documentation index

- README.md: Add structured documentation navigation
- docs/README.md: Complete rewrite as documentation center

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 步骤4：添加重组文档
git add DOCUMENTATION_REORGANIZATION.md
git add DOCUMENTATION_SUMMARY.md
git add GIT_COMMIT_GUIDE.md

git commit -m "docs: add reorganization documentation

- DOCUMENTATION_REORGANIZATION.md: Reorganization plan
- DOCUMENTATION_SUMMARY.md: Summary of changes
- GIT_COMMIT_GUIDE.md: Git commit guide

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 🚫 需要删除的文件

如果 git 显示已删除的文件（原位置的文档），这是正常的：

```bash
# 查看已删除的文件
git status | grep deleted

# 确认删除
git add -u  # 添加所有删除操作
```

**已删除的文件应该包括**：
- DOCUMENT_AGGREGATION_DESIGN.md
- PARALLEL_STRATEGY_DISCUSSION.md
- PHP_PARSER_IMPROVEMENT.md
- EVALUATION_FRAMEWORK.md
- BEFORE_AFTER_COMPARISON.md
- EXECUTIVE_SUMMARY.md
- IMPROVEMENT_PROPOSALS.md
- IMPROVEMENT_ROADMAP.md
- IMPROVEMENT_PLAN.md

---

## 📊 验证提交

提交前验证：

```bash
# 查看即将提交的变更
git diff --cached --stat

# 预览提交信息
git log -1 --pretty=format:"%B"
```

---

## 🔧 如果需要修改

### 撤销暂存

```bash
# 撤销所有暂存
git reset

# 撤销特定文件
git reset HEAD <file>
```

### 修改最后一次提交

```bash
# 修改提交信息
git commit --amend

# 添加遗漏的文件
git add <file>
git commit --amend --no-edit
```

---

## ✅ 提交后验证

```bash
# 查看提交历史
git log --oneline -5

# 查看详细变更
git show HEAD

# 验证目录结构
tree docs/ -L 2
```

---

## 📤 推送到远程

```bash
# 推送到远程仓库
git push origin master

# 如果是新分支
git push -u origin docs-reorganization
```

---

## 🎯 建议

**推荐使用方案1（一次性提交）**，原因：
- ✅ 变更逻辑统一（文档重组）
- ✅ 更清晰的提交历史
- ✅ 更容易回滚（如需要）
- ✅ 符合 Conventional Commits 规范

---

## 📝 Commit Message 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>: <subject>

<body>

<footer>
```

**Type**：
- `docs`: 文档变更
- `feat`: 新功能
- `fix`: Bug 修复
- `refactor`: 代码重构

**本次提交**：
- Type: `docs`
- Subject: "reorganize documentation structure"
- Body: 详细变更列表
- Footer: Co-Authored-By

---

## 🎉 完成

执行推荐的 commit 命令后，文档重组就正式完成了！

下一步可以继续进行：
1. 实施改进计划（docs/planning/improvement-roadmap.md）
2. 验证文档链接
3. 更新 CHANGELOG.md
