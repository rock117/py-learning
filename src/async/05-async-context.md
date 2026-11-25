# 异步上下文管理器

异步资源（数据库连接、HTTP 会话、锁）的获取和释放可能需要 `await`。
`async with` 让你在进入和退出时都能执行异步操作，保证资源正确释放。

## 核心概念

### async with

`async with` 调用 `__aenter__`（进入）和 `__aexit__`（退出），两者都是协程。
退出时**即使发生异常**也会调用 `__aexit__`，保证资源释放。

> [手动实现异步上下文管理器](../code/async/05_async_context.py#L54-L64)

```python
{{#include ../code/async/05_async_context.py:54:64}}
```


关键点：
- `__aenter__` 返回的值赋给 `as` 后的变量
- `__aexit__` 返回 `False`/`None` 时异常正常传播；返回 `True` 会吞掉异常（一般不要这样做）

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `async with` | `try-with-resources` | 资源管理 |
| `__aenter__` | `AutoCloseable` 构造 | 进入时初始化 |
| `__aexit__` | `AutoCloseable.close()` | 退出时清理 |
| `@asynccontextmanager` | — | 装饰器简化写法 |

**关键区别**：Java 的 `try-with-resources` 要求 `close()` 是**同步**方法；
Python 的 `async with` 允许 `__aexit__` 是**协程**，可以 `await` 异步关闭操作。

## 异常时自动清理

> [异常时仍调用 __aexit__](../code/async/05_async_context.py#L65-L79)

```python
{{#include ../code/async/05_async_context.py:65:79}}
```


即使 `with` 块内抛出异常，`__aexit__` 仍会被调用，连接会被正确关闭。
这与 Java 的 `try-with-resources` 行为一致。

## asynccontextmanager 装饰器（推荐）

手动实现 `__aenter__` / `__aexit__` 较繁琐。
`contextlib.asynccontextmanager` 装饰器可以把 `async def + yield` 包成上下文管理器：

> [装饰器写法](../code/async/05_async_context.py#L65-L79)

```python
{{#include ../code/async/05_async_context.py:65:79}}
```


- `yield` 之前的代码 = `__aenter__` 逻辑
- `yield` 的值 = `as` 变量
- `yield` 之后的代码（`finally` 块）= `__aexit__` 逻辑

## `asynccontextmanager` 的执行流程

和同步版完全同构，只是 **`yield` 前后都可以 `await`**。

> [执行流程演示](../code/async/05_async_context.py#L222-L256)

```python
{{#include ../code/async/05_async_context.py:222:256}}
```


```python
@asynccontextmanager
async def traced(name):
    print("① 进 async with 前")
    await asyncio.sleep(0.01)      # 进入时也可以是异步的
    print("② 相当于 __aenter__")
    try:
        yield f"<{name}>"         # ③ 值绑给 as
    finally:
        await asyncio.sleep(0.01)  # 退出时也可以是异步的
        print("④ 相当于 __aexit__")
```

实际输出：

```
① 进 async with 前：开始执行函数体
② 相当于 __aenter__（可以是协程）
③ with 块体执行，x = <res>
④ 回到 yield 之后（相当于 __aexit__）
```

与同步版的逐项对照：

| 同步 `@contextmanager` | 异步 `@asynccontextmanager` |
|---|---|
| `def` | `async def` |
| `with` | `async with` |
| `__enter__` / `__exit__` | `__aenter__` / `__aexit__`（都是协程） |
| `yield` 前后同步执行 | `yield` 前后都可以 `await` |

> ⚠️ `async def` 必须配 `async with`，两者不能混用：
> 用 `with` 打开异步管理器会报 `TypeError: 'async_generator' object is not a context manager`。

实际类型是 `_AsyncGeneratorContextManager`，对应同步版的 `_GeneratorContextManager`。

## 异步上下文管理器的异常与取消

> [异常与取消演示](../code/async/05_async_context.py#L259-L336)

```python
{{#include ../code/async/05_async_context.py:259:336}}
```


### 吞掉普通异常

```python
@asynccontextmanager
async def swallow_value_error():
    try:
        yield
    except ValueError as exc:
        print(f"[吞掉] {exc}")
    # 不重新抛 = 异常消失
```

### 处理后重抛（推荐）

```python
@asynccontextmanager
async def log_and_reraise():
    try:
        yield
    except Exception as exc:
        logger.exception("出错了")
        raise                  # ✅ 一定要重抛
```

### ❗致命坑：吞掉 `CancelledError`

这是异步版比同步版**严重得多**的坑。

```python
@asynccontextmanager
async def bad_suppressor():
    try:
        yield
    except BaseException:      # ❌ 连 CancelledError 一起吞
        pass
```

实测后果：

```
task.done()=True  task.cancelled()=False
cancelled()=False 说明取消【没有真正生效】
```

任务看起来结束了，但 `cancelled()` 是 `False`——**取消信号被吞掉，任务被当成“正常完成”**。结果是：

- 调用方以为已经取消，实际状态回滚/资源清理可能被跳过
- 超时控制、`asyncio.timeout()` 全部失效
- 关机流程里任务无法被优雅终止

正确写法：

```python
@asynccontextmanager
async def good_suppressor():
    try:
        yield
    except ValueError:          # ✅ 只拦具体业务异常
        pass
```

对照结果：

```
❌ except BaseException  -> cancelled()=False   取消被吞
✅ except ValueError     -> cancelled()=True    取消正常传播
```

> ⚠️ `CancelledError` 继承自 **`BaseException`**（不是 `Exception`），所以：
> - `except Exception` 拦不住它（这是对的）
> - 写成 `except:` 或 `except BaseException:` 就会吞掉取消（这是错的）
>
> **规则**：清理逻辑放 `finally`，不要在 `except` 里“包住一切”。

## 实战：连接池模式

> [异步连接池](../code/async/05_async_context.py#L101-L118)

```python
{{#include ../code/async/05_async_context.py:101:118}}
```


连接池用 `Semaphore` 限制并发数，`@asynccontextmanager` 包装 `acquire` 方法。
5 个任务但池大小 2，最多 2 个并发获取连接。

## 嵌套 async with

Python 支持在一行中嵌套多个 `async with`：

> [嵌套 async with](../code/async/05_async_context.py#L138-L148)

```python
{{#include ../code/async/05_async_context.py:138:148}}
```


```python
async with ConnA() as a, ConnB() as b:
    ...
```

等价于两层嵌套的 `async with`。

## 实战：HTTP 会话

模拟 `aiohttp.ClientSession` 的生命周期——创建一次会话，复用底层连接发多个请求：

> [HTTP 会话复用连接](../code/async/05_async_context.py#L149-L167)

```python
{{#include ../code/async/05_async_context.py:149:167}}
```


这是 aiohttp 的推荐用法：一个 `ClientSession` 内发多个请求，
复用 TCP 连接和连接池，退出时自动关闭。

复用 TCP 连接和连接池，退出时自动关闭。

## `contextvars`：异步世界的 ThreadLocal

这是 `async` 章节里最容易出问题的地方，也是与 Java 差异最大的一点。

> [contextvars 示例](../code/async/05_async_context.py#L339-L375)

```python
{{#include ../code/async/05_async_context.py:339:375}}
```

```

### 为什么 ThreadLocal 在 asyncio 里失效

Java 里用 `ThreadLocal` 或 MDC 传 traceId，前提是“**一个线程处理一个请求**”。但 asyncio 是**单线程跑成百上千个协程**，所有协程共享同一个线程，`ThreadLocal` 就退化成了全局共享：

```python
tl = threading.local()

async def work(name):
    tl.name = name
    await asyncio.sleep(0.01)    # 让出控制权，切到其他协程
    return tl.name

await asyncio.gather(work("A"), work("B"), work("C"))
# ['C', 'C', 'C']   全是最后一个写入的
```

### `ContextVar` 的用法

```python
import contextvars

_request_id = contextvars.ContextVar("request_id", default="-")

async def handle(req_id):
    token = _request_id.set(req_id)      # 写入，带回滚令牌
    try:
        await downstream()
    finally:
        _request_id.reset(token)          # 还原，避免污染调用方
```

每个协程有自己独立上下文副本，`gather` 并发执行时互不干扰。

### 三个要点

| 要点 | 说明 |
|------|------|
| **创建时给 `default=`** | 否则未 set 时 `get()` 抛 `LookupError` |
| **`set()` 返回 `token`** | 用完必须 `reset(token)`，否则污染外层 |
| **`copy_context()` 可显式派发** | `asyncio.to_thread` 会自动复制，`run_in_executor` 不会 |

> ⚠️ **MDC 在 async 代码里不要用。** Python 的 `logging` 不会自动读 `ContextVar`，需要在 `Formatter` 里手动 `_request_id.get()`，或者用 `structlog` 这类支持上下文绑定的库。

> [Java 对比]
> | Java | Python async |
> |------|--------------|
> | `ThreadLocal` | ❌ 失效（单线程多协程） |
> | `MDC.put("traceId", id)` | ❌ 同样失效 |
> | — | ✅ `ContextVar`（协程级隔离） |
> | — | ✅ `asyncio.to_thread` 自动复制上下文 |

> [要点] 在 Web 框架里，中间件设置 `ContextVar`，下游业务和日志库读取它——这就是 FastAPI / Starlette 传递请求上下文的方式。

## 小结

- `async with` 调用 `__aenter__` / `__aexit__`，两者都可 `await`
- `@asynccontextmanager + yield` 是最简洁的写法；`async def` 必须配 `async with`
- 适合资源管理：连接、会话、锁、文件句柄
- 异常时 `__aexit__` 仍会被调用，保证资源释放
- **绝对不能吞 `CancelledError`**（它继承 `BaseException`），否则取消与超时会静默失效
- **`ThreadLocal`/MDC 在 asyncio 下失效**，用 `ContextVar`（协程级隔离）

> 📁 [查看完整代码](../code/async/05_async_context.py)
