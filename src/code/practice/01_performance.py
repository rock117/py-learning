# -*- coding: utf-8 -*-
"""
01_performance.py - Python 性能优化深入
=========================================

本文件演示 Python 性能优化的各种技巧，面向有丰富 Java 经验的开发者。

Java 对比要点：
- Java 有 JIT（HotSpot），Python 是解释执行（CPython），性能差距约 10-100 倍
- Java 性能分析常用 JMH / JProfiler / VisualVM，Python 用 cProfile / line_profiler / py-spy
- Java 字符串拼接编译器会优化成 StringBuilder，Python 中 + 拼接在循环里是 O(n^2)
- Java 的 HashMap 查找是 O(1)，Python 的 dict 同样是哈希表 O(1)

运行方式：python 01_performance.py
注意：Windows 控制台默认 GBK 编码，本文件避免在 print 中使用 emoji。
"""

import sys
import time
import timeit
import cProfile
import pstats
import io
import tracemalloc
from functools import lru_cache, partial
from collections import deque
from itertools import islice


# ============================================================
# 1. 性能分析工具链
# ============================================================

def demo_cprofile():
    """cProfile 分析函数调用耗时。

    Java 对比：类似 JProfiler 的方法调用统计，或 JMH 的 @State 注解分析。
    cProfile 是 Python 标准库，无需安装，统计每个函数的调用次数和累计耗时。
    """
    print("=== cProfile 分析 ===")

    def slow_sum(n):
        # 故意写一个低效的求和函数
        s = 0
        for i in range(n):
            s += i
        return s

    def slow_square_sum(n):
        # 故意写一个低效的平方和函数
        s = 0
        for i in range(n):
            s += i * i
        return s

    # 用 cProfile 分析一段代码
    profiler = cProfile.Profile()
    profiler.enable()
    slow_sum(100000)
    slow_square_sum(100000)
    profiler.disable()

    # 输出统计结果到字符串
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")  # 按累计耗时排序
    stats.print_stats(5)  # 只打印前 5 个
    print(stream.getvalue()[:500])
    print("[提示] ncalls=调用次数, tottime=函数自身耗时, cumtime=含子调用累计耗时")


def demo_timeit():
    """timeit 微基准测试。

    Java 对比：类似 JMH 的 @Benchmark，但更轻量。
    timeit 会多次执行以减少误差，默认执行 100 万次。
    """
    print("=== timeit 微基准测试 ===")

    # 对比两种列表创建方式
    t1 = timeit.timeit("list(range(100))", number=10000)
    t2 = timeit.timeit("[i for i in range(100)]", number=10000)

    print(f"list(range(100))        : {t1:.4f}s")
    print(f"[i for i in range(100)]  : {t2:.4f}s")
    print(f"差异: {abs(t1 - t2) / min(t1, t2) * 100:.1f}%")
    print("[提示] timeit 适合微基准测试，避免手写循环计时带来的误差")


def demo_tracemalloc():
    """tracemalloc 内存分配追踪。

    Java 对比：类似 JProfiler 的内存快照功能。
    tracemalloc 追踪 Python 对象的内存分配，帮助定位内存泄漏。
    """
    print("=== tracemalloc 内存分配追踪 ===")

    tracemalloc.start()

    # 分配一些内存
    data1 = [i * i for i in range(10000)]
    data2 = {i: i * i for i in range(10000)}

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    print("内存分配 Top 3（按行号）：")
    for stat in top_stats[:3]:
        print(f"  {stat}")

    tracemalloc.stop()
    print("[提示] tracemalloc 可定位到具体代码行的内存分配")


def demo_line_profiler_note():
    """line_profiler 逐行分析（在注释中说明安装方式）。

    line_profiler 是第三方工具，需要安装：
        pip install line_profiler

    使用方式：
        from line_profiler import profile  # 装饰器（新版）
        或在 IPython 中用 %lprun 魔法命令

    Java 对比：类似 JProfiler 的 "Line Profiling" 功能，精确到每一行。
    """
    print("=== line_profiler 逐行分析（说明） ===")
    print("line_profiler 是第三方工具：pip install line_profiler")
    print("它能统计函数内每一行的执行次数和耗时，非常精确。")
    print("Java 对比：JProfiler 的 Line Profiling 功能。")


