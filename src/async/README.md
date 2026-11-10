# Python 异步编程 (asyncio)

本部分面向**有丰富 Java 经验**的开发者，系统讲解 Python 的 `asyncio` 异步编程。
每个章节都会对比 Java 中的等价概念（如 `CompletableFuture`、`Reactor Flux`、`ExecutorService` 等），
帮助你快速建立心智模型。

## 章节目录

| 章节 | 主题 | 对应 Java 概念 |
|------|------|----------------|
| [01 - 协程基础](01-basics.md) | `async def` 与 `await` | `CompletableFuture` |
| [02 - 事件循环](02-event-loop.md) | Event Loop 生命周期 | Netty `NioEventLoop` |
| [03 - 任务管理](03-tasks.md) | `create_task` / `gather` / `TaskGroup` | `CompletableFuture.allOf` |
| [04 - 异步迭代器与生成器](04-async-iter.md) | `async for` / 异步生成器 | Reactor `Flux` |
| [05 - 异步上下文管理器](05-async-context.md) | `async with` / `__aenter__` | `try-with-resources` |
| [06 - 同步原语](06-primitives.md) | `Lock` / `Event` / `Semaphore` / `Queue` | `java.util.concurrent` |
| [07 - 实战 HTTP 与文件 I/O](07-realworld.md) | `aiohttp` / `aiofiles` / `to_thread` | `AsyncHttpClient` |
| [08 - 高级：取消、超时、异常](08-advanced.md) | `timeout` / `cancel` / `shield` | `orTimeout` / `cancel(true)` |
| [09 - 与 Java 对比](09-java-compare.md) | 并排对照速查 | — |

## 学习路径

建议按顺序学习，因为概念层层递进：

1. **基础篇（01-03）**：先理解协程、事件循环、任务管理这三块核心。
   这是 asyncio 的地基，对应 Java 中理解 `CompletableFuture` + `ExecutorService`。
2. **语法篇（04-05）**：掌握异步迭代器和异步上下文管理器，
   对应 Java 的 `Flux` 流式处理和 `try-with-resources`。
3. **工具篇（06-07）**：学习同步原语和实战 I/O，
   对应 Java 的 `java.util.concurrent` 和 HTTP 客户端。
4. **进阶篇（08-09）**：取消、超时、异常处理等高级话题，
   以及一张完整的 Java ↔ Python 对照速查表。

## 核心心智模型差异

在开始之前，请记住 Python asyncio 与 Java 异步的几个根本差异：

- **Java 异步基于线程/回调**，Python 基于协程（单线程协作式调度）
- **Python 的 `await` 是语法层面的**，编译器会警告你忘记 `await`（Java 的 `CompletableFuture` 忘记 `join` 不会报错）
- **Python 协程在单线程内并发**，没有线程切换开销，但也就无法利用多核（CPU 密集型仍需多进程）
- **Python 异常是抛出式的**，不像 Java `CompletableFuture` 的回调链式处理

> 📁 所有可运行的代码示例位于 [`src/code/async/`](../code/async/) 目录，
> 每个章节文档中会链接到对应的源文件。
