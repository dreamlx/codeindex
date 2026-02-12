# Epic 12: Single File Parse Command - Task Summary (SIMPLIFIED)

**Epic ID**: 12
**Created**: 2026-02-07
**Status**: 🟢 Ready to Start
**Priority**: P0 (Foundational capability)
**Version**: SIMPLIFIED (2-3 days, 20 tests, 1 Story)

---

## 🎯 Quick Overview

**Goal**: 添加 `codeindex parse <file>` 命令，提供单文件解析功能，通过 CLI 输出 JSON 格式的 ParseResult。

**Why**:
- 功能完整性（AST 解析工具的基础能力）
- 松耦合集成（CLI > Python API）
- 工具链友好（LoomGraph 等工具可独立调用）

**Estimated Duration**: 2-3 days (Simplified from 3-5 days)

---

## 📊 Simplified Scope

### Changes from Original Design

| 维度 | 原设计 | 简化版 | 节省 |
|------|--------|--------|------|
| **Story 数量** | 3 个 | 1 个 | -2 |
| **测试数量** | 38 个 | 20 个 | -18 |
| **估算时长** | 3-5 天 | 2-3 天 | -2 天 |
| **新增代码** | ~200 行 | ~100 行 | -50% |
| **Console 输出** | ✅ | ❌ (推迟) | - |

### Removed Features (Out of Scope)

1. ❌ **Console Output Format** (`--output console`)
   - Reason: LoomGraph 只需要 JSON，Console 是"nice to have"
   - Future: v0.13.1 或 v0.14.0

2. ❌ **Story 12.2** (JSON Validation as separate story)
   - Reason: JSON 验证是核心功能的一部分，不应该独立
   - Merged: JSON 验证测试合并到 Story 12.1

3. ❌ **Story 12.3** (Documentation as separate story)
   - Reason: 文档是开发的最后一步，不需要独立 Story
   - Merged: 文档更新作为 Story 12.1 的 Acceptance Criteria

---

## 📋 Single Story Breakdown

### Story 12.1: Parse Command with JSON Output (2-3 days)

**Tasks**:
1. ✅ 创建测试结构（fixtures + test_cli_parse.py）
2. 🔴 编写 20 个失败测试（Red phase）
3. 🔴 实现 `src/codeindex/cli_parse.py` 核心逻辑 (~100 lines)
4. 🔴 集成到 `src/codeindex/cli.py` (1 line)
5. 🔴 运行测试（期望 20 个 PASS）
6. 🔴 Refactor + 代码审查
7. 🔴 文档更新（README + CLAUDE.md + examples）
8. 🔴 集成测试 + 发布准备

**Tests**: 20 tests
- Basic Functionality: 5 tests (Python/PHP/Java + help + version)
- JSON Format Validation: 5 tests (schema + fields + round-trip)
- Error Handling: 5 tests (file not found + unsupported + parse failure + empty + permission)
- Framework Features: 3 tests (ThinkPHP routes + Spring annotations + inheritance)
- Performance: 2 tests (small file <0.1s + large file <1s)

**Deliverables**:
- `src/codeindex/cli_parse.py` (~100 lines)
- `tests/test_cli_parse.py` (~200 lines)
- Test fixtures (Python, PHP, Java files)
- README.md 更新
- CLAUDE.md 更新
- `examples/loomgraph-integration.sh`

---

## 🧪 TDD Workflow Summary

### Day 1: Red + Green (5-6 hours)

**Morning (2-3 hours): Red Phase**
```bash
# 1. 环境准备
git checkout develop
git pull
git checkout -b feature/epic12-single-file-parse

# 2. 创建测试结构
mkdir -p tests/fixtures/cli_parse
touch tests/test_cli_parse.py

# 3. 创建 fixtures（8 个文件）
# simple.py, complete.py, simple.php, Controller.php
# Simple.java, Service.java, broken.py, unsupported.txt

# 4. 编写 20 个失败测试
vim tests/test_cli_parse.py

# 5. 运行测试（期望全部 FAIL）
pytest tests/test_cli_parse.py -v
# Expected: 20 FAILED
```

**Afternoon (3 hours): Green Phase**
```bash
# 6. 创建 cli_parse.py
touch src/codeindex/cli_parse.py

# 7. 实现核心逻辑 (~100 lines)
vim src/codeindex/cli_parse.py

# 8. 集成到 cli.py (1 line)
vim src/codeindex/cli.py

# 9. 运行测试（期望全部 PASS）
pytest tests/test_cli_parse.py -v
# Expected: 20 PASSED

# 10. Commit
git add .
git commit -m "feat(cli): add parse command with JSON output"
```

---

### Day 2: Refactor + Documentation (4 hours)

**Morning (2 hours): Refactor**
```bash
# 11. 代码审查
ruff check src/codeindex/cli_parse.py
pytest tests/test_cli_parse.py --cov=src/codeindex/cli_parse --cov-report=term-missing
# Expected: ≥ 90% coverage

# 12. 优化实现（如果需要）

# 13. Commit (if refactored)
git commit -am "refactor(cli): optimize parse command"
```

