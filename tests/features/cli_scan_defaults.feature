Feature: CLI Scan Default Behavior
  As a new user
  I want codeindex scan-all to work without AI configuration
  So that I can get structural documentation immediately after init

  Background:
    Given a project directory with Python files
    And a valid .codeindex.yaml configuration

  # ===== scan command defaults =====

  Scenario: scan without --ai generates structural output
    When I run scan on a directory without --ai flag
    Then the output should be generated with SmartWriter
    And no AI CLI should be invoked

  Scenario: scan with --ai invokes AI CLI
    Given ai_command is configured in .codeindex.yaml
    When I run scan on a directory with --ai flag
    Then the AI CLI should be invoked

  Scenario: scan with --ai but no ai_command shows error
    Given ai_command is NOT configured in .codeindex.yaml
    When I run scan on a directory with --ai flag
    Then it should print an error about missing ai_command
    And the exit code should be non-zero

  # ===== --fallback deprecation =====

  Scenario: scan with --fallback prints deprecation warning
    When I run scan on a directory with --fallback flag
    Then it should print a deprecation warning for --fallback
    And the output should be generated with SmartWriter

  # ===== --dry-run behavior =====

  Scenario: --dry-run with --ai shows prompt preview
    Given ai_command is configured in .codeindex.yaml
    When I run scan on a directory with --dry-run and --ai flags
    Then it should show a prompt preview
    And no AI CLI should be invoked

  Scenario: --dry-run without --ai prints error
    When I run scan on a directory with --dry-run but without --ai
    Then it should print an error that --dry-run requires --ai
    And the exit code should be non-zero

  # ===== scan-all command defaults =====

  Scenario: scan-all without --ai generates structural output
    When I run scan-all without --ai flag
    Then all directories should be processed with SmartWriter
    And no AI CLI should be invoked

  Scenario: scan-all with --ai invokes AI for all directories
    Given ai_command is configured in .codeindex.yaml
    When I run scan-all with --ai flag
    Then the AI CLI should be invoked for directories

  Scenario: scan-all --fallback prints deprecation warning
    When I run scan-all with --fallback flag
    Then it should print a deprecation warning for --fallback
    And all directories should be processed with SmartWriter
