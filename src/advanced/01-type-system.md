# 类型系统与静态检查

Python 是动态强类型语言，运行期才检查类型。但通过 `typing` 模块配合 `mypy`/`pyright`，
可以在开发期获得类似 Java 编译期的静态类型检查能力。本章系统讲解 Python 类型系统。

## 核心概念

### 类型注解不影响运行

Python 的类型注解默认在运行期**不强制执行**，仅供静态检查工具使用：

```python
def find_user(user_id: int) -> Optional[str]:
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)
```

运行期即使传入字符串也不会报错（除非代码内部依赖类型）。这与 Java 编译期强制检查截然不同。

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `TypeVar("T")` + `Generic[T]` | `<T>` | 泛型类型参数 |
| `Optional[str]` | `Optional<String>` | 可空类型（Python 是 `Union[str, None]` 语法糖） |
| `Union[int, str]` | 无直接对应 | 联合类型，Java 需用接口或重载 |
| `Callable[[int], int]` | `Function<Integer, Integer>` | 函数类型 |
| `Literal["read", "write"]` | `enum Mode` | 字面量类型 |
| `Final[int]` | `final int` | 不可变绑定 |
| `TypedDict` | POJO / `record` | 带类型键的字典 |
| `Protocol` | `interface` | 结构化子类型（无需 `implements`） |
| `@overload` | 方法重载 | Python 仅用于类型检查，运行期单实现 |

## 泛型容器

Python 用 `Generic[T]` 继承声明泛型类，`TypeVar` 声明类型变量：

> [泛型容器 Box 示例](../code/advanced/01_type_system.py#L46-L66)

```python
{{#include ../code/advanced/01_type_system.py:46:66}}
```

注意：运行期 `Box[int]` 和 `Box[str]` 没有区别，类型注解仅供静态检查。

## Optional / Union / Callable

- `Optional[str]` 等价于 `Union[str, None]`，表示可能为 `None`
- `Union[int, str]` 表示多种类型之一，Java 没有直接对应
- `Callable[[int], int]` 表示接收 `int` 返回 `int` 的函数，对应 Java 函数式接口

> [Optional / Union / Callable 演示](../code/advanced/01_type_system.py#L69-L80)

```python
{{#include ../code/advanced/01_type_system.py:69:80}}
```

## Literal / Final / TypedDict

- `Literal["read", "write", "append"]` 限定值为特定字面量，比 Java 枚举更轻量
- `Final[int]` 阻止重新赋值，类似 Java `final`
- `TypedDict` 让字典的键值类型固定，运行期仍是 `dict`

> [Literal / Final / TypedDict 演示](../code/advanced/01_type_system.py#L120-L132)

```python
{{#include ../code/advanced/01_type_system.py:120:132}}
```

## @overload 函数重载

Python 的 `@overload` **仅用于类型检查**，运行期需要一个具体实现靠 `isinstance` 分派。
Java 有真正的编译期重载，这是关键差异。

> [@overload 重载示例](../code/advanced/01_type_system.py#L156-L175)

```python
{{#include ../code/advanced/01_type_system.py:156:175}}
```

## Protocol：结构化子类型

这是 Python 类型系统最强大的特性之一。Java 的 `interface` 是**名义子类型**（nominal），
必须显式 `implements`；Python 的 `Protocol` 是**结构化子类型**（structural），只要形状匹配即可：

```python
class SupportsClose(Protocol):
    def close(self) -> None: ...

class MyResource:  # 无需继承 SupportsClose
    def close(self) -> None: ...
```

`MyResource` 有 `close()` 方法即满足 `SupportsClose` 协议，静态检查通过。

> [Protocol 结构化子类型示例](../code/advanced/01_type_system.py#L259-L267)

```python
{{#include ../code/advanced/01_type_system.py:259:267}}
```

## 协变 / 逆变

对应 Java 的 `? extends` / `? super` 通配符：

| 概念 | Python | Java |
|------|--------|------|
| 协变 | `TypeVar("T_co", covariant=True)` | `List<? extends Number>` |
| 逆变 | `TypeVar("T_contra", contravariant=True)` | `Comparator<? super T>` |

> [协变 / 逆变示例](../code/advanced/01_type_system.py#L280-L296)

```python
{{#include ../code/advanced/01_type_system.py:280:296}}
```

## ParamSpec / TypeVarTuple（高阶泛型）

`ParamSpec`（PEP 612，3.10+）捕获函数参数签名，常用于保留装饰器中函数的签名信息。
`TypeVarTuple`（PEP 646，3.11+）支持可变长度泛型。Java 没有直接对应。

> [ParamSpec / TypeVarTuple 示例](../code/advanced/01_type_system.py#L200-L220)

```python
{{#include ../code/advanced/01_type_system.py:200:220}}
```

## PEP 695 原生泛型语法（3.12+）

3.12+ 引入新语法，无需 `TypeVar` / `Generic`：

```python
class NewBox[T]:
    def __init__(self, value: T) -> None:
        self.value = value

def new_func[T](x: T) -> T:
    return x

type Vector = list[float]  # type 语句创建别名
```

> [PEP 695 示例](../code/advanced/01_type_system.py#L338-L381)

```python
{{#include ../code/advanced/01_type_system.py:338:381}}
```

## 静态检查工具

- **mypy**：`pip install mypy`，然后 `mypy 01_type_system.py`
- **pyright**：`pip install pyright` 或 VSCode Pylance 插件
- 两者都支持 PEP 484 等类型规范

## 小结

- Python 类型注解运行期默认不强制，靠 `mypy`/`pyright` 做静态检查
- `Protocol` 是结构化子类型，无需显式 `implements`，比 Java `interface` 更灵活
- `@overload` 仅用于类型检查，运行期单实现靠 `isinstance` 分派
- 协变/逆变对应 Java 的 `? extends` / `? super`
- 3.12+ 的 PEP 695 提供更简洁的原生泛型语法

> 📁 [查看完整代码](../code/advanced/01_type_system.py)
