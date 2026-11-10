# 事件循环 Event Loop

事件循环是 asyncio 的"心脏"，负责调度协程、处理 I/O 回调、管理定时器。
本章帮助你理解它的生命周期和底层调度机制。

## 核心概念

### 事件循环是什么

事件循环是一个**单线程**的调度器，不断轮询：
1. 就绪的 I/O 事件（网络、管道）
2. 到期的定时器
3. 就绪的回调队列

然后把对应的协程恢复执行。你可以把它想象成一个 `while True` 循环。

> [获取当前事件循环](../code/async/02_event_loop.py#L56-L66)

```python
{{#include ../code/async/02_event_loop.py:56:66}}
```

### asyncio.run —— 推荐入口

`asyncio.run(main())` 封装了完整的生命周期管理：
- 创建新循环
- 运行 main 协程
- 取消未完成的任务
- 关闭循环

**重要**：`asyncio.run` 每次都创建新循环，**不能在已有循环内调用它**。
实际项目中应在 `__main__` 顶层调用，且只调用一次。

> [asyncio.run 演示](../code/async/02_event_loop.py#L31-L55)

```python
{{#include ../code/async/02_event_loop.py:31:55}}
```

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| Event Loop | Netty `NioEventLoop` | 单线程轮询就绪事件 |
| `asyncio.run` | 启动 `EventLoopGroup(1)` | 创建并管理循环 |
| `run_in_executor` | `CompletableFuture.supplyAsync(fn, executor)` | 阻塞调用丢线程池 |
| `asyncio.to_thread` | 同上的语法糖 (3.9+) | 更简洁的写法 |

## run_in_executor：桥接阻塞代码

事件循环是单线程的，如果协程中必须调用阻塞代码（如 `requests.get`、`time.sleep`），
需要用 `run_in_executor` 把它丢到线程池执行，避免卡住事件循环。

> [run_in_executor 三种方式](../code/async/02_event_loop.py#L73-L100)

```python
{{#include ../code/async/02_event_loop.py:73:100}}
```

三种方式：
1. **默认线程池**：`loop.run_in_executor(None, blocking_fn, arg)`
2. **自定义线程池**：传入自己的 `ThreadPoolExecutor`
3. **`asyncio.to_thread`**（3.9+ 推荐）：语法糖，最简洁

这对应 Java 的 `CompletableFuture.supplyAsync(blockingFn, executor)`。

## 调度顺序：call_soon

`call_soon` 把一个同步回调加入事件循环的下一轮执行。
通过它可以观察事件循环的调度顺序：

> [调度顺序演示](../code/async/02_event_loop.py#L101-L127)

```python
{{#include ../code/async/02_event_loop.py:101:127}}
```

理解要点：
- `call_soon` 的回调在当前协程让出控制权（`await`）后才执行
- `await asyncio.sleep(0)` 是一种"让出一次控制权"的技巧

## 底层 API（了解即可）

老式写法（3.10 起已不推荐）：

```python
loop = asyncio.get_event_loop()
loop.run_until_complete(coro)
loop.close()
```

新写法 `asyncio.run` 封装了上面所有步骤。日常开发**请用 `asyncio.run`**。

> [底层 API 演示](../code/async/02_event_loop.py#L128-L159)

```python
{{#include ../code/async/02_event_loop.py:128:159}}
```

## 多个事件循环

一般不需要多个循环。但在某些场景（如子线程中运行异步代码），
可以为每个线程创建独立的循环：

> [每线程一个循环](../code/async/02_event_loop.py#L160-L181)

```python
{{#include ../code/async/02_event_loop.py:160:181}}
```

## 小结

- 事件循环是 asyncio 的调度核心，单线程轮询
- 用 `asyncio.run()` 作为入口，自动管理循环生命周期
- 阻塞调用用 `run_in_executor` / `asyncio.to_thread` 桥接
- `call_soon` 可观察底层调度顺序
- 底层 API 了解即可，日常用 `asyncio.run`

> 📁 [查看完整代码](../code/async/02_event_loop.py)
