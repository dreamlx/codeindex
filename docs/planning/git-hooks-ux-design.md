# Git Hooks 用户体验设计

**Date**: 2026-02-02
**Epic**: 6 - Framework-Agnostic Route Extraction
**Story**: P3.1 - Git Hooks Auto-update
**Focus**: Claude Code 友好的零配置体验

---

## 🎯 设计目标

### 用户场景

```
用户：我刚 git clone 了一个 PHP 项目，想用 codeindex 索引
Claude Code：我帮你配置！
用户：读一下 codeindex 项目的 README
Claude Code：[读取 README] → 执行 `codeindex init --hooks` → 完成！
用户：太简单了！
```

**核心原则**:
1. ✅ **零手动配置** - 一条命令搞定
2. ✅ **Claude Code 可执行** - 所有步骤都是 bash 命令
3. ✅ **智能检测** - 自动识别项目类型
4. ✅ **安全第一** - 默认关闭，用户确认开启
5. ✅ **可撤销** - 随时禁用/卸载

---

## 🏗️ 方案设计

### 方案 1: 一键安装模式（推荐）

#### 命令接口

```bash
# 1. 基础安装（推荐，交互式）
codeindex init --hooks
# 提示：检测到 Git 仓库，是否启用自动索引更新？[y/N]
# 提示：选择触发时机：(1) pre-commit  (2) post-commit  (3) manual
# 生成：.git/hooks/pre-commit + .codeindex.yaml

# 2. 静默安装（Claude Code 友好）
codeindex init --hooks --trigger=pre-commit --yes
# 无提示，直接安装

# 3. 只生成配置不安装
codeindex init --hooks --config-only
# 只修改 .codeindex.yaml，不安装 hook

# 4. 卸载
codeindex hooks uninstall
# 删除 hook，但保留配置
```

#### 安装流程

```python
# src/codeindex/cli_hooks.py

@click.group()
def hooks():
    """Git hooks management commands"""
    pass

@hooks.command()
@click.option('--trigger', type=click.Choice(['pre-commit', 'post-commit', 'manual']),
              default='pre-commit', help='Hook trigger point')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.option('--config-only', is_flag=True, help='Only update config, do not install hook')
def install(trigger, yes, config_only):
    """Install Git hooks for auto-update"""

    # 1. 检查前置条件
    if not Path('.git').exists():
        console.print("[red]Error: Not a git repository[/red]")
        return 1

    if not Path('.codeindex.yaml').exists():
        console.print("[yellow]No .codeindex.yaml found. Run 'codeindex init' first.[/yellow]")
        if not yes:
            if not click.confirm("Create .codeindex.yaml now?"):
                return 1
        # 创建默认配置
        create_default_config()

    # 2. 用户确认（除非 --yes）
    if not yes and not config_only:
        console.print("\n[bold]Git Hook Auto-update Setup[/bold]")
        console.print(f"  Trigger: {trigger}")
        console.print(f"  Action: Update README_AI.md when code changes")
        console.print(f"  Hook location: .git/hooks/{trigger}")

        if not click.confirm("\nProceed?"):
            console.print("[yellow]Installation cancelled.[/yellow]")
            return 0

    # 3. 更新配置文件
    update_config_for_hooks(trigger, enabled=not config_only)
    console.print("[green]✓[/green] Updated .codeindex.yaml")

    # 4. 安装 hook 脚本（如果不是 config-only）
    if not config_only:
        install_hook_script(trigger)
        console.print(f"[green]✓[/green] Installed {trigger} hook")

    # 5. 显示下一步
    console.print("\n[bold green]Setup complete![/bold green]")
    if config_only:
        console.print("Run 'codeindex hooks install' to enable the hook.")
    else:
        console.print(f"Git {trigger} will now auto-update codeindex.")
        console.print("\nTo disable: codeindex hooks disable")
        console.print("To uninstall: codeindex hooks uninstall")

    return 0

@hooks.command()
def uninstall():
    """Uninstall Git hooks"""
    hook_file = Path('.git/hooks/pre-commit')
    if hook_file.exists():
        # 检查是否是我们的 hook
        content = hook_file.read_text()
        if 'codeindex-auto-update' in content:
            hook_file.unlink()
            console.print("[green]✓[/green] Uninstalled pre-commit hook")
        else:
            console.print("[yellow]Hook exists but not created by codeindex[/yellow]")
    else:
        console.print("[yellow]No hook found[/yellow]")

    # 禁用配置
    update_config_for_hooks(enabled=False)
    console.print("[green]✓[/green] Disabled auto-update in config")

@hooks.command()
def status():
    """Show Git hooks status"""
    # 检查配置
    config = load_config()
    enabled = config.get('indexing', {}).get('auto_update', {}).get('enabled', False)
    trigger = config.get('indexing', {}).get('auto_update', {}).get('trigger', 'pre-commit')

    # 检查 hook 文件
    hook_file = Path(f'.git/hooks/{trigger}')
    hook_installed = hook_file.exists()

    # 显示状态
    console.print("\n[bold]Git Hooks Status[/bold]")
    console.print(f"  Config enabled: {'[green]Yes[/green]' if enabled else '[red]No[/red]'}")
    console.print(f"  Hook installed: {'[green]Yes[/green]' if hook_installed else '[red]No[/red]'}")
    console.print(f"  Trigger: {trigger}")

    if enabled and hook_installed:
        console.print("\n[green]✓ Auto-update is active[/green]")
    elif enabled and not hook_installed:
        console.print("\n[yellow]⚠ Config enabled but hook not installed[/yellow]")
        console.print("  Run: codeindex hooks install")
    elif not enabled and hook_installed:
        console.print("\n[yellow]⚠ Hook installed but config disabled[/yellow]")
        console.print("  Run: codeindex hooks enable")
    else:
        console.print("\n[red]✗ Auto-update is not configured[/red]")
        console.print("  Run: codeindex init --hooks")
```

