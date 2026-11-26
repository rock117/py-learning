# -*- coding: utf-8 -*-
"""
09_inheritance.py - 类继承与 super()

本文件面向有丰富 Java 经验的开发者，讲透 Python 的类继承。重点放在与 Java
差异最大、最容易写错的地方：

    - super() 不是「调父类」，而是「调 MRO 中的下一个」
    - 多继承是真多继承（Java 只有接口多继承）
    - 菱形继承下 super() 会「走一条链」，不是「回到同一个父类」
    - 没有 final / private，下划线只是约定

覆盖
----
1.  基本继承与方法重写
2.  super() 的基础用法（为什么必须调 __init__）
3.  super() 的真实含义：MRO 里的「下一个」
4.  菱形继承：协作式 super() 的完整走位
5.  多继承与 C3 线性化
6.  协作式多继承的参数透传
7.  抽象基类 ABC
8.  与 Java 的关键差异
9.  何时该用继承

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
"""

import sys
from abc import ABC, abstractmethod


# =============================================================================
# 1. 基本继承与方法重写
# =============================================================================

def demo_basic_inheritance():
    """最基本的继承与重写。"""
    print("=== 1. 基本继承与方法重写 ===")

    class Animal:
        def __init__(self, name: str):
            self.name = name

        def speak(self) -> str:
            return "..."

        def describe(self) -> str:
            return f"{self.name} says {self.speak()}"

    class Dog(Animal):
        def speak(self) -> str:          # 重写
            return "Woof"

    class Cat(Animal):
        def speak(self) -> str:
            return "Meow"

    print(f"  Dog('Rex').describe() -> {Dog('Rex').describe()}")
    print(f"  Cat('Tom').describe() -> {Cat('Tom').describe()}")
    print(f"  isinstance(Dog('Rex'), Animal) -> {isinstance(Dog('Rex'), Animal)}")

    print("\n  [Java 对比]")
    print("     class Dog extends Animal { @Override String speak() {...} }")
    print("     Python 不需要 @Override，没有编译期检查——拼错方法名就变成新增方法")

    # 演示「拼错方法名」不会报错
    class Typo(Animal):
        def speek(self) -> str:          # 拼错了
            return "Typo"

    t = Typo("X")
    print(f"\n  ⚠️ 拼错方法名 speek（少个 a）：")
    print(f"     Typo('X').speak() = {t.speak()!r}   <- 静默用了父类实现，不报错")
    print("     Java 的 @Override 会在编译期拦下这种错误，Python 不会")


# =============================================================================
# 2. super() 的基础用法
# =============================================================================

def demo_super_basic():
    """为什么子类 __init__ 必须调 super().__init__()。"""
    print("\n=== 2. super() 基础：必须调 __init__ ===")

    class Base:
        def __init__(self, name: str):
            self.name = name
            print(f"    Base.__init__ 设置 name={name!r}")

    class GoodChild(Base):
        def __init__(self, name: str, age: int):
            super().__init__(name)        # ✅ 调用父类初始化
            self.age = age

    class BadChild(Base):
        def __init__(self, name: str, age: int):
            # ❌ 忘了 super().__init__(name)
            self.age = age

    g = GoodChild("Alice", 30)
    print(f"  正确: g.name={g.name!r}, g.age={g.age}")

    b = BadChild("Bob", 25)
    try:
        print(b.name)
    except AttributeError as exc:
        print(f"  错误: 访问 b.name -> AttributeError: {exc}")

    print("\n  [要点] 子类定义 __init__ 会【完全覆盖】父类的，不会自动调用")
    print("  [Java 对比] Java 子类构造器会自动调 super()（无参版本）；")
    print("              Python 必须显式写，否则父类初始化被跳过")


# =============================================================================
# 3. super() 的真实含义：MRO 里的「下一个」
# =============================================================================

def demo_super_is_mro():
    """super() 不是「调父类」，是「调 MRO 中的下一个类」。"""
    print("\n=== 3. super() 的真实含义 ===")

    class A:
        def hello(self) -> str:
            return "A"

    class B(A):
        def hello(self) -> str:
            # 这里的 super() 到底调到谁？答案取决于 self 的实际类型
            return f"B -> {super().hello()}"

    class C(A):
        def hello(self) -> str:
            return f"C -> {super().hello()}"

    class D(B, C):
        def hello(self) -> str:
            return f"D -> {super().hello()}"

    print("  单继承时，super() 看起来就像「调父类」：")
    print(f"    B().hello() = {B().hello()}")

    print("\n  但 D 同时继承 B 和 C：")
    print(f"    D().hello() = {D().hello()}")

    print("\n  关键：B 里的 super() 在 D 的实例上【没有回到 A】")
    print(f"    D 的 MRO: {[c.__name__ for c in D.__mro__]}")
    print("    所以 B.hello 里的 super() 跳到 MRO 里 B 的下一个 -> C")

    print("\n  [结论] super() 的正确理解：")
    print("     不是「调用父类方法」")
    print("     而是「沿 MRO 找到【定义 super() 的那个类】之后的下一个类」")
    print("     [Java 对比] Java 的 super.m() 是静态绑定到直接父类，")
    print("                 Python 的 super() 是动态的，取决于实例的实际类型")


