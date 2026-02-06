# Epic 7: Java 语言支持 - 执行路线图

**版本**: v0.8.0
**目标发布**: 2026-03-15 (5 周后)
**当前状态**: ⏳ Planning
**优先级**: 🔥 P0 (Critical)

---

## 🎯 为什么现在是 Java？

### 战略原因
1. ✅ **v0.6.0 基础已就绪**：AI Docstring Processor 可直接复用
2. ✅ **v0.7.0 工具完善**：JSON Output + PyPI 发布自动化
3. ✅ **市场需求最大**：Java = 企业市场 = 付费用户
4. ✅ **差异化优势**：现有工具对 Java + Spring 支持不佳

### 技术优势
- **JavaDoc 提取**：零工作量（复用 Epic 9 AI processor）
- **Spring 路由**：已有 ThinkPHP 模板（v0.5.0）
- **tree-sitter**：Java 解析器成熟稳定

---

## 📊 功能优先级矩阵

### P0 - 必须有（阻塞发布）

| Story | 功能 | 工作量 | 商业价值 | 技术难度 |
|-------|------|--------|----------|----------|
| 7.1 | Java Parser 集成 | 3 天 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 7.2 | Spring 路由提取 | 5 天 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 7.5 | JavaDoc 提取（AI） | 1 天 | ⭐⭐⭐⭐ | ⭐ (复用 Epic 9) |

**总工作量**: 9 天
**商业价值**: 非常高（解锁企业市场）

### P1 - 应该有（高价值）

| Story | 功能 | 工作量 | 商业价值 | 技术难度 |
|-------|------|--------|----------|----------|
| 7.3 | Maven/Gradle 检测 | 2 天 | ⭐⭐⭐⭐ | ⭐⭐ |
| 7.4 | Java 符号评分 | 2 天 | ⭐⭐⭐ | ⭐⭐ |

**总工作量**: 4 天
**商业价值**: 中高（提升用户体验）

### P2 - 可以有（增强）

| Story | 功能 | 工作量 | 商业价值 | 技术难度 |
|-------|------|--------|----------|----------|
| 7.6 | Java 文件分类 | 1 天 | ⭐⭐⭐ | ⭐ |
| 7.7 | 包结构分析 | 2 天 | ⭐⭐ | ⭐⭐ |
| 7.8 | Lombok 支持 | 2 天 | ⭐⭐⭐ | ⭐⭐⭐ |

**总工作量**: 5 天
**商业价值**: 中（Nice to have）

---

## 📅 5 周冲刺计划

### Week 1: 基础架构（Story 7.1）
**目标**: Java 代码解析能力

**任务**:
- [ ] 集成 tree-sitter-java 解析器
- [ ] 实现 Java 符号提取（类、方法、接口）
- [ ] 提取 import 语句
- [ ] 处理 Java 8-21 语法（lambdas, records, sealed classes）
- [ ] 编写 50+ 单元测试

**产出**:
```bash
✓ codeindex scan ./java-project
✓ 生成包含 Java 类/方法的 README_AI.md
✓ 支持 Java 8-21 所有语法
```

**风险**: tree-sitter-java 兼容性问题
**缓解**: 使用最新稳定版 (v0.23+)

---

### Week 2: Spring 路由提取（Story 7.2）
**目标**: Spring Boot API 路由自动识别

**任务**:
- [ ] 创建 Spring Framework 路由提取器
- [ ] 解析 @RestController, @RequestMapping
- [ ] 解析 @GetMapping, @PostMapping, @PutMapping, @DeleteMapping
- [ ] 提取路径变量和请求参数
- [ ] 生成路由表（类似 ThinkPHP）
- [ ] 编写 30+ 集成测试

**产出**:
```markdown
## Routes (Spring Framework)

| URL | Controller | Method | Location | Description |
|-----|------------|--------|----------|-------------|
| `GET /api/users` | UserController | getUsers | `UserController.java:25` | Get all users |
| `POST /api/users` | UserController | createUser | `UserController.java:45` | Create new user |
```

**风险**: Spring 注解复杂（多种路径拼接方式）
**缓解**: 参考 ThinkPHP 提取器模式，逐步支持

---

### Week 3: JavaDoc + Maven/Gradle（Story 7.5, 7.3）
**目标**: 文档提取 + 项目检测

**任务**:
- [ ] 复用 Epic 9 AI Docstring Processor
- [ ] 配置 JavaDoc 格式处理
- [ ] 测试混合模式（simple + AI）
- [ ] Maven 项目检测（pom.xml）
- [ ] Gradle 项目检测（build.gradle）
- [ ] 自动配置 include paths
- [ ] 编写 20+ 测试

