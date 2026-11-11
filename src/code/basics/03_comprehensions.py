# -*- coding: utf-8 -*-
"""
03_comprehensions.py - 推导式与生成器表达式全集

本文件面向有丰富 Java 经验的开发者，系统讲解 Python 推导式（comprehension）。
它是 Java Stream API 的语法级替代，但更短，且语义有几处关键差异：

    - 列表推导式   [f(x) for x in seq if cond]      ~ stream().map().filter().toList()
    - 字典推导式   {k(x): v(x) for x in seq}         ~ Collectors.toMap
    - 集合推导式   {f(x) for x in seq}               ~ Collectors.toSet
    - 生成器表达式 (f(x) for x in seq)               ~ 惰性 Stream，不落盘

关键差异（Java 开发者最容易错的地方）
--------------------------------------
1. 变量作用域：Python 3 的推导式有自己的作用域，循环变量不会泄漏到外面；
   Java 的 lambda 参数同理不会泄漏，但 for 循环会。
2. 求值时机：生成器表达式是惰性的，只遍历一次；列表推导式立即全部求值。
3. 顺序：嵌套推导式的 for 顺序和嵌套 for 循环一致，从外到内书写。
4. 性能：推导式比 for + append 快，因为循环体在 C 层执行。

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
"""

import sys


# =============================================================================
# 1. 四种推导式
# =============================================================================

def demo_list_comprehension():
    """列表推导式：最常用的一种。"""
    print("=== 1. 列表推导式 ===")

    nums = [1, 2, 3, 4, 5, 6]

    # 基本形式：[表达式 for 变量 in 可迭代对象]
    squares = [n * n for n in nums]
    print(f"  平方:        {squares}")

    # 带条件过滤
    evens = [n for n in nums if n % 2 == 0]
    print(f"  偶数:        {evens}")

    # 表达式里做三元运算（不是过滤）
    labels = ["even" if n % 2 == 0 else "odd" for n in nums]
    print(f"  三元:        {labels}")

    # 多个条件
    both = [n for n in nums if n % 2 == 0 if n > 2]
    print(f"  多条件:      {both}          <- 等价于 n % 2 == 0 and n > 2")

    # 嵌套循环：等价于 for a ... for b ...
    pairs = [(a, b) for a in (1, 2) for b in ("x", "y")]
    print(f"  嵌套循环:    {pairs}")

    print("  [Java 对比] 等价于")
    print("    nums.stream().map(n -> n * n).collect(Collectors.toList())")


def demo_dict_set_comprehension():
    """字典与集合推导式。"""
    print("\n=== 2. 字典 / 集合推导式 ===")

    words = ["apple", "banana", "cherry"]

    # 字典推导式：{键表达式: 值表达式 for ...}
    lengths = {w: len(w) for w in words}
    print(f"  字典推导: {lengths}")

    # 交换键值
    inverted = {v: k for k, v in lengths.items()}
    print(f"  键值反转: {inverted}")

    # 带条件
    long_only = {w: len(w) for w in words if len(w) > 5}
    print(f"  过滤:     {long_only}")

    # 集合推导式：自动去重
    letters = {c for w in words for c in w}
    print(f"  集合推导: {sorted(letters)}")

    print("  [Java 对比] Collectors.toMap 需要处理键冲突；"
          "Python 后出现的同名键直接覆盖")


def demo_generator_expression():
    """生成器表达式：惰性求值。"""
    print("\n=== 3. 生成器表达式 ===")

    nums = range(1, 6)

    # 括号形式，不立即计算
    gen = (n * n for n in nums)
    print(f"  创建: {gen}")
    print("  此时还没有任何计算发生")

    print(f"  第一次迭代: {list(gen)}")
    print(f"  第二次迭代: {list(gen)}   <- 已耗尽，空列表")

    # 可以省一层括号，作为函数唯一参数时
    total = sum(n * n for n in nums)
    print(f"  作为参数: sum(n*n for n in nums) = {total}")

    # 内存对比
    import tracemalloc
    tracemalloc.start()
    big_list = [n for n in range(100_000)]
    list_mem = tracemalloc.get_traced_memory()[0]
    tracemalloc.reset_peak()
    tracemalloc.stop()

    tracemalloc.start()
    big_gen = (n for n in range(100_000))
    gen_mem = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    print(f"\n  100000 元素的列表推导内存: {list_mem / 1024:.0f} KB")
    print(f"  同规模生成器表达式内存:   {gen_mem / 1024:.1f} KB")
    print(f"  节省约 {list_mem / max(gen_mem, 1):.0f} 倍")
    print("  [Java 对比] 对应 Stream 的惰性求值，"
          "但 Java Stream 只能消费一次的限制也一样")


# =============================================================================
# 2. 作用域与语义
# =============================================================================

def demo_scope():
    """推导式的变量作用域（Python 3 的重要变化）。"""
    print("\n=== 4. 变量作用域 ===")

    x = "outer"
    _ = [x for x in range(3)]
    print(f"  推导式外 x = {x!r}   <- 未被泄漏/覆盖")

    # 对比 for 循环：会覆盖
    y = "outer"
    for y in range(3):
        pass
    print(f"  for 循环外 y = {y}   <- 被最后一次迭代覆盖")

    print("  [Python 2 差异] 2.x 的列表推导式会泄漏变量，3.x 已不泄漏")
    print("  [Java 对比] lambda 参数不泄漏，for 循环变量作用域也不同")


