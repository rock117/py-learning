# -*- coding: utf-8 -*-
"""
04_generators.py - 生成器与协程进阶
==================================

本文件演示 Python 生成器的高级用法。
面向有丰富 Java 经验的开发者。

Java 对比：
- Java 没有生成器，类似功能用 Stream API（惰性求值）或 Iterator 实现。
- Python 的 yield 是语言级特性，可暂停/恢复函数执行。
- 生成器是 Python 协程的基础（async/await 之前用 yield 实现协程）。
"""

import itertools
from typing import Generator, Iterator, Iterable, Any


# ============================================================================
# 1. yield from 委托子生成器
# ============================================================================

def sub_gen() -> Generator[int, None, None]:
    """子生成器，产出 1, 2, 3。"""
    yield 1
    yield 2
    yield 3


def delegating_gen() -> Generator[int, None, None]:
    """用 yield from 委托子生成器。

    yield from <iterable> 等价于：
        for item in iterable:
            yield item
    但还能透传 send/throw/close。

    Java 对比：Java 没有直接对应，需要在 Iterator 里手动遍历子迭代器。
    """
    yield 0
    yield from sub_gen()  # 委托给子生成器
    yield 4


def demo_yield_from() -> None:
    """演示 yield from。"""
    print("=== yield from ===")
    print(list(delegating_gen()))  # [0, 1, 2, 3, 4]


# ============================================================================
# 2. send / throw / close 双向通信
# ============================================================================

def echo_server() -> Generator[Any, Any, None]:
    """一个协程式生成器，接收 send 的值并回显。

    生成器不仅能产出值（yield），还能接收值（send）。
    - gen.send(value): 恢复生成器，value 成为 yield 表达式的值
    - gen.throw(exc): 在 yield 处抛出异常
    - gen.close(): 关闭生成器

    Java 对比：Java 没有直接对应，类似功能需要阻塞队列或 Channel。
    """
    print("  服务器启动")
    while True:
        try:
            # yield 产出当前值，send 的值赋给 received
            received = yield
            if received is None:
                break
            print(f"  收到: {received}, 回显: {received}")
        except ValueError as e:
            print(f"  捕获异常: {e}")
    print("  服务器关闭")


def demo_send_throw_close() -> None:
    """演示 send / throw / close。"""
    print("\n=== send / throw / close ===")
    gen = echo_server()
    next(gen)  # 启动生成器，执行到第一个 yield

    gen.send("hello")
    gen.send("world")
    gen.throw(ValueError("故意出错"))  # 3.12+ 推荐单参数签名
    gen.send("继续")
    gen.close()


# ============================================================================
# 3. 生成器管道（惰性求值链，对比 Unix 管道）
# ============================================================================

def generate_numbers(n: int) -> Generator[int, None, None]:
    """生成 0..n-1。"""
    for i in range(n):
        yield i


def filter_even(source: Iterable[int]) -> Generator[int, None, None]:
    """过滤偶数。"""
    for x in source:
        if x % 2 == 0:
            yield x


def square(source: Iterable[int]) -> Generator[int, None, None]:
    """平方。"""
    for x in source:
        yield x * x


def take(n: int, source: Iterable[int]) -> Generator[int, None, None]:
    """取前 n 个。"""
    count = 0
    for x in source:
        if count >= n:
            break
        yield x
        count += 1


def demo_pipeline() -> None:
    """演示生成器管道。

    类似 Unix 管道：cat file | grep ... | sort | head
    每个生成器处理一个元素就传给下一个，惰性求值，内存占用极低。
    """
    print("\n=== 生成器管道 ===")
    # 管道：生成 100 个数 -> 过滤偶数 -> 平方 -> 取前 5 个
    pipeline = take(5, square(filter_even(generate_numbers(100))))
    print(f"管道结果: {list(pipeline)}")

    # 也可以分步看
    print("分步演示:")
    nums = generate_numbers(10)
    evens = filter_even(nums)
    squares = square(evens)
    print(f"  逐步取值: {list(squares)}")


# ============================================================================
# 4. 基于生成器的旧协程（历史了解）
# ============================================================================

def coroutine_avg() -> Generator[float, float, float]:
    """旧式协程：计算移动平均值。

    这是 Python 3.5 之前实现协程的方式（基于 yield）。
    现在推荐用 async/await，但了解历史有助于理解生成器。

    Java 对比：Java 没有协程概念（虚拟线程除外），类似功能用回调或 CompletableFuture。
    """
    total = 0.0
    count = 0
    average = 0.0
    while True:
        value = yield average  # 产出当前平均值，接收新值
        total += value
        count += 1
        average = total / count


