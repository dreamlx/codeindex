# Epic 3: AI Enhancement Optimization

## 📋 Epic Overview

### Epic Statement
As a **codeindex user**, I want **AI enhancement to work reliably on all files including super large ones**, so that **I can generate high-quality README_AI.md for my entire codebase and identify technical debt**.

### Business Value
- **Current Pain**: 50% AI enhancement failure rate on large files
- **Target Outcome**: 90%+ success rate, high-quality READMEs for all files
- **Long-term Value**: Technical debt visibility → Guided refactoring → Better codebase

### Success Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| AI Success Rate | 50% | 90% | % of directories with successful AI enhancement |
| README Quality | 6/10 | 9/10 | User satisfaction survey |
| Large File Handling | 10% | 90% | Success rate for files >5000 lines |
| Tech Debt Visibility | 0% | 100% | % of users who get debt report |

### Scope
**In Scope**:
- ✅ Technical debt detection and reporting
- ✅ Symbol overload analysis
- ✅ Multi-turn dialogue for super large files
- ✅ Hierarchical prompt formatting
- ✅ Smart symbol filtering

**Out of Scope**:
- ❌ Knowledge graph construction (separate project)
- ❌ Real-time code analysis
- ❌ IDE integration

---

## 🎯 Epic Breakdown

### Epic 3.1: Technical Debt Detection System 🔥🔥🔥🔥🔥
**Duration**: 2 weeks
**Priority**: CRITICAL
**Dependencies**: None

### Epic 3.2: Multi-turn Dialogue Enhancement 🔥🔥🔥🔥🔥
**Duration**: 2 weeks
**Priority**: CRITICAL
**Dependencies**: Epic 3.1 (for detecting super large files)

### Epic 3.3: Hierarchical Prompt Optimization 🔥🔥🔥
**Duration**: 1 week
**Priority**: HIGH
**Dependencies**: Epic 3.1, Epic 3.2

---

## 📖 Epic 3.1: Technical Debt Detection System

### Epic Goal
Automatically detect and report technical debt (large files, God Classes, symbol overload) to guide users in refactoring.

### User Stories

---

#### Story 3.1.1: File-level Debt Detection

**User Story**:
```
As a developer,
I want codeindex to detect super large files and God Classes,
So that I know which files need urgent refactoring.
```

**Acceptance Criteria** (BDD Format):

```gherkin
Feature: File-level Technical Debt Detection

  Scenario: Detect super large file (CRITICAL)
    Given a PHP file with 8891 lines
    When I run codeindex scan
    Then it should report a CRITICAL issue "super_large_file"
    And the issue description should include the line count
    And the suggestion should recommend splitting the file

  Scenario: Detect God Class (CRITICAL)
    Given a class with 57 methods
    When I run codeindex scan
    Then it should report a CRITICAL issue "god_class"
    And the suggestion should recommend extracting service classes

  Scenario: Detect large file (HIGH)
    Given a PHP file with 2500 lines
    When I run codeindex scan
    Then it should report a HIGH issue "large_file"
    And the suggestion should recommend refactoring

  Scenario: Normal file passes check
    Given a PHP file with 300 lines and 15 methods
    When I run codeindex scan
    Then no debt issues should be reported for size
```

**Test Cases** (TDD):

```python
# tests/test_tech_debt_detector.py

def test_detect_super_large_file():
    """Should detect files >5000 lines as CRITICAL"""
    # Arrange
    parse_result = create_mock_parse_result(file_lines=8891, symbols=57)
    detector = TechDebtDetector(config)

    # Act
    issues, _ = detector.analyze_file(parse_result, scorer)

    # Assert
    critical_issues = [i for i in issues if i.severity == DebtSeverity.CRITICAL]
    assert len(critical_issues) >= 1
    assert any(i.category == "super_large_file" for i in critical_issues)
    assert any(8891 in str(i.description) for i in issues)

def test_detect_god_class():
    """Should detect classes with >50 methods as CRITICAL"""
    # Arrange
    symbols = [create_mock_symbol(name=f"method{i}") for i in range(57)]
    parse_result = ParseResult(
        path=Path("test.php"),
        symbols=symbols,
        file_lines=8891
    )
    detector = TechDebtDetector(config)

    # Act
    issues, _ = detector.analyze_file(parse_result, scorer)

    # Assert
    god_class_issues = [i for i in issues if "god_class" in i.category]
    assert len(god_class_issues) >= 1
    assert god_class_issues[0].metric_value == 57

def test_normal_file_no_issues():
    """Normal files should pass without issues"""
    # Arrange
    symbols = [create_mock_symbol(name=f"method{i}") for i in range(15)]
    parse_result = ParseResult(
        path=Path("normal.php"),
        symbols=symbols,
        file_lines=300
    )
    detector = TechDebtDetector(config)

    # Act
    issues, _ = detector.analyze_file(parse_result, scorer)

    # Assert
    size_issues = [i for i in issues if "large" in i.category or "god_class" in i.category]
    assert len(size_issues) == 0
```

