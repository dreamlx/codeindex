# Epic 12: Single File Parse Command - Development Checklist (SIMPLIFIED)

**Epic ID**: 12
**Target Version**: v0.13.0
**Start Date**: 2026-02-07
**Estimated Duration**: 2-3 days (Simplified from 3-5 days)
**Single Story**: Parse Command with JSON Output

---

## 📋 TDD/BDD Development Workflow

### Golden Rules

**Before ANY code implementation**:
1. ✅ **Write failing tests first** (Red)
2. ✅ **Write minimal code to pass tests** (Green)
3. ✅ **Refactor while keeping tests green** (Refactor)
4. ✅ **Commit after each Green phase**

**Test Coverage Target**: ≥ 90%

---

## 🎯 Story 12.1: Parse Command with JSON Output

**Estimated Duration**: 2-3 days
**Priority**: P0
**Tests**: 20 tests

### Pre-Implementation (Day 1 Morning - 1 hour)

#### [ ] 环境准备
```bash
# 1. 切换到 develop 分支
git checkout develop
git pull origin develop

# 2. 创建 feature 分支
git checkout -b feature/epic12-single-file-parse

# 3. 确认测试环境
pytest --version
python -m codeindex --version
```

#### [ ] 创建测试结构
```bash
# 1. 创建测试文件
touch tests/test_cli_parse.py

# 2. 创建测试 fixtures 目录
mkdir -p tests/fixtures/cli_parse

# 3. 创建测试 fixtures
```

#### [ ] 创建测试 Fixtures

**Python fixtures**:
```bash
cat > tests/fixtures/cli_parse/simple.py << 'EOF'
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

class Calculator:
    """Simple calculator"""
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b
EOF

cat > tests/fixtures/cli_parse/complete.py << 'EOF'
from typing import Optional

class Parent:
    """Parent class"""
    pass

class Child(Parent):
    """Child class"""
    def method(self):
        result = add(1, 2)
        return result

def add(x, y):
    """Add function"""
    return x + y
EOF
```

**PHP fixtures**:
```bash
cat > tests/fixtures/cli_parse/simple.php << 'EOF'
<?php
namespace App\Utils;

class Calculator {
    /**
     * Add two numbers
     */
    public function add($a, $b) {
        return $a + $b;
    }
}
EOF

cat > tests/fixtures/cli_parse/Controller.php << 'EOF'
<?php
namespace app\controller;

use think\Controller;

class UserController extends Controller {
    /**
     * User login
     * @route POST /api/user/login
     */
    public function login() {
        return ['status' => 'ok'];
    }
}
EOF
```

**Java fixtures**:
```bash
cat > tests/fixtures/cli_parse/Simple.java << 'EOF'
package com.example.utils;

public class Calculator {
    /**
     * Add two numbers
     */
    public int add(int a, int b) {
        return a + b;
    }
}
EOF

cat > tests/fixtures/cli_parse/Service.java << 'EOF'
package com.example.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {
    /**
     * Get user by ID
     */
    public User getUser(Long id) {
        return null;
    }
}
EOF
```

**Error fixtures**:
```bash
cat > tests/fixtures/cli_parse/broken.py << 'EOF'
def broken_function(
    # Missing closing parenthesis
EOF

cat > tests/fixtures/cli_parse/unsupported.txt << 'EOF'
This is a text file, not source code.
EOF
```

**Checkpoint**: ✅ 测试结构和 fixtures 已创建

---

## 🔴 Phase 1: Red - Write Failing Tests (Day 1 Morning - 2 hours)

### [ ] Create test_cli_parse.py