def demo_pyspy_note():
    """py-spy 采样 profiler（在注释中说明）。

    py-spy 是采样式 profiler，无需修改代码，适合生产环境：
        pip install py-spy
        py-spy top --pid <PID>      # 实时查看
        py-spy record -o flame.svg --pid <PID>  # 生成火焰图

    Java 对比：类似 async-profiler，可生成火焰图，低开销。
    """
    print("=== py-spy 采样 profiler（说明） ===")
    print("py-spy 是采样式 profiler：pip install py-spy")
    print("特点：无需修改代码、开销低、可生成火焰图，适合生产环境。")
    print("Java 对比：async-profiler 生成火焰图。")


# ============================================================
# 2. 数据结构选择对性能的影响
# ============================================================

def demo_list_vs_tuple():
    """list vs tuple：创建速度、内存占用对比。

    Java 对比：Java 没有直接对应 tuple 的类型（Record 是 Java 14+ 的类似物）。
    tuple 不可变，创建比 list 快，内存占用更小。
    """
    print("=== list vs tuple ===")

    import sys

    # 创建速度对比
    t_list = timeit.timeit("list(range(1000))", number=10000)
    t_tuple = timeit.timeit("tuple(range(1000))", number=10000)
    print(f"创建 1000 元素 list 耗时: {t_list:.4f}s")
    print(f"创建 1000 元素 tuple 耗时: {t_tuple:.4f}s")

    # 内存占用对比
    a_list = list(range(1000))
    a_tuple = tuple(range(1000))
    print(f"list  内存: {sys.getsizeof(a_list)} bytes")
    print(f"tuple 内存: {sys.getsizeof(a_tuple)} bytes")
    print("[提示] tuple 不可变，无需预留扩容空间，内存更小")


def demo_list_vs_deque():
    """list vs deque：头部插入性能对比。

    Java 对比：Python deque 类似 Java 的 ArrayDeque / LinkedList。
    list 头部插入是 O(n)（要移动元素），deque 头部插入是 O(1)。
    """
    print("=== list vs deque 头部插入 ===")

    n = 50000

    # list 头部插入：O(n)
    lst = []
    t0 = time.perf_counter()
    for i in range(n):
        lst.insert(0, i)
    t_list = time.perf_counter() - t0

    # deque 头部插入：O(1)
    dq = deque()
    t0 = time.perf_counter()
    for i in range(n):
        dq.appendleft(i)
    t_deque = time.perf_counter() - t0

    print(f"list  头部插入 {n} 次: {t_list:.4f}s")
    print(f"deque 头部插入 {n} 次: {t_deque:.4f}s")
    print(f"deque 快约 {t_list / t_deque:.0f} 倍")
    print("[提示] 频繁在头部插入/删除，用 deque 而非 list")


def demo_set_vs_list_lookup():
    """set vs list：成员查找 O(1) vs O(n) 对比。

    Java 对比：Python set 类似 Java HashSet。
    set 查找是哈希表 O(1)，list 查找是线性扫描 O(n)。
    """
    print("=== set vs list 成员查找 ===")

    n = 100000
    data = list(range(n))
    data_set = set(data)
    target = n - 1  # 查找最后一个元素（对 list 最坏情况）

    # list 查找：O(n)
    t0 = time.perf_counter()
    _ = target in data
    t_list = time.perf_counter() - t0

    # set 查找：O(1)
    t0 = time.perf_counter()
    _ = target in data_set
    t_set = time.perf_counter() - t0

    print(f"list  查找 {n} 元素: {t_list * 1e6:.1f} us")
    print(f"set   查找 {n} 元素: {t_set * 1e6:.1f} us")
    print(f"set 快约 {t_list / t_set:.0f} 倍")
    print("[提示] 频繁成员查找，用 set")


