# 任务管理：create_task / gather / wait / TaskGroup

这是 asyncio 中**最常用、最重要**的一章。掌握任务管理，你才能写出真正并发的异步代码。

## 核心概念

### create_task：后台调度

`asyncio.create_task(coro)` 把协程包装为 Task 并立即调度执行。
与直接 `await coro` 不同，`create_task` 不会等待完成，主协程可以继续做别的事。

> [create_task 并发示例](../code/async/03_tasks.py#L32-L56)

```python
{{#include ../code/async/03_tasks.py:32:56}}
```

关键点：两个 `create_task` 后的 `await` 总耗时 ≈ 0.5s（并发），而非 1s（串行）。

### gather：并发 + 按顺序返回

`asyncio.gather(*coros)` 并发运行多个协程，**按传入顺序**返回结果列表。
即使后完成的先返回，结果顺序也与传入一致。

> [gather 按顺序返回](../code/async/03_tasks.py#L57-L73)

```python
{{#include ../code/async/03_tasks.py:57:73}}
```

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `create_task` | `CompletableFuture.supplyAsync` | 后台调度 |
| `gather` | `allOf().thenApply(取所有结果)` | 等待全部并收集 |
| `wait(FIRST_COMPLETED)` | `anyOf` | 任一完成 |
| `TaskGroup` | `StructuredTaskScope` (Java 21) | 结构化并发 |

Python 的 `gather` 比 Java 的 `allOf` 更方便——直接返回结果列表，
而 Java 的 `allOf` 只返回 `Void`，需要自己组装结果。

## gather 的异常处理

默认情况下，`gather` 中任一协程抛异常会立即向上抛出（其他任务继续在后台跑）。
用 `return_exceptions=True` 可以让异常作为结果返回，不抛出：

> [gather 异常处理](../code/async/03_tasks.py#L81-L107)

```python
{{#include ../code/async/03_tasks.py:81:107}}
```

## wait：灵活的等待控制

`asyncio.wait` 返回 `(done, pending)` 两个集合，支持多种等待策略：

| 策略 | 说明 | Java 类比 |
|------|------|-----------|
| `FIRST_COMPLETED` | 任一完成就返回 | `anyOf` |
| `FIRST_EXCEPTION` | 任一抛异常就返回 | — |
| `ALL_COMPLETED`（默认） | 全部完成 | `allOf` |

> [wait 灵活等待](../code/async/03_tasks.py#L108-L133)

```python
{{#include ../code/async/03_tasks.py:108:133}}
```

注意：`wait` 不直接返回结果，需要从 done 集合中取 `task.result()`。

## as_completed：按完成顺序迭代

`asyncio.as_completed` 返回一个迭代器，谁先完成谁先 yield。
适合"先到先处理"的场景：

> [as_completed 按完成顺序](../code/async/03_tasks.py#L134-L153)

```python
{{#include ../code/async/03_tasks.py:134:153}}
```

## TaskGroup：结构化并发（3.11+ 推荐）

`asyncio.TaskGroup` 是 Python 3.11 引入的**结构化并发**机制，是当前推荐写法：

> [TaskGroup 结构化并发](../code/async/03_tasks.py#L154-L181)

```python
{{#include ../code/async/03_tasks.py:154:181}}
```

优势：
- **作用域明确**：`async with` 块退出时所有任务必须完成
- **异常自动传播**：任一任务抛异常，自动取消所有兄弟任务
- **异常聚合**：用 `ExceptionGroup` 包装多个异常

### TaskGroup 异常取消兄弟任务

> [TaskGroup 异常传播](../code/async/03_tasks.py#L182-L207)

```python
{{#include ../code/async/03_tasks.py:182:207}}
```

当 `bad` 任务抛异常时，`good1` 和 `good2` 会被**自动取消**，
抛出的异常用 `BaseExceptionGroup` 包装。

## 性能对比：串行 vs 并发

> [性能对比](../code/async/03_tasks.py#L208-L228)

```python
{{#include ../code/async/03_tasks.py:208:228}}
```

5 个各耗时 0.2s 的请求：
- 串行：1.0s
- gather 并发：0.2s
- 加速比：5x

## 小结

- `create_task`：立即调度协程为后台任务
- `gather`：并发运行，按顺序返回，默认异常立即抛出
- `wait`：灵活控制（`FIRST_COMPLETED` / `ALL_COMPLETED`）
- `as_completed`：按完成顺序迭代
- `TaskGroup` (3.11+)：结构化并发，推荐替代裸 `gather`

> 📁 [查看完整代码](../code/async/03_tasks.py)
