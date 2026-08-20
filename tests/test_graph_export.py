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


def test_python_factory_return_resolves_method_call(tmp_path) -> None:
    """GH #185: ``store = await create_store()`` where ``create_store() ->
    Store`` is an annotated factory. The later ``store.create_entity()`` was
    previously unresolved (dotted callee = dynamic dispatch, GH #127): the
    receiver ``store`` is a local var whose type is statically unknowable in
    general. But here the type IS knowable — it is the factory's return
    annotation, and the factory call is a direct, same-scope assignment.
    Propagate the return type to the var, resolve the method against the
    in-workspace class. The normal factory call edge is retained."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "class Store:\n"
        "    async def create_entity(self) -> None: ...\n"
        "async def create_store() -> Store:\n"
        "    return Store()\n"
        "async def run() -> None:\n"
        "    store = await create_store()\n"
        "    await store.create_entity()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    calls = [e for e in model.edges if e.kind == "CALLS" and e.src == "svc.run"]
    # factory edge retained: run -> svc.create_store
    factory = [e for e in calls if e.dst == "svc.create_store"]
    assert len(factory) == 1
    assert factory[0].resolution_qualifier == "resolved"
    assert factory[0].dst_raw == "create_store"
    # NEW: resolved method call through factory return type
    method = [e for e in calls if e.dst == "svc.Store.create_entity"]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "resolved"
    assert method[0].dst_raw == "store.create_entity"


def test_python_factory_return_sync(tmp_path) -> None:
    """GH #185 sync variant: ``store = create_store()`` (no await). Same
    resolution as the async factory."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "class Store:\n"
        "    def create_entity(self) -> None: ...\n"
        "def create_store() -> Store:\n"
        "    return Store()\n"
        "def run() -> None:\n"
        "    store = create_store()\n"
        "    store.create_entity()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    method = [
        e for e in model.edges
        if e.kind == "CALLS" and e.src == "svc.run"
        and e.dst == "svc.Store.create_entity"
    ]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "resolved"
    assert method[0].dst_raw == "store.create_entity"


def test_python_factory_return_unannotated(tmp_path) -> None:
    """GH #185 boundary: factory with NO return annotation. The receiver type
    is genuinely unknowable; must stay unresolved (no synthesized edge)."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "class Store:\n"
        "    def create_entity(self) -> None: ...\n"
        "def create_store():  # no return annotation\n"
        "    return Store()\n"
        "def run() -> None:\n"
        "    store = create_store()\n"
        "    store.create_entity()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    method = [
        e for e in model.edges
        if e.kind == "CALLS" and e.src == "svc.run"
        and e.dst_raw == "store.create_entity"
    ]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "unresolved"
    assert method[0].dst is None


def test_python_factory_return_union_or_optional(tmp_path) -> None:
    """GH #185 boundary: ``-> Store | None`` and ``-> Optional[Store]`` are
    union/parameterized returns. A union member is not a single in-workspace
    class — resolving it would manufacture a possibly-wrong edge. Must stay
    unresolved."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "from typing import Optional\n"
        "class Store:\n"
        "    def create_entity(self) -> None: ...\n"
        "def create_store_union() -> Store | None:\n"
        "    return Store()\n"
        "def create_store_opt() -> Optional[Store]:\n"
        "    return Store()\n"
        "def run() -> None:\n"
        "    a = create_store_union()\n"
        "    a.create_entity()\n"
        "    b = create_store_opt()\n"
        "    b.create_entity()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    for raw in ("a.create_entity", "b.create_entity"):
        method = [
            e for e in model.edges
            if e.kind == "CALLS" and e.src == "svc.run" and e.dst_raw == raw
        ]
        assert len(method) == 1
        assert method[0].resolution_qualifier == "unresolved"
        assert method[0].dst is None


