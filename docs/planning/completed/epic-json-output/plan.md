# Epic: JSON 输出支持（LoomGraph 集成）

**版本**: v0.7.0
**状态**: 📋 Active
**优先级**: P0
**创建日期**: 2026-02-04
**预计完成**: 2026-02-05

---

## 📖 Epic 概述

### 背景

LoomGraph 是一个代码知识图谱系统，采用 AI-Agent-Friendly 设计理念：
- **用户定位**：AI Agent (Claude Code)，而非人类
- **Pipeline 编排**：在 AI 推理中，而非代码中
- **命令风格**：原子命令可组合，JSON 输出

为了支持 LoomGraph 的索引流程，codeindex 需要提供机器可读的 JSON 输出：

```bash
# LoomGraph Pipeline
codeindex scan <repo> --output json > parse_results.json  # ← codeindex 提供
loomgraph embed parse_results.json --output embeddings.json
loomgraph inject parse_results.json embeddings.json
loomgraph search "用户认证逻辑"
```

### 目标

1. ✅ 添加 `--output json` 选项到 `scan` 和 `scan-all` 命令
2. ✅ 输出格式符合 LoomGraph 的 CLI_DESIGN.md 规范
3. ✅ 保持向后兼容（默认行为不变）
4. ✅ 提供最终用户集成指南

### 影响范围

- **codeindex 开发者**：添加新功能
- **LoomGraph 开发者**：使用 codeindex JSON 输出
- **最终用户**：在自己项目中集成 codeindex + LoomGraph

---

## 🎯 Stories

### Story 1: 实现 ParseResult 序列化

**优先级**: P0（其他 Story 的依赖）

**User Story**:
```
作为 LoomGraph 开发者
我希望 ParseResult 可以序列化为 JSON
以便在 Pipeline 中传递数据
```

**Acceptance Criteria**:
1. ✅ `Symbol` 类有 `to_dict()` 方法
2. ✅ `Call` 类有 `to_dict()` 方法
3. ✅ `Inheritance` 类有 `to_dict()` 方法
4. ✅ `Import` 类有 `to_dict()` 方法
5. ✅ `ParseResult` 类有 `to_dict()` 方法
6. ✅ 所有字段都可序列化（无 Path 对象，转为 str）
7. ✅ 测试用例覆盖所有序列化方法

**实现文件**:
- `src/codeindex/parser.py` - 添加 `to_dict()` 方法
- `tests/test_json_output.py` - 测试序列化

**输出示例**:
```json
{
  "path": "src/user.py",
  "symbols": [
    {
      "name": "UserService",
      "kind": "class",
      "signature": "class UserService:",
      "docstring": "User management service",
      "line_start": 10,
      "line_end": 50
    }
  ],
  "calls": [
    {"caller": "UserService.login", "callee": "db.find", "line": 15}
  ],
  "inheritances": [
    {"child": "UserService", "parent": "BaseService"}
  ],
  "imports": [
    {"module": "typing", "names": ["Optional"], "is_from": true}
  ],
  "module_docstring": "User authentication module",
  "file_lines": 100,
  "error": null
}
```

---

### Story 2: `scan` 命令支持 `--output json`

**优先级**: P0

**User Story**:
```
作为 LoomGraph 开发者
我希望 codeindex scan 可以输出 JSON
以便在 Pipeline 中处理解析结果
```

**Acceptance Criteria**:
1. ✅ `codeindex scan <dir>` 默认行为不变（生成 README_AI.md）
2. ✅ `codeindex scan <dir> --output markdown` 显式指定 markdown 输出
3. ✅ `codeindex scan <dir> --output json` 输出 JSON 到 stdout
4. ✅ JSON 格式包含 `success`, `results`, `summary` 字段
5. ✅ JSON 输出不写文件
6. ✅ 支持中文（`ensure_ascii=False`）
7. ✅ 测试用例覆盖两种输出模式

**实现文件**:
- `src/codeindex/cli.py` - 修改 `scan` 命令
- `tests/test_cli_json.py` - 测试 CLI JSON 输出

**CLI 变更**:
```python
@click.option(
    "--output",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format (markdown writes README_AI.md, json prints to stdout)"
)
def scan(directory: str, output: str, ...):
    # ... existing logic ...

    if output == "json":
        json_output = {
            "success": True,
            "results": [result.to_dict() for result in results],
            "summary": {
                "total_files": len(results),
                "total_symbols": sum(len(r.symbols) for r in results),
                "total_calls": sum(len(r.calls) for r in results),
                "errors": sum(1 for r in results if r.error)
            }
        }
        click.echo(json.dumps(json_output, indent=2, ensure_ascii=False))
    else:
        # 现有的 markdown 输出逻辑
        ...
```

