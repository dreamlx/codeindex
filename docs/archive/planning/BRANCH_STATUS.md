# 分支和版本组织说明

**生成时间**: 2026-02-04
**当前分支**: `feature/epic-json-output`
**当前版本**: 0.6.0 → 准备发布 0.7.0

---

## 📊 当前状态总览

### Master 分支 (生产环境)
```
Branch: master
Version: v0.6.0 (已发布 2026-02-04)
Latest: "Release v0.6.0: Epic 9 (Docstring Extraction)"
```

### 当前功能分支
```
Branch: feature/epic-json-output
Based on: master (commit d13d641)
Commits ahead: 19 commits
Target version: 0.7.0 (待发布)
```

---

## 🎯 功能分支包含的新特性

### 1. JSON Output Mode (Epic: JSON Output Integration)
**Stories 1-5 已完成**
- ✅ `--output json` 标志（machine-readable 输出）
- ✅ 结构化错误处理（ErrorCode, ErrorInfo）
- ✅ ParseResult 序列化（符号、导入、元数据）
- ✅ 文件级错误检测（tree-sitter `has_error`）
- ✅ 完整文档（CLAUDE.md, README.md, CHANGELOG.md）

### 2. Git Hooks Configuration (Story 6)
**已完成**
- ✅ `.codeindex.yaml` 完整配置支持
- ✅ 5种模式：auto, disabled, async, sync, prompt
- ✅ 智能检测：≤2目录=同步，>2=异步
- ✅ 非阻塞异步模式（后台更新）
- ✅ 14个配置测试用例

### 3. PyPI 发布基础设施
**已完成**
- ✅ GitHub Actions 自动发布工作流
- ✅ 完整发布脚本（bump_version.sh, release.sh）
- ✅ 详细文档（pypi-release-guide.md, PYPI_QUICKSTART.md）
- ✅ 包名重命名：codeindex → ai-codeindex

### 4. 包命名策略
**已完成**
- ✅ PyPI 包名：`ai-codeindex` （避免冲突）
- ✅ GitHub 仓库：`codeindex` （保持简洁）
- ✅ CLI 命令：`codeindex` （用户体验优先）
- ✅ Python 导入：`import codeindex` （代码一致性）
- ✅ 完整说明文档（PACKAGE_NAMING.md）

---

## 🔢 版本号说明

### 为什么是 0.7.0？

根据语义化版本（SemVer）规则：

```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     └─ Bug修复: 0.6.0 → 0.6.1
  |     └─────── 新功能:   0.6.0 → 0.7.0  ← 我们在这里
  └───────────── 破坏性变更: 0.x.x → 1.0.0
```

**我们的变更属于 MINOR（新功能）**：
- 新增 `--output json` 标志
- 新增 Git Hooks 配置系统
- 无破坏性变更（向后兼容）

### 之前文档中的 0.5.1 是什么？

**这是一个错误示例版本号**，已在 commit `4035b38` 中全部更正为 0.7.0：
- ❌ 0.5.1 会导致版本倒退（master 已经是 0.6.0）
- ✅ 0.7.0 是正确的下一版本

---

## 📂 Git 分支结构

```
master (v0.6.0)
    │
    ├─ d13d641 (Merge Epic 9)
    │
    └── feature/epic-json-output (19 commits ahead)
         │
         ├─ fb3ad90 Epic JSON Output planning
         ├─ d9c40ec Story 1: ParseResult serialization
         ├─ 5a89ba2 Stories 2 & 3: --output json
         ├─ 8d6bbb4 Story 4: structured error handling
         ├─ 3437fa3 Story 5: documentation
         ├─ 9a6c24b Story 6: Git Hooks config
         ├─ feee6c5 PyPI release infrastructure
         ├─ 58bca2a Package rename to ai-codeindex
         └─ 4035b38 Update version examples to 0.7.0  ← 当前位置
```

---

## 🚀 下一步计划（3个选项）

### 选项 A: 直接发布 v0.7.0 到 Master ⭐ 推荐

**优点**：
- ✅ 最快发布路径
- ✅ 功能完整且测试通过
- ✅ 文档齐全，用户可立即使用

