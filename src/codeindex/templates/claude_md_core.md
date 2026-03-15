## codeindex

This project uses [codeindex](https://github.com/dreamlx/codeindex) (v{version}) for AI-friendly code documentation.

### Code Navigation Priority

1. **Always read `README_AI.md` first** before exploring source code in any directory
2. Use Serena MCP symbolic tools (`find_symbol`, `find_referencing_symbols`) for precise navigation
3. Only read source files when you need implementation details

### Quick Commands

```bash
codeindex scan-all          # Generate all indexes
codeindex scan ./path       # Scan single directory
codeindex scan ./path --ai  # AI-enhanced generation
codeindex symbols           # Global symbol index
codeindex status            # Check index coverage
codeindex --help            # Full command reference
```

After upgrading codeindex, run `codeindex claude-md update` to refresh this section.