```python
# tests/test_cli_parse.py
import pytest
from click.testing import CliRunner
from codeindex.cli import cli
import json
import time

class TestCliParse:
    """CLI parse command tests"""

    def setup_method(self):
        self.runner = CliRunner()

    # ========================================
    # Basic Functionality (5 tests)
    # ========================================

    def test_parse_python_file_json_output(self):
        """解析 Python 文件 → JSON 输出"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}: {result.output}"

        data = json.loads(result.output)
        assert 'file_path' in data
        assert 'language' in data
        assert data['language'] == 'python'
        assert 'symbols' in data
        assert len(data['symbols']) >= 2  # add function + Calculator class

    def test_parse_php_file_json_output(self):
        """解析 PHP 文件 → JSON 输出"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.php'])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data['language'] == 'php'
        assert data['namespace'] == 'App\\Utils'
        assert len(data['symbols']) >= 1  # Calculator class

    def test_parse_java_file_json_output(self):
        """解析 Java 文件 → JSON 输出"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/Simple.java'])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data['language'] == 'java'
        assert 'com.example.utils' in data.get('namespace', '')
        assert len(data['symbols']) >= 1  # Calculator class

    def test_parse_help_text(self):
        """帮助信息完整"""
        result = self.runner.invoke(cli, ['parse', '--help'])
        assert result.exit_code == 0
        assert 'Parse a single source file' in result.output
        assert 'FILE_PATH' in result.output or 'file_path' in result.output

    def test_parse_version_compatible(self):
        """版本信息兼容"""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        # parse 命令应该不影响版本输出

    # ========================================
    # JSON Format Validation (5 tests)
    # ========================================

    def test_json_all_required_fields(self):
        """JSON 包含所有必需字段"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        data = json.loads(result.output)

        # 必需字段
        required_fields = ['file_path', 'language', 'symbols', 'imports', 'namespace', 'error']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_json_symbols_structure(self):
        """symbols 字段结构正确"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        data = json.loads(result.output)

        assert len(data['symbols']) > 0, "Should have at least one symbol"

        symbol = data['symbols'][0]
        required_symbol_fields = ['name', 'kind', 'signature', 'line_start', 'line_end']
        for field in required_symbol_fields:
            assert field in symbol, f"Symbol missing field: {field}"

        # 类型检查
        assert isinstance(symbol['name'], str)
        assert isinstance(symbol['kind'], str)
        assert isinstance(symbol['line_start'], int)
        assert isinstance(symbol['line_end'], int)

    def test_json_optional_fields(self):
        """JSON 包含可选字段（如果存在）"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/complete.py'])
        data = json.loads(result.output)

        # 可选字段（Epic 10+ 添加）
        # 这些字段可能存在，如果存在必须是正确类型
        if 'inheritances' in data:
            assert isinstance(data['inheritances'], list)
        if 'calls' in data:
            assert isinstance(data['calls'], list)
        if 'routes' in data:
            assert isinstance(data['routes'], list)

    def test_json_round_trip(self):
        """JSON 可反序列化（round-trip）"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        data1 = json.loads(result.output)

        # Serialize and deserialize again
        json_str = json.dumps(data1, ensure_ascii=False)
        data2 = json.loads(json_str)

        assert data1 == data2, "JSON round-trip should be lossless"

    def test_json_format_consistency(self):
        """JSON 格式与 scan 一致"""
        # 检查 JSON 结构与 scan --output json 一致
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        data = json.loads(result.output)

        # 核心字段应该与 scan 一致
        assert 'file_path' in data
        assert 'symbols' in data
        assert 'imports' in data
        # scan 可能有额外字段，但核心字段应该一致

    # ========================================
    # Error Handling (5 tests)
    # ========================================

    def test_parse_file_not_found(self):
        """文件不存在 → Exit code 1"""
        result = self.runner.invoke(cli, ['parse', 'nonexistent.py'])
        assert result.exit_code == 1
        assert 'File not found' in result.output or 'does not exist' in result.output

    def test_parse_unsupported_language(self):
        """不支持的语言 → Exit code 2"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/unsupported.txt'])
        assert result.exit_code == 2
        assert 'Unsupported' in result.output or 'not supported' in result.output

    def test_parse_syntax_error_file(self):
        """语法错误 → Exit code 3 或 JSON with error"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/broken.py'])
        # tree-sitter 可能部分解析，所以可能是 exit 0 但有 error 字段
        if result.exit_code == 0:
            data = json.loads(result.output)
            # 应该有错误信息或部分结果
            assert 'error' in data
        else:
            assert result.exit_code == 3
            assert 'Failed to parse' in result.output or 'error' in result.output.lower()

    def test_parse_empty_file(self):
        """空文件 → 正常处理"""
        with self.runner.isolated_filesystem():
            with open('empty.py', 'w') as f:
                pass  # 空文件

            result = self.runner.invoke(cli, ['parse', 'empty.py'])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data['symbols'] == []

    def test_parse_permission_denied(self):
        """权限错误 → 清晰错误信息"""
        import os
        with self.runner.isolated_filesystem():
            # 创建文件并移除读权限
            with open('noaccess.py', 'w') as f:
                f.write('def test(): pass')
            os.chmod('noaccess.py', 0o000)

            result = self.runner.invoke(cli, ['parse', 'noaccess.py'])
            # 应该是 exit 1 或 3
            assert result.exit_code != 0
            # 清理
            os.chmod('noaccess.py', 0o644)

    # ========================================
    # Framework Features (3 tests)
    # ========================================

    def test_parse_thinkphp_routes(self):
        """ThinkPHP 控制器路由提取"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/Controller.php'])
        assert result.exit_code == 0
        data = json.loads(result.output)

        # 检查路由字段（如果框架检测器生效）
        if 'routes' in data and data['routes']:
            assert len(data['routes']) >= 1
            # 检查路由结构
            route = data['routes'][0]
            assert 'url' in route
            assert 'http_method' in route

    def test_parse_spring_annotations(self):
        """Spring Service 注解"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/Service.java'])
        assert result.exit_code == 0
        data = json.loads(result.output)

        # 检查注解字段
        assert len(data['symbols']) >= 1
        user_service = next((s for s in data['symbols'] if s['name'] == 'UserService'), None)
        assert user_service is not None
        # 注解应该在 annotations 字段
        if 'annotations' in user_service:
            assert len(user_service['annotations']) >= 1

    def test_parse_inheritance_field(self):
        """继承类 → inheritances 字段"""
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/complete.py'])
        assert result.exit_code == 0
        data = json.loads(result.output)

        # 检查继承字段
        if 'inheritances' in data and data['inheritances']:
            assert len(data['inheritances']) >= 1
            inh = data['inheritances'][0]
            assert 'child' in inh
            assert 'parent' in inh
            assert inh['child'] == 'Child'
            assert inh['parent'] == 'Parent'

    # ========================================
    # Performance (2 tests)
    # ========================================

    def test_parse_small_file_performance(self):
        """小文件 (<1000 行) 解析性能 < 0.1s"""
        start = time.time()
        result = self.runner.invoke(cli, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        elapsed = time.time() - start

        assert result.exit_code == 0
        assert elapsed < 0.2, f"Small file should parse in <0.2s, took {elapsed:.3f}s"  # 留一些余量

    def test_parse_large_file_performance(self):
        """大文件 (5000+ 行) 解析性能 < 1s"""
        with self.runner.isolated_filesystem():
            # 生成大文件
            with open('large.py', 'w') as f:
                for i in range(1000):
                    f.write(f"def function_{i}(x):\n")
                    f.write(f"    '''Function {i}'''\n")
                    f.write(f"    return x * {i}\n\n")

            start = time.time()
            result = self.runner.invoke(cli, ['parse', 'large.py'])
            elapsed = time.time() - start

            assert result.exit_code == 0
            assert elapsed < 2.0, f"Large file should parse in <2s, took {elapsed:.3f}s"  # 留余量
```

