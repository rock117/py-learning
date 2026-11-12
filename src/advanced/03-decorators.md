# 装饰器进阶

> 本章假设你已会写基础装饰器。如果对 `@deco` 与 `f = deco(f)` 的等价关系、
> 闭包为什么是前提、`wrapper` 为什么要写 `*args, **kwargs` 还有疑问，
> 请先看[装饰器入门](../basics/08-decorators.md)。

本章专注三件事：

1. 叠加顺序（多个装饰器同时作用时谁先谁后）
2. `functools` 提供的现成装饰器（`lru_cache` / `singledispatch` / `cached_property`）
3. 真实项目里的装饰器写法

## 装饰器本质再确认

```python
@simple_logger
def add(a, b):
    return a + b
# 等价于：add = simple_logger(add)
```

装饰器接收原函数，返回一个包装后的新函数。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `@decorator`（语言级） | 注解 + AOP（Spring） | 横切逻辑 |
| 带参数装饰器 | 带参数注解 `@Repeat(3)` | 参数化切面 |
| 类装饰器 | `InvocationHandler` 代理 | 保存状态的代理 |
| `functools.wraps` | 无直接对应 | 保留原函数元信息 |
| `lru_cache` | Guava `CacheBuilder` / Caffeine | 自动 LRU 缓存 |
| `singledispatch` | 方法重载 | 按类型运行时分派 |
| `cached_property` | `@Cacheable` / lazy init getter | 首次计算并缓存 |

## 基础装饰器与带参数装饰器

这两种形态已在[入门章](../basics/08-decorators.md)详细拆解，这里只列代码备查。

### 基础装饰器

最简单的装饰器：打印调用日志，类似 Spring AOP 的 `@Before` 切面：

> [基础日志装饰器](../code/advanced/03_decorators.py#L28-L41)

```python
{{#include ../code/advanced/03_decorators.py:28:41}}
```

### 带参数装饰器（三层嵌套）

最外层接收参数，中间层接收函数，最内层是 wrapper：

> [带参数装饰器 repeat](../code/advanced/03_decorators.py#L56-L77)

```python
{{#include ../code/advanced/03_decorators.py:56:77}}
```

## 类装饰器

类装饰器利用 `__call__` 让实例可调用，优点是可以保存状态（比闭包更清晰）：

> [CountCalls 类装饰器](../code/advanced/03_decorators.py#L92-L112)

```python
{{#include ../code/advanced/03_decorators.py:92:112}}
```

类似 Java 实现 `InvocationHandler` 的代理类。

## functools.wraps 保留元信息

装饰器返回的 wrapper 会"遮盖"原函数的 `__name__`、`__doc__` 等元信息。
`functools.wraps` 把原函数的元信息复制到 wrapper：

> [wraps 对比](../code/advanced/03_decorators.py#L130-L134)

```python
{{#include ../code/advanced/03_decorators.py:130:134}}
```

**写装饰器时务必加 `@functools.wraps(func)`**，否则调试和文档会出问题。

## functools.lru_cache 自动缓存

一行装饰器实现 LRU 缓存，对应 Java 的 Guava Cache / Caffeine：

> [lru_cache 斐波那契缓存](../code/advanced/03_decorators.py#L157-L170)

```python
{{#include ../code/advanced/03_decorators.py:157:170}}
```

`cache_info()` 可查看命中情况。注意：被缓存的函数参数必须可哈希。

## functools.singledispatch 按类型分派

Java 有编译期方法重载，Python 运行期用 `singledispatch` 模拟——按第一个参数类型选择实现：

> [singledispatch to_json](../code/advanced/03_decorators.py#L184-L206)

```python
{{#include ../code/advanced/03_decorators.py:184:206}}
```

## functools.cached_property

首次访问时计算并缓存，后续直接返回。对应 Spring `@Cacheable` 或手写的 lazy init：

> [cached_property 示例](../code/advanced/03_decorators.py#L251-L266)

```python
{{#include ../code/advanced/03_decorators.py:251:266}}
```

## 装饰器叠加顺序

装饰器**从下往上应用，从上往下执行**：

```python
@decorator_a
@decorator_b
def stacked(): ...
# 等价于：stacked = decorator_a(decorator_b(stacked))
# 执行顺序：A before -> B before -> f -> B after -> A after
```

> [装饰器叠加顺序演示](../code/advanced/03_decorators.py#L281-L288)

```python
{{#include ../code/advanced/03_decorators.py:281:288}}
```

## 实战装饰器

三个最常用的实战装饰器：

- **计时 `@timer`**：测量函数耗时
- **重试 `@retry`**：失败自动重试，对应 Spring Retry 的 `@Retryable`
- **日志 `@log_call`**：记录调用与异常

> [计时装饰器](../code/advanced/03_decorators.py#L322-L331)

```python
{{#include ../code/advanced/03_decorators.py:322:331}}
```
>
> [重试装饰器](../code/advanced/03_decorators.py#L334-L353)

```python
{{#include ../code/advanced/03_decorators.py:334:353}}
```
>
> [日志装饰器](../code/advanced/03_decorators.py#L370-L386)

```python
{{#include ../code/advanced/03_decorators.py:370:386}}
```

## 小结

- 装饰器本质是高阶函数，`@decorator` 是 `func = decorator(func)` 的语法糖
- 带参数装饰器需三层嵌套；类装饰器用 `__call__` 保存状态
- **务必用 `functools.wraps` 保留原函数元信息**
- `lru_cache` 一行实现 LRU 缓存，`singledispatch` 实现按类型分派
- 实战三件套：计时、重试、日志

> 📁 [查看完整代码](../code/advanced/03_decorators.py)
