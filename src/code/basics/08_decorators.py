# -*- coding: utf-8 -*-
"""
08_decorators.py - 装饰器入门

本文件面向有丰富 Java 经验的开发者，从「为什么要装饰器」讲到「能自己写出
带参数的装饰器」，一步步推导。进阶用法（叠加顺序、lru_cache、singledispatch）
见 advanced/03_decorators.py。

为什么装饰器算「基础」
----------------------
它出现在 Python 的每个角落：@property、@classmethod、@staticmethod、
@contextmanager、@pytest.fixture、@app.route、@lru_cache……
不先搞懂装饰器，这些全都只能死记。

覆盖
----
1.  为什么需要装饰器（不用它会怎样）
2.  前置：函数是对象
3.  前置：闭包
4.  从零手写装饰器
5.  @ 语法糖的推导
6.  wrapper 的三个必须
7.  带参数的装饰器（三层嵌套）
8.  类装饰器
9.  常见错误

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       全部使用标准库。
"""

import sys
import time
import functools


# =============================================================================
# 1. 为什么需要装饰器
# =============================================================================

def demo_why():
    """同一段横切逻辑被复制到多个函数里。"""
    print("=== 1. 为什么需要装饰器 ===")

    print("  需求：给每个函数加上「打印调用日志」和「计时」。")
    print("\n  ❌ 不用装饰器，每个函数都要抄一遍：")
    print("     def fetch_user(uid):")
    print("         start = time.perf_counter()          # 重复 1")
    print("         print(f'[LOG] fetch_user({uid})')    # 重复 2")
    print("         result = _fetch_user(uid)")
    print("         print(f'[LOG] 耗时 {time.perf_counter()-start:.3f}s')")
    print("         return result")
    print("     def save_order(order):")
    print("         start = time.perf_counter()          # 又是同一套")
    print("         ...")

    print("\n  问题：")
    print("     - 10 个函数就要抄 10 遍，改一次要改 10 处")
    print("     - 真正的业务逻辑被淹没了")

    print("\n  ✅ 用装饰器，横切逻辑只写一次：")
    print("     @logged")
    print("     @timed")
    print("     def fetch_user(uid):")
    print("         return _fetch_user(uid)")

    print("\n  [Java 对比]")
    print("     这正是 Spring AOP 解决的问题（@Around / @Before 切面）。")
    print("     但 Java 靠运行时代理或字节码增强，Python 靠纯函数组合——简单得多。")

    # 真实演示重复代码的痛点
    def timed_raw(fn, *args):
        start = time.perf_counter()
        result = fn(*args)
        return result, time.perf_counter() - start

    def work(n):
        return sum(range(n))

    _, cost = timed_raw(work, 100_000)
    print(f"\n  手动计时一次：work(100000) 耗时 {cost * 1000:.2f}ms")
    print("  每个函数都要这么包一次——这就是装饰器要消除的重复。")


# =============================================================================
# 2. 前置：函数是对象
# =============================================================================

def demo_functions_are_objects():
    """函数可以赋值、传参、作为返回值。"""
    print("\n=== 2. 前置：函数是对象 ===")

    def greet(name):
        return f"Hello, {name}"

    # ① 赋值给变量
    f = greet
    print(f"  ① 函数可以赋值: f = greet; f('A') = {f('A')!r}")
    print(f"     两者同一对象: f is greet -> {f is greet}")

    # ② 作为参数传递
    def apply(func, arg):
        return func(arg)

    print(f"  ② 作为参数: apply(greet, 'B') = {apply(greet, 'B')!r}")

    # ③ 作为返回值
    def make_greeter(prefix):
        def inner(name):
            return f"{prefix}, {name}"
        return inner

    hi = make_greeter("Hi")
    print(f"  ③ 作为返回值: make_greeter('Hi')('C') = {hi('C')!r}")

    # ④ 可以有属性
    greet.owner = "team-a"
    print(f"  ④ 函数有属性: greet.owner = {greet.owner!r}")
    print(f"     常用内置属性: __name__={greet.__name__!r}, "
          f"__module__={greet.__module__!r}")

    print("\n  [Java 对比]")
    print("     Java 的方法不是一等公民，需要 Function/BiFunction 等函数式接口包装；")
    print("     Python 的函数本身就是对象，直接传即可——这是装饰器成立的前提。")


