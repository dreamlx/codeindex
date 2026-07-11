# Pre-release Checklist

**Run this before every `git tag v*.*.*` / PyPI publish.**

The goal is to catch the *upgrade-experience* and *cross-language-docs* mistakes
that unit tests and lint cannot — and to make every release decision
defensible by the same standard, not just whatever the releaser happened to
remember at the time. Lessons baked in from the 0.24.0 navigation-contract
release (which introduced a user-visible default change that needed careful
upgrade messaging).

---

## Workflow

```bash
# 1. Auto-checked portion (~5 min, no API calls)
./scripts/pre_release_check.sh 0.24.0

# 2. Manual checks below (~20-30 min)
# 3. If everything green, follow docs/development/QUICK_START_RELEASE.md
#    for the actual merge + tag + push
```

The script enforces what it can; the rest is judgment that needs a human.

---

## Auto-checked (in `scripts/pre_release_check.sh`)

| # | Check | What it verifies |
|---|---|---|
| 1 | Version consistency | `pyproject.toml` = VERSION, `CHANGELOG.md [VERSION]` present (required), tag doesn't already exist. `RELEASE_NOTES_vVERSION.md` is **optional** (warn only) — write one only for a major/breaking release |
| 2 | Working tree state | Clean tree, on master branch |
| 3 | Full test suite | `pytest -q` (includes slow tests) passes |
| 4 | Ruff lint | `ruff check src/ bench/` clean |
| 5 | Wheel build | `python -m build` produces `dist/ai_codeindex-VERSION-py3-none-any.whl` |
| 6 | Clean-venv install | Fresh venv, `pip install "$(ls dist/*.whl)[all]"` (the `[all]` extras pull language parsers — GH #46), `codeindex --version` matches, `codeindex --help` runs |
| 7 | CI status | `gh run list` shows latest run on current branch succeeded (best-effort) |

If any FAIL, the script exits non-zero and you do not proceed.

---

## Manual checks

The script lists these as a reminder at the end. Each section is a real
question to answer, not a tick-the-box ritual.

### [a] Upgrade simulation

Real upgrade path verification. After upgrade, `codeindex claude-md update`
should refresh the user's project `CLAUDE.md` (ADR-004 — there is no
post-install hook; the CLI command is the canonical refresh path); the new
defaults are supposed to apply only where users had no explicit override;
the new disclaimer is supposed to be additive. Verify each.

```bash
# Pick a target project that has been scanned with the previous version.
# (Could be codeindex itself, manon, or whatever you usually dogfood.)
TARGET=/path/to/some/project

# Snapshot its current README_AI.md state for diff later
cd $TARGET
git stash -u   # if it's git, stash anything uncommitted

# Install the candidate version into a sandbox venv.
# NOTE (GH #46): the `[all]` extras pull the tree-sitter language parsers. A
# bare `pip install <wheel>` installs only the entrypoint — no parsers — so
# scan-all emits structural-only READMEs and the upgrade-sim diff won't match
# what a real `pipx install ai-codeindex[all]` user sees. Quote the arg so the
# shell doesn't glob `[all]`. Do NOT retrofit with `pip install ai-codeindex[all]`
# (no --no-deps) — that re-pulls ai-codeindex from PyPI and silently downgrades
# the sandbox.
SANDBOX=/tmp/codeindex_upgrade_test
rm -rf $SANDBOX && python3 -m venv $SANDBOX
$SANDBOX/bin/pip install "$(ls dist/ai_codeindex-*-py3-none-any.whl)[all]"
$SANDBOX/bin/codeindex --version    # should print the candidate version

# Re-scan
$SANDBOX/bin/codeindex scan-all --ai

# Inspect diff
git diff --stat
git diff README_AI.md  # spot-check one file
```

Acceptance:
- [ ] Diff is ADDITIVE on README headers (new `<!-- codeindex navigation ...`
      line at top, original Generated line still present below)
