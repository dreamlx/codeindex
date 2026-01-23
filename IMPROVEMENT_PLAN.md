# codeindex 改进计划

## 版本目标：v0.3.0 - 智能层级索引

---

## P0: 修复层级判断逻辑 [紧急]

### 问题描述
当前所有目录都使用 `detailed` 级别，导致大型目录被截断到 50KB。

### 根因
1. `scan-all` 非 hierarchical 模式写死了 `level="detailed"`
2. `child_dirs=[]` 没有传递子目录信息
3. 层级判断需要知道完整的目录树结构

### 修复方案

#### 方案 A：强制使用 hierarchical 模式
```python
# cli.py - scan-all 命令默认使用 hierarchical
@click.option('--flat', is_flag=True, help='Disable hierarchical processing')
```

#### 方案 B：两遍扫描
```
第一遍：扫描目录结构，标记哪些目录有子目录
第二遍：根据结构决定每个目录的 level
```

#### 推荐：方案 B（更通用）

### 实现任务
- [x] 1.1 添加 `DirectoryTree` 类，预先构建目录结构 ✅
- [x] 1.2 修改 `scan-all` 命令使用目录树 ✅
- [x] 1.3 修改 `determine_level` 接收目录树而非单个 `has_children` ✅
- [x] 1.4 测试：验证根目录用 overview，中间层用 navigation ✅

---

## P1: 添加 namespace/use 解析 [重要]

### 问题描述
PHP 文件缺少 namespace 和 use 语句解析，无法准确描述模块依赖。

### 当前输出
```markdown
## Dependencies
- ./Service/UserService.php  # 基于 include/require
```

### 目标输出
```markdown
## Namespace
App\Controller

## Dependencies
- App\Service\UserService (use)
- App\Model\User (use)
- Illuminate\Http\Request (use)
```

### 实现任务
- [x] 2.1 解析 `namespace` 声明 ✅
- [x] 2.2 解析 `use` 语句（含 alias 和 group import）✅
- [ ] 2.3 解析 `use trait` 语句
- [x] 2.4 更新 `Import` 数据结构支持 PHP use ✅
- [x] 2.5 在 README 中展示 namespace 信息 ✅

### tree-sitter AST 结构
```
namespace_definition
├── namespace
├── namespace_name
│   └── name: "App\\Controller"
└── compound_statement

namespace_use_declaration
├── use
├── namespace_use_clause
│   ├── qualified_name
│   │   └── name: "App\\Service\\UserService"
│   └── namespace_aliasing_clause (optional)
│       └── name: "Service"
```

---

## P1: 生成全局符号索引 [重要]

### 问题描述
当前每个目录独立索引，无法快速搜索"哪个类实现了支付功能"。

### 目标
生成 `PROJECT_SYMBOLS.md`：
```markdown
# Project Symbols Index

## Classes by Function

### 用户管理
- `App\Controller\UserController` - src/Controller/UserController.php
- `App\Service\UserService` - src/Service/UserService.php
- `App\Model\User` - src/Model/User.php

### 订单处理
- `App\Controller\OrderController` - src/Controller/OrderController.php
...

## All Classes (alphabetical)
| Class | File | Description |
|-------|------|-------------|
| OrderController | src/Controller/OrderController.php | 订单管理 |
| OrderService | src/Service/OrderService.php | 订单业务逻辑 |
...

## Entry Points
- `public/index.php` - Web 入口
- `artisan` - CLI 入口
```

### 实现任务
- [x] 3.1 收集所有目录的解析结果 ✅
- [x] 3.2 按功能/类型对符号分类 ✅
- [x] 3.3 生成全局索引文件 ✅
- [x] 3.4 添加 `codeindex symbols` 命令生成全局索引 ✅

---

## P2: ThinkPHP 模式识别 [增强]

### 问题描述
ThinkPHP 有特定的目录约定，当前没有识别。

