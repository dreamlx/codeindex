"""Write-once graph-export — codeindex → loomgraph data contract (GH #102, ADR-007).

Path A (standalone): ``codeindex graph-export`` does its OWN clean whole-tree
parse, builds a global entity/edge model from the parsed L1 structure, and
dumps a write-once NDJSON artifact. It does **not** touch ``scan-all`` / the
README render path, and does **not** require the #101 2a render-flip.

Why a separate parse (not reuse scan-all's): scan-all parses *render-shaped*
(navigation/detailed levels scan recursively → the same file is parsed under
multiple ancestor dirs). Export needs *whole-tree, each-file-exactly-once* or
the global call graph double-counts. See #102 discussion.

Scope (YELLOW verdict, LoomGraph#30): entity / entity_type / source_id /
description / CALLS / INHERITS, each edge carrying a ``resolution_qualifier``
(resolved | ambiguous | unresolved) so the consumer never mistakes an
unresolved edge for a real one. Schema is **experimental, version 0** —
evidence is Python-single-fixture; TS spot-check pending before any stable
promise.

Deliberately NOT here (ADR-007): persistent/mutable .db, incremental sync,
sqlite-vec, L3 design-doc extraction (all loomgraph's).
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config
from .graph_buffer import GraphBuffer
from .parallel import parse_files_parallel
from .scanner import scan_directory

SCHEMA_VERSION = 0

# The single most important caveat the LoomGraph#30 spike surfaced (E-class):
# AST extraction silently misses dynamically-resolved call sites. A consumer
# must read "no edge" as "not statically resolvable", never as "no caller".
PROVENANCE_COMPLETENESS = (
    "ast-only: dynamic dispatch (getattr / duck-typing / event handlers), "
    "reflection / metaclasses, and decorator wiring are NOT captured; an "
    "absent edge means 'not statically resolvable', not 'none'"
)


@dataclass
class Entity:
    """A code entity (node) in the export graph."""

    id: str
    entity_type: str  # class | function | method
    source_id: str  # relpath:line
    description: str = ""
    provenance: str = "ast"

    def to_record(self) -> dict:
        return {
            "type": "entity",
            "id": self.id,
            "entity_type": self.entity_type,
            "source_id": self.source_id,
            "description": self.description,
            "provenance": self.provenance,
        }


@dataclass
class Edge:
    """A relationship (edge) between two entities."""

    kind: str  # CALLS | INHERITS
    src: str
    dst: str | None
    resolution_qualifier: str  # resolved | ambiguous | unresolved
    source_id: str
    candidates: list[str] = field(default_factory=list)

    def to_record(self) -> dict:
        rec = {
            "type": "edge",
            "kind": self.kind,
            "src": self.src,
            "dst": self.dst,
            "resolution_qualifier": self.resolution_qualifier,
            "source_id": self.source_id,
        }
        # candidates only carried for ambiguous edges (the F-class signal)
        if self.candidates:
            rec["candidates"] = self.candidates
        return rec


@dataclass
class ExportModel:
    """The complete export: meta + entities + edges."""

    entities: list[Entity] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    generator: str = "codeindex"

    def meta_record(self) -> dict:
        return {
            "type": "meta",
            "schema_version": SCHEMA_VERSION,
            "generator": self.generator,
            "provenance_completeness": PROVENANCE_COMPLETENESS,
        }


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _module_of(path: Path, root: Path) -> str:
    """Derive a dotted module name from a file path relative to root."""
    rel = path.resolve().relative_to(root.resolve())
    return rel.with_suffix("").as_posix().replace("/", ".")


def _source_id(path: Path, root: Path, line: int) -> str:
    return f"{path.resolve().relative_to(root.resolve()).as_posix()}:{line}"


def _first_line(text: str) -> str:
    text = (text or "").strip()
    return text.splitlines()[0].strip() if text else ""


def _resolve(
    name: str | None,
    module: str,
    last_index: dict[str, list[str]],
) -> tuple[str, str | None, list[str]]:
    """Resolve a best-effort callee/parent name against the global entity set.

    Returns (resolution_qualifier, dst, candidates). The parser emits
    *file-local* names (e.g. ``Class.method``, ``func``, ``obj.run``); this
    pass is the only place a global, cross-file resolution is attempted.
    """
    if not name:
        return "unresolved", None, []

    last = name.rsplit(".", 1)[-1]
    pool = last_index.get(last, [])
    if not pool:
        return "unresolved", None, []  # external / stdlib / not in tree

    # 1. same-module exact match wins outright
    exact = f"{module}.{name}"
    if exact in pool:
        return "resolved", exact, []

    # 2. full-suffix match (id == name or endswith ".name") — cross-file
    full = [e for e in pool if e == name or e.endswith("." + name)]
    if len(full) == 1:
        return "resolved", full[0], []
    if len(full) > 1:
        return "ambiguous", None, sorted(full)

    # 3. last-segment fallback (bare/dotted callee with no fuller match)
    if len(pool) == 1:
        return "resolved", pool[0], []
    return "ambiguous", None, sorted(pool)


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
def walk_and_parse(root: Path, config: Config) -> GraphBuffer:
    """Export-shaped clean parse: every source file under ``root`` exactly once.

    Unlike scan-all (which re-parses subtrees per render level and excludes
    pass-through dirs), this does ONE recursive scan and groups by parent dir,
    so the export sees every file once and loses none.
    """
    result = scan_directory(root, config, recursive=True)
    parse_results = (
        parse_files_parallel(result.files, config, quiet=True) if result.files else []
    )

    by_dir: dict[Path, list] = defaultdict(list)
    for pr in parse_results:
        by_dir[pr.path.parent].append(pr)

    buffer = GraphBuffer()
    for dir_path, prs in by_dir.items():
        # level / child_dirs are render-only fields, unused by export; the
        # buffer is used here purely as the parsed-data container (#101 IR).
        buffer.record_directory(dir_path, "detailed", prs, [])
    return buffer


def build_export(buffer: GraphBuffer, root: Path) -> ExportModel:
    """Project a populated GraphBuffer into the entity/edge export model."""
    entities: list[Entity] = []
    # last-segment -> entity ids, for cross-file resolution
    last_index: dict[str, list[str]] = defaultdict(list)

    # Pass 1: entities + resolution index
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for sym in pr.symbols:
                eid = f"{module}.{sym.name}"
                entities.append(
                    Entity(
                        id=eid,
                        entity_type=sym.kind,
                        source_id=_source_id(pr.path, root, sym.line_start),
                        description=_first_line(sym.docstring),
                    )
                )
                last_index[sym.name.rsplit(".", 1)[-1]].append(eid)

    # Pass 2: edges (CALLS + INHERITS), resolved against the global index
    edges: list[Edge] = []
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for call in pr.calls:
                src = module if call.caller == "<module>" else f"{module}.{call.caller}"
                qual, dst, cands = _resolve(call.callee, module, last_index)
                edges.append(
                    Edge(
                        kind="CALLS",
                        src=src,
                        dst=dst,
                        resolution_qualifier=qual,
                        source_id=_source_id(pr.path, root, call.line_number),
                        candidates=cands,
                    )
                )
            # Inheritance carries no line of its own; attribute it to the
            # child class's definition line (avoids a misleading ":0").
            child_line = {s.name: s.line_start for s in pr.symbols}
            for inh in pr.inheritances:
                qual, dst, cands = _resolve(inh.parent, module, last_index)
                edges.append(
                    Edge(
                        kind="INHERITS",
                        src=f"{module}.{inh.child}",
                        dst=dst,
                        resolution_qualifier=qual,
                        source_id=_source_id(pr.path, root, child_line.get(inh.child, 0)),
                        candidates=cands,
                    )
                )

    return ExportModel(entities=entities, edges=edges)


def dump_ndjson(model: ExportModel) -> str:
    """Serialise the export model to deterministic NDJSON text."""
    lines = [json.dumps(model.meta_record(), ensure_ascii=False, sort_keys=True)]
    for ent in sorted(model.entities, key=lambda e: e.id):
        lines.append(json.dumps(ent.to_record(), ensure_ascii=False, sort_keys=True))
    for edge in sorted(
        model.edges, key=lambda e: (e.kind, e.src, e.dst or "", e.source_id)
    ):
        lines.append(json.dumps(edge.to_record(), ensure_ascii=False, sort_keys=True))
    return "\n".join(lines) + "\n"
