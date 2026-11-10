# 现代语法特性

Python 3.8+ 引入了一系列现代语法特性，让代码更简洁、更安全、更具表达力。
本章面向有丰富 Java 经验的开发者，逐一讲解这些特性并与 Java 对应概念做对比。

## 海象运算符 `:=` (3.8+)

海象运算符（walrus operator）允许在**表达式内部**进行赋值，避免重复计算和多余的语句。

```python
# 传统写法：先赋值再判断
n = len(text)
if n > 5:
    print(f"长度 {n} 较长")

# walrus 写法：赋值 + 判断一行搞定
if (n := len(text)) > 5:
    print(f"长度 {n} 较长")
```

它在 `while` 循环读取输入、列表推导式复用计算结果时特别好用。

> [walrus 在循环和推导式中的应用](../code/advanced/07_modern_syntax.py#L25-L61)

```python
{{#include ../code/advanced/07_modern_syntax.py:25:61}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `:=` 赋值表达式 | 无直接对应 | Java 需先声明变量再赋值 |
| `if (n := len(s)) > 5` | `if ((n = s.length()) > 5)` | Java 赋值也是表达式，但只能用于简单类型 |

Java 的赋值本身就是表达式（返回被赋的值），但 Java 不能在 `if` 条件里对方法调用结果赋值给变量再比较——需要拆成两行。

## match/case 结构化模式匹配 (3.10+)

`match/case` 是 Python 3.10 引入的强大模式匹配机制，远超简单的 switch。

```python
match value:
    case 0:
        return "零"
    case 1 | 2 | 3:          # 或模式
        return "小数"
    case int(n) if n > 100:  # 类型 + 守卫
        return f"大整数 {n}"
    case [first, *rest]:    # 列表解构
        return f"列表: first={first}, rest={rest}"
    case {"name": name, "age": age}:  # 字典解构
        return f"人物: {name}, {age}岁"
    case _:
        return f"未知: {value!r}"
```

> [match/case 基础：类型匹配、解构、守卫](../code/advanced/07_modern_syntax.py#L63-L97)

```python
{{#include ../code/advanced/07_modern_syntax.py:63:97}}
```

match 还能匹配自定义类，按属性名绑定变量：

> [match/case 匹配类对象](../code/advanced/07_modern_syntax.py#L100-L134)

```python
{{#include ../code/advanced/07_modern_syntax.py:100:134}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `match/case` | `switch` pattern matching (JEP 441, Java 21) | 结构化模式匹配 |
| `case int(n)` | `case Integer n` | 类型模式 |
| `case [first, *rest]` | 无直接对应 | 解构（Java 21 record deconstruction 有限支持） |
| `case _ if guard` | `case ... when guard` | 守卫 |

Python 的 match 支持列表/字典解构，这是 Java switch pattern matching 尚不具备的。

## ExceptionGroup / except* (3.11+)

`ExceptionGroup` 允许一次抛出**多个异常**，`except*` 按类型分别捕获组中的异常。

```python
try:
    raise ExceptionGroup("多个错误", [
        ValidationError("email"),
        NetworkError("timeout"),
        ValidationError("name"),
    ])
except* ValidationError as eg:
    print(f"捕获 {len(eg.exceptions)} 个 ValidationError")
except* NetworkError as eg:
    print(f"捕获 {len(eg.exceptions)} 个 NetworkError")
```

> [ExceptionGroup 与 except* 示例](../code/advanced/07_modern_syntax.py#L136-L150)

```python
{{#include ../code/advanced/07_modern_syntax.py:136:150}}
```

### Java 对比

Java 没有直接对应，一次只能抛一个异常。在并发场景（如 `StructuredTaskScope`）中 Java 会聚合异常，但没有语言级的 `except*` 语法。

## type 语句类型别名 (3.12+)

`type` 语句创建类型别名，比 `typing.TypeAlias` 更清晰，还支持泛型参数。

```python
type Vector = list[float]
type Matrix = list[list[float]]
type Pair[T] = tuple[T, T]
```

> [type 语句与泛型别名](../code/advanced/07_modern_syntax.py#L180-L215)

```python
{{#include ../code/advanced/07_modern_syntax.py:180:215}}
```

### Java 对比

Java 没有直接对应。Java 的类型别名通常靠继承（`typedef` 不存在），或使用 `record` 包装。

## f-string 嵌套 (3.12+)

3.12 之前 f-string 内部不能复用相同引号，3.12 放宽了限制，可以嵌套 f-string。

```python
# 3.12+ 可以嵌套相同引号
print(f"嵌套: {f"{name}"}")
print(f"列表推导: {[f"{x*2}" for x in range(3)]}")

# 格式说明符嵌套
print(f"格式化: {value:{width}.{precision}f}")
```

> [f-string 嵌套与格式说明符](../code/advanced/07_modern_syntax.py#L217-L251)

```python
{{#include ../code/advanced/07_modern_syntax.py:217:251}}
```

## typing.Self (3.11+)

`Self` 表示"当前类的类型"，用于返回 `self` 的方法（如 Builder 模式）。

```python
class Builder:
    def add(self, part: str) -> Self:
        self.parts.append(part)
        return self
```

> [typing.Self 与 Builder 模式](../code/advanced/07_modern_syntax.py#L253-L282)

```python
{{#include ../code/advanced/07_modern_syntax.py:253:282}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `typing.Self` | `this` 类型 (JEP 446, 预览中) | 表示"当前类的类型" |
| 3.11 前用 `TypeVar` + `bound` 模拟 | 递归泛型 `Enum<E extends Enum<E>>` | 旧方案较繁琐 |

`Self` 在继承中也能正确工作：子类调用继承来的方法，返回类型仍是子类。

## 实战：命令解析器

用 `match/case` 实现一个 shell 命令解析器，展示解构、或模式、守卫的综合运用：

> [命令解析器完整实现](../code/advanced/07_modern_syntax.py#L312-L377)

```python
{{#include ../code/advanced/07_modern_syntax.py:312:377}}
```

## 小结

- `:=` 海象运算符在表达式内赋值，避免重复计算
- `match/case` 是强大的结构化模式匹配，支持解构、守卫、类型匹配
- `ExceptionGroup` / `except*` 支持一次抛出和分别捕获多个异常
- `type` 语句创建类型别名（3.12+），比 `TypeAlias` 更清晰
- f-string 3.12+ 支持嵌套相同引号
- `typing.Self` 表示当前类类型，Builder 模式利器

> 📁 [查看完整代码](../code/advanced/07_modern_syntax.py)
