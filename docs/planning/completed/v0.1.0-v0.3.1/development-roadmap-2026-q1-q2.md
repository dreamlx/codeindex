# codeindex Development Roadmap: 2026 Q1-Q2

**Created**: 2026-02-01
**Status**: 🎯 Active Planning
**Current Version**: v0.3.2
**Target Versions**: v0.4.0 (Feb), v0.5.0 (Apr), v0.6.0 (Jun)

---

## 📊 Executive Summary

### Strategic Direction

**From**: 静态代码索引工具 (Static code indexing tool)
**To**: AI 算力驱动的代码演化洞察平台 (AI compute-driven code evolution platform)

### Three Parallel Tracks

```
Track 1: 短期改进 (v0.4.0 - 4周)
├── PHP 项目反馈修复
├── 索引质量提升
└── 用户体验优化

Track 2: 战略基础设施 (v0.5.0 - 8周)
├── Epic 6: Multi-agent Orchestrator
└── 性能突破（10-100倍提速）

Track 3: 智能分支管理 (v0.6.0 - 8周)
├── Epic 5: Intelligent Branch Management
└── 基于 Epic 6 的 multi-agent 能力
```

---

## 🎯 Current Status (v0.3.2)

### ✅ Completed Features

| Feature | Version | Status |
|---------|---------|--------|
| CLI 模块化拆分 | v0.3.1 | ✅ 1062行→31行 |
| 技术债务分析 | v0.3.0 | ✅ tech-debt 命令 |
| 多轮对话处理 | v0.3.0 | ✅ 超大文件支持 |
| 自适应符号提取 | v0.2.0 | ✅ 5-150个符号 |
| 全局符号索引 | v0.1.2 | ✅ PROJECT_SYMBOLS.md |
| AI 增强扫描 | v0.1.2 | ✅ scan-all 两阶段 |

### ❌ Known Issues (From PHP Project Feedback)

| Issue | Severity | Impact |
|-------|----------|--------|
| PROJECT_INDEX.md 描述通用化 | 🔴 HIGH | 无业务语义，难以理解 |
| README_AI.md 子目录描述重复 | 🔴 HIGH | "Module directory" 无区分度 |
| PROJECT_SYMBOLS.md 过大 | 🟡 MEDIUM | 348KB，信息密度低 |
| 缺少业务语义提取 | 🔴 HIGH | 无法理解"干什么" |
| 增量更新缺失 | 🟡 MEDIUM | 每次全量扫描浪费时间 |
| PHPDoc 提取不全 | 🟢 LOW | 缺少描述信息 |

---

## 📅 Release Timeline

### v0.4.0: Quality & Experience (4 weeks, Feb 2026)

**主题**: 修复 PHP 反馈 + 索引质量提升

**发布日期**: 2026-02-28
**类型**: Feature + Bugfix

#### Features

**F1: 业务语义提取增强** (P0 - Critical)
- 问题：描述过于通用（"Business module"、"Module directory"）
- 方案：AI 提取业务语义，生成有意义的描述
- 示例：
  ```
  Before: "Controller module"
  After:  "用户认证和权限管理控制器"
  ```

**F2: 增量更新机制** (P1 - High)
- 问题：每次全量扫描浪费时间
- 方案：基于 git diff 只扫描变化的目录
- CLI: `codeindex scan-all --incremental`

**F3: PROJECT_SYMBOLS 优化** (P1 - High)
- 问题：348KB 文件，信息密度低
- 方案：
  - 分层索引（核心符号 vs 详细符号）
  - 添加符号描述（从 docstring 提取）
  - 支持过滤（只显示 public API）

**F4: PHPDoc 提取** (P2 - Medium)
- 问题：PHP 项目缺少方法描述
- 方案：解析 PHPDoc 注释，提取 @param、@return

**F5: 版本号同步** (P0 - Critical Fix)
- 问题：pyproject.toml 版本号未更新
- 方案：自动化脚本确保版本一致性

