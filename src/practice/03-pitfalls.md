# 常见陷阱与避坑指南

Python 有些陷阱极其隐蔽：语法合法、运行不报错，但行为与直觉相悖。本章列出 16 个最常见陷阱，每个用"错误写法 → 正确写法"对比展示。

> ⚠️ 这是本部分**最该先读**的章节。很多陷阱在生产环境才暴露，排查成本极高。

## 陷阱速查表

| # | 陷阱 | Java 是否有类似问题 |
|---|------|---------------------|
| 1 | 可变默认参数 | 无（Java 参数每次新建） |
| 2 | 闭包延迟绑定 | 有（lambda 捕获变量） |
| 3 | `==` vs `is` | 有，但**语义相反** |
| 4 | 浅拷贝 vs 深拷贝 | 有（`clone` 浅拷贝） |
| 5 | 可变对象作为类属性 | 有（静态可变字段） |
| 6 | async 中阻塞调用 | 有（阻塞 Event Loop） |
| 7 | except 捕获过宽 | 有（`catch Exception`） |
| 8 | finally 中的 return | 有 |
| 9 | 浮点数精度 | 有（`double` 同样问题） |
| 10 | 链式赋值与可变对象 | 无 |
| 11 | with 多资源异常顺序 | 有（try-with-resources） |
| 12 | 线程安全陷阱 | 有（非线程安全集合） |
| 13 | 全局变量陷阱 | 有（可变静态字段） |
| 14 | `__eq__` 和 `__hash__` 一致性 | 有（`equals` / `hashCode`） |
| 15 | 遍历时修改集合 | 有（`ConcurrentModificationException`） |
| 16 | 整数缓存与小整数池 | 有（`Integer Cache`，范围不同） |

> [所有陷阱完整代码](../code/practice/03_pitfalls.py)

---

## 1. 可变默认参数（经典陷阱）

Python 默认参数在**函数定义时求值一次**，不是每次调用新建。