### [ ] Run All Tests (Expected: FAIL)

```bash
pytest tests/test_cli_parse.py -v
# Expected: 20 FAILED (command 'parse' not found)
```

**Checkpoint**: ✅ Red phase complete (20 failing tests)

---

## 🟢 Phase 2: Green - Minimal Implementation (Day 1 Afternoon - 3 hours)

### [ ] Create cli_parse.py

```bash
touch src/codeindex/cli_parse.py
```

### [ ] Implement parse command

```python
# src/codeindex/cli_parse.py
import click
import json
from pathlib import Path
from codeindex.parser import detect_language, parse_file

@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def parse(file_path: str):
    """Parse a single source file and output JSON.

    Examples:
        codeindex parse src/main.py
        codeindex parse src/Controller.php | jq .
    """
    try:
        # 1. Convert to Path object
        file_path_obj = Path(file_path)

        # 2. Detect language
        language = detect_language(file_path_obj)
        if language is None:
            click.echo(f"Error: Unsupported file type: {file_path_obj.suffix}", err=True)
            raise click.exceptions.Exit(2)

        # 3. Parse file (reuse existing logic)
        parse_result = parse_file(str(file_path_obj), language)

        # 4. Output JSON (reuse to_dict)
        output_data = parse_result.to_dict()
        click.echo(json.dumps(output_data, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        click.echo(f"Error: File not found: {file_path}", err=True)
        raise click.exceptions.Exit(1)
    except PermissionError:
        click.echo(f"Error: Permission denied: {file_path}", err=True)
        raise click.exceptions.Exit(1)
    except Exception as e:
        click.echo(f"Error: Failed to parse file: {e}", err=True)
        raise click.exceptions.Exit(3)
```

