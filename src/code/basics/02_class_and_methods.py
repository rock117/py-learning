# -*- coding: utf-8 -*-
"""
02_class_and_methods.py - 类的三种方法装饰器与 property

本文件面向有丰富 Java 经验的开发者，讲解 Python 类里最容易用错的四个概念：
    - 实例方法        def m(self)          ~ Java 普通方法
    - @classmethod    def m(cls)           ~ Java static 方法（但有本质不同）
    - @staticmethod   def m()              ~ Java static 方法（无绑定）
    - @property       def x(self) -> ...   ~ Java getter，但访问时不用括号

核心提醒
--------
Java 的 `static` 方法同时承担了 Python 中 `@staticmethod` 和 `@classmethod`
两个角色的职责。Python 把它们分开了，而且 `@classmethod` 的真正用途是
【替代构造器】——这在 Java 里对应的是 static factory method，但 Python 版本
能自动适配子类，比 Java 更灵活。

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       全部使用标准库。
"""

import sys


# =============================================================================
# 1. 三种方法的基础形态
# =============================================================================

def demo_three_kinds():
    """实例方法 / classmethod / staticmethod 的调用与绑定差异。"""
    print("=== 1. 三种方法的绑定差异 ===")

    class Demo:
        class_attr = "I am class attr"

        def instance_method(self):
            return f"instance_method: self={type(self).__name__}"

        @classmethod
        def cls_method(cls):
            return f"cls_method: cls={cls.__name__}, class_attr={cls.class_attr!r}"

        @staticmethod
        def static_method():
            return "static_method: 没有 self/cls，拿不到类或实例"

    d = Demo()
    print(f"  实例调用  {d.instance_method()}")
    print(f"  类调用    {Demo.cls_method()}")
    print(f"  实例调用  {d.cls_method()}       <- 实例也能调，cls 仍是 Demo")
    print(f"  类调用    {Demo.static_method()}")
    print(f"  实例调用  {d.static_method()}     <- 无绑定，两者等价")

    try:
        Demo.instance_method()
    except TypeError as exc:
        print(f"  类调实例方法 -> TypeError: {exc}")

    print("  [Java 对比] Java 的 static 方法用类名调用，实例调用只是语法糖；"
          "Python 的 classmethod 虽然也能用实例调用，但收到的一直是【类】")


def demo_classmethod_as_factory():
    """classmethod 的核心用途：替代构造器（static factory method）。"""
    print("\n=== 2. @classmethod 作为替代构造器 ===")

    class Point:
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

        def __repr__(self) -> str:
            return f"Point({self.x}, {self.y})"

        @classmethod
        def from_tuple(cls, pair):
            return cls(pair[0], pair[1])

        @classmethod
        def from_string(cls, s: str):
            x, y = s.split(",")
            return cls(float(x), float(y))

        @classmethod
        def origin(cls):
            return cls(0, 0)

    print(f"  正常构造:        {Point(1, 2)}")
    print(f"  from_tuple:      {Point.from_tuple((3, 4))}")
    print(f"  from_string:     {Point.from_string('5.5,6.5')}")
    print(f"  origin:          {Point.origin()}")

    # 关键优势：cls 会自动是子类
    class Point3D(Point):
        def __init__(self, x, y, z=0.0):
            super().__init__(x, y)
            self.z = z

        def __repr__(self) -> str:
            return f"Point3D({self.x}, {self.y}, {self.z})"

    p3 = Point3D.from_tuple((7, 8))
    print(f"\n  子类继承工厂方法: Point3D.from_tuple((7, 8)) = {p3}")
    print(f"  返回类型: {type(p3).__name__}   <- 自动适配子类")
    print("  [Java 对比] Java 的 static 方法不会被继承，"
          "子类调用 Point3D.fromTuple 只能得到 Point；"
          "Python 的 cls 让工厂方法天然支持子类")


def demo_staticmethod_use():
    """staticmethod 的合理用途与误用。"""
    print("\n=== 3. @staticmethod 的合理用途 ===")

    class Temperature:
        def __init__(self, celsius: float):
            self.celsius = celsius

        @staticmethod
        def c_to_f(c: float) -> float:
            # 纯函数：不依赖 self 也不依赖 cls，放类里只是为了归类
            return c * 9 / 5 + 32

        def to_fahrenheit(self) -> float:
            return self.c_to_f(self.celsius)

    print(f"  Temperature.c_to_f(100) = {Temperature.c_to_f(100)}")
    print(f"  Temperature(100).to_fahrenheit() = {Temperature(100).to_fahrenheit()}")
    print("  [要点] 纯工具函数适合 staticmethod；"
          "一旦需要访问类属性就该用 classmethod")
    print("  [误用] 用 staticmethod 做工厂方法会丢失子类适配能力")


# =============================================================================
# 2. property：getter / setter / deleter
# =============================================================================
# [Java 对比] property 等价于 getter/setter，但调用方【不写括号】，
#             字段和属性的访问语法完全一致。

