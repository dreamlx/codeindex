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
import re
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

    # Python constructor: the parser tags a CONSTRUCTOR call's callee as
    # ``Class.__init__`` (parsers/python/calls.py). The call instantiates the
    # CLASS, so the edge must land on the class entity — not a phantom
    # ``__init__`` method. Auto-generated ``__init__`` (dataclass) is never a
    # symbol, so the method entity rarely exists; even when it does (hand-
    # written), the class is the right target (else the class gets ZERO
    # resolved in-edges and is falsely orphan downstream, GH #132). Strip the
    # tag and resolve the class name.
    if name.endswith(".__init__"):
        return _resolve(name[: -len(".__init__")], module, last_index)

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


def _unresolved_breakdown(edges: list[Edge]) -> dict[str, int]:
    """Bucket unresolved edges by ``dst_raw`` shape (GH #148).

    The flat ``N unresolved`` total hid whether the noise was exclude-able
    (external / stdlib / test-framework globals like ``expect``/``screen`` —
    bare tokens) or the AST ceiling (``this.x``/``obj.run`` dynamic dispatch
    per GH #127 — dotted). Two buckets, both mechanically honest:

    - ``bare``   — no ``.`` in ``dst_raw`` (external / stdlib / test globals)
    - ``member`` — dotted ``dst_raw`` (dynamic dispatch, AST ceiling)

    Counts only unresolved edges; resolved/ambiguous are not bucketed. Sums
    to the unresolved total shown in the CLI summary.
    """
    counts = {"bare": 0, "member": 0}
    for e in edges:
        if e.resolution_qualifier != "unresolved":
            continue
        key = "member" if "." in (e.dst_raw or "") else "bare"
        counts[key] += 1
    return counts


def _calls_unresolved_ratio(edges: list[Edge]) -> float | None:
    """Unresolved CALLS as a fraction of all CALLS, or ``None`` if no calls.

    Used by the graph-export summary's high-ratio WARNING (GH #148). Scoped
    to CALLS, not all edges: IMPORTS-unresolved is by-design (external
    packages) and would false-fire on every normal repo with many external
    imports. Test-library noise (``expect``/``screen``) lives in CALLS.
    """
    calls = [e for e in edges if e.kind == "CALLS"]
    if not calls:
        return None
    n_unres = sum(1 for e in calls if e.resolution_qualifier == "unresolved")
    return n_unres / len(calls)


def _module_target(import_module: str, importer_module: str) -> str:
    """Normalise an import module string to an absolute dotted module id.

    Absolute imports (``app.validators``, ``os``) are returned verbatim with
    path separators normalised to ``.``: TS ``/`` (``./api``) and PHP ``\\``
    (``App\\Service`` → ``App.Service``, PSR-4 — GH #118). Relative imports
    (``./api``, ``../lib`` — TS/JS) resolve against the importer module's
    directory.
    """
    if import_module.startswith("."):
        # Python PEP 328 relative import (``.mod``, ``..mod``, ``.``): the
        # leading dot COUNT names a package level — 1 dot = current package
        # (importer's parent), 2 = parent package, N = N levels up. This is
        # NOT the TS/JS ``./`` ``../`` path form; conflating them yields a
        # double-dot id (``pkg..mod``) that never hits the scan tree (GH #133).
        if "/" not in import_module and "\\" not in import_module:
            dots = len(import_module) - len(import_module.lstrip("."))
            rest = import_module[dots:]  # "" (from . import X) or "mod"
            importer_parts = importer_module.split(".") if importer_module else []
            base = importer_parts[:-dots] if dots <= len(importer_parts) else []
            name_parts = rest.split(".") if rest else []
            return ".".join([*base, *name_parts])
        # TS/JS ``./`` ``../`` path form (slash-delimited up-count)
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
# GH #118 / #133: src-layout roots — the file-path-derived module id carries a
# source-root prefix the logical import name lacks. Java Maven:
#   import ``com.foo.Bar`` ≠ module id ``src.main.java.com.foo.Bar``.
# Python src-layout (PEP): file ``src/pkg/mod.py`` → module id ``src.pkg.mod``,
# but import is ``from pkg.mod import X`` (target ``pkg.mod``). Each known root
# is prepended to the import target and re-checked against the scan tree. This
# is layout-specific, NOT a general suffix match — Python ``import os`` won't
# wrongly hit a project ``app.os``, because ``src.main.java.os`` / ``src.os``
# are never in a normal tree.
_SOURCE_ROOT_PREFIXES = (
    "src.main.java.",   # GH #118: Java Maven main
    "src.test.java.",   # GH #118: Java Maven test
    "src.",             # GH #133: Python src-layout (PEP)
)


