# Docstring Extraction Guide

**Epic 9: AI-Powered Docstring Extraction and Normalization**

Version: v0.4.0+
Status: Released

---

## Overview

codeindex's docstring extraction feature uses AI to normalize inconsistent, mixed-language, or cryptic code comments into clear, professional English descriptions. This is especially valuable for:

- **Multi-language projects**: Chinese + English comments mixed together
- **Legacy codebases**: Minimal or cryptic documentation
- **PHP projects**: PHPDoc with inconsistent quality
- **International teams**: Different documentation standards

---

## Quick Start

### 1. Enable Docstring Extraction

Add to `.codeindex.yaml`:

```yaml
docstrings:
  mode: hybrid           # Recommended: Cost-effective selective AI
  cost_limit: 1.0        # Maximum spending limit in USD
```

### 2. Scan with Docstring Processing

```bash
# Scan single directory
codeindex scan src/ --docstring-mode hybrid --show-cost

# Scan entire project
codeindex scan-all --docstring-mode hybrid --show-cost
```

### 3. Check Results

Open generated `README_AI.md` files - docstrings are now normalized!

---

## Modes Comparison

| Mode | AI Usage | Cost (250 dirs) | Quality | Best For |
|------|----------|-----------------|---------|----------|
| **off** | None | $0 | Raw docstrings | Consistent English docs |
| **hybrid** ⭐ | Selective | <$1 (~$0.15) | High | Most projects |
| **all-ai** | Everything | ~$1.50 | Maximum | Critical documentation |

### Mode Details

#### `off` (Default)
```yaml
docstrings:
  mode: off
```

- **Behavior**: Uses raw docstrings without AI processing
- **Cost**: $0
- **When to use**:
  - Existing documentation is already in clean English
  - Cost-sensitive projects
  - No AI CLI available

#### `hybrid` (Recommended ⭐)
```yaml
docstrings:
  mode: hybrid
  cost_limit: 1.0
```

- **Behavior**: AI processes only complex/mixed-language docstrings
- **Decision logic**:
  - ✅ **AI processes**: Structured docs (`@param`, `@return`), mixed language, long/complex comments
  - ⏩ **Skips AI**: Simple English one-liners (e.g., "Get user by ID")
- **Cost**: ~$0.15 for typical 250-directory project
- **Token usage**: ~50,000 tokens (only complex docstrings)
- **When to use**: **Most projects** - best cost/quality balance

#### `all-ai` (Maximum Quality)
```yaml
docstrings:
  mode: all-ai
  cost_limit: 2.0
```

- **Behavior**: AI processes **every** docstring
- **Cost**: ~$1.50 for 250-directory project
- **Token usage**: ~500,000 tokens (all docstrings)
- **When to use**:
  - High-value codebases needing professional docs
  - Multilingual projects requiring consistent normalization
  - Initial cleanup of legacy documentation

---

## Configuration

### Full Configuration

```yaml
# .codeindex.yaml

# Global AI command
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Docstring extraction (Epic 9)
docstrings:
  # Mode: off | hybrid | all-ai
  mode: hybrid

  # AI CLI command (optional, inherits from global if not specified)
  # Useful if you want different AI for docstring processing
  # ai_command: 'claude -p "{prompt}"'

  # Cost limit in USD (prevents runaway costs)
  cost_limit: 1.0
```

### AI Command Inheritance

If `docstrings.ai_command` is not specified, it inherits from global `ai_command`:

```yaml
# This config...
ai_command: 'claude -p "{prompt}"'
docstrings:
  mode: hybrid
  # No ai_command specified

# ...is equivalent to:
ai_command: 'claude -p "{prompt}"'
docstrings:
  mode: hybrid
  ai_command: 'claude -p "{prompt}"'  # Inherited
```

### Cost Limit Protection

The `cost_limit` parameter prevents accidental overspending:

```yaml
docstrings:
  mode: all-ai
  cost_limit: 1.0    # Stop if estimated cost exceeds $1.00
```

- **Monitoring**: Use `--show-cost` to track actual usage
- **Estimation**: Cost = (tokens / 1,000,000) × $3
- **Safety net**: Processing stops if limit is exceeded

---

## CLI Usage

### Override Config Mode

```bash
# Override config with CLI option
codeindex scan src/ --docstring-mode hybrid

# Use all-ai mode temporarily
codeindex scan-all --docstring-mode all-ai

# Disable docstring processing
codeindex scan src/ --docstring-mode off
```

