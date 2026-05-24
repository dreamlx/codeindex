# PyPI 发布指南

**项目**: codeindex (PyPI: ai-codeindex)
**当前版本**: 0.9.0
**下一版本**: 0.10.0 (Multi-Language LoomGraph Support)

---

## 📋 目录

1. [前置准备](#前置准备)
2. [手动发布流程](#手动发布流程)
3. [自动化发布 (GitHub Actions)](#自动化发布-github-actions)
4. [版本管理](#版本管理)
5. [发布检查清单](#发布检查清单)
6. [故障排除](#故障排除)

---

## 🔧 前置准备

### 1. 注册 PyPI 账号

**生产环境 (PyPI)**:
- 注册: https://pypi.org/account/register/
- 生成 API Token: https://pypi.org/manage/account/token/

**测试环境 (TestPyPI)**:
- 注册: https://test.pypi.org/account/register/
- 生成 API Token: https://test.pypi.org/manage/account/token/

### 2. 配置 PyPI 凭证

**方法 1: 使用 `.pypirc` (本地开发)**

```bash
# 创建 ~/.pypirc 文件
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

# 设置权限
chmod 600 ~/.pypirc
```

**方法 2: 使用环境变量 (CI/CD)**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 安装发布工具

```bash
# 安装 build 和 twine
pip install --upgrade build twine

# 验证安装
python -m build --version
twine --version
```

### 4. 必需文件检查

确保以下文件存在且正确：

```bash
codeindex/
├── LICENSE                  # ✅ MIT License
├── README.md                # ✅ PyPI 页面描述
├── CHANGELOG.md             # ✅ 版本历史
├── pyproject.toml           # ✅ 构建配置
├── src/codeindex/
│   └── __init__.py          # ✅ 版本号定义
└── tests/                   # ✅ 测试套件
```

---

## 🚀 手动发布流程

### Step 1: 版本更新

**1.1 更新版本号**

在 3 个地方同步更新版本号：

```bash
# pyproject.toml
version = "0.7.0"

# src/codeindex/__init__.py (如果有)
__version__ = "0.7.0"

# CHANGELOG.md
## [0.7.0] - 2026-02-04
```

**1.2 更新 CHANGELOG**

将 `[Unreleased]` 的内容移到新版本下：

```markdown
## [0.7.0] - 2026-02-04

### Added
- JSON output mode (Stories 1-5)
- Git Hooks configuration support (Story 6)

### Changed
- (列出变更)

### Fixed
- (列出修复)

## [0.6.0] - 2026-02-04
(之前的版本)
```

**1.3 提交版本更新**

```bash
git add pyproject.toml src/codeindex/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.7.0"
```

### Step 2: 创建 Git Tag

```bash
# 创建标签
git tag v0.7.0 -m "Release v0.7.0: JSON Output + Hooks Config"

# 查看标签
git tag -l -n1 v0.7.0

# 推送到远程（包含标签）
git push origin master --tags
```

### Step 3: 构建分发包

```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建 wheel 和 source distribution
python -m build

# 验证生成的文件
ls -lh dist/
# 应该看到:
#   ai_codeindex-0.7.0-py3-none-any.whl
#   ai_codeindex-0.7.0.tar.gz
```

### Step 4: 测试发布 (TestPyPI)

**强烈推荐先在 TestPyPI 测试！**

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 安装测试
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            ai-codeindex==0.7.0

# 验证安装
codeindex --version
# 应输出: codeindex, version 0.7.0

# 测试核心功能
codeindex init
codeindex scan ./tests

# 卸载测试版本
pip uninstall codeindex -y
```

### Step 5: 正式发布 (PyPI)

```bash
# 上传到 PyPI
twine upload dist/*

# 或指定仓库
twine upload --repository pypi dist/*
```

**上传成功后会显示**:

```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading ai_codeindex-0.7.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading ai_codeindex-0.7.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/ai-codeindex/0.7.0/
```

### Step 6: 验证发布

```bash
# 等待 1-2 分钟（PyPI 索引更新）

# 从 PyPI 安装
pip install ai-codeindex==0.7.0

# 验证版本
pip show codeindex
codeindex --version

# 测试功能
codeindex --help
codeindex hooks status
```

### Step 7: 发布后续

**7.1 创建 GitHub Release**

1. 访问 https://github.com/yourusername/codeindex/releases/new
2. 选择标签: `v0.7.0`
3. 标题: `Release v0.7.0: JSON Output + Hooks Config`
4. 描述: 从 CHANGELOG.md 复制内容
5. 附件: 上传 `dist/ai_codeindex-0.7.0.tar.gz`
6. 点击 "Publish release"

**7.2 更新文档**

```bash
# 更新 README.md badges (如果有)
# 更新安装说明
# 更新版本兼容性表格
```

**7.3 社交媒体通知**

- Twitter/X
- Reddit (r/Python)
- Hacker News
- LinkedIn

---

## 🤖 自动化发布 (GitHub Actions)

### 创建 `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*.*.*'  # 匹配 v0.7.0, v1.0.0 等

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run tests
      run: pytest -v

    - name: Run linter
      run: ruff check src/

  publish:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For PyPI trusted publishing

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install build tools
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build distribution
      run: python -m build

    - name: Check distribution
      run: twine check dist/*

    - name: Publish to TestPyPI
      if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/
        password: ${{ secrets.TEST_PYPI_API_TOKEN }}

    - name: Publish to PyPI
      if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}

  create-release:
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
    - uses: actions/checkout@v4

    - name: Extract changelog
      id: changelog
      run: |
        VERSION=${GITHUB_REF#refs/tags/v}
        sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1 > release_notes.md

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        body_path: release_notes.md
        files: dist/*
        draft: false
        prerelease: false
```

### 配置 GitHub Secrets

1. 访问 https://github.com/yourusername/codeindex/settings/secrets/actions
2. 添加 secrets:
   - `PYPI_API_TOKEN`: PyPI API token
   - `TEST_PYPI_API_TOKEN`: TestPyPI API token

### 使用自动化发布

```bash
# 1. 更新版本号并提交
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.7.0"

# 2. 创建并推送标签
git tag v0.7.0 -m "Release v0.7.0"
git push origin master --tags

# 3. GitHub Actions 自动触发：
#    - 运行测试 (Python 3.10, 3.11, 3.12)
#    - 构建分发包
#    - 上传到 TestPyPI
#    - 上传到 PyPI
#    - 创建 GitHub Release
```

---

## 📊 版本管理

### 语义化版本 (SemVer)

格式: `MAJOR.MINOR.PATCH` (例如: 0.7.0)

- **MAJOR**: 破坏性变更 (不兼容的 API 变更)
- **MINOR**: 新功能 (向后兼容)
- **PATCH**: Bug 修复 (向后兼容)

**示例**:

| 变更类型 | 当前版本 | 新版本 | 说明 |
|---------|---------|--------|------|
| Bug 修复 | 0.6.0 | 0.6.1 | 修复 JSON output bug |
| 新功能 | 0.6.1 | 0.7.0 | 添加 Java 支持 |
| 破坏性变更 | 0.6.0 | 1.0.0 | 移除旧 API |

### 版本号在哪里

**必须更新**:

1. ✅ `pyproject.toml` → `[project] version = "0.7.0"`
2. ✅ `CHANGELOG.md` → `## [0.7.0] - 2026-02-04`
3. ✅ Git tag → `v0.7.0`

**可选更新**:

4. `src/codeindex/__init__.py` → `__version__ = "0.7.0"`
5. `README.md` → badges (自动更新)

### 版本号同步脚本

创建 `scripts/bump_version.sh`:

```bash
#!/bin/bash
# Usage: ./scripts/bump_version.sh 0.7.0

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.7.0"
    exit 1
fi

# 更新 pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# 更新 __init__.py (如果存在)
if [ -f "src/codeindex/__init__.py" ]; then
    sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/codeindex/__init__.py
fi

# 更新 CHANGELOG.md (添加新版本标题)
TODAY=$(date +%Y-%m-%d)
sed -i '' "s/## \[Unreleased\]/## [Unreleased]\n\n## [$NEW_VERSION] - $TODAY/" CHANGELOG.md

echo "✅ Version bumped to $NEW_VERSION"
echo "Next steps:"
echo "1. git add pyproject.toml src/codeindex/__init__.py CHANGELOG.md"
echo "2. git commit -m 'chore: bump version to $NEW_VERSION'"
echo "3. git tag v$NEW_VERSION -m 'Release v$NEW_VERSION'"
echo "4. git push origin master --tags"
```

---

## ✅ 发布检查清单

### 发布前检查

- [ ] **所有测试通过**: `pytest -v`
- [ ] **代码规范检查**: `ruff check src/`
- [ ] **文档更新**: README.md, CHANGELOG.md
- [ ] **版本号同步**: pyproject.toml, __init__.py, CHANGELOG.md
- [ ] **Git 状态干净**: `git status`（无未提交的更改）
- [ ] **分支正确**: 在 `master` 或 `main` 分支
- [ ] **依赖版本锁定**: pyproject.toml 中依赖版本明确

### 构建检查

- [ ] **构建成功**: `python -m build`
- [ ] **分发包完整**: dist/ 包含 `.whl` 和 `.tar.gz`
- [ ] **包元数据正确**: `twine check dist/*`
- [ ] **README 渲染正常**: 在 PyPI 页面预览

### 发布后检查

- [ ] **PyPI 页面正常**: https://pypi.org/project/ai-codeindex/
- [ ] **安装测试**: `pip install ai-codeindex==0.7.0`
- [ ] **版本正确**: `codeindex --version`
- [ ] **核心功能正常**: 运行基本命令
- [ ] **GitHub Release 创建**: https://github.com/yourusername/codeindex/releases
- [ ] **文档站点更新**: (如果有)

---

## 🐛 故障排除

### 问题 1: 上传失败 (403 Forbidden)

**错误信息**:
```
HTTPError: 403 Forbidden from https://upload.pypi.org/legacy/
```

**原因**: API token 无效或权限不足

**解决**:
```bash
# 重新生成 PyPI API token
# 确保 scope 是 "Entire account (all projects)"

# 更新 ~/.pypirc
vim ~/.pypirc

# 或使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 问题 2: 版本已存在

**错误信息**:
```
HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/
File already exists.
```

**原因**: PyPI 不允许覆盖已发布的版本

**解决**:
```bash
# 增加 PATCH 版本号
# 0.7.0 → 0.7.1

# 更新版本号
./scripts/bump_version.sh 0.7.1

# 重新构建
rm -rf dist/
python -m build

# 重新上传
twine upload dist/*
```

### 问题 3: 依赖安装失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement tree-sitter-php>=0.23
```

**原因**: PyPI 上没有该版本的依赖包

**解决**:
```bash
# 检查依赖是否在 PyPI 上
pip search tree-sitter-php  # (已弃用)
# 或访问: https://pypi.org/project/tree-sitter-php/

# 如果依赖不存在，调整版本要求
# pyproject.toml
dependencies = [
    "tree-sitter-php>=0.20",  # 降低版本要求
]
```

### 问题 4: README 在 PyPI 上显示为纯文本

**原因**: README.md 格式或 pyproject.toml 配置错误

**解决**:
```toml
# pyproject.toml
[project]
readme = "README.md"  # ← 确保是 .md 后缀
readme = {file = "README.md", content-type = "text/markdown"}

# 或明确指定
[project.readme]
file = "README.md"
content-type = "text/markdown"
```

### 问题 5: 包导入失败

**错误信息**:
```python
ImportError: cannot import name 'cli' from 'codeindex'
```

**原因**: 包结构配置错误

**解决**:
```toml
# pyproject.toml
[tool.hatch.build.targets.wheel]
packages = ["src/codeindex"]  # ← 确保路径正确

# 检查目录结构
src/
└── codeindex/
    ├── __init__.py
    ├── cli.py
    └── ...
```

### 问题 6: twine 上传超时

**错误信息**:
```
ReadTimeoutError: HTTPSConnectionPool(host='upload.pypi.org'): Read timed out.
```

**解决**:
```bash
# 增加超时时间
twine upload --timeout 300 dist/*

# 或分开上传
twine upload dist/ai_codeindex-0.7.0-py3-none-any.whl
twine upload dist/ai_codeindex-0.7.0.tar.gz

# 检查网络连接
ping upload.pypi.org
```

---

## 📚 相关资源

### 官方文档

- [PyPI Official Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Build Documentation](https://build.pypa.io/)
- [Semantic Versioning](https://semver.org/)

### 工具

- [PyPI](https://pypi.org/) - 生产环境
- [TestPyPI](https://test.pypi.org/) - 测试环境
- [PyPI Stats](https://pypistats.org/) - 下载统计

### codeindex 项目

- **GitHub**: https://github.com/yourusername/codeindex
- **PyPI**: https://pypi.org/project/ai-codeindex/
- **文档**: (待添加)

---

## 🎯 快速参考

### 一键发布命令

```bash
# 完整发布流程
./scripts/release.sh 0.7.0
```

创建 `scripts/release.sh`:

```bash
#!/bin/bash
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "🚀 Releasing codeindex v$VERSION"

# 1. 运行测试
echo "1️⃣  Running tests..."
pytest -v

# 2. 代码检查
echo "2️⃣  Running linter..."
ruff check src/

# 3. 更新版本号
echo "3️⃣  Bumping version..."
./scripts/bump_version.sh $VERSION

# 4. 提交变更
echo "4️⃣  Committing changes..."
git add .
git commit -m "chore: bump version to $VERSION"

# 5. 创建标签
echo "5️⃣  Creating tag..."
git tag v$VERSION -m "Release v$VERSION"

# 6. 构建分发包
echo "6️⃣  Building distributions..."
rm -rf dist/ build/ *.egg-info
python -m build

# 7. 检查分发包
echo "7️⃣  Checking distributions..."
twine check dist/*

# 8. 上传到 TestPyPI
echo "8️⃣  Uploading to TestPyPI..."
twine upload --repository testpypi dist/*

# 9. 测试安装
echo "9️⃣  Testing installation from TestPyPI..."
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            --upgrade ai-codeindex==$VERSION

# 10. 上传到 PyPI
echo "🔟 Uploading to PyPI..."
read -p "Continue with PyPI upload? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    twine upload dist/*

    # 11. 推送到 GitHub
    echo "1️⃣1️⃣ Pushing to GitHub..."
    git push origin master --tags

    echo "✅ Release v$VERSION completed!"
    echo "📦 PyPI: https://pypi.org/project/ai-codeindex/$VERSION/"
    echo "📝 Create GitHub Release: https://github.com/yourusername/codeindex/releases/new?tag=v$VERSION"
else
    echo "❌ Release cancelled"
    exit 1
fi
```

### 常用命令速查

```bash
# 检查当前版本
python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])"

# 清理构建文件
rm -rf dist/ build/ *.egg-info src/*.egg-info

# 构建
python -m build

# 检查
twine check dist/*

# 上传到 TestPyPI
twine upload -r testpypi dist/*

# 上传到 PyPI
twine upload dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ codeindex

# 卸载
pip uninstall codeindex -y
```

---

**最后更新**: 2026-02-04
**作者**: codeindex team
**版本**: 1.0
