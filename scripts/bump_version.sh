#!/bin/bash
# Version bump script for codeindex
# Usage: ./scripts/bump_version.sh 0.7.0

set -e

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "❌ Error: Version number required"
    echo "Usage: $0 <version>"
    echo "Example: $0 0.7.0"
    exit 1
fi

# Validate version format (semantic versioning)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Invalid version format"
    echo "Version must be in format: MAJOR.MINOR.PATCH (e.g., 0.7.0)"
    exit 1
fi

echo "🔄 Bumping version to $NEW_VERSION"

# 1. Update pyproject.toml
echo "  → Updating pyproject.toml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi

# 2. Update __init__.py (if exists)
if [ -f "src/codeindex/__init__.py" ]; then
    echo "  → Updating src/codeindex/__init__.py..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/codeindex/__init__.py
    else
        sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/codeindex/__init__.py
    fi
fi

# 3. Update CHANGELOG.md (add new version header)
echo "  → Updating CHANGELOG.md..."
TODAY=$(date +%Y-%m-%d)

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: 将 [Unreleased] 后面添加新版本
    sed -i '' "/## \[Unreleased\]/a\\
\\
## [$NEW_VERSION] - $TODAY
" CHANGELOG.md
else
    # Linux
    sed -i "/## \[Unreleased\]/a\\\n## [$NEW_VERSION] - $TODAY" CHANGELOG.md
fi

echo ""
echo "✅ Version bumped to $NEW_VERSION"
echo ""
echo "📋 Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Edit CHANGELOG.md: Move features from [Unreleased] to [$NEW_VERSION]"
echo "  3. Commit: git add . && git commit -m 'chore: bump version to $NEW_VERSION'"
echo "  4. Tag: git tag v$NEW_VERSION -m 'Release v$NEW_VERSION'"
echo "  5. Push: git push origin master --tags"
echo ""
echo "🚀 Or use automated release:"
echo "   ./scripts/release.sh $NEW_VERSION"
