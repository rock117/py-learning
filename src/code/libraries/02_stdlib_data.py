# -*- coding: utf-8 -*-
"""
02_stdlib_data.py - Python 标准库数据处理模块讲解

本文件面向有丰富 Java 经验的开发者，讲解 Python 标准库中数据处理相关模块：
    - re：正则表达式
    - json：JSON 序列化
    - datetime：日期时间
    - enum：枚举
    - dataclasses：数据类
    - typing：类型注解

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       所有 demo 都可通过 `python 02_stdlib_data.py` 运行，exit code 0。

对比 Java：
    Java 开发者常用 java.util.regex / Jackson / java.time / enum，
    Python 标准库提供了功能对等的实现，且通常更简洁。
"""

import re
import json
import datetime
from datetime import datetime as dt, date, time, timedelta, timezone
from enum import Enum, IntEnum, auto, Flag, IntFlag
from dataclasses import dataclass, field, asdict, astuple, replace
from typing import (
    Optional, Union, List, Dict, Tuple, Set,
    Callable, Any, TypeVar, Generic, Protocol,
    Literal, Final, TypedDict, NewType, TypeAlias,
    runtime_checkable,
)


# =============================================================================
# 第一部分：re 正则表达式
# =============================================================================
# [Java 对比] Python 的 re 模块对应 Java 的 java.util.regex.Pattern/Matcher。
#             语法基本兼容，但 Python 支持命名分组 (?P<name>...) 更直观。

def demo_re_basic():
    """基础匹配 re.match / re.search / re.fullmatch。

    [Java 对比]
      re.match   -> 类似 Pattern.matcher(s).lookingAt()（从头匹配）
      re.search  -> 类似 Pattern.matcher(s).find()（任意位置）
      re.fullmatch -> 类似 Pattern.matches(pattern, s)（整串匹配）
    """
    print("=== re 基础匹配 ===")
    text = "Hello World 123"

    # match 从字符串开头匹配
    m = re.match(r"Hello", text)
    print("match('Hello'):", m.group() if m else None)

    # search 在任意位置搜索第一个匹配
    s = re.search(r"\d+", text)
    print("search('\\d+'):", s.group() if s else None)

    # fullmatch 要求整个字符串完全匹配
    fm = re.fullmatch(r"Hello World \d+", text)
    print("fullmatch:", bool(fm))


def demo_re_findall():
    """查找所有 re.findall / re.finditer。"""
    print("\n=== re.findall / finditer ===")
    text = "电话: 138-0000-1111, 备用: 139-2222-3333"
    # findall 返回所有匹配的字符串列表
    print("findall:", re.findall(r"\d{3}-\d{4}-\d{4}", text))

    # 有分组时返回分组元组
    print("findall(分组):", re.findall(r"(\d{3})-(\d{4})", text))

    # finditer 返回迭代器，节省内存
    for m in re.finditer(r"\d+", text):
        print(f"  匹配: {m.group()} 位置: {m.start()}-{m.end()}")


def demo_re_sub():
    """替换 re.sub / re.subn。"""
    print("\n=== re.sub / subn ===")
    text = "今天是 2024-01-15，明天是 2024-01-16"
    # sub 替换所有匹配
    print("sub:", re.sub(r"\d{4}-\d{2}-\d{2}", "[日期]", text))

    # subn 返回 (替换结果, 替换次数)
    result, count = re.subn(r"\d+", "N", text)
    print("subn:", result, "替换次数:", count)

    # 用函数动态替换
    def double_num(m):
        return str(int(m.group()) * 2)
    print("sub(函数):", re.sub(r"\d+", double_num, "a1 b2 c3"))


def demo_re_split():
    """分割 re.split。"""
    print("\n=== re.split ===")
    # 按非字母数字分割
    print("split:", re.split(r"[^a-zA-Z0-9]+", "hello,world!foo;bar"))

    # 保留分隔符（分组）
    print("split(保留):", re.split(r"([,;])", "a,b;c"))

    # 限制分割次数
    print("split(maxsplit=2):", re.split(r"\s+", "a b c d e", maxsplit=2))


