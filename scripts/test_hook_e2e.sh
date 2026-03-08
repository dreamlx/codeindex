#!/usr/bin/env bash
# Epic #25, Story #26: E2E test for post-install hook
# Tests the hook in a simulated real environment

set -e

echo "🔍 E2E Test: Post-install Hook"
echo "================================"

# Create temporary test directory
TEST_DIR=$(mktemp -d)
echo "Test directory: $TEST_DIR"

# Setup fake home with .claude directory
FAKE_HOME="$TEST_DIR/home"
mkdir -p "$FAKE_HOME/.claude"

# Create initial CLAUDE.md
cat > "$FAKE_HOME/.claude/CLAUDE.md" <<EOF
# My Claude Configuration

Some custom content here.

<!-- CODEINDEX_GUIDE_START v0.11.0 -->
Old codeindex guide from v0.11.0
<!-- CODEINDEX_GUIDE_END -->

More custom content below.
EOF

echo "✅ Created test CLAUDE.md with v0.11.0 content"

# Invoke the hook with fake HOME
export HOME="$FAKE_HOME"
python3 -c "
import sys
sys.path.insert(0, 'src')
from codeindex.hooks import post_install_update_guide
post_install_update_guide()
"

# Verify results
echo ""
echo "📋 Verification:"
echo "================"

# Check if version was updated
if grep -q "<!-- CODEINDEX_GUIDE_START v0.22.2 -->" "$FAKE_HOME/.claude/CLAUDE.md"; then
    echo "✅ Version marker updated to v0.22.2"
else
    echo "❌ Version marker NOT updated"
    exit 1
fi

# Check if core commands are present
if grep -q "codeindex scan" "$FAKE_HOME/.claude/CLAUDE.md"; then
    echo "✅ Core commands present"
else
    echo "❌ Core commands missing"
    exit 1
fi

# Check if custom content was preserved
if grep -q "My Claude Configuration" "$FAKE_HOME/.claude/CLAUDE.md"; then
    echo "✅ Custom content preserved (header)"
else
    echo "❌ Custom content lost"
    exit 1
fi

if grep -q "More custom content below" "$FAKE_HOME/.claude/CLAUDE.md"; then
    echo "✅ Custom content preserved (footer)"
else
    echo "❌ Custom content lost"
    exit 1
fi

# Check if backup was created
BACKUP_COUNT=$(find "$FAKE_HOME/.claude" -name "CLAUDE.md.backup.*" | wc -l)
if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo "✅ Backup created ($BACKUP_COUNT file(s))"
else
    echo "❌ No backup created"
    exit 1
fi

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "🎉 All E2E tests passed!"
