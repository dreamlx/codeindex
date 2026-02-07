"""CLI parse command - Parse a single source file and output JSON.

Epic 12, Story 12.1: Single File Parse Command
This module provides the 'parse' command for parsing individual source files
and outputting structured JSON data for downstream tools like LoomGraph.
"""

import json
import sys
from pathlib import Path

import click

from .parser import FILE_EXTENSIONS, ParseResult, parse_file


@click.command()
@click.argument("file_path", type=click.Path(exists=False))
def parse(file_path: str):
    """Parse a single source file and output JSON.

    FILE_PATH: Path to the source file to parse (Python, PHP, Java)

    Outputs JSON to stdout with the following structure:
    {
        "file_path": "path/to/file.py",
        "language": "python",
        "symbols": [...],
        "imports": [...],
        "namespace": "",
        "error": null
    }

    Exit codes:
        0: Success
        1: File not found or permission denied
        2: Unsupported language
        3: Parse error
    """
    # Convert to Path
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        click.echo(
            json.dumps({"error": f"File not found: {file_path}"}),
            err=True
        )
        sys.exit(1)

    # Check file is readable
    if not path.is_file():
        click.echo(
            json.dumps({"error": f"Not a file: {file_path}"}),
            err=True
        )
        sys.exit(1)

    # Detect language
    suffix = path.suffix.lower()
    language = FILE_EXTENSIONS.get(suffix)

    if not language:
        supported = ", ".join(FILE_EXTENSIONS.keys())
        click.echo(
            json.dumps({
                "error": f"Unsupported language. File extension '{suffix}' "
                         f"not recognized. Supported: {supported}"
            }),
            err=True
        )
        sys.exit(2)

    # Parse file
    try:
        result: ParseResult = parse_file(path, language=language)
    except PermissionError:
        click.echo(
            json.dumps({"error": f"Permission denied: {file_path}"}),
            err=True
        )
        sys.exit(1)
    except Exception as e:
        click.echo(
            json.dumps({"error": f"Failed to parse file: {str(e)}"}),
            err=True
        )
        sys.exit(3)

    # Check for parse errors
    if result.error:
        # tree-sitter may partially parse, so we output the result with error field
        # Exit 0 to allow downstream tools to handle partial results
        pass

    # Build output JSON
    output = {
        "file_path": str(result.path),
        "language": language,
        "symbols": [s.to_dict() for s in result.symbols],
        "imports": [i.to_dict() for i in result.imports],
        "namespace": result.namespace,
        "error": result.error,
    }

    # Output JSON to stdout
    click.echo(json.dumps(output, ensure_ascii=False, indent=2))
