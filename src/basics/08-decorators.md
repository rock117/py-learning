# 装饰器入门

装饰器是 Python 最常用的语言特性之一，也是初学者最容易"会抄不会写"的地方。

它之所以算**基础**，是因为你每天都在用它：

```python
@property
@classmethod
@staticmethod
@contextmanager
@pytest.fixture
@app.route("/users")
@lru_cache(maxsize=128)
```

不先搞懂装饰器，这些全都只能死记硬背。

> 本章讲**入门**：从为什么需要它，到能自己写出带参数的装饰器。
> 进阶用法（叠加顺序、`lru_cache`、`singledispatch`、`cached_property`）见[装饰器进阶](../advanced/03-decorators.md)。

## 为什么需要装饰器

> [动机演示](../code/basics/08_decorators.py#L40-L86)

```python
{{#include ../code/basics/08_decorators.py:40:86}}
```

需求：给每个函数加上"打印调用日志"和"计时"。

不用装饰器时：

```python
def fetch_user(uid):
    start = time.perf_counter()                  # 重复 1
    print(f"[LOG] fetch_user({uid})")            # 重复 2
    result = _fetch_user(uid)
    print(f"[LOG] 耗时 {time.perf_counter()-start:.3f}s")
    return result

def save_order(order):
    start = time.perf_counter()                  # 又是同一套
    print(f"[LOG] save_order({order})")
    ...
```

**问题**：10 个函数抄 10 遍，改一次要改 10 处；真正的业务逻辑被淹没。

用装饰器后：

```python
@logged
@timed
def fetch_user(uid):
    return _fetch_user(uid)
```

横切逻辑只写一次。

> [Java 对比] 这正是 **Spring AOP** 解决的问题（`@Around` / `@Before` 切面）。区别在于：Java 靠运行时代理或字节码增强，Python 靠纯函数组合——简单得多，也没有"代理失效"那些坑。

## 前置一：函数是对象

> [函数即对象](../code/basics/08_decorators.py#L88-L128)

```python
{{#include ../code/basics/08_decorators.py:88:128}}
```

装饰器能成立，前提是 Python 的函数是一等公民：

```python
def greet(name):
    return f"Hello, {name}"

f = greet              # ① 赋值给变量
apply(greet, "B")      # ② 作为参数传递

def make_greeter(prefix):
    def inner(name):
        return f"{prefix}, {name}"
    return inner       # ③ 作为返回值

greet.owner = "team-a" # ④ 函数可以有属性
greet.__name__         # 'greet'，常用元信息
```

> [Java 对比] Java 的方法不是一等公民，要传函数得用 `Function` / `BiFunction` 这类函数式接口包装；Python 直接传函数对象即可。**这是装饰器能实现的根本原因。**

## 前置二：闭包

> [闭包演示](../code/basics/08_decorators.py#L130-L178)

```python
{{#include ../code/basics/08_decorators.py:130:178}}
```

```python
def make_counter():
    count = 0
    def inner():
        nonlocal count        # 修改外层变量
        count += 1
        return count
    return inner

c1 = make_counter()
c1(); c1(); c1()              # 1, 2, 3 —— 独立计数
c2 = make_counter()
c2()                          # 1 —— 另有一份 count
```

每次调用外层函数都会创建**新的闭包环境**。

### 为什么装饰器需要闭包

装饰器要"记住"被装饰的原函数，闭包正好能做这件事：

```python
def deco(func):
    def wrapper():
        func()        # func 来自闭包，被"记住"了
    return wrapper
```

> ⚠️ 闭包捕获的是**变量本身**，不是当时的快照。这是经典的延迟绑定问题：

```python
[lambda: i for i in range(3)]        # 调用后全是 2
[lambda i=i: i for i in range(3)]    # 0, 1, 2（用默认参数固定）
```

详见[常见陷阱](../practice/03-pitfalls.md#2-闭包延迟绑定)。

## 从零手写装饰器

> [手写过程](../code/basics/08_decorators.py#L180-L210)

```python
{{#include ../code/basics/08_decorators.py:180:210}}
```

先不写 `@`，纯手写一遍，理解本质：

```python
# 第一步：普通函数
def add(a, b):
    return a + b

# 第二步：写一个"接收函数、返回函数"的函数
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"[BEFORE] 调用 {func.__name__}")
        result = func(*args, **kwargs)
        print(f"[AFTER] 返回 {result}")
        return result
    return wrapper

# 第三步：手动替换
add = my_decorator(add)
```

`add(1, 2)` 现在会打印前后日志。

**核心**：装饰器就是"函数替换"——`新函数 = 装饰器(旧函数)`。

## `@` 只是语法糖

> [语法糖验证](../code/basics/08_decorators.py#L212-L244)

```python
{{#include ../code/basics/08_decorators.py:212:244}}
```

```python
# 写法 A
def add(a, b):
    return a + b
add = my_decorator(add)

# 写法 B —— 完全等价
@my_decorator
def add(a, b):
    return a + b
```

> [要点] `def` 后面的名字被**重新绑定**成了 `wrapper`。原函数只存在于闭包里，外部已经无法直接访问了。

## `wrapper` 的三个必须

这是实际写装饰器时最容易出错的三个点。

> [三个必须的演示](../code/basics/08_decorators.py#L246-L317)

```python
{{#include ../code/basics/08_decorators.py:246:317}}
```

### 必须 1：`*args, **kwargs`

不写就无法包装带参数的函数：

```python
# ❌
def wrapper():
    return func()
```

实测报错：

```
TypeError: wrapper() takes 0 positional arguments but 1 was given
```

```python
# ✅
def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
```

> 这里用到的正是[星号解包](01-star-unpacking.md)的"收集 + 展开"。

### 必须 2：`return` 原函数的结果

```python
# ❌ 最隐蔽的 bug
def wrapper(*args, **kwargs):
    func(*args, **kwargs)      # 忘记 return
```

实测：`add(1, 2)` 返回 `None`，**不报错**，直到下游用结果时才炸。

### 必须 3：`functools.wraps`

```python
import functools

def decorator(func):
    @functools.wraps(func)     # ✅
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

实测差异：

| | `__name__` | `__doc__` |
|---|---|---|
| 不用 `wraps` | `'wrapper'` | `None` |
| 用了 `wraps` | `'documented_b'` | `'原始文档字符串 B。'` |

**影响面**：日志里的函数名、IDE 提示、`help()`、文档生成、pytest 用例名。

> [Java 对比] Java 的注解不会改变方法元数据；Python 的装饰器**直接替换了函数对象**，所以必须手动保留元信息。

## 带参数的装饰器：三层嵌套

> [三层嵌套示例](../code/basics/08_decorators.py#L319-L370)

```python
{{#include ../code/basics/08_decorators.py:319:370}}
```

目标：`@repeat(times=3)` 让函数重复执行 3 次。

```python
def repeat(times):                       # 第 1 层：接收装饰器参数
    def decorator(func):                 # 第 2 层：接收被装饰函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs):    # 第 3 层：接收调用参数
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator

@repeat(times=3)
def say(name):
    return f"hi {name}"
```

调用 `say("A")` 返回 `['hi A', 'hi A', 'hi A']`。

### 逐层拆解

```
① @repeat(times=3) 先执行 repeat(3)
   -> 返回 decorator（一个只差 func 的函数）
② 再执行 decorator(say)
   -> 返回 wrapper
③ say 被重新绑定为 wrapper
```

等价于：

```python
say = repeat(times=3)(say)
```

### 为什么必须是三层

| 层 | 负责 | 缺了会怎样 |
|---|---|---|
| 第 1 层 | 接收 `times` | `repeat(3)` 无法接收 3 |
| 第 2 层 | 接收 `func` | 不知道要包装谁 |
| 第 3 层 | 接收 `args`/`kwargs` | 无法接收调用实参 |

> ⚠️ 常见错误：最内层忘了 `@functools.wraps(func)` 导致元信息丢失；或者 `return decorator` 写成 `return wrapper` 直接报错。

## 类装饰器

> [类装饰器示例](../code/basics/08_decorators.py#L372-L419)

```python
{{#include ../code/basics/08_decorators.py:372:419}}
```

用 `__call__` 让实例可调用：

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0
        functools.update_wrapper(self, func)   # 保留元信息

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)

@CountCalls
def greet(name):
    return f"Hello, {name}"
```

调用三次后，`greet.count == 3`——状态可以对外读取。

### 与闭包写法的取舍

| | 闭包 | 类装饰器 |
|---|---|---|
| 代码量 | 少 | 多 |
| 状态可读 | ❌ 藏在闭包里 | ✅ `greet.count` |
| 支持继承/扩展 | ❌ | ✅ |
| 适合场景 | 绝大多数 | 需要暴露状态时 |

### 带参数的类装饰器

```python
class Retry:
    def __init__(self, times):      # 接收装饰器参数
        self.times = times
    def __call__(self, func):       # 接收被装饰函数
        def wrapper(*a, **kw):
            ...
        return wrapper
```

注意与无参版本的区别：`__init__` 和 `__call__` 各接收什么，正好对应闭包写法的三层。

## 常见错误

> [完整演示](../code/basics/08_decorators.py#L421-L463)

```python
{{#include ../code/basics/08_decorators.py:421:463}}
```

| 坑 | 后果 |
|---|---|
| 忘记 `return` 原函数结果 | **静默返回 `None`**，最隐蔽 |
| 忘记 `@functools.wraps` | `__name__` 变成 `'wrapper'`，日志/文档全错 |
| `wrapper` 不带 `*args, **kwargs` | 只能包装无参函数 |
| 带参装饰器少写一层 | `@repeat(3)` 会把 3 当成 func |
| **装饰器在导入时就执行** | 里面有 IO/网络会拖慢启动甚至失败 |
| 叠加顺序搞反 | 见下 |

### 叠加顺序

```python
@tag("outer")
@tag("inner")
def content():
    return "X"
```

结果：`<outer><inner>X</inner></outer>`

**规则：下面（离 `def` 越近）的先包装。** 等价于 `content = tag("outer")(tag("inner")(content))`。

### 装饰器在导入期执行

```python
@deco           # 这个调用发生在模块被 import 的时候
def f(): ...
```

所以装饰器里不要做耗时操作（读大文件、连数据库、发网络请求）——会在导入时同步执行。

## Java 对照总表

> [完整对照](../code/basics/08_decorators.py#L466-L483)

```python
{{#include ../code/basics/08_decorators.py:466:483}}
```

| 场景 | Python | Java |
|------|--------|------|
| 横切逻辑 | `@decorator`（函数组合） | AOP `@Around` / `@Before` |
| 带参数 | `@deco(arg)` 三层嵌套 | `@Repeat(3)` 注解属性 |
| 有状态 | 类装饰器 `__call__` | `InvocationHandler` 代理 |
| 元信息 | `functools.wraps` | 注解不改变方法元数据 |
| **执行时机** | **导入时（装饰即替换）** | 运行时织入 |
| 属性访问 | `@property` | getter |
| 测试夹具 | `@pytest.fixture` | `@BeforeEach` |
| 路由 | `@app.route("/x")` | `@RequestMapping` |

## 小结

- 装饰器的本质是**函数替换**：`新函数 = 装饰器(旧函数)`
- 前提是**函数是一等公民** + **闭包**能记住原函数
- `@deco` 完全等价于 `f = deco(f)`
- `wrapper` 的三个必须：`*args/**kwargs`、`return`、`functools.wraps`
- **带参数装饰器 = 三层嵌套**：参数层 → 函数层 → 调用层
- 需要暴露状态时用类装饰器，否则闭包更简洁
- **装饰器在导入期执行**，不要在里面做耗时操作

> 下一步：看[装饰器进阶](../advanced/03-decorators.md)了解叠加顺序、`lru_cache`、`singledispatch`、`cached_property`。

> 📁 [完整代码](../code/basics/08_decorators.py)
