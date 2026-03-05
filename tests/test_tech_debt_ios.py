"""Tests for iOS-specific technical debt detection (Story 2.4).

This test file validates iOS/Swift-specific tech-debt rules:
- Massive View Controller detection (>500 lines or >20 methods)
- Swift file size thresholds (compact language: 800/1500/2500)
- Integration with existing tech-debt detection

Epic: #23
Story: 2.4
"""

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol
from codeindex.symbol_scorer import ScoringContext, SymbolImportanceScorer
from codeindex.tech_debt import DebtSeverity, TechDebtDetector


class TestMassiveViewControllerDetection:
    """Test Massive View Controller anti-pattern detection."""

    def test_detect_massive_view_controller_by_line_count(self, tmp_path):
        """Should detect ViewController with >500 lines as CRITICAL."""
        swift_file = tmp_path / "LargeViewController.swift"
        swift_file.write_text("class LargeViewController: UIViewController {}")

        # Create class symbol with 600 lines
        symbols = [
            Symbol(
                name="LargeViewController",
                kind="class",
                signature="class LargeViewController: UIViewController",
                docstring="",
                line_start=1,
                line_end=600,
            )
        ]

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=650,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should have massive_view_controller issue
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) == 1
        assert mvc_issues[0].severity == DebtSeverity.CRITICAL
        assert mvc_issues[0].metric_value == 600
        assert mvc_issues[0].threshold == 500
        assert "LargeViewController" in mvc_issues[0].description
        assert "600 lines" in mvc_issues[0].description

    def test_detect_massive_view_controller_by_method_count(self, tmp_path):
        """Should detect ViewController with >20 methods as CRITICAL."""
        swift_file = tmp_path / "ComplexViewController.swift"
        swift_file.write_text("class ComplexViewController: UIViewController {}")

        # Create class with 25 methods
        symbols = [
            Symbol(
                name="ComplexViewController",
                kind="class",
                signature="class ComplexViewController: UIViewController",
                docstring="",
                line_start=1,
                line_end=300,
            )
        ]

        # Add 25 methods
        for i in range(25):
            symbols.append(
                Symbol(
                    name=f"ComplexViewController.method{i}",
                    kind="method",
                    signature=f"func method{i}()",
                    docstring="",
                    line_start=10 + i * 10,
                    line_end=18 + i * 10,
                )
            )

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=300,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should have massive_view_controller issue
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) == 1
        assert mvc_issues[0].severity == DebtSeverity.CRITICAL
        assert mvc_issues[0].metric_value == 25
        assert mvc_issues[0].threshold == 20
        assert "ComplexViewController" in mvc_issues[0].description
        assert "25 methods" in mvc_issues[0].description

    def test_detect_massive_view_controller_both_conditions(self, tmp_path):
        """Should detect ViewController that violates both conditions."""
        swift_file = tmp_path / "MassiveViewController.swift"
        swift_file.write_text("class MassiveViewController: UIViewController {}")

        # Create class with 700 lines AND 30 methods
        symbols = [
            Symbol(
                name="MassiveViewController",
                kind="class",
                signature="class MassiveViewController: UIViewController",
                docstring="",
                line_start=1,
                line_end=700,
            )
        ]

        # Add 30 methods
        for i in range(30):
            symbols.append(
                Symbol(
                    name=f"MassiveViewController.method{i}",
                    kind="method",
                    signature=f"func method{i}()",
                    docstring="",
                    line_start=10 + i * 20,
                    line_end=28 + i * 20,
                )
            )

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=750,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should have 2 issues (one for line count, one for method count)
        # OR 1 issue mentioning both violations
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) >= 1
        # At least one should mention the violation
        descriptions = " ".join([i.description for i in mvc_issues])
        assert "MassiveViewController" in descriptions

    def test_normal_view_controller_no_issue(self, tmp_path):
        """Should not flag small ViewController."""
        swift_file = tmp_path / "NormalViewController.swift"
        swift_file.write_text("class NormalViewController: UIViewController {}")

        # Create class with 300 lines and 10 methods
        symbols = [
            Symbol(
                name="NormalViewController",
                kind="class",
                signature="class NormalViewController: UIViewController",
                docstring="",
                line_start=1,
                line_end=300,
            )
        ]

        # Add 10 methods (below threshold)
        for i in range(10):
            symbols.append(
                Symbol(
                    name=f"NormalViewController.method{i}",
                    kind="method",
                    signature=f"func method{i}()",
                    docstring="",
                    line_start=10 + i * 20,
                    line_end=28 + i * 20,
                )
            )

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=300,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should have NO massive_view_controller issue
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) == 0

    def test_detect_nsview_controller(self, tmp_path):
        """Should detect NSViewController (macOS) as well."""
        swift_file = tmp_path / "LargeNSViewController.swift"
        swift_file.write_text("class LargeNSViewController: NSViewController {}")

        symbols = [
            Symbol(
                name="LargeNSViewController",
                kind="class",
                signature="class LargeNSViewController: NSViewController",
                docstring="",
                line_start=1,
                line_end=600,
            )
        ]

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=650,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should detect NSViewController too
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) == 1
        assert "LargeNSViewController" in mvc_issues[0].description

    def test_non_view_controller_not_detected(self, tmp_path):
        """Should not flag large non-ViewController classes."""
        swift_file = tmp_path / "LargeModel.swift"
        swift_file.write_text("class LargeModel {}")

        # Large class but NOT a ViewController
        symbols = [
            Symbol(
                name="LargeModel",
                kind="class",
                signature="class LargeModel",
                docstring="",
                line_start=1,
                line_end=600,
            )
        ]

        # Add 25 methods
        for i in range(25):
            symbols.append(
                Symbol(
                    name=f"LargeModel.method{i}",
                    kind="method",
                    signature=f"func method{i}()",
                    docstring="",
                    line_start=10 + i * 20,
                    line_end=28 + i * 20,
                )
            )

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=650,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should NOT have massive_view_controller issue
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) == 0

        # But should have god_class issue (>20 methods)
        god_class_issues = [
            i for i in result.issues
            if i.category in ("god_class", "god_class_warning")
        ]
        assert len(god_class_issues) > 0

    def test_non_swift_file_not_checked(self, tmp_path):
        """Should not check massive_view_controller for non-Swift files."""
        python_file = tmp_path / "large_view.py"
        python_file.write_text("class LargeViewController: pass")

        symbols = [
            Symbol(
                name="LargeViewController",
                kind="class",
                signature="class LargeViewController",
                docstring="",
                line_start=1,
                line_end=600,
            )
        ]

        parse_result = ParseResult(
            path=python_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=650,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="python"))

        result = detector.analyze_file(parse_result, scorer)

        # Should NOT have massive_view_controller issue (not Swift)
        mvc_issues = [i for i in result.issues if i.category == "massive_view_controller"]
        assert len(mvc_issues) == 0


