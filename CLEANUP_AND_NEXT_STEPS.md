# 文档整理与下一步开发计划

**日期**: 2026-02-06
**当前版本**: v0.11.0
**分析人**: Claude Code

---

## 📊 当前状态总结

### 版本状态
- **最新版本**: v0.11.0 (2026-02-06)
- **最新功能**: Lazy Loading for Language Parsers (架构优化)
- **测试状态**: 783 tests passing, 3 skipped
- **已支持语言**: Python, PHP, Java (3 languages)

### 已完成 Epic
- ✅ Epic 2: Adaptive Symbol Extraction (v0.2.0)
- ✅ Epic 3: Tech Debt Analysis (v0.3.0)
- ✅ Epic 4: Code Refactoring + KISS (v0.3.0-v0.4.0)
- ✅ Epic 6 P3.1: Git Hooks Integration (v0.5.0)
- ✅ Epic 9: AI-Powered Docstring Extraction (v0.6.0)
- ✅ Epic 7: Java Language Support (v0.7.0-v0.8.0)
- ✅ Epic 10 Part 1-2: LoomGraph Integration - Python + PHP (v0.9.0-v0.10.0)
- ✅ Epic JSON Output: JSON 输出支持 (v0.9.0-v0.10.0，作为 Epic 10 的一部分)

---

## 🗂️ 第一部分：文档整理计划

### 问题诊断
根目录累积了大量临时开发文件（38 个 .md 文件），影响项目可维护性：
- Epic 7 相关临时文件（9 个）
- 文档摘要文件（5 个）
- 项目索引临时文件（3 个）
- 发布状态文件（2 个）
- 其他开发临时文件

### 整理方案

#### 1. 归档根目录临时文件

```bash
# 创建归档目录
mkdir -p docs/archive/{summaries,project-index,releases,planning}
mkdir -p docs/planning/completed/epic7-java-support
mkdir -p docs/planning/completed/epic-json-output

# Epic 7 相关文件 → docs/planning/completed/epic7-java-support/
mv EPIC7_CURRENT_STATUS.md docs/planning/completed/epic7-java-support/
mv EPIC7_DESIGN_PHILOSOPHY_RETHINK.md docs/planning/completed/epic7-java-support/
mv EPIC7_GREEN_COMPLETE.md docs/planning/completed/epic7-java-support/
mv EPIC7_JAVA_ROADMAP.md docs/planning/completed/epic7-java-support/
mv EPIC7_PERFORMANCE_CORRECTION.md docs/planning/completed/epic7-java-support/
mv EPIC7_REFACTOR_COMPLETE.md docs/planning/completed/epic7-java-support/
mv EPIC7_STORY_7.1.2-7.1.4_DESIGN.md docs/planning/completed/epic7-java-support/
mv EPIC7_STORY_7.1.4_PERFORMANCE_RETHINK.md docs/planning/completed/epic7-java-support/
mv EPIC7_TEST_STRATEGY.md docs/planning/completed/epic7-java-support/

# 文档摘要文件 → docs/archive/summaries/
mv DOCUMENTATION_REORGANIZATION.md docs/archive/summaries/
mv DOCUMENTATION_REVIEW.md docs/archive/summaries/
mv DOCUMENTATION_SUMMARY.md docs/archive/summaries/
mv DOCUMENTATION_UPDATE_SUMMARY.md docs/archive/summaries/
mv DEVELOPMENT_PLAN_SUMMARY.md docs/archive/summaries/

# 项目索引临时文件 → docs/archive/project-index/
mv PROJECT_INDEX.md docs/archive/project-index/
mv PROJECT_INDEX_KISS.md docs/archive/project-index/
mv PROJECT_INDEX_TEST.md docs/archive/project-index/

# 发布状态文件 → docs/archive/releases/
mv RELEASE_v0.7.0_COMPLETE.md docs/archive/releases/
mv RELEASE_v0.7.0_STATUS.md docs/archive/releases/

# 开发计划临时文件 → docs/archive/planning/
mv BRANCH_STATUS.md docs/archive/planning/
mv IMPROVEMENT_PLAN.md docs/archive/planning/
```

#### 2. 整合独立指南文件到 docs/

```bash
# 这些文件内容应整合到现有文档中，然后删除或归档

# GIT_COMMIT_GUIDE.md → 整合到 docs/development/gitflow-workflow.md
# PACKAGE_NAMING.md + PYPI_QUICKSTART.md → 整合到 docs/development/pypi-release-guide.md
# CLAUDE_CODE_INTEGRATION_UPDATE.md → 整合到 docs/guides/claude-code-integration.md
```

#### 3. 归档已完成的 Active Epic

```bash
# Epic 7 已完成，移动到 completed/
mv docs/planning/active/epic7-java-support.md \
   docs/planning/completed/epic7-java-support/plan.md
mv docs/planning/active/epic7-story-breakdown.md \
   docs/planning/completed/epic7-java-support/story-breakdown.md

# Epic JSON Output 已完成（作为 Epic 10 的一部分）
mv docs/planning/active/epic-json-output.md \
   docs/planning/completed/epic-json-output/plan.md
```

