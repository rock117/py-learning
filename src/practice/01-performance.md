# 性能优化深入

性能优化的核心原则：**不要猜，要测**。先用工具找到瓶颈，再针对性优化，最后验证效果。

本章覆盖 Python 性能分析工具链、数据结构选择、字符串/循环/缓存等常见优化手段，并对比 Java 生态中的等价工具。

## Java 对比：性能分析工具链

| Python 工具 | Java 对应 | 用途 |
|-------------|-----------|------|
| `cProfile` | JProfiler / async-profiler | 函数级性能分析 |
| `timeit` | JMH（Java Microbenchmark Harness） | 微基准测试 |
| `tracemalloc` | VisualVM / JProfiler 内存视图 | 内存分配追踪 |
| `line_profiler` | 无直接对应（JIT 内联） | 逐行性能分析 |
| `py-spy` | async-profiler | 采样式 profiling，低开销 |
| `memory_profiler` | VisualVM | 逐行内存分析 |

> [性能分析工具对比](../code/practice/01_performance.py#L34-L69)

```python
{{#include ../code/practice/01_performance.py:34:69}}
```

## 性能分析工具链

### cProfile：函数级分析

`cProfile` 是 Python 标准库自带的性能分析器，统计每个函数的调用次数和耗时：

> [cProfile 示例](../code/practice/01_performance.py#L34-L69)

```python
{{#include ../code/practice/01_performance.py:34:69}}
```

关键指标：
- `ncalls`：调用次数
- `tottime`：函数自身耗时（不含子调用）
- `cumtime`：累计耗时（含子调用）

用 `pstats` 排序结果，`cumtime` 高的函数是优化重点。

### timeit：微基准测试

`timeit` 精确测量小段代码的执行时间，自动重复多次取最佳值，对应 Java JMH：

> [timeit 示例](../code/practice/01_performance.py#L72-L87)

```python
{{#include ../code/practice/01_performance.py:72:87}}
```

> ⚠️ 不要用 `time.time()` 手动计时做微基准——GC、系统调度、JIT 预热都会干扰结果。
> Python 没有 JIT 预热问题，但 GC 和系统调度同样存在，`timeit` 会自动处理这些。

### tracemalloc：内存分配追踪

`tracemalloc` 追踪内存分配，按调用栈统计，找出内存热点：

> [tracemalloc 示例](../code/practice/01_performance.py#L90-L112)

```python
{{#include ../code/practice/01_performance.py:90:112}}
```

### line_profiler：逐行分析

`line_profiler`（第三方库）可以分析每行代码的耗时，比 `cProfile` 粒度更细：

> [line_profiler 示例](../code/practice/01_performance.py#L115-L130)

```python
{{#include ../code/practice/01_performance.py:115:130}}
```

### py-spy：采样式 profiling

`py-spy` 是采样式 profiler，开销极低，适合生产环境。对应 Java 的 async-profiler：

> [py-spy 使用说明](../code/practice/01_performance.py#L133-L151)

```python
{{#include ../code/practice/01_performance.py:133:151}}
```

## 数据结构选择

选对数据结构是性能优化的第一步。Python 内置数据结构的时间复杂度与 Java 集合框架有对应关系：

| Python | Java | 查找 | 插入 | 适用场景 |
|--------|------|------|------|----------|
| `list` | `ArrayList` | O(n) | O(1) 尾部 | 有序、随机访问 |
| `tuple` | 不可变 `List` | O(n) | 不可变 | 不可变序列 |
| `deque` | `ArrayDeque` | O(n) | O(1) 两端 | 队列/双端操作 |
| `set` | `HashSet` | O(1) | O(1) | 去重、成员判断 |
| `dict` | `HashMap` | O(1) | O(1) | 键值映射 |

> [数据结构性能对比](../code/practice/01_performance.py#L153-L174)

```python
{{#include ../code/practice/01_performance.py:153:174}}
```

关键经验：
- **成员判断用 `set` 不用 `list`**：`x in my_set` 是 O(1)，`x in my_list` 是 O(n)
- **频繁头部插入用 `deque` 不用 `list`**：`list.insert(0, x)` 是 O(n)
- **不可变数据用 `tuple` 不用 `list`**：`tuple` 更省内存，且可作为 `dict` 的键

## 字符串操作优化

### join vs +

`+` 拼接字符串在循环中会创建大量临时对象（类似 Java 的 `String` vs `StringBuilder`）：

> [字符串拼接对比](../code/practice/01_performance.py#L283-L308)

```python
{{#include ../code/practice/01_performance.py:283:308}}
```

| 写法 | Java 对应 | 性能 |
|------|-----------|------|
| `"".join(parts)` | `String.join` / `StringBuilder` | 快 |
| `s += "..."`（循环中） | `s += "..."`（循环中） | 慢，O(n²) |
| `f"{a}{b}"` | `String.format` | 快，推荐 |

### f-string vs format vs %

`f-string`（Python 3.6+）是最快的字符串格式化方式：

> [f-string 性能对比](../code/practice/01_performance.py#L311-L327)

```python
{{#include ../code/practice/01_performance.py:311:327}}
```

## 循环优化

### 列表推导式 vs for append

列表推导式比 `for` + `append` 快 20%-50%，因为减少了函数调用和属性查找：

> [列表推导式对比](../code/practice/01_performance.py#L359-L385)

```python
{{#include ../code/practice/01_performance.py:359:385}}
```

### map vs comprehension

`map` + `lambda` 通常比列表推导式慢（lambda 有调用开销），但 `map` + 内置函数可能更快：

> [map vs comprehension](../code/practice/01_performance.py#L359-L385)

```python
{{#include ../code/practice/01_performance.py:359:385}}
```

## 缓存策略：lru_cache

`functools.lru_cache` 实现 LRU 缓存，对应 Java 的 `Caffeine` / `Guava Cache`：

> [lru_cache 示例](../code/practice/01_performance.py#L442-L475)

```python
{{#include ../code/practice/01_performance.py:442:475}}
```

适用场景：
- 纯函数（相同输入相同输出）
- 计算开销大于缓存查找开销
- 参数可哈希（不可变类型）

> ⚠️ `lru_cache` 缓存的是**返回值**，如果返回可变对象，修改会污染缓存。

## 惰性求值：生成器 vs 列表

生成器不一次性生成所有结果，而是按需产出，对应 Java 的 `Stream`（惰性）vs `List`（即时）：

> [生成器 vs 列表](../code/practice/01_performance.py#L532-L551)

```python
{{#include ../code/practice/01_performance.py:532:551}}
```

| 特性 | 列表 | 生成器 | Java 对应 |
|------|------|--------|-----------|
| 内存 | 一次性分配 | 几乎不占 | `List` vs `Stream` |
| 多次遍历 | 支持 | 不支持 | `List` vs `Stream` |
| 索引访问 | O(1) | 不支持 | `List.get(i)` vs 需 `collect` |
| 适用场景 | 需多次访问/随机访问 | 一次遍历/大数据 | 同 |

## 函数调用开销：局部变量缓存

Python 函数调用有开销（参数传递、栈帧创建）。在热点循环中，把全局/属性查找缓存为局部变量：

> [局部变量缓存](../code/practice/01_performance.py#L625-L652)

```python
{{#include ../code/practice/01_performance.py:625:652}}
```

```python
# 慢：每次循环都做属性查找
for item in data:
    result.append(math.sqrt(item))

# 快：缓存为局部变量
append = result.append
sqrt = math.sqrt
for item in data:
    append(sqrt(item))
```

Java 中方法调用会被 JIT 内联优化，Python 没有 JIT（CPython），所以手动缓存更有效。

## 实战：优化慢函数的全过程

> [优化实战完整流程](../code/practice/01_performance.py#L654-L705)

```python
{{#include ../code/practice/01_performance.py:654:705}}
```

完整流程：
1. **用 cProfile 找瓶颈**：不要猜，用数据定位
2. **用 timeit 验证假设**：对比优化前后的微基准
3. **选对数据结构**：O(n) → O(1) 的提升最显著
4. **减少函数调用**：热点循环中缓存局部变量
5. **考虑缓存**：纯函数用 `lru_cache`
6. **考虑生成器**：大数据避免一次性加载
7. **最终验证**：cProfile 确认瓶颈已消除

## 小结

- **先测后优**：用 `cProfile` 找瓶颈，用 `timeit` 验证效果，不要盲目猜
- **数据结构是基础**：`set` 做成员判断，`deque` 做队列，`tuple` 做不可变
- **字符串用 `join` 和 `f-string`**：循环中不要用 `+`
- **列表推导式比 for append 快**：但不要牺牲可读性
- **`lru_cache` 缓存纯函数**：注意返回可变对象的陷阱
- **生成器省内存**：大数据场景用生成器替代列表
- **热点循环缓存局部变量**：Python 没有 JIT，手动优化更有效

> 📁 [查看完整代码](../code/practice/01_performance.py)
