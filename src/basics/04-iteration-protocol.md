# 迭代协议、for-else 与切片

这一章补的是**基础机制**。生成器、异步迭代器、可迭代容器全都建立在迭代协议之上，但前面的章节默认你已经懂了。同时补充两个 Java 完全没有的能力：`for...else` 和切片协议。

## 迭代协议：`__iter__` / `__next__`

任何对象只要实现了这两个方法，就能被 `for` 遍历：

| 方法 | 作用 |
|------|------|
| `__iter__` | 返回一个迭代器对象 |
| `__next__` | 返回下一个元素；没有更多时 **`raise StopIteration`** |

> [手写迭代器示例](../code/basics/04_iteration_protocol.py#L26-L58)

```python
{{#include ../code/basics/04_iteration_protocol.py:26:58}}
```

```python
class Countdown:
    def __init__(self, n): self.n = n

    def __iter__(self):
        return self              # 迭代器返回自己

    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1
```

`for x in obj` 的展开过程等价于：

```python
it = iter(obj)          # 调用 __iter__
while True:
    try:
        x = next(it)    # 调用 __next__
    except StopIteration:
        break
    ...循环体...
```

> ⚠️ [Java 对比] Java 用 `hasNext()` 返回 boolean 判断结束；Python 用**异常**表示结束。这意味着 `for` 循环体内部永远不会看到 `StopIteration`——它是被协议内部处理的。

## 可迭代对象 vs 迭代器

两者容易混，区别在于能否重复遍历：

| | 可迭代对象（Iterable） | 迭代器（Iterator） |
|---|---|---|
| 实现 | `__iter__` | `__iter__` + `__next__` |
| 例子 | `list` / `dict` / `str` | `iter(list)` / 生成器 |
| 可重复遍历 | ✅ | ❌ 只能一次 |
| `iter(obj) is obj` | ❌ | ✅ |

> [可迭代对象 vs 迭代器](../code/basics/04_iteration_protocol.py#L61-L79)

```python
{{#include ../code/basics/04_iteration_protocol.py:61:79}}
```

```python
data = [1, 2, 3]
list(data), list(data)      # [1,2,3] [1,2,3]   可以两次

it = iter(data)
list(it), list(it)          # [1,2,3] []        第二次是空的
```

> [Java 对比] 这个区分和 Java 一样：`List` 是可迭代的，`Iterator` 是消耗品。区别是 Python 的 `for` 直接吃可迭代对象，不要求你手写 `iterator()`。

## 生成器 = 迭代器的语法糖

> [生成器示例](../code/basics/04_iteration_protocol.py#L82-L105)

```python
{{#include ../code/basics/04_iteration_protocol.py:82:105}}
```

```python
def gen():
    yield 1
    yield 2
    yield 3

g = gen()       # 就是迭代器，有 __iter__ 和 __next__
```

> [要点] 手写迭代器的场景 99% 都可以用生成器替代。只有需要维护复杂状态、或者要复用同一个对象做迭代时，才值得写完整的类。

## `for...else`：循环的 else 分支

Python 的 `for` 和 `while` 可以带 `else`，它**在循环正常结束（没被 `break`）时执行**：

> [for-else 示例](../code/basics/04_iteration_protocol.py#L107-L129)

```python
{{#include ../code/basics/04_iteration_protocol.py:107:129}}
```

```python
for n in nums:
    if n % 2 == 0:
        print(f"找到偶数 {n}")
        break
else:
    print("循环走完都没找到偶数")     # 只有没 break 才执行
```

Java 里同样的逻辑需要一个标志位：

```java
boolean found = false;
for (int n : nums) {
    if (n % 2 == 0) { found = true; break; }
}
if (!found) { ... }
```

`for...else` 就是省掉这个标志位。

> ⚠️ 三个常见误解：
> 1. **`else` 不是"循环没执行"**——空循环也会执行 `else`
> 2. **`else` 必须和 `for`/`while` 同级**，缩进错了语义完全变
> 3. **它属于循环，不属于 `if`**

### `while...else`

规则相同：

> [while-else 示例](../code/basics/04_iteration_protocol.py#L132-L152)

```python
{{#include ../code/basics/04_iteration_protocol.py:132:152}}
```

```python
n = 10
while n > 0:
    n -= 1
    if n == 5:
        break
else:
    print("正常结束")       # n 减到 5 时 break 了，所以不执行
```

### 经典用例：质数判定

`for...else` 最漂亮的用法是"找因子"这种带 break 的搜索：

> [质数判定示例](../code/basics/04_iteration_protocol.py#L155-L175)

```python
{{#include ../code/basics/04_iteration_protocol.py:155:175}}
```

```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            break
    else:
        return True         # 一个因子都没找到
    return False
```

## 切片

切片是 Python 最独特的协议入口，Java 里没有任何等价物。

### 基本语法

`seq[start:stop:step]`，区间是**左闭右开** `[start, stop)`：

> [切片基础](../code/basics/04_iteration_protocol.py#L177-L200)

```python
{{#include ../code/basics/04_iteration_protocol.py:177:200}}
```

```python
s = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

s[2:5]      # [2, 3, 4]
s[:3]       # [0, 1, 2]
s[7:]       # [7, 8, 9]
s[::2]      # [0, 2, 4, 6, 8]      步长 2
s[::-1]     # 反转
s[-3:]      # [7, 8, 9]            负索引从末尾数
```

### 越界行为：切片宽容，索引严格

```python
s[5:100]    # [5, 6, 7, 8, 9]     ✅ stop 越界自动截断
s[100:]     # []                   ✅ 空列表
s[100]      # ❌ IndexError
```

> ⚠️ [Java 对比] Java 的 `subList` 越界抛 `IndexOutOfBoundsException`，Python 切片宽容地截断。这个差异在翻页、分段处理数据时很有用（不用自己 `Math.min`），但也意味着**写错边界不会报错**。

### `slice` 对象与命名切片

切片参数可以封装成对象，重复使用：

> [slice 对象示例](../code/basics/04_iteration_protocol.py#L203-L220)

```python
{{#include ../code/basics/04_iteration_protocol.py:203:220}}
```

```python
HEADER = slice(0, 3)
BODY = slice(3, 7)

record[HEADER]      # 比 record[0:3] 自解释得多
record[BODY]
```

`slice(2, 5)` 和 `s[2:5]` 是等价的——后者在底层就是把参数打包成 `slice` 对象传给 `__getitem__`。

### 自定义类支持切片

这是理解切片本质的关键：**索引和切片走的是同一个 `__getitem__`**，只是参数类型不同（`int` vs `slice`）。

> [自定义切片支持](../code/basics/04_iteration_protocol.py#L223-L258)

```python
{{#include ../code/basics/04_iteration_protocol.py:223:258}}
```

```python
class Playlist:
    def __init__(self, songs):
        self._songs = list(songs)

    def __getitem__(self, index):
        return self._songs[index]      # int 或 slice 都透传

p = Playlist(["a", "b", "c", "d", "e"])
p[0]        # 'a'
p[1:3]      # ['b', 'c']
p[::-1]     # 反转
```

### 只实现 `__getitem__` 也能被 for 遍历

一个古老的协议约定：`for` 找不到 `__iter__` 时，会退化成用 `__getitem__(0)`, `__getitem__(1)`... 直到抛 `IndexError`。

> [旧式迭代协议](../code/basics/04_iteration_protocol.py#L223-L258)

```python
{{#include ../code/basics/04_iteration_protocol.py:223:258}}
```

```python
class OnlyGetitem:
    def __getitem__(self, i):
        if i >= 3:
            raise IndexError
        return i * 10

[x for x in OnlyGetitem()]      # [0, 10, 20]
```

> [要点] 这是历史遗留特性，读老代码时会遇到。新代码请实现 `__iter__`。

### 切片赋值

切片不仅能读，还能写，而且**长度可以不同**：

> [切片赋值示例](../code/basics/04_iteration_protocol.py#L261-L285)

```python
{{#include ../code/basics/04_iteration_protocol.py:261:285}}
```

```python
s = list(range(8))          # [0, 1, 2, 3, 4, 5, 6, 7]

s[2:5] = ["a", "b"]         # [0, 1, 'a', 'b', 5, 6, 7]   替换 3 个为 2 个
s[1:1] = ["inserted"]       # 在位置 1 插入（空切片 = 插入）
s[::2] = ["x"] * 4          # 步长赋值，长度必须精确匹配
del s[1:3]                  # 删除切片
```

> ⚠️ 步长不为 1 时，赋值的长度必须**精确匹配**被替换的元素个数，否则 `ValueError`。

## 常见陷阱

> [完整陷阱演示](../code/basics/04_iteration_protocol.py#L287-L323)

```python
{{#include ../code/basics/04_iteration_protocol.py:287:323}}
```

### 坑 1：迭代时修改容器

```python
s = [1, 2, 3, 4]
for x in s:
    if x == 2:
        s.remove(x)
# s == [1, 3, 4]，3 被跳过了，而且【不报错】
```

正确做法是遍历副本或重新构造：

```python
for x in s[:]: ...                          # 遍历切片副本
s = [x for x in s if x != 2]                # 更推荐
```

### 坑 2：切片是浅拷贝

```python
nested = [[1], [2]]
copy = nested[:]
copy[0].append(99)
# nested == [[1, 99], [2]]    原列表也被改了
```

内层对象仍是共享引用。需要完全独立用 `copy.deepcopy`。

### 坑 3：切片边界

```python
s[len(s):]     # []      不是最后一个元素
s[-1:]         # [最后一个]
s[s.index(1):] # 从某元素到末尾
```

### 坑 4：迭代器耗尽后静默返回空

```python
it = iter([1, 2])
list(it)       # [1, 2]
list(it)       # []       不报错
```

这比 Java 的 `IllegalStateException` 更难发现。

## Java 对照总表

> [查看完整对照代码](../code/basics/04_iteration_protocol.py#L326-L344)

```python
{{#include ../code/basics/04_iteration_protocol.py:326:344}}
```

| 场景 | Python | Java |
|------|--------|------|
| 可迭代对象 | `__iter__` | `Iterable` |
| 迭代器 | `__iter__` + `__next__` | `Iterator` |
| 结束标志 | `raise StopIteration` | `hasNext() == false` |
| 循环结束检测 | `for...else` | 布尔标志位 |
| 索引访问 | `__getitem__` | `get(int)` |
| 切片 | `obj[a:b:c]`（`__getitem__` 收 `slice`） | `subList` / 循环 |
| 长度 | `__len__` | `size()` |
| 切片越界 | 自动截断 | 抛异常 |
| 反转 | `seq[::-1]` | `Collections.reverse` |

## 小结

- 迭代靠 `__iter__` + `__next__`，结束用 **`StopIteration` 异常**而非布尔判断
- 可迭代对象可重复遍历，迭代器只能一次
- **`for...else`** 在循环没有 `break` 时执行，替代 Java 的标志位
- 切片**越界不报错**（自动截断），但单个索引越界会报错
- 索引与切片都走 `__getitem__`，区别只是参数是 `int` 还是 `slice`
- 切片是浅拷贝；迭代中修改容器会静默出错

> 📁 [完整代码](../code/basics/04_iteration_protocol.py)
