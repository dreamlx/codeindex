Feature: CLI Module Split
  As a developer
  I want CLI commands organized in separate modules
  So that the code is more maintainable and testable

  Background:
    Given the codeindex CLI is installed
    And all modules are properly imported

  Scenario: Tech debt command is accessible
    When I run "codeindex tech-debt --help"
    Then the command should display help text
    And no import errors should occur

  Scenario: Config commands are accessible
    When I run "codeindex init --help"
    Then the command should display help text
    When I run "codeindex status --help"
    Then the command should display help text
    When I run "codeindex list-dirs --help"
    Then the command should display help text

  Scenario: Symbol commands are accessible
    When I run "codeindex index --help"
    Then the command should display help text
    When I run "codeindex symbols --help"
    Then the command should display help text
    When I run "codeindex affected --help"
    Then the command should display help text

  Scenario: Scan commands are accessible
    When I run "codeindex scan --help"
    Then the command should display help text
    When I run "codeindex scan-all --help"
    Then the command should display help text

  Scenario: All commands are registered with main
    When I run "codeindex --help"
    Then I should see all subcommands listed
      | scan      |
      | scan-all  |
      | init      |
      | status    |
      | list-dirs |
      | index     |
      | symbols   |
      | affected  |
      | tech-debt |

  Scenario: Backward compatibility maintained
    Given the legacy CLI tests exist
    When I run all CLI tests
    Then all tests should pass
    And no functionality should be broken

  Scenario: No circular imports
    When I import each CLI module
    Then no ImportError should occur
    And no circular dependency should exist

  Scenario: Console is shared across modules
    Given console is defined in cli_common
    When I use console in cli_tech_debt
    And I use console in cli_scan
    Then the same console instance should be used
    And output formatting should be consistent

  Scenario: Module sizes are within limits
    When I check the size of cli.py
    Then it should be less than 100 lines
    When I check the size of cli_tech_debt.py
    Then it should be approximately 250 lines
    When I check the size of cli_config.py
    Then it should be approximately 150 lines
    When I check the size of cli_symbols.py
    Then it should be approximately 200 lines
    When I check the size of cli_scan.py
    Then it should be approximately 300 lines