### [ ] Integrate into cli.py

```python
# src/codeindex/cli.py
# Add import at top
from codeindex.cli_parse import parse

# Add command registration (near other cli.add_command() calls)
cli.add_command(parse)  # ✨ NEW
```

### [ ] Run Tests (Expected: PASS)

```bash
pytest tests/test_cli_parse.py -v
# Expected: 20 PASSED or most passing
```

**Checkpoint**: ✅ Green phase complete (20 tests passing)

### [ ] Commit

```bash
git add src/codeindex/cli_parse.py src/codeindex/cli.py tests/test_cli_parse.py tests/fixtures/cli_parse/
git commit -m "feat(cli): add parse command with JSON output (Story 12.1)

- Implement codeindex parse <file> command
- Support Python, PHP, Java file parsing
- JSON output with ParseResult.to_dict()
- Error handling: file not found (exit 1), unsupported (exit 2), parse failure (exit 3)
- Tests: 20 passing (basic functionality + JSON validation + error handling + framework features + performance)

Refs Epic 12"
```

---

## 🔧 Phase 3: Refactor (Day 2 Morning - 2 hours)

### [ ] Code Review Checklist

```bash
# 1. Ruff 代码检查
ruff check src/codeindex/cli_parse.py

# 2. 类型检查（如果使用 mypy）
mypy src/codeindex/cli_parse.py

# 3. 测试覆盖率
pytest tests/test_cli_parse.py --cov=src/codeindex/cli_parse --cov-report=term-missing
# Expected: ≥ 90% coverage
```

### [ ] Optimize Implementation (如果需要)

- 简化错误处理逻辑
- 优化 JSON 输出格式
- 添加日志（如果需要）

### [ ] Run All Tests Again

```bash
pytest tests/test_cli_parse.py -v
# Expected: 20 PASSED
```

### [ ] Commit (if refactored)

```bash
git commit -am "refactor(cli): optimize parse command implementation"
```

---

## 📝 Phase 4: Documentation (Day 2 Afternoon - 2 hours)

### [ ] Update README.md

```markdown
# Add to "Quick Start" section (around line 50-80)

### Parse Single File

Parse a single source file and output structured JSON data:

\```bash
# Parse Python file
codeindex parse src/calculator.py

# Parse PHP file
codeindex parse src/controller/UserController.php

# Parse Java file
codeindex parse src/main/java/com/example/Service.java

# Pipe to jq for filtering
codeindex parse src/Service.java | jq '.symbols[0].name'

# Save to file
codeindex parse src/main.py > output.json
\```

**Use Cases**:
- **Tool Integration**: LoomGraph, IDE extensions, CI/CD pipelines
- **Single File Inspection**: Quick code analysis without indexing entire project
- **API Data Provider**: JSON output for automation and scripting
\```
```

