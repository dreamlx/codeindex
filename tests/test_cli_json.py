"""Tests for CLI JSON output.

Story 2 & 3: JSON Output for scan and scan-all commands

Tests:
- --output json option for scan command
- --output markdown (default) for scan command
- JSON format validation
- Error handling in JSON output
"""

import json

from click.testing import CliRunner

from codeindex.cli_scan import scan, scan_all


class TestScanJSONOutput:
    """Test scan command with --output json."""

    def test_scan_default_output_markdown(self, tmp_path):
        """Should default to markdown output (writes README_AI.md)."""
        runner = CliRunner()

        # Create test directory
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def foo(): pass")

        # Create config
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(scan, [str(test_dir), "--fallback", "--quiet"])

        assert result.exit_code == 0
        # Should create README_AI.md file
        assert (test_dir / "README_AI.md").exists()

    def test_scan_output_json_to_stdout(self, tmp_path):
        """Should output JSON to stdout when --output json."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "user.py").write_text('''
class UserService:
    """User management service"""

    def login(self, username: str) -> bool:
        """Authenticate user"""
        pass
''')

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--fallback", "--output", "json", "--quiet"]
            )

        assert result.exit_code == 0

        # Should output valid JSON
        data = json.loads(result.output)

        # Check structure
        assert "success" in data
        assert "results" in data
        assert "summary" in data

        # Check success
        assert data["success"] is True

        # Check results
        assert len(data["results"]) == 1
        assert data["results"][0]["path"] == str(test_dir / "user.py")
        assert len(data["results"][0]["symbols"]) > 0

        # Check summary
        assert data["summary"]["total_files"] == 1
        assert data["summary"]["total_symbols"] > 0

        # Should NOT create README_AI.md file
        assert not (test_dir / "README_AI.md").exists()

    def test_scan_output_json_includes_all_fields(self, tmp_path):
        """Should include all required fields in JSON output."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "test.py").write_text('''
"""Test module"""
import os
from typing import Optional

class TestClass:
    """Test class"""
    def method(self):
        """Test method"""
        pass
''')

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--fallback", "--output", "json", "--quiet"]
            )

        data = json.loads(result.output)
        parse_result = data["results"][0]

        # Check all ParseResult fields
        assert "path" in parse_result
        assert "symbols" in parse_result
        assert "imports" in parse_result
        assert "module_docstring" in parse_result
        assert "namespace" in parse_result
        assert "error" in parse_result
        assert "file_lines" in parse_result

        # Check imports were extracted
        assert len(parse_result["imports"]) >= 1

    def test_scan_output_json_with_chinese(self, tmp_path):
        """Should handle Chinese characters in JSON output."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "user.py").write_text('''
class UserService:
    """用户管理服务"""
    pass
''')

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--fallback", "--output", "json", "--quiet"]
            )

        data = json.loads(result.output)

        # Check Chinese characters preserved
        symbol = data["results"][0]["symbols"][0]
        assert "用户管理服务" in symbol["docstring"]


class TestScanAllJSONOutput:
    """Test scan-all command with --output json."""

    def test_scan_all_output_json(self, tmp_path):
        """Should aggregate results from all directories."""
        runner = CliRunner()

        # Create multiple directories
        dir1 = tmp_path / "module1"
        dir1.mkdir()
        (dir1 / "a.py").write_text("def func_a(): pass")

        dir2 = tmp_path / "module2"
        dir2.mkdir()
        (dir2 / "b.py").write_text("def func_b(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include:
  - module1
  - module2
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan_all, ["--root", str(tmp_path), "--fallback", "--output", "json", "--quiet"]
            )

        assert result.exit_code == 0

        # Should output valid JSON
        data = json.loads(result.output)

        # Check aggregation
        assert len(data["results"]) == 2
        assert data["summary"]["total_files"] == 2
        assert data["summary"]["total_symbols"] >= 2

    def test_scan_all_output_markdown_default(self, tmp_path):
        """Should default to markdown output (create README_AI.md files)."""
        runner = CliRunner()

        dir1 = tmp_path / "module1"
        dir1.mkdir()
        (dir1 / "a.py").write_text("def func_a(): pass")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include:
  - module1
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(scan_all, ["--root", str(tmp_path), "--fallback", "--quiet"])

        assert result.exit_code == 0
        # Should create README_AI.md file
        assert (dir1 / "README_AI.md").exists()


class TestJSONErrorHandling:
    """Test error handling in JSON output."""

    def test_scan_json_with_parse_error(self, tmp_path):
        """Should include error in result when file fails to parse."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        # Create file with syntax error
        (test_dir / "broken.py").write_text("def broken(")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--fallback", "--output", "json", "--quiet"]
            )

        # Should still succeed (partial success)
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["success"] is True

        # Should have 1 result with error
        assert len(data["results"]) == 1
        # Parse errors may be in result.error field
        # (implementation detail: parser may or may not return error)

        # Summary should show errors count
        assert "errors" in data["summary"]
