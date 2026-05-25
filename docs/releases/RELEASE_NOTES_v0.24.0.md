# Release Notes - v0.24.0

**Release Date**: 2026-05-25
**Theme**: Navigation contract — make `README_AI.md` work *for* AI agents, not just be readable *by* them

---

## 📊 Overview

v0.24 is a **behavior-quality** release. No new languages, no new extractors — instead, two changes to how `README_AI.md` is generated, plus three operational improvements to `scan-all --ai`. Backed by a measured benchmark (15 hand-graded question pairs across 3 heterogeneous projects) showing that the prior defaults could let an agent over-trust the index and answer detail questions *wrong but faster*.

**Headline changes**:
- `max_readme_size` default: **50KB → 10KB**
- Every generated `README_AI.md` now carries a one-line navigation-contract disclaimer in its header
- `codeindex scan-all --ai` is now **idempotent**: re-running it after a partial failure (rate limit, network) only retries failed dirs; successes are restored from cache (zero AI cost). Force a fresh run with `--retry-all`
- Default `ai_command` in `codeindex init` switched to `claude --model haiku` (faster + cheaper, fewer rate-limit hits; you can swap to sonnet via one config line)
- Per-directory enrichment status now recorded as `<!-- enrichment: ok | failed (reason: ...) -->` HTML marker

**Test coverage**: 1566 tests passing (full suite incl. slow tests, no regressions vs 0.23.2)
**Breaking changes**: none (all defaults; users with explicit config unchanged)
**Backed by**: [ADR-005](../architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) + [2026-05 README impact benchmark](../benchmark/2026-05-readme-impact.md)

---

## ✨ What's New

### 1. Navigation-contract disclaimer in every `README_AI.md`

Every generated index header now starts with:

```
<!-- codeindex navigation index — agent: drill into source via Read/Grep
     for precise mechanism; do not treat this as final word. -->
```

**Why**: Phase F benchmark showed AI agents (claude-sonnet-4-6 in this study) sometimes treated the navigation summary as authoritative and stopped exploring — producing wrong-but-fast answers on detail questions. The disclaimer is an explicit contract telling the agent the index is for orientation, not the final word.

**Impact for humans**: zero — HTML comments don't render in markdown viewers. Only agents reading raw markdown see it.

**Defined once** in `src/codeindex/writers/__init__.py` as `NAVIGATION_DISCLAIMER`; injected by all 5 generation paths (3 writers, `hierarchical.py`, `writer.py` base + fallback).

### 2. `max_readme_size` default 50KB → 10KB

The 50KB cap let a navigation README grow to roughly the same token cost as reading source directly, defeating the index purpose. 10KB keeps each `README_AI.md` in "summary" territory.

**Concrete example from the benchmark** (a 119-file PHP module containing an 8891-line monster class):
- 51KB README: agent used **418K tokens** on one cross-file question
- 10KB README: agent used **148K tokens** on the same question, same answer grade

**Sites updated**: `config.py` (default constant + dataclass + from_dict fallback), `docs/guides/configuration.md`, `examples/.codeindex.yaml`.

### 3. Idempotent `scan-all --ai` + new `--retry-all` flag

Previously, hitting a rate-limit mid-run meant restarting everything — every dir paid AI cost again. Now Phase 2 snapshots existing enrichment state *before* Phase 1 rewrites READMEs, then re-injects cached descriptions for already-`ok` dirs without firing fresh AI calls.

**Typical recovery flow**:
```bash
codeindex scan-all --ai
# ⚠ 7/50 dirs failed enrichment (rate limit)
codeindex scan-all --ai     # only the 7 failed dirs hit AI again
```

For a full rebuild from scratch:
```bash
codeindex scan-all --ai --retry-all
```

### 4. Failure-summary hint with actionable next steps

When Phase 2 has any failed dirs, the CLI now prints a short list and concrete recovery options (retry / `--retry-all` / switch `ai_command` to `claude --model haiku` / `opencode` / `gemini`). No auto-fallback — by design — but the user sees what they can do without consulting docs.

### 5. AI error reason surfaced + persisted

`scan-all --ai` used to log opaque `⚠ <dir>: AI error` and drop the underlying `stderr`. Now logs `⚠ <dir>: AI error — <reason>` AND persists the reason into the README as `<!-- enrichment: failed (reason: ...) -->`. AI consumers can distinguish "structural-only by config" (no marker) from "enrichment attempted and failed" (marker with reason).

