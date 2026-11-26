# -*- coding: utf-8 -*-
"""
10_dunder_methods.py - 特殊方法（dunder methods）

本文件面向有丰富 Java 经验的开发者，系统梳理 Python 的特殊方法。

和 Java 的根本差异
------------------
Java 的 OO 能力靠【接口 + 继承】：要实现 Comparable 才能排序。
Python 靠【协议 + 特殊方法】：只要你的类有 __lt__，sorted() 就能用，
不需要声明 implements 任何东西。这叫「鸭子类型」在语言层面的体现。

覆盖
----
1.  完整速查表（按协议分组）
2.  对象表示：__repr__ / __str__ / __format__
3.  比较与哈希：__eq__ / __hash__ 为什么必须配套
4.  容器协议：__len__ / __getitem__ / __contains__ / __reversed__
5.  算术运算：__add__ / __radd__ / __iadd__
6.  属性访问：__getattr__ vs __getattribute__（最易混）
7.  创建与销毁：__new__ vs __init__、__del__ 为什么不可靠
8.  可调用：__call__
9.  常见陷阱

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
"""

import sys
import gc


# =============================================================================
# 1. 速查表
# =============================================================================

DUNDER_GROUPS = [
    ("对象表示", ["__repr__", "__str__", "__format__", "__bytes__", "__fspath__"]),
    ("比较", ["__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__", "__hash__", "__bool__"]),
    ("容器", ["__len__", "__getitem__", "__setitem__", "__delitem__",
              "__contains__", "__reversed__", "__missing__"]),
    ("迭代", ["__iter__", "__next__", "__aiter__", "__anext__"]),
    ("算术", ["__add__", "__radd__", "__iadd__", "__sub__", "__mul__",
              "__truediv__", "__floordiv__", "__mod__", "__pow__", "__neg__"]),
    ("属性访问", ["__getattr__", "__getattribute__", "__setattr__",
                  "__delattr__", "__dir__"]),
    ("生命周期", ["__new__", "__init__", "__del__", "__init_subclass__",
                  "__class_getitem__"]),
    ("可调用/上下文", ["__call__", "__enter__", "__exit__", "__aenter__", "__aexit__"]),
]


def demo_cheatsheet():
    """按协议分组速查。"""
    print("=== 1. 特殊方法速查表 ===")

    for group, names in DUNDER_GROUPS:
        print(f"\n  {group}:")
        print(f"    {'  '.join(names)}")

    total = sum(len(v) for _, v in DUNDER_GROUPS)
    print(f"\n  本表共 {total} 个（Python 全部约 80+）")
    print("\n  [核心观念] Python 的「协议」是隐式的：")
    print("     只要实现了对应方法，就自动支持该操作，不需要 implements 声明")
    print("     例如实现了 __len__，len(obj) 就能用")
    print("  [Java 对比] Java 必须 implements Comparable 才能用 Collections.sort")


# =============================================================================
# 2. 对象表示
# =============================================================================

def demo_repr_str():
    """__repr__ vs __str__：谁给开发者看，谁给用户看。"""
    print("\n=== 2. 对象表示 ===")

    class Money:
        def __init__(self, amount, currency="CNY"):
            self.amount = amount
            self.currency = currency

        def __repr__(self) -> str:
            # 给开发者：应该能用来重建对象
            return f"Money({self.amount!r}, {self.currency!r})"

        def __str__(self) -> str:
            # 给用户：可读性优先
            return f"{self.amount} {self.currency}"

        def __format__(self, spec: str) -> str:
            # 支持 f"{m:.2f}" 这种格式说明符
            if spec.endswith("f"):
                return f"{self.amount:{spec}} {self.currency}"
            return str(self)

    m = Money(99.5)
    print(f"  repr(m)      = {repr(m)!r}    <- 开发者视角")
    print(f"  str(m)       = {str(m)!r}     <- 用户视角")
    print(f"  print(m)     -> ", end="")
    print(m)
    print(f"  list 中的显示 -> {[m, Money(1)]}   <- 容器用 repr")
    print(f"  f'{{m:.2f}}'  = {f'{m:.2f}'!r}   <- 走了 __format__")

    print("\n  优先级：__str__ 不存在时，str() 会退回用 __repr__")
    print("         写一个类时，至少实现 __repr__，这是调试的基础")

    print("\n  [Java 对比]")
    print("     __repr__ ≈ toString()（但约定要能重建对象）")
    print("     __str__  ≈ 面向终端用户的 display 版本，Java 无对应")

    # 默认 repr 有多没用
    class Empty:
        pass

    print(f"\n  默认 repr: {repr(Empty())!r}   <- 只有内存地址，调试毫无帮助")


