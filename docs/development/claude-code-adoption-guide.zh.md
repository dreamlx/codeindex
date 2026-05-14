# 在老项目中接入 Claude Code

> 本指南面向已有运行中项目、希望升级 Claude Code 使用方式的程序员。语言无关，以迁移为核心。
>
> 读完本文后再读 [`team-workflow-guide.md`](team-workflow-guide.md) —— 那份文档描述的是目标状态，本文告诉你从现在出发怎么到达那里。
>
> **English version**: [claude-code-adoption-guide.md](claude-code-adoption-guide.md)

---

## 核心认知：Claude Code 的效果上限由你给的上下文决定

大多数团队把 Claude Code 当成更聪明的自动补全：粘贴代码、提问、拿到答案。这能用，但浪费了 80% 的价值。

一次有用的 Claude Code 会话和一次令人抓狂的会话，差别几乎总是同一件事：**在你提第一个问题之前，Claude 是否已经理解了你的项目**。

Claude Code 可以访问你的文件和终端，但它不会自动知道：
- 这个项目是干什么的
- 你们遵循什么约定
- 装了哪些工具
- 哪些文件不能动
- 这里的"完成"意味着什么

没有这些上下文，Claude Code 会套用通用模式，这些模式往往和你的代码库冲突。有了它，Claude Code 的表现就像一个已经熟悉这个 repo 的高级工程师。

**提供上下文的方式：`CLAUDE.md`**

---

## 第一部分：CLAUDE.md —— 基础中的基础

### 它是什么

`CLAUDE.md` 是一个普通的 Markdown 文件，Claude Code 在每次会话开始时都会读取它。它是你的项目给 AI 的常驻指令。把它理解成一份 README —— 但读者是 Claude Code，不是人类。

两个层级：
- `~/.claude/CLAUDE.md` —— 全局规则，适用于你所有项目（装一次）
- `<项目根目录>/CLAUDE.md` —— 项目专属规则（提交到 repo）

项目级 `CLAUDE.md` 与全局冲突时优先生效。

### 如何创建

```bash
# 最快的方式：让 Claude Code 生成初稿
# 在项目目录下的 Claude Code 中运行：
/init
```

`/init` 斜杠命令读取你的项目结构，生成一份 `CLAUDE.md` 初稿。然后你编辑它，补上它遗漏的内容。

### CLAUDE.md 应该写什么

一份好的 `CLAUDE.md` 要回答 Claude Code 的这几个问题：

**1. 如何在代码库里导航**
```markdown
## 代码导航
- 入口：`src/app.ts` / `cmd/server/main.go` / `manage.py`
- 核心模块：`src/services/`（业务逻辑）、`src/api/`（HTTP 层）
- 测试：`tests/unit/`、`tests/integration/`
- 禁止修改：`src/generated/`（从 protobuf 自动生成）
```

**2. 如何运行项目**
```markdown
## 命令
- 安装：`npm ci` / `pip install -e ".[dev]"` / `./gradlew build`
- 测试：`npm test` / `pytest -v` / `./gradlew test`
- Lint：`npm run lint` / `ruff check src/` / `./gradlew ktlintCheck`
- 开发服务器：`npm run dev` / `uvicorn app:main --reload`
```

**3. 从代码看不出来的约定**
```markdown
## 约定
- 分支命名：`feature/ticket-NNN-简短描述`
- 提交格式：`feat(auth): add JWT refresh token support`
- API 错误统一返回 `{ error: { code, message } }`，不返回裸字符串
- 数据库迁移文件在 `db/migrations/`，合并后禁止修改
```

**4. 禁止事项**
```markdown
## 禁止
- 禁止对 develop 或 main 执行 `git push --force`
- 禁止手动修改 `package-lock.json`
- 禁止在生产代码中使用 `console.log`，使用 `src/utils/logger.ts` 中的 logger
- 测试禁止访问真实网络或数据库，使用 `tests/fixtures/` 中的 fixture
```

