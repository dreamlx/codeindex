# CodeIndex 系统设计方案

> AI 原生代码库索引系统 - 让 AI Coder 快速理解超大规模代码库

## 1. 问题背景

### 痛点
- 老项目规模巨大（单文件 4000+ 行，代码库几百 GB）
- 直接用 AI Coder 访问非常慢
- 缺少全局架构理解
- 上下文窗口限制导致注意力流失

### 解决思路
**局部自治 + 全局视图** 的分层索引架构：
- 每个目录生成局部索引（`README_AI.md`）
- 支持渐进式读取，AI 进入目录即可感知上下文
- 通过 `provides/consumes` 钩子支持全局图谱构建

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CodeIndex System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   CI/CD      │    │   Git Hook   │    │ Claude Code  │   │
│  │  Pipeline    │    │  post-commit │    │    Skill     │   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              codeindex CLI (Python)                  │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐  │    │
│  │  │ Scanner │ │ Parser  │ │Summarizer│ │  Writer   │  │    │
│  │  │(并行)   │ │(AST)    │ │(LLM)     │ │(Markdown) │  │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                README_AI.md (分散存储)               │    │
│  │   src/auth/README_AI.md                              │    │
│  │   src/services/README_AI.md                          │    │
│  │   src/dao/README_AI.md                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 核心设计原则

1. **Skill 是 "智能调度器"，CLI 是 "执行引擎"**
   - Skill 指导 Claude 如何使用工具和读取索引
   - CLI 执行实际的扫描、解析、生成工作

2. **分散存储，按需聚合**
   - 每个目录独立的 `README_AI.md`
   - 全局图谱按需生成（V2）

3. **MapReduce 思想**
   - Map：每个目录的索引生成
   - Reduce：全局图谱聚合（可选）

---

## 3. CLI 工具设计

### 3.1 安装与命令

```bash
# 安装
pip install codeindex

# 核心命令
codeindex init                    # 初始化配置文件
codeindex scan <path>             # 扫描单个目录
codeindex scan-all                # 扫描整个项目
codeindex scan-all --parallel=8   # 8 进程并行
codeindex status                  # 查看索引覆盖情况
codeindex clean                   # 删除所有索引文件
```

### 3.2 配置文件 `.codeindex.yaml`

```yaml
# 基础配置
version: 1
output_file: README_AI.md

# 扫描范围
include:
  - src/
  - lib/
exclude:
  - "**/test/**"
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/build/**"
  - "**/dist/**"

# LLM 配置
llm:
  provider: anthropic          # anthropic | openai | local
  model: claude-3-haiku        # 默认用便宜的模型
  model_deep: claude-sonnet-4  # 复杂模块用更强的模型

# 并行配置
parallel:
  workers: 4                   # 并行 worker 数
  rate_limit: 50               # requests per minute

# 语言支持
languages:
  - java
  - python
  - javascript
  - typescript
  - go
  - kotlin

# 索引深度
depth:
  default: class               # 默认类级别
  entry_points: method         # 入口点方法级别
```

### 3.3 核心模块设计

```python
# 模块结构
codeindex/
├── __init__.py
├── cli.py              # CLI 入口
├── config.py           # 配置管理
├── scanner.py          # 目录扫描器
├── parser/
│   ├── __init__.py
│   ├── base.py         # 解析器基类
│   ├── java.py         # Java AST 解析
│   ├── python.py       # Python AST 解析
│   └── typescript.py   # TypeScript 解析
├── summarizer.py       # LLM 摘要生成
├── writer.py           # Markdown 写入
└── utils/
    ├── rate_limiter.py # API 限流
    └── hash.py         # 文件哈希
```

---

## 4. 索引文件格式

### 4.1 README_AI.md 完整格式

