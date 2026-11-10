# 上下文管理器进阶

`with` 语句是 Python 资源管理的核心机制。本章深入讲解 `contextlib` 提供的高级工具，
以及如何用 `@contextmanager` 装饰器优雅地实现自定义上下文管理器。

## 回顾：with 与 async with

`with` 语句对应 Java 的 try-with-resources。对象实现 `__enter__` / `__exit__` 即可使用。
异步版本 `async with` 则实现 `__aenter__` / `__aexit__`。

> [async with 基础回顾](../code/advanced/08_context_managers.py#L40-L54)

```python
{{#include ../code/advanced/08_context_managers.py:40:54}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `with obj as x` | `try (var x = obj)` | 自动资源管理 |
| `__enter__` / `__exit__` | `AutoCloseable.close()` | Java 只有 close，Python 分进入/退出 |
| `async with` | 无直接对应 | Java 的 close 是同步的 |

## ExitStack：动态管理多个上下文

Java 的 try-with-resources 可以写多个资源，但数量在编译期固定。Python 的 `ExitStack`
可以**动态添加**任意数量的上下文，退出时按 LIFO 顺序自动清理。

```python
with ExitStack() as stack:
    handles = [stack.enter_context(ManagedFile(f)) for f in files]
    # 退出时按 LIFO 自动调用每个 __exit__
```

> [ExitStack 动态管理多个文件](../code/advanced/08_context_managers.py#L86-L105)

```python
{{#include ../code/advanced/08_context_managers.py:86:105}}
```

ExitStack 还支持 `callback` 方法注册任意清理函数，不需要对象实现 `__enter__`/`__exit__`：

> [ExitStack.callback 注册清理回调](../code/advanced/08_context_managers.py#L106-L119)

```python
{{#include ../code/advanced/08_context_managers.py:106:119}}
```

### AsyncExitStack

异步版本，配合 `async with` 动态管理多个异步上下文：

> [AsyncExitStack 异步版本](../code/advanced/08_context_managers.py#L120-L134)

```python
{{#include ../code/advanced/08_context_managers.py:120:134}}
```

## contextlib.suppress：明确地忽略异常

`suppress` 上下文管理器明确表达"我故意忽略这个异常"，比空 `except` 块更清晰。

```python
# 传统写法
try:
    risky_operation()
except FileNotFoundError:
    pass

# suppress 写法：意图更明确
with suppress(FileNotFoundError, PermissionError):
    risky_operation()
```

> [suppress 忽略指定异常](../code/advanced/08_context_managers.py#L135-L156)

```python
{{#include ../code/advanced/08_context_managers.py:135:156}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `suppress(ExcType)` | `catch (ExcType e) {}` | 空捕获 |
| 退出后自动恢复 | 需手动恢复 | suppress 是上下文管理的 |

## redirect_stdout / redirect_stderr：重定向输出

临时重定向标准输出/错误流，退出 `with` 后自动恢复。

```python
buffer = io.StringIO()
with redirect_stdout(buffer):
    print("这条消息被重定向到 buffer")
# 退出后 stdout 自动恢复
print(f"buffer 内容: {buffer.getvalue()!r}")
```

> [redirect_stdout/stderr 重定向](../code/advanced/08_context_managers.py#L157-L179)

```python
{{#include ../code/advanced/08_context_managers.py:157:179}}
```

### Java 对比

Java 用 `System.setOut(new PrintStream(...))` 重定向，但需要手动恢复原值。
Python 的 `redirect_stdout` 是上下文管理器，退出自动恢复，更安全。

## contextlib.closing：给只有 close() 的对象加 with 支持

有些对象（如 urllib 的 response）只有 `close()` 方法，没有实现 `__enter__`/`__exit__`，
无法直接用 `with`。`closing` 包装器在退出时自动调用 `close()`。

> [closing 包装只有 close() 的对象](../code/advanced/08_context_managers.py#L193-L210)

```python
{{#include ../code/advanced/08_context_managers.py:193:210}}
```

### Java 对比

Java 等价：`try { ... } finally { obj.close(); }`，但 Python 的 `with closing(obj)` 更简洁。

## @contextmanager 装饰器

用生成器函数实现上下文管理器，比写 `__enter__`/`__exit__` 省事得多：
- `yield` 之前 = `__enter__`
- `yield` 的值 = `as` 变量
- `yield` 之后 = `__exit__`

```python
@contextmanager
def indented_block(label: str):
    print(f"[{label}] 进入")
    try:
        yield f"value-of-{label}"  # 交给 as 变量
    finally:
        print(f"[{label}] 退出")
```

> [@contextmanager 装饰器基本用法](../code/advanced/08_context_managers.py#L193-L210)

```python
{{#include ../code/advanced/08_context_managers.py:193:210}}
```

### 在 contextmanager 中处理异常

在 `yield` 处用 `try/except` 捕获异常，不 re-raise 就等于吞掉异常（类似 `__exit__` 返回 True）：

> [contextmanager 中捕获异常](../code/advanced/08_context_managers.py#L224-L234)

```python
{{#include ../code/advanced/08_context_managers.py:224:234}}
```

## 实战：数据库事务管理器

用 `@contextmanager` 实现事务管理：正常退出 commit，异常退出 rollback。

```python
@contextmanager
def transaction(db: FakeDB):
    db.begin()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
```

> [事务成功提交](../code/advanced/08_context_managers.py#L296-L302)

```python
{{#include ../code/advanced/08_context_managers.py:296:302}}
```
>
> [事务异常回滚](../code/advanced/08_context_managers.py#L305-L319)

```python
{{#include ../code/advanced/08_context_managers.py:305:319}}
```

### Java 对比

JDBC 等价写法：
```java
conn.setAutoCommit(false);
try {
    // ... 业务逻辑
    conn.commit();
} catch (Exception e) {
    conn.rollback();
    throw e;
}
```

Python 的 `with transaction(db)` 把这个模式封装成一行，更优雅。

## 嵌套上下文 + ExitStack 组合

ExitStack 可以组合事务与文件等多种上下文，退出按 LIFO 顺序清理：

> [ExitStack 组合事务与文件](../code/advanced/08_context_managers.py#L320-L335)

```python
{{#include ../code/advanced/08_context_managers.py:320:335}}
```

## 小结

- `ExitStack`：动态管理数量不定的上下文（Java 做不到）
- `AsyncExitStack`：异步版，配合 `async with`
- `suppress`：明确地忽略指定异常，比空 catch 更清晰
- `redirect_stdout/stderr`：临时重定向输出，自动恢复
- `closing`：给只有 `close()` 的对象加 with 支持
- `@contextmanager`：用 yield 优雅实现 `__enter__`/`__exit__`
- 实战：`transaction` 管理器 = commit/rollback 模式

> 📁 [查看完整代码](../code/advanced/08_context_managers.py)