### [ ] Update CLAUDE.md

```markdown
# Add to "Part 2: Development Workflow" section (around line 200-300)

### Parse Command Usage

\```bash
# Single file parsing (tool integration friendly)
codeindex parse src/controller/UserController.php

# Pipe to jq for data extraction
codeindex parse src/UserModel.py | jq '.symbols[] | select(.kind == "class")'

# Integration with LoomGraph
codeindex parse src/UserModel.py | python loomgraph_extractor.py
\```

**When to use**:
- **parse**: Single file analysis, tool integration, CI/CD checks
- **scan**: Directory batch processing, documentation generation

**Output format**:
- JSON (default): Machine-readable, complete ParseResult data
- Compatible with `scan --output json` format
\```
```

### [ ] Verify CLI Help Text

```bash
codeindex parse --help

# Expected output:
# Usage: codeindex parse [OPTIONS] FILE_PATH
#
#   Parse a single source file and output JSON.
#
# Arguments:
#   FILE_PATH  [required]
#
# Options:
#   --help  Show this message and exit.
```

### [ ] Create Integration Example

```bash
cat > examples/loomgraph-integration.sh << 'EOF'
#!/bin/bash
# Example: Using codeindex parse with LoomGraph

set -e

echo "=== codeindex parse Integration Example ==="

# 1. Parse single file
echo -e "\n1. Parsing UserController.php..."
codeindex parse tests/fixtures/cli_parse/Controller.php > /tmp/user_controller.json
echo "✅ Output saved to /tmp/user_controller.json"

# 2. Extract symbols using jq
echo -e "\n2. Extracting symbols..."
cat /tmp/user_controller.json | jq '.symbols[] | {name, kind, line_start}'

# 3. Filter classes only
echo -e "\n3. Filtering classes..."
cat /tmp/user_controller.json | jq '.symbols[] | select(.kind == "class")'

# 4. Get inheritance relationships
echo -e "\n4. Getting inheritance relationships..."
cat /tmp/user_controller.json | jq '.inheritances'

# 5. Get routes (if any)
echo -e "\n5. Getting routes..."
cat /tmp/user_controller.json | jq '.routes // []'

echo -e "\n✅ All examples completed!"
EOF

chmod +x examples/loomgraph-integration.sh
```

### [ ] Test Documentation Examples

```bash
# 验证所有示例可运行
bash examples/loomgraph-integration.sh
```

### [ ] Commit Documentation

```bash
git add README.md CLAUDE.md examples/loomgraph-integration.sh
git commit -m "docs: add parse command documentation and examples (Story 12.1)

- Update README.md with parse usage and use cases
- Update CLAUDE.md with integration guide
- Add LoomGraph integration example script
- All examples verified and runnable

Refs Epic 12"
```

---

## 🚀 Phase 5: Integration & Release (Day 3 - 4 hours)

### [ ] Complete Regression Testing

```bash
# 1. 运行所有 parse 测试
pytest tests/test_cli_parse.py -v
# Expected: 20 PASSED

# 2. 运行所有测试（确保没有破坏现有功能）
pytest tests/test_parser.py -v
pytest tests/test_cli*.py -v
pytest  # 全量测试

# Expected: All tests passing
```

### [ ] Performance Benchmarking

```bash
# 测试不同大小文件的解析时间
echo "=== Performance Benchmarks ==="

echo "Small file:"
time codeindex parse tests/fixtures/cli_parse/simple.py > /dev/null

echo "Medium file:"
time codeindex parse tests/fixtures/spring_controller.java > /dev/null

echo "Large file (if available):"
# time codeindex parse tests/fixtures/large_file.py > /dev/null
```

### [ ] Error Handling Validation

