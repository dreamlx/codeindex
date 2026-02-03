# Configuration Changelog

**Purpose**: Track `.codeindex.yaml` configuration changes across versions

**Audience**: Users upgrading from previous versions

---

## Quick Version Check

**Current codeindex version**: Run `codeindex --version`

**Your config version**: Check `version: N` in `.codeindex.yaml`

**Need upgrade?** See migration guides below ⬇️

---

## v0.5.0 (2026-02-03)

### Configuration Changes

⚠️ **New optional configuration added**

#### 1. PROJECT_SYMBOLS.md Generation Control

**Added**:
```yaml
symbols:
  # ... existing adaptive_symbols config ...

  # NEW: Control PROJECT_SYMBOLS.md generation
  project_symbols:
    enabled: false           # Disable global symbol index generation
```

**Why this was added**:
- PROJECT_SYMBOLS.md can become very large (>400KB for large projects)
- Limited value for AI-assisted development in practice
- Better alternatives exist:
  - `PROJECT_INDEX.md` provides module navigation (typically 26KB)
  - Each `README_AI.md` contains directory-specific symbols
  - Serena MCP's `find_symbol()` for precise symbol lookup

**Recommended setting**: `enabled: false` for projects with >100 files

**Migration**:
```yaml
# No action required - defaults to generating PROJECT_SYMBOLS.md
# To disable (recommended for large projects):
symbols:
  adaptive_symbols:
    enabled: true           # Keep existing settings
  project_symbols:
    enabled: false          # NEW: Disable PROJECT_SYMBOLS.md
```

**Backward compatibility**: 100% compatible - defaults to enabled if not specified

### Git Hooks Usage

Git Hooks通过CLI命令管理，**不在配置文件中配置**：

```bash
codeindex hooks install --all
codeindex hooks status
codeindex hooks uninstall --all
```

详见：`docs/guides/git-hooks-integration.md`

---

## v0.4.0 (2026-02-02)

### Configuration Changes

✅ **No configuration changes**

- KISS描述生成器改进不需要配置文件变更
- 向后100%兼容

---

## v0.3.1 (2026-01-28)

### Configuration Changes

✅ **No configuration changes**

- CLI架构重构不影响配置文件
- 所有命令和选项保持不变

---

## v0.3.0 (2026-01-27)

### Configuration Changes

⚠️ **New configuration sections added** (all optional)

#### 1. AI Enhancement Strategy

**Added**:
```yaml
ai_enhancement:
  strategy: "selective"      # NEW: "selective" | "all"
  enabled: true
  size_threshold: 40960      # NEW: >40KB triggers AI
  max_concurrent: 2          # NEW: Max parallel AI calls
  rate_limit_delay: 1.0      # NEW: Seconds between AI calls
```

**Migration**:
```yaml
# Old (v0.2.0) - still works, defaults apply
ai_command: 'claude -p "{prompt}"'

# New (v0.3.0+) - optional enhancement
ai_command: 'claude -p "{prompt}"'
ai_enhancement:
  strategy: "selective"      # Only large files get AI enhancement
  size_threshold: 40960      # Customize threshold (default 40KB)
```

**Why upgrade**: Better control over AI usage and cost

#### 2. Multi-turn Dialogue for Super Large Files

**Added**:
```yaml
# Thresholds for multi-turn dialogue detection
# Triggered when file > 5000 lines OR > 100 symbols
```

Controlled via CLI: `codeindex scan --strategy multi_turn`

**No config file changes needed** - works automatically

#### 3. Technical Debt Thresholds

**Added**:
```yaml
tech_debt:
  file_size:
    large_threshold: 2000           # Lines for "large file" warning
    super_large_threshold: 5000     # Lines for "super large" critical
  god_class:
    method_threshold: 50            # Methods for "god class" detection
  symbol_overload:
    total_threshold: 100            # Total symbols threshold
    noise_ratio: 0.5                # >50% low-quality symbols
  complexity:
    cyclomatic_threshold: 10
    cognitive_threshold: 15
    nesting_threshold: 4
```

**Migration**: Not needed unless you want custom thresholds

**Default behavior**: Uses built-in thresholds (shown above)

### Backward Compatibility

✅ **100% backward compatible**

- All v0.2.0 configs work without modification
- New sections are **optional**
- Defaults apply if not specified

---

## v0.2.0 (2025-01-15)

### Configuration Changes

⚠️ **Major new feature: Adaptive Symbol Extraction**

#### Added Configuration Section

```yaml
symbols:
  adaptive_symbols:
    enabled: false           # ⚠️ Default: disabled for safety
    min_symbols: 5           # Minimum for tiny files
    max_symbols: 150         # Maximum for huge files
    thresholds:              # File size thresholds (lines)
      tiny: 100
      small: 500
      medium: 1500
      large: 3000
      xlarge: 5000
      huge: 8000
      mega: null             # >8000 lines
    limits:                  # Symbol limits per category
      tiny: 5
      small: 15
      medium: 30
      large: 50
      xlarge: 80
      huge: 120
      mega: 150
```

### Migration Guide

**Option 1: Keep existing behavior (recommended for first upgrade)**

```yaml
# No changes needed - adaptive symbols disabled by default
# Your existing config continues to work
```

**Option 2: Enable adaptive symbols**

