"""Tests for technical debt reporting."""

from pathlib import Path

from codeindex.tech_debt import (
    DebtAnalysisResult,
    DebtIssue,
    DebtSeverity,
    FileReport,
    SymbolOverloadAnalysis,
    TechDebtReport,
    TechDebtReporter,
)


class TestFileReport:
    """Test FileReport dataclass."""

    def test_create_file_report_with_debt_analysis(self):
        """Should create FileReport with debt analysis."""
        # Arrange
        debt_result = DebtAnalysisResult(
            issues=[],
            quality_score=95.0,
            file_path=Path("test.py"),
            file_lines=100,
            total_symbols=10,
        )

        # Act
        report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=debt_result,
            symbol_analysis=None,
        )

        # Assert
        assert report.file_path == Path("test.py")
        assert report.debt_analysis == debt_result
        assert report.symbol_analysis is None
        assert report.total_issues == 0

    def test_create_file_report_with_symbol_analysis(self):
        """Should create FileReport with both analyses."""
        # Arrange
        debt_result = DebtAnalysisResult(
            issues=[],
            quality_score=95.0,
            file_path=Path("test.py"),
            file_lines=100,
            total_symbols=10,
        )
        symbol_result = SymbolOverloadAnalysis(
            total_symbols=10,
            filtered_symbols=10,
            filter_ratio=0.0,
            noise_breakdown={},
            quality_score=100.0,
        )

        # Act
        report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=debt_result,
            symbol_analysis=symbol_result,
        )

        # Assert
        assert report.symbol_analysis == symbol_result
        assert report.total_issues == 0

    def test_file_report_counts_issues(self):
        """Should count total issues from debt analysis."""
        # Arrange
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=Path("test.py"),
                metric_value=6000,
                threshold=5000,
                description="Test",
                suggestion="Test",
            ),
            DebtIssue(
                severity=DebtSeverity.HIGH,
                category="large_file",
                file_path=Path("test.py"),
                metric_value=3000,
                threshold=2000,
                description="Test",
                suggestion="Test",
            ),
        ]
        debt_result = DebtAnalysisResult(
            issues=issues,
            quality_score=40.0,
            file_path=Path("test.py"),
            file_lines=6000,
            total_symbols=50,
        )

        # Act
        report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=debt_result,
            symbol_analysis=None,
        )

        # Assert
        assert report.total_issues == 2


