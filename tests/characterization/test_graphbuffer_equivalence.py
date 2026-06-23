"""Run-both-diff equivalence proof for the GraphBuffer seam (GH #101).

Phase 1 of the strangler refactor introduces ``GraphBuffer`` as an in-memory
IR between parse and render, plus :func:`render_directory` — the seam the
eventual SmartWriter flip will call.

This test is the *run-both-diff*: the same fixture is rendered two ways and
the two README trees must be byte-identical (timestamps normalised):

  A. the production worker  -> parse -> ``write_readme`` directly
  B. the same scan/parse    -> ``GraphBuffer.record_directory`` ->
                               ``render_directory`` (the new seam)

The only thing that differs between A and B is the routing through the
buffer's :class:`DirNode` capture + render adapter, so a green diff proves
the IR is a lossless capture of the renderer's input — the precondition for
flipping the live path in a later phase.

Both sides walk ``tree.get_processing_order()`` single-threaded (deepest
dir first), matching the fixture's ``parallel_workers: 1`` so the parent
overview/navigation READMEs read already-written child READMEs in a
deterministic order.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from codeindex.cli_scan import _process_directory_with_smartwriter
from codeindex.config import Config
from codeindex.directory_tree import DirectoryTree
from codeindex.graph_buffer import GraphBuffer, render_directory
from codeindex.parallel import parse_files_parallel
from codeindex.scanner import scan_directory
from codeindex.smart_writer import SmartWriter

FIXTURE = Path(__file__).parent.parent / "fixtures" / "char_graphbuffer" / "project"
_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+")


def _load(root: Path) -> Config:
    return Config.load(root / ".codeindex.yaml")


def _readmes(root: Path) -> dict[str, str]:
    """Map relative README path -> timestamp-normalised content."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("README_AI.md")):
        rel = path.relative_to(root).as_posix()
        out[rel] = _TS_RE.sub("<TS>", path.read_text())
    return out


def _scan_parse(dir_path: Path, tree: DirectoryTree, config: Config):
    """Replicate the worker's scan+parse (the part shared by both sides)."""
    level = tree.get_level(dir_path)
    child_dirs = tree.get_children(dir_path)
    result = scan_directory(dir_path, config, recursive=level != "overview")
    parse_results = (
        parse_files_parallel(result.files, config, quiet=True) if result.files else []
    )
    return level, parse_results, child_dirs


def _run_in(root: Path, fn) -> None:
    prev = Path.cwd()
    os.chdir(root)
    try:
        fn()
    finally:
        os.chdir(prev)


def test_buffer_render_matches_direct_path(tmp_path: Path) -> None:
    side_a = tmp_path / "a" / "project"
    side_b = tmp_path / "b" / "project"
    shutil.copytree(FIXTURE, side_a)
    shutil.copytree(FIXTURE, side_b)

    # Side A: the real production worker (direct parse -> write_readme).
    def run_a() -> None:
        config = _load(side_a)
        tree = DirectoryTree(side_a, config)
        for d in tree.get_processing_order():
            _, success, msg, _ = _process_directory_with_smartwriter(d, tree, config, None)
            assert success, f"A failed for {d}: {msg}"

    # Side B: identical scan/parse, but render THROUGH the GraphBuffer seam.
    def run_b() -> None:
        config = _load(side_b)
        tree = DirectoryTree(side_b, config)
        buffer = GraphBuffer()
        for d in tree.get_processing_order():
            level, parse_results, child_dirs = _scan_parse(d, tree, config)
            node = buffer.record_directory(d, level, parse_results, child_dirs)
            # Fresh writer per dir to match A exactly (isolate the adapter as
            # the sole variable, not writer-instance reuse).
            writer = SmartWriter(config.indexing)
            res = render_directory(writer, node, output_file=config.output_file)
            assert res.success, f"B failed for {d}: {res.error}"
        # The buffer must have captured exactly the processed directories.
        assert len(buffer) == len(tree.get_processing_order())

    _run_in(side_a, run_a)
    _run_in(side_b, run_b)

    a_readmes = _readmes(side_a)
    b_readmes = _readmes(side_b)

    assert set(a_readmes) == set(b_readmes), (
        f"README sets differ: A-only={set(a_readmes) - set(b_readmes)}, "
        f"B-only={set(b_readmes) - set(a_readmes)}"
    )
    for rel in sorted(a_readmes):
        assert a_readmes[rel] == b_readmes[rel], (
            f"buffer-render drift in {rel} (#101 seam must be byte-identical)"
        )
