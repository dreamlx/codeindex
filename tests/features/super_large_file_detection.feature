# Feature: Super Large File Detection
# Epic 3.2 Story 3.2.1
#
# As a codeindex user,
# I want the system to automatically detect super large files,
# So that it can apply the appropriate AI enhancement strategy.

Feature: Super Large File Detection

  Background:
    Given a codeindex configuration is loaded
    And a symbol scorer is available

  Scenario: Detect super large file by line count
    Given a PHP file with 8891 lines
    And the file has 57 symbols
    When I check if it's a super large file
    Then it should be detected as super large
    And the detection reason should be "excessive_lines"
    And it should recommend multi-turn dialogue strategy

  Scenario: Detect super large file by symbol count
    Given a Python file with 3000 lines
    And the file has 120 symbols
    When I check if it's a super large file
    Then it should be detected as super large
    And the detection reason should be "excessive_symbols"
    And it should recommend multi-turn dialogue strategy

  Scenario: Detect super large file by both criteria
    Given a PHP file with 10000 lines
    And the file has 150 symbols
    When I check if it's a super large file
    Then it should be detected as super large
    And the detection reason should be "excessive_lines,excessive_symbols"
    And it should recommend multi-turn dialogue strategy

  Scenario: Normal file is not detected as super large
    Given a Python file with 1500 lines
    And the file has 30 symbols
    When I check if it's a super large file
    Then it should not be detected as super large
    And it should recommend standard AI enhancement

  Scenario: Large file (but not super large) detection
    Given a PHP file with 3000 lines
    And the file has 45 symbols
    When I check if it's a super large file
    Then it should not be detected as super large
    And it should recommend hierarchical prompt strategy

  Scenario: Edge case - exactly at threshold
    Given a Python file with 5000 lines
    And the file has 100 symbols
    When I check if it's a super large file
    Then it should not be detected as super large
    And it should recommend hierarchical prompt strategy

  Scenario: Edge case - just over threshold
    Given a Python file with 5001 lines
    And the file has 101 symbols
    When I check if it's a super large file
    Then it should be detected as super large
    And it should recommend multi-turn dialogue strategy

  Scenario: Auto-select enhancement strategy for mixed project
    Given a project with multiple files
      | filename           | lines | symbols | expected_strategy |
      | small.py           | 300   | 10      | standard          |
      | normal.py          | 800   | 25      | standard          |
      | large.php          | 2500  | 40      | hierarchical      |
      | very_large.php     | 4500  | 80      | hierarchical      |
      | super_large.php    | 8891  | 57      | multi_turn        |
      | huge_symbols.py    | 3000  | 120     | multi_turn        |
    When I select enhancement strategy for each file
    Then each file should use the expected strategy
    And the strategy selection should be logged

  Scenario: Configuration override for thresholds
    Given custom thresholds are configured
      | threshold_name         | value |
      | super_large_lines      | 3000  |
      | super_large_symbols    | 80    |
    And a PHP file with 3500 lines
    And the file has 60 symbols
    When I check if it's a super large file
    Then it should be detected as super large
    And the detection should respect custom thresholds