> [可变默认参数](../code/practice/03_pitfalls.py#L32-L72)

```python
{{#include ../code/practice/03_pitfalls.py:32:72}}
```

**错误：** `def add(item, lst=[])` — 所有调用共享同一个 `lst`，`add(1)` 后 `add(2)` 得到 `[1, 2]` 而非 `[2]`。
**正确：** `def add(item, lst=None)` + 函数体内 `if lst is None: lst = []`。

**Java 对比**：Java 无此问题，每次调用新建对象。Python 仅**可变对象**有此陷阱，`int`/`str`/`tuple` 不受影响。

## 2. 闭包延迟绑定

闭包捕获**变量**而非**值**，循环中创建的闭包最终都引用循环结束后的值。

> [闭包延迟绑定](../code/practice/03_pitfalls.py#L74-L108)

```python
{{#include ../code/practice/03_pitfalls.py:74:108}}
```

**错误：** `funcs.append(lambda: i)` — 所有 lambda 返回 `2`（循环结束后的值）。
**正确：** `funcs.append(lambda i=i: i)` — 用默认参数绑定当前值。

**Java 对比**：Java lambda 要求捕获变量为 effectively final，编译期就避免了此陷阱。但用字段时同样延迟绑定。

## 3. `==` vs `is`（与 Java 正好相反）

> [`==` vs `is`](../code/practice/03_pitfalls.py#L110-L126)

```python
{{#include ../code/practice/03_pitfalls.py:110:126}}
```

| Python | 含义 | Java 对应 |
|--------|------|-----------|
| `==` | 值相等（`__eq__`） | `.equals()` |
| `is` | 同一对象（身份） | `==` |

**错误：** 用 `is` 比较值。`257 is 257` 可能为 `False`（超出小整数缓存 -5~256）。
**正确：** 比较值用 `==`，`is` 仅用于 `None` / 单例 / sentinel。

> ⚠️ Python 缓存 -5~256 的小整数，`is` 在此范围碰巧"正确"，超出就出错。Java 也有 `Integer Cache`（-128~127），但 Java 用 `==` 比较包装类本身就是 bug。

## 4. 浅拷贝 vs 深拷贝

> [浅拷贝 vs 深拷贝](../code/practice/03_pitfalls.py#L189-L213)

```python
{{#include ../code/practice/03_pitfalls.py:189:213}}
```

**错误：** `copied = original.copy()` — 浅拷贝，嵌套列表仍共享引用，修改 `copied[0]` 影响 `original`。
**正确：** `import copy; copied = copy.deepcopy(original)`。

**Java 对比**：Java `clone()` 默认浅拷贝，`ArrayList` 构造方法也是浅拷贝。Python 的 `copy.deepcopy` 是标准库通用深拷贝。

## 5. 可变对象作为类属性

> [可变类属性](../code/practice/03_pitfalls.py#L266-L309)

```python
{{#include ../code/practice/03_pitfalls.py:266:309}}
```

**错误：** `class C: items = []` — 类属性，所有实例共享同一个列表。
**正确：** 在 `__init__` 中 `self.items = []` — 实例属性，各自独立。

**Java 对比**：等价于 `static List items`，所有实例共享。Java 中也是常见陷阱。

## 6. async 中阻塞调用

> [async 阻塞调用](../code/practice/03_pitfalls.py#L311-L355)

```python
{{#include ../code/practice/03_pitfalls.py:311:355}}
```

**错误：** 协程中用 `requests.get()` / `time.sleep()` — 阻塞整个事件循环。
**正确：** 用 `aiohttp` / `asyncio.sleep()` 等异步版本。

**Java 对比**：虚拟线程中阻塞 I/O 会占用载体线程。Python 事件循环单线程，任何阻塞卡住所有协程，约束更严格。

## 7. except 捕获过宽

> [except 捕获过宽](../code/practice/03_pitfalls.py#L357-L395)

```python
{{#include ../code/practice/03_pitfalls.py:357:395}}
```

**错误：** 裸 `except:` — 捕获一切（含 `KeyboardInterrupt`），`pass` 吞掉异常，调试地狱。
**正确：** `except (ValueError, KeyError) as e:` — 精确捕获，记录日志后 `raise` 或处理。

**Java 对比**：等价于 `catch (Exception e)`。裸 `except` 更像 `catch (Throwable)`，会捕获 `SystemExit`。

## 8. finally 中的 return

> [finally return](../code/practice/03_pitfalls.py#L397-L434)

```python
{{#include ../code/practice/03_pitfalls.py:397:434}}
```

**错误：** `try: return 1; finally: return 2` — `finally` 的 `return` 覆盖 `try` 的，结果为 `2`。
**正确：** `finally` 只做清理，不要 `return`。

**Java 对比**：Java 完全相同的陷阱，`finally` 的 `return` 覆盖 `try` 的 `return`。

## 9. 浮点数精度

> [浮点数精度](../code/practice/03_pitfalls.py#L436-L470)

```python
{{#include ../code/practice/03_pitfalls.py:436:470}}
```

**错误：** `0.1 + 0.2 == 0.3` → `False`（结果为 `0.30000000000000004`）。
**正确：** 用 `Decimal('0.1') + Decimal('0.2')` 或 `math.isclose(0.1+0.2, 0.3)`。

**Java 对比**：Java `double` 完全相同，用 `BigDecimal` 对应 Python `Decimal`。

## 10. 链式赋值与可变对象

> [链式赋值](../code/practice/03_pitfalls.py#L472-L504)

```python
{{#include ../code/practice/03_pitfalls.py:472:504}}
```

**错误：** `a = b = []` — `a` 和 `b` 是同一个对象，`a.append(1)` 后 `b` 也是 `[1]`。
**正确：** `a = []; b = []` 或 `b = a.copy()`。

**Java 对比**：Java 无链式赋值语法，不存在此陷阱。

## 11. with 多资源异常顺序

> [with 多资源](../code/practice/03_pitfalls.py#L506-L538)

```python
{{#include ../code/practice/03_pitfalls.py:506:538}}
```

**错误：** `with open(a) as fa, open(b) as fb:` — 若 `open(b)` 失败，`fa` 不会被 `with` 管理（不会关闭）。
**正确：** 嵌套 `with`，或 Python 3.10+ 括号写法：
```python
with (open(a) as fa, open(b) as fb):
    ...
```

**Java 对比**：Java try-with-resources 自动处理所有资源的关闭。Python 需注意打开顺序。

## 12. 线程安全陷阱

> [线程安全](../code/practice/03_pitfalls.py#L563-L602)

```python
{{#include ../code/practice/03_pitfalls.py:563:602}}
```

**错误：** `counter += 1` 在多线程中 — 读-改-写三步，非原子，有竞态。
**正确：** 用 `threading.Lock` 保护，或用 `queue` / `multiprocessing.Value`。

**Java 对比**：Java `i++` 同样非原子，需 `AtomicInteger` / `synchronized`。Python 有 GIL，但 `+=` 仍不保证原子性。

## 13. 全局变量陷阱

> [全局变量](../code/practice/03_pitfalls.py#L643-L673)

```python
{{#include ../code/practice/03_pitfalls.py:643:673}}
```

**错误：** 函数内 `count += 1` 但 `count` 是全局变量 — `UnboundLocalError`（Python 认为是局部变量但未定义）。
**正确：** 函数内 `global count` 声明，或更好：用类封装避免全局状态。

**Java 对比**：Java 修改静态字段不需声明。Python 的 `global`/`nonlocal` 是显式声明，避免意外修改外层作用域。

## 14. `__eq__` 和 `__hash__` 一致性

> [`__eq__` 和 `__hash__`](../code/practice/03_pitfalls.py#L707-L756)

```python
{{#include ../code/practice/03_pitfalls.py:707:756}}
```

**错误：** 定义 `__eq__` 但不定义 `__hash__` — Python 自动将 `__hash__` 设为 `None`，对象不可哈希，放入 `dict`/`set` 报 `TypeError`。
**正确：** 同时定义两者，且**相等的对象必须有相同的 `__hash__`**：
```python
def __eq__(self, other):
    return isinstance(other, Person) and self.name == other.name
def __hash__(self):
    return hash(self.name)
```

**Java 对比**：`equals`/`hashCode` 契约完全相同。区别是 Java 不定义 `hashCode` 用默认值（放入 `HashMap` 出 bug），Python 更严格——定义 `__eq__` 后 `__hash__` 自动设 `None`。

## 15. 遍历时修改集合

> [遍历修改集合](../code/practice/03_pitfalls.py#L758-L800)

```python
{{#include ../code/practice/03_pitfalls.py:758:800}}
```

**错误：** `for item in items: items.remove(item)` — 遍历时修改，跳过元素，结果错误但不报错。
**正确：** 用列表推导式 `items = [x for x in items if cond]`，或遍历副本 `for item in items[:]`。

**Java 对比**：Java 遍历时修改抛 `ConcurrentModificationException`（fail-fast）。Python 不抛异常但行为未定义——更危险，不报错但结果错。

## 16. 整数缓存与小整数池

> [整数缓存](../code/practice/03_pitfalls.py#L129-L149)

```python
{{#include ../code/practice/03_pitfalls.py:129:149}}
```

**陷阱：** `256 is 256` → `True`（缓存内），`257 is 257` → 可能 `False`（缓存外）。
**正确做法：** 永远用 `==` 比较值，`is` 只用于 `None` / 单例 / sentinel。

**Java 对比**：Java `Integer Cache` 范围 -128~127（可配置），Python 是 -5~256。都是实现优化，不应依赖。

---

## 小结

| 陷阱 | 一句话原则 |
|------|-----------|
| 可变默认参数 | 用 `None` 哨兵，函数体内初始化 |
| 闭包延迟绑定 | 默认参数 `lambda x=x: x` 绑定当前值 |
| `==` vs `is` | `==` 比较值，`is` 比较身份 |
| 浅拷贝 | 嵌套结构用 `copy.deepcopy` |
| 类属性 | 可变对象放 `__init__` 做实例属性 |
| async 阻塞 | 用 `await` 版库，不调阻塞 API |
| except 过宽 | 精确捕获，不 `pass` 吞异常 |
| finally return | `finally` 只清理，不 `return` |
| 浮点数 | 用 `Decimal` 或 `math.isclose` |
| 遍历修改 | 列表推导式或遍历副本 |

> 📁 [查看完整代码](../code/practice/03_pitfalls.py)
