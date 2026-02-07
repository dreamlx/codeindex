# For LoomGraph Developers 🤝

欢迎 LoomGraph 项目组！这是 codeindex 为你们准备的单文件解析功能。

## 🚀 TL;DR

```bash
# 安装 codeindex
pip install ai-codeindex[all]

# 解析单个文件，输出 JSON
codeindex parse src/user.py | jq .
```

## 📚 完整集成指南

**👉 必读文档**: [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md)

包含：
- ✅ 为什么选择 CLI 而不是 Python API（松耦合设计）
- ✅ 完整 JSON 格式规范
- ✅ Python/Node.js 集成代码（可直接复制使用）
- ✅ 批量处理、错误处理、性能优化
- ✅ 单元测试示例

## 🎯 快速示例

### Python Integration (推荐)

```python
import json
import subprocess
from pathlib import Path

def parse_file(file_path: Path) -> dict:
    """使用 codeindex CLI 解析文件"""
    result = subprocess.run(
        ["codeindex", "parse", str(file_path)],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)

# 使用
data = parse_file(Path("src/user.py"))
print(f"Found {len(data['symbols'])} symbols")
```

完整的 wrapper 类和错误处理代码请看集成指南。

## 🔧 替换现有 Python API 调用

### 旧方式 ❌（紧耦合）
```python
from codeindex.parser import parse_file  # 需要安装 codeindex Python 包
result = parse_file(file_path)
```

### 新方式 ✅（松耦合）
```python
import subprocess, json
result = subprocess.run(
    ["codeindex", "parse", str(file_path)],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
```

## 📦 JSON 输出格式

```json
{
  "file_path": "src/user.py",
  "language": "python",
  "symbols": [
    {
      "name": "User",
      "kind": "class",
      "signature": "class User(BaseModel):",
      "line_start": 10,
      "line_end": 50
    }
  ],
  "imports": [...],
  "namespace": "",
  "error": null
}
```

详细字段说明见集成指南。

## ⚡ 性能

- 小文件 (<100行): <0.05s
- 大文件 (1000-5000行): 0.15-0.5s
- 实测 parser.py (1355行): **0.099s**

## 🛡️ Exit Codes

- `0`: 成功
- `1`: 文件不存在或权限错误
- `2`: 不支持的文件类型
- `3`: 解析错误（可能有部分结果）

## 🔗 相关文档

| 文档 | 用途 |
|------|------|
| [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md) | **完整集成指南**（必读） |
| [`README.md`](README.md) 第6节 | 快速开始 |
| [`examples/parse_integration_example.sh`](examples/parse_integration_example.sh) | Shell 脚本示例 |
| [`docs/evaluation/epic12-story12.1-validation.md`](docs/evaluation/epic12-story12.1-validation.md) | 验证报告 |

## 📞 支持

遇到问题？
- GitHub Issues: https://github.com/dreamlx/codeindex/issues
- 查看 CHANGELOG: [`CHANGELOG.md`](CHANGELOG.md)

---

**版本**: codeindex >= 0.13.0
**更新日期**: 2026-02-07
**维护**: codeindex team

**开始集成？** 👉 阅读 [`docs/guides/loomgraph-integration.md`](docs/guides/loomgraph-integration.md)
