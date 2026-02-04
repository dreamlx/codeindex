# JSON 输出集成指南

**版本**: v0.7.0
**目标用户**: codeindex 使用者、工具开发者、AI Agent

---

## 📖 概述

codeindex v0.7.0+ 支持 JSON 格式输出，用于：
- 工具集成（如 LoomGraph 代码知识图谱）
- 自动化脚本处理
- AI Agent 工作流
- 数据分析和可视化

---

## 🚀 快速开始

### 基础用法

```bash
# 生成 JSON 输出到 stdout
codeindex scan ./src --output json

# 保存到文件
codeindex scan ./src --output json > parse_results.json

# 使用 jq 查询
codeindex scan ./src --output json | jq '.summary'

# 扫描整个项目
codeindex scan-all --output json > project_analysis.json
```

### 与 LoomGraph 集成

```bash
# Step 1: 解析代码
codeindex scan-all --output json > parse_results.json

# Step 2: 生成向量
loomgraph embed parse_results.json --output embeddings.json

# Step 3: 注入图谱
loomgraph inject parse_results.json embeddings.json

# Step 4: 搜索代码
loomgraph search "用户认证逻辑"
```

---

## 📋 JSON 格式规范

### 成功响应

```json
{
  "success": true,
  "results": [
    {
      "path": "src/auth/user.py",
      "symbols": [
        {
          "name": "UserService",
          "kind": "class",
          "signature": "class UserService:",
          "docstring": "User management service",
          "line_start": 10,
          "line_end": 50
        },
        {
          "name": "UserService.login",
          "kind": "method",
          "signature": "def login(self, username: str, password: str) -> bool:",
          "docstring": "Authenticate user with credentials",
          "line_start": 12,
          "line_end": 25
        }
      ],
      "calls": [
        {
          "caller": "UserService.login",
          "callee": "db.find_user",
          "line": 15
        }
      ],
      "inheritances": [
        {
          "child": "UserService",
          "parent": "BaseService"
        }
      ],
      "imports": [
        {
          "module": "typing",
          "names": ["Optional", "Dict"],
          "is_from": true
        }
      ],
      "module_docstring": "User authentication module",
      "file_lines": 100,
      "error": null
    }
  ],
  "summary": {
    "total_files": 25,
    "total_symbols": 350,
    "total_calls": 890,
    "total_inheritances": 45,
    "total_imports": 120,
    "errors": 0
  }
}
```

### 字段说明

#### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 命令是否成功执行 |
| `results` | array | ParseResult 数组，每个元素对应一个文件 |
| `summary` | object | 统计信息 |
| `error` | object | 错误信息（仅当 success: false） |

#### ParseResult 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `path` | string | 文件路径（相对路径） |
| `symbols` | array | 符号列表（类、函数、方法） |
| `calls` | array | 调用关系列表 |
| `inheritances` | array | 继承关系列表 |
| `imports` | array | 导入列表 |
| `module_docstring` | string | 模块文档字符串 |
| `file_lines` | integer | 文件总行数 |
| `error` | string | 解析错误信息（null 表示无错误） |

#### Symbol 字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | 符号名称 | `"UserService"`, `"UserService.login"` |
| `kind` | string | 符号类型 | `"class"`, `"function"`, `"method"` |
| `signature` | string | 函数/方法签名 | `"def login(self, username: str) -> bool:"` |
| `docstring` | string | 文档字符串 | `"Authenticate user credentials"` |
| `line_start` | integer | 起始行号 | `10` |
| `line_end` | integer | 结束行号 | `50` |

#### Call 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `caller` | string | 调用者 |
| `callee` | string | 被调用者 |
| `line` | integer | 调用所在行号 |

#### Inheritance 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `child` | string | 子类名称 |
| `parent` | string | 父类名称 |

#### Import 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `module` | string | 模块名称 |
| `names` | array | 导入的名称列表 |
| `is_from` | boolean | 是否是 from-import |

---

## ⚠️ 错误处理

### 命令级错误

当命令本身执行失败时（如目录不存在），返回：

```json
{
  "success": false,
  "error": {
    "code": "DIRECTORY_NOT_FOUND",
    "message": "Directory does not exist: /path/to/nonexistent",
    "detail": null
  },
  "results": [],
  "summary": {
    "total_files": 0,
    "total_symbols": 0,
    "errors": 1
  }
}
```

**Exit code**: 1

### 文件级错误

当部分文件解析失败时：

