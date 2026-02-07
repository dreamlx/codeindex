# Quick Start: Automated Release

**TL;DR**: 一键发布新版本到 PyPI

---

## 🚀 Quick Release (5 分钟)

### 步骤 1: 准备文档 (2 分钟)

```bash
# 更新版本相关文档
vim docs/planning/ROADMAP.md        # 更新版本号和 Epic 状态
vim CHANGELOG.md                    # 添加 v0.13.0 变更日志
vim RELEASE_NOTES_v0.13.0.md        # 创建发布说明

# 提交文档
git add docs/ CHANGELOG.md RELEASE_NOTES_v0.13.0.md
git commit -m "docs: prepare v0.13.0 release documentation"
```

### 步骤 2: 合并到 master (1 分钟)

```bash
git checkout master
git merge develop --no-ff -m "Merge develop to master for v0.13.0 release"
```

### 步骤 3: 一键发布 (30 秒)

```bash
make release VERSION=0.13.0
```

**完成！** 🎉

GitHub Actions 将自动：
- ✅ 运行所有测试
- ✅ 构建分发包
- ✅ 发布到 PyPI
- ✅ 创建 GitHub Release

---

## 📋 完整流程

### 第一次使用

```bash
# 1. 安装 Git hooks (只需一次)
make install-hooks

# 2. 查看可用命令
make help
```

### 日常开发

```bash
# 运行测试
make test

# 运行 linter
make lint

# 自动修复 lint 问题
make lint-fix

# 查看版本状态
make status
```

### 发布新版本

```bash
# 在 master 分支
git checkout master

# 运行发布命令
make release VERSION=0.13.0

# 监控 GitHub Actions
# https://github.com/yourusername/codeindex/actions
```

---

## ⚙️ Makefile 常用命令

| 命令 | 说明 |
|------|------|
| `make test` | 运行所有测试 |
| `make lint` | 运行 linter |
| `make lint-fix` | 自动修复 lint 问题 |
| `make clean` | 清理构建文件 |
| `make build` | 构建分发包 |
| `make status` | 查看版本和 Git 状态 |
| `make release VERSION=X.X.X` | 完整发布流程 |

---

## 🔍 背后发生了什么？

### `make release VERSION=0.13.0` 执行流程

```
1. Pre-release checks
   ├─ 检查工作目录干净
   ├─ 检查在 master 分支
   ├─ 运行所有测试
   ├─ 运行 linter
   └─ 检查 RELEASE_NOTES_v0.13.0.md 存在

2. Version bump
   ├─ 更新 pyproject.toml version = "0.13.0"
   └─ 提交: "chore: bump version to 0.13.0"

3. Git operations
   ├─ 创建 tag: v0.13.0
   ├─ 推送 master 分支
   └─ 推送 tag

4. GitHub Actions (自动触发)
   ├─ 多版本测试 (Python 3.10, 3.11, 3.12)
   ├─ 构建分发包 (wheel + sdist)
   ├─ 发布到 PyPI (Trusted Publisher)
   └─ 创建 GitHub Release
```

---

## 🪝 Git Hooks

### Pre-Push Hook (自动安装)

每次 `git push` 前自动运行：
- Linter 检查
- 测试运行
- 版本一致性检查 (master 分支)

**跳过 hook** (紧急情况):
```bash
git push --no-verify
```

---

## 🐛 常见问题

### Q: 如何回滚发布？

```bash
# 删除本地 tag
git tag -d v0.13.0

# 删除远程 tag
git push origin --delete v0.13.0

# 从 PyPI 删除版本 (不推荐，请联系 PyPI 管理员)
```

### Q: 测试在本地通过，但 CI 失败？

检查：
- Python 版本差异 (CI 测试 3.10, 3.11, 3.12)
- 操作系统差异 (Ubuntu vs macOS)
- 清理缓存: `make clean`

### Q: PyPI 发布失败？

1. 检查 PyPI Trusted Publisher 配置
2. 查看 GitHub Actions 日志
3. 验证权限: `id-token: write`

---

## 📚 详细文档

完整指南请参考：
- [Release Workflow](release-workflow.md) - 完整发布流程
- [GitHub Actions](.github/workflows/) - CI/CD 配置
- [Makefile](../../Makefile) - 所有命令源码

---

**快速链接**:
- 监控发布: https://github.com/yourusername/codeindex/actions
- PyPI 项目: https://pypi.org/project/ai-codeindex/
- GitHub Releases: https://github.com/yourusername/codeindex/releases

---

**Last Updated**: 2026-02-07
**Author**: codeindex team
