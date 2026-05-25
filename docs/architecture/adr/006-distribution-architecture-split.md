# ADR 006: 分发架构拆分 — pipx CLI + 独立 plugin repo

## 状态

已采纳 (Accepted) — 2026-05-25

## 背景

v0.24.0 发布过程中，三件事同时浮出水面：

1. **国内镜像同步延迟**：阿里云 PyPI 镜像 v0.24.0 发布后数小时仍返回 0.23.2，国内用户拿不到新版。
2. **ADR-004 的退却惯性**：v0.24.0 已经把 pip post-install hook 撤回，但 CLAUDE.md 注入、git hooks 安装、4 个 Skill（`mo-arch` / `mo-hooks` / `mo-index` / `codeindex-update-guide`）的分发逻辑仍然耦合在 wheel 里，靠 `skills/install.sh` 这种半自动脚本搬运。维护成本高、升级路径脆弱。
3. **codeindex 工具属性双重身份的混淆**：codeindex 是 Python CLI 工具（PyPI 标准分发），但同时也是 Claude Code 用户的代码导航伙伴（需要 Skill + Plugin 集成）。把后者也塞进 wheel 是反层级——就像 npm 包不应该改 VSCode `settings.json`。

继续把所有东西塞进 wheel + 用 `install.sh` 搬运 Skills，可预见的失败模式：

- 用户 `pipx install ai-codeindex` 之后，Skill 没自动 active（pipx 不会跑 install.sh 进用户 home）
- 不用 Claude Code 的用户（Cursor / Continue / 裸 CLI）被强制吃 Claude 相关包袱
- Skill 升级要绑死 wheel 升级周期，反应慢
- 镜像延迟同时拖累 wheel 和 Skill（两者本可解耦）

## 决策

**codeindex 拆为两个独立 artifact**：

| Artifact | 内容 | 分发渠道 | 安装命令 |
|---|---|---|---|
| `ai-codeindex` | 纯 Python CLI（`codeindex scan` / `parse` / `symbols` / `hooks install` / `claude-md update` 等子命令） | PyPI（trusted publisher） | `pipx install ai-codeindex` |
| `dreamlx/codeindex-claude` | Claude Code Plugin，bundle 4 个 Skill + SessionStart 自检 hook + CLAUDE.md template fragment | GitHub（之后提交到 `anthropics/claude-plugins-community`） | `/plugin install codeindex@codeindex-claude`（私有 marketplace 阶段）；通过 community 之后变 `/plugin install codeindex@claude-community` |

**核心原则**：CLI wheel 禁止任何 install-time 修改 `~/.claude/*` 或 `<project>/.claude/*` 的逻辑。Skill / Plugin 配置全部走 Plugin repo + Claude Code 原生 plugin 机制。

### Skill 命名简化

原 `mo-arch` / `mo-hooks` / `mo-index` / `codeindex-update-guide` 在 Plugin 内自动 namespace 成：

- `codeindex:arch`
- `codeindex:hooks`
- `codeindex:index`
- `codeindex:update-guide`

去掉 `mo-` 前缀（旧 prefix 已无价值，Plugin namespace 自动消歧）。

### 用户体验目标

**最终的两行 onboarding**：

```bash
pipx install ai-codeindex                                   # the tool
/plugin install codeindex@claude-community                  # Claude Code integration (optional)
```

不用 Claude Code 的用户只需要第一行。

## 理由

### 1. 为什么 pipx 而不是 pip？

- codeindex 是 CLI 工具（不是库），用户不需要 `import codeindex`
- pipx 的 per-tool venv 隔离消除依赖冲突
- PEP 668 之后 system `pip install` 越来越痛苦，pipx 是现代默认
- pipx 升级是 atomic 操作，不污染其他 Python 环境
- pipx 走 `python -m pip` 但可独立配置 `--index-url`，避开 user 系统级 pip 镜像配置（如阿里云延迟问题）

### 2. 为什么 Plugin 而不是继续 install.sh？

| 维度 | install.sh（现状） | Claude Code Plugin |
|---|---|---|
| 安装一致性 | 用户必须 `cd codeindex/` 跑 `./skills/install.sh`，pipx 用户拿不到 | `/plugin install` 标准命令，平台原生 |
| 升级路径 | 用户必须手动重跑 install.sh | `/plugin update` 或自动 |
| 版本隔离 | Skill 版本绑死 wheel 版本 | 两个 repo 独立 semver |
| 卸载 | 手删 `.claude/skills/` | `/plugin uninstall` |
| 发现性 | README 文字 | community marketplace 列表 |
| 多个 Skill 协调 | 各自独立文件 | Plugin 内 namespace 自动同步 |

### 3. 为什么不一个 monorepo 双 artifact？

考虑过 `codeindex/{cli,plugin}/` 单仓多 artifact，否决理由：

- Plugin 的迭代周期（prompt tuning / Skill workflow 调整）远快于 CLI（parser / extractor 演进），合在一起会让 CHANGELOG 变嘈杂
- CI 配置复杂化（两套不同的 release pipeline）
- 给 Cursor / Continue 加适配时还要再分仓，不如一开始就分

### 4. mo-* 三个 Skill 为什么 bundle 成一个 Plugin 而不是三个独立 Skill？

- 三者共享同一个用户 mental model（"用 codeindex 索引 / 查询 / 自动化"），不可分割
- Plugin 内 Skill 自动 namespace（`codeindex:arch` 等），不存在命名冲突
- 一次 `/plugin install` 拿全套能力，符合 [[feedback-kiss-minimum-viable]]
- 用户反馈如果证明某个 Skill 实际使用率极低，再单拆也不迟（YAGNI）