# =============================================================================
# 3. 比较与哈希
# =============================================================================

def demo_eq_hash():
    """__eq__ 与 __hash__ 的配套规则。"""
    print("\n=== 3. 比较与哈希 ===")

    class Point:
        def __init__(self, x, y):
            self.x, self.y = x, y

        def __eq__(self, other):
            if not isinstance(other, Point):
                return NotImplemented        # 关键：不是 return False
            return (self.x, self.y) == (other.x, other.y)

        def __hash__(self):
            return hash((self.x, self.y))

        def __repr__(self):
            return f"Point({self.x}, {self.y})"

    p1, p2 = Point(1, 2), Point(1, 2)
    print(f"  p1 == p2        -> {p1 == p2}")
    print(f"  hash 相同        -> {hash(p1) == hash(p2)}")
    print(f"  可放进 set       -> {len({p1, p2})} 个元素（去重成功）")

    print("\n  ⚠️ 只定义 __eq__ 不定 __hash__ 的后果：")

    class BadPoint:
        def __init__(self, x): self.x = x
        def __eq__(self, other): return self.x == other.x

    b = BadPoint(1)
    print(f"     BadPoint.__hash__ = {BadPoint.__hash__}")
    try:
        {b}
    except TypeError as exc:
        print(f"     放进 set -> TypeError: {exc}")
    print("     -> 定义了 __eq__ 后，Python 自动把 __hash__ 设为 None")

    print("\n  规则：")
    print("     a == b 为 True 时，hash(a) 必须等于 hash(b)")
    print("     所以改了 __eq__ 就要同步改 __hash__，否则容器行为错乱")

    print("\n  ✅ 不可变对象：__eq__ + __hash__ 都实现（可放进 set/dict）")
    print("  ✅ 可变对象：只实现 __eq__，显式写 __hash__ = None（禁止哈希）")

    # NotImplemented vs False
    print("\n  ⚠️ __eq__ 里应该 return NotImplemented 而不是 False：")

    class A:
        def __eq__(self, other):
            return isinstance(other, A) and True

    class B:
        def __eq__(self, other):
            if not isinstance(other, A):
                return NotImplemented
            return True

    print(f"     A() == 'str' -> {A() == 'str'}   <- 立刻 False，没给对反机会")
    print(f"     B() == 'str' -> {B() == 'str'}   <- NotImplemented 让别人接手")


def demo_ordering():
    """排序需要哪些方法。"""
    print("\n=== 4. 排序：__lt__ 与 total_ordering ===")

    class Version:
        def __init__(self, parts):
            self.parts = tuple(parts)

        def __eq__(self, other):
            return self.parts == other.parts

        def __lt__(self, other):
            return self.parts < other.parts

        def __repr__(self):
            return ".".join(map(str, self.parts))

    vs = [Version([1, 10]), Version([1, 2]), Version([2, 0])]
    print(f"  排序结果: {sorted(vs)}")
    print("  只实现 __eq__ + __lt__，sorted() 就能用")

    # total_ordering 自动补齐其余比较
    from functools import total_ordering

    @total_ordering
    class V2:
        def __init__(self, n): self.n = n
        def __eq__(self, o): return self.n == o.n
        def __lt__(self, o): return self.n < o.n
        def __repr__(self): return f"V2({self.n})"

    print(f"\n  @total_ordering 自动补齐 >=：V2(1) >= V2(2) -> {V2(1) >= V2(2)}")
    print("  只需实现 __eq__ 和 __lt__，其余 4 个自动生成")


# =============================================================================
# 4. 容器协议
# =============================================================================

