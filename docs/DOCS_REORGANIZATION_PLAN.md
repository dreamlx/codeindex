# Docs Reorganization Plan (v0.6.0 Post-Release)

**Created**: 2026-02-04
**Author**: @dreamlx
**Status**: 📋 Proposed

---

## 🎯 Goals

1. **Clarity**: Separate active plans from historical archives
2. **Findability**: Consistent organization by epic/version
3. **Maintainability**: Clear structure for future docs
4. **Usability**: Users can quickly find what they need

---

## 📂 Proposed New Structure

```
docs/
├── README.md                        # Overview + navigation
│
├── guides/                          # User-facing guides (KEEP AS IS ✅)
│   ├── getting-started.md
│   ├── configuration.md
│   ├── advanced-usage.md
│   ├── docstring-extraction.md
│   ├── git-hooks-integration.md
│   ├── migration-v0.6.md
│   └── ...
│
├── planning/                        # Active + archived planning
│   ├── README.md                    # 📌 Index of all epics/stories
│   ├── ROADMAP.md                   # 🎯 Strategic roadmap (single source of truth)
│   │
│   ├── active/                      # 🔥 Current work
│   │   ├── epic7-java-support.md    # Next planned epic
│   │   └── epic8-multi-language.md  # Future epic (TBD)
│   │
│   └── completed/                   # ✅ Historical record
│       ├── epic2-adaptive-symbols/
│       │   ├── plan.md              # Original planning
│       │   └── validation-report.md # Post-completion report
│       ├── epic3-ai-enhancement/
│       │   ├── plan.md
│       │   ├── optimization.md
│       │   └── removal-notes.md     # Why it was removed in v0.6.0
│       ├── epic4-refactoring/
│       │   ├── plan.md
│       │   ├── story-4.3-cli-split.md
│       │   └── story-4.4.5-kiss.md
│       ├── epic6-framework-routes/
│       │   ├── p3.1-git-hooks.md
│       │   └── thinkphp-extractor.md
│       ├── epic9-docstring-extraction/
│       │   ├── plan.md
│       │   └── validation-report.md
│       │
│       ├── v0.1.0-v0.3.1/           # Early phase planning (archived)
│       │   ├── phase1-agile-plan.md
│       │   ├── phase1-story-cards.md
│       │   ├── improvement-proposals.md
│       │   └── ...
│       │
│       └── sprints/                 # Sprint logs (archived)
│           └── sprint-1/
│               ├── DAILY_LOG.md
│               └── week1-review.md
│
├── evaluation/                      # Validation & case studies
│   ├── README.md                    # Evaluation framework
│   ├── framework.md                 # Testing methodology
│   │
│   ├── case-studies/
│   │   ├── php-payment-project.md   # Real-world PHP project
│   │   └── python-api-service.md    # (Future)
│   │
│   └── before-after/                # Feature impact analysis
│       ├── adaptive-symbols.md      # Epic 2
│       ├── docstring-extraction.md  # Epic 9
│       └── git-hooks.md             # Epic 6
│
├── architecture/                    # Design decisions (KEEP AS IS ✅)
│   ├── adr/                         # Architecture Decision Records
│   │   ├── 001-tree-sitter.md
│   │   ├── 002-external-ai-cli.md
│   │   └── 003-docstring-ai-processor.md  # 📌 ADD for Epic 9
│   │
│   └── design/
│       ├── initial-design.md
│       ├── kiss-universal-description.md
│       ├── parallel-strategy.md
│       └── document-aggregation.md
│
└── development/                     # Developer workflow (KEEP AS IS ✅)
    ├── setup.md
    ├── gitflow-workflow.md
    ├── requirements-workflow.md
    └── improvements/                # 📌 Consider moving to planning/completed/
        ├── README.md
        ├── QUICK_START.md
        └── ...
```

---

## 🔄 Migration Steps

### Phase 1: Create New Structure (15 min)

```bash
# Create new directories
mkdir -p docs/planning/active
mkdir -p docs/planning/completed/{epic2-adaptive-symbols,epic3-ai-enhancement,epic4-refactoring,epic6-framework-routes,epic9-docstring-extraction}
mkdir -p docs/planning/completed/v0.1.0-v0.3.1
mkdir -p docs/planning/completed/sprints
mkdir -p docs/evaluation/before-after
```

### Phase 2: Move Active Planning (5 min)

```bash
# Move active epics
mv docs/planning/epic7-java-support.md \
   docs/planning/active/epic7-java-support.md

# Keep ROADMAP.md at top level
# Keep README.md at top level
```

### Phase 3: Archive Completed Epics (20 min)