def test_python_factory_return_external_class(tmp_path) -> None:
    """GH #185 boundary: factory returns an external class (``os.PathLike``)
    not in the scan tree. No entity to resolve to → unresolved."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "import os\n"
        "def make_path() -> os.PathLike:\n"
        "    return os.PathLike()\n"
        "def run() -> None:\n"
        "    p = make_path()\n"
        "    p.is_absolute()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    method = [
        e for e in model.edges
        if e.kind == "CALLS" and e.src == "svc.run"
        and e.dst_raw == "p.is_absolute"
    ]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "unresolved"
    assert method[0].dst is None


def test_python_factory_return_no_such_method(tmp_path) -> None:
    """GH #185 boundary: factory returns an in-workspace class, but the called
    method does not exist on it. Must NOT synthesize a ghost edge to a phantom
    method — stay unresolved."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "class Store:\n"
        "    def create_entity(self) -> None: ...\n"
        "def create_store() -> Store:\n"
        "    return Store()\n"
        "def run() -> None:\n"
        "    store = create_store()\n"
        "    store.missing()  # not on Store\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    method = [
        e for e in model.edges
        if e.kind == "CALLS" and e.src == "svc.run"
        and e.dst_raw == "store.missing"
    ]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "unresolved"
    assert method[0].dst is None