def demo_re_compile():
    """编译 re.compile 与 re.Pattern。

    [Java 对比] Java 中 Pattern.compile 返回可复用 Pattern。
    Python 同样，频繁使用同一正则时建议预编译。
    """
    print("\n=== re.compile ===")
    pattern = re.compile(r"\b\w{4}\b")  # 编译一次，多次使用
    print("Pattern 类型:", type(pattern).__name__)
    print("findall:", pattern.findall("cat dog bird fish"))
    print("search:", pattern.search("I have a bird").group())


def demo_re_group():
    """分组与命名分组 (?P<name>...)。"""
    print("\n=== re 分组与命名分组 ===")
    text = "张三, 25岁, 北京"
    # 普通分组
    m = re.match(r"(\w+),\s*(\d+)岁", text)
    print("group(1):", m.group(1), "group(2):", m.group(2))

    # 命名分组
    m2 = re.match(r"(?P<name>\w+),\s*(?P<age>\d+)岁", text)
    print("name:", m2.group("name"), "age:", m2.group("age"))
    print("groupdict:", m2.groupdict())


def demo_re_greedy():
    """贪婪与非贪婪 .*?。"""
    print("\n=== re 贪婪与非贪婪 ===")
    html = '<a>1</a><a>2</a>'
    # 贪婪：尽可能多匹配
    print("贪婪:", re.findall(r"<a>(.*)</a>", html))   # ['1</a><a>2']
    # 非贪婪：尽可能少匹配
    print("非贪婪:", re.findall(r"<a>(.*?)</a>", html))  # ['1', '2']


def demo_re_assertion():
    """零宽断言 (?=...) / (?!...) / (?<=...) / (?<!...)。

    [注意] 断言不消耗字符，只做位置判断。
    """
    print("\n=== re 零宽断言 ===")
    text = "price: $100, $200, $300"
    # 正向先行断言：匹配后面是 $ 的数字
    # (?<=\$) 表示前面是 $，\d+ 匹配数字
    print("后跟$的数字:", re.findall(r"(?<=\$)\d+", text))

    # 正向先行断言 (?=...)
    print("后面是逗号的位置:", re.findall(r"\w+(?=,)", "a,b,c"))

    # 负向断言 (?!...) / (?<!...)
    print("不以0开头的数字:", re.findall(r"\b(?!0)\d+\b", "01 12 003 45"))


def demo_re_flags():
    """flags: re.IGNORECASE / re.MULTILINE / re.DOTALL / re VERBOSE。"""
    print("\n=== re flags ===")
    # IGNORECASE 忽略大小写
    print("IGNORECASE:", re.findall(r"hello", "Hello HELLO", re.IGNORECASE))

    # MULTILINE 多行模式，^ $ 匹配每行首尾
    text = "line1\nline2\nline3"
    print("MULTILINE:", re.findall(r"^line\d", text, re.MULTILINE))

    # DOTALL 让 . 匹配换行符
    print("DOTALL:", re.findall(r"a.*b", "a\nb", re.DOTALL))

    # VERBOSE 允许在正则中加注释和空白
    pattern = re.compile(r"""
        \d{3}    # 区号
        -        # 分隔符
        \d{4}    # 前四位
        -        # 分隔符
        \d{4}    # 后四位
    """, re.VERBOSE)
    print("VERBOSE:", pattern.findall("138-0000-1111"))


# =============================================================================
# 第二部分：json 模块
# =============================================================================
# [Java 对比] Python 的 json 模块对应 Java 的 Jackson ObjectMapper。
#             但 Python 的 json 只支持基本类型，复杂对象需自定义编码器。

def demo_json_dumps():
    """json.dumps 序列化。

    [Java 对比] 类似 ObjectMapper.writeValueAsString(obj)。
    """
    print("\n=== json.dumps ===")
    data = {"name": "张三", "age": 25, "scores": [90, 85, 88]}
    # dumps 返回 JSON 字符串
    s = json.dumps(data, ensure_ascii=False)  # ensure_ascii=False 保留中文
    print("dumps:", s)

    # indent 美化输出
    print("indent=2:")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # sort_keys 排序键
    print("sort_keys:", json.dumps({"b": 1, "a": 2}, sort_keys=True))


def demo_json_loads():
    """json.loads 反序列化。"""
    print("\n=== json.loads ===")
    s = '{"name": "李四", "age": 30}'
    obj = json.loads(s)
    print("loads:", obj, "类型:", type(obj).__name__)
    print("name:", obj["name"])


