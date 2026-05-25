#!/usr/bin/env python3
"""LLM-as-judge grader. For each (ref_answer, response) pair in results.csv,
asks claude haiku to label CORRECT / PARTIAL / WRONG and writes results_graded.csv.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

GRADE_PROMPT = """You are grading a code-investigation agent's answer to a question about a codebase.

REFERENCE ANSWER (what we know is correct, written after reading the actual source code):
{ref}

AGENT RESPONSE (what to grade):
{resp}

Question: Did the AGENT RESPONSE substantively capture the key technical facts from the REFERENCE ANSWER — specifically the right file paths, method/class names, and the core mechanism described? Minor wording differences are fine; missing or wrong facts are not.

Reply with EXACTLY ONE of these words (no other text):
- CORRECT  : captures all major facts (file path + symbol + mechanism)
- PARTIAL  : captures some facts but misses or misstates key parts
- WRONG    : misses or misstates most key facts, or hallucinates

Reply with just the one word."""


def grade(ref: str, resp: str) -> tuple[str, float]:
    if not resp.strip():
        return "NO_ANSWER", 0.0
    prompt = GRADE_PROMPT.format(ref=ref[:2500], resp=resp[:2500])
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku",
             "--output-format", "json", "--max-budget-usd", "0.10"],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 0.0
    try:
        data = json.loads(proc.stdout)
        if data.get("is_error"):
            return f"ERROR:{data.get('result','')[:40]}", 0.0
        out = (data.get("result") or "").strip().upper()
        if "CORRECT" in out:
            return "CORRECT", 1.0
        if "PARTIAL" in out:
            return "PARTIAL", 0.5
        if "WRONG" in out:
            return "WRONG", 0.0
        return f"UNCLEAR:{out[:40]}", 0.0
    except json.JSONDecodeError:
        return "JSON_ERR", 0.0


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="results.csv")
    p.add_argument("--output", default="results_graded.csv")
    args = p.parse_args()
    rows = list(csv.DictReader(open(args.input)))
    fieldnames = list(rows[0].keys()) + ["grade_label", "grade_score"]
    out_path = Path(args.output)
    fout = out_path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()

    for i, r in enumerate(rows, 1):
        if r.get("is_error") == "True":
            label, score = "SKIP_ERROR", 0.0
        elif r.get("total_tokens") in ("0", ""):
            label, score = "SKIP_ZERO_TOK", 0.0
        else:
            label, score = grade(r.get("ref_answer", ""), r.get("response", ""))
        r["grade_label"] = label
        r["grade_score"] = score
        writer.writerow(r)
        fout.flush()
        tag = "W" if r.get("with_readme") == "True" else "O"
        print(f"[{i:>2}/{len(rows)}] {r['project']:<13} {r['question_id']:<8} {tag}: {label} ({score})")

    fout.close()
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    sys.exit(main() or 0)