---

### Story 3: `scan-all` 命令支持 `--output json`

**优先级**: P0

**User Story**:
```
作为 LoomGraph 开发者
我希望 codeindex scan-all 可以输出整个仓库的 JSON
以便一次性获取所有解析结果
```

**Acceptance Criteria**:
1. ✅ `codeindex scan-all` 默认行为不变（生成多个 README_AI.md）
2. ✅ `codeindex scan-all --output json` 输出聚合的 JSON
3. ✅ JSON 包含所有目录的 ParseResult
4. ✅ summary 统计全局信息
5. ✅ 测试用例覆盖聚合逻辑

**实现文件**:
- `src/codeindex/cli.py` - 修改 `scan_all` 命令
- `tests/test_cli_json.py` - 测试聚合输出

**输出示例**:
```json
{
  "success": true,
  "results": [
    {"path": "src/auth/user.py", "symbols": [...], ...},
    {"path": "src/auth/service.py", "symbols": [...], ...},
    {"path": "src/api/routes.py", "symbols": [...], ...}
  ],
  "summary": {
    "total_files": 25,
    "total_symbols": 350,
    "total_calls": 890,
    "total_inheritances": 45,
    "total_imports": 120,
    "errors": 0
  }
}
```

---

### Story 4: 错误处理和结构化输出

**优先级**: P0

**User Story**:
```
作为 AI Agent
我希望错误信息也以 JSON 格式返回
以便自动化处理错误
```

**Acceptance Criteria**:
1. ✅ 命令执行失败时，返回结构化错误 JSON
2. ✅ 文件级错误记录在 `result.error` 字段
3. ✅ `success: false` 时包含 `error` 对象
4. ✅ 错误对象包含 `code`, `message`, `detail` 字段
5. ✅ 测试用例覆盖错误场景

**错误输出格式**:

**命令级错误** (exit code: 1):
```json
{
  "success": false,
  "error": {
    "code": "DIRECTORY_NOT_FOUND",
    "message": "Directory does not exist: /path/to/nonexistent",
    "detail": null
  },
  "results": [],
  "summary": {"total_files": 0, "total_symbols": 0, "errors": 1}
}
```

**文件级错误** (exit code: 0, 部分成功):
```json
{
  "success": true,
  "results": [
    {
      "path": "src/broken.py",
      "symbols": [],
      "calls": [],
      "inheritances": [],
      "imports": [],
      "module_docstring": "",
      "file_lines": 0,
      "error": "SyntaxError at line 42: unexpected EOF"
    },
    {
      "path": "src/good.py",
      "symbols": [...],
      "error": null
    }
  ],
  "summary": {
    "total_files": 2,
    "total_symbols": 15,
    "errors": 1
  }
}
```

**错误码定义**:
| 错误码 | 说明 | 场景 |
|--------|------|------|
| `DIRECTORY_NOT_FOUND` | 目录不存在 | 扫描不存在的路径 |
| `NO_CONFIG_FOUND` | 配置文件不存在 | scan-all 但没有 .codeindex.yaml |
| `PARSE_ERROR` | 解析失败 | 文件级解析错误 |

---

### Story 5: 文档更新和用户集成指南

**优先级**: P1

**User Story**:
```
作为 codeindex 用户
我希望有清晰的文档说明如何使用 JSON 输出
以便集成到我的工作流中
```

**Acceptance Criteria**:
1. ✅ 更新 `CLAUDE.md` - codeindex 项目自身
2. ✅ 创建 `docs/guides/json-output-integration.md` - 集成指南
3. ✅ 更新 `README.md` - 添加 JSON 输出示例
4. ✅ 创建最终用户模板 `examples/CLAUDE.md.template` - 供其他项目使用

**文档结构**:

#### 1. `CLAUDE.md` 更新（codeindex 项目）

添加 JSON 输出命令示例：
```markdown
## Quick Start (常用命令)

```bash
# 🚀 生成所有目录的索引 (Markdown, 最常用)
codeindex scan-all --fallback

# 🔧 生成 JSON 输出 (供工具集成使用，如 LoomGraph)
codeindex scan-all --output json > parse_results.json

