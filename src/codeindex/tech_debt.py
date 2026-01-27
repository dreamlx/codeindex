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
