# 多语言支持开发测试流程规范

**Created**: 2026-02-07
**Version**: 1.0
**Purpose**: 标准化新语言支持的开发和测试流程

---

## 📋 目录

1. [流程概览](#流程概览)
2. [环境依赖管理](#环境依赖管理)
3. [TDD 开发流程](#tdd-开发流程)
4. [测试覆盖标准](#测试覆盖标准)
5. [CI/CD 集成](#cicd-集成)
6. [已支持语言](#已支持语言)
7. [常见问题](#常见问题)

---

## 流程概览

### 添加新语言支持的标准步骤

```
1. 环境准备 (Day 0)
   └── 安装 tree-sitter-{language}
   └── 更新 pyproject.toml
   └── 验证安装成功

2. TDD 开发 (Day 1-N)
   └── 编写失败测试 (Red)
   └── 实现最小功能 (Green)
   └── 重构优化 (Refactor)
   └── 重复直到功能完整

3. 集成验证 (Day N+1)
   └── 运行完整测试套件
   └── 验证向后兼容性
   └── 性能基准测试
   └── 文档更新

4. 发布准备 (Day N+2)
   └── 更新 CHANGELOG
   └── 生成 README_AI.md
   └── Code Review
   └── 合并到 develop
```

---

## 环境依赖管理

### 依赖声明标准 (pyproject.toml)

```toml
[project.optional-dependencies]
# 语言特定 parsers（按需安装）
python = ["tree-sitter-python>=0.21"]
php = ["tree-sitter-php>=0.23"]
java = ["tree-sitter-java>=0.23.0"]
typescript = ["tree-sitter-typescript>=0.21.0"]  # 未来
go = ["tree-sitter-go>=0.21.0"]                  # 未来
rust = ["tree-sitter-rust>=0.21.0"]              # 未来

# 便捷选项：安装所有语言
all = [
    "tree-sitter-python>=0.21",
    "tree-sitter-php>=0.23",
    "tree-sitter-java>=0.23.0",
    # 未来语言将自动添加到这里
]
```

### 安装命令

```bash
# 方式1: 安装单个语言
pip install -e ".[python]"
pip install -e ".[php]"
pip install -e ".[java]"

# 方式2: 安装所有语言
pip install -e ".[all]"

# 方式3: 开发环境（推荐）
pip install -e ".[dev,all]"

# 方式4: 系统环境（macOS Homebrew Python）
pip3 install tree-sitter-{language} --break-system-packages

# 方式5: 虚拟环境（最佳实践）
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all]"
```

### 验证安装

```bash
# 验证 Python 支持
python3 -c "import tree_sitter_python; print('✅ Python OK')"

# 验证 PHP 支持
python3 -c "import tree_sitter_php; print('✅ PHP OK')"

# 验证 Java 支持
python3 -c "import tree_sitter_java; print('✅ Java OK')"

# 运行相关测试
pytest tests/test_parser.py -k python
pytest tests/test_parser.py -k php
pytest tests/test_parser.py -k java
```

---

## TDD 开发流程

### Phase 1: 基础符号提取 (P0 - Must Have)

**测试目标**: 15-20 tests
**覆盖范围**: 类、函数、方法、签名、基础 docstrings

```python
# tests/test_{language}_parser.py

class TestBasicSymbolExtraction:
    """AC1: 基础符号提取 (5 tests)"""

    def test_simple_function(self, tmp_path):
        """Test 1: 简单函数解析"""
        # Red: 编写失败测试
        # Green: 实现函数提取
        # Refactor: 优化代码结构

    def test_class_with_methods(self, tmp_path):
        """Test 2: 类和方法解析"""

    def test_method_signature(self, tmp_path):
        """Test 3: 方法签名提取"""

    # ... 更多测试
```

**成功标准**:
- ✅ 所有测试通过
- ✅ 代码覆盖率 ≥ 80%
- ✅ 符号提取准确率 ≥ 95%

### Phase 2: 高级特性 (P1 - Important)

**测试目标**: 20-30 tests
**覆盖范围**: 注解、泛型、继承、导入

```python
class TestAnnotations:
    """AC2: 注解/装饰器提取"""

class TestGenerics:
    """AC3: 泛型类型支持"""

class TestInheritance:
    """AC4: 继承关系提取"""

class TestImports:
    """AC5: 导入语句解析"""
```

### Phase 3: 调用关系 (P1 - Important, Epic 11)

**测试目标**: 30-35 tests
**覆盖范围**: 函数调用、方法调用、静态调用、构造函数

```python
class TestBasicCalls:
    """AC1: 基础函数调用 (5 tests)"""

class TestMethodCalls:
    """AC2: 方法调用 (6 tests)"""

class TestStaticCalls:
    """AC3: 静态调用 (5 tests)"""

class TestConstructorCalls:
    """AC4: 构造函数调用 (5 tests)"""

class TestAliasResolution:
    """AC5: 别名解析 (7 tests)"""
```

**成功标准**:
- ✅ 所有测试通过
- ✅ 调用提取准确率 ≥ 95%
- ✅ 别名解析准确率 ≥ 98%

### Phase 4: 边缘情况 (P2 - Nice to Have)

**测试目标**: 10-15 tests
**覆盖范围**: 错误恢复、超大文件、复杂嵌套

```python
class TestErrorRecovery:
    """AC6: 错误恢复"""

class TestEdgeCases:
    """AC7: 边缘情况处理"""
```

---

## 测试覆盖标准

### 按 Story 分解的测试覆盖

| Story | 测试数量 | 覆盖范围 | 优先级 |
|-------|---------|---------|--------|
| 基础符号提取 | 15-20 | 类、函数、方法、签名 | P0 |
| 注解/装饰器 | 10-15 | 语言特定注解 | P1 |
| 继承关系 | 10-15 | extends, implements, 接口 | P1 |
| 导入解析 | 8-12 | import, use, package | P1 |
| 调用关系 | 30-35 | 函数/方法/构造调用 | P1 |
| 边缘情况 | 10-15 | 错误恢复、性能 | P2 |
| **Total** | **~90-120** | **完整语言支持** | - |

### 代码覆盖率目标

```
Core modules (parser.py):           ≥ 90%
Language-specific functions:        ≥ 85%
Overall project:                    ≥ 80%
```

### 测试金字塔

```
    /\
   /  \  E2E Tests (5%)
  /    \  - 完整工作流
 /------\  Integration Tests (15%)
/        \ - JSON output, CLI
/----------\ Unit Tests (80%)
 - Symbol extraction
 - Call extraction
 - Type resolution
```

---

## CI/CD 集成

### GitHub Actions 配置示例

```yaml
# .github/workflows/test-multi-language.yml

name: Multi-Language Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
        language: ["python", "php", "java"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev,${{ matrix.language }}]"

      - name: Run ${{ matrix.language }} tests
        run: |
          pytest tests/test_${{ matrix.language }}_*.py -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 本地预提交检查

```bash
# .git/hooks/pre-commit (或使用 codeindex hooks)

#!/bin/bash
# 运行所有语言测试
pytest tests/test_python_*.py tests/test_java_*.py tests/test_php_*.py

# 检查代码风格
ruff check src/

# 验证类型
mypy src/

# 如果所有检查通过，允许提交
exit 0
```

---

## 已支持语言

### Python ✅ (v0.1.0+)

**Status**: 完全支持
**Parser**: tree-sitter-python ≥0.21
**Features**:
- ✅ 符号提取 (类、函数、方法)
- ✅ 装饰器/注解
- ✅ 继承关系
- ✅ 导入解析 (含别名)
- ✅ 调用关系 (Epic 11)
- ✅ Docstring 提取

**Tests**: 100+ tests passing

---

### PHP ✅ (v0.2.0+)

**Status**: 完全支持
**Parser**: tree-sitter-php ≥0.23
**Features**:
- ✅ 符号提取 (类、方法、函数、属性)
- ✅ 可见性修饰符 (public, private, protected)
- ✅ 继承关系 (extends, implements)
- ✅ Namespace 解析
- ✅ use 语句解析 (含别名)
- ✅ PHPDoc 提取
- ✅ 路由提取 (ThinkPHP)

**Tests**: 80+ tests passing

---

### Java ✅ (v0.7.0+)

**Status**: 完全支持
**Parser**: tree-sitter-java ≥0.23.0
**Features**:
- ✅ 符号提取 (类、方法、字段)
- ✅ 注解提取 (@RestController, @Autowired 等)
- ✅ 泛型类型支持
- ✅ 继承关系 (extends, implements)
- ✅ Package/import 解析
- ✅ 调用关系 (Epic 11)
  - ✅ 静态导入解析
  - ✅ FQN 检测
  - ✅ super() 调用
- ✅ Javadoc 提取

**Tests**: 120+ tests passing

---

### TypeScript 📅 (Planned: v0.13.0)

**Status**: 计划中
**Parser**: tree-sitter-typescript ≥0.21.0
**Estimated Tests**: 100-120
**Key Challenges**:
- TypeScript 特定类型系统
- Interface vs Class
- Decorator 语法
- Module 系统

---

### Go 📅 (Planned: v0.14.0)

**Status**: 计划中
**Parser**: tree-sitter-go ≥0.21.0
**Estimated Tests**: 90-110
**Key Challenges**:
- Package 系统
- Interface 实现（隐式）
- Goroutine/Channel 调用
- defer/panic/recover

---

### Rust 📅 (Planned: v0.15.0)

**Status**: 计划中
**Parser**: tree-sitter-rust ≥0.21.0
**Estimated Tests**: 110-130
**Key Challenges**:
- Trait 系统
- Lifetime 注解
- Macro 展开
- Ownership 语义

---

## 常见问题

### Q1: 为什么需要 --break-system-packages?

**A**: macOS Homebrew Python 3.14 使用 PEP 668 外部管理环境保护机制。

**解决方案**:
1. **推荐**: 使用虚拟环境
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,all]"
   ```

2. **临时**: 使用 --break-system-packages（仅开发环境）
   ```bash
   pip3 install tree-sitter-{lang} --break-system-packages
   ```

### Q2: 如何验证语言支持是否正确安装？

**A**: 使用 3 步验证法：

```bash
# Step 1: Python import 检查
python3 -c "import tree_sitter_{language}; print('✅ OK')"

# Step 2: 运行解析器测试
pytest tests/test_{language}_parser.py -v

# Step 3: 运行完整测试套件
pytest tests/ -k {language} -v
```

### Q3: 添加新语言需要多长时间？

**A**: 根据语言复杂度：

| 语言 | 基础支持 | 完整支持 | Total |
|------|---------|---------|-------|
| 简单 (Go, TypeScript) | 3-5 days | 5-7 days | ~10 days |
| 中等 (Java, PHP) | 5-7 days | 10-14 days | ~3 weeks |
| 复杂 (Rust, C++) | 7-10 days | 14-21 days | ~4 weeks |

### Q4: 如何确保跨语言一致性？

**A**: 遵循统一的数据模型和测试模式：

```python
# 所有语言使用相同的数据结构
@dataclass
class Symbol:
    name: str
    kind: str  # "class", "function", "method"
    signature: str
    # ...

@dataclass
class Call:
    caller: str
    callee: Optional[str]
    call_type: CallType  # 统一枚举
    # ...
```

### Q5: 如何处理语言特定特性？

**A**: 分层设计：

```
Layer 1: 通用特性 (所有语言)
  - 符号提取 (类、函数、方法)
  - 导入解析
  - 调用关系

Layer 2: 语言特定 (可选)
  - Java: 注解
  - Python: 装饰器
  - PHP: Namespace
  - TypeScript: Interface

Layer 3: 框架特定 (插件)
  - ThinkPHP 路由
  - Spring 路由
  - Laravel 路由
```

---

## 最佳实践总结

### ✅ DO

1. **先安装 tree-sitter-{language}**
   在编写测试之前，确保解析器已安装并可导入

2. **遵循 TDD 流程**
   Red → Green → Refactor，小步快跑

3. **使用虚拟环境**
   避免污染系统 Python 环境

4. **编写清晰的测试**
   每个测试只验证一个概念，命名清晰

5. **验证向后兼容性**
   新语言支持不应破坏现有功能

6. **更新文档**
   README, CHANGELOG, 配置示例

### ❌ DON'T

1. **不要跳过测试**
   即使功能"看起来能工作"

2. **不要过度优化**
   先让测试通过，再优化性能

3. **不要忽略边缘情况**
   错误恢复、超大文件、特殊字符

4. **不要硬编码语言逻辑**
   使用可扩展的设计模式

5. **不要忘记 CI/CD**
   确保测试在 CI 环境中也能通过

---

## 参考资料

- **Epic 11 设计**: `docs/planning/epic11-call-relationships.md`
- **TDD 工作流**: `CLAUDE.md` Part 2.5
- **依赖管理**: `pyproject.toml`
- **测试示例**:
  - Python: `tests/test_python_calls.py`
  - Java: `tests/test_java_calls.py`
  - PHP: `tests/test_php_*.py` (未来)

---

**Last Updated**: 2026-02-07
**Next Review**: When adding TypeScript support (v0.13.0)
