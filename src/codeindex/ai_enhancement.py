"""AI enhancement strategies for super large files (Epic 3.2).

This module provides intelligent file size detection and strategy selection
for optimizing AI-powered documentation generation.
"""

from dataclasses import dataclass
from typing import Literal

from codeindex.config import Config
from codeindex.parser import ParseResult

EnhancementStrategy = Literal["standard", "hierarchical", "multi_turn"]


@dataclass
class SuperLargeFileDetection:
    """Result of super large file detection."""

    is_super_large: bool
    reason: str | None  # "excessive_lines", "excessive_symbols", or combination
    recommended_strategy: EnhancementStrategy
    file_lines: int
    symbol_count: int


def is_super_large_file(parse_result: ParseResult, config: Config) -> SuperLargeFileDetection:
    """Detect if a file is super large and needs multi-turn dialogue.

    Uses unified FileSizeClassifier for consistent detection (Epic 4 refactoring).

    A file is considered super large if:
    - Lines > super_large_lines threshold (default 5000), OR
    - Symbols > super_large_symbols threshold (default 100)

    Args:
        parse_result: Parsed file data with symbols and line count
        config: Configuration with super_large thresholds

    Returns:
        SuperLargeFileDetection with detection result and recommended strategy
    """
    from codeindex.file_classifier import FileSizeCategory, FileSizeClassifier

    # Use FileSizeClassifier for unified detection (Epic 4 Story 4.2)
    classifier = FileSizeClassifier(config)
    analysis = classifier.classify(parse_result)

    # Determine if super large
    is_super_large = analysis.category == FileSizeCategory.SUPER_LARGE

    # Determine strategy based on category
    if analysis.category == FileSizeCategory.SUPER_LARGE:
        recommended_strategy = "multi_turn"
    elif analysis.category == FileSizeCategory.LARGE:
        recommended_strategy = "hierarchical"
    else:
        recommended_strategy = "standard"

    return SuperLargeFileDetection(
        is_super_large=is_super_large,
        reason=analysis.reason,
        recommended_strategy=recommended_strategy,
        file_lines=analysis.file_lines,
        symbol_count=analysis.symbol_count,
    )


def select_enhancement_strategy(
    parse_result: ParseResult,
    config: Config,
) -> EnhancementStrategy:
    """Select appropriate AI enhancement strategy based on file size.

    Strategy selection:
    - Super large (>5000 lines OR >100 symbols): multi_turn
    - Large (>2000 lines OR >40 symbols): hierarchical
    - Normal: standard

    Args:
        parse_result: Parsed file data
        config: Configuration with thresholds

    Returns:
        Enhancement strategy: "standard", "hierarchical", or "multi_turn"
    """
    detection = is_super_large_file(parse_result, config)
    return detection.recommended_strategy


# ============================================================================
# Multi-turn Dialogue Implementation (Story 3.2.2)
# ============================================================================


@dataclass
class SymbolGroup:
    """Group of symbols by responsibility."""

    name: str  # Group name (e.g., "CRUD Operations")
    description: str  # What this group does
    symbols: list  # Symbol objects in this group
    top_symbols: list[str]  # Top N symbol names for display


@dataclass
class MultiTurnResult:
    """Result of multi-turn dialogue enhancement."""

    success: bool
    final_readme: str | None
    rounds_completed: list[str]  # ["round1", "round2", "round3"]
    error: str | None
    round_outputs: dict[str, str]  # {"round1": "...", "round2": "...", "round3": "..."}
    total_time: float  # Total seconds taken
    fallback_used: bool  # Whether fallback was triggered