def demo_container():
    """__len__ / __getitem__ / __contains__。"""
    print("\n=== 5. 容器协议 ===")

    class Playlist:
        def __init__(self, songs):
            self._songs = list(songs)

        def __len__(self):
            return len(self._songs)

        def __getitem__(self, i):
            return self._songs[i]           # 支持索引和切片

        def __contains__(self, item):
            return item in self._songs

        def __reversed__(self):
            return reversed(self._songs)

        def __iter__(self):
            return iter(self._songs)

    p = Playlist(["a", "b", "c"])
    print(f"  len(p)        = {len(p)}")
    print(f"  p[0]          = {p[0]!r}")
    print(f"  p[1:]         = {p[1:]}")
    print(f"  'b' in p      = {'b' in p}")
    print(f"  list(reversed(p)) = {list(reversed(p))}")
    print(f"  list(p)       = {list(p)}")

    print("\n  ⚠️ 这些方法的「回退关系」：")
    print("     没有 __contains__ -> 回退用 __iter__ 遍历")
    print("     没有 __iter__     -> 回退用 __getitem__(0..n) 直到 IndexError")
    print("     所以只实现 __getitem__，也能被 for 遍历（但效率低）")

    # 演示只实现 __getitem__ 也能遍历
    class OnlyGetitem:
        def __getitem__(self, i):
            if i >= 3:
                raise IndexError
            return i * 10

    print(f"\n  只实现 __getitem__ 也能 for: {[x for x in OnlyGetitem()]}")

    print("\n  [Java 对比]")
    print("     __len__      ≈ size()")
    print("     __getitem__  ≈ get(int)")
    print("     __contains__ ≈ contains()")
    print("     但 Python 的容器可以不继承任何基类就能用")


def demo_dict_missing():
    """__missing__：dict 子类的默认值。"""
    print("\n=== 6. __missing__：字典的默认值 ===")

    class DefaultDict(dict):
        def __missing__(self, key):
            # 只在 key 不存在时调用
            value = f"<default for {key}>"
            self[key] = value               # 顺便写回
            return value

    d = DefaultDict()
    print(f"  d['a']          = {d['a']!r}")
    print(f"  'a' in d        = {'a' in d}   <- 已被写回")
    print(f"  d.get('b')      = {d.get('b')!r}   <- get 不触发 __missing__")

    print("\n  [要点] __missing__ 只对 d[key] 生效，d.get(key) 不会触发")
    print("  [Java 对比] 对应 Map.computeIfAbsent，但 Python 更透明")


# =============================================================================
# 5. 算术运算
# =============================================================================

def demo_arithmetic():
    """__add__ / __radd__ / __iadd__。"""
    print("\n=== 7. 算术运算：正向 / 反射 / 原地 ===")

    class Vec:
        def __init__(self, x, y):
            self.x, self.y = x, y

        def __repr__(self):
            return f"Vec({self.x}, {self.y})"

        def __add__(self, other):
            print(f"    [__add__] {self} + {other}")
            if isinstance(other, Vec):
                return Vec(self.x + other.x, self.y + other.y)
            return NotImplemented

        def __radd__(self, other):
            print(f"    [__radd__] {other} + {self}  <- 左操作数不支持时才调用")
            if isinstance(other, (int, float)):
                return Vec(self.x + other, self.y + other)
            return NotImplemented

        def __iadd__(self, other):
            print(f"    [__iadd__] {self} += {other}  <- 原地修改")
            self.x += other
            self.y += other
            return self

    v1, v2 = Vec(1, 2), Vec(3, 4)
    print(f"  v1 + v2 = {v1 + v2}")

    print("\n  反射运算：1 + v1（int 不知道怎么加 Vec）")
    print(f"  1 + v1  = {1 + v1}")

    print("\n  原地运算：v1 += 10")
    original_id = id(v1)
    v1 += 10
    print(f"  结果 {v1}，对象 id 是否不变: {id(v1) == original_id}")

    print("\n  [三者区别]")
    print("     __add__    a + b     返回新对象")
    print("     __radd__   b + a     当 a.__add__ 返回 NotImplemented 时尝试")
    print("     __iadd__   a += b    通常原地修改并返回 self")

    print("\n  ⚠️ 不可变类型（如 str、tuple）不应实现 __iadd__ 原地修改")
    print("  [Java 对比] Java 无法重载 + 运算符，只能写 add() 方法")


