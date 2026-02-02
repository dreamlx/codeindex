# 🚀 AI Enhancement 问题快速诊断指南

如果你在 PHP 项目上运行 `codeindex scan-all` 时遇到 AI 增强失败，请按以下步骤操作。

## 📊 问题现象

```
AI增强成功： 4/8 个目录
- ✅ Retail (27KB → 2KB)
- ⚠️ 另外4个目录AI调用失败，使用SmartWriter版本
```

**核心问题**:
- AI成功率低（<60%）
- 仍有51KB的大文件
- 不知道为什么失败

---

## 🔍 第一步：运行诊断工具

```bash
# 进入你的PHP项目目录
cd /Users/dreamlinx/Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488

# 运行诊断（假设codeindex在你的PATH中）
# 或者指定完整路径
python /Users/dreamlinx/Dropbox/Projects/codeindex/scripts/diagnose_ai_failures.py
```

### 预期输出

诊断工具会告诉你：

1. **哪些目录有问题**
   ```
   ┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ 目录               ┃ 文件数 ┃ 符号数 ┃ Prompt大小  ┃ 状态      ┃
   ┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
   │ Retail/Controller  │     45 │    687 │    215.3KB  │ too_large │
   │ Common/Model       │     38 │    542 │    189.7KB  │ risky     │
   └────────────────────┴────────┴────────┴─────────────┴───────────┘
   ```

2. **为什么会失败**
   ```
   🚨 CRITICAL: Prompt太大 (215KB)
   ⏱  超时时间不足：需要255秒，但配置只有120秒
   📊 符号数量过多：687个符号（包括156个get*方法）
   ```

3. **具体改进建议**
   ```
   配置优化建议：
   🔧 max_concurrent: 降低到 2-4
   ⏱  timeout: 增加到 255秒
   🚦 rate_limit_delay: 增加到 2.0秒
   ```

---

## ⚡ 第二步：应用快速修复

### 修复方案1: 调整配置（立即见效，无需改代码）

编辑你的 `.codeindex.yaml`：

```yaml
# AI Enhancement settings
ai_enhancement:
  strategy: "selective"
  enabled: true
  size_threshold: 30720      # 从20KB调整到30KB (更保守)
  max_concurrent: 2          # ⬅️ 从8降低到2（关键！）
  rate_limit_delay: 2.0      # ⬅️ 从1.0增加到2.0（关键！）
```

然后重新运行，并增加超时：

```bash
codeindex scan-all --timeout 240  # ⬅️ 从120增加到240秒
```

**预期改进**: +20% 成功率

### 修复方案2: 排除不必要的符号（立即见效）

如果诊断工具显示大量 `get*` 或 `set*` 方法：

编辑 `.codeindex.yaml`：

```yaml
indexing:
  symbols:
    exclude_patterns:
      - "get*"        # ⬅️ 添加这一行
      - "set*"        # ⬅️ 添加这一行
```

**预期改进**: Prompt大小 -30%，成功率 +15%

### 修复方案3: 组合拳（推荐）

同时应用方案1和方案2：

```yaml
ai_enhancement:
  max_concurrent: 2
  rate_limit_delay: 2.0

indexing:
  symbols:
    exclude_patterns: ["get*", "set*"]
```

运行：
```bash
codeindex scan-all --timeout 240
```

**预期改进**: +35% 成功率

---

## 📈 第三步：验证结果

重新运行后，查看输出：

```bash
Completed: 119/119 directories, 7/8 AI enhanced
```

**成功标准**:
- ✅ AI增强成功率 ≥ 75% (6/8或更好)
- ✅ 没有51KB的大文件
- ✅ 大多数README在5-10KB之间

如果仍然有问题：

1. **重新运行诊断工具** - 看看哪些目录还有问题
2. **针对性处理** - 对仍然失败的目录单独处理

```bash
# 对特定目录增加更长的超时
codeindex scan Application/Retail/Controller --timeout 300
```

---

## 🔧 高级技巧

### 技巧1: 分批处理

不要一次性处理所有目录，分批进行：

```bash
# 第一批：小目录（快速）
codeindex scan-all --timeout 120 2>&1 | grep "✓"

# 第二批：对失败的大目录单独处理
codeindex scan Application/Retail/Controller --timeout 300
codeindex scan Application/Common/Model --timeout 300
```

### 技巧2: 暂时禁用AI

对于超大目录，暂时使用SmartWriter：

```bash
# 只对这个目录禁用AI
codeindex scan Application/Retail/Controller --no-ai
```

SmartWriter版本虽然不如AI精炼，但：
- ✅ 100%成功率
- ✅ 仍然包含所有符号信息
- ✅ 可以后续等Epic 3.1实施后重新生成

### 技巧3: 拆分大目录

如果 `Retail/Controller` 有45个Controller，考虑重构：

```
Retail/Controller/
├── Goods/          # 商品相关 (15个)
├── Order/          # 订单相关 (12个)
└── User/           # 用户相关 (8个)
```

然后重新运行：
```bash
codeindex scan-all
```

每个子目录的prompt会小很多，AI成功率会大幅提升。

---

## 📝 记录和反馈

### 保存诊断报告

```bash
# 将诊断报告保存到文件
python scripts/diagnose_ai_failures.py > ai_diagnosis_report.txt

# 查看报告
cat ai_diagnosis_report.txt
```

### 反馈给开发团队

如果快速修复后仍有问题，请：

1. **保存诊断报告**
2. **创建GitHub Issue**
3. **附上报告和配置**

这将帮助我们优先实施 Epic 3.1（智能压缩）。

---

## ⏭️ 下一步

### 等待Epic 3.1（预计2周）

Epic 3.1 将实施：
- ✅ Prompt智能压缩（自动将200KB压缩到50KB）
- ✅ 自适应超时（自动计算需要的时间）
- ✅ 错误分类和重试（自动重试超时）
- ✅ 详细日志（准确诊断每个失败）

**预期效果**: 成功率从50% → 85%，无需手动配置

### 临时方案

在Epic 3.1完成前：
1. 使用诊断工具找出问题
2. 应用快速修复（调整配置+排除符号）
3. 分批处理或暂时禁用AI

---

## 💬 常见问题

**Q: 诊断工具运行很慢？**
A: 正常，它需要解析所有文件。大型项目可能需要5-10分钟。

**Q: 为什么有些目录即使调整后仍失败？**
A: 可能是prompt确实太大（>300KB）。等Epic 3.1的智能压缩，或暂时用--no-ai。

**Q: SmartWriter版本和AI版本差别大吗？**
A: 信息量相同，但AI版本更精炼、更易读。SmartWriter是完全可用的备选方案。

**Q: 配置调整后需要重新扫描所有目录吗？**
A: 是的，因为配置影响生成的README内容。

---

**相关文档**:
- [完整问题分析](./ai-enhancement-issues.md)
- [改进计划概览](./README.md)

**工具位置**:
- [诊断脚本](../../../scripts/diagnose_ai_failures.py)

**获取帮助**:
- GitHub Issues: https://github.com/dreamlx/codeindex/issues
- Discussions: https://github.com/dreamlx/codeindex/discussions
