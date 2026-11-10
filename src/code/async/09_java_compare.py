"""
09 - Python async 与 Java 对比（面向 Java 开发者）
================================================
本文件用并排对照的方式，帮助 Java 开发者快速建立 Python async 的心智模型。
每个概念都给出 Java 等价代码（注释）和 Python 实现（可运行）。

涵盖：
  1. 异步任务创建
  2. 等待全部完成
  3. 任一完成
  4. 线程池执行
  5. 响应式流
  6. 超时
  7. 取消
  8. 异常处理
  9. 组合操作
"""

import asyncio
import time
import sys


# ===========================================================================
# 1. 异步任务创建
# ===========================================================================
# Java:
#   ExecutorService pool = Executors.newCachedThreadPool();
#   CompletableFuture<String> f = CompletableFuture.supplyAsync(() -> {
#       Thread.sleep(500);
#       return "result";
#   }, pool);
#   String r = f.get();
#
# Python:
async def demo_create_task():
    print("\n=== 1. 异步任务创建 ===")

    async def compute() -> str:
        await asyncio.sleep(0.5)
        return "result"

    # 方式 A：直接 await（同步等待）
    r1 = await compute()
    print(f"  直接 await: {r1}")

    # 方式 B：create_task（后台调度，类似 supplyAsync）
    task = asyncio.create_task(compute())
    # 可以做别的事...
    r2 = await task  # 类似 f.get()
    print(f"  create_task + await: {r2}")


# ===========================================================================
# 2. 等待全部完成 (allOf)
# ===========================================================================
# Java:
#   CompletableFuture<Void> all = CompletableFuture.allOf(f1, f2, f3);
#   all.join();
#
# Python:
async def demo_all_of():
    print("\n=== 2. 等待全部完成 (allOf) ===")

    async def task(n, delay):
        await asyncio.sleep(delay)
        return f"t{n}"

    start = time.time()
    # gather 等价于 allOf + 收集结果
    results = await asyncio.gather(task(1, 0.3), task(2, 0.1), task(3, 0.2))
    print(f"  gather 结果: {results} (耗时 {time.time()-start:.2f}s)")
    # 注意：gather 直接返回结果列表，比 Java 的 allOf 更方便


# ===========================================================================
# 3. 任一完成 (anyOf)
# ===========================================================================
# Java:
#   CompletableFuture<Object> any = CompletableFuture.anyOf(f1, f2, f3);
#   Object first = any.join();
#
# Python:
async def demo_any_of():
    print("\n=== 3. 任一完成 (anyOf) ===")

    async def task(n, delay):
        await asyncio.sleep(delay)
        return f"t{n}"

    start = time.time()
    # 方式 A：wait + FIRST_COMPLETED
    tasks = [asyncio.create_task(task(i, d)) for i, d in [(1, 0.3), (2, 0.1), (3, 0.2)]]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    first = done.pop().result()
    print(f"  第一个完成: {first} (耗时 {time.time()-start:.2f}s)")
    # 取消剩余任务（避免泄漏）
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    # 方式 B (3.12+)：asyncio.wait_for + gather 不太直接，
    # 或用第三方库 anyio 的 move_on_after


# ===========================================================================
# 4. 线程池执行 (supplyAsync with executor)
# ===========================================================================
# Java:
#   CompletableFuture.supplyAsync(() -> blockingCall(), executor);
#
# Python:
def blocking_call(n: int) -> int:
    import time
    time.sleep(0.3)
    return n * n


async def demo_run_in_executor():
    print("\n=== 4. 线程池执行 ===")
    loop = asyncio.get_running_loop()

    # 3.9+ 推荐：asyncio.to_thread
    start = time.time()
    r = await asyncio.to_thread(blocking_call, 5)
    print(f"  to_thread: {r} (耗时 {time.time()-start:.2f}s)")

    # 等价：loop.run_in_executor
    start = time.time()
    r = await loop.run_in_executor(None, blocking_call, 6)
    print(f"  run_in_executor: {r} (耗时 {time.time()-start:.2f}s)")


# ===========================================================================
# 5. 响应式流 (Reactor Flux)
# ===========================================================================
# Java (Reactor):
#   Flux<Integer> flux = Flux.create(sink -> {
#       for (int i = 0; i < 5; i++) {
#           sink.next(i);
#       }
#       sink.complete();
#   });
#   flux.doOnNext(i -> System.out.println(i)).subscribe();
#
# Python: 异步生成器
async def async_stream():
    for i in range(5):
        await asyncio.sleep(0.05)
        yield i


async def demo_reactive_stream():
    print("\n=== 5. 响应式流 (异步生成器) ===")
    # 等价于 flux.subscribe(item -> ...)
    async for item in async_stream():
        print(f"  收到: {item}")

    # 等价于 flux.map(x -> x*2).collectList()
    doubled = [x * 2 async for x in async_stream()]
    print(f"  map + collect: {doubled}")


# ===========================================================================
# 6. 超时 (orTimeout)
# ===========================================================================
# Java:
#   future.orTimeout(200, TimeUnit.MILLISECONDS)
#         .exceptionally(ex -> "timeout");
#
# Python:
async def demo_timeout():
    print("\n=== 6. 超时 ===")

    async def slow():
        await asyncio.sleep(1.0)
        return "done"

    # asyncio.timeout (3.11+)
    if hasattr(asyncio, "timeout"):
        try:
            async with asyncio.timeout(0.2):
                await slow()
        except asyncio.TimeoutError:
            print("  asyncio.timeout 超时!")

    # wait_for (兼容旧版)
    try:
        await asyncio.wait_for(slow(), timeout=0.2)
    except asyncio.TimeoutError:
        print("  wait_for 超时!")


