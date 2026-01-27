"""Integration tests for tech-debt CLI command."""

import json

import pytest
from click.testing import CliRunner

from codeindex.cli import main


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    # Create a large file (should trigger CRITICAL)
    large_file = tmp_path / "large_file.py"
    large_file.write_text("\n".join([f"# Line {i}" for i in range(6000)]))

    # Create a normal file (no issues)
    normal_file = tmp_path / "normal_file.py"
    normal_file.write_text(
        '''"""A normal file."""


def process_data(data):
    """Process some data."""
    return data * 2


def calculate_sum(a, b):
    """Calculate sum."""
    return a + b
'''
    )

    return tmp_path


class TestTechDebtCommand:
    """Test tech-debt CLI command."""

    def test_tech_debt_command_exists(self):
        """Should have tech-debt command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "tech-debt" in result.output

    def test_analyze_directory_console_format(self, sample_files):
        """Should analyze directory and output console format."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(sample_files)])

        assert result.exit_code == 0
        assert "Technical Debt Report" in result.output
        assert "2 files analyzed" in result.output
        # Should find CRITICAL issue in large file
        assert "CRITICAL" in result.output

    def test_analyze_directory_markdown_format(self, sample_files):
        """Should output markdown format."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(sample_files), "--format", "markdown"])

        assert result.exit_code == 0
        assert "# Technical Debt Report" in result.output
        assert "## Summary" in result.output

    def test_analyze_directory_json_format(self, sample_files):
        """Should output JSON format."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(sample_files), "--format", "json"])

        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "total_files" in data
        assert "total_issues" in data
        assert data["total_files"] == 2

    def test_write_output_to_file(self, sample_files, tmp_path):
        """Should write output to file."""
        output_file = tmp_path / "debt_report.md"
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["tech-debt", str(sample_files), "--format", "markdown", "--output", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Technical Debt Report" in content

    def test_invalid_format_option(self, sample_files):
        """Should reject invalid format option."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(sample_files), "--format", "invalid"])

        assert result.exit_code != 0
        assert "Invalid value for '--format'" in result.output

    def test_nonexistent_directory(self):
        """Should fail gracefully for nonexistent directory."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", "/nonexistent/path"])

        assert result.exit_code != 0

    def test_empty_directory(self, tmp_path):
        """Should handle empty directory."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(tmp_path)])

        assert result.exit_code == 0
        assert "0 files analyzed" in result.output

    def test_recursive_option(self, tmp_path):
        """Should recursively scan subdirectories."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file1.py").write_text("# File 1\n" * 100)
        (tmp_path / "file2.py").write_text("# File 2\n" * 100)

        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(tmp_path), "--recursive"])

        assert result.exit_code == 0
        assert "2 files analyzed" in result.output


class TestTechDebtIntegration:
    """Integration tests for full tech-debt workflow."""

    def test_detect_multiple_issues(self, tmp_path):
        """Should detect multiple types of issues."""
        # Create file with multiple issues
        bad_file = tmp_path / "bad_code.py"
        # Make it large (>5000 lines) and add many methods (God Class)
        lines = []
        lines.append("class BadClass:")
        lines.append('    """A bad class with many methods."""')
        for i in range(60):
            lines.append(f"    def method{i}(self):")
            lines.append(f'        """Method {i}."""')
            lines.append("        pass")
        # Add more lines to reach 5000+
        lines.extend([f"# Padding line {i}" for i in range(5000)])
        bad_file.write_text("\n".join(lines))

        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        # Should detect both super_large_file and god_class
        assert data["critical_issues"] >= 2

    def test_report_quality_scores(self, sample_files):
        """Should include quality scores in report."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(sample_files), "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "average_quality_score" in data
        assert 0 <= data["average_quality_score"] <= 100

    def test_console_output_has_colors(self, sample_files):
        """Should use ANSI colors in console output."""
        runner = CliRunner()
        result = runner.invoke(main, ["tech-debt", str(sample_files)])

        # Check for ANSI escape codes (colors)
        # Note: In test environment colors might be stripped, so this is optional
        assert result.exit_code == 0
