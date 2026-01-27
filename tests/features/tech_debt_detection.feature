Feature: Technical Debt Detection
  As a developer
  I want to detect technical debt automatically
  So that I can prioritize refactoring work

  Background:
    Given a TechDebtDetector with default configuration
    And a SymbolImportanceScorer

  Scenario: Normal file passes all checks
    Given a Python file with 300 lines
    And 15 well-structured symbols
    When I analyze technical debt
    Then no CRITICAL issues should be reported
    And no HIGH issues should be reported
    And the quality score should be above 80

  Scenario: Detect super large file
    Given a PHP file with 8891 lines
    And 57 symbols
    When I analyze technical debt
    Then it should report a CRITICAL issue
    And the issue category should be "super_large_file"
    And the issue description should include "8891 lines"
    And the suggestion should recommend splitting the file
    And the quality score should be below 80

  Scenario: Detect God Class
    Given a PHP file with 2000 lines
    And a class "OperateGoods" with 57 methods
    When I analyze technical debt
    Then it should report a CRITICAL issue
    And the issue category should be "god_class"
    And the issue description should mention "OperateGoods"
    And the suggestion should recommend extracting smaller classes
    And the quality score should be below 80

  Scenario: Detect large file (not super large)
    Given a PHP file with 3000 lines
    And 30 symbols
    When I analyze technical debt
    Then it should report a HIGH issue
    And the issue category should be "large_file"
    And the quality score should be between 80 and 90

  Scenario: Multiple issues in one file
    Given a PHP file with 8891 lines
    And a class "HugeClass" with 57 methods
    When I analyze technical debt
    Then it should report 2 or more issues
    And at least one should be CRITICAL for file size
    And at least one should be CRITICAL for God Class
    And the quality score should be below 50