# =============================================================================
# 3. 前置：闭包
# =============================================================================

def demo_closures():
    """闭包：内部函数记住了外层函数的变量。"""
    print("\n=== 3. 前置：闭包 ===")

    def make_counter():
        count = 0

        def inner():
            nonlocal count          # 声明修改外层变量
            count += 1
            return count

        return inner

    c1 = make_counter()
    c2 = make_counter()
    print(f"  c1() = {c1()}, {c1()}, {c1()}   -> 独立计数")
    print(f"  c2() = {c2()}                 -> 另有一份 count")
    print("  每次调用 make_counter() 都会创建一个新的闭包环境")

    # 闭包捕获的是「变量」而不是「值」
    print("\n  ⚠️ 闭包捕获变量本身，不是当时的快照：")

    def make_funcs():
        return [lambda: i for i in range(3)]

    print(f"     [lambda: i for i in range(3)] 调用 -> "
          f"{[f() for f in make_funcs()]}   <- 全是 2")

    # 用默认参数固定当前值
    def make_funcs_fixed():
        return [lambda i=i: i for i in range(3)]

    print(f"     [lambda i=i: i for i in range(3)] -> "
          f"{[f() for f in make_funcs_fixed()]}")

    print("\n  [为什么装饰器需要闭包]")
    print("     装饰器要「记住」被装饰的原函数，闭包正好能做这件事：")
    print("     def deco(func):")
    print("         def wrapper(): ")
    print("             func()          # func 来自闭包")
    print("         return wrapper")
    print("  [Java 对比] 类似 lambda 捕获 effectively final 变量，"
          "但 Python 用 nonlocal 可以修改")


# =============================================================================
# 4. 从零手写装饰器
# =============================================================================

def demo_handwritten():
    """不写 @，纯手写装饰器。"""
    print("\n=== 4. 从零手写装饰器 ===")

    # 第一步：写一个普通函数
    def add(a, b):
        """两数相加。"""
        return a + b

    # 第二步：写一个「接收函数、返回函数」的函数
    def my_decorator(func):
        def wrapper(*args, **kwargs):
            print(f"    [BEFORE] 即将调用 {func.__name__}")
            result = func(*args, **kwargs)
            print(f"    [AFTER]  返回 {result}")
            return result
        return wrapper

    # 第三步：手动替换
    print("  add(1, 2) =", add(1, 2), "  <- 原始行为")
    print("\n  手动装饰：add = my_decorator(add)")
    add = my_decorator(add)
    print("  add(1, 2) =", add(1, 2), "  <- 已加上前后逻辑")

    print("\n  [关键] 装饰器本质就是「函数替换」：")
    print("         新函数 = 装饰器(旧函数)")


# =============================================================================
# 5. @ 语法糖
# =============================================================================

