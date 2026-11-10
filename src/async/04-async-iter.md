# 异步迭代器与异步生成器

当数据源本身是异步的（如分页 API、消息流、日志流），你需要异步迭代。
本章讲解 `async for`、异步生成器和异步推导式。

## 核心概念

### async for：异步迭代

普通 `for` 循环调用 `__iter__` / `__next__`；
`async for` 调用 `__aiter__` / `__anext__`，其中 `__anext__` 可以是协程（能 `await`）。

### 手动实现异步迭代器

需要实现两个魔术方法：
- `__aiter__`：返回迭代器自身
- `__anext__`：返回下一个值（协程），结束时抛 `StopAsyncIteration`

> [手动实现异步迭代器](../code/async/04_async_iter.py#L24-L41)

```python
{{#include ../code/async/04_async_iter.py:24:41}}
```

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| 异步迭代器 | Reactor `Flux` / Java 9 `Flow.Subscriber` | 异步数据流 |
| `async for` | `flux.subscribe(item -> ...)` | 消费流 |
| 异步生成器 | `Flux.create(sink -> ...)` | 产生流 |
| `StopAsyncIteration` | `onComplete()` | 流结束信号 |

Java 的响应式流（Reactor/RxJava）是 push 模型（生产者推数据）；
Python 的异步迭代器是 pull 模型（消费者主动 `async for` 拉取）。

## 异步生成器：async def + yield

比手动实现 `__aiter__` / `__anext__` 更简洁的写法：
在 `async def` 函数中用 `yield`，就得到异步生成器。

> [异步生成器](../code/async/04_async_iter.py#L55-L59)

```python
{{#include ../code/async/04_async_iter.py:55:59}}
```

注意：异步生成器里的 `yield` 不需要 `await`，但函数体中可以 `await` 其他协程。

## 异步推导式

Python 支持在推导式中使用 `async for`：

> [异步推导式](../code/async/04_async_iter.py#L71-L94)

```python
{{#include ../code/async/04_async_iter.py:71:94}}
```

支持四种形式：
- 列表推导：`[x async for x in gen]`
- 集合推导：`{x async for x in gen}`
- 字典推导：`{k: v async for k, v in gen}`
- 生成器表达式：`(x async for x in gen)`

## 实战：流式处理分页 API

异步生成器非常适合流式处理场景。以下示例模拟分页 API 逐页拉取：

> [流式处理分页数据](../code/async/04_async_iter.py#L95-L98)

```python
{{#include ../code/async/04_async_iter.py:95:98}}
```

优势：不需要一次性加载所有数据到内存，逐条处理。

## 生产者-消费者：Queue + 异步生成器

> [Queue 生产消费模式](../code/async/04_async_iter.py#L129-L136)

```python
{{#include ../code/async/04_async_iter.py:129:136}}
```

用 `asyncio.Queue` 解耦生产者和消费者：
- `queue.put(item)`：放入（满了会等待）
- `queue.get()`：取出（空了会等待）
- `queue.task_done()`：标记一个任务处理完成
- `queue.join()`：等待所有任务处理完

## 高级：asend / aclose

异步生成器支持双向通信，可以用 `asend` 向生成器发送值：

> [asend 双向通信](../code/async/04_async_iter.py#L166-L171)

```python
{{#include ../code/async/04_async_iter.py:166:171}}
```

- `gen.asend(value)`：发送值，`yield` 表达式的返回值就是它
- `gen.aclose()`：关闭生成器
- 启动时必须先 `await gen.__anext__()` 或 `await gen.asend(None)`

## 小结

- `async for` 遍历异步迭代器（`__aiter__` / `__anext__`）
- `async def + yield` = 异步生成器，最常用
- 异步推导式：`[x async for x in gen]`
- 适合流式处理：分页 API、日志流、消息队列
- `asend` / `aclose` 用于高级双向通信场景

> 📁 [查看完整代码](../code/async/04_async_iter.py)
