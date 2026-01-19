# ADR 001: 使用 tree-sitter 进行代码解析

## 状态
已采纳 (Accepted)

## 背景
codeindex 需要一个可靠的代码解析器来提取符号信息（类、函数、方法、导入等）。主要考虑以下方案：

1. **AST (Python's ast module)** - Python 内置
2. **tree-sitter** - 多语言增量解析器
3. **Language Server Protocol (LSP)** - 完整的语言服务

## 决策
选择 **tree-sitter** 作为代码解析引擎。

## 理由

### 优势
1. **多语言支持**: 一个统一的 API 支持 30+ 编程语言
2. **高性能**: C 实现，增量解析，适合大型代码库
3. **容错性强**: 即使代码有语法错误也能部分解析
4. **生态成熟**: GitHub 在用，有完善的语言 grammar
5. **Python 绑定**: `py-tree-sitter` 封装良好

### 劣势
1. **学习曲线**: 需要了解 query 语法
2. **依赖外部库**: 每个语言需要独立的 grammar
3. **不如 LSP 精确**: 缺少类型推导、跳转定义等高级功能

### 为什么不选 AST
- 只支持 Python，无法扩展到其他语言
- 需要代码语法完全正确

### 为什么不选 LSP
- 过于重量级，需要启动语言服务器
- 每个语言需要不同的 LSP 实现
- 我们只需要符号提取，不需要完整的 IDE 功能

## 后果

### 积极影响
- 可以轻松扩展到 TypeScript/Java/Go 等语言
- 解析速度快，适合大型项目
- 容错性好，即使有语法错误也能生成部分索引

### 消极影响
- 需要为每个语言编写 tree-sitter query
- 安装时需要下载语言 grammar（增加包大小）

## 实现细节
- Python 解析: `tree-sitter-python`
- Query 文件: `src/codeindex/queries/{language}.scm`
- 增量解析: 未来可通过 `edit()` API 优化

## 参考
- [tree-sitter 官网](https://tree-sitter.github.io/)
- [py-tree-sitter 文档](https://github.com/tree-sitter/py-tree-sitter)