**Tasks**:
- [ ] Create `DebtSeverity` enum (0.5h)
- [ ] Create `DebtIssue` dataclass (0.5h)
- [ ] Implement `TechDebtDetector` class skeleton (1h)
- [ ] Implement super large file detection (2h)
- [ ] Implement God Class detection (2h)
- [ ] Implement large file detection (1h)
- [ ] Write unit tests (3h)
- [ ] Write BDD tests with pytest-bdd (2h)

**Estimate**: 12 hours (1.5 days)

---

#### Story 3.1.2: Symbol Overload Detection

**User Story**:
```
As a developer,
I want codeindex to detect when a file has too many symbols or high noise ratio,
So that I understand why symbols are being filtered and what quality issues exist.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: Symbol Overload Detection

  Scenario: Detect massive symbol count (CRITICAL)
    Given a class with 120 symbols
    When I analyze symbol overload
    Then it should report CRITICAL "massive_symbol_count"
    And the metric_value should be 120
    And threshold should be 100

  Scenario: Detect high noise ratio (HIGH)
    Given a class with 57 total symbols
    And only 30 high-quality symbols (47% noise)
    When I analyze symbol overload
    Then it should report HIGH "low_quality_symbols"
    And the filter_ratio should be approximately 0.47
    And it should include noise breakdown

  Scenario: Detect data class smell
    Given a class with 20 simple getters/setters
    And 10 business methods
    When I analyze symbol overload
    Then the noise_breakdown should show 20 getters_setters
    And the suggestion should mention "Data Class smell"

  Scenario: Good quality class
    Given a class with 20 symbols
    And 18 high-quality symbols (10% noise)
    When I analyze symbol overload
    Then no symbol overload issues should be reported
    And quality_score should be > 80
```

**Test Cases** (TDD):

```python
# tests/test_symbol_overload.py

def test_detect_massive_symbol_count():
    """Should detect 100+ symbols as CRITICAL"""
    # Arrange
    symbols = [create_mock_symbol(f"method{i}") for i in range(120)]
    parse_result = ParseResult(path=Path("test.php"), symbols=symbols, file_lines=10000)
    detector = TechDebtDetector(config)
    scorer = SymbolImportanceScorer()

    # Act
    issues, analysis = detector.analyze_symbol_overload(parse_result, scorer)

    # Assert
    assert analysis.total_symbols == 120
    massive_issues = [i for i in issues if i.category == "massive_symbol_count"]
    assert len(massive_issues) == 1
    assert massive_issues[0].severity == DebtSeverity.CRITICAL

def test_detect_high_noise_ratio():
    """Should detect >50% noise as HIGH debt"""
    # Arrange
    # Create 57 symbols: 27 low-quality (noise), 30 high-quality
    symbols = []

    # 20 simple getters (low quality)
    for i in range(20):
        symbols.append(create_simple_getter(f"getField{i}"))

    # 7 other low-quality
    for i in range(7):
        symbols.append(create_low_quality_method(f"helper{i}"))

    # 30 high-quality business methods
    for i in range(30):
        symbols.append(create_business_method(f"process{i}"))

    parse_result = ParseResult(path=Path("test.php"), symbols=symbols, file_lines=8891)
    detector = TechDebtDetector(config)
    scorer = SymbolImportanceScorer()

    # Act
    issues, analysis = detector.analyze_symbol_overload(parse_result, scorer)

    # Assert
    assert analysis.total_symbols == 57
    assert analysis.filtered_symbols == 30
    assert 0.45 < analysis.filter_ratio < 0.50  # ~47%

    noise_issues = [i for i in issues if "low_quality" in i.category]
    assert len(noise_issues) >= 1
    assert noise_issues[0].severity == DebtSeverity.HIGH

def test_noise_breakdown_analysis():
    """Should correctly categorize noise sources"""
    # Arrange
    symbols = []
    symbols.extend([create_simple_getter(f"get{i}") for i in range(15)])
    symbols.extend([create_simple_setter(f"set{i}") for i in range(5)])
    symbols.extend([create_private_method(f"_helper{i}") for i in range(3)])
    symbols.extend([create_magic_method("__construct")])
    symbols.extend([create_business_method(f"process{i}") for i in range(30)])

    parse_result = ParseResult(path=Path("test.php"), symbols=symbols, file_lines=2000)
    detector = TechDebtDetector(config)
    scorer = SymbolImportanceScorer()

    # Act
    _, analysis = detector.analyze_symbol_overload(parse_result, scorer)

    # Assert
    assert analysis.noise_breakdown["getters_setters"] == 20
    assert analysis.noise_breakdown["private_methods"] == 3
    assert analysis.noise_breakdown["magic_methods"] == 1

def test_quality_score_calculation():
    """Quality score should reflect code quality"""
    # Arrange
    detector = TechDebtDetector(config)

    # Test 1: High quality (90% retention, low noise)
    score1 = detector._calculate_quality_score(
        total=20,
        filtered=18,
        noise_breakdown={"getters_setters": 2}
    )
    assert score1 > 85

    # Test 2: Low quality (53% retention, high noise)
    score2 = detector._calculate_quality_score(
        total=57,
        filtered=30,
        noise_breakdown={"getters_setters": 20, "other_noise": 7}
    )
    assert 40 < score2 < 60

    # Test 3: Very low quality (many symbols, high noise)
    score3 = detector._calculate_quality_score(
        total=120,
        filtered=40,
        noise_breakdown={"getters_setters": 50}
    )
    assert score3 < 40
```

