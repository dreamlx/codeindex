# codeindex 项目概览

## 项目目的
codeindex 是一个 AI 原生的代码索引工具，专为大型代码库设计。它自动使用 tree-sitter 解析和外部 AI CLI 生成智能文档 (`README_AI.md`)，帮助理解大型代码库、新开发者入职和维护活文档。

## 技术栈
- **语言**: Python 3.10+
- **核心依赖**:
  - click (CLI框架)
  - pyyaml (配置文件)
  - rich (终端输出)
  - tree-sitter (代码解析)
  - tree-sitter-python, tree-sitter-php (语言支持)
- **开发工具**:
  - pytest (测试)
  - ruff (代码格式化和检查)
  - hatchling (构建)

## 代码风格和约定
- **行长度**: 100字符
- **代码格式**: 使用 ruff format
- **代码检查**: ruff check
- **测试**: TDD (测试驱动开发)
- **文档字符串**: 100%覆盖
- **类型提示**: Python 3.10+ 支持

## 命令使用
```bash
# 开发模式安装
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行单个测试
pytest tests/test_parser.py::test_parse_simple_function

# 代码检查
ruff check src/

# 代码格式化
ruff format src/

# CLI使用
codeindex scan-all --fallback    # 生成所有索引
codeindex status                  # 查看覆盖率
codeindex symbols                 # 生成符号索引
```

## 项目结构
```
src/codeindex/
├── cli.py              # CLI入口点
├── scanner.py          # 目录扫描
├── parser.py           # tree-sitter解析
├── writer.py           # 格式化和写入
├── invoker.py          # AI CLI调用
├── config.py           # 配置管理
├── smart_writer.py     # 智能写入（分层）
├── hierarchical.py     # 分层处理
├── symbol_scorer.py    # 符号重要性评分 (v0.2.0新增)
├── adaptive_config.py   # 自适应配置 (v0.2.0新增)
├── adaptive_selector.py # 自适应符号选择 (v0.2.0新增)
└── incremental.py       # 增量更新
```

## 关键特性
1. **智能符号评分** (v0.2.0): 5维度评分系统，重要符号优先
2. **自适应符号提取** (v0.2.0): 根据文件大小动态调整符号数量
3. **分层文档生成**: 三级智能索引系统
4. **AI增强**: 支持Claude、OpenAI等AI CLI
5. **并行处理**: 支持多目录并发扫描

## 配置文件
- `.codeindex.yaml`: 项目配置文件
- 支持include/exclude模式
- 可配置AI命令
- 可配置语言支持

## Git工作流
- GitFlow: master ← develop ← feature/*
- 提交格式: feat/scope, fix/scope, docs/scope等
- 版本标签: v0.2.0等

## 重要文件
- `CLAUDE.md`: Claude Code工作指南
- `README_AI.md`: AI生成的目录文档（每个目录）
- `PROJECT_INDEX.md`: 项目概览索引
- `PROJECT_SYMBOLS.md`: 全局符号索引
- `CHANGELOG.md`: 版本变更历史