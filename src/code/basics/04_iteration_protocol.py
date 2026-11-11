# -*- coding: utf-8 -*-
"""
04_iteration_protocol.py - 迭代协议、for-else 与切片协议

本文件面向有丰富 Java 经验的开发者，讲解 Python 迭代机制的三层协议：

    - 迭代协议      __iter__ / __next__ / StopIteration   ~ Java Iterator
    - 序列协议      __len__ / __getitem__（含切片）        ~ List/Collection
    - 控制流补充    for...else / while...else              ~ Java 无对应

为什么单独讲
------------
生成器章、异步迭代章都默认读者已经懂「迭代协议」，但 Java 的 Iterator 与
Python 的差异不小（最重要的两点：Python 的 for 自动调用 iter()，且异常
用 StopIteration 而非 hasNext 判断）。

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
"""

import sys

# =============================================================================
# 1. 迭代协议：__iter__ / __next__
# =============================================================================

def demo_iterator_protocol():
    """手写一个迭代器，理解 for 的展开过程。"""
    print("=== 1. 迭代协议 ===")

    class Countdown:
        """从 n 数到 1 的迭代器。"""

        def __init__(self, n: int):
            self.n = n

        def __iter__(self):
            # 返回迭代器对象本身
            return self

        def __next__(self):
            if self.n <= 0:
                # 关键：用异常表示结束，而不是返回 null
                raise StopIteration
            self.n -= 1
            return self.n + 1

    print(f"  list(Countdown(3)) = {list(Countdown(3))}")
    print("  for 循环等价于：")

    it = iter(Countdown(3))
    while True:
        try:
            value = next(it)
        except StopIteration:
            break
        print(f"    {value}")
    print("  [Java 对比] Java 用 hasNext() 返回 boolean 判断是否结束；"
          "Python 用 StopIteration 异常，所以 for 循环体不会看到它")


def demo_iterable_vs_iterator():
    """可迭代对象 vs 迭代器的区别。"""
    print("\n=== 2. 可迭代对象 vs 迭代器 ===")

    # 列表是可迭代对象，但不是迭代器
    data = [1, 2, 3]
    print(f"  list 有 __iter__: {hasattr(data, '__iter__')}")
    print(f"  list 有 __next__: {hasattr(data, '__next__')}   <- 不是迭代器")

    it = iter(data)
    print(f"  iter(list) 有 __next__: {hasattr(it, '__next__')}")
    print(f"  iter(data) is data: {iter(it) is it}   <- 迭代器的 __iter__ 返回自己")

    # 可迭代对象可以反复遍历，迭代器只能一次
    print(f"  list 遍历两次: {list(data)}, {list(data)}")
    print(f"  iter 遍历两次: {list(it)}, {list(it)}   <- 第二次为空")

    print("  [Java 对比] List 是可迭代的（用 iterator() 拿新的 Iterator），"
          "Iterator 也是耗尽的；分得同样清楚，只是 Python 的 for 直接吃可迭代对象")


def demo_generator_as_iterator():
    """生成器就是迭代器的语法糖。"""
    print("\n=== 3. 生成器 = 迭代器的语法糖 ===")

    def gen():
        yield 1
        yield 2
        yield 3

    g = gen()
    print(f"  g = gen()  ->  {type(g).__name__}")
    print(f"  有 __iter__/__next__: "
          f"{hasattr(g, '__iter__')}/{hasattr(g, '__next__')}")
    print(f"  逐个 next: {next(g)}, {next(g)}, {next(g)}")
    try:
        next(g)
    except StopIteration:
        print("  第四次 next -> StopIteration")
    print("  [要点] 手写迭代器的 99% 场景都可以用生成器替代")


# =============================================================================
# 2. for...else / while...else
# =============================================================================

