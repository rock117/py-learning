# 类继承与 `super()`

Python 的继承看起来和 Java 很像，但有两个根本差异：

1. **多继承是真的多继承**（Java 只有接口能多继承）
2. **`super()` 不是"调父类"**，而是"调 MRO 中的下一个类"

第二点是本章的核心。如果你只记住一件事，请记住它。

## 基本继承与方法重写

> [基本继承示例](../code/basics/09_inheritance.py#L36-L79)

```python
{{#include ../code/basics/09_inheritance.py:36:79}}
```

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."

    def describe(self):
        return f"{self.name} says {self.speak()}"

class Dog(Animal):
    def speak(self):          # 重写
        return "Woof"
```

`Dog("Rex").describe()` 会调用子类的 `speak()` —— 动态分派，和 Java 一致。

```python
isinstance(Dog("Rex"), Animal)      # True
```

### ⚠️ 没有 `@Override` 检查

```python
class Typo(Animal):
    def speek(self):          # 少写一个 a
        return "Typo"

Typo("X").speak()             # '...'  ← 静默用了父类实现，不报错
```

> [Java 对比] Java 的 `@Override` 会在编译期拦下拼写错误。Python 不会——**拼错方法名 = 新增了一个方法**，症状是"我的重写没生效"。

## `super()` 基础：必须调 `__init__`

> [super() 基础](../code/basics/09_inheritance.py#L81-L116)

```python
{{#include ../code/basics/09_inheritance.py:81:116}}
```

```python
class Base:
    def __init__(self, name):
        self.name = name

class GoodChild(Base):
    def __init__(self, name, age):
        super().__init__(name)      # ✅
        self.age = age

class BadChild(Base):
    def __init__(self, name, age):
        self.age = age              # ❌ 忘了 super().__init__(name)

BadChild("Bob", 25).name            # AttributeError
```

> ⚠️ 子类定义 `__init__` 会**完全覆盖**父类的，不会自动调用。

> [Java 对比] Java 子类构造器会**自动**调用父类无参构造器；Python 必须显式写。

## `super()` 的真实含义

这是最容易误解的地方。看一个例子：

> [super() 即 MRO 下一个](../code/basics/09_inheritance.py#L118-L153)

```python
{{#include ../code/basics/09_inheritance.py:118:153}}
```

```python
class A:
    def hello(self): return "A"

class B(A):
    def hello(self): return f"B -> {super().hello()}"

class C(A):
    def hello(self): return f"C -> {super().hello()}"

class D(B, C):
    def hello(self): return f"D -> {super().hello()}"
```

**单继承**时，`super()` 看起来就是"调父类"：

```
B().hello()  ->  B -> A
```

**但 `D` 同时继承 `B` 和 `C` 时**：

```
D().hello()  ->  D -> B -> C -> A
```

注意 `B` 里那句 `super().hello()` **没有回到 `A`，而是去了 `C`**。

原因：

```
D.__mro__ = [D, B, C, A, object]
```

`super()` 的真实语义是：**沿着 MRO，找到"定义 `super()` 的那个类"之后的下一个类**。

| 写法 | 实际含义 |
|------|---------|
| ~~`super()` = 调用父类~~ | ❌ 常见误解 |
| `super()` = MRO 中下一个类 | ✅ 正确理解 |

> [Java 对比] Java 的 `super.m()` 是**静态绑定**到直接父类。Python 的 `super()` 是**动态**的，取决于实例的实际类型。

### 两种写法

> [两种写法](../code/basics/09_inheritance.py#L156-L204)

```python
{{#include ../code/basics/09_inheritance.py:156:204}}
```

```python
super().greet()          # 无参（推荐）
super(B, self).greet()   # 显式，完全等价
```

无参 `super()` 是语法糖，等价于 `super(当前类, self)`。

> ⚠️ 在嵌套的**普通函数**里，无参 `super()` 会失败：

```python
class C(A):
    def greet(self):
        def inner():
            return super().greet()      # RuntimeError: super(): no arguments
        return inner()
```

因为 `inner()` 没有 `self` 参数，编译器无法生成 `super(C, self)`。解法是显式写 `super(C, self).greet()`。

## 菱形继承：协作式 `super()`

> [菱形继承演示](../code/basics/09_inheritance.py#L206-L271)

```python
{{#include ../code/basics/09_inheritance.py:206:271}}
```

```
        Base
       /    \
    Left    Right
       \    /
       Bottom
```

```python
class Base:
    def __init__(self, **kwargs):
        calls.append("Base")
        super().__init__(**kwargs)      # 继续往上走

class Left(Base):
    def __init__(self, **kwargs):
        calls.append("Left")
        super().__init__(**kwargs)

class Right(Base):
    def __init__(self, **kwargs):
        calls.append("Right")
        super().__init__(**kwargs)

class Bottom(Left, Right):
    def __init__(self):
        calls.append("Bottom")
        super().__init__()
```

实际执行顺序：

```
Bottom -> Left -> Right -> Base
```

**每个类只执行一次**，即使 `Base` 被 `Left` 和 `Right` 共享。

### 对照：硬编码父类会出错

```python
class Left2(Base2):
    def __init__(self):
        Base2.__init__(self)      # ❌ 硬编码父类

class Bottom2(Left2, Right2):
    def __init__(self):
        Left2.__init__(self)
        Right2.__init__(self)
```

实测结果：

```
Bottom2 -> Left2 -> Base2 -> Right2 -> Base2
```

`Base2` 被初始化了**两次**。

> [结论] 多继承下**必须用 `super()`**，不要写 `父类名.__init__(self)`。

## 多继承与 C3 线性化

> [C3 演示](../code/basics/09_inheritance.py#L273-L343)

```python
{{#include ../code/basics/09_inheritance.py:273:343}}
```

```
        O
      / | \
     A  B  C
      \ / \ /
       D   E
        \ /
         F
```

实际 MRO：

```
D.__mro__ = D -> A -> B -> O -> object
E.__mro__ = E -> B -> C -> O -> object
F.__mro__ = F -> D -> A -> E -> B -> C -> O -> object
```

F 的顺序看起来有点意外（`A` 排在 `E` 前面），这是因为 C3 要同时满足三条约束：

| 约束 | 含义 |
|------|------|
| 1 | 子类必须排在父类之前 |
| 2 | 多个父类时保持声明顺序 |
| 3 | 同一类只出现一次 |

### 无法满足约束时抛 `TypeError`

```python
class Z(X, Y): pass      # 要求 X 在 Y 前
class W(Y, X): pass      # 要求 Y 在 X 前
class Bad(Z, W): pass    # ❌ 矛盾

# TypeError: Cannot create a consistent method resolution order
```

> [Java 对比] Java 没有类多继承，不存在这个问题。但接口 `default` 方法冲突时，需要显式 `override` 指定用哪个。

## 协作式多继承：参数透传

> [Mixin 参数透传](../code/basics/09_inheritance.py#L345-L387)

```python
{{#include ../code/basics/09_inheritance.py:345:387}}
```

Mixin 是 Python 多继承最常见的用途。关键是 **`**kwargs` 一路透传**：

```python
class LogMixin:
    def __init__(self, **kwargs):
        self.log_enabled = kwargs.pop("log_enabled", True)
        super().__init__(**kwargs)        # ✅ 继续透传剩下的

class CacheMixin:
    def __init__(self, **kwargs):
        self.cache_size = kwargs.pop("cache_size", 128)
        super().__init__(**kwargs)

class Service(LogMixin, CacheMixin):
    def __init__(self, name, **kwargs):
        self.name = name
        super().__init__(**kwargs)
```

```python
s = Service("order-service", log_enabled=False, cache_size=512)
# name='order-service'  log_enabled=False  cache_size=512
```

### 不透传会怎样

```python
class BadMixin:
    def __init__(self, name):        # ❌ 吃掉了 kwargs
        super().__init__()           # ❌ 后面的类收不到参数
```

> [要点] 每个 Mixin 的 `__init__` 都要 `**kwargs` 进、`**kwargs` 出，只 `pop` 自己关心的。

> [Java 对比] Java 用接口 `default` 方法实现类似效果，但**无法携带状态**（字段）。Python 的 Mixin 可以有字段。

## 抽象基类 `ABC`

> [ABC 示例](../code/basics/09_inheritance.py#L389-L460)

```python
{{#include ../code/basics/09_inheritance.py:389:460}}
```

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """子类必须实现。"""

    @abstractmethod
    def perimeter(self) -> float:
        """子类必须实现。"""

    def describe(self):                 # 具体方法，子类可直接用
        return f"{type(self).__name__}: area={self.area():.2f}"

class Circle(Shape):
    def area(self): return 3.14159 * self.r ** 2
    def perimeter(self): return 2 * 3.14159 * self.r
```

### 两种错误都会在**实例化时**报 `TypeError`

```python
Shape()          # 抽象类不能实例化
Bad()            # 缺 perimeter 实现
```

### ⚠️ 对比 `NotImplementedError`

```python
class Bad:
    def area(self):
        raise NotImplementedError       # ❌ 能实例化！
```

不用 `ABC` 时，错误要到**调用时**才暴露。`ABC` 在**实例化时**就报错，更早发现问题。

### 抽象方法可以有实现体

子类可以用 `super().area()` 复用：

```python
class Shape(ABC):
    @abstractmethod
    def area(self):
        return 0.0              # 默认实现

class MyShape(Shape):
    def area(self):
        return super().area() + 1
```

> [Java 对比] `ABC` + `@abstractmethod` ≈ Java 的 `abstract class`。

## 与 Java 的关键差异

> [差异演示](../code/basics/09_inheritance.py#L462-L502)

```python
{{#include ../code/basics/09_inheritance.py:462:502}}
```

### ① 没有 `private` / `protected`

```python
class A:
    def __init__(self):
        self._internal = 1      # 约定私有
        self.__secret = 2       # 名称改写，不是真私有
```

实测：

```python
a._internal                 # 1        ← 能访问
list(a.__dict__)            # ['_internal', '_A__secret']
```

`__secret` 被改写成 `_A__secret`（name mangling），只是**防止意外覆盖**，不是访问控制。

### ② 没有 `final`

任何类都能被继承，任何方法都能被重写。

### ③ 构造器链：Java 自动，Python 手动

| | Java | Python |
|---|---|---|
| 子类构造器 | 隐式调 `super()` | 必须显式写 |
| 无参父构造器缺失 | 编译错误 | 运行时 `AttributeError` |

### ④ 重写没有编译期检查

拼错方法名静默变成新增方法。

### ⑤ `object` 是所有类的根

```python
class A: pass
class A(object): pass      # 3.x 中完全等价
```

## 何时该用继承

> [选择标准](../code/basics/09_inheritance.py#L504-L551)

```python
{{#include ../code/basics/09_inheritance.py:504:551}}
```

| 场景 | 用什么 |
|------|--------|
| 真正的 is-a 关系 | **继承** |
| 只想复用代码 | **组合** |
| 只想约束接口 | **`Protocol`** |
| 框架要求覆写钩子 | 继承（如 Django Model） |
| 提供横切能力 | Mixin |

### 组合优于继承

```python
# ❌ Car is-a Engine？语义错误
class BadCar(Engine): pass

# ✅ Car has-a Engine
class GoodCar:
    def __init__(self):
        self.engine = Engine()
```

### `Protocol`：不继承也能满足接口

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Startable(Protocol):
    def start(self) -> str: ...

isinstance(GoodCar(), Startable)      # True ← 没继承也满足
```

> [优势] 不需要修改被适配的类，也不用引入基类耦合。详见[类型系统与静态检查](../advanced/01-type-system.md#protocol结构化子类型)。

> [总原则] 继承表达 **is-a**，组合表达 **has-a**，`Protocol` 表达 **can-do**。

## Java 对照总表

> [完整对照](../code/basics/09_inheritance.py#L554-L573)

```python
{{#include ../code/basics/09_inheritance.py:554:573}}
```

| 场景 | Python | Java |
|------|--------|------|
| 继承语法 | `class D(B, C)` | `class D extends B implements C` |
| **多继承** | **支持（类也能多继承）** | 只有接口可多继承 |
| 方法解析 | C3 线性化 MRO | 单链，无歧义 |
| **`super`** | **MRO 中的下一个类** | **静态绑定到直接父类** |
| 构造器链 | 必须显式 `super().__init__()` | 隐式调用 |
| 重写检查 | 无（拼错静默新增） | `@Override` 编译期检查 |
| 访问控制 | 下划线约定，无强制 | `private` / `protected` / `public` |
| `final` | 无 | 有 |
| 抽象类 | `ABC` + `@abstractmethod` | `abstract class` |
| 接口契约 | `Protocol`（结构化） | `interface`（名义） |

## 小结

- **`super()` 不是"调父类"，是"沿 MRO 找下一个"** —— 这是最核心的一点
- 多继承下**必须用 `super()`**，硬编码 `父类名.__init__(self)` 会重复初始化
- 菱形继承靠协作式 `super()` 保证每个类只执行一次
- Mixin 的 `__init__` 必须 `**kwargs` 进、`**kwargs` 出，只 `pop` 自己的
- `ABC` 在**实例化时**报错，比 `NotImplementedError` 更早发现问题
- 没有 `@Override` 检查，拼错方法名会静默失效
- 继承表达 is-a，组合表达 has-a，`Protocol` 表达 can-do

> 📁 [完整代码](../code/basics/09_inheritance.py)