# =============================================================================
# 6. 属性访问
# =============================================================================

def demo_attribute_access():
    """__getattr__ vs __getattribute__：最重要的区分。"""
    print("\n=== 8. 属性访问：__getattr__ vs __getattribute__ ===")

    class WithGetattr:
        def __init__(self):
            self.x = 1

        def __getattr__(self, name):
            # 只在【正常查找失败】时调用
            print(f"    [__getattr__ 触发] name={name!r}")
            return f"<dynamic {name}>"

    class WithGetattribute:
        def __init__(self):
            self.x = 1

        def __getattribute__(self, name):
            # 每次属性访问都调用，包括存在的属性
            print(f"    [__getattribute__ 触发] name={name!r}")
            return object.__getattribute__(self, name)

    print("  WithGetattr：访问存在的 x")
    a = WithGetattr()
    print(f"    结果: {a.x}   <- 没有触发 __getattr__")
    print("  访问不存在的 y")
    print(f"    结果: {a.y}")

    print("\n  WithGetattribute：访问存在的 x")
    b = WithGetattribute()
    print(f"    结果: {b.x}   <- 也触发了！")

    print("\n  对比表：")
    rows = [
        ("方法", "调用时机"),
        ("__getattribute__", "【每次】属性访问都调用（含存在的属性）"),
        ("__getattr__", "只在【常规查找失败】后调用"),
    ]
    for idx, (m, when) in enumerate(rows):
        print(f"    {m:<20} {when}")
        if idx == 0:
            print("    " + "-" * 60)

    print("\n  ✅ 绝大多数场景用 __getattr__（代理、ORM 动态字段）")
    print("  ⚠️ __getattribute__ 容易造成无限递归：")
    print("      def __getattribute__(self, name):")
    print("          return self.__dict__[name]   # ❌ self.__dict__ 又触发自己")

    print("\n  [Java 对比] 类似 AOP 的 around 拦截，但 Python 是语言内置")

    # 实战：代理对象
    print("\n  实战：用 __getattr__ 做代理")
    class Proxy:
        def __init__(self, target):
            object.__setattr__(self, "_target", target)

        def __getattr__(self, name):
            print(f"    [代理转发] {name}")
            return getattr(self._target, name)

    class RealService:
        def hello(self): return "real hello"
        def bye(self): return "real bye"

    proxy = Proxy(RealService())
    print(f"    proxy.hello() = {proxy.hello()!r}")


# =============================================================================
# 7. 创建与销毁
# =============================================================================

def demo_new_vs_init():
    """__new__ 与 __init__ 的分工。"""
    print("\n=== 9. __new__ vs __init__ ===")

    class Tracked:
        def __new__(cls, *args, **kwargs):
            print(f"    [__new__]    创建实例前，cls={cls.__name__}")
            instance = super().__new__(cls)      # 实际创建
            return instance

        def __init__(self, value):
            print(f"    [__init__]   实例已存在，初始化 value={value}")
            self.value = value

    print("  Tracked(42):")
    Tracked(42)

    print("\n  分工：")
    print("     __new__   负责【创建】实例，返回实例对象（静态方法）")
    print("     __init__  负责【初始化】，返回 None")

    print("\n  何时需要 __new__：")

    # ① 单例
    class Singleton:
        _instance = None

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    print(f"     ① 单例: Singleton() is Singleton() -> "
          f"{Singleton() is Singleton()}")

    # ② 不可变类型（必须改 __new__，因为值在创建时确定）
    class PositiveInt(int):
        def __new__(cls, value):
            if value < 0:
                raise ValueError("必须为非负")
            return super().__new__(cls, value)

    print(f"     ② 校验不可变类型: PositiveInt(5) = {PositiveInt(5)}")
    try:
        PositiveInt(-1)
    except ValueError as exc:
        print(f"        PositiveInt(-1) -> ValueError: {exc}")

    print("\n  [Java 对比] Java 没有 __new__，对象创建由 new 关键字独占")


