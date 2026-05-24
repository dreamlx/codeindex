## codeindex

This project uses [codeindex](https://github.com/dreamlx/codeindex) (v{version}) for AI-friendly code documentation.

### Code Navigation Priority

1. **Always read `README_AI.md` first** before exploring source code in any directory
2. Use Serena MCP symbolic tools (`find_symbol`, `find_referencing_symbols`) for precise navigation
3. Only read source files when you need implementation details

### Quick Commands

```bash
codeindex scan-all                       # All indexes (structural — no AI cost)
codeindex scan-all --ai                  # + AI per-module description; ok results cached
codeindex scan-all --ai --retry-all      # Force re-enrich every dir, ignore cache
codeindex scan ./path                    # Scan single directory
codeindex scan ./path --ai               # AI-enhanced single dir
codeindex symbols                        # Global symbol index (PROJECT_SYMBOLS.md)
codeindex status                         # Check index coverage
codeindex --help                         # Full command reference
```

### When `scan-all --ai` fails on some dirs

You will see lines like `⚠ <dir>: AI error — <reason>`. Likely transient (rate limit / network).

- Re-run `codeindex scan-all --ai` — successful dirs are restored from cache (no AI cost), only failed ones retry
- If failures persist, edit `ai_command` in `.codeindex.yaml` to switch backend:
  - `claude -p "{prompt}" --allowedTools "Read" --model haiku` — cheaper
  - `opencode run --model <provider>/<model> "{prompt}" | tail -1` — different agent
  - `gemini -p "{prompt}"` — different vendor

### What the markers mean

Each `README_AI.md` has a generator header. AI-enriched ones get a second line:

- `<!-- enrichment: ok -->` — AI description in the `> blockquote` is current
- `<!-- enrichment: failed (reason: ...) -->` — enrichment was attempted and failed; description may be missing
- No marker — structural-only (no `--ai` was run)

After upgrading codeindex, run `codeindex claude-md update` to refresh this section.
