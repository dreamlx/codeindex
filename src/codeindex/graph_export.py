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

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config
from .graph_buffer import GraphBuffer
from .parallel import parse_files_parallel
from .scanner import scan_directory

SCHEMA_VERSION = 1  # v1: per-symbol content_hash (GH #124, #110 gate satisfied)


def _content_hash(source: str, line_start: int, line_end: int) -> str | None:
    """Per-symbol content hash (sha256) over a normalized span (GH #124).

    Normalization (hashline pattern, ref oh-my-openagent packages/hashline-core):
    ``splitlines()`` slice ``[line_start-1 : line_end]`` → per-line ``rstrip()``
    (trailing whitespace) → strip a leading BOM → ``"\\n".join``. The hash is
    over **content, not line numbers** — inserting a line above a symbol shifts
    its ``line_start``/``line_end`` but leaves ``content_hash`` stable, so a
    consumer can skip re-embedding unchanged symbols.

    Returns ``None`` when there's no usable span (``line_start``/``line_end``
    falsy or inverted, or empty slice) — module-level / external / synthetic
    entities.
    """
    if not line_start or not line_end or line_end < line_start:
        return None
    span = source.splitlines()[line_start - 1 : line_end]
    if not span:
        return None
    text = "\n".join(line.rstrip() for line in span)
    if text.startswith("﻿"):
        text = text[1:]
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    # GH #115: parser-derived signature, projected so consumers can build a
    # fuller embedding input (signature + docstring) than description alone.
    # Docstring-less symbols had empty description → no vector → invisible to
    # semantic search; signature is present for ~all symbols. Additive over
    # schema_version 0 (no bump — the 0-version window is for exactly this).
    # codeindex does NOT collapse signature+description; the combine is the
    # consumer's call (ADR-007 seam).
    signature: str = ""
    provenance: str = "ast"
    # GH #124: per-symbol sha256 over a normalized span (content, not line
    # numbers → stable under line shift). None for no-span entities (module /
    # external / synthetic). Additive over schema v0 consumers (ignored).
    content_hash: str | None = None

    def to_record(self) -> dict:
        return {
            "type": "entity",
            "id": self.id,
            "entity_type": self.entity_type,
            "source_id": self.source_id,
            "description": self.description,
            "signature": self.signature,
            "provenance": self.provenance,
            "content_hash": self.content_hash,
        }


