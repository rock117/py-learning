# -*- coding: utf-8 -*-
"""
05_concurrency.py - 并发与并行（非 async）
=========================================

本文件演示 Python 的并发与并行（线程、进程、线程池/进程池）。
面向有丰富 Java 经验的开发者。

Java 对比：
- Java 线程是操作系统原生线程，无 GIL 限制，CPU 密集任务可真并行。
- Python 有 GIL（全局解释器锁），同一时刻只有一个线程执行 Python 字节码。
- Python 的 multiprocessing 用多进程绕过 GIL 实现真并行。
- 注意：本文件用 sys.executable 调用 Python 子进程，兼容 Windows。
"""

import sys
import os
import time
import threading
import multiprocessing
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# ============================================================================
# 1. GIL 深入解释
# ============================================================================

def cpu_bound_task(n: int) -> int:
    """CPU 密集任务：计算素数个数。

    GIL 影响：纯 Python CPU 密集任务，多线程无法真并行。
    因为 GIL 保证同一时刻只有一个线程执行字节码。
    但 I/O 操作（文件、网络、sleep）会释放 GIL，所以 I/O 密集多线程有效。

    Java 对比：JVM 无 GIL，Java 线程可真并行执行 CPU 密集任务。
    """
    count = 0
    for i in range(2, n):
        is_prime = True
        for j in range(2, int(i ** 0.5) + 1):
            if i % j == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count


def io_bound_task(duration: float) -> float:
    """I/O 密集任务：模拟等待。"""
    time.sleep(duration)
    return duration


def demo_gil_explanation() -> None:
    """演示 GIL 对多线程的影响。"""
    print("=== GIL 解释 ===")
    print("GIL（全局解释器锁）保证同一时刻只有一个线程执行 Python 字节码。")
    print("影响：CPU 密集任务多线程无加速；I/O 密集任务多线程有效（I/O 时释放 GIL）。")
    print("Java 对比：JVM 无 GIL，线程可真并行。\n")

    # 单线程 CPU 密集
    start = time.perf_counter()
    cpu_bound_task(50000)
    single_time = time.perf_counter() - start
    print(f"单线程 CPU 任务耗时: {single_time:.3f}s")

    # 多线程 CPU 密集（受 GIL 限制，不会更快）
    start = time.perf_counter()
    threads = []
    for _ in range(4):
        t = threading.Thread(target=cpu_bound_task, args=(50000,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    multi_thread_time = time.perf_counter() - start
    print(f"4 线程 CPU 任务耗时: {multi_thread_time:.3f}s（GIL 限制，无加速）")


# ============================================================================
# 2. 3.13 free-threading（PEP 703，实验性）
# ============================================================================

def demo_free_threading() -> None:
    """说明 3.13 free-threading。

    PEP 703 在 Python 3.13 引入实验性 free-threading（无 GIL 构建）。
    需要特殊编译的 Python（--disable-gil），普通安装默认仍带 GIL。

    Java 对比：free-threading 后，Python 线程行为更接近 Java 线程。
    """
    print("\n=== 3.13 Free-Threading (PEP 703) ===")
    print(f"Python 版本: {sys.version}")
    # 检查是否是 free-threading 构建
    if hasattr(sys, "_is_gil_enabled"):
        gil_enabled = sys._is_gil_enabled()
        print(f"GIL 启用: {gil_enabled}")
    else:
        print("当前 Python 没有免费线程检测 API（标准 GIL 构建）")
    print("Free-threading 需要特殊编译的 Python 3.13+（实验性）。")


# ============================================================================
# 3. threading 基础（对比 Java Thread）
# ============================================================================

def demo_threading() -> None:
    """演示 threading 基础。

    Java 对比：
    - threading.Thread ≈ new Thread(() -> {...}).start()
    - threading.Lock ≈ synchronized / ReentrantLock
    - threading.Event ≈ CountDownLatch / wait-notify
    """
    print("\n=== threading 基础 ===")

    # 共享数据 + 锁
    counter = 0
    lock = threading.Lock()

    def increment():
        nonlocal counter
        for _ in range(100000):
            with lock:  # 相当于 Java synchronized
                counter += 1

    threads = [threading.Thread(target=increment) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"4 线程各加 100000，结果 = {counter}（加锁后正确）")

    # Event 同步
    event = threading.Event()

    def waiter(name: str):
        print(f"  {name} 等待信号...")
        event.wait()  # 阻塞直到 event.set()
        print(f"  {name} 收到信号")

    t = threading.Thread(target=waiter, args=("T1",))
    t.start()
    time.sleep(0.1)
    print("  发送信号")
    event.set()
    t.join()


# ============================================================================
# 4. multiprocessing 真并行（对比 Java 线程）
# ============================================================================

def _worker(n: int) -> int:
    """进程池 worker 函数（必须在模块顶层，Windows 要求可 pickle）。"""
    return cpu_bound_task(n)


def demo_multiprocessing() -> None:
    """演示 multiprocessing 真并行。

    multiprocessing 创建独立进程，每个进程有自己的 GIL，可真并行。
    Java 对比：Java 线程就能真并行，不需要多进程。Python 因 GIL 需要多进程。

    注意：Windows 下 multiprocessing 用 spawn 方式，worker 必须在顶层定义。
    """
    print("\n=== multiprocessing 真并行 ===")

    # 单进程
    start = time.perf_counter()
    r1 = cpu_bound_task(50000)
    r2 = cpu_bound_task(50000)
    single = time.perf_counter() - start
    print(f"单进程 2 次任务: {single:.3f}s, 结果 {r1}+{r2}")

    # 多进程
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(_worker, 50000) for _ in range(2)]
        results = [f.result() for f in futs]
    multi = time.perf_counter() - start
    print(f"2 进程并行: {multi:.3f}s, 结果 {results}")
    print(f"加速比: {single / multi:.2f}x")


# ============================================================================
# 5. concurrent.futures：ThreadPoolExecutor + ProcessPoolExecutor
# ============================================================================

def demo_executors() -> None:
    """演示 ThreadPoolExecutor 和 ProcessPoolExecutor。

    Java 对比：
    - ThreadPoolExecutor ≈ ExecutorService / ThreadPoolExecutor
    - Future ≈ CompletableFuture
    - submit() ≈ submit()
    """
    print("\n=== concurrent.futures ===")

    # ThreadPoolExecutor: 适合 I/O 密集
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(io_bound_task, 0.1) for _ in range(8)]
        results = [f.result() for f in futures]
    print(f"ThreadPool 8 个 I/O 任务: {results}")

    # map 用法
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(io_bound_task, [0.05, 0.05, 0.05]))
    print(f"ThreadPool map: {results}")

    # as_completed: 谁完成谁处理
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(io_bound_task, d): d for d in [0.3, 0.1, 0.2]}
        for f in concurrent.futures.as_completed(futures):
            d = futures[f]
            print(f"  任务 {d}s 完成，结果 {f.result()}")