def demo_dict_vs_list_lookup():
    """dict 查找 vs list 查找：大数据量对比。

    Java 对比：Python dict 类似 Java HashMap。
    """
    print("=== dict vs list 查找 ===")

    n = 100000
    keys = [f"key_{i}" for i in range(n)]
    values = list(range(n))
    mapping = dict(zip(keys, values))

    target_key = f"key_{n - 1}"

    # list 查找：需要遍历
    t0 = time.perf_counter()
    for k, v in zip(keys, values):
        if k == target_key:
            found = v
            break
    t_list = time.perf_counter() - t0

    # dict 查找：O(1)
    t0 = time.perf_counter()
    found = mapping[target_key]
    t_dict = time.perf_counter() - t0

    print(f"list 遍历查找: {t_list * 1e6:.1f} us")
    print(f"dict 直接查找: {t_dict * 1e6:.1f} us")
    print(f"dict 快约 {t_list / t_dict:.0f} 倍")


def demo_getsizeof_compare():
    """用 sys.getsizeof 对比不同数据结构内存。"""
    print("=== sys.getsizeof 内存对比 ===")
    items = list(range(100))
    print(f"list  100 元素: {sys.getsizeof(items)} bytes")
    print(f"tuple 100 元素: {sys.getsizeof(tuple(items))} bytes")
    print(f"set   100 元素: {sys.getsizeof(set(items))} bytes")
    print(f"dict  100 键值: {sys.getsizeof(dict(zip(items, items)))} bytes")
    print("[提示] set/dict 因哈希表结构，内存开销大于 list/tuple")


# ============================================================
# 3. 字符串操作优化
# ============================================================

def demo_string_concat():
    """+ 拼接 vs join（对比 Java StringBuilder）。

    Java 对比：Java 编译器会把 + 拼接优化成 StringBuilder.append()。
    Python 的 + 拼接在循环中每次创建新字符串，是 O(n^2)。
    """
    print("=== 字符串拼接 + vs join ===")

    parts = [str(i) for i in range(1000)]

    # 错误：循环中用 + 拼接，O(n^2)
    t0 = time.perf_counter()
    s = ""
    for p in parts:
        s += p
    t_plus = time.perf_counter() - t0

    # 正确：用 join，O(n)
    t0 = time.perf_counter()
    s2 = "".join(parts)
    t_join = time.perf_counter() - t0

    print(f"+ 拼接 1000 次: {t_plus * 1e6:.1f} us")
    print(f"join    1000 个: {t_join * 1e6:.1f} us")
    print(f"join 快约 {t_plus / t_join:.1f} 倍")
    print("[提示] Python 中 + 拼接在循环里是 O(n^2)，用 join")


def demo_string_format_compare():
    """f-string vs % vs format vs + 性能对比。"""
    print("=== 字符串格式化性能对比 ===")

    name, age = "Alice", 30
    n = 100000

    t_fstring = timeit.timeit(f'f"{{name}} is {{age}}"', globals={"name": name, "age": age}, number=n)
    t_percent = timeit.timeit('"%s is %d" % (name, age)', globals={"name": name, "age": age}, number=n)
    t_format = timeit.timeit('"{} is {}".format(name, age)', globals={"name": name, "age": age}, number=n)
    t_plus = timeit.timeit('name + " is " + str(age)', globals={"name": name, "age": age}, number=n)

    print(f"f-string : {t_fstring:.4f}s")
    print(f"% 格式化 : {t_percent:.4f}s")
    print(f".format  : {t_format:.4f}s")
    print(f"+ 拼接   : {t_plus:.4f}s")
    print("[提示] f-string 最快也最易读，推荐使用")


def demo_string_intern():
    """字符串驻留 intern 机制。

    Python 会自动驻留一些字符串（如标识符），相同内容指向同一对象。
    Java 对比：Java 有字符串常量池（String.intern()），机制类似。
    """
    print("=== 字符串驻留 intern ===")

    # 自动驻留：看起来像标识符的字符串
    a = "hello"
    b = "hello"
    print(f"a = 'hello', b = 'hello' -> a is b: {a is b}")  # True，自动驻留

    # 运行时构造的字符串不会自动驻留
    c = "hel" + "lo"  # 编译期常量折叠，仍可能驻留
    d = "".join(["hel", "lo"])  # 运行时拼接，不驻留
    print(f"c = 'hel'+'lo'   -> a is c: {a is c}")
    print(f"d = join(...)    -> a is d: {a is d}")

    # 手动 intern
    e = sys.intern("".join(["hel", "lo"]))
    print(f"e = intern(d)     -> a is e: {a is e}")
    print("[提示] intern 适合大量重复字符串场景，可节省内存并加速 == 比较")


