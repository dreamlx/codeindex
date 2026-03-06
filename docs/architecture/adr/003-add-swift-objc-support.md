# ADR 003: 添加 Swift/Objective-C 语言支持

## 状态
已采纳 (Accepted) - 2026-03-05

## 背景

codeindex 目前支持 Python、PHP、Java、TypeScript/JavaScript，但尚未支持 iOS 移动开发的核心语言：Swift 和 Objective-C。

**现实需求**:
- 接手了一个 185K LOC 的 iOS 项目（slock-app）
- 混合语言项目：81% Objective-C (112K LOC) + 19% Swift (36K LOC)
- 大量遗留代码需要快速理解和导航
- iOS 开发者市场巨大，但缺乏 AI 友好的代码索引工具

**市场空白**:
- Xcode/AppCode 提供基础导航，但不生成 AI 友好的文档
- SwiftLint/Sourcery 专注于风格检查和代码生成
- 缺少统一的 Swift/Objective-C 知识索引工具

## 决策

**在 codeindex v0.21.0 中添加 Swift 和 Objective-C 语言支持**，分 3 个阶段实施：

1. **Phase 1**: Swift 基础解析（MVP）
2. **Phase 2**: Swift 高级特性（Extension/Protocol/Generic）
3. **Phase 3**: Objective-C 支持（.h/.m 关联）

## 理由

### 1. 技术可行性

**Tree-sitter 支持成熟**:
- ✅ `tree-sitter-swift` - 官方支持，社区活跃
- ✅ `tree-sitter-objc` - 官方支持，稳定
- ✅ 与现有架构完美契合（只需添加新语言 parser）

**实现复杂度可控**:
| 特性 | Swift | Objective-C | 难度 |
|------|-------|-------------|------|
| 类/结构体/枚举 | ⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️ | 中-高 |
| 方法/函数 | ⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️ | 中-高 |
| 继承/协议 | ⭐️⭐️ | ⭐️⭐️⭐️ | 中 |
| Extension/Category | ⭐️⭐️⭐️ | ⭐️⭐️⭐️ | 中 |
| 属性/导入 | ⭐️⭐️ | ⭐️⭐️⭐️⭐️ | 中-高 |

### 2. ROI 分析

**开发成本**:
- 开发时间: 3-4 周
- 人力成本: $4,100-$5,900
- 维护成本: $500/年

**收益**:
- **立即收益**: slock-app 项目索引，节省 80+ 小时（按 70x 效能提升）
- **市场价值**: 开拓 iOS 开发者市场（数百万开发者）
- **战略价值**: 完善 codeindex 语言生态，增强企业采用率

**投资回报周期**: 2-3 个月

### 3. 差异化优势

| 工具 | Swift | Objective-C | AI 友好索引 | 技术债务检测 |
|------|-------|-------------|------------|-------------|
| Xcode | ✅ | ✅ | ❌ | ❌ |
| AppCode | ✅ | ✅ | ❌ | ⚠️ 基础 |
| SwiftLint | ✅ | ❌ | ❌ | ⚠️ 风格检查 |
| **codeindex** | ✅ 计划 | ✅ 计划 | ✅ **独有** | ✅ **完整** |

**核心差异**:
- ✅ README_AI.md 格式，Claude Code/LoomGraph 直接使用
- ✅ 跨语言统一索引（Swift/Objective-C/Python/Java/TypeScript）
- ✅ iOS 特定的技术债务检测（God Class、长方法、循环依赖）

### 4. 为什么现在做

1. **Dogfooding 场景**: slock-app 项目提供完美的验证环境
2. **立即受益**: 每天的开发工作都会用到
3. **快速验证**: 开发过程中就能测试效果
4. **市场窗口**: iOS 开发者工具市场缺乏 AI 友好索引工具

## 技术方案

### 语言解析器选型

| 语言 | 解析器 | 版本 | 状态 |
|------|--------|------|------|
| Swift | tree-sitter-swift | ≥0.6.0 | 官方维护 |
| Objective-C | tree-sitter-objc | ≥0.5.0 | 官方维护 |

### 架构设计

```
src/codeindex/
├── parsers/
│   ├── swift.py           # Swift 解析器（新增）
│   └── objc.py            # Objective-C 解析器（新增）
├── queries/
│   ├── swift.scm          # Swift tree-sitter query（新增）
│   └── objc.scm           # Objective-C tree-sitter query（新增）
├── extractors/
│   └── swift_ui.py        # SwiftUI 特定提取器（可选）
└── parser.py              # 统一解析入口（扩展）
```

### Swift 特殊处理

1. **Extension**: 跨文件类扩展，需要关联到主类
2. **Protocol**: 协议声明和实现需要分别记录
3. **Generic**: 泛型类型参数需要保留
4. **Property Wrapper**: `@State`, `@Published` 等需要识别
5. **Access Control**: `public`, `private`, `internal` 可见性

### Objective-C 特殊处理

1. **头文件关联**: `.h` 和 `.m` 需要匹配（基于文件名）
2. **Category**: 类别扩展需要关联到原类
3. **Protocol**: `@protocol` 声明和实现需要分别记录
4. **Property**: `@property` 属性需要提取 attributes（weak/strong/readonly）
5. **Macro**: 常见宏定义（`#define`, `#import`）需要记录

### 桥接处理

**Bridging Header** (`ProjectName-Bridging-Header.h`):
- 识别 Swift 调用 Objective-C 的桥接文件
- 提取暴露给 Swift 的 Objective-C 类和方法

### 技术债务检测

**iOS 特定反模式**:
1. **Massive View Controller**: 视图控制器 >500 行或 >20 个方法
2. **Retain Cycle**: 潜在的循环引用（delegate 未使用 weak）
3. **Forced Unwrap**: 过多的 `!` 强制解包
4. **Long Method**: 方法 >80 行（Swift）或 >100 行（Objective-C）
5. **God Class**: 类有 >20 个方法（MEDIUM）或 >50 个方法（CRITICAL）