def demo_del_warning():
    """__del__ 为什么不可靠。"""
    print("\n=== 10. __del__ 为什么不可靠 ===")

    log = []

    class Resource:
        def __init__(self, name):
            self.name = name
            log.append(f"create {name}")

        def __del__(self):
            log.append(f"del {self.name}")

    r = Resource("A")
    print(f"  创建后: {log}")
    del r
    print(f"  del r 后: {log}")

    print("\n  ⚠️ 三个不可靠之处：")
    print("     1. 循环引用时可能永远不调用（要靠 GC）")
    print("     2. 解释器退出时调用顺序不确定")
    print("     3. 异常发生时执行路径无法保证")

    # 演示循环引用
    class Node:
        def __init__(self):
            self.other = None

        def __del__(self):
            log.append("Node del")

    a, b = Node(), Node()
    a.other, b.other = b, a
    del a, b
    log.clear()
    print(f"\n  循环引用后立即检查: {log}   <- 还没回收")
    gc.collect()
    print(f"  手动 gc.collect() 后: {log.count('Node del')} 个被回收")

    print("\n  ✅ 正确做法：用 with / contextlib，不要依赖 __del__ 释放资源")
    print("  [Java 对比] Java 的 finalize() 同样不可靠，早已被废弃（JDK 9+ deprecated）")


# =============================================================================
# 8. 可调用
# =============================================================================

def demo_call():
    """__call__ 让实例像函数。"""
    print("\n=== 11. __call__ ===")

    class Multiplier:
        def __init__(self, factor):
            self.factor = factor

        def __call__(self, x):
            return x * self.factor

    double = Multiplier(2)
    print(f"  double = Multiplier(2)")
    print(f"  double(5) = {double(5)}        <- 实例像函数一样调用")
    print(f"  callable(double) = {callable(double)}")

    print("\n  对比闭包：")

    def make_multiplier(factor):
        def inner(x):
            return x * factor
        return inner

    closure = make_multiplier(2)
    print(f"  闭包 make_multiplier(2)(5) = {closure(5)}")

    print("\n  取舍：")
    print("     __call__：状态可读（double.factor），可继承、可加方法")
    print("     闭包    ：更简短，但内部状态取不到")
    print("  [场景] 有状态的函数、装饰器类、策略对象")

    print("\n  [Java 对比] 相当于实现 Function 接口，但调用语法更自然")


# =============================================================================
# 9. 方法访问与绑定
# =============================================================================

def demo_method_binding():
    """Klass.method vs instance.method：为什么两者不一样。"""
    print("\n=== 12. 方法访问与绑定 ===")

    class HandlerBase:
        def __call__(self, x: int) -> int:
            return x * 2

        def name(self) -> str:
            return "base"

    h = HandlerBase()

    print("  ① 类访问 vs 实例访问：")
    from_class = HandlerBase.__call__
    from_instance = h.__call__
    print(f"     HandlerBase.__call__ -> {type(from_class).__name__}")
    print(f"     h.__call__           -> {type(from_instance).__name__}")
    print(f"     两者是同一函数吗: {from_class is from_instance.__func__}")

    print("\n  ② 调用方式：")
    print(f"     HandlerBase.__call__(h, 5) = {HandlerBase.__call__(h, 5)}   <- 手动传 self")
    print(f"     h.__call__(5)              = {h.__call__(5)}        <- self 已绑定")
    print(f"     h(5)                       = {h(5)}        <- 等价")

    # 不传 self 会怎样
    try:
        HandlerBase.__call__(5)
    except TypeError as exc:
        # 异常消息里会带 <locals> 前缀，因为类定义在函数内部
        print(f"\n     不传 self -> {type(exc).__name__}: "
              f"missing 1 required positional argument: 'x'")
        print("        （少传的其实是 self，只是报错指向参数名）")

    print("\n  ③ 绕过子类重写：")

    class Sub(HandlerBase):
        def __call__(self, x: int) -> int:
            return x + 1

    s = Sub()
    print(f"     s(5)                        = {s(5)}   <- 走 Sub 的重写")
    print(f"     HandlerBase.__call__(s, 5)  = {HandlerBase.__call__(s, 5)}   <- 绕过重写")
    print("     [用途] 装饰器/包装器里取原实现；日常调父类应用 super()")

    print("\n  ④ 类属性查找会沿 MRO：")

    class OnlyInParent(HandlerBase):
        pass

    print(f"     OnlyInParent.name = {OnlyInParent.name}")
    print(f"     但 OnlyInParent.__dict__ 里有 name 吗: "
          f"{'name' in OnlyInParent.__dict__}")
    print(f"     HandlerBase.__dict__['name'] -> "
          f"{type(HandlerBase.__dict__['name']).__name__}   <- 原始未绑定函数")

    print("\n  ⑤ __dict__ 拿原始定义，getattr 走查找：")
    raw = HandlerBase.__dict__["name"]
    via_getattr = getattr(HandlerBase, "name")
    print(f"     __dict__['name']      -> {type(raw).__name__}")
    print(f"     getattr(Klass,'name') -> {type(via_getattr).__name__}")
    print("     两者在类上都是普通函数；差异在于子类：")
    print(f"     OnlyInParent.__dict__ 里没有 name -> KeyError")

    print("\n  ⑥ 为什么是这个行为：")
    print("     普通函数实现了 __get__，所以它是【非数据描述符】")
    print("     通过实例访问 -> __get__(instance, owner) 返回绑定方法")
    print("     通过类访问   -> __get__(None, owner) 返回函数本身")
    print("     原理详见 advanced/02-metaprogramming 的描述符一节")

    print("\n  [Java 对比]")
    print("     Java 没有“方法对象”这个层级的访问；")
    print("     最接近的是 Method.invoke(obj, args)，但那是反射调用，不是绑定语义")


