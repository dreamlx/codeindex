# Epic 6: Multi-agent Orchestrator Infrastructure

**Created**: 2026-02-01
**Epic Type**: Platform Infrastructure
**Target Version**: v0.5.0
**Status**: 📋 Planning → 🧪 MVP Validation
**Strategic Importance**: ⭐⭐⭐⭐⭐ (Critical differentiator)

---

## 🎯 Epic Vision

**From**: Single-agent sequential code analysis
**To**: Multi-agent concurrent AI compute platform

Transform codeindex into an **AI算力调度平台**，利用 headless Claude/Opencode 的并发能力，将代码分析速度提升 10-100 倍，为上市公司提供"用算力换速度"的差异化价值。

---

## 📊 Business Context

### Problem Statement

**当前痛点**：
- 单 agent 串行处理大规模代码库耗时数小时
- 竞争对手（SonarQube、CodeClimate）只有静态分析，无语义理解
- 现有 AI 工具（GitHub Copilot）都是单 agent，慢

**目标客户**：
- 上市公司、中大型软件公司
- 有多客户定制版本的 SaaS 公司
- 需要快速代码审查和重复检测的团队

**客户诉求**：
- ⏱️ **速度** - "我愿意付钱，但不愿意等"
- 🎯 **准确** - "AST 分析太粗糙，我要语义理解"
- 📈 **规模** - "我有100+分支，需要批量分析"

### Value Proposition

**Slogan**: "AI 算力集群，10分钟顶10小时"

| 维度 | 传统工具 | 单 AI agent | codeindex v0.5.0 (Multi-agent) |
|------|---------|-------------|-------------------------------|
| **速度** | 5分钟 | 2小时 | **10分钟** ⚡ |
| **质量** | 60%准确率 | 85%准确率 | **95%准确率** 🎯 |
| **规模** | 单项目 | 单项目 | **100+分支并发** 📈 |
| **成本** | 免费 | $50 | $500 (但节省8小时人工) |

**ROI 计算**：
- 节省时间：110分钟
- 开发者时薪：$100/hour
- 时间价值：$183
- AI 成本：$450
- **净收益**：时间节省 > 成本（且体验大幅提升）

---

## 🏗️ Architecture Overview

### Current Architecture (v0.3.2)

```
codeindex (Python)
    ↓ ai_command
Claude CLI (single agent)
    ↓ sequential
Analyze code one by one
    ↓
README_AI.md
```

**性能**：1000个函数 = 500秒

### New Architecture (v0.5.0)

```
codeindex (Python)
    ↓ ai_command with orchestrator
Claude CLI → Orchestrator Skill
    ↓ (internal parallel Task calls)
    ├─→ Worker 1 (Claude/Opencode) ──┐
    ├─→ Worker 2 (Claude/Opencode) ──┤
    ├─→ Worker 3 (Claude/Opencode) ──┼─→ Result Aggregator
    ├─→ ...                         ──┤
    └─→ Worker N (Claude/Opencode) ──┘
    ↓
Final Report
```

**性能**：1000个函数 with 50 workers = 15秒

### Key Components

**1. Orchestrator Skill** (Claude agent)
- Task decomposition (分解任务)
- Worker scheduling (调度)
- Result aggregation (聚合)

**2. Worker Skill** (Claude/Opencode agent)
- Code analysis execution
- Semantic similarity detection
- Structured result output

**3. Python Invoker** (Enhanced)
- Mode detection (simple vs orchestrator)
- File I/O for large data
- Configuration management

**4. Configuration** (.codeindex.yaml)
- Orchestrator mode toggle
- Max workers setting
- Backend selection (Claude/Opencode/mixed)

---

## 📋 Stories and Tasks

### Story 6.1: Orchestrator Skill Foundation

**As a** codeindex user
**I want** multi-agent orchestration capability
**So that** my code analysis can run 10x faster

#### Acceptance Criteria

**AC1**: Orchestrator can decompose task into batches
```python
# Input: 100 functions
orchestrator.decompose(functions, num_workers=10)
# Output: 10 batches of 10 functions each
```

