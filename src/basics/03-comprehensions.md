# 推导式与生成器表达式

推导式（comprehension）是 Python 最具辨识度的语法之一，可以看作 **Java Stream API 的语法级替代**——同样一个"映射 + 过滤 + 收集"的流程，Java 要写五六个方法链，Python 一行写完。

| 形式 | 语法 | 结果类型 | Java 对应 |
|------|------|---------|-----------|
| 列表推导式 | `[f(x) for x in s if p(x)]` | `list` | `s.map(f).filter(p).toList()` |
| 字典推导式 | `{k(x): v(x) for x in s}` | `dict` | `Collectors.toMap` |
| 集合推导式 | `{f(x) for x in s}` | `set` | `Collectors.toSet` |
| 生成器表达式 | `(f(x) for x in s)` | `generator` | `s.map(f)`（惰性不收集） |

## 列表推导式

> [列表推导式示例](../code/basics/03_comprehensions.py#L31-L58)

```python
{{#include ../code/basics/03_comprehensions.py:31:58}}
```

基本形式是 `[表达式 for 变量 in 可迭代对象]`，后面可以跟任意多个 `if` 过滤：

```python
nums = [1, 2, 3, 4, 5, 6]

[n * n for n in nums]                  # 映射
[n for n in nums if n % 2 == 0]        # 过滤
["even" if n % 2 == 0 else "odd" for n in nums]   # 三元（不是过滤！）
[n for n in nums if n % 2 == 0 if n > 2]          # 多条件（等价于 and）
```

⚠️ 最常见的混淆：**`if` 在 `for` 之后是过滤，在 `for` 之前是三元表达式**。位置不同，语义完全不同：

```python
[x for x in nums if x > 2]              # 只保留 > 2 的，长度可变
[x if x > 2 else 0 for x in nums]       # 长度不变，<= 2 的变成 0
```

## 字典与集合推导式

> [字典 / 集合推导式](../code/basics/03_comprehensions.py#L61-L84)

```python
{{#include ../code/basics/03_comprehensions.py:61:84}}
```

```python
words = ["apple", "banana", "cherry"]

{w: len(w) for w in words}              # {'apple': 5, 'banana': 6, ...}
{v: k for k, v in lengths.items()}      # 键值反转
{c for w in words for c in w}           # 集合去重
```

> ⚠️ [Java 对比] `Collectors.toMap` 在遇到重复键时会抛 `IllegalStateException`（除非给 mergeFunction），而 Python 字典推导式里**后出现的同名键直接覆盖**，不会报错。数据有重复键时这个差异很容易造成静默错误。

## 生成器表达式：惰性求值

括号形式创建的是生成器，**不会立即计算**：

> [生成器表达式示例](../code/basics/03_comprehensions.py#L87-L127)

```python
{{#include ../code/basics/03_comprehensions.py:87:127}}
```

```python
gen = (n * n for n in range(1, 6))
print(gen)              # <generator object ...>，此时还没有任何计算

list(gen)               # [1, 4, 9, 16, 25]   第一次迭代
list(gen)               # []                   已耗尽
```

作为函数的唯一参数时可以省掉一层括号：

```python
sum(n * n for n in nums)
max(len(w) for w in words)
```

### 内存差异有多夸张

10 万个元素：

| 形式 | 内存占用 |
|------|---------|
| 列表推导式 `[n for n in range(100_000)]` | 约 3899 KB |
| 生成器表达式 `(n for n in range(100_000))` | 约 0.4 KB |

差了约 **1 万倍**。所以"只要最终结果是求和/最大值/写入文件"这类场景，一律用生成器表达式，不要先建列表再消费。

> ⚠️ 代价是**只能消费一次**。生成器耗尽后再迭代就是空的，而且不会报错——这点和 Java Stream 的 `Stream has already been operated upon or closed` 不同，Python 更安静，也更难排查。

## 变量作用域：Python 3 不泄漏

这是 Python 2 → 3 的一个重要变化，对了解老代码有用：

> [作用域示例](../code/basics/03_comprehensions.py#L129-L144)

```python
{{#include ../code/basics/03_comprehensions.py:129:144}}
```

```python
x = "outer"
_ = [x for x in range(3)]
print(x)        # 'outer'  <- 推导式里的 x 没有覆盖外面的

y = "outer"
for y in range(3):
    pass
print(y)        # 2        <- 普通 for 循环会覆盖
```

推导式有自己的作用域，循环变量不外泄。普通 `for` 循环则相反。

## 嵌套推导式的顺序

多个 `for` 子句**从左到右**等同于**从外到内**的嵌套循环：

> [嵌套顺序示例](../code/basics/03_comprehensions.py#L147-L170)

```python
{{#include ../code/basics/03_comprehensions.py:147:170}}
```

```python
matrix = [[1, 2, 3], [4, 5, 6]]

# 展平：外层先写
[v for row in matrix for v in row]        # [1, 2, 3, 4, 5, 6]

# 等价的手写循环
result = []
for row in matrix:
    for v in row:
        result.append(v)
```

转置时顺序要反过来：

```python
[[matrix[i][j] for i in range(len(matrix))]
 for j in range(len(matrix[0]))]
```

## 性能

> [性能对比](../code/basics/03_comprehensions.py#L173-L205)

```python
{{#include ../code/basics/03_comprehensions.py:173:205}}
```

50 万次 `x * 2`：

| 写法 | 相对耗时 |
|------|---------|
| `for` + `append` | 基准 1.00x |
| 列表推导式 | 约快 1.3–1.5x |
| `map(lambda x: ...)` | 介于两者之间 |

推导式快的原因：循环体在 C 层执行，省掉了每次 `append` 的属性查找和函数调用开销。

> [要点] 简单变换优先用推导式；已经有具名函数时 `map(func, seq)` 也很快；`map` + `lambda` 因为有 lambda 调用开销，通常不如推导式。

## 常见陷阱

### 坑 1：用推导式做副作用

```python
[print(x) for x in range(3)]      # ❌ 构造了一个无用的列表
for x in range(3): print(x)       # ✅
```

### 坑 2：嵌套超过两层

```python
[x for a in A for b in a for x in b if x > 0]     # 已经难读
```

超过两层建议拆成普通循环。可读性比少写两行重要。

### 坑 3：生成器的延迟绑定

```python
funcs = [lambda: i for i in range(3)]
[f() for f in funcs]        # [2, 2, 2]  <- 全是 2

funcs = [lambda i=i: i for i in range(3)]
[f() for f in funcs]        # [0, 1, 2]
```

lambda 捕获的是**变量名**而不是当前值，循环结束后 `i` 停在 2。

> ⚠️ [Java 对比] Java 要求 lambda 捕获 effectively final 的变量，从语法上就禁止了这种情况。Python 允许捕获可变变量，所以才有这个经典的延迟绑定问题——详见[常见陷阱](../practice/03-pitfalls.md)一章。

> [推导式常见坑](../code/basics/03_comprehensions.py#L207-L239)

```python
{{#include ../code/basics/03_comprehensions.py:207:239}}
```

## Java 对照总表

> [查看完整对照代码](../code/basics/03_comprehensions.py#L242-L259)

```python
{{#include ../code/basics/03_comprehensions.py:242:259}}
```

| 需求 | Python | Java Stream |
|------|--------|-------------|
| 映射 | `[f(x) for x in s]` | `s.map(f).toList()` |
| 过滤 | `[x for x in s if p(x)]` | `s.filter(p).toList()` |
| 映射 + 过滤 | `[f(x) for x in s if p(x)]` | `s.filter(p).map(f).toList()` |
| 转字典 | `{k(x): v(x) for x in s}` | `Collectors.toMap` |
| 转集合 | `{f(x) for x in s}` | `Collectors.toSet` |
| 展平 | `[y for x in s for y in x]` | `s.flatMap(Collection::stream)` |
| 惰性 | `(f(x) for x in s)` | `s.map(f)`（未收集） |
| 求和 | `sum(f(x) for x in s)` | `s.mapToInt(f).sum()` |

## 小结

- 四种推导式对应 Stream 的 `map`/`filter`/`collect`，但更短
- **`if` 在 `for` 后是过滤，在 `for` 前是三元**——位置决定语义
- 生成器表达式内存省几个数量级，但**只能消费一次**
- 推导式有独立作用域，循环变量不泄漏；普通 `for` 会泄漏
- 嵌套顺序 = 嵌套循环顺序，超过两层就该拆开
- 字典推导式重复键**静默覆盖**，不像 Java 的 `toMap` 报错

> 📁 [完整代码](../code/basics/03_comprehensions.py)