```bash
# Epic 2: Adaptive Symbols
mv docs/planning/epic2-adaptive-symbols-plan.md \
   docs/planning/completed/epic2-adaptive-symbols/plan.md
mv docs/epic2-validation-report.md \
   docs/planning/completed/epic2-adaptive-symbols/validation-report.md

# Epic 3: AI Enhancement (removed in v0.6.0)
mv docs/planning/epic3-ai-enhancement-optimization.md \
   docs/planning/completed/epic3-ai-enhancement/optimization.md
mv docs/planning/epic3-refactoring-analysis.md \
   docs/planning/completed/epic3-ai-enhancement/refactoring-analysis.md
# Create removal notes
cat > docs/planning/completed/epic3-ai-enhancement/removal-notes.md << 'EOF'
# Epic 3 Removal Notes

**Version**: v0.6.0
**Date**: 2026-02-04

## Why AI Enhancement Was Removed

1. **Information Loss Problem**: Replaced SmartWriter output instead of enhancing it
2. **KISS Principle**: Complexity outweighed benefits
3. **Better Alternative**: Docstring Extraction (Epic 9) solves core problem

See: docs/guides/migration-v0.6.md for migration details
EOF

# Epic 4: Refactoring + KISS
mv docs/planning/epic4-refactoring-plan.md \
   docs/planning/completed/epic4-refactoring/plan.md
mv docs/planning/story-4.3-cli-module-split.md \
   docs/planning/completed/epic4-refactoring/story-4.3-cli-split.md
mv docs/planning/story-4.4.5-kiss-description.md \
   docs/planning/completed/epic4-refactoring/story-4.4.5-kiss.md

# Epic 6: Framework Routes + Git Hooks
mv docs/planning/epic6-framework-routes.md \
   docs/planning/completed/epic6-framework-routes/plan.md
mv docs/planning/git-hooks-ux-design.md \
   docs/planning/completed/epic6-framework-routes/git-hooks-ux.md

# Epic 9: Docstring Extraction
mv docs/planning/epic9-docstring-extraction.md \
   docs/planning/completed/epic9-docstring-extraction/plan.md
# Validation report TBD after PHP project testing

# Early phase documents
mv docs/planning/phase1-*.md docs/planning/completed/v0.1.0-v0.3.1/
mv docs/planning/improvement-*.md docs/planning/completed/v0.1.0-v0.3.1/

# Sprint logs
mv docs/sprints/* docs/planning/completed/sprints/
rmdir docs/sprints
```

### Phase 4: Reorganize Evaluation (10 min)

```bash
# Move validation reports to consistent location
mv docs/evaluation/story-4.4-validation-report.md \
   docs/planning/completed/epic4-refactoring/story-4.4-validation.md
mv docs/evaluation/story-4.4.5-kiss-validation.md \
   docs/planning/completed/epic4-refactoring/story-4.4.5-kiss-validation.md

# Create before-after comparison docs
mv docs/evaluation/before-after.md \
   docs/evaluation/before-after/README.md
```

### Phase 5: Update Index Files (10 min)

Create `docs/planning/README.md`:

```markdown
# Planning Index

## 🔥 Active Epics

| Epic | Version | Priority | Status |
|------|---------|----------|--------|
| [Epic 7: Java Support](active/epic7-java-support.md) | v0.7.0 | P0 | 📋 Planned |
| [Epic 8: Multi-Language](active/epic8-multi-language.md) | v0.8.0 | P0 | 📋 TBD |

## ✅ Completed Epics

| Epic | Version | Completion Date |
|------|---------|-----------------|
| [Epic 2: Adaptive Symbols](completed/epic2-adaptive-symbols/plan.md) | v0.2.0 | 2025-01-15 |
| [Epic 3: AI Enhancement](completed/epic3-ai-enhancement/optimization.md) | v0.3.0 (removed v0.6.0) | 2026-01-27 |
| [Epic 4: Refactoring + KISS](completed/epic4-refactoring/plan.md) | v0.3.1-v0.4.0 | 2026-02-02 |
| [Epic 6: Framework Routes](completed/epic6-framework-routes/plan.md) | v0.5.0 | 2026-02-03 |
| [Epic 9: Docstring Extraction](completed/epic9-docstring-extraction/plan.md) | v0.6.0 | 2026-02-04 |

## 📚 Key Documents

- [Strategic Roadmap](ROADMAP.md) - Long-term vision and priorities
- [Development History](completed/v0.1.0-v0.3.1/improvement-proposals.md) - Early phase decisions
```

Update `docs/evaluation/README.md`:

```markdown
# Evaluation & Validation

## Framework

See [framework.md](framework.md) for our evaluation methodology.

## Case Studies

Real-world projects tested with codeindex:

- [PHP Payment Project](case-studies/php-payment-project.md) - 251 dirs, ThinkPHP framework
- Python API Service (TBD)

## Before/After Analysis

Feature impact measurements:

- [Adaptive Symbols](before-after/adaptive-symbols.md) - Epic 2: Coverage 26% → 100%
- [Docstring Extraction](before-after/docstring-extraction.md) - Epic 9: Quality ⭐⭐ → ⭐⭐⭐⭐⭐
- [Git Hooks](before-after/git-hooks.md) - Epic 6: Dev workflow improvement
```

### Phase 6: Clean Up Root (5 min)