```json
{
  "success": true,
  "results": [
    {
      "path": "src/broken.py",
      "symbols": [],
      "calls": [],
      "inheritances": [],
      "imports": [],
      "module_docstring": "",
      "file_lines": 0,
      "error": "SyntaxError at line 42: unexpected EOF"
    },
    {
      "path": "src/good.py",
      "symbols": [...],
      "error": null
    }
  ],
  "summary": {
    "total_files": 2,
    "total_symbols": 15,
    "errors": 1
  }
}
```

**Exit code**: 0（部分成功）

### 错误码列表

| 错误码 | 说明 | 建议操作 |
|--------|------|----------|
| `DIRECTORY_NOT_FOUND` | 目录不存在 | 检查路径是否正确 |
| `NO_CONFIG_FOUND` | 配置文件不存在 | 运行 `codeindex init` 创建配置 |
| `PARSE_ERROR` | 文件解析失败 | 检查文件语法 |

---

## 🔧 Python 脚本集成

### 基础示例

```python
import json
import subprocess

# 执行 codeindex
result = subprocess.run(
    ["codeindex", "scan", "src/", "--output", "json"],
    capture_output=True,
    text=True,
    check=True
)

# 解析 JSON
data = json.loads(result.stdout)

if data["success"]:
    print(f"Total files: {data['summary']['total_files']}")
    print(f"Total symbols: {data['summary']['total_symbols']}")

    # 遍历符号
    for result in data["results"]:
        for symbol in result["symbols"]:
            if symbol["kind"] == "class":
                print(f"Class: {symbol['name']} at {result['path']}:{symbol['line_start']}")
else:
    print(f"Error: {data['error']['message']}")
```

### 提取所有类名

```python
import json
import subprocess

result = subprocess.run(
    ["codeindex", "scan-all", "--output", "json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

classes = [
    {
        "name": symbol["name"],
        "file": res["path"],
        "line": symbol["line_start"]
    }
    for res in data["results"]
    for symbol in res["symbols"]
    if symbol["kind"] == "class"
]

for cls in classes:
    print(f"{cls['name']:<30} {cls['file']}:{cls['line']}")
```

### 生成调用图

```python
import json
import subprocess
from collections import defaultdict

result = subprocess.run(
    ["codeindex", "scan-all", "--output", "json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# 构建调用图
call_graph = defaultdict(list)

for res in data["results"]:
    for call in res["calls"]:
        call_graph[call["caller"]].append(call["callee"])

# 打印调用图
for caller, callees in call_graph.items():
    print(f"{caller}:")
    for callee in callees:
        print(f"  → {callee}")
```

---

## 🔍 jq 查询示例

### 查看摘要

```bash
codeindex scan-all --output json | jq '.summary'
```

### 提取所有类名

```bash
codeindex scan-all --output json | \
  jq -r '.results[].symbols[] | select(.kind == "class") | .name'
```

### 查找特定文件的符号

```bash
codeindex scan-all --output json | \
  jq '.results[] | select(.path == "src/auth/user.py") | .symbols'
```

### 统计每个文件的符号数量

```bash
codeindex scan-all --output json | \
  jq -r '.results[] | "\(.path): \(.symbols | length) symbols"'
```

### 查找有错误的文件

```bash
codeindex scan-all --output json | \
  jq -r '.results[] | select(.error != null) | "\(.path): \(.error)"'
```

### 提取所有调用关系

```bash
codeindex scan-all --output json | \
  jq -r '.results[].calls[] | "\(.caller) → \(.callee)"'
```

---

## 🤖 AI Agent 集成

### 在 CLAUDE.md 中配置

在你的项目根目录创建 `.claude/CLAUDE.md` 或 `AGENTS.md`：

```markdown
# Project: MyAwesomeProject

## 🔍 Code Analysis Tools

### codeindex - Code Structure Analysis

**Purpose**: Extract code structure and relationships for AI understanding

**Commands**:

```bash
# Generate human-readable documentation
codeindex scan-all

# Generate machine-readable JSON for tools
codeindex scan-all --output json
```

**When to use**:
- Understanding project architecture
- Finding symbol definitions and references
- Analyzing call graphs and dependencies
- Feeding data to knowledge graph systems

**Output**:
- Markdown mode: `README_AI.md` files in each directory
- JSON mode: Structured data to stdout

## 🧠 LoomGraph - Code Knowledge Graph (Optional)

If this project uses LoomGraph for semantic code search:

```bash
# Index codebase
codeindex scan-all --output json > parse.json
loomgraph index .

# Search
loomgraph search "authentication logic"