def _group_symbols_by_responsibility(parse_result: ParseResult) -> list[SymbolGroup]:
    """Group symbols by functional responsibility using naming patterns.

    Groups symbols into categories like:
    - CRUD Operations: create*, update*, delete*, save*, remove*
    - Query Methods: get*, find*, search*, list*, fetch*
    - Validation: validate*, check*, verify*, is*, has*
    - Utility: format*, parse*, convert*, transform*
    - Other: Everything else

    Args:
        parse_result: Parsed file with symbols

    Returns:
        List of SymbolGroups with symbols organized by responsibility
    """
    groups_map = {
        "CRUD Operations": {
            "patterns": ["create", "update", "delete", "save", "remove", "insert", "add"],
            "description": "Create, update, and delete operations",
            "symbols": [],
        },
        "Query Methods": {
            "patterns": ["get", "find", "search", "list", "fetch", "query", "select"],
            "description": "Data retrieval and querying",
            "symbols": [],
        },
        "Validation": {
            "patterns": ["validate", "check", "verify", "is", "has", "ensure"],
            "description": "Data validation and checking",
            "symbols": [],
        },
        "Calculation": {
            "patterns": ["calculate", "compute", "sum", "count", "total", "average"],
            "description": "Calculations and computations",
            "symbols": [],
        },
        "Utility": {
            "patterns": ["format", "parse", "convert", "transform", "build", "generate"],
            "description": "Utility and helper functions",
            "symbols": [],
        },
    }

    # Categorize symbols
    uncategorized = []
    for symbol in parse_result.symbols:
        name_lower = symbol.name.lower()
        categorized = False

        for group_name, group_info in groups_map.items():
            for pattern in group_info["patterns"]:
                if name_lower.startswith(pattern):
                    group_info["symbols"].append(symbol)
                    categorized = True
                    break
            if categorized:
                break

        if not categorized:
            uncategorized.append(symbol)

    # Add "Other" group for uncategorized symbols
    if uncategorized:
        groups_map["Other"] = {
            "description": "Other methods and functions",
            "symbols": uncategorized,
        }

    # Build SymbolGroup objects (only non-empty groups)
    result = []
    for group_name, group_info in groups_map.items():
        if group_info["symbols"]:
            # Get top 3 symbols by name
            top_symbols = [s.name for s in group_info["symbols"][:3]]
            result.append(
                SymbolGroup(
                    name=group_name,
                    description=group_info["description"],
                    symbols=group_info["symbols"],
                    top_symbols=top_symbols,
                )
            )

    return result


def _generate_round1_prompt(parse_result: ParseResult) -> str:
    """Generate Round 1 prompt: Architecture Overview.

    Prompt includes:
    - File statistics (lines, symbol count)
    - Top 5 symbol names
    - Questions about purpose and main components

    Target: <10KB prompt, 10-20 line response

    Args:
        parse_result: Parsed file data

    Returns:
        Round 1 prompt string
    """
    file_path = parse_result.path
    file_lines = parse_result.file_lines
    symbol_count = len(parse_result.symbols)

    # Get top 5 symbols by importance (just by position for now)
    top_symbols = parse_result.symbols[:5]
    symbol_names = [s.name for s in top_symbols]

    prompt = f"""# Round 1: Architecture Overview

You are analyzing a super large file that needs multi-turn dialogue for documentation.

## File Statistics
- Path: {file_path}
- Lines: {file_lines}
- Total Symbols: {symbol_count}

## Top Symbols
{chr(10).join(f'- {name}' for name in symbol_names)}

## Task
Provide a brief architecture overview (10-20 lines) covering:

1. **Purpose**: What is this file's main responsibility?
2. **Main Components**: What are the 3-5 major functional areas?

Keep it concise and high-level. We'll dive deeper in the next rounds."""

    return prompt


def _generate_round2_prompt(
    round1_output: str,
    symbol_groups: list[SymbolGroup],
) -> str:
    """Generate Round 2 prompt: Core Component Analysis.

    Prompt includes:
    - Round 1 architecture overview
    - Grouped symbols (top 3 per group)
    - Questions about component details and interactions

    Target: <15KB prompt, 30-60 line response

    Args:
        round1_output: Output from Round 1
        symbol_groups: Symbols grouped by responsibility

    Returns:
        Round 2 prompt string
    """
    # Format grouped symbols
    groups_text = []
    for group in symbol_groups:
        top_3 = ", ".join(group.top_symbols)
        groups_text.append(
            f"- **{group.name}** ({len(group.symbols)} symbols): {top_3}"
        )

    prompt = f"""# Round 2: Core Component Analysis

## Round 1 Overview
{round1_output}

## Symbol Groups
{chr(10).join(groups_text)}

## Task
Provide detailed component analysis (30-60 lines) covering:

1. **Each Functional Group**: Describe what each group does
2. **Key Method Interactions**: How do methods collaborate?
3. **Data Flow**: How does data move through components?

Be specific but concise. We'll synthesize everything in Round 3."""

    return prompt


