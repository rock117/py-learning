# -*- coding: utf-8 -*-
"""
06_keywords.py - 容易误解的关键字与语句

本文件面向有丰富 Java 经验的开发者，集中讲解几个「天天在用但语义容易理解错」
的 Python 关键字。它们的共同点是：写法眼熟，行为却和 Java 的同名概念不一样。

覆盖
----
1.  lambda            —— 只能写单个表达式，没有多语句 lambda
2.  global / nonlocal —— 作用域声明，LEGB 规则
3.  yield / yield from—— 生成器的两个层次
4.  del               —— 删的是「名字」不是「对象」
5.  assert            —— 会在 python -O 下被整体剥离
6.  is / in / not     —— 身份 vs 相等 vs 成员
7.  pass / elif / None—— 三个小语义
8.  三元表达式        —— 与 Java 的 ?: 顺序不同
9.  for...else        —— 循环的 else（详见迭代协议章）

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
"""

import sys


# =============================================================================
# 1. lambda
# =============================================================================

def demo_lambda():
    """lambda 的能力边界。"""
    print("=== 1. lambda：只能单个表达式 ===")

    add = lambda a, b: a + b
    print(f"  lambda a, b: a + b      -> add(1, 2) = {add(1, 2)}")

    # 三元表达式算「一个表达式」，可以放进 lambda
    classify = lambda n: "even" if n % 2 == 0 else "odd"
    print(f"  带三元                  -> classify(3) = {classify(3)}")

    # 但写不了多条语句
    print("\n  ❌ 不能写多语句：")
    print("     lambda x: (y = x * 2; return y)    # SyntaxError")

    print("\n  ✅ 多语句请用 def：")
    print("     def f(x):")
    print("         y = x * 2")
    print("         return y")

    # 排序 key 是最常见用法
    users = [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]
    print(f"\n  排序 key: {[u['name'] for u in sorted(users, key=lambda u: u['age'])]}")

    print("  [Java 对比] Java 的 lambda 可以写 { ... } 块和多条语句；"
          "Python 只能单表达式，复杂逻辑必须提成具名函数")


# =============================================================================
# 2. global / nonlocal 与 LEGB
# =============================================================================

def demo_scope():
    """LEGB 查找规则与作用域声明。"""
    print("\n=== 2. global / nonlocal 与 LEGB ===")

    print("  LEGB 查找顺序：Local -> Enclosing -> Global -> Builtin")

    x = "global-x"

    def read_global():
        # 只读时不需声明，会按 LEGB 找到全局的 x
        return x

    print(f"    读取全局 x: {read_global()}")

    def shadow():
        x = "local-x"           # 这是【新的局部变量】，不是修改全局
        return x

    print(f"    遮蔽后: {shadow()}  全局 x 仍是 {x!r}")

    def write_global():
        global x                # 显式声明要改全局
        x = "modified"

    write_global()
    print(f"    用 global 修改后 x = {x!r}")

    # nonlocal：修改外层函数（非全局）的变量
    def outer():
        count = 0

        def inner():
            nonlocal count      # 声明 count 来自外层函数
            count += 1
            return count

        inner()
        inner()
        return count

    print(f"\n    nonlocal 累加: outer() = {outer()}")

    print("    ⚠️ nonlocal 找不到外层变量时，是【编译期】SyntaxError，try/except 拓不住")

    print("  [Java 对比] Java 的 lambda 捕获变量必须 effectively final，"
          "根本不允许修改；Python 用 nonlocal 显式声明即可修改外层变量")
    print("  [要点] 只读不需要声明；只有「赋值」时才需要 global/nonlocal")


# =============================================================================
# 3. yield / yield from
# =============================================================================

