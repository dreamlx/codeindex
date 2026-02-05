# Epic 7: Java 支持 - 测试策略与基准项目

**版本**: v1.0
**创建日期**: 2026-02-05
**目标**: 确保Java支持的质量和实用性

---

## 🎯 测试策略概览

### 三层测试金字塔

```
        ┌─────────────┐
        │   E2E Tests │  10 tests (真实项目)
        │   大型OSS项目 │
        └─────────────┘
             ▲
             │
      ┌─────────────────┐
      │ Integration Tests│  30 tests (中型项目片段)
      │  Spring Boot项目  │
      └─────────────────┘
             ▲
             │
   ┌───────────────────────┐
   │    Unit Tests         │  120 tests (合成代码)
   │  Synthetic Fixtures   │
   └───────────────────────┘
```

---

## 📊 测试数据分层策略

### Layer 1: Unit Tests (P0 优先级)

**目的**: 快速验证基础功能
**数据源**: **手写的synthetic代码片段**
**优势**:
- ✅ 精确控制测试场景
- ✅ 快速执行（<1秒）
- ✅ 易于调试和维护
- ✅ 覆盖边界情况

**测试文件结构**:
```
tests/
├── fixtures/
│   └── java/                    # ← 手写Java测试代码
│       ├── simple_class.java    # 基础类
│       ├── interface.java       # 接口
│       ├── enum.java           # 枚举
│       ├── record.java         # Java 14+ Record
│       ├── sealed_class.java   # Java 17+ Sealed
│       ├── spring_controller.java  # Spring注解
│       ├── javadoc_examples.java   # JavaDoc测试
│       └── lombok_example.java     # Lombok注解
└── test_java_parser.py         # Unit tests
```

**示例测试数据** (`tests/fixtures/java/simple_class.java`):
```java
package com.example.demo;

import java.util.List;

/**
 * User entity class.
 *
 * @author codeindex
 * @since 1.0.0
 */
public class User {
    private Long id;
    private String name;

    /**
     * Get user by ID.
     *
     * @param id User ID
     * @return User object
     * @throws UserNotFoundException if user not found
     */
    public User findById(Long id) throws UserNotFoundException {
        // implementation
    }
}
```

### Layer 2: Integration Tests (P1 优先级)

**目的**: 验证真实场景和框架集成
**数据源**: **小型真实Spring Boot项目**
**优势**:
- ✅ 验证框架路由提取
- ✅ 测试多文件依赖关系
- ✅ 发现实际使用中的问题

**推荐项目**:

#### Option 1: Spring Boot Initializer Project (最简单)
```bash
# 使用 Spring Initializer 创建最小项目
https://start.spring.io/

# 配置:
Project: Maven
Language: Java
Spring Boot: 3.2.x
Dependencies: Web, JPA, H2

# 下载并作为测试基准
```

#### Option 2: 手写Minimal Spring Boot Project (推荐)
```
tests/fixtures/spring-boot-minimal/
├── pom.xml                      # Maven配置
├── src/main/java/
│   └── com/example/demo/
│       ├── DemoApplication.java
│       ├── controller/
│       │   ├── UserController.java     # REST API
│       │   └── ProductController.java
│       ├── service/
│       │   └── UserService.java
│       └── model/
│           └── User.java
└── src/test/java/               # Java测试代码
```

**测试覆盖**:
- ✅ Spring Boot应用启动类
- ✅ @RestController路由
- ✅ @Service组件
- ✅ JPA实体
- ✅ Maven依赖检测

### Layer 3: E2E Tests (P2 优先级)

**目的**: 性能测试和完整性验证
**数据源**: **知名开源项目**
**优势**:
- ✅ 真实世界复杂度
- ✅ 性能基准测试
- ✅ 边界情况发现

**推荐开源项目**:

#### P0级别（必须测试）

**1. Spring PetClinic** ⭐⭐⭐⭐⭐
- **URL**: https://github.com/spring-projects/spring-petclinic
- **规模**: ~5k LOC
- **特点**: Spring Boot官方demo，最佳实践
- **测试价值**:
  - ✅ 标准Spring Boot结构
  - ✅ REST API示例
  - ✅ JPA使用
  - ✅ Maven项目
- **使用方式**:
  ```bash
  cd tests/fixtures/
  git clone https://github.com/spring-projects/spring-petclinic.git
  # 或者作为git submodule
  git submodule add https://github.com/spring-projects/spring-petclinic.git tests/fixtures/spring-petclinic
  ```

#### P1级别（应该测试）

**2. JHipster Sample Application** ⭐⭐⭐⭐
- **URL**: https://github.com/jhipster/jhipster-sample-app
- **规模**: ~15k LOC
- **特点**: 企业级全栈应用生成器
- **测试价值**:
  - ✅ 复杂项目结构
  - ✅ 多module支持
  - ✅ 生成代码模式
  - ✅ Gradle + Maven双支持

