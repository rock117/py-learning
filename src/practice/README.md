# 实战经验

本部分**不再教你新特性**，而是帮你积累实战经验：哪些写法更快、哪些写法更 Pythonic、哪些坑必须避开。

前面两部分（异步编程、高级特性）解决的是"知不知道"的问题，本部分解决的是"用得好不好"的问题。

## 章节目录

| 章节 | 主题 | 对应 Java 概念 |
|------|------|----------------|
| [01 - 性能优化深入](01-performance.md) | cProfile / 数据结构选择 / 缓存 / 生成器 | JMH / JProfiler / VisualVM |
| [02 - 最佳实践](02-best-practices.md) | Pythonic 写法 / PEP 8 / 测试 / 日志 / 配置 | JUnit / SLF4J / Spring 配置 |
| [03 - 常见陷阱与避坑指南](03-pitfalls.md) | 可变默认参数 / 闭包绑定 / `==` vs `is` / 线程安全 | Java 中的类似陷阱 |

## 这部分的定位

如果你已经学完了前两部分，掌握了 Python 的语法和高级特性，那么本部分的目标是：

- **性能优化**：知道什么时候该优化、用什么工具分析、怎么验证效果。不是盲目猜，而是用数据说话。
- **最佳实践**：养成 Python 社区公认的好习惯，写出可维护、可测试、可读性强的代码。
- **常见陷阱**：提前知道哪些写法会出 bug，避免在生产环境踩坑。

> 💡 这三块不是"高级技巧"，而是"工程素养"。Java 开发者转 Python 最容易犯的错，就是用 Java 思维写 Python——语法能跑，但不够 Pythonic，甚至埋下隐患。

## 学习建议

推荐按以下顺序阅读：

### 1. 先读陷阱（03）——避免踩坑是最高优先级

有些陷阱（如可变默认参数）一旦上线就是定时炸弹。先建立"什么不能做"的认知，比学"什么能做"更紧迫。

陷阱章节的每个陷阱都标注了 Java 是否有类似问题，帮你快速判断哪些是 Python 独有的、哪些是通用的。重点关注那些 **Java 没有** 或 **语义相反** 的陷阱，这些最容易踩坑。

### 2. 再读最佳实践（02）——养成好习惯

知道陷阱之后，需要知道正确的写法是什么。这部分帮你建立"应该怎么做"的肌肉记忆。

从 Pythonic 语法（`enumerate` / `zip` / walrus）到工程实践（测试 / 日志 / 配置 / 文档），覆盖日常开发的方方面面。每节都有 Java 对比，帮你利用已有经验快速上手。

### 3. 最后读性能优化（01）——按需使用

性能优化是最后一步，不要过早优化。但当你遇到性能问题时，需要知道用什么工具、怎么分析、怎么验证。

这部分的核心原则是"**不要猜，要测**"——先用 `cProfile` 找瓶颈，再用 `timeit` 验证优化效果，最后用 `cProfile` 确认瓶颈已消除。

> ⚠️ **不要过早优化**。这是 Java 和 Python 通用的原则。先用正确的写法把功能做对，
> 再用分析工具找到真正的瓶颈，最后针对性优化。盲目优化往往引入 bug。

## 与 Java 经验的迁移

作为有丰富 Java 经验的开发者，你已经具备很多可迁移的工程能力：

| Java 经验 | Python 对应 | 迁移难度 | 说明 |
|-----------|-------------|----------|------|
| JUnit 测试 | pytest | 低 | 概念相通，`assert` 更简洁 |
| SLF4J 日志 | logging | 低 | 配置方式不同，理念相同 |
| Spring 配置管理 | pydantic-settings / .env | 中 | 理念相同，工具不同 |
| JMH 基准测试 | timeit / cProfile | 中 | 思路相同，API 不同 |
| JProfiler 性能分析 | cProfile / py-spy | 中 | 分析方法一致 |
| Effective Java 条款 | PEP 8 / Pythonic | 高 | 需要重新建立直觉 |
| try-with-resources | `with` 语句 | 低 | 概念直接对应 |
| `equals` / `hashCode` | `__eq__` / `__hash__` | 低 | 契约相同 |

### 迁移难度"高"的部分

以下概念在 Java 中没有直接对应，需要特别注意：

- **Pythonic 写法**：`enumerate` / `zip` / unpacking / walrus operator，Java 没有等价语法
- **EAFP 错误处理**：Python 推崇"先做再说"，Java 习惯"先检查再做"
- **可变默认参数陷阱**：Java 完全没有这个问题，容易忽视
- **`==` vs `is` 语义反转**：与 Java 正好相反，是最容易搞混的点
- **GIL 对并发的影响**：Java 没有 GIL，并发模型完全不同

## 各章节代码索引