def demo_json_file():
    """json.dump / json.load 文件读写。"""
    print("\n=== json.dump / load ===")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        path = f.name
    try:
        # 写入文件
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"x": 1, "y": [2, 3]}, f, ensure_ascii=False, indent=2)
        # 读取文件
        with open(path, "r", encoding="utf-8") as f:
            print("load:", json.load(f))
    finally:
        import os
        os.unlink(path)


def demo_json_custom_encoder():
    """处理日期的自定义编码器（JSONEncoder 子类）。

    [Java 对比] Jackson 用 @JsonFormat 或自定义 JsonSerializer。
    """
    print("\n=== json 自定义编码器 ===")

    class MyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (dt, date)):
                return obj.isoformat()  # ISO 8601 格式
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    data = {"now": dt(2024, 1, 15, 10, 30), "tags": {"a", "b"}}
    print("自定义编码:", json.dumps(data, cls=MyEncoder, ensure_ascii=False))


def demo_json_custom_decoder():
    """自定义解码器：object_hook 处理字典。"""
    print("\n=== json 自定义解码器 ===")

    def as_date(dct):
        # 把带 __date__ 标记的字典转回 date
        if "__date__" in dct:
            return date.fromisoformat(dct["__date__"])
        return dct

    s = '{"event": "launch", "when": {"__date__": "2024-01-15"}}'
    obj = json.loads(s, object_hook=as_date)
    print("解码:", obj)
    print("when 类型:", type(obj["when"]).__name__)


def demo_json_type_map():
    """JSON 与 Python 类型映射表。"""
    print("\n=== JSON 与 Python 类型映射 ===")
    print("object  <-> dict")
    print("array   <-> list")
    print("string  <-> str")
    print("number  <-> int / float")
    print("true    <-> True")
    print("false   <-> False")
    print("null    <-> None")
    print("[注意] Python 的 set / bytes / tuple / 自定义类 需额外处理")


# =============================================================================
# 第三部分：datetime 模块
# =============================================================================
# [Java 对比] Python 的 datetime 对应 Java 的 java.time 包（LocalDateTime 等）。
#             Java 的 java.time 是不可变且线程安全的，Python 的 datetime 也是不可变。

def demo_datetime_now():
    """datetime.now / today / utcnow（已弃用）。"""
    print("\n=== datetime 获取当前时间 ===")
    print("now() =", dt.now())             # 本地时间
    print("today() =", dt.today())          # 等价 now()
    # [注意] utcnow() 在 3.12+ 已弃用，推荐用 now(timezone.utc)
    print("now(utc) =", dt.now(timezone.utc))


def demo_datetime_construct():
    """datetime 构造与属性。"""
    print("\n=== datetime 构造与属性 ===")
    d = dt(2024, 1, 15, 10, 30, 45)
    print("构造:", d)
    print("year:", d.year, "month:", d.month, "day:", d.day)
    print("hour:", d.hour, "minute:", d.minute, "second:", d.second)
    print("weekday():", d.weekday())  # 0=周一
    print("date():", d.date(), "time():", d.time())


def demo_datetime_format():
    """格式化 strftime / strptime。

    [Java 对比] Java 用 DateTimeFormatter.ofPattern("yyyy-MM-dd")。
    Python 用 strftime/strptime，格式符不同：%Y %m %d %H %M %S。
    """
    print("\n=== datetime 格式化 ===")
    d = dt(2024, 1, 15, 10, 30)
    print("strftime:", d.strftime("%Y年%m月%d日 %H:%M:%S"))
    print("isoformat:", d.isoformat())

    # 解析
    s = "2024-01-15 10:30:00"
    parsed = dt.strptime(s, "%Y-%m-%d %H:%M:%S")
    print("strptime:", parsed, "类型:", type(parsed).__name__)


def demo_datetime_timedelta():
    """timedelta 时间差。"""
    print("\n=== timedelta ===")
    d1 = dt(2024, 1, 15)
    d2 = dt(2024, 1, 20)
    delta = d2 - d1
    print("时间差:", delta, "天数:", delta.days)

    # 加减
    print("d1 + 5天:", d1 + timedelta(days=5))
    print("d1 + 12小时:", d1 + timedelta(hours=12))
    print("d1 - 1周:", d1 - timedelta(weeks=1))


