"""Test smells detection for test code quality analysis.

This module provides tools to detect anti-patterns in test code, including:
- Skipped tests (it.skip, xit, @skip, @Ignore, @Disabled)
- Giant test files (>1000 lines)

KISS Principle: Simple regex-based detection, no framework-specific logic.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SmellType(Enum):
    """Types of test smells that can be detected."""

    SKIPPED_TEST = "skipped_test"
    GIANT_TEST_FILE = "giant_test_file"


@dataclass
class Smell:
    """Represents a detected test smell.

    Attributes:
        type: The type of test smell
        file_path: Path to the file containing the smell
        details: Human-readable details about the smell
        line_number: Optional line number where the smell was detected
        metric_value: Optional numeric value (e.g., file size)
    """

    type: SmellType
    file_path: Path
    details: str
    line_number: int | None = None
    metric_value: float | None = None


class TestSmellDetector:
    """Detector for test code anti-patterns.

    This detector uses simple pattern matching to identify common test smells
    across multiple testing frameworks (Jest, Mocha, pytest, JUnit, etc.).

    KISS Approach:
    - Generic regex patterns (not framework-specific)
    - Reuse existing file size detection logic
    - No complex AST analysis
    """

    # Threshold for giant test files (lines)
    GIANT_TEST_FILE_THRESHOLD = 1000

    # Patterns for skipped tests (framework-agnostic)
    # Order matters: more specific patterns first to avoid false matches
    SKIP_PATTERNS = [
        (r"@pytest\.mark\.skip", "@pytest.mark.skip"),   # @pytest.mark.skip
        (r"@unittest\.skip", "@unittest.skip"),          # @unittest.skip
        (r"@Ignore\b", "@Ignore"),                       # @Ignore (JUnit 4)
        (r"@Disabled\b", "@Disabled"),                   # @Disabled (JUnit 5)
        (r"@skip\b", "@skip"),                           # @skip (generic)
        (r"\bxit\s*\(", "xit"),                          # xit() (Jest/Mocha)
        (r"\bxdescribe\s*\(", "xdescribe"),              # xdescribe() (Jest/Mocha)
        (r"(it|describe)\.skip\s*\(", "skip"),           # it.skip(), describe.skip()
    ]

    def detect_skipped_tests(self, file_path: Path) -> list[Smell]:
        """Detect skipped tests using regex pattern matching.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of Smell objects for each skipped test found
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        smells = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            for pattern, label in self.SKIP_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    # Extract the actual matched text for details
                    matched_text = match.group(0)
                    smells.append(
                        Smell(
                            type=SmellType.SKIPPED_TEST,
                            file_path=file_path,
                            details=f"Skipped test detected: {matched_text} at line {line_num}",
                            line_number=line_num,
                        )
                    )
                    # Only match once per line
                    break

        return smells

    def detect_giant_test_file(self, parse_result) -> list[Smell]:
        """Detect overly large test files.

        Only checks files that appear to be test files (based on naming convention).

        Args:
            parse_result: ParseResult object with file metadata

        Returns:
            List containing a Smell if the file is too large, empty otherwise
        """
        # Check if this is a test file
        if not self._is_test_file(parse_result.path):
            return []

        if parse_result.file_lines > self.GIANT_TEST_FILE_THRESHOLD:
            return [
                Smell(
                    type=SmellType.GIANT_TEST_FILE,
                    file_path=parse_result.path,
                    details=f"Test file has {parse_result.file_lines} lines "
                    f"(threshold: {self.GIANT_TEST_FILE_THRESHOLD})",
                    metric_value=parse_result.file_lines,
                )
            ]

        return []

    def analyze_test_file(self, file_path: Path, parse_result) -> list[Smell]:
        """Analyze a test file for all types of test smells.

        Convenience method that runs all detection methods.

        Args:
            file_path: Path to the test file
            parse_result: ParseResult object with file metadata

        Returns:
            Combined list of all detected test smells
        """
        smells = []

        # Detect skipped tests
        smells.extend(self.detect_skipped_tests(file_path))

        # Detect giant test file
        smells.extend(self.detect_giant_test_file(parse_result))

        return smells

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file based on naming conventions.

        Checks for common test file patterns:
        - test_*.py / *_test.py (Python)
        - *.test.js / *.spec.js (JavaScript/TypeScript)
        - *Test.java / *Tests.java (Java)
        - __tests__/ directory (JavaScript)

        Args:
            file_path: Path to check

        Returns:
            True if the file appears to be a test file
        """
        name = file_path.name.lower()
        parts = file_path.parts

        # Check filename patterns
        test_patterns = [
            name.startswith("test_"),           # test_auth.py
            name.endswith("_test.py"),          # auth_test.py
            name.endswith(".test.js"),          # auth.test.js
            name.endswith(".test.ts"),          # auth.test.ts
            name.endswith(".spec.js"),          # auth.spec.js
            name.endswith(".spec.ts"),          # auth.spec.ts
            name.endswith("test.java"),         # AuthTest.java
            name.endswith("tests.java"),        # AuthTests.java
        ]

        if any(test_patterns):
            return True

        # Check directory patterns
        test_dirs = {"__tests__", "tests", "test"}
        if any(part.lower() in test_dirs for part in parts):
            return True

        return False
