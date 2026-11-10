"""
04 - 异步迭代器与异步生成器
============================
本节目标：
  1. 理解 async for：异步迭代，每次 __anext__ 可能 await
  2. 实现异步迭代器（__aiter__ / __anext__）
  3. 异步生成器：async def + yield
  4. 异步推导式：[x async for x in ...]
  5. 异步生成器的实际用途：流式处理

对应 Java 概念：
  - 异步迭代器 ≈ Reactor 的 Flux / Java 9 Flow.Subscriber
  - async for   ≈ flux.subscribe(item -> ...)
  - 异步生成器  ≈ Flux.create(sink -> ...)
"""

import asyncio
import time


# ---------------------------------------------------------------------------
# 1. 手动实现异步迭代器
# ---------------------------------------------------------------------------
class AsyncRange:
    """模拟 range，但每次取下一个值都要 await（模拟 I/O）。"""

    def __init__(self, start: int, stop: int, delay: float = 0.1):
        self.current = start
        self.stop = stop
        self.delay = delay

    def __aiter__(self):  # 注意是 __aiter__ 不是 __iter__
        return self

    async def __anext__(self):  # 注意是 __anext__ 不是 __next__
        if self.current >= self.stop:
            raise StopAsyncIteration  # 异步迭代的结束信号
        await asyncio.sleep(self.delay)  # 模拟异步获取下一个元素
        value = self.current
        self.current += 1
        return value


async def demo_async_iterator():
    print("\n=== 1. 手动实现异步迭代器 ===")
    start = time.time()
    async for num in AsyncRange(0, 5, delay=0.1):
        print(f"  收到: {num} (t={time.time()-start:.2f}s)")
    print("  迭代结束")


# ---------------------------------------------------------------------------
# 2. 异步生成器（更简洁的写法）
# ---------------------------------------------------------------------------
async def async_gen_range(start: int, stop: int, delay: float = 0.1):
    """async def + yield = 异步生成器，比手动实现 __aiter__/__anext__ 简洁。"""
    for i in range(start, stop):
        await asyncio.sleep(delay)  # 模拟异步获取
        yield i  # 注意：异步生成器里 yield 不需要 await


async def demo_async_generator():
    print("\n=== 2. 异步生成器（async def + yield）===")
    async for num in async_gen_range(0, 5, delay=0.1):
        print(f"  yield: {num}")


# ---------------------------------------------------------------------------
# 3. 异步推导式
# ---------------------------------------------------------------------------
async def demo_async_comprehension():
    print("\n=== 3. 异步推导式 ===")

    # 列表推导式
    squares = [x async for x in async_gen_range(0, 5, delay=0.05)]
    print(f"  列表推导: {squares}")

    # 集合推导式
    unique = {x % 3 async for x in async_gen_range(0, 6, delay=0.05)}
    print(f"  集合推导: {unique}")

    # 字典推导式
    mapping = {x: x * x async for x in async_gen_range(0, 4, delay=0.05)}
    print(f"  字典推导: {mapping}")

    # 异步生成器表达式（注意圆括号）
    gen = (x * 2 async for x in async_gen_range(0, 4, delay=0.05))
    async for val in gen:
        print(f"  gen expr: {val}")


# ---------------------------------------------------------------------------
# 4. 实战：流式读取（模拟分页 API）
# ---------------------------------------------------------------------------
async def fetch_page(page: int, size: int = 3) -> list[int]:
    """模拟分页接口，每页返回 size 条数据。"""
    await asyncio.sleep(0.1)  # 模拟网络
    return [page * size + i for i in range(size)]


async def stream_all_pages(size: int = 3):
    """异步生成器：逐页拉取并 yield 每条记录。"""
    page = 0
    while True:
        records = await fetch_page(page, size)
        if not records:
            return
        for record in records:
            yield record
        page += 1
        if page >= 3:  # 演示用，限制 3 页
            return


async def demo_streaming():
    print("\n=== 4. 流式处理分页数据 ===")
    total = 0
    count = 0
    async for record in stream_all_pages(size=3):
        total += record
        count += 1
        print(f"  处理记录 {record}，累计 sum={total}")
    print(f"  共处理 {count} 条，总和 {total}")


# ---------------------------------------------------------------------------
# 5. 并发消费：用 Queue + 多个消费者
# ---------------------------------------------------------------------------
async def producer(queue: asyncio.Queue, n_consumers: int):
    for i in range(5):
        await asyncio.sleep(0.05)
        await queue.put(i)
        print(f"  [生产] {i}")
    # 每个消费者发一个哨兵，让它们都能退出
    for _ in range(n_consumers):
        await queue.put(None)


async def consumer(queue: asyncio.Queue, cid: int):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        await asyncio.sleep(0.1)  # 模拟处理
        print(f"  [消费{cid}] {item}")
        queue.task_done()


async def demo_producer_consumer():
    print("\n=== 5. 异步生成器 + Queue 生产消费 ===")
    queue = asyncio.Queue(maxsize=3)
    n_consumers = 2
    # 一个生产者 + 两个消费者
    await asyncio.gather(
        producer(queue, n_consumers),
        consumer(queue, 1),
        consumer(queue, 2),
    )
    await queue.join()  # 等待所有 task_done


# ---------------------------------------------------------------------------
# 6. 异步生成器的 send / close / 抛异常（高级）
# ---------------------------------------------------------------------------
async def echo_generator():
    """可以用 asend 发送值给生成器。"""
    received = None
    while True:
        # asend 的值会作为 yield 表达式的返回值
        received = yield f"echo: {received}"


async def demo_asend():
    print("\n=== 6. 异步生成器的 asend（高级）===")
    gen = echo_generator()
    # 必须先 await gen.__anext__() 启动（或 await gen.asend(None)）
    first = await gen.__anext__()
    print(f"  启动: {first}")
    r1 = await gen.asend("hello")
    print(f"  发送 hello -> {r1}")
    r2 = await gen.asend("world")
    print(f"  发送 world -> {r2}")
    await gen.aclose()  # 关闭生成器
    print("  已关闭")


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("04 - 异步迭代器与生成器")
    print("=" * 60)

    await demo_async_iterator()
    await demo_async_generator()
    await demo_async_comprehension()
    await demo_streaming()
    await demo_producer_consumer()
    await demo_asend()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - async for 遍历异步迭代器（__aiter__ / __anext__）")
    print("  - async def + yield = 异步生成器，最常用")
    print("  - 异步推导式：[x async for x in gen]")
    print("  - 适合流式处理：分页 API、日志流、消息队列")
    print("  - asend/aclose 用于高级双向通信场景")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