**3. Spring Boot Admin** ⭐⭐⭐⭐
- **URL**: https://github.com/codecentric/spring-boot-admin
- **规模**: ~20k LOC
- **特点**: Spring Boot监控管理平台
- **测试价值**:
  - ✅ 多模块项目
  - ✅ WebFlux使用
  - ✅ 复杂注解

#### P2级别（可选测试）

**4. Apache Commons Lang** ⭐⭐⭐
- **URL**: https://github.com/apache/commons-lang
- **规模**: ~100k LOC
- **特点**: 纯Java工具库，无Spring依赖
- **测试价值**:
  - ✅ 大规模性能测试
  - ✅ 纯Java解析（无框架）
  - ✅ 完善的JavaDoc

---

## 🧪 TDD执行流程

### Week 1: Java Parser (Story 7.1)

**阶段1: Unit Tests (Day 1-2)**
```python
# tests/test_java_parser.py
def test_parse_simple_class():
    """测试最简单的Java类解析"""
    code = """
    public class HelloWorld {
        public static void main(String[] args) {
            System.out.println("Hello");
        }
    }
    """
    result = parse_java(code)
    assert result.symbols[0].name == "HelloWorld"
    assert result.symbols[0].kind == "class"

def test_parse_java_interface():
    """测试接口解析"""
    # 使用 tests/fixtures/java/interface.java

def test_parse_java_enum():
    """测试枚举解析"""

def test_parse_java_record():
    """测试Java 14+ Record"""

def test_extract_imports():
    """测试import语句提取"""
```

**阶段2: Integration Tests (Day 3)**
```python
# tests/test_java_integration.py
def test_scan_minimal_spring_boot():
    """测试扫描最小Spring Boot项目"""
    result = scan_directory("tests/fixtures/spring-boot-minimal")
    assert len(result.files) > 0
    assert "DemoApplication" in result.symbols
```

**阶段3: E2E Tests (Day 4-5)**
```python
# tests/test_java_e2e.py
def test_scan_spring_petclinic():
    """测试扫描Spring PetClinic"""
    result = scan_directory("tests/fixtures/spring-petclinic")
    assert result.success
    assert len(result.symbols) > 50
    # 性能基准：应该在10秒内完成
    assert result.duration < 10.0
```

### Week 2: Spring Routes (Story 7.2)

**阶段1: Unit Tests**
```python
def test_extract_rest_controller():
    """测试@RestController识别"""
    code = """
    @RestController
    @RequestMapping("/api/users")
    public class UserController {
        @GetMapping
        public List<User> getUsers() { }
    }
    """
    routes = extract_spring_routes(code)
    assert routes[0].method == "GET"
    assert routes[0].path == "/api/users"
```

**阶段2-3**: 同上

---

## 📦 测试数据准备计划

### 立即准备（本周）

**1. 创建synthetic fixtures** (2小时)
```bash
mkdir -p tests/fixtures/java
# 手写 10-15 个Java测试文件
# - simple_class.java
# - interface.java
# - enum.java
# - record.java (Java 14+)
# - sealed_class.java (Java 17+)
# - spring_controller.java
# - javadoc_examples.java
# - lombok_example.java
```

**2. 克隆Spring PetClinic** (5分钟)
```bash
cd tests/fixtures
git clone https://github.com/spring-projects/spring-petclinic.git
# 或者作为submodule:
git submodule add https://github.com/spring-projects/spring-petclinic.git tests/fixtures/spring-petclinic
```

**3. 创建minimal Spring Boot project** (1小时)
- Option A: 使用Spring Initializer下载
- Option B: 手写最小项目（5个文件）

### Week 2准备

**4. 添加中型项目** (可选)
- JHipster sample或Spring Boot Admin
- 只有在需要更复杂测试时才添加

---

## 🎓 测试数据选择建议

### 推荐方案（平衡效率和覆盖）

**P0 - 必须有**:
1. ✅ Synthetic fixtures (手写) - Unit tests
2. ✅ Spring PetClinic (git submodule) - E2E tests
3. ✅ Minimal Spring Boot (手写或Spring Initializer) - Integration tests

**P1 - 应该有**:
4. ⏳ JHipster sample或等效项目 - 复杂场景测试

**P2 - 可以有**:
5. ⏳ Apache Commons或类似大型项目 - 性能测试

### 为什么这样选择？

| 项目类型 | 代码量 | 准备时间 | 测试价值 | 优先级 |
|---------|--------|---------|---------|--------|
| Synthetic fixtures | 500 LOC | 2小时 | ⭐⭐⭐⭐⭐ | P0 |
| Spring PetClinic | 5k LOC | 5分钟 | ⭐⭐⭐⭐⭐ | P0 |
| Minimal Spring Boot | 1k LOC | 1小时 | ⭐⭐⭐⭐ | P0 |
| JHipster sample | 15k LOC | 5分钟 | ⭐⭐⭐⭐ | P1 |
| Apache Commons | 100k LOC | 5分钟 | ⭐⭐⭐ | P2 |

---

## 🚀 立即行动项

### 本周末前（准备测试数据）

**Task 1: 创建synthetic fixtures** (优先级最高)
```bash
# 1. 创建目录
mkdir -p tests/fixtures/java

# 2. 手写测试文件（参考上面示例）
# 花2小时精心设计10-15个测试文件
# 每个文件测试一个特定功能
```

