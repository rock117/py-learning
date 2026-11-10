"""
06 - 同步原语：Lock / Event / Condition / Semaphore / Queue / Barrier
=====================================================================
本节目标：
  1. asyncio.Lock：互斥访问共享资源
  2. asyncio.Event：通知等待者
  3. asyncio.Condition：条件等待 + 通知
  4. asyncio.Semaphore：限制并发数
  5. asyncio.Queue：生产者-消费者
  6. asyncio.Barrier (3.11+)：齐步走

对应 Java 概念：
  - asyncio.Lock     ≈ ReentrantLock
  - asyncio.Event    ≈ CountDownLatch(1) + Object.wait/notify
  - asyncio.Condition≈ Object.wait/notify/notifyAll
  - asyncio.Semaphore≈ java.util.concurrent.Semaphore
  - asyncio.Queue    ≈ LinkedBlockingQueue
  - asyncio.Barrier  ≈ CyclicBarrier

⚠️ 重要区别：Python 的这些原语不是线程安全的！
   它们只用于协程间同步。跨线程要用 threading 的原语或 asyncio 跨循环机制。
"""

import asyncio
import time


# ---------------------------------------------------------------------------
# 1. Lock：互斥访问
# ---------------------------------------------------------------------------
async def demo_lock():
    print("\n=== 1. asyncio.Lock：互斥访问 ===")
    lock = asyncio.Lock()
    shared_counter = {"value": 0}

    async def increment(name: str, n: int):
        for _ in range(n):
            async with lock:  # 临界区
                cur = shared_counter["value"]
                await asyncio.sleep(0)  # 故意让出控制权
                shared_counter["value"] = cur + 1

    # 没有 Lock，并发自增会丢失更新；有 Lock，结果正确
    await asyncio.gather(
        increment("A", 100),
        increment("B", 100),
        increment("C", 100),
    )
    print(f"  最终计数: {shared_counter['value']} (应为 300)")


# ---------------------------------------------------------------------------
# 2. Event：通知等待者
# ---------------------------------------------------------------------------
async def demo_event():
    print("\n=== 2. asyncio.Event：通知 ===")
    event = asyncio.Event()

    async def waiter(name: str):
        print(f"  {name} 等待事件...")
        await event.wait()  # 阻塞直到 event.set()
        print(f"  {name} 收到事件，继续执行")

    async def setter():
        await asyncio.sleep(0.3)
        print("  setter 触发事件!")
        event.set()  # 唤醒所有等待者

    await asyncio.gather(waiter("w1"), waiter("w2"), setter())
    # event 是一次性广播：set 后所有 wait 立即返回
    # event.clear() 可重置


# ---------------------------------------------------------------------------
# 3. Condition：条件等待 + 通知
# ---------------------------------------------------------------------------
async def demo_condition():
    print("\n=== 3. asyncio.Condition：生产者-消费者 ===")
    condition = asyncio.Condition()
    queue: list[int] = []
    # 用 Event 通知消费者退出
    stop = asyncio.Event()

    async def consumer(name: str):
        async with condition:
            while not queue and not stop.is_set():
                print(f"  {name} 队列为空，等待...")
                await condition.wait()
            if queue:
                item = queue.pop(0)
                print(f"  {name} 消费: {item}")
            else:
                print(f"  {name} 收到停止信号，退出")

    async def producer():
        await asyncio.sleep(0.2)
        async with condition:
            queue.append(42)
            queue.append(43)
            print("  生产者放入 42, 43，通知所有消费者")
            condition.notify_all()
        await asyncio.sleep(0.1)
        async with condition:
            stop.set()
            condition.notify_all()  # 唤醒剩余等待者退出

    await asyncio.gather(consumer("c1"), consumer("c2"), producer())


