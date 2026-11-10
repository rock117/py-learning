# -*- coding: utf-8 -*-
"""
07_modern_syntax.py - 现代语法特性
==================================

本文件演示 Python 3.8+ 的现代语法特性。
面向有丰富 Java 经验的开发者。

Java 对比：
- walrus := -> Java 没有直接对应（Java 17+ 模式匹配有类似便利）
- match/case -> Java 21 的 switch pattern matching
- ExceptionGroup -> Java 没有直接对应
- type 语句 -> Java 没有直接对应
- typing.Self -> Java 的 this 类型（JEP 446）
"""

import sys
from typing import Any, Optional, Union


# ============================================================================
# 1. walrus := 赋值表达式 (3.8+)
# ============================================================================

def demo_walrus() -> None:
    """演示海象运算符 :=

    := 在表达式内赋值，避免重复计算。
    Java 对比：Java 没有直接对应，需要先声明变量再赋值。
    """
    print("=== walrus := 赋值表达式 ===")

    # 传统写法
    text = "hello world"
    n = len(text)
    if n > 5:
        print(f"  传统: 长度 {n} 较长")

    # walrus 写法：赋值 + 判断一行搞定
    if (n := len(text)) > 5:
        print(f"  walrus: 长度 {n} 较长")

    # 在 while 循环中读取输入
    lines = ["line1", "line2", ""]
    idx = 0
    while (line := lines[idx]) != "":
        print(f"  读取: {line}")
        idx += 1

    # 在列表推导式中复用计算结果
    data = [1, 2, 3, 4, 5]
    # 传统：计算两次
    result1 = [x * 2 for x in data if x * 2 > 4]
    # walrus：计算一次，复用 y
    result2 = [y for x in data if (y := x * 2) > 4]
    print(f"  列表推导: {result1} == {result2}")


# ============================================================================
# 2. match/case 结构化模式匹配 (3.10+)
# ============================================================================

def demo_match_basic() -> None:
    """演示 match/case 基础。

    Java 对比：Java 21 的 switch pattern matching (JEP 441)。
    Python 的 match 更强大，支持解构、守卫、类型匹配。
    """
    print("\n=== match/case 基础 ===")

    def describe(value: Any) -> str:
        match value:
            case 0:
                return "零"
            case 1 | 2 | 3:  # 或模式
                return "小数"
            case int(n) if n > 100:  # 类型 + 守卫
                return f"大整数 {n}"
            case int(n):
                return f"整数 {n}"
            case str(s):
                return f"字符串 '{s}'"
            case [first, *rest]:  # 列表解构
                return f"列表: first={first}, rest={rest}"
            case {"name": name, "age": age}:  # 字典解构
                return f"人物: {name}, {age}岁"
            case _:  # 默认
                return f"未知: {value!r}"

    print(f"  {describe(0)}")
    print(f"  {describe(2)}")
    print(f"  {describe(200)}")
    print(f"  {describe(42)}")
    print(f"  {describe('hello')}")
    print(f"  {describe([1, 2, 3, 4])}")
    print(f"  {describe({'name': 'Alice', 'age': 30})}")
    print(f"  {describe(3.14)}")


def demo_match_class() -> None:
    """演示 match 匹配类。"""
    print("\n=== match/case 类匹配 ===")

    class Point:
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y

    class Circle:
        def __init__(self, radius: float) -> None:
            self.radius = radius

    def handle_shape(shape: Any) -> str:
        match shape:
            case Point(x=0, y=0):
                return "原点"
            case Point(x=x, y=y):
                return f"点 ({x}, {y})"
            case Circle(radius=r) if r > 10:
                return f"大圆 r={r}"
            case Circle(radius=r):
                return f"小圆 r={r}"
            case _:
                return "未知形状"

    print(f"  {handle_shape(Point(0, 0))}")
    print(f"  {handle_shape(Point(3, 4))}")
    print(f"  {handle_shape(Circle(5))}")
    print(f"  {handle_shape(Circle(20))}")


# ============================================================================
# 3. ExceptionGroup / except* (3.11+)
# ============================================================================

def demo_exception_group() -> None:
    """演示 ExceptionGroup 和 except*。

    ExceptionGroup 允许一次抛出多个异常。
    except* 按类型分别捕获组中的异常。

    Java 对比：Java 没有直接对应，通常一次只抛一个异常。
    """
    print("\n=== ExceptionGroup / except* ===")
    if sys.version_info < (3, 11):
        print("  需要 Python 3.11+")
        return

    # 用 exec 包裹以兼容低版本
    code = '''
class ValidationError(Exception):
    def __init__(self, field):
        self.field = field

class NetworkError(Exception):
    pass

errors = [
    ValidationError("email"),
    NetworkError("timeout"),
    ValidationError("name"),
]

try:
    raise ExceptionGroup("多个错误", errors)
except* ValidationError as eg:
    print(f"  捕获 {len(eg.exceptions)} 个 ValidationError")
    for e in eg.exceptions:
        print(f"    字段: {e.field}")
except* NetworkError as eg:
    print(f"  捕获 {len(eg.exceptions)} 个 NetworkError")
'''
    exec(code)


# ============================================================================
# 4. type 语句类型别名 (3.12+)
# ============================================================================