### ThinkPHP 目录约定
```
application/
├── controller/  → 自动路由 /module/controller/action
├── model/       → 数据表映射 (表名 = 类名小写)
├── validate/    → 请求验证规则
├── service/     → 业务逻辑
├── middleware/  → 中间件
├── event/       → 事件订阅
├── command/     → 命令行
├── config/      → 配置文件
└── route/       → 路由定义
```

### 目标输出
```markdown
## Module: Admin (ThinkPHP)

### Routes
| URL | Controller | Action |
|-----|------------|--------|
| /admin/user/index | UserController | index |
| /admin/user/create | UserController | create |

### Models
| Model | Table | Primary Key |
|-------|-------|-------------|
| User | tp_user | id |
| Order | tp_order | id |

### Middleware
- AuthMiddleware → 验证登录状态
- LogMiddleware → 记录请求日志
```

### 实现任务
- [x] 4.1 检测 ThinkPHP 项目（composer.json 或目录结构）✅
- [x] 4.2 解析 controller 生成路由表 ✅
- [x] 4.3 解析 model 提取表名映射 ✅
- [ ] 4.4 添加框架特定分组模式

---

## P3: scan-all AI 增强 [当前]

### 问题描述
当前 `scan-all` 只使用 SmartWriter 生成机械化 README，没有利用 `ai_command` 配置。

### 目标
- `scan-all` 默认对关键目录调用 AI 增强
- `scan-all --no-ai` 使用纯 SmartWriter（当前行为）
- 智能选择哪些目录需要 AI 增强

### 设计原则
```
overview (根目录)     → AI 调用 - 生成项目概述和架构说明
navigation (中间层)   → SmartWriter - 符号列表够用
detailed (叶子目录)   → 可选 AI - 按配置或大小触发
```

---

### Phase 1: 基础 AI 调用 [已完成 ✅]

**目标**：`scan-all` 对 overview 级别调用 AI

**任务清单**：
- [x] P3.1.1 修改 `scan-all` 命令参数 ✅
  - 添加 `--no-ai` 参数（不调用 AI，等同于当前 --fallback）
  - 保留 `--fallback` 作为 `--no-ai` 的别名（兼容性）
  - 默认行为：对 overview 级别调用 AI

- [x] P3.1.2 修改 `process_single_directory` 函数 ✅
  - 判断 level == "overview" 时调用 AI
  - 复用现有 `format_prompt` 和 `invoke_ai_cli`
  - overview 级别使用非递归扫描（避免 prompt 过大）
  - 其他级别继续使用 SmartWriter

- [x] P3.1.3 添加 AI 调用的错误处理 ✅
  - AI 调用失败时 fallback 到 SmartWriter
  - 输出中显示 (AI) 或 (fallback) 标记

- [x] P3.1.4 测试验证 ✅
  - codeindex 项目：1 次 AI 调用，生成架构概述
  - PHP 项目（251 目录）：1 次 AI 调用，生成架构图
  - --no-ai 参数正常工作

**结果**：
```bash
codeindex scan-all           # overview 用 AI (1次调用)，其他用 SmartWriter
codeindex scan-all --no-ai   # 全部用 SmartWriter
```

---

### Phase 2: 智能触发 AI [已完成 ✅]

**目标**：根据配置和文件大小智能决定是否调用 AI

**任务清单**：
- [x] P3.2.1 添加 `ai_enhancement` 配置项 ✅
  ```yaml
  ai_enhancement:
    enabled: true
    size_threshold: 40960 # >40KB 触发 AI 增强
    max_concurrent: 2     # 最大并发 AI 调用
    rate_limit_delay: 1.0 # 调用间隔（秒）
  ```

- [x] P3.2.2 实现两阶段处理 ✅
  - Phase 1: SmartWriter 并行生成所有 README
  - 收集 Oversize Checklist (overview + >threshold)
  - Phase 2: AI 并行增强 checklist 中的目录