**5. 让新人意外的架构决策**
```markdown
## 架构说明
- 我们使用 CQRS：读走 `QueryBus`，写走 `CommandBus`
- 鉴权中间件在路由 handler 之前运行，禁止在 handler 内部加鉴权检查
- 所有外部 API 调用必须经过 `src/gateways/`，不允许在 service 层直接调用 fetch/axios
```

### CLAUDE.md 不应该写什么

- 显而易见的事（`npm install` 安装依赖）
- README.md 里已有、Claude 自己能读到的内容
- 手把手教程 —— Claude Code 读的是指令，不是教程
- 超过约 200 行 —— 太长的 CLAUDE.md 实际上会被忽略

### 好坏对比

| 坏写法（过于模糊） | 好写法（具体可执行） |
|-----------------|-----------------|
| "遵循最佳实践" | "错误：抛出 `src/errors.ts` 中的 `AppError`，不用原生 `Error`" |
| "要写测试" | "测试：用 `jest`，覆盖率阈值 75%，运行命令 `npm test`" |
| "使用 logger" | "日志：`import logger from '@/utils/logger'`，禁止 `console.*`" |
| "小心操作数据库" | "DB：禁止写裸 SQL，使用 `src/repositories/` 中的 Repository 模式" |

---

## 第二部分：给 Claude Code 一张代码地图

CLAUDE.md 告诉 Claude Code 规则。但对于大型代码库，它还需要一张**地图** —— 一种不读每个文件就能理解结构的方式。

### README_AI.md 模式

codeindex 工具为每个目录生成一个 `README_AI.md`，描述该目录包含什么、关键导出是什么、与其他模块的关系。这些文件和源码放在一起，Claude Code 在深入源文件之前会先读它们。

```bash
# 安装 codeindex
pip install ai-codeindex

# 为你的项目生成索引（支持 Python、JS/TS、Java、PHP、Swift）
codeindex init          # 创建 .codeindex.yaml + 将 README_AI.md 加入 .gitignore
codeindex scan-all      # 在每个目录生成 README_AI.md

# 代码变更后，重新扫描
codeindex scan ./src/changed-module
```

效果：Claude Code 第一次就能正确回答"X 在哪里实现的？"，不用搜遍整个代码库。

### 手动替代方案（不用 codeindex 的情况）

在根目录写一个 `PROJECT_MAP.md`，按模块描述。精度不如逐目录文件，但远好于什么都没有：

```markdown
# 项目模块地图

## src/auth/
JWT 鉴权。关键导出：`AuthMiddleware`、`JwtService`、`TokenBlacklist`。
入口：`auth.module.ts`。不处理权限，权限见 `src/rbac/`。

## src/payments/
Stripe 集成。`PaymentService.charge()` 是主入口。
不要直接实例化，通过 `PaymentsModule` DI。
所有 webhook 处理在 `src/payments/webhooks/`。
```

在 `CLAUDE.md` 中引用它：
```markdown
## 代码导航
搜索任何模块前，先读 `PROJECT_MAP.md`。
```

---

## 第三部分：迁移路径 —— 从哪里开始

不要一次性全部采用。以下是按影响力 vs 投入排序的优先级：

### 阶段 0 —— 上下文建立（第 1 天，2 小时）
*解锁后续所有步骤。在用 Claude Code 写第一行代码之前先做这件事。*

1. 在 Claude Code 中运行 `/init` 生成 `CLAUDE.md` 初稿
2. 编辑 `CLAUDE.md`：补充命令、约定、禁止事项
3. 运行 `codeindex scan-all` 生成目录地图（或手写 `PROJECT_MAP.md`）
4. 验收：问 Claude Code"用户鉴权在哪里实现的？"，看答案是否正确

**成功信号**：Claude Code 不靠猜就能导航到正确文件。

### 阶段 1 —— Git 纪律（第 1 周）
*让 Claude Code 的提交安全可追踪。*

1. 确定分支命名约定（`feature/`、`fix/`）
2. 采用约定式提交格式 —— 写进 `CLAUDE.md`
3. 加 pre-commit hook 跑 lint（工具见下方对照表）

pre-commit hook 是一次性安装，之后自动执行质量检查。Claude Code 会遵守 hook，不会建议你绕过它。

