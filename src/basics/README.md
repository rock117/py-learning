# 语言基础补遗

本部分是**前置知识**，建议在阅读异步编程之前先过一遍。

它补的是 Python 基础语法里几个"用得极多但极少被系统讲解"的点。如果你已经能熟练写 Python，可以跳过；但只要你在下面任何一项上卡过，就值得花时间：

- 看到 `f(*args, **kwargs)` 不确定它到底在干什么
- 分不清 `@classmethod` 和 `@staticmethod`
- 写列表推导式时不确定 `if` 该放前面还是后面
- 不知道 `for...else` 的 `else` 什么时候执行
- 不清楚切片的越界行为为什么和 Java 不一样

## 章节目录

| 章节 | 主题 | 对应 Java 概念 |
|------|------|----------------|
| [01 - 星号解包](01-star-unpacking.md) | `*` / `**` 的四种用法、仅关键字参数、字面量解包 | 可变参数 `Object...`（仅覆盖其中一种） |
| [02 - 类的三种方法与 property](02-class-and-methods.md) | `@classmethod` / `@staticmethod` / `@property` | `static` 方法、getter/setter |
| [03 - 推导式与生成器表达式](03-comprehensions.md) | 四种推导式、作用域、嵌套顺序、惰性求值 | Stream 的 `map` / `filter` / `collect` |
| [04 - 迭代协议、for-else 与切片](04-iteration-protocol.md) | `__iter__` / `__next__`、`for...else`、切片协议 | `Iterable` / `Iterator`、`subList` |

## 为什么单独成章

前面的 13 章"高级特性"默认你已经掌握了这些基础，于是：

- 装饰器章大量使用 `*args, **kwargs`，却从未解释它的语义
- 生成器章假设你懂 `__iter__` / `StopIteration`
- 性能章节讨论"推导式比 for 快"，但没讲推导式本身

把这些内容集中到一处，比散落在各章顺带提一句更容易建立完整心智模型。

## 三个最值得记住的差异

**1. 星号在调用处和定义处方向相反**

```python
f(*seq)              # 调用处：把序列【展开】成多个参数
def f(*args): ...    # 定义处：把多个参数【收集】成元组
```

**2. `@classmethod` 的核心是「替代构造器」，不是「静态方法」**

```python
class Point:
    @classmethod
    def from_tuple(cls, pair):     # cls 是实际类，子类调用时自动适配
        return cls(pair[0], pair[1])
```

Java 的 `static` 方法不会这样适配子类。

**3. 切片越界不报错**

```python
s[5:100]     # 自动截断，不抛异常
s[100]       # 单索引越界才抛 IndexError
```

写分页、分段逻辑时这个差异很有用，但也会掩盖边界错误。

## 学习路径

1. **星号解包** —— 最高频，先看，能立刻读懂现有代码里的 `*args`
2. **类的三种方法** —— 写类时立刻会用上，尤其是替代构造器
3. **推导式** —— 日常数据处理的主力语法
4. **迭代协议** —— 理解生成器、异步迭代器的底层机制

> 📁 [本部分代码目录](../code/basics/)
