# 函数式编程工具

Python 虽然不是纯函数式语言，但标准库提供了丰富的函数式编程工具：`itertools`、`functools`、
`operator`，以及 `dataclass(frozen=True)` 和 `NamedTuple` 等不可变值对象。

## itertools：惰性迭代器工具

`itertools` 提供一系列惰性迭代器，对应 Java Stream API 的中间操作。

### chain：拼接多个可迭代对象

```python
list(itertools.chain([1,2,3], [4,5], [6,7,8,9]))
# [1, 2, 3, 4, 5, 6, 7, 8, 9]

list(itertools.chain.from_iterable([[1,2], [3,4], [5,6]]))
# [1, 2, 3, 4, 5, 6]
```

> [chain 拼接迭代器](../code/advanced/09_functional.py#L33-L51)

```python
{{#include ../code/advanced/09_functional.py:33:51}}
```

### groupby：分组（需先排序！）

`groupby` 只对**连续**的相同 key 分组，所以通常要先排序。

> [groupby 分组示例](../code/advanced/09_functional.py#L52-L73)

```python
{{#include ../code/advanced/09_functional.py:52:73}}
```

### combinations / permutations / product

组合、排列、笛卡尔积，组合数学的常用工具：

> [combinations / permutations / product](../code/advanced/09_functional.py#L74-L93)

```python
{{#include ../code/advanced/09_functional.py:74:93}}
```

### islice：惰性切片

`islice` 支持无限迭代器，因为它不预先消费全部数据。

> [islice 惰性切片](../code/advanced/09_functional.py#L94-L113)

```python
{{#include ../code/advanced/09_functional.py:94:113}}
```

### accumulate：前缀累积

```python
list(itertools.accumulate([1,2,3,4,5]))
# [1, 3, 6, 10, 15]  累加

list(itertools.accumulate([1,2,3,4,5], operator.mul))
# [1, 2, 6, 24, 120]  累乘
```

> [accumulate 前缀累积](../code/advanced/09_functional.py#L114-L134)

```python
{{#include ../code/advanced/09_functional.py:114:134}}
```

### Java 对比

| Python itertools | Java Stream | 说明 |
|------------------|-------------|------|
| `chain(a, b)` | `Stream.concat(a, b)` | 拼接 |
| `chain.from_iterable` | `flatMap(List::stream)` | 展平嵌套 |
| `groupby` | `Collectors.groupingBy` | 分组（Python 需先排序） |
| `islice` | `skip(n).limit(m)` | 切片 |
| `takewhile/dropwhile` | `takeWhile/dropWhile` | 条件截取 |
| `starmap` | 无直接对应 | 解包后调用 |

## functools：函数工具

### reduce：归约

```python
functools.reduce(operator.add, [1,2,3,4,5], 0)  # 15
functools.reduce(operator.mul, range(1, 6), 1)   # 120
```

> [reduce 归约](../code/advanced/09_functional.py#L135-L154)

```python
{{#include ../code/advanced/09_functional.py:135:154}}
```

### partial：偏函数（固定部分参数）

```python
square = functools.partial(power, exp=2)
cube = functools.partial(power, exp=3)
```

> [partial 偏函数](../code/advanced/09_functional.py#L155-L178)

```python
{{#include ../code/advanced/09_functional.py:155:178}}
```

### cache / lru_cache：自动记忆化

```python
@functools.lru_cache(maxsize=128)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

> [cache 记忆化与 cache_info](../code/advanced/09_functional.py#L179-L207)

```python
{{#include ../code/advanced/09_functional.py:179:207}}
```

### Java 对比

| Python functools | Java | 说明 |
|------------------|------|------|
| `reduce(op, it, init)` | `stream.reduce(init, op)` | 归约 |
| `partial(func, arg=val)` | `x -> func(x, val)` (lambda) | 固定参数 |
| `@lru_cache` | Guava Cache / 手写 Map | 记忆化 |

## operator 模块

`operator` 模块提供常用操作的函数形式，避免写 lambda，代码更清晰。

```python
# itemgetter：等价于 lambda d: d["name"]
get_name = operator.itemgetter("name")
sorted(data, key=operator.itemgetter("name"))

# attrgetter：等价于 lambda obj: obj.attr
sorted(points, key=operator.attrgetter("x"))

# methodcaller：等价于 lambda s: s.upper()
operator.methodcaller("upper")("hello")
```

> [operator 模块：itemgetter/attrgetter/methodcaller](../code/advanced/09_functional.py#L208-L246)

```python
{{#include ../code/advanced/09_functional.py:208:246}}
```

## dataclass(frozen=True)：不可变值对象

`frozen=True` 让实例不可变，且可哈希（能放进 set / 当 dict key）。

```python
@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float = 0.0
```

> [frozen dataclass 不可变值对象](../code/advanced/09_functional.py#L208-L246)

```python
{{#include ../code/advanced/09_functional.py:208:246}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `@dataclass(frozen=True)` | `record` (Java 14+) | 不可变值对象 |
| 自动生成 `__eq__` / `__hash__` | record 自动生成 equals/hashCode | 值语义 |
| `frozen=True` 才可哈希 | record 天生不可变 | 可放入 set |

## NamedTuple：带类型注解的元组

`NamedTuple` 是 `tuple` 子类，兼具 tuple 的轻量与类型注解，内存比 dataclass 更小。

```python
class Employee(NamedTuple):
    name: str
    age: int
    dept: str = "engineering"
```

> [NamedTuple 带类型元组](../code/advanced/09_functional.py#L302-L313)

```python
{{#include ../code/advanced/09_functional.py:302:313}}
```

## 高阶函数 map / filter

```python
doubled = list(map(lambda x: x * 2, nums))
evens = list(filter(lambda x: x % 2 == 0, nums))
```

> [map / filter 高阶函数](../code/advanced/09_functional.py#L346-L369)

```python
{{#include ../code/advanced/09_functional.py:346:369}}
```

Python 更推荐用**生成器表达式**替代 `map`/`filter`，更 Pythonic：
```python
result = [x for x in (n * n for n in nums) if x > 10]
```

## 实战：生成器管道处理数据流

用生成器函数组装管道，每个阶段都是惰性的，数据逐条流过，内存占用 O(1)。

> [生成器管道处理日志流](../code/advanced/09_functional.py#L370-L417)

```python
{{#include ../code/advanced/09_functional.py:370:417}}
```

### Java 对比

Java 等价：`Stream.of(logs).filter(...).map(...).collect(...)`。
但 Python 的生成器管道可以处理**超大文件**而不占内存，因为每个阶段都是惰性的。

## 更多 itertools 工具

`takewhile` / `dropwhile` / `starmap` / `zip_longest` / `cycle` 等实用工具：

> [更多 itertools 工具](../code/advanced/09_functional.py#L418-L444)

```python
{{#include ../code/advanced/09_functional.py:418:444}}
```

## 小结

- `itertools` 提供惰性迭代器工具，对应 Java Stream 中间操作
- `functools.reduce` 归约，`partial` 偏函数，`cache` 记忆化
- `operator` 模块避免写 lambda，代码更清晰
- `dataclass(frozen=True)` ≈ Java record，不可变值对象
- `NamedTuple` 兼具 tuple 轻量与类型注解
- 生成器管道：惰性、省内存的数据流处理方式

> 📁 [查看完整代码](../code/advanced/09_functional.py)
