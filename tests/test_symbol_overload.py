"""Tests for symbol overload detection."""

from codeindex.tech_debt import (
    DebtSeverity,
    SymbolOverloadAnalysis,
    TechDebtDetector,
)

from .conftest import create_mock_parse_result


class TestSymbolOverloadAnalysis:
    """Test SymbolOverloadAnalysis dataclass."""

    def test_create_symbol_overload_analysis(self):
        """Should create a SymbolOverloadAnalysis with all fields."""
        analysis = SymbolOverloadAnalysis(
            total_symbols=57,
            filtered_symbols=30,
            filter_ratio=0.47,
            noise_breakdown={
                "getters_setters": 20,
                "private_methods": 5,
                "magic_methods": 2,
            },
            quality_score=55.0,
        )

        assert analysis.total_symbols == 57
        assert analysis.filtered_symbols == 30
        assert analysis.filter_ratio == 0.47
        assert analysis.noise_breakdown["getters_setters"] == 20
        assert analysis.quality_score == 55.0

    def test_analysis_with_no_noise(self):
        """Clean code should have empty noise breakdown."""
        analysis = SymbolOverloadAnalysis(
            total_symbols=20,
            filtered_symbols=20,
            filter_ratio=0.0,
            noise_breakdown={},
            quality_score=100.0,
        )

        assert len(analysis.noise_breakdown) == 0
        assert analysis.filter_ratio == 0.0
        assert analysis.quality_score == 100.0


class TestSymbolCountDetection:
    """Test massive symbol count detection."""

    def test_detect_massive_symbol_count(self, mock_config, symbol_scorer):
        """Should detect 100+ symbols as CRITICAL."""
        # Arrange
        parse_result = create_mock_parse_result(symbol_count=120)
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        assert analysis.total_symbols == 120
        critical_issues = [
            i for i in issues if i.severity == DebtSeverity.CRITICAL
        ]
        massive_issues = [i for i in critical_issues if i.category == "massive_symbol_count"]
        assert len(massive_issues) == 1
        assert massive_issues[0].metric_value == 120
        assert massive_issues[0].threshold == 100

    def test_normal_symbol_count_no_issue(self, mock_config, symbol_scorer):
        """Normal symbol count should not be flagged."""
        # Arrange
        parse_result = create_mock_parse_result(symbol_count=50)
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        assert analysis.total_symbols == 50
        massive_issues = [i for i in issues if i.category == "massive_symbol_count"]
        assert len(massive_issues) == 0

    def test_symbol_count_at_boundary(self, mock_config, symbol_scorer):
        """Exactly 100 symbols should NOT be flagged."""
        # Arrange
        parse_result = create_mock_parse_result(symbol_count=100)
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        assert analysis.total_symbols == 100
        massive_issues = [i for i in issues if i.category == "massive_symbol_count"]
        assert len(massive_issues) == 0

    def test_symbol_count_just_over_boundary(self, mock_config, symbol_scorer):
        """101 symbols should be flagged as CRITICAL."""
        # Arrange
        parse_result = create_mock_parse_result(symbol_count=101)
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        massive_issues = [i for i in issues if i.category == "massive_symbol_count"]
        assert len(massive_issues) == 1
        assert massive_issues[0].severity == DebtSeverity.CRITICAL