# 单个目录的 JSON 输出
codeindex scan ./src --output json

# 查看 JSON 格式
codeindex scan ./src --output json | jq .
```

#### 2. `docs/guides/json-output-integration.md`（新建）

完整的集成指南，包含：
- JSON 输出格式说明
- 与 LoomGraph 的集成示例
- 错误处理最佳实践
- 性能优化建议

#### 3. `examples/CLAUDE.md.template`（新建）

**供最终用户使用的模板**，用户复制到自己项目的 `.claude/CLAUDE.md` 或 `AGENTS.md`：

```markdown
# Project: {YOUR_PROJECT_NAME}

## 📚 Code Intelligence Tools

本项目集成了代码分析工具链：

### codeindex - AST 代码解析

**安装**:
```bash
pip install matrix-codeindex
```

**使用**:
```bash
# 生成代码索引（供人类阅读）
codeindex scan-all

# 生成 JSON 输出（供工具链使用）
codeindex scan-all --output json > parse_results.json
```

**输出说明**:
- Markdown 模式：生成 `README_AI.md` 文件，帮助理解代码结构
- JSON 模式：输出到 stdout，供下游工具使用（如 LoomGraph）

**配置文件**: `.codeindex.yaml`
```yaml
include:
  - src
  - lib
exclude:
  - tests
  - node_modules
```

### LoomGraph - 代码知识图谱（可选）

如果项目使用 LoomGraph 进行代码搜索和分析：

```bash
# 索引代码库
codeindex scan-all --output json > parse_results.json
loomgraph embed parse_results.json --output embeddings.json
loomgraph inject parse_results.json embeddings.json

# 搜索代码
loomgraph search "用户认证逻辑"

# 查看调用关系
loomgraph graph "UserService.login" --direction callers
```

## 🔍 AI Agent 使用指南

作为 AI Agent，你可以：

1. **理解项目结构**：阅读各目录的 `README_AI.md`
2. **查找符号**：使用 `PROJECT_SYMBOLS.md` 快速定位
3. **分析代码**：使用 `codeindex scan --output json` 获取结构化数据
4. **语义搜索**：使用 `loomgraph search` 查找相关代码
```

#### 4. `README.md` 更新

添加 JSON 输出示例到 Usage 部分：

```markdown
## Usage

### Generate Documentation (Markdown)

```bash
# Scan a single directory
codeindex scan ./src

# Scan entire project
codeindex scan-all
```

### Generate Structured Data (JSON)

For tool integration (e.g., LoomGraph, custom scripts):

```bash
# Single directory
codeindex scan ./src --output json

# Entire project
codeindex scan-all --output json > parse_results.json

# View with jq
codeindex scan ./src --output json | jq '.summary'
```

**JSON Output Format**:
```json
{
  "success": true,
  "results": [
    {
      "path": "src/user.py",
      "symbols": [...],
      "calls": [...],
      "inheritances": [...],
      "imports": [...]
    }
  ],
  "summary": {
    "total_files": 25,
    "total_symbols": 350,
    "errors": 0
  }
}
```
```

---

### Story 6: Git Hooks 性能优化

**优先级**: P2（用户体验改进）

**User Story**:
```
作为 codeindex 用户
我希望 post-commit hook 不阻塞我的工作
以便提交代码后可以立即继续开发
```

**背景**:

当前 post-commit hook 的性能问题：
- **同步执行**：每次提交都会阻塞用户，等待 AI 更新完成
- **长时间等待**：3 个目录 × 30 秒/目录 = 90 秒阻塞
- **用户体验差**：无法立即 push 或继续工作

**Acceptance Criteria**:
1. ⏳ 添加 `hooks.post_commit.mode` 配置选项
2. ⏳ 实现 `async` 模式（后台异步执行，不阻塞）
3. ⏳ 实现 `sync` 模式（同步执行，保持现有行为）
4. ⏳ 实现 `prompt` 模式（只提醒，不自动执行）
5. ⏳ 实现 `disabled` 模式（完全禁用）
6. ⏳ 智能检测：≤2 个目录用 sync，>2 个目录用 async
7. ⏳ 提供进度提示和日志文件路径
8. ⏳ 更新文档说明各模式的使用场景

**配置示例**:

`.codeindex.yaml`:
```yaml
hooks:
  post_commit:
    mode: async  # disabled | async | sync | prompt
    max_dirs_sync: 2  # 超过此数量自动切换到 async
    log_file: ~/.codeindex/hooks/post-commit.log