def _generate_round3_prompt(
    round1_output: str,
    round2_output: str,
    parse_result: ParseResult,
) -> str:
    """Generate Round 3 prompt: Final README Synthesis.

    Prompt includes:
    - Round 1 overview
    - Round 2 analysis
    - Complete symbol list
    - README format requirements

    Target: <15KB prompt, 100+ line README

    Args:
        round1_output: Output from Round 1
        round2_output: Output from Round 2
        parse_result: Parsed file data with all symbols

    Returns:
        Round 3 prompt string
    """
    # Get all symbol names
    all_symbols = [s.name for s in parse_result.symbols]

    # Limit symbol list if too long (keep prompt under 15KB)
    if len(all_symbols) > 50:
        symbol_list = ", ".join(all_symbols[:50]) + f" ... (+{len(all_symbols) - 50} more)"
    else:
        symbol_list = ", ".join(all_symbols)

    prompt = f"""# Round 3: Final README Synthesis

## Round 1: Architecture Overview
{round1_output}

## Round 2: Component Analysis
{round2_output}

## All Symbols
{symbol_list}

## Task
Generate a complete README_AI.md (100+ lines) with these sections:

# README_AI.md - {parse_result.path.name}

## Purpose
[Based on Round 1]

## Architecture
[Based on Round 1 and Round 2]

## Components
[Detailed breakdown from Round 2]

## Methods
[Key methods with brief descriptions]

Use markdown format. Be comprehensive but well-organized."""

    return prompt


def multi_turn_ai_enhancement(
    parse_result: ParseResult,
    config: Config,
    ai_command: str,
    timeout_per_round: int = 180,
) -> MultiTurnResult:
    """Execute three-round dialogue for super large file documentation.

    Round 1: Architecture Overview (10KB, 10-20 lines)
    Round 2: Core Component Analysis (15KB, 30-60 lines)
    Round 3: Final README Synthesis (15KB, 100+ lines)

    Falls back to standard AI enhancement if any round fails.

    Args:
        parse_result: Parsed file data
        config: Configuration
        ai_command: AI CLI command template
        timeout_per_round: Timeout in seconds per round (default: 180s/3min)

    Returns:
        MultiTurnResult with final README or error
    """
    import time

    from codeindex.invoker import invoke_ai_cli

    start_time = time.time()
    rounds_completed = []
    round_outputs = {}

    try:
        # Round 1: Architecture Overview
        print("🔄 Round 1: Architecture Overview...")
        round1_prompt = _generate_round1_prompt(parse_result)
        round1_start = time.time()

        round1_result = invoke_ai_cli(ai_command, round1_prompt, timeout=timeout_per_round)
        round1_duration = time.time() - round1_start

        if not round1_result.success:
            raise Exception(f"Round 1 failed: {round1_result.error}")

        round1_output = round1_result.output.strip()
        rounds_completed.append("round1")
        round_outputs["round1"] = round1_output
        print(f"✓ Round 1 complete ({round1_duration:.1f}s)")

        # Round 2: Core Component Analysis
        print("🔄 Round 2: Core Component Analysis...")
        symbol_groups = _group_symbols_by_responsibility(parse_result)
        round2_prompt = _generate_round2_prompt(round1_output, symbol_groups)
        round2_start = time.time()

        round2_result = invoke_ai_cli(ai_command, round2_prompt, timeout=timeout_per_round)
        round2_duration = time.time() - round2_start

        if not round2_result.success:
            raise Exception(f"Round 2 failed: {round2_result.error}")

        round2_output = round2_result.output.strip()
        rounds_completed.append("round2")
        round_outputs["round2"] = round2_output
        print(f"✓ Round 2 complete ({round2_duration:.1f}s)")

        # Round 3: Final README Synthesis
        print("🔄 Round 3: Final README Synthesis...")
        round3_prompt = _generate_round3_prompt(round1_output, round2_output, parse_result)
        round3_start = time.time()

        round3_result = invoke_ai_cli(ai_command, round3_prompt, timeout=timeout_per_round)
        round3_duration = time.time() - round3_start

        if not round3_result.success:
            raise Exception(f"Round 3 failed: {round3_result.error}")

        final_readme = round3_result.output.strip()
        rounds_completed.append("round3")
        round_outputs["round3"] = final_readme
        print(f"✓ Round 3 complete ({round3_duration:.1f}s)")

        total_time = time.time() - start_time
        print(f"✅ Multi-turn dialogue complete! Total time: {total_time:.1f}s")

        return MultiTurnResult(
            success=True,
            final_readme=final_readme,
            rounds_completed=rounds_completed,
            error=None,
            round_outputs=round_outputs,
            total_time=total_time,
            fallback_used=False,
        )

    except Exception as e:
        # Fallback to standard AI enhancement
        print(f"⚠️  Multi-turn dialogue failed: {e}")
        print("🔄 Falling back to standard AI enhancement...")

        # TODO: Call standard AI enhancement here
        # For now, return failure
        total_time = time.time() - start_time

        return MultiTurnResult(
            success=False,
            final_readme=None,
            rounds_completed=rounds_completed,
            error=str(e),
            round_outputs=round_outputs,
            total_time=total_time,
            fallback_used=True,
        )
