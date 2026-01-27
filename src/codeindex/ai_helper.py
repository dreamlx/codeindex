"""AI enhancement helper functions (Epic 4 Story 4.1).

This module provides reusable functions for AI enhancement operations,
eliminating code duplication in scan and scan-all commands.
"""

from pathlib import Path

from codeindex.config import Config
from codeindex.parser import ParseResult
from codeindex.writer import WriteResult


def aggregate_parse_results(
    parse_results: list[ParseResult],
    path: Path,
) -> ParseResult:
    """Aggregate multiple parse results into one.

    Combines symbols and line counts from multiple parse results into a single
    ParseResult. This is useful for analyzing multi-file directories.

    Args:
        parse_results: List of parse results to aggregate
        path: Path for the aggregated result

    Returns:
        ParseResult with combined symbols and total line count

    Example:
        >>> pr1 = ParseResult(Path("a.py"), file_lines=100, symbols=[...])
        >>> pr2 = ParseResult(Path("b.py"), file_lines=200, symbols=[...])
        >>> aggregated = aggregate_parse_results([pr1, pr2], Path("dir"))
        >>> aggregated.file_lines
        300
    """
    all_symbols = []
    total_lines = 0

    for pr in parse_results:
        all_symbols.extend(pr.symbols)
        total_lines += pr.file_lines

    return ParseResult(
        path=path,
        file_lines=total_lines,
        symbols=all_symbols,
    )


def execute_multi_turn_enhancement(
    dir_path: Path,
    parse_results: list[ParseResult],
    config: Config,
    timeout: int,
    strategy: str = "auto",
    quiet: bool = False,
) -> tuple[bool, WriteResult | None, str]:
    """Execute multi-turn dialogue enhancement with auto-detection and fallback.

    This function provides a unified interface for multi-turn dialogue enhancement,
    handling detection, execution, and fallback logic. It eliminates code duplication
    between scan and scan-all commands.

    Args:
        dir_path: Directory path for the enhancement
        parse_results: List of parse results to aggregate
        config: Configuration
        timeout: Timeout per round in seconds
        strategy: Enhancement strategy - "auto", "standard", or "multi_turn"
            - "auto": Auto-detect super large files and use multi-turn if needed
            - "multi_turn": Force multi-turn dialogue regardless of file size
            - "standard": Skip multi-turn (returns failure, caller uses standard)
        quiet: Suppress progress output

    Returns:
        Tuple of (success, write_result, message):
        - success: True if multi-turn enhancement succeeded
        - write_result: WriteResult if success, None otherwise
        - message: Status message for logging
            - On success: "Multi-turn complete (X.Xs)"
            - On failure: "Multi-turn not applicable or failed"

    Example:
        >>> success, result, msg = execute_multi_turn_enhancement(
        ...     Path("./src"),
        ...     parse_results,
        ...     config,
        ...     timeout=180,
        ...     strategy="auto"
        ... )
        >>> if success:
        ...     print(f"Success: {result.path}")
        ... else:
        ...     # Fall back to standard enhancement
        ...     print(f"Fallback needed: {msg}")
    """
    from codeindex.ai_enhancement import is_super_large_file, multi_turn_ai_enhancement
    from codeindex.writer import write_readme

    # Step 1: Aggregate parse results
    aggregated = aggregate_parse_results(parse_results, dir_path)

    # Step 2: Determine if multi-turn should be used
    actual_strategy = strategy

    if strategy == "auto":
        # Auto-detect super large files
        detection = is_super_large_file(aggregated, config)
        if detection.is_super_large:
            actual_strategy = "multi_turn"
            if not quiet:
                print(f"  ⚠ Super large file detected: {detection.reason}")
                print("  → Using multi-turn dialogue strategy...")
        else:
            # Not super large, skip multi-turn
            return False, None, "Multi-turn not applicable or failed"
    elif strategy == "standard":
        # Explicitly skip multi-turn
        return False, None, "Multi-turn not applicable or failed"

    # Step 3: Execute multi-turn dialogue
    if actual_strategy == "multi_turn":
        if not quiet:
            print("  → Starting multi-turn dialogue...")

        result = multi_turn_ai_enhancement(
            parse_result=aggregated,
            config=config,
            ai_command=config.ai_command,
            timeout_per_round=timeout,
        )

        if result.success:
            # Step 4: Write README
            write_result = write_readme(dir_path, result.final_readme, config.output_file)

            if write_result.success:
                time_str = f"{result.total_time:.1f}s"
                message = f"Multi-turn complete ({time_str})"
                return True, write_result, message
            else:
                # Write failed
                return False, None, f"Write failed: {write_result.error}"

        # Multi-turn failed
        return False, None, "Multi-turn not applicable or failed"

    # Should not reach here
    return False, None, "Multi-turn not applicable or failed"
