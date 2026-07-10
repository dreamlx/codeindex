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

    # GH #129: a languages mismatch signals the configured `languages` don't
    # cover the project's code files. graph-export consumes this output
    # directly into loomgraph, so a silent partial graph (few entities from a
    # stray `.py` + a TS repo full of uncaptured `.ts`) would stream with
    # `success:true` and downstream would build deps/topology on a broken
    # graph. Two surfaces, one diagnostic source:
    #   - 0 entities  : the classic footgun (analogous to scan-all's GH #105
    #     ``with_files == 0`` guard) — reuse ``language_mismatch_hint``.
    #   - >0 entities : the few-entity false-positive (GH #129) — entities
    #     exist but ≪ the unconfigured-language files. The 0-entity hint text
    #     ("no indexable directories found") is wrong here, so this branch
    #     renders its own partial-graph wording from ``diagnose_language_mismatch``.
    # scan-all deliberately stays at the 0-files guard: its partial output
    # (only some READMEs) is *visible*, whereas graph-export's is silent.
    if not quiet:
        if not model.entities:
            from .scanner import language_mismatch_hint

            hint = language_mismatch_hint(root, config)
            if hint:
                click.echo(f"WARNING: {hint}", err=True)
        else:
            from .scanner import diagnose_language_mismatch

            diag = diagnose_language_mismatch(root, config)
            if diag["candidate_languages"]:
                # Files present whose extensions belong to an unconfigured
                # supported language — what graph-export is leaving on the table.
                present = diag["extensions_present"]
                configured = diag["configured_extensions"]
                uncaptured = [
                    (ext, n) for ext, n in present.most_common() if ext not in configured
                ]
                top = ", ".join(f"{ext} ({n})" for ext, n in uncaptured[:5])
                cands = " / ".join(diag["candidate_languages"])
                click.echo(
                    "WARNING: partial graph — graph-export captured "
                    f"{len(model.entities)} entities but configured languages "
                    f"{diag['configured_languages']} leave code files uncaptured "
                    f"({top}). Add {cands} to .codeindex.yaml `languages:` to "
                    "capture them (run: codeindex config explain languages)",
                    err=True,
                )

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
