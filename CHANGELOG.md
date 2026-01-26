# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Epic 2: Adaptive Symbol Extraction 🎉
- **Adaptive symbol extraction** based on file size (5-150 symbols per file)
- 7-tier file size classification system (tiny/small/medium/large/xlarge/huge/mega)
- `AdaptiveSymbolsConfig` data structure for flexible configuration
- `AdaptiveSymbolSelector` with intelligent limit calculation algorithm
- `file_lines` field in ParseResult for file size tracking
- YAML configuration support for adaptive symbols settings
- 69 new tests for adaptive functionality (18+13+30+8)
- Comprehensive validation report (docs/epic2-validation-report.md)

### Changed - Epic 2
- **SmartWriter** now uses adaptive symbol limits when enabled
- **Config system** supports adaptive_symbols configuration with defaults merging
- **Symbol display** dynamically adjusts from fixed 15 to 5-150 based on file size
- Large file information coverage improved from 26% to 100% (+280%)
- Truncation messages now use filtered symbol count (bug fix)

### Added - Documentation
- Comprehensive documentation structure (docs/)
- Architecture Decision Records (ADR)
- Getting started guide
- Configuration guide
- Roadmap for 2025 Q1
- Epic 2 validation report with real-world testing results

### Changed - Structure
- Migrated design docs to docs/architecture/
- Improved project structure

### Performance
- Adaptive calculation overhead: <1%
- No regression in parsing speed
- Memory usage stable

### Backward Compatibility
- ✅ Adaptive symbols disabled by default (enabled: false)
- ✅ All existing configurations work without modification
- ✅ 66 regression tests passing

## [0.1.3] - 2025-01-15

### Added
- `PROJECT_INDEX.json` and `PROJECT_INDEX.md` for codebase navigation
- System environment reporter example
- Improved README_AI.md auto-generation

### Changed
- Documentation updates
- Version bump to 0.1.3

## [0.1.2] - 2025-01-14

### Added
- Parallel scanning support with `codeindex list-dirs`
- `--dry-run` flag for prompt preview
- Status command to check indexing coverage
- Better error handling for AI CLI failures

### Changed
- Improved CLI output formatting
- Better timeout handling (default 120s)

### Fixed
- Unicode handling in prompts
- Path resolution on Windows

## [0.1.1] - 2025-01-13

### Added
- `--fallback` mode for generating docs without AI
- Configuration validation
- Example `.codeindex.yaml` in examples/

### Fixed
- Tree-sitter grammar installation issues
- Import parsing edge cases

## [0.1.0] - 2025-01-12

### Added
- Initial release
- Python code parsing with tree-sitter
- CLI commands: `scan`, `init`, `status`, `list-dirs`
- External AI CLI integration
- Configuration system (`.codeindex.yaml`)
- Symbol extraction (classes, functions, methods, imports)
- README_AI.md generation
- Basic test suite

### Features
- Parse Python files and extract symbols
- Generate documentation via external AI CLI
- Configurable include/exclude patterns
- Timeout and error handling
- Development mode installation

[Unreleased]: https://github.com/yourusername/codeindex/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/yourusername/codeindex/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/yourusername/codeindex/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/yourusername/codeindex/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/yourusername/codeindex/releases/tag/v0.1.0
