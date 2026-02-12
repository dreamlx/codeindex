# Claude Code 集成指南

本指南帮助你配置项目，让 Claude Code 更好地利用 codeindex 生成的 README_AI.md 文件。

## 📋 概述

codeindex 为你的项目生成了多层次的 README_AI.md 文件，这些文件是 AI 理解你项目架构的最佳入口。通过在项目根目录添加 `CLAUDE.md` 文件，你可以指导 Claude Code 优先使用这些索引文件，而不是盲目搜索源代码。

## 🚀 快速开始

### 1. 复制 CLAUDE.md 模板

在你的项目根目录创建 `CLAUDE.md` 文件（与 README_AI.md 同级），复制以下模板：

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working with this project.

## 📖 项目导航指南

### ⚠️ 重要：本项目使用 codeindex 生成了 README_AI.md 索引

本项目已使用 [codeindex](https://github.com/dreamlx/codeindex) 工具为所有目录生成了 `README_AI.md` 文件。这些文件是理解项目架构的最佳入口，包含了自动提取的符号信息、依赖关系和模块说明。

### 🧭 推荐工作流

#### 1️⃣ 理解项目架构（优先阅读 README_AI.md）

在开始任何代码分析前，请按以下顺序阅读：

```
1. /README_AI.md           # 项目整体概览和目录结构
2. /src/README_AI.md       # 核心源码目录架构
3. /tests/README_AI.md     # 测试结构（如果存在）
4. 相关子目录的 README_AI.md  # 具体模块详情
```

**示例场景：**
- 用户问："这个项目是做什么的？" → 先读 `/README_AI.md`
- 用户问："认证模块在哪里？" → 先读 `/src/README_AI.md`，找到 auth 相关目录，再读 `/src/auth/README_AI.md`
- 用户问："如何运行测试？" → 先读 `/tests/README_AI.md`，了解测试结构

#### 2️⃣ 定位具体代码（精确导航）

**优先使用 Serena MCP 工具（如果可用）：**

```python
# ✅ 推荐：查找符号定义
find_symbol(name_path_pattern="UserAuthenticator")

# ✅ 推荐：查找符号引用
find_referencing_symbols(
    name_path="authenticate",
    relative_path="src/auth/authenticator.py"
)

# ✅ 推荐：获取文件符号概览
get_symbols_overview(
    relative_path="src/auth/authenticator.py",
    depth=1
)
```

**备选方案：使用 Read 工具**

```python
# 当 Serena MCP 不可用时
Read(file_path="src/auth/README_AI.md")  # 先读目录索引
Read(file_path="src/auth/authenticator.py")  # 再读具体文件
```

**❌ 避免的做法：**
- 直接用 Glob/Grep 搜索源码（低效且无结构化信息）
- 不看 README_AI.md 就直接读源代码文件
- 忽略已有的符号索引信息

#### 3️⃣ 修改代码（保持索引同步）

修改代码后，请重新生成 README_AI.md：

```bash
# 重新扫描整个项目
codeindex scan-all

# 或只扫描修改的目录
codeindex scan src/auth
```

**注意：不要手动编辑 README_AI.md 文件，它们会被自动覆盖。**

### 📁 特殊文件说明

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| `README_AI.md` | AI生成的目录索引文件 | 理解任何目录的架构和组件 |
| `PROJECT_SYMBOLS.md` | 全局符号索引（如果存在） | 查找符号定义位置 |
| `.codeindex.yaml` | codeindex 配置文件 | 了解扫描规则和排除模式 |

### 🎯 典型场景示例

#### 场景1：用户问"用户认证是如何实现的？"

```
第1步：读取 /src/README_AI.md
      → 找到认证相关模块（比如 auth/ 目录）

第2步：读取 /src/auth/README_AI.md
      → 了解认证模块的组件、类和函数

第3步：使用 find_symbol(name_path_pattern="authenticate")
      → 精确定位认证函数实现

第4步：使用 find_referencing_symbols
      → 查看认证函数的调用关系
```

#### 场景2：用户问"添加一个新的 API 端点"

```
第1步：读取 /src/api/README_AI.md
      → 理解现有的 API 结构

第2步：查看现有端点的实现
      → 使用 find_symbol 找到类似端点

第3步：按照现有模式添加新端点

第4步：添加后重新生成索引
      → codeindex scan src/api
```

#### 场景3：用户问"这个函数在哪里被调用？"

```
第1步：使用 find_symbol 定位函数定义

第2步：使用 find_referencing_symbols 查找所有引用

第3步：分析调用关系和依赖
```

### 🔄 工作流总结

```
┌─────────────────────────────────────────────────┐
│  用户提问                                        │
└───────────────────┬─────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │ 读 README_AI.md     │  ← 第一步
         │ (理解架构)          │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │ find_symbol         │  ← 第二步
         │ (精确定位)          │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │ Read 源码文件       │  ← 第三步
         │ (查看实现)          │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │ find_referencing    │  ← 第四步
         │ (分析依赖)          │
         └─────────────────────┘
```

### 💡 最佳实践

1. **总是从 README_AI.md 开始**
   - 它提供了结构化的概览，比直接读代码效率高10倍

2. **利用符号索引**
   - find_symbol 比 Grep 更精确，能理解代码结构

3. **保持索引更新**
   - 修改代码后重新运行 codeindex scan

4. **信任索引信息**
   - README_AI.md 中的符号列表、依赖关系都是自动提取的，准确可靠

## 🛠️ 项目特定配置

<!-- 在下方添加你的项目特定说明 -->

### 项目结构

<!-- 示例：
- `src/api/` - REST API 端点
- `src/models/` - 数据模型
- `src/services/` - 业务逻辑
-->

### 关键组件

<!-- 示例：
- `UserService` - 用户管理服务
- `DatabaseConnection` - 数据库连接管理
-->

### 开发规范

<!-- 示例：
- 代码风格：遵循 PEP 8
- 测试：使用 pytest
- 提交规范：Conventional Commits
-->

---

*此文件由 [codeindex](https://github.com/dreamlx/codeindex) 生成。*
*如需更新索引，运行：`codeindex scan-all`*
```

### 2. 自定义项目特定信息

在模板的"项目特定配置"部分填写你的项目信息：

```markdown
### 项目结构

- `src/api/` - REST API 端点
- `src/models/` - 数据库模型
- `src/services/` - 业务逻辑层
- `src/utils/` - 工具函数

### 关键组件

- `UserService` - 用户管理服务（src/services/user_service.py）
- `AuthMiddleware` - 认证中间件（src/middleware/auth.py）
- `DatabaseConnection` - 数据库连接池（src/db/connection.py）

### 开发规范

- 代码风格：遵循 PEP 8，使用 black 格式化
- 测试：使用 pytest，覆盖率要求 ≥ 80%
- 提交规范：Conventional Commits (feat/fix/docs/test/refactor)
```

## 📊 效果对比

### ❌ 没有 CLAUDE.md 时

```
用户：这个项目的认证模块在哪里？

Claude：让我搜索一下... [使用 Glob 搜索 auth*]
      [盲目扫描整个代码库，低效且可能遗漏]
      找到 50 个相关文件，不确定哪个是主要的...
```

### ✅ 有 CLAUDE.md 时

```
用户：这个项目的认证模块在哪里？

Claude：让我先查看 README_AI.md... [读取 src/README_AI.md]
      根据索引，认证模块在 src/auth/ 目录
      [读取 src/auth/README_AI.md]
      核心类是 UserAuthenticator，位于 src/auth/authenticator.py:15
      [精确定位，高效准确]
```

## 🎯 用户收益

1. **提高效率**：Claude Code 能快速理解项目结构，减少无效搜索
2. **更准确**：基于结构化的符号信息，而非文本搜索
3. **更智能**：能理解模块依赖关系和调用图
4. **更省资源**：减少不必要的文件读取和搜索操作

## 🔄 维护说明

### 何时更新 README_AI.md

- ✅ 添加新的模块或组件
- ✅ 重构代码结构
- ✅ 修改公共 API
- ✅ 添加重要的类或函数
- ❌ 修改函数内部实现（无需更新）
- ❌ 添加注释或文档（无需更新）

### 自动化建议

在 pre-commit hook 中添加：

```bash
# .git/hooks/pre-commit
#!/bin/bash

# 检查是否有 Python 文件修改
if git diff --cached --name-only | grep -q '\.py$'; then
    echo "检测到 Python 文件修改，建议运行："
    echo "  codeindex scan-all"
    echo ""
    echo "跳过索引更新？(y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        codeindex scan-all
        git add README_AI.md **/README_AI.md
    fi
fi
```

## 📚 相关资源

- [codeindex GitHub](https://github.com/dreamlx/codeindex)
- [codeindex 文档](https://github.com/dreamlx/codeindex/blob/master/README.md)
- [Claude Code 文档](https://claude.com/claude-code)
- [Serena MCP 工具](https://github.com/serena-mcp)

## 💬 反馈和建议

如果你有任何问题或建议，欢迎：
- 提交 Issue：https://github.com/dreamlx/codeindex/issues
- 参与讨论：https://github.com/dreamlx/codeindex/discussions
