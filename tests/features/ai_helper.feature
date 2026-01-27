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

  # ============================================================================
  # Scenario Group 2: Multi-turn Enhancement Execution
  # ============================================================================

  Scenario: Execute multi-turn with auto-detection for super large file
    Given a directory with 6000 lines and 120 symbols
    When I execute multi-turn enhancement with "auto" strategy
    Then it should detect the file as super large
    And it should execute multi-turn dialogue
    And the enhancement should succeed
    And return a WriteResult with README content

  Scenario: Execute multi-turn with explicit multi_turn strategy
    Given a directory with 2000 lines and 30 symbols
    When I execute multi-turn enhancement with "multi_turn" strategy
    Then it should skip detection
    And it should execute multi-turn dialogue directly
    And the enhancement should succeed

  Scenario: Execute multi-turn with standard strategy (should fail)
    Given a directory with 6000 lines and 120 symbols
    When I execute multi-turn enhancement with "standard" strategy
    Then it should skip detection
    And it should not execute multi-turn dialogue
    And the enhancement should fail
    And return message "Multi-turn not applicable or failed"

  Scenario: Multi-turn enhancement with fallback on Round 1 failure
    Given a directory that will cause Round 1 to fail
    When I execute multi-turn enhancement with "auto" strategy
    Then it should detect the file as super large
    And it should attempt multi-turn dialogue
    And the enhancement should fail
    And return an error message about Round 1 failure

  Scenario: Multi-turn enhancement with quiet mode
    Given a directory with 6000 lines and 120 symbols
    When I execute multi-turn enhancement with quiet=True
    Then it should not print progress messages
    And the enhancement should succeed

  # ============================================================================
  # Scenario Group 3: Integration with scan command
  # ============================================================================

  Scenario: Scan command uses execute_multi_turn_enhancement
    Given a directory to scan with 6000 lines
    When I run "codeindex scan ./path --strategy auto"
    Then it should call execute_multi_turn_enhancement
    And not have duplicate detection logic in scan command

  Scenario: Scan-all command uses execute_multi_turn_enhancement
    Given multiple directories in scan-all Phase 2
    When scan-all processes a super large directory
    Then it should call execute_multi_turn_enhancement
    And share the same logic as scan command

  # ============================================================================
  # Scenario Group 4: Error Handling
  # ============================================================================

  Scenario: Handle AI CLI timeout gracefully
    Given a directory that causes AI CLI timeout
    When I execute multi-turn enhancement
    Then it should return failure
    And include timeout error in message
    And allow caller to fall back to standard enhancement

  Scenario: Handle write failure after successful multi-turn
    Given a directory with successful multi-turn result
    But write_readme will fail
    When I execute multi-turn enhancement
    Then multi-turn dialogue should succeed
    And write operation should fail
    And return appropriate error message
