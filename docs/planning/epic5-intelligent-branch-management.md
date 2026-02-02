# Epic 5: Intelligent Branch Management

**创建日期**: 2026-01-28
**状态**: Planning
**目标版本**: v0.4.0 - v0.6.0
**预计工期**: 9-12 周

---

## 🎯 Epic 总览

### 战略定位

> **让分支间的演化轨迹和合并代价变得可见**
>
> 不是替代人做决策，而是提供决策所需的洞察

### 与"版本地狱治理框架"的映射

本 Epic 是框架中 **Skill B (智能同步助手)** 和 **Skill C (代码演化观察者)** 的基础实现：

```
版本地狱治理框架
├── Skill A: 债务雷达 (codeindex)          ✅ 已完成 (v0.1.0 - v0.3.2)
├── Skill B: 智能同步助手                   🔄 Epic 5 Phase 1-2
│   ├── Upstream 补丁分析                   → Story 5.1.x
│   ├── 影响范围预测                        → Story 5.2.2
│   └── 自动合并建议                        → Story 5.3.1
└── Skill C: 代码演化观察者                  🔄 Epic 5 Phase 2-3
    ├── 相似代码检测                        → Story 5.2.1
    ├── 演化轨迹追踪                        → Story 5.1.1
    └── 分叉代价估算                        → Story 5.3.3
```

### 核心问题

**当前痛点**：
1. 多分支定制版本管理困难
2. 不知道哪些功能在多个分支重复实现
3. 合并上游补丁时不清楚影响范围
4. 技术债务积累，重构无从下手

**Epic 5 解决方案**：
- ✅ 自动检测跨分支的重复代码（相似度分析）
- ✅ 预测上游变更对下游分支的影响
- ✅ 生成合并建议和重构策略
- ✅ 量化分叉的维护代价

---

## 📋 三个 Phase 渐进式交付

### Phase 1: 基础设施层 (v0.4.0)

**目标**: 提供分支对比和变更分析的基础能力
**工期**: 2-3 周
**LLM 依赖**: 无（纯本地运算）

| Story | 功能 | 输出 |
|-------|------|------|
| 5.1.1 | Git 历史分析器 | 函数/模块的演化轨迹 |
| 5.1.2 | 分支对比引擎 | 分支间代码差异报告 |
| 5.1.3 | 变更摘要生成器 | Git 变更的结构化摘要 |

**交付价值**：
- 让开发者快速了解分支差异
- 为后续 LLM 分析提供数据基础
- 可独立使用的实用工具

---

### Phase 2: 智能分析层 (v0.5.0)

**目标**: 使用 LLM 做语义级别的代码理解
**工期**: 3-4 周
**LLM 依赖**: 中等（Claude/GPT API）

| Story | 功能 | LLM 任务 | Token 消耗 |
|-------|------|---------|-----------|
| 5.2.1 | 相似代码检测 | 函数语义比对 | 10-200K |
| 5.2.2 | 影响范围预测 | 变更影响分析 | 20-50K |
| 5.2.3 | 冲突风险评估 | 冲突严重度评分 | 15-40K |

**交付价值**：
- **对应 Skill C 基础能力**：相似代码检测
- **对应 Skill B 基础能力**：影响预测
- 按 token 计费的商业模式基础

---

### Phase 3: 自动化操作层 (v0.6.0)

**目标**: 从"观察者"到"辅助操作者"
**工期**: 4-5 周
**LLM 依赖**: 高（包含复杂推理）

| Story | 功能 | 自动化程度 | Token 消耗 |
|-------|------|-----------|-----------|
| 5.3.1 | 合并建议生成 | 生成策略文档 | 30-80K |
| 5.3.2 | 自动 PR 创建 | GitHub/GitLab API | 20-50K |
| 5.3.3 | 分叉代价报告 | 历史统计 + 推算 | 50-100K |

