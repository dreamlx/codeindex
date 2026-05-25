# ADR 004: 客户 CLAUDE.md 更新机制

## 状态

已修订 (Revised) — 2026-05-25
原决策日期: 2026-03-08

## 背景

codeindex 快速迭代时，客户 `CLAUDE.md` 中的 codeindex 使用指南容易过时：版本号不一致、新命令缺失、用户需要手动同步。

## 决策

**采用 CLI 命令 + 过时提示的两层机制。不实现 pip post-install hook。**

1. **`codeindex claude-md update`** — 显式、幂等更新项目 `CLAUDE.md` 的 codeindex 段落（marker-based injection）
2. **`codeindex claude-md check` 过时提示** — 其他命令路径触发版本不一致警告，引导用户运行 update
3. **`/codeindex-update-guide` Skill**（可选） — Claude Code 环境下交互式深度定制

## 修订理由（2026-05-25）

原决策包含 pip post-install hook 自动更新。**该方案已撤回**：

- ❌ pip 没有稳定的 post-install hook 标准（PEP 660 不覆盖此场景）
- ❌ 原型代码 `hooks.py::post_install_update_guide()`（181 行）写完后从未接到 entry-points，等同死代码，已在 v0.24.0 删除
- ❌ 实现真 hook 需要 setup.py custom command 等 hack 路径，违反 KISS
- ✅ CLI 命令 + 过时警告已覆盖 95% 场景；剩余 5% 用 Skill

KISS：少一个会失败的自动化路径，多一个用户能 own 的命令。

## 实施现状

| 组件 | 状态 | 位置 |
|------|------|------|
| `codeindex claude-md update` | ✅ 已实现 | `src/codeindex/cli_claude_md.py` |
| `codeindex claude-md check` | ✅ 已实现 | `src/codeindex/cli_claude_md.py` |
| 版本过时警告 | ✅ 已实现 | `src/codeindex/claude_md.py::check_outdated()` |
| `/codeindex-update-guide` Skill | ✅ 已实现 | `~/.claude/skills/codeindex-update-guide/` |
| pip post-install hook | ❌ 不实现 | 死代码已在 v0.24.0 删除 |

## 升级流程（当前）

```bash
pip install --upgrade ai-codeindex
codeindex claude-md update      # 显式刷新项目 CLAUDE.md
```

Release notes 与 pre-release checklist 应在升级流程中显式引导这条命令。

## 相关 ADR

- ADR 002: 外部 AI CLI 集成（为什么需要 CLAUDE.md）
- ADR 005: 导航契约与 README 大小上限

---

**决策人**: dreamlinx
**原始日期**: 2026-03-08
**修订日期**: 2026-05-25
**状态**: 已修订，post-install hook 部分已撤回