**各语言 hook 安装：**

```bash
# Python
pip install pre-commit
# 创建 .pre-commit-config.yaml
pre-commit install

# JavaScript/TypeScript
npm install --save-dev husky lint-staged
npx husky init

# 任意语言（原始 git hook）
cat > .git/hooks/pre-commit << 'EOF'
#!/usr/bin/env bash
set -e
# 插入你的 lint 命令
npm run lint    # 或：ruff check src/  或：./gradlew ktlintCheck
EOF
chmod +x .git/hooks/pre-commit
```

**成功信号**：`git commit` 自动跑 linter，有问题的代码提交不进去。

### 阶段 2 —— GitHub Issue 作为工作单元（第 2 周）
*给 Claude Code 每次会话一个明确的目标。*

不要写：*"加用户资料编辑功能"*

要写一个带 checklist 的 Issue：
```markdown
## 目标
用户能在个人资料设置页修改显示名称和头像。

## Checklist
- [ ] `PATCH /api/users/:id` 接受 `{ displayName?, avatarUrl? }`
- [ ] 校验 displayName 长度（3–50 字符）
- [ ] 写入 `users` 表，更新 `updated_at`
- [ ] 返回更新后的用户对象
- [ ] 前端表单不刷页面反映保存结果
- [ ] 校验失败时展示错误提示
```

然后告诉 Claude Code：*"实现 issue #47，遵循 TDD，先写失败的测试。"*

Checklist 条目直接映射为测试用例，Claude Code 逐一处理。

**成功信号**：Issue 的 checklist 和测试文件讲的是同一个故事。

### 阶段 3 —— TDD（第 3–4 周，渐进式）
*最大的文化转变。不要一开始就强推到整个代码库。*

只从**下一个新功能**开始。不要先去给老代码补测试。

规则：任何新函数或 API 接口，在函数存在之前先写调用它的测试。

```
# 和 Claude Code 的会话：
"需要实现密码重置流程（issue #52）。
在写任何实现之前，先写失败的测试。
使用 tests/helpers/auth.ts 中的测试工具。"
```

在新代码上建立习惯，坚持 2–3 周。之后修老代码的 bug 时，把回归测试作为修复的一部分一起加进去。覆盖率会逐渐上升。

**永远不要设定理想化的覆盖率目标。** 先测量当前覆盖率，把门槛设在 `当前值 - 2%`，在 CI 中强制执行。每季度提高 5%。

**成功信号**：没有测试就写代码，你会感到不安。

### 阶段 4 —— CI 门禁（第 2 个月）
*把 hook 在本地执行的检查自动化，覆盖所有贡献者。*

添加 CI 流程（GitHub Actions、GitLab CI 等），至少包含：
- Lint job
- 带覆盖率下限的 Test job（`--coverage-threshold` 或等效参数）

具体的 CI 结构参考 `team-workflow-guide.md §6`，用下方工具对照表换成你的语言。

---

## 第四部分：各语言工具对照表

工作流相同，工具不同。

| 用途 | Python | JavaScript/TypeScript | Java/Kotlin | PHP | Go |
|------|--------|----------------------|-------------|-----|-----|
| **测试框架** | `pytest` | `jest` / `vitest` | JUnit 5 | PHPUnit | `go test` |
| **覆盖率** | `pytest-cov` | `jest --coverage` | JaCoCo | `phpunit --coverage` | `go test -cover` |
| **Linter** | `ruff` | `eslint` | ktlint / Checkstyle | PHP-CS-Fixer | `golangci-lint` |
| **类型检查** | `mypy` | `tsc --noEmit` | 内置 | `phpstan` | 内置 |
| **格式化** | `ruff format` | `prettier` | ktlint | PHP-CS-Fixer | `gofmt` |
| **Pre-commit** | `pre-commit` | `husky` + `lint-staged` | pre-commit / Maven | pre-commit | pre-commit |
| **构建** | `python -m build` | `npm run build` | `./gradlew build` | `composer install` | `go build` |
| **包管理** | `pip` / `poetry` | `npm` / `pnpm` | Maven / Gradle | Composer | Go modules |