def _check_fallbacks(target: str, module_set: set[str]) -> str | None:
    """Shared resolution chain for a dotted module-id ``target``.

    Tries, in order: exact scan-tree match → src-layout prefix (GH #118/#133)
    → Python ``__init__`` barrel (GH #133) → TS ``index`` barrel (GH #140).
    Returns the resolved module id, or ``None``. Shared by the main
    ``_resolve_module`` path and the #139 alias branch so both follow the same
    fallback order — adding a new fallback here fixes both at once.
    """
    if target in module_set:
        return target
    for prefix in _SOURCE_ROOT_PREFIXES:
        candidate = prefix + target
        if candidate in module_set:
            return candidate
    # Package-level import (``from . import X`` / ``from pkg import Y``): the
    # target is a package/dir name, but the scan tree stores its init module.
    # Python __init__.py → ``pkg.__init__`` (GH #133); checked before TS index
    # so a (pathological) mixed Python+TS dir resolves to the Python package.
    if target + ".__init__" in module_set:
        return target + ".__init__"
    # TS/JS barrel: ``from "."`` / ``from "./sub"`` targets a directory whose
    # ``index.ts`` is the module. The scan tree stores it as ``dir.index``
    # (web/index.ts → web.index), not as the bare dir id (GH #140).
    if target + ".index" in module_set:
        return target + ".index"
    return None


# --------------------------------------------------------------------------- #
# TS path-alias resolution (GH #139) — tsconfig.json paths/baseUrl
# --------------------------------------------------------------------------- #
# Strip ``//`` line and ``/* */`` block comments from JSONC text WITHOUT
# touching ``//`` inside string literals. A single alternation matches either a
# comment (discarded) or a double-quoted string literal (kept via group). Naive
# ``re.sub(r"//.*", ...)`` would delete the ``://`` inside ``"http://..."``.
_JSONC_COMMENT_RE = re.compile(
    r'//[^\n]*'              # // line comment
    r'|/\*.*?\*/'            # /* block comment */ (DOTALL spans newlines)
    r'|"(?:\\.|[^"\\])*"',   # " string literal " (preserved)
    re.DOTALL,
)


def _strip_jsonc_comments(text: str) -> str:
    """Remove ``//`` and ``/* */`` comments from JSONC, preserving string
    literals. No new dependency (json5/commentjson not in the wheel)."""
    def _sub(m: re.Match) -> str:
        if m.group(0).startswith('"'):
            return m.group(0)  # keep string literal verbatim
        return ""              # drop comment
    return _JSONC_COMMENT_RE.sub(_sub, text)