def demo_super_forms():
    """super() 的两种写法。"""
    print("\n=== 4. super() 的两种写法 ===")

    class A:
        def greet(self) -> str:
            return "A.greet"

    class B(A):
        def greet(self) -> str:
            # 无参形式（3.x 推荐）：自动取当前类和 self
            via_zero_arg = super().greet()
            # 显式形式：完全等价
            via_explicit = super(B, self).greet()
            return f"{via_zero_arg} == {via_explicit}"

    print(f"  无参 super() 与 super(B, self):")
    print(f"    {B().greet()}")
    print("\n  [要点] 无参 super() 是编译器提供的语法糖，等价于 super(当前类, self)")

    # 演示：在嵌套的普通函数里，无参 super() 会失败
    class C(A):
        def greet(self) -> str:
            def inner():
                # inner 不是方法，没有 self 可解析
                return super().greet()

            return inner()

    try:
        C().greet()
    except RuntimeError as exc:
        print(f"\n  ⚠️ 嵌套普通函数里用无参 super() -> RuntimeError: {exc}")
        print("     因为 inner() 没有 self 参数，编译器无法生成 super(C, self)")
        print("     解法：写成 super(C, self).greet()")

    class C2(A):
        def greet(self) -> str:
            def inner():
                return super(C2, self).greet()     # ✅ 显式传入

            return inner()

    print(f"     super(C2, self) 写法: {C2().greet()!r}")


# =============================================================================
# 4. 菱形继承
# =============================================================================

def demo_diamond():
    """菱形继承下，协作式 super() 保证每个类只执行一次。"""
    print("\n=== 5. 菱形继承：协作式 super() ===")

    calls = []

    class Base:
        def __init__(self, **kwargs):
            calls.append("Base")
            super().__init__(**kwargs)     # 终点：object.__init__

    class Left(Base):
        def __init__(self, **kwargs):
            calls.append("Left")
            super().__init__(**kwargs)     # 继续往 MRO 下一个走

    class Right(Base):
        def __init__(self, **kwargs):
            calls.append("Right")
            super().__init__(**kwargs)

    class Bottom(Left, Right):
        def __init__(self):
            calls.append("Bottom")
            super().__init__()

    print(f"  Bottom 的 MRO: {[c.__name__ for c in Bottom.__mro__]}")
    Bottom()                                # 实例化触发整条链
    print(f"  实际调用顺序: {' -> '.join(calls)}")

    print("\n  每个类只执行【一次】，即使 Base 被 Left 和 Right 共享")
    print("  这正是 MRO 的顺序：Bottom -> Left -> Right -> Base -> object")

    # 对照：如果不用 super()，而是直接调父类
    print("\n  对照：如果写成 Base.__init__(self) 会怎样？")
    direct_calls = []

    class Base2:
        def __init__(self):
            direct_calls.append("Base2")

    class Left2(Base2):
        def __init__(self):
            direct_calls.append("Left2")
            Base2.__init__(self)           # ❌ 硬编码父类

    class Right2(Base2):
        def __init__(self):
            direct_calls.append("Right2")
            Base2.__init__(self)           # ❌ 硬编码父类

    class Bottom2(Left2, Right2):
        def __init__(self):
            direct_calls.append("Bottom2")
            Left2.__init__(self)           # ❌ 硬编码，根本走不到 Right2
            Right2.__init__(self)

    Bottom2()
    print(f"  调用顺序: {' -> '.join(direct_calls)}")
    print("  ❌ Base2 被初始化了【两次】，Right2 也重复了")
    print("  [结论] 多继承下必须用 super()，不要写 父类名.__init__(self)")


# =============================================================================
# 5. 多继承与 C3 线性化
# =============================================================================