# ============================================================
# 4. 循环与推导式优化
# ============================================================

def demo_comprehension_vs_loop():
    """for + append vs 列表推导式 vs map 性能对比。"""
    print("=== 推导式 vs 循环 vs map ===")

    n = 100000

    # for + append
    t0 = time.perf_counter()
    result1 = []
    for i in range(n):
        result1.append(i * i)
    t_loop = time.perf_counter() - t0

    # 列表推导式
    t0 = time.perf_counter()
    result2 = [i * i for i in range(n)]
    t_compr = time.perf_counter() - t0

    # map
    t0 = time.perf_counter()
    result3 = list(map(lambda i: i * i, range(n)))
    t_map = time.perf_counter() - t0

    print(f"for + append: {t_loop * 1e3:.2f} ms")
    print(f"列表推导式  : {t_compr * 1e3:.2f} ms")
    print(f"map        : {t_map * 1e3:.2f} ms")
    print("[提示] 列表推导式在 C 层执行，比 for+append 快")


def demo_nested_loop_optimization():
    """嵌套循环优化：用 dict 替代内层查找。"""
    print("=== 嵌套循环优化 ===")

    n = 1000
    items = list(range(n))
    lookup = {v: v * 2 for v in range(n)}

    # 低效：内层用 list.index 查找 O(n)，整体 O(n^2)
    t0 = time.perf_counter()
    result1 = []
    for a in items[:200]:
        idx = items.index(a)
        result1.append(lookup[items[idx]])
    t_slow = time.perf_counter() - t0

    # 高效：直接用 dict 查找 O(1)
    t0 = time.perf_counter()
    result2 = [lookup[a] for a in items[:200]]
    t_fast = time.perf_counter() - t0

    print(f"内层 list.index: {t_slow * 1e3:.2f} ms")
    print(f"直接 dict 查找 : {t_fast * 1e3:.2f} ms")
    print(f"快约 {t_slow / t_fast:.0f} 倍")


def demo_avoid_repeated_compute():
    """避免循环内重复计算。"""
    print("=== 避免循环内重复计算 ===")

    data = list(range(10000))

    # 低效：每次循环都调用 len
    t0 = time.perf_counter()
    result1 = []
    for i in data:
        result1.append(i * len(data))  # len(data) 重复计算
    t_slow = time.perf_counter() - t0

    # 高效：缓存到局部变量
    t0 = time.perf_counter()
    n = len(data)
    result2 = [i * n for i in data]
    t_fast = time.perf_counter() - t0

    print(f"循环内重复 len(): {t_slow * 1e3:.2f} ms")
    print(f"缓存到局部变量  : {t_fast * 1e3:.2f} ms")
    print("[提示] 循环内不变的计算应提到循环外")


# ============================================================
# 5. 缓存策略
# ============================================================

def demo_lru_cache():
    """lru_cache 效果演示。

    Java 对比：类似 Guava Cache / Caffeine，但更轻量。
    lru_cache 是装饰器，自动缓存函数结果。
    """
    print("=== lru_cache 效果 ===")

    call_count = 0

    @lru_cache(maxsize=128)
    def fib(n):
        nonlocal call_count
        call_count += 1
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    # 第一次计算
    call_count = 0
    t0 = time.perf_counter()
    result = fib(30)
    t_first = time.perf_counter() - t0
    print(f"fib(30) 首次计算: {t_first * 1e3:.2f} ms, 实际调用 {call_count} 次")

    # 第二次直接命中缓存
    call_count = 0
    t0 = time.perf_counter()
    result2 = fib(30)
    t_second = time.perf_counter() - t0
    print(f"fib(30) 缓存命中: {t_second * 1e6:.1f} us, 实际调用 {call_count} 次")

    print(f"缓存信息: {fib.cache_info()}")
    print("[提示] lru_cache 适合纯函数（相同输入相同输出）")


