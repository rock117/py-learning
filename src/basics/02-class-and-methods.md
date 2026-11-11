# 类的三种方法与 property

Python 类里最容易让 Java 开发者写错的，是 `@classmethod`、`@staticmethod` 和 `@property`。

根源在于：**Java 的 `static` 方法在 Python 里被拆成了两个东西**，而且 Python 多了一个 Java 完全没有的属性访问机制。

## 三种方法的绑定差异

```python
class Demo:
    class_attr = "I am class attr"

    def instance_method(self):        # self = 实例
        ...

    @classmethod
    def cls_method(cls):              # cls = 类
        ...

    @staticmethod
    def static_method():              # 无绑定
        ...
```

| 方法类型 | 第一个参数 | 能访问实例 | 能访问类属性 | 类调用 | 实例调用 |
|----------|-----------|-----------|-------------|--------|---------|
| 实例方法 | `self` | ✅ | ✅（经 `self`） | ❌ | ✅ |
| `@classmethod` | `cls` | ❌ | ✅ | ✅ | ✅（`cls` 仍是类） |
| `@staticmethod` | 无 | ❌ | ❌ | ✅ | ✅（等价） |

> [三种方法的绑定差异](../code/basics/02_class_and_methods.py#L29-L60)

```python
{{#include ../code/basics/02_class_and_methods.py:29:60}}
```

注意最后一行：实例调用 `@classmethod` 时，传进去的 `cls` **仍然是类**，不是实例。这和 Java 的 static 方法"实例调用只是语法糖"表现一致，但机制不同。

## `@classmethod` 的真正用途：替代构造器

这是它存在的主要理由，也是 Java 开发者最容易忽略的：

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    @classmethod
    def from_tuple(cls, pair):
        return cls(pair[0], pair[1])

    @classmethod
    def from_string(cls, s):
        x, y = s.split(",")
        return cls(float(x), float(y))

    @classmethod
    def origin(cls):
        return cls(0, 0)
```

Python 不支持方法重载，所以"用不同方式构造对象"必须换名字。`from_tuple` / `from_string` / `origin` 这种命名是标准惯例（也见于 `datetime.fromtimestamp`、`dict.fromkeys`）。

> [工厂方法示例](../code/basics/02_class_and_methods.py#L63-L107)

```python
{{#include ../code/basics/02_class_and_methods.py:63:107}}
```

### 关键优势：`cls` 自动适配子类

```python
class Point3D(Point):
    def __init__(self, x, y, z=0.0):
        super().__init__(x, y)
        self.z = z

p3 = Point3D.from_tuple((7, 8))    # 返回 Point3D，不是 Point
```

因为 `cls` 是运行时的实际类，工厂方法天然支持子类。

> ⚠️ [Java 对比] Java 的 `static` 方法**不会被继承**（会被隐藏），`Point3D.fromTuple()` 调用的是父类版本，只能返回 `Point`。要在 Java 里实现同样的效果，得用泛型自引用 `static <T extends Point> T fromTuple(...)` 或 builder，非常笨重。

## `@staticmethod` 的合理用途

只有一种情况值得用：**纯函数，不依赖实例也不依赖类**，放进类里纯粹是为了归类命名。

```python
class Temperature:
    @staticmethod
    def c_to_f(c):
        return c * 9 / 5 + 32

    def to_fahrenheit(self):
        return self.c_to_f(self.celsius)
```

> [staticmethod 用法](../code/basics/02_class_and_methods.py#L110-L137)

```python
{{#include ../code/basics/02_class_and_methods.py:110:137}}
```

> ⚠️ 用 `@staticmethod` 写工厂方法是一个常见误用——它拿不到 `cls`，子类适配能力就丢了。**需要构造对象就用 `@classmethod`。**

## `property`：让 getter 像字段一样访问

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("半径不能为负")
        self._radius = value

    @property
    def area(self):          # 只读属性
        return 3.14159 * self._radius ** 2
```

调用方不需要括号：

```python
c = Circle(2)
print(c.radius)      # 2      <- 不是 c.radius()
print(c.area)        # 12.57
c.radius = 3         # 触发校验
```

> [property 基本用法](../code/basics/02_class_and_methods.py#L139-L179)

```python
{{#include ../code/basics/02_class_and_methods.py:139:179}}
```

三个要点：

1. **`@property` 只读**（没有 setter 时赋值会 `AttributeError`）
2. **setter 里必须用 `self._radius`**，写成 `self.radius = value` 会无限递归
3. **派生字段**（如 `area`）放 property 里，能保证永远和源数据一致

> [派生字段示例](../code/basics/02_class_and_methods.py#L182-L205)

```python
{{#include ../code/basics/02_class_and_methods.py:182:205}}
```

### Python 的惯例：先写公有字段

```python
class P:
    def __init__(self):
        self.x = 1        # 直接公有字段
```

**不是**一开始就 `private` + getter/setter。等真的需要校验或计算时，再改成 `property`，**调用方代码完全不用动**——这是 `property` 最大的价值。

> ⚠️ [Java 对比] Java 习惯一开始就写 `private int x;` + `getX()`/`setX()`，20 行的类配 60 行样板代码。Python 里这样做是反模式，`ruff` 之类工具甚至不会替生成 getter。

> [property 与公有字段的取舍](../code/basics/02_class_and_methods.py#L208-L223)

```python
{{#include ../code/basics/02_class_and_methods.py:208:223}}
```

## 常见陷阱

### 坑 1：忘记 `@staticmethod`

```python
class A:
    def f(x): return x      # 少写了 @staticmethod

A().f(1)     # TypeError: f() takes 1 positional argument but 2 were given
```

因为实例调用时，`self` 被绑到了 `x` 上。

### 坑 2：setter 里递归

```python
@radius.setter
def radius(self, v):
    self.radius = v        # ❌ 无限递归
```

### 坑 3：子类赋值会让类属性"分裂"

```python
class Counter:
    count = 0

    @classmethod
    def increment(cls):
        cls.count += 1

class ChildCounter(Counter):
    pass

Counter.increment()
ChildCounter.increment()
# Counter.count     == 1
# ChildCounter.count == 1    <- 子类有了【自己的】count
```

`cls.count += 1` 在子类上执行时，会**在子类上创建新属性**，而不是修改父类的。这是 Python 属性查找与赋值规则（赋值总是写入"当前命名空间"）导致的，Java 的 static 字段是每个类一份，行为类似但不够直观。

> [常见陷阱演示](../code/basics/02_class_and_methods.py#L225-L262)

```python
{{#include ../code/basics/02_class_and_methods.py:225:262}}
```

## Java 对照总表

> [查看完整对照代码](../code/basics/02_class_and_methods.py#L265-L282)

```python
{{#include ../code/basics/02_class_and_methods.py:265:282}}
```

| 场景 | Python | Java |
|------|--------|------|
| 实例方法 | `def m(self)` | 普通方法 |
| 类方法 | `@classmethod def m(cls)` | `static` 方法（但能拿到类对象） |
| 静态方法 | `@staticmethod def m()` | `static` 方法 |
| 替代构造器 | `@classmethod` 工厂方法 | `static` factory method |
| 子类适配工厂 | `cls` 自动是子类 | 不支持（只能泛型自引用） |
| 只读属性 | `@property` | `getX()` |
| 可写属性 | `@x.setter` | `getX()` + `setX()` |
| 访问语法 | `obj.x`（无括号） | `obj.getX()` |

## 小结

- **`@classmethod`** 的核心用途是替代构造器，`cls` 让工厂方法自动适配子类
- **`@staticmethod`** 只用于纯函数归类，不要拿它写工厂方法
- **`@property`** 让 getter 字段化访问；先写公有字段，需要时再包
- setter 里必须用 `self._xxx`，否则递归
- 类属性在子类上赋值会分裂成独立副本

> 📁 [完整代码](../code/basics/02_class_and_methods.py)