- [x] P3.2.3 实现并发控制 ✅
  - 使用 Semaphore 限制并发 AI 调用数
  - 添加调用间隔延迟（rate limiting）
  - ThreadPoolExecutor + Semaphore 实现

- [x] P3.2.4 测试验证 ✅
  - codeindex 项目：1 AI 调用（overview）
  - PHP 项目（251 目录）：5 AI 调用（1 overview + 4 oversize）
  - AI 成功压缩：50KB → 7KB
  - 并发控制正常工作

**实现结果**：
```bash
codeindex scan-all           # 两阶段处理（SmartWriter + AI 增强）
codeindex scan-all --no-ai   # 强制全部用 SmartWriter

# PHP 项目测试结果：
# Phase 1: 251/251 directories (SmartWriter)
# Phase 2: 5 directories (1 overview, 4 oversize >40KB)
#   - Model: 50KB → 7KB ✓
#   - Controller: 50KB → 6KB ✓
#   - Business: 47KB → 6KB ✓
```

---

### Phase 3: 增量更新 [未来]

- [ ] P3.3.1 检测已有 README 的修改时间
- [ ] P3.3.2 比较源文件修改时间
- [ ] P3.3.3 只对有变化的目录重新生成
- [ ] P3.3.4 添加 `--force` 参数强制全部重新生成

---

## P4: AI 智能总结大文件 [路线图]

### 问题描述
当 PROJECT_SYMBOLS.md 超过 100KB 时，机械列表信息密度低，无人阅读。

### 解决方案
二次处理：检测文件大小 > 阈值时，触发 AI 总结。

### 实现任务
- [ ] 4.1 添加配置项 `ai_summary_threshold: 102400`
- [ ] 4.2 检测生成文件大小，超阈值触发 AI
- [ ] 4.3 设计 AI prompt（分组、核心类、架构概述）
- [ ] 4.4 生成 PROJECT_OVERVIEW.md（AI 版）
- [ ] 4.5 添加 `codeindex symbols --ai` 强制使用 AI

---

## P5: 从 PHPDoc 提取描述 [可选增强]

### 问题描述
当前只提取了符号签名，没有提取 PHPDoc 中的描述。

### 收益分析
- 如果 PHPDoc 质量好 → 对 AI 理解帮助大
- 如果 PHPDoc 缺失/质量差 → 收益有限
- 建议作为可选功能

### 实现任务
- [ ] 5.1 解析 PHPDoc 注释块
- [ ] 5.2 提取 @param、@return、@throws 标签
- [ ] 5.3 提取描述文本（第一行）
- [ ] 5.4 更新 Symbol 数据结构支持 tags

---

## 实现优先级

```
Week 1: P0 (层级判断修复)
├── Day 1-2: DirectoryTree 类 + 两遍扫描
├── Day 3: 修改 scan-all 命令
└── Day 4-5: 测试 + 修复

Week 2: P1 (namespace + 全局索引)
├── Day 1-2: namespace/use 解析
├── Day 3-4: 全局符号索引生成
└── Day 5: 测试 + 文档

Week 3: P2 (ThinkPHP + PHPDoc)
├── Day 1-2: ThinkPHP 模式识别
├── Day 3-4: PHPDoc 解析
└── Day 5: 测试 + 发布 v0.3.0
```

---

## 验收标准

### P0 验收
- [ ] Application/README_AI.md 使用 `overview` 级别，大小 < 15KB
- [ ] Application/Admin/README_AI.md 使用 `navigation` 级别
- [ ] Application/Admin/Controller/README_AI.md 使用 `detailed` 级别

### P1 验收
- [ ] PHP 文件的 namespace 正确显示
- [ ] use 语句作为依赖项列出
- [ ] PROJECT_SYMBOLS.md 包含所有类的索引

### P2 验收
- [ ] ThinkPHP 项目显示路由表
- [ ] PHPDoc 描述显示在符号旁边
