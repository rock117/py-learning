# -*- coding: utf-8 -*-
"""
01_type_system.py - 类型系统与静态检查
======================================

本文件演示 Python 的类型系统（typing 模块）及静态类型检查。
面向有丰富 Java 经验的开发者，通过对比 Java 帮助理解。

Java 对比：
- Java 是静态强类型语言，编译期即检查类型。
- Python 是动态强类型语言，运行期才检查类型；但通过 typing + mypy/pyright
  可以在开发期获得类似 Java 的静态类型检查能力。
- Python 的类型注解在运行期默认不影响执行（除非用 `from __future__ import annotations`
  或运行期类型检查库如 pydantic / beartype）。

静态检查工具（注释说明，无需运行）：
- mypy: `pip install mypy`，然后 `mypy 01_type_system.py`
- pyright: `pip install pyright` 或 VSCode Pylance 插件
- 两者都支持 PEP 484 / 483 等类型规范。
"""

import sys
from typing import (
    Generic,
    TypeVar,
    Optional,
    Union,
    Callable,
    Literal,
    Final,
    TypedDict,
    Protocol,
    overload,
    Any,
    List,
    Dict,
    TypeAlias,
)

# ============================================================================
# 1. typing 基础：Generic / TypeVar / Optional / Union / Callable
# ============================================================================

# TypeVar: 泛型类型变量
# Java 对比：<T>。Python 需要显式声明 TypeVar，相当于 Java 的类型参数 T。
T = TypeVar("T")  # 简单泛型，不限制类型
K = TypeVar("K")
V = TypeVar("V")


class Box(Generic[T]):
    """一个简单的泛型容器。

    Java 对比：
        class Box<T> { private T value; ... }
    Python 用 Generic[T] 继承来声明泛型类。
    """

    def __init__(self, value: T) -> None:
        self._value: T = value  # 类型注解，运行期不强制

    def get(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        self._value = value


def demo_generic_box() -> None:
    """演示泛型容器 Box。"""
    print("=== Generic Box ===")
    int_box: Box[int] = Box(42)  # 相当于 Java Box<Integer>
    str_box: Box[str] = Box("hello")
    print(f"int_box = {int_box.get()}, type = {type(int_box.get())}")
    print(f"str_box = {str_box.get()}, type = {type(str_box.get())}")
    # 注意：运行期 int_box 和 str_box 没有区别，类型注解仅供静态检查


# Optional / Union
# Java 对比：Optional<T>（但 Python 的 Optional 只是 Union[T, None] 的语法糖）
def find_user(user_id: int) -> Optional[str]:
    """返回用户名，找不到返回 None。

    Java 对比：
        Optional<String> findUser(int id)  // Java 用 Optional 包装
    Python 的 Optional[str] 等价于 Union[str, None]，表示可能为 None。
    """
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)  # 找不到返回 None


def demo_optional_union() -> None:
    """演示 Optional / Union。"""
    print("\n=== Optional / Union ===")
    print(f"find_user(1) = {find_user(1)!r}")  # 'Alice'
    print(f"find_user(99) = {find_user(99)!r}")  # None

    # Union: 多种类型之一
    # Java 对比：Java 没有直接的 Union，需要用接口或重载。
    def process(value: Union[int, str]) -> str:
        if isinstance(value, int):
            return f"int: {value * 2}"
        return f"str: {value.upper()}"

    print(process(5))      # int: 10
    print(process("hi"))   # str: HI


# Callable: 函数类型
# Java 对比：Java 用函数式接口（如 Function<T,R>、Consumer<T>）。
def apply_twice(func: Callable[[int], int], x: int) -> int:
    """对 x 应用 func 两次。

    Java 对比：
        int applyTwice(Function<Integer,Integer> func, int x)
    """
    return func(func(x))


def demo_callable() -> None:
    """演示 Callable 类型注解。"""
    print("\n=== Callable ===")
    result = apply_twice(lambda n: n + 10, 5)  # (5+10)+10 = 25
    print(f"apply_twice(lambda n: n+10, 5) = {result}")


