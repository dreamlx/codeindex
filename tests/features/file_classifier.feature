# Feature: Unified File Size Classification
# Epic 4 Story 4.2
#
# As a developer,
# I want a unified file size classification system,
# So that tech_debt and ai_enhancement modules use consistent thresholds.

Feature: Unified File Size Classification

  Background:
    Given a codeindex configuration is loaded
    And a file size classifier is initialized

  # ============================================================================
  # Scenario Group 1: Basic File Size Classification
  # ============================================================================

  Scenario: Classify tiny file
    Given a Python file with 300 lines and 10 symbols
    When I classify the file size
    Then it should be categorized as "tiny"
    And it should not be super large
    And it should not be large

  Scenario: Classify small file
    Given a Python file with 800 lines and 15 symbols
    When I classify the file size
    Then it should be categorized as "small"
    And it should not be super large

  Scenario: Classify medium file
    Given a PHP file with 1500 lines and 25 symbols
    When I classify the file size
    Then it should be categorized as "medium"
    And it should not be large

  Scenario: Classify large file by line count
    Given a PHP file with 3000 lines and 45 symbols
    When I classify the file size
    Then it should be categorized as "large"
    And it should be large but not super large
    And the reason should include "line threshold"

  Scenario: Classify super large file by line count
    Given a PHP file with 6000 lines and 50 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And it should be super large
    And the reason should be "excessive_lines"

  Scenario: Classify super large file by symbol count
    Given a Python file with 3000 lines and 120 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And it should be super large
    And the reason should be "excessive_symbols"

  Scenario: Classify super large file by both criteria
    Given a PHP file with 10000 lines and 150 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And the reason should be "excessive_lines,excessive_symbols"

  # ============================================================================
  # Scenario Group 2: Edge Cases and Thresholds
  # ============================================================================

  Scenario: File exactly at super large line threshold (not super large)
    Given a Python file with 5000 lines and 50 symbols
    When I classify the file size
    Then it should be categorized as "large"
    And it should not be super large

  Scenario: File just over super large line threshold
    Given a Python file with 5001 lines and 50 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And it should be super large

  Scenario: File exactly at super large symbol threshold (not super large)
    Given a Python file with 3000 lines and 100 symbols
    When I classify the file size
    Then it should be categorized as "large"
    And it should not be super large

  Scenario: File just over super large symbol threshold
    Given a Python file with 3000 lines and 101 symbols
    When I classify the file size
    Then it should be categorized as "super_large"
    And it should be super large

  # ============================================================================
  # Scenario Group 3: Custom Configuration
  # ============================================================================

  Scenario: Use custom thresholds from config
    Given custom thresholds are configured:
      | threshold_name      | value |
      | super_large_lines   | 3000  |
      | super_large_symbols | 80    |
    And a Python file with 3500 lines and 60 symbols
    When I classify the file size
    Then it should respect the custom threshold
    And be categorized as "super_large"
    And the reason should be "excessive_lines"

  Scenario: Multiple size categories with custom thresholds
    Given custom thresholds are configured:
      | threshold_name      | value |
      | super_large_lines   | 4000  |
      | large_lines         | 1500  |
    And files with different sizes:
      | lines | symbols | expected_category |
      | 500   | 10      | small             |
      | 2000  | 30      | large             |
      | 5000  | 50      | super_large       |
    When I classify each file
    Then each should match its expected category

  # ============================================================================
  # Scenario Group 4: Integration with Existing Modules
  # ============================================================================

  Scenario: Tech debt module uses FileSizeClassifier
    Given a file for tech debt analysis with 6000 lines
    When I analyze technical debt
    Then it should use FileSizeClassifier for size detection
    And not use hard-coded SUPER_LARGE_FILE constant
    And detection should respect config thresholds

  Scenario: AI enhancement module uses FileSizeClassifier
    Given a file for AI enhancement with 6000 lines
    When I select enhancement strategy
    Then it should use FileSizeClassifier.is_super_large()
    And not use separate is_super_large_file() logic
    And strategy selection should be consistent with tech debt

  Scenario: Consistent detection across modules
    Given a file with 5500 lines and 110 symbols
    When I detect size in tech debt module
    And I detect size in ai enhancement module
    Then both should agree it is super large
    And both should use the same thresholds
    And both should report the same reason

  # ============================================================================
  # Scenario Group 5: FileSizeAnalysis Data Structure
  # ============================================================================

  Scenario: FileSizeAnalysis contains complete information
    Given a PHP file with 6000 lines and 120 symbols
    When I classify the file size
    Then the analysis should contain:
      | field                      | value                          |
      | category                   | super_large                    |
      | file_lines                 | 6000                           |
      | symbol_count               | 120                            |
      | exceeds_line_threshold     | True                           |
      | exceeds_symbol_threshold   | True                           |
      | reason                     | excessive_lines,excessive_symbols |

  Scenario: Query convenience methods
    Given a super large file with 6000 lines
    And a file size classifier
    When I call is_super_large()
    Then it should return True
    When I call is_large()
    Then it should return True
    When I call get_category()
    Then it should return "super_large"
