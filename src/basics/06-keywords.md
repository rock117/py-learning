# 容易误解的关键字

这一章集中处理几个"写法和 Java 眼熟、行为却不一样"的关键字。它们的共同陷阱是：**你以为懂了，但细节是错的**。

| 关键字 | 关键差异 |
|--------|---------|
| `lambda` | 只能写**单个表达式**，不能多语句 |
| `global` / `nonlocal` | 只读不需声明，**赋值才需要** |
| `yield` / `yield from` | 生成器；Java 无对应 |
| `del` | 删除**名字绑定**，不是对象 |
| `assert` | 在 `python -O` 下**被整体剥离** |
| `is` / `==` | 与 Java **正好相反** |
| `pass` / `elif` / `None` | 语法细节 |
| 三元表达式 | **语序**与 Java 相反 |

## `lambda`：只能单个表达式

> [lambda 示例](../code/basics/06_keywords.py#L30-L60)

```python
{{#include ../code/basics/06_keywords.py:30:60}}
```

```python
add = lambda a, b: a + b
classify = lambda n: "even" if n % 2 == 0 else "odd"    # 三元算一个表达式
```

但**写不了多条语句**：

```python
# ❌ SyntaxError
lambda x: (y = x * 2; return y)
```

需要多条语句就老实写 `def`。

> ⚠️ [Java 对比] Java 的 lambda 可以写 `{ ... }` 代码块和多条语句，Python 不行。这不是能力退化，而是 Python 的哲学：lambda 只用于"一次性小函数"，复杂逻辑应该具名。

最常见用途是排序的 `key`：

```python
sorted(users, key=lambda u: u["age"])
```

## `global` / `nonlocal` 与 LEGB

Python 查找变量的顺序是 **LEGB**：Local → Enclosing → Global → Builtin。

> [作用域示例](../code/basics/06_keywords.py#L62-L113)

```python
{{#include ../code/basics/06_keywords.py:62:113}}
```

**只读不需要声明**：

```python
x = "global-but-read"

def f():
    return x        # 直接能找到全局的 x
```

**赋值才需要 `global`**：

```python
def f():
    global x
    x = "modified"  # 没有 global 的话，这只是新建局部变量
```

**修改外层函数变量用 `nonlocal`**：

```python
def outer():
    count = 0
    def inner():
        nonlocal count   # 声明 count 来自外层函数，不是新建
        count += 1
    inner(); inner()
    return count         # 2
```

> ⚠️ `nonlocal` 找不到外层变量时是**编译期 `SyntaxError`**，`try/except` 抓不住。

> [Java 对比] Java 的 lambda 只能捕获 **effectively final** 的变量，根本不允许修改；Python 的 `nonlocal` 显式声明后就可以改。这是两种语言的闭包模型差异。

## `yield` 与 `yield from`

> [yield 示例](../code/basics/06_keywords.py#L115-L161)

```python
{{#include ../code/basics/06_keywords.py:115:161}}
```

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1
```

`yield from` 把子迭代器的元素逐个产出，省掉一层循环：

```python
def nested():
    yield 1
    yield from [2, 3]      # 等价于 for x in [2,3]: yield x
    yield 6
```

它还会**转发 `send()` / `throw()` / `close()`** 给子生成器，并作为表达式时取子生成器的 `return` 值。

> [Java 对比] Java 没有生成器。`Stream` 是拉取式的单向数据流，无法与生产者双向通信（`send`）。

生成器的完整用法见[生成器与协程进阶](../advanced/04-generators.md)。

## `del`：删的是名字，不是对象

> [del 示例](../code/basics/06_keywords.py#L163-L194)

```python
{{#include ../code/basics/06_keywords.py:163:194}}
```

```python
a = [1, 2, 3]
b = a
del a          # 删掉名字 a，列表还在（b 仍指向它）
print(b)       # [1, 2, 3]
```

`del` 也能删容器元素和切片：

```python
del lst[0]
del lst[1:3]
del d["k"]
```

> [Java 对比] Java 没有 `del` 语句。对象回收完全交给 GC，不能手动解除引用。Python 的 `del` 只是**减少引用计数**，对象在最后一个引用消失时才回收。

## `assert`：会在 `-O` 下消失

> [assert 示例](../code/basics/06_keywords.py#L196-L231)

```python
{{#include ../code/basics/06_keywords.py:196:231}}
```

```python
assert v > 0, f"必须为正数，收到 {v}"
```

表面看像参数校验，但**用 `python -O` 运行时，所有 `assert` 会被编译器整体移除**。

> ⚠️ 因此 `assert` **绝不能**用于：
> - 用户输入校验（用户能绕过）
> - 业务规则检查（生产环境失效）
> - 权限判断（安全漏洞）

✅ 正确用途：

| 用途 | 说明 |
|------|------|
| 内部不变量 | 开发期自检，比如"这个列表此时必定非空" |
| 测试断言 | pytest 大量使用 `assert` |
| 类型收窄 | 帮助 `mypy` 推断类型 |

生产校验请用显式 `if` + `raise`：

```python
if v <= 0:
    raise ValueError(f"必须为正数，收到 {v}")
```

> [Java 对比] Java 的 `assert` 同样默认关闭（需 `-ea` 开启），两边踩的是**同一个坑**。

## `is` 与 `==`：与 Java 正好相反

这是从 Java 过来**最大的混淆源**。

> [身份比较示例](../code/basics/06_keywords.py#L233-L270)

```python
{{#include ../code/basics/06_keywords.py:233:270}}
```

```python
a = [1, 2]
b = [1, 2]

a == b      # True   值相等（等价于 Java 的 equals）
a is b      # False  不是同一对象（等价于 Java 的 ==）
```

| Python | 含义 | Java 对应 |
|--------|------|-----------|
| `a == b` | 值相等 | `a.equals(b)` |
| `a is b` | 身份相同 | `a == b`（引用比较） |

**用 `is` 的场景只有三个**：

```python
x is None
x is True          # 或 False，但一般直接写 if x:
x is y             # 判断是否同一对象
```

> ⚠️ **不要用 `is` 比较数字和字符串**。小整数缓存、字符串驻留会让某些情况"看起来能用"，但结果依赖实现，不可依赖。详见[常见陷阱](../practice/03-pitfalls.md)。

## `pass` / `elif` / `None`

> [小语法示例](../code/basics/06_keywords.py#L272-L307)

```python
{{#include ../code/basics/06_keywords.py:272:307}}
```

**`pass`**：语法占位，什么也不做。空代码块必须写它：

```python
class Empty:
    pass
```

**`elif`**：Python 用一个关键字，Java 是两个词 `else if`：

```python
if score >= 90:   grade = "A"
elif score >= 80: grade = "B"      # 不是 else if
else:             grade = "C"
```

**`None`**：唯一的空值，类型是 `NoneType`。

> [Java 对比] 对应 `null`，但 **`None` 是一个真实对象**——可以传参、比较、有类型。Python 没有 `NullPointerException`，但访问 `None` 的属性会抛 `AttributeError`。

## 三元表达式：语序相反

> [三元表达式示例](../code/basics/06_keywords.py#L309-L328)

```python
{{#include ../code/basics/06_keywords.py:309:328}}
```

```python
# Python：条件在中间
"big" if n > 3 else "small"

# Java：条件在最前
n > 3 ? "big" : "small"
```

> ⚠️ 语序不同，这是从 Java 过来最容易写错的地方。嵌套超过两层建议改成 `if/elif`：

```python
# 可读性差
"A" if s >= 90 else ("B" if s >= 80 else "C")

# 更好
if s >= 90:   label = "A"
elif s >= 80: label = "B"
else:         label = "C"
```

## Java 对照总表

> [完整对照代码](../code/basics/06_keywords.py#L331-L351)

```python
{{#include ../code/basics/06_keywords.py:331:351}}
```

| 关键字 | Python 语义 | Java 对应 |
|--------|-------------|-----------|
| `lambda` | 只能单表达式 | 可写块和多语句 |
| `global` | 声明修改模块级变量 | 无（字段天然可变） |
| `nonlocal` | 声明修改外层函数变量 | 捕获需 effectively final |
| `yield` | 生成器产出 | 无 |
| `yield from` | 委托给子生成器 | 无 |
| `del` | 解除名字绑定 | 无 |
| `assert` | `-O` 下被剥离 | `-ea` 关闭 / `-da` 开启 |
| `is` | 身份比较 | `==`（引用比较） |
| `==` | 值比较 | `equals()` |
| `elif` | 单关键字 | `else if` |
| `x if c else y` | 条件在中间 | `c ? x : y` |

## 小结

- **`lambda` 只能单表达式**，复杂逻辑用 `def`
- 只读变量不需声明；**赋值时才需要** `global` / `nonlocal`
- `del` 删的是名字，对象在最后一个引用消失时才回收
- **`assert` 在 `-O` 下消失**，不能做生产校验
- **`is` 与 `==` 和 Java 正好相反**——`==` 是值比较
- 三元表达式**语序相反**，条件在中间

> 相关章节：[闭包与延迟绑定](../practice/03-pitfalls.md#2-闭包延迟绑定)、[`==` vs `is`](../practice/03-pitfalls.md#3--vs-is与-java-正好相反)

> 📁 [完整代码](../code/basics/06_keywords.py)