**交付价值**：
- **对应 Skill B 完整功能**：智能同步助手
- **对应 Skill C 高级功能**：分叉代价可视化
- 真正减少手工工作量

---

## 🔍 Story 5.2.1 详细设计：相似代码检测

### 核心挑战

相似代码检测需要支持 **三种完全不同的场景**：

| 场景 | 规模 | 触发时机 | 响应时间 | Token 消耗 |
|------|------|---------|---------|-----------|
| **场景 1: 增量检测** | 小（< 1K lines） | Code Review、CI/CD | < 1分钟 | 5-20K |
| **场景 2: 跨分支比较** | 中到大 | 合并评估、分支清理 | 5-10分钟 | 50-200K |
| **场景 3: 全量审查** | 大（整个代码库） | 季度审查、重构规划 | 可后台运行 | 100K-1M+ |

### Sub-Story 拆分

#### **Story 5.2.1a: 增量重复检测** ⭐ MVP

**用户故事**：
> "我刚提交了一个 PR，想知道是否有重复代码，避免被 reviewer 打回"

**命令设计**：
```bash
# 检测当前 commit
codeindex find-duplicates --commit HEAD

# 检测特定 commit
codeindex find-duplicates --commit abc123

# 检测 PR（GitHub API）
codeindex find-duplicates --pr 123

# 只检测特定文件
codeindex find-duplicates --files src/auth.py,src/api.py
```

**技术实现**：

**两阶段过滤策略**：
1. **快速 AST 过滤**（本地，< 1秒）
   - Tree-sitter 解析新增代码
   - 与现有代码库做 AST 结构比对
   - 筛选出结构相似度 > 70% 的候选

2. **LLM 语义确认**（远程，10-30秒）
   - 只对候选进行 LLM 分析
   - 返回相似度分数 + 建议

**输出示例**：
```
🔍 Duplicate Detection (Commit abc123)

✅ Analyzed 12 new/modified functions in 8.5 seconds

Found 2 potential duplicates:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ⚠️  HIGH SIMILARITY (85%)

   New:      src/auth/login.py::authenticate_user()
             Lines 23-45 (23 lines)

   Existing: src/legacy/auth.py::user_login()
             Lines 67-92 (26 lines)

   💡 Suggestion:
   Consider reusing existing user_login() or extract
   common authentication logic to a shared function.

   🔗 View diff: codeindex compare auth/login.py:23 legacy/auth.py:67

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. ℹ️  MEDIUM SIMILARITY (72%)

   New:      src/api/validator.py::validate_email()
   Existing: src/utils/validation.py::check_email()

   💡 Suggestion:
   Small differences in error handling. May be intentional.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
   - Functions analyzed: 12
   - Duplicates found: 2 high, 1 medium
   - Token consumed: 12,450 tokens ($0.015)
   - Time: 8.5s
```

**性能优化**：
- ✅ 只分析新增/修改的代码（不是全量）
- ✅ AST 比对结果本地缓存
- ✅ LLM 批量调用（一次发送 5-10 对）
- ✅ 可配置相似度阈值（默认 70%）

**工作量**: 2-3 周
**优先级**: ⭐⭐⭐⭐⭐（最高）

---

#### **Story 5.2.1b: 跨分支重复检测** 🎯 核心

**用户故事**：
> "客户 A 和客户 B 的定制分支都实现了用户认证，我想知道能不能合并"

**命令设计**：
```bash
# 比较两个分支
codeindex find-duplicates \
  --branch feature/customer-a \
  --branch feature/customer-b

# 比较当前分支与 main
codeindex find-duplicates --branch main

# 多分支交叉比较
codeindex find-duplicates \
  --branches main,feature/a,feature/b,feature/c \
  --multi-way
```

**技术实现**：

**三阶段智能过滤**：

1. **Git Diff 提取**（快速）
   ```python
   # 提取各分支特有代码
   branch_a_unique = git diff main..feature/a
   branch_b_unique = git diff main..feature/b
   ```