class TestSwiftFileSizeThresholds:
    """Test Swift files use compact language thresholds."""

    def test_swift_uses_compact_thresholds(self, tmp_path):
        """Swift files should use compact thresholds (800/1500/2500)."""
        swift_file = tmp_path / "MediumFile.swift"
        swift_file.write_text("// Swift code")

        # 900 lines should trigger MEDIUM for compact languages
        parse_result = ParseResult(
            path=swift_file,
            symbols=[],
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=900,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should have medium_file issue (900 > 800 for compact)
        size_issues = [
            i for i in result.issues
            if i.category in ("medium_file", "large_file", "super_large_file")
        ]
        assert len(size_issues) == 1
        assert size_issues[0].category == "medium_file"
        assert size_issues[0].threshold == 800

    def test_swift_large_file_threshold(self, tmp_path):
        """Swift file >1500 lines should be HIGH (large_file)."""
        swift_file = tmp_path / "LargeFile.swift"
        swift_file.write_text("// Swift code")

        parse_result = ParseResult(
            path=swift_file,
            symbols=[],
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=1800,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        size_issues = [
            i for i in result.issues
            if i.category in ("medium_file", "large_file", "super_large_file")
        ]
        assert len(size_issues) == 1
        assert size_issues[0].category == "large_file"
        assert size_issues[0].threshold == 1500

    def test_swift_critical_file_threshold(self, tmp_path):
        """Swift file >2500 lines should be CRITICAL (super_large_file)."""
        swift_file = tmp_path / "MassiveFile.swift"
        swift_file.write_text("// Swift code")

        parse_result = ParseResult(
            path=swift_file,
            symbols=[],
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=3000,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        size_issues = [
            i for i in result.issues
            if i.category in ("medium_file", "large_file", "super_large_file")
        ]
        assert len(size_issues) == 1
        assert size_issues[0].category == "super_large_file"
        assert size_issues[0].threshold == 2500


class TestSwiftIntegrationWithExistingRules:
    """Test Swift files work with all existing tech-debt rules."""

    def test_swift_god_class_detection(self, tmp_path):
        """Swift classes should trigger God Class detection."""
        swift_file = tmp_path / "GodClass.swift"
        swift_file.write_text("class GodClass {}")

        # Create class with 60 methods
        symbols = [
            Symbol(
                name="GodClass",
                kind="class",
                signature="class GodClass",
                docstring="",
                line_start=1,
                line_end=500,
            )
        ]

        for i in range(60):
            symbols.append(
                Symbol(
                    name=f"GodClass.method{i}",
                    kind="method",
                    signature=f"func method{i}()",
                    docstring="",
                    line_start=10 + i * 8,
                    line_end=17 + i * 8,
                )
            )

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=500,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should detect god_class (>50 methods CRITICAL)
        god_class_issues = [i for i in result.issues if i.category == "god_class"]
        assert len(god_class_issues) == 1
        assert god_class_issues[0].severity == DebtSeverity.CRITICAL

    def test_swift_long_method_detection(self, tmp_path):
        """Swift methods should trigger long method detection."""
        swift_file = tmp_path / "LongMethod.swift"
        swift_file.write_text("class MyClass {}")

        symbols = [
            Symbol(
                name="MyClass.longMethod",
                kind="method",
                signature="func longMethod()",
                docstring="",
                line_start=10,
                line_end=200,  # 191 lines
            )
        ]

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=220,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should detect long_method (>150 lines HIGH)
        long_method_issues = [i for i in result.issues if i.category == "long_method"]
        assert len(long_method_issues) == 1
        assert long_method_issues[0].severity == DebtSeverity.HIGH
        assert long_method_issues[0].metric_value == 191

    def test_swift_too_many_functions(self, tmp_path):
        """Swift files should trigger too_many_functions detection."""
        swift_file = tmp_path / "UtilityFunctions.swift"
        swift_file.write_text("// Utility functions")

        # Create 20 top-level functions
        symbols = []
        for i in range(20):
            symbols.append(
                Symbol(
                    name=f"utilFunction{i}",
                    kind="function",
                    signature=f"func utilFunction{i}()",
                    docstring="",
                    line_start=10 + i * 10,
                    line_end=18 + i * 10,
                )
            )

        parse_result = ParseResult(
            path=swift_file,
            symbols=symbols,
            imports=[],
            calls=[],
            inheritances=[],
            file_lines=250,
        )

        config = Config(languages=["swift"])
        detector = TechDebtDetector(config)
        scorer = SymbolImportanceScorer(ScoringContext(file_type="swift"))

        result = detector.analyze_file(parse_result, scorer)

        # Should detect too_many_functions (>15 functions MEDIUM)
        func_issues = [i for i in result.issues if i.category == "too_many_functions"]
        assert len(func_issues) == 1
        assert func_issues[0].severity == DebtSeverity.MEDIUM
