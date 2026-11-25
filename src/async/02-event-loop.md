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

> [run_in_executor 三种方式](../code/async/02_event_loop.py#L73-L102)

```python
{{#include ../code/async/02_event_loop.py:73:102}}
```

```

三种方式：
1. **默认线程池**：`loop.run_in_executor(None, blocking_fn, arg)`
2. **自定义线程池**：传入自己的 `ThreadPoolExecutor`
3. **`asyncio.to_thread`**（3.9+ 推荐）：语法糖，最简洁

这对应 Java 的 `CompletableFuture.supplyAsync(blockingFn, executor)`。

## 阻塞调用：哪些、为什么、怎么办

这是实际开发中最重要的一节。先回答一个常见问题：

> **`async def` 里能不能调 `open()` / `requests.get`？**
> 能调，**但整个事件循环会停住**，所有其他协程一起卡。

### 代价有多大

> [阻塞对比演示](../code/async/02_event_loop.py#L112-L164)

```python
{{#include ../code/async/02_event_loop.py:112:164}}
```


实测：5 个“读文件”任务（每个阻塞 0.1s）

| 写法 | 耗时 | 说明 |
|------|------|------|
| 直接在 `async def` 里调 | **0.52s** | 串行执行，5 × 0.1s |
| `await asyncio.to_thread(...)` | **0.10s** | 真并发 |

提速 **5.1 倍**。

更直观的证据——阻塞期间心跳协程完全无法运行：

```
→ 阻塞的 0.1s 里，心跳只跑了 0 次（若不被阻塞应约 10 次）
```

> [要点] 事件循环是单线程的。一个协程里出现阻塞调用，**整个循环停转**，
> 所有并发能力归零。这就是“用了 asyncio 却没有变快”的根本原因。

### 哪些是阻塞的

| 阻塞（需桥接） | 异步替代 |
|---|---|
| `open()` / `f.read()` / `f.write()` | `asyncio.to_thread` / `aiofiles` |
| `requests.get()` | `httpx.AsyncClient` / `aiohttp` |
| `psycopg2` / `mysqlclient` | `asyncpg` / `aiomysql` / SQLAlchemy async |
| `time.sleep()` | `asyncio.sleep()` |
| `urllib.request` | `aiohttp` |
| 大量 CPU 计算 | `ProcessPoolExecutor` |
| `boto3` | `aioboto3` |

> ⚠️ 判断标准：**函数名里没有 `async`、返回的不是 awaitable，就是阻塞的**。
> 不要因为“它是 IO，应该不阻塞吧”而想当然。

### 读文件：三种方案

> [文件 I/O 三种方案](../code/async/02_event_loop.py#L167-L210)

```python
{{#include ../code/async/02_event_loop.py:167:210}}
```


```python
# A. 直接 open —— 阻塞（仅适合启动时读配置等一次性操作）
with open(path, encoding="utf-8") as f:
    content = f.read()

# B. to_thread —— 推荐，零依赖
def _read():
    with open(path, encoding="utf-8") as f:
        return f.read()
content = await asyncio.to_thread(_read)

# B2. 带参数：位置参数直接跟在后面
lines = await asyncio.to_thread(_read_lines, 1)

# C. aiofiles —— 专用异步库，高频小文件场景
async with aiofiles.open(path, encoding="utf-8") as f:
    content = await f.read()
```

选择建议：

| 场景 | 方案 |
|------|------|
| **绝大多数场景** | `asyncio.to_thread`（零依赖） |
| 高频小文件读写 | `aiofiles`（避免线程池开销） |
| 启动时读一次配置 | 直接用 `open` 即可 |

### `to_thread` 的代价

> [to_thread 的限制](../code/async/02_event_loop.py#L213-L248)

```python
{{#include ../code/async/02_event_loop.py:213:248}}
```


| 限制 | 说明 |
|------|------|
| **受线程数限制** | 默认 `min(32, CPU+4)`，本机实测 24 个线程 |
| **GIL 依然存在** | CPU 密集任务用它不会变快 |
| CPU 密集场景 | 应该用 `ProcessPoolExecutor` |
| 不传递 `ContextVar` | 需显式 `copy_context()` |
| 异常传播 | 线程里的异常会原样抛回协程 ✅ |

实测：20 个 0.1s 阻塞任务，24 线程下 1 批完成（0.10s）；若超过线程数，会按批次排队。

> [Java 对比] `to_thread` ≈ `CompletableFuture.supplyAsync(fn, executor)`，
> 同样的线程池上限、同样的异常传播方式。

## 调度顺序：call_soon

`call_soon` 把一个同步回调加入事件循环的下一轮执行。
通过它可以观察事件循环的调度顺序：

> [调度顺序演示](../code/async/02_event_loop.py#L249-L275)

```python
{{#include ../code/async/02_event_loop.py:249:275}}
```

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

> [底层 API 演示](../code/async/02_event_loop.py#L276-L307)

```python
{{#include ../code/async/02_event_loop.py:276:307}}
```

```

## 多个事件循环

一般不需要多个循环。但在某些场景（如子线程中运行异步代码），
可以为每个线程创建独立的循环：

> [每线程一个循环](../code/async/02_event_loop.py#L308-L329)

```python
{{#include ../code/async/02_event_loop.py:308:329}}
```

```

## 小结

- 事件循环是 asyncio 的调度核心，单线程轮询
- 用 `asyncio.run()` 作为入口，自动管理循环生命周期
- 阻塞调用用 `run_in_executor` / `asyncio.to_thread` 桥接
- **`async def` 里直接调阻塞函数会卡住整个循环**，并发能力归零；读文件用 `to_thread` 或 `aiofiles`
- `call_soon` 可观察底层调度顺序
- 底层 API 了解即可，日常用 `asyncio.run`

> 📁 [查看完整代码](../code/async/02_event_loop.py)