# ---------------------------------------------------------------------------
# 4. Semaphore：限制并发数（最常用！）
# ---------------------------------------------------------------------------
async def demo_semaphore():
    print("\n=== 4. asyncio.Semaphore：限制并发 ===")
    sem = asyncio.Semaphore(3)  # 最多 3 个协程同时进入临界区

    async def limited_task(n: int):
        async with sem:
            print(f"  任务{n} 开始 (并发槽位已占)")
            await asyncio.sleep(0.2)
            print(f"  任务{n} 完成")

    # 10 个任务，但并发限制 3，所以是分批执行
    await asyncio.gather(*[limited_task(i) for i in range(10)])
    print("  实战用途：限制 HTTP 并发数，避免压垮下游")


# ---------------------------------------------------------------------------
# 5. Queue：生产者-消费者（带容量）
# ---------------------------------------------------------------------------
async def demo_queue():
    print("\n=== 5. asyncio.Queue：生产者-消费者 ===")
    queue = asyncio.Queue(maxsize=2)  # 容量 2
    n_consumers = 2

    async def producer(name: int):
        for i in range(3):
            await queue.put(f"item-{name}-{i}")  # 满了会阻塞
            print(f"  生产者{name} 放入 item-{name}-{i} (qsize={queue.qsize()})")

    async def consumer(name: int):
        while True:
            item = await queue.get()
            if item is None:
                queue.task_done()
                break
            print(f"  消费者{name} 取出 {item}")
            await asyncio.sleep(0.1)  # 模拟处理
            queue.task_done()

    async def coordinator():
        # 先让所有生产者跑完
        await asyncio.gather(producer(0), producer(1))
        # 再放入 n_consumers 个哨兵，让每个消费者都能退出
        for _ in range(n_consumers):
            await queue.put(None)

    # 1 个协调者 + 2 个消费者
    await asyncio.gather(coordinator(), consumer(0), consumer(1))
    await queue.join()  # 等待所有 task_done


# ---------------------------------------------------------------------------
# 6. Barrier (3.11+)：齐步走
# ---------------------------------------------------------------------------
async def demo_barrier():
    print("\n=== 6. asyncio.Barrier (3.11+)：齐步走 ===")
    if not hasattr(asyncio, "Barrier"):
        print("  当前 Python 版本不支持 asyncio.Barrier (需 3.11+)")
        return

    barrier = asyncio.Barrier(3)  # 等 3 个协程到齐

    async def runner(name: str, prep_time: float):
        print(f"  {name} 准备中 ({prep_time}s)...")
        await asyncio.sleep(prep_time)
        print(f"  {name} 到达屏障，等待其他人")
        await barrier.wait()  # 阻塞直到 3 个都到
        print(f"  {name} 起跑!")

    await asyncio.gather(
        runner("A", 0.1),
        runner("B", 0.3),
        runner("C", 0.5),
    )


# ---------------------------------------------------------------------------
# 7. 实战：用 Semaphore 限制 HTTP 并发
# ---------------------------------------------------------------------------
async def fetch_with_limit(sem: asyncio.Semaphore, url: str, delay: float):
    async with sem:
        await asyncio.sleep(delay)
        return f"<{url}>"


async def demo_realworld_semaphore():
    print("\n=== 7. 实战：限制 HTTP 并发 ===")
    sem = asyncio.Semaphore(5)  # 最多 5 个并发请求
    urls = [f"url{i}" for i in range(20)]

    start = time.time()
    results = await asyncio.gather(
        *[fetch_with_limit(sem, u, 0.1) for u in urls]
    )
    elapsed = time.time() - start
    print(f"  20 个请求，并发 5，总耗时 {elapsed:.2f}s")
    print(f"  理论: ceil(20/5) * 0.1 = 0.4s")


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("06 - 同步原语")
    print("=" * 60)

    await demo_lock()
    await demo_event()
    await demo_condition()
    await demo_semaphore()
    await demo_queue()
    await demo_barrier()
    await demo_realworld_semaphore()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - Lock：互斥（协程间，非线程间）")
    print("  - Event：一次性广播通知")
    print("  - Condition：条件等待 + 通知")
    print("  - Semaphore：限制并发数（实战最常用）")
    print("  - Queue：生产者-消费者解耦")
    print("  - Barrier (3.11+)：齐步走")
    print("  ⚠️ 这些原语只用于协程间，不是线程安全的")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
