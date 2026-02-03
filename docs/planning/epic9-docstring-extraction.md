# Epic 9: AI-Powered Docstring Extraction

**Version**: v0.6.0
**Target Date**: 2026-02-15 (2 weeks)
**Status**: 📋 Planning
**Priority**: 🔥 P0 (High Priority - User has real PHP project)

---

## 📋 Epic Overview

### Vision

Enable codeindex to extract and normalize documentation comments from any programming language using AI-powered understanding, without complex language-specific parsers.

### Strategic Context

**Why This Epic Now?**

1. 🔥 **Real User Need**: User has 251-directory PHP project requiring immediate value
2. 🎯 **Fast Validation**: 1-2 weeks to prove AI-powered architecture
3. 🏗️ **Foundation for Multi-Language**: Reusable AI processor for Java, TypeScript, Go, Rust
4. 💡 **KISS Principle**: No complex parsers - AI handles all formats naturally

**Priority Change**: Originally planned Java support (v0.6.0), but moved to v0.7.0. PHP docstring extraction moved up because:
- User has real project to validate on
- Faster iteration cycle (2 weeks vs 6 weeks for Java)
- Proves AI architecture before investing in Java parser
- Same AI processor will work for Java (zero extra effort)

### Goals

#### Primary Goals (Must Have)

1. **Universal Docstring Understanding** - AI extracts documentation from any format:
   - PHPDoc (`/** @param */`)
   - Inline comments (`// description`)
   - Mixed language (Chinese + English)
   - Irregular formats

2. **Cost-Effective Processing** - Hybrid mode achieves:
   - <$1 per 250-directory scan
   - 80%+ extraction coverage
   - Quality: ⭐⭐ → ⭐⭐⭐⭐⭐ (README_AI.md descriptions)

3. **PHP Project Validation** - Test on real user project:
   - 251 directories
   - 1926 symbols
   - ThinkPHP framework

#### Secondary Goals (Nice to Have)

4. **Configuration & CLI** - User control:
   - `--docstring-mode hybrid|all-ai|off`
   - Cost tracking and reporting

5. **Foundation for Java** - Architecture proven:
   - Reusable `DocstringProcessor` class
   - 10 minutes to add Java support (just tree-sitter integration)

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Extraction Coverage** | 80%+ of PHP methods | Count methods with docstrings in README_AI.md |
| **Cost (Hybrid Mode)** | <$1 per 250-dir scan | Track API costs during user validation |
| **Quality Improvement** | ⭐⭐ → ⭐⭐⭐⭐⭐ | User subjective rating on README_AI.md descriptions |
| **Processing Time** | <10 min for 250 dirs | Measure total scan-all runtime |
| **Reusability** | <10 min to add Java | Time to implement JavaDoc after PHP done |

---

## 🎯 User Stories

### Story 9.1: Docstring Processor Core (P0) 🔥

**Priority**: P0 (Critical Path)
**Effort**: 2 days
**Dependencies**: None

**As a** developer
**I want** an AI-powered docstring processor
**So that** codeindex can extract and normalize documentation from any language

**Acceptance Criteria**:

1. ✅ `DocstringProcessor` class exists in `src/codeindex/docstring_processor.py`
2. ✅ Supports two modes:
   - `hybrid`: Simple extraction (first line) + selective AI for complex cases
   - `all-ai`: AI processes all comments (highest quality)
3. ✅ Batch processing: 1 AI call per file (not per comment)
4. ✅ Prompt template generates structured JSON output:
   ```json
   {
     "symbols": [
       {
         "name": "getUserList",
         "description": "Retrieves paginated user list with optional filtering",
         "quality": "high"
       }
     ]
   }
   ```
5. ✅ Fallback to simple extraction if AI fails
6. ✅ Cost tracking: Log tokens used per file
7. ✅ Test coverage ≥ 90%

**Technical Design**:

