"""Tests for technical debt report formatters."""

from pathlib import Path

from codeindex.tech_debt import (
    DebtAnalysisResult,
    DebtIssue,
    DebtSeverity,
    FileReport,
    TechDebtReport,
)
from codeindex.tech_debt_formatters import (
    ConsoleFormatter,
    JSONFormatter,
    MarkdownFormatter,
)


class TestConsoleFormatter:
    """Test ConsoleFormatter."""

    def test_format_empty_report(self):
        """Should format empty report."""
        # Arrange
        formatter = ConsoleFormatter()
        report = TechDebtReport()

        # Act
        output = formatter.format(report)

        # Assert
        assert "Technical Debt Report" in output
        assert "0 files analyzed" in output
        assert "0 issues found" in output
        assert "Quality Score: 100.0" in output

    def test_format_report_with_single_file(self):
        """Should format report with single file."""
        # Arrange
        formatter = ConsoleFormatter()
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=Path("test.py"),
                metric_value=6000,
                threshold=5000,
                description="File has 6000 lines (threshold: 5000)",
                suggestion="Split into 3-5 smaller files",
            )
        ]
        file_report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=issues,
                quality_score=70.0,
                file_path=Path("test.py"),
                file_lines=6000,
                total_symbols=50,
            ),
            symbol_analysis=None,
        )
        report = TechDebtReport(
            file_reports=[file_report],
            total_files=1,
            total_issues=1,
            critical_issues=1,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            average_quality_score=70.0,
        )

        # Act
        output = formatter.format(report)

        # Assert
        assert "1 files analyzed" in output
        assert "1 issues found" in output
        assert "Quality Score: 70.0" in output
        assert "CRITICAL" in output
        assert "test.py" in output
        assert "super_large_file" in output

    def test_format_includes_severity_counts(self):
        """Should include counts for each severity level."""
        # Arrange
        formatter = ConsoleFormatter()
        file_report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[
                    DebtIssue(
                        severity=DebtSeverity.CRITICAL,
                        category="test",
                        file_path=Path("test.py"),
                        metric_value=100,
                        threshold=50,
                        description="Critical issue",
                        suggestion="Fix it",
                    ),
                    DebtIssue(
                        severity=DebtSeverity.HIGH,
                        category="test",
                        file_path=Path("test.py"),
                        metric_value=100,
                        threshold=50,
                        description="High issue",
                        suggestion="Fix it",
                    ),
                ],
                quality_score=55.0,
                file_path=Path("test.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )
        report = TechDebtReport(
            file_reports=[file_report],
            total_files=1,
            total_issues=2,
            critical_issues=1,
            high_issues=1,
            medium_issues=0,
            low_issues=0,
            average_quality_score=55.0,
        )

        # Act
        output = formatter.format(report)

        # Assert
        assert "CRITICAL: 1" in output
        assert "HIGH: 1" in output


class TestMarkdownFormatter:
    """Test MarkdownFormatter."""

    def test_format_empty_report(self):
        """Should format empty report as markdown."""
        # Arrange
        formatter = MarkdownFormatter()
        report = TechDebtReport()

        # Act
        output = formatter.format(report)

        # Assert
        assert "# Technical Debt Report" in output
        assert "## Summary" in output
        assert "- **Files Analyzed:** 0" in output
        assert "- **Total Issues:** 0" in output
        assert "- **Quality Score:** 100.0" in output

    def test_format_report_with_issues(self):
        """Should format report with issues section."""
        # Arrange
        formatter = MarkdownFormatter()
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=Path("test.py"),
                metric_value=6000,
                threshold=5000,
                description="File has 6000 lines",
                suggestion="Split file",
            )
        ]
        file_report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=issues,
                quality_score=70.0,
                file_path=Path("test.py"),
                file_lines=6000,
                total_symbols=50,
            ),
            symbol_analysis=None,
        )
        report = TechDebtReport(
            file_reports=[file_report],
            total_files=1,
            total_issues=1,
            critical_issues=1,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            average_quality_score=70.0,
        )

        # Act
        output = formatter.format(report)

        # Assert
        assert "## Issues by Severity" in output
        assert "### CRITICAL (1)" in output
        assert "test.py" in output
        assert "super_large_file" in output

    def test_format_uses_markdown_tables(self):
        """Should use markdown table format."""
        # Arrange
        formatter = MarkdownFormatter()
        file_report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[
                    DebtIssue(
                        severity=DebtSeverity.HIGH,
                        category="large_file",
                        file_path=Path("test.py"),
                        metric_value=3000,
                        threshold=2000,
                        description="File is large",
                        suggestion="Split file",
                    )
                ],
                quality_score=85.0,
                file_path=Path("test.py"),
                file_lines=3000,
                total_symbols=30,
            ),
            symbol_analysis=None,
        )
        report = TechDebtReport(
            file_reports=[file_report],
            total_files=1,
            total_issues=1,
            critical_issues=0,
            high_issues=1,
            medium_issues=0,
            low_issues=0,
            average_quality_score=85.0,
        )

        # Act
        output = formatter.format(report)

        # Assert
        assert "| File |" in output
        assert "| --- |" in output  # Table separator


class TestJSONFormatter:
    """Test JSONFormatter."""

    def test_format_empty_report(self):
        """Should format empty report as JSON."""
        # Arrange
        formatter = JSONFormatter()
        report = TechDebtReport()

        # Act
        output = formatter.format(report)

        # Assert
        import json

        data = json.loads(output)
        assert data["total_files"] == 0
        assert data["total_issues"] == 0
        assert data["average_quality_score"] == 100.0
        assert data["file_reports"] == []

    def test_format_report_with_issues(self):
        """Should format report with issues as JSON."""
        # Arrange
        formatter = JSONFormatter()
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=Path("test.py"),
                metric_value=6000,
                threshold=5000,
                description="File has 6000 lines",
                suggestion="Split file",
            )
        ]
        file_report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=issues,
                quality_score=70.0,
                file_path=Path("test.py"),
                file_lines=6000,
                total_symbols=50,
            ),
            symbol_analysis=None,
        )
        report = TechDebtReport(
            file_reports=[file_report],
            total_files=1,
            total_issues=1,
            critical_issues=1,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            average_quality_score=70.0,
        )

        # Act
        output = formatter.format(report)

        # Assert
        import json

        data = json.loads(output)
        assert data["total_files"] == 1
        assert data["total_issues"] == 1
        assert data["critical_issues"] == 1
        assert len(data["file_reports"]) == 1
        assert data["file_reports"][0]["file_path"] == "test.py"
        assert len(data["file_reports"][0]["issues"]) == 1
        assert data["file_reports"][0]["issues"][0]["severity"] == "CRITICAL"

    def test_json_is_valid_format(self):
        """Should produce valid JSON."""
        # Arrange
        formatter = JSONFormatter()
        report = TechDebtReport(
            file_reports=[],
            total_files=0,
            total_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            average_quality_score=100.0,
        )

        # Act
        output = formatter.format(report)

        # Assert - should not raise
        import json

        json.loads(output)
