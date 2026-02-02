# 规划和路线图

本目录包含 codeindex 的规划文档、改进路线图和执行摘要。

## 📖 核心文档

### 快速了解（推荐阅读顺序）

1. **[executive-summary.md](executive-summary.md)** - ⭐ 执行摘要
   - 当前评估问题分析
   - 改进方向总览
   - 行动计划（3个Phase）
   - 一页读懂全部

2. **[improvement-roadmap.md](improvement-roadmap.md)** - 🚀 改进路线图
   - Phase 1：核心改进（本周）
     - 符号重要性评分系统
     - 自适应符号提取策略
   - Phase 2：评估体系（下周）
     - 自动化评估框架
   - Phase 3：可选增强（未来）
     - 双模式索引
     - 框架感知评分

3. **[improvement-proposals.md](improvement-proposals.md)** - 📋 详细改进提案
   - 提案1：符号提取策略优化（⭐⭐⭐）
   - 提案2：双层索引模式（⭐⭐）
   - 提案3：符号重要性评分（⭐⭐⭐）
   - 提案4：工具定位文档优化（⭐）
   - 提案5：评估测试用例（⭐⭐）

### 归档文档

- **[improvement-plan-archive.md](improvement-plan-archive.md)** - 早期改进计划（已被 roadmap 替代）

## 📊 关键数据

### 改进目标

| 指标 | 改进前 | 目标 | 提升 |
|------|--------|------|------|
| 大文件符号数 | 15个 | 80-120个 | +433%-700% |
| 关键API覆盖率 | 70% | 95% | +36% |
| 符号选择准确性 | 60% | 92% | +53% |
| 噪音符号比例 | 25% | <10% | -60% |
| 导航效率评分 | 72/100 | 92/100 | +28% |
| Token消耗增加 | - | <20% | 可控 |

### 实施时间线

```
Week 1 (本周)：核心改进
├── Day 1-2: 符号重要性评分
├── Day 3-4: 自适应符号提取
└── Day 5: 验证和调优

Week 2 (下周)：评估体系
├── Day 6-8: 自动化评估框架
└── Day 9-10: 文档和发布

Future (未来)：可选增强
├── 双模式索引（按需）
└── 框架感知（按需）
```

## 🎯 使用指南

### 我应该读哪个文档？

**如果你想...**

- 📝 **快速了解改进方向** → 读 `executive-summary.md`
- 🚀 **查看实施计划** → 读 `improvement-roadmap.md`
- 🔍 **深入技术细节** → 读 `improvement-proposals.md`
- 📊 **评估改进效果** → 读 [evaluation/framework.md](../evaluation/framework.md)
- 💡 **查看具体案例** → 读 [evaluation/before-after.md](../evaluation/before-after.md)

### 文档关系

```
executive-summary.md           # 总览（1页）
    ↓
improvement-roadmap.md         # 实施计划（详细）
    ↓
improvement-proposals.md       # 技术提案（非常详细）
    ↓
[实施] → 代码和测试
    ↓
evaluation/framework.md        # 验证效果
```

## 🔗 相关文档

### 评估相关
- [评估框架](../evaluation/framework.md) - 如何评估 codeindex
- [改进对比](../evaluation/before-after.md) - 改进前后效果对比
- [案例研究](../evaluation/case-studies/) - 真实项目案例

### 开发相关
- [开发改进记录](../development/improvements/) - 技术实现细节
- [架构设计](../architecture/design/) - 设计文档

### 历史路线图
- [roadmap/2025-Q1.md](roadmap/2025-Q1.md) - 2025 Q1 规划
- [roadmap/dependency-graph-update.md](roadmap/dependency-graph-update.md) - 依赖图更新

## 📝 下一步行动

1. ✅ 阅读 `executive-summary.md` 了解全局
2. ✅ 阅读 `improvement-roadmap.md` 了解实施计划
3. ✅ 决定是否立即实施 Phase 1
4. ✅ 用你的项目验证改进效果
5. ✅ 提供反馈和建议

---

**重要提醒**：所有改进都围绕一个核心原则 —— **保持"快速导航"的核心价值，同时提升信息完整性**。
