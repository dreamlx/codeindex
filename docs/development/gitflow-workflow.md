# 分支与发布工作流

codeindex 实际采用的 git 工作流说明。**已从早期的 GitFlow(develop/release 分支)迁移到
trunk-based + squash-merge**(2026-07,随 develop 分支删除)。

---

## 🌳 分支结构

```
master (受保护，单一集成分支，所有 release 从此打 tag)
  ↑
  ├─ feature/<topic>   短生命周期 feature 分支
  ├─ fix/<topic>       bug 修复分支
  ├─ refactor/<topic>  重构分支
  └─ spike/<topic>     探索性 spike 分支(可不合入)
```

**没有 develop / release 分支**。`master` 既是集成分支也是生产分支，发布靠打 tag
(`vX.Y.Z`)，不另开 release 分支。

---

## 🚀 日常开发工作流

### 1. 开始新工作

```bash
# 从最新 master 切 feature 分支
git checkout master
git pull origin master
git checkout -b feature/<topic-description>
git push -u origin feature/<topic-description>
```

分支命名约定(与历史一致)：`feature/`、`fix/`、`refactor/`、`spike/`，后接
kebab-case 描述，可带 issue 号(`fix/135-scan-all-fixture-pollution`)。

### 2. TDD 开发循环

```bash
# Red: 写测试
pytest tests/test_<module>.py          # 应失败

# Green: 实现
# Refactor: 优化 + lint
ruff check src/
ruff format src/
pytest tests/test_<module>.py          # 应通过
```

### 3. 提交(Conventional Commits)

```bash
git add src/codeindex/<module>.py tests/test_<module>.py
git commit -m "feat(graph-export): add REFERENCES edges (#128 v1, TS/JS)"
```

提交前须跑**全套** pytest(非 `-m "not slow"` —— characterization/golden 不带 slow
标记会静默漏)。`codeindex scan-all` 会污染 `tests/fixtures/char_graphbuffer/`
基线，该目录的 `README_AI.md` 已 gitignore。

### 4. 推送 + 开 PR

```bash
git push origin feature/<topic-description>
```

GitHub 上开 PR，base = `master`。PR 标题用 conventional commit 格式，正文带
`Closes #<issue>`(若关联 issue)。

### 5. Squash-merge + 删分支

PR 通过 CI 与 review 后，**squash-merge** 进 master(单 commit，PR 号附在标题末尾
如 `(#138)`)。合并后 GitHub 自动删除 feature 分支；本地定期 prune：

```bash
git fetch --prune origin
```

---

## 📦 发布流程

发布即打 tag，不开 release 分支：

```bash
# 1. 确认 master 干净且为最新
git checkout master
git pull origin master

# 2. 跑 pre-release 检查(校验 CHANGELOG，RELEASE_NOTES 仅警告)
bash scripts/pre_release_check.sh

# 3. 更新版本号 + CHANGELOG
#    pyproject.toml: version = "X.Y.Z"
#    CHANGELOG.md:   ## [X.Y.Z] - <date> + 条目
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to X.Y.Z"

# 4. 打 tag 并推送
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin master
git push origin vX.Y.Z

# 5.(major/breaking 才写)docs/releases/RELEASE_NOTES_vX.Y.Z.md
```

patch / 常规 minor 不写 RELEASE_NOTES，CHANGELOG 是每版必更的 ledger。
详见 `pre-release-checklist.md`。

---

## 🔧 常用命令速查

```bash
# 分支
git branch -a                    # 全部分支
git checkout -b feature/<topic>  # 新建并切换
git branch -d <branch>           # 删本地(已合并)
git push origin --delete <branch># 删远程
git fetch --prune                # 清理已删远程分支引用

# 同步
git pull origin master
git push origin feature/<topic>

# 提交
git status
git diff
git commit -m "feat(<scope>): <subject>"
git log --oneline -10
```

---

## 📋 Commit Message 规范

[Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>
```

- **type**：`feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `perf`
- **scope**：`graph-export` / `hooks` / `ai` / `parser` / `cli` / `init` 等
- 关联 issue 用 footer `Closes #N` 或标题内 `(#N)`

示例(取自本仓历史)：

```
fix(graph-export): honor explicit include: in .codeindex.yaml (#137)
feat(graph-export): per-symbol content_hash (schema v1, #124) (#125)
fix(java): align call.caller with sym.name (simple class) — Java edges were dangling (#76)
```

---

## ✅ 最佳实践

- **feature 分支短命**(1–3 天)，合并即删，不堆陈旧分支
- **squash-merge** 保留干净线性历史，一个 PR 一个 commit
- **一个 PR 一个主题**，不混无关改动
- **提交前全套 pytest**，不只跑 `not slow`
- **发布靠 tag 不靠分支**，master 随时可发

---

## 🔗 相关文档

- [Conventional Commits](https://www.conventionalcommits.org/)
- [pre-release-checklist.md](pre-release-checklist.md)
- [test-architecture.md](test-architecture.md)
