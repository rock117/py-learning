"""
03 - 任务管理：create_task / gather / wait / as_completed / TaskGroup
====================================================================
本节目标：这是最常用、最重要的一节！
  1. create_task：把协程调度为后台 Task
  2. gather：并发运行多个协程，按顺序返回结果
  3. wait：等待完成，可控制完成条件
  4. as_completed：谁先完成谁先返回
  5. TaskGroup (3.11+)：结构化并发，推荐
  6. 串行 vs 并发的性能对比

对应 Java 概念：
  - create_task ≈ CompletableFuture.supplyAsync
  - gather      ≈ CompletableFuture.allOf().thenApply(取所有结果)
  - wait(FIRST_COMPLETED) ≈ CompletableFuture.anyOf
  - TaskGroup    ≈ 结构化并发（Java 21 的 StructuredTaskScope）
"""

import asyncio
import time


async def fetch(url: str, delay: float = 0.5) -> str:
    """模拟异步 HTTP 请求。"""
    await asyncio.sleep(delay)
    return f"<response from {url}>"


# ---------------------------------------------------------------------------
# 1. create_task：后台调度
# ---------------------------------------------------------------------------
async def demo_create_task():
    print("\n=== 1. create_task：后台调度 ===")
    start = time.time()

    # ❌ 串行：先等 task1 再创建 task2，总耗时 1s
    # r1 = await fetch("a", 0.5)
    # r2 = await fetch("b", 0.5)

    # ✅ 并发：create_task 立即调度，不等它完成
    task1 = asyncio.create_task(fetch("a", 0.5))
    task2 = asyncio.create_task(fetch("b", 0.5))

    # 此时两个任务都在后台跑，主协程可以做别的事
    print(f"  两个任务已创建，主协程继续 (t={time.time()-start:.2f}s)")
    await asyncio.sleep(0.1)  # 模拟做别的事

    # 等待结果
    r1, r2 = await task1, await task2
    print(f"  结果: {r1} | {r2} (总耗时 {time.time()-start:.2f}s)")
    # 关键：总耗时 ≈ 0.5s，而不是 1s


# ---------------------------------------------------------------------------
# 2. gather：并发 + 按顺序返回结果
# ---------------------------------------------------------------------------
async def demo_gather():
    print("\n=== 2. gather：并发并按顺序返回 ===")
    start = time.time()

    # gather 按传入顺序返回结果，即使后完成的先返回
    results = await asyncio.gather(
        fetch("slow", 0.5),
        fetch("fast", 0.1),
        fetch("mid", 0.3),
    )
    print(f"  结果顺序与传入一致: {results}")
    print(f"  总耗时: {time.time()-start:.2f}s (并发，约等于最慢的 0.5s)")


# ---------------------------------------------------------------------------
# 3. gather 异常处理
# ---------------------------------------------------------------------------
async def fetch_with_error(url: str, delay: float) -> str:
    await asyncio.sleep(delay)
    if url == "bad":
        raise ValueError(f"请求 {url} 失败")
    return f"<response from {url}>"


async def demo_gather_exceptions():
    print("\n=== 3. gather 的异常处理 ===")

    # 默认：任一协程抛异常，gather 立即抛出（其他任务继续跑）
    try:
        await asyncio.gather(
            fetch_with_error("good", 0.1),
            fetch_with_error("bad", 0.2),
            fetch_with_error("good2", 0.3),
        )
    except ValueError as e:
        print(f"  默认模式：gather 抛出 {e}")

    # return_exceptions=True：异常作为结果返回，不抛出
    results = await asyncio.gather(
        fetch_with_error("good", 0.1),
        fetch_with_error("bad", 0.2),
        fetch_with_error("good2", 0.3),
        return_exceptions=True,
    )
    print(f"  return_exceptions=True: {results}")
    # 注意：good2 的任务在 bad 抛异常时仍在跑，结果会包含它


