# -*- coding: utf-8 -*-
"""
02_metaprogramming.py - 面向对象与元编程
========================================

本文件演示 Python 的元编程能力：描述符、元类、ABC、__slots__、dunder 等。
面向有丰富 Java 经验的开发者。

Java 对比：
- Java 的元编程主要靠注解处理器（APT）、反射、ASM 字节码操作。
- Python 的元编程更直接：元类可在类创建时动态修改类，描述符可控制属性访问。
- Python 的"类也是对象"，类本身是 type 的实例。
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, List, Iterator
import sys

T = TypeVar("T")


# ============================================================================
# 1. 描述符 descriptor：__get__ / __set__ / __delete__
# ============================================================================

class ValidatedField:
    """一个数据描述符，实现带校验的属性。

    Java 对比：
    - Java 通常用 getter/setter + 校验逻辑，或 Lombok @Setter 加校验。
    - Python 的描述符把"属性访问"这一行为抽象成对象，更灵活。

    描述符协议：
    - __get__(instance, owner): 读取时调用
    - __set__(instance, value): 赋值时调用
    - __delete__(instance): del 时调用
    只有 __get__ 的是非数据描述符；有 __get__ + __set__ 的是数据描述符。
    """

    def __init__(self, name: str, min_val: int = 0, max_val: int = 100) -> None:
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.internal_name = f"_validated_{name}"

    def __get__(self, instance: Any, owner: type) -> Any:
        if instance is None:
            return self  # 类级别访问返回描述符本身
        return getattr(instance, self.internal_name, None)

    def __set__(self, instance: Any, value: Any) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self.name} 必须是数字")
        if not (self.min_val <= value <= self.max_val):
            raise ValueError(f"{self.name} 必须在 {self.min_val}-{self.max_val} 之间")
        setattr(instance, self.internal_name, value)

    def __delete__(self, instance: Any) -> None:
        if hasattr(instance, self.internal_name):
            delattr(instance, self.internal_name)
            print(f"  删除 {self.name}")


class Student:
    """使用描述符的类。"""
    score = ValidatedField("score", 0, 100)
    age = ValidatedField("age", 0, 150)

    def __init__(self, name: str, score: int, age: int) -> None:
        self.name = name
        self.score = score  # 触发 __set__
        self.age = age


def demo_descriptor() -> None:
    """演示描述符。"""
    print("=== Descriptor ===")
    s = Student("Alice", 90, 20)
    print(f"name={s.name}, score={s.score}, age={s.age}")
    s.score = 85
    print(f"修改后 score={s.score}")
    try:
        s.score = 150  # 超范围
    except ValueError as e:
        print(f"校验失败: {e}")
    del s.score
    print(f"删除后 score={s.score}")


# ============================================================================
# 2. property：描述符的语法糖
# ============================================================================

class Temperature:
    """用 property 实现带校验的属性。

    Java 对比：Java 用 getter/setter，Python 用 @property 装饰器。
    property 本质是一个数据描述符。
    """

    def __init__(self, celsius: float) -> None:
        self.celsius = celsius  # 注意：这会触发 setter

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32


def demo_property() -> None:
    """演示 property。"""
    print("\n=== Property ===")
    t = Temperature(25.0)
    print(f"celsius={t.celsius}, fahrenheit={t.fahrenheit}")
    t.celsius = 0
    print(f"冰点 fahrenheit={t.fahrenheit}")
    try:
        Temperature(-300)
    except ValueError as e:
        print(f"错误: {e}")


# ============================================================================
# 3. 元类 metaclass
# ============================================================================

# 用 type 直接创建类
def demo_type_creation() -> None:
    """用 type() 动态创建类。

    Java 对比：Java 无法在运行时这样动态创建类（除非用 ASM/CGLib）。
    type(name, bases, attrs) 是 Python 创建类的根本方式。
    class 关键字本质上是调用 type()。
    """
    print("\n=== type() 创建类 ===")

    # 动态创建一个类
    methods = {
        "greet": lambda self: f"Hello from {self.__class__.__name__}",
        "x": 0,
    }
    DynamicClass = type("DynamicClass", (object,), methods)
    obj = DynamicClass()
    print(obj.greet())


# 自定义元类
class SingletonMeta(type):
    """元类：确保类只有一个实例。

    Java 对比：Java 单例通常用 private 构造 + 静态方法，或枚举单例。
    Python 用元类拦截 __call__，在类创建实例时控制。

    元类是"创建类的类"。普通类的"类"是 type，自定义元类继承 type。
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=SingletonMeta):
    """使用 SingletonMeta 元类的单例类。"""
    def __init__(self) -> None:
        print("  Database 初始化（只执行一次）")
        self.connected = True


def demo_metaclass() -> None:
    """演示元类单例。"""
    print("\n=== Metaclass Singleton ===")
    db1 = Database()
    db2 = Database()
    print(f"db1 is db2: {db1 is db2}")  # True


# ============================================================================
# 4. __init_subclass__：比元类轻量的钩子
# ============================================================================