**Tasks**:
- [ ] Implement `SymbolOverloadAnalysis` dataclass (1h)
- [ ] Implement `analyze_symbol_overload()` method (4h)
- [ ] Implement `_analyze_noise_breakdown()` (2h)
- [ ] Implement `_calculate_quality_score()` (2h)
- [ ] Write unit tests for symbol overload (4h)
- [ ] Write BDD tests (2h)
- [ ] Add integration tests with real PHP files (2h)

**Estimate**: 17 hours (2 days)

---

#### Story 3.1.3: Technical Debt Report Generation

**User Story**:
```
As a developer,
I want a comprehensive technical debt report in Markdown format,
So that I can prioritize refactoring work and track improvement over time.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: Technical Debt Report Generation

  Scenario: Generate complete report
    Given a project with 119 files
    And 23 technical debt issues detected
    And 2 CRITICAL, 5 HIGH, 10 MEDIUM, 6 LOW issues
    When I run codeindex tech-debt
    Then a TECH_DEBT_REPORT.md file should be created
    And it should include Executive Summary
    And it should include Critical Issues section
    And it should include Refactoring Priority List
    And it should include Symbol Quality Analysis

  Scenario: Executive summary accuracy
    Given detected issues with severity breakdown
    When I generate the report
    Then the summary should show correct totals
    And files analyzed count should match
    And severity counts should be accurate

  Scenario: Refactoring priority list
    Given 3 files with critical issues
    And 5 files with high issues
    When I generate the report
    Then files should be ordered by severity score
    And each file should show issue count
    And top issues should be listed for each file

  Scenario: Actionable recommendations
    Given a file with God Class and high noise
    When I generate the report
    Then it should provide specific refactoring steps
    And it should show expected improvement metrics
    And it should reference design patterns
```

**Test Cases** (TDD):

```python
# tests/test_tech_debt_report.py

def test_generate_report_structure():
    """Report should have all required sections"""
    # Arrange
    issues = create_mock_issues(count=23)
    report = TechDebtReport(
        project_path=Path.cwd(),
        total_files=119,
        total_issues=23,
        issues_by_severity={
            DebtSeverity.CRITICAL: 2,
            DebtSeverity.HIGH: 5,
            DebtSeverity.MEDIUM: 10,
            DebtSeverity.LOW: 6,
        },
        issues=issues
    )

    # Act
    markdown = generate_markdown_report(report)

    # Assert
    assert "# Technical Debt Report" in markdown
    assert "## Executive Summary" in markdown
    assert "## 🚨 Critical Issues" in markdown
    assert "## 📋 Refactoring Priority List" in markdown
    assert "## 📊 Symbol Quality Analysis" in markdown
    assert "Total Files Analyzed: 119" in markdown
    assert "Total Issues Found: 23" in markdown

def test_executive_summary_accuracy():
    """Summary statistics should be accurate"""
    # Arrange
    issues = [
        create_mock_issue(severity=DebtSeverity.CRITICAL),
        create_mock_issue(severity=DebtSeverity.CRITICAL),
        create_mock_issue(severity=DebtSeverity.HIGH),
        create_mock_issue(severity=DebtSeverity.HIGH),
        create_mock_issue(severity=DebtSeverity.HIGH),
    ]
    report = TechDebtReport(
        project_path=Path.cwd(),
        total_files=50,
        total_issues=5,
        issues_by_severity={
            DebtSeverity.CRITICAL: 2,
            DebtSeverity.HIGH: 3,
            DebtSeverity.MEDIUM: 0,
            DebtSeverity.LOW: 0,
        },
        issues=issues
    )

    # Act
    markdown = generate_markdown_report(report)

    # Assert
    assert "🔴🔴 CRITICAL: 2" in markdown
    assert "🔴 HIGH: 3" in markdown

def test_refactoring_priority_list():
    """Files should be ordered by severity"""
    # Arrange
    file1 = Path("OperateGoods.class.php")
    file2 = Path("OrderController.class.php")

    issues = [
        create_mock_issue(severity=DebtSeverity.CRITICAL, file_path=file1),
        create_mock_issue(severity=DebtSeverity.CRITICAL, file_path=file1),
        create_mock_issue(severity=DebtSeverity.HIGH, file_path=file2),
    ]

    report = TechDebtReport(
        project_path=Path.cwd(),
        total_files=10,
        total_issues=3,
        issues_by_severity={
            DebtSeverity.CRITICAL: 2,
            DebtSeverity.HIGH: 1,
        },
        issues=issues
    )

    # Act
    candidates = report.get_refactoring_candidates()

    # Assert
    assert len(candidates) == 2
    assert candidates[0] == file1  # Should be first (2 critical issues)
    assert candidates[1] == file2

def test_save_report_to_file():
    """Report should be saved to specified path"""
    # Arrange
    report = create_mock_report()
    output_path = Path("/tmp/test_debt_report.md")

    # Act
    save_report(report, output_path)

    # Assert
    assert output_path.exists()
    content = output_path.read_text()
    assert "# Technical Debt Report" in content

    # Cleanup
    output_path.unlink()
```