**AC2**: Orchestrator can launch workers in parallel
```python
# Launch 10 workers concurrently via Task tool
# All workers complete within 2x single-worker time
```

**AC3**: Orchestrator aggregates results correctly
```python
# 10 workers return results
# Orchestrator merges into single report
# No duplicates, no missing results
```

#### Tasks

- [ ] **Task 6.1.1**: Create orchestrator skill template (2 days)
  - skill.md definition
  - Task decomposition logic
  - Batch file writing

- [ ] **Task 6.1.2**: Implement parallel worker launching (3 days)
  - Single message with multiple Task calls
  - Handle 2, 5, 10 workers
  - Verify parallelism

- [ ] **Task 6.1.3**: Implement result aggregation (2 days)
  - Read all worker outputs
  - Merge results
  - Conflict resolution (if needed)

- [ ] **Task 6.1.4**: Error handling (2 days)
  - Worker timeout handling
  - Worker failure retry
  - Partial failure tolerance

**Estimate**: 9 days

---

### Story 6.2: Worker Skill Implementation

**As an** orchestrator
**I want** specialized worker agents
**So that** I can distribute analysis tasks

#### Acceptance Criteria

**AC1**: Worker can analyze a batch of function pairs
```python
# Input: batch of 20 function pairs
# Output: similarity scores for each pair
# Time: < 30 seconds
```

**AC2**: Worker output is structured and parseable
```json
{
  "batch_id": 1,
  "results": [
    {"pair_id": 1, "similarity": 0.85, "is_duplicate": true}
  ]
}
```

**AC3**: Worker handles errors gracefully
```python
# If LLM call fails, return error without crashing
# If function unparseable, skip and log
```

#### Tasks

- [ ] **Task 6.2.1**: Create worker skill template (2 days)
  - skill.md definition
  - Batch reading logic
  - Output writing logic

- [ ] **Task 6.2.2**: Implement similarity analysis (3 days)
  - LLM prompt for semantic comparison
  - Scoring algorithm
  - Threshold filtering

- [ ] **Task 6.2.3**: Result formatting (1 day)
  - JSON output structure
  - Error reporting

- [ ] **Task 6.2.4**: Performance optimization (2 days)
  - Reduce token usage
  - Optimize prompt
  - Benchmark

**Estimate**: 8 days

---

### Story 6.3: Python Integration

**As a** developer
**I want** codeindex to support orchestrator mode
**So that** I can use multi-agent analysis from CLI

#### Acceptance Criteria

**AC1**: Configuration supports orchestrator mode
```yaml
ai:
  mode: "orchestrator"  # New config option
  orchestrator:
    max_workers: 10
```

**AC2**: Invoker detects mode and routes correctly
```python
invoker = AIInvoker(config)
# If mode="orchestrator", call orchestrator skill
# If mode="simple", use old behavior
```

**AC3**: CLI command works end-to-end
```bash
codeindex find-duplicates --commit HEAD --workers 10
# Successfully runs with 10 workers
# Outputs aggregated results
```

#### Tasks

- [ ] **Task 6.3.1**: Extend config schema (1 day)
  - Add ai.mode field
  - Add orchestrator section
  - Backward compatibility

- [ ] **Task 6.3.2**: Modify AIInvoker (3 days)
  - Mode detection
  - Task file creation
  - Orchestrator invocation
  - Result file reading

- [ ] **Task 6.3.3**: CLI command integration (2 days)
  - Add --workers flag
  - Progress display
  - Error handling

- [ ] **Task 6.3.4**: End-to-end testing (2 days)
  - Test with 1, 5, 10 workers
  - Verify results match single-agent
  - Performance benchmarking

**Estimate**: 8 days

---

### Story 6.4: MVP Validation

**As a** product owner
**I want** to validate multi-agent provides value
**So that** we can decide on full investment

#### Acceptance Criteria

**AC1**: Speed improvement ≥ 5x
```
Baseline (1 worker): 100 seconds
Test (10 workers): ≤ 20 seconds
Speedup: 5x ✅
```

