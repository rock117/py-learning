# -*- coding: utf-8 -*-
"""
03_pitfalls.py - 常见陷阱与避坑指南
====================================

本文件演示 Python 编程中的常见陷阱，展示错误写法和正确写法对比。
面向有丰富 Java 经验的开发者。

Java 对比要点：
- Python 的可变默认参数陷阱在 Java 中不存在（Java 不支持默认参数值）
- Python 的 == 和 is 与 Java 正好相反（Java == 比较引用，equals 比较值）
- Python 的浅拷贝/深拷贝与 Java clone() 类似
- Python 异步阻塞调用陷阱在 Java 中不适用（Java 用线程池）

运行方式：python 03_pitfalls.py
注意：Windows 控制台默认 GBK 编码，本文件避免在 print 中使用 emoji。
"""

import sys
import copy
import time
import math
import threading
import asyncio
import decimal


# ============================================================
# 1. 可变默认参数（经典陷阱）
# ============================================================

def demo_mutable_default_arg():
    """可变默认参数（经典陷阱）。

    错误：def f(x=[]) 每次调用共享同一个列表。
    原因：默认参数在函数定义时创建一次，不是每次调用创建。
    正确：def f(x=None): x = x or [] 或 x = x if x is not None else []

    Java 对比：Java 没有此问题，因为 Java 不支持参数默认值。
    """
    print("=== 可变默认参数陷阱 ===")

    # ---- 错误写法 ----
    def append_bad(item, lst=[]):
        """[警告] 错误：默认参数 lst 在定义时创建一次，所有调用共享。"""
        lst.append(item)
        return lst

    r1 = append_bad(1)
    r2 = append_bad(2)
    print(f"  错误 - append_bad(1) = {r1}")  # [1, 2] 而非 [1]
    print(f"  错误 - append_bad(2) = {r2}")  # [1, 2] 污染了！
    print(f"  [警告] 两次调用共享同一个列表: {append_bad.__defaults__}")

    # ---- 正确写法 ----
    def append_good(item, lst=None):
        """正确：用 None 作为哨兵，函数内创建新列表。"""
        if lst is None:
            lst = []
        lst.append(item)
        return lst

    r3 = append_good(1)
    r4 = append_good(2)
    print(f"  正确 - append_good(1) = {r3}")  # [1]
    print(f"  正确 - append_good(2) = {r4}")  # [2]
    print("[提示] 可变默认参数用 None 哨兵模式替代")


# ============================================================
# 2. 闭包延迟绑定
# ============================================================

def demo_closure_late_binding():
    """闭包延迟绑定。

    错误：lambda 循环变量捕获的是引用不是值。
    原因：闭包捕获的是变量名（引用），不是当时的值。
         循环结束时变量已变为最终值。
    正确：用默认参数绑定当前值，或用 functools.partial。

    Java 对比：Java lambda 也有类似问题，但 Java 要求变量 effectively final，
              所以不会出现这种"延迟绑定"的意外，反而更安全。
    """
    print("=== 闭包延迟绑定 ===")

    # ---- 错误写法 ----
    funcs_bad = []
    for i in range(3):
        funcs_bad.append(lambda: i)  # 捕获的是变量 i 的引用
    print(f"  错误 - {[f() for f in funcs_bad]}")  # [2, 2, 2] 而非 [0, 1, 2]

    # ---- 正确写法1：默认参数绑定当前值 ----
    funcs_good1 = []
    for i in range(3):
        funcs_good1.append(lambda x=i: x)  # 默认参数在定义时求值
    print(f"  正确 - {[f() for f in funcs_good1]}")  # [0, 1, 2]

    # ---- 正确写法2：用 functools.partial ----
    from functools import partial
    funcs_good2 = [partial(lambda x: x, i) for i in range(3)]
    print(f"  正确 - {[f() for f in funcs_good2]}")  # [0, 1, 2]
    print("[提示] 闭包捕获变量引用，用默认参数或 partial 绑定当前值")


# ============================================================
# 3. == vs is
# ============================================================

def demo_eq_vs_is():
    """== vs is。

    == 比较值，is 比较身份（内存地址）。
    Java 对比：Java 的 == 比较引用（地址），equals 比较值——正好相反！
    """
    print("=== == vs is ===")

    a = [1, 2, 3]
    b = [1, 2, 3]
    c = a

    print(f"  a = [1,2,3], b = [1,2,3], c = a")
    print(f"  a == b: {a == b}")  # True，值相等
    print(f"  a is b: {a is b}")  # False，不同对象
    print(f"  a is c: {a is c}")  # True，同一对象
    print("  Java 对比：Java 的 == 比较引用(地址)，equals 比较值，与 Python 正好相反！")