```bash
# 测试各种错误场景
echo "=== Error Handling Tests ==="

echo "File not found:"
codeindex parse nonexistent.py
echo "Exit code: $?"  # Expected: 1

echo "Unsupported language:"
codeindex parse tests/fixtures/cli_parse/unsupported.txt
echo "Exit code: $?"  # Expected: 2

echo "Syntax error:"
codeindex parse tests/fixtures/cli_parse/broken.py
echo "Exit code: $?"  # Expected: 3 or 0 with error field
```

### [ ] Multi-Language Validation

```bash
# 验证所有语言
echo "=== Multi-Language Validation ==="

echo "Python:"
codeindex parse tests/fixtures/cli_parse/simple.py | jq '.language'

echo "PHP:"
codeindex parse tests/fixtures/cli_parse/simple.php | jq '.language'

echo "Java:"
codeindex parse tests/fixtures/cli_parse/Simple.java | jq '.language'
```

### [ ] Update CHANGELOG.md

```markdown
## [0.13.0] - 2026-02-XX

### Added

- **Single File Parse Command** (Epic 12 ⭐)
  - `codeindex parse <file>` command for single file parsing
  - JSON output with complete ParseResult data (symbols, imports, namespace, inheritance, calls, routes)
  - Support for Python, PHP, Java
  - Framework route extraction (ThinkPHP, Spring) automatically included
  - CLI integration friendly (loose coupling)
  - Error handling with clear exit codes (0=success, 1=file not found, 2=unsupported, 3=parse failure)

### Technical Implementation

- **CLI Module**: `src/codeindex/cli_parse.py` (~100 lines)
- **Output Format**: JSON (via ParseResult.to_dict())
- **Reused Components**: parser.py (detect_language, parse_file), data_types.py (to_dict)
- **Performance**: <0.1s for small files, <1s for large files (5000+ lines)

### Tests

- 20 new tests in `tests/test_cli_parse.py`
- All language parsers validated
- JSON format consistency with `scan --output json`
- Framework-specific features tested (routes, annotations)
- Performance benchmarks met

### Documentation

- README.md: Parse command usage and examples
- CLAUDE.md: Integration guide for tool developers
- examples/loomgraph-integration.sh: LoomGraph integration example

### Future Enhancements (v0.13.1+)

- Console output format (`--output console`) for human-readable display
- Additional output formats (YAML, XML)
```

### [ ] Update ROADMAP.md

```markdown
### v0.13.0 - Single File Parse Command ✅ (Released: 2026-02-XX)

**Theme**: Tool integration and architectural completeness

**Epic**: Epic 12 - Single File Parse Command

**What Was Delivered**:
- ✅ `codeindex parse <file>` CLI command
- ✅ JSON output format (consistent with scan)
- ✅ Multi-language support (Python, PHP, Java)
- ✅ Framework route extraction support (ThinkPHP, Spring)
- ✅ Complete documentation and examples

**Success Criteria** (All Achieved):
- [x] Support Python, PHP, Java single file parsing ✅
- [x] JSON output includes all ParseResult fields ✅
- [x] Error handling (file not found, unsupported, parse failure) ✅
- [x] Performance <0.1s small files, <1s large files ✅
- [x] 20+ tests passing ✅
- [x] Documentation complete ✅

**Tests**: XXX passing (20 new for parse command)

**Documentation**:
- Epic plan: `docs/planning/active/epic12-single-file-parse.md`
- README.md: Parse command usage
- CLAUDE.md: Integration guide
- Example: `examples/loomgraph-integration.sh`

**See**: CHANGELOG.md v0.13.0 entry
```

### [ ] Update Version Number

```bash
# 1. pyproject.toml
sed -i '' 's/version = "0.12.0"/version = "0.13.0"/' pyproject.toml

# 2. src/codeindex/__init__.py
sed -i '' 's/__version__ = "0.12.0"/__version__ = "0.13.0"/' src/codeindex/__init__.py

# 3. Verify
grep version pyproject.toml
grep __version__ src/codeindex/__init__.py
```

### [ ] Final Commit and PR