**Tasks**:
- [ ] Implement `TechDebtReport` dataclass (1h)
- [ ] Implement `generate_markdown_report()` (4h)
- [ ] Implement executive summary section (1h)
- [ ] Implement critical issues section (2h)
- [ ] Implement refactoring priority list (2h)
- [ ] Implement symbol quality analysis section (2h)
- [ ] Implement `save_report()` (1h)
- [ ] Write unit tests (4h)
- [ ] Write BDD tests (2h)

**Estimate**: 19 hours (2.5 days)

---

#### Story 3.1.4: CLI Integration and User Experience

**User Story**:
```
As a developer,
I want seamless CLI integration for technical debt analysis,
So that I can easily run scans and get actionable reports.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: CLI Technical Debt Commands

  Scenario: Run standalone tech-debt command
    Given a project directory with 119 files
    When I run "codeindex tech-debt"
    Then it should scan all files
    And display a summary of issues
    And save TECH_DEBT_REPORT.md
    And print the report location

  Scenario: Integrate with scan-all command
    Given I run "codeindex scan-all"
    When scanning completes
    Then it should automatically detect tech debt
    And display debt warnings in the output
    And mention critical issues
    And suggest running tech-debt for details

  Scenario: Custom output path
    When I run "codeindex tech-debt --output custom-report.md"
    Then the report should be saved to custom-report.md

  Scenario: README warnings for problematic files
    Given a file with 57 symbols (47% noise)
    When I generate its README_AI.md
    Then the README should include a quality warning
    And show total vs filtered symbols
    And reference the tech debt report
```

**Test Cases** (TDD):

```python
# tests/test_cli_tech_debt.py

def test_tech_debt_command_basic():
    """Should run tech-debt command successfully"""
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(cli.main, ['tech-debt', '--root', 'tests/fixtures/php_project'])

    # Assert
    assert result.exit_code == 0
    assert "Analyzing Technical Debt" in result.output
    assert "Total Issues:" in result.output
    assert "TECH_DEBT_REPORT.md" in result.output

def test_tech_debt_command_with_output():
    """Should save report to custom path"""
    # Arrange
    runner = CliRunner()
    output_path = Path("/tmp/custom_debt.md")

    # Act
    result = runner.invoke(cli.main, [
        'tech-debt',
        '--root', 'tests/fixtures/php_project',
        '--output', str(output_path)
    ])

    # Assert
    assert result.exit_code == 0
    assert output_path.exists()

    # Cleanup
    output_path.unlink()

def test_scan_all_includes_debt_detection():
    """scan-all should include debt analysis"""
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(cli.main, ['scan-all', '--root', 'tests/fixtures/small_project'])

    # Assert
    assert result.exit_code == 0
    assert "Phase 3: Technical Debt Analysis" in result.output or \
           "Technical Debt" in result.output

def test_readme_includes_quality_warning():
    """README should show warnings for problematic files"""
    # Arrange
    config = Config.load()
    writer = SmartWriter(config.indexing)

    # Create a parse result with symbol overload
    symbols = [create_mock_symbol(f"method{i}") for i in range(57)]
    parse_result = ParseResult(
        path=Path("OperateGoods.class.php"),
        symbols=symbols,
        file_lines=8891
    )

    # Act
    output = writer.write_readme(
        dir_path=Path("/tmp/test"),
        parse_results=[parse_result],
        level="detailed"
    )

    # Assert
    content = output.path.read_text()
    assert "⚠️" in content or "Warning" in content
    assert "57 symbols" in content or "symbol" in content.lower()
```

