# 内存与性能

Python 用**引用计数 + 分代 GC** 管理内存，与 Java 的 JVM GC（可达性分析）机制不同。
本章讲解引用计数、循环引用、弱引用、性能分析工具与内存优化。

## 核心概念

### 引用计数

Python 主要靠引用计数回收对象：**引用归零立即回收**。循环引用无法靠引用计数解决，需要分代 GC。

Java 不用引用计数，靠 GC 可达性分析批量回收。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| 引用计数 + 分代 GC | JVM GC（G1/ZGC） | 内存回收机制 |
| `sys.getrefcount(obj)` | 无直接对应 | 查看引用计数 |
| `gc.collect()` | `System.gc()`（仅建议） | 手动回收 |
| `weakref.ref` | `WeakReference` | 弱引用 |
| `WeakValueDictionary` | `WeakHashMap` | 弱引用字典 |
| `__slots__` | 固定字段（Java 默认） | 省内存 |
| `tracemalloc` | VisualVM / JProfiler | 内存追踪 |
| `cProfile` | JProfiler / async-profiler | 性能分析 |
| `timeit` | JMH | 微基准测试 |

## 引用计数 + 分代 GC

> [引用计数演示](../code/advanced/06_memory_perf.py#L28-L35)

```python
{{#include ../code/advanced/06_memory_perf.py:28:35}}
```

`__del__` 在引用归零时触发，类似 Java `finalize`（但更及时）。

### 循环引用

> [循环引用与 GC](../code/advanced/06_memory_perf.py#L59-L84)

```python
{{#include ../code/advanced/06_memory_perf.py:59:84}}
```

循环引用的对象互相引用，引用计数不为零，但已不可达。`gc` 模块检测循环引用并回收。

## 弱引用 weakref

弱引用不增加引用计数，对象可被回收。对应 Java `WeakReference` / `WeakHashMap`，常用于缓存、观察者模式：

> [weakref 演示](../code/advanced/06_memory_perf.py#L86-L117)

```python
{{#include ../code/advanced/06_memory_perf.py:86:117}}
```

## gc 模块手动控制

Java GC 是自动的，`System.gc()` 只是建议。Python 的 `gc` 模块可以禁用、手动触发、查看统计：

> [gc 模块控制](../code/advanced/06_memory_perf.py#L119-L142)

```python
{{#include ../code/advanced/06_memory_perf.py:119:142}}
```

## __slots__ 内存优化

`__slots__` 省去 `__dict__`，每个对象省约 100+ 字节。大量对象时效果显著：

> [__slots__ 内存对比](../code/advanced/06_memory_perf.py#L144-L148)

```python
{{#include ../code/advanced/06_memory_perf.py:144:148}}
```

## tracemalloc 内存追踪

`tracemalloc` 追踪内存分配，按行号统计，对应 Java VisualVM / JProfiler：

> [tracemalloc 演示](../code/advanced/06_memory_perf.py#L207-L228)

```python
{{#include ../code/advanced/06_memory_perf.py:207:228}}
```

## cProfile / timeit 性能分析

- **cProfile**：函数级性能分析，对应 JProfiler / async-profiler
- **timeit**：精确计时，对应 JMH（Java Microbenchmark Harness）

> [cProfile 演示](../code/advanced/06_memory_perf.py#L230-L235)

```python
{{#include ../code/advanced/06_memory_perf.py:230:235}}
```
>
> [timeit 演示](../code/advanced/06_memory_perf.py#L265-L281)

```python
{{#include ../code/advanced/06_memory_perf.py:265:281}}
```

## 列表 vs 生成器内存对比

列表一次性分配所有内存，生成器几乎不占内存：

> [列表 vs 生成器](../code/advanced/06_memory_perf.py#L283-L307)

```python
{{#include ../code/advanced/06_memory_perf.py:283:307}}
```

100 万元素列表约 8MB，生成器仅约 200 字节，内存节省数万倍。

## 实战：优化内存密集场景

大数据集用生成器逐条处理，避免一次性加载：

> [内存优化实战](../code/advanced/06_memory_perf.py#L309-L353)

```python
{{#include ../code/advanced/06_memory_perf.py:309:353}}
```

## 小结

- Python 用**引用计数 + 分代 GC**，引用归零立即回收，循环引用靠 GC 模块
- `weakref` 不增加引用计数，对应 Java `WeakReference`，用于缓存
- `__slots__` 省去 `__dict__`，大量对象时省内存显著
- `tracemalloc` 追踪内存分配，`cProfile` 分析性能，`timeit` 精确计时
- 大数据集用生成器逐条处理，避免一次性加载到内存

> 📁 [查看完整代码](../code/advanced/06_memory_perf.py)
