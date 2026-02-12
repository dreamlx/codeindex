# Feature: Interactive Setup Wizard
# Epic 15 Story 15.1
#
# As a developer,
# I want an interactive setup wizard when I run `codeindex init`,
# So that I can configure my project with smart defaults in under 1 minute.

Feature: Interactive Setup Wizard

  Background:
    Given I am in a project directory
    And no .codeindex.yaml exists

  # ============================================================================
  # Scenario Group 1: Language Auto-Detection
  # ============================================================================

  Scenario: Detect Python project
    Given the project contains Python files
    When I run the interactive wizard
    Then Python should be auto-detected
    And the wizard should suggest Python in the languages list

  Scenario: Detect multi-language project
    Given the project contains Python and PHP files
    When I run the interactive wizard
    Then Python and PHP should be auto-detected
    And the wizard should suggest both languages

  Scenario: Detect Java project with Spring Boot
    Given the project contains Java files with Spring annotations
    When I run the interactive wizard
    Then Java should be auto-detected
    And Spring Boot framework should be detected

  # ============================================================================
  # Scenario Group 2: Smart Pattern Inference
  # ============================================================================

  Scenario: Infer include patterns from project structure
    Given a project with src/ and lib/ directories
    When I run the interactive wizard
    Then the wizard should suggest including src/ and lib/
    And suggest excluding tests/ and __pycache__/

  Scenario: Infer exclude patterns from common artifacts
    Given a project with node_modules/ and .git/ directories
    When I run the interactive wizard
    Then the wizard should suggest excluding node_modules/
    And suggest excluding .git/

  # ============================================================================
  # Scenario Group 3: Configuration Creation
  # ============================================================================

  Scenario: Create .codeindex.yaml with user choices
    When I run the interactive wizard
    And I select Python as language
    And I accept default include patterns
    And I disable Git Hooks
    Then a .codeindex.yaml should be created
    And it should contain language: python
    And it should contain suggested include patterns
    And hooks.post_commit.enabled should be false

  Scenario: Create .codeindex.yaml with all features enabled
    When I run the interactive wizard
    And I select Python and PHP as languages
    And I accept default patterns
    And I enable Git Hooks with auto mode
    And I request CODEINDEX.md creation
    Then .codeindex.yaml should be created with both languages
    And hooks.post_commit.mode should be auto
    And CODEINDEX.md should be created

  # ============================================================================
  # Scenario Group 4: Performance Auto-Tuning
  # ============================================================================

  Scenario: Auto-tune parallel_workers for small project
    Given a project with 50 files
    When I run the interactive wizard
    Then parallel_workers should be set to 4

  Scenario: Auto-tune parallel_workers for large project
    Given a project with 2000 files
    When I run the interactive wizard
    Then parallel_workers should be set to 16

  Scenario: Auto-tune batch_size based on project size
    Given a project with 500 files
    When I run the interactive wizard
    Then batch_size should be set to 50

  # ============================================================================
  # Scenario Group 5: AI CLI Configuration
  # ============================================================================

  Scenario: Skip AI CLI configuration
    When I run the interactive wizard
    And I choose to skip AI CLI setup
    Then ai_command should not be in .codeindex.yaml

  Scenario: Configure Claude CLI
    When I run the interactive wizard
    And I choose to configure AI CLI
    And I select Claude as the AI tool
    Then ai_command should be 'claude -p "{prompt}" --allowedTools "Read"'

  # ============================================================================
  # Scenario Group 6: CODEINDEX.md Generation
  # ============================================================================

  Scenario: Create CODEINDEX.md guide for AI agents
    When I run the interactive wizard
    And I request CODEINDEX.md creation
    Then CODEINDEX.md should be created in project root
    And it should contain codeindex usage instructions
    And it should contain configuration reference

  Scenario: Skip CODEINDEX.md creation
    When I run the interactive wizard
    And I skip CODEINDEX.md creation
    Then CODEINDEX.md should not be created

  # ============================================================================
  # Scenario Group 7: Git Hooks Installation
  # ============================================================================

  Scenario: Install Git Hooks with auto mode
    When I run the interactive wizard
    And I enable Git Hooks with auto mode
    Then Git Hooks should be installed
    And post-commit hook should be configured with mode auto

  Scenario: Skip Git Hooks installation
    When I run the interactive wizard
    And I skip Git Hooks installation
    Then Git Hooks should not be installed
    And hooks.post_commit.enabled should be false

  # ============================================================================
  # Scenario Group 8: Wizard Success Metrics
  # ============================================================================

  Scenario: Complete wizard in under 1 minute
    When I run the interactive wizard
    And I make all default choices
    Then the wizard should complete
    And the total time should be under 60 seconds

  Scenario: Wizard with zero manual configuration
    When I run the interactive wizard
    And I accept all smart defaults
    Then .codeindex.yaml should be created
    And all languages should be auto-detected
    And all patterns should be auto-inferred
    And no manual input should be required

  # ============================================================================
  # Scenario Group 9: CLAUDE.md Injection
  # ============================================================================

  Scenario: Create CLAUDE.md when it does not exist
    When I request CLAUDE.md injection
    Then CLAUDE.md should be created in project root with codeindex section
    And it should contain the codeindex marker
    And it should contain "Always read README_AI.md"

  Scenario: Inject into existing CLAUDE.md
    Given the project has an existing CLAUDE.md
    When I request CLAUDE.md injection
    Then CLAUDE.md should contain the codeindex section
    And the original content should be preserved after the injection

  Scenario: Idempotent injection on re-run
    Given CLAUDE.md already has codeindex injection
    When I request CLAUDE.md injection
    Then CLAUDE.md should contain exactly one codeindex section
    And the content between markers should be updated

  Scenario: Skip CLAUDE.md injection
    When I skip CLAUDE.md injection
    Then CLAUDE.md should not exist in project root
