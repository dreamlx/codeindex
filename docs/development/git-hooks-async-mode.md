# Git Hooks Async Mode

**版本**: v4
**实施日期**: 2026-02-04
**Story**: Epic JSON Output, Story 6

---

## 🎯 问题

**当前 post-commit hook 性能问题**：
- 同步执行：阻塞用户工作流
- 长时间等待：3 个目录 × 30 秒 = 90 秒阻塞
- 用户体验差：无法立即 push 或继续开发

## ✅ 解决方案

**智能异步模式**：
- ≤2 个目录：同步执行（快速完成，保持现有体验）
- >2 个目录：异步执行（后台运行，立即返回）

## 🚀 实现

### 核心改动

**文件结构**：
```
.git/hooks/
├── post-commit           # v4: 主 hook（带异步支持）
├── post-commit-update-logic.sh  # 共享更新逻辑
├── post-commit.v3.backup # v3 备份
└── ~/.codeindex/hooks/   # 运行时文件
    ├── post-commit.log   # 异步日志
    ├── post-commit.pid   # 进程 ID
    └── post-commit.lock  # 锁文件
```

### 工作流程

#### 同步模式（≤2 目录）
```
提交代码 → 分析变更 → 更新 README → 创建 commit → 完成
         ↑________________________等待_________________↑
```

#### 异步模式（>2 目录）
```
提交代码 → 分析变更 → 启动后台进程 → 立即返回
                     ↓
                  （后台）更新 README → 创建 commit
```

### 用户体验

**同步模式输出（2 个目录）**：
```bash
📝 Post-commit: Analyzing changes...
   Update level: full
   Found 2 directory(ies) to check

→ Running in sync mode (waiting for completion)

→ Updating src/codeindex/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

→ Updating tests/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

→ Committing 2 updated README_AI.md file(s)...
✓ README_AI.md updates committed

✓ Post-commit hook completed
```

**异步模式输出（3 个目录）**：
```bash
📝 Post-commit: Analyzing changes...
   Update level: full
   Found 3 directory(ies) to check

⚡ Running in async mode (non-blocking)
   3 directories will be updated in background
   Log: ~/.codeindex/hooks/post-commit.log

   To check progress: tail -f ~/.codeindex/hooks/post-commit.log
   Or wait for completion: while [ -f ~/.codeindex/hooks/post-commit.lock ]; do sleep 1; done

✓ You can continue working. Updates will commit automatically.
```

## 🛠️ 技术细节

### 锁文件机制

防止多个后台进程同时运行：
```bash
# 检查锁文件
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE")
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "⚠ Another update in progress"
        exit 0
    fi
fi

# 创建锁文件
echo $$ > "$LOCK_FILE"
```

### 后台进程

使用 `nohup` 确保进程不被终端关闭：
```bash
nohup zsh -c '
    # 更新逻辑
    source post-commit-update-logic.sh

    # 清理
    rm -f "$LOCK_FILE" "$PID_FILE"
' > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
```

### 日志管理

日志文件格式：
```
=== Post-commit async update started at 2026-02-04T10:30:15 ===
Commit: 5a89ba2 - feat(json): add --output json
Update level: full
Directories: 3

→ Updating src/codeindex/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

→ Updating tests/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

→ Updating docs/README_AI.md
   Invoking AI CLI...
   ✓ Updated via AI

→ Committing 3 updated README_AI.md file(s)...
✓ README_AI.md updates committed

=== Update completed at 2026-02-04T10:32:30 ===
```

## 📊 性能对比

| 场景 | v3 (sync) | v4 (async) | 改进 |
|------|-----------|------------|------|
| 2 个目录 | 60 秒（阻塞） | 60 秒（阻塞） | 无变化 |
| 3 个目录 | 90 秒（阻塞） | <1 秒（立即返回） | ✅ 90 倍提升 |
| 5 个目录 | 150 秒（阻塞） | <1 秒（立即返回） | ✅ 150 倍提升 |

## 🔍 监控和调试

### 检查后台进程状态

```bash
# 检查是否有更新在运行
ls -la ~/.codeindex/hooks/post-commit.lock

# 查看进程 ID
cat ~/.codeindex/hooks/post-commit.pid

# 检查进程是否存在
ps aux | grep $(cat ~/.codeindex/hooks/post-commit.pid)
```

### 实时查看日志

```bash
# 实时跟踪
tail -f ~/.codeindex/hooks/post-commit.log

# 查看最近日志
tail -50 ~/.codeindex/hooks/post-commit.log
```

### 等待完成

```bash
# 阻塞等待完成
while [ -f ~/.codeindex/hooks/post-commit.lock ]; do
    echo "Waiting..."
    sleep 1
done
echo "✓ Update completed"
```

## 🚨 故障排查

### 后台进程卡住

```bash
# 1. 检查锁文件
ls -la ~/.codeindex/hooks/post-commit.lock

# 2. 查看日志最后几行
tail -20 ~/.codeindex/hooks/post-commit.log

# 3. 手动清理（如果确认进程已死）
rm ~/.codeindex/hooks/post-commit.lock
rm ~/.codeindex/hooks/post-commit.pid
```

### 恢复到 v3

```bash
# 如果需要回退
cp .git/hooks/post-commit.v3.backup .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

## 🔮 未来改进

Story 6 完整实现将包括：
- [ ] 配置文件支持 (`.codeindex.yaml`)
- [ ] 手动选择模式 (async/sync/prompt/disabled)
- [ ] 并行处理多个目录
- [ ] 更详细的进度提示
- [ ] 日志文件轮转

## 📝 变更日志

**v4 (2026-02-04)**:
- ✅ 智能异步模式（≤2 sync, >2 async）
- ✅ 后台进程支持 (nohup)
- ✅ 锁文件防并发
- ✅ 日志文件记录
- ✅ 清晰的用户提示

**v3 (2026-01-19)**:
- 使用 `codeindex affected` 智能检测
- 增量更新支持

**v2 (2026-01-15)**:
- 基础 post-commit hook

---

**测试覆盖**:
- ✅ 2 个目录（同步模式）
- ✅ 3 个目录（异步模式）
- ✅ 并发提交（锁文件保护）
- ✅ 后台进程完成后自动 commit
- ⏳ 配置文件支持（待 Story 6 完整实现）