**步骤**：
```bash
# 1. 切换到 master 分支
git checkout master

# 2. 合并功能分支
git merge feature/epic-json-output --no-ff

# 3. 运行发布脚本（自动化版本更新）
./scripts/release.sh 0.7.0

# 脚本会自动：
# - 运行测试和 lint
# - 更新 pyproject.toml 和 __init__.py
# - 更新 CHANGELOG.md (手动编辑)
# - 创建 commit 和 tag
# - 构建分发包
# - 上传到 TestPyPI (可选)
# - 上传到 PyPI
# - 推送到 GitHub

# 4. 发布完成后删除功能分支
git branch -d feature/epic-json-output
```

**时间**：约 10-15 分钟（含手动编辑 CHANGELOG）

---

### 选项 B: 通过 Develop 分支（严格 GitFlow）

**优点**：
- ✅ 遵循严格的 GitFlow 规范
- ✅ 多人协作时更安全
- ✅ 可以批量合并多个功能

**步骤**：
```bash
# 1. 切换到 develop 分支（如果没有则创建）
git checkout -b develop master

# 2. 合并功能分支到 develop
git merge feature/epic-json-output --no-ff

# 3. 测试 develop 分支
pytest -v
ruff check src/

# 4. 从 develop 创建 release 分支
git checkout -b release/0.7.0 develop

# 5. 在 release 分支更新版本号
./scripts/bump_version.sh 0.7.0

# 6. 合并到 master 并发布
git checkout master
git merge release/0.7.0 --no-ff
git tag v0.7.0 -m "Release v0.7.0: JSON Output + Hooks Config"
git push origin master --tags

# 7. 合并回 develop
git checkout develop
git merge release/0.7.0 --no-ff
git push origin develop

# 8. 删除 release 分支
git branch -d release/0.7.0
```

**时间**：约 20-25 分钟

---

### 选项 C: 继续在功能分支开发

**适用场景**：
- 还有其他功能要添加
- 想等待更多测试反馈
- 计划批量发布多个 Epic

**步骤**：
```bash
# 保持在 feature/epic-json-output 分支
git checkout feature/epic-json-output

# 继续开发新功能...
# (例如：Epic JSON Output Story 7-9)

# 等待合适时机再合并到 master
```

---

## 📝 发布前检查清单

无论选择哪个选项，发布前必须确认：

### 代码质量
- [ ] 所有测试通过: `pytest -v`
- [ ] 代码规范通过: `ruff check src/`
- [ ] 无未提交的更改: `git status`
- [ ] Git Hooks 已安装并测试

### 文档完整性
- [ ] CHANGELOG.md 已更新（将 [Unreleased] 移到 [0.7.0]）
- [ ] README.md 包含所有新功能说明
- [ ] CLAUDE.md 包含 JSON output 和 hooks 示例
- [ ] API 文档同步更新

### 版本号一致性
- [ ] `pyproject.toml`: `version = "0.7.0"`
- [ ] `src/codeindex/__init__.py`: `__version__ = "0.7.0"`
- [ ] `CHANGELOG.md`: `## [0.7.0] - 2026-02-04`

### PyPI 发布准备
- [ ] PyPI API Token 已配置（~/.pypirc）
- [ ] TestPyPI 测试安装成功
- [ ] GitHub Actions 工作流已测试
- [ ] LICENSE 文件存在（MIT）

---

## 🎯 我的建议

**推荐：选项 A（直接发布 v0.7.0）**

**理由**：
1. ✅ **功能完整**：JSON Output + Hooks Config 都已完成并测试
2. ✅ **文档齐全**：用户可以立即使用
3. ✅ **测试通过**：所有测试用例都通过
4. ✅ **影响可控**：都是新增功能，不影响现有用户
5. ✅ **用户需求**：JSON output 对工具集成很重要

**发布后收益**：
- 用户可以使用 `--output json` 集成到自己的工具链
- Git Hooks 配置让用户可以自定义更新策略
- PyPI 发布让安装更简单（`pip install ai-codeindex`）

---

## 🤝 需要您确认

请选择您希望采用的方案：

**A. 立即发布 v0.7.0** - 运行 `./scripts/release.sh 0.7.0`
**B. 使用 GitFlow** - 先合并到 develop 分支
**C. 继续开发** - 在功能分支上添加更多特性

---

## 📞 后续步骤

确认方案后，我将：
1. 按照您选择的方案执行合并/发布流程
2. 更新 CHANGELOG.md（需要您审核）
3. 运行完整测试套件
4. 执行发布脚本
5. 验证 PyPI 发布成功
6. 创建 GitHub Release

---

**文档版本**: 1.0
**生成工具**: Claude Code
**项目**: codeindex (ai-codeindex on PyPI)
