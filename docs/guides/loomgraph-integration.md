# LoomGraph 集成指南

**目标读者**: LoomGraph 项目组开发者
**版本**: codeindex v0.13.0+
**更新日期**: 2026-02-07

---

## 🎯 架构设计：松耦合 CLI 方案

### 架构概览

```
codeindex (CLI)  →  LoomGraph (CLI)  →  LightRAG (API)
   独立工具          调度编排            存储服务
```

### 为什么选择 CLI 而不是 Python API？

| 维度 | CLI 调用（推荐） | Python API 调用 |
|------|------------------|----------------|
| **耦合度** | ✅ 松耦合 | ❌ 紧耦合 |
| **依赖管理** | ✅ 独立安装 | ❌ 必须同环境 |
| **版本升级** | ✅ 独立升级 | ❌ 需要同步升级 |
| **环境隔离** | ✅ 进程隔离 | ❌ 共享 Python 环境 |
| **跨语言支持** | ✅ 任何语言可调用 | ❌ 仅限 Python |
| **错误隔离** | ✅ 进程崩溃不影响调用方 | ❌ 异常可能传播 |

**结论**: CLI 方案提供更好的架构独立性和可维护性。

---

## 📦 快速开始

### 1. 安装 codeindex

```bash
# 推荐：使用 pipx 隔离安装
pipx install ai-codeindex[all]

# 或者：pip 安装
pip install ai-codeindex[all]

# 验证安装
codeindex --version
# 输出: codeindex, version 0.13.0
```

### 2. 基本用法

```bash
# 解析单个 Python 文件
codeindex parse src/myfile.py

# 解析 Java 文件
codeindex parse Service.java

# 解析 PHP 文件
codeindex parse Controller.php
```

### 3. 验证功能

```bash
# 检查 parse 命令是否可用
codeindex parse --help

# 测试解析（使用 codeindex 自己的代码）
codeindex parse $(python -c "import codeindex; print(codeindex.__file__.replace('__init__.py', 'parser.py'))")
```

---

## 📋 JSON 输出格式详解

### 完整输出结构

```json
{
  "file_path": "src/auth/user.py",
  "language": "python",
  "symbols": [
    {
      "name": "User",
      "kind": "class",
      "signature": "class User(BaseModel):",
      "docstring": "User authentication model with JWT support",
      "line_start": 10,
      "line_end": 50,
      "annotations": [
        {
          "name": "dataclass",
          "arguments": {}
        }
      ]
    },
    {
      "name": "User.authenticate",
      "kind": "method",
      "signature": "def authenticate(self, password: str) -> bool:",
      "docstring": "Authenticate user with password",
      "line_start": 25,
      "line_end": 30,
      "annotations": []
    }
  ],
  "imports": [
    {
      "module": "typing",
      "names": ["Dict", "Optional"],
      "is_from": true,
      "alias": null
    },
    {
      "module": "pydantic",
      "names": [],
      "is_from": false,
      "alias": "pd"
    }
  ],
  "namespace": "",
  "error": null
}
```

### 字段说明

#### 顶层字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `file_path` | string | 文件路径（相对或绝对） | `"src/auth/user.py"` |
| `language` | string | 语言标识 | `"python"`, `"php"`, `"java"` |
| `symbols` | array | 符号列表（类/函数/方法） | `[{...}, {...}]` |
| `imports` | array | 导入语句列表 | `[{...}]` |
| `namespace` | string | 命名空间/包名（PHP/Java） | `"com.example.service"` |
| `error` | string\|null | 错误信息（如果有） | `null` 或 `"Parse error: ..."` |

#### Symbol 对象

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | 符号名称 | `"User"`, `"User.authenticate"` |
| `kind` | string | 符号类型 | `"class"`, `"function"`, `"method"` |
| `signature` | string | 完整签名 | `"def authenticate(self, password: str) -> bool:"` |
| `docstring` | string | 文档字符串 | `"Authenticate user with password"` |
| `line_start` | int | 起始行号（1-based） | `10` |
| `line_end` | int | 结束行号（1-based） | `50` |
| `annotations` | array | 注解/装饰器列表 | `[{"name": "Service", "arguments": {}}]` |