#### Stories

- **Story 4.4**: 业务语义提取 (5 days)
  - Task 4.4.1: AI prompt 优化（提取业务含义）
  - Task 4.4.2: 目录描述生成器
  - Task 4.4.3: 测试和验证

- **Story 4.5**: 增量更新机制 (5 days)
  - Task 4.5.1: Git diff 分析器
  - Task 4.5.2: 智能目录选择
  - Task 4.5.3: CLI 集成

- **Story 4.6**: PROJECT_SYMBOLS 重构 (3 days)
  - Task 4.6.1: 分层索引设计
  - Task 4.6.2: 符号描述提取
  - Task 4.6.3: 过滤和优化

- **Story 4.7**: PHPDoc 支持 (2 days)
  - Task 4.7.1: PHPDoc 解析器
  - Task 4.7.2: 集成到 PHP parser

**Timeline**:
- Week 1: Story 4.4 + 4.5
- Week 2: Story 4.6 + 4.7
- Week 3: 集成测试
- Week 4: Bug 修复 + 发布

**Success Criteria**:
- ✅ PHP 项目索引质量评分从 ⭐⭐ 提升到 ⭐⭐⭐⭐
- ✅ 增量扫描速度提升 80%+
- ✅ PROJECT_SYMBOLS 文件大小减少 50%+
- ✅ 所有已知 issues 修复

---

### v0.5.0: Multi-agent Infrastructure (8 weeks, Apr 2026)

**主题**: AI 算力调度平台

**发布日期**: 2026-04-30
**类型**: Major Feature (Epic 6)

#### Epic 6: Multi-agent Orchestrator

**Vision**: 利用 headless Claude/Opencode 并发能力，将代码分析速度提升 10-100 倍

**Phase 1: MVP (4 weeks, Mar 2026)**

- **Week 1**: Story 6.1 - Orchestrator Skill Foundation
  - Orchestrator skill 模板
  - Task 分解逻辑
  - 并发 worker 启动（2-5个）

- **Week 2**: Story 6.2 - Worker Skill Implementation
  - Worker skill 模板
  - 相似度分析逻辑
  - 结构化输出

- **Week 3**: Story 6.3 - Python Integration
  - Config 扩展 (ai.mode = "orchestrator")
  - AIInvoker 改造
  - CLI 集成

- **Week 4**: Story 6.4 - MVP Validation
  - 性能测试（1 vs 5 vs 10 workers）
  - 质量验证
  - Go/No-Go 决策

**MVP Success Criteria**:
- ✅ 10 workers 相比 1 worker 速度提升 ≥ 5x
- ✅ 质量不降低（≥85% 准确率）
- ✅ 成本增加 < 15x

**Phase 2: Production (4 weeks, Apr 2026)** - If MVP succeeds

- **Week 5-6**: 优化和增强
  - Story 6.5: Smart task partitioning
  - Story 6.6: Caching mechanism
  - Story 6.7: Mixed backend (Claude + Opencode)

- **Week 7-8**: 稳定性和发布
  - Story 6.8: Advanced error handling
  - Story 6.9: Performance tuning
  - Story 6.10: Documentation + Release

**Production Success Criteria**:
- ✅ 50+ workers 并发稳定运行
- ✅ 速度提升 30x+
- ✅ 支持混合 backend（Claude + Opencode）
- ✅ 缓存命中率 > 60%

#### Configuration Example

```yaml
# .codeindex.yaml v0.5.0
ai:
  mode: "orchestrator"  # New!
  command: "claude"

  orchestrator:
    skill: "codeindex-orchestrator"
    max_workers: 20
    strategy: "dynamic"

  worker:
    skill: "code-analyzer-worker"
    timeout: 300
    retry: 3

  cache:
    enabled: true
    backend: "sqlite"
```

---

### v0.6.0: Intelligent Branch Management (8 weeks, Jun 2026)

**主题**: 版本地狱治理（基于 Epic 6 的 multi-agent 能力）

