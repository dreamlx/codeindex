"""BDD tests for technical debt detection using pytest-bdd."""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol
from codeindex.symbol_scorer import SymbolImportanceScorer
from codeindex.tech_debt import (
    DebtAnalysisResult,
    DebtIssue,
    DebtSeverity,
    TechDebtDetector,
    TechDebtReporter,
)
from codeindex.tech_debt_formatters import (
    ConsoleFormatter,
    JSONFormatter,
    MarkdownFormatter,
)

# Load all scenarios from the feature files
scenarios("features/tech_debt_detection.feature")
scenarios("features/symbol_overload_detection.feature")
scenarios("features/tech_debt_reporting.feature")


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
def report_critical_issue(request):
    """Check that a CRITICAL issue was reported."""
    # Handle both analysis_result and symbol_overload_result fixtures
    if "symbol_overload_result" in request.fixturenames:
        result = request.getfixturevalue("symbol_overload_result")
        issues = result["issues"]
    else:
        result = request.getfixturevalue("analysis_result")
        issues = result.issues

    critical_issues = [i for i in issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical_issues) >= 1


@then("it should report a HIGH issue")
def report_high_issue(analysis_result):
    """Check that a HIGH issue was reported."""
    high_issues = [i for i in analysis_result.issues if i.severity == DebtSeverity.HIGH]
    assert len(high_issues) >= 1


@then(parsers.parse('the issue category should be "{category}"'))
def issue_category(request, category):
    """Check that an issue with the specified category exists."""
    # Handle both analysis_result and symbol_overload_result fixtures
    if "symbol_overload_result" in request.fixturenames:
        result = request.getfixturevalue("symbol_overload_result")
        issues = result["issues"]
    else:
        result = request.getfixturevalue("analysis_result")
        issues = result.issues

    categories = [i.category for i in issues]
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


# Symbol Overload Detection steps


@given(parsers.parse("a PHP file with {count:d} symbols"), target_fixture="symbol_overload_data")
def php_file_with_symbols(count):
    """Create a PHP file with specified number of symbols."""
    from tests.conftest import create_mock_parse_result

    return {"parse_result": create_mock_parse_result(symbol_count=count)}


@when("I analyze symbol overload", target_fixture="symbol_overload_result")
def analyze_symbol_overload(symbol_overload_data, tech_debt_detector, symbol_scorer):
    """Analyze symbol overload."""
    parse_result = symbol_overload_data["parse_result"]
    issues, analysis = tech_debt_detector.analyze_symbol_overload(parse_result, symbol_scorer)
    return {"issues": issues, "analysis": analysis}


@then("no massive symbol count issues should be reported")
def no_massive_symbol_issues(symbol_overload_result):
    """Check that no massive symbol count issues were reported."""
    issues = symbol_overload_result["issues"]
    massive_issues = [i for i in issues if i.category == "massive_symbol_count"]
    assert len(massive_issues) == 0


@then(parsers.parse("the analysis should show {count:d} total symbols"))
def analysis_shows_total_symbols(symbol_overload_result, count):
    """Check that analysis shows correct total symbol count."""
    analysis = symbol_overload_result["analysis"]
    assert analysis.total_symbols == count


@then(parsers.parse("the metric value should be {value:d}"))
def metric_value_equals(symbol_overload_result, value):
    """Check that metric value matches expected."""
    issues = symbol_overload_result["issues"]
    assert any(i.metric_value == value for i in issues)


# Technical Debt Reporting steps


@given("a TechDebtReporter", target_fixture="reporter")
def tech_debt_reporter_fixture():
    """Create a TechDebtReporter."""
    return TechDebtReporter()