#### Import 对象

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `module` | string | 模块名 | `"typing"`, `"numpy"` |
| `names` | array | 导入的名称列表 | `["Dict", "Optional"]` |
| `is_from` | bool | 是否是 from 导入 | `true` (from X import Y), `false` (import X) |
| `alias` | string\|null | 别名（如果有） | `"np"` (import numpy as np) |

---

## 🔌 LoomGraph 集成方案

### 方案 A: Python subprocess 调用（推荐）

```python
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class CodeIndexParser:
    """codeindex CLI wrapper for LoomGraph"""

    def __init__(self, codeindex_bin: str = "codeindex"):
        """
        Args:
            codeindex_bin: Path to codeindex executable (default: "codeindex" in PATH)
        """
        self.codeindex_bin = codeindex_bin
        self._verify_installation()

    def _verify_installation(self):
        """Verify codeindex is installed and accessible"""
        try:
            result = subprocess.run(
                [self.codeindex_bin, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            print(f"✓ codeindex available: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                f"codeindex not found or not working. "
                f"Please install: pip install ai-codeindex[all]"
            ) from e

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single source file using codeindex CLI.

        Args:
            file_path: Path to the source file

        Returns:
            Parsed result as dict with keys:
            - file_path: str
            - language: str
            - symbols: List[Dict]
            - imports: List[Dict]
            - namespace: str
            - error: str | None

        Raises:
            FileNotFoundError: If file doesn't exist (exit code 1)
            ValueError: If file type is unsupported (exit code 2)
            RuntimeError: If parsing failed (exit code 3)
        """
        try:
            result = subprocess.run(
                [self.codeindex_bin, "parse", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30  # 30s timeout for large files
            )

            # Parse JSON output
            data = json.loads(result.stdout)

            # Handle exit codes
            if result.returncode == 1:
                raise FileNotFoundError(f"File not found or permission denied: {file_path}")
            elif result.returncode == 2:
                raise ValueError(f"Unsupported file type: {file_path}")
            elif result.returncode == 3:
                # Parse error, but data might be partial
                print(f"Warning: Parse error for {file_path}: {data.get('error')}")

            return data

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON output from codeindex: {e}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Parsing timeout (>30s) for {file_path}")


# 使用示例
if __name__ == "__main__":
    parser = CodeIndexParser()

    # 解析单个文件
    result = parser.parse_file(Path("src/user.py"))

    print(f"Language: {result['language']}")
    print(f"Symbols: {len(result['symbols'])}")
    print(f"Imports: {len(result['imports'])}")

    # 提取类名列表
    classes = [s['name'] for s in result['symbols'] if s['kind'] == 'class']
    print(f"Classes: {classes}")
```

### 方案 B: Node.js/TypeScript 调用

```typescript
import { spawn } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';

interface ParseResult {
  file_path: string;
  language: string;
  symbols: Symbol[];
  imports: Import[];
  namespace: string;
  error: string | null;
}

interface Symbol {
  name: string;
  kind: 'class' | 'function' | 'method';
  signature: string;
  docstring: string;
  line_start: number;
  line_end: number;
  annotations: Annotation[];
}

interface Import {
  module: string;
  names: string[];
  is_from: boolean;
  alias: string | null;
}

interface Annotation {
  name: string;
  arguments: Record<string, string>;
}

class CodeIndexParser {
  constructor(private codeindexBin: string = 'codeindex') {}

  async parseFile(filePath: string): Promise<ParseResult> {
    return new Promise((resolve, reject) => {
      const process = spawn(this.codeindexBin, ['parse', filePath]);

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code === 1) {
          reject(new Error(`File not found: ${filePath}`));
        } else if (code === 2) {
          reject(new Error(`Unsupported file type: ${filePath}`));
        } else if (code === 3) {
          console.warn(`Parse error for ${filePath}: ${stderr}`);
        }

        try {
          const result = JSON.parse(stdout) as ParseResult;
          resolve(result);
        } catch (e) {
          reject(new Error(`Invalid JSON output: ${e}`));
        }
      });

      process.on('error', (err) => {
        reject(new Error(`Failed to spawn codeindex: ${err.message}`));
      });
    });
  }
}

// 使用示例
(async () => {
  const parser = new CodeIndexParser();
  const result = await parser.parseFile('src/user.py');

  console.log(`Language: ${result.language}`);
  console.log(`Symbols: ${result.symbols.length}`);
  console.log(`Classes: ${result.symbols.filter(s => s.kind === 'class').map(s => s.name)}`);
})();
```

