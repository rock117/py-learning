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
# 4. 阻塞调用：哪些、为什么、怎么办
# ---------------------------------------------------------------------------
# 本节回答一个实际问题：async def 里能不能调 open() / requests？
# 答案是「能调，但会卡住整个事件循环」，因为它们都是同步阻塞的。


def blocking_read(path: str) -> str:
    """同步阻塞读文件（模拟真实文件 I/O）。"""
    _ = time.sleep(0.1)          # 真实场景是磁盘 I/O 或 requests.get
    with open(path, encoding="utf-8") as f:
        return f.read()


async def demo_blocking_antipattern():
    """对比：阻塞调用 vs 异步挂起，看事件循环是否被卡住。"""
    print("\n=== 4. 阻塞调用会卡住整个事件循环 ===")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "data.txt"
        p.write_text("hello async", encoding="utf-8")

        # ① 反面：在协程里直接调阻塞函数
        async def bad_task(i: int):
            return blocking_read(str(p))       # 直接调用，卡住循环

        start = time.perf_counter()
        results = await asyncio.gather(*[bad_task(i) for i in range(5)])
        bad_cost = time.perf_counter() - start
        print(f"  ❌ 直接调阻塞函数 × 5: {bad_cost:.2f}s  "
              f"（理论并发应为 0.1s，实际串行）")

        # ② 侧面证据：阻塞期间其他协程完全无法运行
        ticks = 0

        async def heartbeat():
            nonlocal ticks
            for _ in range(50):
                await asyncio.sleep(0.01)
                ticks += 1

        async def blocking_hold():
            blocking_read(str(p))      # 阻塞 0.1s

        hb = asyncio.create_task(heartbeat())
        await blocking_hold()
        ticks_during_block = ticks
        await hb
        print(f"  → 阻塞的 0.1s 里，心跳只跑了 {ticks_during_block} 次"
              f"（若不被阻塞应约 10 次）")

        # ③ 正面：to_thread 把阻塞丢进线程池
        async def good_task(i: int):
            return await asyncio.to_thread(blocking_read, str(p))

        start = time.perf_counter()
        await asyncio.gather(*[good_task(i) for i in range(5)])
        good_cost = time.perf_counter() - start
        print(f"  ✅ asyncio.to_thread × 5: {good_cost:.2f}s  "
              f"（约 0.1s，真并发）")

        print(f"\n  提速约 {bad_cost / good_cost:.1f}x")

    print("\n  结论：async def 里【可以】调阻塞函数，但整个事件循环会停住，")
    print("        所有其他协程一起卡")


async def demo_file_io_options():
    """读文件的三种方案。"""
    print("\n=== 5. 读文件：三种方案 ===")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "demo.txt"
        p.write_text("line1\nline2\n", encoding="utf-8")

        # 方案 A：直接 open（阻塞）——小文件、低频调用才可接受
        with open(p, encoding="utf-8") as f:
            content_a = f.read()
        print(f"  A. 直接 open：{content_a.strip()!r}  <- 阻塞")

        # 方案 B：to_thread（推荐，无额外依赖）
        def _read():
            with open(p, encoding="utf-8") as f:
                return f.read()

        content_b = await asyncio.to_thread(_read)
        print(f"  B. to_thread： {content_b.strip()!r}  <- 不阻塞循环")

        # 向 to_thread 传参数
        def _read_lines(n: int):
            with open(p, encoding="utf-8") as f:
                return f.readlines()[:n]

        lines = await asyncio.to_thread(_read_lines, 1)
        print(f"  B2. 带参数：   {lines}  <- 位置参数直接跟后面")

        # 方案 C：aiofiles（需安装，真异步 I/O）
        try:
            import aiofiles
            async with aiofiles.open(p, encoding="utf-8") as f:
                content_c = await f.read()
            print(f"  C. aiofiles：  {content_c.strip()!r}  <- 专用异步库")
        except ImportError:
            print("  C. aiofiles：  [未安装] pip install aiofiles（可选方案）")

    print("\n  选择建议：")
    print("    - 绝大多数场景：asyncio.to_thread（零依赖）")
    print("    - 高频小文件读写：aiofiles（避免线程池开销）")
    print("    - 启动时读一次配置：直接用 open 即可")


async def demo_to_thread_caveats():
    """to_thread 的代价与限制。"""
    print("\n=== 6. to_thread 的代价 ===")

    loop = asyncio.get_running_loop()
    executor = getattr(loop, "_default_executor", None)
    max_workers = getattr(executor, "_max_workers", "未知")
    print(f"  默认线程池上限: {max_workers}（CPU 数 + 4）")
    print("  -> 全是阻塞调用时，并发度受线程数限制，不会无限扩展")

    # 20 个 0.1s 阻塞任务（若线程数够多，能全部并发完成）
    start = time.perf_counter()
    await asyncio.gather(*[asyncio.to_thread(time.sleep, 0.1) for _ in range(20)])
    cost = time.perf_counter() - start
    print(f"\n  20 个 0.1s 阻塞任务：{cost:.2f}s")
    if isinstance(max_workers, int):
        waves = -(-20 // max_workers)          # 向上取整的批数
        print(f"  {max_workers} 个线程需要约 {waves} 批，"
              f"理论下限约 {waves * 0.1:.1f}s")
    print("  -> 任务数远超线程数时，会按批次排队，耗时成比例增长")

    print("\n  [限制清单]")
    print("    1. 受线程数限制，不是真正的无限并发")
    print("    2. GIL 依然存在：CPU 密集任务用 to_thread 不会变快")
    print("    3. CPU 密集应用 ProcessPoolExecutor")
    print("    4. to_thread 不传递 ContextVar（需 copy_context）")
    print("    5. 线程里的异常会原样抛回协程")

    print("  [Java 对比]")
    print("    to_thread ≈ CompletableFuture.supplyAsync(fn, executor)")
    print("    同样的线程池上限、同样的异常传播方式")


# ---------------------------------------------------------------------------
# 7. 事件循环如何调度：用 call_soon 观察调度顺序
# ---------------------------------------------------------------------------
async def demo_scheduling():
    print("\n=== 7. 事件循环调度顺序 ===")
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
    print("\n=== 8. 底层 API（了解即可）===")
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
    print("\n=== 9. 每个线程一个循环 ===")
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
    await demo_blocking_antipattern()
    await demo_file_io_options()
    await demo_to_thread_caveats()
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
