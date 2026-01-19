#!/bin/bash
# Install codeindex skills for Claude Code
#
# Source: skills/src/
# Targets:
#   Project:  .claude/skills/ (auto-discovered, default)
#   Personal: ~/.claude/skills/ (globally available)
#
# Usage:
#   ./install.sh              # Install to project (default)
#   ./install.sh --project    # Same as above
#   ./install.sh --personal   # Install to ~/.claude/skills/

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_SRC="$SCRIPT_DIR/src"
PROJECT_TARGET="$PROJECT_ROOT/.claude/skills"
PERSONAL_TARGET="$HOME/.claude/skills"

# Parse arguments
TARGET_MODE="project"
if [[ "$1" == "--personal" ]]; then
    TARGET_MODE="personal"
elif [[ "$1" == "--project" ]] || [[ -z "$1" ]]; then
    TARGET_MODE="project"
elif [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo -e "${CYAN}codeindex Skills Installer${NC}"
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --project   Install to .claude/skills/ (default, auto-discovered)"
    echo "  --personal  Install to ~/.claude/skills/ (globally available)"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./install.sh              # Install to current project"
    echo "  ./install.sh --personal   # Install globally"
    exit 0
else
    echo -e "${RED}Unknown option: $1${NC}"
    echo "Use --help for usage information"
    exit 1
fi

echo -e "${CYAN}codeindex Skills Installer${NC}\n"

# Check source exists
if [ ! -d "$SKILLS_SRC" ]; then
    echo -e "${RED}Error: Source directory not found: $SKILLS_SRC${NC}"
    exit 1
fi

# Set target directory
if [[ "$TARGET_MODE" == "personal" ]]; then
    TARGET_DIR="$PERSONAL_TARGET"
    echo -e "Installing to: ${YELLOW}Personal Skills${NC} ($TARGET_DIR)\n"
else
    TARGET_DIR="$PROJECT_TARGET"
    echo -e "Installing to: ${YELLOW}Project Skills${NC} ($TARGET_DIR)\n"
fi

# Create target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}Creating $TARGET_DIR${NC}"
    mkdir -p "$TARGET_DIR"
fi

# Find and install all skills
installed=0
for skill_src in "$SKILLS_SRC"/*/; do
    if [ -d "$skill_src" ] && [ -f "$skill_src/SKILL.md" ]; then
        skill_name=$(basename "$skill_src")
        skill_dst="$TARGET_DIR/$skill_name"

        # Remove existing and copy fresh
        rm -rf "$skill_dst"
        cp -r "$skill_src" "$skill_dst"

        echo -e "${GREEN}✓${NC} Installed: $skill_name"
        ((installed++))
    fi
done

if [ $installed -eq 0 ]; then
    echo -e "${RED}No skills found in $SKILLS_SRC${NC}"
    exit 1
fi

echo -e "\n${GREEN}Done!${NC} Installed $installed skill(s) to: $TARGET_DIR"
echo ""
echo -e "Available commands:"
for skill_src in "$SKILLS_SRC"/*/; do
    if [ -d "$skill_src" ] && [ -f "$skill_src/SKILL.md" ]; then
        skill_name=$(basename "$skill_src")
        # Extract description from YAML front matter
        desc=$(grep -A1 "^description:" "$skill_src/SKILL.md" | head -1 | sed 's/description: //' | cut -c1-60)
        echo -e "  ${CYAN}/$skill_name${NC} - $desc..."
    fi
done

echo ""
if [[ "$TARGET_MODE" == "project" ]]; then
    echo -e "${YELLOW}Note:${NC} Project skills are auto-discovered when in this directory."
else
    echo -e "${YELLOW}Note:${NC} Restart Claude Code for personal skills to take effect."
fi