---

## 🚀 批量处理模式

### 场景 1: 批量解析目录

```python
from pathlib import Path
from typing import List, Dict
import concurrent.futures

def parse_directory(
    dir_path: Path,
    pattern: str = "*.py",
    max_workers: int = 4
) -> List[Dict]:
    """批量解析目录中的所有文件"""
    parser = CodeIndexParser()
    files = list(dir_path.rglob(pattern))

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(parser.parse_file, f): f
            for f in files
        }

        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                print(f"✓ Parsed {file}")
            except Exception as e:
                print(f"✗ Failed to parse {file}: {e}")

    return results

# 使用
results = parse_directory(Path("src/"), pattern="*.py", max_workers=8)
print(f"Total files parsed: {len(results)}")
```

### 场景 2: 流式处理（Shell 管道）

```bash
#!/bin/bash
# 批量解析并合并为单个 JSON 数组

find src/ -name "*.py" | while read file; do
  codeindex parse "$file"
done | jq -s '.'
```

---

## 🛡️ 错误处理最佳实践

### 1. Exit Code 处理

```python
def parse_with_fallback(file_path: Path) -> Optional[Dict]:
    """解析文件，失败时返回 None 而不是抛异常"""
    try:
        return parser.parse_file(file_path)
    except FileNotFoundError:
        print(f"Skipping missing file: {file_path}")
        return None
    except ValueError:
        print(f"Skipping unsupported file: {file_path}")
        return None
    except RuntimeError as e:
        print(f"Parse error for {file_path}: {e}")
        return None
```

### 2. 部分解析结果处理

```python
def extract_symbols_safely(result: Dict) -> List[Dict]:
    """提取符号，即使有解析错误"""
    if result.get('error'):
        print(f"Warning: Partial parse result due to: {result['error']}")

    # 即使有错误，symbols 列表可能仍然包含部分结果
    return result.get('symbols', [])
```

### 3. 超时处理

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    """超时上下文管理器"""
    def handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds}s")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# 使用
try:
    with timeout(60):
        result = parser.parse_file(large_file)
except TimeoutError:
    print("File too large, skipping...")
```

---

## 📊 性能考虑

### 基准性能

| 文件大小 | 解析时间 | 符号数 |
|---------|---------|--------|
| <100 行 | <0.05s | <10 |
| 100-1000 行 | 0.05-0.15s | 10-50 |
| 1000-5000 行 | 0.15-0.5s | 50-200 |
| >5000 行 | 0.5-2s | 200+ |

### 优化建议

1. **并行处理**: 使用 ThreadPoolExecutor 并行解析多个文件
2. **批量过滤**: 在调用前过滤不支持的文件类型
3. **缓存结果**: 对于不常变化的文件，缓存解析结果
4. **增量解析**: 只解析修改过的文件

```python
import hashlib
from pathlib import Path

class CachedParser:
    def __init__(self, cache_dir: Path = Path(".cache")):
        self.parser = CodeIndexParser()
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, file_path: Path) -> str:
        """计算文件的缓存键（基于内容哈希）"""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def parse_file_cached(self, file_path: Path) -> Dict:
        """带缓存的解析"""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            return json.loads(cache_file.read_text())

        result = self.parser.parse_file(file_path)
        cache_file.write_text(json.dumps(result))
        return result
```

---

## 🔄 版本兼容性

### 检查 codeindex 版本

```python
import re

