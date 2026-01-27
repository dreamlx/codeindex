# Feature: Multi-turn Dialogue for Super Large Files
# Epic 3.2 Story 3.2.2
#
# As a codeindex user,
# I want super large files to be processed using a three-round dialogue,
# So that the AI can generate high-quality README despite the size.

Feature: Multi-turn Dialogue Enhancement

  Background:
    Given a codeindex configuration is loaded
    And AI CLI is available and responding

  Scenario: Three-round dialogue execution for super large file
    Given a super large PHP file with 8891 lines and 57 symbols
    And the file is "OperateGoods.class.php"
    When I run multi-turn AI enhancement
    Then it should execute Round 1 (Architecture Overview)
    And it should execute Round 2 (Core Component Analysis)
    And it should execute Round 3 (Final README Synthesis)
    And each round's prompt should be under 20KB
    And the final README should be generated successfully
    And the README should contain "Purpose" section
    And the README should contain "Components" section

  Scenario: Round 1 - Architecture Overview prompt format
    Given a super large file with statistics
      | lines | symbols | classes | functions |
      | 8891  | 57      | 1       | 57        |
    And the file has top symbols
      | symbol_name      | importance_score |
      | OperateGoods     | 100              |
      | createGoods      | 85               |
      | updateGoods      | 80               |
      | getGoodsList     | 75               |
      | deleteGoods      | 70               |
    When I generate Round 1 prompt
    Then the prompt should include file statistics
    And the prompt should include top 5 symbol names
    And the prompt should ask for file purpose
    And the prompt should ask for main components
    And the prompt size should be less than 10KB
    And the expected response should be 10-20 lines

  Scenario: Round 1 produces valid architecture overview
    Given a super large file "OperateGoods.class.php"
    When I execute Round 1 with AI
    Then Round 1 should return an overview
    And the overview should describe the purpose
    And the overview should list main components
    And the overview length should be between 10 and 30 lines

  Scenario: Round 2 - Core Component Analysis prompt format
    Given Round 1 output is available
      """
      Purpose: Goods management module for CRUD and inventory
      Main Components:
      - OperateGoods: Core class
      - CRUD Operations: Create, update, delete goods
      - Inventory Management: Stock tracking
      - Price Calculation: Pricing logic
      """
    And symbols are grouped by responsibility
      | group_name             | symbol_count | top_symbols                                    |
      | CRUD Operations        | 15           | createGoods, updateGoods, deleteGoods          |
      | Inventory Management   | 20           | adjustStock, checkStock, getStockLevel         |
      | Price Calculation      | 12           | calculatePrice, applyDiscount, getPriceHistory |
      | Query Methods          | 10           | getGoodsList, getGoodsById, searchGoods        |
    When I generate Round 2 prompt
    Then the prompt should include Round 1 output
    And the prompt should include grouped symbols with top 3 per group
    And the prompt should ask for component analysis
    And the prompt should ask for method collaboration
    And the prompt size should be less than 15KB

  Scenario: Round 2 produces detailed component analysis
    Given Round 1 completed successfully
    And grouped symbols are available
    When I execute Round 2 with AI
    Then Round 2 should return component analysis
    And the analysis should describe each functional group
    And the analysis should explain key method interactions
    And the analysis length should be between 30 and 60 lines

  Scenario: Round 3 - Final README Synthesis prompt format
    Given Round 1 and Round 2 outputs are available
    And complete symbol list is available
    When I generate Round 3 prompt
    Then the prompt should include Round 1 overview
    And the prompt should include Round 2 analysis
    And the prompt should include complete symbol names
    And the prompt should specify README format requirements
    And the prompt should request markdown output
    And the prompt size should be less than 15KB

  Scenario: Round 3 produces complete README
    Given Round 1 and Round 2 completed successfully
    When I execute Round 3 with AI
    Then Round 3 should return a complete README
    And the README should be valid markdown
    And the README should have "# README_AI.md" header
    And the README should have "## Purpose" section
    And the README should have "## Architecture" section
    And the README should have "## Components" section
    And the README should have "## Methods" section
    And the README length should be greater than 100 lines

  Scenario: Fallback to standard enhancement when Round 1 fails
    Given a super large file is being processed
    When Round 1 fails with timeout error
    Then the system should log the failure
    And the system should fallback to standard AI enhancement
    And a fallback notification should be shown to user
    And a README should still be generated

  Scenario: Fallback when Round 2 fails
    Given Round 1 completed successfully
    When Round 2 fails with AI error
    Then the system should log the failure
    And the system should fallback to standard AI enhancement
    And use Round 1 output if possible
    And a fallback notification should be shown to user

  Scenario: Fallback when Round 3 fails
    Given Round 1 and Round 2 completed successfully
    When Round 3 fails with validation error
    Then the system should log the failure
    And the system should use SmartWriter as fallback
    And combine Round 1 and Round 2 outputs
    And a fallback notification should be shown to user

  Scenario: Progress indicators during multi-turn dialogue
    Given a super large file is being processed
    When multi-turn dialogue starts
    Then the CLI should display "Using multi-turn dialogue"
    When Round 1 starts
    Then the CLI should display "Round 1: Architecture Overview"
    When Round 1 completes in 30 seconds
    Then the CLI should display "✓ Round 1: Architecture Overview (30s)"
    When Round 2 starts
    Then the CLI should display "Round 2: Core Component Analysis"
    When Round 2 completes in 60 seconds
    Then the CLI should display "✓ Round 2: Core Analysis (60s)"
    When Round 3 starts
    Then the CLI should display "Round 3: Final Synthesis"
    When Round 3 completes in 45 seconds
    Then the CLI should display "✓ Round 3: Final Synthesis (45s)"

  Scenario: Total time tracking for multi-turn dialogue
    Given a super large file is being processed
    When multi-turn dialogue completes successfully
    Then the total time should be logged
    And the time per round should be logged
    And the user should see total enhancement time

  Scenario: Multi-turn dialogue with timeout per round
    Given each round has a 180 second timeout
    And a super large file is being processed
    When Round 2 takes longer than 180 seconds
    Then Round 2 should be terminated
    And a timeout error should be raised
    And the fallback mechanism should be triggered