# ---------------------------------------------------------------------------
# 4. wait：更灵活的等待控制
# ---------------------------------------------------------------------------
async def demo_wait():
    print("\n=== 4. wait：灵活等待控制 ===")
    start = time.time()

    tasks = [
        asyncio.create_task(fetch("a", 0.5)),
        asyncio.create_task(fetch("b", 0.1)),
        asyncio.create_task(fetch("c", 0.3)),
    ]

    # FIRST_COMPLETED：任一完成就返回
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print(f"  FIRST_COMPLETED: 第一个完成={done.pop().result()!r}")
    print(f"  仍在运行的任务数: {len(pending)} (t={time.time()-start:.2f}s)")

    # 继续等待剩余
    done2, pending2 = await asyncio.wait(pending)
    print(f"  全部完成: {[t.result() for t in done2 | done]}")

    # 还有 FIRST_COMPLETED / ALL_COMPLETED（默认）
    # 注意：wait 返回 (done, pending) 两个集合，不直接返回结果


# ---------------------------------------------------------------------------
# 5. as_completed：谁先完成谁先 yield
# ---------------------------------------------------------------------------
async def demo_as_completed():
    print("\n=== 5. as_completed：按完成顺序迭代 ===")
    start = time.time()

    coros = [
        fetch("slow", 0.5),
        fetch("fast", 0.1),
        fetch("mid", 0.3),
    ]

    # as_completed 返回一个迭代器，每 next() 得到最早完成的 Future
    for future in asyncio.as_completed(coros):
        result = await future
        print(f"  完成: {result} (t={time.time()-start:.2f}s)")
    # 输出顺序：fast(0.1) -> mid(0.3) -> slow(0.5)


# ---------------------------------------------------------------------------
# 6. TaskGroup (3.11+)：结构化并发，推荐！
# ---------------------------------------------------------------------------
async def demo_taskgroup():
    print("\n=== 6. TaskGroup：结构化并发 (3.11+) ===")
    start = time.time()

    results = {}

    async def worker(name: str, delay: float):
        await asyncio.sleep(delay)
        results[name] = f"<{name} done>"

    # TaskGroup 是上下文管理器，退出时自动等待所有任务完成
    # 任一任务抛异常，会取消其他所有任务（ExceptionGroup）
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker("a", 0.5))
            tg.create_task(worker("b", 0.1))
            tg.create_task(worker("c", 0.3))
        # 退出 with 块时所有任务已完成
    except Exception as e:
        print(f"  异常: {e!r}")

    print(f"  结果: {results} (耗时 {time.time()-start:.2f}s)")
    print("  优势：作用域明确、异常自动传播、自动取消兄弟任务")


# ---------------------------------------------------------------------------
# 7. TaskGroup 异常传播演示
# ---------------------------------------------------------------------------
async def demo_taskgroup_exception():
    print("\n=== 7. TaskGroup 异常会取消兄弟任务 ===")

    async def good(n):
        await asyncio.sleep(0.3)
        print(f"    good{n} 完成")
        return n

    async def bad():
        await asyncio.sleep(0.1)
        raise RuntimeError("故意失败")

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(good(1))
            tg.create_task(bad())
            tg.create_task(good(2))
    except BaseExceptionGroup as eg:
        # 3.11+ 用 ExceptionGroup 包装多个异常
        print(f"  捕获 ExceptionGroup: {eg.exceptions}")
        print("  注意：good1/good2 被自动取消，不会完成")


# ---------------------------------------------------------------------------
# 8. 性能对比：串行 vs gather vs TaskGroup
# ---------------------------------------------------------------------------
async def demo_performance():
    print("\n=== 8. 性能对比 ===")
    urls = [f"url{i}" for i in range(5)]

    # 串行
    start = time.time()
    for u in urls:
        await fetch(u, 0.2)
    serial_time = time.time() - start

    # gather 并发
    start = time.time()
    await asyncio.gather(*[fetch(u, 0.2) for u in urls])
    gather_time = time.time() - start

    print(f"  串行 5 个请求: {serial_time:.2f}s")
    print(f"  gather 并发 5 个: {gather_time:.2f}s")
    print(f"  加速比: {serial_time/gather_time:.1f}x")


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("03 - 任务管理")
    print("=" * 60)

    await demo_create_task()
    await demo_gather()
    await demo_gather_exceptions()
    await demo_wait()
    await demo_as_completed()
    await demo_taskgroup()
    await demo_taskgroup_exception()
    await demo_performance()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - create_task：立即调度协程为后台任务")
    print("  - gather：并发运行，按顺序返回，默认异常立即抛出")
    print("  - wait：灵活控制（FIRST_COMPLETED / ALL_COMPLETED）")
    print("  - as_completed：按完成顺序迭代")
    print("  - TaskGroup (3.11+)：结构化并发，推荐替代裸 gather")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
