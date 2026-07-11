"""Tests for the write-once graph-export (GH #102, Path A).

Covers the global cross-file resolution that turns file-local parser output
into a graph: a golden NDJSON snapshot plus explicit assertions on every
``resolution_qualifier`` state (resolved intra/cross-file, ambiguous,
unresolved) so the test proves the resolver works, not just that bytes are
stable.

Regenerate golden after an intentional change::

    CODEINDEX_UPDATE_GOLDEN=1 pytest tests/test_graph_export.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from codeindex.config import Config
from codeindex.graph_export import build_export, dump_ndjson, walk_and_parse

FIXTURE = Path(__file__).parent / "fixtures" / "graph_export" / "project"
GOLDEN = Path(__file__).parent / "fixtures" / "graph_export" / "export.ndjson"
UPDATE = os.environ.get("CODEINDEX_UPDATE_GOLDEN") == "1"


def _model():
    config = Config.load(FIXTURE / ".codeindex.yaml")
    buffer = walk_and_parse(FIXTURE, config)
    return build_export(buffer, FIXTURE)


def _edges(model, kind=None):
    return [e for e in model.edges if kind is None or e.kind == kind]


class TestContentHash:
    """Per-symbol content_hash (#124): stable under line shift, normalizes form."""

    def test_stable_under_line_shift(self):
        from codeindex.graph_export import _content_hash

        # Same symbol body at different line positions (blank lines inserted above).
        src_v1 = "def f():\n    return 1\n"            # f at line 1-2
        src_v2 = "\n\n\ndef f():\n    return 1\n"       # f at line 4-5
        h1 = _content_hash(src_v1, line_start=1, line_end=2)
        h2 = _content_hash(src_v2, line_start=4, line_end=5)
        assert h1 == h2, "hash must depend on content, not line numbers"

    def test_normalizes_trailing_whitespace(self):
        from codeindex.graph_export import _content_hash

        clean = "def f():\n    return 1\n"
        dirty = "def f():   \n    return 1\t\n"
        assert _content_hash(clean, 1, 2) == _content_hash(dirty, 1, 2)

    def test_normalizes_crlf(self):
        from codeindex.graph_export import _content_hash

        lf = "def f():\n    return 1\n"
        crlf = "def f():\r\n    return 1\r\n"
        assert _content_hash(lf, 1, 2) == _content_hash(crlf, 1, 2)

    def test_normalizes_bom(self):
        from codeindex.graph_export import _content_hash

        no_bom = "def f():\n    return 1\n"
        with_bom = "﻿def f():\n    return 1\n"
        assert _content_hash(no_bom, 1, 2) == _content_hash(with_bom, 1, 2)

    def test_none_for_no_span(self):
        from codeindex.graph_export import _content_hash

        assert _content_hash("anything", 0, 0) is None
        assert _content_hash("anything", 5, 3) is None  # end < start
        assert _content_hash("", 1, 5) is None  # empty source

    def test_different_content_different_hash(self):
        from codeindex.graph_export import _content_hash

        a = "def f():\n    return 1\n"
        b = "def f():\n    return 2\n"
        assert _content_hash(a, 1, 2) != _content_hash(b, 1, 2)


def _edge(model, src, dst=None, kind="CALLS"):
    for e in model.edges:
        if e.kind == kind and e.src == src and (dst is None or e.dst == dst):
            return e
    return None


# --------------------------------------------------------------------------- #
# golden snapshot
# --------------------------------------------------------------------------- #
def test_export_golden() -> None:
    actual = dump_ndjson(_model())
    if UPDATE:
        GOLDEN.write_text(actual)
        return
    assert GOLDEN.exists(), "missing golden; run CODEINDEX_UPDATE_GOLDEN=1"
    assert actual == GOLDEN.read_text(), "graph-export drift (#102 schema change?)"


# --------------------------------------------------------------------------- #
# entities
# --------------------------------------------------------------------------- #
def test_entities_qualified_and_typed() -> None:
    model = _model()
    by_id = {e.id: e for e in model.entities}

    # module-qualified ids, method names carry their class
    assert by_id["app.service.AuthService"].entity_type == "class"
    assert by_id["app.service.AuthService.authenticate"].entity_type == "method"
    assert by_id["app.validators.validate"].entity_type == "function"
    assert by_id["web.api.queryRaw"].entity_type == "function"

    # source_id is relpath:line, provenance ast, description = docstring 1st line
    assert by_id["app.validators.validate"].source_id == "app/validators.py:4"
    assert by_id["app.validators.validate"].provenance == "ast"
    assert by_id["app.service.AuthService"].description == "Authenticates users."


def test_entity_carries_signature() -> None:
    """GH #115: entity records project ``Symbol.signature``.

    ``signature`` is additive over the schema_version 0 artifact (no version
    bump — see issue). It closes the embedding-coverage hole: docstring-less
    symbols had an empty ``description`` → no embedding vector → invisible to
    downstream semantic search. A signature is present for ~all symbols, so a
    consumer can build ``description = signature + docstring`` and reach full
    coverage. codeindex stays a dumb emitter — it does NOT collapse the two;
    the combine is the consumer's call (ADR-007 seam)."""
    model = _model()
    by_id = {e.id: e for e in model.entities}

    # docstring-less symbol: description empty, but signature populated — the
    # exact hole #115 closes (workers.py Builder.run / Packer.run / kickoff).
    assert by_id["app.workers.kickoff"].description == ""
    assert by_id["app.workers.kickoff"].signature == "def kickoff() -> None"
    assert by_id["app.workers.Builder.run"].signature == "def run(self) -> None"

    # docstring present: both carry signal, kept as separate fields.
    assert by_id["app.service.AuthService"].signature == "class AuthService"
    assert by_id["app.service.AuthService"].description == "Authenticates users."


def test_entity_record_has_signature_field() -> None:
    """The NDJSON record (what consumers read) must carry the signature key."""
    model = _model()
    by_id = {e.id: e for e in model.entities}
    rec = by_id["app.workers.kickoff"].to_record()
    assert "signature" in rec
    assert rec["signature"] == "def kickoff() -> None"


# --------------------------------------------------------------------------- #
# every resolution_qualifier state (the actual point of the export)
# --------------------------------------------------------------------------- #
def test_resolved_intra_file() -> None:
    e = _edge(_model(), "app.service.AuthService.login")
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "app.service.AuthService.authenticate"


def test_resolved_cross_file() -> None:
    model = _model()
    # python cross-file
    e = _edge(model, "app.service.AuthService.authenticate")
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "app.validators.validate"
    # typescript cross-file
    t = _edge(model, "web.index.bootstrap")
    assert t.resolution_qualifier == "resolved"
    assert t.dst == "web.api.fetchUser"


def test_ambiguous_carries_candidates() -> None:
    # bare `run()` callee — last-segment matches Builder.run + Packer.run
    # (step-2 full-suffix) → genuine AMBIGUOUS.
    e = _edge(_model(), "app.workers.kickoff")
    assert e.resolution_qualifier == "ambiguous"
    assert e.dst is None
    assert e.candidates == ["app.workers.Builder.run", "app.workers.Packer.run"]


def test_dotted_callee_is_unresolved() -> None:
    # GH #127: dotted callee `obj.run()` — the receiver `obj` is a runtime
    # parameter, statically unknowable. This is dynamic dispatch → UNRESOLVED,
    # NOT ambiguous. The previous step-3 last-segment fallback spammed every
    # `.run` entity into candidates (here Builder.run/Packer.run), producing
    # ghost edges downstream.
    e = _edge(_model(), "app.workers.dispatch")
    assert e is not None
    assert e.resolution_qualifier == "unresolved"
    assert e.dst is None
    assert e.candidates == []
    # the raw dotted name survives so a consumer can stub/filter it
    assert e.dst_raw == "obj.run"


def test_unresolved_external() -> None:
    # os.getcwd is not in the fixture -> must not be faked as resolved
    e = _edge(_model(), "app.service.AdminService.cwd")
    assert e.resolution_qualifier == "unresolved"
    assert e.dst is None
    assert e.candidates == []
    # the raw name must survive so a consumer can stub/filter it
    assert e.dst_raw == "os.getcwd"


def test_inherits_edge_resolved() -> None:
    e = _edge(_model(), "app.service.AdminService", kind="INHERITS")
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "app.service.AuthService"


# --------------------------------------------------------------------------- #
# IMPORTS edges (GH #117) — module→module, additive over schema_version 0
# --------------------------------------------------------------------------- #
def test_imports_edge_resolved_intra_project() -> None:
    """``from app.validators import validate`` (service.py:5) → IMPORTS edge
    src=app.service (importer module, no entity backing — container-level,
    like a ``<module>`` CALLS src), dst=app.validators (the imported module,
    resolved because app/validators.py is in the scan tree)."""
    e = _edge(_model(), "app.service", dst="app.validators", kind="IMPORTS")
    assert e is not None
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "app.validators"
    assert e.dst_raw == "app.validators"
    assert e.source_id == "app/service.py:5"


def test_imports_edge_unresolved_external() -> None:
    """``import os`` (service.py:3) — stdlib, not in the scan tree → dst is
    null, dst_raw preserves ``os`` so a consumer can stub/filter."""
    import_edges = [
        e for e in _model().edges
        if e.kind == "IMPORTS" and e.src == "app.service"
    ]
    os_edge = [e for e in import_edges if e.dst_raw == "os"]
    assert len(os_edge) == 1
    assert os_edge[0].resolution_qualifier == "unresolved"
    assert os_edge[0].dst is None
    assert os_edge[0].source_id == "app/service.py:3"


def test_imports_edge_relative_resolved_ts() -> None:
    """``import { fetchUser } from "./api"`` (index.ts:3) — TS relative import.
    ``./api`` resolves against the importer module's directory (``web``) →
    ``web.api`` (web/api.ts is in the tree). dst_raw keeps ``./api``."""
    e = _edge(_model(), "web.index", dst="web.api", kind="IMPORTS")
    assert e is not None
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "web.api"
    assert e.dst_raw == "./api"
    assert e.source_id == "web/index.ts:3"


def test_imports_edge_record_shape() -> None:
    """IMPORTS edges serialise with the same record shape as other edges."""
    e = _edge(_model(), "app.service", dst="app.validators", kind="IMPORTS")
    assert e is not None
    rec = e.to_record()
    assert rec["type"] == "edge"
    assert rec["kind"] == "IMPORTS"
    assert rec["src"] == "app.service"
    assert rec["dst"] == "app.validators"
    assert rec["dst_raw"] == "app.validators"
    assert rec["resolution_qualifier"] == "resolved"


# --------------------------------------------------------------------------- #
# IMPORTS edges — Java/PHP resolution + line (GH #118, follow-up to #117)
# Independent tmp_path fixtures (no main-golden pollution). Main golden stays
# Python+TS; these prove per-language resolution + non-zero source_id line.
# --------------------------------------------------------------------------- #
def test_imports_edge_php_namespace_resolved(tmp_path) -> None:
    """GH #118: PHP ``use App\\Service`` resolves to ``App/Service.py`` via
    ``\\`` → ``.`` (PSR-4). #117 left PHP unresolved — the file-path-derived
    module id (``App.Service``) never equalled the raw import (``App\\Service``).
    The IMPORTS edge source_id also carries the real line (#118 fills it)."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [php]\n")
    app = tmp_path / "App"
    app.mkdir()
    (app / "Service.php").write_text("<?php\nnamespace App;\nclass Service {}\n")
    (app / "Controller.php").write_text(
        "<?php\nnamespace App;\nuse App\\Service;\nclass Controller {}\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "App.Controller", dst="App.Service", kind="IMPORTS")
    assert e is not None, "PHP IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "App.Service"
    assert e.dst_raw == "App\\Service"  # original backslash preserved
    assert e.source_id == "App/Controller.php:3"  # use on line 3, filled per #118


def test_imports_edge_java_maven_resolved(tmp_path) -> None:
    """GH #118: Java ``import com.foo.Bar`` resolves to
    ``src/main/java/com/foo/Bar.java`` despite the Maven src-layout prefix.
    The import's logical name (``com.foo.Bar``) ≠ the file-path-derived module
    id (``src.main.java.com.foo.Bar``) — #117 left every Java IMPORTS
    unresolved. Resolution strips the known Maven source root, so it never
    fires for non-Java (Python ``import os`` won't wrongly hit ``app.os``)."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [java]\n")
    pkg = tmp_path / "src" / "main" / "java" / "com" / "foo"
    pkg.mkdir(parents=True)
    (pkg / "Bar.java").write_text("package com.foo;\npublic class Bar {}\n")
    (pkg / "Baz.java").write_text(
        "package com.foo;\nimport com.foo.Bar;\npublic class Baz {}\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    # importer module id is file-path-derived (src.main.java.com.foo.Baz);
    # dst resolves to the Bar entity's module id (same Maven prefix).
    e = _edge(
        model,
        "src.main.java.com.foo.Baz",
        dst="src.main.java.com.foo.Bar",
        kind="IMPORTS",
    )
    assert e is not None, "Java IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"
    assert e.dst_raw == "com.foo.Bar"  # original Java import string preserved
    assert e.source_id == "src/main/java/com/foo/Baz.java:2"  # import on line 2


def test_python_constructor_resolves_to_class_entity(tmp_path) -> None:
    """GH #132: ``AuthService()`` is a CONSTRUCTOR call; the Python parser tags
    the callee as ``AuthService.__init__`` (calls.py:268). The call instantiates
    the CLASS, so the CALLS edge must land on the class entity — not a phantom
    ``__init__`` method (dataclass/auto-generated ``__init__`` is never a
    symbol, so before #132 the edge was unresolved and the class got ZERO
    in-edges → falsely orphan downstream)."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "class AuthService:\n"  # no explicit __init__ — dataclass-style
        "    def login(self):\n"
        "        return 1\n"
    )
    (tmp_path / "main.py").write_text(
        "from svc import AuthService\n"
        "def run():\n"
        "    a = AuthService()\n"  # constructor call inside a function body
        "    return a\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    # exactly one CALLS edge out of main.run, resolving to the class entity
    calls = [e for e in model.edges if e.kind == "CALLS" and e.src == "main.run"]
    assert len(calls) == 1
    assert calls[0].resolution_qualifier == "resolved"
    assert calls[0].dst == "svc.AuthService"  # class entity, NOT .__init__
    # the raw constructor tag survives so a consumer can stub/filter
    assert calls[0].dst_raw == "AuthService.__init__"


def test_python_constructor_inherits_class_still_resolves(tmp_path) -> None:
    """GH #132 guard: a class WITH an explicit ``__init__`` method must ALSO
    resolve its constructor call to the class entity, not to the method. The
    previous behavior resolved 325 such edges to the ``__init__`` method entity
    (misdirect), leaving the class itself zero-in-edge."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "class Widget:\n"
        "    def __init__(self):\n"  # explicit __init__ — IS a symbol entity
        "        self.x = 1\n"
    )
    (tmp_path / "main.py").write_text(
        "from svc import Widget\n"
        "def run():\n"
        "    w = Widget()\n"
        "    return w\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    calls = [e for e in model.edges if e.kind == "CALLS" and e.src == "main.run"]
    assert len(calls) == 1
    assert calls[0].resolution_qualifier == "resolved"
    assert calls[0].dst == "svc.Widget"  # class, not svc.Widget.__init__
    assert calls[0].dst_raw == "Widget.__init__"


def test_python_src_layout_import_resolves(tmp_path) -> None:
    """GH #133: Python src-layout. The file-path-derived module id carries a
    ``src.`` prefix the import statement lacks: file ``src/myproj/svc.py`` →
    module id ``src.myproj.svc``, but the import is ``from myproj.svc import
    foo`` (target ``myproj.svc``). #118 fixed this for Java (Maven
    ``src/main/java``); Python needs the same src-layout fallback. Non-src
    layout (pkg directly under root) already matches and is unaffected."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    pkg = tmp_path / "src" / "myproj"
    pkg.mkdir(parents=True)
    (pkg / "svc.py").write_text("def foo():\n    return 1\n")
    (pkg / "cli.py").write_text(
        "from myproj.svc import foo\nfoo()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    # importer module id is path-derived (src.myproj.cli); dst resolves to the
    # target module id (src.myproj.svc) via the src. prefix fallback.
    e = _edge(model, "src.myproj.cli", dst="src.myproj.svc", kind="IMPORTS")
    assert e is not None, "Python src-layout IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "src.myproj.svc"
    assert e.dst_raw == "myproj.svc"  # original import string preserved


def test_python_relative_import_resolves(tmp_path) -> None:
    """GH #133: Python PEP 328 relative imports (``.mod``, ``..mod``,
    ``from . import X``) — the dot count names a package level, NOT a path
    separator like TS ``./``. ``_module_target`` only knew the TS form, so a
    Python ``.mod`` produced a double-dot id (``pkg..mod``) that never matched
    the scan tree — 292 relative IMPORTS unresolved in the codeindex
    self-dogfood. Each leading dot = up one package level from the importer's
    parent (1 dot = current package, 2 = parent package)."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    pkg = tmp_path / "pkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "util.py").write_text("def u():\n    return 1\n")
    (sub / "__init__.py").write_text("")
    (sub / "svc.py").write_text("def s():\n    return 1\n")
    # importer: pkg/sub/cli.py — module id pkg.sub.cli
    (sub / "cli.py").write_text(
        "from . import svc\n"        # 1 dot → pkg.sub.svc
        "from ..util import u\n"     # 2 dots → pkg.util
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    # `from . import svc` → target is the current package pkg.sub; the scan
    # tree stores it as pkg.sub.__init__ (the __init__.py module id), so dst
    # resolves to that — the package-level container (GH #133 __init__ fallback).
    e1 = _edge(model, "pkg.sub.cli", dst="pkg.sub.__init__", kind="IMPORTS")
    assert e1 is not None, "from . import X edge missing"
    assert e1.resolution_qualifier == "resolved"
    assert e1.dst_raw == "."

    # `from ..util import u` → 2 dots → pkg.util
    e2 = _edge(model, "pkg.sub.cli", dst="pkg.util", kind="IMPORTS")
    assert e2 is not None, "from ..util import u edge missing"
    assert e2.resolution_qualifier == "resolved"
    assert e2.dst_raw == "..util"


# --------------------------------------------------------------------------- #
# REFERENCES edges (GH #128) — symbol-level import-ref + type-ref
# Additive: connect non-callable exported symbols (const/interface/type_alias)
# that are otherwise zero-edge → falsely flagged orphan by downstream topology.
# --------------------------------------------------------------------------- #
def test_references_edge_from_named_import() -> None:
    """import-ref: ``import { fetchUser } from './api'`` (web/index.ts:3) →
    REFERENCES edge src=web.index, dst=web.api.fetchUser. Without #128 the
    exported `fetchUser` function was connected only via its CALLS edge from
    bootstrap; an exported const/type that is imported-but-never-called would
    be zero-edge. import-ref gives such symbols a real edge."""
    e = _edge(_model(), "web.index", dst="web.api.fetchUser", kind="REFERENCES")
    assert e is not None
    assert e.resolution_qualifier == "resolved"
    assert e.dst_raw == "./api.fetchUser"
    assert e.source_id == "web/index.ts:3"  # the import line


def test_references_edge_from_type_annotation() -> None:
    """type-ref: ``Promise<T[]>`` / ``Promise<unknown>`` in web/api.ts reference
    no scan-tree entity (TS builtin), so they resolve unresolved and emit NO
    edge. The positive case is a user-defined type used in type position; this
    test asserts the resolution machinery does not over-fire on builtins
    (the #127 lesson: don't manufacture edges)."""
    # No user-defined types are referenced in the main fixture's TS, so there
    # should be exactly 0 type-ref REFERENCES edges from web.api / web.index.
    refs = [e for e in _edges(_model(), kind="REFERENCES")]
    web_refs = [e for e in refs if e.src.startswith("web.")]
    assert all(e.dst not in {"Promise", "T", "unknown"} for e in web_refs), web_refs


def test_references_edge_type_ref_connects_declared_type(tmp_path) -> None:
    """GH #128 type-ref: a ``type_alias``/``interface`` used only via ``: Foo``
    annotation (never called, never inherited) was zero-edge → orphan. The
    type-ref pass emits using-module → type-entity so it is connected. This is
    the same-module `XxxProps` pattern that cleared 100% of remaining
    interface/type_alias orphans on fabricOS in the spike."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "types.ts").write_text("export interface Payload { id: number }\n")
    (tmp_path / "use.ts").write_text(
        "import { Payload } from './types';\n"
        "export function send(p: Payload) { return p; }\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    # import-ref: use.ts imports Payload → REFERENCES use → types.Payload
    imp_e = _edge(model, "use", dst="types.Payload", kind="REFERENCES")
    assert imp_e is not None, "import-ref edge missing"
    assert imp_e.dst_raw == "./types.Payload"

    # type-ref: `: Payload` annotation in use.ts → same edge (deduped) —
    # the type is now connected, not orphan. Either the import-ref or the
    # type-ref produced the edge; both must converge on the same (src,dst).
    assert any(
        e.kind == "REFERENCES" and e.src == "use" and e.dst == "types.Payload"
        for e in model.edges
    ), [(e.kind, e.src, e.dst) for e in model.edges if e.kind == "REFERENCES"]




# --------------------------------------------------------------------------- #
# TS path-alias resolution (GH #139) — tsconfig.json paths/baseUrl
# Independent tmp_path fixtures (no main-golden pollution). A bare `@/...`
# specifier previously hit the bare-module fallback (_module_target:265),
# got dot-ified to `@.components.Foo`, never matched the scan tree, and the
# IMPORTS/REFERENCES edges through the alias were silently dropped → downstream
# orphan false-positives. _resolve_module now expands aliases BEFORE the
# fallback chain.
# --------------------------------------------------------------------------- #
def test_ts_path_alias_resolves(tmp_path) -> None:
    """GH #139: ``@/components/Foo`` resolves via tsconfig ``paths`` (no
    baseUrl). Before #139 the bare-module fallback turned it into
    ``@.components.Foo`` (never in the scan tree) and every alias import got
    zero IMPORTS/REFERENCES edges → orphan false-positive downstream."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps({"compilerOptions": {"paths": {"@/*": ["src/*"]}}})
    )
    comp = tmp_path / "src" / "components"
    comp.mkdir(parents=True)
    (comp / "Foo.ts").write_text("export function Foo(): number { return 1; }\n")
    (tmp_path / "src" / "app.ts").write_text(
        'import { Foo } from "@/components/Foo";\nexport function run() { return Foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    imp = _edge(model, "src.app", dst="src.components.Foo", kind="IMPORTS")
    assert imp is not None, "alias IMPORTS edge missing"
    assert imp.resolution_qualifier == "resolved"
    assert imp.dst_raw == "@/components/Foo"  # original alias preserved

    ref = _edge(
        model, "src.app", dst="src.components.Foo.Foo", kind="REFERENCES"
    )
    assert ref is not None, "alias REFERENCES edge missing"
    assert ref.dst_raw == "@/components/Foo.Foo"


def test_ts_path_alias_baseurl_subdir(tmp_path) -> None:
    """GH #139: ``baseUrl`` is the dir paths targets resolve against.
    ``baseUrl: "src"`` + ``paths: {"@/*": ["components/*"]}`` means ``@/Foo``
    → ``src/components/Foo`` (the target ``components/*`` is relative to
    baseUrl ``src``). Without baseUrl handling the resolved target would miss
    the ``src.`` prefix the file-path-derived module id carries."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "baseUrl": "src",
                    "paths": {"@/*": ["components/*"]},
                }
            }
        )
    )
    comp = tmp_path / "src" / "components"
    comp.mkdir(parents=True)
    (comp / "Foo.ts").write_text("export function Foo(): number { return 1; }\n")
    (tmp_path / "src" / "app.ts").write_text(
        'import { Foo } from "@/Foo";\nexport function run() { return Foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "src.app", dst="src.components.Foo", kind="IMPORTS")
    assert e is not None, "alias with baseUrl IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"


def test_ts_path_alias_non_alias_falls_through(tmp_path) -> None:
    """GH #139 guard: a tsconfig with ``@/*`` alias must NOT mangle a plain
    relative import ``./local``. The alias branch only fires when an alias key
    matches; non-alias specifiers fall through to the normal relative-path
    resolution unchanged."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps({"compilerOptions": {"paths": {"@/*": ["src/*"]}}})
    )
    (tmp_path / "local.ts").write_text("export function L(): number { return 1; }\n")
    (tmp_path / "app.ts").write_text(
        'import { L } from "./local";\nexport function run() { return L(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "app", dst="local", kind="IMPORTS")
    assert e is not None, "non-alias relative IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"
    assert e.dst_raw == "./local"


def test_ts_path_alias_unmatched_stays_unresolved(tmp_path) -> None:
    """GH #139 guard: an alias that MATCHES a paths key but points at a file
    not in the scan tree must stay ``unresolved`` — it must NOT fall through to
    _module_target, which would dot-ify ``@/nonexistent/Foo`` into the bogus
    ``@.nonexistent.Foo``. dst_raw keeps the original alias string."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps({"compilerOptions": {"paths": {"@/*": ["src/*"]}}})
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text(
        'import { Foo } from "@/nonexistent/Foo";\nexport function run() { return 0; }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "src.app", kind="IMPORTS")
    assert e is not None
    assert e.resolution_qualifier == "unresolved"
    assert e.dst is None
    assert e.dst_raw == "@/nonexistent/Foo"  # NOT mangled to @.nonexistent.Foo


def test_tsconfig_jsonc_comments_parse(tmp_path) -> None:
    """GH #139: tsconfig.json commonly carries ``//`` line and ``/* */`` block
    comments (JSONC, not strict JSON). Without stripping them, ``json.loads``
    fails and every alias import degrades to unresolved — a silent regression
    on real-world tsconfigs. Comments are stripped before parsing; no new
    dependency added."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        '{\n'
        '  // compiler options\n'
        '  "compilerOptions": {\n'
        '    /* path aliases */\n'
        '    "paths": { "@/*": ["src/*"] }\n'
        '  }\n'
        '}\n'
    )
    comp = tmp_path / "src" / "components"
    comp.mkdir(parents=True)
    (comp / "Foo.ts").write_text("export function Foo(): number { return 1; }\n")
    (tmp_path / "src" / "app.ts").write_text(
        'import { Foo } from "@/components/Foo";\nexport function run() { return Foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "src.app", dst="src.components.Foo", kind="IMPORTS")
    assert e is not None, "alias from JSONC tsconfig not parsed"
    assert e.resolution_qualifier == "resolved"


def test_ts_path_alias_multi_target(tmp_path) -> None:
    """GH #139: ``paths`` values are LISTS — TS tries each target in order. A
    file present only under the SECOND target (``src/legacy/*``) must resolve
    via that fallback, not stay unresolved because the first (``src/*``)
    missed."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps(
            {"compilerOptions": {"paths": {"@/*": ["src/*", "src/legacy/*"]}}}
        )
    )
    legacy = tmp_path / "src" / "legacy"
    legacy.mkdir(parents=True)
    (legacy / "Foo.ts").write_text("export function Foo(): number { return 1; }\n")
    (tmp_path / "src" / "app.ts").write_text(
        'import { Foo } from "@/Foo";\nexport function run() { return Foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "src.app", dst="src.legacy.Foo", kind="IMPORTS")
    assert e is not None, "multi-target alias second-target IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"


# --------------------------------------------------------------------------- #
# whole-file invariants
# --------------------------------------------------------------------------- #
def test_meta_and_ndjson_shape() -> None:
    text = dump_ndjson(_model())
    first = json.loads(text.splitlines()[0])
    assert first["type"] == "meta"
    assert first["schema_version"] == 1  # v1: content_hash (#124)
    assert "ast-only" in first["provenance_completeness"]
    # every line is valid json with a type tag
    for line in text.splitlines():
        assert json.loads(line)["type"] in {"meta", "entity", "edge"}


def test_cli_writes_artifact_matching_golden(tmp_path) -> None:
    import shutil

    from click.testing import CliRunner

    from codeindex.cli import main

    proj = tmp_path / "project"
    shutil.copytree(FIXTURE, proj)
    out = proj / "graph-export.ndjson"
    result = CliRunner().invoke(
        main,
        ["graph-export", "--root", str(proj), "-o", str(out), "--quiet"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert out.read_text() == GOLDEN.read_text()


def test_each_file_parsed_once() -> None:
    """Export-shaped walk must not double-count (no recursive overlap)."""
    config = Config.load(FIXTURE / ".codeindex.yaml")
    buffer = walk_and_parse(FIXTURE, config)
    seen = [pr.path for node in buffer.directories() for pr in node.parse_results]
    assert len(seen) == len(set(seen)), "a file was parsed more than once"


# --------------------------------------------------------------------------- #
# language-mismatch warning (GH #93)
# --------------------------------------------------------------------------- #
class TestLanguageMismatchWarning:
    """GH #93: ``loomgraph index`` on a Java repo with default
    ``languages=[python]`` silently produced 0 entities. ``graph-export`` must
    surface the same guidance ``list-dirs`` / ``scan-all`` do (single source:
    :func:`language_mismatch_hint`) — the footgun lives at the export layer too,
    because loomgraph consumes graph-export output directly.

    Fixtures place source under ``src/`` because the default ``include`` is
    ``['src/', 'lib/', 'tests/', 'examples/']`` — a file at the repo root is
    outside include roots and wouldn't be scanned at all.
    """

    @staticmethod
    def _write_src(tmp_path: Path, name: str, content: str) -> None:
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / name).write_text(content, encoding="utf-8")

    def test_warns_when_language_not_configured(self, tmp_path) -> None:
        self._write_src(tmp_path, "Foo.java", "class Foo {}\n")
        # no .codeindex.yaml → defaults to languages=[python]
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        # backward compat: still exits 0 and emits NDJSON (does not fail)
        assert result.exit_code == 0
        # the warning surfaces the missing language and points at `languages:`
        assert "java" in result.output.lower()
        assert "languages" in result.output.lower()

    def test_warns_when_few_entities_but_language_mismatch(self, tmp_path) -> None:
        """GH #129: the few-entity false-positive. A TS repo with a stray
        ``.py`` script yields a handful of entities (≠0), so the 0-entity guard
        is bypassed and graph-export silently emits a partial graph with
        ``success:true``. The mismatch warning must still fire — entities > 0
        but ≪ the unconfigured-language code files is exactly the silent
        footgun the 0-entity guard was meant to catch.

        Mirrors the HEXFORCE-RN report: 7 ``.py`` entities + 81 ``.ts``/``.tsx``
        uncaptured, no warning.
        """
        self._write_src(tmp_path, "foo.py", "def f():\n    return 1\n")
        self._write_src(tmp_path, "app.ts", "export const x = 1\n")
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        # still exits 0 and emits NDJSON (does not fail)
        assert result.exit_code == 0
        # the partial-graph warning names the unconfigured language and the
        # captured-entity count, so a consumer/CI doesn't mistake partial for done
        assert "typescript" in result.output.lower()
        assert "partial" in result.output.lower()

    def test_mismatch_warning_filters_non_code_ext(self, tmp_path) -> None:
        """GH #129 comment: the uncaptured list must only name extensions of a
        supported-but-unconfigured language. A stray ``.md``/``.yaml`` is never
        a ``languages:`` target, so listing it (29 ``.md`` in the codeindex
        self-dogfood) drowns the real signal (the ``.ts`` the user should add a
        language for). The list now mirrors ``candidate_languages``'s filter."""
        self._write_src(tmp_path, "foo.py", "def f():\n    return 1\n")
        self._write_src(tmp_path, "app.ts", "export const x = 1\n")
        # noise: non-code files that are never a `languages:` target
        self._write_src(tmp_path, "README.md", "# readme\n")
        self._write_src(tmp_path, "conf.yaml", "key: value\n")
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # isolate the uncaptured-list segment (the parenthesised ext list right
        # after "uncaptured"). Whole-output substring checks false-pass: the
        # NDJSON body mentions "yaml"/"ts" in its provenance blurb, and the
        # warning's own help text names ".codeindex.yaml".
        warn_line = next(
            (ln for ln in result.output.splitlines() if "partial graph" in ln),
            "",
        )
        seg = warn_line.split("uncaptured")[1].split(").")[0]
        # the real code file is named...
        assert ".ts" in seg
        # ...the non-code noise is NOT
        assert ".md" not in seg
        assert ".yaml" not in seg

    def test_no_warning_when_languages_match(self, tmp_path) -> None:
        self._write_src(tmp_path, "foo.py", "def f():\n    return 1\n")
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "no indexable directories" not in result.output

    def test_quiet_suppresses_warning(self, tmp_path) -> None:
        self._write_src(tmp_path, "Foo.java", "class Foo {}\n")
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-", "--quiet"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "java" not in result.output.lower()


class TestIncludeRespected:
    """walk_and_parse must honor ``config.include`` (GH loomgraph#107).

    graph-export previously scanned the whole tree from root, ignoring
    ``.codeindex.yaml include:`` — only ``exclude:`` was applied (via
    ``should_exclude``). So a repo with ``include: [src/]`` still ingested
    ``docs/``/``tests/`` code, polluting downstream topology. scan-all's
    ``find_all_directories`` applies include correctly; graph-export's
    ``walk_and_parse`` must match that behaviour.
    """

    @staticmethod
    def _repo(tmp_path: Path) -> Path:
        """src/ (product code) + docs/spikes/ (non-product code)."""
        src = tmp_path / "src"
        docs = tmp_path / "docs" / "spikes"
        src.mkdir(parents=True)
        docs.mkdir(parents=True)
        (src / "real.py").write_text("def product_fn():\n    return 1\n")
        (docs / "junk.py").write_text("def spike_fn():\n    return 2\n")
        return tmp_path

    def test_include_limits_scan_to_listed_paths(self, tmp_path: Path) -> None:
        root = self._repo(tmp_path)
        (root / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [python]\ninclude: [src/]\n"
        )
        config = Config.load(root / ".codeindex.yaml")
        model = build_export(walk_and_parse(root, config), root)
        names = {e.id for e in model.entities}
        assert any("product_fn" in n for n in names), names
        assert not any("spike_fn" in n for n in names), f"include ignored — docs leaked: {names}"

    def test_no_include_scans_everything(self, tmp_path: Path) -> None:
        """No .codeindex.yaml → graph-export scans the whole tree."""
        root = self._repo(tmp_path)
        config = Config()
        model = build_export(walk_and_parse(root, config), root)
        names = {e.id for e in model.entities}
        assert any("product_fn" in n for n in names)
        assert any("spike_fn" in n for n in names), names

    def test_no_include_key_scans_whole_tree(self, tmp_path: Path) -> None:
        """No `include:` key in .codeindex.yaml → whole-tree scan (root-level repos)."""
        root = self._repo(tmp_path)
        (root / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
        config = Config.load(root / ".codeindex.yaml")
        model = build_export(walk_and_parse(root, config), root)
        names = {e.id for e in model.entities}
        assert any("product_fn" in n for n in names), names
        assert any("spike_fn" in n for n in names), names  # docs NOT excluded w/o include key