# =============================================================================
# 10. 陷阱
# =============================================================================

def demo_pitfalls():
    """常见错误。"""
    print("\n=== 13. 常见陷阱 ===")

    print("  坑 1  返回 NotImplemented 写成 raise NotImplementedError")
    print("         __eq__ 里应该 return NotImplemented，让 Python 尝试反射比较")
    print("         raise NotImplementedError 会直接抛异常，破坏比较协议")

    print("\n  坑 2  定义 __eq__ 却忘了 __hash__")
    print("         -> 对象变成 unhashable，无法放进 set/dict 键")

    print("\n  坑 3  __getattribute__ 里访问 self.xxx 造成无限递归")
    print("         应使用 object.__getattribute__(self, name)")

    print("\n  坑 4  用 __del__ 释放文件/连接")
    print("         -> 循环引用或解释器退出时可能永远不执行")

    print("\n  坑 5  只实现 __repr__ 但没有 __str__")
    print("         -> 没问题，str() 会退回用 __repr__；反之则调试信息很难看")

    print("\n  坑 6  __len__ 返回负数或非整数")
    try:
        class Bad:
            def __len__(self): return -1
        len(Bad())
    except ValueError as exc:
        print(f"         len(Bad()) -> ValueError: {exc}")

    print("\n  坑 7  可变对象实现 __hash__ 后又被修改")
    print("         -> 哈希值变了，在 set 里就再也找不到了")


def print_java_mapping():
    print("\n=== 14. Java 对照总表 ===")
    rows = [
        ("Python", "Java", "说明"),
        ("__repr__", "toString()", "开发者视角，应可重建"),
        ("__str__", "无", "用户视角"),
        ("__eq__", "equals()", "值相等"),
        ("__hash__", "hashCode()", "必须与 __eq__ 一致"),
        ("__lt__", "Comparable.compareTo", "排序"),
        ("__len__", "size()", "容器长度"),
        ("__getitem__", "get(int)", "索引访问"),
        ("__iter__", "Iterable.iterator()", "迭代"),
        ("__call__", "Function.apply", "实例可调用"),
        ("__new__", "无（new 关键字）", "创建实例"),
        ("__init__", "构造器", "初始化实例"),
        ("__del__", "finalize()（已废弃）", "均不可靠"),
        ("__enter__/__exit__", "AutoCloseable", "上下文管理"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 66)
    print("特殊方法（dunder methods）")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 66)

    demo_cheatsheet()
    demo_repr_str()
    demo_eq_hash()
    demo_ordering()
    demo_container()
    demo_dict_missing()
    demo_arithmetic()
    demo_attribute_access()
    demo_new_vs_init()
    demo_del_warning()
    demo_call()
    demo_method_binding()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 66)
    print("所有 demo 运行完成！")
    print("=" * 66)


if __name__ == "__main__":
    main()
