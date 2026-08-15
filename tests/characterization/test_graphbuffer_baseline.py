"""Characterization net for the GraphBuffer IR refactor (GH #101).

This is the **safety net** for a refactor-under-net: it pins the current
(master) behaviour of the scan -> parse -> write pipeline so the upcoming
GraphBuffer restructure can be proven to change *nothing observable*.

Per ADR-007 / #101 the equivalence guarantee is:

    "everything deterministic" + "what is fed to the AI" stays byte-identical;
    the AI's stochastic output is NOT in scope (it varies on master already).

Three hard-gate layers, all on a Python + TS fixture:

  1. PROJECT_SYMBOLS.md          -> golden byte-diff (pure structure)
  2. README_AI.md structure      -> golden byte-diff, AI frozen (mock invoker)
  3. prompt fed to the AI        -> golden byte-diff (guards #94-class silent
                                    quality regressions: GraphBuffer changing
                                    the AI context while structure stays green)

Non-determinism is normalised out:
  * the scan root path           -> ``<ROOT>``
  * ISO timestamps in generator  -> ``<TS>``
    comments

Regenerate goldens (after an intentional, reviewed behaviour change) with::

    CODEINDEX_UPDATE_GOLDEN=1 pytest tests/characterization/test_graphbuffer_baseline.py

On master (no refactor) the tests must be green without regen.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from click.testing import CliRunner

from codeindex.cli import main
from codeindex.invoker import InvokeResult

FIXTURE = Path(__file__).parent.parent / "fixtures" / "char_graphbuffer" / "project"
GOLDEN = Path(__file__).parent.parent / "fixtures" / "char_graphbuffer" / "golden"

_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+")
UPDATE = os.environ.get("CODEINDEX_UPDATE_GOLDEN") == "1"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _normalize(text: str, root: Path) -> str:
    """Strip the two known non-deterministic sources from generated output."""
    text = text.replace(str(root.resolve()), "<ROOT>").replace(str(root), "<ROOT>")
    text = _TS_RE.sub("<TS>", text)
    return text


def _collect_readmes(root: Path) -> str:
    """Concatenate every README_AI.md under ``root`` into one stable snapshot."""
    parts: list[str] = []
    for path in sorted(root.rglob("README_AI.md")):
        rel = path.relative_to(root).as_posix()
        parts.append(f"===== {rel} =====\n{_normalize(path.read_text(), root)}")
    return "\n".join(parts)


def _copy_fixture(tmp_path: Path) -> Path:
    # Nest under a FIXED-name parent so the scan root's parent_name (which leaks
    # into the root dir's enrich prompt as "Parent: ...") is deterministic —
    # pytest's tmp_path basename (test-name + counter) is not stable across runs.
    proj = tmp_path / "wsroot" / "project"
    # Ignore on-disk README_AI.md pollution from repo-root scan-all (#135):
    # a stale `<!-- enrichment: ok -->` marker would be preserved by the
    # structural rewrite (GH #38) and drift the goldens on local runs.
    shutil.copytree(FIXTURE, proj, ignore=shutil.ignore_patterns("README_AI.md"))
    return proj


def _assert_or_update(name: str, actual: str) -> None:
    golden_path = GOLDEN / name
    if UPDATE:
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual)
        return
    assert golden_path.exists(), (
        f"missing golden {name}; run CODEINDEX_UPDATE_GOLDEN=1 to create it"
    )
    assert actual == golden_path.read_text(), (
        f"characterization drift in {name} (#101 must keep this byte-identical)"
    )


def _run(args: list[str], cwd: Path) -> None:
    """Invoke the CLI with cwd set to the project (commands read cwd config)."""
    prev = Path.cwd()
    os.chdir(cwd)
    try:
        result = CliRunner().invoke(main, args, catch_exceptions=False)
        assert result.exit_code == 0, f"{args} failed: {result.output}"
    finally:
        os.chdir(prev)


# --------------------------------------------------------------------------- #
# layer 1 + structural READMEs: deterministic, no AI
# --------------------------------------------------------------------------- #
def test_structural_readmes(tmp_path: Path) -> None:
    proj = _copy_fixture(tmp_path)
    _run(["scan-all", "--root", str(proj), "--no-ai", "--quiet"], cwd=proj)
    _assert_or_update("structural_readmes.txt", _collect_readmes(proj))


def test_project_symbols(tmp_path: Path) -> None:
    proj = _copy_fixture(tmp_path)
    _run(["scan-all", "--root", str(proj), "--no-ai", "--quiet"], cwd=proj)
    _run(["symbols", "--output", "PROJECT_SYMBOLS.md", "--quiet"], cwd=proj)
    actual = _normalize((proj / "PROJECT_SYMBOLS.md").read_text(), proj)
    _assert_or_update("project_symbols.md", actual)


# --------------------------------------------------------------------------- #
# layer 3 (prompt snapshot) + frozen-AI READMEs: AI mocked to a fixed stub
# --------------------------------------------------------------------------- #
def test_enrich_prompts_and_frozen_ai_readmes(tmp_path: Path, monkeypatch) -> None:
    proj = _copy_fixture(tmp_path)
    captured: list[str] = []

    def fake_invoke(config, prompt, *args, **kwargs):  # noqa: ANN001
        captured.append(prompt)
        return InvokeResult(success=True, output="stub-description", command="<stub>")

    # cli_scan re-imports invoke_ai from .invoker at call time (enrich path), so
    # patching the home module catches it; patch the module-level binding too
    # for the single-dir path's safety (ADR-008: invoke_ai dispatches API/CLI).
    monkeypatch.setattr("codeindex.invoker.invoke_ai", fake_invoke)
    monkeypatch.setattr("codeindex.cli_scan.invoke_ai", fake_invoke, raising=False)

    _run(["scan-all", "--root", str(proj), "--quiet"], cwd=proj)

    # layer 3: the exact prompts fed to the AI (sorted for stable ordering)
    prompts_snapshot = "\n===== PROMPT =====\n".join(
        _normalize(p, proj) for p in sorted(captured)
    )
    _assert_or_update("enrich_prompts.txt", prompts_snapshot)

    # frozen-AI READMEs: structure + deterministic stub injection
    _assert_or_update("frozen_ai_readmes.txt", _collect_readmes(proj))
