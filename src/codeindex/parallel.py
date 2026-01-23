"""Parallel processing utilities for codeindex."""

import concurrent.futures
from dataclasses import dataclass
from pathlib import Path
from typing import List

from rich.console import Console

from .config import Config
from .parser import ParseResult, parse_file
from .scanner import scan_directory

console = Console()


@dataclass
class BatchResult:
    """Result of processing a batch of files."""
    parse_results: List[ParseResult]
    success_count: int
    error_count: int


def parse_files_parallel(
    files: List[Path],
    config: Config,
    quiet: bool = False
) -> list[ParseResult]:
    """
    Parse files using multiple workers in parallel.

    Args:
        files: List of files to parse
        config: Configuration object
        quiet: Whether to suppress output

    Returns:
        List of parse results (same order as input)
    """
    if not files:
        return []

    if config.parallel_workers <= 1 or len(files) < config.batch_size:
        # Use sequential processing for small jobs or single worker
        if not quiet:
            console.print(f"  [dim]→ Parsing {len(files)} files sequentially...[/dim]")
        return [parse_file(f) for f in files]

    # Process files in parallel
    if not quiet:
        console.print(
            f"  [dim]→ Parsing {len(files)} files with {config.parallel_workers} workers...[/dim]"
        )

    parse_results = [None] * len(files)  # Pre-allocate to maintain order

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(parse_file, file): i
            for i, file in enumerate(files)
        }

        # Process results as they complete
        completed = 0
        errors = 0

        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                parse_results[index] = result
                if result.error:
                    errors += 1
            except Exception as e:
                # Create error result
                error_result = ParseResult(
                    path=files[index],
                    error=f"Processing error: {str(e)}"
                )
                parse_results[index] = error_result
                errors += 1

            completed += 1
            if not quiet and completed % 10 == 0:
                console.print(f"  [dim]→ Processed {completed}/{len(files)} files...[/dim]")

    if not quiet:
        success = len(files) - errors
        console.print(f"  [dim]→ Parsed {success} files successfully, {errors} errors[/dim]")

    return parse_results


def scan_directories_parallel(
    directories: List[Path],
    config: Config,
    quiet: bool = False
) -> List[Path]:
    """
    Scan multiple directories in parallel for batch processing.

    Args:
        directories: List of directories to process
        config: Configuration object
        quiet: Whether to suppress output

    Returns:
        List of results for each directory
    """
    if not directories:
        return []

    if config.parallel_workers <= 1 or len(directories) == 1:
        # Sequential processing
        return [scan_directory(d, config, d.parent) for d in directories]

    if not quiet:
        console.print(
            f"  [dim]→ Processing {len(directories)} directories in parallel...[/dim]"
        )

    # Use ThreadPoolExecutor for I/O bound directory scanning
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
        futures = {
            executor.submit(scan_directory, d, config, d.parent): d
            for d in directories
        }

        results = []
        completed = 0

        for future in concurrent.futures.as_completed(futures):
            dir_path = futures[future]
            try:
                result = future.result()
                results.append(result)
                if not quiet and len(result.files) > 0:
                    console.print(
                        f"  [dim]→ Found {len(result.files)} files in {dir_path.name}[/dim]"
                    )
            except Exception as e:
                if not quiet:
                    console.print(f"  [yellow]⚠ Error scanning {dir_path.name}: {e}[/yellow]")

            completed += 1
            if not quiet and completed % 5 == 0:
                console.print(
                    f"  [dim]→ Processed {completed}/{len(directories)} "
                    f"directories...[/dim]"
                )

    return results