def demo_datetime_date_time():
    """date / time 类。"""
    print("\n=== date / time 类 ===")
    d = date(2024, 1, 15)
    t = time(10, 30, 45)
    print("date:", d, "time:", t)
    print("date.today():", date.today())
    # date 和 time 可组合成 datetime
    print("combine:", dt.combine(d, t))


def demo_datetime_timezone():
    """timezone 时区处理（3.9+ zoneinfo）。"""
    print("\n=== datetime 时区 ===")
    # 固定时区偏移
    tz_bj = timezone(timedelta(hours=8), name="CST")
    d = dt(2024, 1, 15, 10, 30, tzinfo=tz_bj)
    print("带时区:", d, "tzinfo:", d.tzinfo)

    # 3.9+ zoneinfo 使用 IANA 时区名
    try:
        from zoneinfo import ZoneInfo
        d_ny = dt(2024, 1, 15, 10, 30, tzinfo=ZoneInfo("America/New_York"))
        print("纽约时间:", d_ny)
        # 转时区
        print("转为北京:", d_ny.astimezone(ZoneInfo("Asia/Shanghai")))
    except Exception as e:
        print("zoneinfo 不可用:", e)


def demo_datetime_timestamp():
    """timestamp 与 fromtimestamp。"""
    print("\n=== datetime 时间戳 ===")
    d = dt(2024, 1, 15, 10, 30)
    ts = d.timestamp()  # 转 Unix 时间戳（秒）
    print("timestamp:", ts)
    print("fromtimestamp:", dt.fromtimestamp(ts))
    # UTC 时间戳
    print("utcfromtimestamp:", dt.fromtimestamp(ts, tz=timezone.utc))


# =============================================================================
# 第四部分：enum 模块
# =============================================================================
# [Java 对比] Python 的 enum 对应 Java 的 enum，但功能更灵活。
#             Java enum 本质是单例类，Python enum 也是类。

def demo_enum_basic():
    """Enum 基础。"""
    print("\n=== Enum 基础 ===")

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    c = Color.RED
    print("值:", c, "name:", c.name, "value:", c.value)
    # 按值查找
    print("Color(2):", Color(2))
    # 按名查找
    print("Color['BLUE']:", Color["BLUE"])
    # 迭代
    print("所有成员:", list(Color))


def demo_enum_intenum():
    """IntEnum / IntStrEnum。"""
    print("\n=== IntEnum ===")

    class Status(IntEnum):
        OK = 200
        NOT_FOUND = 404
        ERROR = 500

    # IntEnum 可与 int 比较、运算
    print("Status.OK == 200:", Status.OK == 200)
    print("Status.OK + 1:", Status.OK + 1)
    # [注意] 普通 Enum 不支持与 int 比较


def demo_enum_auto():
    """auto 自动赋值。"""
    print("\n=== enum.auto ===")

    class Direction(Enum):
        UP = auto()
        DOWN = auto()
        LEFT = auto()
        RIGHT = auto()

    print("UP.value:", Direction.UP.value)  # 1
    print("所有:", list(Direction))


def demo_enum_custom():
    """自定义值与 __init__。"""
    print("\n=== enum 自定义值 ===")

    class Planet(Enum):
        MERCURY = (1, "水星", 3.303e23)
        VENUS = (2, "金星", 4.869e24)
        EARTH = (3, "地球", 5.976e24)

        def __init__(self, num, cn_name, mass):
            self.num = num
            self.cn_name = cn_name
            self.mass = mass

    p = Planet.EARTH
    print(f"{p.name}: 编号={p.num}, 中文={p.cn_name}, 质量={p.mass}")


def demo_enum_flag():
    """Flag / IntFlag 位运算枚举。

    [Java 对比] 类似 Java 的 EnumSet，但 Python 用位运算更直接。
    """
    print("\n=== Flag / IntFlag ===")

    class Perm(IntFlag):
        R = 4   # 读
        W = 2   # 写
        X = 1   # 执行

    p = Perm.R | Perm.W  # 组合
    print("R|W =", p, "值:", int(p))
    print("包含 W:", Perm.W in p)
    print("R & W =", Perm.R & Perm.W)  # 0


# =============================================================================
# 第五部分：dataclasses 模块（进阶）
# =============================================================================
# [Java 对比] dataclass 对应 Java 14+ 的 record，自动生成 __init__/__repr__/__eq__。
#             但 dataclass 更灵活，支持可变字段、默认工厂等。