| 章节 | 代码文件 | 主要内容 |
|------|----------|----------|
| 性能优化 | [`01_performance.py`](../code/practice/01_performance.py) | cProfile / timeit / tracemalloc / line_profiler / py-spy / 数据结构对比 / 字符串优化 / 循环优化 / lru_cache / 生成器 / 局部变量缓存 / 优化实战 |
| 最佳实践 | [`02_best_practices.py`](../code/practice/02_best_practices.py) | Pythonic 语法 / walrus / ruff / 类型注解 / EAFP / 异常链 / src layout / pytest / logging / pydantic-settings / docstring |
| 常见陷阱 | [`03_pitfalls.py`](../code/practice/03_pitfalls.py) | 可变默认参数 / 闭包绑定 / `==` vs `is` / 浅拷贝 / 类属性 / async 阻塞 / except 过宽 / finally return / 浮点数 / 链式赋值 / with 多资源 / 线程安全 / 全局变量 / `__eq__`/`__hash__` / 遍历修改 / 整数缓存 |

> 📁 所有可运行的代码示例位于 [`src/code/practice/`](../code/practice/) 目录，
> 每个章节文档中会链接到对应的源文件。

## 前置知识

本部分假设你已经掌握以下内容（来自前两部分）：

- **异步编程**：`async`/`await` 基础、事件循环、异步上下文管理器（陷阱章节会用到）
- **高级特性**：类型注解、装饰器、生成器、上下文管理器、并发模型（最佳实践和性能章节会用到）
- **Python 基础语法**：类、函数、异常处理、数据结构（本部分不再重复讲解基础语法）

如果你还没学完前两部分，建议至少了解以下概念：
- `with` 语句和上下文管理器（陷阱 #11）
- `async`/`await` 基础（陷阱 #6）
- `__eq__` / `__hash__` dunder 方法（陷阱 #14）
- 生成器和 `yield`（性能优化章节）

## 各章节详细预览

### 性能优化深入（01）

性能优化的核心原则：**不要猜，要测**。本章覆盖：

- **性能分析工具链**：`cProfile`（函数级分析）、`timeit`（微基准）、`tracemalloc`（内存追踪）、`line_profiler`（逐行分析）、`py-spy`（采样式 profiling）
- **数据结构选择**：`list` vs `tuple` vs `deque` vs `set` vs `dict` 的时间复杂度对比，对应 Java `ArrayList` / `ArrayDeque` / `HashSet` / `HashMap`
- **字符串操作优化**：`join` vs `+`（对应 Java `StringBuilder`），`f-string` vs `format` vs `%`
- **循环优化**：列表推导式 vs `for` + `append`，`map` vs comprehension
- **缓存策略**：`functools.lru_cache`，对应 Java `Caffeine` / `Guava Cache`
- **惰性求值**：生成器 vs 列表，对应 Java `Stream` vs `List`
- **函数调用开销**：局部变量缓存技巧（Python 无 JIT，手动优化更有效）
- **实战**：优化慢函数的全过程（分析 → 假设 → 验证 → 确认）

### 最佳实践（02）

"Pythonic"不是玄学，而是社区沉淀的编码习惯。本章覆盖：

- **Pythonic 写法**：`enumerate` / `zip` / unpacking / walrus operator
- **代码风格**：PEP 8 + `ruff`（lint + format 一体化）+ 类型注解
- **错误处理**：EAFP（先做再说）vs LBYL（先检查再做），精确异常捕获，异常链
- **项目结构**：src layout，`pyproject.toml`，`__init__.py` 模块组织
- **测试**：pytest `fixture` / `parametrize` / 原生 `assert`，对应 JUnit 5
- **日志**：`logging` 配置，结构化日志，对应 SLF4J / Logback
- **配置管理**：环境变量 / `.env` / `pydantic-settings`，对应 Spring `@ConfigurationProperties`
- **文档**：Google style docstring 规范

### 常见陷阱与避坑指南（03）

16 个最常见陷阱，每个用"错误写法 → 正确写法"对比，并标注 Java 是否有类似问题：

- **Python 独有陷阱**：可变默认参数、链式赋值与可变对象
- **语义反转**：`==` vs `is`（与 Java 正好相反）
- **通用陷阱**：浅拷贝、可变类属性、except 过宽、finally return、浮点数精度、线程安全、遍历修改集合
- **Python 特有约束**：闭包延迟绑定、async 阻塞调用、全局变量 `global` 声明、`__eq__`/`__hash__` 自动设 `None`
- **实现细节**：整数缓存（Python -5~256 vs Java -128~127）

## 小结

- 本部分聚焦实战经验：性能、习惯、避坑，不是学新特性而是积累工程素养
- 推荐阅读顺序：**陷阱 → 最佳实践 → 性能优化**（先避坑，再养成习惯，最后按需优化）
- Java 工程经验大部分可迁移，但"Pythonic"需要重新建立直觉
- 迁移难度最高的是：Pythonic 语法、EAFP 风格、`==`/`is` 语义反转、GIL 对并发的影响
- 性能优化核心原则：不要猜，要测——先用工具分析瓶颈，再针对性优化，最后验证效果
- 陷阱章节的每个陷阱都标注了 Java 是否有类似问题，帮你快速判断优先级
- 所有代码示例可运行，建议边读边敲，加深理解

> 📁 所有可运行的代码示例位于 [`src/code/practice/`](../code/practice/) 目录，
> 每个章节文档中会链接到对应的源文件，包含完整可运行的代码。

> 💡 **提示**：如果你时间有限，建议至少读完陷阱章节（03），这是投入产出比最高的部分。