def demo_old_coroutine() -> None:
    """演示旧式协程。"""
    print("\n=== 旧式协程 ===")
    coro = coroutine_avg()
    next(coro)  # 启动，执行到第一个 yield

    print(f"  send(10) -> {coro.send(10)}")   # avg = 10.0
    print(f"  send(20) -> {coro.send(20)}")   # avg = 15.0
    print(f"  send(30) -> {coro.send(30)}")   # avg = 20.0
    coro.close()


# ============================================================================
# 5. itertools 与生成器结合
# ============================================================================

def demo_itertools() -> None:
    """演示 itertools 与生成器结合。

    itertools 提供高效的迭代器工具，与生成器配合非常强大。
    Java 对比：Java Stream API 有类似功能（map/filter/takeWhile 等）。
    """
    print("\n=== itertools + 生成器 ===")

    # count: 无限计数
    counter = itertools.count(10, 2)  # 从 10 开始，步长 2
    print(f"count(10,2) 前5个: {[next(counter) for _ in range(5)]}")

    # cycle: 循环
    cycler = itertools.cycle(["A", "B", "C"])
    print(f"cycle ABC 前7个: {[next(cycler) for _ in range(7)]}")

    # chain: 串联多个可迭代对象
    chained = itertools.chain([1, 2], [3, 4], [5])
    print(f"chain: {list(chained)}")

    # islice: 切片（对无限序列取前 N 个）
    infinite = (x ** 2 for x in itertools.count())
    print(f"无限平方序列前5: {list(itertools.islice(infinite, 5))}")

    # groupby: 分组
    data = [("a", 1), ("a", 2), ("b", 3), ("b", 4), ("c", 5)]
    for key, group in itertools.groupby(data, key=lambda x: x[0]):
        print(f"  分组 {key}: {list(group)}")

    # starmap: 解包后调用
    pairs = [(1, 2), (3, 4), (5, 6)]
    print(f"starmap add: {list(itertools.starmap(lambda a, b: a + b, pairs))}")


# ============================================================================
# 6. 实战：流式处理大文件
# ============================================================================

def read_lines_simulated(lines: list) -> Generator[str, None, None]:
    """模拟逐行读取大文件。

    真实场景：open("big.txt") 本身就是迭代器，逐行 yield。
    生成器避免一次性加载整个文件到内存。
    """
    for line in lines:
        yield line.strip()


def parse_log_line(line: str) -> dict:
    """解析日志行。"""
    parts = line.split(" ", 2)
    if len(parts) < 3:
        return {}
    return {"level": parts[0], "time": parts[1], "msg": parts[2]}


def filter_by_level(level: str, source: Iterable[dict]) -> Generator[dict, None, None]:
    """过滤指定级别的日志。"""
    for entry in source:
        if entry.get("level") == level:
            yield entry


def demo_stream_processing() -> None:
    """演示流式处理。"""
    print("\n=== 实战：流式处理 ===")
    # 模拟日志文件内容
    fake_lines = [
        "INFO 10:00:00 server started",
        "ERROR 10:00:01 connection failed",
        "INFO 10:00:02 retrying",
        "ERROR 10:00:03 timeout",
        "INFO 10:00:04 recovered",
    ]

    # 管道：读取 -> 解析 -> 过滤 ERROR
    lines = read_lines_simulated(fake_lines)
    parsed = (parse_log_line(l) for l in lines)  # 生成器表达式
    errors = filter_by_level("ERROR", parsed)

    print("ERROR 日志:")
    for err in errors:
        print(f"  {err}")


# ============================================================================
# 7. 实战：无限序列
# ============================================================================

def fibonacci_gen() -> Generator[int, None, None]:
    """无限斐波那契序列。

    生成器可以表达无限序列，按需取值。
    Java 对比：Java 需要自己实现 Iterator，或用 Stream.iterate。
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def primes_gen() -> Generator[int, None, None]:
    """无限素数序列。"""
    n = 2
    while True:
        if all(n % i != 0 for i in range(2, int(n ** 0.5) + 1)):
            yield n
        n += 1


def demo_infinite_sequences() -> None:
    """演示无限序列。"""
    print("\n=== 无限序列 ===")
    fib = fibonacci_gen()
    print(f"斐波那契前10: {[next(fib) for _ in range(10)]}")

    primes = primes_gen()
    print(f"素数前10: {[next(primes) for _ in range(10)]}")

    # 用 islice 安全取值
    fib2 = fibonacci_gen()
    first_20 = list(itertools.islice(fib2, 20))
    print(f"斐波那契前20: {first_20}")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_yield_from()
    demo_send_throw_close()
    demo_pipeline()
    demo_old_coroutine()
    demo_itertools()
    demo_stream_processing()
    demo_infinite_sequences()
    print("\n所有生成器示例运行完毕。")