def demo_intern_integer_cache():
    """整数缓存 -5 到 256 的陷阱。

    CPython 缓存了 -5 到 256 的整数对象，这些范围内的 is 比较可能为 True。
    但这不保证跨实现一致，不应依赖此行为。
    """
    print("=== 整数缓存陷阱 ===")

    # 小整数缓存范围内
    x = 256
    y = 256
    print(f"  x=256, y=256 -> x is y: {x is y}")  # True（缓存）

    # 超出缓存范围
    a = 257
    b = 257
    print(f"  a=257, b=257 -> a is b: {a is b}")  # 可能 False

    # 但编译期常量可能仍相同
    print(f"  257 is 257: {257 is 257}")  # True（编译期优化）
    print("  [警告] 不要依赖整数缓存，用 == 比较值")


def demo_string_intern_pitfall():
    """字符串驻留导致的 == 和 is 结果相同（误导）。"""
    print("=== 字符串驻留误导 ===")

    s1 = "hello"
    s2 = "hello"
    print(f"  s1='hello', s2='hello' -> s1 is s2: {s1 is s2}")  # True
    print(f"  s1 == s2: {s1 == s2}")  # True
    print("  [警告] is 和 == 结果相同是驻留导致的巧合，不要因此混用")
    print("  正确做法：比较值永远用 ==，比较身份用 is")


def demo_none_comparison():
    """None 比较应该用 is。"""
    print("=== None 比较用 is ===")

    x = None
    # 推荐
    print(f"  x is None: {x is None}")  # True
    # 不推荐（虽然能工作，但不符合 PEP 8）
    print(f"  x == None: {x == None}")  # True

    # 为什么用 is：如果对象重载了 __eq__，== None 可能有副作用
    class Weird:
        def __eq__(self, other):
            return True  # 总是返回 True，即使是 None

    w = Weird()
    print(f"  Weird() == None: {w == None}")  # True（被 __eq__ 欺骗）
    print(f"  Weird() is None: {w is None}")  # False（is 不受 __eq__ 影响）
    print("[提示] PEP 8 规定：与 None 比较用 is / is not，不用 ==")


# ============================================================
# 4. 浅拷贝 vs 深拷贝
# ============================================================

def demo_shallow_vs_deep_copy():
    """浅拷贝 vs 深拷贝。

    copy.copy 浅拷贝：只复制第一层，嵌套对象仍共享引用。
    copy.deepcopy 深拷贝：递归复制所有层级。

    Java 对比：Java 的 clone() 默认是浅拷贝，需手动实现深拷贝。
    """
    print("=== 浅拷贝 vs 深拷贝 ===")

    original = [[1, 2], [3, 4], "hello"]

    # 浅拷贝
    shallow = copy.copy(original)
    shallow[0].append(99)  # 修改嵌套列表
    print(f"  原始: {original}")  # [[1, 2, 99], [3, 4], 'hello'] 被影响！
    print(f"  浅拷贝: {shallow}")

    # 深拷贝
    original2 = [[1, 2], [3, 4], "hello"]
    deep = copy.deepcopy(original2)
    deep[0].append(99)
    print(f"  原始2: {original2}")  # [[1, 2], [3, 4], 'hello'] 不受影响
    print(f"  深拷贝: {deep}")
    print("[提示] 浅拷贝只复制第一层，嵌套可变对象仍共享；深拷贝递归复制")


def demo_nested_list_shallow_pitfall():
    """嵌套列表浅拷贝的陷阱。"""
    print("=== 嵌套列表浅拷贝陷阱 ===")

    # 错误：用 list() 或 [:] 浅拷贝嵌套列表
    matrix = [[0] * 3] * 3  # 3 行 3 列
    matrix[0][0] = 1
    print(f"  错误 [[0]*3]*3 修改[0][0]: {matrix}")  # 所有行都被修改！

    # 正确：用列表推导式创建独立行
    matrix2 = [[0] * 3 for _ in range(3)]
    matrix2[0][0] = 1
    print(f"  正确 [[0]*3 for _] 修改[0][0]: {matrix2}")  # 只有第一行修改
    print("[提示] [[x]*n]*m 创建的是同一行的引用，用推导式创建独立行")