**Tasks**:
- [ ] Implement `tech-debt` CLI command (3h)
- [ ] Add `--output` option (1h)
- [ ] Integrate debt detection into `scan-all` (2h)
- [ ] Add quality warnings to SmartWriter (3h)
- [ ] Update CLI help text and documentation (1h)
- [ ] Write CLI integration tests (3h)
- [ ] Write end-to-end tests (3h)
- [ ] Update user documentation (2h)

**Estimate**: 18 hours (2.5 days)

---

### Epic 3.1 Summary

**Total Stories**: 4
**Total Estimate**: 66 hours (8-9 days ≈ 2 weeks)

**Story Breakdown**:
- Story 3.1.1: File-level Detection (1.5 days)
- Story 3.1.2: Symbol Overload (2 days)
- Story 3.1.3: Report Generation (2.5 days)
- Story 3.1.4: CLI Integration (2.5 days)

**Deliverables**:
- ✅ `TechDebtDetector` class with comprehensive detection
- ✅ Technical debt report generation
- ✅ CLI commands (`codeindex tech-debt`)
- ✅ Integration with `scan-all`
- ✅ Quality warnings in README files
- ✅ 50+ unit tests
- ✅ 20+ BDD scenarios

---

## 📖 Epic 3.2: Multi-turn Dialogue Enhancement

### Epic Goal
Enable high-quality AI enhancement for super large files (>5000 lines) using multi-turn dialogue strategy.

### User Stories

---

#### Story 3.2.1: Super Large File Detection

**User Story**:
```
As a codeindex user,
I want the system to automatically detect super large files,
So that it can apply the appropriate AI enhancement strategy.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: Super Large File Detection

  Scenario: Detect super large file by line count
    Given a file with 8891 lines
    When I check if it's a super large file
    Then it should return True
    And recommend multi-turn dialogue

  Scenario: Detect super large file by symbol count
    Given a file with 120 symbols
    When I check if it's a super large file
    Then it should return True

  Scenario: Normal file detection
    Given a file with 1500 lines and 30 symbols
    When I check if it's a super large file
    Then it should return False
    And recommend standard AI enhancement

  Scenario: Auto-select enhancement strategy
    Given a mix of files: 3 normal, 1 large, 1 super large
    When I run scan-all
    Then normal files should use standard AI
    And large files should use hierarchical prompt
    And super large files should use multi-turn dialogue
```

**Test Cases** (TDD):

```python
# tests/test_super_large_detection.py

def test_detect_by_line_count():
    """Should detect >5000 lines as super large"""
    # Arrange
    parse_result = ParseResult(
        path=Path("huge.php"),
        file_lines=8891,
        symbols=[create_mock_symbol(f"m{i}") for i in range(57)]
    )

    # Act
    is_super_large = is_super_large_file(parse_result)

    # Assert
    assert is_super_large is True

def test_detect_by_symbol_count():
    """Should detect >100 symbols as super large"""
    # Arrange
    parse_result = ParseResult(
        path=Path("huge.php"),
        file_lines=3000,
        symbols=[create_mock_symbol(f"m{i}") for i in range(120)]
    )

    # Act
    is_super_large = is_super_large_file(parse_result)

    # Assert
    assert is_super_large is True

def test_normal_file_not_detected():
    """Normal files should not be detected as super large"""
    # Arrange
    parse_result = ParseResult(
        path=Path("normal.php"),
        file_lines=1500,
        symbols=[create_mock_symbol(f"m{i}") for i in range(30)]
    )

    # Act
    is_super_large = is_super_large_file(parse_result)

    # Assert
    assert is_super_large is False

def test_select_enhancement_strategy():
    """Should auto-select appropriate strategy"""
    # Arrange
    results = [
        ParseResult(path=Path("normal.php"), file_lines=500, symbols=[]),
        ParseResult(path=Path("large.php"), file_lines=2500, symbols=[]),
        ParseResult(path=Path("super.php"), file_lines=8891, symbols=[]),
    ]

    # Act
    strategies = [select_enhancement_strategy(r) for r in results]

    # Assert
    assert strategies[0] == "standard"
    assert strategies[1] == "hierarchical"
    assert strategies[2] == "multi_turn"
```

**Tasks**:
- [ ] Implement `is_super_large_file()` function (1h)
- [ ] Implement `select_enhancement_strategy()` (2h)
- [ ] Add configuration for thresholds (1h)
- [ ] Write unit tests (2h)
- [ ] Write BDD tests (1h)

**Estimate**: 7 hours (1 day)

---

#### Story 3.2.2: Three-round Dialogue Implementation