```python
class DocstringProcessor:
    """AI-powered docstring extraction and normalization."""

    def __init__(self, ai_command: str, mode: str = "hybrid"):
        """Initialize processor with AI CLI and mode."""

    def process_file(self, file_path: Path, symbols: list[Symbol]) -> dict:
        """
        Process all docstrings in a file.

        Args:
            file_path: Path to source file
            symbols: List of symbols with raw docstrings

        Returns:
            Dict mapping symbol name to normalized description
        """

    def _should_use_ai(self, docstring: str) -> bool:
        """Decide if AI is needed (hybrid mode logic)."""

    def _generate_prompt(self, file_content: str, symbols: list) -> str:
        """Generate AI prompt for batch processing."""

    def _call_ai(self, prompt: str) -> dict:
        """Call AI CLI and parse JSON response."""

    def _fallback_extract(self, docstring: str) -> str:
        """Simple fallback: first line, max 60 chars."""
```

**Tests**:
- `test_hybrid_mode_simple_extraction` - No AI for clean docstrings
- `test_hybrid_mode_ai_for_complex` - AI for irregular comments
- `test_all_ai_mode` - AI processes everything
- `test_batch_processing` - Single AI call per file
- `test_fallback_on_ai_failure` - Graceful degradation
- `test_cost_tracking` - Token counting
- `test_json_parsing` - Handle malformed AI responses

---

### Story 9.2: PHP Parser Integration (P0) 🔥

**Priority**: P0 (Critical Path)
**Effort**: 2 days
**Dependencies**: Story 9.1

**As a** PHP developer
**I want** codeindex to extract PHPDoc comments
**So that** my PHP project gets high-quality README_AI.md files

**Acceptance Criteria**:

1. ✅ `parser.py` extracts raw docstrings from PHP files
2. ✅ Supports multiple comment formats:
   - PHPDoc blocks (`/** ... */`)
   - Single-line comments (`// ...`)
   - Inline comments after code
3. ✅ `SmartWriter` integrates `DocstringProcessor`
4. ✅ Symbol descriptions in README_AI.md show normalized docstrings
5. ✅ Validates on user's PHP project (251 directories)
6. ✅ Test coverage ≥ 90%

**Technical Design**:

```python
# In parser.py
def parse_file(path: Path, language: str) -> ParseResult:
    """Parse file and extract symbols with raw docstrings."""

    if language == "php":
        # Use tree-sitter-php
        tree = php_parser.parse(content)
        symbols = _extract_php_symbols(tree, content)

    return ParseResult(path=path, symbols=symbols, ...)

def _extract_php_symbols(tree, content: str) -> list[Symbol]:
    """Extract PHP symbols with raw docstrings."""
    # Query for function_definition, method_declaration, class_declaration
    # Extract preceding comment nodes
    # Return Symbol(docstring=raw_comment_text, ...)
```

```python
# In smart_writer.py
class SmartWriter:
    def __init__(self, ..., docstring_processor: DocstringProcessor = None):
        self.docstring_processor = docstring_processor

    def _generate_detailed(self, parse_results: list[ParseResult]) -> str:
        if self.docstring_processor:
            # Process docstrings for all files in batch
            for result in parse_results:
                normalized = self.docstring_processor.process_file(
                    result.path, result.symbols
                )
                # Update symbol descriptions
                for symbol in result.symbols:
                    if symbol.name in normalized:
                        symbol.docstring = normalized[symbol.name]

        # Generate markdown with improved descriptions
        ...
```

**Tests**:
- `test_parse_phpdoc_block` - Extract `/** @param */` comments
- `test_parse_inline_comment` - Extract `//` comments
- `test_parse_mixed_language` - Handle Chinese + English
- `test_parse_class_docstring` - Class-level comments
- `test_parse_method_docstring` - Method-level comments
- `test_integration_with_processor` - End-to-end flow
- `test_fallback_without_processor` - Works without AI

---

### Story 9.3: Configuration & CLI (P1)

**Priority**: P1 (High Value)
**Effort**: 1 day
**Dependencies**: Story 9.1, 9.2

**As a** user
**I want** to control docstring extraction mode and cost
**So that** I can balance quality vs budget

**Acceptance Criteria**:

1. ✅ Configuration in `.codeindex.yaml`:
   ```yaml
   docstrings:
     mode: hybrid          # hybrid | all-ai | off
     ai_command: 'claude -p "{prompt}" --allowedTools Read'
     cost_limit: 1.0       # Max $1 per scan
   ```