def demo_dataclass_basic():
    """@dataclass 基础。"""
    print("\n=== dataclass 基础 ===")

    @dataclass
    class Point:
        x: int
        y: int

    p = Point(1, 2)
    print("构造:", p)
    print("相等:", Point(1, 2) == p)  # 自动生成 __eq__


def demo_dataclass_field():
    """field() 默认值与 default_factory。

    [注意] 可变默认值（如 list）必须用 default_factory，否则所有实例共享。
    """
    print("\n=== dataclass field ===")

    @dataclass
    class Student:
        name: str
        scores: list = field(default_factory=list)  # 每个实例独立 list
        grade: str = "A"

    s1 = Student("Alice")
    s1.scores.append(90)
    s2 = Student("Bob")
    print("s1:", s1, "s2:", s2)  # s2.scores 不受影响


def demo_dataclass_frozen():
    """frozen=True 不可变。"""
    print("\n=== dataclass frozen ===")

    @dataclass(frozen=True)
    class Coordinate:
        lat: float
        lon: float

    c = Coordinate(39.9, 116.4)
    print("frozen:", c)
    try:
        c.lat = 40.0  # 会抛 FrozenInstanceError
    except Exception as e:
        print("修改失败:", type(e).__name__)


def demo_dataclass_post_init():
    """__post_init__ 后处理。"""
    print("\n=== dataclass __post_init__ ===")

    @dataclass
    class Rectangle:
        width: float
        height: float
        area: float = 0.0

        def __post_init__(self):
            # 在 __init__ 后自动调用，用于计算派生字段
            self.area = self.width * self.height

    r = Rectangle(3, 4)
    print("area 自动计算:", r.area)


def demo_dataclass_inherit():
    """继承 dataclass。"""
    print("\n=== dataclass 继承 ===")

    @dataclass
    class Base:
        x: int = 0

    @dataclass
    class Child(Base):
        y: int = 0
        # [注意] 父类有默认值时，子类新增字段也应有默认值或排在后面

    c = Child(x=1, y=2)
    print("继承:", c)


def demo_dataclass_slots():
    """slots=True (3.10+) 节省内存、禁止动态属性。"""
    print("\n=== dataclass slots ===")

    @dataclass(slots=True)
    class Slim:
        a: int
        b: int

    s = Slim(1, 2)
    print("slots:", s)
    try:
        s.c = 3  # 不允许新增属性
    except AttributeError as e:
        print("禁止新增属性:", e)


def demo_dataclass_helpers():
    """asdict / astuple / replace。"""
    print("\n=== dataclass 辅助函数 ===")

    @dataclass
    class Item:
        name: str
        qty: int

    it = Item("apple", 5)
    print("asdict:", asdict(it))
    print("astuple:", astuple(it))
    # replace 生成修改后的新实例（不改变原对象）
    it2 = replace(it, qty=10)
    print("replace:", it2, "原对象:", it)


# =============================================================================
# 第六部分：typing 模块（实战用法）
# =============================================================================
# [Java 对比] typing 对应 Java 的泛型系统，但 Python 是"渐进式类型"（运行时不强制）。
#             类型注解主要用于静态检查（mypy / IDE）。

def demo_typing_basic():
    """常用类型：Optional, Union, List, Dict, Tuple, Set。"""
    print("\n=== typing 基础 ===")
    # Optional[X] 等价于 Union[X, None]
    def greet(name: Optional[str] = None) -> str:
        return f"Hi, {name or 'Guest'}"
    print(greet(), "|", greet("Tom"))

    # Union 多类型
    def process(x: Union[int, str]) -> int:
        return len(str(x)) if isinstance(x, str) else x
    print("Union:", process(10), process("abc"))

    # 3.10+ 可用 X | Y 语法
    # def f(x: int | str) -> int: ...


def demo_typing_callable():
    """Callable, Any, TypeVar。"""
    print("\n=== typing Callable / Any / TypeVar ===")
    # Callable[[参数类型], 返回类型]
    def apply(fn: Callable[[int], int], x: int) -> int:
        return fn(x)
    print("apply:", apply(lambda n: n * 2, 5))

    # Any 表示任意类型（尽量少用）
    def echo(x: Any) -> Any:
        return x
    print("Any:", echo(123))

    # TypeVar 泛型类型变量
    T = TypeVar("T")
    def first(lst: list[T]) -> T:  # 3.12+ 可直接用 list[T]
        return lst[0]
    print("first:", first([1, 2, 3]))


