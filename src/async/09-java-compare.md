# Python async 与 Java 对比

本章用**并排对照**的方式，帮助 Java 开发者快速建立 Python async 的心智模型。
每个概念都给出 Java 等价代码（注释）和 Python 实现。

## 速查对照表

| 场景 | Java | Python |
|------|------|--------|
| 异步任务创建 | `CompletableFuture.supplyAsync` | `asyncio.create_task` |
| 等待全部 | `CompletableFuture.allOf` | `asyncio.gather` |
| 任一完成 | `CompletableFuture.anyOf` | `asyncio.wait(FIRST_COMPLETED)` |
| 线程池 | `ExecutorService` | `loop.run_in_executor` / `to_thread` |
| 响应式流 | Reactor `Flux` | 异步生成器 (`async def + yield`) |
| 超时 | `orTimeout()` | `asyncio.timeout` / `wait_for` |
| 取消 | `Future.cancel(true)` | `task.cancel()` |
| 异常处理 | `exceptionally` / `handle` | `try/except` |
| 串行组合 | `thenCompose` | `await` 串联 |
| 并行合并 | `thenCombine` | `gather` + 合并 |
| 互斥锁 | `ReentrantLock` | `asyncio.Lock` |
| 信号量 | `Semaphore` | `asyncio.Semaphore` |
| 事件 | `CountDownLatch` / `Event` | `asyncio.Event` |
| 队列 | `BlockingQueue` | `asyncio.Queue` |
| 结构化并发 | `StructuredTaskScope` (21) | `asyncio.TaskGroup` (3.11) |

> [速查表完整代码](../code/async/09_java_compare.py#L290-L315)

```python
{{#include ../code/async/09_java_compare.py:290:315}}
```

## 1. 异步任务创建

> [任务创建对比](../code/async/09_java_compare.py#L36-L61)

```python
{{#include ../code/async/09_java_compare.py:36:61}}
```

Java 用 `CompletableFuture.supplyAsync(() -> ..., pool)` 提交到线程池；
Python 用 `asyncio.create_task(coro)` 调度到事件循环。

## 2. 等待全部完成 (allOf)

> [allOf 对比](../code/async/09_java_compare.py#L62-L83)

```python
{{#include ../code/async/09_java_compare.py:62:83}}
```

Java 的 `allOf` 只返回 `Void`，需要自己组装结果；
Python 的 `gather` **直接返回结果列表**，更方便。

## 3. 任一完成 (anyOf)

> [anyOf 对比](../code/async/09_java_compare.py#L84-L112)

```python
{{#include ../code/async/09_java_compare.py:84:112}}
```

Python 用 `asyncio.wait(tasks, return_when=FIRST_COMPLETED)`，
注意要手动取消剩余的 pending 任务，避免任务泄漏。

## 4. 线程池执行 (supplyAsync with executor)

> [线程池对比](../code/async/09_java_compare.py#L119-L146)

```python
{{#include ../code/async/09_java_compare.py:119:146}}
```

- `asyncio.to_thread(fn, arg)`（3.9+ 推荐）：语法糖
- `loop.run_in_executor(None, fn, arg)`：底层 API

## 5. 响应式流 (Reactor Flux)

> [响应式流对比](../code/async/09_java_compare.py#L153-L171)

```python
{{#include ../code/async/09_java_compare.py:153:171}}
```

Java Reactor 的 `Flux` 对应 Python 的异步生成器：
- `flux.subscribe(item -> ...)` → `async for item in gen`
- `flux.map(x -> x*2).collectList()` → `[x*2 async for x in gen]`

## 6. 超时 (orTimeout)

> [超时对比](../code/async/09_java_compare.py#L172-L200)

```python
{{#include ../code/async/09_java_compare.py:172:200}}
```

- `asyncio.timeout(0.2)`（3.11+）：上下文管理器
- `asyncio.wait_for(coro, timeout=0.2)`：兼容旧版

## 7. 取消 (Future.cancel)

> [取消对比](../code/async/09_java_compare.py#L201-L228)

```python
{{#include ../code/async/09_java_compare.py:201:228}}
```

Java 的 `future.cancel(true)` 通过中断线程实现；
Python 的 `task.cancel()` 通过抛 `CancelledError` 实现。
协程应在 `except CancelledError` 中清理资源后重新抛出。

## 8. 异常处理 (exceptionally / handle)

> [异常处理对比](../code/async/09_java_compare.py#L229-L261)

```python
{{#include ../code/async/09_java_compare.py:229:261}}
```

Java 用回调链：`future.exceptionally(ex -> "fallback")`；
Python 用 `try/except`，更直观，也更容易调试。

## 9. 组合操作 (thenCompose / thenCombine)

> [组合操作对比](../code/async/09_java_compare.py#L262-L289)

```python
{{#include ../code/async/09_java_compare.py:262:289}}
```

- `thenCompose`（串行依赖）→ Python 直接 `await` 串联
- `thenCombine`（并行合并）→ `gather` + 合并

Python 的 `await` 让串行组合天然简单，不需要 `thenCompose` 的回调嵌套。

## 核心心智模型差异

> [心智模型总结](../code/async/09_java_compare.py#L316-L343)

```python
{{#include ../code/async/09_java_compare.py:316:343}}
```

1. **Java 异步基于线程/回调**，Python 基于协程（单线程协作式）
2. **Python 的 `await` 是语法层面的**，编译器保证不会忘记 `await`
3. **Python 没有 GIL 之外的多线程并行**，但协程并发足够 I/O 场景
4. **Python 异常是抛出式**，不像 Java `CompletableFuture` 的回调链
5. **TaskGroup 比 Java 的 StructuredTaskScope 更早成熟**

## 小结

对于 Java 开发者，记住一个核心映射：
**`CompletableFuture` → `asyncio`，`ExecutorService` → 事件循环**。

Python 的异步代码看起来像同步代码（`await` 串联），
比 Java 的回调链或 `CompletableFuture` 链式调用更直观。
代价是你必须理解协程的挂起/恢复机制，以及单线程协作式调度的特点。

> 📁 [查看完整代码](../code/async/09_java_compare.py)
