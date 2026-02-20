"""Tests for technical debt detection."""

from pathlib import Path

from codeindex.parser import Import, ParseResult, Symbol
from codeindex.tech_debt import (
    DebtAnalysisResult,
    DebtIssue,
    DebtSeverity,
    TechDebtDetector,
)

from .conftest import create_mock_parse_result


class TestDebtSeverity:
    """Test DebtSeverity enum."""

    def test_severity_levels_exist(self):
        """Should have all severity levels defined."""
        assert hasattr(DebtSeverity, "CRITICAL")
        assert hasattr(DebtSeverity, "HIGH")
        assert hasattr(DebtSeverity, "MEDIUM")
        assert hasattr(DebtSeverity, "LOW")

    def test_severity_ordering(self):
        """Severity levels should have meaningful ordering."""
        # CRITICAL should be highest priority (lowest value if using int enum)
        assert DebtSeverity.CRITICAL.value < DebtSeverity.HIGH.value
        assert DebtSeverity.HIGH.value < DebtSeverity.MEDIUM.value
        assert DebtSeverity.MEDIUM.value < DebtSeverity.LOW.value


class TestDebtIssue:
    """Test DebtIssue dataclass."""

    def test_create_debt_issue(self):
        """Should create a DebtIssue with all fields."""
        issue = DebtIssue(
            severity=DebtSeverity.CRITICAL,
            category="super_large_file",
            file_path=Path("test.php"),
            metric_value=8891,
            threshold=5000,
            description="File has 8891 lines (threshold: 5000)",
            suggestion="Split into 3-5 smaller files by responsibility",
        )

        assert issue.severity == DebtSeverity.CRITICAL
        assert issue.category == "super_large_file"
        assert issue.file_path == Path("test.php")
        assert issue.metric_value == 8891
        assert issue.threshold == 5000
        assert "8891" in issue.description
        assert "split" in issue.suggestion.lower()


class TestDebtAnalysisResult:
    """Test DebtAnalysisResult dataclass."""

    def test_create_analysis_result(self):
        """Should create a DebtAnalysisResult with all fields."""
        issue = DebtIssue(
            severity=DebtSeverity.CRITICAL,
            category="super_large_file",
            file_path=Path("test.php"),
            metric_value=8891,
            threshold=5000,
            description="File has 8891 lines",
            suggestion="Split the file",
        )

        result = DebtAnalysisResult(
            issues=[issue],
            quality_score=40.0,
            file_path=Path("test.php"),
            file_lines=8891,
            total_symbols=57,
        )

        assert len(result.issues) == 1
        assert result.quality_score == 40.0
        assert result.file_path == Path("test.php")
        assert result.file_lines == 8891
        assert result.total_symbols == 57

    def test_analysis_result_with_no_issues(self):
        """Normal files should have empty issues list."""
        result = DebtAnalysisResult(
            issues=[],
            quality_score=95.0,
            file_path=Path("normal.php"),
            file_lines=300,
            total_symbols=15,
        )

        assert len(result.issues) == 0
        assert result.quality_score > 90


class TestTechDebtDetector:
    """Test TechDebtDetector class."""

    def test_create_detector(self, mock_config):
        """Should create a TechDebtDetector with config."""
        detector = TechDebtDetector(mock_config)
        assert detector is not None
        assert detector.config == mock_config

    def test_detector_has_thresholds(self, mock_config):
        """Detector should have all detection thresholds configured."""
        detector = TechDebtDetector(mock_config)
        assert hasattr(detector, "classifier")
        # God Class thresholds
        assert detector.GOD_CLASS_METHODS_WARN == 20
        assert detector.GOD_CLASS_METHODS_CRITICAL == 50
        assert detector.GOD_CLASS_METHODS == 50  # backward compat
        # Long method thresholds
        assert detector.LONG_METHOD_WARN == 80
        assert detector.LONG_METHOD_HIGH == 150
        # Function/coupling thresholds
        assert detector.MAX_TOP_LEVEL_FUNCTIONS == 15
        assert detector.MAX_INTERNAL_IMPORTS == 8
        # Language-aware file size thresholds
        assert "compact" in detector.FILE_SIZE_THRESHOLDS
        assert "verbose" in detector.FILE_SIZE_THRESHOLDS
        assert detector.FILE_SIZE_THRESHOLDS["compact"]["medium"] == 800
        assert detector.FILE_SIZE_THRESHOLDS["verbose"]["medium"] == 1500


