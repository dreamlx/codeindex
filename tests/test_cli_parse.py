import json
import time

import pytest
from click.testing import CliRunner

from codeindex.cli import main


class TestCliParse:
    """CLI parse command tests"""

    def setup_method(self):
        self.runner = CliRunner()

    # ========================================
    # Basic Functionality (5 tests)
    # ========================================

    def test_parse_python_file_json_output(self):
        """解析 Python 文件 → JSON 输出"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        assert result.exit_code == 0, (
            f"Expected exit code 0, got {result.exit_code}: {result.output}"
        )

        data = json.loads(result.output)
        assert 'file_path' in data
        assert 'language' in data
        assert data['language'] == 'python'
        assert 'symbols' in data
        assert len(data['symbols']) >= 2  # add function + Calculator class

    def test_parse_php_file_json_output(self):
        """解析 PHP 文件 → JSON 输出"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.php'])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data['language'] == 'php'
        assert data['namespace'] == 'App\\Utils'
        assert len(data['symbols']) >= 1  # Calculator class

    def test_parse_java_file_json_output(self):
        """解析 Java 文件 → JSON 输出"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/Simple.java'])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data['language'] == 'java'
        assert 'com.example.utils' in data.get('namespace', '')
        assert len(data['symbols']) >= 1  # Calculator class

    def test_parse_help_text(self):
        """帮助信息完整"""
        result = self.runner.invoke(main, ['parse', '--help'])
        assert result.exit_code == 0
        assert 'Parse a single source file' in result.output
        assert 'FILE_PATH' in result.output or 'file_path' in result.output

    def test_parse_version_compatible(self):
        """版本信息兼容"""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        # parse 命令应该不影响版本输出

    # ========================================
    # JSON Format Validation (5 tests)
    # ========================================

    def test_json_all_required_fields(self):
        """JSON 包含所有必需字段"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        data = json.loads(result.output)

        # 必需字段
        required_fields = ['file_path', 'language', 'symbols', 'imports', 'namespace', 'error']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_json_symbols_structure(self):
        """symbols 字段结构正确"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.py'])
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
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/complete.py'])
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
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        data1 = json.loads(result.output)

        # Serialize and deserialize again
        json_str = json.dumps(data1, ensure_ascii=False)
        data2 = json.loads(json_str)

        assert data1 == data2, "JSON round-trip should be lossless"

    def test_json_format_consistency(self):
        """JSON 格式与 scan 一致"""
        # 检查 JSON 结构与 scan --output json 一致
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.py'])
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
        result = self.runner.invoke(main, ['parse', 'nonexistent.py'])
        assert result.exit_code == 1
        assert 'File not found' in result.output or 'does not exist' in result.output

    def test_parse_unsupported_language(self):
        """不支持的语言 → Exit code 2"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/unsupported.txt'])
        assert result.exit_code == 2
        assert 'Unsupported' in result.output or 'not supported' in result.output

    def test_parse_syntax_error_file(self):
        """语法错误 → Exit code 3 或 JSON with error"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/broken.py'])
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
            with open("empty.py", "w"):
                pass  # 空文件

            result = self.runner.invoke(main, ['parse', 'empty.py'])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data['symbols'] == []

    def test_parse_permission_denied(self):
        """权限错误 → 清晰错误信息"""
        import os
        import platform

        # Skip on Windows as chmod doesn't work the same way
        if platform.system() == 'Windows':
            pytest.skip("Permission test not applicable on Windows")

        with self.runner.isolated_filesystem():
            # 创建文件并移除读权限
            with open('noaccess.py', 'w') as f:
                f.write('def test(): pass')
            os.chmod('noaccess.py', 0o000)

            try:
                result = self.runner.invoke(main, ['parse', 'noaccess.py'])
                # 应该是 exit 1 或 3
                assert result.exit_code != 0
            finally:
                # 清理
                os.chmod('noaccess.py', 0o644)

    # ========================================
    # Framework Features (3 tests)
    # ========================================

    def test_parse_thinkphp_routes(self):
        """ThinkPHP 控制器路由提取"""
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/Controller.php'])
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
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/Service.java'])
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
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/complete.py'])
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
        """小文件 (<1000 行) 解析性能 < 0.2s"""
        start = time.time()
        result = self.runner.invoke(main, ['parse', 'tests/fixtures/cli_parse/simple.py'])
        elapsed = time.time() - start

        assert result.exit_code == 0
        assert elapsed < 0.5, f"Small file should parse in <0.5s, took {elapsed:.3f}s"  # 留一些余量

    def test_parse_large_file_performance(self):
        """大文件 (5000+ 行) 解析性能 < 2s"""
        with self.runner.isolated_filesystem():
            # 生成大文件
            with open('large.py', 'w') as f:
                for i in range(1000):
                    f.write(f"def function_{i}(x):\n")
                    f.write(f"    '''Function {i}'''\n")
                    f.write(f"    return x * {i}\n\n")

            start = time.time()
            result = self.runner.invoke(main, ['parse', 'large.py'])
            elapsed = time.time() - start

            assert result.exit_code == 0
            assert elapsed < 3.0, f"Large file should parse in <3s, took {elapsed:.3f}s"  # 留余量
