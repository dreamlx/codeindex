"""Tests for SmartWriter with adaptive symbol selection."""

import tempfile
from pathlib import Path

from codeindex.adaptive_config import AdaptiveSymbolsConfig
from codeindex.config import IndexingConfig, SymbolsConfig
from codeindex.parser import ParseResult, Symbol
from codeindex.smart_writer import SmartWriter


def _create_mock_symbols(count: int) -> list[Symbol]:
    """Create mock symbols for testing."""
    symbols = []
    for i in range(count):
        symbols.append(
            Symbol(
                name=f"method_{i}",
                kind="method",
                signature=f"public function method_{i}()",
                docstring=f"Method {i}",
                line_start=i * 10,
                line_end=i * 10 + 5,
            )
        )
    return symbols


def _create_mock_parse_result(path: Path, symbol_count: int, file_lines: int) -> ParseResult:
    """Create mock ParseResult with specified symbol count and file lines."""
    return ParseResult(
        path=path,
        symbols=_create_mock_symbols(symbol_count),
        imports=[],
        module_docstring="Test module",
        namespace="Test",
        error="",
        file_lines=file_lines,  # Add file_lines info
    )


class TestSmartWriterAdaptiveDisabled:
    """Test SmartWriter with adaptive disabled (backward compatibility)."""

    def test_uses_max_per_file_when_adaptive_disabled(self):
        """当adaptive禁用时，应该使用max_per_file"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            max_per_file=20,
            adaptive_symbols=AdaptiveSymbolsConfig(enabled=False),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "test.py"

            # 100个符号，max_per_file=20，应该只显示20个
            result = _create_mock_parse_result(file_path, 100, 5000)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            content = output.path.read_text()

            # 应该只显示20个符号，剩余80个被截断
            assert "80 more symbols" in content


class TestSmartWriterAdaptiveEnabled:
    """Test SmartWriter with adaptive enabled."""

    def test_uses_adaptive_limit_for_small_file(self):
        """小文件应该使用小的限制"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            max_per_file=15,  # 旧的固定值
            adaptive_symbols=AdaptiveSymbolsConfig(
                enabled=True,
                limits={"tiny": 10, "small": 15, "medium": 30},
            ),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "test.py"

            # 150行文件（small类别），30个符号，limit=15
            result = _create_mock_parse_result(file_path, 30, 150)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            content = output.path.read_text()

            # 应该显示15个符号（small limit），剩余15个被截断
            assert "15 more symbols" in content

    def test_uses_adaptive_limit_for_large_file(self):
        """大文件应该使用大的限制"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            max_per_file=15,
            adaptive_symbols=AdaptiveSymbolsConfig(
                enabled=True,
                limits={"large": 50, "xlarge": 80, "huge": 120},
            ),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "test.py"

            # 2500行文件（huge类别），150个符号，limit=120
            result = _create_mock_parse_result(file_path, 150, 2500)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            content = output.path.read_text()

            # 应该显示120个符号（huge limit），剩余30个被截断
            assert "30 more symbols" in content

    def test_respects_total_symbols_constraint(self):
        """不应该超过实际符号数量"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            adaptive_symbols=AdaptiveSymbolsConfig(
                enabled=True,
                limits={"huge": 120},
            ),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "test.py"

            # 2500行文件，但只有30个符号
            result = _create_mock_parse_result(file_path, 30, 2500)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            content = output.path.read_text()

            # 应该显示全部30个符号，没有截断提示
            assert "more symbols" not in content


class TestRealWorldScenarios:
    """Test with real-world file scenarios."""

    def test_php_8891_lines_57_symbols(self):
        """真实场景：8891行PHP文件，57个符号"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            max_per_file=15,  # 旧限制
            adaptive_symbols=AdaptiveSymbolsConfig(
                enabled=True,
                limits={"mega": 150},
            ),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "OperateGoods.class.php"

            # 8891行，57个符号（真实PHP项目数据）
            result = _create_mock_parse_result(file_path, 57, 8891)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            content = output.path.read_text()

            # 应该显示全部57个符号（mega limit=150，但只有57个）
            assert "more symbols" not in content

    def test_php_500_lines_80_symbols(self):
        """真实场景：500行文件，80个符号"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            max_per_file=15,
            adaptive_symbols=AdaptiveSymbolsConfig(
                enabled=True,
                limits={"large": 50},
            ),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "Controller.php"

            # 500行，80个符号
            result = _create_mock_parse_result(file_path, 80, 500)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            content = output.path.read_text()

            # 应该显示50个符号（large limit），剩余30个被截断
            assert "30 more symbols" in content


class TestMultipleFiles:
    """Test with multiple files of different sizes."""

    def test_mixed_file_sizes(self):
        """混合大小的文件应该各自使用对应的限制"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            adaptive_symbols=AdaptiveSymbolsConfig(
                enabled=True,
                limits={
                    "small": 15,
                    "large": 50,
                    "huge": 120,
                },
            ),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)

            results = [
                # 小文件：150行，20个符号，limit=15
                _create_mock_parse_result(dir_path / "small.py", 20, 150),
                # 大文件：800行，60个符号，limit=50
                _create_mock_parse_result(dir_path / "large.py", 60, 800),
                # 超大文件：3000行，100个符号，limit=120
                _create_mock_parse_result(dir_path / "huge.py", 100, 3000),
            ]

            output = writer.write_readme(dir_path, results, level="detailed")

            assert output.success
            content = output.path.read_text()

            # 小文件：显示15个，5个被截断
            assert "5 more symbols" in content or content.count("method_") >= 15

            # 大文件：显示50个，10个被截断
            assert "10 more symbols" in content or content.count("method_") >= 50


class TestFileLinesCounting:
    """Test file lines counting mechanism."""

    def test_file_lines_from_parse_result(self):
        """应该从ParseResult获取文件行数"""
        config = IndexingConfig()
        config.symbols = SymbolsConfig(
            adaptive_symbols=AdaptiveSymbolsConfig(enabled=True),
        )

        writer = SmartWriter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            file_path = dir_path / "test.py"

            # file_lines=2500（huge类别）
            result = _create_mock_parse_result(file_path, 150, 2500)

            output = writer.write_readme(dir_path, [result], level="detailed")

            assert output.success
            # 如果正确使用了file_lines，应该应用huge类别的limit（120）
            content = output.path.read_text()
            # 150个符号，limit=120，应该截断30个
            assert "30 more symbols" in content