def demo_custom_copy():
    """自定义 __copy__ / __deepcopy__。"""
    print("=== 自定义 __copy__ / __deepcopy__ ===")

    class Matrix:
        def __init__(self, data):
            self.data = data

        def __copy__(self):
            # 浅拷贝：复制 data 列表但不复制嵌套元素
            return Matrix(self.data[:])

        def __deepcopy__(self, memo):
            # 深拷贝：递归复制
            return Matrix(copy.deepcopy(self.data, memo))

        def __repr__(self):
            return f"Matrix({self.data})"

    m1 = Matrix([[1, 2], [3, 4]])
    m2 = copy.copy(m1)
    m3 = copy.deepcopy(m1)

    m2.data[0][0] = 99
    print(f"  浅拷贝修改后 m1: {m1}")  # 受影响
    m3.data[0][0] = 0
    print(f"  深拷贝修改后 m1: {m1}")  # 不受影响
    print("[提示] 实现 __copy__/__deepcopy__ 控制拷贝行为")


# ============================================================
# 5. 可变对象作为类属性
# ============================================================

def demo_mutable_class_attribute():
    """可变对象作为类属性。

    错误：类属性用可变对象，所有实例共享。
    正确：在 __init__ 中创建实例属性。

    Java 对比：Java 的 static 字段也有类似问题，但 Python 更容易踩坑。
    """
    print("=== 可变对象作为类属性 ===")

    # ---- 错误写法 ----
    class BadCounter:
        items = []  # 类属性，所有实例共享！

        def add(self, item):
            self.items.append(item)

    c1 = BadCounter()
    c2 = BadCounter()
    c1.add("a")
    c2.add("b")
    print(f"  错误 - c1.items: {c1.items}")  # ['a', 'b'] 被共享！
    print(f"  错误 - c2.items: {c2.items}")  # ['a', 'b']

    # ---- 正确写法 ----
    class GoodCounter:
        def __init__(self):
            self.items = []  # 实例属性，每个实例独立

        def add(self, item):
            self.items.append(item)

    c3 = GoodCounter()
    c4 = GoodCounter()
    c3.add("a")
    c4.add("b")
    print(f"  正确 - c3.items: {c3.items}")  # ['a']
    print(f"  正确 - c4.items: {c4.items}")  # ['b']
    print("[提示] 可变对象放在 __init__ 中作为实例属性，不要做类属性")


# ============================================================
# 6. 异步代码中的阻塞调用
# ============================================================

def demo_async_blocking_call():
    """异步代码中的阻塞调用。

    错误：async 函数中调用 time.sleep / requests.get 等阻塞函数。
    正确：用 asyncio.sleep / aiohttp 或 asyncio.to_thread。
    阻塞调用会冻结整个事件循环。

    Java 对比：Java 用线程池，阻塞一个线程不影响其他线程。
              Python asyncio 是单线程事件循环，阻塞会冻结全部。
    """
    print("=== 异步阻塞调用陷阱 ===")

    async def bad_async():
        """[警告] 错误：time.sleep 阻塞事件循环。"""
        time.sleep(0.1)  # 阻塞！整个事件循环卡住
        return "done"

    async def good_async():
        """正确：asyncio.sleep 让出控制权。"""
        await asyncio.sleep(0.1)  # 非阻塞，允许其他协程运行
        return "done"

    async def run_with_to_thread():
        """正确：用 asyncio.to_thread 在线程中运行阻塞代码。"""
        result = await asyncio.to_thread(time.sleep, 0.05)
        return "done via thread"

    async def main_async():
        # 演示正确写法（不演示错误的，因为会卡住）
        results = await asyncio.gather(
            good_async(),
            good_async(),
            run_with_to_thread(),
        )
        return results

    results = asyncio.run(main_async())
    print(f"  asyncio.gather 结果: {results}")
    print("  [警告] async 中不要用 time.sleep/requests，用 asyncio.sleep/aiohttp")
    print("  [提示] 必须用阻塞库时，用 asyncio.to_thread 包裹")


# ============================================================
# 7. except 捕获过宽
# ============================================================

