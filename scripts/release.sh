#!/bin/bash
# Complete release automation script for codeindex
# Usage: ./scripts/release.sh 0.7.0

set -e

VERSION=$1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ -z "$VERSION" ]; then
    echo -e "${RED}❌ Error: Version number required${NC}"
    echo "Usage: $0 <version>"
    echo "Example: $0 0.7.0"
    exit 1
fi

echo -e "${CYAN}🚀 Releasing codeindex v$VERSION${NC}"
echo ""

# 0. Check prerequisites
echo -e "${YELLOW}0️⃣  Checking prerequisites...${NC}"
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || { echo "❌ Python not found"; exit 1; }
command -v pip3 >/dev/null 2>&1 || command -v pip >/dev/null 2>&1 || { echo "❌ pip not found"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git not found"; exit 1; }

# Check if on master branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "master" ] && [ "$BRANCH" != "main" ]; then
    echo -e "${RED}❌ Not on master/main branch (current: $BRANCH)${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Uncommitted changes detected${NC}"
    git status --short
    read -p "Stash and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash
    else
        exit 1
    fi
fi

# 1. Run tests
echo ""
echo -e "${YELLOW}1️⃣  Running tests...${NC}"
if ! pytest -v --tb=short; then
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Tests passed${NC}"

# 2. Run linter
echo ""
echo -e "${YELLOW}2️⃣  Running linter...${NC}"
if ! ruff check src/; then
    echo -e "${RED}❌ Lint errors found!${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo -e "${GREEN}✓ Linter passed${NC}"

# 3. Bump version
echo ""
echo -e "${YELLOW}3️⃣  Bumping version...${NC}"
./scripts/bump_version.sh $VERSION
echo -e "${GREEN}✓ Version bumped${NC}"

# 4. Verify CHANGELOG has version entry
echo ""
echo -e "${YELLOW}4️⃣  Verifying CHANGELOG.md...${NC}"
if ! grep -q "## \[$VERSION\]" CHANGELOG.md; then
    echo -e "${RED}❌ Version [$VERSION] not found in CHANGELOG.md${NC}"
    echo ""
    echo -e "${YELLOW}   CHANGELOG.md should already have a [$VERSION] section.${NC}"
    echo -e "${YELLOW}   Best practice: update [Unreleased] section during development,${NC}"
    echo -e "${YELLOW}   then rename it to [$VERSION] before releasing.${NC}"
    echo ""
    read -p "   Open CHANGELOG.md to fix? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-vim} CHANGELOG.md
        # Re-check after edit
        if ! grep -q "## \[$VERSION\]" CHANGELOG.md; then
            echo -e "${RED}❌ Still no [$VERSION] section. Aborting.${NC}"
            exit 1
        fi
    else
        exit 1
    fi
fi
echo -e "${GREEN}✓ CHANGELOG.md has [$VERSION] entry${NC}"

# 5. Review changes
echo ""
echo -e "${YELLOW}5️⃣  Review changes${NC}"
git diff pyproject.toml src/codeindex/__init__.py CHANGELOG.md

read -p "Commit these changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Release cancelled${NC}"
    exit 1
fi

# 6. Commit changes
echo ""
echo -e "${YELLOW}6️⃣  Committing changes...${NC}"
git add pyproject.toml src/codeindex/__init__.py CHANGELOG.md
git commit -m "chore: bump version to $VERSION"
echo -e "${GREEN}✓ Changes committed${NC}"

# 6.5 Refresh README_AI indexes (release-time, per #166 — not per-commit)
echo ""
echo -e "${YELLOW}6️⃣.5️⃣  Refreshing README_AI indexes...${NC}"
codeindex scan-all
codeindex claude-md update
git add CLAUDE.md PROJECT_SYMBOLS.md '*README_AI.md'
git diff --cached --quiet || git commit -m "docs: refresh README_AI for v$VERSION"

# 7. Create tag
echo ""
echo -e "${YELLOW}7️⃣  Creating tag v$VERSION...${NC}"
git tag v$VERSION -m "Release v$VERSION"
echo -e "${GREEN}✓ Tag created${NC}"

# 8. Build distributions
echo ""
echo -e "${YELLOW}8️⃣  Building distributions...${NC}"
rm -rf dist/ build/ *.egg-info src/*.egg-info
python3 -m build
echo -e "${GREEN}✓ Distributions built${NC}"

# 9. Check distributions
echo ""
echo -e "${YELLOW}9️⃣  Checking distributions...${NC}"
twine check dist/*
echo -e "${GREEN}✓ Distributions checked${NC}"

# 10. Upload to TestPyPI
echo ""
echo -e "${YELLOW}🔟 Upload to TestPyPI${NC}"
read -p "   Upload to TestPyPI first? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if twine upload --repository testpypi dist/*; then
        echo -e "${GREEN}✓ Uploaded to TestPyPI${NC}"
        echo "   View at: https://test.pypi.org/project/codeindex/$VERSION/"

        # Test installation
        read -p "   Test installation from TestPyPI? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip install --index-url https://test.pypi.org/simple/ \
                        --extra-index-url https://pypi.org/simple/ \
                        --upgrade "ai-codeindex==$VERSION"

            # Verify
            if codeindex --version | grep -q "$VERSION"; then
                echo -e "${GREEN}✓ TestPyPI installation successful${NC}"
            else
                echo -e "${RED}❌ Version mismatch!${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠ TestPyPI upload failed (may already exist)${NC}"
    fi
fi

# 11. Upload to PyPI
echo ""
echo -e "${YELLOW}1️⃣1️⃣ Upload to PyPI${NC}"
echo -e "${RED}   ⚠️  This will publish to production PyPI!${NC}"
read -p "   Continue with PyPI upload? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if twine upload dist/*; then
        echo -e "${GREEN}✓ Uploaded to PyPI${NC}"

        # 12. Push to GitHub
        echo ""
        echo -e "${YELLOW}1️⃣2️⃣ Pushing to GitHub...${NC}"
        git push origin $BRANCH --tags
        echo -e "${GREEN}✓ Pushed to GitHub${NC}"

        # Success!
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✅ Release v$VERSION completed!${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "📦 PyPI: ${CYAN}https://pypi.org/project/codeindex/$VERSION/${NC}"
        echo -e "🐙 GitHub: ${CYAN}https://github.com/yourusername/codeindex/releases/tag/v$VERSION${NC}"
        echo ""
        echo "📋 Next steps:"
        echo "  1. Create GitHub Release (automated by Actions)"
        echo "  2. Announce on social media"
        echo "  3. Update documentation site"
        echo ""
    else
        echo -e "${RED}❌ PyPI upload failed!${NC}"
        echo "   You may need to:"
        echo "   1. Check your PyPI API token"
        echo "   2. Verify version doesn't already exist"
        echo "   3. Run 'twine upload dist/*' manually"
        exit 1
    fi
else
    echo -e "${YELLOW}❌ Release cancelled (PyPI upload skipped)${NC}"
    echo ""
    echo "To complete later:"
    echo "  twine upload dist/*"
    echo "  git push origin $BRANCH --tags"
    exit 1
fi