# Query call graph
loomgraph graph "UserService.login" --direction callers
```

## 📋 AI Agent Workflow

As an AI agent, you should:

1. **Understand structure**: Read `README_AI.md` files first
2. **Find symbols**: Use `PROJECT_SYMBOLS.md` for quick lookup
3. **Analyze relationships**: Use `codeindex scan --output json` for structured data
4. **Semantic search**: Use `loomgraph search` when available
```

### Claude Code Skill 示例

```python
# claude_code_skill.py
"""
Skill: Analyze codebase structure
Trigger: User asks about code architecture or symbol locations
"""

import json
import subprocess

def analyze_codebase(query: str) -> dict:
    """
    Analyze codebase structure using codeindex.

    Args:
        query: User's query about code structure

    Returns:
        Structured analysis results
    """
    # Get JSON data
    result = subprocess.run(
        ["codeindex", "scan-all", "--output", "json"],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)

    # Analyze based on query
    if "class" in query.lower():
        classes = [
            symbol for res in data["results"]
            for symbol in res["symbols"]
            if symbol["kind"] == "class"
        ]
        return {"type": "classes", "results": classes}

    elif "call" in query.lower() or "usage" in query.lower():
        calls = [
            call for res in data["results"]
            for call in res["calls"]
        ]
        return {"type": "calls", "results": calls}

    else:
        return {"type": "summary", "results": data["summary"]}
```

---

## 📊 性能优化

### 大型项目

对于大型项目（>1000 文件），考虑：

1. **分批处理**：
   ```bash
   # 只扫描特定目录
   codeindex scan src/core --output json
   ```

2. **使用 .codeindex.yaml 过滤**：
   ```yaml
   include:
     - src
     - lib
   exclude:
     - tests
     - node_modules
     - "**/migrations/*"
   ```

3. **管道处理**：
   ```bash
   # 边扫描边处理，避免大文件
   codeindex scan-all --output json | python process.py
   ```

### 内存优化

JSON 输出是流式的，不会一次性加载所有数据到内存：

```python
import json
import subprocess

# 使用流式处理
proc = subprocess.Popen(
    ["codeindex", "scan-all", "--output", "json"],
    stdout=subprocess.PIPE,
    text=True
)

# 逐行处理（如果需要）
data = json.load(proc.stdout)
```

---

## 🧪 测试和验证

### 验证 JSON 格式

```bash
# 使用 jq 验证
codeindex scan src/ --output json | jq empty

# 使用 Python 验证
codeindex scan src/ --output json | python -m json.tool > /dev/null
```

### 测试错误处理

```bash
# 测试目录不存在
codeindex scan nonexistent/ --output json
# 预期：返回 success: false

# 测试部分文件失败
# (创建一个有语法错误的文件)
echo "def broken(" > broken.py
codeindex scan . --output json | jq '.summary.errors'
# 预期：errors > 0
```

---

## 🔗 相关资源

- [codeindex README](../../README.md) - 项目主文档
- [CLAUDE.md](../../CLAUDE.md) - codeindex 开发指南
- [LoomGraph CLI Design](https://github.com/dreamlx/LoomGraph/blob/main/docs/api/CLI_DESIGN.md) - LoomGraph 集成规范
- [Epic: JSON Output](../planning/active/epic-json-output.md) - 功能设计文档

---

## 💡 最佳实践

1. **优先使用 scan-all**：获取完整项目视图
2. **配置 .codeindex.yaml**：排除无关目录
3. **保存 JSON 到文件**：便于调试和重复使用
4. **使用 jq 查询**：快速提取所需信息
5. **检查 summary.errors**：确保数据完整性
6. **在 CLAUDE.md 中记录**：帮助 AI Agent 理解工具链

---

## ❓ FAQ

**Q: JSON 输出和 Markdown 输出有什么区别？**

A:
- Markdown：生成人类可读的文档（README_AI.md），适合浏览和理解
- JSON：生成机器可读的数据（stdout），适合工具集成和自动化

**Q: 可以同时生成两种输出吗？**

A: 分两次运行：
```bash
codeindex scan src/  # 生成 README_AI.md
codeindex scan src/ --output json > data.json  # 生成 JSON
```

**Q: JSON 输出性能如何？**

A: 与 Markdown 输出相同，因为数据已经在内存中，只是序列化格式不同。

**Q: 支持其他语言吗？**

A: 当前仅支持 Python，未来版本会添加 Java、JavaScript 等语言支持。

**Q: JSON 输出可以增量更新吗？**

A: v0.7.0 不支持，每次都是全量扫描。增量更新功能将在未来版本实现。

---

**版本**: v0.7.0
**最后更新**: 2026-02-04