把你的语言对应命令写进 `CLAUDE.md` 的 `## 命令` 下。Claude Code 用你指定的命令，不会自己假设。

---

## 第五部分：有效的 Claude Code 对话模式

### 每次会话先给方位

不要直接提问，先让 Claude Code 定位：

```
# 差 —— Claude Code 每次会话从零开始
"怎么加限流？"

# 好 —— Claude Code 知道自己在哪里
"我们在处理 API 网关（src/gateway/）。需要对所有认证路由加每用户限流。
限流配置在 src/config/limits.ts。
Redis 用于共享状态（见 src/cache/redis.ts）。
先读相关文件，再写失败的测试。"
```

### 明确引用 Issue 号和文件路径

```
"实现 issue #31。涉及的 service 是 src/notifications/email.service.ts。
测试放在 tests/unit/notifications/。用 tests/mocks/email.ts 里现有的 email mock。"
```

### 委托完整任务，不是单步操作

```
# 差 —— 你变成了循环控制器
"写测试。"
[Claude 写测试]
"现在跑一下。"
[Claude 跑测试]
"现在实现。"

# 好 —— Claude Code 处理整个循环
"用 TDD 实现结账折扣校验（issue #44）。
写测试，跑测试（应该失败），实现直到通过，然后提交。"
```

### 复杂改动先要方案

```
"在写任何代码之前：给 auth 系统加多租户需要改哪些文件？
列出来并说明每个文件为什么需要改。"
```

这能在深入 200 行代码之前暴露预期之外的依赖。

### 长任务中间设检查点

跨多个模块的任务，主动要求中间状态汇报：

```
"停下来告诉我：你到目前为止改了什么，还剩什么，
有没有需要我做决定的地方才能继续？"
```

---

## 第六部分：Claude Code 能替代什么，不能替代什么

### 它能加速的事

- 写样板代码（CRUD 接口、测试桩、迁移文件）
- 导航不熟悉的代码区域
- 把 Issue checklist 转化为测试用例
- PR 前的 QA 检查清单
- 解释一段代码在做什么

### 它不能替代的事

| 职责 | 仍然由你负责 |
|------|------------|
| 架构决策 | Claude Code 可以给选项，你来决定 |
| "这个功能对不对？" | 产品判断是你的 |
| PR 审批 | 合并前需要人工 review |
| 事故响应 | Claude Code 可以协助排查，不能主导 |
| 安全审查 | Claude Code 辅助，你来核实 |

### 浪费时间的反模式

| 你的操作 | 结果 | 更好的做法 |
|----------|------|-----------|
| 给模糊的需求 | Claude Code 自己发明需求 | 先写 Issue checklist |
| "帮我修 CI"但不给上下文 | 它猜测根因 | 粘贴完整 CI 错误日志 |
| 不读 diff 直接接受方案 | 细微 bug 混入 main | 每次改动都要读 diff |
| 用它生成文档 | 文档和代码越走越远 | 从代码生成文档（docstring、JSDoc） |
| 跳过 CLAUDE.md 建立 | 套用通用模式，和你的代码库冲突 | 阶段 0 花 2 小时，节省几天 |

---

## 快速自测：你的项目 Claude Code 就绪了吗？

逐项检查，每个"否"就是阶段 0–2 里的一个缺口。

**上下文**
- [ ] `CLAUDE.md` 存在，包含命令、约定、禁止事项
- [ ] Claude Code 能正确回答"[核心功能] 在哪里实现的？"

**Git 纪律**
- [ ] 所有工作在 feature 分支上（没有直接向 main 提交）
- [ ] 提交信息遵循统一格式
- [ ] pre-commit hook 会跑 lint

**测试**
- [ ] 你知道当前覆盖率是多少
- [ ] CI 在测试失败时会报红
- [ ] 新代码有配套测试

**可追踪性**
- [ ] 每个 PR 都关联了 GitHub Issue
- [ ] Issue 有验收 checklist

全部勾上，Claude Code 在你们团队的表现就会像一个已经上手的工程师。
有几项缺失，就从阶段 0 开始，按顺序推进，不要跳步骤。
