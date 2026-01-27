Feature: Symbol Overload Detection
  As a developer
  I want to detect symbol overload issues
  So that I understand code quality problems

  Background:
    Given a TechDebtDetector with default configuration
    And a SymbolImportanceScorer

  Scenario: Detect massive symbol count
    Given a PHP file with 120 symbols
    When I analyze symbol overload
    Then it should report a CRITICAL issue
    And the issue category should be "massive_symbol_count"
    And the metric value should be 120

  Scenario: Normal symbol count
    Given a PHP file with 50 symbols
    When I analyze symbol overload
    Then no massive symbol count issues should be reported
    And the analysis should show 50 total symbols
