# Release Notes v0.19.0 — TypeScript/JavaScript Language Support

**Date**: 2026-02-19

## Highlights

codeindex now parses TypeScript and JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`) using tree-sitter. A single `TypeScriptParser` class handles all 4 file types with 3 grammar variants.

## What's New

### Full TS/JS Parsing Pipeline

```bash
# Install with TypeScript support
pip install ai-codeindex[typescript]
# or all languages
pip install ai-codeindex[all]

# Parse a TypeScript file
codeindex parse src/service.ts | jq .

# Scan a TS/JS project
codeindex scan ./src --languages typescript,javascript
```

### Symbol Extraction

- Classes (with generics, abstract, decorators)
- Functions (named, arrow, async, generators)
- Methods (instance, static, getters/setters, constructors)
- Interfaces (TS only)
- Enums (string, numeric, const)
- Type aliases (TS only)
- Const/let/var declarations
- React function components (JSX/TSX)
- Namespaces (TS only)
- Ambient declarations (.d.ts)

### Import/Export Extraction

- ES modules: `import { X } from 'module'`, default, namespace, side-effect
- CommonJS: `const X = require('module')`
- Type-only: `import type { X } from 'module'`
- Re-exports: `export { X } from 'module'`
- Barrel exports: `export * from 'module'`

### Inheritance & Call Graphs

- Class extends/implements
- Interface extends (single and multiple)
- Function/method/static/constructor calls
- Chained method calls

## Grammar Routing

| Extension | Grammar | Parser |
|-----------|---------|--------|
| `.ts` | `language_typescript()` | TypeScriptParser |
| `.tsx` | `language_tsx()` | TypeScriptParser |
| `.js` | `language()` (javascript) | TypeScriptParser |
| `.jsx` | `language()` (javascript) | TypeScriptParser |

## Test Coverage

- 77 new tests (68 unit + 9 integration)
- 1143 total tests passing
- 0 failures

## Dependencies

- `tree-sitter-typescript>=0.23.2` (contains both TS and TSX grammars)
- `tree-sitter-javascript>=0.25.0`

## Configuration

Add to `.codeindex.yaml`:

```yaml
languages:
  - typescript
  - javascript
```
