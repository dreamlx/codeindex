#!/usr/bin/env bash
# Pre-release sanity check for codeindex.
#
# Runs the automatable portion of the pre-release checklist defined in
# docs/development/pre-release-checklist.md. Exit code 0 means all auto
# checks passed AND the human checklist is ready to walk through; non-zero
# means at least one auto check failed and you should NOT tag yet.
#
# Usage:
#   scripts/pre_release_check.sh 0.24.0
#
# Run from repo root. Does not push, tag, merge, or build into wheel
# directly into PyPI — strictly read-only + local-build sandbox.

set -u

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    echo "Usage: $0 <version>  (e.g. 0.24.0)"
    exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass()  { echo "  ✓ $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail()  { echo "  ✗ $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
warn()  { echo "  ⚠ $1"; WARN_COUNT=$((WARN_COUNT+1)); }
section() { echo ""; echo "── $1 ──"; }

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "✗ not in a git repo"; exit 1; }
cd "$REPO_ROOT"

echo "Pre-release check for codeindex v$VERSION"
echo "Repo: $REPO_ROOT"

# ── 1. Version-string consistency ─────────────────────────────────
section "1. Version-string consistency"

# This gate runs PRE-bump (it's read-only — the bump happens in release.sh
# step 3). So pyproject is *expected* to still hold the old version; the
# target version lands after bump_version.sh. A match here would actually be
# wrong (either already bumped, or a stale pre-bump). Warn, don't fail —
# the real version-consistency check is release.sh's post-bump build (step 8-9)
# and the TestPyPI/PyPI install (step 10-11), both post-bump.
PYPROJECT_VER=$(grep -E '^version = ' pyproject.toml | head -1 | sed -E 's/version = "([^"]+)"/\1/')
if [[ "$PYPROJECT_VER" == "$VERSION" ]]; then
    warn "pyproject.toml already at $VERSION (expected pre-bump); bump_version.sh will be a no-op"
else
    pass "pyproject.toml is $PYPROJECT_VER (pre-bump); bump_version.sh will set $VERSION"
fi

if grep -qE "^## \[$VERSION\]" CHANGELOG.md; then
    pass "CHANGELOG.md has [$VERSION] section"
else
    fail "CHANGELOG.md missing [$VERSION] section"
fi

# RELEASE_NOTES are OPTIONAL — CHANGELOG (above) is the mandatory per-release
# record. Write a RELEASE_NOTES only for a major / breaking / announced release
# (there it doubles as the announcement). A patch or routine minor needs none.
NOTES_FILE="docs/releases/RELEASE_NOTES_v${VERSION}.md"
if [[ -f "$NOTES_FILE" ]]; then
    pass "$NOTES_FILE exists"
else
    warn "$NOTES_FILE absent — fine for a patch/minor; write one only for a major or breaking release"
fi

if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    fail "git tag v$VERSION already exists — bump version or delete tag"
else
    pass "git tag v$VERSION does not yet exist (good)"
fi

# ── 1b. README_AI release-time refresh (#166) ─────────────────────
section "1b. README_AI refresh freshness"

# The CLAUDE.md codeindex section is stamped with the tool version at refresh
# time (claude-md update), so after a refresh it carries the target version —
# external truth that a refresh happened after the version bump, before the tag.
# But this gate is read-only and runs PRE-bump+PRE-refresh (the stamp lands in
# release.sh step 6.5), so the section still holds the OLD stamp — a mismatch
# is expected here, not a failure. The real stamp verification is that the
# dirty-README check below passes AND release.sh step 6.5 ran claude-md update.
if grep -q "(v$VERSION) for AI-friendly" CLAUDE.md; then
    pass "CLAUDE.md codeindex section stamped v$VERSION"
else
    warn "CLAUDE.md still stamped with pre-release version (refresh happens in release.sh step 6.5)"
fi

DIRTY_README=$(git status --porcelain -- '*README_AI.md' | wc -l | tr -d ' ')
if [[ "$DIRTY_README" == "0" ]]; then
    pass "no dirty README_AI.md files"
else
    fail "$DIRTY_README uncommitted README_AI.md file(s) — commit the refresh before tagging"
fi

# ── 2. Working tree state ─────────────────────────────────────────
section "2. Working tree state"

if [[ -z "$(git status --porcelain)" ]]; then
    pass "working tree clean"
else
    warn "working tree has uncommitted changes (will not be in the release)"
fi

CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" == "master" || "$CURRENT_BRANCH" == "main" ]]; then
    pass "on $CURRENT_BRANCH branch"
else
    warn "on $CURRENT_BRANCH branch (release script expects master)"
fi

# ── 3. Test suite (full, including slow) ──────────────────────────
section "3. Test suite (pytest -v, includes slow)"

if [[ -f .venv/bin/pytest ]]; then
    PYTEST=.venv/bin/pytest
elif command -v pytest >/dev/null 2>&1; then
    PYTEST=pytest
else
    fail "pytest not found"
    PYTEST=""
fi

if [[ -n "$PYTEST" ]]; then
    if $PYTEST -q >/tmp/pre_release_pytest.log 2>&1; then
        TEST_SUMMARY=$(tail -1 /tmp/pre_release_pytest.log)
        pass "pytest passed — $TEST_SUMMARY"
    else
        fail "pytest failed — see /tmp/pre_release_pytest.log"
        tail -10 /tmp/pre_release_pytest.log | sed 's/^/    /'
    fi
fi

# ── 4. Ruff lint ──────────────────────────────────────────────────
section "4. Ruff lint"

if [[ -f .venv/bin/ruff ]]; then
    RUFF=.venv/bin/ruff
