Feature: Technical Debt Reporting
  As a developer
  I want to generate technical debt reports in different formats
  So that I can analyze code quality across multiple files

  Background:
    Given a TechDebtReporter

  Scenario: Generate report for single file with issues
    Given a file "bad_code.py" with 1 CRITICAL issue
    When I generate a report
    Then the report should show 1 files analyzed
    And the report should show 1 total issues
    And the report should show 1 CRITICAL issues

  Scenario: Generate report for multiple files
    Given a file "file1.py" with 1 CRITICAL issue
    And a file "file2.py" with 2 HIGH issues
    And a file "file3.py" with no issues
    When I generate a report
    Then the report should show 3 files analyzed
    And the report should show 3 total issues
    And the report should show 1 CRITICAL issues
    And the report should show 2 HIGH issues
    And the average quality score should be 85.0

  Scenario: Format report as console output
    Given a file "test.py" with 1 CRITICAL issue
    When I generate a report
    And I format the report as console
    Then the output should contain "Technical Debt Report"
    And the output should contain "CRITICAL"
    And the output should contain "test.py"

  Scenario: Format report as markdown
    Given a file "test.py" with 1 HIGH issue
    When I generate a report
    And I format the report as markdown
    Then the output should contain "# Technical Debt Report"
    And the output should contain "## Summary"
    And the output should contain "### HIGH"
    And the output should contain "| File |"

  Scenario: Format report as JSON
    Given a file "test.py" with 1 CRITICAL issue
    When I generate a report
    And I format the report as JSON
    Then the output should be valid JSON
    And the JSON should contain "total_files": 1
    And the JSON should contain "critical_issues": 1