### Track Costs

```bash
# Show token usage and estimated cost
codeindex scan src/ --docstring-mode hybrid --show-cost

# Output example:
# ✓ Created (detailed, 12.5KB): src/README_AI.md
#   → Docstring processing: 1500 tokens (~$0.0045)
```

### Combine with Other Options

```bash
# Hybrid mode + parallel scanning + cost tracking
codeindex scan-all \
  --docstring-mode hybrid \
  --show-cost \
  --parallel 8

# All-AI mode + hierarchical processing
codeindex scan-all \
  --docstring-mode all-ai \
  --hierarchical \
  --show-cost
```

---

## Supported Languages

### PHP (Fully Supported)

**PHPDoc blocks** (`/** ... */`):
```php
/**
 * 获取用户列表 Get user list
 * @param int $page 页码 Page number
 * @param int $limit 每页数量 Items per page
 * @return array 用户数据 User data
 */
function getUserList($page, $limit) {
    return [];
}
```

**Inline comments** (`//`):
```php
// 获取用户 Get user
function getUser($id) {
    return [];
}
```

**AI Output** (hybrid mode):
```
Retrieves paginated user list with configurable page size
```

### Python (Coming Soon)

- Docstrings (triple quotes)
- Inline comments (`#`)

### JavaScript/TypeScript (Planned)

- JSDoc (`/** ... */`)
- Inline comments (`//`)

---

## Real-World Examples

### Example 1: PHP Payment Gateway

**Before** (mixed language):
```php
/**
 * 处理支付回调 Process payment callback
 * @param array $data 支付数据 Payment data
 * @return bool 是否成功 Success status
 */
public function handleCallback($data) { ... }
```

**After** (hybrid mode):
```
Processes payment gateway callback and updates order status
```

**Result**: Clean, professional description without language mixing.

---

### Example 2: Legacy PHP CRUD

**Before** (cryptic):
```php
// get lst
function getLst($p, $l) { ... }

// upd usr
function updUsr($id, $data) { ... }
```

**After** (all-ai mode):
```
Retrieves paginated list with configurable page size and limit

Updates user record by ID with provided data dictionary
```

**Result**: Meaningful descriptions inferred from code context.

---

### Example 3: PHP Framework Controller

**Before** (structured PHPDoc):
```php
/**
 * User controller
 * @author John Doe
 * @version 1.0
 * @since 2024-01-15
 */
class UserController {
    /**
     * Index action
     * @param Request $request HTTP request object
     * @return Response JSON response with user list
     * @throws Exception If database connection fails
     */
    public function index(Request $request) { ... }
}
```

**After** (hybrid mode):
```
Main controller for user management operations

Returns paginated user list as JSON response
```

**Result**: Concise descriptions focusing on functionality, not metadata.

---

## How It Works

### Processing Flow

```
1. Parse File
   └─> Extract raw docstrings with tree-sitter

2. Analyze Docstrings (if mode != "off")
   └─> Decide: Simple or Complex?
       ├─> Simple English one-liner → Skip AI (free)
       └─> Complex/Mixed language → Process with AI

3. Batch AI Call
   └─> Single API call per file (not per symbol)
       └─> Input: All complex docstrings in file
       └─> Output: Normalized descriptions

4. Generate README
   └─> Use AI-normalized descriptions
       └─> Fallback to raw docstrings if AI fails
```

### Decision Logic (Hybrid Mode)

**Skip AI** (free processing):
- Length ≤ 60 characters
- Single line
- Pure ASCII (no Chinese/special chars)
- No structured markers (`@param`, `@return`)

**Use AI** (processes with AI):
- Contains structured markers (`@param`, `@return`, `@throws`)
- Mixed language (Chinese + English)
- Multi-line complex descriptions
- Length > 60 characters

**Example**:
```php
// "Get user" → Skip AI ⏩ (simple, clean)
// "获取用户 Get user" → Use AI 🤖 (mixed language)
// "/** @param int $id User ID */" → Use AI 🤖 (structured)
```

---

## Performance

### Batch Processing

- **1 AI call per file** (not per symbol)
- Example: File with 10 functions → 1 API call for all 10
- Reduces API overhead and cost

### Parallel Safe

Works with `--parallel` option:
```bash
codeindex scan-all --parallel 8 --docstring-mode hybrid
```

Each worker processes files independently with its own DocstringProcessor instance.

### Token Usage