def check_codeindex_version(min_version: str = "0.13.0") -> bool:
    """检查 codeindex 版本是否满足最低要求"""
    result = subprocess.run(
        ["codeindex", "--version"],
        capture_output=True,
        text=True
    )

    # 输出格式: "codeindex, version 0.13.0"
    match = re.search(r'version (\d+\.\d+\.\d+)', result.stdout)
    if not match:
        raise RuntimeError("Cannot determine codeindex version")

    current = tuple(map(int, match.group(1).split('.')))
    required = tuple(map(int, min_version.split('.')))

    return current >= required

# 使用
if not check_codeindex_version("0.13.0"):
    raise RuntimeError("codeindex >= 0.13.0 required for parse command")
```

### JSON 格式稳定性承诺

codeindex 保证：
- ✅ **字段只增不减**: 新版本可能添加字段，但不会删除现有字段
- ✅ **向后兼容**: v0.13.0+ 的 JSON 格式向后兼容
- ✅ **语义化版本**: MAJOR 版本变更才会有破坏性变化

---

## 🧪 测试建议

### 单元测试示例

```python
import unittest
from unittest.mock import patch, MagicMock

class TestCodeIndexIntegration(unittest.TestCase):

    def setUp(self):
        self.parser = CodeIndexParser()

    def test_parse_python_file(self):
        """测试解析 Python 文件"""
        result = self.parser.parse_file(Path("tests/fixtures/simple.py"))

        self.assertEqual(result['language'], 'python')
        self.assertGreater(len(result['symbols']), 0)
        self.assertIsNone(result['error'])

    def test_file_not_found(self):
        """测试文件不存在错误"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(Path("nonexistent.py"))

    def test_unsupported_file_type(self):
        """测试不支持的文件类型"""
        with self.assertRaises(ValueError):
            self.parser.parse_file(Path("README.md"))

    @patch('subprocess.run')
    def test_timeout_handling(self, mock_run):
        """测试超时处理"""
        mock_run.side_effect = subprocess.TimeoutExpired("codeindex", 30)

        with self.assertRaises(RuntimeError) as cm:
            self.parser.parse_file(Path("large_file.py"))

        self.assertIn("timeout", str(cm.exception).lower())
```

---

## 📚 FAQ

### Q1: codeindex parse 和 scan 的区别？

**A**:
- `parse`: 解析**单个文件**，输出 JSON，用于程序化集成
- `scan`: 扫描**目录**，生成 README_AI.md 文档，用于人类阅读

### Q2: 为什么不直接使用 scan --output json？

**A**:
- `scan` 针对目录，包含多个文件的聚合数据
- `parse` 针对单个文件，更轻量，更适合逐文件处理
- `parse` 启动更快（无需配置文件）

### Q3: 支持哪些语言？

**A**:
- Python (.py)
- PHP (.php, .phtml)
- Java (.java)

### Q4: 如何处理大文件（>10000 行）？

**A**:
- codeindex 可以处理大文件，但可能需要 2-5 秒
- 建议设置合理的超时时间（30-60 秒）
- 考虑使用缓存策略避免重复解析

### Q5: 可以在 Docker 容器中使用吗？

**A**:
可以！示例 Dockerfile:
```dockerfile
FROM python:3.10-slim
RUN pip install ai-codeindex[all]
CMD ["codeindex", "parse", "/input/file.py"]
```

---

## 🔗 相关资源

- **codeindex GitHub**: https://github.com/dreamlx/codeindex
- **PyPI Package**: https://pypi.org/project/ai-codeindex/
- **示例脚本**: `examples/parse_integration_example.sh`
- **验证报告**: `docs/evaluation/epic12-story12.1-validation.md`

---

## 📞 支持与反馈

遇到问题？
1. 查看 codeindex 日志: `codeindex parse file.py --verbose` (如果实现)
2. 提交 Issue: https://github.com/dreamlx/codeindex/issues
3. 查看 CHANGELOG: `docs/CHANGELOG.md`

---

**最后更新**: 2026-02-07
**适用版本**: codeindex >= 0.13.0
**维护者**: codeindex team
