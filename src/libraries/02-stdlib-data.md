# 标准库数据处理

本章覆盖 Python 处理结构化数据时最常用的六个模块：`re`、`json`、`datetime`、`enum`、`dataclasses`、`typing`。
对应 Java 的 `java.util.regex`、Jackson、`java.time`、`enum`、`record`、泛型系统。

## 总览：Python ↔ Java 对应表

| Python 模块 | Java 对应 | 用途 / 关键差异 |
|-------------|-----------|-----------------|
| `re` | `java.util.regex` | 语法基本兼容，命名分组写作 `(?P<name>...)` |
| `json` | Jackson `ObjectMapper` | 只认识基础类型，复杂对象必须自己挂 hook |
| `datetime` | `java.time` | 模块名与类名同名，导入方式容易踩坑 |
| `enum` | `enum` | ⚠️ Python 的 `Enum` **不能**和 `int` 比较 |
| `dataclasses` | `record` | 字段**默认可变**，可变默认值必须用工厂 |
| `typing` | 泛型系统 | 运行期不强制，靠 mypy / IDE 检查 |

> [示例](../code/libraries/02_stdlib_data.py)

## re：正则表达式

### 三个匹配入口与查找替换

Java 的 `Matcher` 只有 `matches()`（整串）和 `find()`（任意位置），Python 多了一个「从头匹配」：