**Afternoon (2 hours): Documentation**
```bash
# 14. 更新文档
vim README.md CLAUDE.md

# 15. 创建示例脚本
vim examples/loomgraph-integration.sh
chmod +x examples/loomgraph-integration.sh

# 16. 验证示例可运行
bash examples/loomgraph-integration.sh

# 17. Commit
git commit -am "docs: add parse command documentation"
```

---

### Day 3: Integration & Release (4 hours)

**Morning (2 hours): Integration Testing**
```bash
# 18. 完整回归测试
pytest  # 全量测试

# 19. 性能基准测试
time codeindex parse tests/fixtures/cli_parse/simple.py

# 20. 错误处理验证
codeindex parse nonexistent.py  # Exit 1
codeindex parse tests/fixtures/cli_parse/unsupported.txt  # Exit 2

# 21. 多语言验证
codeindex parse tests/fixtures/cli_parse/simple.py | jq '.language'
```

**Afternoon (2 hours): Release**
```bash
# 22. 更新 CHANGELOG.md + ROADMAP.md
vim CHANGELOG.md docs/planning/ROADMAP.md

# 23. 更新版本号
sed -i '' 's/version = "0.12.0"/version = "0.13.0"/' pyproject.toml

# 24. 创建 PR
git push origin feature/epic12-single-file-parse
gh pr create --title "feat: Single File Parse Command (Epic 12 - Simplified)"
```

---

## 📝 Key Files Summary

### New Files (4 files)
```
src/codeindex/
└── cli_parse.py           (~100 lines) ✨ NEW

tests/
├── test_cli_parse.py      (~200 lines) ✨ NEW
└── fixtures/cli_parse/    (8 files) ✨ NEW
    ├── simple.py
    ├── complete.py
    ├── simple.php
    ├── Controller.php
    ├── Simple.java
    ├── Service.java
    ├── broken.py
    └── unsupported.txt

examples/
└── loomgraph-integration.sh  ✨ NEW
```

### Modified Files (5 files)
```
src/codeindex/
└── cli.py                 (1 line change) ✨ MODIFIED

docs/
├── README.md              (add parse section) ✨ MODIFIED
├── CLAUDE.md              (add parse guide) ✨ MODIFIED
├── CHANGELOG.md           (add v0.13.0 entry) ✨ MODIFIED
└── planning/ROADMAP.md    (add Epic 12) ✨ MODIFIED
```

### Reused Components
```
src/codeindex/
├── parser.py              → detect_language(), parse_file()
└── data_types.py          → ParseResult.to_dict()

src/codeindex/extractors/
├── thinkphp.py            → ThinkPHP route extraction
└── spring.py              → Spring route extraction
```

---

## 🎯 Success Criteria Checklist

### Functional (Core)
- [ ] `codeindex parse <file>` 命令可用
- [ ] 支持 Python、PHP、Java 文件
- [ ] JSON 输出格式正确（包含所有 ParseResult 字段）
- [ ] 错误处理完善（3 种错误码）

### Quality (Tests)
- [ ] 20 测试通过
- [ ] 测试覆盖率 ≥ 90%
- [ ] 代码审查通过（ruff check）
- [ ] 性能达标（<0.1s 小文件，<1s 大文件）

### Documentation (Completeness)
- [ ] README.md 更新
- [ ] CLAUDE.md 更新
- [ ] CLI help text 完整
- [ ] 示例脚本可运行

### Integration (Compatibility)
- [ ] 与现有命令兼容
- [ ] 不破坏现有功能
- [ ] LoomGraph 集成验证

---

## 🚀 Ready to Start?

### First Command

```bash
# Branch setup
git checkout develop
git pull origin develop
git checkout -b feature/epic12-single-file-parse

# Start Day 1 Morning tasks
mkdir -p tests/fixtures/cli_parse
touch tests/test_cli_parse.py

# Create fixtures (follow checklist)
# Then write 20 failing tests
```

### Next Steps

1. 按照 `epic12-development-checklist.md` 执行 TDD 流程
2. 每个 Green phase 完成后立即 commit
3. 每日更新 checklist 进度
4. 最后完成文档和 PR

---

## 📚 Reference Documents

- **Epic Plan**: `docs/planning/active/epic12-single-file-parse.md`
- **Development Checklist**: `docs/planning/active/epic12-development-checklist.md` (MAIN GUIDE)
- **Design Philosophy**: Serena memory `design_philosophy`
- **Multi-Language Workflow**: `docs/development/multi-language-support-workflow.md`

---

## 💡 Why Simplified?

**Original Design Issues**:
1. Story 12.2 (JSON Validation) 不应该独立 → 合并到 Story 12.1
2. Console 输出不是 MVP → 推迟到 v0.13.1
3. 测试数量过多（38 个）→ 简化到 20 个

**Simplified Benefits**:
- ✅ 更聚焦核心功能（JSON 输出）
- ✅ 更快交付（2-3 天 vs 3-5 天）
- ✅ 避免过度设计（移除非必需功能）
- ✅ TDD 更简洁（一次 Red-Green-Refactor 循环）

---

**Status**: 🟢 Ready to Start
**Next Action**: Execute Day 1 Morning tasks from development checklist
**Estimated Completion**: 2026-02-09 (2-3 days)