```bash
# Remove obsolete files
rm -f docs/planning/day5-documentation-summary.md  # Replaced by README
rm -f docs/planning/day6-git-hooks-completion.md   # Superseded by git-hooks-integration.md
rm -f docs/planning/v0.4.0-execution-plan.md       # Completed, use ROADMAP.md
rm -f docs/planning/sprint1-*.md                   # Moved to sprints/

# Keep these for now (may delete later):
# - development-roadmap-2026-q1-q2.md (duplicate of ROADMAP.md?)
# - executive-summary.md (useful summary)
# - IMPLEMENTATION_GUIDE.md (if still relevant)
```

---

## 📝 Post-Migration Tasks

### 1. Update ROADMAP.md

```bash
# Fix current version
sed -i '' 's/Current Version.*: v0.5.0/Current Version: v0.6.0/' docs/planning/ROADMAP.md

# Update v0.6.0 section (completed)
# Update Epic status table
# Add v0.7.0 section (Java Support)
```

### 2. Update Epic 9 Status

```bash
# Update status in completed/epic9-docstring-extraction/plan.md
sed -i '' 's/Status.*: 📋 Planning/Status: ✅ Completed (v0.6.0)/' \
  docs/planning/completed/epic9-docstring-extraction/plan.md
```

### 3. Create ADR for Epic 9

Create `docs/architecture/adr/003-ai-powered-docstring-processor.md`:

```markdown
# ADR 003: AI-Powered Docstring Processor

**Status**: Accepted
**Date**: 2026-02-04
**Decision Makers**: @dreamlx

## Context

Need to extract documentation from multiple languages (PHP, Java, TypeScript, Go) with varied formats:
- Structured (PHPDoc, JavaDoc, JSDoc)
- Unstructured (inline comments)
- Mixed language (Chinese + English)

Traditional approach: Language-specific parsers (phpDocumentor, JavaDoc parser)
- High complexity
- Maintenance burden
- Can't handle irregular formats

## Decision

Use **AI-powered universal docstring processor** instead of language-specific parsers.

Architecture:
- `DocstringProcessor` class with two modes: hybrid, all-ai
- Batch processing: 1 AI call per file (not per symbol)
- Cost optimization: Hybrid mode <$1 per 250 directories
- Language-agnostic: Same processor for PHP, Java, TypeScript, etc.

## Consequences

**Positive**:
- ✅ Zero language-specific code (10 min to add Java support)
- ✅ Handles all formats naturally (structured, unstructured, mixed language)
- ✅ Cost-effective (<$1 per 250 dirs in hybrid mode)
- ✅ Graceful fallback to raw docstrings

**Negative**:
- ⚠️ Requires external AI CLI (claude, openai)
- ⚠️ Network latency (mitigated by batch processing)
- ⚠️ API costs (mitigated by hybrid mode)

## Alternatives Considered

1. **Language-specific parsers** - Rejected due to complexity
2. **Regex extraction** - Rejected due to unreliability
3. **Tree-sitter docstring nodes** - Rejected due to limited coverage

## References

- Epic 9: docs/planning/completed/epic9-docstring-extraction/plan.md
- Implementation: src/codeindex/docstring_processor.py
- User Guide: docs/guides/docstring-extraction.md
```

### 4. Update docs/README.md

Add reorganization notes and new navigation structure.

---

## ✅ Benefits of New Structure

1. **Clear Separation**
   - Active work in `planning/active/`
   - Historical records in `planning/completed/`
   - Users don't see outdated documents

2. **Consistent Organization**
   - Each epic has own directory with plan + validation
   - Easy to find related documents

3. **Better Navigation**
   - Index files in each section
   - Clear hierarchy

4. **Maintainability**
   - New epics follow same pattern
   - Easy to archive when completed

5. **Discoverability**
   - Users can browse completed epics chronologically
   - Case studies grouped together

---

## 🤔 Open Questions

1. **development/improvements/** - Move to planning/completed/ or keep?
   - Recommendation: Move to `planning/completed/v0.1.0-v0.3.1/improvements/`

2. **Multiple roadmap files** - Keep both `ROADMAP.md` and `development-roadmap-2026-q1-q2.md`?
   - Recommendation: Merge into single `ROADMAP.md`, archive old one

3. **executive-summary.md** - Still relevant?
   - Recommendation: Keep if it provides unique value, otherwise archive

4. **PLANNING_COMPLETE.md** - What is this?
   - Recommendation: Review content, likely obsolete

---

## 📅 Timeline

- **Phase 1-3**: 40 minutes (create structure, move files)
- **Phase 4-5**: 20 minutes (update indexes)
- **Phase 6**: 10 minutes (cleanup)
- **Post-migration tasks**: 30 minutes (update ROADMAP, ADR, README)

**Total**: ~1.5 hours

---

## 🚀 Execution

Ready to execute? Run:

```bash
# Option 1: Manual execution (recommended first time)
# Follow phases 1-6 above step by step

# Option 2: Automated script (after reviewing plan)
# bash scripts/reorganize-docs.sh
```

---

**Status**: 📋 Awaiting approval
**Next Step**: Review with @dreamlx, then execute
