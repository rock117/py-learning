# -*- coding: utf-8 -*-
"""
06_memory_perf.py - 内存与性能
==============================

本文件演示 Python 的内存管理与性能分析工具。
面向有丰富 Java 经验的开发者。

Java 对比：
- Java 用 JVM GC（分代回收、G1/ZGC 等），对象在堆上，引用可达性分析。
- Python 用引用计数 + 分代 GC，循环引用靠 GC 模块处理。
- Python 对象内存开销比 Java 大（每个对象有 __dict__ 等元数据）。
"""

import sys
import gc
import weakref
import timeit
import cProfile
import tracemalloc
from typing import List, Generator


# ============================================================================
# 1. 引用计数 + 分代 GC
# ============================================================================

class Trackable:
    """用于跟踪对象生命周期。"""
    def __init__(self, name: str) -> None:
        self.name = name
        print(f"  创建 {self.name}")

    def __del__(self) -> None:
        print(f"  销毁 {self.name}")


def demo_ref_count() -> None:
    """演示引用计数。

    Python 主要靠引用计数回收对象：引用归零立即回收。
    循环引用无法靠引用计数解决，需要分代 GC。

    Java 对比：Java 不用引用计数，靠 GC 可达性分析批量回收。
    """
    print("=== 引用计数 ===")
    obj = Trackable("A")
    print(f"  refcount = {sys.getrefcount(obj)}")  # 至少 2（obj + getrefcount 参数）

    ref2 = obj
    print(f"  加一个引用后 refcount = {sys.getrefcount(obj)}")

    del obj
    print("  删除 obj 后")
    del ref2  # 引用归零，触发 __del__
    print("  （已销毁）")


def demo_cycle_gc() -> None:
    """演示循环引用与分代 GC。"""
    print("\n=== 循环引用与 GC ===")

    class Node:
        def __init__(self, name: str) -> None:
            self.name = name
            self.partner: "Node" = None

    a = Node("A")
    b = Node("B")
    a.partner = b  # 循环引用
    b.partner = a
    print("  创建循环引用 a <-> b")

    del a
    del b
    # 此时引用计数不为零（互相引用），但已不可达
    print("  删除 a, b 后，引用计数非零（循环引用）")
    print(f"  手动 gc.collect() 回收: {gc.collect()} 个对象")
    # gc 模块检测循环引用并回收


# ============================================================================
# 2. 弱引用 weakref（对比 WeakReference）
# ============================================================================

def demo_weakref() -> None:
    """演示弱引用。

    弱引用不增加引用计数，对象可被回收。
    Java 对比：java.lang.ref.WeakReference / WeakHashMap。
    常用于缓存、观察者模式。
    """
    print("\n=== weakref 弱引用 ===")

    class BigObject:
        def __init__(self, data: str) -> None:
            self.data = data

    obj = BigObject("important data")
    ref = weakref.ref(obj)  # 创建弱引用

    print(f"  弱引用指向: {ref().data if ref() else None}")
    del obj  # 强引用删除，对象被回收
    print(f"  删除强引用后弱引用: {ref()}")  # None

    # WeakValueDictionary / WeakKeyDictionary
    cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
    temp = BigObject("cached")
    cache["key"] = temp
    print(f"  缓存存在: {'key' in cache}")
    del temp
    print(f"  删除后缓存: {'key' in cache}")  # False，被回收


# ============================================================================
# 3. gc 模块手动控制
# ============================================================================

def demo_gc_control() -> None:
    """演示 gc 模块手动控制。

    Java 对比：Java GC 是自动的，System.gc() 只是建议。
    Python 的 gc 模块可以禁用、手动触发、查看统计。
    """
    print("\n=== gc 模块 ===")
    print(f"  当前阈值: {gc.get_threshold()}")  # (700, 10, 10) 分代阈值
    print(f"  当前统计: {gc.get_stats()}")

    # 禁用 GC（慎用）
    gc.disable()
    print("  GC 已禁用")
    gc.enable()
    print("  GC 已启用")

    # 手动回收
    collected = gc.collect()
    print(f"  手动回收 {collected} 个对象")


# ============================================================================
# 4. __slots__ 内存优化效果对比
# ============================================================================

class PointDict:
    """普通类，用 __dict__。"""
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class PointSlots:
    """用 __slots__，省内存。"""
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


def demo_slots_memory() -> None:
    """演示 __slots__ 内存优化。

    __slots__ 省去 __dict__，每个对象省约 100+ 字节。
    大量对象时效果显著。
    """
    print("\n=== __slots__ 内存对比 ===")
    p1 = PointDict(1.0, 2.0)
    p2 = PointSlots(1.0, 2.0)
    print(f"  PointDict 对象大小: {sys.getsizeof(p1)} bytes")
    print(f"  PointSlots 对象大小: {sys.getsizeof(p2)} bytes")

    # 批量对比
    count = 100000
    dict_list = [PointDict(i, i) for i in range(count)]
    slots_list = [PointSlots(i, i) for i in range(count)]

    # 用 tracemalloc 精确测量
    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()
    del dict_list
    del slots_list
    gc.collect()

    dict_list2 = [PointDict(i, i) for i in range(count)]
    snapshot2 = tracemalloc.take_snapshot()
    stats2 = snapshot2.compare_to(snapshot1, "lineno")
    for stat in stats2[:3]:
        print(f"  PointDict x{count}: {stat}")

    del dict_list2
    gc.collect()

    slots_list2 = [PointSlots(i, i) for i in range(count)]
    snapshot3 = tracemalloc.take_snapshot()
    stats3 = snapshot3.compare_to(snapshot2, "lineno")
    for stat in stats3[:3]:
        print(f"  PointSlots x{count}: {stat}")

    del slots_list2
    tracemalloc.stop()


