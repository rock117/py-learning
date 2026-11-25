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
| 不传递 `ContextVar` | `run_in_executor` 不会传，`to_thread` 会（见下节） |
| 异常传播 | 线程里的异常会原样抛回协程 ✅ |

实测：20 个 0.1s 阻塞任务，24 线程下 1 批完成（0.10s）；若超过线程数，会按批次排队。

> [Java 对比] `to_thread` ≈ `CompletableFuture.supplyAsync(fn, executor)`，
> 同样的线程池上限、同样的异常传播方式。

## 优化阻塞调用：对照表

发现“用了 asyncio 却没变快”时，先对照症状找原因：

| 症状 | 原因 | 对策 |
|------|------|------|
| 请求串行、根本没并发 | 循环里有阻塞调用 | 换异步库，或包 `to_thread` |
| 加了 `to_thread` 但并发上不去 | 线程池被占满 | 换异步库 / 调大池 / 加 `Semaphore` |
| 内存飙高、延迟有毛刺 | 线程过多、GIL 争抢 | 收敛并发，限制池大小 |
| 日志 traceId 串了 / 丢了 | `run_in_executor` 不传 `ContextVar` | 换 `to_thread` |
| 线程任务永远不结束 | 阻塞调用没设超时 | 必接加 `timeout=` |

### 优先级 1：换异步库（最优解）

`to_thread` 是**补救措施**，不是最优解。每个线程仍占约 8MB 栈、受 GIL 约束、线程数有上限。

| 阻塞库 | 异步替代 |
|--------|-----------|
| `requests` | `httpx.AsyncClient` / `aiohttp` |
| `psycopg2` | `asyncpg` / SQLAlchemy async |
| `open()` / `f.read()` | `aiofiles` |
| `boto3` | `aioboto3` |
| `redis-py` | `redis.asyncio` |
| `time.sleep` | `asyncio.sleep`（零成本） |

**判断标准**：

- 在**请求主路径且高频** → 一定换库
- 只是**启动时读配置** → 直接用 `open` 即可

### 优先级 2：必须包时，用 `to_thread` 而不是 `run_in_executor`

