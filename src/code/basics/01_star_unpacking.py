# -*- coding: utf-8 -*-
"""
01_star_unpacking.py - 星号解包：`*` 与 `**` 的完整用法

本文件面向有丰富 Java 经验的开发者，讲透 Python 星号（asterisk）的四种用法。
Java 的 varargs 只覆盖了其中一种，其余三种在 Java 里没有对应语法。

四种用法速览
------------
1. 调用时展开位置参数   f(*seq)
2. 调用时展开关键字参数 f(**mapping)
3. 定义时收集参数       def f(*args, **kwargs)
4. 字面量解包           [*a, *b] / (*a, *b) / {*a, *b} / {**d1, **d2}

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       全部使用标准库，无需额外安装。
"""

import sys


# =============================================================================
# 1. 调用时展开位置参数：f(*seq)
# =============================================================================
# [Java 对比] 大致相当于把数组传给 Object... 形参，但 Python 不要求
#             目标函数是可变参数，任何位置的普通形参都能被 * 填充。

def demo_call_unpack_positional():
    """`*` 在调用处展开任意可迭代对象。"""
    print("=== 1. 调用时展开位置参数 f(*seq) ===")

    def channel_of(analysis_session_id, stream_id, media_timeline_id):
        return f"ch-{analysis_session_id}-{stream_id}-{media_timeline_id}"

    identities = (1, 2, 3)
    print(f"  元组解包: channel_of(*{identities}) = {channel_of(*identities)}")

    # 不限于元组：list / range / set / 生成器 都可以
    print(f"  列表:     channel_of(*[4, 5, 6]) = {channel_of(*[4, 5, 6])}")
    print(f"  range:    channel_of(*range(3)) = {channel_of(*range(3))}")
    print(f"  生成器:   channel_of(*(x for x in (7, 8, 9))) = "
          f"{channel_of(*(x for x in (7, 8, 9)))}")

    # 与普通参数混用：先写普通参数，*seq 补足剩余位置
    def f(x, y, z):
        return (x, y, z)

    print(f"  混用:     f(0, *(1, 2)) = {f(0, *(1, 2))}")
    # 多个 * 可以连用（3.5+）
    print(f"  连用:     f(*(0,), *(1,), *(2,)) = {f(*(0,), *(1,), *(2,))}")

    print("  [对比] 不传 * 时 channel_of(identities) 会把整个元组当成第一个参数"
          " -> TypeError")
    print("  [Java 对比] Java 只有 `void f(Object...` 这种形参才能接收展开的数组，"
          "且语法上直接传数组即可；Python 必须显式写 *")


def demo_call_unpack_keywords():
    """`**` 在调用处展开字典为关键字参数。"""
    print("\n=== 2. 调用时展开关键字参数 f(**mapping) ===")

    def create_user(name, age, city="Unknown"):
        return f"{name}/{age}/{city}"

    params = {"name": "Alice", "age": 30}
    print(f"  正常展开: {create_user(**params)}")
    print(f"  混合写法: {create_user(city='Beijing', **params)}")

    # 未知键会报错
    try:
        create_user(**{"name": "Bob", "age": 25, "nickname": "x"})
    except TypeError as exc:
        print(f"  多余关键字 -> TypeError: {exc}")

    # 与位置参数重复会报错
    try:
        create_user("Alice", **{"name": "Bob", "age": 25})
    except TypeError as exc:
        print(f"  参数重复   -> TypeError: {exc}")

    print("  [Java 对比] Java 完全没有对应语法；"
          "最接近的是 Map + 反射 Method.invoke，但类型不安全")


def demo_call_unpack_mixed():
    """位置展开与关键字展开组合，模拟「转发任意参数」。"""
    print("\n=== 3. 位置 + 关键字混合转发 ===")

    def target(a, b, c=None, d=None):
        return {"a": a, "b": b, "c": c, "d": d}

    def wrapper(*args, **kwargs):
        # 装饰器的标准写法：原样转发所有参数
        return target(*args, **kwargs)

    print(f"  wrapper(1, 2, c=3, d=4) = {wrapper(1, 2, c=3, d=4)}")
    print(f"  wrapper(*(1, 2), **{{'d': 9}}) = {wrapper(*(1, 2), **{'d': 9})}")
    print("  [要点] wrapper(*args, **kwargs) 会丢失函数签名，"
          "现代写法配合 functools.wraps + ParamSpec 保留类型信息")