elif command -v ruff >/dev/null 2>&1; then
    RUFF=ruff
else
    warn "ruff not found, skipping lint"
    RUFF=""
fi

if [[ -n "$RUFF" ]]; then
    if $RUFF check src/ bench/ >/tmp/pre_release_ruff.log 2>&1; then
        pass "ruff check clean"
    else
        fail "ruff check found issues — see /tmp/pre_release_ruff.log"
    fi
fi

# ── 5. Build wheel ────────────────────────────────────────────────
section "5. Build wheel"

rm -rf dist/ build/
if python3 -m build >/tmp/pre_release_build.log 2>&1; then
    # Pre-bump: the wheel carries the OLD pyproject version, not $VERSION
    # (bump happens in release.sh step 3, after this read-only gate). So we
    # only check that A wheel was built — the version-matched wheel is
    # verified post-bump by release.sh step 9 (twine check) + the TestPyPI/
    # PyPI install smoke (step 10-11). Flagging a pre-bump version mismatch
    # here is a guaranteed false positive.
    WHEEL=$(ls dist/*.whl 2>/dev/null | head -1)
    if [[ -n "$WHEEL" ]]; then
        pass "build succeeded (wheel: $(basename "$WHEEL"))"
        if [[ "$WHEEL" != *"ai_codeindex-${VERSION}-py3-none-any.whl" ]]; then
            warn "wheel is pre-bump version; release.sh bumps then rebuilds to ${VERSION}"
        fi
    else
        fail "build succeeded but no wheel in dist/"
        ls -1 dist/ 2>/dev/null | sed 's/^/    /'
    fi
else
    fail "python -m build failed — see /tmp/pre_release_build.log"
    tail -10 /tmp/pre_release_build.log | sed 's/^/    /'
fi

# ── 6. Clean-venv install smoke test ──────────────────────────────
section "6. Clean-venv install + codeindex --version"

# Pre-bump: the wheel carries the old version, so `--version` will report the
# old version, not $VERSION — that's expected here. The post-bump version
# match is verified by release.sh step 10-11 (TestPyPI/PyPI install). This
# step still has value: it proves the wheel installs cleanly and the CLI
# runs in a fresh venv (catches missing deps / import errors). We check the
# install + --help, and only warn on the version mismatch.
SANDBOX=/tmp/codeindex_release_sandbox_$$
rm -rf "$SANDBOX"
python3 -m venv "$SANDBOX" >/dev/null 2>&1
WHEEL=$(ls dist/*.whl 2>/dev/null | head -1)
if [[ -n "$WHEEL" ]]; then
    if "$SANDBOX/bin/pip" install "$WHEEL" >/tmp/pre_release_install.log 2>&1; then
        REPORTED_VER=$("$SANDBOX/bin/codeindex" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "??")
        if [[ "$REPORTED_VER" == "$VERSION" ]]; then
            pass "clean-venv codeindex --version = $VERSION"
        else
            warn "clean-venv codeindex --version = $REPORTED_VER (pre-bump; release.sh bumps to $VERSION)"
        fi
        # minimal command smoke — the real value of this step post-bump-fix
        if "$SANDBOX/bin/codeindex" --help >/dev/null 2>&1; then
            pass "codeindex --help works in clean venv"
        else
            fail "codeindex --help failed in clean venv"
        fi
    else
        fail "pip install in clean venv failed — see /tmp/pre_release_install.log"
    fi
else
    warn "skipping clean-install (no wheel built)"
fi
rm -rf "$SANDBOX"

# ── 7. CI status on current branch (best-effort) ──────────────────
section "7. CI status on $CURRENT_BRANCH (via gh, best-effort)"

if command -v gh >/dev/null 2>&1; then
    CI_STATE=$(gh run list --branch "$CURRENT_BRANCH" --limit 1 --json status,conclusion --jq '.[0].conclusion // .[0].status' 2>/dev/null)
    case "$CI_STATE" in
        success) pass "latest CI run on $CURRENT_BRANCH: success" ;;
        in_progress|queued) warn "latest CI run on $CURRENT_BRANCH: $CI_STATE (wait for completion before tag)" ;;
        "") warn "could not query CI status (gh auth issue?)" ;;
        *) fail "latest CI run on $CURRENT_BRANCH: $CI_STATE — investigate before tag" ;;
    esac
else
    warn "gh CLI not installed, cannot check CI"
fi

# ── 8. Manual-check reminder ──────────────────────────────────────
section "8. Manual checks (this script cannot verify — see checklist)"
cat <<'EOF'
  Walk through docs/development/pre-release-checklist.md sections:

    [a] Upgrade simulation: install previous version in a sandbox, scan
        a project, then upgrade and rescan. Diff should be additive only.
    [b] Translation parity: do RELEASE_NOTES + CHANGELOG entries match
        the conventions of recent releases? Add Chinese version if
        prior releases had one.
    [c] Bench smoke: cd bench/ && run one question end-to-end against
        the version you're about to ship.
    [d] Self-read RELEASE_NOTES from a stranger's POV — are upgrade
        warnings prominent? Is "what to expect on first scan" clear?
    [e] Confirm GitHub Actions on the prior push completed green
        (re-check #7 above).
EOF

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo "─────────────────────────────────────────"
echo "Summary: $PASS_COUNT passed / $FAIL_COUNT failed / $WARN_COUNT warnings"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo "✗ DO NOT TAG — fix failures first"
    exit 1
fi
if [[ "$WARN_COUNT" -gt 0 ]]; then
    echo "⚠ Warnings present — review before proceeding"
fi
echo "Auto-checks ok. Complete the manual checklist before tag push."
exit 0
