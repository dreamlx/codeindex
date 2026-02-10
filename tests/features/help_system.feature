# Feature: Enhanced Help System
# Epic 15 Story 15.3
#
# As a developer,
# I want comprehensive help documentation for codeindex configuration,
# So that I can understand and tune all available settings.

Feature: Enhanced Help System

  Background:
    Given codeindex CLI is available

  # ============================================================================
  # Scenario Group 1: --help-config Flag
  # ============================================================================

  Scenario: Display full configuration reference
    When I run "codeindex init --help-config"
    Then the output should contain "Configuration Reference"
    And the output should contain "parallel_workers"
    And the output should contain "batch_size"
    And the output should contain "Performance Settings"

  Scenario: Configuration help shows parameter descriptions
    When I run "codeindex init --help-config"
    Then the output should contain parameter description for "parallel_workers"
    And the output should contain parameter description for "batch_size"
    And the output should contain parameter description for "ai_command"

  Scenario: Configuration help shows value ranges
    When I run "codeindex init --help-config"
    Then the output should contain "Range: 1-32" for parallel_workers
    And the output should contain "Range: 10-200" for batch_size

  Scenario: Configuration help shows performance recommendations
    When I run "codeindex init --help-config"
    Then the output should contain "Small projects (<100 files): 4"
    And the output should contain "Medium projects (100-1000 files): 8"
    And the output should contain "Large projects (>1000 files): 16"

  # ============================================================================
  # Scenario Group 2: Config Explain Command
  # ============================================================================

  Scenario: Explain parallel_workers parameter
    When I run "codeindex config explain parallel_workers"
    Then the output should contain "Number of concurrent workers"
    And the output should contain "Default: CPU count"
    And the output should contain "Recommendation"

  Scenario: Explain batch_size parameter
    When I run "codeindex config explain batch_size"
    Then the output should contain "Files processed per batch"
    And the output should contain "Default: 50"
    And the output should contain "Trade-off"

  Scenario: Explain hooks.post_commit.mode parameter
    When I run "codeindex config explain hooks.post_commit.mode"
    Then the output should contain "auto"
    And the output should contain "disabled"
    And the output should contain "async"
    And the output should contain "sync"

  Scenario: Explain non-existent parameter
    When I run "codeindex config explain nonexistent"
    Then the output should contain "Unknown parameter"
    And the exit code should be 1

  # ============================================================================
  # Scenario Group 3: Help Output Formatting
  # ============================================================================

  Scenario: Help output is properly formatted
    When I run "codeindex init --help-config"
    Then the output should use tables or structured formatting
    And the output should be readable in terminal

  Scenario: Help output includes examples
    When I run "codeindex init --help-config"
    Then the output should contain configuration examples
    And the output should contain YAML syntax examples

  # ============================================================================
  # Scenario Group 4: Performance Tuning Guidance
  # ============================================================================

  Scenario: Show performance tuning for small projects
    When I run "codeindex config explain parallel_workers"
    Then the output should contain "Small projects (<100 files): 4"

  Scenario: Show performance tuning for large projects
    When I run "codeindex config explain parallel_workers"
    Then the output should contain "Large projects (>1000 files): 16"

  Scenario: Show memory vs speed trade-offs
    When I run "codeindex config explain batch_size"
    Then the output should contain "Larger = faster but more memory"
    And the output should contain "Smaller = slower but less memory"

  # ============================================================================
  # Scenario Group 5: Context-Aware Help
  # ============================================================================

  Scenario: Help references current project settings
    Given a .codeindex.yaml exists with parallel_workers: 8
    When I run "codeindex config explain parallel_workers"
    Then the output should contain "Current value: 8"

  Scenario: Help suggests improvements for current settings
    Given a .codeindex.yaml exists with parallel_workers: 32
    And the system has 8 CPU cores
    When I run "codeindex config explain parallel_workers"
    Then the output should contain "Warning: Value exceeds CPU count"
