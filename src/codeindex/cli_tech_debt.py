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
    # Some languages have multiple extensions (e.g., objc: .h and .m)
    extensions = {
        'python': ['*.py'],
        'php': ['*.php'],
        'javascript': ['*.js'],
        'typescript': ['*.ts'],
        'java': ['*.java'],
        'go': ['*.go'],
        'rust': ['*.rs'],
        'cpp': ['*.cpp'],
        'c': ['*.c'],
        'swift': ['*.swift'],
        'objc': ['*.h', '*.m'],  # Objective-C has header and implementation files
    }

    files = []
    for lang in languages:
        ext_patterns = extensions.get(lang, [])
        # Handle both single pattern (old format) and list of patterns
        if isinstance(ext_patterns, str):
            ext_patterns = [ext_patterns]

        for ext in ext_patterns:
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
) -> list[dict]:
    """Analyze files for technical debt and test smells.

    Args:
        files: List of source files to analyze
        detector: Technical debt detector instance
        reporter: Reporter to collect results
        show_progress: Whether to show progress messages

    Returns:
        List of test smell dictionaries
    """
    from .parser import parse_file
    from .test_smells import TestSmellDetector

    test_smell_detector = TestSmellDetector()
    test_smells_data = []

    for file_path in files:
        try:
            parse_result = parse_file(file_path)

            if parse_result.error:
                _handle_parse_error(file_path, parse_result.error, show_progress)
                continue

            # Analyze single file and collect test smells
            file_test_smells = _analyze_single_file(
                file_path, parse_result, detector, reporter, test_smell_detector
            )
            test_smells_data.extend(file_test_smells)

        except Exception as e:
            _handle_analysis_error(file_path, e, show_progress)
            continue

    return test_smells_data


def _get_file_type(file_path: Path) -> str:
    """Determine file type from extension."""
    file_ext = file_path.suffix.lower()
    if file_ext == '.py':
        return 'python'
    elif file_ext == '.php':
        return 'php'
    elif file_ext == '.js':
        return 'javascript'
    elif file_ext == '.ts':
        return 'typescript'
    elif file_ext in ('.h', '.m'):
        return 'objc'
    elif file_ext == '.swift':
        return 'swift'
    else:
        return file_ext[1:] if file_ext else 'unknown'


def _create_scorer(parse_result, file_type: str) -> SymbolImportanceScorer:
    """Create symbol importance scorer for file."""
    scoring_context = ScoringContext(
        framework=None,
        file_type=file_type,
        total_symbols=len(parse_result.symbols),
    )
    return SymbolImportanceScorer(scoring_context)


def _analyze_single_file(
    file_path: Path,
    parse_result,
    detector: TechDebtDetector,
    reporter: TechDebtReporter,
    test_smell_detector,
) -> list[dict]:
    """Analyze single file for technical debt and test smells."""
    # Get file type and create scorer
    file_type = _get_file_type(file_path)
    scorer = _create_scorer(parse_result, file_type)

    # Detect technical debt
    debt_analysis = detector.analyze_file(parse_result, scorer)

    # Analyze symbol overload
    symbol_issues, symbol_analysis = detector.analyze_symbol_overload(
        parse_result, scorer
    )
    debt_analysis.issues.extend(symbol_issues)

    # Add to reporter
    reporter.add_file_result(
        file_path=file_path,
        debt_analysis=debt_analysis,
        symbol_analysis=symbol_analysis,
    )

    # Detect and format test smells
    return _collect_test_smells(file_path, parse_result, test_smell_detector)


def _collect_test_smells(file_path: Path, parse_result, test_smell_detector) -> list[dict]:
    """Detect and format test smells for a file."""
    test_smells = test_smell_detector.analyze_test_file(file_path, parse_result)
    test_smells_data = []

    if test_smells:
        for smell in test_smells:
            # Use absolute path if relative_to fails
            try:
                rel_path = smell.file_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = smell.file_path

            test_smells_data.append({
                "path": str(rel_path),
                "type": smell.type.value,
                "details": smell.details,
                "line_number": smell.line_number,
                "metric_value": smell.metric_value,
            })

    return test_smells_data


def _handle_parse_error(file_path: Path, error: str, show_progress: bool):
    """Handle parse errors during file analysis."""
    if show_progress:
        console.print(
            f"[yellow]⚠ Skipping {file_path.name}: {error}[/yellow]"
        )


def _handle_analysis_error(file_path: Path, error: Exception, show_progress: bool):
    """Handle analysis errors during file processing."""
    if show_progress:
        console.print(f"[red]✗ Error analyzing {file_path.name}: {error}[/red]")


def _format_and_output(
    report: TechDebtReport,
    format: str,
    output: Path | None,
    quiet: bool,
    test_smells: list[dict] | None = None,
    target_path: Path | None = None,
) -> None:
    """Format and output the technical debt report.

    Args:
        report: Technical debt report to format
        format: Output format (console, markdown, or json)
        output: Optional output file path
        quiet: Whether to suppress status messages
        test_smells: Optional list of test smell dictionaries (new in v0.22.0)
        target_path: Target path that was analyzed (new in v0.22.1)
    """
    # Select formatter
    if format == "console":
        formatter = ConsoleFormatter()
    elif format == "markdown":
        formatter = MarkdownFormatter()
    else:  # json
        formatter = JSONFormatter()

    # Pass test_smells and target_path to formatter (backward compatible)
    if format == "json":
        formatted_output = formatter.format(
            report,
            test_smells=test_smells,
            target_path=str(target_path.absolute()) if target_path else None,
        )
    else:
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
    """Analyze technical debt and code quality in a directory.

    Scans source files for technical debt issues including:
    - Super large files (>5000 lines)
    - Large files (>2000 lines)
    - God Classes (>50 methods)
    - Massive symbol count (>100 symbols)
    - High noise ratio (>50% low-quality symbols)
    - Test smells (skipped tests, giant test files) [v0.22.0+]

    Results can be output in console, markdown, or JSON format.
    """
    try:
        # Load config
        config = Config.load()

        # Auto-enable recursive for Java projects (deep package structures)
        has_java = "java" in (config.languages or [])
        if has_java and not recursive:
            recursive = True

        # Initialize detector and reporter
        detector = TechDebtDetector(config)
        reporter = TechDebtReporter()

        # Find all source files to analyze
        files_to_analyze = _find_source_files(path, recursive)

        # Handle empty directory
        if not files_to_analyze:
            report = reporter.generate_report()
            _format_and_output(report, format, output, quiet, test_smells=[], target_path=path)
            return

        # Only show progress if not JSON to stdout (JSON needs clean output)
        show_progress = not quiet and not (format == "json" and output is None)

        if show_progress:
            console.print(f"[dim]Analyzing {len(files_to_analyze)} source files...[/dim]")

        # Parse and analyze each file (now returns test_smells)
        test_smells = _analyze_files(files_to_analyze, detector, reporter, show_progress)

        # Generate and output report
        report = reporter.generate_report()
        _format_and_output(
            report, format, output, quiet, test_smells=test_smells, target_path=path
        )

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise click.Abort()