```

**实现方案**:

#### 1. Async 模式实现

使用 `nohup` 后台执行：
```bash
# Hook 检测到需要更新
if [ "$MODE" = "async" ] || [ "$DIR_COUNT" -gt "$MAX_DIRS_SYNC" ]; then
    echo "⚠️  README_AI.md updates running in background"
    echo "   Log: $LOG_FILE"
    echo "   PID: $(cat $PID_FILE)"

    # 后台执行
    nohup bash -c "
        # ... AI 更新逻辑 ...
        git commit --no-verify -m 'docs: auto-update README_AI.md'
    " > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    exit 0  # 立即返回，不阻塞用户
fi
```

#### 2. Prompt 模式实现

只输出提示，不执行：
```bash
if [ "$MODE" = "prompt" ]; then
    echo "⚠️  ${DIR_COUNT} directories need README_AI.md updates"
    echo "   Run: codeindex affected --update"
    exit 0
fi
```

#### 3. 智能检测

```bash
# 默认行为：小项目同步，大项目异步
if [ -z "$MODE" ]; then
    if [ "$DIR_COUNT" -le 2 ]; then
        MODE="sync"
    else
        MODE="async"
    fi
fi
```

**Hook 输出示例（async 模式）**:

```bash
📝 Post-commit: Analyzing changes...
   Update level: full
   Found 3 directory(ies) to check

⚠️  README_AI.md updates running in background (async mode)
   Log: ~/.codeindex/hooks/post-commit.log
   PID: 12345

   To check progress: tail -f ~/.codeindex/hooks/post-commit.log
   To wait: wait 12345

✓ Commit completed! You can continue working.
```

**技术细节**:

1. **PID 文件管理**：`~/.codeindex/hooks/post-commit.pid`
2. **日志文件**：`~/.codeindex/hooks/post-commit.log`（按日期滚动）
3. **锁文件**：防止多个后台进程同时运行
4. **错误处理**：后台进程失败时不影响用户

**测试场景**:

1. **小项目（≤2 目录）**：默认 sync，立即完成
2. **中项目（3-5 目录）**：默认 async，后台运行
3. **大项目（>5 目录）**：async + 进度提示
4. **手动配置**：`.codeindex.yaml` 覆盖默认行为
5. **并发提交**：锁文件防止冲突

**风险与缓解**:

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 后台进程失败 | README 未更新 | 记录详细日志，提供手动修复命令 |
| 多个后台进程 | 资源竞争 | 使用锁文件，只允许一个进程 |
| 用户切换分支 | 后台提交到错误分支 | 记录原始分支，检查后再提交 |

**预期收益**:

- **用户体验**：提交后立即返回（< 1 秒）
- **工作流畅度**：不影响 push、checkout 等操作
- **灵活性**：用户可根据项目规模选择模式

---

## 📋 实施计划

### Phase 1: 核心功能（4-6 小时）

#### Task 1.1: 实现序列化方法（2 小时）
- [ ] 添加 `Symbol.to_dict()`
- [ ] 添加 `Call.to_dict()`
- [ ] 添加 `Inheritance.to_dict()`
- [ ] 添加 `Import.to_dict()`
- [ ] 添加 `ParseResult.to_dict()`
- [ ] 编写测试 `tests/test_json_output.py`

#### Task 1.2: 修改 `scan` 命令（1 小时）
- [ ] 添加 `--output` 选项
- [ ] 实现 JSON 输出逻辑
- [ ] 实现 markdown 输出逻辑（现有代码重构）
- [ ] 编写测试 `tests/test_cli_json.py`

#### Task 1.3: 修改 `scan-all` 命令（1 小时）
- [ ] 添加 `--output` 选项
- [ ] 实现 JSON 聚合逻辑
- [ ] 编写测试

#### Task 1.4: 错误处理（1-2 小时）
- [ ] 实现命令级错误 JSON 输出
- [ ] 实现文件级错误处理
- [ ] 添加错误码定义
- [ ] 编写错误场景测试

### Phase 2: 文档更新（2 小时）

#### Task 2.1: 更新项目文档（1 小时）
- [ ] 更新 `CLAUDE.md`
- [ ] 更新 `README.md`
- [ ] 更新 `CHANGELOG.md`

#### Task 2.2: 创建集成指南（1 小时）
- [ ] 创建 `docs/guides/json-output-integration.md`
- [ ] 创建 `examples/CLAUDE.md.template`
- [ ] 添加 LoomGraph 集成示例

### Phase 3: 测试和验证（1 小时）

#### Task 3.1: 集成测试
- [ ] 端到端测试 `scan --output json`
- [ ] 端到端测试 `scan-all --output json`
- [ ] 验证 JSON 格式符合 LoomGraph 规范

#### Task 3.2: 文档验证
- [ ] 验证所有命令示例可执行
- [ ] 验证 JSON 输出格式正确

---

## 🎯 验收标准

### 功能验收

```bash
# ✅ 1. Markdown 输出（默认行为）
codeindex scan src/
# 预期：生成 src/README_AI.md

