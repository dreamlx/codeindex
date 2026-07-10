# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **graph-export REFERENCES edges: symbol-level import-ref + type-ref**
  (GH #128, v1 — TS/JS only). A new `REFERENCES` edge kind connects exported
  symbols referenced only via `import { X }` or `: X` type annotations —
  non-callable declarations (`const` / `interface` / `type_alias`) that were
  previously zero-edge and got falsely flagged `orphan` by downstream topology.
  Two passes: (a) **import-ref** — each named/default import whose target
  module resolves and whose name matches an exported entity emits
  importer-module → `{target}.{name}`; (b) **type-ref** — each `type_identifier`
  in type position (param/return annotations, generic args, `as` assertions),
  resolved via the global last-segment index (same-module exact preferred),
  emits using-module → type entity. Declaration-name nodes are skipped (no
  spurious self-refs). Both dedup to one edge per (src-module, dst-entity).
  Impact on fabricOS (TS): orphan 55.8% → 36.5%; `interface` orphan 95.7% →
  5.4%, `type_alias` 100% → 3.7% — the type-declaration orphan problem is
  effectively solved. Remaining orphans are `variable` (local consts, out of
  v1 scope — value-ref is hard and risks the #127 over-broad-candidate
  pattern) and JSX component functions. v1 is TS/JS only; Python/Java have the
  same gap but lower declaration density (follow-up).
- **graph-export IMPORTS edges: Java/PHP/Swift/ObjC `source_id` line +
  Java/PHP resolution** (GH #118, follow-up to #117). `Import.line` is now
  filled for Java/PHP/Swift/ObjC — previously default `0`, so the IMPORTS
  edge `source_id` read `file:0` for these languages (Python/TS were already
  filled under #117). Java intra-project imports now resolve via Maven
  src-layout stripping (`com.foo.Bar` ↔ `src/main/java/com/foo/Bar.java`);
  PHP `use` resolves via `\` → `.` (PSR-4, `App\Service` ↔ `App/Service.php`).
  The Maven match is layout-specific, **not** a general suffix match — Python
  `import os` still correctly stays unresolved. Swift/ObjC framework imports
  remain mostly unresolved (acceptable; `dst_raw` preserves the framework name).

### Fixed

- **graph-export dotted-callee false-ambiguous edges** (GH #127). A dotted
  callee whose receiver is a runtime variable (`obj.run`, `db.exec`,
  `res.json`) was wrongly classified `ambiguous` and dumped every same-name
  entity into `candidates` via the step-3 last-segment fallback — almost
  always a mis-match, since the receiver's type is statically unknowable
  (dynamic dispatch). On fabricOS this was 502 of 544 `ambiguous` edges
  (92%); downstream loomgraph materialised ~20 ghost `→ server/test` edges
  (defended client-side at LoomGraph#101). These dotted callees now resolve
  as `unresolved`, consistent with `provenance_completeness` ("dynamic
  dispatch NOT captured"). Bare callees (`run()`) are unchanged — genuine
  same-name collisions still resolve `ambiguous`. Also removes the now-dead
  step-3 fallback (provably unreachable: step-2 full-suffix already decides
  every bare name, since `last_index` keys ARE the entity last-segment).
- **`codeindex --version` went stale after a pyproject bump in editable
  installs**: `__version__` read `dist-info` metadata via
  `importlib.metadata`, which editable installs bake at install time, so
  `--version` reported the install-time version (e.g. 0.30.0) instead of the
  current source (0.32.0) until reinstall. This once masked a shipped fix
  when a spike read the stale `--version` and concluded the Java call-graph
  fix hadn't landed. Resolve from the source-tree `pyproject.toml` when
  reachable; fall back to metadata for wheel/pipx installs. Adds a
  default-path depth regression test.

## [0.32.0] - 2026-07-06

### Fixed

- **Java call-chain dangling edges** (GH #76, cross-repo root cause with
  LoomGraph): Java parser's `calls.py` built `caller` from `full_class_name`
  (package-qualified) while `symbols.py` built `sym.name` from simple class
  name, so `graph-export`'s `edge.src` (`module + caller`) never matched
  `entity.id` (`module + sym.name`) — every Java edge source dangled.
  LoomGraph downstream saw `graph=0 callees`, 81% orphan, `coupling=0.0`.
  Fixed: `caller = f"{class_name}.{method}"` (simple, aligned with sym.name);
  drop `full_class_name`. Verified on spring-petclinic: `edge.src==entity.id`
  0%→71%; loomgraph orphan 81%→49%, coupling 0.0→0.621, graph(OwnerController)
  0→4 callees. Python unaffected (parser kept caller/sym.name same form).
- **graph-export silent 0 entities** (GH #93): a Java repo under the default
  `languages=[python]` silently yielded 0 entities with `success:true`.
  `graph-export` now warns on stderr when 0 entities result, reusing the
  single-source `language_mismatch_hint` from list-dirs/scan-all. stdout NDJSON
  contract stays clean for `loomgraph index` (`-o -`).

### Changed

- **Product positioning clarified** (ADR-009): codeindex is the parser engine
  for [LoomGraph](https://github.com/dreamlx/LoomGraph) — the "see" layer.
  Users install LoomGraph (`pipx install loomgraph`), which pulls `ai-codeindex`
  as a dependency. Two repos, one product from the user's view. Methodology
  role (agent-native middleware "see" instance) decoupled from product form.

## [0.31.0] - 2026-07-06

### Added

- **graph-export per-symbol `content_hash`** (schema v1, GH #124, #110 gate
  satisfied): each entity record carries a `sha256` over a normalized
  symbol-span slice (trailing-ws / line-ending / BOM normalized; content not
  line numbers → stable under line shift). Lets loomgraph skip re-embedding
  unchanged symbols (symbol-level incremental, vs prior file-level warm-diff).
  `null` for no-span entities. Additive over v0 — old loomgraph reader warns
  on `schema_version: 1` but still imports (content_hash ignored, backward
  compatible).
- **Direct HTTP API as default AI backend** (ADR-008, partially reverses
  ADR-002): new `ai:` config section — DeepSeek `deepseek-chat` default,
  OpenAI-compatible `/chat/completions` via httpx. `ai_command` (CLI)
  retained as escape hatch. Precedence: `ai_command` > `ai.api_key` > error.
  API key via env `CODEINDEX_AI_API_KEY` (provider-agnostic, preferred),
  `DEEPSEEK_API_KEY` (backcompat), or yaml `ai.api_key`.
  Reuses GH-97 transient retry (`_retry_transient` shared by CLI + API paths;
  HTTP 429/5xx/timeout/connection match existing `_TRANSIENT_ERROR_PATTERNS`,
  401/402/403 fail fast). Trigger: Anthropic mass account bans made the
  prior `claude` CLI default unreliable.
- **`invoke_ai(config, ...)` dispatch** + `resolve_ai_backend` +
  `invoke_ai_api` (invoker.py). All AI call sites routed through it
  (cli_scan single-dir + Phase-2 enrich, semantic_extractor,
  docstring_processor). docstring_processor also gains GH-97 retry (was
  inline `subprocess.run` with no retry).
- **`codeindex init --dry-run`** (GH #88): previews init's 3 mutation targets
  (`.codeindex.yaml` create, `CLAUDE.md` codeindex-section inject, `.gitignore`
  README_AI.md append) without writing. Uses the same detection as the real
  init (`_collect_init_targets`), so it can't drift from init's actual
  behavior — replaces the `codeindex:index` SKILL Step 0 hardcoded bash, and
  gives bare-CLI users (pipx, no plugin) a preview too. Existing targets show
  as "Already in place"; `--dry-run` bypasses the exists/force gate.

### Changed

- Config: `AIConfig` dataclass (`provider/base_url/model/api_key/timeout/
  max_tokens` + `resolved_api_key` env-first property); `Config.ai` field;
  `DEFAULT_CONFIG_TEMPLATE` rewritten — `ai:` section main path, `ai_command`
  commented as escape hatch (uncommented claude line removed).
- `init --yes` seeds the `ai:` section instead of
  `ai_command=RECOMMENDED_AI_COMMAND`; post-init message points at
  `CODEINDEX_AI_API_KEY`.
- **Provider UX** (multi-provider, not DeepSeek-locked): env name is now
  `CODEINDEX_AI_API_KEY` (provider-agnostic; `DEEPSEEK_API_KEY` kept as
  backcompat from the initial ADR-008 release) — was hardcoded to DeepSeek,
  which made "switch provider" confusing. `PROVIDER_PRESETS`
  (deepseek/openai/ollama/llama-server) auto-fill `base_url`/`model` when
  `provider` is set; explicit fields override. `DEFAULT_CONFIG_TEMPLATE`
  shows multi-provider examples (OpenAI / Ollama / self-host llama-server /
  vllm / LMStudio) so users see how to point codeindex at their own backend.

### Removed

- Dead `hooks/` directory (templates + README): described an obsolete
  AI-CLI async post-commit flow that no longer exists. Actual hook = thin
  wrapper generated by `cli_hooks.py` → `codeindex hooks run post-commit`
  → `run_post_commit_hook` (structural rescan of affected dirs). Live hook
  assets: `scripts/hooks/hook-common.sh` (pre-commit/pre-push) +
  `src/codeindex/cli_hooks.py` (generation) + `docs/guides/git-hooks-integration.md`.

## [0.30.0] - 2026-07-04

**Theme**: `codeindex hooks rerun` — the user-facing post-commit escape
hatch (GH #89). The hidden `hooks run` (#34) is the shell hook script's
internal contract; `rerun` is its visible counterpart: force-rerun the
post-commit hook against HEAD when it didn't fire (doc-only commit skipped
by the shell wrapper's loop guard, retroactive populate after flipping
`hooks.post_commit.enabled: false → true`, or a historical stale README
predating the #84 merge-commit fix). Calls the Python logic directly,
bypassing the shell wrapper. Plus a CLAUDE.md injection-template section
documenting the escape hatch — the hooks section previously had none, so
agents suggested `git commit --allow-empty` workarounds.

### Added

- **`codeindex hooks rerun <hook>`** (GH #89): visible user command that
  force-reruns a hook against HEAD, bypassing the shell wrapper's doc-only
  loop guard. Sibling to the hidden `hooks run` (#34, shell contract) —
  `run` = internal/hidden, `rerun` = user/visible. No `--force` / `--ref`
  flags: rerun IS the force path (backfill beyond HEAD uses `scan-all`).
  Background — the post-commit hook can miss a commit (doc-only loop-guard
  skip; `enabled: false` at the time; stale README predating #84). #84
  (merge-commit `-m` fix) and #87 (`enabled: false` install warn) are
  already shipped, so `rerun` is a backfill / escape-hatch, not a bug
  workaround. Note: `hooks.post_commit.enabled` is checked only at install
  (reminder warn, #87); runtime doesn't gate on it, so `rerun` "bypasses"
  it by construction.
- **CLAUDE.md template: "When the post-commit hook didn't fire" section**
  (en + zh, GH #89): documents `codeindex hooks rerun post-commit` as the
  escape hatch. Per the AI-facing-refs escape-hatch rule — the hooks
  section previously had no escape hatch, so agents suggested
  `git commit --allow-empty -m "trigger hook"` (destructive workaround).

### Changed

- **CLAUDE.md core template: trimmed two redundancies** (en + zh): merged
  "Code Navigation Priority" rules 2+3 (two sides of one rule — "README
  sufficient" vs "drill into source") into one; stopped repeating the
  navigation-contract comment text in the markers list (already shown in
  the "What README_AI.md is" section). Surfaced via grump meta-lens review.
  No behavior change.

## [0.29.0] - 2026-07-03

**Theme**: `graph-export` emits `IMPORTS` edges (GH #117) — the third edge kind,
after `CALLS`/`INHERITS`. Module→module import relationships were entirely
absent from the export contract, so `loomgraph deps` (module dependency graph)
returned empty and the IMPORTS filter in `loomgraph graph` had no data.
loomgraph-side `VALID_EDGE_KINDS` already included `IMPORTS` (LoomGraph#77),
waiting on this emit. Schema stays at `0` (no bump — additive new edge kind,
same 0-version gate rationale as #115 in v0.28.0).

### Added

- **`graph-export` emits `IMPORTS` edges** (GH #117): a new edge kind for
  module→module import relationships, projected from the already-parsed
  `ParseResult.imports`. `src` = the importer module id (no entity backing —
  module-level, same shape as a `<module>`-level `CALLS` `src`; the consumer
  materialises the container); `dst` = the imported module id if a scanned
  file maps to it, else `null` with `dst_raw` carrying the original import
  string. Resolution is **module-level**, not entity-level — `from
  app.validators import validate` → `dst` is `app.validators` (the module),
  not `validate` (the symbol). Relative imports (`./api`, `../lib` — TS/JS)
  resolve against the importer's directory. `Import.line` added to the parser
  dataclass so `source_id` is the import statement's `relpath:line`; filled
  for Python/TS, `0` (file-level) for PHP/Java/Swift/ObjC pending a parser
  follow-up. **Schema stays at `0`** (no bump): a new edge kind is additive —
  old consumers ignore unknown `kind` values; `1` is reserved for shape
  freeze (ADR-007 gate). Drives `loomgraph deps` and `loomgraph graph --kind
  IMPORTS` (downstream already gated on it, LoomGraph#77). No breaking
  changes; no migration.

## [0.28.0] - 2026-07-03

**Theme**: graph-export `signature` + a sweep of init/scan UX bugs. The headline
is an additive `signature` field on `graph-export` entity records (GH #115) —
closes an embedding-coverage hole measured by the loomgraph EPIC-015 spike
(docstring-less symbols had an empty `description` → no vector → invisible to
semantic search). Schema stays at `0` (no bump — additive, per ADR-007's
0-version gate). Plus six bug fixes across language detection, non-TTY `init`,
CLAUDE.md localization, and silent-empty scans. No breaking changes; no
migration. loomgraph is the sole graph-export consumer and is coordinated via
the issue (read-if-present, not a version-floor reject).

### Added

- **`graph-export` entity records now carry a `signature` field** (GH #115): projected from the already-extracted `Symbol.signature`. Closes an embedding-coverage hole measured by the loomgraph EPIC-015 spike — docstring-less symbols had an empty `description` → no embedding vector → invisible to downstream semantic search (~4% of entities on codeindex itself, ~15% on `src/loomgraph`). A signature is present for ~100% of symbols, so a consumer can build `description = signature + docstring` and reach full coverage. codeindex stays a dumb emitter: it emits `signature` and `description` as **separate** fields and does **not** collapse them — the combine is the consumer's call (ADR-007 seam). **Schema stays at `0`** (no bump): additive field addition during the 0-version window is exactly what ADR-007's gate permits ("fields/format may change without deprecation while at version 0"), and a known follow-up (`#110` content-hash for incremental staleness) would otherwise force an immediate 0→1→2. Consumers should read `signature` if present and warn if absent, not hard-reject on a version floor.

### Fixed

- **Internal `hooks run` no longer clutters `hooks --help`** (GH #34): `codeindex hooks run <name>` is invoked by the generated shell hook scripts, not by users, but it was advertised alongside `install`/`status`/`uninstall` — reading like a user-facing command. Marked the subcommand `hidden=True`; invocation is unchanged (the shell scripts still call it).
- **Language detection no longer surfaces unparseable `go` / `rust`** (GH #112): `skill_helpers.detect_project_languages` used its own inline ext→language table that had drifted to include `.go` / `.rs` — languages codeindex has no parser for. Detecting them could seed `.codeindex.yaml` with a language that then scans/parses to nothing (a detect-but-unparseable silent-empty, same class as #80). The table is now derived from a single new source, `scanner.EXTENSION_TO_LANGUAGE` (the inverse of `LANGUAGE_EXTENSIONS`), so detection stays in lockstep with the scannable set and cannot drift again. (Production `init` detection — `init_wizard.detect_languages` — was already scanner-derived and unaffected; this was the redundant second table.) The full "single language registry" consolidation was **deferred** — with the #80 drift-guards now covering scanner ≡ parser and scanner ⊆ packages, the remaining maps are ergonomics, not a correctness gap.
- **Swift / Objective-C files are no longer silently skipped** (GH #80): `scanner.LANGUAGE_EXTENSIONS` (the map the scanner uses to decide which files to walk into) had drifted behind `parser.FILE_EXTENSIONS` — full `swift/` and `objc/` parser modules existed and `parse` dispatched `.swift` / `.h` / `.m`, but the scanner only knew 5 languages. A user with `languages: [swift]` (or `[objc]`) in `.codeindex.yaml` got an empty extension set → every matching file skipped → empty scan with no diagnostic (the same silent-cliff class as #74/#105). Added swift (`[.swift]`) and objc (`[.h, .m]`, matching the parser exactly — not `.mm`, which the parser does not dispatch), plus the corresponding `init_wizard.PARSER_PACKAGES` entries the existing drift-guard test requires. A new test pins `LANGUAGE_EXTENSIONS ≡ FILE_EXTENSIONS` so the two maps cannot drift again.
- **`codeindex init` in a non-TTY gives an actionable error instead of cryptic `Aborted!`** (GH #44): running `init` (no flags) in CI / sandbox / container / piped input fell through to the wizard's `click.confirm`/`prompt`, which raise a bare `Abort` — the user saw only `Aborted!` with no hint. `init` now guards interactive mode on `sys.stdin.isatty()` and, when stdin is not a TTY, raises a `click.ClickException` that names the fix (`Re-run with --yes …`). `--yes` / `-y` is unaffected.
- **Injected CLAUDE.md section now matches the host language (zh / en)** (GH #77, final piece): the `## codeindex` section was English-only, breaking style mid-file in a Chinese CLAUDE.md and signalling "the tool didn't understand my project" (the hardcoded language list and `opencode`/`gemini` boilerplate were already removed in v0.26.0). `claude_md.inject` now auto-detects the host CLAUDE.md language via a CJK-ratio heuristic (`detect_locale`, which strips the codeindex section first so `claude-md update` stays idempotent and matches the *host*, not our own prose) and renders a localized template; a fresh file with no host content defaults to English. `codeindex init --lang {auto,zh,en}` and `codeindex claude-md update --lang …` provide an explicit override (`auto` is the default). Ships a Chinese template (`templates/claude_md_core_zh.md`) alongside the English one.
- **`scan-all` no longer silently indexes nothing on a language mismatch** (GH #105): the `languages` footgun — e.g. `languages: [python]` on a TypeScript repo — made `scan-all` walk to "0/0 directories" and exit cleanly, indistinguishable from "nothing to do" (an agent then debugs for minutes; a human gives up). The actionable diagnostic that `list-dirs` already emitted (GH #74 — names the configured languages, the extensions actually present, and which language to add) is now a single shared helper `scanner.language_mismatch_hint`, and `scan-all` surfaces it too. The empty-signal was also corrected from `total_directories == 0` to `with_files == 0`: a directory whose files don't match `languages` still counts as a directory but yields nothing to process, so the old guard missed exactly this case.
- **`languages` default no longer contradicts itself** (GH #105): the runtime fallback (`DEFAULT_LANGUAGES`) is `[python]`, but the unused `DEFAULT_CONFIG_TEMPLATE` / `Config.create_default()` seed carried `languages: [php]` (a legacy artifact — `create_default` is dead code; `codeindex init` writes auto-detected languages instead). Aligned the template to `python` and clarified the comment so anyone copy-pasting or rendering it gets a value consistent with the actual fallback.

## [0.27.0] - 2026-06-28

**Theme**: graph-export + parser robustness. Ships the new `codeindex
graph-export` command — codeindex's write-once data contract with loomgraph
(ADR-007, gated GREEN/YELLOW by the LoomGraph#30 consumption spike) — plus
the in-run AI retry (#97) and the cross-language partial-parse recovery (#95)
that were sitting unreleased on master. graph-export is **additive**: it is a
standalone command, the new `GraphBuffer` IR (#101) it reuses is dormant
(unwired into `scan-all`), and existing `scan-all` / `parse` / `symbols`
output is unchanged. No migration needed.

### Added

- **`codeindex graph-export` — write-once graph artifact for loomgraph** (GH #102, ADR-007, **experimental schema_version 0**): a standalone command that does its own clean whole-tree parse and dumps NDJSON of code entities (`class`/`function`/`method`, module-qualified id + `source_id` + first-line description + `provenance`) and `CALLS`/`INHERITS` edges. It is **decoupled from `scan-all`/README render** — the LoomGraph#30 consumption spike (verdict 🟡 YELLOW) justified the export but not the #101 render-flip, and the two are architecturally independent (export needs the buffer *populated*, not the render path *flipped*). The parser emits *file-local* names, so the export performs the only cross-file resolution pass: every edge carries a **`resolution_qualifier`** (`resolved` / `ambiguous` / `unresolved`, with `candidates` on ambiguous) so a consumer never reads an unresolved edge as real, plus **`dst_raw`** (the original best-effort name) so a consumer can still synthesise an external stub or filter framework noise when `dst` is null, and the meta header carries **`provenance_completeness`** flagging that AST extraction misses dynamic dispatch / reflection (the spike's E-class finding — an absent edge means "not statically resolvable", not "none"). Schema is experimental and Python-validated; a TS spot-check precedes any stable-contract promise. Reuses the #101 `GraphBuffer` purely as the parsed-data container; ships no persistent/mutable state (ADR-007).
- **`scan-all --ai` retries transient AI failures in-run** (GH #97): a serial enrichment pass that hit a one-off haiku timeout / rate-limit / 5xx previously lost that directory until a manual re-run (observed 12/50 transient failures in the GH #94 A/B). `invoke_ai_cli` now takes `max_attempts` (scan paths use 3) and retries with exponential backoff, but **only** on recognised-transient signals (`_is_transient`: timeout, rate-limit, 429, 502/503/529, overload, connection reset, …). Permanent failures — a misconfigured `ai_command` (`command not found`, exit 127) or any unlabeled non-zero exit — **fail fast** (single attempt) so they are not hammered N× across every directory. Not a backend/direct-API change: the agent-CLI invocation stays the only transport. Default `max_attempts=1` preserves single-shot behavior for every other caller.

### Fixed

- **TypeScript parser no longer zeroes out a whole file on one unsupported construct** (GH #95): the bundled `tree-sitter-typescript` grammar (0.23.2 — the latest published, so this is *not* a stale pin but upstream grammar lag) does not parse some modern-TS constructs, e.g. `export type *` (TS 5.0) and generic-typed tagged templates like Prisma `$queryRaw<{...}[]>`...``. The parser bailed the moment `tree.root_node.has_error` was true, returning `symbols: []` — so a single unparseable line dropped the file's entire class/method set from `PROJECT_SYMBOLS.md` and its directory `README_AI.md` (hit 2/608 `.ts` files on a real monorepo, silently). tree-sitter error recovery is *local*, so the surrounding symbols are still in the tree. `TypeScriptParser.parse` now extracts symbols regardless of `has_error`, returns whatever is recoverable flagged with a new `ParseResult.partial=True`, and only surfaces the hard `error="Syntax error in source file"` when nothing at all could be recovered. Consumers that branch on `result.error` (enrichment, tech-debt, error counts) are unaffected — a partial file has `error=None` so its recovered symbols flow through. Verified: `LockController.ts` with a `$queryRaw<T>` line went from `symbols: []` to recovering its class + all 4 members.
- **Same partial-parse recovery applied to all remaining parsers** (GH #95 fast-follow): the identical `has_error` early-bail existed in `base` (used by Swift), `python`, `java`, `php`, and `objc`. All now extract regardless of `has_error`, return recoverable symbols flagged `partial=True`, and only emit the hard error when nothing is recoverable — so a single malformed construct no longer zeroes a whole file in any supported language. Cross-language regression test (`tests/test_parser_partial_recovery.py`) covers python/java/php/swift/objc; two Java tests that asserted the old all-or-nothing contract were updated to the graceful-degradation contract.

## [0.26.2] - 2026-06-22

**Theme**: enrichment-quality patch. `scan-all --ai` was silently writing punt
text ("I need the file names") as the directory description for leaf dirs and
caching it as `enrichment: ok`. A/B on a real TS monorepo: 23/50 punts → 0/50.
No contract change.

> **Upgrade note**: existing `README_AI.md` files enriched by ≤0.26.1 may carry
> poisoned descriptions stamped `enrichment: ok`, which the cache will not
> refresh on its own. After upgrading, run **`codeindex scan-all --ai --retry-all`**
> once to flush and regenerate them.

### Fixed

- **`scan-all --ai` enrichment now feeds each directory its OWN files/symbols, fixing leaf-dir punts** (GH #94): `_enrich_directories_with_ai` built the prompt from `build_safe_subdir_context(child_dirs)` — child *directory* names only — while `build_enrich_prompt` instructed the model "based ONLY on the file names and symbol names above." A leaf dir's content is *files*, not subdirs, so the prompt carried nothing to describe; worse, a single uninformative child like `__tests__` made the subdir context non-empty and short-circuited the README fallback. On a TypeScript monorepo this hit 21/50 enriched dirs (`controllers`, `services`, `routes`, `screens`, `pages` — all the leaf code dirs), and the model correctly punted ("I need the file names and symbol names"). New `cli_scan._build_enrich_summary` re-parses the directory's own files **non-recursively** (`scan_directory(recursive=False)` — no subtree leak) and runs them through the existing `extract_symbol_summary`, then `enricher.merge_enrich_context` combines that (primary) with the subdir names (supplementary). Both sources are AST/tree-derived, never README markdown, so the anti-injection-chain property `build_safe_subdir_context` was built for is preserved. `build_enrich_prompt`'s instruction was de-lied ("based ONLY on the information above (file names, symbol names, and subdirectories)") and a dir with genuinely no indexable content is now marked `failed (reason: no indexable content)` — retryable — instead of being sent a self-contradictory prompt. *(The original issue blamed `parallel_workers=16` concurrency; that was a confounded experiment — enrichment is a serial loop and the punts occurred serially. Diagnosis corrected by source read + clean repro before this fix.)*
- **Punt detection (`looks_like_refusal`) now covers the leaf-dir phrasings it was missing** (GH #94, extends GH #85): the GH #85 refusal table had `i need more` but not `i need specific`, and **zero Chinese prefixes** — so `I need specific file names…` / `我需要…文件名和符号名` / `请提供…` slipped through and were stamped `<!-- enrichment: ok -->`, poisoning the cache (skipped on re-run without `--retry-all`). Added `i need specific` plus a deliberately specific Chinese set (`我需要`, `请提供`, `需要具体`, `信息不足`, `我看到的信息`) — kept narrow so legit one-liners that merely contain `需要` (e.g. "需要登录的接口") are not misclassified, locked by `test_chinese_descriptions_with_xuyao_are_not_refusals`.

## [0.26.1] - 2026-06-05

**Theme**: GitFlow + non-Python UX patch. Four bug fixes from continued fabricOS dogfood — all paths where `codeindex` silently no-op'd or warned about state that wasn't real. No contract changes.

### Fixed

- **`codeindex hooks install post-commit` now warns when `.codeindex.yaml` disables the hook** (GH #87): `codeindex init` ships the yaml with `hooks.post_commit.enabled: false` by default, so the installed `.git/hooks/post-commit` wrapper would check the flag at runtime and silently no-op. The install command printed ✓, the user committed code, and `README_AI.md` never updated — classic "installed but not working" trap. New `_maybe_warn_post_commit_disabled` helper reads the yaml after install; when `post_commit.enabled` is false (or absent), prints an actionable reminder with the exact yaml snippet to flip. No behavior change to the install itself — patch-safe. (The doubly-opt-in default itself is a separate contract question deliberately deferred from this patch; the reminder is enough to unblock the first-time path.)
- **`codeindex init` no longer false-flags installed TS/JS parsers as missing + install hint matches the documented pipx path** (GH #86): `init_wizard.PARSER_PACKAGES` enumerated only python/php/java even though scanner gained TS/JS parsers (#73) and the parser modules exist under `src/codeindex/parsers/{typescript,javascript}/`. Result on a TS-only project: `init --yes` printed `Warning: Missing parsers for: javascript, typescript` despite `pipx inject ai-codeindex tree-sitter-{typescript,javascript}` confirming the packages were already installed. Worse, the hint said `Install with: pip install ai-codeindex[...]` — contradicts the entire documented install path (`pipx install ai-codeindex` everywhere else in CLAUDE.md, README, hooks/index SKILL) and doesn't even work cleanly for a pipx-managed env. Fix: extend `PARSER_PACKAGES` to include typescript/javascript; change the install hint to `pipx inject ai-codeindex tree-sitter-<lang> [tree-sitter-<lang2>...]` (matches the rest of the doc surface). New structural test `test_parser_package_map_covers_scanner_supported_set` locks the invariant — adding a language to scanner.py without exposing it via `PARSER_PACKAGES` will fail the test, preventing the GH #86 drift class from recurring (same pattern as the #73 structural guard).
- **`scan-all --ai` no longer caches AI refusal text as `enrichment: ok`** (GH #85): when the configured AI backend declined to answer for a directory (e.g. haiku returning "I don't see any file names or symbol names provided…"), Phase 2 wrote the refusal verbatim into the directory's `README_AI.md` blockquote AND stamped `<!-- enrichment: ok -->`. Subsequent `scan-all --ai` runs saw the `ok` marker, skipped re-enrichment, and the garbage description stuck in the cache forever. New `enricher.looks_like_refusal(text)` helper detects common refusal prefixes (case-insensitive: `I don't`, `I cannot`, `I'm unable`, `no file`, `insufficient context`, `as an AI`, etc.); when matched, the directory is marked `failed (reason: ai-refused)` so the next run retries automatically (idempotent re-enrichment policy already in place). Refusal-pattern detection happens on the cleaned/truncated AI output (~80 chars) — refusal phrasing always lives in the first ~30 chars so truncation doesn't blind the check.
- **Post-commit hook now fires on merge commits** (GH #84): the shell wrapper's loop guard used `git diff-tree --no-commit-id --name-only -r HEAD`, which returns **empty on merge commits** by default — `-m` is required to enumerate per-parent changes. Empty → `NON_DOC_FILES` empty → wrapper exits 0 without delegating to `codeindex hooks run post-commit`. Net effect on GitFlow projects: `README_AI.md` files never auto-updated on PR merges (the commits that actually bring new code to `main` / `develop`). Reported live on fabricOS HEAD `171702b` (Merge PR #7). Fix: add `-m` to the diff-tree command. Verified against a real merge commit in this repo (`e240ba0` — Merge develop for 0.26.0 release): old logic saw 0 files, new logic sees the 20 files actually changed. New regression test in `tests/test_cli_hooks.py::TestHookGeneration::test_post_commit_loop_guard_handles_merge_commits` locks both directions (rejects the broken pattern, requires either `-m` or `git show --name-only`).

## [0.26.0] - 2026-06-01

**Theme**: dogfood-driven CLI bug sweep. Five user-reported issues from fabricOS dogfood — mostly UX cliffs in `init` and `list-dirs` on non-Python projects, plus a navigation-correctness bug in nav-level `README_AI.md`. One contract change in `init --yes` so first `scan-all --ai` works out of the box.

### Changed

- **`codeindex init --yes` now seeds the recommended `ai_command`** (GH #75): the generated `.codeindex.yaml` includes `ai_command: 'claude -p "{prompt}" --model haiku --allowedTools "Read"'` so the first `codeindex scan-all --ai` works without "AI not configured" — the path the `codeindex:index` skill recommends by default. The documented default in `DEFAULT_CONFIG_TEMPLATE` and the actually-written value now share a single source of truth (`config.RECOMMENDED_AI_COMMAND`). Contract change vs pre-0.26: AI used to be opt-in at both layers (yaml absent AND `--ai` flag required); now opt-in lives only at the CLI flag — `--ai` is still required to spend tokens, but the yaml no longer blocks first-try success. The pre-existing regression test `test_generated_config_no_ai_command` was renamed to `test_generated_config_seeds_recommended_ai_command` and inverted to lock the new contract.

### Fixed

- **`codeindex init` CLAUDE.md injection drops hardcoded `.py / .php / .java` examples and alternate-backend boilerplate** (GH #77, partial): the injected `## codeindex` section used to instruct users to "read the actual `.py` / `.php` / `.java` / etc." — wrong on TS / Swift / Go projects — and listed `opencode run` / `gemini -p` as ai_command alternatives in every project's CLAUDE.md regardless of which backend the user actually chose. Template now uses language-neutral wording ("read the source files") and links the backend-swap recipe to `codeindex --help` instead of inlining all options. Two regression tests (`test_build_section_does_not_hardcode_language_extensions`, `test_build_section_does_not_advertise_alternative_backends`) lock these absences. **Deferred to a follow-up**: zh/en locale detection (#77 also asked for the injection to match the host CLAUDE.md's language; that's a distinct design question — heuristic vs `--lang` flag vs dual templates — and out of this PR's scope).
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
