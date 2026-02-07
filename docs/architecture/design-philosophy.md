# Design Philosophy & Principles

**For**: Contributors and maintainers of codeindex
**Purpose**: Understanding the core design decisions and architectural principles

---

## Core Design Philosophy

**"ParseResult is a programmable data structure, not just text for AI"**

codeindex's core value proposition:
1. **Extract structured, programmable code information** (our role)
2. **Support multiple automated analyses** (route extraction, symbol scoring, dependency analysis)
3. **Provide AI enhancement** (AI understands semantics, writes documentation)

**Key principle**: We extract structure (What), AI understands semantics (Why)

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Structure Extraction (tree-sitter)        │
│  - Parse source code to AST                         │
│  - Extract symbols, signatures, annotations         │
│  - Build ParseResult (programmable data structure)  │
│  - Languages: Python, PHP, Java (future: Go, Rust) │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│  Layer 2: Automated Analysis (programmatic)         │
│  - Route extraction (Spring/ThinkPHP/Laravel)       │
│  - Symbol scoring (importance ranking)              │
│  - Dependency analysis (import graphs)              │
│  - Technical debt detection                         │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│  Layer 3: AI Enhancement (semantic understanding)   │
│  - Understand business intent                       │
│  - Summarize architecture and design patterns       │
│  - Write README documentation                       │
│  - Extract and normalize docstrings                 │
└─────────────────────────────────────────────────────┘
```

---

## ParseResult Multi-Purpose Design

**Data Structure**:
```python
@dataclass
class ParseResult:
    symbols: list[Symbol]      # Classes, functions, methods
    imports: list[Import]      # Import statements
    namespace: str             # Package name/namespace
    annotations: list          # Decorators/annotations (Java/Python)
```

**Usage 1: Format for AI** → Generate README_AI.md
**Usage 2: Route extraction** → Programmatically traverse symbols/annotations (Story 7.2)
**Usage 3: Symbol scoring** → Rank importance based on annotations (Story 7.4)
**Usage 4: Fallback mode** → Generate README without AI
**Usage 5: Global symbol index** → PROJECT_SYMBOLS.md
**Usage 6: Dependency analysis** → Analyze import relationships

**Critical insight**: ParseResult is not just for AI consumption—it's a programmable data structure for automated analysis.

---

## Performance Architecture

### The Real Bottleneck: AI Invocation (not tree-sitter)

**Time breakdown**:
```
Directory scan:       0.05s (10 files)
tree-sitter parsing:  0.1s  (10 files, ThreadPool)
Format prompt:        0.01s
AI invocation:        10s   ← 99% of time!
Write file:           0.01s

Total: ~10s
```

**Key insights**:
1. ✅ **tree-sitter is fast** - even large Java files parse in milliseconds
2. ✅ **AI invocation is slow** - I/O bound, waiting for network/process response
3. ✅ **ThreadPool is sufficient** - I/O operations not limited by Python GIL
4. ❌ **ProcessPool NOT needed** - AI invocation is I/O bound, not CPU bound

---

## Parallelization Strategy

**Current implementation**: `src/codeindex/parallel.py`

```python
def parse_files_parallel(files, config):
    """Use ThreadPoolExecutor for parallel parsing"""
    with ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
        # Parse files in parallel (tree-sitter fast, no bottleneck)
        results = list(executor.map(parse_file, files))