def demo_yield():
    """生成器与委托生成。"""
    print("\n=== 3. yield / yield from ===")

    def countdown(n):
        while n > 0:
            yield n
            n -= 1

    print(f"  yield 逐个产出: {list(countdown(3))}")

    def nested():
        yield 1
        yield from [2, 3]        # 把另一个可迭代对象的元素逐个产出
        yield from range(4, 6)
        yield 6

    print(f"  yield from 拼接: {list(nested())}")

    # yield from 还会转发 send / throw（高级用法）
    print("\n  yield from 的作用：")
    print("    - 把子迭代器的元素逐个产出（省掉 for 循环）")
    print("    - 转发 send() / throw() / close() 给子生成器")
    print("    - 作为表达式时，值是子生成器的 return 值")

    def sub():
        received = yield 10
        return f"子生成器收到 {received}"

    def outer():
        result = yield from sub()
        yield result

    g = outer()
    print(f"\n  首次 next -> {next(g)}")
    try:
        g.send("hello")            # send 会被转发给 sub 的 yield
    except StopIteration:
        pass
    print(f"  再次 next -> 最终值: {list(outer())}")

    print("  [Java 对比] Java 没有生成器；Stream 是拉取式的，无法双向通信")


# =============================================================================
# 4. del
# =============================================================================

def demo_del():
    """del 删除的是名字/引用，不是对象本身。"""
    print("\n=== 4. del：删名字不删对象 ===")

    a = [1, 2, 3]
    b = a                      # 同一个列表的两个名字
    del a                      # 删掉名字 a，不销毁列表
    print(f"  del a 后 b 仍可用: {b}")
    try:
        a
    except NameError:
        print("  再访问 a -> NameError（名字没了）")

    # del 也能删容器元素 / 切片
    lst = [1, 2, 3, 4, 5]
    del lst[0]
    print(f"\n  del lst[0] -> {lst}")
    del lst[1:3]
    print(f"  del lst[1:3] -> {lst}")

    d = {"k": 1}
    del d["k"]
    print(f"  del d['k'] -> {d}")

    print("\n  [要点] 对象在被【最后一个引用】消失时才回收（引用计数）")
    print("  [Java 对比] Java 没有 del 语句；对象的回收完全交给 GC，"
          "不能手动解除引用")


# =============================================================================
# 5. assert
# =============================================================================

def demo_assert():
    """assert 的真实语义与陷阱。"""
    print("\n=== 5. assert：会在 -O 下消失 ===")

    def check(v):
        assert v > 0, f"必须为正数，收到 {v}"
        return v

    print(f"  check(5) = {check(5)}")
    try:
        check(-1)
    except AssertionError as exc:
        print(f"  check(-1) -> AssertionError: {exc}")

    print("\n  ⚠️ 关键陷阱：python -O 会整体移除 assert")
    print("     -O 优化模式下，assert 语句根本不会执行")
    print("     所以断言【不能】用于：")
    print("       - 用户输入校验（用户能绕过）")
    print("       - 业务规则检查（生产环境失效）")

    print("\n  ✅ assert 的正确用途：")
    print("       - 内部不变量 / 开发期自检")
    print("       - 测试代码（pytest 大量使用 assert）")
    print("       - 类型收窄（配合 mypy）")

    print("\n  ✅ 生产校验请用显式 if + raise：")
    print("     if v <= 0:")
    print("         raise ValueError(f'必须为正数，收到 {v}')")

    print("  [Java 对比] Java 的 assert 同样默认关闭（需 -ea 开启），"
          "两边踩的是同一个坑")


# =============================================================================
# 6. is / in / not
# =============================================================================

