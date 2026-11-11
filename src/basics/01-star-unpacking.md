# 星号解包：`*` 与 `**`

Python 的星号是本教程里**被代码用例最多、却最晚被系统讲解**的语法。装饰器、`functools.partial`、日志封装里到处是 `*args, **kwargs`，但很少有人讲清楚它其实有四种完全不同的用法，其中三种 Java 里根本没有对应语法。

## 四种用法一览

| # | 用法 | 位置 | 示例 |
|---|------|------|------|
| 1 | 展开位置参数 | 调用处 | `f(*seq)` |
| 2 | 展开关键字参数 | 调用处 | `f(**mapping)` |
| 3 | 收集参数 | 定义处 | `def f(*args, **kwargs)` |
| 4 | 字面量解包 | 表达式 | `[*a, *b]` / `{**d1, **d2}` |

最容易搞混的是 1 和 3：**同一个 `*`，在调用处是"展开"，在定义处是"收集"，方向正好相反。**

## 调用时展开位置参数 `f(*seq)`

这是你最先会遇到的形式：

```python
identities = (frame.analysis_session_id, frame.stream_id, frame.media_timeline_id)
channel = channel_of(*identities)
```

`channel_of(*identities)` 完全等价于 `channel_of(1, 2, 3)`——把元组拆成三个独立的位置参数。如果漏掉 `*`，写成了 `channel_of(identities)`，那么整个元组会被当成**第一个**参数传入，直接 `TypeError`。

