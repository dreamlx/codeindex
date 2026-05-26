# 项目命名说明

## 📦 命名空间设计

本项目采用**分离命名空间**策略，在不同场景使用不同名称：

| 类型 | 名称 | 用途 | 示例 |
|------|------|------|------|
| **PyPI 包名** | `ai-codeindex` | 用户安装 | `pip install ai-codeindex` |
| **GitHub 仓库** | `codeindex` | 代码托管 | `github.com/username/codeindex` |
| **CLI 命令** | `codeindex` | 命令行使用 | `codeindex scan ./src` |
| **Python 导入** | `codeindex` | 代码中导入 | `import codeindex` |
| **包目录** | `codeindex` | 源码组织 | `src/codeindex/` |

## 🎯 为什么这样设计？

### 1. PyPI 名称冲突

**问题**：PyPI 上已有 `codeindex` 项目（语义搜索客户端，2025-12-02 更新）

**解决**：使用 `ai-codeindex` 作为 PyPI 包名
- ✅ 清晰表达 AI-native 特性
- ✅ 避免名称冲突
- ✅ SEO 友好（搜索 "ai codeindex" 可直接找到）

### 2. 用户体验优先

**保持简洁的用户接口**：

```bash
# 安装时使用完整名称（明确标识）
pip install ai-codeindex

# 使用时简洁（提高效率）
codeindex --version
codeindex scan ./src

# 代码中简洁（可读性好）
import codeindex
from codeindex import Parser
```

### 3. 品牌一致性

**GitHub 仓库名保持 `codeindex`**：
- ✅ 简短易记的 URL：`github.com/username/codeindex`
- ✅ 项目文档中统一使用 `codeindex`
- ✅ 避免用户混淆

## 📚 类似案例

许多知名项目都采用这种策略：

```bash
# PyPI 包名 ≠ GitHub 仓库名
pip install Pillow              # → github.com/python-pillow/Pillow
pip install beautifulsoup4      # → github.com/wention/BeautifulSoup4
pip install scikit-learn        # → github.com/scikit-learn/scikit-learn
pip install python-dateutil     # → github.com/dateutil/dateutil
pip install msgpack-python      # → github.com/msgpack/msgpack-python
```

## 🔗 项目链接

### 官方链接

- **PyPI**: https://pypi.org/project/ai-codeindex/
- **TestPyPI**: https://test.pypi.org/project/ai-codeindex/
- **GitHub**: https://github.com/yourusername/codeindex
- **Documentation**: https://github.com/yourusername/codeindex#readme

### 安装

```bash
# 从 PyPI 安装
pip install ai-codeindex

# 从 GitHub 安装
pip install git+https://github.com/yourusername/codeindex.git

# 开发模式
git clone https://github.com/yourusername/codeindex.git
cd codeindex
pip install -e ".[dev]"
```

## 📝 文档中的引用规则

### README.md 和用户文档

- **安装命令**：使用 `pip install ai-codeindex`
- **CLI 使用**：使用 `codeindex` 命令
- **项目名称**：可使用 "codeindex" 或 "ai-codeindex"
- **链接引用**：PyPI 链接使用 `ai-codeindex`，GitHub 链接使用 `codeindex`

### 代码示例

```python
# ✅ 正确：导入时使用 codeindex
import codeindex
from codeindex import Parser

# ✅ 正确：安装说明中使用 ai-codeindex
# pip install ai-codeindex
```

## 🚀 发布流程

### PyPI 发布

```bash
# 1. 构建（自动使用 pyproject.toml 中的 ai-codeindex）
python -m build

# 2. 检查
twine check dist/*
# 输出: Checking dist/ai_codeindex-0.7.0-py3-none-any.whl: PASSED

# 3. 上传
twine upload dist/*
# 上传到: https://pypi.org/project/ai-codeindex/
```

### GitHub 发布

```bash
# 标签使用版本号（不含包名）
git tag v0.7.0 -m "Release v0.7.0"
git push origin master --tags

# GitHub Release 标题
"Release v0.7.0: JSON Output + Hooks Config"
```

## 🔧 配置文件

### pyproject.toml

```toml
[project]
name = "ai-codeindex"  # ← PyPI 包名
# ...

[project.scripts]
codeindex = "codeindex.cli:main"  # ← CLI 命令名

[tool.hatch.build.targets.wheel]
packages = ["src/codeindex"]  # ← Python 包名
```

### setup.py (如果使用)

```python
setup(
    name="ai-codeindex",      # PyPI 包名
    packages=["codeindex"],   # Python 包名
    entry_points={
        "console_scripts": [
            "codeindex=codeindex.cli:main",  # CLI 命令
        ],
    },
)
```

## ❓ 常见问题

### Q: 用户会不会困惑？

A: 不会。这是 Python 生态系统的常见做法，用户习惯了：
- 安装时用 PyPI 包名（`pip install ai-codeindex`）
- 使用时用简短命令（`codeindex`）

### Q: import 时用什么名称？

A: 使用 `import codeindex`（不是 `import ai-codeindex`）
- Python 导入名称由包目录决定（`src/codeindex/`）
- 与 PyPI 包名无关

### Q: 需要修改哪些文件？

A: 只需修改以下文件中的 **安装命令** 和 **PyPI 链接**：
- ✅ `pyproject.toml` → `name = "ai-codeindex"`
- ✅ `README.md` → `pip install ai-codeindex`
- ✅ 发布文档 → PyPI URLs
- ❌ 不改：CLI 命令、import 语句、GitHub URLs

### Q: 如何搜索项目？

A: 多种方式都可以找到：
- PyPI: 搜索 "ai-codeindex" 或 "codeindex"
- GitHub: 搜索 "codeindex"
- Google: "ai codeindex" 或 "codeindex python"

## 📊 命名决策历史

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-02-04 | 原始包名：`codeindex` | 简短、直观 |
| 2026-02-04 | 发现冲突：PyPI 已有 `codeindex` | 2025-12-02 更新的语义搜索项目 |
| 2026-02-04 | 更改为：`ai-codeindex` | 避免冲突，强调 AI-native 特性 |
| 2026-02-04 | 保持：CLI 命令仍为 `codeindex` | 用户体验优先 |

---

**最后更新**: 2026-02-04
**维护者**: codeindex team
