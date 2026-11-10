"""
01 - 协程基础：async def 与 await
================================
本节目标：
  1. 理解 async def 定义的是"协程函数"，调用它得到"协程对象"
  2. 理解 await 的作用：暂停当前协程，交还控制权给事件循环
  3. 对比同步 sleep 与异步 sleep 的本质区别
  4. 掌握执行协程的几种方式

对应 Java 概念：
  - async def  ≈ 返回 CompletableFuture<T> 的方法
  - await      ≈ CompletableFuture.get()，但不会阻塞线程，而是"挂起"协程
  - asyncio.run ≈ 启动一个 Netty EventLoop 并运行入口任务
"""

import asyncio
import time


# ---------------------------------------------------------------------------
# 1. 最简单的协程
# ---------------------------------------------------------------------------
async def say_hello(name: str) -> str:
    """async def 定义协程函数。注意：它仍是普通函数，
    只是调用它不会立即执行，而是返回一个 coroutine 对象。"""
    print(f"  [hello] 开始处理 {name}")
    await asyncio.sleep(0.5)  # await：把控制权还给事件循环，0.5s 后恢复
    print(f"  [hello] 完成处理 {name}")
    return f"Hello, {name}!"


# ---------------------------------------------------------------------------
# 2. 协程对象 vs 执行
# ---------------------------------------------------------------------------
def demo_coroutine_object():
    print("\n=== 2. 协程对象不等于执行 ===")
    coro = say_hello("world")
    print(f"  调用 async def 得到的是: {coro!r}")  # <coroutine object>
    # 必须用 await / asyncio.run / create_task 才会执行
    # 这里我们手动 close 掉，避免 RuntimeWarning
    coro.close()
    print("  (协程对象未被执行，已关闭)")


# ---------------------------------------------------------------------------
# 3. await 的"挂起"语义
# ---------------------------------------------------------------------------
async def demo_await_semantics():
    print("\n=== 3. await 会挂起当前协程 ===")
    start = time.time()

    # 串行 await：总耗时 = 0.5 + 0.5 = 1s
    await asyncio.sleep(0.5)
    await asyncio.sleep(0.5)

    print(f"  串行两次 await sleep 耗时: {time.time()-start:.2f}s")


# ---------------------------------------------------------------------------
# 4. 同步 sleep vs 异步 sleep（关键区别！）
# ---------------------------------------------------------------------------
def sync_sleep_demo():
    """time.sleep 会阻塞整个线程，事件循环也无法运行其他协程。"""
    print("\n=== 4a. 同步 time.sleep 阻塞线程 ===")
    start = time.time()
    time.sleep(0.5)
    print(f"  time.sleep(0.5) 耗时: {time.time()-start:.2f}s (阻塞了线程)")


async def async_sleep_demo():
    """asyncio.sleep 不会阻塞线程，它只是让事件循环去执行其他协程。"""
    print("\n=== 4b. 异步 asyncio.sleep 不阻塞线程 ===")
    start = time.time()
    await asyncio.sleep(0.5)
    print(f"  asyncio.sleep(0.5) 耗时: {time.time()-start:.2f}s (未阻塞线程)")


# ---------------------------------------------------------------------------
# 5. 执行协程的三种方式
# ---------------------------------------------------------------------------
async def worker(n: int) -> int:
    await asyncio.sleep(0.1)
    return n * 2


async def demo_three_ways():
    print("\n=== 5. 执行协程的三种方式 ===")

    # 方式 A：直接 await（最常见）
    r1 = await worker(1)
    print(f"  A. await 直接调用: {r1}")

    # 方式 B：create_task 调度为后台任务，稍后 await
    task = asyncio.create_task(worker(2))
    # 这里可以做别的事情...
    r2 = await task
    print(f"  B. create_task + await task: {r2}")

    # 方式 C：gather 并发执行多个（第 3 课详讲）
    r3 = await asyncio.gather(worker(3), worker(4))
    print(f"  C. gather 并发: {r3}")


# ---------------------------------------------------------------------------
# 6. awaitable 概念：协程、Task、Future 都是 awaitable
# ---------------------------------------------------------------------------
async def demo_awaitables():
    print("\n=== 6. awaitable 的三种形态 ===")

    # 协程本身
    coro = worker(10)
    print(f"  协程对象: {coro!r}")
    r1 = await coro
    print(f"  await 协程: {r1}")

    # Task
    task = asyncio.create_task(worker(11))
    print(f"  Task 对象: {task!r}")
    r2 = await task
    print(f"  await Task: {r2}")

    # Future（底层，日常很少直接用）
    fut = asyncio.get_event_loop().create_future()
    fut.set_result(42)
    r3 = await fut
    print(f"  await Future: {r3}")


# ---------------------------------------------------------------------------
# 入口：asyncio.run
# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("01 - 协程基础")
    print("=" * 60)

    demo_coroutine_object()
    await demo_await_semantics()
    sync_sleep_demo()
    await async_sleep_demo()
    await demo_three_ways()
    await demo_awaitables()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - async def 定义协程函数，调用得到协程对象（不执行）")
    print("  - await 挂起当前协程，交还控制权给事件循环")
    print("  - asyncio.sleep 非阻塞，time.sleep 阻塞整个线程")
    print("  - 执行协程：await / create_task / gather")
    print("=" * 60)


if __name__ == "__main__":
    # asyncio.run 是程序入口，它会：
    #   1. 创建一个新的事件循环
    #   2. 运行传入的协程直到完成
    #   3. 关闭事件循环
    asyncio.run(main())