2. **函数签名聚类**（本地，快）
   ```python
   # 按函数名、参数相似度分组
   # 例：authenticate_user vs user_login vs verify_user
   # → 都是 "authentication" 组
   ```

3. **LLM 语义分组**（远程，中速）
   ```python
   # 对每组函数做语义比对
   # 输出：这3个函数都是"用户认证"功能
   ```

**输出示例**：
```
🔍 Cross-Branch Duplication Analysis

Comparing:
  - feature/customer-a (352 unique functions)
  - feature/customer-b (289 unique functions)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Group 1: User Authentication (3 implementations)

┌─ feature/customer-a
│  src/auth/custom_auth.py::authenticate()
│  Lines: 45-78 (34 lines)
│
├─ feature/customer-b
│  src/security/user_login.py::verify_user()
│  Lines: 23-61 (39 lines)
│
└─ main
   src/auth/login.py::check_credentials()
   Lines: 12-38 (27 lines)

📊 Similarity Matrix:
   customer-a ↔ customer-b: 78%
   customer-a ↔ main: 62%
   customer-b ↔ main: 71%

💡 Refactoring Suggestion:
   Extract common authentication logic to:
   src/auth/base_authenticator.py::authenticate()

   Estimated effort: 4-6 hours
   Potential consolidation: 100 lines → 50 lines

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Group 2: Email Validation (2 implementations)

┌─ feature/customer-a
│  src/validators/email.py::validate()
│
└─ feature/customer-b
   src/utils/checks.py::email_check()

Similarity: 92% (almost identical!)

💡 Suggestion: Merge to main branch immediately

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Summary:
   - Total duplicate groups: 15
   - High priority (>80%): 5 groups
   - Medium priority (70-80%): 7 groups
   - Low priority (<70%): 3 groups

   Estimated duplicate lines: 1,247 (3.2% of branches)
   Potential consolidation effort: 2-3 days

   Token consumed: 87,320 tokens ($0.105)
   Analysis time: 6m 23s
```

**性能优化**（关键！）：
```python
# 问题：分支可能有数千个函数，两两比对 = O(n²)

# 解决方案：分层过滤
class BranchComparator:
    def compare(self, branch_a, branch_b):
        # 1. 签名过滤（本地，快）
        candidates = self._filter_by_signature(branch_a, branch_b)
        # 筛选：1000 函数 → 100 候选

        # 2. AST 过滤（本地，快）
        similar = self._filter_by_ast(candidates)
        # 筛选：100 候选 → 20 高相似

        # 3. LLM 确认（远程，慢）
        duplicates = self._llm_semantic_check(similar)
        # 确认：20 高相似 → 8 真重复

        return self._group_by_purpose(duplicates)
```

**工作量**: 3-4 周
**优先级**: ⭐⭐⭐⭐（高，版本地狱核心）

---

#### **Story 5.2.1c: 全量重复审查** 📊 完整

**用户故事**：
> "季度技术债务清理，想全面了解项目有多少重复代码，优先重构哪些模块"

**命令设计**：
```bash
# 全量扫描（后台运行）
codeindex find-duplicates --full-scan \
  --output duplication-report.md

# 只扫描核心模块
codeindex find-duplicates --full-scan \
  --path src/core \
  --threshold 0.75

# 按模块分组报告
codeindex find-duplicates --full-scan \
  --group-by module \
  --format json

# 增量模式（第二次扫描更快）
codeindex find-duplicates --full-scan \
  --incremental
```

**技术实现**：

**增量 + 缓存策略**（性能关键！）

```python
class FullScanDetector:
    def scan(self, project_path):
        # 1. 检查缓存数据库
        db = DuplicationCache(project_path)
        cached_results = db.load()

        # 2. 只分析变更文件
        changed_files = self._detect_changes(cached_results)

        # 3. 模块化分析（并行）
        results = []
        for module in self._split_by_module():
            # 每个模块独立分析
            duplicates = self._analyze_module(module)
            results.extend(duplicates)

        # 4. 跨模块聚类
        groups = self._cluster_duplicates(results)

        # 5. 保存缓存
        db.save(groups)

        return self._generate_report(groups)
```