**发布日期**: 2026-06-30
**类型**: Major Feature (Epic 5, revised)

#### Epic 5: Intelligent Branch Management (Revised)

**Vision**: 利用 multi-agent 并发能力解决"版本地狱"问题

**Features**:

**F1: Git History Analysis** (Week 1-2)
- Story 5.1.1: Git 历史分析器
- Story 5.1.2: 分支对比引擎

**F2: Multi-agent Duplicate Detection** (Week 3-5)
- Story 5.2.1: 增量重复检测（commit 级别）
- Story 5.2.2: 跨分支重复检测（基于 Epic 6）
  - 使用 50+ workers 并发分析
  - 1000+ 函数对比，10分钟完成

**F3: Evolution Insights** (Week 6-7)
- Story 5.3.1: 代码演化轨迹追踪
- Story 5.3.2: 分叉代价估算

**F4: Automation** (Week 8)
- Story 5.4.1: 合并建议生成
- Story 5.4.2: 自动 PR 创建（可选）

**Success Criteria**:
- ✅ 2个分支（各1000函数）对比，< 15分钟
- ✅ 准确率 > 90%
- ✅ 自动生成可执行的合并建议

#### Use Case Example

```bash
# 检测 feature/a 和 feature/b 的重复代码
codeindex find-duplicates \
  --branch feature/a \
  --branch feature/b \
  --workers 50

# 输出示例：
# 🔍 Analyzing 2 branches with 50 workers...
# ⚡ Parallel execution: 1,250 function pairs analyzed in 12 minutes
# 📊 Found 23 duplicate function pairs (avg similarity: 0.82)
# 💡 Recommendation: Extract 5 common modules to reduce 80% duplication
# 📝 Report saved to: branch_comparison_report.md
```

---

## 🗓️ Detailed Schedule

### February 2026 (v0.4.0)

| Week | Focus | Deliverables |
|------|-------|-------------|
| Week 1 (Feb 3-7) | Story 4.4 + 4.5 | 业务语义提取 + 增量更新 |
| Week 2 (Feb 10-14) | Story 4.6 + 4.7 | PROJECT_SYMBOLS 优化 + PHPDoc |
| Week 3 (Feb 17-21) | 集成测试 | 所有功能端到端测试 |
| Week 4 (Feb 24-28) | Bug 修复 + 发布 | v0.4.0 Release |

### March 2026 (Epic 6 MVP)

| Week | Focus | Deliverables |
|------|-------|-------------|
| Week 5 (Mar 3-7) | Story 6.1 | Orchestrator Skill |
| Week 6 (Mar 10-14) | Story 6.2 | Worker Skill |
| Week 7 (Mar 17-21) | Story 6.3 | Python Integration |
| Week 8 (Mar 24-28) | Story 6.4 | MVP Validation + Decision |

**Decision Point (Mar 28)**: Go/No-Go on Phase 2

### April 2026 (Epic 6 Production or Pivot)

**If MVP succeeds**:

| Week | Focus | Deliverables |
|------|-------|-------------|
| Week 9 (Apr 1-4) | Story 6.5 + 6.6 | Smart partitioning + Caching |
| Week 10 (Apr 7-11) | Story 6.7 | Mixed backend |
| Week 11 (Apr 14-18) | Story 6.8 + 6.9 | Error handling + Performance |
| Week 12 (Apr 21-25) | Story 6.10 | Documentation + v0.5.0 Release |

**If MVP fails**: Pivot to alternative approach or Epic 5 Phase 1 (Git analysis)

### May-June 2026 (Epic 5)

| Week | Focus | Deliverables |
|------|-------|-------------|
| Week 13-14 | Story 5.1.1 + 5.1.2 | Git 历史分析 + 分支对比 |
| Week 15-17 | Story 5.2.1 + 5.2.2 | 重复检测（基于 Epic 6） |
| Week 18-19 | Story 5.3.1 + 5.3.2 | 演化洞察 |
| Week 20 | Story 5.4 | 自动化 + v0.6.0 Release |