class TestFileSizeDetection:
    """Test file size detection functionality."""

    def test_detect_super_large_file(self, mock_config, symbol_scorer):
        """Should detect files >5000 lines as CRITICAL."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=8891, symbol_count=57)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        critical_issues = [i for i in result.issues if i.severity == DebtSeverity.CRITICAL]
        assert len(critical_issues) >= 1
        assert any(i.category == "super_large_file" for i in critical_issues)
        # Check description includes line count
        super_large_issue = next(i for i in critical_issues if i.category == "super_large_file")
        assert "8891" in super_large_issue.description
        assert super_large_issue.metric_value == 8891
        assert super_large_issue.threshold == 5000

    def test_super_large_file_has_split_suggestion(self, mock_config, symbol_scorer):
        """Super large file suggestion should recommend splitting."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=8891)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        super_large_issue = next(
            i for i in result.issues if i.category == "super_large_file"
        )
        assert "split" in super_large_issue.suggestion.lower()
        assert "3-5" in super_large_issue.suggestion or "smaller" in super_large_issue.suggestion

    def test_detect_large_file(self, mock_config, symbol_scorer):
        """Should detect files >2000 lines as HIGH (not CRITICAL)."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=3000, symbol_count=30)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        high_issues = [i for i in result.issues if i.severity == DebtSeverity.HIGH]
        assert len(high_issues) >= 1
        assert any(i.category == "large_file" for i in high_issues)
        # Should NOT have CRITICAL super_large_file issue
        critical_issues = [i for i in result.issues if i.severity == DebtSeverity.CRITICAL]
        assert not any(i.category == "super_large_file" for i in critical_issues)

    def test_normal_file_no_size_issues(self, mock_config, symbol_scorer):
        """Normal files should have no size-related issues."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=300, symbol_count=15)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        size_issues = [
            i for i in result.issues if i.category in ("super_large_file", "large_file")
        ]
        assert len(size_issues) == 0
        assert result.quality_score > 90  # Should have high quality score

    def test_file_at_large_threshold_boundary(self, mock_config, symbol_scorer):
        """File with exactly 2000 lines should NOT be flagged."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=2000)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        size_issues = [
            i for i in result.issues if i.category in ("super_large_file", "large_file")
        ]
        assert len(size_issues) == 0

    def test_file_just_over_large_threshold(self, mock_config, symbol_scorer):
        """File with 2001 lines (PHP/verbose) should be flagged as medium_file (>1500)."""
        # Arrange - default file_path=test.php uses verbose thresholds (medium=1500)
        parse_result = create_mock_parse_result(file_lines=2001)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert - 2001 > 1500 (verbose medium) but < 2500 (verbose large)
        medium_issues = [i for i in result.issues if i.category == "medium_file"]
        assert len(medium_issues) == 1
        assert medium_issues[0].severity == DebtSeverity.MEDIUM

    def test_file_at_super_large_threshold_boundary(self, mock_config, symbol_scorer):
        """File with exactly 5000 lines should NOT be flagged as super large."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=5000)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        super_large_issues = [i for i in result.issues if i.category == "super_large_file"]
        assert len(super_large_issues) == 0
        # But should be flagged as large_file
        large_issues = [i for i in result.issues if i.category == "large_file"]
        assert len(large_issues) == 1

    def test_file_just_over_super_large_threshold(self, mock_config, symbol_scorer):
        """File with 5001 lines should be flagged as super_large_file."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=5001)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        super_large_issues = [i for i in result.issues if i.category == "super_large_file"]
        assert len(super_large_issues) == 1
        assert super_large_issues[0].severity == DebtSeverity.CRITICAL
        # Should NOT also flag as large_file (super_large takes precedence)
        large_issues = [i for i in result.issues if i.category == "large_file"]
        assert len(large_issues) == 0


class TestGodClassDetection:
    """Test God Class detection functionality."""

    def test_detect_god_class(self, mock_config, symbol_scorer):
        """Should detect classes with >50 methods as CRITICAL."""
        # Arrange
        parse_result = create_mock_parse_result(
            file_lines=2000, class_name="OperateGoods", methods_per_class=57
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        critical_issues = [i for i in result.issues if i.severity == DebtSeverity.CRITICAL]
        assert len(critical_issues) >= 1
        god_class_issues = [i for i in critical_issues if i.category == "god_class"]
        assert len(god_class_issues) == 1
        assert "OperateGoods" in god_class_issues[0].description
        assert god_class_issues[0].metric_value == 57
        assert god_class_issues[0].threshold == 50

    def test_god_class_suggestion_calculates_split_count(self, mock_config, symbol_scorer):
        """God Class suggestion should recommend specific number of classes."""
        # Arrange
        parse_result = create_mock_parse_result(
            file_lines=2000, class_name="OperateGoods", methods_per_class=57
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issue = next(i for i in result.issues if i.category == "god_class")
        # 57 methods / 20 = 2.85 → should suggest at least 3 classes
        assert "extract" in god_class_issue.suggestion.lower()
        assert "3" in god_class_issue.suggestion or "smaller" in god_class_issue.suggestion

    def test_normal_class_no_god_class_issue(self, mock_config, symbol_scorer):
        """Normal classes should not be flagged as God Class."""
        # Arrange
        parse_result = create_mock_parse_result(
            file_lines=500, class_name="UserService", methods_per_class=20
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 0

    def test_class_at_god_class_threshold_boundary(self, mock_config, symbol_scorer):
        """Class with exactly 50 methods should NOT be flagged."""
        # Arrange
        parse_result = create_mock_parse_result(
            file_lines=1000, class_name="LargeService", methods_per_class=50
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 0

    def test_class_just_over_god_class_threshold(self, mock_config, symbol_scorer):
        """Class with 51 methods should be flagged as God Class."""
        # Arrange
        parse_result = create_mock_parse_result(
            file_lines=1000, class_name="LargeService", methods_per_class=51
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 1
        assert god_class_issues[0].severity == DebtSeverity.CRITICAL

    def test_multiple_classes_in_one_file(self, mock_config, symbol_scorer):
        """Should detect multiple God Classes in one file."""
        # Arrange - manually create parse result with two God Classes
        from codeindex.parser import ParseResult, Symbol

        symbols = []
        # First God Class: UserManager with 55 methods
        for i in range(55):
            symbols.append(
                Symbol(
                    name=f"UserManager::method{i}",
                    kind="method",
                    signature=f"public function method{i}()",
                    docstring="",
                    line_start=i * 10,
                    line_end=i * 10 + 5,
                )
            )
        # Second God Class: OrderProcessor with 60 methods
        for i in range(60):
            symbols.append(
                Symbol(
                    name=f"OrderProcessor::process{i}",
                    kind="method",
                    signature=f"public function process{i}()",
                    docstring="",
                    line_start=1000 + i * 10,
                    line_end=1000 + i * 10 + 5,
                )
            )

        parse_result = ParseResult(
            path=Path("multi_class.php"), file_lines=2500, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 2
        class_names = [i.description for i in god_class_issues]
        assert any("UserManager" in desc for desc in class_names)
        assert any("OrderProcessor" in desc for desc in class_names)

    def test_python_style_method_names(self, mock_config, symbol_scorer):
        """Should handle Python-style method names (ClassName.method_name)."""
        # Arrange - manually create parse result with Python-style names
        from codeindex.parser import ParseResult, Symbol

        symbols = []
        for i in range(55):
            symbols.append(
                Symbol(
                    name=f"DataProcessor.process_item_{i}",
                    kind="method",
                    signature=f"def process_item_{i}(self):",
                    docstring="",
                    line_start=i * 10,
                    line_end=i * 10 + 5,
                )
            )

        parse_result = ParseResult(
            path=Path("processor.py"), file_lines=1000, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 1
        assert "DataProcessor" in god_class_issues[0].description

    def test_ignore_functions_not_methods(self, mock_config, symbol_scorer):
        """Should not count standalone functions as class methods."""
        # Arrange - create 60 standalone functions (not methods)
        parse_result = create_mock_parse_result(file_lines=1000, symbol_count=60)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 0  # Standalone functions don't count


class TestQualityScoreCalculation:
    """Test quality score calculation."""

    def test_quality_score_normal_file(self, mock_config, symbol_scorer):
        """Normal files should have high quality score (>80)."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=300, symbol_count=15)
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        assert result.quality_score > 80
        assert result.quality_score == 100.0  # No issues = perfect score

    def test_quality_score_with_critical_issue(self, mock_config, symbol_scorer):
        """Critical issues should significantly reduce quality score (-30)."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=8891)  # Super large file
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        # 100 - 30 (CRITICAL) = 70
        assert result.quality_score == 70.0

    def test_quality_score_with_high_issue(self, mock_config, symbol_scorer):
        """High issues should moderately reduce quality score (-15)."""
        # Arrange
        parse_result = create_mock_parse_result(file_lines=3000)  # Large file
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        # 100 - 15 (HIGH) = 85
        assert result.quality_score == 85.0

    def test_quality_score_multiple_issues(self, mock_config, symbol_scorer):
        """Multiple issues should cumulate score reduction."""
        # Arrange - super large file with God Class
        parse_result = create_mock_parse_result(
            file_lines=8891, class_name="HugeClass", methods_per_class=57
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        # 100 - 30 (super_large_file CRITICAL) - 30 (god_class CRITICAL) = 40
        assert result.quality_score == 40.0
        assert len(result.issues) == 2

    def test_quality_score_minimum_zero(self, mock_config, symbol_scorer):
        """Quality score should not go below 0."""
        # Arrange - create a file with many issues
        from codeindex.parser import ParseResult, Symbol

        symbols = []
        # Create 5 God Classes (each -30 = -150 total)
        for class_num in range(5):
            for method_num in range(60):
                symbols.append(
                    Symbol(
                        name=f"GodClass{class_num}::method{method_num}",
                        kind="method",
                        signature=f"public function method{method_num}()",
                        docstring="",
                        line_start=class_num * 1000 + method_num * 10,
                        line_end=class_num * 1000 + method_num * 10 + 5,
                    )
                )

        parse_result = ParseResult(
            path=Path("terrible.php"), file_lines=8891, symbols=symbols  # Super large file
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        # 100 - 30 (super_large) - 5*30 (god_classes) = 100 - 180 = -80, but min is 0
        assert result.quality_score == 0.0
        assert result.quality_score >= 0.0

    def test_quality_score_mixed_severities(self, mock_config, symbol_scorer):
        """Should correctly calculate score with mixed severity issues."""
        # Arrange - large file (not super large) with God Class
        parse_result = create_mock_parse_result(
            file_lines=3000,  # Large file (HIGH: -15)
            class_name="LargeClass",
            methods_per_class=57,  # God Class (CRITICAL: -30)
        )
        detector = TechDebtDetector(mock_config)

        # Act
        result = detector.analyze_file(parse_result, symbol_scorer)

        # Assert
        # 100 - 15 (large_file HIGH) - 30 (god_class CRITICAL) = 55
        assert result.quality_score == 55.0

    def test_quality_score_decreases_with_more_issues(self, mock_config, symbol_scorer):
        """Adding more issues should decrease quality score."""
        # Arrange
        detector = TechDebtDetector(mock_config)

        # Normal file
        normal = create_mock_parse_result(file_lines=300, symbol_count=15)
        result_normal = detector.analyze_file(normal, symbol_scorer)

        # Large file
        large = create_mock_parse_result(file_lines=3000, symbol_count=30)
        result_large = detector.analyze_file(large, symbol_scorer)

        # Super large file
        super_large = create_mock_parse_result(file_lines=8891, symbol_count=57)
        result_super_large = detector.analyze_file(super_large, symbol_scorer)

        # Assert
        assert result_normal.quality_score > result_large.quality_score
        assert result_large.quality_score > result_super_large.quality_score
        assert result_normal.quality_score == 100.0
        # large: 3000 lines (large_file HIGH -15) + 30 functions (too_many_functions MEDIUM -5) = 80
        assert result_large.quality_score == 80.0
        # super_large: 8891 lines (super_large_file CRITICAL -30) + 57 functions (too_many_functions MEDIUM -5) = 65
        assert result_super_large.quality_score == 65.0


class TestLongMethodDetection:
    """Test long method/function detection."""

    def test_short_method_no_issue(self, mock_config, symbol_scorer):
        """Methods <=80 lines should not be flagged."""
        parse_result = create_mock_parse_result(
            file_lines=200, functions_count=3, method_lines=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 0

    def test_medium_long_method(self, mock_config, symbol_scorer):
        """Methods >80 lines should be flagged as MEDIUM."""
        symbols = [
            Symbol(
                name="big_function",
                kind="function",
                signature="def big_function():",
                docstring="",
                line_start=1,
                line_end=91,  # 91 lines (>80)
            ),
        ]
        parse_result = ParseResult(
            path=Path("test.py"), file_lines=200, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 1
        assert long_method_issues[0].severity == DebtSeverity.MEDIUM
        assert long_method_issues[0].metric_value == 91

    def test_very_long_method(self, mock_config, symbol_scorer):
        """Methods >150 lines should be flagged as HIGH."""
        symbols = [
            Symbol(
                name="huge_function",
                kind="function",
                signature="def huge_function():",
                docstring="",
                line_start=1,
                line_end=180,  # 180 lines (>150)
            ),
        ]
        parse_result = ParseResult(
            path=Path("test.py"), file_lines=300, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 1
        assert long_method_issues[0].severity == DebtSeverity.HIGH
        assert long_method_issues[0].metric_value == 180

    def test_method_at_80_boundary(self, mock_config, symbol_scorer):
        """Method with exactly 80 lines should NOT be flagged."""
        symbols = [
            Symbol(
                name="boundary_func",
                kind="function",
                signature="def boundary_func():",
                docstring="",
                line_start=1,
                line_end=80,  # exactly 80 lines
            ),
        ]
        parse_result = ParseResult(
            path=Path("test.py"), file_lines=200, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 0

    def test_method_at_81_boundary(self, mock_config, symbol_scorer):
        """Method with 81 lines should be flagged as MEDIUM."""
        symbols = [
            Symbol(
                name="boundary_func",
                kind="function",
                signature="def boundary_func():",
                docstring="",
                line_start=1,
                line_end=81,  # 81 lines (>80)
            ),
        ]
        parse_result = ParseResult(
            path=Path("test.py"), file_lines=200, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 1
        assert long_method_issues[0].severity == DebtSeverity.MEDIUM

    def test_multiple_long_methods(self, mock_config, symbol_scorer):
        """Should detect multiple long methods in same file."""
        symbols = [
            Symbol(
                name="func_a",
                kind="function",
                signature="def func_a():",
                docstring="",
                line_start=1,
                line_end=90,
            ),
            Symbol(
                name="func_b",
                kind="function",
                signature="def func_b():",
                docstring="",
                line_start=100,
                line_end=260,  # 161 lines (HIGH)
            ),
        ]
        parse_result = ParseResult(
            path=Path("test.py"), file_lines=400, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 2
        severities = {i.severity for i in long_method_issues}
        assert DebtSeverity.MEDIUM in severities
        assert DebtSeverity.HIGH in severities


class TestTooManyFunctionsDetection:
    """Test too-many-functions detection."""

    def test_few_functions_no_issue(self, mock_config, symbol_scorer):
        """<=15 top-level functions should not be flagged."""
        parse_result = create_mock_parse_result(
            file_lines=500, functions_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        func_issues = [i for i in result.issues if i.category == "too_many_functions"]
        assert len(func_issues) == 0

    def test_too_many_functions(self, mock_config, symbol_scorer):
        """More than 15 top-level functions should be flagged as MEDIUM."""
        parse_result = create_mock_parse_result(
            file_lines=500, functions_count=16
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        func_issues = [i for i in result.issues if i.category == "too_many_functions"]
        assert len(func_issues) == 1
        assert func_issues[0].severity == DebtSeverity.MEDIUM
        assert func_issues[0].metric_value == 16
        assert func_issues[0].threshold == 15

    def test_exactly_15_functions_no_issue(self, mock_config, symbol_scorer):
        """Exactly 15 functions should NOT be flagged."""
        parse_result = create_mock_parse_result(
            file_lines=500, functions_count=15
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        func_issues = [i for i in result.issues if i.category == "too_many_functions"]
        assert len(func_issues) == 0

    def test_methods_not_counted_as_functions(self, mock_config, symbol_scorer):
        """Class methods should not be counted as top-level functions."""
        parse_result = create_mock_parse_result(
            file_lines=500, class_name="MyClass", methods_per_class=20
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        func_issues = [i for i in result.issues if i.category == "too_many_functions"]
        assert len(func_issues) == 0


class TestHighCouplingDetection:
    """Test high import coupling detection."""

    def test_few_imports_no_issue(self, mock_config, symbol_scorer):
        """<=8 internal imports should not be flagged."""
        imports = [
            Import(module=".utils", names=["helper"], is_from=True),
            Import(module=".config", names=["Config"], is_from=True),
            Import(module=".parser", names=["ParseResult"], is_from=True),
        ]
        parse_result = create_mock_parse_result(
            file_path="test.py", file_lines=200, imports=imports
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        coupling_issues = [i for i in result.issues if i.category == "high_coupling"]
        assert len(coupling_issues) == 0

    def test_high_internal_imports(self, mock_config, symbol_scorer):
        """More than 8 internal imports should be flagged as MEDIUM."""
        imports = [
            Import(module=f".module{i}", names=[f"Class{i}"], is_from=True)
            for i in range(9)
        ]
        parse_result = create_mock_parse_result(
            file_path="test.py", file_lines=200, imports=imports
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        coupling_issues = [i for i in result.issues if i.category == "high_coupling"]
        assert len(coupling_issues) == 1
        assert coupling_issues[0].severity == DebtSeverity.MEDIUM
        assert coupling_issues[0].metric_value == 9
        assert coupling_issues[0].threshold == 8

    def test_external_imports_not_counted(self, mock_config, symbol_scorer):
        """External (non-relative) imports should NOT be counted."""
        imports = [
            Import(module="os", names=["path"], is_from=True),
            Import(module="sys", names=[], is_from=False),
            Import(module="pathlib", names=["Path"], is_from=True),
            Import(module="typing", names=["Dict"], is_from=True),
            Import(module="json", names=[], is_from=False),
            Import(module="dataclasses", names=["dataclass"], is_from=True),
            Import(module="collections", names=["defaultdict"], is_from=True),
            Import(module="enum", names=["Enum"], is_from=True),
            Import(module="functools", names=["lru_cache"], is_from=True),
            Import(module="re", names=[], is_from=False),
        ]
        parse_result = create_mock_parse_result(
            file_path="test.py", file_lines=200, imports=imports
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        coupling_issues = [i for i in result.issues if i.category == "high_coupling"]
        assert len(coupling_issues) == 0

    def test_exactly_8_internal_imports_no_issue(self, mock_config, symbol_scorer):
        """Exactly 8 internal imports should NOT be flagged."""
        imports = [
            Import(module=f".module{i}", names=[f"Class{i}"], is_from=True)
            for i in range(8)
        ]
        parse_result = create_mock_parse_result(
            file_path="test.py", file_lines=200, imports=imports
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        coupling_issues = [i for i in result.issues if i.category == "high_coupling"]
        assert len(coupling_issues) == 0


class TestLanguageAwareThresholds:
    """Test language-aware file size thresholds."""

    def test_python_file_medium_threshold(self, mock_config, symbol_scorer):
        """Python file at 900 lines should be flagged as medium_file (>800)."""
        parse_result = create_mock_parse_result(
            file_path="test.py", file_lines=900, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        medium_issues = [i for i in result.issues if i.category == "medium_file"]
        assert len(medium_issues) == 1
        assert medium_issues[0].severity == DebtSeverity.MEDIUM

    def test_java_file_at_900_no_issue(self, mock_config, symbol_scorer):
        """Java file at 900 lines should NOT be flagged (verbose lang, medium=1500)."""
        parse_result = create_mock_parse_result(
            file_path="Test.java", file_lines=900, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        size_issues = [
            i for i in result.issues
            if i.category in ("medium_file", "large_file", "super_large_file")
        ]
        assert len(size_issues) == 0

    def test_php_file_uses_verbose_thresholds(self, mock_config, symbol_scorer):
        """PHP file at 1600 lines should be flagged as medium_file (verbose: >1500 medium)."""
        parse_result = create_mock_parse_result(
            file_path="test.php", file_lines=1600, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        medium_issues = [i for i in result.issues if i.category == "medium_file"]
        assert len(medium_issues) == 1
        assert medium_issues[0].severity == DebtSeverity.MEDIUM

    def test_typescript_uses_compact_thresholds(self, mock_config, symbol_scorer):
        """TypeScript file at 900 lines should be flagged as medium_file (compact: >800)."""
        parse_result = create_mock_parse_result(
            file_path="app.ts", file_lines=900, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        medium_issues = [i for i in result.issues if i.category == "medium_file"]
        assert len(medium_issues) == 1

    def test_python_large_threshold(self, mock_config, symbol_scorer):
        """Python file at 1600 lines should be flagged as large_file (compact: >1500)."""
        parse_result = create_mock_parse_result(
            file_path="big.py", file_lines=1600, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        large_issues = [i for i in result.issues if i.category == "large_file"]
        assert len(large_issues) == 1
        assert large_issues[0].severity == DebtSeverity.HIGH

    def test_python_critical_threshold(self, mock_config, symbol_scorer):
        """Python file at 2600 lines should be flagged as super_large_file (compact: >2500)."""
        parse_result = create_mock_parse_result(
            file_path="huge.py", file_lines=2600, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        critical_issues = [i for i in result.issues if i.category == "super_large_file"]
        assert len(critical_issues) == 1
        assert critical_issues[0].severity == DebtSeverity.CRITICAL

    def test_java_critical_threshold(self, mock_config, symbol_scorer):
        """Java file at 5100 lines should be flagged as super_large_file (verbose: >5000)."""
        parse_result = create_mock_parse_result(
            file_path="Huge.java", file_lines=5100, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        critical_issues = [i for i in result.issues if i.category == "super_large_file"]
        assert len(critical_issues) == 1
        assert critical_issues[0].severity == DebtSeverity.CRITICAL

    def test_go_uses_verbose_thresholds(self, mock_config, symbol_scorer):
        """Go file should use verbose thresholds."""
        parse_result = create_mock_parse_result(
            file_path="main.go", file_lines=900, symbol_count=10
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        size_issues = [
            i for i in result.issues
            if i.category in ("medium_file", "large_file", "super_large_file")
        ]
        assert len(size_issues) == 0


class TestGodClassWarningTier:
    """Test the new MEDIUM warning tier for God Class (>20 methods)."""

    def test_class_with_25_methods_medium_warning(self, mock_config, symbol_scorer):
        """Class with >20 but <=50 methods should be MEDIUM god_class_warning."""
        parse_result = create_mock_parse_result(
            file_lines=500, class_name="MediumClass", methods_per_class=25
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        god_issues = [
            i for i in result.issues
            if i.category in ("god_class", "god_class_warning")
        ]
        assert len(god_issues) == 1
        assert god_issues[0].severity == DebtSeverity.MEDIUM

    def test_class_with_20_methods_no_warning(self, mock_config, symbol_scorer):
        """Class with exactly 20 methods should NOT be flagged."""
        parse_result = create_mock_parse_result(
            file_lines=500, class_name="OkClass", methods_per_class=20
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        god_issues = [
            i for i in result.issues
            if i.category in ("god_class", "god_class_warning")
        ]
        assert len(god_issues) == 0

    def test_class_with_51_methods_critical(self, mock_config, symbol_scorer):
        """Class with >50 methods should still be CRITICAL god_class (not double-reported)."""
        parse_result = create_mock_parse_result(
            file_lines=1000, class_name="HugeClass", methods_per_class=51
        )
        detector = TechDebtDetector(mock_config)

        result = detector.analyze_file(parse_result, symbol_scorer)

        god_issues = [
            i for i in result.issues
            if i.category in ("god_class", "god_class_warning")
        ]
        assert len(god_issues) == 1
        assert god_issues[0].severity == DebtSeverity.CRITICAL
        assert god_issues[0].category == "god_class"