def demo_property_basic():
    """property 的基本用法。"""
    print("\n=== 4. @property 基本用法 ===")

    class Circle:
        def __init__(self, radius: float):
            self._radius = radius

        @property
        def radius(self) -> float:
            return self._radius

        @radius.setter
        def radius(self, value: float) -> None:
            if value < 0:
                raise ValueError("半径不能为负")
            self._radius = value

        @property
        def area(self) -> float:
            import math
            return math.pi * self._radius ** 2

    c = Circle(2)
    print(f"  c.radius = {c.radius}        <- 不加括号，像访问字段")
    print(f"  c.area   = {c.area:.4f}      <- 只读，没有 setter")
    c.radius = 3
    print(f"  赋值后 c.radius = {c.radius}")

    try:
        c.radius = -1
    except ValueError as exc:
        print(f"  非法赋值 -> ValueError: {exc}")

    try:
        c.area = 100
    except AttributeError as exc:
        print(f"  给只读属性赋值 -> AttributeError: {exc}")

    print("  [Java 对比] Java 写 getRadius()/setRadius()，调用处要区分；"
          "Python 用 property 让调用方直接 c.radius")


def demo_property_computed():
    """property 做派生字段与缓存。"""
    print("\n=== 5. property 做派生字段 ===")

    class Rectangle:
        def __init__(self, w: float, h: float):
            self.w = w
            self.h = h

        @property
        def area(self) -> float:
            # 每次访问重新计算，永远和数据一致
            return self.w * self.h

        @property
        def is_square(self) -> bool:
            return self.w == self.h

    r = Rectangle(3, 4)
    print(f"  area = {r.area}, is_square = {r.is_square}")
    r.w = 4
    print(f"  改 w=4 后 area = {r.area}, is_square = {r.is_square}  <- 自动同步")
    print("  [Java 对比] Java 需要在 setter 里手动更新派生字段，"
          "或每次 getter 里重算")


def demo_property_vs_public():
    """该用 property 还是直接用公有属性。"""
    print("\n=== 6. 何时用 property ===")
    print("  Python 惯例是【先写公有属性】，需要时再用 property 包装：")
    print("    class P:")
    print("        def __init__(self): self.x = 1     # 公有字段")
    print("    # 后来需要校验，改成 property，调用方代码不用动")
    print("  [Java 对比] Java 习惯一开始就写 private + getter/setter，")
    print("              20 行的类配 60 行样板代码；Python 不需要")
    print("  [要点] property 的 setter 里访问自身属性要用 _xxx，"
          "否则无限递归")


# =============================================================================
# 3. 常见陷阱
# =============================================================================

def demo_pitfalls():
    """三个高频错误。"""
    print("\n=== 7. 常见陷阱 ===")

    # 坑 1：忘记 @staticmethod，第一个参数被当成 self
    print("  坑 1  忘记 @staticmethod")
    print("         class A:")
    print("             def f(x): return x    # 实例调用时 x 拿到 self")
    print("         A().f(1) -> TypeError: f() takes 1 positional argument but 2 were given")

    # 坑 2：property setter 里递归
    print("\n  坑 2  property setter 递归")
    print("         @radius.setter")
    print("         def radius(self, v): self.radius = v   # 无限递归")
    print("         正确写法: self._radius = v")

    # 坑 3：classmethod 里修改类属性影响所有实例
    print("\n  坑 3  classmethod 里改类属性会影响全局")

    class Counter:
        count = 0

        @classmethod
        def increment(cls):
            cls.count += 1      # 注意：这会创建/修改 cls 上的属性

    Counter.increment()
    Counter.increment()
    print(f"         Counter.count = {Counter.count}  <- 类级状态，所有实例共享")

    class ChildCounter(Counter):
        pass

    ChildCounter.increment()
    print(f"         Counter.count = {Counter.count}")
    print(f"         ChildCounter.count = {ChildCounter.count}  <- 子类有了自己的副本")
    print("         [Java 对比] Java 的 static 字段是每个类一份，"
          "Python 的类属性在子类赋值时会分裂")


def print_java_mapping():
    print("\n=== 8. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("实例方法", "def m(self)", "普通方法"),
        ("类方法", "@classmethod def m(cls)", "static 方法（但能拿类对象）"),
        ("静态方法", "@staticmethod def m()", "static 方法"),
        ("替代构造器", "@classmethod 工厂方法", "static factory method"),
        ("子类适配工厂", "cls 自动是子类", "不支持"),
        ("只读属性", "@property", "getter"),
        ("可写属性", "@x.setter", "getter + setter"),
        ("访问语法", "obj.x（无括号）", "obj.getX()"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 62)
    print("类的三种方法装饰器与 property")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 62)

    demo_three_kinds()
    demo_classmethod_as_factory()
    demo_staticmethod_use()
    demo_property_basic()
    demo_property_computed()
    demo_property_vs_public()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 62)
    print("所有 demo 运行完成！")
    print("=" * 62)


if __name__ == "__main__":
    main()