#### Hook 脚本生成

```python
def install_hook_script(trigger: str):
    """安装 Git hook 脚本"""
    hook_file = Path(f'.git/hooks/{trigger}')

    # 检查是否已存在其他 hook
    if hook_file.exists():
        existing_content = hook_file.read_text()
        if 'codeindex-auto-update' not in existing_content:
            # 存在其他 hook，需要合并
            console.print("[yellow]Warning: Existing hook found[/yellow]")
            if not click.confirm("Append codeindex hook to existing file?"):
                raise click.Abort()

            # 追加模式
            with open(hook_file, 'a') as f:
                f.write('\n\n')
                f.write(generate_hook_script(trigger))
        else:
            # 覆盖我们自己的 hook
            hook_file.write_text(generate_hook_script(trigger))
    else:
        # 新建
        hook_file.write_text(generate_hook_script(trigger))
        hook_file.chmod(0o755)  # 可执行权限

def generate_hook_script(trigger: str) -> str:
    """生成 hook 脚本内容"""

    if trigger == 'pre-commit':
        return '''#!/bin/bash
# codeindex-auto-update
# Auto-generated by codeindex. Safe to edit.

# 检测 staged 的代码文件
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|php|java|ts|js|go|rs|cpp|c|h)$')

if [ -z "$STAGED_FILES" ]; then
    exit 0  # 没有代码文件变更
fi

echo "📝 codeindex: Updating documentation..."

# 提取受影响的目录（去重）
DIRS=$(echo "$STAGED_FILES" | xargs dirname | sort -u)

# 只更新这些目录（快速）
for dir in $DIRS; do
    codeindex scan "$dir" --quiet 2>&1 | grep -v "^Scanning" || true
done

# 自动 stage 更新的 README_AI.md
git add '**/README_AI.md' 2>/dev/null || true

echo "✓ Documentation updated"
exit 0
'''

    elif trigger == 'post-commit':
        return '''#!/bin/bash
# codeindex-auto-update
# Auto-generated by codeindex. Safe to edit.

# post-commit: 提交后更新（不会阻塞提交）
CHANGED_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD | grep -E '\\.(py|php|java|ts|js|go|rs|cpp|c|h)$')

if [ -z "$CHANGED_FILES" ]; then
    exit 0
fi

echo "📝 codeindex: Updating documentation (background)..."

DIRS=$(echo "$CHANGED_FILES" | xargs dirname | sort -u)

for dir in $DIRS; do
    codeindex scan "$dir" --quiet &
done

wait
echo "✓ Documentation updated"
exit 0
'''

    else:
        raise ValueError(f"Unknown trigger: {trigger}")
```

#### 配置文件更新

```python
def update_config_for_hooks(trigger: str = 'pre-commit', enabled: bool = True):
    """更新 .codeindex.yaml"""
    config_file = Path('.codeindex.yaml')

    if config_file.exists():
        config = yaml.safe_load(config_file.read_text())
    else:
        config = {}

    # 确保结构存在
    if 'indexing' not in config:
        config['indexing'] = {}

    # 更新 auto_update 配置
    config['indexing']['auto_update'] = {
        'enabled': enabled,
        'trigger': trigger,  # pre-commit / post-commit / manual
        'quiet': True,       # 静默输出
        'ignore_errors': True,  # 不因索引失败阻塞提交
    }

    # 写回
    config_file.write_text(yaml.dump(config, sort_keys=False, allow_unicode=True))
```