class TestTechDebtReport:
    """Test TechDebtReport dataclass."""

    def test_create_empty_report(self):
        """Should create empty TechDebtReport."""
        # Act
        report = TechDebtReport()

        # Assert
        assert report.file_reports == []
        assert report.total_files == 0
        assert report.total_issues == 0
        assert report.critical_issues == 0
        assert report.high_issues == 0
        assert report.medium_issues == 0
        assert report.low_issues == 0
        assert report.average_quality_score == 100.0

    def test_create_report_with_one_file(self):
        """Should create report with one file."""
        # Arrange
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=Path("test.py"),
                metric_value=6000,
                threshold=5000,
                description="Test",
                suggestion="Test",
            )
        ]
        debt_result = DebtAnalysisResult(
            issues=issues,
            quality_score=70.0,
            file_path=Path("test.py"),
            file_lines=6000,
            total_symbols=50,
        )
        file_report = FileReport(
            file_path=Path("test.py"),
            debt_analysis=debt_result,
            symbol_analysis=None,
        )

        # Act
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

        # Assert
        assert report.total_files == 1
        assert report.total_issues == 1
        assert report.critical_issues == 1
        assert report.average_quality_score == 70.0

    def test_create_report_with_multiple_files(self):
        """Should aggregate statistics from multiple files."""
        # Arrange
        file_report1 = FileReport(
            file_path=Path("test1.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[
                    DebtIssue(
                        severity=DebtSeverity.CRITICAL,
                        category="test",
                        file_path=Path("test1.py"),
                        metric_value=100,
                        threshold=50,
                        description="Test",
                        suggestion="Test",
                    )
                ],
                quality_score=70.0,
                file_path=Path("test1.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )
        file_report2 = FileReport(
            file_path=Path("test2.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[
                    DebtIssue(
                        severity=DebtSeverity.HIGH,
                        category="test",
                        file_path=Path("test2.py"),
                        metric_value=100,
                        threshold=50,
                        description="Test",
                        suggestion="Test",
                    )
                ],
                quality_score=85.0,
                file_path=Path("test2.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )

        # Act
        report = TechDebtReport(
            file_reports=[file_report1, file_report2],
            total_files=2,
            total_issues=2,
            critical_issues=1,
            high_issues=1,
            medium_issues=0,
            low_issues=0,
            average_quality_score=77.5,
        )

        # Assert
        assert report.total_files == 2
        assert report.total_issues == 2
        assert report.critical_issues == 1
        assert report.high_issues == 1
        assert report.average_quality_score == 77.5


class TestTechDebtReporter:
    """Test TechDebtReporter class."""

    def test_create_reporter(self):
        """Should create an empty TechDebtReporter."""
        # Act
        reporter = TechDebtReporter()

        # Assert
        assert reporter is not None
        assert len(reporter._file_reports) == 0

    def test_add_single_file_result(self):
        """Should add a file result to the reporter."""
        # Arrange
        reporter = TechDebtReporter()
        debt_result = DebtAnalysisResult(
            issues=[],
            quality_score=95.0,
            file_path=Path("test.py"),
            file_lines=100,
            total_symbols=10,
        )

        # Act
        reporter.add_file_result(
            file_path=Path("test.py"),
            debt_analysis=debt_result,
            symbol_analysis=None,
        )

        # Assert
        assert len(reporter._file_reports) == 1
        assert reporter._file_reports[0].file_path == Path("test.py")

    def test_add_multiple_file_results(self):
        """Should add multiple file results."""
        # Arrange
        reporter = TechDebtReporter()

        # Act
        reporter.add_file_result(
            file_path=Path("test1.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[],
                quality_score=95.0,
                file_path=Path("test1.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )
        reporter.add_file_result(
            file_path=Path("test2.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[],
                quality_score=85.0,
                file_path=Path("test2.py"),
                file_lines=200,
                total_symbols=20,
            ),
            symbol_analysis=None,
        )

        # Assert
        assert len(reporter._file_reports) == 2

    def test_generate_report_for_empty_reporter(self):
        """Should generate empty report."""
        # Arrange
        reporter = TechDebtReporter()

        # Act
        report = reporter.generate_report()

        # Assert
        assert report.total_files == 0
        assert report.total_issues == 0
        assert report.average_quality_score == 100.0

    def test_generate_report_for_single_file(self):
        """Should generate report with correct statistics for single file."""
        # Arrange
        reporter = TechDebtReporter()
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="super_large_file",
                file_path=Path("test.py"),
                metric_value=6000,
                threshold=5000,
                description="Test",
                suggestion="Test",
            ),
            DebtIssue(
                severity=DebtSeverity.HIGH,
                category="large_file",
                file_path=Path("test.py"),
                metric_value=3000,
                threshold=2000,
                description="Test",
                suggestion="Test",
            ),
        ]
        reporter.add_file_result(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=issues,
                quality_score=55.0,
                file_path=Path("test.py"),
                file_lines=6000,
                total_symbols=50,
            ),
            symbol_analysis=None,
        )

        # Act
        report = reporter.generate_report()

        # Assert
        assert report.total_files == 1
        assert report.total_issues == 2
        assert report.critical_issues == 1
        assert report.high_issues == 1
        assert report.medium_issues == 0
        assert report.low_issues == 0
        assert report.average_quality_score == 55.0

    def test_generate_report_for_multiple_files(self):
        """Should aggregate statistics from multiple files."""
        # Arrange
        reporter = TechDebtReporter()

        # File 1: 1 CRITICAL issue, quality 70.0
        reporter.add_file_result(
            file_path=Path("test1.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[
                    DebtIssue(
                        severity=DebtSeverity.CRITICAL,
                        category="test",
                        file_path=Path("test1.py"),
                        metric_value=100,
                        threshold=50,
                        description="Test",
                        suggestion="Test",
                    )
                ],
                quality_score=70.0,
                file_path=Path("test1.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )

        # File 2: 2 HIGH issues, quality 85.0
        reporter.add_file_result(
            file_path=Path("test2.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[
                    DebtIssue(
                        severity=DebtSeverity.HIGH,
                        category="test",
                        file_path=Path("test2.py"),
                        metric_value=100,
                        threshold=50,
                        description="Test1",
                        suggestion="Test1",
                    ),
                    DebtIssue(
                        severity=DebtSeverity.HIGH,
                        category="test",
                        file_path=Path("test2.py"),
                        metric_value=100,
                        threshold=50,
                        description="Test2",
                        suggestion="Test2",
                    ),
                ],
                quality_score=85.0,
                file_path=Path("test2.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )

        # File 3: No issues, quality 100.0
        reporter.add_file_result(
            file_path=Path("test3.py"),
            debt_analysis=DebtAnalysisResult(
                issues=[],
                quality_score=100.0,
                file_path=Path("test3.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )

        # Act
        report = reporter.generate_report()

        # Assert
        assert report.total_files == 3
        assert report.total_issues == 3
        assert report.critical_issues == 1
        assert report.high_issues == 2
        assert report.medium_issues == 0
        assert report.low_issues == 0
        # Average: (70 + 85 + 100) / 3 = 85.0
        assert report.average_quality_score == 85.0

    def test_generate_report_with_all_severity_levels(self):
        """Should count all severity levels correctly."""
        # Arrange
        reporter = TechDebtReporter()
        issues = [
            DebtIssue(
                severity=DebtSeverity.CRITICAL,
                category="test",
                file_path=Path("test.py"),
                metric_value=100,
                threshold=50,
                description="Critical",
                suggestion="Fix critical",
            ),
            DebtIssue(
                severity=DebtSeverity.HIGH,
                category="test",
                file_path=Path("test.py"),
                metric_value=100,
                threshold=50,
                description="High",
                suggestion="Fix high",
            ),
            DebtIssue(
                severity=DebtSeverity.MEDIUM,
                category="test",
                file_path=Path("test.py"),
                metric_value=100,
                threshold=50,
                description="Medium",
                suggestion="Fix medium",
            ),
            DebtIssue(
                severity=DebtSeverity.LOW,
                category="test",
                file_path=Path("test.py"),
                metric_value=100,
                threshold=50,
                description="Low",
                suggestion="Fix low",
            ),
        ]
        reporter.add_file_result(
            file_path=Path("test.py"),
            debt_analysis=DebtAnalysisResult(
                issues=issues,
                quality_score=50.0,
                file_path=Path("test.py"),
                file_lines=100,
                total_symbols=10,
            ),
            symbol_analysis=None,
        )

        # Act
        report = reporter.generate_report()

        # Assert
        assert report.critical_issues == 1
        assert report.high_issues == 1
        assert report.medium_issues == 1
        assert report.low_issues == 1