> [re 基础匹配演示](../code/libraries/02_stdlib_data.py#L41-L62) ·
> [findall 演示](../code/libraries/02_stdlib_data.py#L65-L77) ·
> [sub 演示](../code/libraries/02_stdlib_data.py#L80-L94) ·
> [split 演示](../code/libraries/02_stdlib_data.py#L97-L107)

```python
{{#include ../code/libraries/02_stdlib_data.py:97:107}}
```

| Python | Java 对应 | 语义 |
|--------|-----------|------|
| `re.match(p, s)` | `matcher.lookingAt()` | 只从**开头**匹配，不要求整串 |
| `re.search(p, s)` | `matcher.find()` | 任意位置找第一个 |
| `re.fullmatch(p, s)` | `matcher.matches()` | 整串必须完全匹配 |

```python
re.findall(r"(\d{3})-(\d{4})", text)   # 有分组时返回 tuple 列表
re.subn(r"\d+", "N", text)             # 返回 (结果, 替换次数)，Java 需自己数
re.split(r"([,;])", "a,b;c")           # 保留分隔符：Python 特有
```

> ⚠️ 这是 Java 开发者最常犯的错：Java 的 `String.matches()` 是**整串匹配**，
> 而 Python 长得最像的 `re.match()` 是**前缀匹配**——`re.match(r"Hello", "Hello World")` 会成功。
> 要做 Java `matches()` 那种严格校验，必须用 `re.fullmatch()`。
>
> `re.findall` 另有个坑：**有分组时返回分组内容而不是整段匹配**；只有一个分组时返回字符串列表，
> 两个以上分组才返回 tuple 列表。

### 预编译、命名分组与断言

> [re.compile 演示](../code/libraries/02_stdlib_data.py#L110-L120) ·
> [分组演示](../code/libraries/02_stdlib_data.py#L123-L134) ·
> [贪婪演示](../code/libraries/02_stdlib_data.py#L137-L144) ·
> [零宽断言演示](../code/libraries/02_stdlib_data.py#L147-L162)

```python
{{#include ../code/libraries/02_stdlib_data.py:147:162}}
```

```python
pattern = re.compile(r"\b\w{4}\b")                  # 对应 Pattern.compile()
m = re.match(r"(?P<name>\w+),\s*(?P<age>\d+)岁", text)
m.group("name"), m.groupdict()         # 按名字取 / {'name': '张三', 'age': '25'}

re.findall(r"<a>(.*)</a>", html)       # 贪婪：['1</a><a>2']
re.findall(r"(?<=\$)\d+", "price: $100")   # 后行断言：前面是 $
re.findall(r"\w+(?=,)", "a,b,c")           # 先行断言：后面是逗号
```

> ⚠️ 命名分组语法是 `(?P<name>...)`，**不是** Java 的 `(?<name>...)`。
> `re` 内部有 512 条编译缓存，小规模场景不预编译也没事；但 `re` **不支持递归**（那是第三方 `regex` 库的能力）。

### flags

> [flags 演示](../code/libraries/02_stdlib_data.py#L165-L193)

```python
{{#include ../code/libraries/02_stdlib_data.py:165:193}}
```

```python
re.findall(r"hello", "Hello", re.IGNORECASE)
re.findall(r"^line\d", text, re.MULTILINE)   # ^ $ 按行匹配
re.compile(r"""\d{3}  # 区号
               -      # 分隔符""", re.VERBOSE)  # 多行注释模式，对应 Pattern.COMMENTS
```

## json：序列化

对应 Jackson 的 `ObjectMapper`，但它是**零配置**的：没有注解、没有反射、也没有类型推导。

> ⚠️ `ensure_ascii=True` 是**默认值**，中文会被转成 `\u5f20\u4e09`。Jackson 默认输出原始 UTF-8，
> 所以你会发现「同样的对象，Python 输出一堆转义字符」。几乎每个项目第一件事就是在封装层关掉它。

> [dumps 演示](../code/libraries/02_stdlib_data.py#L195-L211) ·
> [loads 演示](../code/libraries/02_stdlib_data.py#L214-L220) ·
> [类型映射演示](../code/libraries/02_stdlib_data.py#L276-L286) ·
> [自定义编码器演示](../code/libraries/02_stdlib_data.py#L241-L257) ·
> [自定义解码器演示](../code/libraries/02_stdlib_data.py#L260-L273)

```python
{{#include ../code/libraries/02_stdlib_data.py:260:273}}
```

```python
json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
json.loads('{"name": "李四"}')   # 永远返回 dict / list / str / int / float / bool / None

class MyEncoder(json.JSONEncoder):
    def default(self, obj):          # 只对「不认识的对象」调用，对应 @JsonSerialize
        if isinstance(obj, (dt, date)):
            return obj.isoformat()
        return super().default(obj)  # 其余交给父类抛 TypeError

def as_date(dct):                    # object_hook 作用于每一个 JSON object
    if "__date__" in dct:
        return date.fromisoformat(dct["__date__"])
    return dct
json.loads(s, object_hook=as_date)
```

| JSON | Python | Java |
|------|--------|------|
| `object` / `array` | `dict` / `list` | `Map` / `List` |
| `number` | `int` / `float` | `Integer` / `Double` |
| `true` / `false` / `null` | `True` / `False` / `None` | `Boolean` / `null` |

> ⚠️ 和 Jackson 最大的架构差异：Jackson 能靠 `Class<T>` + 反射把 JSON 直接变成 POJO；`json.loads` 只给你一堆裸 `dict`，
> **没有任何类型信息**。`object_hook` 的入参也永远是 `dict`，**无法**直接造出自定义类——这正是 Pydantic 存在的理由。
> 另外 `tuple` / `set` / `bytes` / `datetime` 全都不是 JSON 原生类型；文件读写 `json.dump` / `json.load` 同样要传 `encoding="utf-8"`。

## datetime：日期时间

对应 `java.time`。两者都**不可变、线程安全**，这是和旧的 `java.util.Date` / `Calendar` 的本质区别。

### ⚠️ 导入陷阱与构造

标准库的模块叫 `datetime`，里面的类也有一大半叫 `datetime`：

> [now 演示](../code/libraries/02_stdlib_data.py#L295-L301) ·
> [构造演示](../code/libraries/02_stdlib_data.py#L304-L312)

```python
{{#include ../code/libraries/02_stdlib_data.py:304:312}}
```

```python
import datetime
datetime.datetime.now()            # 模块.类.方法

from datetime import datetime as dt
dt.now()                           # 别名导入，本书统一采用
```

Java 里 `java.time.LocalDateTime` 不会和包名撞车，Python 会。`utcnow()` 从 3.12 起已弃用，请改用 `dt.now(timezone.utc)`。

### 格式化、timedelta、时区与时间戳

> [格式化演示](../code/libraries/02_stdlib_data.py#L315-L329) ·
> [timedelta 演示](../code/libraries/02_stdlib_data.py#L332-L343) ·
> [时区演示](../code/libraries/02_stdlib_data.py#L357-L373) ·
> [时间戳演示](../code/libraries/02_stdlib_data.py#L376-L391)

```python
{{#include ../code/libraries/02_stdlib_data.py:376:391}}
```

```python
d.strftime("%Y年%m月%d日 %H:%M:%S")
dt.strptime("2024-01-15 10:30:00", "%Y-%m-%d %H:%M:%S")
d1 + timedelta(weeks=1)               # d2 - d1 得到 timedelta(days=5)
d_ny = dt(2024, 1, 15, 10, 30, tzinfo=ZoneInfo("America/New_York"))   # 3.9+
d_ny.astimezone(ZoneInfo("Asia/Shanghai"))                            # 转时区
ts = dt(2024, 1, 15, 10, 30).timestamp()   # 秒（float）, naive 会按本地时区解释
```

| Java `DateTimeFormatter` | Python `strftime` | 差异 |
|--------------------------|-------------------|------|
| `yyyy` / `MM` / `dd` | `%Y` / `%m` / `%d` | 注意 `%Y` 是**大写** |
| `HH` / `mm` / `ss` | `%H` / `%M` / `%S` | ⚠️ `%m` 是月、`%M` 是分 |
| `EEE` | `%a` | 星期缩写 |

> ⚠️ 模板字母大小写含义完全不同（`%y` 两位年 / `%Y` 四位年）；`strftime` 还依赖 C 库实现，
> 跨平台上 `%z`（时区偏移）的输出格式并不一致。

`timedelta` 是 Java `Duration` / `Period` 的**合体**，最小单位是微秒，不支持「一个月」「一年」这种日历语义。
`ZoneInfo` 对应 `ZoneId`，用 IANA 时区名而不是缩写。

> ⚠️ **naive 与 aware 是 Python 独有的概念**：不带 `tzinfo` 的 `datetime` 没有任何时区含义，
> 但 `.timestamp()` 照样能调，会默默按本地时区解释——然后给你一个可能错 8 小时的数字。
> Java 的 `LocalDateTime` 压根不提供 `toEpochSecond()`，强迫你想清楚。**涉及服务器时一律用 aware datetime。**

## enum：枚举

对应 Java `enum`，但**没有**「枚举带构造器并直接实现接口」那套单例模式玩法。

### 基础、IntEnum 与 auto

> [Enum 演示](../code/libraries/02_stdlib_data.py#L393-L409) ·
> [IntEnum 演示](../code/libraries/02_stdlib_data.py#L412-L424) ·
> [auto 演示](../code/libraries/02_stdlib_data.py#L427-L438)

```python
{{#include ../code/libraries/02_stdlib_data.py:427:438}}
```

```python
class Color(Enum):
    RED = 1
Color.RED.name, Color.RED.value    # 'RED', 1
Color(2), Color["RED"]             # 按值 / 按名查找

class Status(IntEnum):
    OK = 200
Status.OK == 200                   # True，只有 IntEnum 能和 int 比
```

> ⚠️ `Color.RED == 1` 是 **False**，而且**不报错**。所以 `if status == 200` 这种写法在普通 `Enum` 上会静默失败，
> 排查起来极其费时。需要数值语义就用 `IntEnum`。
>
> 另一个区别：Java 里 `enum` 常当配置值集合用，Python 里更常见的是模块级常量或 `Literal`。

### 自定义值与 Flag

> [自定义值演示](../code/libraries/02_stdlib_data.py#L441-L456) ·
> [Flag 演示](../code/libraries/02_stdlib_data.py#L459-L481)

```python
{{#include ../code/libraries/02_stdlib_data.py:459:481}}
```

```python
class Planet(Enum):
    EARTH = (3, "地球", 5.976e24)
    def __init__(self, num, cn_name, mass):
        self.num, self.cn_name, self.mass = num, cn_name, mass

class Perm(IntFlag):
    R, W, X = 4, 2, 1
p = Perm.R | Perm.W     # 位运算组合
Perm.W in p             # True
```

`IntFlag` 对应 Java 的 `EnumSet<Perm>`，但语法上是**原生位运算**——`|` 直接得到成员，`in` 就是「位是否被置上」。

## dataclasses：数据类

最接近 Java 14+ 的 `record`，但**默认可变**，这是最大的语义反差。

> [基础演示](../code/libraries/02_stdlib_data.py#L483-L494) ·
> [field 演示](../code/libraries/02_stdlib_data.py#L497-L513) ·
> [frozen 演示](../code/libraries/02_stdlib_data.py#L516-L530) ·
> [__post_init__ 演示](../code/libraries/02_stdlib_data.py#L533-L548) ·
> [继承演示](../code/libraries/02_stdlib_data.py#L551-L565) ·
> [slots 演示](../code/libraries/02_stdlib_data.py#L568-L582) ·
> [辅助函数演示](../code/libraries/02_stdlib_data.py#L585-L606)

```python
{{#include ../code/libraries/02_stdlib_data.py:585:606}}
```

```python
@dataclass
class Point:
    x: int
    y: int
Point(1, 2) == Point(1, 2)          # True，自动生成 __eq__（按字段比较）

@dataclass
class Student:
    name: str
    scores: list = field(default_factory=list)   # 必须！写 scores: list = [] 会直接报错

@dataclass(frozen=True)
class Coordinate:
    lat: float
    lon: float
# c.lat = 40.0  →  FrozenInstanceError（注意：不是 AttributeError）

@dataclass
class Rectangle:
    width: float
    height: float
    area: float = 0.0
    def __post_init__(self):        # 相当于 record 的紧凑构造器
        self.area = self.width * self.height
asdict(it), astuple(it), replace(it, qty=10)
```

| 特性 | `@dataclass` | Java `record` |
|------|--------------|---------------|
| 可变性 | **默认可变**，`frozen=True` 才不可变 | 永远不可变 |
| 相等性 | 自动 `__eq__` | 自动 `equals` / `hashCode` |
| 哈希 | `frozen=True` 时才生成 `__hash__` | 永远可哈希 |
| 内存 | 有 `__dict__`，可用 `slots=True` 优化 | JVM 对象头 |

> ⚠️ 可变默认值其实是 Python 函数默认参数坑的延伸。好消息是 `@dataclass` 会主动检测并抛 `ValueError`
> （不像普通函数会静默共享同一个 list）。
>
> `frozen=True` 之后 `__post_init__` 里的 `self.x = ...` 也会失败，必须用 `object.__setattr__` 绕过。
> 另外继承时「有默认值的字段不能排在无默认值字段前面」——纯粹是 Python 函数参数顺序限制的体现。
>
> `slots=True`（3.10+）会去掉 `__dict__`，因此 `cached_property`、动态属性、随意赋值全部失效。

## typing：类型注解

注解**运行期不强制执行**，只服务于静态检查。完整机制见 [类型系统与静态检查](../advanced/01-type-system.md)，这里只讲实战写法。

> [基础演示](../code/libraries/02_stdlib_data.py#L608-L619) ·
> [Callable 演示](../code/libraries/02_stdlib_data.py#L625-L642) ·
> [Generic 演示](../code/libraries/02_stdlib_data.py#L645-L662) ·
> [Protocol 演示](../code/libraries/02_stdlib_data.py#L665-L687) ·
> [Literal / Final 演示](../code/libraries/02_stdlib_data.py#L690-L700) ·
> [TypedDict 演示](../code/libraries/02_stdlib_data.py#L703-L712) ·
> [NewType 演示](../code/libraries/02_stdlib_data.py#L715-L720)

```python
{{#include ../code/libraries/02_stdlib_data.py:715:720}}
```

```python
def greet(name: Optional[str] = None) -> str: ...
def process(x: Union[int, str]) -> int: ...
def f(x: int | str) -> int: ...                 # 3.10+ 的简写
def apply(fn: Callable[[int], int], x: int) -> int: ...
def set_mode(mode: Literal["r", "w", "a"]) -> str: ...    # 比 enum 轻量
MAX_SIZE: Final[int] = 100

class UserDict(TypedDict):          # 给「本来就是 dict 的 JSON」加类型
    name: str
    age: int
UserId = NewType("UserId", int)     # 运行期就是 int，静态检查视为不同类型

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> str: ...
isinstance(Circle(), Drawable)    # True，只要形状匹配（无需继承）
```

`Protocol` 是**结构化子类型**：`Circle` 不继承 `Drawable` 也算数，只要方法签名匹配，而 Java `interface` 必须 `implements`。
`Generic[T]` 对应 Java 的 `<T>`；`TypedDict` 运行期零开销但 static 检查能揪出拼错的键；
`NewType` 则在静态层面区分 `UserId` 和 `OrderId`，避免「两个 int 传反了」。

> ⚠️ `isinstance` 检查 `Protocol` 需要 `@runtime_checkable`，而且它**只检查方法名是否存在**，
> 不检查参数和返回类型——`isinstance` 通过不代表类型真的对得上。

## 小结

- **`re.match` 是前缀匹配**，Java `matches()` 的等价物是 `re.fullmatch`；命名分组用 `(?P<name>...)`
- **`json.dumps` 默认转义非 ASCII**，要 `ensure_ascii=False`；`json.loads` 只给裸 `dict`，没有类型信息
- **别写 `import datetime` 然后到处 `datetime.datetime`**；naive datetime 的 `.timestamp()` 会按本地时区猜测
- **普通 `Enum` 不与 `int` 比较且不报错**，需要数值语义就用 `IntEnum` / `IntFlag`
- **dataclass 默认可变**，可变默认值必须用 `default_factory`；`frozen=True` 时 `__post_init__` 也不能赋值
- **`TypedDict` 是给 JSON 加类型的最省事方案**，`Protocol` 提供 Java interface 没有的结构化子类型

> 📁 [查看完整代码](../code/libraries/02_stdlib_data.py)
