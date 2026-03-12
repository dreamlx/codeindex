## 🔍 CodeIndex 使用指南

### 📦 已安装版本
- **当前版本**: v{version}
- **安装位置**: `/Users/dreamlinx/Projects/codeindex`

### 🚀 核心命令

#### 1. 初始化配置
```bash
cd /your/project
codeindex init  # 生成 .codeindex.yaml 配置文件
```

#### 2. 扫描与文档生成
```bash
# 扫描单个目录（生成结构化 README_AI.md）
codeindex scan ./src/auth

# 扫描所有目录（SmartWriter 模式）
codeindex scan-all

# 当配置了 ai_command 时，自动启用 AI 一句话模块描述
# Phase 1: 生成结构化 README_AI.md
# Phase 2: AI 为每个非叶子目录生成 blockquote 功能描述
codeindex scan-all

# 禁用 AI 增强（仅结构化文档）
codeindex scan-all --no-ai

# 单目录完整 AI 生成（AI 生成整个 README 内容）
codeindex scan ./src/auth --ai

# 预览 AI 提示词（不执行）
codeindex scan ./src/auth --ai --dry-run

# 生成 JSON 输出（用于工具集成）
codeindex scan ./src --output json
codeindex scan-all --output json > parse_results.json
```

#### 3. 符号索引与导航
```bash
# 生成全局符号索引（PROJECT_SYMBOLS.md）
codeindex symbols

# 生成模块概览索引（PROJECT_INDEX.md）
codeindex index

# Git 变更影响分析
codeindex affected --since HEAD~5 --until HEAD
codeindex affected --json  # CI/CD 集成
```

#### 4. 技术债务分析 (v0.22.0+)
```bash
# 分析目录的技术债务
codeindex tech-debt ./src

# 不同输出格式
codeindex tech-debt ./src --format console    # 控制台（默认）
codeindex tech-debt ./src --format markdown   # Markdown 文档
codeindex tech-debt ./src --format json       # JSON 格式

# 递归分析 + 保存报告
codeindex tech-debt ./src --recursive --output debt_report.md
```

**检测问题**:
- 🔴 超大文件（>5000 行）
- 🔴 上帝类（>50 方法）
- 🟡 符号过载（>100 符号）
- 🟠 高噪音比（>50% 低质量符号）

#### 5. 状态检查
```bash
# 查看索引状态（哪些目录已生成文档）
codeindex status
```

### 🌍 语言支持

| 语言 | 状态 | 特性 | 版本 |
|------|------|------|------|
| Python | ✅ 已支持 | 类、函数、方法、导入、docstring | v0.1.0+ |
| PHP | ✅ 已支持 | 类（继承/接口）、方法（可见性、静态、返回类型）、属性、函数、PHPDoc | v0.2.0+ |
| TypeScript | ✅ 已支持 | 类、接口、函数、导入导出 | v0.3.0+ |
| JavaScript | ✅ 已支持 | 类、函数、导入导出 | v0.3.0+ |
| Java | ✅ 已支持 | 类、接口、方法、字段、包 | v0.6.0+ |
| Go | ✅ 已支持 | 类型、函数、方法、接口 | v0.6.0+ |
| Rust | ✅ 已支持 | 结构体、枚举、trait、函数 | v0.6.0+ |
| Swift | ✅ 已支持 | 类、结构体、枚举、协议、扩展、方法、属性 | v0.21.0+ |
| Objective-C | ✅ 已支持 | 类、协议、类别、属性、方法（实例/类） | v0.21.0+ |

### 💡 最佳实践

1. **初始化项目时**:
   ```bash
   codeindex init
   codeindex scan-all  # 生成完整索引
   ```

2. **日常开发**:
   - 使用 Git Hooks 自动更新（mode: auto）
   - 大改动后手动运行 `codeindex affected` 检查影响范围

3. **AI Code 使用**:
   - 先让 AI 读取 README_AI.md，而非直接 Glob/Grep
   - 使用 Serena MCP 符号工具进行精确导航
   - 只在需要时才读取源文件

4. **技术债务管理**:
   ```bash
   # 定期运行债务分析
   codeindex tech-debt ./src --recursive --output reports/tech-debt.md
   ```

### 🔗 相关资源

- **项目地址**: `/Users/dreamlinx/Projects/codeindex`
- **在线文档**: [GitHub README](https://github.com/yourusername/codeindex)
- **配置指南**: `docs/guides/configuration.md`
- **Claude Code 集成**: `docs/guides/claude-code-integration.md`
- **Git Hooks 指南**: `docs/guides/git-hooks-integration.md`

---

**💡 提示**: 运行 `/codeindex-update-guide` 可以深度定制本指南（需要 v0.22.3+）