```markdown
---
# 元数据区（机器解析）
path: src/services/auth
type: module
languages: [java, kotlin]
complexity: high
last_indexed: 2025-01-15T10:00:00Z
content_hash: abc123def456

# 语义钩子 - 图谱构建关键
provides:
  - symbol: AuthService
    type: class
    signature: "public class AuthService implements IAuthProvider"
    description: 核心认证服务
  - symbol: JwtTokenManager
    type: class
    description: JWT 令牌管理

consumes:
  - ref: src/common/config/ConfigLoader
    usage: configuration
  - ref: src/dao/UserRepository
    usage: data-access
  - ref: external:spring-security
    usage: framework

entry_points:
  - symbol: AuthController.login
    http: POST /api/auth/login
  - symbol: AuthController.logout
    http: POST /api/auth/logout

exports_to: []  # 反向链接，由 sync-graph 填充（V2）
---

# Auth 模块

## 职责
处理用户认证、JWT 令牌管理、权限校验。

## 技术栈
- Spring Security
- JWT (io.jsonwebtoken)
- BCrypt 密码加密

## 核心类

### AuthService
认证核心逻辑，支持 OAuth2 和本地认证。
- `authenticate(username, password)`: 验证用户凭据
- `refreshToken(token)`: 刷新访问令牌

### JwtTokenManager
JWT 生成与验证。
- `generateToken(user)`: 生成访问令牌
- `validateToken(token)`: 验证令牌有效性
- `extractClaims(token)`: 提取令牌信息

## 关键流程

### 用户登录
1. `AuthController.login` 接收请求
2. `AuthService.authenticate` 验证凭据
3. `JwtTokenManager.generateToken` 生成令牌
4. 返回访问令牌和刷新令牌

### 令牌刷新
1. `AuthController.refresh` 接收刷新令牌
2. `JwtTokenManager.validateToken` 验证有效性
3. `JwtTokenManager.generateToken` 生成新令牌

## 配置依赖
- `jwt.secret`: JWT 签名密钥
- `jwt.expiration`: 令牌过期时间（秒）
- `jwt.refresh-expiration`: 刷新令牌过期时间

## 注意事项
- 密钥存储在环境变量，不要硬编码
- 敏感操作（修改密码）需要二次验证
- 令牌黑名单存储在 Redis
```

### 4.2 目录结构示例

```
project-root/
├── .codeindex.yaml           # 配置文件
├── .codeindex/               # 全局索引目录（V2）
│   └── global_graph.json     # 全局拓扑
│
├── src/
│   ├── README_AI.md          # src 目录概览
│   │
│   ├── auth/
│   │   ├── README_AI.md      # auth 模块索引
│   │   ├── AuthService.java
│   │   └── JwtTokenManager.java
│   │
│   ├── services/
│   │   ├── README_AI.md      # services 模块索引
│   │   ├── user/
│   │   │   └── README_AI.md
│   │   └── order/
│   │       └── README_AI.md
│   │
│   └── dao/
│       └── README_AI.md
```

---

## 5. Claude Code Skill 设计

### 5.1 /sc:index-repo - 索引生成

创建文件 `~/.claude/skills/index-repo.md`:

```markdown
---
name: index-repo
description: 为代码库生成 AI 友好的索引
version: 1.0.0
---

# 索引生成 Skill

## 触发场景
- 用户说"索引这个项目"/"生成代码索引"
- 首次接触大型代码库
- 代码库结构发生重大变化

## 前置检查
1. 检查 codeindex 是否安装：
   ```bash
   which codeindex || echo "请先安装: pip install codeindex"
   ```

2. 检查配置文件：
   ```bash
   cat .codeindex.yaml 2>/dev/null || echo "需要初始化配置"
   ```

## 执行流程

### 首次索引
```bash
# 1. 初始化配置（如果不存在）
codeindex init

# 2. 让用户确认/调整配置
# 显示 .codeindex.yaml 内容

# 3. 执行全量索引
codeindex scan-all --parallel=4

# 4. 显示结果
codeindex status
```

### 更新索引
```bash
# 只扫描指定目录
codeindex scan src/services/auth
```

## 输出解读
- 扫描了多少目录/文件
- 生成了多少 README_AI.md
- 耗时和 API 调用次数
- 任何错误或警告

## 注意事项
- 大项目首次索引建议在 CI/CD 中运行
- 需要设置 ANTHROPIC_API_KEY 环境变量
- 索引文件建议加入 .gitignore（或提交到仓库供团队共享）
```

### 5.2 /sc:arch-query - 架构查询

创建文件 `~/.claude/skills/arch-query.md`:

```markdown
---
name: arch-query
description: 基于索引回答代码架构问题
version: 1.0.0
---

# 架构查询 Skill

## 触发场景
- 用户询问"这个项目是做什么的"
- 用户询问"XX功能在哪里实现"
- 用户询问"XX模块的依赖关系"
- 用户需要理解代码架构

## 索引文件说明

### 位置
每个目录下的 `README_AI.md`

### 关键字段（YAML Front-matter）
- `path`: 当前目录路径
- `provides`: 该模块提供的符号（类、函数）
- `consumes`: 该模块依赖的其他模块
- `entry_points`: 对外暴露的入口点

### 内容区（Markdown）
- 模块职责描述
- 核心类/函数说明
- 关键流程
- 注意事项

## 查询策略

### 1. 整体了解
```bash
# 读取项目根目录或 src 目录的索引
cat src/README_AI.md
```

### 2. 定位模块
根据用户问题中的关键词，找到相关目录的索引：
```bash
# 例如用户问认证相关
cat src/auth/README_AI.md
cat src/services/auth/README_AI.md
```

### 3. 追踪依赖
使用 `consumes` 字段追踪依赖链：
```yaml
consumes:
  - ref: src/dao/UserRepository