#### 4. 保留的核心文件

根目录应只保留以下核心文档：
- ✅ README.md - 项目概览
- ✅ README_AI.md - AI 生成的项目索引
- ✅ CLAUDE.md - 开发者指南（Claude Code）
- ✅ CHANGELOG.md - 版本变更记录
- ✅ PROJECT_SYMBOLS.md - 全局符号索引
- ✅ RELEASE_NOTES_v*.md - 版本发布说明

---

## 🎯 第二部分：下一步开发建议

### ROADMAP 状态分析

**问题**:
- ROADMAP.md 计划的 v0.11.0 内容（TypeScript/Go/Rust support）尚未实现
- 实际 v0.11.0 实现的是 Lazy Loading 架构优化
- 需要调整路线图以反映实际进度

### 开发优先级分析

基于以下因素评估：
1. **用户价值** - 功能对用户的实际价值
2. **技术成熟度** - 现有架构的支持程度
3. **工作量** - 预计开发时间
4. **战略重要性** - 对项目长期发展的影响

### 推荐方案：v0.12.0 开发计划

#### 🥇 推荐选项 1: Epic 10 Part 3 - Java LoomGraph

**优先级**: P0 ⭐⭐⭐⭐⭐

**理由**:
1. **完成 LoomGraph 三语言支持** - Python ✅, PHP ✅, Java 待完成
2. **Epic 10 的自然延续** - 保持开发连贯性
3. **技术债务最小** - 复用已有的 Java parser 和 LoomGraph 架构
4. **快速交付** - 预计 1-2 天完成

**Scope**:
- Story 10.1.3: Java inheritance extraction
  - `extends` relationships (single inheritance)
  - `implements` relationships (multiple interfaces)
  - Generic type handling (strip type parameters like `<T>`)
  - Nested class inheritance with full paths

**Success Criteria**:
- [ ] Extract Java inheritance relationships (extends + implements)
- [ ] JSON output compatible with LoomGraph format
- [ ] Consistent with Python/PHP implementation
- [ ] ~20-25 new tests

**预计工作量**: 1-2 days
**目标版本**: v0.12.0

---

#### 🥇 推荐选项 2: Epic 11 - Call Relationship Extraction

**优先级**: P1 ⭐⭐⭐⭐⭐

**理由**:
1. **LoomGraph 核心需求** - 函数调用图是知识图谱的关键节点
2. **差异化优势** - 很少有工具能准确提取调用关系
3. **技术挑战适中** - 类似于 inheritance extraction
4. **支持三语言** - Python, PHP, Java 同步开发

**Scope**:
- Story 11.1: Python call extraction
  - Function calls: `foo()`, `module.func()`
  - Method calls: `obj.method()`, `self.method()`
  - Constructor calls: `MyClass()`

- Story 11.2: PHP call extraction
  - Function calls: `foo()`, `\Namespace\func()`
  - Method calls: `$obj->method()`, `self::staticMethod()`
  - Constructor calls: `new MyClass()`

- Story 11.3: Java call extraction
  - Method calls: `obj.method()`, `this.method()`
  - Static calls: `Class.staticMethod()`
  - Constructor calls: `new MyClass()`

- Story 11.4: LoomGraph Integration
  - Add `calls` field to `ParseResult`
  - `Call` dataclass: caller, callee, line_number, is_static
  - JSON serialization

**Success Criteria**:
- [ ] Extract function/method calls from all 3 languages
- [ ] Distinguish internal vs external calls
- [ ] Track call locations (line numbers)
- [ ] JSON output compatible with LoomGraph

**预计工作量**: 4-6 days
**目标版本**: v0.12.0

---

### 🎯 最终推荐：v0.12.0 组合方案

**建议组合**: Epic 10 Part 3 (快速完成) + Epic 11 (高价值)

**开发顺序**:
1. **Week 1, Day 1-2**: Epic 10 Part 3 - Java LoomGraph
   - 完成 LoomGraph 三语言全覆盖
   - 快速胜利，提升士气

2. **Week 1-2, Day 3-8**: Epic 11 - Call Relationship Extraction
   - 核心知识图谱功能
   - 技术挑战适中

**版本目标**:
- **v0.12.0**: Epic 10 Part 3 + Epic 11
- **预计发布**: 2026-02-13 (1-2 weeks)
- **预计新增测试**: ~90-100 tests

---

### 备选方案

#### 备选 1: Epic 8 - TypeScript Language Support

如果团队希望优先扩展语言支持：

**Scope**:
- TypeScript parser (tree-sitter-typescript)
- JSDoc extraction (AI-powered)
- React component detection
- TypeScript type annotations
- LoomGraph Integration (inheritance + import alias)

**预计工作量**: 3-5 days
**优先级**: P0 (Multi-language foundation)