**User Story**:
```
As a codeindex user,
I want super large files to be processed using a three-round dialogue,
So that the AI can generate high-quality README despite the size.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: Multi-turn Dialogue for Super Large Files

  Scenario: Three-round dialogue execution
    Given a super large file with 8891 lines and 57 symbols
    When I run AI enhancement with multi-turn
    Then it should execute Round 1 (Architecture Overview)
    And execute Round 2 (Core Component Analysis)
    And execute Round 3 (Final README Synthesis)
    And each round should have prompt < 20KB
    And the final README should be high quality

  Scenario: Round 1 - Architecture Overview
    Given a super large file
    When I execute Round 1
    Then the prompt should include file statistics
    And request purpose and main components
    And the response should be 10-20 lines

  Scenario: Round 2 - Core Component Analysis
    Given Round 1 output
    When I execute Round 2
    Then the prompt should include Round 1 insights
    And focus on the core class/component
    And include grouped symbols list
    And the response should be 30-50 lines

  Scenario: Round 3 - Final Synthesis
    Given Round 1 and Round 2 outputs
    When I execute Round 3
    Then the prompt should combine previous insights
    And request final README format
    And the output should be valid markdown
    And include all required sections

  Scenario: Fallback on failure
    Given Round 2 fails with timeout
    When the multi-turn process fails
    Then it should fallback to standard enhancement
    And log the failure reason
```

**Test Cases** (TDD):

```python
# tests/test_multi_turn_dialogue.py

def test_three_round_execution():
    """Should execute all three rounds successfully"""
    # Arrange
    parse_result = create_super_large_parse_result()
    config = Config.load()

    # Act
    readme = ai_enhance_super_large_file(
        dir_path=Path("/test"),
        parse_results=[parse_result],
        timeout=180
    )

    # Assert
    assert readme is not None
    assert len(readme) > 0
    assert "# README_AI.md" in readme
    # Verify it called AI 3 times (mock)
    assert mock_invoke_ai_cli.call_count == 3

def test_round1_prompt_format():
    """Round 1 should have correct prompt format"""
    # Arrange
    parse_result = create_super_large_parse_result()

    # Act
    prompt = _generate_round1_prompt(parse_result)

    # Assert
    assert "TASK 1: Generate Architecture Overview" in prompt
    assert "Purpose" in prompt
    assert "Main Components" in prompt
    assert len(prompt.encode()) < 20 * 1024  # <20KB

def test_round2_uses_round1_output():
    """Round 2 should incorporate Round 1 insights"""
    # Arrange
    round1_output = "This is a goods management module..."
    parse_result = create_super_large_parse_result()

    # Act
    prompt = _generate_round2_prompt(round1_output, parse_result)

    # Assert
    assert "Building on the overview:" in prompt
    assert round1_output in prompt
    assert "TASK 2: Analyze Core Component" in prompt

def test_round3_synthesis():
    """Round 3 should synthesize previous rounds"""
    # Arrange
    round1_output = "Overview..."
    round2_output = "Core analysis..."

    # Act
    prompt = _generate_round3_prompt(round1_output, round2_output)

    # Assert
    assert round1_output in prompt
    assert round2_output in prompt
    assert "TASK 3: Generate Final README" in prompt
    assert "markdown" in prompt.lower()

def test_fallback_on_failure():
    """Should fallback to standard if multi-turn fails"""
    # Arrange
    parse_result = create_super_large_parse_result()
    mock_invoke_ai_cli.side_effect = TimeoutError("Round 2 timeout")

    # Act
    readme = ai_enhance_super_large_file(
        dir_path=Path("/test"),
        parse_results=[parse_result],
        timeout=180
    )

    # Assert
    # Should have attempted Round 1 and 2, then fallen back
    assert mock_invoke_ai_cli.call_count >= 2
    assert readme is not None  # Fallback should still return something

@pytest.mark.integration
def test_real_ai_enhancement():
    """Integration test with real AI (slow)"""
    # Arrange
    parse_result = load_real_php_file("tests/fixtures/OperateGoods.class.php")
    config = Config.load()

    # Act
    readme = ai_enhance_super_large_file(
        dir_path=Path("/test"),
        parse_results=[parse_result],
        timeout=300
    )

    # Assert
    assert readme is not None
    assert "# README_AI.md" in readme
    assert "Purpose" in readme or "Architecture" in readme
    assert len(readme) > 500  # Should be substantial
```

**Tasks**:
- [ ] Implement `ai_enhance_super_large_file()` skeleton (2h)
- [ ] Implement `_generate_round1_prompt()` (2h)
- [ ] Implement `_generate_round2_prompt()` (2h)
- [ ] Implement `_generate_round3_prompt()` (2h)
- [ ] Implement fallback mechanism (2h)
- [ ] Implement error handling and logging (2h)
- [ ] Write unit tests for each round (4h)
- [ ] Write integration tests (3h)
- [ ] Write BDD tests (2h)

