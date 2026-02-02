# AI Enhancement 改进计划

本目录包含 AI Enhancement 功能的问题分析、改进方案和工具。

## 📚 文档

### [ai-enhancement-issues.md](./ai-enhancement-issues.md)
**完整的问题分析和改进方案文档**

包含：
- 📊 实际生产环境问题反馈
- 🔍 根因分析（4大问题）
- 🎯 改进方案（智能压缩、超时优化、并发控制、错误诊断）
- 📋 实施计划（分3个Epic）
- 🧪 测试策略
- 📊 预期改进效果

**适合阅读对象**：开发者、技术决策者

---

## 🛠️ 工具

### [scripts/diagnose_ai_failures.py](../../../scripts/diagnose_ai_failures.py)
**AI增强失败诊断工具**

立即分析你的项目，找出AI增强失败的原因。

#### 使用方法

```bash
# 在项目根目录运行
cd /path/to/your/project
python /path/to/codeindex/scripts/diagnose_ai_failures.py

# 或指定项目路径
python scripts/diagnose_ai_failures.py /path/to/your/project
```

#### 输出报告

诊断工具会生成详细报告，包括：

1. **总体统计** - Prompt大小分布
2. **问题目录详情** - 哪些目录prompt过大
3. **改进建议** - 针对每个问题的具体建议
4. **配置优化建议** - max_concurrent、timeout等
5. **下一步行动** - 优先级排序的清单

---

## 🚀 快速修复指南

如果你的PHP项目AI增强失败率高，可以立即尝试：

### 方案1: 调整配置（立即见效）

编辑 `.codeindex.yaml`：

```yaml
ai_enhancement:
  max_concurrent: 2          # 从8降低到2
  rate_limit_delay: 2.0      # 从1.0增加到2.0

# 在CLI参数中增加超时
# codeindex scan-all --timeout 240
```

**预期改进**: +20% 成功率

### 方案2: 排除不重要的符号（立即见效）

```yaml
indexing:
  symbols:
    exclude_patterns:
      - "get*"
      - "set*"
```

**预期改进**: Prompt大小 -30%，成功率 +15%

---

## 📋 Epic 3 实施跟踪

### Epic 3.1: 快速修复 🔥🔥🔥🔥🔥

| Story | 状态 | ETA |
|-------|------|-----|
| 3.1.1 Prompt智能压缩 | 📝 规划中 | 2周 |
| 3.1.2 自适应超时 | 📝 规划中 | 1周 |
| 3.1.3 错误分类和重试 | 📝 规划中 | 1周 |
| 3.1.4 详细日志 | 📝 规划中 | 1周 |

**目标**: AI成功率从50% → 80%+

---

**最后更新**: 2026-01-27
**维护者**: codeindex team