def test_python_factory_return_descends_to_subclass_impl(tmp_path) -> None:
    """GH #185 extension (base-class descent): the factory's return type names
    an abstract base (``-> Store(ABC)``) whose ``@abstractmethod`` has no
    method entity (parser skips abstract methods), while the concrete impl
    lives on a single in-workspace subclass. The receiver ``store.method()``
    must resolve to the subclass impl, not stay unresolved.

    This is the common Python DI shape (``create_session() -> Session(ABC)``,
    ``create_graph_store() -> GraphStore(ABC)``) and the most frequent factory
    pattern in real codebases. Without descent, every factory-routed call to an
    ABC method reads as an orphan — ``loomgraph graph insert_custom_kg`` shows
    0 callers despite 3 factory-wide call sites (GH loomgraph #230)."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "from abc import ABC, abstractmethod\n"
        "class Store(ABC):\n"
        "    @abstractmethod\n"
        "    def write(self) -> None: ...\n"
        "class SqliteStore(Store):\n"
        "    def write(self) -> None: ...\n"
        "async def create_store() -> Store:\n"
        "    return SqliteStore()\n"
        "async def run() -> None:\n"
        "    store = await create_store()\n"
        "    store.write()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    method = [
        e for e in model.edges
        if e.kind == "CALLS" and e.src == "svc.run"
        and e.dst_raw == "store.write"
    ]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "resolved"
    # descends to the subclass impl, not the abstract base (which has no entity)
    assert method[0].dst == "svc.SqliteStore.write"


def test_python_factory_return_descends_ambiguous_multiple_subclasses(tmp_path) -> None:
    """GH #185 boundary: when two subclasses both override the method, descent
    is genuinely ambiguous (dynamic dispatch) — must NOT guess, stay
    unresolved. Mirrors the AMBIGUOUS contract of bare callees."""
    (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
    (tmp_path / "svc.py").write_text(
        "from abc import ABC, abstractmethod\n"
        "class Store(ABC):\n"
        "    @abstractmethod\n"
        "    def write(self) -> None: ...\n"
        "class SqliteStore(Store):\n"
        "    def write(self) -> None: ...\n"
        "class PgStore(Store):\n"
        "    def write(self) -> None: ...\n"
        "async def create_store() -> Store:\n"
        "    return SqliteStore()\n"
        "async def run() -> None:\n"
        "    store = await create_store()\n"
        "    store.write()\n"
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    method = [
        e for e in model.edges
        if e.kind == "CALLS" and e.src == "svc.run"
        and e.dst_raw == "store.write"
    ]
    assert len(method) == 1
    assert method[0].resolution_qualifier == "unresolved"
    assert method[0].dst is None


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


def test_ts_path_alias_dotprefix_target(tmp_path) -> None:
    """GH #144: paths targets commonly carry a leading ``./`` (Vite, Next.js,
    fabricOS — and the TS handbook example itself): ``"@/*": ["./src/*"]``.
    Before #144 the ``_dot`` closure inside ``_load_tsconfig_paths`` did a raw
    ``.replace("/", ".")`` which turned ``./src/*`` into ``..src.*`` (leading
    ``.`` → dot, then ``src`` → ``..src``), never matching ``module_set``'s
    ``src.*`` entries → 100% of ``@/`` alias imports stayed unresolved.
    Fix: normalize like ``baseUrl`` already does (drop empty + ``.`` segments)."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps({"compilerOptions": {"paths": {"@/*": ["./src/*"]}}})
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
    assert imp is not None, "dotprefix-target alias IMPORTS edge missing"
    assert imp.resolution_qualifier == "resolved"
    assert imp.dst_raw == "@/components/Foo"

    ref = _edge(
        model, "src.app", dst="src.components.Foo.Foo", kind="REFERENCES"
    )
    assert ref is not None, "dotprefix-target alias REFERENCES edge missing"


def test_ts_path_alias_dotprefix_with_baseurl(tmp_path) -> None:
    """GH #144: ``./``-prefix must also be stripped when ``baseUrl`` is set —
    ``baseUrl: "src"`` + ``paths: {"@/*": ["./components/*"]}`` → ``@/Foo``
    resolves to ``src.components.Foo``. Before #144 ``./components/*`` became
    ``..components.*`` and with base_prefix → ``src...components.*`` (orphan)."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "baseUrl": "src",
                    "paths": {"@/*": ["./components/*"]},
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
    assert e is not None, "dotprefix-target + baseUrl IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"




# --------------------------------------------------------------------------- #
# TS barrel resolution (GH #140) — `from "."` / `from "./sub"` + re-export
# Independent tmp_path fixtures. `from "."` (current dir's index.ts) was routed
# through the Python PEP 328 branch and produced the right directory id, but
# _resolve_module had no `.index` fallback (only `.__init__`), so barrel
# IMPORTS/REFERENCES edges were dropped. Named re-exports (`export { X } from
# "./mod"` in a barrel) were indistinguishable from regular imports, so
# `import { X } from "."` reaching a barrel could not follow the re-export to
# the real definition module. Wildcard `export * from` stays out of scope.
# --------------------------------------------------------------------------- #
def test_ts_from_dot_resolves_to_index(tmp_path) -> None:
    """GH #140: ``import { foo } from "."`` (web/main.ts) targets the current
    directory's ``index.ts``. The PEP 328 branch yields the dir id ``web``;
    the new ``.index`` fallback resolves it to ``web.index``. Before #140 there
    was no `.index` fallback (only `.__init__`), so the barrel module never
    resolved → zero IMPORTS/REFERENCES edges → orphan false-positive."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.ts").write_text("export function foo(): number { return 1; }\n")
    (web / "main.ts").write_text(
        'import { foo } from ".";\nexport function run() { return foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    imp = _edge(model, "web.main", dst="web.index", kind="IMPORTS")
    assert imp is not None, "from '.' IMPORTS edge missing"
    assert imp.resolution_qualifier == "resolved"
    assert imp.dst_raw == "."

    ref = _edge(model, "web.main", dst="web.index.foo", kind="REFERENCES")
    assert ref is not None, "from '.' REFERENCES edge missing"


def test_ts_from_subdir_resolves_to_index(tmp_path) -> None:
    """GH #140: ``import { foo } from "./components"`` targets a subdirectory
    whose ``index.ts`` is the module. ``./components`` → dir id
    ``web.components`` → ``.index`` fallback → ``web.components.index``."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    web = tmp_path / "web"
    comp = web / "components"
    comp.mkdir(parents=True)
    (comp / "index.ts").write_text("export function foo(): number { return 1; }\n")
    (web / "main.ts").write_text(
        'import { foo } from "./components";\nexport function run() { return foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "web.main", dst="web.components.index", kind="IMPORTS")
    assert e is not None, "from './subdir' IMPORTS edge missing"
    assert e.resolution_qualifier == "resolved"


def test_ts_barrel_named_reexport_propagates(tmp_path) -> None:
    """GH #140 core: barrel re-export propagation. ``web/index.ts`` does
    ``export { fetchUser } from "./api"`` (re-exports api's symbol — it does
    NOT define ``fetchUser`` locally). Downstream ``import { fetchUser } from
    "."`` resolves the module to ``web.index`` but ``web.index.fetchUser`` is
    not a local entity. The re-export pre-pass builds
    ``{web.index: {fetchUser: web.api}}`` and Pass 4 follows the chain to the
    real definition ``web.api.fetchUser``. Without this, ``fetchUser`` got zero
    in-edges → falsely orphan downstream."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    web = tmp_path / "web"
    web.mkdir()
    (web / "api.ts").write_text("export function fetchUser(): number { return 1; }\n")
    (web / "index.ts").write_text('export { fetchUser } from "./api";\n')
    (web / "main.ts").write_text(
        'import { fetchUser } from ".";\nexport function run() { return fetchUser(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    # module resolves to the barrel
    imp = _edge(model, "web.main", dst="web.index", kind="IMPORTS")
    assert imp is not None, "barrel IMPORTS edge missing"

    # REFERENCES edge follows the re-export to the real definition module
    ref = _edge(model, "web.main", dst="web.api.fetchUser", kind="REFERENCES")
    assert ref is not None, "barrel re-export REFERENCES edge missing"
    assert ref.dst_raw == "..fetchUser"  # dst_raw = imp.module + "." + name = "." + "fetchUser"


def test_ts_barrel_chained_reexport(tmp_path) -> None:
    """GH #140: chained barrels (A → B → C → definition). ``web/index.ts``
    re-exports from ``./b``, which re-exports from ``./c``, which defines
    ``foo``. Pass 4's while-loop follows the chain through two barrels to
    ``web.c.foo``."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    web = tmp_path / "web"
    web.mkdir()
    (web / "c.ts").write_text("export function foo(): number { return 1; }\n")
    (web / "b.ts").write_text('export { foo } from "./c";\n')
    (web / "index.ts").write_text('export { foo } from "./b";\n')
    (web / "main.ts").write_text(
        'import { foo } from ".";\nexport function run() { return foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    ref = _edge(model, "web.main", dst="web.c.foo", kind="REFERENCES")
    assert ref is not None, "chained barrel re-export REFERENCES edge missing"


def test_ts_barrel_reexport_cycle_safe(tmp_path) -> None:
    """GH #140 guard: cyclic re-exports (a re-exports from b, b re-exports
    from a) must terminate — the ``visited`` set breaks the cycle — and emit
    NO REFERENCES edge for the unresolved name (honest unresolved, no hang, no
    ghost edge)."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    web = tmp_path / "web"
    web.mkdir()
    # Neither a nor b defines `foo` locally — they only re-export each other.
    (web / "a.ts").write_text('export { foo } from "./b";\n')
    (web / "b.ts").write_text('export { foo } from "./a";\n')
    (web / "index.ts").write_text('export { foo } from "./a";\n')
    (web / "main.ts").write_text(
        'import { foo } from ".";\nexport function run() { return 0; }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    refs = [
        e for e in model.edges
        if e.kind == "REFERENCES" and e.src == "web.main" and e.dst and "foo" in e.dst
    ]
    assert refs == [], f"cyclic re-export must not manufacture a foo edge: {refs}"


def test_ts_barrel_wildcard_still_skipped(tmp_path) -> None:
    """GH #140 guard: wildcard ``export * from "./api"`` in a barrel is still
    skipped (documented out-of-scope at :502-503 — needs cross-file member
    tracking). The barrel module IMPORTS edge IS emitted; the propagated
    REFERENCES edge for ``foo`` is NOT. Must not crash and must not
    manufacture a ghost edge."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    web = tmp_path / "web"
    web.mkdir()
    (web / "api.ts").write_text("export function foo(): number { return 1; }\n")
    (web / "index.ts").write_text('export * from "./api";\n')
    (web / "main.ts").write_text(
        'import { foo } from ".";\nexport function run() { return foo(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    imp = _edge(model, "web.main", dst="web.index", kind="IMPORTS")
    assert imp is not None, "wildcard barrel IMPORTS edge missing"

    ref = _edge(model, "web.main", dst="web.api.foo", kind="REFERENCES")
    assert ref is None, "wildcard re-export must NOT propagate (out of scope)"


def test_ts_barrel_reexport_via_alias(tmp_path) -> None:
    """GH #139 + #140 interaction: a barrel re-export using an alias specifier
    (``export { fetchUser } from "@/api"``). The re-export pre-pass calls
    _resolve_module with ``alias_map``, so the alias expands before the barrel
    table is built, and Pass 4 follows the chain to ``src.api.fetchUser``.
    Without #139 landing first, this re-export target would be unresolved."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [typescript]\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps({"compilerOptions": {"paths": {"@/*": ["src/*"]}}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "api.ts").write_text("export function fetchUser(): number { return 1; }\n")
    (src / "index.ts").write_text('export { fetchUser } from "@/api";\n')
    (src / "main.ts").write_text(
        'import { fetchUser } from ".";\nexport function run() { return fetchUser(); }\n'
    )
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    ref = _edge(model, "src.main", dst="src.api.fetchUser", kind="REFERENCES")
    assert ref is not None, "barrel re-export via alias REFERENCES edge missing"


def test_python_from_dot_still_uses_init(tmp_path) -> None:
    """GH #140 guard: Python ``from . import X`` must still resolve to the
    ``__init__`` module (NOT the TS ``.index`` fallback). ``.__init__`` is
    checked before ``.index`` in ``_check_fallbacks`` so a (pathological)
    mixed Python+TS dir resolves to the Python package. This re-asserts the
    #133 ``__init__`` path is unaffected by the new ``.index`` branch."""
    (tmp_path / ".codeindex.yaml").write_text(
        "version: 1\nlanguages: [python]\n"
    )
    pkg = tmp_path / "pkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (sub / "__init__.py").write_text("")
    (sub / "svc.py").write_text("def s():\n    return 1\n")
    (sub / "cli.py").write_text("from . import svc\n")
    config = Config.load(tmp_path / ".codeindex.yaml")
    model = build_export(walk_and_parse(tmp_path, config), tmp_path)

    e = _edge(model, "pkg.sub.cli", dst="pkg.sub.__init__", kind="IMPORTS")
    assert e is not None, "Python from . import X edge missing"
    assert e.resolution_qualifier == "resolved"
    assert e.dst == "pkg.sub.__init__"  # NOT pkg.sub.index
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

    @staticmethod
    def _write_python_config(proj: Path) -> None:
        """Force python-only languages so the test is isolated from the host
        repo's gitignored ``.codeindex.yaml``. ``CliRunner().invoke`` does
        not change cwd, so ``Config.load(None)`` would otherwise read
        ``Path.cwd()/.codeindex.yaml`` — on the codeindex dev machine that's a
        5-language dogfood config, so java/typescript are already "configured"
        and the mismatch hint returns None. Writing an explicit python-only
        config under the ``--root`` (read by cli_graph_export.py:44) forces
        the real footgun regardless of where the test runs (GH #177 release
        flow fix)."""
        (proj / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [python]\n", encoding="utf-8"
        )

    def test_warns_when_language_not_configured(self, tmp_path) -> None:
        self._write_src(tmp_path, "Foo.java", "class Foo {}\n")
        self._write_python_config(tmp_path)
        # no .codeindex.yaml → defaults to languages=[python]
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        # GH #147: 0-entity export = data-loss-class (empty graph consumed by
        # loomgraph) → exit non-zero so CI/tooling detect it (was: exit 0).
        assert result.exit_code != 0
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
        self._write_python_config(tmp_path)
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
        self._write_python_config(tmp_path)
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
        self._write_python_config(tmp_path)
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
        self._write_python_config(tmp_path)
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-", "--quiet"],
            catch_exceptions=False,
        )
        # GH #147: --quiet must not bypass the data-loss exit code (exit code is
        # a machine signal, not output); the hint text stays suppressed.
        assert result.exit_code != 0
        assert "java" not in result.output.lower()


# --------------------------------------------------------------------------- #
# unresolved breakdown + high-ratio warning (GH #148)
# --------------------------------------------------------------------------- #
class TestUnresolvedBreakdown:
    """GH #148: the graph-export summary reported only a flat ``N unresolved``
    total, so a dogfood repo drowned by test-library calls (``expect``/
    ``screen``/``jest``) was indistinguishable from a graph hitting the AST
    ceiling (``this.x``/``obj.run`` dynamic dispatch, GH #127).

    Two additions share the summary pipe:
      (a) breakdown — bucket unresolved edges by ``dst_raw`` shape into
          ``bare`` (no ``.``: external / stdlib / test-framework globals) and
          ``member`` (dotted: dynamic dispatch, the AST ceiling).
      (b) hint, not gate — if unresolved CALLS exceed ~70% of CALLS, emit a
          WARNING pointing at test files. IMPORTS-unresolved is by-design
          (external packages) and deliberately excluded from the ratio so a
          normal repo with many external imports doesn't false-fire. Per
          ``no_gate_from_dogfood`` this never auto-excludes; the user keeps
          control.
    """

    def test_breakdown_buckets_bare_and_member(self) -> None:
        from codeindex.graph_export import Edge, _unresolved_breakdown

        edges = [
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:1",
                dst_raw="expect",
            ),
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:2",
                dst_raw="this.run",
            ),
            Edge(
                kind="CALLS",
                src="m.a",
                dst="m.b",
                resolution_qualifier="resolved",
                source_id="a.py:3",
                dst_raw="b",
            ),
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="ambiguous",
                source_id="a.py:4",
                dst_raw="dup",
            ),
            Edge(
                kind="IMPORTS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:5",
                dst_raw="react",
            ),
            # empty dst_raw counts as bare (no dot)
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:6",
                dst_raw="",
            ),
        ]
        bd = _unresolved_breakdown(edges)
        # bare = expect, react, "" (3); member = this.run (1); sums to all unresolved (4)
        assert bd == {"bare": 3, "member": 1}

    def test_calls_unresolved_ratio(self) -> None:
        from codeindex.graph_export import Edge, _calls_unresolved_ratio

        # no CALLS edges → None (avoid divide-by-zero, nothing to warn about)
        assert _calls_unresolved_ratio([]) is None
        assert _calls_unresolved_ratio(
            [
                Edge(
                    kind="IMPORTS",
                    src="m.a",
                    dst=None,
                    resolution_qualifier="unresolved",
                    source_id="a.py:1",
                    dst_raw="react",
                )
            ]
        ) is None

        # ratio is over CALLS only: imports don't expand the denominator
        edges = [
            Edge(
                kind="CALLS",
                src="m.a",
                dst="m.b",
                resolution_qualifier="resolved",
                source_id="a.py:1",
                dst_raw="b",
            ),
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:2",
                dst_raw="print",
            ),
            Edge(
                kind="IMPORTS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:3",
                dst_raw="os",
            ),
        ]
        # 1 unresolved call / 2 calls = 0.5
        assert _calls_unresolved_ratio(edges) == 0.5

        # all calls unresolved → 1.0
        all_unres = [
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:1",
                dst_raw="expect",
            ),
            Edge(
                kind="CALLS",
                src="m.a",
                dst=None,
                resolution_qualifier="unresolved",
                source_id="a.py:2",
                dst_raw="screen",
            ),
        ]
        assert _calls_unresolved_ratio(all_unres) == 1.0

    def test_cli_warns_on_high_unresolved_ratio(self, tmp_path) -> None:
        """A function whose body calls only external/test-framework names
        yields 100% unresolved CALLS → the high-ratio WARNING must fire and
        name test files as the likely cause."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "t.py").write_text(
            "def f():\n    expect(screen).toBe(1)\n    render(x)\n", encoding="utf-8"
        )
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", str(tmp_path / "out.ndjson")],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # the high-ratio WARNING (not the dim "unresolved" total) names test files
        assert "high unresolved" in result.output.lower()
        assert "test" in result.output.lower()

    def test_cli_no_warning_when_low_ratio(self, tmp_path) -> None:
        """A repo with a healthy resolved-call majority (one internal call
        resolved, one external) sits at 50% — below the 70% threshold, so no
        high-ratio WARNING."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "t.py").write_text(
            "def a():\n    return 1\n"
            "def b():\n    a()\n    print(1)\n",
            encoding="utf-8",
        )
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", str(tmp_path / "out.ndjson")],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # the dim summary line still names "unresolved", but no WARNING line
        assert "WARNING" not in result.output


# --------------------------------------------------------------------------- #
# Java entity-id / edge-src de-doubling (GH #154 Part 1)
# --------------------------------------------------------------------------- #
class TestJavaEntityIdDeDouble:
    """GH #154: a Java file is named after its public class, so the module path
    already ends in the class name. The parser's ``sym.name`` / ``caller`` /
    inheritance ``child`` ALSO carry the class (``Foo.bar``), so a naive
    ``f"{module}.{name}"`` DOUBLES it: ``...Foo.Foo.bar``. Doubled ids never
    match the (un-doubled) callee ``dst_raw``, so ~all Java CALLS go unresolved
    and loomgraph sees a 60%-orphan graph (PetClinic).

    The fix collapses when the module's last segment == the name's first
    segment. No-op for Python/TS (file name ≠ class name, condition never
    matches). MUST de-double both entity ids AND edge ``src`` — de-doubling
    only ids breaks ``src == entity.id`` and orphans edges at the source
    (spike measured orphan 60%→79% for ids-only, 60%→41% for both).
    """

    @staticmethod
    def _java_repo(tmp_path: Path) -> Path:
        """One Java class Foo with two methods; baz() calls bar()."""
        (tmp_path / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [java]\ninclude: [src/]\n"
        )
        pkg = tmp_path / "src" / "com" / "example"
        pkg.mkdir(parents=True)
        (pkg / "Foo.java").write_text(
            "package com.example;\n"
            "public class Foo {\n"
            "    public void bar() {}\n"
            "    public void baz() { bar(); }\n"
            "}\n",
            encoding="utf-8",
        )
        return tmp_path

    def test_entity_ids_not_doubled(self, tmp_path: Path) -> None:
        root = self._java_repo(tmp_path)
        config = Config.load(root / ".codeindex.yaml")
        model = build_export(walk_and_parse(root, config), root)
        ids = {e.id for e in model.entities}
        # class + 2 methods, all single-class. Java collapses both the triple
        # (Foo.Foo.bar → Foo.bar) and the class double (Foo.Foo → Foo) via the
        # is_java gate. TS function double is NOT collapsed (no is_java).
        assert "src.com.example.Foo" in ids, ids
        assert "src.com.example.Foo.bar" in ids, ids
        assert "src.com.example.Foo.baz" in ids, ids
        assert not any("Foo.Foo" in i for i in ids), f"doubled id present: {ids}"

    def test_calls_src_not_doubled(self, tmp_path: Path) -> None:
        """edge.src must match the entity-id form (single class), else the
        edge orphanes at the source even when the callee resolves."""
        root = self._java_repo(tmp_path)
        config = Config.load(root / ".codeindex.yaml")
        model = build_export(walk_and_parse(root, config), root)
        calls = [e for e in model.edges if e.kind == "CALLS"]
        assert calls, "no CALLS edges emitted (fixture parse issue)"
        # every CALLS src is single-class form, landing on a real entity id
        ids = {e.id for e in model.entities}
        assert not any(".Foo.Foo" in e.src for e in calls), f"doubled src: {[e.src for e in calls]}"
        for e in calls:
            assert e.src in ids, f"CALLS src {e.src!r} not an entity id (orphaned at source)"

    def test_inherits_src_lands_on_class_entity(self, tmp_path: Path) -> None:
        """INHERITS child is a FQN (``com.example.Sub``); its src must land on
        the class entity id. The class id keeps the simple-name double
        (``...Sub.Sub``) per _qualified_id — what matters is src == entity id,
        not that the id is single."""
        (tmp_path / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [java]\ninclude: [src/]\n"
        )
        pkg = tmp_path / "src" / "com" / "example"
        pkg.mkdir(parents=True)
        (pkg / "Base.java").write_text("package com.example;\npublic class Base {}\n")
        (pkg / "Sub.java").write_text(
            "package com.example;\npublic class Sub extends Base {}\n"
        )
        config = Config.load(tmp_path / ".codeindex.yaml")
        model = build_export(walk_and_parse(tmp_path, config), tmp_path)
        ids = {e.id for e in model.entities}
        inh = [e for e in model.edges if e.kind == "INHERITS"]
        assert inh, "no INHERITS edges emitted"
        for e in inh:
            assert e.src in ids, f"INHERITS src {e.src!r} not an entity id (orphaned at source); ids={ids}"

    def test_ts_function_double_not_collapsed(self, tmp_path: Path) -> None:
        """GH #154: the is_java gate means a TS function named after its file
        KEEPS the module.name double (``Foo.ts`` → ``...Foo.Foo``). TS
        REFERENCES resolution depends on this form; collapsing it (treating TS
        like Java) would orphan every named-import reference edge."""
        (tmp_path / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [typescript]\n"
        )
        pkg = tmp_path / "src" / "components"
        pkg.mkdir(parents=True)
        (pkg / "Foo.ts").write_text("export function Foo(): number { return 1; }\n")
        config = Config.load(tmp_path / ".codeindex.yaml")
        model = build_export(walk_and_parse(tmp_path, config), tmp_path)
        ids = {e.id for e in model.entities}
        # the double is preserved (TS, not Java) — REFERENCES depends on it
        assert "src.components.Foo.Foo" in ids, ids


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


# --------------------------------------------------------------------------- #
# repo-wide language fingerprint (GH #175)
# --------------------------------------------------------------------------- #
class TestLanguageFingerprint:
    """GH #175: the diagnose_language_mismatch hint walks ``config.include``
    (default ``[src/, lib/, tests/, examples/]``), but graph-export with no
    explicit ``include`` scans the **whole tree**. A repo whose real source
    lives outside those default include roots (a RN app with TS under ``app/``,
    or a root-level project with TS at the root) is a diagnostic blind spot:
    ``language_mismatch_hint`` returns None, so the 0-entity gate's carve-out
    ("truly empty → exit 0") fires on a repo that is *not* empty, and a
    few-entity export (stray ``.py`` under ``ios/Pods/``) emits no partial-graph
    warning because ``diagnose_language_mismatch`` never saw the uncaptured TS.

    The fingerprint walks the whole tree (not ``config.include``) so it catches
    what the diagnose blind spot misses. Mirrors loomgraph's
    ``_language_fingerprint_warning`` (loomgraph#161) — same threshold, same
    skip dirs, same advisory (non-blocking) shape for the >0-entity case.
    """

    @staticmethod
    def _write_ts(repo: Path, n: int) -> None:
        """Seed ``n`` .tsx files so the count clears the ≥10 threshold."""
        d = repo / "app"
        d.mkdir(exist_ok=True)
        for i in range(n):
            (d / f"c{i}.tsx").write_text(
                f"export const C{i} = () => {i};\n", encoding="utf-8"
            )

    def test_root_level_ts_repo_zero_entities_fail_loud(self, tmp_path) -> None:
        """Pure-TS repo at the root (no ``src/``, no ``.codeindex.yaml``):
        0 indexable files → 0 entities. ``language_mismatch_hint`` is None
        (default include roots don't exist), so the old carve-out exited 0
        silently. The fingerprint sees the TS, so 0 entities + a real language
        present = data-loss (empty graph consumed by loomgraph) → exit non-zero,
        mirroring the #147 0-entity fail-loud for the diagnose blind spot.

        Note: ``CliRunner().invoke`` does NOT change cwd, so ``Config.load``
        would read the codeindex repo's own ``.codeindex.yaml`` (which has
        ``languages: [python, java, php, typescript, javascript]``) and the
        TS would be *captured*, not missed. Writing an explicit python-only
        ``.codeindex.yaml`` in the temp repo forces the real footgun
        (python-only default on a TS repo) regardless of where the test runs.
        """
        self._write_ts(tmp_path, 12)
        (tmp_path / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [python]\n", encoding="utf-8"
        )
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        assert result.exit_code != 0, result.output
        assert "typescript" in result.output.lower(), result.output
        assert "fingerprint" in result.output.lower(), result.output

    def test_rn_shape_stray_py_under_pods_warns_advisory(self, tmp_path) -> None:
        """HEXFORCE-RN shape: TS under ``app/`` (outside default include),
        stray ``.py`` under ``ios/Pods/``. graph-export scans the whole tree
        → captures the stray ``.py`` entities (>0), so this is NOT the 0-entity
        gate. But ``diagnose_language_mismatch`` walks ``config.include``
        (blind to ``app/``) → candidate_languages empty → the #131 partial-graph
        warning never fires. The fingerprint walks the whole tree and catches
        the uncaptured TS — advisory only (exit 0): the graph is partial, not
        empty, so the user gets a warning but CI isn't broken.

        Explicit python-only ``.codeindex.yaml`` (see the sibling test's note
        on CliRunner/cwd) forces the real footgun.
        """
        self._write_ts(tmp_path, 12)
        pods = tmp_path / "ios" / "Pods" / "Boost"
        pods.mkdir(parents=True)
        (pods / "build.py").write_text("def build(): return 1\n", encoding="utf-8")
        (pods / "fix.py").write_text("def fix(): return 1\n", encoding="utf-8")
        (tmp_path / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [python]\n", encoding="utf-8"
        )
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        # >0 entities → advisory, not data-loss → exit 0 (graph is partial,
        # not empty)
        assert result.exit_code == 0, result.output
        assert "typescript" in result.output.lower(), result.output
        assert "fingerprint" in result.output.lower(), result.output

    def test_no_fingerprint_when_languages_cover_source(self, tmp_path) -> None:
        """Negative: a pure-python repo with a python-only ``.codeindex.yaml``
        has its dominant language (python) == the effective languages → no
        fingerprint warning. Guards against false-positives on python repos
        (the common case)."""
        src = tmp_path / "src"
        src.mkdir()
        for i in range(12):
            (src / f"m{i}.py").write_text(
                f"def f{i}(): return {i}\n", encoding="utf-8"
            )
        (tmp_path / ".codeindex.yaml").write_text(
            "version: 1\nlanguages: [python]\n", encoding="utf-8"
        )
        from click.testing import CliRunner

        from codeindex.cli import main

        result = CliRunner().invoke(
            main,
            ["graph-export", "--root", str(tmp_path), "-o", "-"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        assert "fingerprint" not in result.output.lower(), result.output