def demo_mro_c3():
    """C3 线性化怎么算。"""
    print("\n=== 6. 多继承与 C3 线性化 ===")

    class O:
        pass

    class A(O):
        pass

    class B(O):
        pass

    class C(O):
        pass

    class D(A, B):
        pass

    class E(B, C):
        pass

    class F(D, E):
        pass

    print("  结构:")
    print("        O")
    print("      / | \\")
    print("     A  B  C")
    print("      \\ / \\ /")
    print("       D   E")
    print("        \\ /")
    print("         F")

    for cls in (D, E, F):
        print(f"\n  {cls.__name__}.__mro__ = "
              f"{' -> '.join(c.__name__ for c in cls.__mro__)}")

    print("\n  C3 的三个约束：")
    print("    1. 子类必须排在父类之前")
    print("    2. 多个父类时，保持声明顺序")
    print("    3. 同一类只出现一次")

    print("\n  ⚠️ 无法满足约束时会抛 TypeError：")

    class X:
        pass

    class Y:
        pass

    try:
        class Z(X, Y):
            pass

        class W(Y, X):
            pass

        # 同时继承 Z 和 W：Z 要求 X 在 Y 前，W 要求 Y 在 X 前
        class Bad(Z, W):
            pass
    except TypeError as exc:
        print(f"    TypeError: {exc}")

    print("\n  [Java 对比] Java 没有类多继承，根本不存在这个问题；")
    print("              但接口的 default 方法冲突需要显式 override 解决")


# =============================================================================
# 6. 协作式多继承的参数透传
# =============================================================================

def demo_cooperative_kwargs():
    """多继承时 __init__ 必须一路透传 **kwargs。"""
    print("\n=== 7. 协作式多继承：参数透传 ===")

    class LogMixin:
        def __init__(self, **kwargs):
            self.log_enabled = kwargs.pop("log_enabled", True)
            super().__init__(**kwargs)     # ✅ 继续透传剩下的参数

    class CacheMixin:
        def __init__(self, **kwargs):
            self.cache_size = kwargs.pop("cache_size", 128)
            super().__init__(**kwargs)

    class Service(LogMixin, CacheMixin):
        def __init__(self, name: str, **kwargs):
            self.name = name
            super().__init__(**kwargs)

    s = Service("order-service", log_enabled=False, cache_size=512)
    print(f"  Service('order-service', log_enabled=False, cache_size=512)")
    print(f"    name={s.name!r}  log_enabled={s.log_enabled}  "
          f"cache_size={s.cache_size}")

    print("\n  关键写法：")
    print("    class LogMixin:")
    print("        def __init__(self, **kwargs):")
    print("            self.x = kwargs.pop('x', 默认值)")
    print("            super().__init__(**kwargs)   # 透传剩余参数")

    print("\n  ⚠️ 如果不透传：")
    print("    class BadMixin:")
    print("        def __init__(self, name):     # ❌ 吃掉了 kwargs")
    print("            super().__init__()         # ❌ 后面的类收不到参数")

    print("\n  [要点] Mixin 模式是 Python 多继承最常见的用途")
    print("  [Java 对比] Java 用接口 default 方法实现类似效果，")
    print("              但无法携带状态（字段）")


# =============================================================================
# 7. 抽象基类
# =============================================================================

def demo_abc():
    """ABC 与 @abstractmethod。"""
    print("\n=== 8. 抽象基类 ABC ===")

    class Shape(ABC):
        @abstractmethod
        def area(self) -> float:
            """子类必须实现。"""

        @abstractmethod
        def perimeter(self) -> float:
            """子类必须实现。"""

        def describe(self) -> str:          # 具体方法，子类可直接用
            return f"{type(self).__name__}: area={self.area():.2f}"

    class Circle(Shape):
        def __init__(self, r: float):
            self.r = r

        def area(self) -> float:
            return 3.14159 * self.r ** 2

        def perimeter(self) -> float:
            return 2 * 3.14159 * self.r

    class Square(Shape):
        def __init__(self, a: float):
            self.a = a

        def area(self) -> float:
            return self.a ** 2

        def perimeter(self) -> float:
            return 4 * self.a

    print(f"  {Circle(2).describe()}")
    print(f"  {Square(3).describe()}")

    # 不能实例化抽象类
    try:
        Shape()
    except TypeError as exc:
        print(f"\n  实例化抽象类 -> TypeError: {exc}")

    # 缺方法也不能实例化
    class Bad(Shape):
        def area(self) -> float:
            return 0.0
        # 没实现 perimeter

    try:
        Bad()
    except TypeError as exc:
        print(f"  缺 abstractmethod -> TypeError: {exc}")

    # 有 abstractmethod 但仍可调 super()
    print("\n  [要点] 抽象方法可以有实现体，子类可用 super().area() 复用")
    print("  [Java 对比] ABC + @abstractmethod ≈ abstract class")

    # 对比 NotImplementedError 的陷阱
    print("\n  ⚠️ 对比：不用 ABC，只 raise NotImplementedError")
    print("     class Bad:")
    print("         def area(self):")
    print("             raise NotImplementedError")
    print("     -> 可以实例化！错误到【调用时】才暴露")
    print("     ABC 则在【实例化时】就报错，更早发现问题")