> [调用时展开位置参数](../code/basics/01_star_unpacking.py#L28-L55)

```python
{{#include ../code/basics/01_star_unpacking.py:28:55}}
```

`*` 不限于元组，任何可迭代对象都行：

```python
channel_of(*[4, 5, 6])                    # list
channel_of(*range(3))                     # range
channel_of(*(x for x in (7, 8, 9)))       # 生成器
```

还可以和普通参数混用，或者连用多个 `*`：

```python
f(0, *(1, 2))            # -> f(0, 1, 2)
f(*(0,), *(1,), *(2,))   # 3.5+ 支持多个 *
```

> [Java 对比] Java 只有 `void f(Object... args)` 这种形参才接收展开的数组，而且**语法上不区分**——直接写 `f(array)` 就行。Python 必须显式写出 `*`，这也意味着你不能"顺手"把数组当单个参数传，误用会被立刻发现。

## 调用时展开关键字参数 `f(**mapping)`

`**` 把字典拆成关键字参数：

```python
params = {"name": "Alice", "age": 30}
create_user(**params)                       # -> create_user(name="Alice", age=30)
create_user(city="Beijing", **params)       # 混合写法
```

两个限制：

- 字典的键**必须是字符串**（因为它们要变成参数名）
- 不能与已有的位置参数/关键字参数重复，否则 `TypeError`

> [关键字展开示例](../code/basics/01_star_unpacking.py#L58-L82)

```python
{{#include ../code/basics/01_star_unpacking.py:58:82}}
```

> ⚠️ `**` 展开是很多"配置透传"代码的基础，但也容易掩盖拼写错误。如果字典里多了一个目标函数不认识的键，会直接报 `unexpected keyword argument`——这其实是好事，比静默忽略安全。

> [Java 对比] Java 完全没有这个语法。最接近的是用 `Map` + 反射 `Method.invoke`，但类型完全不安全，而且性能差一个数量级。

## 位置 + 关键字混合转发

装饰器的标准写法就是两者的组合：

```python
def wrapper(*args, **kwargs):
    return target(*args, **kwargs)
```

> [混合转发示例](../code/basics/01_star_unpacking.py#L85-L106)

```python
{{#include ../code/basics/01_star_unpacking.py:85:106}}
```

这是"收集"（定义处）和"展开"（调用处）在同一个函数里的配合——`def wrapper(*args, **kwargs)` 先把任意参数收成 tuple 和 dict，再原样展开给 `target`。

## 定义时收集参数 `def f(*args, **kwargs)`

> [定义时收集参数](../code/basics/01_star_unpacking.py#L108-L140)

```python
{{#include ../code/basics/01_star_unpacking.py:108:140}}
```

```python
def show(*args, **kwargs):
    print(args)      # tuple  (1, 2, 3)
    print(kwargs)    # dict   {'x': 1}
```

注意 `args` 是 **tuple**（不可变），`kwargs` 是 **dict**。这点与 Java 的 `Object...` 收成数组不同。

完整的参数顺序必须是这样：

```python
def full_form(pos, default=0, *args, keyword_only, **kwargs):
    ...
```

从左到右：位置参数 → 带默认值 → `*args` → 仅关键字参数 → `**kwargs`。

### 仅关键字参数（Java 没有的能力）

`*` 之后、`**kwargs` 之前的参数，**只能按关键字传**。如果只用 `*` 作分隔符（不带名字），就是强制后续参数全部按关键字传：

```python
def strictly_kw(a, *, b):
    ...

strictly_kw(1, b=2)    # ✅
strictly_kw(1, 2)      # ❌ TypeError
```

> [Java 对比] Java 要避免"参数顺序写错"只能靠 builder 模式或大量重载。Python 用 `*` 一行解决。

## 一个字面量解包的坑

在容器字面量里用 `*` / `**` 拼接，是 Python 3.5+ 的语法：

```python
[*a, *b]                 # 列表拼接
(*a, *b)                 # 元组拼接
{*s1, *s2}               # 集合合并
{**d1, **d2}             # 字典合并，后者覆盖同名键
```

> [字面量解包示例](../code/basics/01_star_unpacking.py#L164-L192)

```python
{{#include ../code/basics/01_star_unpacking.py:164:192}}
```

> ⚠️ 注意 `{*s1, *s2}` 是**集合**推导语法的近亲，结果无序；如果要保持顺序请用列表。另外 Python 3.9+ 起字典还有更简洁的合并运算符 `d1 | d2`。

## 常见坑

### 坑 1：只做浅层展开

`*` 不会递归展开。元组里嵌元组时，展开后第一个参数仍是元组：

```python
nested = ((1, 2), 3, 4)
three_args(*nested)          # -> three_args((1, 2), 3, 4)
```

要真正摊平，需要自己处理：

```python
three_args(*nested[0], *nested[2:])
```

这条对你那段 `channel_of(*identities)` 直接相关：如果哪天 `analysis_session_id` 本身变成了元组或列表，`*identities` **不会报错**，只是把一个容器传进了本该是标量的位置。

### 坑 2：个数对得上，类型错了也不报错

```python
three_args(*(1, None, "3"))     # 静默通过，直到真正用到才炸
```

Python 是动态类型，解包只检查**参数个数**，不检查类型。要防住这类问题，要么加类型注解配 `mypy`，要么在调用前显式校验：

```python
assert len(identities) == 3, identities
channel = channel_of(*identities)
```

### 坑 3：个数不匹配立刻 TypeError

这是唯一会立刻失败的情况：

```python
three_args(*[1, 2])          # TypeError: 缺少 1 个位置参数
three_args(*[1, 2, 3, 4])    # TypeError: 多了 1 个位置参数
```

### 坑 4：与 `lru_cache` 组合时的缓存键

`@lru_cache` 装饰的函数，`f(1, 2, 3)` 和 `f(*(1, 2, 3))` 参数完全相同，**命中同一份缓存**（这符合直觉）。但 `f((1, 2, 3))` 是只传一个参数，会直接 `TypeError`。

> [常见坑完整演示](../code/basics/01_star_unpacking.py#L194-L254)

```python
{{#include ../code/basics/01_star_unpacking.py:194:254}}
```

### 坑 5：numpy 二维数组按第一维迭代

```python
arr = np.array([[1, 2], [3, 4]])
two(*arr)            # -> (array([1, 2]), array([3, 4]))   展开的是【行】
two(*arr.ravel())    # -> (1, 2)                          展平后才是标量
```

涉及数值计算时这个坑特别隐蔽，因为参数个数往往恰好对得上。

## Java 对照总表

> [查看完整对照代码](../code/basics/01_star_unpacking.py#L256-L272)

```python
{{#include ../code/basics/01_star_unpacking.py:256:272}}
```

| 场景 | Python | Java |
|------|--------|------|
| 定义可变参数 | `def f(*args)` | `void f(Object... args)` |
| 调用展开 | `f(*seq)` | `f(array)`（仅 varargs 形参可用） |
| 定义关键字参数 | `def f(**kw)` | 无 |
| 关键字展开 | `f(**mapping)` | 无（需反射） |
| 仅关键字参数 | `def f(a, *, b)` | 无（靠 builder） |
| 列表拼接 | `[*a, *b]` | `Stream.concat` / `addAll` |
| 字典合并 | `{**d1, **d2}` 或 `d1 \| d2` | `new HashMap<>()` + `putAll` |

## 小结

- **调用处 `*` 展开，定义处 `*` 收集**，方向相反
- `*seq` 适用任何可迭代对象，不要求目标函数是可变参数
- `**` 展开要求键全是字符串，且不能与已有参数冲突
- 只做浅层展开；类型错误不会在解包时报出
- 仅关键字参数 `def f(a, *, b)` 是 Java builder 模式的一行替代

> 📁 [完整代码](../code/basics/01_star_unpacking.py)
