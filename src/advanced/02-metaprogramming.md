# 面向对象与元编程

Python 的元编程比 Java 更直接：元类可在类创建时动态修改类，描述符可控制属性访问。
本章讲解描述符、元类、ABC、`__slots__`、dunder 方法等核心机制。

## 核心概念

### "类也是对象"

在 Python 中，类本身是 `type` 的实例。`class` 关键字本质上是调用 `type()`。
这意味着你可以在运行时动态创建类、修改类——这在 Java 中需要 ASM/CGLib 字节码操作。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| 描述符 (`__get__`/`__set__`) | getter/setter + Lombok | 控制属性访问 |
| `property` | getter/setter | 描述符的语法糖 |
| 元类 (`metaclass`) | 注解处理器 / ASM | 拦截类创建 |
| `type(name, bases, attrs)` | ASM 动态生成类 | 运行时创建类 |
| `__init_subclass__` | 反射扫描 / SPI | 子类定义时的钩子 |
| `ABC` + `@abstractmethod` | `abstract class` / `interface` | 抽象基类 |
| `__slots__` | 固定字段（Java 默认行为） | 省内存，禁止动态属性 |
| `__eq__`/`__hash__`/`__lt__` | `equals`/`hashCode`/`compareTo` | 数据模型方法 |

## 描述符 descriptor

描述符把"属性访问"这一行为抽象成对象。实现 `__get__`/`__set__`/`__delete__` 的类即可作为描述符。
有 `__set__` 的是**数据描述符**，只有 `__get__` 的是**非数据描述符**。