def demo_type_statement() -> None:
    """演示 type 语句创建类型别名。

    Java 对比：Java 没有直接对应。
    type 语句是 3.12+ 新语法，比 typing.TypeAlias 更清晰。
    """
    print("\n=== type 语句 (3.12+) ===")
    if sys.version_info < (3, 12):
        print("  需要 Python 3.12+，当前用 typing.TypeAlias 演示")
        from typing import TypeAlias
        Vector: TypeAlias = list[float]
        Matrix: TypeAlias = list[list[float]]
        print(f"  Vector = {Vector}")
        print(f"  Matrix = {Matrix}")
        v: Vector = [1.0, 2.0, 3.0]
        print(f"  v = {v}")
        return

    code = '''
type Vector = list[float]
type Matrix = list[list[float]]
type Pair[T] = tuple[T, T]

v: Vector = [1.0, 2.0]
m: Matrix = [[1.0, 2.0], [3.0, 4.0]]
p: Pair[int] = (10, 20)
print(f"  Vector = {v}")
print(f"  Matrix = {m}")
print(f"  Pair[int] = {p}")
'''
    exec(code)


# ============================================================================
# 5. f-string 嵌套 (3.12+)
# ============================================================================

def demo_fstring_nested() -> None:
    """演示 3.12+ f-string 嵌套。

    3.12 之前 f-string 内部不能复用引号，3.12 放宽了限制。
    """
    print("\n=== f-string 嵌套 (3.12+) ===")

    # 3.12 之前也能用的基础用法
    name = "Alice"
    age = 30
    print(f"  {name} is {age}")

    # 嵌套表达式
    data = {"key": "value"}
    print(f"  data = {data}")

    # 3.12+ 可以嵌套相同引号
    if sys.version_info >= (3, 12):
        print(f"  嵌套: {f"{name}"}")  # f-string 内嵌套 f-string
        print(f"  列表推导: {[f"{x*2}" for x in range(3)]}")
    else:
        # 低版本用不同引号
        print(f"  嵌套: {f'{name}'}")
        print(f"  列表推导: {[f'{x*2}' for x in range(3)]}")

    # 格式说明符嵌套
    width = 10
    precision = 2
    value = 3.14159
    print(f"  格式化: {value:{width}.{precision}f}")


# ============================================================================
# 6. typing.Self (3.11+)
# ============================================================================

def demo_self_type() -> None:
    """演示 typing.Self。

    Self 表示"当前类的类型"，用于返回 self 的方法。
    Java 对比：Java 的 this 类型（JEP 446，预览中）。

    3.11 之前需要用 TypeVar + bound 实现类似效果。
    """
    print("\n=== typing.Self (3.11+) ===")
    if sys.version_info < (3, 11):
        print("  需要 Python 3.11+，用 TypeVar 模拟")
        from typing import TypeVar
        TSelf = TypeVar("TSelf", bound="Builder")

        class Builder:
            def __init__(self) -> None:
                self.parts: list = []
            def add(self: "TSelf", part: str) -> "TSelf":
                self.parts.append(part)
                return self
            def build(self) -> str:
                return " ".join(self.parts)

        b = Builder().add("hello").add("world")
        print(f"  结果: {b.build()}")
        return

    code = '''
from __future__ import annotations
from typing import Self

class Builder:
    def __init__(self) -> None:
        self.parts: list = []
    def add(self, part: str) -> Self:  # 返回 Self 类型
        self.parts.append(part)
        return self
    def build(self) -> str:
        return " ".join(self.parts)
b = Builder().add("hello").add("world")
print(f"  结果: {b.build()}")

# Self 在继承中也正确
class FancyBuilder(Builder):
    def add_exclaim(self) -> Self:
        self.parts.append("!")
        return self

fb = FancyBuilder().add("hi").add_exclaim()
print(f"  子类结果: {fb.build()}")
print(f"  返回类型仍是 FancyBuilder（Self 的威力）")
'''
    exec(code)


# ============================================================================
# 7. 实战：用 match/case 实现命令解析器
# ============================================================================

def demo_command_parser() -> None:
    """实战：用 match/case 实现命令解析器。

    模拟一个简单的 shell 命令解析器。
    """
    print("\n=== 实战：命令解析器 ===")

    def parse_command(cmd: str) -> dict:
        """解析命令字符串为结构化数据。"""
        parts = cmd.strip().split()
        if not parts:
            return {"type": "empty"}

        match parts:
            case ["quit" | "exit"]:
                return {"type": "quit"}
            case ["help"]:
                return {"type": "help"}
            case ["echo", *words]:
                return {"type": "echo", "text": " ".join(words)}
            case ["ls", path] if path.startswith("/"):
                return {"type": "ls", "path": path, "absolute": True}
            case ["ls", path]:
                return {"type": "ls", "path": path, "absolute": False}
            case ["ls"]:
                return {"type": "ls", "path": ".", "absolute": False}
            case ["cp" | "mv", src, dst]:
                return {"type": parts[0], "src": src, "dst": dst}
            case ["grep", pattern, *files]:
                return {"type": "grep", "pattern": pattern, "files": files}
            case [cmd, *args]:
                return {"type": "unknown", "cmd": cmd, "args": args}

    # 测试
    commands = [
        "quit",
        "help",
        "echo hello world",
        "ls /home",
        "ls docs",
        "ls",
        "cp a.txt b.txt",
        "mv old new",
        "grep TODO *.py",
        "rm -rf /",
    ]

    for cmd in commands:
        result = parse_command(cmd)
        print(f"  '{cmd}' -> {result}")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_walrus()
    demo_match_basic()
    demo_match_class()
    demo_exception_group()
    demo_type_statement()
    demo_fstring_nested()
    demo_self_type()
    demo_command_parser()
    print("\n所有现代语法示例运行完毕。")
