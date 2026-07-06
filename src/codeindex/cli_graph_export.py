"""CLI graph-export command — write-once graph artifact for loomgraph (GH #102).

Standalone (Path A): does its own clean whole-tree parse and dumps a
write-once NDJSON graph. Does not touch scan-all / README render.
See ``codeindex.graph_export`` and ADR-007.
"""

from pathlib import Path

import click

from .cli_common import console
from .config import Config
from .graph_export import build_export, dump_ndjson, walk_and_parse


@click.command(name="graph-export")
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    help="Project root to export (default: current directory).",
)
@click.option(
    "--output",
    "-o",
    default="graph-export.ndjson",
    help="Output NDJSON path, or '-' for stdout (default: graph-export.ndjson).",
)
@click.option("--quiet", "-q", is_flag=True, help="Minimal output.")
def graph_export(root: Path, output: str, quiet: bool):
    """Export the code graph (entities + CALLS/INHERITS edges) as write-once NDJSON.

    EXPERIMENTAL (schema_version 0): the contract with loomgraph per ADR-007.
    Each edge carries a resolution_qualifier (resolved / ambiguous / unresolved)
    so a consumer never mistakes an unresolved edge for a real one.
    """
    config_path = root / ".codeindex.yaml"
    config = Config.load(config_path if config_path.exists() else None)

    buffer = walk_and_parse(root, config)
    model = build_export(buffer, root)

    # GH #93: 0 entities signals a languages mismatch (analogous to scan-all's
    # GH #105 ``with_files == 0`` guard). Surface the hint instead of silently
    # emitting an empty graph — loomgraph consumes this output and would
    # otherwise import 0 entities with ``success:true``. To **stderr**: ``-o -``
    # streams NDJSON on stdout and a warning there would corrupt the contract.
    if not quiet and not model.entities:
        from .scanner import language_mismatch_hint

        hint = language_mismatch_hint(root, config)
        if hint:
            click.echo(f"WARNING: {hint}", err=True)

    text = dump_ndjson(model)

    if output == "-":
        click.echo(text, nl=False)
        return

    out_path = Path(output)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.write_text(text, encoding="utf-8")

    if not quiet:
        n_amb = sum(
            1 for e in model.edges if e.resolution_qualifier == "ambiguous"
        )
        n_unres = sum(
            1 for e in model.edges if e.resolution_qualifier == "unresolved"
        )
        console.print(
            f"[green]✓[/green] graph-export → {out_path} "
            f"[dim]({len(model.entities)} entities, {len(model.edges)} edges; "
            f"{n_amb} ambiguous, {n_unres} unresolved)[/dim]"
        )