**Estimate**: 21 hours (3 days)

---

#### Story 3.2.3: Prompt Size Optimization

**User Story**:
```
As a system,
I want to ensure each round's prompt is under 20KB,
So that the AI can process it reliably within token limits.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: Prompt Size Optimization

  Scenario: Round 1 prompt size
    Given a file with 8891 lines and 57 symbols
    When I generate Round 1 prompt
    Then the prompt size should be < 10KB

  Scenario: Round 2 prompt size
    Given Round 1 output and symbol groups
    When I generate Round 2 prompt
    Then the prompt size should be < 15KB

  Scenario: Round 3 prompt size
    Given Round 1 and Round 2 outputs
    When I generate Round 3 prompt
    Then the prompt size should be < 15KB

  Scenario: Symbol grouping for large classes
    Given a class with 57 symbols
    When I format symbols for Round 2
    Then symbols should be grouped by responsibility
    And each group should show only top 3 methods
    And total formatted size should be < 5KB
```

**Test Cases** (TDD):

```python
# tests/test_prompt_optimization.py

def test_round1_prompt_size():
    """Round 1 prompt should be compact"""
    # Arrange
    parse_result = ParseResult(
        path=Path("huge.php"),
        file_lines=8891,
        symbols=[create_mock_symbol(f"m{i}") for i in range(57)]
    )

    # Act
    prompt = _generate_round1_prompt(parse_result)

    # Assert
    assert len(prompt.encode()) < 10 * 1024  # <10KB

def test_symbol_grouping_compression():
    """Grouped symbols should be compact"""
    # Arrange
    symbols = [create_mock_symbol(f"method{i}") for i in range(57)]

    # Act
    grouped = _format_symbols_grouped(symbols)

    # Assert
    assert len(grouped.encode()) < 5 * 1024  # <5KB
    assert "Retrieval" in grouped  # Should have groups
    assert "top" in grouped.lower() or "..." in grouped  # Should show truncation

def test_round2_prompt_within_limit():
    """Round 2 prompt should not exceed 15KB"""
    # Arrange
    round1_output = "A" * 500  # Simulate output
    parse_result = create_super_large_parse_result()

    # Act
    prompt = _generate_round2_prompt(round1_output, parse_result)

    # Assert
    assert len(prompt.encode()) < 15 * 1024  # <15KB

def test_round3_prompt_within_limit():
    """Round 3 prompt should not exceed 15KB"""
    # Arrange
    round1_output = "A" * 500
    round2_output = "B" * 1000

    # Act
    prompt = _generate_round3_prompt(round1_output, round2_output)

    # Assert
    assert len(prompt.encode()) < 15 * 1024  # <15KB
```

**Tasks**:
- [ ] Implement `_format_symbols_grouped()` (3h)
- [ ] Implement prompt size validation (1h)
- [ ] Add logging for prompt sizes (1h)
- [ ] Optimize Round 1 prompt (1h)
- [ ] Optimize Round 2 prompt (2h)
- [ ] Optimize Round 3 prompt (1h)
- [ ] Write size validation tests (2h)
- [ ] Performance testing (1h)

**Estimate**: 12 hours (1.5 days)

---

#### Story 3.2.4: Multi-turn CLI Integration

**User Story**:
```
As a user,
I want to see clear feedback when multi-turn dialogue is being used,
So that I understand why processing is taking longer.
```

**Acceptance Criteria** (BDD):

```gherkin
Feature: Multi-turn User Feedback

  Scenario: Display multi-turn indicator
    Given a super large file being processed
    When AI enhancement starts
    Then the CLI should display "Using multi-turn dialogue"
    And show progress for each round
    And display estimated time

  Scenario: Round progress indicators
    When Round 1 completes
    Then display "✓ Round 1: Architecture Overview (30s)"
    When Round 2 completes
    Then display "✓ Round 2: Core Analysis (60s)"
    When Round 3 completes
    Then display "✓ Round 3: Final Synthesis (45s)"

  Scenario: Fallback notification
    Given Round 2 fails
    When fallback is triggered
    Then display warning message
    And explain why it fell back
    And still complete the enhancement
```

**Test Cases** (TDD):