**Task 2: 添加Spring PetClinic**
```bash
# 方案A: Git submodule (推荐)
git submodule add https://github.com/spring-projects/spring-petclinic.git tests/fixtures/spring-petclinic
git submodule update --init --recursive

# 方案B: 直接克隆
cd tests/fixtures
git clone https://github.com/spring-projects/spring-petclinic.git
echo "tests/fixtures/spring-petclinic/" >> .gitignore
```

**Task 3: 创建minimal Spring Boot project**
```bash
# 方案A: Spring Initializer
# 访问 https://start.spring.io/
# 配置: Maven, Java 17, Spring Boot 3.2.x, Web依赖
# 下载并解压到 tests/fixtures/spring-boot-minimal/

# 方案B: 手写（更可控）
# 创建5个文件的最小项目
mkdir -p tests/fixtures/spring-boot-minimal/src/main/java/com/example/demo
# ... 手写代码
```

### Week 1 Day 1（开始TDD）

**Task 4: 编写第一个测试**
```python
# tests/test_java_parser.py
def test_parse_simple_java_class():
    """RED phase: 这个测试现在会失败"""
    code = Path("tests/fixtures/java/simple_class.java").read_text()
    result = parse_java(code)
    assert result.symbols[0].name == "User"
```

---

## 💡 关键决策

### ❓ 是否需要所有这些测试项目？

**答案**: **不需要全部，分阶段添加**

**MVP阶段（Week 1-2）**:
- ✅ Synthetic fixtures - 必须
- ✅ Spring PetClinic - 必须
- ⏳ Minimal Spring Boot - 应该有
- ❌ 其他项目 - 暂不需要

**完整阶段（Week 3-5）**:
- ✅ 所有P0项目
- ✅ 添加1个P1项目（JHipster或等效）
- ⏳ P2项目根据需要决定

### ❓ Git submodule vs 直接克隆？

**推荐**: **Git submodule**

**优势**:
- ✅ 版本锁定（确保测试稳定）
- ✅ 自动更新（可选）
- ✅ 仓库大小可控

**劣势**:
- ⚠️ 新克隆需要 `--recurse-submodules`
- ⚠️ 学习曲线

**替代方案**: 如果嫌麻烦，可以直接克隆并添加到`.gitignore`

### ❓ 需要手写多少synthetic fixtures？

**建议**: **10-15个文件，覆盖关键场景**

**必须覆盖**:
1. ✅ Simple class (fields + methods)
2. ✅ Interface
3. ✅ Enum
4. ✅ Abstract class
5. ✅ Generic class
6. ✅ Nested class
7. ✅ Record (Java 14+)
8. ✅ Sealed class (Java 17+)
9. ✅ Spring @RestController
10. ✅ Spring @Service
11. ✅ JavaDoc with tags
12. ✅ Lombok annotations
13. ✅ Complex imports
14. ✅ Package declaration
15. ✅ Multi-level inheritance

**时间投入**: 2-3小时（一次性）
**回报**: 整个Epic期间都会使用，价值极高

---

## 🎯 总结

### ✅ 测试策略已明确

**三层金字塔**:
1. Unit Tests (120个) - Synthetic fixtures
2. Integration Tests (30个) - Minimal Spring Boot
3. E2E Tests (10个) - Spring PetClinic

### ✅ 测试数据已规划

**P0必须**:
- Synthetic fixtures (手写2-3小时)
- Spring PetClinic (git submodule 5分钟)
- Minimal Spring Boot (1小时)

### ✅ TDD流程已定义

**每个Story**:
1. Red: 写测试（synthetic fixtures）
2. Green: 最小实现
3. Refactor: 优化
4. Integration: 测试真实项目
5. E2E: 性能和完整性验证

---

## 🤔 需要讨论的问题

### Q1: 是否现在就准备所有测试数据？

**我的建议**:
- ✅ **立即准备**: Synthetic fixtures + Spring PetClinic
- ⏳ **Week 2准备**: Minimal Spring Boot
- ⏳ **按需准备**: 其他项目

### Q2: 是否需要我帮你创建synthetic fixtures？

**我可以**:
- ✅ 生成10-15个标准Java测试文件
- ✅ 覆盖Java 8-21所有关键特性
- ✅ 包含Spring注解示例
- ✅ 包含JavaDoc示例

**预计时间**: 10分钟（AI生成）vs 2小时（手写）

### Q3: Git submodule还是直接克隆？

**我的建议**:
- ✅ **推荐**: Git submodule（专业项目做法）
- ⏳ **替代**: 直接克隆+.gitignore（更简单）

**你的选择**？

---

**准备好讨论这些问题了吗？** 🚀

如果你同意这个测试策略，我可以：
1. 立即生成synthetic fixtures（10-15个Java文件）
2. 设置Spring PetClinic submodule
3. 创建minimal Spring Boot project
4. 开始编写第一个TDD测试

**下一步**: 输入你的决定或问题！
