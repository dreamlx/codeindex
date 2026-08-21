# codeindex Strategic Roadmap

**Last Updated**: 2026-08-21
**Current Version**: v0.40.0
**Vision**: LoomGraph 的 parser engine —— 多语言 AST → structural slice → graph-export NDJSON
**Positioning**: the "see" layer([ADR-009](../architecture/adr/009-codeindex-loomgraph-parser-engine.md))。用户操作 LoomGraph,codeindex 是其解析后端;也可 standalone 用于 README_AI.md navigation index。

---

## 📍 Current Status (v0.33.1)

### ✅ Completed Capabilities

| Feature | Version | Status |
|---------|---------|--------|
| **Python Support** | v0.1.0 | ✅ Full support |
| **Adaptive Symbol Extraction** | v0.2.0 | ✅ 5-150 symbols/file |
| **Technical Debt Analysis** | v0.3.0 | ✅ Complexity metrics |
| **CLI Modularization** | v0.3.1 | ✅ 6 focused modules |
| **KISS Description Generator** | v0.4.0 | ✅ Universal patterns |
| **Git Hooks Integration** | v0.5.0 | ✅ Pre/Post-commit |
| **Framework Routes (ThinkPHP)** | v0.5.0 | ✅ Plugin architecture |
| **AI-Powered Docstring Extraction** | v0.6.0 | ✅ Universal doc processor |
| **Java Language Support** | v0.7.0-v0.8.0 | ✅ Parser + Spring Routes + Lombok |
| **LoomGraph Integration (Python/PHP)** | v0.9.0-v0.10.0 | ✅ Inheritance + Import Alias |
| **Lazy Loading Architecture** | v0.11.0 | ✅ Optional language parsers |
| **Call Relationships Extraction** | v0.12.0 | ✅ Python/Java/PHP calls |
| **Single File Parse + Parser Modularization + Windows** | v0.13.0 | ✅ 3622→374 lines, UTF-8 |
| **Interactive Setup Wizard + Help System** | v0.14.0 | ✅ Smart defaults + Auto-detection |
| **Test Architecture Migration** | v0.15.0 | ✅ YAML+Jinja2 template system |
| **CLI UX Restructuring** | v0.16.0 | ✅ Zero-AI default, --ai opt-in |
| **CLAUDE.md Injection** | v0.17.0 | ✅ AI agent auto-onboarding |
| **Enriched Overview/Navigation README** | v0.18.0 | ✅ Recursive stats, Key Components |
| **TypeScript/JavaScript Support** | v0.19.0 | ✅ Full TS/JS/TSX/JSX parsing |
| **Enhanced Tech-Debt Detection** | v0.20.0 | ✅ 5 dimensions, language-aware thresholds |
| **Swift/Objective-C Support** | v0.21.0 | ✅ iOS/macOS, .h/.m association |
| **Tech-Debt Test Smells + debt-scan alias** | v0.22.0 | ✅ Framework-agnostic test anti-patterns |
| **AI-Enhanced Module Descriptions (enricher)** | v0.23.0 | ✅ Structural + AI micro-enhancement, scan-all auto-AI |
| **claude-md update/status CLI** | v0.23.1 | ✅ CLAUDE.md section version tracking |
| **Hook portability + mypy + coverage gate** | v0.23.2 | ✅ bash shebang, CI type check, cov≥78 |
| **Navigation-contract disclaimer + idempotent scan-all --ai** | v0.24.0 | ✅ ADR-005, 10KB cap, warm cache re-runs |
| **Distribution Split: CLI wheel + Claude Code plugin** | v0.25.0 | ✅ ADR-006, `codeindex doctor` |
| **Dogfood CLI bug sweep (init/list-dirs/TS-detect/nav-flatten)** | v0.26.0 | ✅ fabricOS dogfood fixes |
| **Enrichment quality (leaf-dir punts, refusal cache, merge-commit hook)** | v0.26.1-v0.26.2 | ✅ A/B 23/50→0/50 punts |
| **`graph-export` command (ADR-007, schema v0)** | v0.27.0 | ✅ CALLS/INHERITS edges, resolution_qualifier |
| **graph-export `signature` field + init/scan UX + CLAUDE.md localization** | v0.28.0 | ✅ zh/en auto-detect, language-registry dedup |
| **graph-export IMPORTS edges** | v0.29.0 | ✅ Module→module import relationships |
| **`hooks rerun` escape hatch** | v0.30.0 | ✅ Force-rerun post-commit against HEAD |
| **graph-export per-symbol content_hash (schema v1)** | v0.31.0 | ✅ Symbol-level incremental staleness |
| **Java caller alignment + ADR-009 positioning** | v0.32.0 | ✅ #76 Java edges 0%→71% resolve; parser-engine 定位 |
| **graph-export REFERENCES edges + Python constructor/src-layout + IMPORTS resolution** | v0.33.0 | ✅ TS/JS import-ref+type-ref; orphan 55.8%→36.5% |
| **graph-export honors `include:` in .codeindex.yaml** | v0.33.1 | ✅ #137, no more whole-tree pollution |