# =============================================================================
# 8. 与 Java 的关键差异
# =============================================================================

def demo_java_diff():
    """没有 final / private / 构造器链。"""
    print("\n=== 9. 与 Java 的关键差异 ===")

    print("  ① 没有 private / protected，下划线只是【约定】")
    print("     class A:")
    print("         def __init__(self):")
    print("             self._internal = 1      # 约定私有")
    print("             self.__secret = 2       # 名称改写成 _A__secret")
    print("         # 但外部仍可访问 a._internal")

    class A:
        def __init__(self):
            self._internal = 1
            self.__secret = 2

    a = A()
    print(f"\n     实测 a._internal = {a._internal}   <- 能访问")
    print(f"     a.__dict__.keys() = {list(a.__dict__)}")
    print("     -> __secret 被改名成 _A__secret（name mangling），不是真私有")

    print("\n  ② 没有 final")
    print("     任何类都能被继承，任何方法都能被重写（除非用 __init_subclass__ 拦）")

    print("\n  ③ 构造器链：Java 自动，Python 手动")
    print("     Java: 子类构造器隐含 super()")
    print("     Python: 必须显式写 super().__init__(...)")

    print("\n  ④ 方法重写没有 @Override 检查")
    print("     拼错方法名不会报错，变成新增方法（见第 1 节演示）")

    print("\n  ⑤ object 是所有类的根")
    print("     class A: pass  等价于  class A(object): pass（3.x）")

    print("\n  ⑥ isinstance 会沿 MRO 查找")
    print(f"     isinstance(Bottom(), Base) 在菱形结构中为 True")


# =============================================================================
# 9. 何时该用继承
# =============================================================================

def demo_when_to_inherit():
    """继承 vs 组合 vs Protocol。"""
    print("\n=== 10. 何时该用继承 ===")

    print("  ✅ 适合用继承：")
    print("     - 真正的 is-a 关系（Dog is an Animal）")
    print("     - 框架要求覆写钩子（如 Django Model、pytest 插件）")
    print("     - 抽象基类定义契约")
    print("     - Mixin 提供横切能力（日志、缓存）")

    print("\n  ❌ 不适合用继承：")
    print("     - 只是想复用代码 -> 用组合")
    print("     - 只是想约束接口 -> 用 Protocol")

    print("\n  组合优于继承的例子：")

    class Engine:
        def start(self) -> str:
            return "engine started"

    # ❌ 继承：Car is-a Engine？语义错误
    class BadCar(Engine):
        pass

    # ✅ 组合：Car has-a Engine
    class GoodCar:
        def __init__(self):
            self.engine = Engine()

        def start(self) -> str:
            return f"car: {self.engine.start()}"

    print(f"     ❌ BadCar().start() = {BadCar().start()!r}   <- 语义错乱")
    print(f"     ✅ GoodCar().start() = {GoodCar().start()!r}")

    print("\n  结构化子类型（不继承也能满足接口）：")

    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class Startable(Protocol):
        def start(self) -> str: ...

    print(f"     isinstance(GoodCar(), Startable) = "
          f"{isinstance(GoodCar(), Startable)}   <- 没继承也满足")
    print("     [优势] 不需要修改被适配的类，也不用引入基类耦合")

    print("\n  [总原则] 继承表达 is-a，组合表达 has-a，Protocol 表达 can-do")


def print_java_mapping():
    print("\n=== 11. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("继承语法", "class D(B, C)", "class D extends B implements C"),
        ("多继承", "支持（类也能多继承）", "只有接口可多继承"),
        ("方法解析", "C3 线性化 MRO", "单链，无歧义"),
        ("super", "MRO 中的下一个类", "静态绑定到直接父类"),
        ("构造器链", "必须显式 super().__init__()", "隐式调用 super()"),
        ("重写检查", "无（拼错就静默新增）", "@Override 编译期检查"),
        ("访问控制", "下划线约定，无强制", "private / protected / public"),
        ("final", "无", "有"),
        ("抽象类", "ABC + @abstractmethod", "abstract class"),
        ("接口契约", "Protocol（结构化）", "interface（名义）"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 66)
    print("类继承与 super()")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 66)

    demo_basic_inheritance()
    demo_super_basic()
    demo_super_is_mro()
    demo_super_forms()
    demo_diamond()
    demo_mro_c3()
    demo_cooperative_kwargs()
    demo_abc()
    demo_java_diff()
    demo_when_to_inherit()
    print_java_mapping()

    print("\n" + "=" * 66)
    print("所有 demo 运行完成！")
    print("=" * 66)


if __name__ == "__main__":
    main()
