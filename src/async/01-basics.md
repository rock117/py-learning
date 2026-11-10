# 协程基础：async def 与 await

本章是 asyncio 的入门基石。我们将理解 `async def` 定义的是什么、`await` 做了什么，
以及同步阻塞与异步挂起的本质区别。

## 核心概念

### async def 定义的是"协程函数"

用 `async def` 定义的函数叫**协程函数**（coroutine function）。
调用它**不会立即执行**，而是返回一个**协程对象**（coroutine object）。
协程对象必须交给事件循环调度才会真正运行。

```python
async def say_hello(name: str) -> str:
    await asyncio.sleep(0.5)
    return f"Hello, {name}!"

coro = say_hello("world")  # 得到协程对象，尚未执行
```

### await 的语义

`await` 的作用是**挂起当前协程**，把控制权交还给事件循环。
事件循环可以去执行其他就绪的协程，等被 await 的操作完成后，再恢复当前协程。

> [查看最简单的协程定义](../code/async/01_basics.py#L23-L34)

```python
{{#include ../code/async/01_basics.py:23:34}}
```

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `async def` | 返回 `CompletableFuture<T>` 的方法 | 定义异步单元 |
| `await` | `future.get()` | 等待结果，但 Python 是挂起而非阻塞线程 |
| `asyncio.run(main())` | 启动 Netty EventLoop 并运行入口任务 | 程序入口 |
| 协程对象 | 尚未执行的 `Supplier` | 调用得到对象，不立即执行 |

关键区别：Java 的 `future.get()` **阻塞当前线程**；
Python 的 `await` **挂起当前协程**，线程可以继续跑别的协程。

## 协程对象 ≠ 执行

这是新手最容易踩的坑。调用 `async def` 函数只是创建对象：

> [协程对象不等于执行](../code/async/01_basics.py#L35-L47)

```python
{{#include ../code/async/01_basics.py:35:47}}
```

必须通过以下方式之一才会执行：
- `await coro` — 在另一个协程内直接等待
- `asyncio.create_task(coro)` — 调度为后台任务
- `asyncio.run(coro)` — 作为程序入口运行

## 同步 sleep vs 异步 sleep

这是理解"阻塞"与"挂起"差异的关键：

| `time.sleep(0.5)` | `await asyncio.sleep(0.5)` |
|-------------------|---------------------------|
| 阻塞整个线程 | 挂起当前协程 |
| 事件循环无法运行其他协程 | 事件循环可以调度其他协程 |
| 相当于 Java 的 `Thread.sleep()` | 相当于 Java 的异步延迟调度 |

> [同步 sleep 阻塞线程](../code/async/01_basics.py#L62-L67)

```python
{{#include ../code/async/01_basics.py:62:67}}
```
>
> [异步 sleep 不阻塞线程](../code/async/01_basics.py#L70-L80)

```python
{{#include ../code/async/01_basics.py:70:80}}
```

**在协程中绝对不要用 `time.sleep`**，它会卡住整个事件循环。

## 执行协程的三种方式

> [三种执行方式示例](../code/async/01_basics.py#L86-L106)

```python
{{#include ../code/async/01_basics.py:86:106}}
```

1. **直接 `await`**：最常见，串行等待结果
2. **`create_task`**：调度为后台任务，稍后 `await`（第 3 课详讲）
3. **`gather`**：并发执行多个协程（第 3 课详讲）

## awaitable 的三种形态

在 Python 中，凡是能用 `await` 等待的对象都叫 **awaitable**，有三种：

| 类型 | 说明 | Java 类比 |
|------|------|-----------|
| 协程 (coroutine) | `async def` 调用的返回值 | `Supplier` |
| Task | `create_task` 包装的协程 | `CompletableFuture` |
| Future | 底层容器，日常很少直接用 | `CompletableFuture` 底层 |

> [awaitable 三种形态演示](../code/async/01_basics.py#L107-L131)

```python
{{#include ../code/async/01_basics.py:107:131}}
```

## 程序入口：asyncio.run

`asyncio.run(main())` 是标准入口，它会：
1. 创建一个新的事件循环
2. 运行传入的协程直到完成
3. 取消未完成的任务
4. 关闭事件循环

> [asyncio.run 入口](../code/async/01_basics.py#L132-L158)

```python
{{#include ../code/async/01_basics.py:132:158}}
```

## 小结

- `async def` 定义协程函数，调用得到协程对象（不执行）
- `await` 挂起当前协程，交还控制权给事件循环
- `asyncio.sleep` 非阻塞，`time.sleep` 阻塞整个线程
- 执行协程的三种方式：`await` / `create_task` / `gather`
- `asyncio.run()` 是程序入口，只调用一次

> 📁 [查看完整代码](../code/async/01_basics.py)