def _load_tsconfig_paths(root: Path) -> dict[str, list[str]]:
    """Read a single ``root/tsconfig.json`` and return TS path-alias mappings.

    Returns ``{alias_key: [dotted_target_patterns]}`` where both keys and
    target patterns may contain ``*`` (matching tsconfig ``paths`` semantics).
    Targets are stored as **dotted module-id patterns** (``src/*`` →
    ``src.*``), the same form ``module_set`` uses, so expansion needs no
    re-dotting. No ``extends`` / project-refs / monorepo support (single root
    tsconfig, per #139 scope). Fails soft — any parse error returns ``{}``,
    never crashing export.
    """
    tsconfig = root / "tsconfig.json"
    if not tsconfig.exists():
        return {}
    raw = tsconfig.read_text(errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # JSONC (// and /* */ comments) is not strict JSON — strip and retry.
        try:
            data = json.loads(_strip_jsonc_comments(raw))
        except json.JSONDecodeError:
            return {}  # malformed even after stripping — degrade to no-alias
    if not isinstance(data, dict):
        return {}
    compiler_options = data.get("compilerOptions")
    if not isinstance(compiler_options, dict):
        return {}
    paths = compiler_options.get("paths")
    if not isinstance(paths, dict) or not paths:
        return {}

    # baseUrl → dotted prefix (``"src"`` → ``"src"``; ``"."``/``""``/absent →
    # ``""``). Paths targets are relative to baseUrl.
    base_prefix = ""
    base_url = compiler_options.get("baseUrl")
    if isinstance(base_url, str) and base_url not in ("", "."):
        base_prefix = ".".join(
            p for p in base_url.replace("\\", "/").split("/") if p and p != "."
        )

    def _dot(s: str) -> str:
        # Normalize like baseUrl above: drop empty + ``.`` segments so a
        # ``./``-prefixed target (``./src/*`` — Vite/Next.js/fabricOS default,
        # GH #144) dots to ``src.*`` not ``..src.*`` (leading ``.`` → dot).
        parts = [p for p in s.replace("\\", "/").split("/") if p and p != "."]
        return ".".join(parts)

    out: dict[str, list[str]] = {}
    for alias_key, targets in paths.items():
        if not isinstance(alias_key, str) or not isinstance(targets, list):
            continue
        dotted_targets: list[str] = []
        for t in targets:
            if not isinstance(t, str) or not t:
                continue
            d = _dot(t)
            if base_prefix:
                d = f"{base_prefix}.{d}" if d else base_prefix
            dotted_targets.append(d)
        if dotted_targets:
            out[alias_key] = dotted_targets
    return out


def _expand_alias(specifier: str, alias_map: dict[str, list[str]]) -> list[str]:
    """Expand a TS import specifier against tsconfig ``paths`` aliases.

    Returns candidate **dotted module-id** strings (list because a paths value
    is a multi-target fallback list). Empty list = no alias matched → caller
    falls through to normal relative/absolute resolution. First matching alias
    key wins (dict insertion order = tsconfig order, matching TS behaviour).
    """
    candidates: list[str] = []
    for alias_key, targets in alias_map.items():
        if "*" in alias_key:
            star = alias_key.index("*")
            prefix = alias_key[:star]
            suffix = alias_key[star + 1:]
            if not specifier.startswith(prefix):
                continue
            if suffix and not specifier.endswith(suffix):
                continue
            if len(prefix) + len(suffix) > len(specifier):
                continue
            # remainder is a path fragment (``components/Foo``) — dot-ify to
            # match the dotted target pattern and module_set form.
            remainder = (
                specifier[len(prefix):len(specifier) - len(suffix)]
                .replace("\\", ".")
                .replace("/", ".")
            )
            for t in targets:
                candidates.append(t.replace("*", remainder) if "*" in t else t)
        elif specifier == alias_key:
            candidates.extend(targets)
        if candidates:
            break  # first matching key wins
    return candidates


def _resolve_module(
    import_module: str,
    importer_module: str,
    module_set: set[str],
    alias_map: dict[str, list[str]] | None = None,
) -> tuple[str, str | None]:
    """Resolve an import target to a module id in the scan tree (IMPORTS edges).

    Unlike ``_resolve`` (which resolves a callee/parent *name* against the
    entity set), this resolves a *module* target: ``dst`` is a dotted module
    id with **no entity backing** (module-level, like a ``<module>`` CALLS
    src) — the consumer materialises the container if it wants one (ADR-007
    entity-centric contract). Returns ``(resolution_qualifier, dst)``;
    ``dst_raw`` (the original import string) is the caller's responsibility.

    src-layout fallback (GH #118 Java Maven, #133 Python src): the import's
    logical name is prepended with each known source root and re-checked
    against the scan tree.

    TS path-alias (GH #139): if ``alias_map`` is given and the specifier
    matches a tsconfig ``paths`` key, the alias is expanded to candidate dotted
    module ids and resolved through the same fallback chain. An alias that
    matches but resolves to nothing STAYS unresolved — it must NOT fall through
    to ``_module_target``, which would dot-ify ``@/components`` into the bogus
    ``@.components``.
    """
    if not import_module:
        return "unresolved", None
    if alias_map:
        for cand in _expand_alias(import_module, alias_map):
            resolved = _check_fallbacks(cand, module_set)
            if resolved:
                return "resolved", resolved
        # Alias matched (non-empty expansion) but nothing resolved → do NOT
        # fall through; _module_target would mangle the alias specifier.
        if _expand_alias(import_module, alias_map):
            return "unresolved", None
    target = _module_target(import_module, importer_module)
    resolved = _check_fallbacks(target, module_set)
    if resolved:
        return "resolved", resolved
    return "unresolved", None


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
def _explicit_include(root: Path) -> list[str]:
    """Return ``include`` only if the user wrote it in ``.codeindex.yaml``.

    ``Config.load`` fills ``include`` with ``DEFAULT_INCLUDE`` when the yaml
    omits the key, which would make graph-export skip a root-level project
    entirely. We read the raw yaml so "absent" stays distinct from "default" —
    absent → whole-tree scan; present (even empty) → honor the list.
    """
    import yaml

    cfg = root / ".codeindex.yaml"
    if not cfg.exists():
        return []
    try:
        data = yaml.safe_load(cfg.read_text()) or {}
    except yaml.YAMLError:
        return []
    if "include" in data:
        inc = data.get("include") or []
        return [str(p) for p in inc]
    return []


def walk_and_parse(root: Path, config: Config) -> GraphBuffer:
    """Export-shaped clean parse: every source file under ``root`` exactly once.

    Unlike scan-all (which re-parses subtrees per render level and excludes
    pass-through dirs), this does ONE recursive scan and groups by parent dir,
    so the export sees every file once and loses none.

    Honors ``config.include`` only when the user **explicitly** wrote it in
    ``.codeindex.yaml`` — then only the listed roots are scanned, so
    ``include: [src/]`` keeps ``docs/``/``tests/`` out of the graph (GH
    loomgraph#107). When ``include`` is absent the whole tree is scanned
    (backward-compatible with root-level projects). This differs from
    ``find_all_directories``, which treats the ``DEFAULT_INCLUDE`` fallback as
    active — graph-export must not, or a repo with no ``src/`` would index
    nothing. ``exclude`` is applied by ``scan_directory`` either way.
    """
    explicit_include = _explicit_include(root)
    scan_roots: list[Path] = []
    if explicit_include:
        for rel in explicit_include:
            inc = (root / rel).resolve()
            if inc.is_dir():
                scan_roots.append(inc)
    else:
        scan_roots = [root]

    files: list[Path] = []
    for inc in scan_roots:
        files.extend(scan_directory(inc, config, recursive=True).files)
    parse_results = (
        parse_files_parallel(files, config, quiet=True) if files else []
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
    # TS path-alias map from tsconfig.json (GH #139); empty when no tsconfig.
    alias_map = _load_tsconfig_paths(root)

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
                qual, dst = _resolve_module(imp.module, module, module_set, alias_map)
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
    #
    # Barrel re-export propagation (GH #140): a barrel module re-exports names
    # it does NOT define locally (``export { X } from "./mod"``). When an
    # import resolves to such a barrel, ``cand = barrel.X`` misses (X is not a
    # local entity). A pre-pass built ``reexport_map`` (barrel_module →
    # {exported_name: source_module}); here we follow the chain to the real
    # definition module. Wildcard ``export * from`` is excluded (no member
    # tracking, documented skip). The ``visited`` set bounds chained barrels
    # (A→B→C→def) and breaks cycles (A↔B) — no ghost edges, no hang.
    entity_ids = {e.id for e in entities}
    # Re-export pre-pass: barrel_module → {exported_name: source_module}.
    reexport_map: dict[str, dict[str, str]] = defaultdict(dict)
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for imp in pr.imports:
                if not imp.is_reexport:
                    continue
                _rq, target = _resolve_module(imp.module, module, module_set, alias_map)
                if not target:
                    continue
                for name in imp.names:
                    if not name or name == "*":
                        continue
                    reexport_map[module][name] = target
    seen_refs: set[tuple[str, str]] = set()  # dedup (src-module, dst-entity)
    for node in buffer.directories():
        for pr in node.parse_results:
            module = _module_of(pr.path, root)
            for imp in pr.imports:
                _q, target = _resolve_module(imp.module, module, module_set, alias_map)
                if not target:
                    continue
                for name in imp.names:
                    if not name or name == "*":
                        continue
                    cand_target = target
                    cand = f"{cand_target}.{name}"
                    # Follow the barrel re-export chain to the real definition.
                    visited = {cand_target}
                    while cand not in entity_ids:
                        nxt = reexport_map.get(cand_target, {}).get(name)
                        if not nxt or nxt in visited:
                            break  # no re-export, or cycle — give up honestly
                        visited.add(nxt)
                        cand_target = nxt
                        cand = f"{cand_target}.{name}"
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