**AC2**: Quality maintained or improved
```
Baseline accuracy: 85%
Test accuracy: ≥ 85%
```

**AC3**: Cost increase < 15x
```
Baseline cost: $10
Test cost: ≤ $150 (overhead < 50%)
```

#### Tasks

- [ ] **Task 6.4.1**: Benchmark suite creation (2 days)
  - Create test dataset (100-500 functions)
  - Baseline measurement script
  - Metrics collection

- [ ] **Task 6.4.2**: Run experiments (3 days)
  - Test: 1, 5, 10, 20 workers
  - Measure: time, quality, cost
  - Document results

- [ ] **Task 6.4.3**: Analysis and decision (2 days)
  - ROI analysis
  - Bottleneck identification
  - Go/No-Go recommendation

**Estimate**: 7 days

---

## 📅 Timeline

### Phase 1: MVP (4 weeks)

**Week 1: Orchestrator Foundation**
- Story 6.1 (Orchestrator Skill)
- Deliverable: Working orchestrator with 2-5 workers

**Week 2: Worker Implementation**
- Story 6.2 (Worker Skill)
- Deliverable: Worker that analyzes batches

**Week 3: Python Integration**
- Story 6.3 (Python Integration)
- Deliverable: End-to-end working CLI

**Week 4: Validation**
- Story 6.4 (MVP Validation)
- Deliverable: Performance data + Go/No-Go decision

### Phase 2: Production (4 weeks) - If MVP successful

**Week 5-6: Optimization**
- Story 6.5: Smart task partitioning
- Story 6.6: Caching mechanism
- Story 6.7: Mixed backend support (Claude + Opencode)

**Week 7-8: Robustness**
- Story 6.8: Advanced error handling
- Story 6.9: Performance tuning
- Story 6.10: Documentation and release

---

## 🔧 Configuration Design

### .codeindex.yaml Extensions

```yaml
# Traditional mode (backward compatible)
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Or: Orchestrator mode
ai:
  mode: "orchestrator"  # "simple" | "orchestrator"
  command: "claude"

  orchestrator:
    skill: "codeindex-orchestrator"
    max_workers: 10           # Maximum concurrent workers
    strategy: "dynamic"       # "fixed" | "dynamic"
    timeout: 300              # Worker timeout (seconds)

  worker:
    skill: "code-analyzer-worker"
    retry: 3                  # Retry failed workers

  # Data transfer (large datasets)
  data:
    method: "file"            # "file" | "prompt"
    temp_dir: "/tmp/codeindex"
```

### Advanced Configuration (Phase 2)

```yaml
ai:
  mode: "orchestrator"

  # Mixed backend support
  backend: "mixed"  # "claude" | "opencode" | "mixed"

  mixed:
    backends:
      - name: "claude"
        command: "claude"
        weight: 0.7         # 70% tasks to Claude
      - name: "opencode"
        command: "opencode"
        weight: 0.3         # 30% tasks to Opencode
    strategy: "weighted"    # "round-robin" | "weighted" | "least-loaded"

  orchestrator:
    max_workers: 50

    # Smart partitioning
    partitioning:
      strategy: "complexity-based"  # "equal" | "complexity-based"
      min_batch_size: 5
      max_batch_size: 50

  # Caching
  cache:
    enabled: true
    backend: "sqlite"
    ttl: 86400
    path: ".codeindex/cache.db"
```

---

## 🎯 Success Metrics

### Technical Metrics

| Metric | Baseline (v0.3.2) | Target (v0.5.0 MVP) | Target (v0.5.0 Final) |
|--------|-------------------|---------------------|----------------------|
| **Speed** | 500s (1000 funcs) | 50s (10 workers) | 15s (50 workers) |
| **Speedup** | 1x | 10x | 33x |
| **Quality** | 85% (single LLM) | ≥85% | ≥90% |
| **Max Scale** | 1000 functions | 5000 functions | 50000 functions |
| **Concurrency** | 1 agent | 10 agents | 100 agents |

### Business Metrics