**产出**:
```bash
✓ JavaDoc 自动提取到 README_AI.md
✓ 自动检测 src/main/java, src/test/java
✓ 排除 target/, build/ 目录
✓ 支持 multi-module 项目
```

**风险**: JavaDoc AI 处理成本
**缓解**: 默认使用 hybrid 模式（仅对复杂注释用 AI）

---

### Week 4: 符号评分 + 文档（Story 7.4）
**目标**: 智能优先级排序

**任务**:
- [ ] 实现 Java 符号评分算法
- [ ] 高分：public API, interfaces, @Service/@Controller
- [ ] 低分：private methods, getters/setters
- [ ] 集成到自适应符号提取（v0.2.0）
- [ ] 更新 README.md（Java 使用指南）
- [ ] 编写 JAVA_GUIDE.md
- [ ] 编写 15+ 测试

**产出**:
```yaml
# 符号评分示例
@RestController                # Score: 100 (高优先级)
  public interface UserService # Score: 90
  @GetMapping("/users")        # Score: 85
  public void getUser()        # Score: 70
  private void helper()        # Score: 30 (低优先级)
  public String getName()      # Score: 20 (getter)
```

---

### Week 5: 打磨 + 发布（Story 7.6 可选）
**目标**: 质量保证 + 发布准备

**任务**:
- [ ] 端到端测试（真实 Spring Boot 项目）
- [ ] 性能测试（100k+ LOC Java 项目）
- [ ] 文档完善（示例、FAQ）
- [ ] CHANGELOG 更新
- [ ] 可选：Java 文件分类（Test, Config, Entity）
- [ ] 准备 demo 项目
- [ ] 发布博客文章

**产出**:
```
✓ 测试覆盖率 > 90%
✓ 支持真实 Spring Boot 项目
✓ 完整用户文档
✓ Demo 项目 + 视频演示
✓ v0.8.0 发布到 PyPI
```

---

## 🧪 测试策略

### 单元测试（~120 tests）
```python
# Java Parser
test_parse_java_class()
test_parse_java_interface()
test_parse_java_enum()
test_parse_java_record()           # Java 14+
test_parse_java_sealed_class()     # Java 17+
test_extract_method_signatures()
test_extract_imports()

# Spring Route Extractor
test_extract_rest_controller_routes()
test_extract_request_mapping()
test_extract_get_mapping()
test_extract_post_mapping()
test_extract_path_variables()
test_extract_request_params()
test_route_description_from_javadoc()

# JavaDoc Extraction
test_extract_class_javadoc()
test_extract_method_javadoc()
test_parse_param_tags()
test_parse_return_tags()
test_ai_javadoc_processing()

# Maven/Gradle Detection
test_detect_maven_project()
test_detect_gradle_project()
test_auto_configure_paths()
test_exclude_generated_code()

# Symbol Scoring
test_score_public_class()
test_score_interface()
test_score_spring_annotations()
test_score_private_methods()
test_score_getters_setters()
```

### 集成测试（~30 tests）
```python
# Real Spring Boot projects
test_scan_spring_boot_starter()
test_scan_spring_boot_microservice()
test_scan_multi_module_maven_project()
test_scan_gradle_kotlin_dsl_project()

# Performance tests
test_scan_100k_loc_java_project()
test_parallel_java_parsing()
test_memory_usage_large_project()
```

### E2E 测试（~10 tests）
```bash
# Real-world scenarios
test_scan_spring_petclinic()      # Spring Boot demo app
test_scan_jhipster_project()      # Enterprise stack
test_scan_apache_commons()        # Large OSS project
test_generate_api_documentation() # Full workflow
```

---

## 🎓 学习资源需求

### tree-sitter-java
- **文档**: https://github.com/tree-sitter/tree-sitter-java
- **API**: Python binding (tree-sitter-java)
- **学习时间**: 0.5 天（已有 Python/PHP 经验）

### Spring Framework
- **路由注解**: @RequestMapping, @GetMapping, @PostMapping
- **组件注解**: @RestController, @Service, @Repository
- **参考**: https://docs.spring.io/spring-framework/reference/web/webmvc.html
- **学习时间**: 1 天（熟悉注解体系）

### JavaDoc
- **格式**: https://www.oracle.com/technical-resources/articles/java/javadoc-tool.html
- **标签**: @param, @return, @throws, @see
- **学习时间**: 0.5 天（复用 Epic 9 AI processor）

---

## 📦 依赖更新

### pyproject.toml
```toml
[project]
dependencies = [
    "tree-sitter-java>=0.23.0",  # ← 新增
    # ... 现有依赖
]

[project.optional-dependencies]
dev = [
    # ... 现有 dev 依赖
    "pytest-benchmark",  # 性能测试
]
```

---

## 🚨 风险与缓解

