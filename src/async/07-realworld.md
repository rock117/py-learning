# 实战：HTTP 与文件 I/O

本章把前面学到的概念应用到真实场景：异步 HTTP 请求、异步文件 I/O、
并发控制、错误重试和批量下载。

## 核心概念

### asyncio.to_thread：桥接阻塞库

不需要第三方库，用 `asyncio.to_thread`（3.9+）就能把阻塞调用丢到线程池：

> [to_thread 桥接阻塞 HTTP](../code/async/07_realworld.py#L32-L39)

```python
{{#include ../code/async/07_realworld.py:32:39}}
```

3 个各延迟 1s 的请求，并发执行总耗时约 1s（而非串行的 3s）。
这是**零依赖**的异步方案——用标准库 `urllib` 也能并发。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `aiohttp` | `AsyncHttpClient` / `WebClient` | 异步 HTTP 客户端 |
| `aiofiles` | `AsynchronousFileChannel` | 异步文件 I/O |
| `asyncio.to_thread` | `CompletableFuture.supplyAsync(fn, executor)` | 桥接阻塞调用 |

## aiohttp：异步 HTTP 客户端

如果安装了 `aiohttp`，可以用原生异步 HTTP 客户端：

> [aiohttp 异步 HTTP](../code/async/07_realworld.py#L66-L91)

```python
{{#include ../code/async/07_realworld.py:66:91}}
```

推荐用法：一个 `ClientSession` 复用连接池，发多个请求。
这对应 Java 的 `WebClient` 或 `AsyncHttpClient`。

## 用 Semaphore 限制并发

> [限制并发数](../code/async/07_realworld.py#L92-L95)

```python
{{#include ../code/async/07_realworld.py:92:95}}
```

50 个请求，并发限制 10，避免压垮下游服务。
`Semaphore` + `gather` 是实际项目中最常见的并发控制模式。

## 异步文件 I/O

### asyncio.to_thread 方式（零依赖）

> [to_thread 文件 I/O](../code/async/07_realworld.py#L121-L125)

```python
{{#include ../code/async/07_realworld.py:121:125}}
```

并发读写 5 个文件，用 `to_thread` 把阻塞的 `open/read/write` 丢到线程池。

### aiofiles 方式（第三方库）

> [aiofiles 异步文件 I/O](../code/async/07_realworld.py#L165-L191)

```python
{{#include ../code/async/07_realworld.py:165:191}}
```

`aiofiles` 提供真正的异步文件 I/O API，语法与同步 `open` 类似：
```python
async with aiofiles.open(path, "w") as f:
    await f.write("hello")
```

## 错误重试模式

> [带重试的异步请求](../code/async/07_realworld.py#L192-L206)

```python
{{#include ../code/async/07_realworld.py:192:206}}
```

实现带指数退避的重试逻辑：
- 最多重试 `max_retries` 次
- 每次失败后等待 `delay * attempt`（指数退避）
- 全部失败后抛出最后一个异常

## 并发下载

> [并发下载文件](../code/async/07_realworld.py#L221-L227)

```python
{{#include ../code/async/07_realworld.py:221:227}}
```

结合 `Semaphore` 限制并发 + `to_thread` 写文件 + `gather` 并发调度，
实现批量下载模式。6 个文件，并发 3。

## 小结

- `asyncio.to_thread`：桥接阻塞库，无需第三方依赖
- `aiohttp`：异步 HTTP，`ClientSession` 复用连接
- `aiofiles`：异步文件 I/O
- `Semaphore`：限制并发，保护下游
- 重试 + 指数退避：提高健壮性
- `gather` + `Semaphore` 是最常用的并发控制组合

> 📁 [查看完整代码](../code/async/07_realworld.py)
