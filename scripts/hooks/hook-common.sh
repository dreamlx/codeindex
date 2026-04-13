#!/bin/zsh
# Common utilities for Git hooks
# Source this file in all hooks to reduce code duplication

# ============================================
# Color Definitions
# ============================================
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[0;33m'
export CYAN='\033[0;36m'
export RESET='\033[0m'

# ============================================
# Repository Utilities
# ============================================

# Get repository root directory
get_repo_root() {
    git rev-parse --show-toplevel
}

# ============================================
# Virtual Environment Management
# ============================================

# Activate virtual environment (required for all hooks)
# Returns 0 on success, 1 on failure
activate_venv() {
    local repo_root=$(get_repo_root)

    if [ -f "$repo_root/.venv/bin/activate" ]; then
        source "$repo_root/.venv/bin/activate"
        return 0
    elif [ -f "$repo_root/venv/bin/activate" ]; then
        source "$repo_root/venv/bin/activate"
        return 0
    else
        echo -e "${RED}✗ Virtual environment not found${RESET}"
        echo -e "${YELLOW}→ Create with: python3 -m venv .venv${RESET}"
        echo -e "${YELLOW}→ Install: pip install -e '.[dev,all]'${RESET}"
        return 1
    fi
}

# ============================================
# Tool Discovery
# ============================================

# Find a tool (prefer venv, fallback to system)
# Usage: find_tool ruff
# Returns: path to tool or empty string (sets exit code)
find_tool() {
    local tool=$1
    local repo_root=$(get_repo_root)

    if [ -f "$repo_root/.venv/bin/$tool" ]; then
        echo "$repo_root/.venv/bin/$tool"
        return 0
    elif command -v $tool &> /dev/null; then
        echo "$tool"
        return 0
    else
        echo -e "${RED}✗ $tool not found${RESET}" >&2
        echo -e "${YELLOW}→ Install: pip install $tool${RESET}" >&2
        return 1
    fi
}

# ============================================
# Time Measurement
# ============================================

# Start timing (returns timestamp)
time_start() {
    date +%s
}

# End timing and return elapsed seconds
# Usage: elapsed=$(time_end $start_time)
time_end() {
    local start=$1
    local end=$(date +%s)
    echo $((end - start))
}

# ============================================
# Pretty Output
# ============================================

# Print section header
section_header() {
    local message=$1
    echo -e "${CYAN}${message}${RESET}"
}

# Print success message
success() {
    local message=$1
    echo -e "${GREEN}✓ ${message}${RESET}"
}

# Print warning message
warning() {
    local message=$1
    echo -e "${YELLOW}⚠ ${message}${RESET}"
}

# Print error message
error() {
    local message=$1
    echo -e "${RED}✗ ${message}${RESET}"
}

# Print completion message with time
completed() {
    local hook_name=$1
    local elapsed=$2
    echo ""
    echo -e "${GREEN}✓ [$hook_name] Completed in ${elapsed}s${RESET}"
}