**输出示例**：
```markdown
# Full Project Duplication Report

**Project**: my-ecommerce (12,345 functions analyzed)
**Analysis Date**: 2026-01-28
**Analysis Time**: 45 minutes
**Token Consumed**: 234,567 tokens ($0.28)

## 📊 Executive Summary

- **Total Duplicate Groups**: 87
- **Total Duplicate Lines**: 4,523 (3.2% of codebase)
- **Potential Savings**: ~1,800 lines after refactoring
- **Estimated Effort**: 1-2 weeks

## 🔴 High Priority (>90% similarity)

### Group 1: Database Connection Handler
**Impact**: 225 lines of nearly identical code

**Locations**:
1. `src/db/mysql.py::connect()` (45 lines)
2. `src/db/postgres.py::connect()` (48 lines)
3. `src/legacy/db_utils.py::db_connect()` (42 lines)
4. `src/api/database.py::init_connection()` (46 lines)
5. `src/worker/db.py::setup_db()` (44 lines)

**Similarity**: 94%

**Refactoring Strategy**:
```python
# Proposed: src/db/base.py
class DatabaseConnector(ABC):
    @abstractmethod
    def connect(self, config):
        pass

class MySQLConnector(DatabaseConnector):
    # specific implementation
```

**Estimated Effort**: 4 hours
**Risk**: Low (pure refactoring)

---

### Group 2: Email Validation
... (类似格式)

## 🟡 Medium Priority (70-90% similarity)
... (15 groups)

## 🟢 Low Priority (<70% similarity)
... (可选重构)

## 📈 Breakdown by Module

| Module | Duplicate Groups | Duplicate Lines | Priority |
|--------|------------------|-----------------|----------|
| `src/db` | 23 | 1,247 | 🔴 Highest |
| `src/api` | 15 | 892 | 🟡 High |
| `src/utils` | 12 | 634 | 🟡 Medium |
| `src/worker` | 8 | 421 | 🟢 Low |

## 🎯 Recommendations

1. **Immediate Actions** (Week 1)
   - Refactor `src/db` connection handlers (Group 1-5)
   - Merge email validation functions (Group 6-8)

2. **Short Term** (Month 1)
   - Create common utility library for `src/utils` duplicates
   - Establish code review checklist

3. **Long Term** (Quarter 1)
   - Consider microservices split for `src/api`
   - Implement pre-commit duplication check

## 📊 Trend Analysis (if incremental)

**Change since last scan (30 days ago)**:
- New duplicates: +12 groups (+8%)
- Resolved: -3 groups (-2%)
- Net change: +9 groups (+6%)

⚠️ **Warning**: Duplication is increasing. Consider stricter code review.
```

**性能优化策略**：
```python
# 挑战：大项目可能有 10K-100K 函数

# 策略 1: 智能采样
config = {
    "min_function_lines": 10,  # 忽略 trivial 函数
    "max_tokens": 200000,      # Token 上限
    "sample_strategy": "high_complexity_first"  # 优先分析复杂函数
}

# 策略 2: 分布式计算
# 将项目分成 N 个模块，并行分析
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(analyze_module, module)
        for module in project.modules
    ]

# 策略 3: 增量扫描
# 首次：全量扫描 → 存 SQLite
# 后续：只扫变更文件 → 更新缓存
# 每月：全量刷新
```

**工作量**: 2-3 周
**优先级**: ⭐⭐⭐（中）

---

## 🏗️ 技术架构

### 核心组件设计