### 风险 1: tree-sitter-java 兼容性
**概率**: 中
**影响**: 高（阻塞整个 Epic）
**缓解**:
- Week 1 早期验证
- 准备 fallback plan（使用 javaparser 库）

### 风险 2: Spring 路由提取复杂度
**概率**: 高
**影响**: 中（可以简化实现）
**缓解**:
- MVP：只支持最常见的注解（@GetMapping, @PostMapping）
- 后续版本：增量添加更多注解

### 风险 3: JavaDoc AI 成本超预算
**概率**: 低
**影响**: 低（可用 hybrid 模式）
**缓解**:
- 默认 hybrid 模式（Epic 9 已优化）
- 只对复杂 JavaDoc 使用 AI

### 风险 4: 时间不足
**概率**: 中
**影响**: 高（延期发布）
**缓解**:
- P0 功能优先（Parser + Spring Routes）
- P1/P2 可推迟到 v0.8.1

---

## 📈 成功指标

### 技术指标
- [ ] 解析成功率 > 95%（测试 10+ 真实项目）
- [ ] Spring 路由提取准确率 = 100%
- [ ] 测试覆盖率 > 90%
- [ ] 扫描速度 > 2k LOC/s
- [ ] 支持 Java 8, 11, 17, 21

### 用户体验指标
- [ ] README_AI.md 对 Java 项目有用（用户反馈）
- [ ] 路由表完整准确（Spring Boot 项目）
- [ ] 文档清晰（用户无需看源码就能理解）

### 商业指标
- [ ] PyPI 下载量 > 500 (首月)
- [ ] GitHub stars 增长 > 100
- [ ] 获得首个 Java 企业用户反馈

---

## 📚 文档清单

### 用户文档
- [ ] `docs/guides/java-quick-start.md` - Java 快速开始
- [ ] `docs/guides/spring-boot-integration.md` - Spring Boot 集成
- [ ] `docs/guides/maven-gradle-setup.md` - Maven/Gradle 配置
- [ ] `README.md` - 更新 Java 示例

### 开发者文档
- [ ] `docs/development/adding-language-support.md` - 添加新语言指南
- [ ] `docs/development/parser-architecture.md` - 解析器架构
- [ ] `CLAUDE.md` - 更新 Java 工作流

### 发布文档
- [ ] `CHANGELOG.md` - v0.8.0 变更日志
- [ ] `RELEASE_NOTES_v0.8.0.md` - 发布说明
- [ ] Blog post - "codeindex now supports Java!"

---

## 🎯 MVP 范围（最小可行产品）

如果时间紧张，**最小可发布版本**包含：

### 必须有（3 周 MVP）
1. ✅ Java Parser (Story 7.1) - 3 天
2. ✅ Spring Routes (Story 7.2，简化版) - 4 天
3. ✅ JavaDoc (Story 7.5，hybrid mode) - 1 天
4. ✅ 基本测试 + 文档 - 3 天

**总工作量**: 11 天（2.5 周缓冲）

### 推迟到 v0.8.1
- Maven/Gradle 自动检测（Story 7.3）
- 符号评分（Story 7.4）
- 文件分类（Story 7.6）

---

## 🔄 迭代计划

### v0.8.0 (Epic 7 P0)
- Java Parser
- Spring Routes (基础)
- JavaDoc (AI)

### v0.8.1 (Epic 7 P1)
- Maven/Gradle 检测
- 符号评分
- Spring Routes 增强

### v0.8.2 (Epic 7 P2)
- 文件分类
- 包结构分析
- Lombok 支持

---

## 📞 Next Steps

### 立即开始（本周）
1. ✅ **决策确认**: Java 是 v0.8.0 重点（您已确认 ✓）
2. ⏳ **环境准备**: 安装 tree-sitter-java，准备测试项目
3. ⏳ **Story 7.1**: 开始 Java Parser 实现

### 本周末前
- [ ] 完成 Story 7.1 的 TDD 测试（RED phase）
- [ ] 基本的 Java 类解析工作原型

### 下周一
- [ ] Story 7.1 实现完成（GREEN phase）
- [ ] 开始 Story 7.2（Spring Routes）

---

## 🤝 需要帮助？

**我（Claude Code）可以帮你**:
1. ✅ 编写 TDD 测试（RED-GREEN-REFACTOR）
2. ✅ 实现 Java Parser 集成
3. ✅ 创建 Spring Route Extractor
4. ✅ 配置 JavaDoc AI 处理
5. ✅ 生成完整文档

**准备好开始了吗？**

输入 "开始 Story 7.1" 立即开始 Java Parser 实现！

---

**Epic Owner**: @dreamlinx
**Updated**: 2026-02-05
**Status**: ⏳ Ready to Start
**Estimated Completion**: 2026-03-15 (5 weeks)