def demo_typing_generic():
    """Generic 与泛型容器。"""
    print("\n=== typing Generic ===")

    T = TypeVar("T")

    class Stack(Generic[T]):
        def __init__(self):
            self._items: list[T] = []
        def push(self, item: T) -> None:
            self._items.append(item)
        def pop(self) -> T:
            return self._items.pop()

    s: Stack[int] = Stack()
    s.push(1)
    s.push(2)
    print("Generic Stack pop:", s.pop())


def demo_typing_protocol():
    """Protocol 结构化子类型（鸭子类型的静态版）。"""
    print("\n=== typing Protocol ===")

    @runtime_checkable
    class Drawable(Protocol):
        def draw(self) -> str: ...

    class Circle:
        def draw(self) -> str:
            return "画圆"

    class Square:
        def draw(self) -> str:
            return "画方"

    def render(obj: Drawable) -> None:
        print("渲染:", obj.draw())

    # Circle/Square 无需继承 Drawable，只要实现了 draw 方法即可
    render(Circle())
    render(Square())
    print("Circle 是 Drawable:", isinstance(Circle(), Drawable))


def demo_typing_literal_final():
    """Literal, Final, TypedDict。"""
    print("\n=== typing Literal / Final / TypedDict ===")
    # Literal 限定字面量值
    def set_mode(mode: Literal["r", "w", "a"]) -> str:
        return f"模式: {mode}"
    print("Literal:", set_mode("w"))

    # Final 不可重新赋值（静态检查层面）
    MAX_SIZE: Final[int] = 100
    print("Final:", MAX_SIZE)


def demo_typing_typeddict():
    """TypedDict 给字典加类型约束。"""
    print("\n=== typing TypedDict ===")

    class UserDict(TypedDict):
        name: str
        age: int

    u: UserDict = {"name": "Alice", "age": 25}
    print("TypedDict:", u)


def demo_typing_newtype():
    """NewType 创建语义不同的类型别名。"""
    print("\n=== typing NewType ===")
    UserId = NewType("UserId", int)
    uid = UserId(1001)  # 运行时仍是 int，但静态检查可区分
    print("NewType:", uid, "类型:", type(uid).__name__)


def demo_typing_alias():
    """类型别名与 TypeAlias (3.10+)。"""
    print("\n=== typing 类型别名 ===")
    # 简单别名
    Vector = list[float]  # 3.9+ 内置泛型
    v: Vector = [1.0, 2.0, 3.0]
    print("Vector:", v)

    # TypeAlias 显式声明（3.10+）
    # Matrix: TypeAlias = list[list[float]]


# =============================================================================
# 主入口
# =============================================================================
def main():
    """运行所有 demo。"""
    print("=" * 70)
    print("Python 标准库数据处理模块演示 - 面向 Java 开发者")
    print("=" * 70)

    # re
    demo_re_basic()
    demo_re_findall()
    demo_re_sub()
    demo_re_split()
    demo_re_compile()
    demo_re_group()
    demo_re_greedy()
    demo_re_assertion()
    demo_re_flags()

    # json
    demo_json_dumps()
    demo_json_loads()
    demo_json_file()
    demo_json_custom_encoder()
    demo_json_custom_decoder()
    demo_json_type_map()

    # datetime
    demo_datetime_now()
    demo_datetime_construct()
    demo_datetime_format()
    demo_datetime_timedelta()
    demo_datetime_date_time()
    demo_datetime_timezone()
    demo_datetime_timestamp()

    # enum
    demo_enum_basic()
    demo_enum_intenum()
    demo_enum_auto()
    demo_enum_custom()
    demo_enum_flag()

    # dataclasses
    demo_dataclass_basic()
    demo_dataclass_field()
    demo_dataclass_frozen()
    demo_dataclass_post_init()
    demo_dataclass_inherit()
    demo_dataclass_slots()
    demo_dataclass_helpers()

    # typing
    demo_typing_basic()
    demo_typing_callable()
    demo_typing_generic()
    demo_typing_protocol()
    demo_typing_literal_final()
    demo_typing_typeddict()
    demo_typing_newtype()
    demo_typing_alias()

    print("\n" + "=" * 70)
    print("所有 demo 运行完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