# =============================================================================
# 2. 定义时收集参数：def f(*args, **kwargs)
# =============================================================================
# [Java 对比] *args 对应 Java 的 Object... args（收成 tuple，不可变）；
#             **kwargs 的「收集关键字参数」在 Java 中无对应物。

def demo_def_collect():
    """定义处的 `*` / `**` 做收集，与调用处语义正好相反。"""
    print("\n=== 4. 定义时收集参数 ===")

    def show(*args, **kwargs):
        print(f"    args   type={type(args).__name__:<6} value={args}")
        print(f"    kwargs type={type(kwargs).__name__:<6} value={kwargs}")

    print("  show(1, 2, 3):")
    show(1, 2, 3)
    print("  show(x=1, y=2):")
    show(x=1, y=2)
    print("  show(1, k=2):")
    show(1, k=2)

    # 参数种类顺序：位置 / 默认 / *args / 仅关键字 / **kwargs
    def full_form(pos, default=0, *args, keyword_only, **kwargs):
        return (pos, default, args, keyword_only, kwargs)

    print("\n  full_form(1, 2, 3, 4, keyword_only=5, extra=6) =")
    print(f"    {full_form(1, 2, 3, 4, keyword_only=5, extra=6)}")
    print("  [要点] keyword_only 位于 * 之后，只能按关键字传")

    # 裸 * 强制后续参数只能按关键字传
    def strictly_kw(a, *, b):
        return f"a={a}, b={b}"

    print(f"  strictly_kw(1, b=2) = {strictly_kw(1, b=2)}")
    try:
        strictly_kw(1, 2)
    except TypeError as exc:
        print(f"  strictly_kw(1, 2)   -> TypeError: {exc}")
    print("  [Java 对比] Java 无此能力，只能靠 builder 或重载规避参数顺序错误")


def demo_unpack_vs_collect():
    """同一个星号，在调用处和定义处语义相反。"""
    print("\n=== 5. 两副面孔：展开 vs 收集 ===")
    print("  调用处  f(*seq)     -> 把序列【展开】成多个位置参数")
    print("  定义处  def f(*seq) -> 把多个位置参数【收集】成元组")
    print("  同一个符号，方向相反 —— 这是最容易混淆的地方")

    def f(*args):
        return args

    data = (1, 2, 3)
    print(f"\n  f(*{data}) = {f(*data)}   (展开成 3 个参数，又被收成元组)")
    print("  [Java 对比] Java 的 varargs 同样定义处收集、调用处展开，"
          "但语法上不区分（f(T...) / f(arr)），没有显式的 * 标记")


# =============================================================================
# 3. 字面量解包：[*a, *b] / {**d1, **d2}
# =============================================================================
# [Java 对比] Java 无对应语法，只能用 Stream.concat / putAll 之类的 API。

def demo_literal_unpack():
    """在容器字面量里用 * / ** 拼接。"""
    print("\n=== 6. 字面量解包（3.5+）===")

    a = [1, 2, 3]
    b = [4, 5]
    print(f"  列表拼接: [*a, *b] = {[*a, *b]}")
    print(f"  插入元素: [0, *a, 99] = {[0, *a, 99]}")

    t1, t2 = (1, 2), (3,)
    print(f"  元组拼接: (*t1, *t2) = {(*t1, *t2)}")

    s1, s2 = {1, 2}, {2, 3}
    print(f"  集合合并: {{*s1, *s2}} = {sorted({*s1, *s2})}")

    d1 = {"a": 1, "b": 2}
    d2 = {"b": 20, "c": 3}
    print(f"  字典合并: {{**d1, **d2}} = { {**d1, **d2} }   (后者覆盖同名键)")
    print(f"  字典覆盖: {{**d1, 'b': 99}} = { {**d1, 'b': 99} }")

    # 3.9+ 更简洁的合并运算符
    print(f"  3.9+ 合并: d1 | d2 = {d1 | d2}")
    print("  [Java 对比] List.of / Map.of 不可变，"
          "拼接要靠 Stream.concat 或 new HashMap<>(map) 再 putAll")


