"""BDD tests for technical debt detection using pytest-bdd."""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol
from codeindex.symbol_scorer import SymbolImportanceScorer
from codeindex.tech_debt import DebtSeverity, TechDebtDetector

# Load all scenarios from the feature file
scenarios("features/tech_debt_detection.feature")


# Background steps


@given("a TechDebtDetector with default configuration", target_fixture="tech_debt_detector")
def tech_debt_detector_fixture():
    """Create a TechDebtDetector with default configuration."""
    config = Config.load()
    return TechDebtDetector(config)


@given("a SymbolImportanceScorer", target_fixture="symbol_scorer")
def symbol_scorer_fixture():
    """Create a SymbolImportanceScorer."""
    config = Config.load()
    return SymbolImportanceScorer(config)


# Given steps


@given(parsers.parse("a {language:w} file with {lines:d} lines"), target_fixture="file_data")
def file_with_lines(lines, language):
    """Create a file with specified number of lines."""
    extension = "py" if language == "Python" else "php"
    return {"path": Path(f"test.{extension}"), "file_lines": lines, "symbols": []}


@given(parsers.parse("{count:d} well-structured symbols"), target_fixture="file_data")
def well_structured_symbols(file_data, count):
    """Add well-structured symbols to the file."""
    symbols = []
    for i in range(count):
        symbols.append(
            Symbol(
                name=f"function{i}",
                kind="function",
                signature=f"def function{i}():",
                docstring="A well-documented function",
                line_start=i * 20,
                line_end=i * 20 + 15,
            )
        )
    file_data["symbols"] = symbols
    return file_data


@given(parsers.parse("{count:d} symbols"), target_fixture="file_data")
def symbols(file_data, count):
    """Add symbols to the file."""
    symbols = []
    for i in range(count):
        symbols.append(
            Symbol(
                name=f"function{i}",
                kind="function",
                signature=f"function function{i}()",
                docstring="",
                line_start=i * 20,
                line_end=i * 20 + 15,
            )
        )
    file_data["symbols"] = symbols
    return file_data


@given(
    parsers.parse('a class "{class_name}" with {method_count:d} methods'),
    target_fixture="file_data",
)
def class_with_methods(file_data, class_name, method_count):
    """Add a class with specified number of methods."""
    symbols = []
    for i in range(method_count):
        symbols.append(
            Symbol(
                name=f"{class_name}::method{i}",
                kind="method",
                signature=f"public function method{i}()",
                docstring="",
                line_start=i * 10,
                line_end=i * 10 + 5,
            )
        )
    file_data["symbols"] = symbols
    return file_data


# When steps


@when("I analyze technical debt", target_fixture="analysis_result")
def analyze_debt(file_data, tech_debt_detector, symbol_scorer):
    """Analyze the file for technical debt."""
    parse_result = ParseResult(
        path=file_data["path"],
        file_lines=file_data["file_lines"],
        symbols=file_data["symbols"],
    )
    result = tech_debt_detector.analyze_file(parse_result, symbol_scorer)
    return result


# Then steps


@then("no CRITICAL issues should be reported")
def no_critical_issues(analysis_result):
    """Check that no CRITICAL issues were reported."""
    critical_issues = [i for i in analysis_result.issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical_issues) == 0


@then("no HIGH issues should be reported")
def no_high_issues(analysis_result):
    """Check that no HIGH issues were reported."""
    high_issues = [i for i in analysis_result.issues if i.severity == DebtSeverity.HIGH]
    assert len(high_issues) == 0


@then("the quality score should be above 80")
def quality_score_above_80(analysis_result):
    """Check that quality score is above 80."""
    assert analysis_result.quality_score > 80


@then("it should report a CRITICAL issue")
def report_critical_issue(analysis_result):
    """Check that a CRITICAL issue was reported."""
    critical_issues = [i for i in analysis_result.issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical_issues) >= 1


@then("it should report a HIGH issue")
def report_high_issue(analysis_result):
    """Check that a HIGH issue was reported."""
    high_issues = [i for i in analysis_result.issues if i.severity == DebtSeverity.HIGH]
    assert len(high_issues) >= 1


@then(parsers.parse('the issue category should be "{category}"'))
def issue_category(analysis_result, category):
    """Check that an issue with the specified category exists."""
    categories = [i.category for i in analysis_result.issues]
    assert category in categories


@then(parsers.parse('the issue description should include "{text}"'))
def issue_description_includes(analysis_result, text):
    """Check that issue description includes specified text."""
    descriptions = [i.description for i in analysis_result.issues]
    assert any(text in desc for desc in descriptions)


@then(parsers.parse('the issue description should mention "{text}"'))
def issue_description_mentions(analysis_result, text):
    """Check that issue description mentions specified text."""
    descriptions = [i.description for i in analysis_result.issues]
    assert any(text in desc for desc in descriptions)


@then("the suggestion should recommend splitting the file")
def suggestion_split_file(analysis_result):
    """Check that suggestion recommends splitting."""
    suggestions = [i.suggestion for i in analysis_result.issues]
    assert any("split" in sugg.lower() for sugg in suggestions)


@then("the suggestion should recommend extracting smaller classes")
def suggestion_extract_classes(analysis_result):
    """Check that suggestion recommends extracting classes."""
    suggestions = [i.suggestion for i in analysis_result.issues]
    assert any("extract" in sugg.lower() for sugg in suggestions)


@then("the quality score should be below 80")
def quality_score_below_80(analysis_result):
    """Check that quality score is below 80."""
    assert analysis_result.quality_score < 80


@then("the quality score should be below 50")
def quality_score_below_50(analysis_result):
    """Check that quality score is below 50."""
    assert analysis_result.quality_score < 50


@then("the quality score should be between 80 and 90")
def quality_score_between_80_and_90(analysis_result):
    """Check that quality score is between 80 and 90."""
    assert 80 <= analysis_result.quality_score <= 90


@then(parsers.parse("it should report {count:d} or more issues"))
def report_multiple_issues(analysis_result, count):
    """Check that multiple issues were reported."""
    assert len(analysis_result.issues) >= count


@then("at least one should be CRITICAL for file size")
def critical_for_file_size(analysis_result):
    """Check for CRITICAL file size issue."""
    critical_file_issues = [
        i
        for i in analysis_result.issues
        if i.severity == DebtSeverity.CRITICAL and "file" in i.category
    ]
    assert len(critical_file_issues) >= 1


@then("at least one should be CRITICAL for God Class")
def critical_for_god_class(analysis_result):
    """Check for CRITICAL God Class issue."""
    critical_god_class = [
        i
        for i in analysis_result.issues
        if i.severity == DebtSeverity.CRITICAL and i.category == "god_class"
    ]
    assert len(critical_god_class) >= 1