> [ContextVar 差异实测](../code/async/02_event_loop.py#L249-L274)

```python
{{#include ../code/async/02_event_loop.py:249:274}}
```

```python
request_id.set("req-123")

await asyncio.to_thread(read_cv)                      # 'req-123'   ✅
await loop.run_in_executor(None, read_cv)             # '<unset>'   ❌
```

`to_thread` 内部会 `copy_context()`，日志 traceId、用户身份不会丢；`run_in_executor` 不会。

> [要点] 需要上下文传递时**一律用 `asyncio.to_thread`**，它同时是 3.9+ 推荐的语法糖。

### 优先级 3：限制线程池大小

> [自定义线程池实测](../code/async/02_event_loop.py#L275-L307)

```python
{{#include ../code/async/02_event_loop.py:275:307}}
```

```python
from concurrent.futures import ThreadPoolExecutor

loop = asyncio.get_running_loop()
loop.set_default_executor(ThreadPoolExecutor(max_workers=8))
```

实测 6 个 0.1s 任务：

| 线程池 | 耗时 | 说明 |
|--------|------|------|
| 默认（24） | 0.10s | 1 批完成 |
| 自定义（2） | 0.30s | 3 批 × 0.1s |

**线程池大小直接决定并发上限**：

- 池子太大 → 每个线程约 8MB 栈 + 上下文切换开销，可能拖垮内存
- 池子太小 → 并发上不去，任务排队

> [建议] 按 IO 特性估算：`max_workers` ≈ 期望并发数，不要盲目调大。

### 优先级 4：外层再套 `Semaphore` 双层限流

> [双层限流实测](../code/async/02_event_loop.py#L308-L344)

```python
{{#include ../code/async/02_event_loop.py:308:344}}
```

```python
sem = asyncio.Semaphore(5)

async def limited_task(i):
    async with sem:                     # ← 先限流
        return await asyncio.to_thread(blocking_call, i)
```

实测 50 个任务、`Semaphore(5)`：耗时 0.52s，**峰值并发正好是 5**。

| 机制 | 保护什么 |
|------|-----------|
| `Semaphore` | 同时**进入**的任务数——保护下游服务 |
| 线程池 | 实际**并行**的线程数——保护本机内存 |

> ⚠️ **只靠线程池不够**：线程池有界，但**排队无界**——10000 个任务会先把内存吃满。
> 必须用 `Semaphore` 在进入线程池前就限流。

> ⚠️ **阻塞调用必接加 `timeout=`**，否则线程可能永久卡住不释放。

### 优先级 5：结构性优化

**批量合并**：N 次小调用 → 1 次批量调用

```python
# ❌ 100 次线程切换
await asyncio.gather(*[asyncio.to_thread(get_user, i) for i in ids])

# ✅ 一次批量接口
await asyncio.to_thread(get_users_batch, ids)
```

**提前加载**：启动时读到内存，请求路径上不碰 IO。

**缓存**：不变的阻塞结果用 `functools.lru_cache` 包在**同步函数**上——命中就不进线程池。

## 完整改写示例

从“串行 + 阻塞 + 无超时”逐步改到可用：

```python
# ❌ 优化前：100 个 URL × 0.5s = 50 秒
async def fetch_all(urls):
    results = []
    for url in urls:                    # 串行
        r = requests.get(url)           # 阻塞整个循环，无超时
        results.append(r.json())
    return results
```

```python
# ✅ 优化后：换成异步库 + 限流 + 超时
import asyncio, httpx

async def fetch_all(urls):
    sem = asyncio.Semaphore(20)
    async with httpx.AsyncClient(timeout=5) as client:
        async def one(url):
            async with sem:
                return (await client.get(url)).json()
        return await asyncio.gather(
            *(one(u) for u in urls), return_exceptions=True
        )
# 100 个 URL，20 并发 × 0.5s = 2.5 秒（约 20 倍）
```

如果**实在无法换库**（比如内部老服务只提供同步 SDK），退而求其次：

```python
async def fetch_all_fallback(urls):
    sem = asyncio.Semaphore(20)

    def _get(url):
        return requests.get(url, timeout=5).json()   # 必接加 timeout

    async def one(url):
        async with sem:
            return await asyncio.to_thread(_get, url)

    return await asyncio.gather(*(one(u) for u in urls),
                                return_exceptions=True)
```

> [要点] `return_exceptions=True` 让单个失败不影响其余，事后统一处理异常。

## 调度顺序：call_soon

`call_soon` 把一个同步回调加入事件循环的下一轮执行。
通过它可以观察事件循环的调度顺序：

> [调度顺序演示](../code/async/02_event_loop.py#L345-L371)

```python
{{#include ../code/async/02_event_loop.py:345:371}}
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

> [底层 API 演示](../code/async/02_event_loop.py#L372-L403)

```python
{{#include ../code/async/02_event_loop.py:372:403}}
```

```

## 多个事件循环

一般不需要多个循环。但在某些场景（如子线程中运行异步代码），
可以为每个线程创建独立的循环：

> [每线程一个循环](../code/async/02_event_loop.py#L404-L425)

```python
{{#include ../code/async/02_event_loop.py:404:425}}
```

```

## 小结

- 事件循环是 asyncio 的调度核心，单线程轮询
- 用 `asyncio.run()` 作为入口，自动管理循环生命周期
- 阻塞调用用 `run_in_executor` / `asyncio.to_thread` 桥接
- **`async def` 里直接调阻塞函数会卡住整个循环**，并发能力归零；读文件用 `to_thread` 或 `aiofiles`
- **优先级**：换异步库 > `to_thread` > 限制线程池 > `Semaphore` 限流；阻塞调用必接加 `timeout`
- `call_soon` 可观察底层调度顺序
- 底层 API 了解即可，日常用 `asyncio.run`

> 📁 [查看完整代码](../code/async/02_event_loop.py)