```python
# 组件 1: DuplicateDetector（核心引擎）
class DuplicateDetector:
    """统一的重复代码检测引擎"""

    def __init__(self, similarity_threshold=0.7, use_llm=True):
        self.threshold = threshold
        self.use_llm = use_llm
        self.cache = DuplicationCache()

    def detect(self, scope: DetectionScope) -> DuplicationReport:
        """统一入口，支持所有场景"""
        candidates = self._extract_candidates(scope)
        pairs = self._fast_filter(candidates)
        if self.use_llm:
            similarities = self._llm_compare(pairs)
        else:
            similarities = self._ast_compare(pairs)
        return self._generate_report(similarities)

# 组件 2: DetectionScope（场景抽象）
class DetectionScope:
    """抽象不同检测场景"""
    pass

class CommitScope(DetectionScope):
    """场景 1: 单个 commit"""
    def __init__(self, commit_sha: str):
        self.commit = commit_sha

class BranchScope(DetectionScope):
    """场景 2: 跨分支"""
    def __init__(self, branches: List[str]):
        self.branches = branches

class FullScanScope(DetectionScope):
    """场景 3: 全量"""
    def __init__(self, path: str = "."):
        self.path = path

# 组件 3: SimilarityComparator（相似度计算）
class SimilarityComparator:
    def ast_similarity(self, func_a, func_b) -> float:
        """AST 结构相似度（快速，本地）"""
        # Tree-sitter AST diff

    def semantic_similarity(self, func_a, func_b) -> float:
        """语义相似度（LLM）"""
        # LLM prompt: "Compare these two functions semantically"

    def hybrid_similarity(self, func_a, func_b) -> float:
        """混合策略（先 AST 再 LLM）"""
        ast_sim = self.ast_similarity(func_a, func_b)
        if ast_sim > 0.6:
            return self.semantic_similarity(func_a, func_b)
        return ast_sim

# 组件 4: DuplicationCache（性能优化）
class DuplicationCache:
    """SQLite 缓存相似度结果"""

    def __init__(self):
        self.db = sqlite3.connect(".codeindex/duplication.db")

    def get(self, func_a_hash, func_b_hash) -> Optional[float]:
        """查询缓存"""

    def set(self, func_a_hash, func_b_hash, similarity: float):
        """写入缓存"""
```

### 配置文件设计

```yaml
# .codeindex.yaml 扩展

# 相似代码检测配置
duplication:
  # 相似度阈值
  similarity_threshold: 0.7

  # 检测方法
  detection_method: "hybrid"  # "ast" | "semantic" | "hybrid"

  # LLM 设置
  llm:
    enabled: true
    model: "claude-sonnet"
    max_tokens_per_scan: 100000  # 防止超支

  # 性能优化
  cache:
    enabled: true
    ttl_days: 30  # 缓存 30 天

  # 过滤规则
  ignore:
    - "test/*"  # 忽略测试代码
    - "*/migrations/*"

  min_function_lines: 10  # 忽略小于 10 行的函数

  # 白名单（已知的"故意不同"）
  whitelist:
    - ["src/auth/login.py::login", "src/auth/oauth.py::oauth_login"]
```

### CLI 命令统一接口

```bash
# 场景 1: 增量检测
codeindex find-duplicates --commit HEAD
codeindex find-duplicates --pr 123
codeindex find-duplicates --since HEAD~5

# 场景 2: 跨分支
codeindex find-duplicates --branch feature/a --branch feature/b
codeindex find-duplicates --branches main,feature/a,feature/b

# 场景 3: 全量
codeindex find-duplicates --full-scan
codeindex find-duplicates --full-scan --path src/core

# 通用选项
--threshold 0.75           # 相似度阈值
--method semantic          # 检测方法
--output report.md         # 输出文件
--format markdown|json     # 输出格式
--no-llm                   # 只用 AST，不用 LLM
--max-tokens 50000         # LLM token 上限
--cache                    # 使用缓存
--progress                 # 显示进度条
```

---

## 🤖 LLM Prompt 设计

### Prompt 1: 语义相似度判断

