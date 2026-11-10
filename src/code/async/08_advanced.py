"""
08 - 高级：取消、超时、异常、子进程
==================================
本节目标：
  1. 超时控制：asyncio.timeout (3.11+) / asyncio.wait_for
  2. 取消任务：task.cancel() 与 CancelledError
  3. shield：保护任务不被取消
  4. 异常在 gather / TaskGroup 中的传播
  5. 优雅关闭：处理取消时的清理
  6. 异步子进程：create_subprocess_exec

对应 Java 概念：
  - asyncio.timeout ≈ CompletableFuture.orTimeout
  - task.cancel()    ≈ Future.cancel(true)
  - CancelledError  ≈ InterruptedException
  - shield          ≈ 不可取消的 future
  - subprocess      ≈ ProcessBuilder + 异步读取
"""

import asyncio
import time
import sys


# ---------------------------------------------------------------------------
# 1. 超时：asyncio.timeout (3.11+ 推荐)
# ---------------------------------------------------------------------------
async def slow_task(seconds: float):
    print(f"  任务开始，将运行 {seconds}s")
    try:
        await asyncio.sleep(seconds)
        return f"任务完成 ({seconds}s)"
    except asyncio.CancelledError:
        print(f"  任务被取消 (在 {seconds}s 任务中)")
        raise  # 取消异常应当传播


async def demo_timeout():
    print("\n=== 1. asyncio.timeout (3.11+) ===")
    if not hasattr(asyncio, "timeout"):
        print("  当前版本不支持 asyncio.timeout，用 wait_for 替代")
        return

    # 正常完成
    try:
        async with asyncio.timeout(1.0):
            result = await slow_task(0.3)
        print(f"  结果: {result}")
    except asyncio.TimeoutError:
        print("  超时!")

    # 超时
    print("  ---")
    try:
        async with asyncio.timeout(0.2):
            result = await slow_task(1.0)
        print(f"  结果: {result}")
    except asyncio.TimeoutError:
        print("  捕获超时!")


# ---------------------------------------------------------------------------
# 2. wait_for（兼容旧版本）
# ---------------------------------------------------------------------------
async def demo_wait_for():
    print("\n=== 2. asyncio.wait_for（兼容 3.8+）===")
    try:
        # 等待 slow_task，最多 0.2s
        result = await asyncio.wait_for(slow_task(1.0), timeout=0.2)
        print(f"  结果: {result}")
    except asyncio.TimeoutError:
        print("  wait_for 超时!")
    # wait_for 超时会自动取消被等待的协程


# ---------------------------------------------------------------------------
# 3. 手动取消任务
# ---------------------------------------------------------------------------
async def demo_manual_cancel():
    print("\n=== 3. 手动取消任务 ===")
    task = asyncio.create_task(slow_task(2.0))
    await asyncio.sleep(0.1)
    print("  主动取消任务...")
    task.cancel()  # 请求取消

    try:
        await task
    except asyncio.CancelledError:
        print("  等待被取消的任务，捕获 CancelledError")

    print(f"  task.cancelled() = {task.cancelled()}")


# ---------------------------------------------------------------------------
# 4. 优雅处理取消：清理资源
# ---------------------------------------------------------------------------
async def demo_graceful_cancel():
    print("\n=== 4. 优雅处理取消（清理资源）===")

    async def task_with_cleanup():
        print("  申请资源")
        try:
            await asyncio.sleep(10)
            print("  正常完成（不会执行到这里）")
        except asyncio.CancelledError:
            print("  收到取消信号，清理资源中...")
            await asyncio.sleep(0.05)  # 模拟清理
            print("  资源已释放")
            raise  # 重新抛出，让调用者知道被取消了

    task = asyncio.create_task(task_with_cleanup())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("  外层捕获取消")


# ---------------------------------------------------------------------------
# 5. shield：保护任务不被取消
# ---------------------------------------------------------------------------
async def demo_shield():
    print("\n=== 5. asyncio.shield：保护任务 ===")

    async def important_task():
        print("  重要任务开始")
        await asyncio.sleep(0.3)
        print("  重要任务完成")
        return "important-result"

    task = asyncio.create_task(important_task())
    await asyncio.sleep(0.05)

    # shield 保护：即使外层取消，被保护的任务仍会继续
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=0.1)
    except asyncio.TimeoutError:
        print("  外层超时，但被 shield 的任务仍在跑")
        # 等它真正完成
        result = await task
        print(f"  最终拿到结果: {result}")