```yaml
# Add this section to your .codeindex.yaml
symbols:
  adaptive_symbols:
    enabled: true            # ← Enable feature
    # Use defaults or customize thresholds
```

**Benefits of enabling**:
- Large files: 26% → 100% information coverage (+280%)
- Dynamic symbol limits: 5-150 per file (vs fixed 15)
- Better handling of both tiny and huge files

**Risks**:
- README_AI.md content changes (more symbols for large files)
- May need to regenerate all documentation

### Backward Compatibility

✅ **Zero breaking changes**

- Default: `enabled: false`
- All existing configs work without modification
- All 66 regression tests passing

### Testing Your Upgrade

```bash
# Before enabling adaptive symbols
codeindex scan src/ --fallback

# Enable in .codeindex.yaml
symbols:
  adaptive_symbols:
    enabled: true

# Test on a single directory first
codeindex scan src/codeindex --fallback

# Compare outputs, then roll out project-wide
codeindex scan-all --fallback
```

---

## v0.1.3 (2025-01-15)

### Configuration Changes

✅ **No configuration changes**

- PROJECT_INDEX generation doesn't require config changes

---

## v0.1.2 (2025-01-14)

### Configuration Changes

⚠️ **New optional fields**

**Added**:
```yaml
ai_timeout: 120              # Timeout in seconds (default: 120)
parallel_workers: 8          # Parallel scan workers (default: 8)
batch_size: 50               # Batch size for parallel processing
```

**Migration**: Not required - defaults apply

---

## v0.1.1 (2025-01-13)

### Configuration Changes

✅ **Configuration file support stabilized**

**Added**:
- Validation for `.codeindex.yaml` format
- Better error messages for invalid configs

**Migration**: None - v0.1.0 configs work as-is

---

## v0.1.0 (2025-01-12)

### Initial Configuration Schema

**Basic structure**:
```yaml
version: 1

ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

include:
  - src/
  - lib/

exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.git/**"

languages:
  - python

output_file: README_AI.md
```

---

## Configuration Version Schema

### Version Field

```yaml
version: 1    # Configuration schema version
```

**Current version**: 1 (since v0.1.0)

**Future versions**: Will be introduced if breaking changes occur

**Purpose**:
- Allows automated migration tools
- Helps users identify outdated configs

---

## Migration Checklist

### Upgrading from v0.2.0 to v0.5.0-beta1

```bash
✅ Check your config version
cat .codeindex.yaml | grep version

✅ Verify backward compatibility
codeindex validate-config    # (future command)

✅ Optional: Add new features
# 1. AI enhancement strategy (v0.3.0)
# 2. Tech debt thresholds (v0.3.0)

✅ Test before full rollout
codeindex scan src/codeindex --fallback

✅ Regenerate documentation
codeindex scan-all --fallback
```

### Upgrading from v0.1.x to v0.5.0-beta1

```bash
✅ Review breaking changes
# None - all versions 100% backward compatible

✅ Add optional new features
# See v0.2.0 and v0.3.0 sections above

✅ Update configuration file
cp examples/.codeindex.yaml .codeindex.yaml.new
# Merge your customizations

✅ Test
codeindex scan . --dry-run
```

---

## Best Practices

### When to Update Configuration

1. **Mandatory**: Never (all versions backward compatible)
2. **Recommended**:
   - When upgrading across major versions (v0.1.x → v0.3.x)
   - When you want new features (adaptive symbols, AI strategies)
   - When default thresholds don't fit your project
3. **Optional**:
   - Fine-tuning for your project's specific needs

### Versioning Your Configuration

**Track in git**:
```bash
git add .codeindex.yaml
git commit -m "config: update to v0.5.0 schema"
```

**Document customizations**:
```yaml
# .codeindex.yaml
version: 1

# Custom thresholds for large monorepo project
symbols:
  adaptive_symbols:
    enabled: true
    max_symbols: 200    # Increased from default 150
```

### Testing Configuration Changes

```bash
# 1. Validate syntax
codeindex init --validate    # (future command)

# 2. Test on single directory
codeindex scan src/core --dry-run

# 3. Compare before/after
diff README_AI.md.old README_AI.md

# 4. Roll out gradually
codeindex scan src/core      # Test one module
codeindex scan-all           # Full project
```

---

## FAQ

**Q: Do I need to update my config when upgrading codeindex?**

A: No. All versions are 100% backward compatible. Update only if you want new features.

**Q: What happens if I use old config with new codeindex version?**

A: It works perfectly. New features use default values.

**Q: How do I know which config version I have?**

A: Check `version: N` field in `.codeindex.yaml`. If missing, it's v0.1.0 format.

**Q: Will future versions break my config?**

A: Only if there's a major version bump (v2.0.0). We'll provide migration tools.

**Q: Should I enable adaptive symbols?**

A: For new projects: Yes. For existing projects: Test first, benefits are significant for large files.

---

## Related Documentation

- **Configuration Reference**: `docs/guides/configuration.md`
- **Migration Tools**: `codeindex config upgrade` (future)
- **Changelog**: `CHANGELOG.md`
- **Upgrade Guide**: `docs/guides/upgrading.md` (future)

---

**Last Updated**: 2026-02-03
**Config Schema Version**: 1
**codeindex Version**: v0.5.0-beta1