---

## 📖 README 文档设计（Claude Code 友好）

### 关键部分：快速开始

```markdown
## 🚀 Quick Start

### Installation

\`\`\`bash
# Using pipx (recommended)
pipx install codeindex

# Or using pip
pip install codeindex
\`\`\`

### Setup in Your Project

\`\`\`bash
# Step 1: Initialize codeindex with Git hooks (one command!)
cd /path/to/your/project
codeindex init --hooks --yes

# That's it! Now codeindex will auto-update when you commit.
\`\`\`

**What just happened?**
- ✅ Created `.codeindex.yaml` with smart defaults
- ✅ Installed Git pre-commit hook
- ✅ Configured auto-update on commit

**Claude Code Users**: Just ask Claude to run the above command!

---

### Manual Setup (if you prefer)

\`\`\`bash
# Step 1: Create config
codeindex init

# Step 2: Scan your codebase
codeindex scan-all

# Step 3: (Optional) Enable auto-update
codeindex init --hooks
\`\`\`

---

### Verify Installation

\`\`\`bash
# Check hooks status
codeindex hooks status

# Expected output:
# ✓ Auto-update is active
#   Trigger: pre-commit
\`\`\`

---

## 🤖 For Claude Code Users

**Recommended workflow:**

1. **Ask Claude to read this README:**
   \`\`\`
   User: Read the README from codeindex project
   Claude: [reads documentation]
   \`\`\`

2. **Ask Claude to set up codeindex:**
   \`\`\`
   User: Help me set up codeindex in this project
   Claude: I'll run: codeindex init --hooks --yes
   [executes command]
   ✓ Setup complete!
   \`\`\`

3. **That's it! Start coding:**
   - Every commit auto-updates documentation
   - No manual intervention needed
   - Claude can read updated README_AI.md files

---

## ⚙️ Configuration

### Auto-update Settings

Edit `.codeindex.yaml`:

\`\`\`yaml
indexing:
  auto_update:
    enabled: true           # Enable/disable auto-update
    trigger: pre-commit     # When to update: pre-commit | post-commit | manual
    quiet: true             # Suppress output
    ignore_errors: true     # Don't block commit if indexing fails
\`\`\`

### Disable Auto-update

\`\`\`bash
# Temporarily disable
codeindex hooks disable

# Completely uninstall
codeindex hooks uninstall
\`\`\`

### Re-enable

\`\`\`bash
codeindex hooks enable
# or
codeindex init --hooks --yes
\`\`\`
```

---

## 🎯 Claude Code 集成示例

### 场景 1: 新项目初始化

**用户对话**:
```
User: 我刚 clone 了一个 PHP 项目，帮我配置 codeindex

Claude Code: 好的，我来帮你配置。首先让我检查项目状态...

[执行] ls -la | grep .git
[确认] 这是一个 Git 仓库

[执行] codeindex init --hooks --yes

✓ Created .codeindex.yaml
✓ Installed pre-commit hook
✓ Setup complete!

现在你每次 commit 时，codeindex 会自动更新代码索引。

要生成初始索引，运行：
codeindex scan-all

需要我执行吗？
```

### 场景 2: 检查状态

**用户对话**:
```
User: 检查一下 codeindex 的配置状态

Claude Code: 让我检查一下...

[执行] codeindex hooks status

Git Hooks Status
  Config enabled: Yes
  Hook installed: Yes
  Trigger: pre-commit

✓ Auto-update is active

一切正常！每次提交时会自动更新索引。
```

### 场景 3: 禁用/启用

**用户对话**:
```
User: 暂时关闭自动更新

Claude Code: 好的

[执行] codeindex hooks disable

✓ Disabled auto-update

需要重新启用时，运行：
codeindex hooks enable
```

---

## 🔧 高级场景

### 场景 4: 已有 pre-commit hook

```bash
# 检测到已有 hook
$ codeindex init --hooks

[yellow]Warning: Existing pre-commit hook found[/yellow]

Current hook content:
---
#!/bin/bash
npm run lint
---

Options:
  1. Append codeindex to existing hook (recommended)
  2. Replace with codeindex hook only
  3. Skip hook installation (config only)

Choice [1]: 1

✓ Appended codeindex to existing hook
✓ Updated .codeindex.yaml

Your hook now runs:
  1. npm run lint
  2. codeindex auto-update
```

### 场景 5: 多人协作项目

**最佳实践**:

```bash
# .codeindex.yaml (提交到 repo)
indexing:
  auto_update:
    enabled: false  # 默认禁用（团队成员自主选择）
    trigger: pre-commit

# 每个开发者自己决定是否启用
$ codeindex init --hooks  # 本地启用
```