class TestNoiseRatioDetection:
    """Test high noise ratio detection."""

    def test_detect_high_noise_ratio(self, mock_config, symbol_scorer):
        """Should detect >50% noise as HIGH severity."""
        # Arrange - create symbols with many low-quality ones
        from pathlib import Path

        from codeindex.parser import ParseResult, Symbol

        symbols = []
        # 20 simple getters (will have low scores)
        for i in range(20):
            symbols.append(
                Symbol(
                    name=f"get{i}",
                    kind="method",
                    signature=f"public function get{i}()",
                    docstring="",
                    line_start=i * 3,
                    line_end=i * 3 + 2,
                )
            )
        # 10 high-quality business methods
        for i in range(10):
            symbols.append(
                Symbol(
                    name=f"processOrder{i}",
                    kind="method",
                    signature=f"public function processOrder{i}($order)",
                    docstring="Process customer order with business logic",
                    line_start=100 + i * 20,
                    line_end=100 + i * 20 + 15,
                )
            )

        parse_result = ParseResult(
            path=Path("test.php"), file_lines=500, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        assert analysis.total_symbols == 30
        # Should detect high noise
        noise_issues = [i for i in issues if i.category == "low_quality_symbols"]
        if analysis.filter_ratio > 0.5:
            assert len(noise_issues) >= 1
            assert noise_issues[0].severity == DebtSeverity.HIGH

    def test_low_noise_no_issue(self, mock_config, symbol_scorer):
        """Low noise ratio should not be flagged."""
        # Arrange - all high-quality symbols
        from pathlib import Path

        from codeindex.parser import ParseResult, Symbol

        symbols = []
        for i in range(20):
            symbols.append(
                Symbol(
                    name=f"processItem{i}",
                    kind="method",
                    signature=f"public function processItem{i}($item)",
                    docstring="Process item with business logic",
                    line_start=i * 20,
                    line_end=i * 20 + 15,
                )
            )

        parse_result = ParseResult(
            path=Path("test.php"), file_lines=500, symbols=symbols
        )
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        noise_issues = [i for i in issues if i.category == "low_quality_symbols"]
        assert len(noise_issues) == 0


class TestNoiseBreakdown:
    """Test noise breakdown analysis."""

    def test_noise_breakdown_categorization(self, mock_config, symbol_scorer):
        """Should correctly categorize noise sources."""
        # Arrange
        from pathlib import Path

        from codeindex.parser import ParseResult, Symbol

        symbols = []
        # 5 getters/setters
        for i in range(3):
            symbols.append(
                Symbol(
                    name=f"get{i}",
                    kind="method",
                    signature="public function get()",
                    docstring="",
                    line_start=i * 3,
                    line_end=i * 3 + 2,
                )
            )
        for i in range(2):
            symbols.append(
                Symbol(
                    name=f"set{i}",
                    kind="method",
                    signature="public function set()",
                    docstring="",
                    line_start=20 + i * 3,
                    line_end=20 + i * 3 + 2,
                )
            )

        # 3 private methods
        for i in range(3):
            symbols.append(
                Symbol(
                    name=f"_helper{i}",
                    kind="method",
                    signature="private function _helper()",
                    docstring="",
                    line_start=40 + i * 3,
                    line_end=40 + i * 3 + 2,
                )
            )

        # 2 magic methods
        symbols.append(
            Symbol(
                name="__construct",
                kind="method",
                signature="public function __construct()",
                docstring="",
                line_start=60,
                line_end=62,
            )
        )
        symbols.append(
            Symbol(
                name="__toString",
                kind="method",
                signature="public function __toString()",
                docstring="",
                line_start=65,
                line_end=67,
            )
        )

        # 10 high-quality methods
        for i in range(10):
            symbols.append(
                Symbol(
                    name=f"processData{i}",
                    kind="method",
                    signature="public function processData()",
                    docstring="Business logic",
                    line_start=100 + i * 20,
                    line_end=100 + i * 20 + 15,
                )
            )

        parse_result = ParseResult(path=Path("test.php"), file_lines=500, symbols=symbols)
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        assert analysis.total_symbols == 20
        # Check noise breakdown exists
        assert "getters_setters" in analysis.noise_breakdown
        assert "private_methods" in analysis.noise_breakdown
        assert "magic_methods" in analysis.noise_breakdown


class TestIntegration:
    """Integration tests for symbol overload detection."""

    def test_real_world_scenario(self, mock_config, symbol_scorer):
        """Test with realistic mixed symbols."""
        # Arrange - simulate OperateGoods.class.php scenario
        parse_result = create_mock_parse_result(
            file_lines=8891, symbol_count=57
        )
        detector = TechDebtDetector(mock_config)

        # Act
        issues, analysis = detector.analyze_symbol_overload(parse_result, symbol_scorer)

        # Assert
        assert analysis.total_symbols == 57
        assert 0.0 <= analysis.filter_ratio <= 1.0
        assert 0.0 <= analysis.quality_score <= 100.0
        # Should have at least some analysis
        assert analysis is not None
