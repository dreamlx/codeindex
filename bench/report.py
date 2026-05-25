#!/usr/bin/env python3
"""Print headline comparison from a *_graded.csv produced by grade.py.

Aggregates per-project across variants (wo/disclaimer/guide if present) and
prints per-question deltas sorted by README impact. Run with no args after
`make grade` to see what your benchmark says.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict


def variant_of(r: dict) -> str:
    if r.get("with_readme") == "False":
        return "wo"
    if r.get("with_guide") == "True":
        return "guide"
    return "disclaimer"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("graded_csv")
    args = p.parse_args()

    rows = [r for r in csv.DictReader(open(args.graded_csv))
            if r["is_error"] == "False" and r["total_tokens"] not in ("0", "")]
    if not rows:
        print("No valid rows in", args.graded_csv)
        return 1

    variants = sorted({variant_of(r) for r in rows})

    print(f"\n=== Per-project averages by variant ({args.graded_csv}) ===\n")
    print(f"{'project':<16} {'variant':<11} {'N':>3} {'score':>6} {'sec':>5} {'tok':>10} {'cost':>6}")
    print("-" * 64)
    agg = defaultdict(lambda: defaultdict(list))
    for r in rows:
        agg[r["project"]][variant_of(r)].append(r)
    for proj in sorted(agg):
        for v in variants:
            xs = agg[proj].get(v, [])
            if not xs:
                continue
            avg_s  = sum(float(x["grade_score"]) for x in xs) / len(xs)
            avg_t  = sum(float(x["wall_sec"])    for x in xs) / len(xs)
            avg_to = sum(int(x["total_tokens"])  for x in xs) / len(xs)
            tot_c  = sum(float(x["cost_usd"])    for x in xs)
            print(f"{proj:<16} {v:<11} {len(xs):>3} {avg_s:>6.2f} {avg_t:>5.0f} {int(avg_to):>10,} {tot_c:>5.2f}")
        print()

    print("=== Per-question (sorted by Δtime: WITH-disclaimer vs WO) ===\n")
    print(f"{'project':<16} {'qid':<10} {'wo_grade':<10} {'wt_grade':<10} {'wo_sec':>6} {'wt_sec':>6} {'Δsec%':>6} {'Δtok%':>7}")
    deltas = []
    for proj, vmap in agg.items():
        wos = {r["question_id"]: r for r in vmap.get("wo", [])}
        wits = {r["question_id"]: r for r in vmap.get("disclaimer", [])}
        for qid, wo in wos.items():
            wi = wits.get(qid)
            if not wi:
                continue
            ds = (float(wi["wall_sec"])    - float(wo["wall_sec"]))    / float(wo["wall_sec"])    * 100
            dt = (int(wi["total_tokens"])  - int(wo["total_tokens"]))  / int(wo["total_tokens"])  * 100
            deltas.append((proj, qid, wo["grade_label"], wi["grade_label"],
                           float(wo["wall_sec"]), float(wi["wall_sec"]), ds, dt))
    for row in sorted(deltas, key=lambda x: x[6]):
        proj, qid, wog, wig, wos_, wis_, ds, dt = row
        print(f"{proj:<16} {qid:<10} {wog:<10} {wig:<10} {wos_:>6.0f} {wis_:>6.0f} {ds:>+5.0f}% {dt:>+6.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
