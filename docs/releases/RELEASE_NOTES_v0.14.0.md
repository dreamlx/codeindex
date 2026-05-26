# Release Notes - v0.14.0

**Release Date**: 2026-02-10
**Theme**: User Onboarding Enhancement (用户引导体验增强)

---

## 🎯 Overview

v0.14.0 dramatically improves the first-time user experience with an intelligent setup wizard and comprehensive help system. This release enables both interactive human setup (<1 minute) and non-interactive CI/CD integration.

---

## ✨ Major Features

### 📋 Epic 15 - User Onboarding Enhancement

#### Story 15.1: Interactive Setup Wizard ⭐

**What's New**:
- Enhanced `codeindex init` with step-by-step intelligent wizard
- **Smart Auto-Detection**:
  - Programming languages (Python, PHP, Java - parser-supported only)
  - Web frameworks (Spring, ThinkPHP, Laravel)
  - Project structure for optimal include/exclude patterns
- **Auto-Tuning Performance Settings**:
  - `parallel_workers`: Optimized based on file count and CPU cores
  - `batch_size`: Dynamically adjusted for project size (20-100)
- **Optional Features**:
  - Git Hooks installation with mode selection (auto/async/sync/disabled)
  - CODEINDEX.md AI integration guide generation
  - AI CLI configuration (Claude, ChatGPT, custom)

**Non-Interactive Mode** (CI/CD Ready):
```bash
codeindex init --yes --quiet
```

**Test Coverage**: 18 BDD scenarios (100% passing)

#### Story 15.3: Enhanced Help System ⭐

**What's New**:
- Comprehensive configuration parameter documentation
- **Context-Aware Help**:
  - Shows current values from `.codeindex.yaml`
  - Validates settings against system resources (CPU count)
  - Warns about potential issues (e.g., parallel_workers > CPU count)

**New CLI Commands**:
```bash
# Detailed parameter help
codeindex config explain parallel_workers

# Full configuration reference
codeindex init --help-config
```

**Rich Documentation** for each parameter:
- Type, default value, valid range
- Usage recommendations (small/medium/large projects)
- Performance trade-offs
- YAML syntax examples

**Test Coverage**: 15 BDD scenarios (100% passing)

---

## 🐛 Critical Fixes

### Language Support Documentation Correction

**Issue**: Previous documentation incorrectly claimed support for JavaScript, TypeScript, Go, Rust, Ruby.

**Fixed**:
- **Clarified**: Only Python, PHP, Java have full parser support
- **Corrected wizard**: Commented out unsupported language detection
- **Updated help**: `config_help.py` now shows accurate language list
- **Updated ROADMAP.md**: Shifted TypeScript/JavaScript to v0.15.0, Go to v0.16.0

**User Feedback**: "JS, TS, Go, Rust, Ruby 我们好像还没有支持吧？" - Confirmed and corrected ✅

---

## 📊 Epic 12-14 (Bundled from previous work)

### Epic 12: Single File Parse Command

- New `codeindex parse <file>` command
- JSON output for tool integration
- Support for Python, PHP, Java

### Epic 13: Parser Modularization

- Refactored `parser.py` (3622→374 lines, -89.7%)
- Modular architecture: `parsers/` package
- Benefits: maintainability, extensibility, reduced technical debt

### Epic 14: Windows Platform Compatibility

- **UTF-8 Encoding Fix**: Cross-platform README_AI.md compatibility
- **Path Length Optimization**: 40-60% reduction, supports deep directories
- Fixed `**/__pycache__/**` pattern matching

---

## 📈 Statistics

- **Total Tests**: 977 passing, 11 skipped (100% pass rate)
- **Test Coverage**: 33 new BDD tests for Epic 15
- **Code Added**: ~3,785 lines
- **New Modules**:
  - `init_wizard.py` (543 lines)
  - `config_help.py` (295 lines)
  - `cli_config_commands.py` (46 lines)

---

## 🔧 Breaking Changes

**None**. This release is 100% backward compatible.

---

## 📚 Documentation Updates

- Updated `ROADMAP.md`: Corrected version timeline and language support
- Archived Epic 15 to `docs/planning/completed/`
- Updated `docs/planning/README.md`: Added Epic 11-15 completion records

---

## 🚀 Getting Started

### New Users

```bash
# Interactive setup (recommended)
pipx install ai-codeindex[all]
cd your-project
codeindex init
```

### CI/CD Integration

```bash
# Non-interactive setup
codeindex init --yes --quiet
```

### Explore Help System

```bash
# Full configuration reference
codeindex init --help-config

# Specific parameter help
codeindex config explain parallel_workers
codeindex config explain batch_size
```

---

## 🙏 Acknowledgments

Special thanks to user feedback that identified the language support documentation issue and prompted immediate correction.

---

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

**Upgrade Command**:
```bash
pipx upgrade ai-codeindex[all]
```

**Previous Release**: [v0.12.0](RELEASE_NOTES_v0.12.0.md)
**GitHub Release**: https://github.com/dreamlx/codeindex/releases/tag/v0.14.0