def demo_manual_cache_vs_lru():
    """手动缓存 vs lru_cache。"""
    print("=== 手动缓存 vs lru_cache ===")

    # 手动缓存
    manual_cache = {}

    def fib_manual(n):
        if n in manual_cache:
            return manual_cache[n]
        if n < 2:
            r = n
        else:
            r = fib_manual(n - 1) + fib_manual(n - 2)
        manual_cache[n] = r
        return r

    @lru_cache(maxsize=None)
    def fib_lru(n):
        if n < 2:
            return n
        return fib_lru(n - 1) + fib_lru(n - 2)

    t1 = timeit.timeit("fib_manual(30)", globals={"fib_manual": fib_manual}, number=100)
    t2 = timeit.timeit("fib_lru(30)", globals={"fib_lru": fib_lru}, number=100)
    print(f"手动缓存 100 次: {t1:.4f}s")
    print(f"lru_cache 100 次: {t2:.4f}s")
    print("[提示] lru_cache 用 C 实现，比手动 dict 缓存更快，且自带淘汰策略")


def demo_cache_invalidation():
    """缓存失效场景：可变参数或副作用导致缓存错误。"""
    print("=== 缓存失效场景 ===")

    @lru_cache(maxsize=128)
    def process_list(lst):
        # 注意：lru_cache 要求参数可哈希，list 不可哈希会报错
        return sum(lst)

    # list 不可哈希，需要转 tuple
    try:
        process_list([1, 2, 3])
    except TypeError as e:
        print(f"[警告] list 不可哈希: {e}")

    # 正确：用 tuple
    print(f"process_list((1,2,3)) = {process_list((1, 2, 3))}")
    print("[提示] lru_cache 要求参数可哈希，list/dict 需转 tuple/frozenset")


# ============================================================
# 6. 惰性求值
# ============================================================

def demo_generator_vs_list():
    """生成器 vs 列表内存与性能对比。

    Java 对比：Python 生成器类似 Java 的 Stream（惰性求值）。
    生成器不一次性生成所有元素，按需产出，节省内存。
    """
    print("=== 生成器 vs 列表 ===")

    # 列表：一次性分配所有内存
    big_list = [i * i for i in range(1000000)]
    list_mem = sys.getsizeof(big_list)

    # 生成器：几乎不占内存
    big_gen = (i * i for i in range(1000000))
    gen_mem = sys.getsizeof(big_gen)

    print(f"100万元素 list 内存: {list_mem / 1024 / 1024:.1f} MB")
    print(f"生成器内存        : {gen_mem} bytes")
    print(f"内存节省约 {list_mem / gen_mem:.0f} 倍")
    print("[提示] 大数据量优先用生成器，按需计算")


def demo_islice():
    """itertools.islice 处理大数据。"""
    print("=== itertools.islice 处理大数据 ===")

    # 无限生成器
    def natural_numbers():
        i = 0
        while True:
            yield i
            i += 1

    # 用 islice 取前 5 个，无需生成全部
    first_five = list(islice(natural_numbers(), 5))
    print(f"无限生成器前 5 个: {first_five}")

    # 跳过前 3 个，取接下来 3 个
    skipped = list(islice(natural_numbers(), 3, 6))
    print(f"跳过 3 取 3 个   : {skipped}")
    print("[提示] islice 让生成器支持切片语义，适合流式处理")


# ============================================================
# 7. 函数调用开销
# ============================================================

def demo_function_call_overhead():
    """函数调用 vs 内联。"""
    print("=== 函数调用开销 ===")

    n = 1000000

    # 函数调用
    def square(x):
        return x * x

    t0 = time.perf_counter()
    for i in range(n):
        square(i)
    t_call = time.perf_counter() - t0

    # 内联
    t0 = time.perf_counter()
    for i in range(n):
        i * i
    t_inline = time.perf_counter() - t0

    print(f"函数调用 {n} 次: {t_call * 1e3:.2f} ms")
    print(f"内联     {n} 次: {t_inline * 1e3:.2f} ms")
    print(f"函数调用开销约 {(t_call - t_inline) / n * 1e9:.1f} ns/次")
    print("[提示] Python 函数调用有开销，热点路径可考虑内联或用内置函数")


def demo_functools_partial():
    """functools.partial 偏函数。

    Java 对比：类似 Java 的柯里化或 lambda 固定参数。
    """
    print("=== functools.partial ===")

    def power(base, exponent):
        return base ** exponent

    # 固定 exponent 参数
    square = partial(power, exponent=2)
    cube = partial(power, exponent=3)

    print(f"square(4) = {square(4)}")
    print(f"cube(3)   = {cube(3)}")
    print("[提示] partial 用于固定部分参数，创建专用函数")


