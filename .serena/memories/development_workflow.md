# codeindex 开发指南

## 必须阅读的文件
1. **CLAUDE.md** - Claude Code工作流程指南
2. **src/codeindex/README_AI.md** - 核心模块架构
3. **tests/README_AI.md** - 测试结构和覆盖
4. **docs/planning/** - Epic/Story规划文档

## 代码导航最佳实践

### 理解架构时
1. 先读 README_AI.md 文件（分层结构）
2. 使用 PROJECT_SYMBOLS.md 查找符号位置
3. 使用 find_symbol 查看具体定义

### 查找代码时
```python
# 查找符号定义
find_symbol(name_path_pattern="AdaptiveSymbolSelector")

# 查找符号引用
find_referencing_symbols(name_path="calculate_limit", relative_path="src/codeindex/adaptive_selector.py")

# 获取文件概览
get_symbols_overview(relative_path="src/codeindex/parser.py", depth=1)
```

## TDD开发流程（严格）
1. **Red**: 写失败的测试
2. **Green**: 实现最小代码使测试通过
3. **Refactor**: 重构优化

### 测试命令
```bash
# 运行所有测试
pytest -v

# 运行特定测试
pytest tests/test_new_feature.py -v

# 测试覆盖率
pytest --cov=src/codeindex --cov-report=term-missing

# 要求：核心模块 ≥ 90%，整体 ≥ 80%
```

## 代码质量检查
提交前必须通过：
```bash
# 1. 测试全部通过
pytest -v

# 2. 代码规范检查
ruff check src/

# 3. 类型检查（可选）
mypy src/
```

## 修改代码流程
1. **创建feature分支**
2. **TDD实现**
3. **更新CHANGELOG.md**
4. **提交到develop**
5. **合并到master并打tag**

## 重要提醒
- ❌ 不要直接修改生成的 README_AI.md
- ❌ 不要跳过测试写实现
- ❌ 不要用 Glob/Grep 搜索代码
- ✅ 使用 Serena MCP 的符号工具
- ✅ 先读 README_AI.md 理解架构
- ✅ 遵循 GitFlow 工作流