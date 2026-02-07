# codeindex 发布自动化系统

**当前版本**: v0.12.1
**最后更新**: 2026-02-07

---

## 核心命令

### 开发环境准备（必须！）
```bash
# ⚠️ CRITICAL: 必须激活虚拟环境
source .venv/bin/activate

# 验证环境
which python3  # 应显示 .venv/bin/python3

# 安装依赖
pip install -e ".[dev,all]"
```

### 发布流程
```bash
# 一键发布命令
make release VERSION=X.X.X

# 等价于以下步骤:
# 1. Pre-release checks (tests, lint, version files)
# 2. Update version in pyproject.toml
# 3. Create Git tag vX.X.X
# 4. Push to origin (master + tag)
# 5. Trigger GitHub Actions for PyPI publishing
```

### 其他常用命令
```bash
make test              # 运行所有测试
make lint              # 代码检查
make lint-fix          # 自动修复 lint 问题
make install-hooks     # 安装 Git hooks
make status            # 查看版本和 Git 状态
make clean             # 清理构建文件
```

---

## Git Hooks

### 安装
```bash
make install-hooks
```

### Pre-push Hook
自动执行：
- Linter 检查 (ruff)
- 测试运行 (pytest)
- master 分支版本一致性检查

**跳过检查**（紧急情况）:
```bash
git push --no-verify
```

---

## GitHub Actions

### CI 测试 (.github/workflows/ci.yml)
**触发**: Push/PR to develop/master

**测试矩阵**:
- Python: 3.10, 3.11, 3.12
- OS: Ubuntu, macOS

**检查项**:
- Linter (ruff check)
- Tests with coverage (pytest --cov)
- Code format (ruff format)
- Build check (python -m build)

### 自动发布 (.github/workflows/publish.yml)
**触发**: Push tag `v*.*.*`

**工作流**:
1. 运行测试 (Python 3.10, 3.11, 3.12)
2. 构建分发包 (wheel + sdist)
3. 发布到 PyPI (Trusted Publisher, 无需 API token)
4. 创建 GitHub Release
5. 附加 RELEASE_NOTES_vX.X.X.md

---

## PyPI Trusted Publisher

**优势**:
- ✅ 无需管理 API tokens
- ✅ 短期凭证（每次发布时动态生成）
- ✅ 仅限指定仓库和 workflow
- ✅ 防止凭证泄露

**配置**: 
- PyPI 项目设置 → Trusted Publishers
- 仓库: dreamlx/codeindex
- Workflow: publish.yml
- Environment: release (可选)

---

## 完整发布示例

```bash
# 0. 确保在虚拟环境中
source .venv/bin/activate
which python3  # 验证

# 1. 在 develop 完成开发
git checkout develop
# ... 开发和测试 ...
git push origin develop

# 2. 准备发布文档
vim docs/planning/ROADMAP.md        # 更新版本和 Epic 状态
vim CHANGELOG.md                    # 添加变更日志
vim RELEASE_NOTES_v0.13.0.md        # 创建发布说明

git add docs/ CHANGELOG.md RELEASE_NOTES_v0.13.0.md
git commit -m "docs: prepare v0.13.0 release documentation"

# 3. 合并到 master
git checkout master
git merge develop --no-ff -m "Merge develop to master for v0.13.0 release"

# 4. 一键发布
make release VERSION=0.13.0

# 5. 监控 GitHub Actions
# https://github.com/dreamlx/codeindex/actions

# 6. 验证发布（5-10 分钟后）
# - PyPI: https://pypi.org/project/ai-codeindex/0.13.0/
# - GitHub: https://github.com/dreamlx/codeindex/releases/tag/v0.13.0
```

---

## 时间对比

**自动化前** (手动流程):
```
1. 更新版本号 (手动编辑)
2. 运行测试
3. 运行 linter
4. 提交版本更新
5. 创建 tag
6. 推送
7. 构建分发包
8. 检查分发包
9. 上传到 PyPI (需要输入密码)
10. 创建 GitHub Release (手动在 Web 界面)

总计: ~20 分钟，容易出错
```

**自动化后**:
```bash
# 准备文档（一次性）
vim ROADMAP.md CHANGELOG.md RELEASE_NOTES_v0.13.0.md
git add docs/ && git commit -m "docs: prepare release"

# 合并到 master
git checkout master
git merge develop --no-ff

# 一键发布
make release VERSION=0.13.0

总计: ~2 分钟，自动化，零错误
```

**时间节省**: 90%
**错误率**: 从 ~20% 降到 ~0%

---

## 常见问题

### Q: 虚拟环境未激活导致的错误
**症状**: `ModuleNotFoundError: No module named 'click'`

**解决**:
```bash
source .venv/bin/activate
pip install -e ".[dev,all]"
```

### Q: Pre-push hook 失败
**原因**: 测试失败或 lint 错误

**解决**:
```bash
# 查看具体错误
make test
make lint

# 紧急情况跳过 hook
git push --no-verify
```

### Q: GitHub Actions 发布失败
**检查**:
1. 测试是否全部通过？
2. RELEASE_NOTES_vX.X.X.md 是否存在？
3. PyPI Trusted Publisher 是否配置正确？

---

## 相关文档

- **快速指南**: `docs/development/QUICK_START_RELEASE.md`
- **完整流程**: `docs/development/release-workflow.md`
- **Makefile**: 运行 `make help` 查看所有命令
- **CONTRIBUTING.md**: 开发规范和 TDD 流程

---

**最后更新**: 2026-02-07
**codeindex 版本**: v0.12.1