# ============================================================================
# 6. 何时用什么：CPU 密集 vs I/O 密集
# ============================================================================

def demo_when_to_use() -> None:
    """说明何时用线程 vs 进程。"""
    print("\n=== 何时用什么 ===")
    print("CPU 密集（计算）：用 multiprocessing / ProcessPoolExecutor")
    print("  原因：绕过 GIL，多核真并行")
    print("I/O 密集（网络/文件/sleep）：用 threading / ThreadPoolExecutor")
    print("  原因：I/O 时释放 GIL，线程切换开销小")
    print("大量 I/O 且无阻塞库：考虑 asyncio（本文件不涉及）")
    print("Java 对比：Java 线程两种场景都适用，无 GIL 限制。")


# ============================================================================
# 7. subprocess 调用外部命令（对比 ProcessBuilder）
# ============================================================================

def demo_subprocess() -> None:
    """演示 subprocess 调用外部命令。

    Java 对比：
    - subprocess.run() ≈ ProcessBuilder.start() + waitFor()
    - subprocess.Popen ≈ Process
    注意 Windows 环境用 sys.executable 调用 Python。
    """
    print("\n=== subprocess ===")

    # run: 简单调用，等待完成
    result = subprocess.run(
        [sys.executable, "-c", "print('hello from subprocess')"],
        capture_output=True, text=True
    )
    print(f"stdout: {result.stdout.strip()}")
    print(f"returncode: {result.returncode}")

    # 获取版本
    result = subprocess.run(
        [sys.executable, "--version"],
        capture_output=True, text=True
    )
    print(f"Python 版本: {result.stdout.strip()}")

    # Popen: 更灵活，可交互
    proc = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdout.write('line1\\nline2\\n')"],
        stdout=subprocess.PIPE, text=True
    )
    stdout, _ = proc.communicate()
    print(f"Popen 输出行数: {len(stdout.strip().splitlines())}")


# ============================================================================
# 8. 实战：CPU 密集用进程池，I/O 阻塞用线程池
# ============================================================================

def demo_practical() -> None:
    """实战对比。"""
    print("\n=== 实战对比 ===")
    N = 40000

    # I/O 密集：线程池更快
    print("[I/O 密集任务]")
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(io_bound_task, [0.2] * 4))
    thread_io = time.perf_counter() - start
    print(f"  线程池: {thread_io:.3f}s")

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:
        list(pool.map(io_bound_task, [0.2] * 4))
    proc_io = time.perf_counter() - start
    print(f"  进程池: {proc_io:.3f}s（进程启动开销大）")

    # CPU 密集：进程池更快
    print("[CPU 密集任务]")
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(_worker, [N] * 4))
    thread_cpu = time.perf_counter() - start
    print(f"  线程池: {thread_cpu:.3f}s（GIL 限制）")

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:
        list(pool.map(_worker, [N] * 4))
    proc_cpu = time.perf_counter() - start
    print(f"  进程池: {proc_cpu:.3f}s（真并行）")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    # Windows 下 multiprocessing 需要 freeze_support
    multiprocessing.freeze_support()

    demo_gil_explanation()
    demo_free_threading()
    demo_threading()
    demo_multiprocessing()
    demo_executors()
    demo_when_to_use()
    demo_subprocess()
    demo_practical()
    print("\n所有并发示例运行完毕。")