2. ✅ CLI option: `codeindex scan --docstring-mode hybrid`
3. ✅ Cost reporting: `codeindex scan --show-cost`
4. ✅ Dry-run mode shows prompt without calling AI
5. ✅ Backward compatible: defaults to `off` (no AI)
6. ✅ Documentation updated

**Technical Design**:

```python
# In config.py
@dataclass
class DocstringConfig:
    mode: str = "off"           # off | hybrid | all-ai
    ai_command: str = ""
    cost_limit: float = 1.0     # USD

@dataclass
class Config:
    ...
    docstrings: DocstringConfig = field(default_factory=DocstringConfig)
```

```python
# In cli.py
@click.option(
    "--docstring-mode",
    type=click.Choice(["off", "hybrid", "all-ai"]),
    help="Docstring extraction mode (default: from config)",
)
@click.option(
    "--show-cost",
    is_flag=True,
    help="Show estimated AI cost after scan",
)
def scan(..., docstring_mode, show_cost):
    ...
```

**Tests**:
- `test_config_docstring_section` - Parse YAML config
- `test_cli_docstring_mode_option` - Override via CLI
- `test_cost_tracking` - Track and report costs
- `test_dry_run_with_docstrings` - Show prompt
- `test_backward_compatibility` - Defaults to off

---

### Story 9.4: Real PHP Project Validation (P0) 🔥

**Priority**: P0 (Critical Validation)
**Effort**: 1 day
**Dependencies**: Story 9.1, 9.2, 9.3

**As a** PHP developer with a large project
**I want** to validate docstring extraction on my 251-directory codebase
**So that** I can confirm it works in production

**Acceptance Criteria**:

1. ✅ Scan user's PHP project: 251 directories, 1926 symbols
2. ✅ Hybrid mode cost: <$1 for full scan
3. ✅ Extraction coverage: 80%+ of methods have descriptions
4. ✅ Quality rating: User rates ⭐⭐⭐⭐⭐ (vs previous ⭐⭐)
5. ✅ Performance: <10 minutes for full scan
6. ✅ No crashes or errors on any file
7. ✅ Case study documented

**Validation Plan**:

```bash
# Step 1: Backup current README_AI.md files
cp -r Application Application.backup

# Step 2: Configure hybrid mode
cat > .codeindex.yaml <<EOF
docstrings:
  mode: hybrid
  ai_command: 'claude -p "{prompt}" --allowedTools Read'
EOF

# Step 3: Scan all directories
time codeindex scan-all --show-cost

# Step 4: Compare quality
# - Before: Generic method names (e.g., "index", "create")
# - After: Descriptive (e.g., "Retrieve paginated user list")

# Step 5: Measure metrics
codeindex status  # Check coverage
grep -r "Description:" Application/*/README_AI.md | wc -l  # Count descriptions
```

**Success Metrics**:
- [ ] Cost: $0.XX (target <$1.00)
- [ ] Coverage: XX% (target 80%+)
- [ ] Quality: ⭐⭐⭐⭐⭐ (user rating)
- [ ] Time: X:XX minutes (target <10:00)
- [ ] Errors: 0 (target 0)

**Case Study** (to be documented):
- `docs/evaluation/case-studies/php-project-docstrings.md`
- Before/after comparison screenshots
- Cost breakdown by directory size
- Quality improvement examples

---

### Story 9.5: Documentation & Examples (P2)

**Priority**: P2 (Polish)
**Effort**: 1 day
**Dependencies**: Story 9.4 (validation complete)

**As a** new user
**I want** clear documentation on docstring extraction
**So that** I can use it effectively in my projects

**Acceptance Criteria**:

1. ✅ User guide: `docs/guides/docstring-extraction.md`
2. ✅ Developer guide: `docs/architecture/docstring-processor.md`
3. ✅ Configuration examples for PHP, Java (preview)
4. ✅ Cost optimization tips
5. ✅ Troubleshooting section
6. ✅ Updated CHANGELOG.md

**Documentation Outline**:

**User Guide** (`docs/guides/docstring-extraction.md`):
```markdown
# Docstring Extraction Guide

## Quick Start

## Modes Comparison
- Off: No AI (current behavior)
- Hybrid: Smart extraction (recommended, <$1)
- All-AI: Maximum quality (higher cost)

## Configuration
- .codeindex.yaml examples
- CLI options

## Cost Optimization
- Hybrid mode vs All-AI
- Selective directory scanning
- Batch processing tips

## Troubleshooting
- AI errors
- Malformed comments
- Performance issues
```

**Developer Guide** (`docs/architecture/docstring-processor.md`):
```markdown
# Docstring Processor Architecture

## Design Philosophy
- KISS principle: No complex parsers
- AI-powered understanding
- Universal approach

## How It Works
- Batch processing flow
- Prompt engineering
- JSON response parsing

## Extending to New Languages
1. Add tree-sitter integration
2. Extract raw comments
3. Reuse DocstringProcessor (done!)

## Testing Strategy
- Unit tests
- Integration tests
- Cost benchmarks
```

**Tests**:
- `test_documentation_examples` - Validate YAML examples
- `test_configuration_reference` - Check completeness

---

## 📅 Implementation Timeline

### Week 1 (Days 1-5): Core Implementation

**Day 1-2: Story 9.1 - Docstring Processor Core**
- [ ] Create `DocstringProcessor` class
- [ ] Implement hybrid mode logic
- [ ] Implement all-AI mode
- [ ] Add cost tracking
- [ ] Write 10+ unit tests
- [ ] Achieve 90%+ coverage

**Day 3-4: Story 9.2 - PHP Parser Integration**
- [ ] Extend `parser.py` for PHP docstrings
- [ ] Integrate `DocstringProcessor` into `SmartWriter`
- [ ] Test on sample PHP files
- [ ] Write integration tests
- [ ] Achieve 90%+ coverage

**Day 5: Story 9.3 - Configuration & CLI**
- [ ] Add `docstrings` config section
- [ ] Add CLI options (`--docstring-mode`, `--show-cost`)
- [ ] Update configuration docs
- [ ] Test backward compatibility

### Week 2 (Days 6-10): Validation & Polish

**Day 6-7: Story 9.4 - Real PHP Project Validation**
- [ ] Backup user's PHP project
- [ ] Run full scan with hybrid mode
- [ ] Measure cost, coverage, quality
- [ ] Fix any issues discovered
- [ ] Document case study

**Day 8: Bug Fixes & Optimization**
- [ ] Address validation findings
- [ ] Optimize prompt efficiency
- [ ] Improve error handling
- [ ] Performance tuning

**Day 9-10: Story 9.5 - Documentation**
- [ ] Write user guide
- [ ] Write developer guide
- [ ] Update CHANGELOG.md
- [ ] Create examples
- [ ] Final review

**Target Completion**: 2026-02-15 (Friday)

---

## 🏗️ Technical Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     SmartWriter                              │
│  - Orchestrates README_AI.md generation                     │
│  - Integrates DocstringProcessor                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                DocstringProcessor                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Mode Selection                                      │   │
│  │  - hybrid: Simple + Selective AI                    │   │
│  │  - all-ai: AI processes everything                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Batch Processing                                    │   │
│  │  - 1 AI call per file (not per comment)            │   │
│  │  - Prompt template with all symbols                 │   │
│  │  - Structured JSON response                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Fallback Strategy                                   │   │
│  │  - AI failure → Simple extraction (first line)      │   │
│  │  - Malformed JSON → Parse partial results           │   │
│  │  - Timeout → Skip AI, use raw docstrings            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Cost Tracking                                       │   │
│  │  - Token counting (input + output)                  │   │
│  │  - Per-file cost estimation                         │   │
│  │  - Total cost reporting                             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  AI CLI (External)                           │
│  - Claude CLI, OpenAI API, etc.                             │
│  - Headless mode (returns text/JSON)                        │
└─────────────────────────────────────────────────────────────┘
```

### Hybrid Mode Logic

```python
def _should_use_ai(self, docstring: str) -> bool:
    """
    Decide if AI is needed for this docstring.

    Hybrid mode uses AI only when necessary:
    - Simple cases: NO AI (fast, free)
    - Complex cases: YES AI (accurate, costs tokens)
    """
    if not docstring or len(docstring.strip()) == 0:
        return False  # Empty → No AI

    # Simple case: Clean one-liner in English
    # Example: "Get user list"
    if len(docstring) <= 60 and docstring.count('\n') == 0:
        if not self._contains_non_ascii(docstring):
            return False  # Simple English → No AI

    # Complex cases that need AI:
    # - Mixed language (Chinese + English)
    # - Multi-line with structure (@param, @return)
    # - Irregular formatting
    # - Very long (>60 chars)
    return True
