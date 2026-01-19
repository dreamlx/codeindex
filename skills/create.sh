#!/bin/bash
# Create a new skill template
#
# Usage:
#   ./create.sh <skill-name>
#   ./create.sh <skill-name> --edit
#
# Example:
#   ./create.sh my-feature
#   ./create.sh my-feature --edit  # Opens in $EDITOR

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/src"

# Check arguments
if [[ -z "$1" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo -e "${CYAN}Create New Skill${NC}"
    echo ""
    echo "Usage: ./create.sh <skill-name> [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  skill-name   Name of the skill (lowercase, no spaces)"
    echo ""
    echo "Options:"
    echo "  --edit       Open SKILL.md in \$EDITOR after creation"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./create.sh my-feature"
    echo "  ./create.sh code-review --edit"
    echo ""
    echo "Skill Structure:"
    echo "  skills/src/<name>/"
    echo "  └── SKILL.md    # Required: Instructions + YAML front matter"
    exit 0
fi

SKILL_NAME="$1"
OPEN_EDITOR=false
if [[ "$2" == "--edit" ]]; then
    OPEN_EDITOR=true
fi

# Validate skill name
if [[ ! "$SKILL_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo -e "${RED}Error: Skill name must be lowercase, start with a letter, and contain only letters, numbers, and hyphens${NC}"
    echo "Example: my-feature, code-review, doc-gen"
    exit 1
fi

if [[ ${#SKILL_NAME} -gt 64 ]]; then
    echo -e "${RED}Error: Skill name must be 64 characters or less${NC}"
    exit 1
fi

SKILL_DIR="$SKILLS_SRC/$SKILL_NAME"

# Check if already exists
if [ -d "$SKILL_DIR" ]; then
    echo -e "${RED}Error: Skill '$SKILL_NAME' already exists at $SKILL_DIR${NC}"
    exit 1
fi

echo -e "${CYAN}Creating skill: $SKILL_NAME${NC}\n"

# Create directory
mkdir -p "$SKILL_DIR"

# Create SKILL.md template
cat > "$SKILL_DIR/SKILL.md" << 'EOF'
---
name: SKILL_NAME_PLACEHOLDER
description: Brief description of what this skill does. Use when user wants to [action]. Triggered by phrases like "[trigger phrase 1]", "[trigger phrase 2]".
---

# SKILL_NAME_PLACEHOLDER

Brief description of the skill's purpose.

## Trigger Scenarios

Use this skill when user:
- Asks about [topic 1]
- Wants to [action 1]
- Says "[trigger phrase]"

## Workflow

### Step 1: Gather Context

```bash
# Example command
ls -la
```

### Step 2: Perform Action

Describe what to do...

### Step 3: Verify Results

Check that the action completed successfully.

## Response Format

When responding:
1. **Start with location/context**
2. **Explain the purpose**
3. **Show relationships/dependencies**
4. **Provide code references if needed**

## Best Practices

- Tip 1
- Tip 2
- Tip 3
EOF

# Replace placeholder with actual skill name
sed -i '' "s/SKILL_NAME_PLACEHOLDER/$SKILL_NAME/g" "$SKILL_DIR/SKILL.md"

echo -e "${GREEN}✓${NC} Created: $SKILL_DIR/SKILL.md"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Edit the SKILL.md file to add your instructions"
echo "  2. Update the 'description' field in YAML front matter (critical for triggering!)"
echo "  3. Run ./install.sh to deploy to project"
echo ""
echo -e "File location: ${CYAN}$SKILL_DIR/SKILL.md${NC}"

# Open in editor if requested
if [[ "$OPEN_EDITOR" == true ]]; then
    if [[ -n "$EDITOR" ]]; then
        echo -e "\nOpening in $EDITOR..."
        $EDITOR "$SKILL_DIR/SKILL.md"
    elif command -v code &> /dev/null; then
        echo -e "\nOpening in VS Code..."
        code "$SKILL_DIR/SKILL.md"
    elif command -v vim &> /dev/null; then
        echo -e "\nOpening in vim..."
        vim "$SKILL_DIR/SKILL.md"
    else
        echo -e "\n${YELLOW}No editor found. Please edit manually:${NC}"
        echo "  $SKILL_DIR/SKILL.md"
    fi
fi
