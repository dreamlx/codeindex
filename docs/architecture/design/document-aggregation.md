# 文档聚合方案设计

## 🎯核心思路

基于"LLM仍需读源码"的结论，文档聚合应该**聚焦于导航和概览**，而不是替代源码阅读。

## 📊 聚合策略

### 策略 1: 简单目录列表
```
## Subdirectories
- Application/Admin - Admin management module
- Application/BMall - Shopping mall features
- Application/Cashier - Payment processing
```

### 策略 2: 摘要式聚合（推荐）
```
## Subdirectories

### Application/Admin
- **Purpose**: Admin management interface
- **Key Files**: 33 controllers, 8 business classes
- **README_AI.md**: ./Application/Admin/README_AI.md

### Application/BMall
- **Purpose**: E-commerce platform
- **Key Files**: Store management, order processing
- **README_AI.md**: ./Application/BMall/README_AI.md
```

### 策略 3: 深度聚合（过于复杂）
❌ 不推荐 - 会增加解析复杂度，违背"不精确分析import"的初衷

## 🎨 具体实现方案

### 方案A: 智能摘要提取

```python
def extract_directory_summary(child_readme_path: Path) -> Dict[str, str]:
    """
    从子目录的README_AI.md中提取简短摘要。

    查找模式：
    1. ## Purpose 或 ## 目的 之后的第一段
    2. 如果没有，取第一个实际内容行
    3. 如果都没有，使用默认描述
    """
```

### 方案B: 基于文件统计的智能描述

```python
def generate_directory_summary(dir_path: Path, scan_result) -> str:
    """
    基于目录内容生成描述。
    """
    file_patterns = {
        '*Controller.class.php': 'Control interface',
        '*Model.class.php': 'Data model',
        '*Service.class.php': 'Business logic',
        'config*': 'Configuration',
        'test*': 'Tests'
    }

    # 统计文件类型并生成描述
    description_parts = []

    if controller_count > 10:
        description_parts.append("comprehensive controllers")
    if has_models:
        description_parts.append("data models")

    return " ".join(description_parts) or "Module directory"
```

### 方案C: 混合方案（最终推荐）

1. **第一层聚合**：文件统计 + 简单描述
2. **第二层引用**：提供README_AI.md链接
3. **第三层导航**：层级结构展示

## 📋 文档结构设计

### 最终生成的父目录README_AI.md结构：

```markdown
# Parent Directory

## Overview
- **Direct files**: 15 files
- **Subdirectories**: 8 modules
- **Total coverage**: 85% indexed

## Directory Structure
```
Parent/
├── Core/              (12 files) - Core functionality
├── Controllers/        (8 files)  - API endpoints
├── Services/           (15 files) - Business logic
└── Utils/              (6 files)  - Utilities
```

## Subdirectories

### Core/
- **Purpose**: Core system functionality and base classes
- **Files**: Base*, Config*, Exception*
- **README**: 📄 ./Core/README_AI.md
- **Status**: ✅ Indexed

### Controllers/
- **Purpose**: REST API and web controllers
- **Files**: User*, Auth*, Profile*
- **README**: 📄 ./Controllers/README_AI.md
- **Status**: ✅ Indexed

## Local Files
(this directory's own files)

...

## Quick Links
- 📊 [Project Overview](./PROJECT_INDEX.md)
- 🔍 [Search this directory](./search.html)
- 📧 [API Documentation](./api.md)
```

## 🚀 实现优先级

### Phase 1: 基础聚合
1. ✅ 收集子目录列表
2. ✅ 统计文件数量
3. ✅ 提供README链接

### Phase 2: 智能描述
1. 🎯 从子README提取Purpose
2. 🎯 基于文件名生成智能描述
3. 🎯 状态标识（✅ 已索引 / ⚠️ 部分 / ❌ 未索引）

### Phase 3: 可视化结构
1. 📐 ASCII树形图
2. 📊 覆盖率统计
3. 🔗 快速导航链接

## 🤔 实现细节考虑

### 处理特殊情况
```python
# 1. 空目录处理
if not children:
    return []  # 不显示子目录部分

# 2. 子目录README不存在
if not child_readme.exists():
    description = generate_description_from_files(child_path)

# 3. 避免循环引用
if child_path in processed_paths:
    continue
```

### 性能优化
- 使用缓存避免重复读取子README
- 批量生成减少IO操作
- 增量更新机制

## 💡 界面交互考虑

CLI输出示例：
```
Processing Application (level 2) with 8 children...
  ├── Admin/    ✓ 46 files → README_AI.md
  ├── BMall/    ✓ 32 files → README_AI.md
  ├── ...       ⚠️ 15 files →生成中...
```

用户看到：
- 清晰的层级进度
- 每个子目录的文件统计
- 成功/失败状态
- 生成的文档位置

这个方案平衡了信息量和实现复杂度，你觉得如何？