| Metric | Target |
|--------|--------|
| **Customer Tier** | Enterprise (上市公司) |
| **Price Point** | $999-$4999/month |
| **Value Prop** | "10x faster than single-agent" |
| **Differentiation** | Only tool with 100-agent concurrency |

---

## 🚧 Risks and Mitigation

### Risk 1: Claude API Rate Limits

**Risk**: API provider limits concurrent requests
**Impact**: Can't achieve 100-agent concurrency
**Mitigation**:
- Start with 10-20 agents (safe)
- Support mixed backends (distribute load)
- Implement queuing if hit limits

### Risk 2: Worker Startup Overhead

**Risk**: Starting 100 agents takes too long
**Impact**: No net speedup
**Mitigation**:
- Measure overhead in MVP
- Implement worker pooling if needed
- Use dynamic worker count

### Risk 3: Result Inconsistency

**Risk**: Different agents give different similarity scores
**Impact**: Unreliable results
**Mitigation**:
- Use confidence thresholds
- Implement voting mechanism
- A/B test consistency

### Risk 4: Cost Explosion

**Risk**: 100x concurrency = 100x cost
**Impact**: Not economically viable
**Mitigation**:
- Smart task filtering (don't analyze obvious non-duplicates)
- Caching (avoid re-analyzing same pairs)
- Tiered pricing (customers pay for speed)

---

## 📦 Deliverables

### MVP Deliverables (Week 4)

- ✅ Working orchestrator skill
- ✅ Working worker skill
- ✅ Python integration with CLI
- ✅ Performance benchmark data
- ✅ Go/No-Go recommendation document

### Production Deliverables (Week 8)

- ✅ Production-ready orchestrator (50+ workers)
- ✅ Advanced features (caching, mixed backend)
- ✅ Comprehensive documentation
- ✅ Performance tuning complete
- ✅ Release notes for v0.5.0

---

## 🔗 Dependencies

### Depends On
- v0.3.2 released ✅
- Claude Code Task tool available ✅
- Headless Claude/Opencode accessible ✅

### Enables
- **Epic 5**: Intelligent Branch Management (uses multi-agent for duplicate detection)
- **Epic 7**: Large-scale Code Migration (analyze entire codebases in minutes)
- **Future**: Real-time code review (multi-agent parallel review)

---

## 💡 Open Questions

### Technical Questions

1. **Max Concurrency**: What's the actual limit for Claude Task tool?
   - Need to test: 10, 20, 50, 100 workers
   - Document findings in MVP

2. **Worker Isolation**: Are workers truly parallel or serialized internally?
   - Verify with timestamps
   - Check Claude Code documentation

3. **Data Transfer**: File I/O vs embedded prompt?
   - Benchmark both approaches
   - Choose based on performance

4. **State Management**: Do workers need shared state?
   - Current design: stateless workers ✅
   - Revisit if needed

### Business Questions

1. **Pricing Model**: Per-worker or flat fee?
   - Proposal: Tiered by max_workers (10/50/200)
   - Get customer feedback

2. **Target Customer**: SMB or Enterprise?
   - Focus: Enterprise (上市公司) with $$$
   - SMB can use single-agent mode

---

## 📝 Next Steps

### Immediate (This Week)
1. ✅ Create Epic 6 document (this file)
2. ⏳ Get approval on architecture
3. ⏳ Create orchestrator skill template
4. ⏳ Start Task 6.1.1 (orchestrator foundation)

### Next Week
- Begin Week 1 development (Story 6.1)
- Daily standup to track progress
- Prototype with 2-5 workers

### Decision Point (Week 4)
- Review MVP data
- Go/No-Go on Phase 2
- Adjust Epic 5 timeline based on results

---

**Status**: 📋 Ready for Review
**Approval Needed**: Architecture, Timeline, Budget
**Risk Level**: Medium (new technology, unproven at scale)
**Recommendation**: **Proceed with MVP** (4 weeks, low risk, high potential)

---

Generated: 2026-02-01
Epic: 6 - Multi-agent Orchestrator Infrastructure
Strategic Importance: Critical for competitive differentiation
