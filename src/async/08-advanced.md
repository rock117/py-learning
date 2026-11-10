# 高级：取消、超时、异常、子进程

本章涵盖 asyncio 的高级话题：超时控制、任务取消、异常传播和异步子进程。
这些是生产级异步代码必须掌握的内容。

## 核心概念

### 超时控制

Python 提供两种超时机制：

**asyncio.timeout (3.11+ 推荐)**——上下文管理器形式：

> [asyncio.timeout 超时](../code/async/08_advanced.py#L38-L64)

```python
{{#include ../code/async/08_advanced.py:38:64}}
```

**asyncio.wait_for (兼容旧版)**——函数形式：

> [wait_for 超时](../code/async/08_advanced.py#L65-L78)

```python
{{#include ../code/async/08_advanced.py:65:78}}
```

两者超时后都会抛 `asyncio.TimeoutError`，并自动取消被等待的协程。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `asyncio.timeout` | `CompletableFuture.orTimeout` | 超时控制 |
| `task.cancel()` | `Future.cancel(true)` | 请求取消 |
| `CancelledError` | `InterruptedException` | 取消异常 |
| `asyncio.shield` | 不可取消的 future | 保护任务不被取消 |
| `create_subprocess_exec` | `ProcessBuilder` + 异步读取 | 异步子进程 |

## 手动取消任务

> [手动取消任务](../code/async/08_advanced.py#L79-L96)

```python
{{#include ../code/async/08_advanced.py:79:96}}
```

`task.cancel()` 请求取消，被取消的任务会抛 `CancelledError`。
`task.cancelled()` 返回是否被取消。

**重要**：`CancelledError` 应当向上传播，不要吞掉。

## 优雅处理取消：清理资源

> [优雅取消清理资源](../code/async/08_advanced.py#L97-L122)

```python
{{#include ../code/async/08_advanced.py:97:122}}
```

在 `except asyncio.CancelledError` 中执行清理逻辑（释放资源），
然后 `raise` 重新抛出，让调用者知道被取消了。

这对应 Java 中 `InterruptedException` 的处理模式——清理后重新抛出或标记中断状态。

## shield：保护任务不被取消

> [shield 保护任务](../code/async/08_advanced.py#L123-L147)

```python
{{#include ../code/async/08_advanced.py:123:147}}
```

`asyncio.shield(task)` 保护任务不被外层取消。
即使外层超时，被 shield 的任务仍会继续运行直到完成。

适用场景：某些"必须完成"的操作（如日志提交），不希望被外层超时取消。

## gather 中的异常传播

> [gather 异常传播](../code/async/08_advanced.py#L148-L180)

```python
{{#include ../code/async/08_advanced.py:148:180}}
```

两种模式：
- **默认**：任一协程抛异常，`gather` 立即抛出（其他任务继续在后台跑）
- **`return_exceptions=True`**：异常作为结果返回，不抛出——可以遍历检查每个结果

## TaskGroup 异常取消兄弟任务

> [TaskGroup 异常取消兄弟](../code/async/08_advanced.py#L181-L209)

```python
{{#include ../code/async/08_advanced.py:181:209}}
```

`TaskGroup` 中任一任务抛异常，会**自动取消所有兄弟任务**，
并用 `BaseExceptionGroup` 包装所有异常。这是结构化并发的核心保证。

## 异步子进程

> [异步子进程](../code/async/08_advanced.py#L210-L237)

```python
{{#include ../code/async/08_advanced.py:210:237}}
```

`asyncio.create_subprocess_exec` 创建子进程：
- `proc.communicate()`：一次性获取 stdout/stderr
- `async for line in proc.stdout`：流式逐行读取输出

对应 Java 的 `ProcessBuilder`，但 Python 可以用 `async for` 流式读取。

## 超时 + 清理组合实战

> [超时 + 清理组合](../code/async/08_advanced.py#L238-L258)

```python
{{#include ../code/async/08_advanced.py:238:258}}
```

实际项目中常见的模式：每个请求独立设置超时，
超时返回 `None` 而非抛异常，用 `gather` 并发执行。

## 小结

- `asyncio.timeout` (3.11+) / `wait_for`：超时控制
- `task.cancel()`：请求取消，抛 `CancelledError`
- 优雅取消：`try/except CancelledError` 中清理资源后重新抛出
- `shield`：保护任务不被外层取消
- `gather(return_exceptions=True)`：异常作为结果
- `TaskGroup`：异常自动取消兄弟任务
- `create_subprocess_exec`：异步子进程，支持流式读取

> 📁 [查看完整代码](../code/async/08_advanced.py)
