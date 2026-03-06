"""Integration tests for debt-scan CLI command.

Tests the end-to-end functionality of the debt-scan command including:
- JSON output format
- Console output format
- Test smells detection integration
- Technical debt detection integration
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from codeindex.cli import main


class TestDebtScanCLI:
    """Test debt-scan command integration."""

    def test_debt_scan_json_output(self, tmp_path):
        """Should generate valid JSON output."""
        # Create a test file with issues
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
import pytest

@pytest.mark.skip
def test_skipped():
    pass

def test_working():
    assert True
            """
        )

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(tmp_path), "--format", "json", "--quiet"])

        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.output)

        # Verify structure (v0.22.0+ unified format)
        assert "target_path" in output  # v0.22.1+
        assert "timestamp" in output
        assert "summary" in output
        assert "giant_files" in output
        assert "giant_functions" in output
        assert "test_smells" in output
        assert "maintainability_scores" in output

        # Backward compatible fields
        assert "total_files" in output
        assert "average_quality_score" in output

        # Verify target_path is set
        assert output["target_path"] != ""

        # Verify summary
        assert output["summary"]["total_files"] == 1
        assert output["summary"]["test_smells"] >= 1  # Should detect @pytest.mark.skip

    def test_debt_scan_console_output(self, tmp_path):
        """Should generate readable console output."""
        # Create a test file
        test_file = tmp_path / "simple.py"
        test_file.write_text("def hello(): return 'world'")

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(tmp_path), "--format", "console", "--quiet"])

        assert result.exit_code == 0

        # Check output contains key elements (now using English ConsoleFormatter)
        assert "Technical Debt Report" in result.output or "Files analyzed" in result.output
        assert "Summary" in result.output or "files analyzed" in result.output.lower()

    def test_debt_scan_detects_test_smells(self, tmp_path):
        """Should detect various types of test smells."""
        # Use Python test file (always supported)
        test_file = tmp_path / "test_problematic.py"
        test_file.write_text(
            """
import pytest

def test_working():
    assert True

@pytest.mark.skip
def test_broken():
    pass

@pytest.mark.skip
def test_another_broken():
    pass
            """
        )

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(tmp_path), "--format", "json", "--quiet"])

        assert result.exit_code == 0
        output = json.loads(result.output)

        # Should detect multiple skipped tests
        assert len(output["test_smells"]) >= 2
        assert all(smell["type"] == "skipped_test" for smell in output["test_smells"])

    def test_debt_scan_detects_giant_files(self, tmp_path):
        """Should detect giant files in technical debt."""
        # Create a large file
        test_file = tmp_path / "giant.py"
        test_file.write_text("\n".join([f"# Line {i}" for i in range(2600)]))  # >2500 lines

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(tmp_path), "--format", "json", "--quiet"])

        assert result.exit_code == 0
        output = json.loads(result.output)

        # Should detect giant file
        assert output["summary"]["giant_files"] >= 1
        assert len(output["giant_files"]) >= 1
        assert output["giant_files"][0]["severity"] == "critical"

    def test_debt_scan_empty_directory(self, tmp_path):
        """Should handle empty directories gracefully."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(empty_dir), "--format", "json", "--quiet"])

        assert result.exit_code == 0
        output = json.loads(result.output)

        # Should return valid JSON with zero files
        assert output["summary"]["total_files"] == 0

    def test_debt_scan_recursive_flag(self, tmp_path):
        """Should recursively scan subdirectories."""
        # Create nested structure
        (tmp_path / "sub1").mkdir()
        (tmp_path / "sub1" / "file1.py").write_text("def foo(): pass")
        (tmp_path / "sub2").mkdir()
        (tmp_path / "sub2" / "file2.py").write_text("def bar(): pass")

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(tmp_path), "--format", "json", "--recursive", "--quiet"])

        assert result.exit_code == 0
        output = json.loads(result.output)

        # Should find both files
        assert output["summary"]["total_files"] == 2


class TestDebtScanEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_path(self):
        """Should fail gracefully for nonexistent paths."""
        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", "/nonexistent/path", "--quiet"])

        assert result.exit_code != 0

    def test_file_instead_of_directory(self, tmp_path):
        """Should reject file paths (requires directory)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(test_file), "--quiet"])

        assert result.exit_code != 0  # Should fail


class TestDebtScanIntegrationWithRealProject:
    """Test debt-scan on the codeindex project itself."""

    def test_scan_own_tests_directory(self):
        """Should successfully scan codeindex's own tests directory."""
        # Get the project root (where tests/ directory is)
        project_root = Path(__file__).parent.parent
        tests_dir = project_root / "tests"

        if not tests_dir.exists():
            pytest.skip("tests directory not found")

        runner = CliRunner()
        result = runner.invoke(main, ["debt-scan", str(tests_dir), "--format", "json", "--quiet"])

        assert result.exit_code == 0
        output = json.loads(result.output)

        # Verify realistic results
        assert output["summary"]["total_files"] > 50  # codeindex has many test files
        assert "test_smells" in output  # Should detect some skipped tests
        assert output["summary"]["avg_maintainability"] > 5  # Should have decent quality
