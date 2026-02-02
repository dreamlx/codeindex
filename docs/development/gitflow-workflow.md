# GitFlow 工作流指南

Phase 1 开发的 GitFlow 分支管理和工作流程。

---

## 🌳 分支结构

```
main (生产分支，受保护)
  ↑
  └─ release/v1.1.0 (发布分支，Phase 1 完成后创建)
       ↑
       └─ develop (开发分支，Phase 1 的集成分支)
            ↑
            ├─ feature/symbol-scorer-base
            ├─ feature/scorer-visibility
            ├─ feature/scorer-semantics
            ├─ feature/scorer-documentation
            ├─ feature/scorer-complexity
            ├─ feature/scorer-naming
            ├─ feature/integrate-scorer
            ├─ feature/adaptive-config
            ├─ feature/adaptive-algorithm
            └─ feature/adaptive-integration
```

---

## 🚀 初始化工作流

### 1. 创建 develop 分支

```bash
# 确保在最新的 main 分支
git checkout main
git pull origin main

# 创建 develop 分支
git checkout -b develop

# 推送到远程
git push -u origin develop

# 在 GitHub 设置 develop 为默认分支（可选）
```

### 2. 保护分支设置（GitHub）

在 GitHub → Settings → Branches：

**保护 main 分支**：
- [x] Require pull request reviews before merging
- [x] Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- [x] Include administrators

**保护 develop 分支**（可选）：
- [x] Require status checks to pass before merging
- [x] Require branches to be up to date before merging

---

## 📝 日常开发工作流

### Story 开发完整流程

#### Step 1: 开始新 Story

```bash
# 1. 确保在最新的 develop
git checkout develop
git pull origin develop

# 2. 创建 feature 分支
# 命名规范: feature/<story-description>
git checkout -b feature/symbol-scorer-base

# 3. 验证分支
git branch
# * feature/symbol-scorer-base
#   develop
```

#### Step 2: TDD 开发循环

```bash
# Red: 编写测试
vim tests/test_symbol_scorer.py
pytest tests/test_symbol_scorer.py  # 应该失败（红灯）

# Green: 实现功能
vim src/codeindex/symbol_scorer.py
pytest tests/test_symbol_scorer.py  # 应该通过（绿灯）

# Refactor: 优化代码
ruff check src/codeindex/symbol_scorer.py
ruff format src/codeindex/symbol_scorer.py
pytest tests/test_symbol_scorer.py  # 确保仍然通过
```

#### Step 3: 提交代码

```bash
# 查看变更
git status
git diff

# 暂存变更
git add src/codeindex/symbol_scorer.py tests/test_symbol_scorer.py

# 提交（使用 Conventional Commits 规范）
git commit -m "feat(scorer): implement symbol scorer base architecture

- Create SymbolImportanceScorer class
- Add ScoringContext dataclass
- Implement score() method framework
- Add comprehensive unit tests (5 test cases)

Tests: 5/5 passing
Coverage: 95%

Closes #STORY-1.1.1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Step 4: 推送到远程

```bash
# 首次推送
git push -u origin feature/symbol-scorer-base

# 后续推送
git push
```

#### Step 5: 创建 Pull Request (PR)

在 GitHub 上：

1. 进入仓库页面
2. 点击 "Pull requests" → "New pull request"
3. Base: `develop` ← Compare: `feature/symbol-scorer-base`
4. 填写 PR 模板：

```markdown
## Story

STORY-1.1.1: 创建评分器基础架构

## Changes

- Create SymbolImportanceScorer class
- Add ScoringContext dataclass
- Implement score() method framework
- Add comprehensive unit tests

## Testing

- [x] All unit tests pass (5/5)
- [x] Coverage ≥ 90% (95%)
- [x] Lint checks pass
- [x] Manual testing completed

## Checklist