```
You are a code similarity analyzer. Compare the following two functions and determine their semantic similarity.

Function A:
```python
{function_a_code}
```

Function B:
```python
{function_b_code}
```

Analyze:
1. Do they achieve the same goal?
2. Are the core algorithms similar?
3. What are the key differences?

Respond in JSON format:
{
  "similarity_score": 0.0-1.0,
  "is_duplicate": true/false,
  "reasoning": "brief explanation",
  "key_differences": ["diff1", "diff2"],
  "recommendation": "reuse|refactor|keep_separate"
}
```

### Prompt 2: 重复代码分组

```
You are analyzing multiple similar functions. Group them by their semantic purpose.

Functions:
1. src/a.py::func1()
   ```python
   {code1}
   ```

2. src/b.py::func2()
   ```python
   {code2}
   ```

3. src/c.py::func3()
   ```python
   {code3}
   ```

For each function, provide:
- Purpose summary
- Group ID (functions with same purpose get same ID)

Output JSON:
{
  "groups": [
    {
      "group_id": "auth_validation",
      "purpose": "User authentication validation",
      "functions": [1, 2, 5]
    },
    ...
  ]
}
```

### Prompt 3: 重构建议

```
Given these duplicate functions, suggest a refactoring strategy.

Duplicate Group:
- Function A:
  ```python
  {code_a}
  ```

- Function B:
  ```python
  {code_b}
  ```

- Function C:
  ```python
  {code_c}
  ```

Provide:
1. Common logic that can be extracted
2. Differences that need parameterization
3. Proposed abstract function signature
4. Estimated effort (hours)

Output as structured markdown.
```

---

## 🧩 扩展场景（可选）

### 场景 4: 跨项目比较

```bash
# 公司有多个相关项目
codeindex find-duplicates \
  --projects project-a,project-b,project-c

# 用例：发现可提取的公共库
```

### 场景 5: 与开源库比较

```bash
# 检测是否"重新发明轮子"
codeindex find-duplicates --check-opensource

# 例：检测到你的 sort() 函数与 Python 内置很相似
# → 建议直接用标准库
```

### 边界情况处理

**1. False Positives（误报）**
```yaml
# .codeindex.yaml
duplication:
  whitelist:
    # 相似但有意设计不同的函数对
    - ["src/auth/login.py::login", "src/auth/oauth.py::oauth_login"]
```

**2. 隐私模式**
```bash
# 不想代码发送到 LLM
codeindex find-duplicates --no-llm --method ast

# 只用 AST 结构比对，不用语义分析
```

**3. 进度跟踪**
```bash
# 大项目全量扫描，需要进度条
[████████░░░░░░░░░░] 45% (4523/10000 functions)
Estimated time remaining: 12m 34s
```

---

## 📅 实施时间表

### 2026-02 (6 周) - Phase 1

| Week | 任务 | 交付物 |
|------|------|--------|
| 1-2 | Story 5.1.1: Git 历史分析器 | `codeindex git-history` 命令 |
| 3-4 | Story 5.1.2: 分支对比引擎 | `codeindex compare-branches` 命令 |
| 5 | Story 5.1.3: 变更摘要生成 | `codeindex summarize-changes` 命令 |
| 6 | v0.4.0 发布 + Phase 2 规划 | Release v0.4.0 |

### 2026-03 (6 周) - Phase 2

| Week | 任务 | 交付物 |
|------|------|--------|
| 1-2 | Story 5.2.1a: 增量重复检测 | 基础功能 + LLM 集成 |
| 3 | Story 5.2.1a: 优化和测试 | MVP 完成 |
| 4-5 | Story 5.2.2: 影响范围预测 | `predict-impact` 命令 |
| 6 | Story 5.2.3: 冲突风险评估 | `assess-conflicts` 命令 |

### 2026-04 (4 周) - Phase 2 完成

