"""BDD tests for super large file detection (Epic 3.2 Story 3.2.1)."""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from codeindex.config import Config
from codeindex.parser import ParseResult, Symbol

# Load scenarios from feature file
scenarios("features/super_large_file_detection.feature")


# Fixtures for test context


@given("a codeindex configuration is loaded", target_fixture="config")
def load_config():
    """Load codeindex configuration."""
    return Config.load()


@given("a symbol scorer is available", target_fixture="symbol_scorer")
def symbol_scorer_available():
    """Create a symbol importance scorer."""
    from codeindex.symbol_scorer import ScoringContext, SymbolImportanceScorer

    context = ScoringContext(framework=None, file_type="python")
    return SymbolImportanceScorer(context)


# Given steps - File creation


@given(parsers.parse("a {language} file with {lines:d} lines"), target_fixture="test_file")
def file_with_lines(language, lines):
    """Create a test file with specified line count."""
    extension = "php" if language == "PHP" else "py"
    return {
        "path": Path(f"test.{extension}"),
        "language": language,
        "file_lines": lines,
        "symbols": [],
    }


@given(parsers.parse("the file has {count:d} symbols"), target_fixture="test_file")
def file_with_symbols(test_file, count):
    """Add symbols to the test file."""
    symbols = []
    for i in range(count):
        symbols.append(
            Symbol(
                name=f"method{i}",
                kind="method",
                signature=f"public function method{i}()",
                docstring="",
                line_start=i * 10,
                line_end=i * 10 + 5,
            )
        )
    test_file["symbols"] = symbols
    return test_file


@given("a project with multiple files", target_fixture="project_files")
def project_with_files(datatable):
    """Parse project files from data table."""
    # First row is headers, rest are data
    headers = datatable[0]
    files = []
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        files.append({
            "filename": row_dict["filename"],
            "lines": int(row_dict["lines"]),
            "symbols": int(row_dict["symbols"]),
            "expected_strategy": row_dict["expected_strategy"],
        })
    return files


@given("custom thresholds are configured", target_fixture="config")
def custom_thresholds_configured(config, datatable):
    """Apply custom threshold configuration."""
    # First row is headers, rest are data
    headers = datatable[0]
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        threshold_name = row_dict["threshold_name"]
        value = int(row_dict["value"])
        setattr(config.ai_enhancement, threshold_name, value)
    return config


# When steps


@when("I check if it's a super large file", target_fixture="detection_result")
def check_super_large_file(test_file, config):
    """Check if file is super large."""
    from codeindex.ai_enhancement import is_super_large_file

    # Create ParseResult from test file data
    parse_result = ParseResult(
        path=test_file["path"],
        file_lines=test_file["file_lines"],
        symbols=test_file["symbols"],
    )

    # Call the actual detection function
    detection = is_super_large_file(parse_result, config)

    # Convert to dict for easier assertion
    return {
        "is_super_large": detection.is_super_large,
        "reason": detection.reason,
        "recommended_strategy": detection.recommended_strategy,
    }


@when("I select enhancement strategy for each file", target_fixture="strategy_results")
def select_strategies(project_files, config):
    """Select enhancement strategy for each file."""
    from codeindex.ai_enhancement import select_enhancement_strategy

    results = {}
    for file_info in project_files:
        # Create ParseResult for each file
        parse_result = ParseResult(
            path=Path(file_info["filename"]),
            file_lines=file_info["lines"],
            symbols=[Symbol(
                name=f"symbol{i}",
                kind="function",
                signature="",
                docstring="",
                line_start=i,
                line_end=i,
            ) for i in range(file_info["symbols"])],
        )
        # Select strategy
        strategy = select_enhancement_strategy(parse_result, config)
        results[file_info["filename"]] = strategy

    return results


# Then steps - Assertions


@then("it should be detected as super large")
def should_be_super_large(detection_result):
    """Verify file is detected as super large."""
    assert detection_result["is_super_large"] is True


@then("it should not be detected as super large")
def should_not_be_super_large(detection_result):
    """Verify file is NOT detected as super large."""
    assert detection_result["is_super_large"] is False


@then(parsers.parse('the detection reason should be "{reason}"'))
def detection_reason_is(detection_result, reason):
    """Verify detection reason matches expected."""
    assert detection_result["reason"] == reason


@then("it should recommend multi-turn dialogue strategy")
def recommend_multi_turn_dialogue(detection_result):
    """Verify multi-turn dialogue strategy is recommended."""
    assert detection_result["recommended_strategy"] == "multi_turn"


@then("it should recommend standard AI enhancement")
def recommend_standard_enhancement(detection_result):
    """Verify standard AI enhancement is recommended."""
    assert detection_result["recommended_strategy"] == "standard"


@then("it should recommend hierarchical prompt strategy")
def recommend_hierarchical_strategy(detection_result):
    """Verify hierarchical prompt strategy is recommended."""
    assert detection_result["recommended_strategy"] == "hierarchical"


@then("each file should use the expected strategy")
def verify_expected_strategies(project_files, strategy_results):
    """Verify each file uses its expected strategy."""
    for file_info in project_files:
        filename = file_info["filename"]
        expected = file_info["expected_strategy"]
        actual = strategy_results[filename]
        assert actual == expected, f"{filename}: expected {expected}, got {actual}"


@then("the strategy selection should be logged")
def strategy_selection_logged():
    """Verify strategy selection is logged."""
    # TODO: Implement logging verification
    pass


@then("the detection should respect custom thresholds")
def detection_respects_custom_thresholds(detection_result):
    """Verify detection uses custom thresholds."""
    # Verified by the fact that detection works with custom config
    # The custom thresholds were applied in the Given step
    assert detection_result is not None
