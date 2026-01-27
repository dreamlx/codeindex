"""Technical debt detection for code analysis.

This module provides tools to detect and analyze technical debt in codebases,
including file size issues, God Classes, and code quality metrics.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

from codeindex.config import Config
from codeindex.parser import ParseResult
from codeindex.symbol_scorer import SymbolImportanceScorer


class DebtSeverity(IntEnum):
    """Severity levels for technical debt issues.

    Lower values indicate higher severity (CRITICAL is most severe).
    """

    CRITICAL = 1  # Must fix: super large files, God Classes
    HIGH = 2  # Should fix: large files, complex methods
    MEDIUM = 3  # Consider fixing: moderate issues
    LOW = 4  # Nice to fix: minor issues


@dataclass
class DebtIssue:
    """Represents a technical debt issue detected in code.

    Attributes:
        severity: The severity level of the issue
        category: Category identifier (e.g., "super_large_file", "god_class")
        file_path: Path to the file containing the issue
        metric_value: Actual measured value (e.g., line count, method count)
        threshold: The threshold value that was exceeded
        description: Human-readable description of the issue
        suggestion: Actionable suggestion for fixing the issue
    """

    severity: DebtSeverity
    category: str
    file_path: Path
    metric_value: float
    threshold: float
    description: str
    suggestion: str


@dataclass
class DebtAnalysisResult:
    """Result of analyzing a file for technical debt.

    Attributes:
        issues: List of detected technical debt issues
        quality_score: Overall code quality score (0-100, higher is better)
        file_path: Path to the analyzed file
        file_lines: Number of lines in the file
        total_symbols: Total number of symbols in the file
    """

    issues: list[DebtIssue] = field(default_factory=list)
    quality_score: float = 100.0
    file_path: Path = Path()
    file_lines: int = 0
    total_symbols: int = 0


@dataclass
class SymbolOverloadAnalysis:
    """Analysis result of symbol overload detection.

    Attributes:
        total_symbols: Total number of symbols in the file
        filtered_symbols: Number of high-quality symbols after filtering
        filter_ratio: Ratio of filtered symbols (0.0 to 1.0)
        noise_breakdown: Dictionary categorizing noise sources
            Keys: "getters_setters", "private_methods", "magic_methods", "other"
            Values: Count of symbols in each category
        quality_score: Symbol quality score (0-100, higher is better)
            Based on filter ratio and noise breakdown
    """

    total_symbols: int = 0
    filtered_symbols: int = 0
    filter_ratio: float = 0.0
    noise_breakdown: dict[str, int] = field(default_factory=dict)
    quality_score: float = 100.0


@dataclass
class FileReport:
    """Report for a single file's technical debt analysis.

    Attributes:
        file_path: Path to the analyzed file
        debt_analysis: DebtAnalysisResult for the file
        symbol_analysis: Optional SymbolOverloadAnalysis for the file
        total_issues: Total number of issues detected (computed property)
    """

    file_path: Path
    debt_analysis: DebtAnalysisResult
    symbol_analysis: SymbolOverloadAnalysis | None = None

    @property
    def total_issues(self) -> int:
        """Calculate total number of issues."""
        return len(self.debt_analysis.issues)


@dataclass
class TechDebtReport:
    """Aggregate report for technical debt across multiple files.

    Attributes:
        file_reports: List of FileReport for each analyzed file
        total_files: Total number of files analyzed
        total_issues: Total number of issues across all files
        critical_issues: Count of CRITICAL severity issues
        high_issues: Count of HIGH severity issues
        medium_issues: Count of MEDIUM severity issues
        low_issues: Count of LOW severity issues
        average_quality_score: Average quality score across all files
    """

    file_reports: list[FileReport] = field(default_factory=list)
    total_files: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    average_quality_score: float = 100.0


class TechDebtReporter:
    """Reporter for aggregating technical debt analysis across multiple files.

    This class collects analysis results from multiple files and generates
    aggregate reports with overall statistics.
    """

    def __init__(self):
        """Initialize the reporter."""
        self._file_reports: list[FileReport] = []

    def add_file_result(
        self,
        file_path: Path,
        debt_analysis: DebtAnalysisResult,
        symbol_analysis: SymbolOverloadAnalysis | None = None,
    ):
        """Add a file analysis result to the reporter.

        Args:
            file_path: Path to the analyzed file
            debt_analysis: DebtAnalysisResult for the file
            symbol_analysis: Optional SymbolOverloadAnalysis for the file
        """
        file_report = FileReport(
            file_path=file_path,
            debt_analysis=debt_analysis,
            symbol_analysis=symbol_analysis,
        )
        self._file_reports.append(file_report)

    def generate_report(self) -> TechDebtReport:
        """Generate aggregate report from all collected file results.

        Returns:
            TechDebtReport with aggregated statistics
        """
        if not self._file_reports:
            return TechDebtReport()

        # Aggregate statistics
        total_files = len(self._file_reports)
        total_issues = 0
        critical_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        total_quality_score = 0.0

        for file_report in self._file_reports:
            total_issues += file_report.total_issues
            total_quality_score += file_report.debt_analysis.quality_score

            # Count issues by severity
            for issue in file_report.debt_analysis.issues:
                if issue.severity == DebtSeverity.CRITICAL:
                    critical_issues += 1
                elif issue.severity == DebtSeverity.HIGH:
                    high_issues += 1
                elif issue.severity == DebtSeverity.MEDIUM:
                    medium_issues += 1
                elif issue.severity == DebtSeverity.LOW:
                    low_issues += 1

        average_quality_score = total_quality_score / total_files

        return TechDebtReport(
            file_reports=self._file_reports,
            total_files=total_files,
            total_issues=total_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            average_quality_score=average_quality_score,
        )


class TechDebtDetector:
    """Detector for technical debt in code.

    This class analyzes parsed code to identify technical debt issues
    such as oversized files, God Classes, and code quality problems.

    Attributes:
        config: Configuration object
        SUPER_LARGE_FILE: Threshold for super large files (>5000 lines)
        LARGE_FILE: Threshold for large files (>2000 lines)
        GOD_CLASS_METHODS: Threshold for God Class detection (>50 methods)
    """

    SUPER_LARGE_FILE = 5000  # Lines
    LARGE_FILE = 2000  # Lines
    GOD_CLASS_METHODS = 50  # Methods per class
    MASSIVE_SYMBOL_COUNT = 100  # Total symbols
    HIGH_NOISE_RATIO = 0.5  # 50% filter ratio

    def __init__(self, config: Config):
        """Initialize the technical debt detector.

        Args:
            config: Configuration object
        """
        self.config = config

    def analyze_file(
        self, parse_result: ParseResult, scorer: SymbolImportanceScorer
    ) -> DebtAnalysisResult:
        """Analyze a file for technical debt.

        Args:
            parse_result: The parsed file to analyze
            scorer: Symbol importance scorer for quality analysis

        Returns:
            DebtAnalysisResult containing detected issues and quality score
        """
        issues = []

        # Detect file-level issues
        issues.extend(self._detect_file_size_issues(parse_result))

        # Detect class-level issues (God Class)
        issues.extend(self._detect_god_class(parse_result))

        # Calculate quality score based on issues
        quality_score = self._calculate_quality_score(parse_result, issues)

        return DebtAnalysisResult(
            issues=issues,
            quality_score=quality_score,
            file_path=parse_result.path,
            file_lines=parse_result.file_lines,
            total_symbols=len(parse_result.symbols),
        )

    def _detect_file_size_issues(self, parse_result: ParseResult) -> list[DebtIssue]:
        """Detect file size related technical debt.

        Args:
            parse_result: The parsed file to analyze

        Returns:
            List of DebtIssue for file size problems
        """
        issues = []
        lines = parse_result.file_lines

        if lines > self.SUPER_LARGE_FILE:
            issues.append(
                DebtIssue(
                    severity=DebtSeverity.CRITICAL,
                    category="super_large_file",
                    file_path=parse_result.path,
                    metric_value=lines,
                    threshold=self.SUPER_LARGE_FILE,
                    description=f"File has {lines} lines (threshold: {self.SUPER_LARGE_FILE})",
                    suggestion="Split into 3-5 smaller files by responsibility",
                )
            )
        elif lines > self.LARGE_FILE:
            issues.append(
                DebtIssue(
                    severity=DebtSeverity.HIGH,
                    category="large_file",
                    file_path=parse_result.path,
                    metric_value=lines,
                    threshold=self.LARGE_FILE,
                    description=f"File has {lines} lines (threshold: {self.LARGE_FILE})",
                    suggestion="Consider splitting into 2-3 smaller modules",
                )
            )

        return issues

    def _detect_god_class(self, parse_result: ParseResult) -> list[DebtIssue]:
        """Detect God Class anti-pattern.

        A God Class is a class with too many responsibilities, indicated by
        having an excessive number of methods.

        Args:
            parse_result: The parsed file to analyze

        Returns:
            List of DebtIssue for God Class problems
        """
        issues = []

        # Group methods by class name
        class_methods: dict[str, list] = defaultdict(list)
        for symbol in parse_result.symbols:
            if symbol.kind == "method":
                # Extract class name from method name
                # Supports both PHP (ClassName::methodName) and Python (ClassName.methodName)
                if "::" in symbol.name:
                    class_name = symbol.name.split("::")[0]
                elif "." in symbol.name and not symbol.name.startswith("_"):
                    class_name = symbol.name.split(".")[0]
                else:
                    continue  # Not a class method

                class_methods[class_name].append(symbol)

        # Check each class for too many methods
        for class_name, methods in class_methods.items():
            method_count = len(methods)
            if method_count > self.GOD_CLASS_METHODS:
                suggested_split_count = max(3, method_count // 20)
                issues.append(
                    DebtIssue(
                        severity=DebtSeverity.CRITICAL,
                        category="god_class",
                        file_path=parse_result.path,
                        metric_value=method_count,
                        threshold=self.GOD_CLASS_METHODS,
                        description=f"Class '{class_name}' has {method_count} methods "
                        f"(threshold: {self.GOD_CLASS_METHODS})",
                        suggestion=f"Extract {suggested_split_count} smaller classes by "
                        f"responsibility",
                    )
                )

        return issues

    def _calculate_quality_score(
        self, parse_result: ParseResult, issues: list[DebtIssue]
    ) -> float:
        """Calculate overall code quality score.

        Starts with 100 points and deducts based on issue severity:
        - CRITICAL: -30 points
        - HIGH: -15 points
        - MEDIUM: -5 points
        - LOW: -2 points

        Args:
            parse_result: The parsed file
            issues: List of detected issues

        Returns:
            Quality score (0-100, higher is better)
        """
        score = 100.0

        for issue in issues:
            if issue.severity == DebtSeverity.CRITICAL:
                score -= 30
            elif issue.severity == DebtSeverity.HIGH:
                score -= 15
            elif issue.severity == DebtSeverity.MEDIUM:
                score -= 5
            elif issue.severity == DebtSeverity.LOW:
                score -= 2

        # Ensure score doesn't go below 0
        return max(0.0, score)

    def analyze_symbol_overload(
        self, parse_result: ParseResult, scorer: SymbolImportanceScorer
    ) -> tuple[list[DebtIssue], SymbolOverloadAnalysis]:
        """Analyze symbol overload issues.

        Detects:
        - Massive symbol count (>100 symbols)
        - High noise ratio (>50% filtered)
        - Data Class smell (>66% getters/setters)

        Args:
            parse_result: The parsed file to analyze
            scorer: Symbol importance scorer for quality analysis

        Returns:
            Tuple of (issues list, SymbolOverloadAnalysis)
        """
        issues = []
        total_symbols = len(parse_result.symbols)

        # Detect massive symbol count
        if total_symbols > self.MASSIVE_SYMBOL_COUNT:
            issues.append(
                DebtIssue(
                    severity=DebtSeverity.CRITICAL,
                    category="massive_symbol_count",
                    file_path=parse_result.path,
                    metric_value=total_symbols,
                    threshold=self.MASSIVE_SYMBOL_COUNT,
                    description=f"File has {total_symbols} symbols "
                    f"(threshold: {self.MASSIVE_SYMBOL_COUNT})",
                    suggestion="Split into multiple modules to reduce cognitive load",
                )
            )

        # Score all symbols and filter
        scored_symbols = []
        for symbol in parse_result.symbols:
            score = scorer.score(symbol)
            scored_symbols.append((symbol, score))

        # Use standard threshold for filtering (30.0 is a reasonable cutoff)
        threshold = 30.0
        filtered_symbols = [s for s, score in scored_symbols if score >= threshold]

        # Calculate metrics
        filtered_count = len(filtered_symbols)
        filter_ratio = 1.0 - (filtered_count / total_symbols) if total_symbols > 0 else 0.0

        # Analyze noise breakdown
        noise_breakdown = self._analyze_noise_breakdown(
            parse_result.symbols, filtered_symbols
        )

        # Detect high noise ratio
        if filter_ratio > self.HIGH_NOISE_RATIO:
            noise_description = self._format_noise_description(noise_breakdown)
            issues.append(
                DebtIssue(
                    severity=DebtSeverity.HIGH,
                    category="low_quality_symbols",
                    file_path=parse_result.path,
                    metric_value=filter_ratio,
                    threshold=self.HIGH_NOISE_RATIO,
                    description=f"High symbol noise ratio: {filter_ratio*100:.1f}% "
                    f"({total_symbols - filtered_count}/{total_symbols} symbols filtered). "
                    f"{noise_description}",
                    suggestion=self._suggest_noise_reduction(noise_breakdown),
                )
            )

        # Calculate quality score
        quality_score = self._calculate_symbol_quality_score(
            total_symbols, filtered_count, noise_breakdown
        )

        analysis = SymbolOverloadAnalysis(
            total_symbols=total_symbols,
            filtered_symbols=filtered_count,
            filter_ratio=filter_ratio,
            noise_breakdown=noise_breakdown,
            quality_score=quality_score,
        )

        return issues, analysis

    def _analyze_noise_breakdown(
        self, all_symbols: list, filtered_symbols: list
    ) -> dict[str, int]:
        """Analyze and categorize noise sources.

        Args:
            all_symbols: All symbols in the file
            filtered_symbols: High-quality symbols after filtering

        Returns:
            Dictionary with noise categories and counts
        """
        # Get filtered symbol names for quick lookup
        filtered_names = {s.name for s in filtered_symbols}

        # Categorize noise
        breakdown = {
            "getters_setters": 0,
            "private_methods": 0,
            "magic_methods": 0,
            "other": 0,
        }

        for symbol in all_symbols:
            if symbol.name in filtered_names:
                continue  # Skip high-quality symbols

            # Categorize this noise symbol
            if symbol.name.startswith(("get", "set")) and len(symbol.name) > 3:
                # Simple getter/setter pattern
                breakdown["getters_setters"] += 1
            elif symbol.name.startswith("_") and not symbol.name.startswith("__"):
                # Private method (single underscore)
                breakdown["private_methods"] += 1
            elif symbol.name.startswith("__") and symbol.name.endswith("__"):
                # Magic method
                breakdown["magic_methods"] += 1
            else:
                breakdown["other"] += 1

        return breakdown

    def _format_noise_description(self, noise_breakdown: dict[str, int]) -> str:
        """Format noise breakdown into readable description.

        Args:
            noise_breakdown: Dictionary of noise categories and counts

        Returns:
            Human-readable description
        """
        parts = []
        if noise_breakdown.get("getters_setters", 0) > 0:
            parts.append(f"{noise_breakdown['getters_setters']} getters/setters")
        if noise_breakdown.get("private_methods", 0) > 0:
            parts.append(f"{noise_breakdown['private_methods']} private methods")
        if noise_breakdown.get("magic_methods", 0) > 0:
            parts.append(f"{noise_breakdown['magic_methods']} magic methods")
        if noise_breakdown.get("other", 0) > 0:
            parts.append(f"{noise_breakdown['other']} other low-quality symbols")

        return "Breakdown: " + ", ".join(parts) if parts else "No breakdown available"

    def _suggest_noise_reduction(self, noise_breakdown: dict[str, int]) -> str:
        """Generate suggestions for reducing symbol noise.

        Args:
            noise_breakdown: Dictionary of noise categories and counts

        Returns:
            Actionable suggestion
        """
        getters_setters = noise_breakdown.get("getters_setters", 0)
        total_noise = sum(noise_breakdown.values())

        if getters_setters > total_noise * 0.66:
            # Data Class smell
            return (
                "Data Class smell detected: >66% getters/setters. "
                "Consider using DTOs, value objects, or applying Tell Don't Ask principle"
            )
        elif getters_setters > 10:
            return (
                "High number of getters/setters. "
                "Consider encapsulating data with behavior or using data classes"
            )
        else:
            return (
                "Reduce low-quality symbols: improve method naming, "
                "merge helpers, or extract utilities"
            )

    def _calculate_symbol_quality_score(
        self, total: int, filtered: int, noise_breakdown: dict[str, int]
    ) -> float:
        """Calculate symbol quality score.

        Args:
            total: Total symbol count
            filtered: Filtered (high-quality) symbol count
            noise_breakdown: Noise categorization

        Returns:
            Quality score (0-100, higher is better)
        """
        if total == 0:
            return 100.0

        # Base score from retention ratio
        retention_ratio = filtered / total
        score = retention_ratio * 100

        # Penalty for getters/setters (Data Class smell)
        getters_setters = noise_breakdown.get("getters_setters", 0)
        if getters_setters > total * 0.5:
            score -= 20  # Heavy penalty for Data Class
        elif getters_setters > total * 0.3:
            score -= 10  # Moderate penalty

        # Penalty for many private methods (poor encapsulation)
        private_methods = noise_breakdown.get("private_methods", 0)
        if private_methods > total * 0.3:
            score -= 10

        return max(0.0, score)