# ✅ 2. JSON 输出到 stdout
codeindex scan src/ --output json
# 预期：输出 JSON 到 stdout，无文件生成

# ✅ 3. JSON 输出重定向
codeindex scan src/ --output json > output.json
# 预期：生成 output.json 文件

# ✅ 4. 整个仓库的 JSON 输出
codeindex scan-all --output json
# 预期：输出所有目录的聚合 JSON

# ✅ 5. 错误处理
codeindex scan nonexistent/ --output json
# 预期：返回 success: false 的 JSON

# ✅ 6. 格式验证
codeindex scan src/ --output json | jq empty
# 预期：jq 成功解析，无错误

# ✅ 7. LoomGraph 集成
codeindex scan-all --output json > parse.json
loomgraph embed parse.json --output embeddings.json
# 预期：LoomGraph 可以正确解析
```

### 性能验收

| 项目规模 | 文件数 | 符号数 | JSON 输出时间 | 要求 |
|---------|-------|--------|--------------|------|
| 小型 | < 50 | < 500 | < 2s | 满足 |
| 中型 | 50-200 | 500-2000 | < 10s | 满足 |
| 大型 | 200-1000 | 2000-10000 | < 60s | 满足 |

### 文档验收

- [ ] CLAUDE.md 包含 JSON 输出示例
- [ ] README.md 更新 Usage 部分
- [ ] 集成指南文档完整
- [ ] 最终用户模板可用

---

## 🔗 相关文档

**LoomGraph 设计文档**:
- [CLI_DESIGN.md](https://github.com/dreamlx/LoomGraph/blob/main/docs/api/CLI_DESIGN.md) - LoomGraph CLI 规范
- [SYSTEM_DESIGN.md](https://github.com/dreamlx/LoomGraph/blob/main/docs/architecture/SYSTEM_DESIGN.md) - LoomGraph 系统架构

**codeindex 内部文档**:
- [parser.py](../../src/codeindex/parser.py) - ParseResult 数据结构
- [cli.py](../../src/codeindex/cli.py) - CLI 命令实现

---

## 📊 进度跟踪

| Story | 状态 | 进度 | 预计完成 |
|-------|------|------|----------|
| Story 1: 序列化 | ✅ DONE | 100% | 2026-02-04 |
| Story 2: scan 支持 | ✅ DONE | 100% | 2026-02-04 |
| Story 3: scan-all 支持 | ✅ DONE | 100% | 2026-02-04 |
| Story 4: 错误处理 | 📋 TODO | 0% | 2026-02-04 |
| Story 5: 文档更新 | 📋 TODO | 0% | 2026-02-05 |
| Story 6: Git Hooks 优化 | 📋 TODO | 0% | 2026-02-05 |

**总体进度**: 3/6 (50%)

---

## 📝 Notes

### 设计决策

1. **为什么用 `--output` 而不是 `--format`?**
   - `--output` 更直观，表示输出格式
   - 与 LoomGraph CLI 风格一致

2. **为什么 JSON 输出到 stdout 而不是文件?**
   - 符合 Unix 哲学（管道组合）
   - AI Agent 可以直接处理 stdout
   - 灵活：可重定向到文件或传给下一个命令

3. **为什么 scan 和 scan-all 都要支持?**
   - 不同使用场景：快速测试 vs 完整索引
   - 给 AI Agent 更多控制权

### 风险和缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| JSON 输出性能问题 | 高 | 低 | 实现增量序列化，避免全量加载 |
| 格式不兼容 | 高 | 低 | 严格遵循 LoomGraph 规范，添加集成测试 |
| 破坏现有行为 | 高 | 低 | 默认行为不变，添加回归测试 |

---

**状态**: 📋 待实施
**负责人**: @dreamlx
**审核人**: LoomGraph Team

