# 生成器与协程进阶

Python 的 `yield` 是语言级特性，可暂停/恢复函数执行。生成器是 Python 协程的基础。
Java 没有生成器，类似功能用 Stream API（惰性求值）或 Iterator 实现。

## 核心概念

### 生成器函数

含 `yield` 的函数是生成器函数，调用它返回一个生成器对象。每次 `next()` 执行到 `yield` 暂停，
`yield` 后的值被产出。再次 `next()` 从暂停处恢复。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `yield` | 无直接对应 | 暂停/恢复执行 |
| `yield from` | 手动遍历子迭代器 | 委托子生成器 |
| `gen.send(value)` | 阻塞队列 / Channel | 双向通信 |
| 生成器管道 | Stream API | 惰性求值链 |
| 旧式协程（yield） | 回调 / CompletableFuture | 协程雏形 |
| itertools | Stream API | 迭代器工具 |

## yield from 委托子生成器

`yield from <iterable>` 等价于遍历并逐个 yield，但还能透传 `send`/`throw`/`close`：

> [yield from 委托](../code/advanced/04_generators.py#L23-L27)

```python
{{#include ../code/advanced/04_generators.py:23:27}}
```

## send / throw / close 双向通信

生成器不仅能产出值，还能通过 `send` 接收值，实现双向通信：

- `gen.send(value)`：恢复生成器，`value` 成为 `yield` 表达式的值
- `gen.throw(exc)`：在 `yield` 处抛出异常
- `gen.close()`：关闭生成器

> [echo_server 双向通信](../code/advanced/04_generators.py#L55-L75)

```python
{{#include ../code/advanced/04_generators.py:55:75}}
```

Java 没有直接对应，类似功能需要阻塞队列或 Channel。

## 生成器管道（惰性求值链）

类似 Unix 管道 `cat | grep | sort | head`，每个生成器处理一个元素就传给下一个，
惰性求值，内存占用极低：

> [生成器管道](../code/advanced/04_generators.py#L95-L98)

```python
{{#include ../code/advanced/04_generators.py:95:98}}
```

这是处理大数据集的核心模式，对应 Java Stream API 的链式操作。

## 基于生成器的旧协程（历史了解）

Python 3.5 之前用 `yield` 实现协程。`send` 向协程传值，`yield` 产出中间结果：

> [旧式协程 coroutine_avg](../code/advanced/04_generators.py#L147-L162)

```python
{{#include ../code/advanced/04_generators.py:147:162}}
```

现在推荐用 `async/await`，但了解历史有助于理解生成器与协程的关系。

## itertools 与生成器结合

`itertools` 提供高效的迭代器工具，与生成器配合非常强大，对应 Java Stream API：

| itertools | Java Stream | 说明 |
|-----------|-------------|------|
| `count(10, 2)` | `Stream.iterate` | 无限计数 |
| `cycle(["A","B"])` | 无直接对应 | 循环 |
| `chain([1,2],[3,4])` | `Stream.concat` | 串联 |
| `islice(gen, 5)` | `stream.limit(5)` | 切片 |
| `groupby(data, key)` | `Collectors.groupingBy` | 分组 |
| `starmap(func, pairs)` | 无直接对应 | 解包后调用 |

> [itertools 演示](../code/advanced/04_generators.py#L181-L217)

```python
{{#include ../code/advanced/04_generators.py:181:217}}
```

## 实战：流式处理大文件

生成器避免一次性加载整个文件到内存。`open()` 本身就是迭代器，逐行 yield：

> [流式处理日志管道](../code/advanced/04_generators.py#L219-L226)

```python
{{#include ../code/advanced/04_generators.py:219:226}}
```

## 实战：无限序列

生成器可以表达无限序列，按需取值：

> [无限斐波那契与素数序列](../code/advanced/04_generators.py#L270-L279)

```python
{{#include ../code/advanced/04_generators.py:270:279}}
```

用 `itertools.islice` 安全取值，避免无限循环。

## 小结

- `yield` 是语言级特性，可暂停/恢复函数执行，Java 没有直接对应
- `yield from` 委托子生成器并透传 `send`/`throw`/`close`
- `send`/`throw`/`close` 实现生成器双向通信
- 生成器管道实现惰性求值链，内存占用极低，对应 Java Stream API
- 旧式协程基于 `yield`，现代代码用 `async/await`
- 无限序列用 `islice` 安全取值

> 📁 [查看完整代码](../code/advanced/04_generators.py)
