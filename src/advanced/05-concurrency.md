# 并发与并行（非 async）

本章讲解 Python 的线程、进程与线程池/进程池。理解 **GIL** 是 Python 并发的关键——
它决定了 CPU 密集任务必须用多进程才能真并行。

## 核心概念：GIL

GIL（全局解释器锁）保证同一时刻只有一个线程执行 Python 字节码。

- **CPU 密集任务**：多线程受 GIL 限制，无法真并行
- **I/O 密集任务**：I/O 操作（文件、网络、sleep）会释放 GIL，多线程有效

> [GIL 影响演示](../code/advanced/05_concurrency.py#L30-L48)

```python
{{#include ../code/advanced/05_concurrency.py:30:48}}
```

## Java 对比

| Python | Java | 说明 |
|--------|------|------|
| GIL 限制 | JVM 无 GIL | Python 线程无法真并行 CPU 任务 |
| `threading.Thread` | `new Thread()` | 线程 |
| `threading.Lock` | `synchronized` / `ReentrantLock` | 互斥锁 |
| `threading.Event` | `CountDownLatch` / wait-notify | 信号同步 |
| `multiprocessing` | 无需（Java 线程即可） | 多进程绕过 GIL |
| `ThreadPoolExecutor` | `ExecutorService` | 线程池 |
| `ProcessPoolExecutor` | 无直接对应 | 进程池 |
| `Future` | `CompletableFuture` | 异步结果 |
| `subprocess.run` | `ProcessBuilder` | 调用外部命令 |

## GIL 深入

> [GIL 解释与对比](../code/advanced/05_concurrency.py#L30-L48)

```python
{{#include ../code/advanced/05_concurrency.py:30:48}}
```

Java 线程是操作系统原生线程，无 GIL 限制，CPU 密集任务可真并行。Python 因 GIL 需要多进程。

## 3.13 free-threading（PEP 703，实验性）

PEP 703 在 Python 3.13 引入实验性 free-threading（无 GIL 构建），需要特殊编译的 Python：

> [free-threading 说明](../code/advanced/05_concurrency.py#L87-L108)

```python
{{#include ../code/advanced/05_concurrency.py:87:108}}
```

free-threading 后，Python 线程行为更接近 Java 线程。

## threading 基础

`threading.Thread` 对应 Java `Thread`，`Lock` 对应 `synchronized`，`Event` 对应 `CountDownLatch`：

> [threading 基础：锁与 Event](../code/advanced/05_concurrency.py#L110-L156)

```python
{{#include ../code/advanced/05_concurrency.py:110:156}}
```

## multiprocessing 真并行

`multiprocessing` 创建独立进程，每个进程有自己的 GIL，可真并行。
对应 Java 线程（Java 线程就能真并行，不需要多进程）。

> [multiprocessing 真并行](../code/advanced/05_concurrency.py#L158-L160)

```python
{{#include ../code/advanced/05_concurrency.py:158:160}}
```

⚠️ Windows 下 multiprocessing 用 spawn 方式，worker 必须在模块顶层定义（可 pickle）。

## concurrent.futures：线程池与进程池

`ThreadPoolExecutor` 适合 I/O 密集，`ProcessPoolExecutor` 适合 CPU 密集：

> [Executor 演示](../code/advanced/05_concurrency.py#L194-L225)

```python
{{#include ../code/advanced/05_concurrency.py:194:225}}
```

`as_completed` 实现谁完成谁处理，对应 Java `CompletableFuture.anyOf` 的思路。

## 何时用什么

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| CPU 密集（计算） | `multiprocessing` / `ProcessPoolExecutor` | 绕过 GIL，多核真并行 |
| I/O 密集（网络/文件/sleep） | `threading` / `ThreadPoolExecutor` | I/O 时释放 GIL，切换开销小 |
| 大量 I/O 且无阻塞库 | `asyncio` | 单线程高并发（本文件不涉及） |

Java 线程两种场景都适用，无 GIL 限制。

> [何时用什么](../code/advanced/05_concurrency.py#L227-L240)

```python
{{#include ../code/advanced/05_concurrency.py:227:240}}
```

## subprocess 调用外部命令

`subprocess.run()` 对应 Java `ProcessBuilder.start()` + `waitFor()`：

> [subprocess 演示](../code/advanced/05_concurrency.py#L242-L278)

```python
{{#include ../code/advanced/05_concurrency.py:242:278}}
```

## 实战对比

I/O 密集任务线程池更快（进程启动开销大）；CPU 密集任务进程池更快（真并行）：

> [实战对比](../code/advanced/05_concurrency.py#L280-L330)

```python
{{#include ../code/advanced/05_concurrency.py:280:330}}
```

## 小结

- **GIL 是 Python 并发的核心约束**：CPU 密集多线程无加速，I/O 密集多线程有效
- CPU 密集用 `multiprocessing`/`ProcessPoolExecutor` 绕过 GIL
- I/O 密集用 `threading`/`ThreadPoolExecutor`
- `concurrent.futures` 的 `Future` 对应 Java `CompletableFuture`
- Windows 下 multiprocessing worker 必须在顶层定义（可 pickle）
- 3.13 free-threading 是未来方向，但目前仍实验性

> 📁 [查看完整代码](../code/advanced/05_concurrency.py)
