# `with` 语句与上下文管理器

`with` 只做一件事：**进入时准备资源，退出时一定清理**。它把释放逻辑封装进对象本身，调用方不可能忘记。

这一章从零讲起。如果你只想知道"`with` 是什么"，看完前两节就够；要自己写上下文管理器，看后面几节。

## 为什么需要 `with`

没有 `with` 时，资源管理有三种写法，各有问题：

```python
# ❌ 写法一：手动关闭，异常时泄漏
f = open(path)
data = f.read()        # 这里抛异常，f 永远不会关闭
f.close()

# ⚠️ 写法二：try/finally，正确但啰嗦
f = open(path)
try:
    data = f.read()
finally:
    f.close()          # 必须自己写，且容易漏

# ✅ 写法三：with，释放逻辑在对象内部
with open(path) as f:
    data = f.read()
```

> [三种写法对比](../code/basics/05_with_statement.py#L38-L81)

```python
{{#include ../code/basics/05_with_statement.py:38:81}}
```

> [Java 对比] 这就是 Java 7 的 **try-with-resources**，概念完全对应：

| | Java | Python |
|---|---|---|
| 语法 | `try (var x = obj) { }` | `with obj as x:` |
| 协议 | `AutoCloseable.close()` | `__enter__` / `__exit__` |
| 异常时清理 | `close()` 仍执行 | `__exit__` 仍执行 |

## `with` 到底做了什么

`with obj as x:` 的展开过程：

```python
mgr = obj
x = mgr.__enter__()                 # ① 进入，返回值绑定给 x
try:
    ...with 块内的代码...
except Exception as e:
    if not mgr.__exit__(type(e), e, e.__traceback__):
        raise                        # ② __exit__ 返回 True 则吞掉异常
else:
    mgr.__exit__(None, None, None)   # ② 正常退出
```

> [展开过程演示](../code/basics/05_with_statement.py#L83-L127)

```python
{{#include ../code/basics/05_with_statement.py:83:127}}
```

关键点：**`__exit__` 一定会被调用**，这是 `with` 存在的全部理由。

## 常见内置用法

> [常用场景演示](../code/basics/05_with_statement.py#L129-L178)

```python
{{#include ../code/basics/05_with_statement.py:129:178}}
```

| 场景 | 写法 | Java 对应 |
|------|------|-----------|
| 文件 | `with open(p) as f:` | try-with-resources |
| 加锁 | `with lock:` | `synchronized` / `lock()+finally` |
| 临时目录 | `with TemporaryDirectory() as d:` | 无（需自己 deleteRecursively） |
| 重定向输出 | `with redirect_stdout(buf):` | `System.setOut` 手动还原 |
| 临时改精度 | `with localcontext():` | 无惯用对应 |

`with lock:` 最值得注意——它同时完成了 `acquire()` 和 `finally: release()` 两件事：

```python
lock = threading.Lock()

with lock:            # 自动 acquire
    counter += 1      # 自动 release，即使抛异常
```

### 临时修改全局状态

这是一个容易忽略但很有用的模式：

> [localcontext 示例](../code/basics/05_with_statement.py#L181-L197)

```python
{{#include ../code/basics/05_with_statement.py:181:197}}
```

```python
with localcontext() as ctx:
    ctx.prec = 4
    Decimal(1) / Decimal(3)      # 用 4 位精度
# 退出后自动恢复原精度
```

比手动"存旧值 → 改 → 还原"安全得多，因为即使块内抛异常也会还原。

## 自己实现：类

需要维护状态（比如对外暴露耗时）时，用类：

> [类实现示例](../code/basics/05_with_statement.py#L199-L236)

```python
{{#include ../code/basics/05_with_statement.py:199:236}}
```

```python
class Timer:
    def __enter__(self):
        self._start = time.perf_counter()
        return self                  # 返回值给 as 变量

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        return False                 # False/None = 不吞异常

with Timer() as t:
    time.sleep(0.02)
print(t.elapsed)                     # 事后可读取状态
```

`__exit__` 的三个参数：异常类型、异常值、traceback。正常退出时三者都是 `None`。

> [要点] `__enter__` 返回 `self` 是常见惯例，这样 `as` 变量能拿到管理器对象本身。

## 自己实现：`@contextmanager`

不需要维护状态时，方式更简洁：

> [装饰器实现示例](../code/basics/05_with_statement.py#L238-L282)

```python
{{#include ../code/basics/05_with_statement.py:238:282}}
```

```python
from contextlib import contextmanager

@contextmanager
def resource(name):
    print(f"[setup] 打开 {name}")
    try:
        yield {"name": name}         # yield 之前 = __enter__
    finally:
        print(f"[teardown] 关闭 {name}")   # yield 之后 = __exit__
```

- `yield` 的值 → `as` 后面的变量
- **必须包在 `try/finally` 里**，否则块内抛异常时清理逻辑不会执行

## `@contextmanager` 的执行流程

理解它的关键是：**`yield` 把函数一分为二**。

> [执行流程演示](../code/basics/05_with_statement.py#L284-L323)

```python
{{#include ../code/basics/05_with_statement.py:284:323}}
```

```python
@contextmanager
def traced(name):
    print("① 进 with 前：开始执行函数体")
    print("② 相当于 __enter__")
    try:
        yield f"<{name}>"          # ③ 暂停，控制权交回 with 块，值绑给 as
    finally:
        print("④ 回到 yield 之后（相当于 __exit__）")

with traced("res") as x:
    print(f"③ with 块体执行，x = {x}")
```

实际输出顺序：

```
① 进 with 前：开始执行函数体（yield 之前）
② 相当于 __enter__
③ with 块体执行，x = <res>
④ 回到 yield 之后（相当于 __exit__）
```

与类写法的映射关系：

| 类写法 | `@contextmanager` 写法 |
|--------|------------------------|
| `__enter__` 的代码 | `yield` **之前**的代码 |
| `__enter__` 的返回值 | `yield` **的值** |
| `__exit__` 的代码 | `yield` **之后**的代码 |

> [要点] 底层上，`@contextmanager` 把生成器包装成了 `_GeneratorContextManager`：
> `__enter__` 调 `next(gen)`，`__exit__` 调 `gen.throw()` / `gen.close()`。
> 这也解释了为什么 **`yield` 处是异常注入点**——异常是从 `yield` 那一行抛出来的，所以只有 `try/finally` 能保证清理。

> [要点] 99% 的场景用 `@contextmanager` 就够了，只有需要重复进入同一对象时才用类。

## `__exit__` 返回 `True` 会吞掉异常

这是 Python 独有的能力，Java 的 try-with-resources 做不到。

> [吞异常演示](../code/basics/05_with_statement.py#L284-L323)

```python
{{#include ../code/basics/05_with_statement.py:284:323}}
```
```

```python
class Swallow:
    def __exit__(self, exc_type, exc_val, exc_tb):
        return True                  # 块内任何异常都消失

with Swallow():
    raise ValueError("看不见我")     # 不会抛出，程序继续
```

标准库提供了现成版本：

```python
from contextlib import suppress

with suppress(FileNotFoundError):
    open("不存在.txt")
```

> ⚠️ **不要滥用。** 吞掉异常会让 bug 难以定位。库作者尤其不要默认吞异常；即使要吞，也应在文档里写清楚只吞哪一类。

### `@contextmanager` 写法下的异常处理

装饰器写法没有 `__exit__` 返回值可用，**是否吞掉异常取决于你是否重新 `raise`**。

> [装饰器异常处理演示](../code/basics/05_with_statement.py#L325-L376)

```python
{{#include ../code/basics/05_with_statement.py:325:376}}
```

**① 吞掉（不重新抛）**

```python
@contextmanager
def swallow_value_error():
    try:
        yield
    except ValueError as exc:
        print(f"[吞掉] {exc}")
    # 不重新抛 = 异常消失
```

**② 处理后重新抛出（推荐）**

```python
@contextmanager
def log_and_reraise():
    try:
        yield
    except Exception as exc:
        logger.exception("出错了")
        raise                  # ✅ 关键：一定要重抛
```

**③ 只拦截特定类型**

```python
@contextmanager
def only_ignore_keyerror():
    try:
        yield
    except KeyError:
        pass                  # 只忽略 KeyError，其他照常传播
```

实际运行结果：

```
[吞掉] ValueError: 看不见我
程序继续执行
[记录] RuntimeError: 要传出去
异常已向上传播，调用方能感知
[忽略] KeyError
TypeError 未被拦截，正常传播
```

| 需求 | 类写法 | 装饰器写法 |
|------|--------|-----------|
| 吞异常 | `__exit__` 返回 `True` | `except` 块里不 `raise` |
| 传播异常 | `__exit__` 返回 `False`/`None` | `except` 块里 `raise` |
| 只吞特定类型 | `except_type in (...)` 判断后返回 `True` | `except SomeError:` |

> ⚠️ `except` 块里**不写 `raise` 就等于吞异常**。写的时候务必想清楚：这里是真的可以忽略，还是只是忘了重抛？

## 多资源与退出顺序

> [多资源示例](../code/basics/05_with_statement.py#L284-L323)

```python
{{#include ../code/basics/05_with_statement.py:284:323}}
```
```

```python
# 推荐：一行管多个
with open(a) as fin, open(b, "w") as fout:
    fout.write(fin.read())

# 等价但缩进更深
with open(a) as fin:
    with open(b, "w") as fout:
        ...
```

退出顺序是 **LIFO（后进先出）**：

```
enter A → enter B → enter C → 块内 → exit C → exit B → exit A
```

这与 Java try-with-resources 的关闭顺序一致。当 B 依赖 A 时必须注意顺序。

## 常见陷阱

> [完整陷阱演示](../code/basics/05_with_statement.py#L325-L376)

```python
{{#include ../code/basics/05_with_statement.py:325:376}}
```
```

### 坑 1：`@contextmanager` 里忘了 `try/finally`

```python
@contextmanager
def bad():
    r = acquire()
    yield r              # ❌ 块内抛异常时不会 release
    release(r)

@contextmanager
def good():
    r = acquire()
    try:
        yield r
    finally:
        release(r)       # ✅
```

### 坑 2：同一个生成器对象不能重复 `with`

```python
cm = once()
with cm: pass
with cm: pass        # ❌ AttributeError（生成器已耗尽）

# 正确：每次都调用工厂函数
with once(): pass
with once(): pass
```

### 坑 3：`__exit__` 参数顺序写错

固定签名，三个位置参数，顺序不能乱：

```python
def __exit__(self, exc_type, exc_val, exc_tb):
```

### 坑 4：块内 `return` 也会触发 `__exit__`

```python
def f():
    with open(p) as fh:
        return fh.read()      # 文件依然会被关闭 ✅
```

这点和 Java 一致，不必担心资源泄漏。

### 坑 5：需要对象却忘了 `as`

```python
with open(p):          # 能用，但拿不到文件对象
    pass

with open(p) as f:     # 需要对象时务必 as
    ...
```

## Java 对照总表

> [完整对照代码](../code/basics/05_with_statement.py#L379-L413)

```python
{{#include ../code/basics/05_with_statement.py:379:413}}
```
```

| 场景 | Python | Java |
|------|--------|------|
| 资源管理 | `with obj as x:` | `try (var x = obj)` |
| 协议 | `__enter__` / `__exit__` | `AutoCloseable.close()` |
| 多资源 | `with a, b:` | `try (a; b)` |
| 退出顺序 | LIFO | LIFO |
| 异常时清理 | 一定执行 | 一定执行 |
| **吞异常** | `__exit__` 返回 `True` | **无此能力** |
| 异步版 | `async with` | 无（`close` 同步） |

## 小结

- `with` = try/finally 的封装，`__exit__` **一定**会被调用
- `__enter__` 的返回值绑定给 `as` 变量
- 日常用 `@contextmanager`，需要暴露状态时用类
- `yield` 必须包在 `try/finally` 里，否则异常时不清理
- **`__exit__` 返回 `True` 会静默吞异常**——Python 独有，慎用
- 多资源按 LIFO 退出，与 Java try-with-resources 一致

> 进阶内容（`ExitStack` 动态管理、`redirect_stdout`、多重嵌套）见[上下文管理器进阶](../advanced/08-context-managers.md)；异步版本见[异步上下文管理器](../async/05-async-context.md)。

> 📁 [完整代码](../code/basics/05_with_statement.py)
