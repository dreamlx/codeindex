"""Formatters for technical debt reports.

This module provides different output formatters for technical debt reports:
- ConsoleFormatter: Human-readable console output with colors
- MarkdownFormatter: Markdown format for documentation
- JSONFormatter: Machine-readable JSON format
"""

import json
from abc import ABC, abstractmethod

from codeindex.tech_debt import DebtSeverity, TechDebtReport


class ReportFormatter(ABC):
    """Abstract base class for report formatters."""

    @abstractmethod
    def format(self, report: TechDebtReport) -> str:
        """Format a technical debt report.

        Args:
            report: TechDebtReport to format

        Returns:
            Formatted report as string
        """
        pass


class ConsoleFormatter(ReportFormatter):
    """Formatter for console output with ANSI colors."""

    # ANSI color codes
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, report: TechDebtReport) -> str:
        """Format report for console output.

        Args:
            report: TechDebtReport to format

        Returns:
            Formatted string with ANSI colors
        """
        lines = []

        # Header
        lines.append(f"\n{self.BOLD}Technical Debt Report{self.RESET}")
        lines.append("=" * 50)

        # Summary
        lines.append(f"\n{self.BOLD}Summary:{self.RESET}")
        lines.append(f"  Files analyzed: {report.total_files} files analyzed")
        lines.append(f"  Total issues: {report.total_issues} issues found")
        lines.append(f"  Quality Score: {report.average_quality_score:.1f}")

        # Severity breakdown
        if report.total_issues > 0:
            lines.append(f"\n{self.BOLD}Issues by Severity:{self.RESET}")
            if report.critical_issues > 0:
                lines.append(f"  {self.RED}CRITICAL: {report.critical_issues}{self.RESET}")
            if report.high_issues > 0:
                lines.append(f"  {self.YELLOW}HIGH: {report.high_issues}{self.RESET}")
            if report.medium_issues > 0:
                lines.append(f"  MEDIUM: {report.medium_issues}")
            if report.low_issues > 0:
                lines.append(f"  LOW: {report.low_issues}")

        # File details
        if report.file_reports:
            lines.append(f"\n{self.BOLD}Files:{self.RESET}")
            for file_report in report.file_reports:
                if file_report.total_issues > 0:
                    lines.append(f"\n  {file_report.file_path}:")
                    for issue in file_report.debt_analysis.issues:
                        severity_color = self._get_severity_color(issue.severity)
                        lines.append(
                            f"    {severity_color}{issue.severity.name}{self.RESET} "
                            f"[{issue.category}] {issue.description}"
                        )

        lines.append("")
        return "\n".join(lines)

    def _get_severity_color(self, severity: DebtSeverity) -> str:
        """Get ANSI color code for severity level."""
        if severity == DebtSeverity.CRITICAL:
            return self.RED
        elif severity == DebtSeverity.HIGH:
            return self.YELLOW
        else:
            return ""


class MarkdownFormatter(ReportFormatter):
    """Formatter for Markdown output."""

    def format(self, report: TechDebtReport) -> str:
        """Format report as Markdown.

        Args:
            report: TechDebtReport to format

        Returns:
            Formatted Markdown string
        """
        lines = []

        # Header
        lines.append("# Technical Debt Report")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Files Analyzed:** {report.total_files}")
        lines.append(f"- **Total Issues:** {report.total_issues}")
        lines.append(f"- **Quality Score:** {report.average_quality_score:.1f}/100")
        lines.append("")

        # Severity breakdown
        if report.total_issues > 0:
            lines.append("### Issues by Severity")
            lines.append("")
            lines.append(f"- **CRITICAL:** {report.critical_issues}")
            lines.append(f"- **HIGH:** {report.high_issues}")
            lines.append(f"- **MEDIUM:** {report.medium_issues}")
            lines.append(f"- **LOW:** {report.low_issues}")
            lines.append("")

        # Issues by severity level
        if report.total_issues > 0:
            lines.append("## Issues by Severity")
            lines.append("")

            # CRITICAL issues
            if report.critical_issues > 0:
                lines.append(f"### CRITICAL ({report.critical_issues})")
                lines.append("")
                lines.extend(self._format_issues_table(report, DebtSeverity.CRITICAL))
                lines.append("")

            # HIGH issues
            if report.high_issues > 0:
                lines.append(f"### HIGH ({report.high_issues})")
                lines.append("")
                lines.extend(self._format_issues_table(report, DebtSeverity.HIGH))
                lines.append("")

            # MEDIUM issues
            if report.medium_issues > 0:
                lines.append(f"### MEDIUM ({report.medium_issues})")
                lines.append("")
                lines.extend(self._format_issues_table(report, DebtSeverity.MEDIUM))
                lines.append("")

            # LOW issues
            if report.low_issues > 0:
                lines.append(f"### LOW ({report.low_issues})")
                lines.append("")
                lines.extend(self._format_issues_table(report, DebtSeverity.LOW))
                lines.append("")

        return "\n".join(lines)

    def _format_issues_table(
        self, report: TechDebtReport, severity: DebtSeverity
    ) -> list[str]:
        """Format issues of a specific severity as a markdown table."""
        lines = []
        lines.append("| File | Category | Description | Suggestion |")
        lines.append("| --- | --- | --- | --- |")

        for file_report in report.file_reports:
            for issue in file_report.debt_analysis.issues:
                if issue.severity == severity:
                    file_path = issue.file_path.name
                    lines.append(
                        f"| {file_path} | {issue.category} | "
                        f"{issue.description} | {issue.suggestion} |"
                    )

        return lines


class JSONFormatter(ReportFormatter):
    """Formatter for JSON output."""

    def format(self, report: TechDebtReport) -> str:
        """Format report as JSON.

        Args:
            report: TechDebtReport to format

        Returns:
            Formatted JSON string
        """
        data = {
            "total_files": report.total_files,
            "total_issues": report.total_issues,
            "critical_issues": report.critical_issues,
            "high_issues": report.high_issues,
            "medium_issues": report.medium_issues,
            "low_issues": report.low_issues,
            "average_quality_score": report.average_quality_score,
            "file_reports": [
                {
                    "file_path": str(file_report.file_path),
                    "quality_score": file_report.debt_analysis.quality_score,
                    "file_lines": file_report.debt_analysis.file_lines,
                    "total_symbols": file_report.debt_analysis.total_symbols,
                    "total_issues": file_report.total_issues,
                    "issues": [
                        {
                            "severity": issue.severity.name,
                            "category": issue.category,
                            "metric_value": issue.metric_value,
                            "threshold": issue.threshold,
                            "description": issue.description,
                            "suggestion": issue.suggestion,
                        }
                        for issue in file_report.debt_analysis.issues
                    ],
                }
                for file_report in report.file_reports
            ],
        }

        return json.dumps(data, indent=2)