# ============================================================================
# 2. Literal / Final / TypedDict
# ============================================================================

# Literal: 限定值为特定字面量
# Java 对比：Java 没有直接对应，需要用枚举或常量。Python 的 Literal 更轻量。
def set_mode(mode: Literal["read", "write", "append"]) -> str:
    """模式只能是 'read'/'write'/'append'。

    Java 对比：通常用 enum Mode { READ, WRITE, APPEND }
    """
    return f"mode set to {mode}"


# Final: 不可变绑定（类似 Java final）
MAX_SIZE: Final[int] = 100  # 静态检查器会阻止重新赋值


class Config(TypedDict):
    """TypedDict: 字典的键值类型固定。

    Java 对比：类似一个 POJO / record，但运行期仍是 dict。
    Python 3.8+ 支持。
    """
    host: str
    port: int
    debug: bool


def demo_literal_final_typeddict() -> None:
    """演示 Literal / Final / TypedDict。"""
    print("\n=== Literal / Final / TypedDict ===")
    print(set_mode("read"))
    # set_mode("xxx")  # 静态检查会报错，运行期不报错
    print(f"MAX_SIZE = {MAX_SIZE}")

    cfg: Config = {"host": "localhost", "port": 8080, "debug": False}
    print(f"Config = {cfg}, host = {cfg['host']}")


# ============================================================================
# 3. @overload 函数重载
# ============================================================================

# Python 的 overload 仅用于类型检查，运行期需要用一个具体实现
# Java 对比：Java 有真正的编译期重载，Python 用 @overload 模拟签名


@overload
def parse(value: int) -> int: ...
@overload
def parse(value: str) -> str: ...
@overload
def parse(value: list) -> int: ...


def parse(value):
    """根据输入类型返回不同结果。

    Java 对比：
        int parse(int v) { return v; }
        String parse(String v) { return v; }
    Python 运行期只有一个实现，靠 isinstance 分派。
    """
    if isinstance(value, int):
        return value * 2
    if isinstance(value, str):
        return value.upper()
    if isinstance(value, list):
        return len(value)
    raise TypeError("unsupported type")


def demo_overload() -> None:
    """演示 @overload。"""
    print("\n=== @overload ===")
    print(f"parse(10) = {parse(10)}")        # 20
    print(f"parse('ab') = {parse('ab')}")     # AB
    print(f"parse([1,2,3]) = {parse([1,2,3])}")  # 3


# ============================================================================
# 4. ParamSpec / TypeVarTuple（高阶泛型）
# ============================================================================

# ParamSpec: 捕获函数的参数签名（PEP 612，3.10+）
# Java 对比：Java 没有直接对应，需要用函数式接口或反射。
try:
    from typing import ParamSpec, TypeVarTuple, Unpack
    P = ParamSpec("P")
    Ts = TypeVarTuple("Ts")
    HAS_PARAMSPEC = True
except ImportError:
    HAS_PARAMSPEC = False