### 5. 外部 prereq（`codeindex` 必须在 PATH）怎么处理？

Claude Code Plugin spec 目前**没有** declarative `requires` 字段。我们用 SessionStart hook 自检：

```sh
# codeindex-claude/hooks/check-codeindex.sh
if ! command -v codeindex >/dev/null 2>&1; then
  echo "⚠ codeindex plugin loaded but \`codeindex\` CLI not in PATH."
  echo "  Install: pipx install ai-codeindex"
fi
```

每次会话起来跑一次，错过的用户秒看到清晰提示。比 Skill 调用时才报错友好。

## 实施计划

参考 codeindex repo Epic `v0.25.0 — Distribution architecture split`（issue 链接待补）。

简版时间线（约 5 工作日）：

- **A1**：本 ADR（已完成）
- **A2**：`gh repo create dreamlx/codeindex-claude`，bootstrap 骨架（`.claude-plugin/plugin.json` + 4 个 Skill 占位 + SessionStart hook + README + `marketplace.json`）
- **A3**：从现有 codeindex repo `skills/src/` 和 `.claude/skills/` 把 4 个 Skill 迁移到新 repo，更名去 `mo-` 前缀
- **A4**：Plugin README 明确写 prereq（先 `pipx install ai-codeindex`）+ 截图引导
- **B1**：codeindex repo: `codeindex init` 砍掉所有 `~/.claude` 副作用，只生成 `.codeindex.yaml`
- **B2**：codeindex repo README 主推 `pipx install` + 引导 plugin install
- **B3**：`codeindex claude-md update` / `codeindex hooks install` 加 deprecation 提示（"will be plugin-managed in v1.0"），但保留命令
- **B4**：CHANGELOG.md + RELEASE_NOTES_v0.25.0.md 写迁移指南
- **C**：同步发版 codeindex v0.25.0 + codeindex-claude v0.1.0

## 影响范围

### 代码变更（codeindex repo）

- `src/codeindex/cli_config.py::init`：砍掉 `_update_gitignore` 之外的 `~/.claude` 副作用（如果有）
- `skills/` 目录：标记 deprecation，CHANGELOG 引导用户改装 plugin
- `README.md` / `CLAUDE.md`：主推 `pipx install`，加 plugin install 一段
- `CHANGELOG.md` + `RELEASE_NOTES_v0.25.0.md`：迁移指南

### 新建仓库

- `dreamlx/codeindex-claude`（公开）

### 用户影响

| 现有用户场景 | v0.25.0 之后 |
|---|---|
| 已经 `pip install ai-codeindex` + 跑过 `./skills/install.sh` | Skills 仍能用（旧 `.claude/skills/{mo-*}` 不主动删），但新 release 不再更新它们；建议改用 `/plugin install` |
| 已经 `pip install ai-codeindex` + 没装 skills | `pipx install ai-codeindex` 取代旧装；想要 Claude 集成走 `/plugin install` |
| 新用户 | 两行 onboarding（pipx + /plugin），与 README 一致 |
| 不用 Claude Code 的用户（Cursor / 裸 CLI） | 只 `pipx install ai-codeindex`，零 Claude 包袱 |

### 文档变更

- ADR-006（本文件，新增）
- ADR-004 状态加交叉链接到 ADR-006
- README.md（codeindex + codeindex-claude 两份）
- CLAUDE.md（codeindex 项目根）
- 新 repo 的 README.md / marketplace.json

## 替代方案（已否决）

### 方案 1：继续单 wheel + 加更多 install-time magic

- ❌ 已经在 ADR-004 撤回过 post-install hook，再撞同一面墙没意义
- ❌ pipx 用户拿不到 Skill 是死结
- ❌ Cursor 等非 Claude Code 用户被强制吃集成包袱

### 方案 2：monorepo 双 artifact（`codeindex/{cli,plugin}/`）

- ❌ Plugin 迭代周期快、CLI 慢，强绑 CHANGELOG 嘈杂
- ❌ CI 复杂化
- ❌ 给 Cursor 加适配时还要再分（拖延决策）

### 方案 3：把 Skill 也发到 PyPI（`ai-codeindex-skills` package）

- ❌ PyPI 不是 Claude Code 的 plugin 分发机制，用户依然要手工符号链接到 `~/.claude/skills/`
- ❌ Plugin 已经是平台原生标准，绕开它就是反平台

## 成功指标

### 量化指标（6 个月后评估）

- ✅ Plugin install 数量（marketplace 数据）
- ✅ "CLAUDE.md 没自动更新" 类 issue 数量下降 ≥80%
- ✅ Cursor / Continue 用户安装 codeindex CLI 的反馈出现（说明分离让非 Claude 用户能用）

### 质性指标

- ✅ 新用户能凭 README 两行命令独立 onboard，不需要支持介入
- ✅ Skill 升级（prompt tuning）不再触发 wheel 发版

## 相关 ADR

- ADR 002: 外部 AI CLI 集成（为什么需要 CLAUDE.md）
- ADR 004: 客户 CLAUDE.md 更新机制（本决策的 precedent—第一次退却 install-time magic）
- ADR 005: 导航契约与 README 大小上限（codeindex 价值在消费侧的进一步明确）

## 参考资料

- Claude Code plugin spec: https://code.claude.com/docs/en/plugins-reference.md
- Plugin marketplace: https://code.claude.com/docs/en/plugin-marketplaces.md
- pipx 推荐做法：https://pipx.pypa.io/

---

**决策人**: dreamlinx
**日期**: 2026-05-25
**状态**: 已采纳，待实施（v0.25.0 周期）