def demo_nested_order():
    """嵌套推导式的顺序。"""
    print("\n=== 5. 嵌套推导式：for 的书写顺序 ===")

    matrix = [[1, 2, 3], [4, 5, 6]]

    # 按行遍历
    row_major = [v for row in matrix for v in row]
    print(f"  展平（外→内）: {row_major}")

    # 等价写法
    manual = []
    for row in matrix:
        for v in row:
            manual.append(v)
    print(f"  等价的循环:    {manual}")

    # 转置：注意顺序是 for j ... for i ...
    transposed = [[matrix[i][j] for i in range(len(matrix))]
                  for j in range(len(matrix[0]))]
    print(f"  转置:          {transposed}")

    print("  [要点] 多个 for 子句按【从左到右】等同于【从外到内】的嵌套循环")
    print("  [Java 对比] flatMap 相当于展平，但嵌套顺序要自己控制")


def demo_performance():
    """推导式 vs 循环 vs map 的性能。"""
    print("\n=== 6. 性能对比 ===")
    import time

    n = 500_000
    data = list(range(n))

    t0 = time.perf_counter()
    a = []
    for x in data:
        a.append(x * 2)
    t_loop = time.perf_counter() - t0

    t0 = time.perf_counter()
    b = [x * 2 for x in data]
    t_comp = time.perf_counter() - t0

    t0 = time.perf_counter()
    c = list(map(lambda x: x * 2, data))
    t_map = time.perf_counter() - t0

    print(f"  for + append : {t_loop * 1000:6.1f} ms")
    print(f"  列表推导式    : {t_comp * 1000:6.1f} ms   ({t_loop / t_comp:.2f}x)")
    print(f"  map + lambda : {t_map * 1000:6.1f} ms   ({t_loop / t_map:.2f}x)")
    print(f"  结果一致: {a == b == c}")
    print("  [要点] 简单变换优先推导式；已有具名函数时 map 也很快；"
          "lambda 有调用开销")


# =============================================================================
# 3. 常见陷阱
# =============================================================================

def demo_pitfalls():
    """推导式的高频错误。"""
    print("\n=== 7. 常见陷阱 ===")

    # 坑 1：用推导式做副作用
    print("  坑 1  用推导式做副作用（反模式）")
    print("         [print(x) for x in range(3)]  <- 只为调用 print，"
          "却构造了无用列表")
    print("         正确: for x in range(3): print(x)")

    # 坑 2：嵌套推导式超过两层可读性骤降
    print("\n  坑 2  层数过多")
    print("         [x for a in A for b in a for x in b if x > 0]  <- 已经难读")
    print("         超过两层建议拆成普通循环，可读性优先")

    # 坑 3：生成器表达式只可消费一次
    print("\n  坑 3  生成器只可消费一次")
    gen = (x for x in range(3))
    first = list(gen)
    second = list(gen)
    print(f"         第一次: {first}   第二次: {second}")

    # 坑 4：推导式里的闭包延迟绑定
    print("\n  坑 4  推导式里嵌套 lambda 的延迟绑定")
    funcs_bad = [lambda: i for i in range(3)]
    print(f"         [lambda: i for i in range(3)] 调用结果: "
          f"{[f() for f in funcs_bad]}   <- 全是 2")
    print("         正确: [lambda i=i: i for i in range(3)]")
    funcs_ok = [lambda i=i: i for i in range(3)]
    print(f"         结果: {[f() for f in funcs_ok]}")

    print("  [Java 对比] Java 的 lambda 捕获的是 effectively final 的变量，"
          "不存在这个问题；Python 是延迟绑定")


def print_java_mapping():
    print("\n=== 8. Java 对照总表 ===")
    rows = [
        ("需求", "Python 推导式", "Java Stream"),
        ("映射", "[f(x) for x in s]", "s.map(f).toList()"),
        ("过滤", "[x for x in s if p(x)]", "s.filter(p).toList()"),
        ("映射+过滤", "[f(x) for x in s if p(x)]", "s.filter(p).map(f).toList()"),
        ("转字典", "{k(x): v(x) for x in s}", "Collectors.toMap"),
        ("转集合", "{f(x) for x in s}", "Collectors.toSet"),
        ("展平", "[y for x in s for y in x]", "s.flatMap(Collection::stream)"),
        ("惰性", "(f(x) for x in s)", "s.map(f)（未收集）"),
        ("求和", "sum(f(x) for x in s)", "s.mapToInt(f).sum()"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 62)
    print("推导式与生成器表达式全集")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 62)

    demo_list_comprehension()
    demo_dict_set_comprehension()
    demo_generator_expression()
    demo_scope()
    demo_nested_order()
    demo_performance()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 62)
    print("所有 demo 运行完成！")
    print("=" * 62)


if __name__ == "__main__":
    main()
