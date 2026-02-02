# codeindex 常用命令

## 核心命令
```bash
# 生成所有目录索引（最常用）
codeindex scan-all --fallback

# 查看会扫描哪些目录
codeindex list-dirs

# 生成全局符号索引
codeindex symbols

# 查看索引覆盖率
codeindex status

# 初始化配置
codeindex init
```

## 扫描命令
```bash
# 扫描单个目录
codeindex scan ./src/auth

# 预览prompt（不执行）
codeindex scan ./src/auth --dry-run

# 不使用AI生成（fallback模式）
codeindex scan ./src/auth --fallback

# AI增强所有目录（高质量）
codeindex scan-all --ai-all
```

## 开发命令
```bash
# 安装（开发模式）
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check src/

# 代码格式化
ruff format src/

# 重新生成所有索引
codeindex scan-all --fallback
```

## 高级命令
```bash
# 查看符号详情
codeindex find-symbol --name "ClassName" --path "./src/module.py"

# 查看符号引用
codeindex find-references --name "method_name"

# 增量更新（只更新变更文件）
codeindex scan-all --incremental

# 并行处理（提高速度）
codeindex scan-all --workers 8
```

## MCP技能（已安装）
- `/mo:arch` - 查询代码架构
- `/mo:index` - 生成项目索引