# =============================================================================
# 4. 常见坑
# =============================================================================

def demo_pitfalls():
    """星号解包的五个高频坑。"""
    print("\n=== 7. 常见坑 ===")

    def three_args(x, y, z):
        return f"x={x!r}, y={y!r}, z={z!r}"

    # 坑 1：只做浅层展开，不会递归
    #        三元组里嵌一个元组，展开后仍是 3 个参数，但第一个是元组
    nested = ((1, 2), 3, 4)
    print(f"  坑 1  浅层展开: three_args(*{nested})")
    print(f"         -> {three_args(*nested)}")
    print("         第一个参数拿到的是元组 (1, 2)，不是 1")
    print("         需要递归时要显式处理: three_args(*nested[0], *nested[2:])")
    print(f"         递归展开后 -> {three_args(*nested[0], *nested[2:])}")

    # 坑 2：参数个数匹配时，类型错了也不报错
    mixed = (1, None, "3")
    print(f"\n  坑 2  类型静默: three_args(*{mixed})")
    print(f"         -> {three_args(*mixed)}")
    print("         个数对上就不会报错，类型问题要等运行到才暴露")

    # 坑 3：个数不匹配立刻 TypeError
    for bad in [(1, 2), (1, 2, 3, 4)]:
        try:
            three_args(*bad)
        except TypeError as exc:
            print(f"  坑 3  个数不匹配 {bad} -> TypeError: {exc}")

    # 坑 4：与 lru_cache 组合时，缓存键的组成方式
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def cached(a, b, c):
        return a + b + c

    cached(1, 2, 3)
    cached(1, 2, 3)          # 完全相同 -> 命中缓存
    print(f"\n  坑 4  lru_cache: {cached.cache_info()}")
    print("         f(*(1,2,3)) 与 f(1,2,3) 参数相同，命中同一缓存；")
    print("         但 f((1,2,3)) 只算一个参数，直接 TypeError")

    # 坑 5：numpy 二维数组按第一维迭代
    try:
        import numpy as np

        arr = np.array([[1, 2], [3, 4]])

        def two(x, y):
            return (x, y)

        print(f"\n  坑 5  numpy 二维数组 *arr 展开的是【行】:")
        print(f"         -> {two(*arr)}")
        print("         要展平成标量用 *arr.ravel()")
    except ImportError:
        print("\n  坑 5  [跳过] numpy 未安装，装后可演示二维数组展开行为")


# =============================================================================
# 5. Java 对照总表
# =============================================================================

def print_java_mapping():
    print("\n=== 8. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("定义可变参数", "def f(*args)", "void f(Object... args)"),
        ("调用展开", "f(*seq)", "f(array)（仅 varargs 形参可用）"),
        ("定义关键参数", "def f(**kw)", "无"),
        ("关键字展开", "f(**mapping)", "无（需反射 Method.invoke）"),
        ("仅关键字参数", "def f(a, *, b)", "无（靠 builder 模式）"),
        ("列表拼接", "[*a, *b]", "Stream.concat / addAll"),
        ("字典合并", "{**d1, **d2} 或 d1 | d2", "new HashMap + putAll"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 62)
    print("星号解包：* 与 ** 的完整用法")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 62)

    demo_call_unpack_positional()
    demo_call_unpack_keywords()
    demo_call_unpack_mixed()
    demo_def_collect()
    demo_unpack_vs_collect()
    demo_literal_unpack()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 62)
    print("所有 demo 运行完成！")
    print("=" * 62)


if __name__ == "__main__":
    main()