**文件大小阈值** (iOS 属于 "compact" 语言):
- MEDIUM: 800 lines
- LARGE: 1500 lines
- CRITICAL: 2500 lines

## 实施计划

### Phase 1: Swift MVP (Week 1)

**目标**: 快速验证，支持基础 Swift 解析

**Scope**:
- ✅ 类（class）、结构体（struct）、枚举（enum）定义
- ✅ 方法（method）、函数（function）、属性（property）
- ✅ 继承关系（inheritance）、协议（protocol）
- ✅ 导入依赖（import）
- ✅ 模块文档字符串（docstring）
- ✅ README_AI.md 生成

**产出**:
- `src/codeindex/parsers/swift.py`
- `src/codeindex/queries/swift.scm`
- `tests/test_parser_swift.py` (>20 test cases)

**验证**: 能够解析 slock-app 的 280 个 Swift 文件

### Phase 2: Swift 高级特性 (Week 2)

**Scope**:
- ✅ Extension 支持（跨文件类扩展）
- ✅ Protocol 高级特性（关联类型、默认实现）
- ✅ Generic 泛型类型解析
- ✅ Property Wrapper 识别
- ✅ 技术债务检测（God Class、Long Method）

**产出**:
- `src/codeindex/tech_debt.py` 扩展（iOS 反模式）
- `tests/test_tech_debt_swift.py`

### Phase 3: Objective-C 支持 (Week 3-4)

**Scope**:
- ✅ .h/.m 文件关联
- ✅ 接口（@interface）和实现（@implementation）
- ✅ Category 支持
- ✅ Protocol 声明
- ✅ 属性（@property）和宏定义（#define）
- ✅ 桥接头文件处理（Bridging Header）

**产出**:
- `src/codeindex/parsers/objc.py`
- `src/codeindex/queries/objc.scm`
- `tests/test_parser_objc.py`

**验证**: 能够解析 slock-app 的 818 个 Objective-C 文件

### Phase 4: 集成与优化 (Optional)

**Scope**:
- ✅ UIKit/SwiftUI 框架识别
- ✅ Storyboard 关联（如果需要）
- ✅ CocoaPods/SPM 依赖分析
- ✅ 性能优化（大型 iOS 项目）

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Tree-sitter 解析不完整 | 中 | 中 | 增量实现，先支持常见模式，逐步完善 |
| Objective-C 宏过于复杂 | 高 | 低 | 跳过复杂宏，只处理常见宏定义 |
| .h/.m 关联失败 | 中 | 中 | 启发式匹配（文件名），容错处理 |
| Extension 跨文件关联困难 | 中 | 低 | 同文件优先，跨文件作为可选功能 |
| 维护成本增加 | 低 | 中 | 良好的测试覆盖（≥90%），文档完善 |

**总体风险**: ⚠️ **中等**（可控）

## 后果

### 积极影响

1. **立即收益**:
   - slock-app 项目快速索引和导航
   - 混合语言项目统一管理（Swift ↔ Objective-C）
   - 技术债务可视化，指导重构

2. **战略价值**:
   - 完善 codeindex 语言生态（覆盖主流移动开发）
   - 开拓 iOS 开发者市场（数百万潜在用户）
   - 增强企业采用率（iOS 支持是企业必需品）

3. **生态协同**:
   - LoomGraph 可索引 iOS 项目知识图谱
   - Claude Code 可理解 iOS 项目架构
   - 统一的技术债务检测标准

### 消极影响

1. **开发成本**: 3-4 周开发时间，$4K-$6K 投入
2. **维护负担**: 新增 2 种语言，需要持续维护
3. **测试复杂度**: iOS 特性多样，测试用例增加
4. **文档工作**: 需要编写 Swift/Objective-C 使用文档

### 长期影响

1. **语言生态**: 为未来添加 Kotlin/Dart 打下基础
2. **社区贡献**: iOS 开发者可能贡献更多 iOS 特定功能
3. **商业价值**: iOS 支持可能成为付费版本的差异化功能

## 成功标准

### MVP 成功标准 (Phase 1)

- ✅ 能够解析 slock-app 的 280 个 Swift 文件
- ✅ 提取 ≥90% 的类、方法、属性
- ✅ 生成可读的 README_AI.md
- ✅ 测试覆盖率 ≥85%
- ✅ 解析速度 <5 秒/100 文件

### 完整成功标准 (Phase 3)

- ✅ 支持 Swift + Objective-C 混合项目
- ✅ .h/.m 文件正确关联 ≥95%
- ✅ Extension/Category 正确关联 ≥90%
- ✅ 技术债务检测准确率 ≥90%
- ✅ 完整的 slock-app 索引生成 <30 秒
- ✅ 测试覆盖率 ≥90%

## 参考资料

- [tree-sitter-swift](https://github.com/alex-pinkus/tree-sitter-swift)
- [tree-sitter-objc](https://github.com/tree-sitter/tree-sitter-objc)
- [Swift Language Guide](https://docs.swift.org/swift-book/)
- [Objective-C Programming Guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/Introduction/Introduction.html)
- [codeindex 设计哲学](../design-philosophy.md)

## 关联文档

- GitHub Issue: #21 "Add Swift/Objective-C Language Support"
- 可行性分析: `reports/swift-objc-support-analysis.md`
- 实施计划: Epic 文档（待创建）

---

**决策日期**: 2026-03-05
**决策者**: dreamlinx
**审核者**: AI Assistant (Claude Sonnet 4.5)
**下次审核**: 2026-04-05 (Phase 1 完成后)