def with_paramspec() -> None:
    """ParamSpec 演示（仅静态检查，运行期无效果）。"""
    print("\n=== ParamSpec / TypeVarTuple ===")
    if not HAS_PARAMSPEC:
        print("ParamSpec 不可用（需要 Python 3.10+）")
        return

    # ParamSpec 用于保留装饰器中函数的参数签名
    # 静态检查器能看到 logged 调用后函数签名不变
    def logged(func: Callable[P, V]) -> Callable[P, V]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> V:
            print(f"  calling {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

    @logged
    def greet(name: str, times: int) -> str:
        return (f"hi {name} " * times).strip()

    print(greet("Bob", 2))

    # TypeVarTuple: 可变长度泛型（PEP 646，3.11+）
    # Java 对比：Java 有可变参数 ... 但类型层面不统一。
    def first_item(tup: tuple[Unpack[Ts]]) -> Any:  # 静态检查用
        return tup[0] if tup else None

    print(f"first_item((1,'x',True)) = {first_item((1, 'x', True))}")


# ============================================================================
# 5. Protocol（结构化子类型，对比 Java interface）
# ============================================================================

# Protocol: 结构化子类型（鸭子类型 + 静态检查）
# Java 对比：Java interface 是名义子类型（nominal），必须显式 implements。
# Python Protocol 是结构化子类型（structural），只要形状匹配即可。
class SupportsClose(Protocol):
    """任何有 close() 方法的对象都满足此协议。

    Java 对比：
        interface SupportsClose { void close(); }
        class MyFile implements SupportsClose { ... }  // 必须显式 implements
    Python 中无需显式声明，只要有 close() 方法即可。
    """
    def close(self) -> None: ...


class MyResource:
    """无需继承 SupportsClose，只要有 close() 方法即满足协议。"""
    def close(self) -> None:
        print("  MyResource closed")


def close_resource(r: SupportsClose) -> None:
    r.close()


def demo_protocol() -> None:
    """演示 Protocol 结构化子类型。"""
    print("\n=== Protocol ===")
    res = MyResource()
    close_resource(res)  # 结构匹配，静态检查通过


# ============================================================================
# 6. 协变 / 逆变（对比 Java ? extends / ? super）
# ============================================================================

# 协变 covariant=True：子类型关系随类型参数同向变化
#   Java: List<? extends Number>
# 逆变 contravariant=True：子类型关系反向变化
#   Java: List<? super Number> / Comparator<? super T>
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


class Producer(Generic[T_co]):
    """协变：Producer[Dog] 是 Producer[Animal] 的子类型。

    Java 对比：List<? extends Animal> —— 只读，不能写入。
    """
    def __init__(self, item: T_co) -> None:
        self._item = item

    def produce(self) -> T_co:
        return self._item


class Consumer(Generic[T_contra]):
    """逆变：Consumer[Animal] 是 Consumer[Dog] 的子类型。

    Java 对比：List<? super Dog> —— 只写，读取为 Object。
    """
    def consume(self, item: T_contra) -> None:
        print(f"  consumed {item}")


def demo_variance() -> None:
    """演示协变 / 逆变。"""
    print("\n=== 协变 / 逆变 ===")
    # 协变示例
    p_dog: Producer[str] = Producer("dog")
    p_object: Producer[object] = p_dog  # 协变：Producer[str] <: Producer[object]
    print(f"produce = {p_object.produce()}")

    # 逆变示例
    c_object: Consumer[object] = Consumer()
    c_str: Consumer[str] = c_object  # 逆变：Consumer[object] <: Consumer[str]
    c_str.consume("hello")  # Consumer[object] 能消费任何对象，当然能消费 str


# ============================================================================
# 7. PEP 695 (3.12+) 原生泛型语法
# ============================================================================

def demo_pep695() -> None:
    """PEP 695 原生泛型语法（3.12+）。"""
    print("\n=== PEP 695 原生泛型语法 ===")
    if sys.version_info < (3, 12):
        print("PEP 695 需要 Python 3.12+，当前版本不支持")
        return

    # 3.12+ 新语法，无需 TypeVar / Generic
    # 用 exec 包裹避免低版本语法错误
    code = '''
class NewBox[T]:
    def __init__(self, value: T) -> None:
        self.value = value
    def get(self) -> T:
        return self.value

def new_func[T](x: T) -> T:
    return x

type Vector = list[float]  # type 语句创建别名

b = NewBox(123)
print(f"NewBox = {b.get()}")
print(f"new_func('x') = {new_func('x')}")
print(f"Vector alias: {[1.0, 2.0]}")
'''
    exec(code)


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_generic_box()
    demo_optional_union()
    demo_callable()
    demo_literal_final_typeddict()
    demo_overload()
    with_paramspec()
    demo_protocol()
    demo_variance()
    demo_pep695()
    print("\n所有类型系统示例运行完毕。")
