"""In-memory IR between parse and render (GH #101, ADR-007).

``GraphBuffer`` is a per-run, in-memory intermediate representation of a
scanned project. It sits between the *parse* stage and the README *render*
stage, decoupling :class:`~codeindex.writers.SmartWriter` from the live
scan/parse loop.

Scope — Phase 1 (strangler step), deliberately minimal:

* Holds one :class:`DirNode` per indexed directory: the render inputs
  (``level``, ``parse_results``, ``child_dirs``) the renderer currently
  consumes.
* Provides :func:`render_directory` — the seam the eventual SmartWriter flip
  will call. Rendering *from* the buffer must stay byte-identical to the
  direct ``parse -> write_readme`` path (proven by
  ``tests/characterization/test_graphbuffer_equivalence.py``).

Deliberately **out of scope** for Phase 1:

* The global call / inheritance graph and the write-once graph-export
  artifact. Per ADR-007 that substrate is gated on LoomGraph#30 and is not
  built until that consumption spike comes back GREEN.
* Wiring into the production ``scan-all`` loop (the flip). Until the buffer
  is the renderer's source of truth, paying its RAM cost in production buys
  nothing, so it stays test-only for now.

This module is pure data plus a thin adapter: no AI, no I/O of its own beyond
what :meth:`SmartWriter.write_readme` already performs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .parser import ParseResult
from .writers import LevelType, SmartWriter, WriteResult


@dataclass
class DirNode:
    """One indexed directory's render inputs, captured in the buffer.

    Attributes mirror exactly the arguments
    :meth:`SmartWriter.write_readme` consumes, so the buffer is a faithful,
    lossless capture of the renderer's input at the moment of the scan.
    """

    path: Path
    level: LevelType
    parse_results: list[ParseResult] = field(default_factory=list)
    child_dirs: list[Path] = field(default_factory=list)


class GraphBuffer:
    """Per-run, in-memory map of directory -> :class:`DirNode`.

    Insertion is single-threaded *by contract*: callers may produce
    ``parse_results`` with a parallel pool, but each directory is recorded
    once from a single collecting thread. The buffer performs no locking.
    """

    def __init__(self) -> None:
        self._dirs: dict[Path, DirNode] = {}

    def record_directory(
        self,
        dir_path: Path,
        level: LevelType,
        parse_results: list[ParseResult],
        child_dirs: list[Path],
    ) -> DirNode:
        """Capture one directory's render inputs and return the node."""
        node = DirNode(
            path=dir_path,
            level=level,
            parse_results=list(parse_results),
            child_dirs=list(child_dirs),
        )
        self._dirs[dir_path] = node
        return node

    def get(self, dir_path: Path) -> DirNode | None:
        """Return the buffered node for ``dir_path`` (or ``None``)."""
        return self._dirs.get(dir_path)

    def directories(self) -> list[DirNode]:
        """Return all buffered nodes (insertion order)."""
        return list(self._dirs.values())

    def __len__(self) -> int:
        return len(self._dirs)

    def __contains__(self, dir_path: object) -> bool:
        return dir_path in self._dirs


def render_directory(
    writer: SmartWriter,
    node: DirNode,
    output_file: str = "README_AI.md",
) -> WriteResult:
    """Render one directory's README from a buffered :class:`DirNode`.

    This is the seam the eventual SmartWriter flip will use: the renderer's
    inputs come from the buffer, not from a fresh inline parse. It must stay
    byte-identical to ``writer.write_readme(... parse_results ...)`` on the
    same inputs.
    """
    return writer.write_readme(
        dir_path=node.path,
        parse_results=node.parse_results,
        level=node.level,
        child_dirs=node.child_dirs,
        output_file=output_file,
    )