---

## 📊 Priority Matrix

### P0: Critical (Must Fix Before Next Release)

| Issue | Epic/Story | Target | Days |
|-------|-----------|--------|------|
| 业务语义缺失 | Story 4.4 | v0.4.0 | 5 |
| 版本号同步 | Task 4.0.1 | v0.4.0 | 0.5 |
| PROJECT_INDEX 无区分度 | Story 4.4 | v0.4.0 | 5 |

### P1: High (Important for User Experience)

| Issue | Epic/Story | Target | Days |
|-------|-----------|--------|------|
| 增量更新缺失 | Story 4.5 | v0.4.0 | 5 |
| PROJECT_SYMBOLS 过大 | Story 4.6 | v0.4.0 | 3 |
| Multi-agent 基础设施 | Epic 6 MVP | v0.5.0 | 28 |

### P2: Medium (Nice to Have)

| Issue | Epic/Story | Target | Days |
|-------|-----------|--------|------|
| PHPDoc 提取 | Story 4.7 | v0.4.0 | 2 |
| use trait 解析 | Story 4.8 | v0.4.1 | 2 |
| AI 智能总结大文件 | Story 4.9 | v0.4.1 | 3 |

### P3: Low (Future Optimization)

| Issue | Epic/Story | Target | Days |
|-------|-----------|--------|------|
| 符号评分优化 | Story 4.10 | v0.5.0+ | 3 |
| low_quality_symbols 阈值 | Story 4.11 | v0.5.0+ | 1 |

---

## 🎯 Resource Allocation

### Development Team

假设：1名全职开发者（你 + Claude Code）

**Time Allocation**:
- **Feb (v0.4.0)**: 100% on 短期改进
- **Mar (Epic 6 MVP)**: 100% on Multi-agent infrastructure
- **Apr**:
  - If MVP succeeds: 100% on Epic 6 Production
  - If MVP fails: Re-evaluate, possibly 50% Epic 5 + 50% other improvements
- **May-Jun (Epic 5)**: 100% on Intelligent Branch Management

### Budget Allocation

**AI Compute Costs** (估算):

| Phase | Workers | Est. API Cost | Total |
|-------|---------|---------------|-------|
| v0.4.0 Development | 1 | $200/month | $200 |
| Epic 6 MVP Testing | 1-10 | $500/month | $500 |
| Epic 6 Production | 10-50 | $2000/month | $4000 |
| Epic 5 Development | 50+ | $3000/month | $6000 |

**Total Budget (Feb-Jun)**: ~$11,000 in AI compute

**Expected ROI**:
- Target customers: 上市公司
- Price point: $999-$4999/month
- Need: 3-10 customers to break even

---

## 🔗 Integration Points

### Between Epics

```
Epic 6 (Multi-agent) 是 Epic 5 (Branch Management) 的基础设施

Epic 6 提供:
- Orchestrator framework
- Worker pool management
- Parallel task execution

Epic 5 使用:
- 跨分支重复检测（需要并发分析1000+函数对）
- 大规模代码演化分析
- 实时合并冲突预测
```

### With External Systems

**Claude Code**:
- Skills integration (Orchestrator + Worker)
- Task tool for parallelism
- MCP servers for extended capabilities

**Git**:
- Git history analysis (Epic 5)
- Branch comparison (Epic 5)
- Incremental update (v0.4.0)

**PHP / Python Projects**:
- Language-specific parsers
- Tree-sitter integration
- PHPDoc / Python docstring extraction

---

## 📈 Success Metrics

### v0.4.0 Success Criteria

| Metric | Baseline | Target |
|--------|----------|--------|
| 索引质量评分 | ⭐⭐ | ⭐⭐⭐⭐ |
| 增量扫描速度 | N/A | 80%+ 提升 |
| PROJECT_SYMBOLS 大小 | 348KB | <175KB |
| 业务语义覆盖率 | 10% | 80%+ |

