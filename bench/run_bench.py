#!/usr/bin/env python3
"""Benchmark: does README_AI.md measurably help agent comprehension?

For each (project, question) pair, runs `claude -p` twice:
  A) WITHOUT README_AI.md (Read tool blocked from those files)
  B) WITH    README_AI.md (full Read access)

Captures wall time, API time, total tokens, cost, response text, and any
permission denials. Writes one row per run to results.csv.

Usage:
    python3 run_bench.py --questions questions.yaml --output results.csv
    python3 run_bench.py --questions questions.yaml --only manon  # one project
    python3 run_bench.py --dry-run                                # show plan
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

AGENT_MODEL = "sonnet"
AGENT_TIMEOUT_S = 300
AGENT_BUDGET_USD = 0.50
ALLOWED_TOOLS = "Read,Glob,Grep"
DISALLOW_README = "Read(**/README_AI.md)"

# Phase J: tool-selection guide injected as system prompt addendum
# (variant "guide"). Mirrors what we'd recommend in CLAUDE.md but doesn't
# require modifying the project's CLAUDE.md.
TOOL_SELECTION_GUIDE = """When investigating code in this project:
- "What does X module do" / high-level architecture: read README_AI.md (it's a navigation index, accurate at module level).
- "Where is X implemented" / find file containing X: use README_AI.md to narrow scope, then Read the actual source file.
- "How does X actually work" / precise mechanism / specific behavior: do NOT rely on README_AI.md alone — it is a navigation index, not a detailed doc, and may oversimplify or omit important detail. Read the relevant source file directly or use Grep.
- Finding a specific string anywhere: use Grep directly.
The README_AI.md disclaimer at the top of each index explicitly confirms this contract."""


def run_agent(project_dir: Path, question: str, with_readme: bool,
              with_guide: bool = False) -> dict:
    cmd = [
        "claude", "-p", question,
        "--model", AGENT_MODEL,
        "--allowedTools", ALLOWED_TOOLS,
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
        "--max-budget-usd", str(AGENT_BUDGET_USD),
    ]
    if not with_readme:
        cmd.extend(["--disallowedTools", DISALLOW_README])
    if with_guide:
        cmd.extend(["--append-system-prompt", TOOL_SELECTION_GUIDE])

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=project_dir, capture_output=True, text=True,
            timeout=AGENT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "wall_sec": AGENT_TIMEOUT_S}
    wall = round(time.monotonic() - t0, 2)

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"json parse failed: {e}", "wall_sec": wall,
                "raw_stdout": proc.stdout[:500], "raw_stderr": proc.stderr[:500]}

    u = data.get("usage", {})
    total_tokens = (
        u.get("input_tokens", 0)
        + u.get("output_tokens", 0)
        + u.get("cache_creation_input_tokens", 0)
        + u.get("cache_read_input_tokens", 0)
    )
    return {
        "wall_sec": wall,
        "api_ms": data.get("duration_api_ms", 0),
        "ttft_ms": data.get("ttft_ms", 0),
        "num_turns": data.get("num_turns", 0),
        "input_tokens": u.get("input_tokens", 0),
        "output_tokens": u.get("output_tokens", 0),
        "cache_read_tokens": u.get("cache_read_input_tokens", 0),
        "cache_creation_tokens": u.get("cache_creation_input_tokens", 0),
        "total_tokens": total_tokens,
        "cost_usd": data.get("total_cost_usd", 0),
        "permission_denials": len(data.get("permission_denials", [])),
        "is_error": data.get("is_error", False),
        "response": data.get("result", ""),
    }


CSV_FIELDS = [
    "project", "question_id", "question", "ref_answer", "with_readme",
    "with_guide",
    "wall_sec", "api_ms", "ttft_ms", "num_turns",
    "input_tokens", "output_tokens", "cache_read_tokens",
    "cache_creation_tokens", "total_tokens", "cost_usd",
    "permission_denials", "is_error", "response", "error",
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--questions", default="questions.yaml")
    p.add_argument("--output", default="results.csv")
    p.add_argument("--only", help="only run for this project key")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-existing", action="store_true",
                   help="Skip (project,q_id,with_readme,with_guide) combos already in output CSV with non-error result")
    p.add_argument("--variants", default="wo,disclaimer",
                   help="Comma-separated list of variants to run. Choices: wo, disclaimer, guide.")
    args = p.parse_args()

    variant_specs = {
        "wo":         {"with_readme": False, "with_guide": False},
        "disclaimer": {"with_readme": True,  "with_guide": False},
        "guide":      {"with_readme": True,  "with_guide": True},
    }
    selected_variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    for v in selected_variants:
        if v not in variant_specs:
            print(f"!! unknown variant {v!r}; choices: {list(variant_specs)}")
            return 2

    cfg = yaml.safe_load(Path(args.questions).read_text())

    existing_ok = set()
    if args.skip_existing and Path(args.output).exists():
        with Path(args.output).open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("is_error", "True") == "False" and row.get("total_tokens", "0") not in ("0", "", "0.0"):
                    key = (row["project"], row["question_id"], row["with_readme"],
                           row.get("with_guide", "False"))
                    existing_ok.add(key)
        print(f"Skip-existing: {len(existing_ok)} successful rows already in CSV")

    plan = []
    for proj_key, proj in cfg["projects"].items():
        if args.only and proj_key != args.only:
            continue
        proj_path = Path(proj["path"]).expanduser()
        if not proj_path.is_dir():
            print(f"!! {proj_key}: {proj_path} not a directory, skip")
            continue
        for q in proj["questions"]:
            for vname in selected_variants:
                spec = variant_specs[vname]
                key = (proj_key, q["id"], str(spec["with_readme"]), str(spec["with_guide"]))
                if key in existing_ok:
                    continue
                plan.append((proj_key, proj_path, q, vname, spec))

    print(f"Planned: {len(plan)} runs  (projects, questions, variants)")
    if args.dry_run:
        for proj_key, _, q, vname, _ in plan:
            print(f"  [{vname:>10}] {proj_key}#{q['id']}: {q['question'][:55]}")
        return 0

    # Open CSV (append mode for resumability)
    out_path = Path(args.output)
    file_exists = out_path.exists()
    fout = out_path.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fout, fieldnames=CSV_FIELDS)
    if not file_exists:
        writer.writeheader()

    done = 0
    for proj_key, proj_path, q, vname, spec in plan:
        done += 1
        print(f"[{done}/{len(plan)}] [{vname:>10}] {proj_key}#{q['id']}: ", end="", flush=True)
        try:
            res = run_agent(proj_path, q["question"],
                            with_readme=spec["with_readme"],
                            with_guide=spec["with_guide"])
        except Exception as e:
            res = {"error": f"exception: {e}", "wall_sec": 0}

        row = {
            "project": proj_key,
            "question_id": q["id"],
            "question": q["question"],
            "ref_answer": q.get("ref_answer", ""),
            "with_readme": spec["with_readme"],
            "with_guide": spec["with_guide"],
            "wall_sec": res.get("wall_sec", ""),
            "api_ms": res.get("api_ms", ""),
            "ttft_ms": res.get("ttft_ms", ""),
            "num_turns": res.get("num_turns", ""),
            "input_tokens": res.get("input_tokens", ""),
            "output_tokens": res.get("output_tokens", ""),
            "cache_read_tokens": res.get("cache_read_tokens", ""),
            "cache_creation_tokens": res.get("cache_creation_tokens", ""),
            "total_tokens": res.get("total_tokens", ""),
            "cost_usd": res.get("cost_usd", ""),
            "permission_denials": res.get("permission_denials", ""),
            "is_error": res.get("is_error", ""),
            "response": (res.get("response", "") or "")[:2000],
            "error": res.get("error", ""),
        }
        writer.writerow(row)
        fout.flush()
        msg = f"{res.get('wall_sec','?')}s, ${res.get('cost_usd', '?')}, {res.get('total_tokens','?')} tok"
        if res.get("error"):
            msg = f"ERROR: {res['error']}"
        print(msg)

    fout.close()
    print(f"\nResults written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
