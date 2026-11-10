# Python 高级特性

本部分面向**有丰富 Java 经验**的开发者，系统讲解 Python 的类型系统、元编程、装饰器、生成器、并发与性能等高级特性。
每个章节都会对比 Java 中的等价概念（如泛型、注解处理器、`ExecutorService`、`WeakReference` 等），
帮助你快速建立心智模型。

## 章节目录

| 章节 | 主题 | 对应 Java 概念 |
|------|------|----------------|
| [01 - 类型系统与静态检查](01-type-system.md) | `typing` / `Protocol` / `overload` / 协变逆变 | 泛型、`interface`、方法重载 |
| [02 - 面向对象与元编程](02-metaprogramming.md) | 描述符、元类、ABC、`__slots__`、dunder | 反射、APT、`abstract class` |
| [03 - 装饰器进阶](03-decorators.md) | 带参装饰器、类装饰器、`functools` | 注解 + AOP（Spring） |
| [04 - 生成器与协程进阶](04-generators.md) | `yield from` / `send` / 管道 / itertools | `Stream` / `Iterator` |
| [05 - 并发与并行（非 async）](05-concurrency.md) | `threading` / `multiprocessing` / GIL | `Thread` / `ExecutorService` |
| [06 - 内存与性能](06-memory-perf.md) | 引用计数、GC、`weakref`、`cProfile` | JVM GC、JMH、VisualVM |

## 学习路径与优先级

推荐按以下顺序学习，概念层层递进：

1. **类型系统（01）**：如果你写的是中大型项目，类型注解 + `mypy`/`pyright` 是必备能力。
   对应 Java 的静态类型检查，是"工程化"的基石。优先级最高。
2. **元编程（02）**：理解描述符、元类、dunder 方法，才能读懂主流框架（Django ORM、SQLAlchemy）。
   对应 Java 的反射 + 字节码增强。优先级高。
3. **装饰器（03）**：Python 工程中无处不在，对应 Java 的 AOP。优先级高。
4. **生成器（04）**：惰性求值与流式处理的核心，对应 Java Stream API。优先级中。
5. **并发（05）**：理解 GIL 是 Python 并发的关键，对应 Java 并发包。优先级中。
6. **内存与性能（06）**：性能调优时再深入，对应 JVM 调优。优先级按需。

> 💡 如果你时间有限，建议至少完成 **01 → 02 → 03** 三章，这三块是理解 Python 生态的钥匙。

## 核心心智模型差异

在开始之前，请记住 Python 与 Java 的几个根本差异：

- **Python 是动态强类型**：运行期才检查类型，但通过 `typing` 可获得静态检查能力
- **Python 的"类也是对象"**：类本身是 `type` 的实例，可在运行时动态创建/修改
- **Python 有 GIL**：同一时刻只有一个线程执行字节码，CPU 密集需用多进程
- **Python 用引用计数 + 分代 GC**：对象引用归零立即回收，循环引用靠 GC 模块
- **Python 元编程更直接**：无需 ASM/CGLib，元类和描述符是语言级特性

> 📁 所有可运行的代码示例位于 [`src/code/advanced/`](../code/advanced/) 目录，
> 每个章节文档中会链接到对应的源文件。