#### 备选 2: Framework Routes - FastAPI/Django/Laravel

如果希望完善 framework intelligence：

**Scope**:
- FastAPI route extraction (Python)
- Django URL extraction (Python)
- Laravel route extraction (PHP)

**预计工作量**: 3-4 days
**优先级**: P1 (Framework intelligence)

---

## 📋 决策矩阵

| 选项 | 用户价值 | 技术成熟度 | 工作量 | 优先级 | 推荐度 |
|------|---------|-----------|-------|--------|--------|
| **Epic 10 Part 3** (Java LoomGraph) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1-2 days | P0 | ⭐⭐⭐⭐⭐ |
| **Epic 11** (Call Relationships) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4-6 days | P1 | ⭐⭐⭐⭐⭐ |
| Epic 8 (TypeScript) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 3-5 days | P0 | ⭐⭐⭐⭐ |
| Framework Routes | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 3-4 days | P1 | ⭐⭐⭐⭐ |

---

## 🚀 行动计划

### Phase 1: 文档整理 (优先执行)

**预计时间**: 1-2 hours

1. **执行文档归档脚本** (见上文 Section 1)
2. **更新 docs/planning/README.md**
   - 移除 epic7, epic-json-output 从 Active 列表
   - 添加到 Completed 列表
3. **更新 ROADMAP.md**
   - 标记 v0.11.0 为已完成（Lazy Loading）
   - 调整 v0.12.0 计划为 Epic 10 Part 3 + Epic 11
   - 推迟 TypeScript/Go/Rust 到 v0.13.0+
4. **重新生成 README_AI.md**
   ```bash
   codeindex scan-all --fallback
   ```

### Phase 2: v0.12.0 开发 (紧接着执行)

**预计时间**: 1-2 weeks

#### Step 1: 创建 Epic 10 Part 3 计划文档
```bash
# 创建 epic 计划
vim docs/planning/active/epic10-part3-java-loomgraph.md
```

#### Step 2: TDD 开发 - Java Inheritance
```bash
# 1. 创建 feature 分支
git checkout -b feature/epic10-part3-java-inheritance

# 2. 编写测试（Red）
vim tests/test_java_inheritance.py

# 3. 实现功能（Green）
vim src/codeindex/java_parser.py

# 4. 运行测试
pytest tests/test_java_inheritance.py -v

# 5. 重构（Refactor）
# 优化代码，保持测试通过
```

#### Step 3: 创建 Epic 11 计划文档
```bash
vim docs/planning/active/epic11-call-relationships.md
```

#### Step 4: TDD 开发 - Call Extraction
```bash
# 1. 创建 feature 分支
git checkout -b feature/epic11-call-relationships

# 2. 按语言顺序开发
# - Python call extraction (2 days)
# - PHP call extraction (1.5 days)
# - Java call extraction (1.5 days)
# - LoomGraph integration (1 day)
```

### Phase 3: 发布 v0.12.0

```bash
# 1. 合并所有 feature 分支到 develop
git checkout develop
git merge feature/epic10-part3-java-inheritance
git merge feature/epic11-call-relationships

# 2. 更新版本号
vim src/codeindex/__init__.py  # __version__ = "0.12.0"

# 3. 更新 CHANGELOG.md
vim CHANGELOG.md

# 4. 创建 Release Notes
vim RELEASE_NOTES_v0.12.0.md

# 5. 运行完整测试套件
pytest -v

# 6. 合并到 master 并打 tag
git checkout master
git merge develop
git tag v0.12.0
git push origin master --tags

# 7. 发布到 PyPI
python -m build
twine upload dist/*
```

---

## 📝 后续版本规划

### v0.13.0 (预计 2026-03)
- Epic 8: TypeScript Language Support
- JSDoc AI extraction
- React component detection

### v0.14.0 (预计 2026-04)
- Framework Routes: FastAPI, Django, Laravel
- Go Language Support (基础)

### v0.15.0+ (预计 2026-05+)
- Rust Language Support
- Real-time Indexing (Watch mode)
- LSP Server

---

## ✅ 检查清单

### 文档整理
- [ ] 归档根目录临时文件
- [ ] 整合独立指南到 docs/
- [ ] 移动已完成 Epic 到 completed/
- [ ] 更新 docs/planning/README.md
- [ ] 更新 ROADMAP.md
- [ ] 重新生成 README_AI.md

### v0.12.0 开发
- [ ] 创建 Epic 10 Part 3 计划文档
- [ ] 实现 Java inheritance extraction (TDD)
- [ ] 创建 Epic 11 计划文档
- [ ] 实现 Python call extraction (TDD)
- [ ] 实现 PHP call extraction (TDD)
- [ ] 实现 Java call extraction (TDD)
- [ ] LoomGraph integration testing
- [ ] 更新文档和 CHANGELOG
- [ ] 发布 v0.12.0

---

**状态**: 待执行
**负责人**: @dreamlx
**创建日期**: 2026-02-06
**最后更新**: 2026-02-06
