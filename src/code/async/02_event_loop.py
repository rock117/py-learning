"""
02 - 事件循环 Event Loop
========================
本节目标：
  1. 理解事件循环是 asyncio 的"心脏"，负责调度协程
  2. 掌握 asyncio.run 的使用（推荐入口）
  3. 了解底层 API：get_event_loop / new_event_loop / set_event_loop
  4. 用 run_in_executor 把阻塞调用丢给线程池
  5. 理解事件循环的生命周期

对应 Java 概念：
  - Event Loop ≈ Netty 的 NioEventLoop，单线程轮询就绪事件
  - asyncio.run ≈ 启动并管理一个 EventLoopGroup(1)
  - run_in_executor ≈ CompletableFuture.supplyAsync(blockingFn, executor)
"""

import asyncio
import time
import concurrent.futures


# ---------------------------------------------------------------------------
# 1. asyncio.run —— 推荐入口
# ---------------------------------------------------------------------------
async def quick_task():
    print("  [quick_task] 运行中")
    await asyncio.sleep(0.1)
    return "done"


def demo_asyncio_run():
    print("\n=== 1. asyncio.run：推荐入口 ===")
    # asyncio.run 内部做了完整生命周期管理：
    #   - 创建新循环
    #   - 运行 main 协程
    #   - 取消未完成的任务
    #   - 关闭循环
    # 注意：asyncio.run 每次都创建新循环，不能在已有循环内调用它。
    # 这里我们在子线程中调用，模拟"程序入口"场景。
    import threading
    result_box = []

    def run_entry():
        result_box.append(asyncio.run(quick_task()))

    t = threading.Thread(target=run_entry)
    t.start()
    t.join()
    print(f"  asyncio.run 返回: {result_box[0]}")
    print("  实际项目中，asyncio.run(main()) 应在 __main__ 顶层调用，只调用一次")


# ---------------------------------------------------------------------------
# 2. 查看当前事件循环
# ---------------------------------------------------------------------------
async def demo_current_loop():
    print("\n=== 2. 获取当前事件循环 ===")
    loop = asyncio.get_running_loop()  # 3.7+，在协程内获取正在运行的循环
    print(f"  当前运行循环: {loop!r}")
    print(f"  是否运行中: {loop.is_running()}")
    print(f"  循环策略: {asyncio.get_event_loop_policy()!r}")


# ---------------------------------------------------------------------------
# 3. run_in_executor：在事件循环中跑阻塞代码
# ---------------------------------------------------------------------------
def blocking_io(seconds: float) -> str:
    """模拟一个阻塞的同步函数（如 requests.get、time.sleep）。"""
    time.sleep(seconds)
    return f"阻塞 {seconds}s 完成"


async def demo_run_in_executor():
    print("\n=== 3. run_in_executor：阻塞调用丢线程池 ===")
    loop = asyncio.get_running_loop()

    # 方式 A：用默认线程池
    start = time.time()
    result = await loop.run_in_executor(None, blocking_io, 0.3)
    print(f"  默认线程池: {result} (耗时 {time.time()-start:.2f}s)")

    # 方式 B：自定义线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        start = time.time()
        # 并发跑两个阻塞任务
        r1, r2 = await asyncio.gather(
            loop.run_in_executor(pool, blocking_io, 0.3),
            loop.run_in_executor(pool, blocking_io, 0.3),
        )
        print(f"  自定义线程池并发: {r1} | {r2} (耗时 {time.time()-start:.2f}s)")

    # 方式 C：3.9+ 推荐用 asyncio.to_thread（语法糖）
    start = time.time()
    result = await asyncio.to_thread(blocking_io, 0.3)
    print(f"  asyncio.to_thread: {result} (耗时 {time.time()-start:.2f}s)")


# ---------------------------------------------------------------------------
# 4. 事件循环如何调度：用 call_soon 观察调度顺序
# ---------------------------------------------------------------------------
async def demo_scheduling():
    print("\n=== 4. 事件循环调度顺序 ===")
    loop = asyncio.get_running_loop()

    order = []

    def sync_callback(name):
        order.append(f"sync:{name}")

    async def async_step(name):
        order.append(f"async-start:{name}")
        await asyncio.sleep(0)
        order.append(f"async-end:{name}")

    # call_soon 把同步回调加入下一轮循环
    loop.call_soon(sync_callback, "A")
    order.append("main-before-await")
    await async_step("B")
    order.append("main-after-await")
    loop.call_soon(sync_callback, "C")
    await asyncio.sleep(0)  # 让 C 执行
    print(f"  执行顺序: {order}")


# ---------------------------------------------------------------------------
# 5. 底层 API：手动管理循环（不推荐，了解即可）
# ---------------------------------------------------------------------------
def demo_low_level_api():
    print("\n=== 5. 底层 API（了解即可）===")
    # 老写法（3.10 起已不推荐）：
    #   loop = asyncio.get_event_loop()
    #   loop.run_until_complete(coro)
    #   loop.close()
    #
    # 新写法：asyncio.run 封装了上面所有步骤。
    # 这里在子线程中演示手动创建并设置循环（因为主线程已有运行中的循环）。
    import threading
    box = []

    def run_manual():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(quick_task())
            box.append(result)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    t = threading.Thread(target=run_manual)
    t.start()
    t.join()
    print(f"  手动 run_until_complete: {box[0]}")
    print("  日常开发请用 asyncio.run，无需手动管理循环")


# ---------------------------------------------------------------------------
# 6. 多个事件循环（一般不需要，了解边界情况）
# ---------------------------------------------------------------------------
def demo_multiple_loops():
    print("\n=== 6. 每个线程一个循环 ===")
    import threading

    results = []

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            r = loop.run_until_complete(quick_task())
            results.append(r)
        finally:
            loop.close()

    t = threading.Thread(target=run_in_thread)
    t.start()
    t.join()
    print(f"  子线程中运行结果: {results}")


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("02 - 事件循环 Event Loop")
    print("=" * 60)

    demo_asyncio_run()
    await demo_current_loop()
    await demo_run_in_executor()
    await demo_scheduling()
    demo_low_level_api()
    demo_multiple_loops()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - 事件循环是 asyncio 的调度核心，单线程轮询")
    print("  - 用 asyncio.run() 作为入口，自动管理循环生命周期")
    print("  - 阻塞调用用 run_in_executor / asyncio.to_thread 桥接")
    print("  - call_soon 可观察底层调度顺序")
    print("  - 底层 API 了解即可，日常用 asyncio.run")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