| Week | 任务 | 交付物 |
|------|------|--------|
| 1-2 | Story 5.2.1b: 跨分支检测 | 核心价值功能 |
| 3 | Story 5.2.1c: 全量审查 | 完整能力 |
| 4 | v0.5.0 发布 | Release v0.5.0 |

### 2026-05 (5 周) - Phase 3

| Week | 任务 | 交付物 |
|------|------|--------|
| 1-2 | Story 5.3.1: 合并建议生成 | 智能建议功能 |
| 3-4 | Story 5.3.2: 自动 PR 创建 | GitHub/GitLab 集成 |
| 5 | Story 5.3.3: 分叉代价报告 | 完整报告功能 |

### 2026-06 (1 周) - Epic 5 完成

| Week | 任务 | 交付物 |
|------|------|--------|
| 1 | 集成测试 + 文档完善 | Release v0.6.0 |

---

## 💰 商业模式

### Token 消耗估算

| 功能 | 场景 | Token 消耗 | 预估成本 (Claude Sonnet) |
|------|------|-----------|-------------------------|
| 增量检测 | 单个 commit | 5-20K | $0.006 - $0.024 |
| 跨分支比较 | 2 个分支 | 50-200K | $0.06 - $0.24 |
| 全量审查 | 中型项目 | 100-500K | $0.12 - $0.60 |
| 全量审查 | 大型项目 | 500K-1M | $0.60 - $1.20 |

### 定价策略

| 套餐 | 包含功能 | 月度额度 | 适用场景 |
|------|---------|---------|---------|
| 基础版 | Phase 1 (本地) | 免费 | 单仓库技术债务 |
| 专业版 | Phase 1+2 | 1M tokens | 小团队（5-10人） |
| 企业版 | Phase 1+2+3 | 5M tokens | 多分支版本管理 |

---

## ✅ 验收标准

### Phase 1 (v0.4.0)

- [ ] Git 历史分析器能够追踪函数演化
- [ ] 分支对比引擎准确识别代码差异
- [ ] 变更摘要生成结构化报告
- [ ] 所有功能纯本地运算（无 LLM）
- [ ] 文档完整，包含使用示例

### Phase 2 (v0.5.0)

- [ ] 增量检测准确率 > 85%
- [ ] 跨分支检测能处理 1000+ 函数
- [ ] 影响范围预测误报率 < 15%
- [ ] LLM token 消耗在预期范围内
- [ ] 支持缓存和增量计算

### Phase 3 (v0.6.0)

- [ ] 合并建议质量可用（人工评估）
- [ ] 自动 PR 创建成功率 > 90%
- [ ] 分叉代价报告准确反映维护成本
- [ ] GitHub/GitLab API 集成稳定
- [ ] 完整的用户文档和 API 文档

---

## 🎯 下一步行动

**立即可以开始的工作**：

1. **技术预研**（1-2 天）
   - GitPython vs pygit2 对比
   - Branch diff 算法调研
   - AST 相似度算法选型

2. **设计 Story 5.1.1 详细方案**（2-3 天）
   - TDD 测试用例设计
   - 数据结构定义
   - CLI 命令接口设计

3. **准备开发环境**（1 天）
   - 安装 GitPython
   - 准备测试用的多分支仓库
   - 配置 LLM API keys

**需要决策的问题**：

1. ✅ 是否认同这个 Epic 规划？
2. ⏸️ Phase 1 是否先做 MVP 快速验证？
3. ⏸️ LLM 集成优先 Claude 还是支持多模型？
4. ⏸️ 是否需要 Web UI 或只提供 CLI？

---

## 📚 相关文档

- [版本地狱治理方案框架](../../Desktop/一行码云/版本地狱治理方案-框架.md)
- [Epic 4: Code Refactoring Plan](./epic4-refactoring-plan.md)
- [CHANGELOG.md](../../CHANGELOG.md)
- [README.md](../../README.md)

---

**文档状态**: ✅ Complete
**最后更新**: 2026-01-28
**责任人**: Development Team
**审核人**: Pending