```

### Prompt Template

```python
DOCSTRING_PROMPT = """You are analyzing source code documentation comments.

Extract and normalize docstrings for the following symbols:

File: {file_path}

Symbols:
{symbols_list}

For each symbol, generate a concise description (max 60 characters):
1. Use imperative mood ("Get user list", not "Gets user list")
2. Focus on WHAT the code does, not HOW
3. Combine information from all comment types (PHPDoc, inline, etc.)
4. Handle mixed languages (prefer English if available)
5. Remove noise (@param, @return, TODO, etc.)

Return JSON format:
{{
  "symbols": [
    {{
      "name": "methodName",
      "description": "Concise description here",
      "quality": "high|medium|low"
    }}
  ]
}}

If a symbol has no meaningful documentation, omit it from the response.
"""
```

### Cost Analysis

**Hybrid Mode Estimation** (250 directories, 1926 symbols):

| Component | Tokens | Cost @ $15/1M in | Cost @ $75/1M out |
|-----------|--------|------------------|-------------------|
| **Input** | ~50K | $0.75 | - |
| **Output** | ~10K | - | $0.75 |
| **Total** | 60K | **$1.50** | - |

**Optimization Strategies**:
1. Hybrid mode: Only 20-30% files need AI → Cost: **$0.30-$0.45** ✅
2. Batch processing: 1 call per file (not per symbol) → -90% calls
3. Short prompts: Max 500 tokens per file → Minimal input cost
4. Selective scanning: Skip test files, generated code

**Target**: <$1 per 250-directory scan ✅

---

## ✅ Acceptance Checklist

### Functional Requirements

- [ ] `DocstringProcessor` class implemented
- [ ] Hybrid mode works (simple extraction + selective AI)
- [ ] All-AI mode works (maximum quality)
- [ ] PHP docstring extraction from tree-sitter
- [ ] SmartWriter integration complete
- [ ] Configuration support (`.codeindex.yaml`)
- [ ] CLI options (`--docstring-mode`, `--show-cost`)
- [ ] Cost tracking and reporting
- [ ] Fallback on AI errors

### Quality Requirements

- [ ] Test coverage ≥ 90% (core modules)
- [ ] All tests passing (pytest -v)
- [ ] Ruff linting passing (ruff check src/)
- [ ] No performance regression (<10 min for 250 dirs)

### Validation Requirements

- [ ] Real PHP project scan successful (251 dirs)
- [ ] Cost <$1 for hybrid mode ✅
- [ ] Extraction coverage ≥80% ✅
- [ ] Quality rating ⭐⭐⭐⭐⭐ (user feedback)
- [ ] Case study documented

### Documentation Requirements

- [ ] User guide created
- [ ] Developer guide created
- [ ] Configuration examples provided
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)

---

## 🔄 Dependencies

### Upstream Dependencies (Blockers)

None - Epic 9 can start immediately.

### Downstream Dependencies (Enabled By)

1. **Epic 7: Java Language Support (v0.7.0)**
   - Will reuse `DocstringProcessor` for JavaDoc
   - Only need to add tree-sitter-java integration
   - Estimated effort: 10 minutes to extend

2. **v0.8.0: Multi-Language Support**
   - TypeScript: JSDoc extraction (reuse DocstringProcessor)
   - Go: doc comment extraction (reuse DocstringProcessor)
   - Rust: doc comment extraction (reuse DocstringProcessor)

3. **Future: API Documentation Generation**
   - High-quality symbol descriptions enable auto-generation
   - OpenAPI specs from route extractors + docstrings

---

## 🎯 Success Metrics

### Quantitative Metrics

| Metric | Baseline (v0.5.0) | Target (v0.6.0) | Measurement |
|--------|-------------------|-----------------|-------------|
| **Extraction Coverage** | 0% (no docstrings) | 80%+ | Count symbols with descriptions |
| **Description Quality** | ⭐⭐ (generic names) | ⭐⭐⭐⭐⭐ (descriptive) | User subjective rating |
| **Cost per 250-dir scan** | N/A | <$1.00 | Track API costs |
| **Processing time** | ~8 min | <10 min | Time codeindex scan-all |
| **Error rate** | 0% | <1% | Count AI failures / total files |

### Qualitative Metrics

1. **User Satisfaction**
   - User rates feature ⭐⭐⭐⭐⭐
   - User reports README_AI.md is now "production-ready"

2. **Developer Experience**
   - Adding Java support takes <10 minutes
   - Other developers can add new languages easily

3. **Architecture Validation**
   - KISS principle proven (no complex parsers needed)
   - AI-powered approach scales to all languages

---

## 🚧 Risks & Mitigations

### Risk 1: AI Cost Exceeds Budget

**Impact**: High
**Probability**: Medium
**Mitigation**:
- Default to hybrid mode (not all-AI)
- Add cost limit config (default $1)
- Add `--show-cost` dry-run before actual scan
- Batch processing (1 call per file, not per symbol)

### Risk 2: AI Generates Malformed JSON

**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Robust JSON parsing with error handling
- Fallback to simple extraction if parsing fails
- Log malformed responses for debugging
- Add validation in tests

### Risk 3: Performance Degradation

**Impact**: Medium
**Probability**: Low
**Mitigation**:
- Parallel AI calls (max 2 concurrent)
- Skip AI for tiny files (<10 lines)
- Cache AI responses per file (future optimization)

### Risk 4: PHP Project Has Unique Edge Cases

**Impact**: High
**Probability**: Medium
**Mitigation**:
- Start with small subset (10 directories)
- Iterate based on findings
- Add tests for edge cases discovered
- User provides feedback during validation

### Risk 5: Java Support Reuse Not Smooth

**Impact**: Low
**Probability**: Low
**Mitigation**:
- Design `DocstringProcessor` to be language-agnostic
- Test with mock data before PHP implementation
- Document extension guide in Story 9.5

---

## 📚 Related Documents

- **Strategic Roadmap**: `docs/planning/ROADMAP.md`
- **Configuration Guide**: `docs/guides/configuration.md`
- **Case Study** (TBD): `docs/evaluation/case-studies/php-project-docstrings.md`
- **GitHub Epic Issue**: [Epic 9: AI-Powered Docstring Extraction](https://github.com/dreamlx/codeindex/issues/XX)

---

## 📝 Notes

### Design Decisions

**Q: Why AI-powered instead of traditional parsers?**
A: Traditional parsers (PHPDocParser, JavaDocParser) are:
- Complex (100+ lines of regex per language)
- Brittle (can't handle irregular formats)
- Language-specific (need separate implementation for each)

AI-powered approach is:
- Simple (10 lines fallback + AI prompt)
- Universal (works for all languages)
- Robust (handles irregular, mixed-language comments)

**Q: Why hybrid mode instead of all-AI?**
A: Cost optimization. Hybrid mode:
- Uses AI only when needed (20-30% of files)
- Achieves 80% of quality at 30% of cost
- Recommended default for production use

**Q: Why batch processing (1 call per file)?**
A: Efficiency:
- 1000 symbols → 1000 AI calls (slow, expensive)
- 1000 symbols in 50 files → 50 AI calls (fast, cheap)
- Batch processing reduces calls by 95%+

### Future Enhancements (Not in v0.6.0)

1. **Caching**: Cache AI responses per file hash (avoid re-processing unchanged files)
2. **Streaming**: Stream AI responses for large files (reduce latency)
3. **Multi-Model**: Support multiple AI providers (Claude, GPT-4, Gemini)
4. **Fine-Tuning**: Train custom model for docstring extraction (reduce cost)

---

**Epic Status**: 📋 Planning Complete
**Ready for Implementation**: Yes
**Next Step**: Create GitHub Epic Issue + 5 Story Issues
**Owner**: @dreamlx
**Last Updated**: 2026-02-03