### v0.5.0 Success Criteria

| Metric | Baseline (v0.4.0) | Target |
|--------|-------------------|--------|
| 分析速度 (1000 funcs) | 500s | <50s (10x) |
| 最大并发 workers | 1 | 20+ |
| 质量（准确率） | 85% | 90%+ |
| 支持规模 | 1K functions | 10K+ functions |

### v0.6.0 Success Criteria

| Metric | Baseline | Target |
|--------|----------|--------|
| 跨分支对比速度 | N/A | <15 min (2 branches, 1K funcs each) |
| 重复检测准确率 | N/A | 90%+ |
| 自动化建议采纳率 | N/A | 70%+ |

---

## 🚨 Risk Management

### Risk 1: MVP 失败（Epic 6 不可行）

**概率**: 30%
**影响**: High
**缓解措施**:
- 4周 MVP 快速验证
- Go/No-Go 决策点清晰
- Fallback plan: 专注 Epic 5 Phase 1（Git 分析，无需 multi-agent）

### Risk 2: Claude API Rate Limits

**概率**: 40%
**影响**: Medium
**缓解措施**:
- 从10 workers 开始，逐步扩展
- 支持混合 backend（Claude + Opencode）
- 实现智能队列和限流

### Risk 3: PHP 项目反馈修复不彻底

**概率**: 20%
**影响**: Medium
**缓解措施**:
- v0.4.0 专注于索引质量
- 与用户密切沟通
- 快速迭代修复

### Risk 4: 时间延期

**概率**: 50%
**影响**: Medium
**缓解措施**:
- 每周复盘进度
- 灵活调整 Story 优先级
- MVP 优先，功能可后延

---

## 📝 Action Items

### This Week (Feb 3-7)

**Immediate Actions**:
1. ✅ 创建 Epic 6 文档
2. ⏳ 创建 v0.4.0 开发计划
3. ⏳ 修复版本号同步问题
4. ⏳ 开始 Story 4.4（业务语义提取）

**Preparation**:
- [ ] Review PHP 项目反馈细节
- [ ] 设计业务语义提取 AI prompt
- [ ] 准备增量更新技术方案
- [ ] 研究 Claude Code Task tool 并发限制

### Next Week (Feb 10-14)

- [ ] Complete Story 4.4 + 4.5
- [ ] Start Story 4.6 + 4.7
- [ ] Daily progress tracking

### End of Month (Feb 28)

- [ ] v0.4.0 Released
- [ ] PHP 项目反馈全部修复
- [ ] 准备 Epic 6 MVP 开发

---

## 🎯 Strategic Milestones

### Q1 2026 Milestones

| Date | Milestone | Status |
|------|-----------|--------|
| Feb 7 | Epic 6 规划完成 | ⏳ In Progress |
| Feb 28 | v0.4.0 Released | 📋 Planned |
| Mar 28 | Epic 6 MVP 完成 + Go/No-Go 决策 | 📋 Planned |

### Q2 2026 Milestones

| Date | Milestone | Status |
|------|-----------|--------|
| Apr 30 | v0.5.0 Released (Multi-agent) | 📋 Planned |
| Jun 30 | v0.6.0 Released (Branch Mgmt) | 📋 Planned |

---

## 📞 Stakeholder Communication

### Weekly Updates

**Format**: Every Friday
**Content**:
- What was completed this week
- What's planned for next week
- Blockers and risks
- Metrics and progress

### Monthly Reviews

**Format**: Last Friday of month
**Content**:
- Sprint retrospective
- Key achievements
- Lessons learned
- Roadmap adjustments

---

**Document Status**: ✅ Ready for Execution
**Next Review**: 2026-02-07 (Weekly Update #1)
**Owner**: Development Team
**Approver**: Product Owner

---

Generated: 2026-02-01
Roadmap Version: 1.0
Coverage: 2026 Q1-Q2 (Feb-Jun)
