# 同步原语：Lock / Event / Condition / Semaphore / Queue / Barrier

asyncio 提供了一套协程间同步原语，概念上对应 Java 的 `java.util.concurrent`，
但有一个**关键区别**：它们只用于**协程间**同步，不是线程安全的。

## ⚠️ 重要提醒

Python 的 asyncio 同步原语**不是线程安全的**！
它们只在**同一个事件循环内的协程间**使用。
跨线程同步要用 `threading` 模块的原语或 asyncio 的跨循环机制。

## Java 对比总览

| Python | Java | 说明 |
|--------|------|------|
| `asyncio.Lock` | `ReentrantLock` | 互斥访问 |
| `asyncio.Event` | `CountDownLatch(1)` + `wait/notify` | 一次性广播通知 |
| `asyncio.Condition` | `Object.wait/notify/notifyAll` | 条件等待 + 通知 |
| `asyncio.Semaphore` | `java.util.concurrent.Semaphore` | 限制并发数 |
| `asyncio.Queue` | `LinkedBlockingQueue` | 生产者-消费者 |
| `asyncio.Barrier` (3.11+) | `CyclicBarrier` | 齐步走 |

## Lock：互斥访问

> [Lock 互斥访问](../code/async/06_primitives.py#L31-L54)

```python
{{#include ../code/async/06_primitives.py:31:54}}
```

`async with lock` 保护临界区。没有 Lock 时并发自增会丢失更新；
有 Lock 时结果正确（300）。

## Event：通知等待者

> [Event 通知](../code/async/06_primitives.py#L55-L76)

```python
{{#include ../code/async/06_primitives.py:55:76}}
```

- `event.wait()`：阻塞直到 `set()`
- `event.set()`：唤醒所有等待者
- `event.clear()`：重置（可复用）

Event 是一次性广播：`set` 后所有 `wait` 立即返回。

## Condition：条件等待 + 通知

> [Condition 生产者-消费者](../code/async/06_primitives.py#L77-L112)

```python
{{#include ../code/async/06_primitives.py:77:112}}
```

经典的生产者-消费者模式：
- `condition.wait()`：释放锁并等待，被通知后重新获取锁
- `condition.notify_all()`：唤醒所有等待者

对应 Java 的 `Object.wait()` / `notifyAll()`。

## Semaphore：限制并发数（最常用！）

> [Semaphore 限制并发](../code/async/06_primitives.py#L113-L130)

```python
{{#include ../code/async/06_primitives.py:113:130}}
```

`asyncio.Semaphore(n)` 限制最多 n 个协程同时进入临界区。
**实战中最常用**——限制 HTTP 并发数，避免压垮下游服务。

## Queue：生产者-消费者

> [Queue 生产者-消费者](../code/async/06_primitives.py#L131-L165)

```python
{{#include ../code/async/06_primitives.py:131:165}}
```

`asyncio.Queue(maxsize=n)` 是带容量限制的异步队列：
- `put(item)`：满了会等待
- `get()`：空了会等待
- `task_done()`：标记处理完成
- `join()`：等待所有任务处理完

对应 Java 的 `LinkedBlockingQueue`。

## Barrier (3.11+)：齐步走

> [Barrier 齐步走](../code/async/06_primitives.py#L166-L190)

```python
{{#include ../code/async/06_primitives.py:166:190}}
```

`asyncio.Barrier(n)` 等待 n 个协程都到达后再一起继续。
对应 Java 的 `CyclicBarrier`。

## 实战：限制 HTTP 并发

> [用 Semaphore 限制 HTTP 并发](../code/async/06_primitives.py#L191-L194)

```python
{{#include ../code/async/06_primitives.py:191:194}}
```

20 个请求，并发限制 5，总耗时 ≈ ceil(20/5) × 0.1 = 0.4s。
这是实际项目中最常见的 Semaphore 用法。

## 小结

- `Lock`：互斥（协程间，非线程间）
- `Event`：一次性广播通知
- `Condition`：条件等待 + 通知
- `Semaphore`：限制并发数（实战最常用）
- `Queue`：生产者-消费者解耦
- `Barrier` (3.11+)：齐步走
- ⚠️ 这些原语只用于协程间，不是线程安全的

> 📁 [查看完整代码](../code/async/06_primitives.py)
