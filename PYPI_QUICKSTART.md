# PyPI 发布快速参考

## 🚀 一键发布 (推荐)

```bash
# 完整自动化发布流程
./scripts/release.sh 0.7.0
```

这个脚本会自动：
1. ✅ 运行测试
2. ✅ 运行代码检查
3. ✅ 更新版本号
4. ✅ 提示编辑 CHANGELOG
5. ✅ 提交变更并创建 tag
6. ✅ 构建分发包
7. ✅ 上传到 TestPyPI（可选）
8. ✅ 上传到 PyPI
9. ✅ 推送到 GitHub

---

## 📝 手动发布步骤

### 1. 前置准备（首次发布）

```bash
# 安装发布工具
pip install --upgrade build twine

# 配置 PyPI 凭证
cat > ~/.pypirc <<EOF
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF

chmod 600 ~/.pypirc
```

### 2. 更新版本号

```bash
# 使用脚本（推荐）
./scripts/bump_version.sh 0.7.0

# 或手动编辑
vim pyproject.toml           # version = "0.7.0"
vim src/codeindex/__init__.py  # __version__ = "0.7.0"
vim CHANGELOG.md             # ## [0.7.0] - 2026-02-04
```

### 3. 提交并打标签

```bash
git add .
git commit -m "chore: bump version to 0.7.0"
git tag v0.7.0 -m "Release v0.7.0"
```

### 4. 构建和发布

```bash
# 清理旧文件
rm -rf dist/ build/ *.egg-info

# 构建
python -m build

# 检查
twine check dist/*

# 上传到 TestPyPI（推荐先测试）
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            ai-codeindex==0.7.0

# 验证
codeindex --version

# 上传到 PyPI（正式发布）
twine upload dist/*

# 推送到 GitHub
git push origin master --tags
```

---

## 🤖 使用 GitHub Actions 自动发布

### 配置步骤

1. **获取 PyPI API Token**
   - 访问 https://pypi.org/manage/account/token/
   - 创建新 token（Scope: "Entire account"）
   - 复制 token（只显示一次）

2. **配置 GitHub Secrets**
   - 访问 GitHub 仓库 Settings → Secrets and variables → Actions
   - 添加 secrets:
     - `PYPI_API_TOKEN`: 你的 PyPI token
     - `TEST_PYPI_API_TOKEN`: 你的 TestPyPI token

3. **触发自动发布**
   ```bash
   # 创建并推送标签即可触发
   git tag v0.7.0 -m "Release v0.7.0"
   git push origin master --tags
   ```

4. **查看发布进度**
   - 访问 GitHub → Actions → "Publish to PyPI"
   - 自动运行：测试 → 构建 → 上传 → 创建 Release

---

## 📊 版本号规则

遵循语义化版本 (SemVer)：`MAJOR.MINOR.PATCH`

| 变更类型 | 当前 | 新版本 | 说明 |
|---------|------|--------|------|
| Bug 修复 | 0.6.0 | 0.6.1 | PATCH +1 |
| 新功能 | 0.6.1 | 0.7.0 | MINOR +1 |
| 破坏性变更 | 0.6.0 | 1.0.0 | MAJOR +1 |

---

## ✅ 发布前检查清单

在运行 `./scripts/release.sh` 之前确认：

- [ ] 所有测试通过: `pytest -v`
- [ ] 代码规范通过: `ruff check src/`
- [ ] CHANGELOG.md 已更新
- [ ] 在 master/main 分支
- [ ] 无未提交的更改: `git status`
- [ ] 依赖版本正确
- [ ] README.md 文档完整

---

## 🐛 常见问题

### 上传失败 (403 Forbidden)

```bash
# 检查 API token
cat ~/.pypirc

# 或使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
twine upload dist/*
```

### 版本已存在

```bash
# PyPI 不允许覆盖已发布版本
# 需要增加版本号
./scripts/bump_version.sh 0.7.1
python -m build
twine upload dist/*
```

### README 显示为纯文本

```toml
# pyproject.toml
[project]
readme = "README.md"  # ← 确保是 .md 后缀
```

---

## 📚 完整文档

详细发布指南: [`docs/development/pypi-release-guide.md`](docs/development/pypi-release-guide.md)

包含：
- 前置准备详解
- 手动发布完整流程
- GitHub Actions 自动化
- 版本管理最佳实践
- 故障排除完整指南

---

## 🔗 相关链接

- **PyPI**: https://pypi.org/project/ai-codeindex/
- **TestPyPI**: https://test.pypi.org/project/ai-codeindex/
- **GitHub**: https://github.com/yourusername/codeindex
- **PyPI Guide**: https://packaging.python.org/tutorials/packaging-projects/

---

**快速命令速查**

```bash
# 版本管理
./scripts/bump_version.sh 0.7.0

# 完整发布
./scripts/release.sh 0.7.0

# 手动构建
python -m build

# 检查分发包
twine check dist/*

# 上传 TestPyPI
twine upload -r testpypi dist/*

# 上传 PyPI
twine upload dist/*

# GitHub Actions 发布
git tag v0.7.0 -m "Release v0.7.0"
git push origin master --tags
```
