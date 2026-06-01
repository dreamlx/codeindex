# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **`codeindex list-dirs` no longer silently returns empty when configured `languages` doesn't match present files** (GH #74): previously, `list-dirs` printed nothing and exited 0 whenever the language filter excluded everything — indistinguishable from "nothing to index" and the single worst UX class (agents loop through `--help` / `docs` / `doctor` / `pipx list` debugging; humans give up). New `scanner.diagnose_language_mismatch` helper walks the include roots, counts actual file extensions, and identifies which codeindex-supported languages would cover them. When `list-dirs` returns empty AND files-with-known-extensions are present, it now raises a `ClickException` to stderr with the configured `languages`, the top file types seen, and the specific languages to add (e.g. "add `typescript / javascript` to `.codeindex.yaml` `languages:`"). Truly empty include roots stay silent + exit 0 — preserving scripts that pipe `list-dirs` as a "anything to index?" probe.
- **`codeindex init` now detects TypeScript / JavaScript projects** (GH #73): `init_wizard.py` carried a stale local `LANGUAGE_EXTENSIONS` map listing only Python / PHP / Java behind a "no parser yet" comment, despite `scanner.py` having gained TS/JS parsers (and full parser modules existing under `src/codeindex/parsers/typescript/`). On a TS-only repo, `detect_languages()` returned `[]` → no `languages:` block was written → at scan time the runtime defaulted to `DEFAULT_LANGUAGES=["python"]` → 0 files matched → silent `list-dirs` empty (the user-visible symptom). Fix imports `LANGUAGE_EXTENSIONS` from `scanner.py` as the single source of truth, so any language the scanner supports is now also detectable by init. Verified end-to-end on a TS fixture (`init --yes` writes `languages: [typescript]`, `list-dirs` returns the include root). A new structural test `test_init_language_set_covers_scanner_supported_set` locks the invariant — adding a language to scanner.py will fail this test until init can also see it, preventing the drift class from recurring.
- **Navigation-level `README_AI.md` no longer flattens descendant files into `## Files`** (GH #76): nav-level scans are recursive (per the GH #45 stats note), so `parse_results` includes every descendant. `NavigationGenerator` was iterating them with `result.path.name` only — dropping the path prefix — so a subdir file like `src/components/ui/badge.tsx` showed up in `src/README_AI.md`'s `## Files` as bare `badge.tsx`. Any agent reading `src/README_AI.md` then issuing `Read src/badge.tsx` got a 404 (or worse: a confident wrong-file Read on a name collision). Fix filters `parse_results` to `r.path.parent == dir_path` before grouping. Each subdir's files remain available via that subdir's own `README_AI.md`. Verified on fabricOS: `src/README_AI.md ## Files` shrank from 33 flattened entries to the single real direct child `main.tsx`. Test helpers `_make_result` / `_create_mock_parse_result` gained an optional `parent_dir` kwarg so fixtures pass through the new filter when a `tmp_path` is the dir under test.
- **Structural rewrites no longer wipe AI enrichment** (GH #38): a `scan-all --ai` run injects an `<!-- enrichment: ok -->` marker and a `> description` blockquote, but any later structural-only write — a post-commit hook running `scan-all` without `--ai`, or Phase 1 of the next `--ai` run — used to erase both. The idempotent cache then went cold, so the next `scan-all --ai` re-paid the full N AI calls instead of restoring from cache. `SmartWriter.write_readme` now captures the ok marker + blockquote before overwriting and re-injects them, so the cache stays warm across non-AI invocations. Unenriched READMEs are untouched (no fabricated marker).

## [0.25.0] - 2026-05-26

**Theme**: distribution split — `pipx` CLI + Claude Code plugin. See [release notes](docs/releases/RELEASE_NOTES_v0.25.0.md) + [ADR-006](docs/architecture/adr/006-distribution-architecture-split.md).

### Changed

- **`codeindex init` is now minimal** (B1): creates only project-scoped scaffolding — `.codeindex.yaml`, a codeindex section injected into the project's `CLAUDE.md`, and a `.gitignore` entry. It no longer creates `CODEINDEX.md` or installs git hooks. Hooks are opt-in via `codeindex hooks install`; Claude Code users get richer `CLAUDE.md` upkeep via the plugin. `init` has never touched `~/.claude/*` and a regression test now locks that invariant.
- **Recommended install is `pipx install ai-codeindex`** (B2): the README leads with pipx (isolated CLI env, no dependency conflicts); `pip install --user` is the fallback. Added a China-mirror footnote (`pipx install --index-url https://pypi.org/simple/ ai-codeindex`) for when a local mirror lags upstream PyPI.

### Added

- **Claude Code plugin** ([dreamlx/codeindex-claude](https://github.com/dreamlx/codeindex-claude)): bundles the four skills (`codeindex:arch` / `:index` / `:hooks` / `:update-guide`) plus a SessionStart hook that checks the CLI is on `PATH`. Install with `/plugin marketplace add dreamlx/codeindex-claude` + `/plugin install codeindex@codeindex-claude`. This replaces the in-repo `skills/install.sh` mechanism. The plugin skills orchestrate the CLI — e.g. `codeindex:update-guide` drives `codeindex claude-md update`, `codeindex:hooks` drives `codeindex hooks install` — so the CLI commands remain first-class (see [ADR-006](docs/architecture/adr/006-distribution-architecture-split.md) "engine vs affordance").
- **`codeindex doctor`**: read-only health/sync diagnostic. Reports the installed CLI version, `.codeindex.yaml` presence + language-parser health, the project `CLAUDE.md` codeindex-section version vs the CLI, and — when a Claude Code environment is detected — the installed `codeindex-claude` plugin version. Each problem prints an actionable fix (`pipx inject …` for missing parsers, `codeindex claude-md update` for a stale section, `/plugin install …` when the plugin is absent). Editor-agnostic: the plugin section is skipped silently when `~/.claude/plugins` doesn't exist, so Cursor / bare-CLI users get a clean report. Exits non-zero when an error-level finding (e.g. a configured language with no installed parser) is present, so it's CI-usable. Never mutates anything. This is the single place that answers "am I up to date across the two artifacts, and what do I upgrade?"

### Deprecated

- **`skills/` directory + `skills/install.sh`** (B4): the old skill installer now warns and defaults to abort, pointing users to the plugin. The directory is removed in v1.0. (Note: the `codeindex claude-md` and `codeindex hooks` *CLI commands* are **not** deprecated — they are the engine the plugin skills ride on. An earlier plan to deprecate them was reverted; see ADR-006.)

## [0.24.0] - 2026-05-25

**Theme**: navigation contract — see [release notes](docs/releases/RELEASE_NOTES_v0.24.0.md) + [ADR-005](docs/architecture/adr/005-navigation-disclaimer-and-readme-size-cap.md).

### Added

- **Navigation-contract disclaimer at top of every `README_AI.md`** (`<!-- codeindex navigation index — agent: drill into source via Read/Grep for precise mechanism; do not treat this as final word. -->`). Injected by all 5 generation sites (`writers/{overview,navigation,detailed}_generator.py`, `hierarchical.py`, `writer.py` base+fallback) via the new `writers.NAVIGATION_DISCLAIMER` constant. Tells AI agents to use the index as orientation only and verify details in source. Backed by Phase F benchmark (2026-05): when agents over-trusted oversized READMEs they returned wrong answers on 3/15 detail questions while running faster — the speed gain hid quality loss. Renderers ignore the HTML comment so human-facing markdown is unchanged. `cli_symbols.py` Purpose-section parser is unaffected (comments don't interfere with markdown section detection).
- **`enricher.mark_enrichment_status()`**: Records AI enrichment outcome as `<!-- enrichment: ok | failed (reason: ...) -->` HTML comment under the Generated header in `README_AI.md`. Lets AI consumers distinguish "structural-only by config" (no marker) from "enrichment attempted and failed" (marker with reason).
- **`enricher.build_safe_subdir_context()`**: Builds AI-enrichment prompt context from `DirectoryTree.get_children()` (bare subdir names only). Used by `_enrich_directories_with_ai` ahead of `extract_summary_from_readme`. Closes a prompt-injection chain where README markdown — containing AI-generated descriptions sourced from arbitrary source docstrings — was regex-extracted and fed into the next enrichment prompt. The README-parsing path remains as fallback for dirs without indexed children.
- **Idempotent `scan-all --ai` re-runs**: Phase 2 now snapshots existing enrichment state (`enricher.extract_blockquote_description()` + `enricher.has_successful_enrichment()`) *before* Phase 1 rewrites READMEs, then re-injects cached descriptions for already-ok dirs without firing fresh AI calls. After a transient-failure scenario (e.g. claude-API rate limit on N/M dirs), the user just re-runs `codeindex scan-all --ai` and only the previously-failed dirs hit the AI backend; successes cost zero tokens. Use `--retry-all` to force a real AI call for every dir.
- **Failure-summary hint**: When Phase 2 has any failed dirs, prints a short list plus actionable next steps (retry / `--retry-all` / switch `ai_command` to `claude --model haiku` / `opencode` / `gemini`). Per design: no auto-fallback — surface the options, let the user choose.

### Changed

- **AI enrichment error surfaces stderr**: `scan-all --ai` previously logged opaque `⚠ <dir>: AI error` and dropped `invoke_result.error`. Now logs `⚠ <dir>: AI error — <first line of stderr>` and writes the same reason into the directory's README via `mark_enrichment_status(..., "failed", reason=...)`. Successful enrichment writes `<!-- enrichment: ok -->`.
- **Documentation: removed `--fallback` from recommended commands** (CLAUDE.md, requirements-workflow.md, pypi-release-guide.md). Flag has been deprecated since structural mode became default; the hidden flag still accepts/warns for backward compat.

### Fixed

- **Navigation-level READMEs double-counted files and symbols** (GH #45). `NavigationGenerator` was adding child-README aggregates on top of `parse_results`, but `cli_scan.py` runs navigation-level scans with `recursive=True` — so `parse_results` already covered descendants. Result: nav-level `**Files**`/`**Symbols**` were inflated (e.g. `src/codeindex/parsers/` showed `Files: 64` instead of the true 34). Overview-level aggregation is unchanged (that path scans non-recursively and legitimately needs to sum child stats). Bug introduced in 1355b0a (pre-v0.18.0); became more visible in v0.24.0 because the 10KB `max_readme_size` cap bumped more dirs into the navigation tier.

## [0.23.2] - 2026-04-14

### Changed

- **Hook shebangs**: `#!/bin/zsh` → `#!/usr/bin/env bash` for cross-platform portability.
- **Unified hook install**: `make install-hooks` now delegates to `codeindex hooks install --all`.
- **Post-commit logging**: stderr redirected to `~/.codeindex/hooks/post-commit.log` instead of `/dev/null`.
- **Debug detection**: Replaced ~50 lines of regex-based L2 check with ruff `T201`/`T100` rules.

### Added

- **`hook-common.sh` versioned**: Added to `scripts/hooks/` and auto-copied on `codeindex hooks install`.
- **mypy**: Added as dev dependency with baseline config; CI runs informational type check on core modules.
- **Coverage gate**: CI enforces `--cov-fail-under=78` to prevent coverage regression.
- **`make typecheck`**: New Makefile target for mypy on core modules.

## [0.23.1] - 2026-03-15

### Added

- **`codeindex claude-md update/status` CLI commands**: Manage codeindex section in project CLAUDE.md with version tracking.
- **Startup version-outdated hint**: Every `codeindex` CLI invocation checks if CLAUDE.md section is outdated and prints a reminder.
- **Unified `claude_md.py` module**: Single source of truth for CLAUDE.md injection, replacing fragmented hooks.py + init_wizard.py logic.

### Changed

- **CLAUDE.md template simplified**: 130 lines → 22 lines. Removed hardcoded paths, language support table, and verbose configuration examples.
- **Unified marker format**: `<!-- codeindex:start v{version} -->` with backward compatibility for old markers without version.
- **`init_wizard.py` injection**: Now delegates to `claude_md.py` module instead of inline template.

### Fixed

- **Dead code cleanup**: Removed `hooks.py` `post_install_update_guide()` (181 lines) that was never wired to pip entry points.
- **Dead import fix**: `cli_config.py` referenced non-existent `install_hooks` from `hooks.py`, now uses correct `install_hook` from `cli_hooks.py`.

## [0.23.0] - 2026-03-12

### Added

- **AI-Enhanced Module Descriptions** (Epic #25, Stories 25.1–25.3): Redefine `--ai` mode from full AI takeover to structural + AI micro-enhancement.
  - **Blockquote description support**: `extract_module_description()` now reads `> description` as Strategy 0 (highest priority)
  - **AI enrichment module** (`src/codeindex/enricher.py`): Generates one-line functional descriptions per module using symbol names + file names
  - **Concise prompt design**: ~200-400 tokens per directory, ≤30 char output, 10-20x cheaper than old `--ai` mode
  - **Batch AI calls**: Groups multiple directories per AI invocation to reduce overhead
  - **scan-all auto-AI**: Automatically enables Phase 2 AI enrichment when `ai_command` is configured (no `--ai` flag needed)
  - **`--no-ai` opt-out**: Explicitly disable AI enrichment for structural-only output
  - **`--ai` / `--no-ai` mutual exclusion**: Clear error when both flags are used

- **Post-commit hook thin wrapper** (Issue #30 fix): Redesigned hook architecture for maintainability.
  - **Thin shell wrapper** (~30 lines): Only handles loop guard + venv activation
  - **Python logic** via `codeindex hooks run post-commit`: All business logic in upgradeable Python
  - **Upgrade path**: `pip install --upgrade ai-codeindex` auto-updates hook behavior (no reinstall needed)
  - **No custom AI prompts**: Uses `codeindex scan` pipeline, eliminating commit changelog noise

### Fixed

- **AI mode commit changelog noise** (#30): Post-commit hook no longer injects git diff into custom AI prompts. Uses standard `codeindex scan` pipeline instead.
- **Enricher prompt accuracy**: Improved from "20 chars/brief" to "30 chars/concise" for better description quality.

### Changed

- **`--no-ai` flag**: Changed from hidden/deprecated to active opt-out flag for scan-all.
- **Post-commit hook generation**: `_generate_post_commit_script()` now generates thin wrapper delegating to Python.
- **Documentation**: All hook and scan-all docs rewritten for AI CLI agent readers.

### Technical Details

- **New module**: `src/codeindex/enricher.py` — AI enrichment with `enrich_directory()` and `_enrich_directories_with_ai()`
- **New CLI subcommand**: `codeindex hooks run post-commit` — Python-side post-commit logic
- **New tests**: 15 tests (7 scan-all auto-AI + 8 post-commit hook)
- **Total tests**: 1532 passed

## [0.22.2] - 2026-03-08

### Added

- **Post-install hook for automatic CLAUDE.md updates** (Epic #25, Story #26): Automatically updates `~/.claude/CLAUDE.md` after `pip install --upgrade ai-codeindex`.
  - **Marker-based injection**: Idempotent updates using `<!-- CODEINDEX_GUIDE_START vX.X.X -->` markers
  - **Version detection**: Automatically extracts and updates version numbers
  - **Backup creation**: Creates timestamped backups before modification (`CLAUDE.md.backup.YYYYMMDD_HHMMSS`)
  - **CI environment detection**: Skips updates in GitHub Actions, GitLab CI, Jenkins, CircleCI, and generic CI environments
  - **Silent failure handling**: Gracefully handles permission errors and missing directories
  - **Content preservation**: Preserves user customizations before/after guide section
  - **Template system**: Uses `src/codeindex/templates/claude_md_core.md` for guide content

- **Core guide template** (`src/codeindex/templates/claude_md_core.md`): Comprehensive codeindex usage guide for Claude Code users.
  - **Complete command reference**: All core commands (scan, tech-debt, symbols, index, status)
  - **Language support table**: 9 languages with version information
  - **Best practices**: AI Code integration workflow and tips
  - **Auto-updated on install**: Version number dynamically replaced from package metadata

### Technical Details

- **Implementation**: `src/codeindex/hooks.py` with 4 core functions:
  - `_is_ci_environment()`: CI/CD detection (6 environment variables)
  - `_extract_version_from_file()`: Regex-based version extraction
  - `_inject_core_guide()`: Marker-based content replacement
  - `post_install_update_guide()`: Main hook orchestration
- **Test coverage**: 87% (21 tests: 18 unit + 3 integration)
- **Documentation**: ADR 004 (`docs/architecture/adr/004-automatic-claude-md-update.md`)

- **`/codeindex-update-guide` skill** (Epic #25, Story #27): Interactive Claude Code skill for deep CLAUDE.md customization.
  - **Project analysis**: Detects languages (10 extensions), .codeindex.yaml, LoomGraph integration
  - **Personalized suggestions**: Profile-based recommendations (Swift docs, LoomGraph tips, version updates)
  - **Version diff**: Markdown-formatted comparison between old and new versions
  - **Language table diff**: Highlights newly supported languages
  - **Selective updates**: Apply all or choose specific suggestions
  - **Backup & rollback**: Timestamped backups with one-command restore
  - **Implementation**: `src/codeindex/skill_helpers.py` with 9 helper functions
  - **Test coverage**: 80% (25 unit tests)

## [0.22.1] - 2026-03-06

### Added

- **tech-debt JSON output enhancement**: Added `target_path` field to record analyzed directory path.
  - **Use case**: LoomGraph integration and logging/tracing
  - **Format**: Absolute path (e.g., `/Users/username/project/src`)
  - **Default**: "." if not provided (backward compatible)
  - **Cost**: Minimal (1 field addition, <5 minutes implementation)

### Changed

- **JSONFormatter**: Now accepts optional `target_path` parameter (v0.22.1+)
- **tech-debt command**: Automatically passes target path to JSON output

## [0.22.0] - 2026-03-06

### Added

- **Enhanced tech-debt command with test smells detection** (Issue #24): Unified code quality analysis.
  - **Test smells detection**: Automatic detection of skipped tests (`it.skip()`, `xit()`, `@pytest.mark.skip`, `@unittest.skip`, `@Ignore`, `@Disabled`) and giant test files (>1000 lines)
  - **Framework-agnostic**: Supports Jest, Mocha, pytest, unittest, JUnit 4/5 without framework-specific logic
  - **Enhanced JSON output**: Added `timestamp`, `summary` (with `test_smells` count, `avg_maintainability`), `giant_files`, `giant_functions`, `maintainability_scores`, and `test_smells` fields
  - **Backward compatible**: All existing JSON fields preserved for existing integrations
  - **LoomGraph ready**: JSON format optimized for LoomGraph technical debt analysis integration

- **debt-scan command alias**: `debt-scan` is now an alias for `tech-debt` (backward compatibility for v0.22.0 users)
  - `codeindex debt-scan ./src` ≡ `codeindex tech-debt ./src`
  - All options and output formats work identically

- **Test smells detection module** (test_smells.py): Framework-agnostic test code anti-pattern detection.
  - **Skipped tests detection**: Regex-based pattern matching across 8 patterns
  - **Giant test files**: Detects test files >1000 lines (reusing file size detection logic)
  - **Test file recognition**: Automatic identification via naming patterns (test_*.py, *.test.js, *Test.java) and directory conventions (__tests__/, tests/)

- **KISS implementation**: Simple, maintainable design following YAGNI principle.
  - **90% code reuse**: tech-debt detection, scanner, parser, symbol scorer
  - **Deferred features**: Cyclomatic complexity (use long method detection instead), comment rate analysis, Mock detection (low ROI)
  - **Unified command**: Single entry point reduces user confusion and maintenance burden

### Changed

- **tech-debt command**: Now includes test smells detection by default (all output formats)
- **JSONFormatter**: Enhanced with LoomGraph-compatible fields while maintaining backward compatibility

### Tests

- **test_test_smells.py**: 13 unit tests for test smells detection (100% passing)
- **test_cli_debt_scan.py**: 9 integration tests for debt-scan/tech-debt (100% passing)
- **Total**: 22 tests, all passing

### Documentation

- **Unified documentation**: tech-debt command now documented as comprehensive quality analysis tool
- **Backward compatibility**: debt-scan alias preserved for existing users

### Performance

- **Scan speed**: 97 test files analyzed in <1 second
- **Memory**: Minimal overhead (~5%) over previous tech-debt implementation

## [0.21.0] - 2026-03-06

### Added

- **Swift language support** (Epic 23 - Phase 1 & 2): Full parsing for `.swift` files using tree-sitter-swift v0.6.0.
  - **Symbol extraction**: classes, structs, enums, protocols, methods, properties, initializers, deinitializers, subscripts, top-level functions
  - **Import extraction**: import statements with module names
  - **Inheritance extraction**: class inheritance, protocol conformance, protocol inheritance
  - **Extension support**: extensions with protocol conformance, constrained extensions, cross-file extension tracking
  - **Docstring extraction**: Swift doc comments (`///` and `/** */`), preserves formatting
  - **Advanced features**: property wrappers (@State, @Published), generic type parameters, access modifiers
  - 23 comprehensive Swift tests (12 MVP + 11 advanced features)

- **Objective-C language support** (Epic 23 - Phase 3): Full parsing for `.h` and `.m` files using tree-sitter-objc v3.0.2.
  - **Symbol extraction**: @interface/@implementation declarations, methods (class/instance), properties, protocols, categories
  - **File association**: .h/.m file pairing by basename, symbol merging with deduplication, association accuracy ≥95%
  - **Protocol support**: @protocol declarations, protocol inheritance, @optional/@required method sections
  - **Category support**: NSString+ZCHelp pattern, category method extraction, base class association
  - **Preprocessing**: NS_ASSUME_NONNULL_BEGIN/END macro handling, NS_SWIFT_NAME removal, __attribute__ cleanup
  - 51 comprehensive Objective-C tests (13 basic + 18 association + 12 categories + 11 bridging)

- **Swift/Objective-C integration** (Epic 23 - Phase 3): Mixed project support for iOS/macOS development.
  - **Bridging header detection**: *-Bridging-Header.h pattern recognition, exposed Objective-C API extraction
  - **Mixed project parsing**: 814 files in real-world iOS project (280 Swift + 534 Objective-C)
  - **Association accuracy**: 91.5% .h/.m pairing in production codebase
  - 9 end-to-end integration tests

- **Tech-debt language support** (Epic 23): Objective-C and Swift file recognition in `codeindex tech-debt` command.
  - File extension mapping: `.h`, `.m` (objc), `.swift` (swift)
  - Language-specific noise thresholds: objc=70% (more lenient for categories), swift=60%, default=50%
  - Real-world validation: 28 files analyzed, 22 issues detected, 97.5/100 quality score

- **New optional dependency group**: `pip install ai-codeindex[swift]` installs tree-sitter-swift v0.6.0 and tree-sitter-objc v3.0.2
- **Scanner support**: `swift` and `objc` in `LANGUAGE_EXTENSIONS` and `.codeindex.yaml` config
- **CLI integration**: `codeindex parse file.swift` and `codeindex parse Header.h` produce JSON output

### Changed

- **Tech-debt noise ratio thresholds**: Adjusted for language-specific patterns (objc: 50%→70%, swift: 50%→60%). Objective-C categories and Swift extensions are intentionally simple utility code and should not be penalized.

### Fixed

- **Objective-C preprocessing**: Apple framework macros (NS_ASSUME_NONNULL_BEGIN/END, NS_SWIFT_NAME, __attribute__) now handled via preprocessing to ensure successful parsing. Previous 52% failure rate reduced to 0%.
- **POSIX newline requirement**: All test files now include trailing newline to satisfy tree-sitter-objc parser requirements.

### Validation

- **Real-world project**: slock-app (HEXFPORCE) - 814 files, 91.5% .h/.m association accuracy
- **Performance**: <1s for 28 files, <30s for full project indexing
- **Test coverage**: 1422 tests passing (74 new Swift/Objective-C tests), 13 skipped
- **Validation reports**: `docs/evaluation/epic23-slock-app-validation.md`, `docs/evaluation/epic23-tech-debt-validation.md`

## [0.20.0] - 2026-02-20

### Added

- **Enhanced tech-debt detection** (#20): Expanded from 2 to 5 detection dimensions with language-aware thresholds.
  - **Long method/function detection**: >80 lines (MEDIUM), >150 lines (HIGH)
  - **Too many top-level functions**: >15 functions per file (MEDIUM)
  - **High import coupling**: >8 internal/relative imports (MEDIUM)
  - **Language-aware file size thresholds**: Compact languages (Python/TS/JS: 800/1500/2500) vs verbose languages (PHP/Java/Go: 1500/2500/5000)
  - **3-tier file size detection**: medium_file/large_file/super_large_file
  - **2-tier God Class detection**: warning at >20 methods (MEDIUM), critical at >50 (CRITICAL)
  - 25 new tests, 55 total tech-debt tests

### Changed

- **SmartWriter refactored** into modular `writers/` package: `core.py`, `detailed_generator.py`, `navigation_generator.py`, `overview_generator.py`, `utils.py`. Original `smart_writer.py` reduced from 864 to thin re-export wrapper.
- **FileSizeClassifier thresholds lowered**: super_large 5000→2500, large 2000→1500, medium added at 800 lines.

## [0.19.0] - 2026-02-19

### Added

- **TypeScript/JavaScript language support** (Epic 20): Full parsing for `.ts`, `.tsx`, `.js`, `.jsx` files using tree-sitter-typescript and tree-sitter-javascript. Single `TypeScriptParser` class handles all 4 file types with 3 grammar variants (typescript, tsx, javascript).
  - **Symbol extraction**: classes, functions, methods, interfaces, enums, type aliases, const/let/var declarations, arrow functions, getter/setters, abstract classes, generics
  - **Import/export extraction**: ES module imports (named, default, namespace, side-effect), CommonJS `require()`, type-only imports, re-exports, barrel exports
  - **Inheritance extraction**: class extends, implements, interface extends (single and multiple)
  - **Call extraction**: function calls, method calls, static calls, constructor calls (`new`), chained calls
  - **TS-specific features**: decorators, React JSX/TSX components, namespaces, ambient declarations (.d.ts)
  - 77 new tests (68 unit + 9 integration), all passing
- **New optional dependency group**: `pip install ai-codeindex[typescript]` installs tree-sitter-typescript and tree-sitter-javascript
- **Scanner support**: `typescript` and `javascript` in `LANGUAGE_EXTENSIONS` and `.codeindex.yaml` config
- **CLI integration**: `codeindex parse file.ts` produces JSON output with full symbol/import/call data

## [0.18.0] - 2026-02-18

### Added

- **Enriched overview/navigation README_AI.md**: Overview and navigation level READMEs now show aggregated file/symbol counts from child modules instead of zeros. Module descriptions show structured info (e.g., "42 files | 313 symbols | classes: Config, Door...") instead of "Module directory". Overview level includes a Key Components table surfacing top class/function symbols across the project.
- **2-level directory tree in overview**: Module Structure tree now expands one level deeper, showing subdirectories of each top-level module (capped at 15 per module). Provides better architecture visibility for AI agents.
- **Real project validation framework**: `scripts/validate_real_projects.py` with 3-layer validation (L1 functional, L2 quality+AI, L3 experience). Includes baseline comparison, regression detection, and `make validate-*` targets.

## [0.17.3] - 2026-02-13

### Changed

- **CLAUDE.md template improved**: Added first-time setup instructions (review config → scan-all → optional hooks) to the injected CLAUDE.md section, so AI agents know to configure `.codeindex.yaml` before scanning.
- **Post-init message updated**: Now guides users to "Review .codeindex.yaml" as step 1, ensuring include/exclude patterns are verified before scanning.

## [0.17.2] - 2026-02-13

### Changed

- **docs/guides/ audit & cleanup**: Full alignment with v0.17.1. Updated 5 guide files (git-hooks-integration, contributing, configuration, configuration-changelog, docstring-extraction) fixing stale versions, wrong URLs, outdated architecture descriptions, and missing version entries.
- **docs/guides/ consolidation**: Removed 3 redundant files (docstring-extraction.md, configuration-changelog.md, migration-v0.6.md). Moved 3 internal files to docs/internal/. Guide count reduced from 14 to 8.
- **Makefile**: Added docs review reminder to pre-release-check.

## [0.17.1] - 2026-02-12

### Changed

- **README.md full restructure**: Reduced from 1255 to 295 lines (-76%). Now a concise navigation hub linking to existing `docs/guides/` content. Removed duplicate sections, updated for v0.17.0 features, fixed stale version claims.
- **CHANGELOG.md trimmed**: Reduced from 1080 to 319 lines (-70%). Removed internal implementation details from v0.6–v0.12, fixed all comparison links (`yourusername` → `dreamlx`), added missing version links (v0.7–v0.17).

## [0.17.0] - 2026-02-12

### Added

- **CLAUDE.md injection via `codeindex init`**: The init wizard now injects a codeindex instructions section into the project's `CLAUDE.md` file, so Claude Code automatically knows to use README_AI.md files on startup. Supports creating new files, prepending to existing files, and idempotent updates via HTML comment markers (`<!-- codeindex:start/end -->`).
- **Interactive wizard Step 5/6**: New "AI agent integration" step asks whether to inject into CLAUDE.md (default: yes). Steps renumbered from 5 to 6.
- **Non-interactive mode support**: `codeindex init --yes` injects into CLAUDE.md by default (safe — it's just markdown).
- **`inject_claude_md()` and `has_claude_md_injection()`**: Public API functions in `init_wizard` module for programmatic use.

## [0.16.1] - 2026-02-12

### Fixed

- **README.md false version claims**: Removed v0.16.0 labels from unimplemented framework route extractors (Laravel, FastAPI, Django, Express.js). These are planned features, not yet released.
- **Updated roadmap**: Fixed "Latest Improvements" section to reflect actual v0.16.0 changes instead of stale v0.14.0 content.

## [0.16.0] - 2026-02-12

### Changed (Breaking)

- **`scan` default mode reversed** (Story 19.1): `codeindex scan` now generates structural documentation by default (no AI required). Use `--ai` flag to enable AI-enhanced documentation. This makes the zero-config experience work out of the box.
- **`scan-all` default mode reversed** (Story 19.1): Same change as `scan` — structural mode is now the default.
- **`--fallback` deprecated**: Flag is now a hidden no-op that prints a deprecation warning. Will be removed in a future version.
- **`--dry-run` requires `--ai`**: Since dry-run previews the AI prompt, it now requires the `--ai` flag.

### Added

- **Pass-through directory skipping** (Story 19.5): Directories with no code files and single subdirectory are automatically skipped during scanning. Avoids redundant README_AI.md in deep structures (e.g., Java Maven `src/main/java/com/...`).
- **Parser installation detection** (Story 19.4): `codeindex init` now checks which tree-sitter parsers are installed and warns about missing ones with install commands.
- **Post-init guidance** (Story 19.2): Init wizard now suggests `scan-all` as immediate next step (works without AI). AI-enhanced docs mentioned as optional.
- **Post-commit hook auto-update**: `codeindex hooks install post-commit` now generates a fully functional hook that runs `codeindex scan` for affected directories and auto-commits updated README_AI.md files.
- **mo-hooks skill**: New Claude Code skill for customers to set up auto-update hooks.

### Improved

- **Java auto-recursive tech-debt** (Story 19.6a): `codeindex tech-debt` automatically enables `--recursive` for Java projects (deep package structures). Removes the old hint message.
- **Language-aware noise analysis** (Story 19.6b): `_analyze_noise_breakdown` now skips getter/setter counting for Java files (JavaBeans convention). Python/PHP noise analysis unchanged.

### Fixed

- **Post-commit hook not updating files**: Generated hook was missing `cd "$REPO_ROOT"`, used pipe subshells causing `git add` to run in wrong context, and `set -e` caused silent failures.

## [0.15.1] - 2026-02-12

### Fixed

- **`scan-all` missing Java files** (BUG-1): Refactored `find_all_directories` and `scan_directory` to use unified `get_language_extensions()` instead of hardcoded extension checks. Adding new languages now only requires updating the `LANGUAGE_EXTENSIONS` dict.
- **`tech-debt` 0 files for Java projects** (BUG-2): Added hint suggesting `--recursive` flag when no files found and Java is configured (deep package structures).
- **Java getter/setter false positives** (IMP-1): Skip naming pattern penalty for Java files where getters/setters are standard JavaBeans convention.

## [0.15.0] - 2026-02-12

### Changed

- **Test Architecture Migration** (Epic 18)
  - Migrated all inheritance tests to template-based generation system
  - Python: 30 tests generated from `test_generator/specs/python.yaml`
  - PHP: 23 tests generated from `test_generator/specs/php.yaml`
  - Java: 29 tests generated from `test_generator/specs/java.yaml`
  - 100% legacy test coverage preserved (63/63 scenarios)
  - 19 additional advanced test scenarios added
  - Single Jinja2 template shared across all languages

### Added

- **Test Generator Tooling** (`test_generator/`)
  - `generator.py`: CLI for YAML + Jinja2 → pytest test generation
  - `specs/`: YAML specifications for Python, PHP, Java inheritance tests
  - `templates/inheritance_test.py.j2`: Shared test template
  - `scripts/`: Analysis and comparison utilities

### Removed

- Legacy hand-written inheritance test files (preserved in `backup/legacy-tests-20260211` branch)

## [0.14.0] - 2026-02-10

### Added

- **Interactive Setup Wizard** (Epic 15 - Story 15.1)
  - Enhanced `codeindex init` with intelligent, step-by-step wizard
  - Smart auto-detection (languages, frameworks, project structure)
  - Non-interactive mode for CI/CD (`--yes`, `--quiet` flags)

- **Enhanced Help System** (Epic 15 - Story 15.3)
  - `codeindex config explain <parameter>`: Detailed parameter help
  - `codeindex init --help-config`: Full configuration reference

- **Single File Parse Command** (Epic 12 - Story 12.1)
  - New `codeindex parse <file>` command for parsing individual source files
  - JSON output with structured data (symbols, imports, namespace)
  - Exit codes: 0 (success), 1 (file error), 2 (unsupported language), 3 (parse error)

### Changed

- **Parser Modularization** (Epic 13)
  - Refactored monolithic `parser.py` (3622 lines) into modular `parsers/` package
  - `BaseLanguageParser`, `PythonParser`, `PhpParser`, `JavaParser`
  - Simplified `parser.py` to 374 lines (-89.7%)

### Fixed

- **Windows Cross-Platform Compatibility**
  - UTF-8 encoding fix for cross-platform README_AI.md files
  - Windows path length optimization (relative paths instead of absolute, 40-60% shorter)

## [0.12.0] - 2026-02-07

### Added

- **Call Relationships Extraction** (Epic 11)
  - **Python**: Function, method, constructor calls with import alias and super() resolution (35 tests)
  - **Java**: Method, static, constructor calls with package import resolution (26 tests)
  - **PHP**: Function, method, static calls with namespace resolution (25 tests)
  - **LoomGraph JSON integration**: Call serialization, round-trip support, backward compatible (12 tests)
  - Unified `Call` dataclass with `CallType` enum across all languages

- **Java Inheritance Extraction** (Epic 10 Part 3)
  - `extends`, `implements`, interface inheritance, generic type handling
  - Nested class support, fully qualified name resolution, `java.lang.*` implicit imports
  - 25 tests covering all scenarios

- **Multi-Language Development Workflow** documentation (600+ lines guide)

## [0.11.0] - 2026-02-06

### Added

- **Lazy Loading for Language Parsers**: Parsers only imported when needed, with caching and helpful error messages

### Changed

- **BREAKING**: Language parsers moved to optional dependencies
  - Install: `pip install ai-codeindex[python]`, `[php]`, `[java]`, or `[all]`

### Migration

- Existing users: `pip install --upgrade ai-codeindex[all]`

## [0.10.1] - 2026-02-06

### Fixed

- **JSON Output Clean Stream**: `--output json` now produces clean JSON without progress messages

## [0.10.0] - 2026-02-06

### Added

- **PHP LoomGraph Integration** (Epic 10 Part 2)
  - PHP inheritance extraction: `extends` (single), `implements` (multiple interfaces)
  - PHP import alias extraction: `use X as Y`, group imports `use A\{B as C, D}`
  - 32 new tests (777 total)

### Changed

- **PHP Use Statement Parsing** (Breaking): Import alias now in `Import.alias` field instead of `Import.names`. `names` field is always `[]` for PHP use statements.

## [0.9.0] - 2026-02-06

### Added

- **LoomGraph Integration Support** (Epic 10 - MVP)
  - `Inheritance` dataclass (child-parent), `Import.alias` field, `ParseResult.inheritances`
  - Python inheritance extraction (single, multiple, nested class relationships)
  - Python import alias extraction (`import X as Y`, `from X import Y as Z`)
  - 67 new tests, integration validation for LoomGraph compatibility

### Changed

- **BREAKING**: Import parsing now creates separate Import objects for each imported name (enables granular alias tracking)

## [0.8.0] - 2026-02-06

### Added

- **Complete Java Language Support** (Epic 7 Complete - 11 Stories, 184 new tests)
  - Advanced features: generic bounds, throws, lambdas, module system (Java 9+)
  - **Spring Framework route extraction**: `@GetMapping`/`@PostMapping`/etc., path composition, path variables
  - **Lombok support**: `@Data`, `@Builder`, `@Getter`/`@Setter`, constructors, logging
  - Robustness: edge cases, error recovery, nested classes, Unicode identifiers

## [0.7.0] - 2026-02-05

### Added

- **Java Language Support** (Epic 7 MVP)
  - Complete parser: classes, interfaces, enums, records, sealed classes, generics
  - **Annotation extraction**: Spring, JPA, Bean Validation with full argument parsing
  - **Spring Framework test suite**: Controllers, Services, Repositories, Entities, Configuration
  - **Parallel directory scanning**: ThreadPoolExecutor, configurable workers, 3-4x speedup
  - **JSON output mode**: `--output json` for machine-readable output
  - **Git hooks configuration**: 5 modes (auto/disabled/async/sync/prompt) in `.codeindex.yaml`

## [0.6.0] - 2026-02-04

### BREAKING CHANGES

**AI Enhancement feature completely removed** — based on real-world testing and KISS principle. SmartWriter output was being replaced (not enhanced) by AI, losing routes tables and method signatures.

Removed: `ai_enhancement` config, multi-turn dialogue, `--strategy`/`--ai-all` options, `ai_enhancement.py` module.

Kept: SmartWriter (core README generation), Docstring Extraction (Epic 9), `FileSizeClassifier`, all 415 tests passing.

**Migration**: Remove `ai_enhancement:` from `.codeindex.yaml`. Use `codeindex scan <dir>` for per-directory AI docs.

### Added

- **AI-Powered Docstring Extraction** (Epic 9): Multi-language normalization (PHP + Python), three modes (off/hybrid/all-ai), batch processing, cost estimation (~$0.15/250 dirs)

## [0.5.0] - 2026-02-03

### Added

- **Git Hooks Integration** (Epic 6, P3.1)
  - `codeindex hooks install/uninstall/status` CLI commands
  - Pre-commit: ruff lint + debug code detection
  - Post-commit: automatic README_AI.md updates with `codeindex affected`
  - Backup & safety: automatic backup/restore of existing hooks

### Documentation

- Configuration upgrade guide (`docs/guides/configuration-changelog.md`, 442 lines)
- CLAUDE.md refactoring (1929 → 496 lines, -74%)

## [0.4.0] - 2026-02-02

### Changed

- **KISS Universal Description Generator** (Story 4.4.5): Complete redesign with zero-assumption, language-agnostic module descriptions. Format: `{path}: {count} {pattern} ({symbol_list})`. Eliminated all hardcoded business domain mappings.

## [0.3.1] - 2026-01-28

### Changed

- **CLI Module Split** (Story 4.3): Refactored monolithic `cli.py` into 6 focused modules (`cli.py`, `cli_common.py`, `cli_scan.py`, `cli_config.py`, `cli_symbols.py`, `cli_tech_debt.py`). 1062 → 31 lines in cli.py (-97.1%).

## [0.3.0] - 2026-01-27

### Configuration Changes
⚠️ New optional sections: `ai_enhancement.strategy`, `tech_debt.*`, multi-turn thresholds. Migration not required — all optional with sensible defaults.

### Added

- **Code Refactoring** (Epic 4): AI Helper module, File Size Classifier, 20 new unit tests
- **Multi-turn Dialogue for Super Large Files** (Epic 3.2): Three-round dialogue for files >5000 lines or >100 symbols, intelligent strategy selection, 22 BDD tests
- **Technical Debt Analysis** (Epic 3.1): Complexity metrics, symbol overload detection, console/markdown/JSON reporting, `tech-debt` CLI command, 69 new tests
- **Adaptive Symbol Extraction** (Epic 2): Dynamic 5-150 symbols per file, 7-tier classification, YAML config, 69 new tests

## [0.1.3] - 2025-01-15

### Added
- `PROJECT_INDEX.json` and `PROJECT_INDEX.md` for codebase navigation

## [0.1.2] - 2025-01-14

### Added
- Parallel scanning support with `codeindex list-dirs`
- `--dry-run` flag for prompt preview
- Status command to check indexing coverage

### Fixed
- Unicode handling in prompts
- Path resolution on Windows

## [0.1.1] - 2025-01-13

### Added
- `--fallback` mode for generating docs without AI
- Configuration validation

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

[Unreleased]: https://github.com/dreamlx/codeindex/compare/v0.17.2...HEAD
[0.17.2]: https://github.com/dreamlx/codeindex/compare/v0.17.1...v0.17.2
[0.17.1]: https://github.com/dreamlx/codeindex/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/dreamlx/codeindex/compare/v0.16.1...v0.17.0
[0.16.1]: https://github.com/dreamlx/codeindex/compare/v0.16.0...v0.16.1
[0.16.0]: https://github.com/dreamlx/codeindex/compare/v0.15.1...v0.16.0
[0.15.1]: https://github.com/dreamlx/codeindex/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/dreamlx/codeindex/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/dreamlx/codeindex/compare/v0.12.0...v0.14.0
[0.12.0]: https://github.com/dreamlx/codeindex/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/dreamlx/codeindex/compare/v0.10.1...v0.11.0
[0.10.1]: https://github.com/dreamlx/codeindex/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/dreamlx/codeindex/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/dreamlx/codeindex/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/dreamlx/codeindex/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/dreamlx/codeindex/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/dreamlx/codeindex/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/dreamlx/codeindex/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dreamlx/codeindex/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/dreamlx/codeindex/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/dreamlx/codeindex/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dreamlx/codeindex/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/dreamlx/codeindex/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/dreamlx/codeindex/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dreamlx/codeindex/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dreamlx/codeindex/releases/tag/v0.1.0
