"""CLI commands for technical debt analysis.

This module provides the tech-debt command for analyzing technical debt
in a directory, including file size issues, god classes, and symbol overload.
"""

from pathlib import Path

import click

from .cli_common import console
from .config import Config
from .symbol_scorer import ScoringContext, SymbolImportanceScorer
from .tech_debt import TechDebtDetector, TechDebtReport, TechDebtReporter
from .tech_debt_formatters import ConsoleFormatter, JSONFormatter, MarkdownFormatter


def _find_source_files(
    path: Path, recursive: bool, languages: list[str] | None = None
) -> list[Path]:
    """Find source files in the given directory based on language configuration.

    Args:
        path: Directory path to search
        recursive: If True, search subdirectories recursively
        languages: List of languages to include (optional, uses config if None)

    Returns:
        List of source file paths
    """
    # Load languages from config if not provided
    if languages is None:
        config = Config.load()
        languages = config.languages

    # Map languages to file extensions
    extensions = {
        'python': '*.py',
        'php': '*.php',
        'javascript': '*.js',
        'typescript': '*.ts',
        'java': '*.java',
        'go': '*.go',
        'rust': '*.rs',
        'cpp': '*.cpp',
        'c': '*.c',
    }

    files = []
    for lang in languages:
        ext = extensions.get(lang)
        if ext:
            if recursive:
                files.extend([f for f in path.rglob(ext) if f.is_file()])
            else:
                files.extend([f for f in path.glob(ext) if f.is_file()])

    return files


def _analyze_files(
    files: list[Path],
    detector: TechDebtDetector,
    reporter: TechDebtReporter,
    show_progress: bool,
) -> None:
    """Analyze files and add results to reporter.

    Args:
        files: List of source files to analyze
        detector: Technical debt detector instance
        reporter: Reporter to collect results
        show_progress: Whether to show progress messages
    """
    from .parser import parse_file

    for file_path in files:
        try:
            # Parse file
            parse_result = parse_file(file_path)

            if parse_result.error:
                if show_progress:
                    console.print(
                        f"[yellow]⚠ Skipping {file_path.name}: {parse_result.error}[/yellow]"
                    )
                continue

            # Determine file type based on extension
            file_ext = file_path.suffix.lower()
            if file_ext == '.py':
                file_type = 'python'
            elif file_ext == '.php':
                file_type = 'php'
            elif file_ext == '.js':
                file_type = 'javascript'
            elif file_ext == '.ts':
                file_type = 'typescript'
            else:
                file_type = file_ext[1:] if file_ext else 'unknown'

            # Create scorer context
            scoring_context = ScoringContext(
                framework=None,
                file_type=file_type,
                total_symbols=len(parse_result.symbols),
            )
            scorer = SymbolImportanceScorer(scoring_context)

            # Detect technical debt
            debt_analysis = detector.analyze_file(parse_result, scorer)

            # Analyze symbol overload
            symbol_issues, symbol_analysis = detector.analyze_symbol_overload(
                parse_result, scorer
            )

            # Merge symbol overload issues into debt analysis
            debt_analysis.issues.extend(symbol_issues)

            # Add to reporter
            reporter.add_file_result(
                file_path=file_path,
                debt_analysis=debt_analysis,
                symbol_analysis=symbol_analysis,
            )

        except Exception as e:
            if show_progress:
                console.print(f"[red]✗ Error analyzing {file_path.name}: {e}[/red]")
            continue


def _format_and_output(
    report: TechDebtReport,
    format: str,
    output: Path | None,
    quiet: bool,
) -> None:
    """Format and output the technical debt report.

    Args:
        report: Technical debt report to format
        format: Output format (console, markdown, or json)
        output: Optional output file path
        quiet: Whether to suppress status messages
    """
    # Select formatter
    if format == "console":
        formatter = ConsoleFormatter()
    elif format == "markdown":
        formatter = MarkdownFormatter()
    else:  # json
        formatter = JSONFormatter()

    formatted_output = formatter.format(report)

    # Write output
    if output:
        output.write_text(formatted_output)
        if not quiet:
            console.print(f"[green]✓ Report written to {output}[/green]")
    else:
        # Print to stdout
        print(formatted_output)


@click.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--format",
    type=click.Choice(["console", "markdown", "json"], case_sensitive=False),
    default="console",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write output to file instead of stdout",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively scan subdirectories",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Minimal output",
)
def tech_debt(path: Path, format: str, output: Path | None, recursive: bool, quiet: bool):
    """Analyze technical debt in a directory.

    Scans source files for technical debt issues including:
    - Super large files (>5000 lines)
    - Large files (>2000 lines)
    - God Classes (>50 methods)
    - Massive symbol count (>100 symbols)
    - High noise ratio (>50% low-quality symbols)

    Results can be output in console, markdown, or JSON format.
    """
    try:
        # Load config
        config = Config.load()

        # Initialize detector and reporter
        detector = TechDebtDetector(config)
        reporter = TechDebtReporter()

        # Find all source files to analyze
        files_to_analyze = _find_source_files(path, recursive)

        # Handle empty directory
        if not files_to_analyze:
            report = reporter.generate_report()
            _format_and_output(report, format, output, quiet)
            return

        # Only show progress if not JSON to stdout (JSON needs clean output)
        show_progress = not quiet and not (format == "json" and output is None)

        if show_progress:
            console.print(f"[dim]Analyzing {len(files_to_analyze)} source files...[/dim]")

        # Parse and analyze each file
        _analyze_files(files_to_analyze, detector, reporter, show_progress)

        # Generate and output report
        report = reporter.generate_report()
        _format_and_output(report, format, output, quiet)

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise click.Abort()
