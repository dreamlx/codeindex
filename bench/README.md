# bench/ — codeindex benchmark harness

Internal tooling for measuring whether codeindex output (`README_AI.md`)
measurably helps agent comprehension. **Not shipped to end users**, not part
of the wheel. Produced the data backing
[ADR-005](../docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md)
and the [public benchmark report](../docs/benchmark/2026-05-readme-impact.md).

## What it does

For each (project, question) pair, runs `claude -p` twice (or three times):

| variant | agent context |
|---|---|
| `wo` | `README_AI.md` files hidden via `--disallowedTools 'Read(**/README_AI.md)'` |
| `disclaimer` | full access (current shipped state — README has navigation-contract disclaimer) |
| `guide` | above + `--append-system-prompt` injecting a tool-selection table (tested + rejected, see ADR-005) |

Captures wall time, API time, total tokens, cost, response, permission denials.
Optional second pass with `grade.py` uses haiku to label each response
`CORRECT` / `PARTIAL` / `WRONG`.

## Quick start

```bash
cd bench/
make setup                # copies *.yaml.example → *.yaml for you to edit
# edit targets.yaml (project paths) + questions.yaml (Qs + ref answers)
make scan                 # rescans your projects with codeindex (haiku, ~2 min each)
make run                  # default: VARIANTS=wo,disclaimer ⇒ N×2 sonnet runs
make grade                # LLM-as-judge with haiku
make report               # headline comparison table
```

Costs roughly $0.20–$0.50 per (question, variant) on sonnet; $0.01 per
grader call on haiku. Plan for $3–7 total on a 15-question full run.

## What questions to write

Hand-write 5 questions per project that you (or a sub-agent you brief)
would actually ask after `cd`ing into the repo cold. Mix:

- **structural** — "where is X implemented" / "what's the entry point"
- **behavioral** — "trace the data flow for Y" / "how does Z actually work"
- **architectural** — "how do A and B relate" / "what's the plugin model"

Ground each `ref_answer` in actual source files (paths, symbol names, line
numbers), not in `README_AI.md` — otherwise you bias the grader toward
"WITH-README looks correct because both texts came from the same generator".

For a large legacy project with selective `include:` in its `.codeindex.yaml`,
**only ask questions whose answers live inside the indexed scope**. Otherwise
the WITH-README variant inherits the same "the index doesn't cover this dir"
handicap as WO and the test is confounded. This was Phase D2 of the 2026-05
benchmark — see ADR-005 history.

## Files

- `Makefile` — top-level entry points
- `run_bench.py` — sonnet runner, writes per-row CSV with all metrics
- `grade.py` — haiku judge: ref_answer vs response → CORRECT/PARTIAL/WRONG
- `report.py` — pretty-print headline from `*_graded.csv`
- `targets.yaml.example` — list of projects to benchmark (you must edit)
- `questions.yaml.example` — per-project questions + ref_answers (you must edit)

Results, logs, and your local `targets.yaml`/`questions.yaml` are
`.gitignore`d — this directory ships only the harness, not the data.

## What's NOT here

- No metrics persistence / database / dashboard — CSVs are it.
- No statistical significance testing — single-shot variance is high; treat
  any individual question as anecdote, an aggregate across 10+ Qs as signal.
- No multi-agent comparison — fixed to `claude -p`. Adapt `run_agent()` in
  `run_bench.py` if you want to swap the agent.