- [x] Tests added/updated
- [x] Documentation updated
- [x] Code formatted (ruff)
- [x] No breaking changes
- [x] Ready for review
```

5. 请求代码审查（Request review）

#### Step 6: 代码审查

**审查者检查**：
- [ ] 代码符合项目规范
- [ ] 测试覆盖充分
- [ ] 无明显 bug
- [ ] 性能无明显问题
- [ ] 文档完整

**审查通过后**：
- Approve PR
- 可以合并

#### Step 7: 合并到 develop

**方式 1：通过 GitHub UI**

1. 点击 "Merge pull request"
2. 选择 "Create a merge commit" （推荐）
3. 点击 "Confirm merge"
4. 删除 feature 分支（GitHub 会提示）

**方式 2：本地合并**

```bash
# 1. 切换到 develop
git checkout develop

# 2. 拉取最新代码
git pull origin develop

# 3. 合并 feature 分支（使用 --no-ff 保留分支历史）
git merge --no-ff feature/symbol-scorer-base

# 4. 推送到远程
git push origin develop

# 5. 删除本地 feature 分支
git branch -d feature/symbol-scorer-base

# 6. 删除远程 feature 分支
git push origin --delete feature/symbol-scorer-base
```

---

## 📦 发布流程（Phase 1 完成后）

### Step 1: 创建 release 分支

```bash
# 1. 从 develop 创建 release 分支
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0

# 2. 更新版本号
vim pyproject.toml  # 修改 version = "1.1.0"

# 3. 更新 CHANGELOG
vim CHANGELOG.md  # 添加 v1.1.0 变更记录

# 4. 提交版本更新
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): prepare v1.1.0 release

- Update version to 1.1.0
- Add CHANGELOG entries for Phase 1 improvements

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 5. 推送 release 分支
git push -u origin release/v1.1.0
```

### Step 2: 测试和修复

```bash
# 在 release 分支上进行最后的测试
pytest
ruff check src/

# 如果发现问题，在 release 分支上修复
git commit -m "fix(release): fix issue found in release testing"
```

### Step 3: 合并到 main

```bash
# 1. 切换到 main
git checkout main
git pull origin main

# 2. 合并 release 分支
git merge --no-ff release/v1.1.0

# 3. 创建版本标签
git tag -a v1.1.0 -m "Release v1.1.0: Phase 1 improvements

Features:
- Symbol importance scoring system
- Adaptive symbol extraction
- Improved large file handling

See CHANGELOG.md for details."

# 4. 推送到远程
git push origin main
git push origin v1.1.0
```

### Step 4: 合并回 develop

```bash
# 1. 切换到 develop
git checkout develop

# 2. 合并 release 分支
git merge --no-ff release/v1.1.0

# 3. 推送到远程
git push origin develop
```

### Step 5: 清理 release 分支

```bash
# 删除本地 release 分支
git branch -d release/v1.1.0

# 删除远程 release 分支（可选）
git push origin --delete release/v1.1.0
```

---

## 🔧 常用命令速查

### 分支管理

```bash
# 查看所有分支
git branch -a

# 查看当前分支
git branch

# 切换分支
git checkout <branch-name>

# 创建并切换分支
git checkout -b <branch-name>

# 删除本地分支
git branch -d <branch-name>

# 强制删除本地分支
git branch -D <branch-name>

# 删除远程分支
git push origin --delete <branch-name>
```

### 同步代码

```bash
# 拉取最新代码
git pull origin <branch-name>

# 推送本地代码
git push origin <branch-name>

# 首次推送新分支
git push -u origin <branch-name>
```

### 提交管理

```bash
# 查看状态
git status

# 查看差异
git diff

# 暂存所有变更
git add .

# 暂存特定文件
git add <file-name>

# 提交
git commit -m "message"

# 修改最后一次提交
git commit --amend

# 查看提交历史
git log --oneline -10
```

### 合并和冲突

```bash
# 合并分支（保留分支历史）
git merge --no-ff <branch-name>