def demo_bare_except():
    """except 捕获过宽。

    错误：裸 except 或 except Exception 吞掉所有异常。
    正确：精确捕获特定异常。

    except Exception 会捕获 KeyboardInterrupt 吗？不会！
    但裸 except: 会捕获（包括 KeyboardInterrupt 和 SystemExit）。
    """
    print("=== except 捕获过宽 ===")

    # ---- 错误：裸 except 吞掉所有 ----
    def bad_handler():
        try:
            raise ValueError("业务错误")
        except:  # [警告] 吞掉所有异常，包括 KeyboardInterrupt！
            print("  [错误示例] 吞掉了所有异常")

    bad_handler()

    # ---- 正确：精确捕获 ----
    def good_handler():
        try:
            raise ValueError("业务错误")
        except ValueError as e:
            print(f"  [正确示例] 精确捕获: {e}")

    good_handler()

    # 验证 except Exception 不捕获 KeyboardInterrupt
    print(f"  except Exception 会捕获 KeyboardInterrupt 吗? 否")
    print(f"  裸 except: 会捕获 KeyboardInterrupt 吗? 是")
    print("  [提示] KeyboardInterrupt 继承自 BaseException，不是 Exception")
    print("  异常层次: BaseException -> Exception / KeyboardInterrupt / SystemExit")


# ============================================================
# 8. finally 中的 return
# ============================================================

def demo_finally_return():
    """finally 中的 return 吞掉异常。

    finally 中 return 会吞掉 try 中的异常。
    finally 中 raise 会覆盖 try 中的异常。
    """
    print("=== finally 中的 return ===")

    # finally 中 return 吞掉异常
    def swallow_exception():
        try:
            raise ValueError("原始异常")
        except ValueError:
            print("  捕获到异常")
            return "from except"
        finally:
            return "from finally"  # [警告] 吞掉了 except 的返回值！

    result = swallow_exception()
    print(f"  finally return 结果: {result}")  # from finally

    # finally 中 raise 覆盖异常
    def override_exception():
        try:
            raise ValueError("原始异常")
        finally:
            raise RuntimeError("finally 中的新异常")  # 覆盖原始异常

    try:
        override_exception()
    except RuntimeError as e:
        print(f"  finally raise 结果: {e}")  # finally 中的新异常
    print("  [警告] finally 中不要 return/raise，会吞掉或覆盖 try 中的异常")


# ============================================================
# 9. 浮点数精度
# ============================================================

def demo_float_precision():
    """浮点数精度。

    0.1 + 0.2 != 0.3 的经典问题。
    原因：IEEE 754 浮点数无法精确表示某些十进制小数。

    Java 对比：Java 也有同样的 IEEE 754 问题。
    """
    print("=== 浮点数精度 ===")

    a = 0.1
    b = 0.2
    c = 0.3

    print(f"  0.1 + 0.2 = {a + b}")  # 0.30000000000000004
    print(f"  0.1 + 0.2 == 0.3: {a + b == c}")  # False

    # 正确1：用 math.isclose
    print(f"  math.isclose(0.1+0.2, 0.3): {math.isclose(a + b, c)}")  # True

    # 正确2：用 round
    print(f"  round(0.1+0.2, 10) == 0.3: {round(a + b, 10) == c}")  # True

    # 正确3：用 decimal.Decimal 精确计算
    da = decimal.Decimal("0.1")
    db = decimal.Decimal("0.2")
    print(f"  Decimal('0.1') + Decimal('0.2') = {da + db}")  # 0.3
    print(f"  Decimal 比较等于 0.3: {da + db == decimal.Decimal('0.3')}")  # True
    print("  [提示] 金额计算用 Decimal，普通比较用 math.isclose")
    print("  Java 对比：Java 也有 IEEE 754 问题，用 BigDecimal 解决")


# ============================================================
# 10. 链式赋值与可变对象
# ============================================================

def demo_chained_assignment():
    """链式赋值与可变对象。

    a = b = [] 两个变量指向同一个列表。
    """
    print("=== 链式赋值陷阱 ===")

    # 错误：链式赋值可变对象
    a = b = []
    a.append(1)
    print(f"  a = b = []; a.append(1)")
    print(f"  a = {a}, b = {b}")  # b 也变了！
    print(f"  a is b: {a is b}")  # True

    # 正确：分别创建
    c = []
    d = []
    c.append(1)
    print(f"  c = []; d = []; c.append(1)")
    print(f"  c = {c}, d = {d}")  # d 不变
    print(f"  c is d: {c is d}")  # False

    # 字典同理
    e = f = {}
    e["key"] = "value"
    print(f"  e = f = {{}}; e['key']='value'")
    print(f"  e = {e}, f = {f}")  # f 也变了
    print("[提示] a = b = [] 共享同一对象，需要独立对象要分开赋值")