# ===========================================================================
# 7. 取消 (Future.cancel)
# ===========================================================================
# Java:
#   future.cancel(true);  // 中断线程
#
# Python:
async def demo_cancel():
    print("\n=== 7. 取消 ===")

    async def long_running():
        try:
            await asyncio.sleep(10)
            return "finished"
        except asyncio.CancelledError:
            print("  被取消，清理中...")
            raise

    task = asyncio.create_task(long_running())
    await asyncio.sleep(0.1)
    task.cancel()  # 等价于 future.cancel(true)
    try:
        await task
    except asyncio.CancelledError:
        print(f"  task.cancelled() = {task.cancelled()}")


# ===========================================================================
# 8. 异常处理 (exceptionally / handle)
# ===========================================================================
# Java:
#   future.exceptionally(ex -> "fallback")
#         .thenAccept(r -> ...);
#
# Python:
async def demo_exception_handling():
    print("\n=== 8. 异常处理 ===")

    async def risky():
        await asyncio.sleep(0.1)
        raise ValueError("oops")

    # 等价于 exceptionally
    try:
        await risky()
    except ValueError as e:
        result = f"fallback ({e})"
        print(f"  exceptionally 等价: {result}")

    # 等价于 handle (正常和异常都处理)
    async def with_handle():
        try:
            return await risky()
        except ValueError as e:
            return f"handled: {e}"

    r = await with_handle()
    print(f"  handle 等价: {r}")


# ===========================================================================
# 9. 组合操作 (thenCompose / thenCombine)
# ===========================================================================
# Java:
#   f1.thenCompose(r1 -> CompletableFuture.supplyAsync(() -> r1 + "+"))
#    .thenCombine(f2, (a, b) -> a + b);
#
# Python: 直接 await 串起来（天然支持）
async def demo_compose():
    print("\n=== 9. 组合操作 ===")

    async def step1():
        await asyncio.sleep(0.1)
        return "data1"

    async def step2(prev: str):
        await asyncio.sleep(0.1)
        return f"{prev}+data2"

    async def step3():
        await asyncio.sleep(0.1)
        return "data3"

    # thenCompose：串行依赖
    r1 = await step1()
    r2 = await step2(r1)
    print(f"  thenCompose: {r2}")

    # thenCombine：并行 + 合并
    a, b = await asyncio.gather(step2("x"), step3())
    print(f"  thenCombine: {a} + {b}")


# ===========================================================================
# 10. 心智模型对照表（打印）
# ===========================================================================
def print_cheatsheet():
    print("\n=== 10. 速查表 ===")
    table = [
        ("异步任务", "CompletableFuture.supplyAsync", "asyncio.create_task"),
        ("等待全部", "CompletableFuture.allOf", "asyncio.gather"),
        ("任一完成", "CompletableFuture.anyOf", "asyncio.wait(FIRST_COMPLETED)"),
        ("线程池", "ExecutorService", "loop.run_in_executor / to_thread"),
        ("响应式流", "Reactor Flux", "异步生成器 (async def + yield)"),
        ("超时", "orTimeout()", "asyncio.timeout / wait_for"),
        ("取消", "Future.cancel(true)", "task.cancel()"),
        ("异常处理", "exceptionally/handle", "try/except"),
        ("串行组合", "thenCompose", "await 串联"),
        ("并行合并", "thenCombine", "gather + 合并"),
        ("互斥锁", "ReentrantLock", "asyncio.Lock"),
        ("信号量", "Semaphore", "asyncio.Semaphore"),
        ("事件", "CountDownLatch/Event", "asyncio.Event"),
        ("队列", "BlockingQueue", "asyncio.Queue"),
        ("结构化并发", "StructuredTaskScope(21)", "asyncio.TaskGroup(3.11)"),
    ]
    print(f"  {'场景':<12} {'Java':<32} {'Python'}")
    print(f"  {'-'*12} {'-'*32} {'-'*30}")
    for scene, j, p in table:
        print(f"  {scene:<12} {j:<32} {p}")


# ===========================================================================
async def main():
    print("=" * 60)
    print("09 - Python async 与 Java 对比")
    print("=" * 60)

    await demo_create_task()
    await demo_all_of()
    await demo_any_of()
    await demo_run_in_executor()
    await demo_reactive_stream()
    await demo_timeout()
    await demo_cancel()
    await demo_exception_handling()
    await demo_compose()
    print_cheatsheet()

    print("\n" + "=" * 60)
    print("核心心智模型差异：")
    print("  1. Java 异步基于线程/回调，Python 基于协程（单线程协作式）")
    print("  2. Python 的 await 是语法层面的，编译器保证不会忘记 await")
    print("  3. Python 没有 GIL 之外的多线程并行，但协程并发足够 I/O 场景")
    print("  4. Python 异常是抛出式，不像 Java CompletableFuture 的回调链")
    print("  5. TaskGroup 比 Java 的 StructuredTaskScope 更早成熟")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