# 查看冲突文件
git status

# 解决冲突后继续合并
git add <resolved-file>
git commit

# 取消合并
git merge --abort
```

---

## 📋 Commit Message 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档变更
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（不是新功能，也不是修复）
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建过程或辅助工具变更

### Scope 范围

- `scorer`: 符号评分器
- `adaptive`: 自适应符号提取
- `config`: 配置系统
- `parser`: 解析器
- `writer`: 写入器

### 示例

```bash
# 新功能
git commit -m "feat(scorer): add visibility scoring

- Implement _score_visibility() method
- Support PHP visibility keywords
- Support Python naming conventions

Tests: 6/6 passing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Bug 修复
git commit -m "fix(scorer): handle symbols without signature

- Add null check for symbol.signature
- Return default score for invalid symbols
- Add test for edge case

Fixes #123

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 文档
git commit -m "docs(scorer): add usage examples

- Add docstring examples
- Update README with scoring documentation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 🚨 常见问题

### Q1: 忘记从 develop 创建 feature 分支

```bash
# 如果已经在 main 上开发
git stash  # 暂存当前变更
git checkout develop
git checkout -b feature/my-feature
git stash pop  # 恢复变更
```

### Q2: 需要从 develop 获取最新代码

```bash
# 在 feature 分支上
git checkout develop
git pull origin develop
git checkout feature/my-feature
git merge develop  # 或者使用 rebase
```

### Q3: 解决合并冲突

```bash
# 1. 合并时发生冲突
git merge develop
# CONFLICT (content): Merge conflict in file.py

# 2. 查看冲突文件
git status

# 3. 编辑冲突文件，解决冲突
vim file.py
# 找到 <<<<<<< HEAD ... ======= ... >>>>>>> 标记
# 手动解决冲突

# 4. 标记为已解决
git add file.py

# 5. 完成合并
git commit
```

### Q4: 提交到错误的分支

```bash
# 如果还没有 push
git reset --soft HEAD~1  # 撤销最后一次提交，保留变更
git stash  # 暂存变更
git checkout correct-branch
git stash pop
git commit
```

---

## ✅ 最佳实践

### 1. 分支命名

- ✅ `feature/symbol-scorer-base` - 清晰描述
- ✅ `feature/scorer-visibility` - 简洁明了
- ❌ `feature/fix` - 太模糊
- ❌ `my-branch` - 无意义

### 2. 提交频率

- ✅ 每完成一个小功能就提交
- ✅ 每个测试通过后提交
- ❌ 等到下班才提交一次
- ❌ 一天提交几十次琐碎的修改

### 3. 提交内容

- ✅ 一个提交解决一个问题
- ✅ 相关的变更放在一起
- ❌ 一个提交包含多个不相关的功能
- ❌ 提交包含临时调试代码

### 4. 合并策略

- ✅ 使用 `--no-ff` 保留分支历史
- ✅ 定期从 develop 合并最新代码
- ❌ 使用 fast-forward 合并（丢失分支信息）
- ❌ 长时间不同步 develop（容易冲突）

### 5. 分支生命周期

- ✅ Feature 分支短暂（1-3天）
- ✅ 完成后立即合并和删除
- ❌ Feature 分支存在数周
- ❌ 合并后保留大量废弃分支

---

## 📊 分支状态检查

### 查看分支状态

```bash
# 查看本地分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 查看已合并的分支
git branch --merged

# 查看未合并的分支
git branch --no-merged

# 清理已删除的远程分支引用
git fetch --prune
```

---

## 🔗 相关文档

- [phase1-agile-plan.md](../planning/phase1-agile-plan.md) - Phase 1 开发计划
- [phase1-story-cards.md](../planning/phase1-story-cards.md) - Story 详细卡片
- [Conventional Commits](https://www.conventionalcommits.org/) - 提交规范
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) - Git Flow 原始文章