def demo_syntax_sugar():
    """@deco 与 f = deco(f) 完全等价。"""
    print("\n=== 5. @ 语法糖的推导 ===")

    def my_decorator(func):
        def wrapper(*args, **kwargs):
            print(f"    [LOG] {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

    # 写法 A：手写
    def add_manual(a, b):
        return a + b
    add_manual = my_decorator(add_manual)

    # 写法 B：@ 语法
    @my_decorator
    def add_sugar(a, b):
        return a + b

    print("  写法 A：add = my_decorator(add)")
    print(f"    add_manual(1, 2) = {add_manual(1, 2)}")
    print("\n  写法 B：@my_decorator 写在 def 上方")
    print(f"    add_sugar(1, 2) = {add_sugar(1, 2)}")
    print("\n  两者完全等价，@ 只是语法糖")

    print("\n  [要点] def 后面的名字被「重新绑定」成了 wrapper，")
    print("         原函数只存在于闭包里，外部已无法直接访问")


# =============================================================================
# 6. wrapper 的三个必须
# =============================================================================

def demo_wrapper_essentials():
    """*args/**kwargs、return、wraps。"""
    print("\n=== 6. wrapper 的三个必须 ===")

    # 必须 1：用 *args, **kwargs 才能包装任意函数
    def bad_decorator(func):
        def wrapper():                       # ❌ 无参数
            return func()                    # ❌ 无参数
        return wrapper

    @bad_decorator
    def greet_any(name, greeting="Hello"):
        return f"{greeting}, {name}"

    print("  必须 1：*args, **kwargs")
    try:
        greet_any("Alice")
    except TypeError as exc:
        print(f"    ❌ 不写 *args 时调用 -> TypeError: {exc}")
    print("    ✅ 正确写法: def wrapper(*args, **kwargs): return func(*args, **kwargs)")

    # 必须 2：必须 return 原函数的返回值
    def forget_return(func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)            # ❌ 忘记 return
        return wrapper

    @forget_return
    def add_forget(a, b):
        return a + b

    print("\n  必须 2：return 原函数的结果")
    print(f"    ❌ 忘记 return -> add_forget(1, 2) = {add_forget(1, 2)}")
    print("    这是最隐蔽的 bug：函数不报错，但返回 None")

    # 必须 3：functools.wraps 保留元信息
    def no_wraps(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def with_wraps(func):
        @functools.wraps(func)               # ✅
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    @no_wraps
    def documented_a(x):
        """原始文档字符串 A。"""
        return x

    @with_wraps
    def documented_b(x):
        """原始文档字符串 B。"""
        return x

    print("\n  必须 3：functools.wraps")
    print(f"    ❌ 不用 wraps -> __name__={documented_a.__name__!r}, "
          f"__doc__={documented_a.__doc__!r}")
    print(f"    ✅ 用了 wraps -> __name__={documented_b.__name__!r}, "
          f"__doc__={documented_b.__doc__!r}")
    print("    影响：日志里的函数名、IDE 提示、文档生成、pytest 的用例名")

    print("\n  [Java 对比]")
    print("     Java 的注解不会改变方法签名/元数据；")
    print("     Python 的装饰器直接替换了函数对象，所以必须手动保留元信息")


# =============================================================================
# 7. 带参数的装饰器
# =============================================================================

def demo_param_decorator():
    """三层嵌套：为什么需要三层。"""
    print("\n=== 7. 带参数的装饰器（三层嵌套）===")

    print("  目标：@repeat(times=3) 让函数重复执行 3 次")

    # 第 1 层：接收【装饰器参数】
    def repeat(times):
        # 第 2 层：接收【被装饰的函数】
        def decorator(func):
            # 第 3 层：接收【函数调用参数】
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                results = [func(*args, **kwargs) for _ in range(times)]
                return results
            return wrapper
        return decorator

    @repeat(times=3)
    def say(name):
        return f"hi {name}"

    print(f"\n  @repeat(times=3) 调用 say('A') -> {say('A')}")

    print("\n  逐层拆解：")
    print("    ① @repeat(times=3) 先执行 repeat(3)")
    print("       -> 返回 decorator（一个只差 func 的函数）")
    print("    ② 再执行 decorator(say)")
    print("       -> 返回 wrapper")
    print("    ③ say 被重新绑定为 wrapper")
    print("\n  等价于：say = repeat(times=3)(say)")

    # 验证等价性
    def raw_say(name):
        return f"hi {name}"

    manual = repeat(times=2)(raw_say)
    print(f"\n  手动等价写法 repeat(2)(raw_say)('B') -> {manual('B')}")

    print("\n  为什么必须是三层？")
    print("    第 1 层拿 times        —— 没有它，repeat(3) 无法接收 3")
    print("    第 2 层拿 func         —— 没有它，不知道要包装谁")
    print("    第 3 层拿 args/kwargs  —— 没有它，无法接收调用实参")
    print("    每层职责不同，缺一不可")

    print("\n  [易错点] 最内层忘了 @functools.wraps(func)，元信息会丢")
    print("  [易错点] 返回层级写错：return decorator 写成 return wrapper 会直接报错")


# =============================================================================
# 8. 类装饰器
# =============================================================================

def demo_class_decorator():
    """用类的 __call__ 做装饰器。"""
    print("\n=== 8. 类装饰器 ===")

    class CountCalls:
        """统计函数被调用的次数（状态保存在实例上）。"""

        def __init__(self, func):
            self.func = func
            self.count = 0
            functools.update_wrapper(self, func)     # 保留元信息

        def __call__(self, *args, **kwargs):
            self.count += 1
            print(f"    第 {self.count} 次调用 {self.func.__name__}")
            return self.func(*args, **kwargs)

    @CountCalls
    def greet(name):
        return f"Hello, {name}"

    greet("A")
    greet("B")
    result = greet("C")
    print(f"  最终结果: {result}")
    print(f"  调用次数可从对象读取: greet.count = {greet.count}")

    print("\n  [对比闭包写法] 用闭包也能计数，但状态藏在闭包里取不到：")
    print("     def count_deco(func):")
    print("         count = 0")
    print("         def wrapper(...):")
    print("             nonlocal count; count += 1")
    print("         return wrapper")
    print("     -> 外部拿不到 count")

    print("\n  [取舍] 需要对外暴露状态时用类；否则闭包更简洁")

    print("\n  带参数的类装饰器（在 __init__ 收参数，__call__ 收函数）：")
    print("     class Retry:")
    print("         def __init__(self, times): self.times = times")
    print("         def __call__(self, func):")
    print("             def wrapper(*a, **kw): ...")
    print("             return wrapper")


# =============================================================================
# 9. 常见错误
# =============================================================================

def demo_pitfalls():
    """六个实际会踩的坑。"""
    print("\n=== 9. 常见错误 ===")

    print("  坑 1  忘记 return 原函数结果")
    print("         -> 函数静默返回 None，最隐蔽")

    print("\n  坑 2  忘记 @functools.wraps")
    print("         -> __name__ 变成 'wrapper'，日志和文档全错")

    print("\n  坑 3  wrapper 不带 *args, **kwargs")
    print("         -> 只能包装无参函数，其他一律 TypeError")

    print("\n  坑 4  带参装饰器少写一层")
    print("         @repeat(3) 若只写两层，3 会被当成 func")

    print("\n  坑 5  装饰器在「导入时」就执行了")
    print("         @deco 的效果发生在模块导入阶段，不是每次调用时")
    print("         -> 装饰器里有 IO/网络，会拖慢导入甚至直接失败")

    # 真实演示
    print("\n  坑 6  叠加顺序容易反")

    def tag(name):
        def deco(func):
            @functools.wraps(func)
            def wrapper(*a, **kw):
                return f"<{name}>{func(*a, **kw)}</{name}>"
            return wrapper
        return deco

    @tag("outer")
    @tag("inner")
    def content():
        return "X"

    print(f"         @tag('outer') 在上、@tag('inner') 在下")
    print(f"         结果: {content()}")
    print("         -> 下面的先包装，上面的后包装（从内到外应用）")
    print("         记忆：离 def 越近越先执行")

    print("\n  [要点] 装饰器在导入期执行——这也是为什么它不能用来做"
          "「运行时才决定的逻辑」")


def print_java_mapping():
    print("\n=== 10. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("横切逻辑", "@decorator（函数组合）", "AOP @Around/@Before"),
        ("带参数", "@deco(arg) 三层嵌套", "@Repeat(3) 注解属性"),
        ("有状态", "类装饰器 __call__", "InvocationHandler 代理"),
        ("元信息", "functools.wraps", "注解不改变方法元数据"),
        ("执行时机", "导入时（装饰即替换）", "运行时织入"),
        ("函数当类方法", "@property/@classmethod", "getter / static"),
        ("测试夹具", "@pytest.fixture", "@BeforeEach"),
        ("路由", "@app.route('/x')", "@RequestMapping"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 64)
    print("装饰器入门：从为什么到怎么写")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 64)

    demo_why()
    demo_functions_are_objects()
    demo_closures()
    demo_handwritten()
    demo_syntax_sugar()
    demo_wrapper_essentials()
    demo_param_decorator()
    demo_class_decorator()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 64)
    print("所有 demo 运行完成！")
    print("=" * 64)
    print("进阶内容见：advanced/03_decorators.py")
    print("=" * 64)


if __name__ == "__main__":
    main()