### 6. Default `ai_command` switched to claude haiku

`codeindex init` now writes:
```yaml
ai_command: 'claude -p "{prompt}" --model haiku --allowedTools "Read"'
```

Tested at 12-way parallel on a 251-directory project: zero rate-limit failures, 11min wall time, ~$0.50 total. Switch to sonnet for higher quality with one config line; escape hatches documented inline.

### 7. New `bench/` benchmark harness

Reproducible Makefile + Python harness for measuring `README_AI.md` impact on agent comprehension. Not packaged in the wheel — only useful for codeindex maintainers / contributors validating future prompt or format changes. See [`bench/README.md`](../../bench/README.md).

### 8. ADR-005 + public benchmark report

- `docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md` — design decision record
- `docs/benchmark/2026-05-readme-impact.md` — anonymized public writeup of the 30-run experiment + the Phase F3 size-cap test + the Phase J 3-way disclaimer A/B

---

## 📦 Upgrade Guide

### For users on 0.23.x

```bash
pip install --upgrade ai-codeindex
codeindex claude-md update    # required: refreshes your project CLAUDE.md
codeindex scan-all --ai       # rescan to pick up the new README header + size cap
```

> **Note**: `codeindex claude-md update` is the canonical refresh path — there is no pip post-install hook (ADR-004 was revised; the prototype was removed in this release). Run the command explicitly after every upgrade.

### What you will see on your next `scan-all`

1. **Every `README_AI.md` gets a new top line** — the navigation-contract HTML comment. Additive only; downstream parsers (markdown renderers, `codeindex symbols`, etc.) unaffected.

2. **Some `README_AI.md` files may shrink significantly** — only if you do NOT have `max_readme_size` explicitly set in your `.codeindex.yaml`. The new 10KB default is intentional (see "What's New" #2); per-file structural detail is preserved but bounded. If you want the old behavior, set:
   ```yaml
   indexing:
     max_readme_size: 51200  # 50KB, old default
   ```
   *But read [ADR-005](../architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md) first — the benchmark evidence suggests larger isn't better for agent comprehension.*

3. **Git diff will be noisy on the first scan** after upgrade — expect every `README_AI.md` to show:
   - +1 line at top (disclaimer)
   - +1 line below Generated (enrichment marker for AI-enriched dirs)
   - Possibly shorter body (if 10KB cap kicked in)
   You can verify the structure is sane by spot-checking one file, then commit the regeneration as a single "docs: README_AI.md refresh after codeindex 0.24 upgrade" commit.

### No-action upgrades

- **Existing `ai_command` in `.codeindex.yaml`**: unchanged behavior. Default change only affects new `codeindex init`.
- **Existing `max_readme_size` in `.codeindex.yaml`**: unchanged. Your value wins.
- **Tests / CI**: 1547 tests pass; no API changes to the codeindex Python package.

---

## 🔬 Why we made these changes

We ran a 15-question hand-graded benchmark on 3 heterogeneous projects (small Python CLI, medium Python pipeline, large legacy PHP) measuring whether `README_AI.md` actually helps a sonnet agent investigate code. Headline:

| Variant | Avg wall time | Avg tokens | Avg correctness |
|---|---|---|---|
| Without README | baseline | baseline | **0.67** |
| With README (pre-v0.24) | -19% | -28% | **0.63** ↓ |

The 0.04 average quality drop hid 3 specific questions (out of 15) where WITH-README went from CORRECT to WRONG/PARTIAL — agent over-trusted the index. v0.24's disclaimer + size cap target exactly that failure mode. Phase J confirmed the disclaimer alone is sufficient to recover the quality on the worst F-phase failure. Full data + methodology: [benchmark report](../benchmark/2026-05-readme-impact.md).

---

## 🙏 Acknowledgments

- The "navigation, not authoritative" framing is from `docs/planning/executive-summary.md` (v0.12-era user insight), now empirically validated.
- Phase F1 LLM-as-judge grading caught the speed-hides-quality pattern the headline metrics would have missed — without it this release would have been "ship and ship wrong."

---

## 📋 Full Changelog

See [CHANGELOG.md](../../CHANGELOG.md) `[0.24.0]` section.