# ---------------------------------------------------------------------------
# 6. gather 中的异常传播
# ---------------------------------------------------------------------------
async def demo_gather_exception():
    print("\n=== 6. gather 异常传播 ===")

    async def good(n):
        await asyncio.sleep(0.1)
        return n

    async def bad():
        await asyncio.sleep(0.2)
        raise ValueError("bad task failed")

    # 默认：任一异常立即抛出，其他任务继续在后台跑
    try:
        await asyncio.gather(good(1), bad(), good(2))
    except ValueError as e:
        print(f"  默认模式抛出: {e}")

    # return_exceptions=True：异常作为结果
    results = await asyncio.gather(
        good(1), bad(), good(2), return_exceptions=True
    )
    print(f"  return_exceptions=True: {results}")
    # 可以遍历检查每个结果
    for r in results:
        if isinstance(r, Exception):
            print(f"    异常: {r}")
        else:
            print(f"    正常: {r}")


# ---------------------------------------------------------------------------
# 7. TaskGroup 的异常会取消兄弟任务
# ---------------------------------------------------------------------------
async def demo_taskgroup_cancel_siblings():
    print("\n=== 7. TaskGroup 异常取消兄弟任务 ===")

    async def good(n):
        try:
            await asyncio.sleep(0.3)
            print(f"    good{n} 完成")
            return n
        except asyncio.CancelledError:
            print(f"    good{n} 被取消")
            raise

    async def bad():
        await asyncio.sleep(0.1)
        raise RuntimeError("bad failed")

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(good(1))
            tg.create_task(bad())
            tg.create_task(good(2))
    except BaseExceptionGroup as eg:
        for e in eg.exceptions:
            print(f"  捕获: {e!r}")


# ---------------------------------------------------------------------------
# 8. 异步子进程
# ---------------------------------------------------------------------------
async def demo_subprocess():
    print("\n=== 8. 异步子进程 ===")

    # 简单：运行命令并获取输出
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c", "print('hello from subprocess')",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    print(f"  stdout: {stdout.decode().strip()}")
    print(f"  returncode: {proc.returncode}")

    # 流式读取输出
    print("  --- 流式读取 ---")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c",
        "import time\nfor i in range(3):\n    print(f'line {i}', flush=True)\n    time.sleep(0.1)",
        stdout=asyncio.subprocess.PIPE,
    )
    async for line in proc.stdout:
        print(f"  收到: {line.decode().strip()}")
    await proc.wait()


# ---------------------------------------------------------------------------
# 9. 超时 + 取消的组合实战
# ---------------------------------------------------------------------------
async def demo_timeout_with_cleanup():
    print("\n=== 9. 超时 + 清理组合 ===")

    async def fetch_with_timeout(url: str, timeout: float):
        try:
            async with asyncio.timeout(timeout):
                # 模拟请求
                await asyncio.sleep(0.5)
                return f"data from {url}"
        except asyncio.TimeoutError:
            print(f"  {url} 请求超时 ({timeout}s)")
            return None

    results = await asyncio.gather(
        fetch_with_timeout("fast.com", 1.0),    # 成功
        fetch_with_timeout("slow.com", 0.2),    # 超时
    )
    print(f"  结果: {results}")


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("08 - 高级：取消、超时、异常、子进程")
    print("=" * 60)

    await demo_timeout()
    await demo_wait_for()
    await demo_manual_cancel()
    await demo_graceful_cancel()
    await demo_shield()
    await demo_gather_exception()
    await demo_taskgroup_cancel_siblings()
    await demo_subprocess()
    await demo_timeout_with_cleanup()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - asyncio.timeout (3.11+) / wait_for：超时控制")
    print("  - task.cancel()：请求取消，抛 CancelledError")
    print("  - 优雅取消：try/except CancelledError 中清理资源")
    print("  - shield：保护任务不被外层取消")
    print("  - gather(return_exceptions=True)：异常作为结果")
    print("  - TaskGroup：异常自动取消兄弟任务")
    print("  - create_subprocess_exec：异步子进程")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
