# Feature: AI Enhancement Helper Functions
# Epic 4 Story 4.1
#
# As a developer,
# I want multi-turn execution logic extracted into reusable functions,
# So that I can eliminate code duplication in scan and scan-all commands.

Feature: AI Enhancement Helper Functions

  Background:
    Given a codeindex configuration is loaded
    And an AI CLI command is configured

  # ============================================================================
  # Scenario Group 1: ParseResult Aggregation
  # ============================================================================

  Scenario: Aggregate multiple parse results from different files
    Given multiple parse results:
      | filename   | lines | symbols |
      | file1.py   | 1000  | 20      |
      | file2.py   | 2000  | 30      |
      | file3.py   | 500   | 10      |
    When I aggregate them into one ParseResult
    Then the aggregated result should contain 60 symbols
    And the total line count should be 3500

  Scenario: Aggregate single parse result
    Given a single parse result with 1000 lines and 20 symbols
    When I aggregate it into one ParseResult
    Then the result should be identical to the input
    And have 20 symbols and 1000 lines

  Scenario: Aggregate empty parse results list
    Given an empty list of parse results
    When I aggregate them into one ParseResult
    Then the result should have 0 symbols
    And 0 lines