> [带校验的描述符 ValidatedField](../code/advanced/02_metaprogramming.py#L26-L61)

```python
{{#include ../code/advanced/02_metaprogramming.py:26:61}}
```

描述符常用于 ORM 框架（如 Django 的字段、SQLAlchemy 的 Column）。

### 普通方法也是描述符

这一点很重要：**`function` 本身就实现了 `__get__`**，所以类是方法、property、staticmethod
乃至 ORM 字段，底层走的是同一套机制。

```python
def f(self, x): return x
f.__get__          # 存在！函数是非数据描述符
```

调用时根据“从哪里访问”返回不同结果：

| 访问方式 | 调用 | 返回 |
|---------|------|------|
| 实例 | `obj.method` | `__get__(obj, type(obj))` -> **绑定方法**（self 已固定） |
| 类 | `Klass.method` | `__get__(None, Klass)` -> **裸函数**（需手动传 self） |

这解释了两件经常让人困惑的事：

```python
Klass.method              # <function>      未绑定
obj.method                # <bound method>  self 已绑定
Klass.method(obj, 1)      # 等价于 obj.method(1)
```

以及为什么“通过类访问会沿 MRO 找”：因为 `Klass.method` 用的是
`type.__getattribute__`，它本身就会走 MRO。

> 使用层面的讲解（什么时候该这么写、有什么坑）见
> [特殊方法 - 方法访问与绑定](../../basics/10-dunder-methods.md#方法访问与绑定)。

### 描述符协议与查找优先级

实例属性查找的完整顺序：

1. **数据描述符**（有 `__set__`）—— 优先级最高
2. 实例 `__dict__`
3. **非数据描述符**（只有 `__get__`，包括普通函数）
4. 类属性 / `__getattr__` 兵底

这解释了为什么：

- 普通方法（非数据描述符）可以被实例属性遮蔽（`obj.method = 1` 能成功）
- 而 `property`（数据描述符）不能（赋值会走 setter 或报 `AttributeError`）

## property：描述符的语法糖

`@property` 是描述符的便捷写法，本质是一个数据描述符：

> [property 实现带校验属性](../code/advanced/02_metaprogramming.py#L94-L116)

```python
{{#include ../code/advanced/02_metaprogramming.py:94:116}}
```

## 元类 metaclass

元类是"创建类的类"。普通类的"类"是 `type`，自定义元类继承 `type`。
通过拦截 `__call__`，元类可以在类创建实例时进行控制。

### 用 type() 动态创建类

> [type() 动态创建类](../code/advanced/02_metaprogramming.py#L137-L156)

```python
{{#include ../code/advanced/02_metaprogramming.py:137:156}}
```

Java 无法在运行时这样动态创建类（除非用 ASM/CGLib）。

### 自定义元类实现单例

> [SingletonMeta 元类单例](../code/advanced/02_metaprogramming.py#L157-L171)

```python
{{#include ../code/advanced/02_metaprogramming.py:157:171}}
```

Java 单例通常用 private 构造 + 静态方法，或枚举单例。Python 用元类拦截 `__call__`。

## __init_subclass__：比元类轻量的钩子

3.6+ 引入的钩子，子类被定义时自动调用，避免使用元类。常用于插件注册：

> [__init_subclass__ 插件注册](../code/advanced/02_metaprogramming.py#L193-L206)

```python
{{#include ../code/advanced/02_metaprogramming.py:193:206}}
```

Java 没有直接对应，需要用反射扫描或 SPI 机制。

## ABC 抽象基类

对应 Java 的 `abstract class` / `interface`：

> [ABC 抽象基类示例](../code/advanced/02_metaprogramming.py#L227-L245)

```python
{{#include ../code/advanced/02_metaprogramming.py:227:245}}
```

`@abstractmethod` 标记的方法子类必须实现，否则实例化时抛 `TypeError`。

## __slots__：固定属性集合

Python 默认每个对象有 `__dict__` 存任意属性。`__slots__` 关闭 `__dict__`，固定属性集合：
- 优点：省内存、访问更快
- 缺点：不能动态添加属性

> [__slots__ 内存对比](../code/advanced/02_metaprogramming.py#L281-L292)

```python
{{#include ../code/advanced/02_metaprogramming.py:281:292}}
```

Java 对象字段默认就是固定的，类似 `__slots__` 的行为。

## __class_getitem__：支持类泛型下标

让类支持 `MyList[int]` 语法。Java 泛型 `List<Integer>` 是编译期语法，Python 是运行期方法：

> [__class_getitem__ 示例](../code/advanced/02_metaprogramming.py#L320-L335)

```python
{{#include ../code/advanced/02_metaprogramming.py:320:335}}
```

## 数据模型 dunder 方法

> 系统讲解（各类协议、`__eq__`/`__hash__` 配套、`__getattr__` vs `__getattribute__`）
> 见[特殊方法（dunder）](../basics/10-dunder-methods.md)。本节只列最常用对照。

Python 通过 dunder（双下划线）方法实现运算符重载和协议：

| dunder | Java 对应 | 用途 |
|--------|-----------|------|
| `__eq__` / `__hash__` | `equals` / `hashCode` | 相等比较、哈希 |
| `__lt__` | `Comparable.compareTo` | 排序 |
| `__repr__` | `toString` | 字符串表示 |
| `__iter__` | `Iterable.iterator` | 迭代 |

> 元编程场景下，这些方法常与元类/描述符配合使用。例如元类通过 `__call__`
> 拦截实例创建（见上文单例实现），描述符通过 `__get__` 拦截属性访问。

> [dunder 方法实现示例](../code/advanced/02_metaprogramming.py#L350-L380)

```python
{{#include ../code/advanced/02_metaprogramming.py:350:380}}
```

## 小结

- 描述符把属性访问抽象成对象，是 ORM 字段的底层机制
- `property` 是描述符的语法糖
- 元类拦截类创建，对应 Java 的字节码增强；`__init_subclass__` 是更轻量的替代
- `ABC` + `@abstractmethod` 对应 Java 抽象类/接口
- `__slots__` 固定属性集合，省内存，类似 Java 对象的默认行为
- dunder 方法实现运算符重载和协议，对应 Java 的 `equals`/`hashCode`/`compareTo`

> 📁 [查看完整代码](../code/advanced/02_metaprogramming.py)
