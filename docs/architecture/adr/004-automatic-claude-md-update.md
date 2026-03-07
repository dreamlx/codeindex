# ADR 004: 客户 CLAUDE.md 自动更新机制

## 状态
已采纳 (Accepted) - 2026-03-08

## 背景

codeindex 快速迭代（v0.11.0 → v0.21.0，2 周内发布 3 个版本），但客户的 `~/.claude/CLAUDE.md` 中的 codeindex 使用指南无法同步更新，导致：

**现实问题**:
- 用户文档过时：客户看到的是 v0.11.0 文档，实际安装了 v0.21.0
- 新功能缺失：tech-debt 增强（v0.22.0）、Swift/Objective-C 支持（v0.21.0）未体现
- 手动更新成本高：用户需要记住检查、手动复制、容易遗漏
- 版本不一致混乱：不同客户看到的文档版本不同，支持困难

**触发事件**:
- 2026-03-08 发现项目 CLAUDE.md 版本号不一致（v0.6.0 vs v0.21.0）
- 全局 ~/.claude/CLAUDE.md 更加过时（v0.11.0）
- 最近 2 周内 3 个版本发布，手动更新不可持续

## 决策

**采用混合方案（Post-install Hook + Skill）实现自动更新机制**：

1. **Post-install Hook（v0.22.2）**: 静默更新核心内容（80% 需求）
2. **Skill（v0.22.3）**: 交互式深度定制（20% 高级需求）

### 架构设计

```
pip install --upgrade ai-codeindex
    ↓
Post-install Hook（自动执行）
    ├─ 检测版本变化
    ├─ Marker-based injection（幂等更新）
    ├─ 更新核心内容（版本号、基本命令）
    └─ 提示: "💡 Run /codeindex-update-guide for advanced customization"

/codeindex-update-guide（用户可选）
    ↓
Skill（交互式）
    ├─ 项目分析（语言检测、配置检测）
    ├─ 个性化建议（"你有 Swift 文件，添加 Swift 文档？"）
    ├─ 显示 diff（让用户确认）
    └─ 应用更新 + 备份
```

### 更新范围划分

| 内容 | Post-install Hook | Skill | 原因 |
|------|-------------------|-------|------|
| 版本号 | ✅ 主要 | ✅ 复核 | 基础信息，必须同步 |
| 核心命令 | ✅ 主要 | ✅ 增强 | scan/parse/tech-debt 基础用法 |
| 语言支持表格 | ❌ 不更新 | ✅ 主要 | 需要用户确认（项目相关） |
| tech-debt 详细文档 | ✅ 基础 | ✅ 完整 | Hook 更新简版，Skill 完整版 |
| 项目特定配置 | ❌ 不涉及 | ✅ 专属 | Swift 项目的特殊配置等 |
| 个性化建议 | ❌ 不涉及 | ✅ 专属 | 基于项目分析的智能建议 |

## 理由

### 1. 为什么不用单一方案？

#### Option A: 仅 Post-install Hook
- ❌ **缺点**: 无法个性化，一刀切更新可能不适合所有用户
- ❌ **风险**: 用户不知道被修改，透明度低
- ❌ **限制**: 无法基于项目特点智能建议
- ✅ **优点**: 自动化程度高，用户无感知

#### Option B: 仅 Skill
- ❌ **缺点**: 需要主动触发，用户可能忘记
- ❌ **问题**: 新用户不知道有这个 skill
- ❌ **依赖**: 只能在 Claude Code 环境中使用
- ✅ **优点**: 完全透明，用户可控

#### Option C: 混合方案（采纳）
- ✅ **Hook 保底**: 保证基础内容自动同步（80% 用户需求）
- ✅ **Skill 增强**: 提供深度定制（20% 高级用户）
- ✅ **优势互补**: Hook 的自动化 + Skill 的灵活性
- ✅ **渐进式**: 可以分阶段实现，风险可控

### 2. 技术可行性

**Post-install Hook**:
```python
# pyproject.toml (PEP 660 支持)
[project.entry-points."pip.post-install"]
codeindex = "codeindex.hooks:post_install_update_guide"

# 关键技术
✅ Marker-based injection（借鉴现有 CLAUDE.md injection 机制）
✅ 版本检测（避免重复更新）
✅ 幂等性保证（多次更新不破坏内容）
✅ 异常处理（静默失败，不阻塞安装）
✅ CI 环境检测（跳过 CI/CD 环境）
```

**Skill**:
```markdown
# ~/.claude/skills/codeindex-update-guide/SKILL.md
✅ Read CLAUDE.md（读取当前内容）
✅ 项目分析（语言检测、框架检测）
✅ Diff 生成（Markdown 格式展示变更）
✅ Edit CLAUDE.md（Marker-based 更新）
✅ 备份 + 回滚（安全保障）
```

### 3. ROI 分析

**开发成本**:
- Post-install Hook: 1 周（40 小时）→ $1,400
- Skill: 2 周（80 小时）→ $2,800
- 测试 + 文档: 1 周（40 小时）→ $1,400
- **总计**: 4 周，$5,600

**收益**:
- **时间节省**: 每个客户每次升级节省 15 分钟手动更新
  - 假设 100 个活跃用户，每年 6 次升级 → 100 × 6 × 15 = 9,000 分钟 (150 小时)
- **支持成本降低**: 减少"文档过时"相关的支持请求（估计 30%）
- **用户体验提升**: 用户始终看到最新、准确的文档
- **维护成本降低**: 不再需要手动通知用户更新文档

**投资回报周期**: 2-3 个月

### 4. 风险与缓解