@given(
    parsers.parse('a file "{filename}" with {count:d} CRITICAL issue'),
    target_fixture="reporter",
)
@given(
    parsers.parse('a file "{filename}" with {count:d} CRITICAL issues'),
    target_fixture="reporter",
)
def file_with_critical_issues(reporter, filename, count):
    """Add a file with CRITICAL issues to reporter."""
    from pathlib import Path

    issues = [
        DebtIssue(
            severity=DebtSeverity.CRITICAL,
            category="test",
            file_path=Path(filename),
            metric_value=100,
            threshold=50,
            description=f"Critical issue {i+1}",
            suggestion="Fix it",
        )
        for i in range(count)
    ]
    reporter.add_file_result(
        file_path=Path(filename),
        debt_analysis=DebtAnalysisResult(
            issues=issues,
            quality_score=70.0,
            file_path=Path(filename),
            file_lines=100,
            total_symbols=10,
        ),
        symbol_analysis=None,
    )
    return reporter


@given(
    parsers.parse('a file "{filename}" with {count:d} HIGH issue'),
    target_fixture="reporter",
)
@given(
    parsers.parse('a file "{filename}" with {count:d} HIGH issues'),
    target_fixture="reporter",
)
def file_with_high_issues(reporter, filename, count):
    """Add a file with HIGH issues to reporter."""
    from pathlib import Path

    issues = [
        DebtIssue(
            severity=DebtSeverity.HIGH,
            category="test",
            file_path=Path(filename),
            metric_value=100,
            threshold=50,
            description=f"High issue {i+1}",
            suggestion="Fix it",
        )
        for i in range(count)
    ]
    reporter.add_file_result(
        file_path=Path(filename),
        debt_analysis=DebtAnalysisResult(
            issues=issues,
            quality_score=85.0,
            file_path=Path(filename),
            file_lines=100,
            total_symbols=10,
        ),
        symbol_analysis=None,
    )
    return reporter


@given(parsers.parse('a file "{filename}" with no issues'), target_fixture="reporter")
def file_with_no_issues(reporter, filename):
    """Add a file with no issues to reporter."""
    from pathlib import Path

    reporter.add_file_result(
        file_path=Path(filename),
        debt_analysis=DebtAnalysisResult(
            issues=[],
            quality_score=100.0,
            file_path=Path(filename),
            file_lines=100,
            total_symbols=10,
        ),
        symbol_analysis=None,
    )
    return reporter


@when("I generate a report", target_fixture="report")
def generate_report(reporter):
    """Generate report from reporter."""
    return reporter.generate_report()


@when("I format the report as console", target_fixture="formatted_output")
def format_as_console(report):
    """Format report as console output."""
    formatter = ConsoleFormatter()
    return formatter.format(report)


@when("I format the report as markdown", target_fixture="formatted_output")
def format_as_markdown(report):
    """Format report as markdown."""
    formatter = MarkdownFormatter()
    return formatter.format(report)


@when("I format the report as JSON", target_fixture="formatted_output")
def format_as_json(report):
    """Format report as JSON."""
    formatter = JSONFormatter()
    return formatter.format(report)


@then(parsers.parse("the report should show {count:d} files analyzed"))
def report_shows_files_analyzed(report, count):
    """Check files analyzed count."""
    assert report.total_files == count


@then(parsers.parse("the report should show {count:d} total issues"))
def report_shows_total_issues(report, count):
    """Check total issues count."""
    assert report.total_issues == count


@then(parsers.parse("the report should show {count:d} CRITICAL issues"))
def report_shows_critical_issues(report, count):
    """Check CRITICAL issues count."""
    assert report.critical_issues == count


@then(parsers.parse("the report should show {count:d} HIGH issues"))
def report_shows_high_issues(report, count):
    """Check HIGH issues count."""
    assert report.high_issues == count


@then(parsers.parse("the average quality score should be {score:f}"))
def average_quality_score_equals(report, score):
    """Check average quality score."""
    assert report.average_quality_score == score


@then(parsers.parse('the output should contain "{text}"'))
def output_contains(formatted_output, text):
    """Check that output contains text."""
    assert text in formatted_output


@then("the output should be valid JSON")
def output_is_valid_json(formatted_output):
    """Check that output is valid JSON."""
    import json

    json.loads(formatted_output)  # Should not raise


@then(parsers.parse('the JSON should contain "{key}": {value:d}'))
def json_contains_key_value(formatted_output, key, value):
    """Check that JSON contains key-value pair."""
    import json

    data = json.loads(formatted_output)
    assert data[key] == value
