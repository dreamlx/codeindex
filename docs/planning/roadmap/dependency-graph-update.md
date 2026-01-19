# Roadmap: 依赖图更新 (Dependency Graph Update)

> Status: **Planned** | Priority: **P1** | Target: Enterprise Edition

## 概述

依赖图更新是面向企业级大型项目的高级特性，通过语义分析精确追踪代码变化的影响范围，实现最小化的文档更新。

## 问题背景

### 当前方案：智能增量更新

```
git diff → 统计变化行数 → 阈值判断 → 更新决策
```

**局限性**：
- 基于数量判断，可能过度更新或遗漏
- 无法识别 API 变化 vs 内部重构
- 大型项目中效率不够优化

### 企业级场景需求

| 特点 | 挑战 | 需求 |
|------|------|------|
| 代码量大 (100K+ 行) | 全量更新不可行 | 精确的增量更新 |
| 依赖关系复杂 | 变化影响范围难判断 | 依赖追踪 |
| 多团队协作 | 文档同步困难 | 自动化更新 |
| CI/CD 集成 | 不能阻塞流水线 | 快速反馈 |
| 渐进式改造 | 需要知道进度 | 状态追踪 |

## 方案设计

### 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                    Dependency Graph                      │
├─────────────────────────────────────────────────────────┤
│  Module A ──exports──▶ [func1, Class1, const1]          │
│     ▲                                                    │
│     │ imports                                            │
│     │                                                    │
│  Module B ──exports──▶ [func2, Class2]                  │
│     ▲                                                    │
│     │ imports                                            │
│     │                                                    │
│  Module C ──exports──▶ [func3]                          │
└─────────────────────────────────────────────────────────┘
```

### 更新流程

```
1. Git Commit
      │
      ▼
2. Diff Analysis ─────────────────────┐
   - 识别变化的文件                    │
   - 提取变化的符号 (exports)          │
      │                               │
      ▼                               │
3. Impact Analysis                    │
   - 查询依赖图                        │
   - 计算影响范围                      │
   - 分级: L0/L1/L2                   │
      │                               │
      ▼                               │
4. Update Decision                    │
   - L0: 直接变化 → 必须更新           │
   - L1: API 依赖 → 建议更新           │
   - L2: 间接依赖 → 可选更新           │
      │                               │
      ▼                               │
5. Execute Updates                    │
   - 并行更新受影响的 README_AI.md    │
   - 更新依赖图缓存                    │
└─────────────────────────────────────┘
```

### 数据模型

```python
@dataclass
class ModuleNode:
    path: str
    exports: list[Symbol]           # 导出的符号
    imports: list[ImportRef]        # 导入的引用
    dependents: set[str]            # 被哪些模块依赖
    readme_hash: str                # README_AI.md 的 hash
    last_updated: datetime          # 最后更新时间

@dataclass
class DependencyGraph:
    nodes: dict[str, ModuleNode]

    def get_impact(self, changed_files: list[str]) -> ImpactResult:
        """计算变化影响范围"""
        ...

    def needs_update(self, path: str) -> bool:
        """检查是否需要更新"""
        ...
```

## 企业级权衡分析

### 速度 vs 精确度

| 场景 | 智能增量 | 依赖图 | 推荐 |
|------|----------|--------|------|
| 小项目 (<10K 行) | ✓ 快速 | ✗ 过度设计 | 智能增量 |
| 中型项目 (10K-100K) | △ 可用 | ✓ 更精确 | 可选 |
| 大型项目 (>100K) | ✗ 效率低 | ✓ 必要 | 依赖图 |

### 首次构建成本

```
项目规模        智能增量      依赖图
──────────────────────────────────
10K 行         ~1 分钟       ~2 分钟
50K 行         ~5 分钟       ~8 分钟
100K 行        ~10 分钟      ~15 分钟
500K 行        ~50 分钟      ~60 分钟
```

**关键点**：首次构建差异不大，但日常更新依赖图更高效。

### 日常更新成本

```
变更场景              智能增量          依赖图
────────────────────────────────────────────────
修改 1 个文件内部     更新 1 目录       更新 1 目录
修改 1 个 API        更新 1 目录       更新 1 + N 依赖方
重构 10 个文件       更新 10 目录      更新实际影响的 M 目录
大规模重构           可能全量更新      精确更新受影响部分
```

### ROI 分析

```
                    智能增量                依赖图
─────────────────────────────────────────────────────
实现成本            低 (~2 天)             中 (~2 周)
维护成本            低                     中
AI 调用成本/月      高 (可能重复更新)       低 (精确更新)
文档准确性          中                     高
团队接受度          高 (简单)              中 (需要理解)

适用场景            个人/小团队项目        企业级/大型项目
```

## 实现路线

### Phase 1: 基础设施 (2 周)

- [ ] 设计依赖图数据结构
- [ ] 实现依赖提取 (基于现有 parser)
- [ ] 依赖图持久化 (JSON/SQLite)
- [ ] 基本的查询 API

### Phase 2: 变化检测 (2 周)

- [ ] Git diff 集成
- [ ] 符号级别的变化检测
- [ ] API 变化 vs 内部变化区分
- [ ] 影响范围计算

### Phase 3: 更新策略 (1 周)

- [ ] 分级更新逻辑 (L0/L1/L2)
- [ ] 配置化策略
- [ ] 与现有 hook 集成

### Phase 4: 企业特性 (2 周)

- [ ] 并行更新优化
- [ ] 增量图更新 (不需要全量重建)
- [ ] 状态报告和仪表盘
- [ ] CI/CD 集成指南

## 配置示例

```yaml
# .codeindex.yaml - 企业版配置
update_strategy: dependency_graph  # 或 incremental

dependency_graph:
  enabled: true
  storage: .codeindex/graph.json

  # 更新策略
  levels:
    L0_direct:     auto      # 直接变化：自动更新
    L1_api_deps:   prompt    # API 依赖：提示确认
    L2_indirect:   manual    # 间接依赖：手动触发

  # 性能优化
  parallel_updates: 4         # 并行更新数
  cache_ttl: 3600            # 图缓存时间 (秒)

  # CI/CD 模式
  ci_mode:
    fail_on_outdated: false  # 过时文档是否失败
    report_only: true        # 只报告，不更新
```

## CLI 命令

```bash
# 构建/更新依赖图
codeindex graph build          # 全量构建
codeindex graph update         # 增量更新
codeindex graph show           # 可视化

# 分析影响
codeindex affected             # 显示当前变化影响
codeindex affected --since v1.0.0  # 自某版本以来

# 更新
codeindex scan --affected      # 只更新受影响的
codeindex scan --level L1      # 更新到 L1 级别
```

## 与智能增量的对比总结

| 维度 | 智能增量 | 依赖图 |
|------|----------|--------|
| **判断依据** | 变化行数 | 符号语义 |
| **精确度** | 中 | 高 |
| **实现复杂度** | 低 | 中 |
| **首次成本** | 低 | 中 |
| **日常成本** | 中-高 | 低 |
| **适用规模** | <50K 行 | >50K 行 |
| **推荐场景** | 个人/小团队 | 企业/大型项目 |

## 结论

对于企业级老项目改造：

1. **短期**：使用智能增量更新快速获得价值
2. **中期**：评估项目规模，决定是否启用依赖图
3. **长期**：大型项目应迁移到依赖图更新以优化成本

**关键指标**：当 AI 调用成本或更新时间成为瓶颈时，切换到依赖图更新。

---

*Last updated: 2026-01-19*