```
然后读取 `src/dao/README_AI.md`

### 4. 深入细节
必要时读取具体源码文件

## 示例对话

**用户**: 用户登录是怎么实现的？

**AI 执行步骤**:
1. 读取 `src/README_AI.md` 了解项目结构
2. 找到 auth 相关模块，读取 `src/auth/README_AI.md`
3. 从 entry_points 找到 `AuthController.login`
4. 从 consumes 追踪到数据访问层
5. 综合信息回答用户

## 无索引时的降级策略
如果目录下没有 README_AI.md：
1. 提示用户运行 `/sc:index-repo`
2. 或使用传统方式（Glob + Grep + Read）探索代码
```

---

## 6. 工作流集成

### 6.1 工作流全景

```
┌─────────────────────────────────────────────────────────────┐
│                     工作流全景                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  【首次索引 - CI/CD】                                         │
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐       │
│  │ Clone  │ -> │ Init   │ -> │ Scan   │ -> │ Commit │       │
│  │ Repo   │    │ Config │    │ All    │    │ Index  │       │
│  └────────┘    └────────┘    └────────┘    └────────┘       │
│                                                              │
│  【日常开发 - Git Hook】                                      │
│  ┌────────┐    ┌────────┐    ┌────────┐                     │
│  │ Commit │ -> │  Hook  │ -> │ Update │                     │
│  │ Code   │    │Trigger │    │ Index  │                     │
│  └────────┘    └────────┘    └────────┘                     │
│                                                              │
│  【AI 辅助开发 - Skill】                                      │
│  ┌────────┐    ┌────────┐    ┌────────┐                     │
│  │ Ask Q  │ -> │ Read   │ -> │ Answer │                     │
│  │        │    │ Index  │    │        │                     │
│  └────────┘    └────────┘    └────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Git Hook 配置

**文件**: `.git/hooks/post-commit`

```bash
#!/bin/bash
# CodeIndex 增量更新 Hook

# 检查 codeindex 是否安装
if ! command -v codeindex &> /dev/null; then
    exit 0
fi

# 获取变更的目录（去重）
changed_dirs=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | xargs -I {} dirname {} | sort -u)

if [ -z "$changed_dirs" ]; then
    exit 0
fi

echo "[CodeIndex] Updating index for changed directories..."

# 并行更新索引
for dir in $changed_dirs; do
    if [ -d "$dir" ]; then
        codeindex scan "$dir" --quiet &
    fi
done
wait

echo "[CodeIndex] Index update complete"
```

**安装脚本**: `scripts/install-hooks.sh`

```bash
#!/bin/bash
# 安装 Git Hook

HOOK_DIR=".git/hooks"
HOOK_FILE="$HOOK_DIR/post-commit"

# 确保 hooks 目录存在
mkdir -p "$HOOK_DIR"

# 写入 hook
cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# CodeIndex 增量更新 Hook
if ! command -v codeindex &> /dev/null; then
    exit 0
fi
changed_dirs=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | xargs -I {} dirname {} | sort -u)
if [ -z "$changed_dirs" ]; then
    exit 0
fi
for dir in $changed_dirs; do
    if [ -d "$dir" ]; then
        codeindex scan "$dir" --quiet &
    fi
done
wait
EOF

chmod +x "$HOOK_FILE"
echo "Git hook installed: $HOOK_FILE"
```

### 6.3 GitHub Actions

**文件**: `.github/workflows/codeindex.yml`

```yaml
name: Update Code Index

on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'lib/**'
  workflow_dispatch:
    inputs:
      full_scan:
        description: 'Run full scan instead of incremental'
        required: false
        default: 'false'

jobs:
  index:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 2  # 需要比较上一个 commit

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install codeindex
        run: pip install codeindex

      - name: Run incremental indexing
        if: github.event.inputs.full_scan != 'true'
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          changed_dirs=$(git diff --name-only HEAD~1 HEAD | xargs -I {} dirname {} | sort -u)
          for dir in $changed_dirs; do
            if [ -d "$dir" ]; then
              codeindex scan "$dir"
            fi
          done

      - name: Run full indexing
        if: github.event.inputs.full_scan == 'true'
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: codeindex scan-all --parallel=4

      - name: Commit index files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add "**/README_AI.md"
          git diff --staged --quiet || git commit -m "chore: update code index [skip ci]"
          git push