**或者团队统一启用**:

```bash
# .codeindex.yaml (提交到 repo)
indexing:
  auto_update:
    enabled: true  # 团队统一启用
    trigger: pre-commit

# 项目 README
## Setup
\`\`\`bash
git clone ...
codeindex init --hooks --yes  # 所有成员都运行
\`\`\`
```

---

## 🛡️ 安全设计

### 1. 默认安全策略

```yaml
# 默认配置
indexing:
  auto_update:
    enabled: false        # 默认关闭
    ignore_errors: true   # 不阻塞提交
    timeout: 30           # 30秒超时
```

### 2. Hook 脚本特性

```bash
#!/bin/bash
# codeindex-auto-update

# 1. 错误不阻塞提交
set +e  # 允许命令失败

# 2. 超时保护
timeout 30s codeindex scan "$dir" || true

# 3. 静默输出（可选）
codeindex scan "$dir" --quiet 2>&1 | grep -v "^Scanning" || true

# 4. 后台执行（post-commit 模式）
codeindex scan "$dir" &

# 5. 总是返回成功
exit 0
```

### 3. 用户控制

```bash
# 随时禁用
codeindex hooks disable

# 临时跳过（单次提交）
git commit --no-verify -m "message"

# 完全卸载
codeindex hooks uninstall
```

---

## 📊 用户体验对比

### 传统方式（其他工具）

```bash
# 1. 安装工具
pip install some-tool

# 2. 手动创建配置文件
cat > .sometool.yaml <<EOF
hooks:
  pre-commit:
    - run: some-tool index
      stages: [commit]
EOF

# 3. 安装 hook 框架
pip install pre-commit
pre-commit install

# 4. 测试
pre-commit run --all-files

# 总计：4步，3个工具，1个配置文件
```

### codeindex 方式

```bash
# 一条命令
codeindex init --hooks --yes

# 总计：1步，搞定！
```

**对比**:
- ✅ 步骤减少 75%
- ✅ 工具数量减少 67%
- ✅ 学习成本降低 80%
- ✅ Claude Code 可直接执行

---

## 🎓 设计哲学

### 1. Convention over Configuration

**默认就好用**:
- 自动检测项目类型（PHP/Python/Java）
- 自动选择合适的触发时机（pre-commit）
- 自动配置安全策略（不阻塞提交）

### 2. Progressive Disclosure

**简单优先，高级可选**:

```bash
# 层级 1：零配置
codeindex init --hooks --yes  # 99% 用户够用

# 层级 2：基础配置
codeindex init --hooks --trigger=post-commit

# 层级 3：高级配置
# 编辑 .codeindex.yaml 自定义
```

### 3. Safe by Default

**绝不破坏用户工作流**:
- ❌ 不自动启用（需要用户确认）
- ❌ 不阻塞提交（索引失败不影响 commit）
- ❌ 不覆盖已有 hook（智能合并）
- ✅ 可随时禁用/卸载

### 4. Claude Code First

**为 AI 助手优化**:
- ✅ 所有操作都是 bash 命令
- ✅ 输出清晰易读（Claude 可理解）
- ✅ 错误信息明确（Claude 可处理）
- ✅ 文档完整（Claude 可学习）

---

## 📝 实施清单

### Phase 1: 核心命令（2天）

- [ ] `codeindex init --hooks` 命令
- [ ] `codeindex hooks install/uninstall/status` 命令
- [ ] Hook 脚本生成逻辑
- [ ] 配置文件更新逻辑
- [ ] 已有 hook 检测和合并

### Phase 2: 安全增强（1天）

- [ ] 超时保护
- [ ] 错误隔离（不阻塞提交）
- [ ] 用户确认流程
- [ ] 卸载清理

### Phase 3: 文档和测试（1天）

- [ ] README 更新（Claude Code 友好）
- [ ] 单元测试（10个）
- [ ] 集成测试（hook 执行）
- [ ] 多场景验证

**总计**: 4天

---

## 🎯 成功指标

### 用户体验目标

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| 安装成功率 | >95% | 命令执行成功率 |
| 零配置可用性 | >90% | 默认配置满足需求比例 |
| Claude Code 可执行性 | 100% | 所有操作都是命令 |
| 用户满意度 | ⭐⭐⭐⭐⭐ | 反馈评分 |

### 技术目标

| 指标 | 目标 |
|------|------|
| Hook 执行时间 | <2秒（单目录） |
| 不阻塞提交 | 100%（即使失败） |
| 兼容性 | Git 2.0+ |
| 测试覆盖率 | >85% |

---

**Generated**: 2026-02-02
**Status**: Design Complete
**Next**: Implementation (4天)