### 📚 Version History (v0.22.0+)

| Version | Date | Highlights |
|---------|------|------------|
| **v0.33.1** | 2026-07-11 | 🔧 graph-export honors `include:` (#137) |
| **v0.33.0** | 2026-07-10 | 🔗 REFERENCES edges (TS/JS) + Python constructor/src-layout resolution (#127-133) |
| **v0.32.0** | 2026-07-06 | ☕ Java caller alignment (#76) + ADR-009 parser-engine positioning |
| **v0.31.0** | 2026-07-06 | 🧬 Per-symbol `content_hash` (schema v1, #124) |
| **v0.30.0** | 2026-07-04 | 🔁 `hooks rerun` post-commit escape hatch (#89) |
| **v0.29.0** | 2026-07-03 | 📥 graph-export IMPORTS edges (#117) |
| **v0.28.0** | 2026-07-03 | ✍️ graph-export `signature` field (#115) + init/scan UX + CLAUDE.md zh/en |
| **v0.27.0** | 2026-06-28 | 📤 `graph-export` command (ADR-007) + AI retry (#97) + partial-parse recovery (#95) |
| **v0.26.2** | 2026-06-22 | 🐛 Enrichment leaf-dir punts fixed (23/50→0/50) |
| **v0.26.1** | 2026-06-05 | 🐛 Hooks disabled warn + TS parser packages + refusal cache + merge-commit hook |
| **v0.26.0** | 2026-06-01 | 🐛 Dogfood CLI bug sweep (init/list-dirs/TS-detect/nav-flatten) |
| **v0.25.0** | 2026-05-26 | 📦 Distribution split: CLI wheel + Claude Code plugin (ADR-006) |
| **v0.24.0** | 2026-05-25 | 🧭 Navigation-contract disclaimer + 10KB cap (ADR-005) |
| **v0.23.2** | 2026-04-14 | 🔧 Hook portability (bash shebang) + mypy + coverage gate |
| **v0.23.1** | 2026-03-15 | 🔧 `claude-md update/status` CLI + startup version hint |
| **v0.23.0** | 2026-03-12 | 🤖 AI-Enhanced module descriptions (enricher) + post-commit thin wrapper |
| **v0.22.2** | 2026-03-08 | 🐛 Patch |
| **v0.22.1** | 2026-03-06 | 🐛 Patch |
| **v0.22.0** | 2026-03-06 | 🧪 Tech-debt test smells + `debt-scan` alias (#24) |

**v0.1.0–v0.21.0 历史**:见 [CHANGELOG.md](../../CHANGELOG.md)。

---

## 🎯 Strategic Direction

### 当前主线:graph-export NDJSON contract(v0.27.0+)

v0.27 起核心交付从「多语言 parser + README navigation」转向 **graph-export NDJSON
contract** —— codeindex 作为 LoomGraph parser engine 的唯一 seam。v0.27–v0.33
围绕这个 contract 密集迭代:

- **Edge kinds 逐步齐全**:`CALLS`/`INHERITS`(v0.27)→ `IMPORTS`(v0.29)→
  `REFERENCES`(v0.33,TS/JS import-ref + type-ref)
- **Resolution 精度提升**:Java caller 对齐(#76,0%→71%)、Python constructor→class
  (#132)、src-layout/relative imports(#133)、dotted-callee 判 unresolved(#127)
- **Schema演进**:v0(additive,ADR-007 gate)→ v1(per-symbol `content_hash`,#124)
- **正确性 guard**:language-mismatch warn(#93/#129/#131)、few-entity warn、
  `include:` honoring(#137)

### 已完成的战略支柱

1. **Multi-Language Parsing** ✅ — Python/PHP/Java/TS/JS/Swift/ObjC 七语言
2. **Navigation Index (README_AI.md)** ✅ — ADR-005 导航契约 + 10KB 边界
3. **Distribution Split** ✅ — CLI wheel + plugin(ADR-006)
4. **Graph-Export Contract** ✅(持续迭代)— ADR-007 stateless,ADR-009 parser-engine 定位

### 后续方向(baseline 驱动,非承诺)

以下由 **LoomGraph 下游 baseline** 驱动优先级,不预先排期:

- **REFERENCES edges 扩展到 Python/Java**:v0.33 v1 只覆盖 TS/JS;Python/Java 有相同
  type-declaration orphan gap,但 declaration density 低,follow-up
- **Schema v1 增量落地**:content_hash(#124)已 emit,等 loomgraph 真用上 symbol-level
  增量后再迭代([content-hash anchor idea](#) 备忘)
- **非 callable orphan**:TS `variable`(local const)仍 orphan,值引用难捕获且风险
  #127 over-broad pattern —— 待 baseline 证明值得再做
- **Go/Rust/C# 语言**:历史规划项,未实现;无真实下游需求前不启动

> **原则**(来自 dogfood 教训):不从自己 dogfood 的 edge-case 体验推 size gate /
> defensive friction;新语言/新 feature 由 acquired-user baseline 驱动,非自我推演。

---

## 📊 Language Support Status

| Language | Since | Parsing | Calls | Inheritance | Imports | REFERENCES |
|----------|-------|---------|-------|-------------|---------|------------|
| **Python** | v0.1.0 | ✅ | ✅ | ✅ | ✅ (#133 src-layout) | 📋 follow-up |
| **PHP** | v0.5.0 | ✅ | ✅ | ✅ | ✅ (#118 PSR-4) | 📋 follow-up |
| **Java** | v0.7.0 | ✅ | ✅ (#76) | ✅ | ✅ (#118 Maven) | 📋 follow-up |
| **TypeScript/JS** | v0.19.0 | ✅ | ✅ | ✅ | ✅ | ✅ (#128 v1) |
| **Swift** | v0.21.0 | ✅ | ✅ | ✅ | ⚠️ framework unresolved | 📋 follow-up |
| **Objective-C** | v0.21.0 | ✅ | ✅ | ✅ | ⚠️ framework unresolved | 📋 follow-up |

---

## 📈 Success Metrics

| Metric | v0.21.0 | v0.33.1 (current) | Notes |
|--------|---------|-------------------|-------|
| **Languages** | 6 | 7 (Python/PHP/Java/TS/JS/Swift/ObjC) | +ObjC |
| **graph-export edge kinds** | 0 | 3 (CALLS/INHERITS/IMPORTS/REFERENCES) | +REFERENCES v0.33 |
| **graph-export schema** | — | v1 (content_hash) | #124 |
| **Java edge resolve rate** | — | 71% (#76) | 0%→71% |
| **TS orphan rate (fabricOS)** | 55.8% | 36.5% (#128) | type-decl orphan solved |
| **Tests passing** | 1422 | 1754+ | |
| **Distribution** | monorepo | CLI wheel + plugin (ADR-006) | |

---

## 🔗 Related Documents

- **[CHANGELOG](../../CHANGELOG.md)** — 完整版本历史(every-release ledger)
- **[ADRs](../architecture/adr/)** — 架构决策(001-009)
- **[Executive Summary](executive-summary.md)** — 「navigation index,非权威文档」定位论证
- **[2026-05 README Impact Benchmark](../benchmark/2026-05-readme-impact.md)** — ADR-005 实证
- **GitHub Issues**:https://github.com/dreamlx/codeindex/issues

---

**Roadmap Status**: 🎯 Active
**Maintained By**: @dreamlx
**Last Updated**: 2026-08-21
**Current Version**: v0.40.0