```python
# tests/test_multi_turn_cli.py

def test_multi_turn_indicator():
    """Should display multi-turn indicator"""
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(cli.main, [
        'scan-all',
        '--root', 'tests/fixtures/super_large_project'
    ])

    # Assert
    assert "multi-turn dialogue" in result.output.lower()
    assert "super large file" in result.output.lower()

def test_round_progress_display():
    """Should show progress for each round"""
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(cli.main, ['scan-all', '--root', 'tests/fixtures/super_large_project'])

    # Assert
    assert "Round 1" in result.output or "Architecture" in result.output
    assert "Round 2" in result.output or "Core" in result.output
    assert "Round 3" in result.output or "Synthesis" in result.output

def test_fallback_notification():
    """Should notify user when fallback occurs"""
    # Arrange
    runner = CliRunner()
    # Mock AI to fail on Round 2

    # Act
    result = runner.invoke(cli.main, ['scan-all'])

    # Assert
    # Should see fallback message
    assert "fallback" in result.output.lower() or "warning" in result.output.lower()
```

**Tasks**:
- [ ] Add multi-turn progress indicators (2h)
- [ ] Implement round-by-round output (2h)
- [ ] Add timing information (1h)
- [ ] Implement fallback notifications (1h)
- [ ] Write CLI output tests (2h)
- [ ] Update documentation (1h)

**Estimate**: 9 hours (1 day)

---

### Epic 3.2 Summary

**Total Stories**: 4
**Total Estimate**: 49 hours (6-7 days ≈ 2 weeks with buffer)

**Story Breakdown**:
- Story 3.2.1: Detection (1 day)
- Story 3.2.2: Three-round Dialogue (3 days)
- Story 3.2.3: Prompt Optimization (1.5 days)
- Story 3.2.4: CLI Integration (1 day)

**Deliverables**:
- ✅ Multi-turn dialogue implementation
- ✅ Automatic strategy selection
- ✅ Prompt size optimization
- ✅ User-friendly CLI feedback
- ✅ Fallback mechanisms
- ✅ 40+ unit tests
- ✅ 15+ BDD scenarios

---

## 📖 Epic 3.3: Hierarchical Prompt Optimization

### Epic Goal
Improve AI enhancement quality for medium and large files (500-5000 lines) using hierarchical prompt formatting.

### User Stories

*(Summarized for brevity - would follow same TDD/BDD format)*

#### Story 3.3.1: Hierarchical Prompt Formatter
- Implement symbol grouping by responsibility
- Implement top-N selection per group
- Adaptive detail levels

**Estimate**: 2 days

#### Story 3.3.2: Auto Mode Selection
- Implement automatic format selection based on file size
- flat (<500 lines) → hierarchical (500-2000) → compressed (2000-5000)

**Estimate**: 1 day

#### Story 3.3.3: Integration and Testing
- Integrate with SmartWriter
- End-to-end testing on real projects
- Performance benchmarking

**Estimate**: 2 days

---

## 📊 Complete Epic 3 Summary

### Timeline

```
Week 1-2: Epic 3.1 - Technical Debt Detection
  Days 1-2: Story 3.1.1 (File-level Detection)
  Days 3-4: Story 3.1.2 (Symbol Overload)
  Days 5-7: Story 3.1.3 (Report Generation)
  Days 8-9: Story 3.1.4 (CLI Integration)

Week 3-4: Epic 3.2 - Multi-turn Dialogue
  Day 10: Story 3.2.1 (Detection)
  Days 11-13: Story 3.2.2 (Three-round Dialogue)
  Days 14-15: Story 3.2.3 (Prompt Optimization)
  Day 16: Story 3.2.4 (CLI Integration)

Week 5: Epic 3.3 - Hierarchical Prompt
  Days 17-18: Story 3.3.1 (Formatter)
  Day 19: Story 3.3.2 (Auto Selection)
  Days 20-21: Story 3.3.3 (Integration)
```

### Resource Requirements
- **Developer**: 1 full-time (21 days)
- **Test Coverage**: Unit + Integration + BDD
- **Documentation**: Inline + User Guide + API Docs

### Success Criteria
| Metric | Current | Target | Epic Delivery |
|--------|---------|--------|---------------|
| AI Success Rate | 50% | 90% | 88-92% |
| README Quality | 6/10 | 9/10 | 8.5-9/10 |
| Large File Success | 10% | 90% | 85-90% |
| Tech Debt Visibility | 0% | 100% | 100% |
| Test Coverage | 75% | 90% | 90%+ |

---

## 📝 Next Steps

1. **Review and Approve Epic**
   - [ ] Review Epic 3 plan
   - [ ] Approve scope and estimates
   - [ ] Assign to sprint

2. **Setup Development Environment**
   - [ ] Create feature branch: `feature/epic3-ai-optimization`
   - [ ] Setup test fixtures
   - [ ] Configure CI/CD for new tests

3. **Start Sprint 1: Epic 3.1**
   - [ ] Begin Story 3.1.1
   - [ ] Daily standup
   - [ ] TDD/BDD cycle

---

**Document Version**: 1.0
**Created**: 2026-01-27
**Author**: codeindex team
**Status**: READY FOR IMPLEMENTATION ✅