# ============================================================
# 11. with 语句多个资源的异常顺序
# ============================================================

def demo_multiple_context_managers():
    """多个 contextmanager 嵌套时 __exit__ 的调用顺序。

    __exit__ 按 LIFO（后进先出）顺序调用，类似栈的展开。
    """
    print("=== 多个 contextmanager 异常顺序 ===")

    class Resource:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            print(f"    [进入] {self.name}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            print(f"    [退出] {self.name}, 异常: {exc_type.__name__ if exc_type else '无'}")
            return False  # 不吞异常

    print("  正常情况（无异常）：")
    with Resource("A") as a, Resource("B") as b:
        print("    [执行] with 块内")

    print()
    print("  异常情况（B 中抛异常）：")
    try:
        with Resource("A") as a, Resource("B") as b:
            print("    [执行] 抛出异常前")
            raise ValueError("测试异常")
            print("    [执行] 不会到达")
    except ValueError as e:
        print(f"    [捕获] {e}")
    print("  [提示] __exit__ 按 LIFO 顺序：B 先退出，再 A 退出")


def demo_context_manager_swallow_exception():
    """异常在 __exit__ 中被吞掉的情况。"""
    print("=== __exit__ 吞掉异常 ===")

    class SwallowingResource:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            print(f"    [退出] 收到异常: {exc_type.__name__ if exc_type else '无'}")
            return True  # 返回 True 吞掉异常！

    with SwallowingResource():
        raise ValueError("这个异常会被吞掉")
    print("  [警告] __exit__ 返回 True 会吞掉 with 块内的异常")
    print("  [提示] 除非有特殊需求，__exit__ 应返回 False")


# ============================================================
# 12. 线程安全陷阱
# ============================================================

def demo_thread_safety():
    """线程安全陷阱。

    threading 中共享可变对象需要锁。
    asyncio 中协程是单线程的，但 await 点可能被打断。

    Java 对比：Java 线程安全问题更常见，因为 Java 更频繁使用多线程。
    """
    print("=== 线程安全陷阱 ===")

    # ---- 错误：无锁共享计数器 ----
    counter_bad = {"value": 0}

    def increment_bad():
        for _ in range(100000):
            counter_bad["value"] += 1  # [警告] 非原子操作！

    threads = [threading.Thread(target=increment_bad) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"  无锁 - 期望 400000, 实际: {counter_bad['value']}")  # 小于 400000

    # ---- 正确：用锁保护 ----
    counter_good = {"value": 0}
    lock = threading.Lock()

    def increment_good():
        for _ in range(100000):
            with lock:  # 加锁
                counter_good["value"] += 1

    threads = [threading.Thread(target=increment_good) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"  有锁 - 期望 400000, 实际: {counter_good['value']}")  # 400000
    print("  [提示] 共享可变对象必须加锁，用 with lock: 自动释放")


def demo_asyncio_race_condition():
    """asyncio 中 await 点可能被打断。"""
    print("=== asyncio 竞态条件 ===")

    async def unsafe_increment(counter, n):
        for _ in range(n):
            # [警告] 读-改-写之间有 await，可能被打断
            current = counter["value"]
            await asyncio.sleep(0)  # 让出控制权
            counter["value"] = current + 1

    async def safe_increment(counter, n, lock):
        for _ in range(n):
            async with lock:  # 异步锁保护
                current = counter["value"]
                await asyncio.sleep(0)
                counter["value"] = current + 1

    async def main():
        # 无锁
        c1 = {"value": 0}
        await asyncio.gather(unsafe_increment(c1, 1000), unsafe_increment(c1, 1000))
        print(f"  无锁 - 期望 2000, 实际: {c1['value']}")

        # 有锁
        c2 = {"value": 0}
        lock = asyncio.Lock()
        await asyncio.gather(safe_increment(c2, 1000, lock), safe_increment(c2, 1000, lock))
        print(f"  有锁 - 期望 2000, 实际: {c2['value']}")

    asyncio.run(main())
    print("  [提示] asyncio 虽单线程，但 await 间可被打断，竞态仍需 asyncio.Lock")


# ============================================================
# 13. 全局变量陷阱
# ============================================================

def demo_global_variable():
    """函数内修改全局变量需要 global 声明。"""
    print("=== 全局变量陷阱 ===")

    # 用列表模拟全局状态（避免真正污染模块级全局变量）
    state = {"value": 0}

    def read_state():
        # 读取外部变量无需声明
        return state["value"]

    def modify_state_bad():
        # [警告] 错误：尝试重新绑定外部变量名会创建局部变量
        # state = {"value": 99}  # 这会创建局部变量，不修改外部的 state
        pass

    def modify_state_good():
        # 正确：修改可变对象的内容（不需要 global）
        state["value"] += 1

    print(f"  读取状态: {read_state()}")
    modify_state_good()
    print(f"  修改后  : {read_state()}")

    # 真正的 global 场景演示（用模块级变量）
    print("  --- 模块级 global 演示 ---")
    print("  # 模块顶层: counter = 0")
    print("  # def inc():")
    print("  #     global counter  # 声明后才能修改")
    print("  #     counter += 1")
    print("  [提示] 修改可变对象内容无需 global；重新绑定变量名才需要 global 声明")


def demo_class_vs_instance_variable():
    """类变量 vs 实例变量的混淆。"""
    print("=== 类变量 vs 实例变量 ===")

    class Dog:
        species = "Canis lupus"  # 类变量，所有实例共享
        count = 0  # 类变量

        def __init__(self, name):
            self.name = name  # 实例变量，每个实例独立
            Dog.count += 1  # 修改类变量用类名

    d1 = Dog("Rex")
    d2 = Dog("Buddy")

    print(f"  d1.name = {d1.name}, d2.name = {d2.name}")  # 各自独立
    print(f"  d1.species = {d1.species}")  # 共享类变量
    print(f"  Dog.count = {Dog.count}")  # 2

    # 陷阱：通过实例修改类变量
    d1.species = "Canis familiaris"  # 这会创建实例属性，不影响类变量！
    print(f"  d1.species = {d1.species}")  # 实例属性
    print(f"  d2.species = {d2.species}")  # 仍是类变量
    print(f"  Dog.species = {Dog.species}")  # 类变量不变
    print("  [提示] 通过实例赋值会创建实例属性遮蔽类变量，修改类变量用 类名.变量")


# ============================================================
# 14. __eq__ 和 __hash__ 一致性
# ============================================================

def demo_eq_hash_consistency():
    """__eq__ 和 __hash__ 一致性。

    重写 __eq__ 后 __hash__ 被设为 None，对象不可哈希。
    可变对象不应可哈希。
    dict/set 依赖 __hash__ 和 __eq__。
    """
    print("=== __eq__ 和 __hash__ 一致性 ===")

    # 重写 __eq__ 但不重写 __hash__
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

        # 不定义 __hash__ -> 自动设为 None，不可哈希

    p = Point(1, 2)
    try:
        hash(p)
    except TypeError as e:
        print(f"  [警告] 重写 __eq__ 后不可哈希: {e}")

    # 正确：同时定义 __eq__ 和 __hash__
    class HashablePoint:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

        def __hash__(self):
            return hash((self.x, self.y))

    p1 = HashablePoint(1, 2)
    p2 = HashablePoint(1, 2)
    print(f"  p1 == p2: {p1 == p2}")  # True
    print(f"  hash(p1) == hash(p2): {hash(p1) == hash(p2)}")  # True
    print(f"  可放入 set: {len({p1, p2})}")  # 1（因为相等）
    print("  [提示] 重写 __eq__ 必须同时重写 __hash__，否则不可哈希")
    print("  规则：a == b 则 hash(a) == hash(b)（反之不必）")


# ============================================================
# 15. 遍历时修改集合
# ============================================================

def demo_modify_during_iteration():
    """遍历时修改集合。

    错误：遍历 list/dict 时修改大小。
    正确：遍历副本或收集修改后统一处理。
    """
    print("=== 遍历时修改集合 ===")

    # ---- 错误：遍历 list 时删除 ----
    nums = [1, 2, 3, 4, 5, 6]
    # for i in nums:
    #     if i % 2 == 0:
    #         nums.remove(i)  # [警告] 会跳过元素！

    # 正确1：遍历副本
    nums_copy = [1, 2, 3, 4, 5, 6]
    for i in nums_copy[:]:  # 遍历副本
        if i % 2 == 0:
            nums_copy.remove(i)
    print(f"  遍历副本删除偶数: {nums_copy}")  # [1, 3, 5]

    # 正确2：列表推导式创建新列表
    nums_comp = [1, 2, 3, 4, 5, 6]
    nums_comp = [x for x in nums_comp if x % 2 != 0]
    print(f"  推导式过滤偶数: {nums_comp}")  # [1, 3, 5]

    # ---- dict 遍历时修改 ----
    d = {"a": 1, "b": 2, "c": 3}
    # for k in d:
    #     if d[k] < 2:
    #         del d[k]  # [警告] RuntimeError: 字典大小改变！

    # 正确：收集要删除的键
    to_delete = [k for k, v in d.items() if v < 2]
    for k in to_delete:
        del d[k]
    print(f"  dict 删除值<2的项: {d}")  # {'b': 2, 'c': 3}
    print("  [提示] 遍历时修改集合会出错，遍历副本或收集后统一处理")


# ============================================================
# 16. 字符串格式化陷阱
# ============================================================

def demo_string_format_pitfalls():
    """字符串格式化陷阱。

    % 格式化的 %s 和 %r 区别。
    f-string 中引号嵌套问题（3.12 前后）。
    """
    print("=== 字符串格式化陷阱 ===")

    # %s vs %r
    text = "hello\nworld"
    print(f"  原始字符串: {text!r}")  # repr 形式
    print(f"  %s 格式: {'%s' % text}")  # hello（换行生效）
    print(f"  %r 格式: {'%r' % text}")  # 'hello\\nworld'（转义显示）
    print("  [提示] %s 用 str()，%r 用 repr()，调试用 %r 看原始内容")

    # f-string 引号嵌套（Python 3.12 前后）
    key = "name"
    value = "Alice"

    # Python 3.12 之前：f-string 内不能重用外层引号
    # print(f"{'name'}")  # 3.12 前报错，3.12+ 可以
    # 解决：用不同引号
    print(f"  f-string 不同引号: {f'key={key!r}'}")

    # Python 3.12+：可以重用引号
    print(f"  3.12+ 嵌套: {f'{key}={value}'}")  # 3.12+ 可用相同引号
    print("  [提示] 3.12 前 f-string 内外引号必须不同，3.12+ 可重用")

    # f-string 表达式中的反斜杠（3.12 前不允许）
    # 错误（3.12 前）：f"{'\n'.join(lines)}"
    # 正确：先计算再嵌入
    lines = ["a", "b"]
    joined = "\n".join(lines)
    print(f"  f-string 反斜杠: {f'{joined}'}")
    print("  [提示] 3.12 前 f-string 表达式内不能用反斜杠，先提取到变量")


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print("Python 常见陷阱与避坑指南 - 面向 Java 开发者")
    print("=" * 60)
    print()

    sections = [
        ("可变默认参数", [demo_mutable_default_arg]),
        ("闭包延迟绑定", [demo_closure_late_binding]),
        ("== vs is", [
            demo_eq_vs_is, demo_intern_integer_cache,
            demo_string_intern_pitfall, demo_none_comparison,
        ]),
        ("浅拷贝 vs 深拷贝", [
            demo_shallow_vs_deep_copy,
            demo_nested_list_shallow_pitfall,
            demo_custom_copy,
        ]),
        ("可变对象作为类属性", [demo_mutable_class_attribute]),
        ("异步阻塞调用", [demo_async_blocking_call]),
        ("except 捕获过宽", [demo_bare_except]),
        ("finally 中的 return", [demo_finally_return]),
        ("浮点数精度", [demo_float_precision]),
        ("链式赋值与可变对象", [demo_chained_assignment]),
        ("with 多资源异常顺序", [
            demo_multiple_context_managers,
            demo_context_manager_swallow_exception,
        ]),
        ("线程安全陷阱", [
            demo_thread_safety,
            demo_asyncio_race_condition,
        ]),
        ("全局变量陷阱", [
            demo_global_variable,
            demo_class_vs_instance_variable,
        ]),
        ("__eq__ 和 __hash__ 一致性", [demo_eq_hash_consistency]),
        ("遍历时修改集合", [demo_modify_during_iteration]),
        ("字符串格式化陷阱", [demo_string_format_pitfalls]),
    ]

    for title, funcs in sections:
        print()
        print("# " + "=" * 56)
        print(f"# {title}")
        print("# " + "=" * 56)
        for func in funcs:
            print()
            func()

    print()
    print("=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