- [ ] No `README_AI.md` lost content unexpectedly (some shrinkage is OK if
      `max_readme_size` default changed; large shrinkage = expected for
      hit-the-cap dirs, no shrinkage = expected for everything else)
- [ ] Explicit overrides in `.codeindex.yaml` were respected
- [ ] `codeindex symbols` still produces a working `PROJECT_SYMBOLS.md`
- [ ] `codeindex claude-md update` correctly refreshed the project
      CLAUDE.md section (per ADR-004)

### [b] Translation / docs parity

codeindex's docs are mixed Chinese/English by historical accident:
- ADRs, design philosophy: English
- Planning, executive summary, improvement plans: Chinese
- CHANGELOG: English
- Recent release notes: English

Check whether *this* release should add/refresh Chinese versions:

- [ ] **README parity**: if `README.md` changed since `README_zh.md` was last
      synced, run `make readme-zh`, review the diff, and commit. `README_zh.md`
      is a *derived* artifact — regenerate it, don't hand-edit (see ADR / the
      `readme-zh` target). Same for `*.zh.md` doc pairs.
- [ ] Compare against the last 3 releases — if any had Chinese parallel
      docs (e.g. `RELEASE_NOTES_v0.X.0_zh.md`), this one should too
- [ ] If the release touches user-facing strings (CLI output, error
      messages, README templates), check both languages are consistent or
      the change is purely English-side
- [ ] CHANGELOG section for this version: complete, ordered (Added →
      Changed → Fixed → Removed), no `[Unreleased]` orphan content

### [c] Bench smoke test

You ARE the user. Run the bench harness against the candidate version on
one real project + one real question. Should take ~3 min.

```bash
cd bench/
# Edit targets.yaml + questions.yaml to use the candidate version
# (if you have an "install from local wheel" target, that's ideal)
make run     # 1 question × 2 variants ≈ 2 sonnet calls ≈ $0.30
make grade
```

Acceptance:
- [ ] Both variants completed without error
- [ ] Grader returned CORRECT or PARTIAL on the WITH-disclaimer variant
- [ ] No `is_error=True` rows
- [ ] Cost in expected range (~$0.30-0.50 for 1 question)

### [d] RELEASE_NOTES_vX.Y.Z.md self-read

Read your own release notes as if you were a user who just `pip install
--upgrade`d and is wondering what to expect. Specifically:

- [ ] First section answers "should I upgrade?" within 3 lines
- [ ] If any default behavior changed, there is an explicit "What you will
      see on next scan-all" paragraph
- [ ] Every breaking-ish change links to an ADR or design doc
- [ ] Upgrade tips include the exact override syntax for users who want
      the old behavior
- [ ] Acknowledgments / provenance section credits the source of any
      benchmark data or external insight

### [e] GH Actions CI on the pushed branch

```bash
gh run list --branch master --limit 3
```

Acceptance:
- [ ] Latest run on master = success
- [ ] No in-progress run (wait if so)

---

## What this checklist explicitly does NOT cover

- **Beta testing**: codeindex does not currently ship betas. If a release
  is risky enough you want one, ship `0.X.Y-beta1` to TestPyPI manually
  before this checklist applies.
- **Customer-specific validation**: enterprise users may have private
  codebases where a new default behaves badly. We cannot test those from
  here. If you have access to one, run section [c] against it too.
- **GitHub release notes**: created automatically by the publish workflow
  on tag push. Source of truth is `docs/releases/RELEASE_NOTES_vX.Y.Z.md`.

---

## After all checks pass

```bash
git checkout master
git pull origin master
git tag -a v0.24.0 -m "Release v0.24.0 — <one-line theme>"
git push origin v0.24.0   # ← this triggers PyPI publish; irreversible
```

Then monitor:
- `gh run watch` on the publish workflow
- `pip install ai-codeindex==0.24.0` from a clean venv as a smoke test
- The first issue or two on GitHub for any "this broke my workflow" reports

If a critical issue surfaces within hours: do NOT delete the PyPI release
(can't). Cut `0.24.1` with the fix and ship a release note clarifying the
recommended action for 0.24.0 users.