class PluginBase:
    """基类，子类注册时自动调用 __init_subclass__。

    Java 对比：Java 没有直接对应，需要用反射扫描或 SPI 机制。
    __init_subclass__ 是 3.6+ 引入的轻量钩子，避免使用元类。
    """

    registry: List[type] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # 每当有子类被定义时，自动注册
        PluginBase.registry.append(cls)
        print(f"  注册插件: {cls.__name__}")


class PluginA(PluginBase):
    pass


class PluginB(PluginBase):
    pass


def demo_init_subclass() -> None:
    """演示 __init_subclass__。"""
    print("\n=== __init_subclass__ ===")
    print(f"已注册插件: {[c.__name__ for c in PluginBase.registry]}")


# ============================================================================
# 5. ABC 抽象基类
# ============================================================================

class Shape(ABC):
    """抽象基类，对比 Java abstract class / interface。

    Java 对比：
        abstract class Shape { abstract double area(); }
    Python 用 abc.ABC + @abstractmethod。
    """

    @abstractmethod
    def area(self) -> float:
        ...

    @abstractmethod
    def perimeter(self) -> float:
        ...

    def describe(self) -> str:
        """具体方法，子类可直接用。"""
        return f"{self.__class__.__name__}: area={self.area():.2f}"


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius


def demo_abc() -> None:
    """演示 ABC。"""
    print("\n=== ABC ===")
    c = Circle(5)
    print(c.describe())
    try:
        Shape()  # 不能实例化抽象类
    except TypeError as e:
        print(f"无法实例化抽象类: {e}")


# ============================================================================
# 6. __slots__：固定属性集合，省内存
# ============================================================================

class PointWithDict:
    """普通类，用 __dict__ 存属性。"""
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class PointWithSlots:
    """用 __slots__ 固定属性，省内存。

    Java 对比：Java 对象字段固定，类似 __slots__。
    Python 默认每个对象有 __dict__ 存任意属性，__slots__ 关闭它。
    优点：省内存、访问更快。缺点：不能动态添加属性。
    """
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def demo_slots() -> None:
    """演示 __slots__。"""
    print("\n=== __slots__ ===")
    p1 = PointWithDict(1, 2)
    p2 = PointWithSlots(1, 2)
    print(f"PointWithDict: x={p1.x}, y={p1.y}")
    print(f"PointWithSlots: x={p2.x}, y={p2.y}")

    p1.z = 3  # 普通类可以动态加属性
    print(f"PointWithDict 动态加 z={p1.z}")
    try:
        p2.z = 3  # slots 类不允许
    except AttributeError as e:
        print(f"PointWithSlots 不允许动态属性: {e}")

    # 内存对比（粗略）
    import sys
    print(f"PointWithDict size = {sys.getsizeof(p1)} bytes")
    print(f"PointWithSlots size = {sys.getsizeof(p2)} bytes")


# ============================================================================
# 7. __class_getitem__：支持类泛型下标
# ============================================================================

class MyList(Generic[T]):
    """支持 MyList[int] 语法的类。

    __class_getitem__ 让类支持下标语法：MyList[int]
    Java 对比：Java 泛型 List<Integer> 是编译期语法，Python 是运行期方法。
    """

    def __init__(self, items: List[T]) -> None:
        self._items = items

    def __class_getitem__(cls, item: Any) -> Any:
        print(f"  MyList[{item}] 被访问")
        return cls

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)


def demo_class_getitem() -> None:
    """演示 __class_getitem__。"""
    print("\n=== __class_getitem__ ===")
    _ = MyList[int]  # 触发 __class_getitem__
    ml = MyList([1, 2, 3])
    print(f"MyList items = {list(ml)}")


# ============================================================================
# 8. 数据模型 dunder：__eq__/__hash__/__lt__/__iter__/__repr__
# ============================================================================

class Person:
    """实现常用 dunder 方法。

    Java 对比：
    - __eq__ / __hash__ -> equals() / hashCode()
    - __lt__ -> Comparable.compareTo()
    - __repr__ -> toString()
    - __iter__ -> Iterable.iterator()
    """

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Person):
            return NotImplemented
        return self.name == other.name and self.age == other.age

    def __hash__(self) -> int:
        return hash((self.name, self.age))

    def __lt__(self, other: "Person") -> bool:
        return self.age < other.age

    def __repr__(self) -> str:
        return f"Person(name={self.name!r}, age={self.age})"

    def __iter__(self):
        yield self.name
        yield self.age


def demo_dunder() -> None:
    """演示数据模型方法。"""
    print("\n=== Dunder Methods ===")
    p1 = Person("Alice", 30)
    p2 = Person("Alice", 30)
    p3 = Person("Bob", 25)
    print(f"p1 == p2: {p1 == p2}")  # True
    print(f"p1 < p3: {p1 < p3}")    # False (30 < 25)
    print(f"repr: {p1!r}")
    print(f"iter: {list(p1)}")
    print(f"hash equal: {hash(p1) == hash(p2)}")

    # 排序
    people = [Person("C", 40), Person("A", 20), Person("B", 30)]
    people.sort()
    print(f"按年龄排序: {people}")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_descriptor()
    demo_property()
    demo_type_creation()
    demo_metaclass()
    demo_init_subclass()
    demo_abc()
    demo_slots()
    demo_class_getitem()
    demo_dunder()
    print("\n所有元编程示例运行完毕。")
