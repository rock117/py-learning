# 标准库核心

本章覆盖 Python 标准库中出场率最高的五个模块：`os` / `sys`、`pathlib`、`collections`、`itertools`、`functools`。
每个模块都给出 Java 对应物，并重点标出**行为差异**——那些你在 Java 里形成的直觉，在 Python 里会失效的地方。

## 总览：Python ↔ Java 对应表

| Python 模块 | Java 对应 | 关键差异 |
|-------------|-----------|----------|
| `os`, `os.path` | `Files` + `Paths` | 路径是**字符串**，没有 `Path` 对象 |
| `sys` | `System` + `Runtime` | `argv` 含脚本名；`sys.path` ≈ classpath |
| `pathlib` | `java.nio.file.Path` | 最接近的对应物，新代码只用它 |
| `collections` | `java.util` + Guava | `deque` ↔ `ArrayDeque`、`Counter` ↔ Multiset |
| `itertools` | `java.util.stream` | 惰性一次性消费，但没有 `.collect()` |
| `functools` | `java.util.function` | `reduce` 需 import，不再是内置函数 |

> [示例](../code/libraries/01_stdlib_core.py)

## os 与 sys

### os.path：基于字符串的路径操作

`os.path` 全是**纯函数**，输入输出都是 `str`。它不校验路径是否存在、也没有对象语义上的约束——
字符串拼错了它不会拦你。