def demo_identity():
    """is 是身份比较，== 是值比较。"""
    print("\n=== 6. is / in / not ===")

    a = [1, 2]
    b = [1, 2]
    print(f"  a == b  -> {a == b}     值相等")
    print(f"  a is b  -> {a is b}    身份不同")
    print(f"  a is a  -> {a is a}")

    # 唯一应该用 is 的场景
    print("\n  ✅ 用 is 的场景只有三个：")
    print(f"     x is None      -> {(None is None)}")
    print(f"     x is True/False")
    print(f"     x is y（判断同一对象）")

    print("\n  ⚠️ 不要用 is 比较数字/字符串：")
    x = int("1000")
    y = int("1000")
    print(f"     int('1000') is int('1000') -> {x is y}   （实现相关，不可依赖）")

    # in：成员判断
    print(f"\n  in 成员判断:")
    print(f"     3 in [1, 2, 3]        -> {3 in [1, 2, 3]}")
    print(f"     'k' in {{'k': 1}}       -> {'k' in {'k': 1}}")
    print(f"     'abc' in 'xabcx'      -> {'abc' in 'xabcx'}   子串")

    # not：注意 not in / is not 的写法
    print(f"\n  not in / is not:")
    print(f"     4 not in [1,2,3]      -> {4 not in [1, 2, 3]}")
    print(f"     a is not b            -> {a is not b}")
    print("  [Java 对比] Java 的 == 对引用类型是身份比较，equals 是值比较——"
          "与 Python 正好相反！这是最大的混淆源")


# =============================================================================
# 7. pass / elif / None
# =============================================================================

def demo_small_semantics():
    """三个小语义。"""
    print("\n=== 7. pass / elif / None ===")

    print("  pass：语法占位，什么都不做")
    class Empty:
        pass                    # 空类体必须有 pass

    def todo():
        pass                    # 待实现

    print(f"     空类可实例化: {type(Empty()).__name__}")

    print("\n  elif：Python 用 elif 而不是 Java 的 else if")
    score = 85
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    else:
        grade = "C"
    print(f"     score={score} -> {grade}")
    print("     [Java 对比] Java 写 else if（两个词），Python 是一个关键字 elif")

    print("\n  None：唯一的空值，类型是 NoneType")
    print(f"     type(None) = {type(None).__name__}")
    print(f"     None is None -> {None is None}")
    print(f"     bool(None) -> {bool(None)}   （falsy）")
    print("     [Java 对比] 对应 null，但 None 是一个真实对象，可以传参、比较")
    print("     [注意] Python 没有 NullPointerException，"
          "但访问 None 的属性会 AttributeError")


# =============================================================================
# 8. 三元表达式
# =============================================================================

def demo_ternary():
    """条件表达式的语序与 Java 相反。"""
    print("\n=== 8. 三元表达式 ===")

    n = 5

    # Python：条件在中间
    py = "big" if n > 3 else "small"
    print(f"  Python:  \"big\" if n > 3 else \"small\"   -> {py}")

    # Java：条件在最前
    print(f"  Java:    n > 3 ? \"big\" : \"small\"")
    print("  [要点] 语序不同，这是从 Java 过来最容易写错的地方之一")

    # 嵌套要加括号提升可读性
    score = 85
    label = "A" if score >= 90 else ("B" if score >= 80 else "C")
    print(f"\n  嵌套（建议加括号）: score={score} -> {label}")

    print("  [要点] 嵌套超过两层建议改成 if/elif，可读性优先")


def print_java_mapping():
    print("\n=== 9. Java 对照总表 ===")
    rows = [
        ("关键字", "Python 语义", "Java 对应"),
        ("lambda", "只能单表达式", "可以写块和多语句"),
        ("global", "声明修改模块级变量", "无（字段天然可变）"),
        ("nonlocal", "声明修外层函数变量", "捕获需 effectively final"),
        ("yield", "生成器产出", "无"),
        ("yield from", "委托给子生成器", "无"),
        ("del", "解除名字绑定", "无"),
        ("assert", "-O 下被剥离", "-ea 关闭 / -da 开启"),
        ("is", "身份比较", "==（引用比较）"),
        ("==", "值比较", "equals()"),
        ("elif", "单关键字", "else if"),
        ("x if c else y", "条件在中间", "c ? x : y"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 64)
    print("容易误解的关键字与语句")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 64)

    demo_lambda()
    demo_scope()
    demo_yield()
    demo_del()
    demo_assert()
    demo_identity()
    demo_small_semantics()
    demo_ternary()
    print_java_mapping()

    print("\n" + "=" * 64)
    print("所有 demo 运行完成！")
    print("=" * 64)


if __name__ == "__main__":
    main()