@dataclass
class Edge:
    """A relationship (edge) between two entities."""

    kind: str  # CALLS | INHERITS | IMPORTS
    src: str
    dst: str | None
    resolution_qualifier: str  # resolved | ambiguous | unresolved
    source_id: str
    dst_raw: str = ""  # original best-effort callee/parent name (file-local)
    candidates: list[str] = field(default_factory=list)

    def to_record(self) -> dict:
        rec = {
            "type": "edge",
            "kind": self.kind,
            "src": self.src,
            "dst": self.dst,
            # the raw name we tried to resolve — load-bearing for unresolved
            # edges (dst is null), so a consumer can still synthesise an
            # external stub or filter test/framework noise (e.g. `expect`).
            "dst_raw": self.dst_raw,
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

    # 3. No full-suffix match in the pool. For a DOTTED callee (``obj.run``)
    #    this is dynamic dispatch — the receiver is a runtime parameter whose
    #    type is statically unknowable, so a last-segment fallback would only
    #    manufacture ghost edges (GH #127: 502/544 ambiguous edges in fabricOS
    #    were this false positive). A BARE callee cannot reach here: every
    #    pool member's id ends with ``.{last}`` (last_index keys ARE the last
    #    segment), so step 2 already decided all of them. Unresolved is the
    #    honest answer either way.
    return "unresolved", None, []


def _module_target(import_module: str, importer_module: str) -> str:
    """Normalise an import module string to an absolute dotted module id.

    Absolute imports (``app.validators``, ``os``) are returned verbatim with
    path separators normalised to ``.``: TS ``/`` (``./api``) and PHP ``\\``
    (``App\\Service`` → ``App.Service``, PSR-4 — GH #118). Relative imports
    (``./api``, ``../lib`` — TS/JS) resolve against the importer module's
    directory.
    """
    if import_module.startswith("."):
        stripped = import_module
        up = 0
        while stripped.startswith("../"):
            up += 1
            stripped = stripped[3:]
        while stripped.startswith("./"):
            stripped = stripped[2:]
        importer_parts = importer_module.split(".") if importer_module else []
        dir_parts = importer_parts[:-1] if importer_parts else []
        if up:
            dir_parts = dir_parts[:-up] if up <= len(dir_parts) else []
        name_parts = [p for p in stripped.split("/") if p]
        return ".".join([*dir_parts, *name_parts])
    return import_module.replace("\\", ".").replace("/", ".")  # GH #118: PHP \\ → .


# GH #118: Java Maven src-layout — the file-path-derived module id carries a
# src/main/java (or src/test/java) prefix the logical import name lacks:
# import ``com.foo.Bar`` ≠ module id ``src.main.java.com.foo.Bar``. Prepended
# here so the import resolves. This is layout-specific, NOT a general suffix
# match — Python ``import os`` won't wrongly hit a project ``app.os``, because
# ``src.main.java.os`` is never in the tree.
_MAVEN_SOURCE_ROOTS = ("src.main.java.", "src.test.java.")


def _resolve_module(
    import_module: str,
    importer_module: str,
    module_set: set[str],
) -> tuple[str, str | None]:
    """Resolve an import target to a module id in the scan tree (IMPORTS edges).

    Unlike ``_resolve`` (which resolves a callee/parent *name* against the
    entity set), this resolves a *module* target: ``dst`` is a dotted module
    id with **no entity backing** (module-level, like a ``<module>`` CALLS
    src) — the consumer materialises the container if it wants one (ADR-007
    entity-centric contract). Returns ``(resolution_qualifier, dst)``;
    ``dst_raw`` (the original import string) is the caller's responsibility.

    Java imports need a Maven src-layout fallback (GH #118): the import's
    logical name is prepended with each known Maven source root and re-checked
    against the scan tree.
    """
    if not import_module:
        return "unresolved", None
    target = _module_target(import_module, importer_module)
    if target in module_set:
        return "resolved", target
    for prefix in _MAVEN_SOURCE_ROOTS:
        candidate = prefix + target
        if candidate in module_set:
            return "resolved", candidate
    return "unresolved", None


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
    # all scanned module ids, for IMPORTS resolution (GH #117)
    module_set: set[str] = set()

    # Pass 1: entities + resolution index
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            module_set.add(module)
            # Read source once per file (ParseResult has no source field, GH #124);
            # all symbols in this file share it for content_hash span slicing.
            try:
                source = pr.path.read_text(errors="replace")
            except OSError:
                source = ""
            for sym in pr.symbols:
                eid = f"{module}.{sym.name}"
                entities.append(
                    Entity(
                        id=eid,
                        entity_type=sym.kind,
                        source_id=_source_id(pr.path, root, sym.line_start),
                        description=_first_line(sym.docstring),
                        signature=sym.signature,
                        content_hash=_content_hash(source, sym.line_start, sym.line_end),
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
                        dst_raw=call.callee or "",
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
                        dst_raw=inh.parent or "",
                        candidates=cands,
                    )
                )

    # Pass 3: IMPORTS edges (module→module, GH #117). Additive over schema 0
    # — no version bump. src is the importer module id (no entity backing,
    # like a <module> CALLS src); dst is the imported module id if it's a file
    # in the scan tree, else null with dst_raw carrying the original string.
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for imp in pr.imports:
                qual, dst = _resolve_module(imp.module, module, module_set)
                edges.append(
                    Edge(
                        kind="IMPORTS",
                        src=module,
                        dst=dst,
                        resolution_qualifier=qual,
                        source_id=_source_id(pr.path, root, imp.line),
                        dst_raw=imp.module or "",
                    )
                )

    # Pass 4: REFERENCES edges — symbol-level import-ref (GH #128).
    # For each named/default import whose target module resolved AND whose
    # imported name matches an exported entity in that module, emit an edge
    # importer-module → {target_module}.{name}. Connects non-callable exported
    # symbols (const / interface / type_alias) imported by name that are
    # otherwise zero-edge and get falsely flagged orphan. Namespace (`*`)
    # imports are skipped (they need per-usage member tracking, out of scope).
    entity_ids = {e.id for e in entities}
    seen_refs: set[tuple[str, str]] = set()  # dedup (src-module, dst-entity)
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for imp in pr.imports:
                _q, target = _resolve_module(imp.module, module, module_set)
                if not target:
                    continue
                for name in imp.names:
                    if not name or name == "*":
                        continue
                    cand = f"{target}.{name}"
                    if cand not in entity_ids or (module, cand) in seen_refs:
                        continue
                    seen_refs.add((module, cand))
                    edges.append(
                        Edge(
                            kind="REFERENCES",
                            src=module,
                            dst=cand,
                            resolution_qualifier="resolved",
                            source_id=_source_id(pr.path, root, imp.line),
                            dst_raw=f"{imp.module}.{name}",
                        )
                    )

    # Pass 5: REFERENCES edges — type-ref (GH #128). For each type identifier
    # used in type position, resolve it via the global last-segment index
    # (same-module exact preferred, mirroring _resolve) and emit
    # using-module → type entity. Connects declared types that are referenced
    # only via `: Foo` annotations — including same-module `XxxProps` — which
    # import-ref cannot reach (no import exists). Multi-match names resolve
    # unresolved and are skipped (the #127 lesson: don't manufacture edges).
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for tr in pr.type_refs:
                _q, dst, _c = _resolve(tr.name, module, last_index)
                if not dst or (module, dst) in seen_refs:
                    continue
                seen_refs.add((module, dst))
                edges.append(
                    Edge(
                        kind="REFERENCES",
                        src=module,
                        dst=dst,
                        resolution_qualifier="resolved",
                        source_id=_source_id(pr.path, root, tr.line),
                        dst_raw=tr.name or "",
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
