# 异步上下文管理器

异步资源（数据库连接、HTTP 会话、锁）的获取和释放可能需要 `await`。
`async with` 让你在进入和退出时都能执行异步操作，保证资源正确释放。

## 核心概念

### async with

`async with` 调用 `__aenter__`（进入）和 `__aexit__`（退出），两者都是协程。
退出时**即使发生异常**也会调用 `__aexit__`，保证资源释放。

> [手动实现异步上下文管理器](../code/async/05_async_context.py#L24-L51)

```python
{{#include ../code/async/05_async_context.py:24:51}}
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

## 小结

- `async with` 调用 `__aenter__` / `__aexit__`，两者都可 `await`
- `@asynccontextmanager + yield` 是最简洁的写法
- 适合资源管理：连接、会话、锁、文件句柄
- 异常时 `__aexit__` 仍会被调用，保证资源释放

> 📁 [查看完整代码](../code/async/05_async_context.py)