```

**Why ThreadPool instead of ProcessPool?**
1. ✅ tree-sitter parsing is fast (milliseconds), not a bottleneck
2. ✅ AI invocation is I/O bound (not limited by GIL)
3. ✅ ThreadPool starts quickly, lower memory overhead
4. ❌ ProcessPool for CPU-bound tasks, not applicable here

**Real optimization target**: Parallelize scanning multiple directories (scan-all)
```
Current: Sequential processing of 50 directories × 10s = 500s
Optimized: Parallel processing with 8 workers = 62.5s (8x faster)
```

---

## Adding New Language Support

### ⚠️ CRITICAL: Common Misconceptions

**❌ WRONG**: "Different languages need different parallelization strategies"
- Java files are large → need ProcessPool
- Python files are small → use ThreadPool

**✅ CORRECT**: All languages use the same strategy
- AI Command handles all languages uniformly
- tree-sitter is fast for all languages
- Bottleneck is AI invocation (I/O bound)
- ThreadPool works for all languages

**Do NOT do this**:
```yaml
# ❌ WRONG design
parallel_strategy:
  python: threads
  java: processes    # Incorrect!
  go: threads
```

**Correct approach**:
```yaml
# ✅ CORRECT design
parallel_workers: 8  # Unified config for all languages
```

---

### Checklist for Adding New Language (e.g., Go)

**Step 1: tree-sitter integration** (Required)
```python
# src/codeindex/parser.py
import tree_sitter_go as tsgo

GO_LANGUAGE = Language(tsgo.language())
PARSERS["go"] = Parser(GO_LANGUAGE)
FILE_EXTENSIONS[".go"] = "go"
```

**Step 2: Symbol extraction** (Required)
Priority:
- P0 (Must have): Classes, functions/methods, signatures, basic docstrings
- P1 (Important): Annotations/decorators, import statements, namespaces
- P2 (Optional): Generics, exceptions, lambdas, advanced features

**Reason**: P0 info sufficient for README, P1 needed for route extraction and symbol scoring

**Step 3: DO NOT add language-specific parallelization** ❌
- All languages use the same ThreadPool
- No need to distinguish by language
- AI Command handles all languages

**Step 4: Framework-specific features** (Optional)
If framework route extraction needed (e.g., Gin for Go):
- Create extractor plugin: `src/codeindex/extractors/gin_extractor.py`
- Depend on ParseResult.symbols annotations
- Follow ThinkPHP extractor plugin pattern

---

## Common Design Pitfalls

### Pitfall 1: Over-reliance on AI ❌

**Wrong idea**: "Let AI do everything, we just pass source code"

**Problems**:
- ❌ Cannot support route extraction (needs programmatic traversal)
- ❌ Cannot support symbol scoring (needs structured data)
- ❌ Cannot support fallback mode
- ❌ Increases AI costs

**Correct approach**: We extract structure, AI understands semantics

---

### Pitfall 2: Misidentifying bottlenecks ❌

**Wrong idea**: "Java file parsing is slow, need ProcessPool optimization"

**Reality**:
- ✅ tree-sitter is very fast (even large files are milliseconds)
- ✅ Real bottleneck is AI invocation (seconds, I/O bound)
- ✅ ThreadPool is already sufficient

**Correct optimization**: Parallelize multiple directory scanning, not single file parsing

---

### Pitfall 3: Language-specific parallelization ❌

**Wrong idea**: "Java files large, need ProcessPool; Python files small, use ThreadPool"

**Reality**:
- ✅ AI Command handles all languages uniformly
- ✅ Bottleneck is AI invocation (not parsing)
- ✅ I/O bound tasks best served by ThreadPool

**Correct approach**: Unified ThreadPool with reasonable worker count

---

## Key Takeaways for Future Development

1. **ParseResult is multi-purpose** - Not just for AI, also for programs
2. **We extract structure, AI understands semantics** - Clear division of labor
3. **Bottleneck is AI invocation, not tree-sitter** - Don't over-optimize parsing
4. **ThreadPool works for all languages** - No need for language-specific strategies
5. **Annotation extraction is necessary** - Supports route extraction and symbol scoring

---

## Related Resources

- **Architecture decisions**: Search for "ADR-" in documentation
- **Epic planning docs**: `docs/planning/epic*.md`
- **Serena memory**: `design_philosophy` (older version, this doc is canonical)

---

**Last Updated**: 2026-02-07
**Version**: v0.12.1