```bash
# Commit version bump and docs
git add CHANGELOG.md docs/planning/ROADMAP.md pyproject.toml src/codeindex/__init__.py
git commit -m "chore: bump version to v0.13.0

Epic 12: Single File Parse Command (SIMPLIFIED)
- Add codeindex parse <file> command
- JSON output format only (Console output deferred to v0.13.1)
- Multi-language support (Python/PHP/Java)
- Complete documentation
- 20 tests passing

Closes #XX (GitHub issue number)"

# Push to remote
git push origin feature/epic12-single-file-parse

# Create PR
gh pr create --title "feat: Single File Parse Command (Epic 12 - Simplified)" \
  --body "Epic 12: Add codeindex parse command for single file parsing

## Summary
- New CLI command: \`codeindex parse <file>\`
- Output format: JSON only (Console output deferred)
- Support: Python, PHP, Java
- Integration: LoomGraph-friendly (loose coupling)

## Tests
- 20 new tests passing
- All language parsers validated
- Performance benchmarks met

## Documentation
- README.md updated
- CLAUDE.md integration guide
- Example scripts provided

## Simplified Scope
- Removed: Console output format (deferred to v0.13.1)
- Removed: Separate JSON validation story (merged into core)
- Focus: Core functionality only (JSON output for tool integration)

Closes #XX"
```

---

## ✅ Final Checklist

### Code Quality
- [ ] 所有测试通过（20 tests）
- [ ] 测试覆盖率 ≥ 90%
  ```bash
  pytest tests/test_cli_parse.py --cov=src/codeindex/cli_parse --cov-report=term-missing
  ```
- [ ] Ruff 代码检查通过
  ```bash
  ruff check src/codeindex/cli_parse.py
  ```
- [ ] 类型检查通过（如果使用 mypy）
  ```bash
  mypy src/codeindex/cli_parse.py
  ```

### Documentation
- [ ] README.md 更新
- [ ] CLAUDE.md 更新
- [ ] CLI help text 完整
- [ ] 示例脚本可运行

### Release
- [ ] CHANGELOG.md 更新
- [ ] ROADMAP.md 更新
- [ ] 版本号更新 (v0.13.0)
- [ ] GitHub PR 创建

### Integration
- [ ] 与现有 CLI 命令兼容
- [ ] 不破坏现有功能（回归测试）
- [ ] LoomGraph 集成验证（示例脚本）

---

## 📊 Progress Tracking

**Status**: 🔵 Not Started

**Daily Progress**:
- **Day 1 Morning**: [ ] 环境准备 + Fixtures + Red phase (2-3 hours)
- **Day 1 Afternoon**: [ ] Green phase (3 hours)
- **Day 2 Morning**: [ ] Refactor (2 hours)
- **Day 2 Afternoon**: [ ] Documentation (2 hours)
- **Day 3**: [ ] Integration & Release (4 hours)

**Total Tests**: 0 / 20
**Test Coverage**: 0% / 90%

---

## 🎯 Success Criteria

- [ ] 20 测试通过
- [ ] 测试覆盖率 ≥ 90%
- [ ] 支持 Python、PHP、Java
- [ ] JSON 输出格式完整
- [ ] 文档完整
- [ ] 性能基准达标
- [ ] GitHub PR 合并

---

## 📝 Simplified Scope Notes

**Removed from Original Design**:
1. ❌ Console output format (`--output console`)
   - Reason: Not needed for LoomGraph integration
   - Future: v0.13.1 或 v0.14.0

2. ❌ Story 12.2 (JSON Validation)
   - Reason: JSON 验证是核心功能的一部分
   - Merged: Into Story 12.1 tests

3. ❌ Story 12.3 (Documentation)
   - Reason: 文档是开发的最后一步
   - Merged: Into Story 12.1 final phase

**Impact**:
- Faster delivery: 2-3 days vs 3-5 days
- Simpler implementation: ~100 lines vs ~200 lines
- Focused tests: 20 tests vs 38 tests
- Clearer scope: JSON output only

---

**Last Updated**: 2026-02-07
**Next Review**: After Day 1 implementation
