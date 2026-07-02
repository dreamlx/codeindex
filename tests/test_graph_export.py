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
    assert by_id["app.workers.kickoff"].signature == "def kickoff(obj) -> None"
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
    assert rec["signature"] == "def kickoff(obj) -> None"


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
    e = _edge(_model(), "app.workers.kickoff")
    assert e.resolution_qualifier == "ambiguous"
    assert e.dst is None
    assert e.candidates == ["app.workers.Builder.run", "app.workers.Packer.run"]


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
# whole-file invariants
# --------------------------------------------------------------------------- #
def test_meta_and_ndjson_shape() -> None:
    text = dump_ndjson(_model())
    first = json.loads(text.splitlines()[0])
    assert first["type"] == "meta"
    assert first["schema_version"] == 0
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