**Typical 250-directory PHP project** (1926 symbols):

| Mode | Symbols Processed | Tokens | Cost |
|------|------------------|--------|------|
| hybrid | ~100-200 (complex only) | ~50,000 | ~$0.15 |
| all-ai | 1926 (all symbols) | ~500,000 | ~$1.50 |

**Formula**: Cost ≈ (tokens / 1,000,000) × $3

---

## Cost Optimization Tips

### 1. Use Hybrid Mode (Default)

```yaml
docstrings:
  mode: hybrid    # ⭐ Best cost/quality balance
```

Processes only complex docstrings, skips simple ones.

### 2. Set Cost Limits

```yaml
docstrings:
  cost_limit: 1.0    # Stop if cost exceeds $1.00
```

Prevents accidental overspending.

### 3. Test on Single Directory First

```bash
# Test cost on one directory
codeindex scan src/controllers/ --docstring-mode hybrid --show-cost

# Check output:
# → Docstring processing: 500 tokens (~$0.0015)

# Extrapolate for full project:
# 100 dirs × $0.0015 = ~$0.15 total
```

### 4. Use All-AI Selectively

```bash
# Use all-ai only for critical directories
codeindex scan src/core/ --docstring-mode all-ai
codeindex scan src/helpers/ --docstring-mode off
```

### 5. Monitor Usage

```bash
# Always use --show-cost during development
codeindex scan-all --docstring-mode hybrid --show-cost

# Track cumulative cost across runs
```

---

## Troubleshooting

### Issue: AI Not Processing Docstrings

**Symptoms**: Docstrings appear unchanged in README_AI.md

**Possible causes**:
1. **Mode is `off`**: Check `.codeindex.yaml` → `docstrings.mode`
2. **No AI command**: Verify `ai_command` is set
3. **Hybrid skipped AI**: Docstrings were simple enough (working as intended)

**Solution**:
```bash
# Force all-ai mode to verify
codeindex scan src/ --docstring-mode all-ai --show-cost

# Check if AI was called (should see token count)
```

---

### Issue: Cost Exceeds Limit

**Symptoms**: Processing stops with cost limit error

**Possible causes**:
1. `cost_limit` too low
2. Large project with many complex docstrings
3. All-AI mode on huge project

**Solution**:
```yaml
# Increase cost limit
docstrings:
  cost_limit: 5.0    # Increase from 1.0 to 5.0
```

Or use selective processing:
```bash
# Process only critical directories
codeindex scan src/core/ --docstring-mode all-ai
codeindex scan src/utils/ --docstring-mode off
```

---

### Issue: Poor Quality Descriptions

**Symptoms**: AI-generated descriptions are generic or wrong

**Possible causes**:
1. Insufficient code context
2. Ambiguous original docstrings
3. AI model limitations

**Solution**:
1. **Add context to docstrings**:
   ```php
   // Before: "Process data"
   // After: "Process payment data and update order status"
   ```

2. **Use all-ai mode**: More aggressive processing
   ```bash
   codeindex scan src/ --docstring-mode all-ai
   ```

3. **Try different AI model**: Update `ai_command` in config

---

## Migration Guide

### From No Docstring Processing

**Step 1**: Add config section
```yaml
docstrings:
  mode: hybrid
  cost_limit: 1.0
```

**Step 2**: Test on single directory
```bash
codeindex scan src/controllers/ --show-cost
```

**Step 3**: Scan entire project
```bash
codeindex scan-all --show-cost
```

### From `off` to `hybrid`

No migration needed! Just update config:

```yaml
# Before
docstrings:
  mode: off

# After
docstrings:
  mode: hybrid
```

Then re-scan:
```bash
codeindex scan-all
```

### From `hybrid` to `all-ai`

Update config and increase cost limit:

```yaml
# Before
docstrings:
  mode: hybrid
  cost_limit: 1.0

# After
docstrings:
  mode: all-ai
  cost_limit: 5.0    # Increased for higher processing
```

---

## Best Practices

### 1. Start with Hybrid Mode

```yaml
docstrings:
  mode: hybrid    # Recommended default
```

Provides 80% of all-ai quality at 10% of the cost.

### 2. Always Use --show-cost

```bash
codeindex scan-all --docstring-mode hybrid --show-cost
```

Monitor spending during development.

### 3. Set Realistic Cost Limits