# ============================================================================
# 5. tracemalloc 内存追踪
# ============================================================================

def demo_tracemalloc() -> None:
    """演示 tracemalloc 追踪内存分配。"""
    print("\n=== tracemalloc ===")
    tracemalloc.start()

    # 模拟内存分配
    data1 = [list(range(100)) for _ in range(100)]
    data2 = {f"key_{i}": f"value_{i}" * 10 for i in range(100)}

    snapshot = tracemalloc.take_snapshot()
    top = snapshot.statistics("lineno")
    print("  内存分配 Top 3:")
    for stat in top[:3]:
        print(f"    {stat}")

    del data1, data2
    tracemalloc.stop()


# ============================================================================
# 6. cProfile / timeit 性能分析
# ============================================================================

def slow_function() -> int:
    """一个慢函数，用于 profile。"""
    total = 0
    for i in range(100000):
        total += i ** 2
    return total


def fast_function() -> int:
    """用列表推导式，更快。"""
    return sum(i ** 2 for i in range(100000))


def demo_cprofile() -> None:
    """演示 cProfile 性能分析。

    Java 对比：类似 JProfiler / VisualVM / async-profiler。
    """
    print("\n=== cProfile ===")
    profiler = cProfile.Profile()
    profiler.enable()
    slow_function()
    fast_function()
    profiler.disable()

    # 打印统计
    import io
    import pstats
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(5)
    print(stream.getvalue())


def demo_timeit() -> None:
    """演示 timeit 精确计时。

    Java 对比：类似 JMH（Java Microbenchmark Harness）。
    """
    print("=== timeit ===")
    # 测量慢函数
    t1 = timeit.timeit(slow_function, number=10)
    t2 = timeit.timeit(fast_function, number=10)
    print(f"  slow_function x10: {t1:.4f}s")
    print(f"  fast_function x10: {t2:.4f}s")
    print(f"  快 {t1 / t2:.2f}x")


# ============================================================================
# 7. 列表 vs 生成器内存对比
# ============================================================================

def demo_list_vs_generator() -> None:
    """演示列表 vs 生成器的内存差异。"""
    print("\n=== 列表 vs 生成器 ===")

    # 列表：一次性分配所有内存
    big_list = [i ** 2 for i in range(1000000)]
    list_size = sys.getsizeof(big_list)
    print(f"  列表 100万元素: {list_size / 1024 / 1024:.2f} MB")

    # 生成器：几乎不占内存
    big_gen = (i ** 2 for i in range(1000000))
    gen_size = sys.getsizeof(big_gen)
    print(f"  生成器 100万元素: {gen_size} bytes")

    # 求和对比（结果相同）
    list_sum = sum(big_list)
    gen_sum = sum(big_gen)
    print(f"  列表求和 = {list_sum}")
    print(f"  生成器求和 = {gen_sum}")
    print(f"  生成器内存节省: {list_size / gen_size:.0f}x")


# ============================================================================
# 8. 实战：优化内存密集场景
# ============================================================================

def demo_optimization() -> None:
    """实战：优化读取大量数据的场景。"""
    print("\n=== 实战：内存优化 ===")

    # 场景：处理 100 万条记录，每条是 (id, name) 元组

    # 方式1：全部加载到列表（高内存）
    tracemalloc.start()
    records_list = [(i, f"name_{i}") for i in range(500000)]
    _, peak1 = tracemalloc.get_traced_memory()
    print(f"  列表方式峰值内存: {peak1 / 1024 / 1024:.2f} MB")
    del records_list
    gc.collect()

    # 方式2：用生成器逐条处理（低内存）
    def record_gen(n: int) -> Generator[tuple, None, None]:
        for i in range(n):
            yield (i, f"name_{i}")

    # 只保留处理结果，不保留原始数据
    result = sum(r[0] for r in record_gen(500000))
    _, peak2 = tracemalloc.get_traced_memory()
    print(f"  生成器方式峰值内存: {peak2 / 1024 / 1024:.2f} MB")
    print(f"  结果: {result}")

    tracemalloc.stop()
    print("  结论：大数据集用生成器逐条处理，避免一次性加载。")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_ref_count()
    demo_cycle_gc()
    demo_weakref()
    demo_gc_control()
    demo_slots_memory()
    demo_tracemalloc()
    demo_cprofile()
    demo_timeit()
    demo_list_vs_generator()
    demo_optimization()
    print("\n所有内存与性能示例运行完毕。")