```

### 6.4 GitLab CI

**文件**: `.gitlab-ci.yml`

```yaml
stages:
  - index

update-index:
  stage: index
  image: python:3.11
  only:
    - main
    - develop
  script:
    - pip install codeindex
    - codeindex scan-all --parallel=4
    - git config user.name "GitLab CI"
    - git config user.email "ci@gitlab.com"
    - git add "**/README_AI.md"
    - git diff --staged --quiet || git commit -m "chore: update code index [skip ci]"
    - git push https://oauth2:${CI_JOB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git HEAD:${CI_COMMIT_REF_NAME}
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

---

## 7. 版本规划

### V1 - MVP（当前目标）

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 单目录扫描 | P0 | 核心功能 |
| 多目录并行 | P0 | 性能关键 |
| README_AI.md 生成 | P0 | 基础格式 |
| provides/consumes 钩子 | P0 | 类级别 |
| 多语言 AST 解析 | P1 | Java/Python/JS/TS |
| Git Hook 脚本 | P1 | 模板提供 |
| CI/CD 模板 | P1 | GitHub/GitLab |
| LLM 摘要生成 | P1 | Haiku 为主 |

### V2 - 增强

| 功能 | 说明 |
|------|------|
| 全局图谱聚合 | sync-graph 命令 |
| 方法级细粒度 | 针对 entry_points |
| 增量检测优化 | 基于文件 hash |
| 缓存机制 | 避免重复 API 调用 |
| 自定义模板 | 支持不同格式输出 |

### V3 - 高级

| 功能 | 说明 |
|------|------|
| 向量搜索 | 语义搜索索引 |
| 可视化 | 依赖图谱可视化 |
| IDE 插件 | VSCode/IntelliJ 集成 |
| 多仓库支持 | Monorepo 优化 |

---

## 8. 实现建议

### 8.1 推荐技术栈

```
Python 3.11+
├── Click           # CLI 框架
├── tree-sitter     # 多语言 AST 解析
├── anthropic       # Claude API
├── pydantic        # 配置/数据模型
├── rich            # 终端美化
└── multiprocessing # 并行处理
```

### 8.2 关键实现点

1. **AST 解析器**
   - 使用 tree-sitter 支持多语言
   - 提取类、函数、导入语句
   - 生成结构化的符号表

2. **LLM 摘要**
   - 分块处理大文件（<4000 tokens/块）
   - Haiku 做初步分析
   - 关键模块用 Sonnet
   - 实现 rate limiter

3. **并行处理**
   - 按目录划分任务
   - 共享 rate limiter
   - 进度条显示

4. **输出格式**
   - YAML front-matter + Markdown
   - 支持机器解析和人类阅读

### 8.3 目录结构建议

```
codeindex/
├── pyproject.toml
├── README.md
├── src/
│   └── codeindex/
│       ├── __init__.py
│       ├── __main__.py      # python -m codeindex
│       ├── cli.py           # Click CLI
│       ├── config.py        # Pydantic 配置
│       ├── scanner.py       # 目录扫描
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── java.py
│       │   ├── python.py
│       │   └── typescript.py
│       ├── summarizer.py    # LLM 调用
│       ├── writer.py        # Markdown 生成
│       └── utils/
│           ├── rate_limiter.py
│           └── hash.py
├── tests/
└── examples/
    ├── .codeindex.yaml
    └── README_AI.md
```

---

## 9. 快速开始（实现后）

```bash
# 1. 安装
pip install codeindex

# 2. 初始化项目
cd your-project
codeindex init

# 3. 编辑配置（可选）
vim .codeindex.yaml

# 4. 设置 API Key
export ANTHROPIC_API_KEY=your-key

# 5. 运行索引
codeindex scan-all --parallel=4

# 6. 查看状态
codeindex status

# 7. 安装 Git Hook（可选）
./scripts/install-hooks.sh
```

---

## 附录 A: 常见问题

### Q: 索引文件应该提交到 Git 吗？
建议提交。这样团队成员和 CI 环境都能共享索引，AI Coder 也能直接读取。

### Q: 如何处理敏感信息？
索引只包含结构描述，不包含实际代码逻辑。但如果担心，可以把 README_AI.md 加入 .gitignore。

### Q: 大文件如何处理？
分块处理。4000 行的文件会被分成多个块，分别分析后合并。

### Q: API 成本估算？
- 小项目（100 个目录）：约 $1-2（使用 Haiku）
- 大项目（1000 个目录）：约 $10-20
- 增量更新成本很低

---

*文档版本: 1.0.0*
*创建日期: 2025-01-15*
*作者: AI 协作设计*