```yaml
# For typical project (250 dirs)
docstrings:
  cost_limit: 1.0    # Hybrid mode

# For large enterprise project (1000+ dirs)
docstrings:
  cost_limit: 5.0    # All-AI mode
```

### 4. Process Incrementally

```bash
# Don't process entire monorepo at once
# Process modules incrementally:

codeindex scan backend/core/ --docstring-mode all-ai
codeindex scan backend/api/ --docstring-mode hybrid
codeindex scan backend/utils/ --docstring-mode off
```

### 5. Version Control Integration

```bash
# Add pre-commit hook to auto-update docs
codeindex hooks install --all

# Docstrings processed automatically on commit
```

---

## FAQ

### Q: What languages are supported?

**A**: Currently PHP (v0.4.0+). Python support coming soon.

---

### Q: How accurate is cost estimation?

**A**: Within ±20% for typical projects. Actual cost depends on:
- Token count (varies by docstring complexity)
- AI provider rates (example uses $3/1M tokens)

---

### Q: Can I use different AI for docstrings?

**A**: Yes! Specify custom `ai_command`:
```yaml
ai_command: 'claude -p "{prompt}"'   # For README generation
docstrings:
  mode: hybrid
  ai_command: 'gpt-4 "{prompt}"'      # For docstring processing
```

---

### Q: Does it work offline?

**A**: Only in `off` mode. Hybrid and all-ai require AI CLI access.

---

### Q: What if AI fails?

**A**: Graceful fallback to raw docstrings. No broken READMEs!

---

### Q: How to disable for specific directories?

**A**: Use CLI override:
```bash
codeindex scan src/legacy/ --docstring-mode off
```

Or exclude in config:
```yaml
exclude:
  - "**/legacy/**"
```

---

## Performance Benchmarks

### Typical PHP Project (251 directories, 1926 symbols)

| Mode | Processing Time | Token Usage | Cost | Quality |
|------|----------------|-------------|------|---------|
| off | 15s | 0 | $0 | Raw |
| hybrid | 25s (+67%) | 50K | $0.15 | High |
| all-ai | 60s (+300%) | 500K | $1.50 | Maximum |

**Conclusion**: Hybrid mode adds minimal overhead with significant quality improvement.

---

## Integration Examples

### With CI/CD

```yaml
# .github/workflows/docs.yml
name: Update Documentation

on: [push]

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install codeindex
        run: pipx install codeindex
      - name: Generate docs
        run: codeindex scan-all --docstring-mode hybrid
      - name: Commit changes
        run: |
          git add README_AI.md
          git commit -m "docs: auto-update with AI docstrings"
          git push
```

### With Pre-commit Hooks

```bash
# Install hooks
codeindex hooks install --all

# Auto-processes docstrings on commit
git commit -m "feat: add payment processing"

# Output:
# 🔍 Running pre-commit checks...
# ✓ Lint check passed
# ✓ No debug code found
# 📝 Post-commit: Analyzing changes...
# → Docstring processing: 500 tokens (~$0.0015)
# ✓ Updated README_AI.md
```

---

## Roadmap

### v0.4.0 (Released) ✅
- ✅ PHP docstring extraction
- ✅ Hybrid mode (selective AI)
- ✅ All-AI mode (maximum quality)
- ✅ CLI options (`--docstring-mode`, `--show-cost`)
- ✅ Cost tracking and limits

### v0.5.0 (Planned)
- ⏳ Python docstring extraction
- ⏳ JavaScript/TypeScript JSDoc support
- ⏳ Multi-model support (OpenAI, Anthropic, local LLMs)
- ⏳ Custom prompt templates for docstrings

### v1.0.0 (Future)
- 🎯 Smart caching (avoid re-processing unchanged docstrings)
- 🎯 Docstring quality scoring
- 🎯 Interactive refinement mode
- 🎯 Batch cost optimization

---

## Related Documentation

- **Configuration Guide**: `docs/guides/configuration.md`
- **CLI Reference**: `docs/guides/advanced-usage.md`
- **Epic 9 Planning**: `docs/planning/epic9-docstring-extraction.md`
- **PHP Parser**: `docs/development/improvements/php-parser.md`

---

## Support

For issues, questions, or feedback:
- **GitHub Issues**: https://github.com/yourusername/codeindex/issues
- **Discussions**: https://github.com/yourusername/codeindex/discussions
- **Documentation**: https://codeindex.readthedocs.io

---

**Last Updated**: 2026-02-03
**Version**: v0.4.0
**Status**: Production Ready ✅