| 风险 | 严重性 | 概率 | 缓解措施 |
|------|--------|------|----------|
| pip 兼容性问题 | 中 | 低 | 检测 pip 版本，提供 fallback |
| 用户文件权限 | 低 | 中 | try-except 静默失败 |
| 内容冲突 | 中 | 低 | Marker-based，只更新特定区域 |
| CI 环境误触发 | 低 | 中 | 检测 CI 环境跳过 |
| Hook 失败阻塞安装 | 高 | 低 | 异常处理，不抛出错误 |

## 实施计划

### Phase 1: Post-install Hook（v0.22.2，1 周）

**Epic**: 实现基础自动更新机制
**Story**:
1. 设计 Marker-based injection 机制
2. 实现版本检测逻辑
3. 实现核心内容更新（版本号、基本命令）
4. 实现备份机制
5. 编写单元测试 + 集成测试
6. 文档更新

**验收标准**:
- ✅ pip install --upgrade 后自动更新 ~/.claude/CLAUDE.md
- ✅ 版本号正确更新
- ✅ 核心命令（scan, tech-debt）更新
- ✅ 多次更新幂等（不重复内容）
- ✅ 异常不阻塞安装
- ✅ CI 环境跳过更新

### Phase 2: Skill（v0.22.3，2 周）

**Epic**: 实现交互式深度定制
**Story**:
1. 设计 Skill 结构和交互流程
2. 实现项目分析（语言检测、配置检测）
3. 实现 Diff 生成和展示
4. 实现交互式确认流程
5. 实现 Marker-based 更新
6. 实现备份 + 回滚机制
7. 编写测试
8. 文档 + 示例

**验收标准**:
- ✅ /codeindex-update-guide 触发 skill
- ✅ 检测项目语言（Python/Swift/Java 等）
- ✅ 显示 diff（Markdown 格式）
- ✅ 用户确认后更新
- ✅ 自动备份 CLAUDE.md
- ✅ 支持回滚操作
- ✅ 个性化建议（基于项目分析）

### Phase 3: 优化与增强（v0.23.0+，持续）

**可能的增强**:
- AI 驱动的更新建议（Claude 分析项目，智能推荐）
- 多文件协同更新（同时检查 .codeindex.yaml）
- 版本跳跃检测（v0.11.0 → v0.21.0 完整重置）
- 更新历史记录（记录每次更新的内容）
- A/B 测试不同更新策略

## 替代方案（已否决）

### 方案 1: 手动更新 + 文档提醒
- ❌ **问题**: 用户容易忘记，文档过时率高
- ❌ **成本**: 每次版本都需要通知用户
- ❌ **体验**: 用户需要手动复制粘贴

### 方案 2: 集成到 codeindex init 命令
- ❌ **问题**: 用户可能不运行 init（只运行 scan）
- ❌ **时机**: init 通常只在项目开始时运行一次
- ❌ **缺点**: 无法在升级后自动更新

### 方案 3: 独立 CLI 命令（codeindex update-guide）
- ❌ **问题**: 需要用户主动运行，容易遗忘
- ❌ **学习**: 新增命令，增加学习成本
- ✅ **优点**: 可以作为 Skill 的 fallback

## 影响范围

### 代码变更
- ✅ 新增: `src/codeindex/hooks.py`（Post-install hook）
- ✅ 新增: `~/.claude/skills/codeindex-update-guide/SKILL.md`
- ✅ 修改: `pyproject.toml`（entry-points 配置）
- ✅ 新增: `tests/test_hooks.py`
- ✅ 新增: `tests/test_skill_update_guide.py`

### 文档变更
- ✅ 更新: `README.md`（说明自动更新机制）
- ✅ 更新: `CHANGELOG.md`（v0.22.2, v0.22.3）
- ✅ 新增: `docs/guides/auto-update-guide.md`
- ✅ 更新: `CLAUDE.md`（说明 /codeindex-update-guide）

### 用户影响
- ✅ **正面**: 用户始终看到最新文档，无需手动更新
- ✅ **正面**: 高级用户可以使用 Skill 深度定制
- ⚠️ **中性**: 用户需要知道有 /codeindex-update-guide 可用（通过 Hook 提示消息）
- ⚠️ **风险**: 极少数情况下 Hook 可能失败（已缓解）

## 成功指标

### 量化指标（6 个月后评估）
- ✅ **自动更新率**: ≥90% 用户的 CLAUDE.md 版本与安装版本一致
- ✅ **Skill 使用率**: ≥20% 用户使用过 /codeindex-update-guide
- ✅ **支持请求减少**: "文档过时"相关支持请求减少 ≥50%
- ✅ **用户满意度**: NPS 评分提升（通过用户反馈）

### 质性指标
- ✅ 用户反馈: "升级后文档自动更新，很方便"
- ✅ 维护成本: 减少手动通知用户更新的工作量
- ✅ 一致性: 所有用户文档版本一致，支持更容易

## 后续工作

1. **v0.22.2**: 实现 Post-install Hook
2. **v0.22.3**: 实现 Skill
3. **v0.23.0**: 收集用户反馈，优化流程
4. **v0.24.0**: 考虑 AI 驱动的智能建议

## 参考资料

- PEP 660: Editable installs for pyproject.toml based builds
- 现有 CLAUDE.md injection 机制（`init_wizard.py`）
- Claude Code Skill 开发指南
- 用户反馈: GitHub Issues #XXX

## 相关 ADR

- ADR 002: 外部 AI CLI 集成（为什么需要 CLAUDE.md）
- ADR 003: Swift/Objective-C 支持（触发本次更新需求的版本）

---

**决策人**: dreamlinx
**日期**: 2026-03-08
**状态**: 已采纳，待实施
**下一步**: 创建 GitHub Issue + Epic/Story
