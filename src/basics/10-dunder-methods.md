# 特殊方法（dunder methods）

Python 的面向对象能力和 Java 有一个根本差异：

| | Java | Python |
|---|---|---|
| 能力来源 | 接口 + 继承 | **协议 + 特殊方法** |
| 排序 | 必须 `implements Comparable` | 有 `__lt__` 就能 `sorted()` |
| 长度 | 必须实现 `Collection` | 有 `__len__` 就能 `len()` |

**不需要声明 implements 任何东西**——只要方法存在，操作就自动可用。这是鸭子类型在语言层面的体现。

## 速查表

> [完整速查](../code/basics/10_dunder_methods.py#L52-L70)

```python
{{#include ../code/basics/10_dunder_methods.py:52:70}}
```

| 分组 | 方法 |
|------|------|
| **对象表示** | `__repr__` `__str__` `__format__` `__bytes__` `__fspath__` |
| **比较** | `__eq__` `__ne__` `__lt__` `__le__` `__gt__` `__ge__` `__hash__` `__bool__` |
| **容器** | `__len__` `__getitem__` `__setitem__` `__delitem__` `__contains__` `__reversed__` `__missing__` |
| **迭代** | `__iter__` `__next__` `__aiter__` `__anext__` |
| **算术** | `__add__` `__radd__` `__iadd__` `__sub__` `__mul__` `__truediv__` `__neg__` 等 |
| **属性访问** | `__getattr__` `__getattribute__` `__setattr__` `__delattr__` `__dir__` |
| **生命周期** | `__new__` `__init__` `__del__` `__init_subclass__` `__class_getitem__` |
| **可调用/上下文** | `__call__` `__enter__` `__exit__` `__aenter__` `__aexit__` |

> 本教程只讲最常用的 30 个左右，Python 全部约 80+。

## 对象表示

> [表示方法演示](../code/basics/10_dunder_methods.py#L72-L119)

```python
{{#include ../code/basics/10_dunder_methods.py:72:119}}
```

```python
class Money:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        return f"Money({self.amount!r}, {self.currency!r})"   # 开发者

    def __str__(self):
        return f"{self.amount} {self.currency}"               # 用户
```

实际差异：

```python
repr(m)      # "Money(99.5, 'CNY')"     ← 开发者视角
str(m)       # '99.5 CNY'              ← 用户视角
[m, Money(1)]  # 容器里显示 repr
```

### 三个方法的定位

| 方法 | 给谁看 | Java 对应 |
|------|--------|-----------|
| `__repr__` | **开发者**，应能重建对象 | `toString()` |
| `__str__` | **终端用户**，可读性优先 | 无 |
| `__format__` | `f"{obj:.2f}"` 的格式说明符 | 无 |

### `__str__` 缺失时会退回 `__repr__`

```python
class Empty: pass
repr(Empty())    # '<__main__.Empty object at 0x...>'  ← 调试毫无帮助
```

> [要点] **至少实现 `__repr__`**。这是调试的基础，比 `__str__` 更重要。

### `__format__`

> [format 演示](../code/basics/10_dunder_methods.py#L72-L119)

```python
{{#include ../code/basics/10_dunder_methods.py:72:119}}
```

```python
def __format__(self, spec):
    if spec.endswith("f"):
        return f"{self.amount:{spec}} {self.currency}"
    return str(self)

f"{m:.2f}"    # '99.50 CNY'
```

## 比较与哈希

> [`__eq__`/`__hash__` 演示](../code/basics/10_dunder_methods.py#L121-L180)

```python
{{#include ../code/basics/10_dunder_methods.py:121:180}}
```

### ⚠️ 定义 `__eq__` 会让对象变成不可哈希

```python
class BadPoint:
    def __eq__(self, other):
        return self.x == other.x

{BadPoint(1)}    # TypeError: unhashable type: 'BadPoint'
```

因为 Python 自动把 `BadPoint.__hash__` 设为 `None`。

### 配套规则

> **`a == b` 为 True 时，`hash(a)` 必须等于 `hash(b)`**

| 对象类型 | 做法 |
|---------|------|
| **不可变**（`Point`、`Money`） | 实现 `__eq__` + `__hash__`，可放进 set/dict |
| **可变**（列表式容器） | 只实现 `__eq__`，显式 `__hash__ = None` |

```python
class Point:
    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented      # ✅ 不是 return False
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))
```

### ⚠️ `return NotImplemented` 而非 `False`

这是最容易搞错的细节：

| 写法 | 结果 |
|------|------|
| `return False` | 立刻判定不相等，**不给对方机会** |
| `return NotImplemented` | 告诉 Python "我不认识他，试试对方的 `__eq__`" |
| `raise NotImplementedError` | ❌ 直接抛异常，破坏协议 |

> 详见[常见陷阱第 14 条](../practice/03-pitfalls.md)。

### 排序只需 `__eq__` + `__lt__`

> [排序演示](../code/basics/10_dunder_methods.py#L183-L220)

```python
{{#include ../code/basics/10_dunder_methods.py:183:220}}
```

```python
sorted([Version([1,10]), Version([1,2])])    # 实现 __lt__ 即可
```

或者用 `functools.total_ordering` 自动补齐其余 4 个比较方法：

```python
@total_ordering
class V2:
    def __eq__(self, o): return self.n == o.n
    def __lt__(self, o): return self.n < o.n
# 现在 >= > <= 都能用了
```

## 容器协议

> [容器协议演示](../code/basics/10_dunder_methods.py#L222-L271)

```python
{{#include ../code/basics/10_dunder_methods.py:222:271}}
```

```python
class Playlist:
    def __len__(self): return len(self._songs)
    def __getitem__(self, i): return self._songs[i]      # 支持索引和切片
    def __contains__(self, item): return item in self._songs
    def __reversed__(self): return reversed(self._songs)
    def __iter__(self): return iter(self._songs)
```

### 方法的回退关系

| 缺失的方法 | 回退行为 |
|-----------|---------|
| `__contains__` | 用 `__iter__` 遍历 |
| `__iter__` | 用 `__getitem__(0..n)` 直到 `IndexError` |

所以**只实现 `__getitem__` 也能被 `for` 遍历**（但效率低）：

```python
class OnlyGetitem:
    def __getitem__(self, i):
        if i >= 3: raise IndexError
        return i * 10

[x for x in OnlyGetitem()]    # [0, 10, 20]
```

### `__missing__`：字典默认值

> [`__missing__` 演示](../code/basics/10_dunder_methods.py#L274-L296)

```python
{{#include ../code/basics/10_dunder_methods.py:274:296}}
```

```python
class DefaultDict(dict):
    def __missing__(self, key):
        value = f"<default for {key}>"
        self[key] = value        # 顺便写回
        return value
```

> ⚠️ 只对 `d[key]` 生效，`d.get(key)` **不会**触发。

> [Java 对比] 对应 `Map.computeIfAbsent`，但 Python 更透明。

## 算术运算

> [算术演示](../code/basics/10_dunder_methods.py#L298-L349)

```python
{{#include ../code/basics/10_dunder_methods.py:298:349}}
```

三个容易混的方法：

| 方法 | 触发时机 | 典型实现 |
|------|---------|---------|
| `__add__` | `a + b` | 返回新对象 |
| `__radd__` | `b + a`，且 `b.__add__` 返回 `NotImplemented` | 处理 `1 + obj` |
| `__iadd__` | `a += b` | 原地修改并返回 `self` |

```python
class Vec:
    def __add__(self, other):        # Vec + Vec
        if isinstance(other, Vec):
            return Vec(self.x + other.x, self.y + other.y)
        return NotImplemented

    def __radd__(self, other):       # 1 + Vec
        if isinstance(other, (int, float)):
            return Vec(self.x + other, self.y + other)
        return NotImplemented

    def __iadd__(self, other):       # Vec += 10，原地
        self.x += other
        return self
```

实测：

```python
v1 + v2    # [__add__]  -> Vec(4, 6)
1 + v1     # [__radd__] -> Vec(2, 3)    int 不知道怎么加 Vec，转给 Vec
v1 += 10   # [__iadd__] -> 原地，id 不变
```

> ⚠️ 不可变类型（`str`、`tuple`）**不应**实现 `__iadd__` 原地修改。

> [Java 对比] Java 无法重载 `+` 运算符，只能写 `add()` 方法。

## 属性访问

**这是本章最需要记清的一节。**

> [`__getattr__` vs `__getattribute__`](../code/basics/10_dunder_methods.py#L351-L421)

```python
{{#include ../code/basics/10_dunder_methods.py:351:421}}
```

```python
class WithGetattr:
    def __init__(self): self.x = 1
    def __getattr__(self, name):
        return f"<dynamic {name}>"

a = WithGetattr()
a.x      # 1           ← 不触发
a.y      # 触发！返回 '<dynamic y>'
```

```python
class WithGetattribute:
    def __init__(self): self.x = 1
    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

b = WithGetattribute()
b.x      # 也触发！每次访问都调用
```

### 对比表

| 方法 | 调用时机 |
|------|---------|
| `__getattribute__` | **每次**属性访问都调用（含存在的属性） |
| `__getattr__` | 只在**常规查找失败**后调用 |

### 选择建议

| 场景 | 用哪个 |
|------|--------|
| 代理对象、ORM 动态字段 | ✅ `__getattr__` |
| 需要拦截**所有**访问（极少） | `__getattribute__` |

> ⚠️ `__getattribute__` 极易造成**无限递归**：

```python
def __getattribute__(self, name):
    return self.__dict__[name]        # ❌ self.__dict__ 又触发自己
    # 正确：object.__getattribute__(self, name)
```

### 实战：代理对象

```python
class Proxy:
    def __init__(self, target):
        object.__setattr__(self, "_target", target)

    def __getattr__(self, name):
        return getattr(self._target, name)
```

> [Java 对比] 类似 AOP 的 around 拦截，但 Python 是语言内置，不需要动态代理。

## 创建与销毁

> [`__new__` vs `__init__`](../code/basics/10_dunder_methods.py#L423-L471)

```python
{{#include ../code/basics/10_dunder_methods.py:423:471}}
```

```python
class Tracked:
    def __new__(cls, *args, **kwargs):
        print("[__new__] 创建实例前")
        return super().__new__(cls)      # 实际创建

    def __init__(self, value):
        print("[__init__] 实例已存在")
        self.value = value
```

### 分工

| 方法 | 职责 | 返回值 |
|------|------|--------|
| `__new__` | **创建**实例 | 实例对象 |
| `__init__` | **初始化**实例 | `None` |

### 何时需要 `__new__`

**① 单例**

```python
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**② 校验不可变类型**（值在创建时就固定，改不了 `__init__`）

```python
class PositiveInt(int):
    def __new__(cls, value):
        if value < 0:
            raise ValueError("必须为非负")
        return super().__new__(cls, value)
```

### ⚠️ `__del__` 不可靠

> [`__del__` 演示](../code/basics/10_dunder_methods.py#L474-L520)

```python
{{#include ../code/basics/10_dunder_methods.py:474:520}}
```

三个不可靠之处：

| 问题 | 说明 |
|------|------|
| 循环引用 | 可能永远不调用，要等 GC |
| 解释器退出 | 调用顺序不确定 |
| 异常发生时 | 执行路径无法保证 |

实测循环引用：

```python
a, b = Node(), Node()
a.other, b.other = b, a
del a, b
# 此时 __del__ 未调用
gc.collect()    # 手动 GC 后才回收
```

> ✅ **正确做法**：用 `with` / `contextlib` 显式释放，不要依赖 `__del__`。

> [Java 对比] Java 的 `finalize()` 同样不可靠，JDK 9 起已 deprecated。

## 可调用

> [`__call__` 演示](../code/basics/10_dunder_methods.py#L522-L558)

```python
{{#include ../code/basics/10_dunder_methods.py:522:558}}
```

```python
class Multiplier:
    def __init__(self, factor):
        self.factor = factor
    def __call__(self, x):
        return x * self.factor

double = Multiplier(2)
double(5)          # 10      ← 实例像函数一样调用
callable(double)   # True
```

### 与闭包的取舍

| | `__call__` | 闭包 |
|---|---|---|
| 状态可读 | ✅ `double.factor` | ❌ 藏在闭包里 |
| 可继承/加方法 | ✅ | ❌ |
| 代码量 | 多 | 少 |

> [场景] 有状态的函数、装饰器类、策略对象。

## 常见陷阱

> [完整演示](../code/basics/10_dunder_methods.py#L560-L589)

```python
{{#include ../code/basics/10_dunder_methods.py:560:589}}
```

| 坑 | 后果 |
|---|---|
| `raise NotImplementedError` 代替 `return NotImplemented` | 破坏比较协议 |
| 定义 `__eq__` 忘了 `__hash__` | 对象变 unhashable |
| `__getattribute__` 里访问 `self.xxx` | 无限递归 |
| 用 `__del__` 释放文件/连接 | 可能永远不执行 |
| 可变对象实现 `__hash__` 后又被修改 | 在 set 里再也找不到 |
| `__len__` 返回负数 | `ValueError: __len__() should return >= 0` |

## Java 对照总表

> [完整对照](../code/basics/10_dunder_methods.py#L592-L614)

```python
{{#include ../code/basics/10_dunder_methods.py:592:614}}
```

| Python | Java | 说明 |
|--------|------|------|
| `__repr__` | `toString()` | 开发者视角，应可重建 |
| `__str__` | 无 | 用户视角 |
| `__eq__` | `equals()` | 值相等 |
| `__hash__` | `hashCode()` | 必须与 `__eq__` 一致 |
| `__lt__` | `Comparable.compareTo` | 排序 |
| `__len__` | `size()` | 容器长度 |
| `__getitem__` | `get(int)` | 索引访问 |
| `__iter__` | `Iterable.iterator()` | 迭代 |
| `__call__` | `Function.apply` | 实例可调用 |
| `__new__` | 无（`new` 关键字） | 创建实例 |
| `__init__` | 构造器 | 初始化实例 |
| `__del__` | `finalize()`（已废弃） | 均不可靠 |

## 小结

- Python 的能力靠**协议**而非继承：有方法就能用，无需 `implements`
- **至少实现 `__repr__`**，它是调试的基础
- `__eq__` 与 `__hash__` **必须配套**，否则对象不可哈希
- `__eq__` 里返回 **`NotImplemented`**（不是 `False`、不是抛异常）
- 排序只需 `__lt__`，或 `@total_ordering` 自动补齐
- **`__getattr__` 只在找不到时调用，`__getattribute__` 每次访问都调用**
- `__new__` 创建、`__init__` 初始化；单例和不可变类型才需要 `__new__`
- **不要用 `__del__` 释放资源**，用 `with`

> 相关章节：[迭代协议](04-iteration-protocol.md)、[`with` 语句](05-with-statement.md)、[类继承](09-inheritance.md)、[元编程进阶](../advanced/02-metaprogramming.md)

> 📁 [完整代码](../code/basics/10_dunder_methods.py)
