# Scripts Directory

Utility scripts and tools for codeindex development and maintenance.

---

## 📁 Structure

```
scripts/
├── README.md           # This file
├── legacy/             # Archived experimental code
└── hooks/              # Git hook scripts (optional)
```

---

## 🗂️ Contents

### legacy/

Experimental code from early development (moved during Phase 1 cleanup).

**Files**:
- `hierarchical_strategy.py` - Early hierarchical indexing experiments
- `PROJECT_INDEX.json` - Sample project index output

**Purpose**: Archive useful ideas that shouldn't clutter the root directory.

See: [legacy/README.md](legacy/README.md)

### hooks/

Git hook scripts for project automation (if present).

See: [docs/guides/git-hooks-integration.md](../docs/guides/git-hooks-integration.md)

---

## 🛠️ Adding New Scripts

When adding utility scripts:

1. **Choose appropriate location**:
   - Development tools → `scripts/dev/`
   - Release tools → `scripts/release/`
   - One-off utilities → `scripts/utils/`

2. **Document in this README**

3. **Add usage examples**

4. **Make executable** (if shell script):
   ```bash
   chmod +x scripts/my-script.sh
   ```

---

## 📝 Usage Examples

Scripts are typically run from the project root:

```bash
# Example: Run a Python utility script
python scripts/utils/my-tool.py

# Example: Run a shell script
./scripts/dev/setup.sh
```

---

## 🔗 Related

- **Development Guide**: [CLAUDE.md](../CLAUDE.md)
- **Git Hooks**: [docs/guides/git-hooks-integration.md](../docs/guides/git-hooks-integration.md)

---

**Last Updated**: 2026-02-07