def demo_for_else():
    """for-else：循环正常结束（没被 break）时执行 else。"""
    print("\n=== 4. for...else ===")

    def find_first_even(nums):
        for n in nums:
            if n % 2 == 0:
                print(f"    找到偶数 {n}，break")
                break
        else:
            # 没有 break 才会执行到这里
            print("    循环走完都没找到偶数")

    print("  [1, 2, 3]:")
    find_first_even([1, 2, 3])
    print("  [1, 3, 5]:")
    find_first_even([1, 3, 5])

    print("  [Java 对比] Java 需要在循环外加一个 boolean found 标志：")
    print("    boolean found = false;")
    print("    for (int n : nums) { if (n % 2 == 0) { found = true; break; } }")
    print("    if (!found) { ... }")
    print("  Python 的 else 就是省掉这个标志")


def demo_while_else():
    """while-else 同理。"""
    print("\n=== 5. while...else ===")

    n = 10
    while n > 0:
        n -= 1
        if n == 5:
            print(f"  n 减到 5，break")
            break
    else:
        print("  正常结束")

    n = 3
    while n > 0:
        n -= 1
    else:
        print(f"  n=3 循环正常结束（n 现在是 {n}）")

    print("  [要点] else 属于循环，不属于 if；缩进层级是 for/while 的同级")
    print("  [易错] 把 else 当成「循环没执行」是误解——空循环也会执行 else")