def demo_local_variable_cache():
    """局部变量缓存全局/属性查找。"""
    print("=== 局部变量缓存 ===")

    n = 1000000

    # 每次循环都做全局查找
    global_func = len
    t0 = time.perf_counter()
    for i in range(n):
        global_func([1, 2, 3])
    t_global = time.perf_counter() - t0

    # 缓存到局部变量
    local_func = len
    t0 = time.perf_counter()
    for i in range(n):
        local_func([1, 2, 3])
    t_local = time.perf_counter() - t0

    print(f"全局查找 {n} 次: {t_global * 1e3:.2f} ms")
    print(f"局部缓存 {n} 次: {t_local * 1e3:.2f} ms")
    print("[提示] 热点循环中将全局/属性查找缓存到局部变量可提速")


# ============================================================
# 8. 实战：优化一个慢函数
# ============================================================

def demo_optimize_slow_function():
    """实战：给一个低效函数做 profiling -> 定位瓶颈 -> 逐步优化 -> 对比前后性能。"""
    print("=== 实战：优化慢函数 ===")

    # ---- 原始低效版本 ----
    def find_pairs_slow(numbers, target):
        """找出所有和为 target 的数对。O(n^2) 暴力法。"""
        pairs = []
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                if numbers[i] + numbers[j] == target:
                    pairs.append((numbers[i], numbers[j]))
        return pairs

    # ---- 优化版本：用 dict 一次遍历 ----
    def find_pairs_fast(numbers, target):
        """用哈希表优化到 O(n)。"""
        seen = set()
        pairs = []
        for num in numbers:
            complement = target - num
            if complement in seen:
                pairs.append((complement, num))
            seen.add(num)
        return pairs

    data = list(range(2000))
    target = 1999

    # 对比正确性
    r_slow = find_pairs_slow(data, target)
    r_fast = find_pairs_fast(data, target)
    assert len(r_slow) == len(r_fast), "结果数量不一致"

    # 对比性能
    t0 = time.perf_counter()
    find_pairs_slow(data, target)
    t_slow = time.perf_counter() - t0

    t0 = time.perf_counter()
    find_pairs_fast(data, target)
    t_fast = time.perf_counter() - t0

    print(f"原始 O(n^2) 版本: {t_slow * 1e3:.2f} ms")
    print(f"优化 O(n)   版本: {t_fast * 1e3:.2f} ms")
    print(f"优化后快约 {t_slow / t_fast:.0f} 倍")
    print("[总结] 优化步骤：1.profiling 定位 -> 2.分析算法复杂度 -> 3.用哈希表降复杂度 -> 4.验证正确性")


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print("Python 性能优化深入 - 面向 Java 开发者")
    print("=" * 60)
    print()

    demos = [
        ("性能分析工具链", [
            demo_cprofile,
            demo_timeit,
            demo_tracemalloc,
            demo_line_profiler_note,
            demo_pyspy_note,
        ]),
        ("数据结构选择", [
            demo_list_vs_tuple,
            demo_list_vs_deque,
            demo_set_vs_list_lookup,
            demo_dict_vs_list_lookup,
            demo_getsizeof_compare,
        ]),
        ("字符串操作优化", [
            demo_string_concat,
            demo_string_format_compare,
            demo_string_intern,
        ]),
        ("循环与推导式优化", [
            demo_comprehension_vs_loop,
            demo_nested_loop_optimization,
            demo_avoid_repeated_compute,
        ]),
        ("缓存策略", [
            demo_lru_cache,
            demo_manual_cache_vs_lru,
            demo_cache_invalidation,
        ]),
        ("惰性求值", [
            demo_generator_vs_list,
            demo_islice,
        ]),
        ("函数调用开销", [
            demo_function_call_overhead,
            demo_functools_partial,
            demo_local_variable_cache,
        ]),
        ("实战优化", [
            demo_optimize_slow_function,
        ]),
    ]

    for section, funcs in demos:
        print()
        print("# " + "=" * 56)
        print(f"# {section}")
        print("# " + "=" * 56)
        for func in funcs:
            print()
            func()

    print()
    print("=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
