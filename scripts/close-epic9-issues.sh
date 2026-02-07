#!/bin/bash
# Script to close Epic 9 issues
# Created: 2026-02-07
# Usage: ./scripts/close-epic9-issues.sh

set -e

echo "🔍 Checking GitHub CLI authentication..."
gh auth status || {
    echo "❌ Not authenticated. Run: gh auth login"
    exit 1
}

echo ""
echo "📋 Closing Epic 9 Issue #1..."
gh issue close 1 --comment "✅ Completed in v0.6.0 (2026-02-04). Epic 9: AI-Powered Docstring Extraction successfully delivered.

See:
- CHANGELOG.md v0.6.0 entry
- docs/planning/completed/epic9-docstring-extraction/
- Tests: 415 passing, 3 skipped

All acceptance criteria met:
- [x] Extract docstrings from 80%+ PHP methods
- [x] AI cost <\$1 per 250 directories (~\$0.15 achieved)
- [x] Quality improvement: ⭐⭐ → ⭐⭐⭐⭐⭐
- [x] Universal architecture for Java/TypeScript/Go"

echo ""
echo "📋 Closing Story Issues #2-#6..."
gh issue close 2 3 4 5 6 --comment "✅ Completed as part of Epic 9 (v0.6.0, 2026-02-04).

See Epic #1 and CHANGELOG.md v0.6.0 entry for details."

echo ""
echo "✅ All Epic 9 issues closed successfully!"
echo ""
echo "📊 Current issues:"
gh issue list