def demo_prime_example():
    """for-else 的经典用例：判定质数。"""
    print("\n=== 6. 经典用例：质数判定 ===")

    def is_prime(n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                break
        else:
            return True
        return False

    primes = [n for n in range(2, 30) if is_prime(n)]
    print(f"  2~29 的质数: {primes}")


# =============================================================================
# 3. 切片协议
# =============================================================================

def demo_slicing_basics():
    """切片基本语法与常见用法。"""
    print("\n=== 7. 切片基础 ===")

    s = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    print(f"  s          = {s}")
    print(f"  s[2:5]     = {s[2:5]}      <- [start, stop)")
    print(f"  s[:3]      = {s[:3]}")
    print(f"  s[7:]      = {s[7:]}")
    print(f"  s[::2]     = {s[::2]}      <- 步长 2")
    print(f"  s[::-1]    = {s[::-1]}      <- 反转")
    print(f"  s[-3:]     = {s[-3:]}      <- 负索引从末尾数")
    print(f"  s[1:-1]    = {s[1:-1]}")

    # 越界不报错（与 Java 不同）
    print(f"\n  s[5:100]   = {s[5:100]}   <- stop 越界不报错，自动截断")
    print(f"  s[100:]    = {s[100:]}        <- 空列表")
    try:
        s[100]
    except IndexError as exc:
        print(f"  s[100]     -> IndexError: {exc}   <- 单个索引越界会报错")

    print("  [Java 对比] Java 的 subList 越界抛 IndexOutOfBoundsException；"
          "Python 切片宽容地截断")


def demo_slice_object():
    """slice 对象与命名切片。"""
    print("\n=== 8. slice 对象 ===")

    s = list(range(10))
    sl = slice(2, 5)
    print(f"  slice(2, 5) -> {s[sl]}")

    # 负步长
    rev = slice(None, None, -1)
    print(f"  slice(None, None, -1) -> {s[rev]}")

    # 命名切片提升可读性
    HEADER = slice(0, 3)
    BODY = slice(3, 7)
    record = ["h1", "h2", "h3", "b1", "b2", "b3", "b4", "b5"]
    print(f"  HEADER={record[HEADER]}  BODY={record[BODY]}")
    print("  [Java 对比] Java 无 slice 对象，只能重复写 subList(0, 3)")


def demo_getitem_slicing():
    """自定义类支持切片。"""
    print("\n=== 9. 自定义类支持切片 ===")

    class Playlist:
        def __init__(self, songs):
            self._songs = list(songs)

        def __getitem__(self, index):
            # 索引和切片都走这里：切片时 index 是 slice 对象
            return self._songs[index]

        def __len__(self):
            return len(self._songs)

        def __iter__(self):
            return iter(self._songs)

    p = Playlist(["a", "b", "c", "d", "e"])
    print(f"  p[0]     = {p[0]}")
    print(f"  p[1:3]   = {p[1:3]}")
    print(f"  p[::-1]  = {p[::-1]}")
    print(f"  len(p)   = {len(p)}")
    print(f"  list(p)  = {list(p)}")

    # 只实现 __getitem__ 也能被 for 遍历
    class OnlyGetitem:
        def __getitem__(self, i):
            if i >= 3:
                raise IndexError
            return i * 10

    print(f"\n  只实现 __getitem__ 也能 for 遍历: {[x for x in OnlyGetitem()]}")
    print("  [要点] 旧式迭代协议：for 找不到 __iter__ 时会退化为 __getitem__(0..n)")
    print("  [Java 对比] Java 的切片和遍历都依赖接口，"
          "必须显式实现 Iterable/List")


def demo_slice_assignment():
    """切片赋值与删除。"""
    print("\n=== 10. 切片赋值 ===")

    s = list(range(8))
    print(f"  初始:           {s}")

    s[2:5] = ["a", "b"]
    print(f"  s[2:5] = a,b:   {s}   <- 长度可以不同")

    s[1:1] = ["inserted"]
    print(f"  s[1:1] 插入:    {s}")

    s[::2] = ["x"] * len(s[::2])
    print(f"  s[::2] 步长赋值: {s}")

    del s[1:3]
    print(f"  del s[1:3]:     {s}")
    print("  [Java 对比] Java 的 List 只能 add/remove/set 逐个操作，"
          "没有批量切片赋值")


# =============================================================================
# 4. 常见陷阱
# =============================================================================

def demo_pitfalls():
    """高频错误。"""
    print("\n=== 11. 常见陷阱 ===")

    # 坑 1：在迭代中修改容器
    print("  坑 1  迭代时修改容器")
    s = [1, 2, 3, 4]
    try:
        for x in s:
            if x == 2:
                s.remove(x)
    except RuntimeError as exc:
        print(f"         不会报错，但结果诡异: {s}（漏掉了 3）")
    print("         正确: for x in s[:]  或  s = [x for x in s if x != 2]")

    # 坑 2：切片是浅拷贝
    print("\n  坑 2  切片是浅拷贝")
    nested = [[1], [2]]
    copy = nested[:]
    copy[0].append(99)
    print(f"         原列表也被改了: {nested}")
    print("         深拷贝需要 copy.deepcopy")

    # 坑 3：反转字符串用切片最快，但反转范围需注意
    print("\n  坑 3  切片边界")
    print("         s[len(s):]  是空列表，不是最后一个元素")
    print("         s[-1:]      才是最后一个元素")

    # 坑 4：for-else 缩进错误
    print("\n  坑 4  else 缩进")
    print("         else 必须和 for 同级；如果误缩进到 if 里，语义完全改变")

    # 坑 5：迭代器耗尽后无提示
    print("\n  坑 5  迭代器耗尽后继续迭代不会报错，只是空")
    it = iter([1, 2])
    list(it)
    print(f"         耗尽后再 list: {list(it)}")


def print_java_mapping():
    print("\n=== 12. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("可迭代对象", "__iter__", "Iterable"),
        ("迭代器", "__iter__ + __next__", "Iterator"),
        ("结束标志", "raise StopIteration", "hasNext() == false"),
        ("循环结束检测", "for...else", "布尔标志位"),
        ("索引访问", "__getitem__", "get(int)"),
        ("切片", "obj[a:b:c]（__getitem__ 收 slice）", "subList / 循环"),
        ("长度", "__len__", "size()"),
        ("切片越界", "自动截断", "抛异常"),
        ("反转", "seq[::-1]", "Collections.reverse"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 62)
    print("迭代协议、for-else 与切片协议")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 62)

    demo_iterator_protocol()
    demo_iterable_vs_iterator()
    demo_generator_as_iterator()
    demo_for_else()
    demo_while_else()
    demo_prime_example()
    demo_slicing_basics()
    demo_slice_object()
    demo_getitem_slicing()
    demo_slice_assignment()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 62)
    print("所有 demo 运行完成！")
    print("=" * 62)


if __name__ == "__main__":
    main()