> [os.path 演示](../code/libraries/01_stdlib_core.py#L66-L91)

```python
{{#include ../code/libraries/01_stdlib_core.py:66:91}}
```

```python
p = os.path.join("a", "b", "c.txt")   # Windows: a\b\c.txt
os.path.splitext(p)                    # ('a\\b\\c', '.txt')，返回 tuple
os.path.normpath("a//b/../c")          # a\c，纯字符串归一化，不碰磁盘
```

> ⚠️ `os.path` 的行为取决于**运行平台**，不是取决于路径长相。Windows 上 `join("a","b")` 得 `a\b`，
> Linux 上得 `a/b`。别用它拼接 URL 或「远程 Linux 机器上的路径」。

### os.environ 与 os.walk

对应 `System.getenv()`，但 Python 这个是**可写**的映射视图；`os.walk` 则对应 `Files.walk()`，
但允许你在遍历中**原地修改 `dirnames`** 来剪枝。

> [os.environ 演示](../code/libraries/01_stdlib_core.py#L94-L113) ·
> [os.walk 演示](../code/libraries/01_stdlib_core.py#L115-L137)

```python
{{#include ../code/libraries/01_stdlib_core.py:115:137}}
```

```python
os.environ.get("PATH", "")          # 不存在返回默认值，不抛 KeyError
os.environ["MY_VAR"] = "hello"      # 只影响当前进程及子进程

for dirpath, dirnames, filenames in os.walk("."):
    if depth > 1:
        dirnames.clear()   # 原地清空，阻止继续向下递归
        continue
```

> ⚠️ Windows 上 `os.environ` 的键**不区分大小写**（`os.environ["path"]` 能取到 `PATH`），Linux/macOS 区分。
> `os.walk` 的剪枝技巧依赖于 `dirnames` 是**可变 list**，`Files.walk()` 里没有等价手段。

### sys：解释器自身的运行时信息

> [sys 基础演示](../code/libraries/01_stdlib_core.py#L140-L161)

```python
{{#include ../code/libraries/01_stdlib_core.py:140:161}}
```

| Python | Java 对应 | 差异要点 |
|--------|-----------|----------|
| `sys.argv` | `main(String[] args)` | ⚠️ `argv[0]` 是**脚本名**，Java 的 `args` 不含程序名 |
| `sys.path` | classpath | 是**可变 list**，运行时可 `insert(0, ...)` 热插拔模块 |
| `sys.modules` | 已加载类缓存 | 模块级单例注册表 |
| `sys.platform` | `System.getProperty("os.name")` | 值是 `win32` / `linux` / `darwin` |
| `sys.exit(n)` | `System.exit(n)` | 抛的是 `SystemExit`，可被 `except` 捕获 |

> ⚠️ `sys.platform` 在 Windows 上返回 `"win32"`（**即使你是 64 位**），在 macOS 上返回 `"darwin"`。
> 判断操作系统优先用 `os.name == "nt"`。

### sys.stdout：标准流是文本流对象

> [sys 标准流演示](../code/libraries/01_stdlib_core.py#L164-L186)

```python
{{#include ../code/libraries/01_stdlib_core.py:164:186}}
```

```python
sys.stdout.reconfigure(encoding="utf-8")   # 3.7+ 解决 Windows 控制台中文乱码
```

> ⚠️ Windows 控制台默认编码通常是 GBK（`cp936`）。Java 里 `System.out.println("中文")` 一般没事，
> 但 Python 输出超出 GBK 的字符（如 emoji）会直接抛 `UnicodeEncodeError`。所以本书所有 demo 都不用 emoji。

## pathlib：推荐替代 os.path

`pathlib.Path` 是 Python 版的 `java.nio.file.Path`，而且更顺手——拼接用 `/` 运算符，文件读写直接挂在对象上。

> [pathlib 基础演示](../code/libraries/01_stdlib_core.py#L188-L204)

```python
{{#include ../code/libraries/01_stdlib_core.py:188:204}}
```

```python
p = Path("a") / "b" / "c.txt"
p.name, p.stem, p.suffix, p.parent, p.parts
# 'c.txt', 'c', '.txt', 'a/b', ('a', 'b', 'c.txt')
```

| 操作 | `pathlib` | Java `Path` |
|------|-----------|-------------|
| 拼接 | `Path("a") / "b"` | `Path.of("a").resolve("b")` |
| 去扩展名 | `p.stem` | 需手写 `substring` |
| 父目录 | `p.parent` | `p.getParent()` |

### 便捷文件读写

Java 要到 11 才有 `Files.readString` / `writeString`，而 pathlib 一直就有：

> [pathlib 文件读写演示](../code/libraries/01_stdlib_core.py#L207-L228)

```python
{{#include ../code/libraries/01_stdlib_core.py:207:228}}
```

```python
tmp.write_text("第一行\n第二行\n", encoding="utf-8")
content = tmp.read_text(encoding="utf-8")
```

> ⚠️ `write_text()` 默认使用**系统编码**（Windows 通常是 GBK），而 Java 的 `Files.writeString` 默认 UTF-8。
> 有中文的地方请**显式传 `encoding="utf-8"`**，否则 Linux 写入的文件到 Windows 上就是乱码。

### glob 与路径元信息

> [pathlib glob 遍历](../code/libraries/01_stdlib_core.py#L231-L241) ·
> [pathlib 文件信息](../code/libraries/01_stdlib_core.py#L244-L255) ·
> [pathlib 创建删除演示](../code/libraries/01_stdlib_core.py#L258-L285)

```python
{{#include ../code/libraries/01_stdlib_core.py:258:285}}
```

```python
list(Path(".").glob("*.py"))     # 只匹配当前层
list(Path(".").rglob("*.py"))    # 递归匹配（r = recursive）
d.mkdir(parents=True, exist_ok=True)   # 等价 mkdir -p
f.unlink()                             # 删文件；删目录用 d.rmdir()（仅空目录）
```

> ⚠️ `mkdir()` 默认 `exist_ok=False`，目录已存在会抛 `FileExistsError`——而 Java 的 `Files.createDirectories()`
> 对已存在目录**静默成功**。同理 `unlink()` 删不存在的文件会抛异常，`File.delete()` 只返回 `false`。
> 这是从 Java 迁过来后「莫名报错」的第一大来源。

## collections：高级容器

| Python | Java 对应 | 差异要点 |
|--------|-----------|----------|
| `namedtuple` | `record` | 不可变、可按索引访问、可解包 |
| `Counter` | Guava `Multiset` | 缺键返回 **0**，不是 `null` |
| `defaultdict` | `computeIfAbsent` | **读取即写入**，有副作用 |
| `OrderedDict` | `LinkedHashMap` | 3.7+ 普通 `dict` 也已有序 |
| `deque` | `ArrayDeque` | 支持 `maxlen`，不支持切片 |
| `ChainMap` | 无直接对应 | 多映射串联查找，不复制 |

### namedtuple：轻量不可变记录

> [namedtuple 演示](../code/libraries/01_stdlib_core.py#L287-L309)

```python
{{#include ../code/libraries/01_stdlib_core.py:287:309}}
```

```python
Point = namedtuple("Point", ["x", "y"])
p.x, p[0]                        # 按名字 / 按索引都能访问
p._replace(x=10)                 # 返回新实例，原对象不变
```

比 Java 的 `record` 多了「按索引访问」和「可解包」，但它**没有类型注解**（想要注解用 `typing.NamedTuple`）。

### Counter / defaultdict

> [Counter 演示](../code/libraries/01_stdlib_core.py#L312-L327) ·
> [defaultdict 演示](../code/libraries/01_stdlib_core.py#L330-L347)

```python
{{#include ../code/libraries/01_stdlib_core.py:330:347}}
```

```python
c.most_common(2)            # 最高频的 2 个
c - Counter({"the": 1})     # 逐键相减，负数结果被丢弃

dd = defaultdict(list)
dd[word[0]].append(word)    # 不存在的键自动创建 []
```

> ⚠️ `Counter` 缺键时返回 `0` 而不是 `KeyError`。`defaultdict` 更狠：**只是读取** `dd[k]` 就会把键写入字典
> （`[]` 触发工厂，`in` / `get` 不会）。两者都会干扰「键是否存在」的判断。

### OrderedDict / deque / ChainMap

> [OrderedDict 演示](../code/libraries/01_stdlib_core.py#L350-L369) ·
> [deque 演示](../code/libraries/01_stdlib_core.py#L372-L390) ·
> [ChainMap 演示](../code/libraries/01_stdlib_core.py#L393-L416)

```python
{{#include ../code/libraries/01_stdlib_core.py:393:416}}
```

```python
dq = deque([1, 2, 3], maxlen=5)   # 满了自动从另一端丢弃；不支持切片
dq.appendleft(0)                  # 左侧插入 O(1)，而 list.insert(0, x) 是 O(n)

od.move_to_end("a")               # 移到末尾
od.popitem(last=False)            # 弹出最旧的一个（FIFO）——LRU 积木

cm = ChainMap(user_prefs, defaults)   # 前面的优先
cm["theme"] = "blue"                  # 写入只落到第一个映射
```

Java 没有 ChainMap，通常得 `new HashMap<>(defaults); putAll(userPrefs)` 复制一份。

## itertools：惰性迭代器工具

`itertools` 是 Python 的 `Stream` API，但有两个本质差别：**没有 `.collect()`**（要拿结果必须 `list(...)`），
以及输出是**一次性迭代器**——消费掉就没了。

| itertools | Java Stream 对应 | 备注 |
|-----------|------------------|------|
| `chain` | `Stream.concat` / `flatMap` | `chain.from_iterable` 用于嵌套 |
| `groupby` | `Collectors.groupingBy` | ⚠️ 只合并**相邻**相同元素 |
| `combinations` / `permutations` | 无 | 组合 / 排列 |
| `islice` / `starmap` / `accumulate` | `limit` / `skip` / `reduce` | `starmap` 把 tuple 解包为参数 |
| `cycle` / `repeat` / `count` | `iterate` / `generate` | 无限流，必须配 `islice` |

### chain 与 groupby

> [chain 演示](../code/libraries/01_stdlib_core.py#L418-L427) ·
> [groupby 演示](../code/libraries/01_stdlib_core.py#L430-L440)

```python
{{#include ../code/libraries/01_stdlib_core.py:430:440}}
```

```python
list(chain.from_iterable([[1, 2], [3]]))   # 等价 flatMap
for key, group in groupby(sorted(data, key=f), key=f):
    print(key, list(group))
```

> ⚠️ `groupby` 与 `Collectors.groupingBy` 语义**完全不同**：它只把**连续**的相同 key 归为一组，
> 不先 `sorted()` 就会把同一个 key 分成多组。而且 `group` 是共享底层迭代器的子迭代器，
> 必须在进入下一轮循环前 `list(group)` 消费掉。

### 排列组合、islice 与无限流

> [排列组合演示](../code/libraries/01_stdlib_core.py#L443-L452) ·
> [islice 演示](../code/libraries/01_stdlib_core.py#L455-L464) ·
> [starmap 演示](../code/libraries/01_stdlib_core.py#L466-L476) ·
> [无限迭代器演示](../code/libraries/01_stdlib_core.py#L479-L489) ·
> [tee 演示](../code/libraries/01_stdlib_core.py#L492-L507)

```python
{{#include ../code/libraries/01_stdlib_core.py:492:507}}
```

```python
list(combinations("ABC", 2))                # 组合，无序
list(permutations("ABC", 2))                # 排列，有序
list(islice(count(10, 2), 5))               # 从 10 开始、步长 2，取 5 个
list(starmap(pow, [(2, 3), (4, 5)]))        # [8, 1024]
list(accumulate([1, 3, 5, 7]))              # [1, 4, 9, 16]
it1, it2 = tee(range(5), 2)                 # 把一个迭代器复制成两个
```

> ⚠️ `count` / `cycle` / `repeat` 是**无限**迭代器，不截断就 `list()` 会吃光内存。
> `tee` 之后**原迭代器不要再用**；副本消费速度相差很大时缓冲区会一直涨，不如直接 `list()` 一次。

## functools：函数式工具

| functools | Java 对应 | 差异要点 |
|-----------|-----------|----------|
| `reduce` | `Stream.reduce` | Python 3 已移到 `functools`，不再内置 |
| `partial` | lambda 固定参数 | 返回可调用对象 |
| `cache` / `lru_cache` | Caffeine / Guava Cache | 按**参数**做 key，参数必须可哈希 |
| `cached_property` | 手写 lazy getter + `volatile` | 缓存在实例 `__dict__` 里 |
| `singledispatch` | 方法重载 | 按**第一个参数**的类型分派 |
| `total_ordering` / `wraps` | `Comparable` / 无对应 | 补全比较方法 / 装饰器保留元信息 |

### reduce / partial / 缓存

> [reduce 演示](../code/libraries/01_stdlib_core.py#L509-L522) ·
> [partial 演示](../code/libraries/01_stdlib_core.py#L525-L542) ·
> [cache 演示](../code/libraries/01_stdlib_core.py#L545-L564)

```python
{{#include ../code/libraries/01_stdlib_core.py:545:564}}
```

```python
reduce(lambda x, y: x + y, [1, 2, 3, 4], 100)    # 110，带初值
b2int = partial(int, base=2)                     # b2int("1010") == 10

@cache                    # 3.9+，等价 lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
slow_func.cache_info()    # hits / misses / maxsize / currsize
```

> ⚠️ 序列为空且没给初值时 `reduce` 抛 `TypeError`（Java 的 `Stream.reduce` 返回 `Optional`）。
> `lru_cache` 的 key 由**调用参数**构成，传 `list` / `dict` 会直接抛 `TypeError`；
> `@cache` 无上限且是进程级全局，长期运行的服务请优先用 `lru_cache(maxsize=N)`。

### cached_property / singledispatch

> [cached_property 演示](../code/libraries/01_stdlib_core.py#L567-L587) ·
> [singledispatch 演示](../code/libraries/01_stdlib_core.py#L590-L616)

```python
{{#include ../code/libraries/01_stdlib_core.py:590:616}}
```

```python
@cached_property
def expensive(self):        # 第一次访问计算，之后直接命中实例 __dict__
    return [1, 2, 3]

@singledispatch
def process(obj): ...

@process.register(str)      # 按第一个参数类型分派
def _(obj): ...
```

`singledispatch` 是 Java 方法重载的动态版：Java 在**编译期**按静态类型选方法，
Python 在**运行期**按实际对象的 MRO 查找最具体的实现（子类实例会命中父类的注册项）。
`cached_property` 则要求类有 `__dict__`，所以配 `@dataclass(slots=True)` 会直接无法工作。

### total_ordering / wraps

> [total_ordering 演示](../code/libraries/01_stdlib_core.py#L619-L643) ·
> [wraps 演示](../code/libraries/01_stdlib_core.py#L646-L673)

```python
{{#include ../code/libraries/01_stdlib_core.py:646:673}}
```

```python
@total_ordering
class Student:
    def __eq__(self, other): return self.score == other.score
    def __lt__(self, other): return self.score < other.score   # 其余自动生成

@wraps(func)                # 保留 __name__ / __doc__ / __wrapped__
def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
```

`wraps` 解决的是 Java 里不存在的问题——Python 装饰器本质是**函数替换**，不加 `wraps` 的话
`greet.__name__` 会变成 `wrapper`，日志、`help()`、`singledispatch` 全都认错人。

## 小结

- **路径只用 `pathlib`**：`/` 拼接、`read_text` / `write_text`，但**务必显式指定 `encoding="utf-8"`**
- **`mkdir` 默认 `exist_ok=False`**，`unlink` 删不存在的文件会抛异常——和 Java 的静默语义相反
- **`sys.argv[0]` 是脚本名**；`sys.platform` 在 Windows 上返回 `"win32"`
- **`Counter` 缺键返回 0**，`defaultdict` 读取即写入：两者都会干扰「键是否存在」的判断
- **`deque` 两端 O(1) 但不支持切片**；`OrderedDict.move_to_end` 是现成的 LRU 积木
- **`groupby` 只合并相邻元素**，必须先排序；`tee` 之后原迭代器不可再用
- **`lru_cache` 的参数必须可哈希**，缓存是进程级的；`cached_property` 与 `slots=True` 不兼容

> 📁 [查看完整代码](../code/libraries/01_stdlib_core.py)
