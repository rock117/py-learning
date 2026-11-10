# 内省与反射

Python 的动态特性让内省（introspection）比 Java 反射更强大、更简单。本章讲解 `inspect` 模块、
`__dict__`、`__mro__`、动态属性访问，以及实战中的 ORM 映射和插件系统。

## inspect：获取函数签名

`inspect.signature` 能拿到完整的参数名、默认值、注解——比 Java 反射信息更丰富。

```python
sig = inspect.signature(greet)
for name, param in sig.parameters.items():
    print(f"{name}: kind={param.kind.name}, default={param.default}")
```

还可以用 `sig.bind()` 绑定参数，验证调用是否合法：

> [inspect 获取函数签名与参数绑定](../code/advanced/10_introspection.py#L33-L57)

```python
{{#include ../code/advanced/10_introspection.py:33:57}}
```

### Java 对比

| Python inspect | Java reflect | 说明 |
|----------------|--------------|------|
| `signature(func)` | `Method.getParameters()` | Python 能拿到参数名 |
| 参数名、默认值、注解 | 只有类型（需 `-parameters` 才有名字） | Python 信息更全 |
| `sig.bind()` | 无直接对应 | 参数绑定验证 |

## inspect：获取源码

Python 能在运行时直接获取函数的**源码**，Java 做不到（只能反编译字节码）。

> [inspect 获取源码与定义位置](../code/advanced/10_introspection.py#L58-L71)

```python
{{#include ../code/advanced/10_introspection.py:58:71}}
```

## inspect：调用栈

`inspect.stack()` 获取当前调用栈，类似 Java 的 `Thread.currentThread().getStackTrace()`。

> [inspect 调用栈](../code/advanced/10_introspection.py#L72-L78)

```python
{{#include ../code/advanced/10_introspection.py:72:78}}
```

## __dict__：查看对象属性

实例的 `__dict__` 存储实例属性，类的 `__dict__` 存储类属性和方法（只读 `mappingproxy`）。

```python
p = Person("Alice", 30)
p.__dict__          # {'name': 'Alice', 'age': 30}
p.email = "a@b.com" # 动态添加实例属性（Java 做不到）
```

> [__dict__ 查看对象属性](../code/advanced/10_introspection.py#L96-L104)

```python
{{#include ../code/advanced/10_introspection.py:96:104}}
```

### Java 对比

Java 字段在编译期固定，不能运行时动态添加。Python 可以随时给实例或类添加属性。

## __mro__：方法解析顺序

Python 支持多继承，用 **C3 线性化**算法确定方法查找顺序（MRO）。

```python
class D(B, C): pass
D.__mro__  # [D, B, C, A, object]
```

> [__mro__ 方法解析顺序](../code/advanced/10_introspection.py#L130-L132)

```python
{{#include ../code/advanced/10_introspection.py:130:132}}
```

### Java 对比

Java 不支持类多继承（只有接口多继承），没有 MRO 问题。Python 的 `super()` 按 MRO 跳转。

## getattr / setattr / hasattr：动态属性访问

```python
getattr(p, "name")           # 等价于 p.name
getattr(p, "email", "N/A")   # 带默认值
setattr(p, "salary", 50000)  # 动态设置
hasattr(p, "age")             # 检查存在
delattr(p, "salary")          # 删除属性
```

> [getattr/setattr/hasattr 动态属性访问](../code/advanced/10_introspection.py#L167-L199)

```python
{{#include ../code/advanced/10_introspection.py:167:199}}
```

### Java 对比

| Python | Java reflect | 说明 |
|--------|--------------|------|
| `getattr(obj, "name")` | `Field.get(obj)` | 动态读取 |
| `setattr(obj, "name", v)` | `Field.set(obj, v)` | 动态设置 |
| `hasattr(obj, "name")` | `getDeclaredField` + try-catch | 检查存在 |

Python 的 `getattr`/`setattr` 不需要先获取 Field 对象，直接用字符串名访问，更简洁。

## dir()：列出所有属性

`dir()` 列出对象的所有属性和方法，类似 Java 的 `getMethods() + getFields()`。

> [dir() 列出所有属性](../code/advanced/10_introspection.py#L200-L218)

```python
{{#include ../code/advanced/10_introspection.py:200:218}}
```

## __getattr__ vs __getattribute__

这两个魔术方法容易混淆，区别关键：

| 方法 | 触发时机 | 用途 | Java 类比 |
|------|----------|------|-----------|
| `__getattr__` | 属性**不存在**时 | 兜底/惰性加载/代理 | 动态代理 `InvocationHandler` |
| `__getattribute__` | **每次**属性访问 | 拦截所有访问 | AOP 切面 |

> [__getattr__ 惰性加载示例](../code/advanced/10_introspection.py#L219-L235)

```python
{{#include ../code/advanced/10_introspection.py:219:235}}
```
>
> [__getattribute__ 全拦截示例](../code/advanced/10_introspection.py#L238-L252)

```python
{{#include ../code/advanced/10_introspection.py:238:252}}
```

> **注意**：`__getattribute__` 内部访问 `self.xxx` 会再次触发自身，容易无限递归。
> 必须用 `object.__getattribute__` 来避免。

## 实战：简易 ORM 映射

用 `__init_subclass__` + 描述符（`Column`）实现类似 JPA `@Entity` 的 ORM 基类。

> [ORM 基类与 Column 描述符](../code/advanced/10_introspection.py#L272-L298)

```python
{{#include ../code/advanced/10_introspection.py:272:298}}
```
>
> [ORM 实体定义与 SQL 生成](../code/advanced/10_introspection.py#L320-L325)

```python
{{#include ../code/advanced/10_introspection.py:320:325}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `Column` 描述符 | `@Column` 注解 | 字段定义 |
| `__init_subclass__` | 注解处理器 / 字节码增强 | 子类注册 |
| `to_dict()` / `columns()` | JPA 反射映射 | 实体与数据库互转 |

## 实战：插件系统

通过 `importlib` 动态导入模块，用 `dir()` + `getattr()` 发现其中的插件函数。

> [插件系统：动态发现与加载](../code/advanced/10_introspection.py#L351-L383)

```python
{{#include ../code/advanced/10_introspection.py:351:383}}
```

### Java 对比

Java 的 `ServiceLoader` / SPI 机制需要声明 `META-INF/services/` 文件，Python 用 `dir()`
扫描即可，更灵活。

## type() 与 isinstance() 的内省

```python
type(p).__name__     # 类名
type(p).__bases__    # 父类元组
isinstance(p, Person)
issubclass(Person, object)

# 动态创建类
DynamicClass = type("DynamicClass", (object,), {"greet": lambda self: "hi"})
```

> [type/isinstance/issubclass 与动态创建类](../code/advanced/10_introspection.py#L384-L404)

```python
{{#include ../code/advanced/10_introspection.py:384:404}}
```

## 小结

- `inspect`：函数签名、源码、调用栈，比 Java 反射信息更丰富
- `__dict__`：实例/类的属性表，可动态增删（Java 做不到）
- `__mro__`：多继承的方法查找顺序（C3 线性化）
- `getattr`/`setattr`/`hasattr`：动态属性访问，比 Java Field 更简洁
- `__getattr__` 兜底，`__getattribute__` 全拦截
- 实战：ORM 用描述符 + `__init_subclass__`，插件用 `importlib`

> 📁 [查看完整代码](../code/advanced/10_introspection.py)
