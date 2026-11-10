"""
05 - 异步上下文管理器
=====================
本节目标：
  1. 理解 async with：进入/退出时可能 await
  2. 实现 __aenter__ / __aexit__
  3. 用 contextlib.asynccontextmanager 简化
  4. 实战：连接池、HTTP client、数据库会话

对应 Java 概念：
  - async with ≈ try-with-resources，但 close 可能异步
  - Java 的 try-with-resources 要求 AutoCloseable.close() 同步
  - Python 的 async with 允许 __aexit__ 是协程
"""

import asyncio
from contextlib import asynccontextmanager
import time


# ---------------------------------------------------------------------------
# 1. 手动实现异步上下文管理器
# ---------------------------------------------------------------------------
class AsyncDBConnection:
    """模拟异步数据库连接。"""

    def __init__(self, name: str):
        self.name = name
        self.connected = False

    async def __aenter__(self):
        print(f"  [DB] 正在连接 {self.name}...")
        await asyncio.sleep(0.2)  # 模拟异步连接
        self.connected = True
        print(f"  [DB] 已连接 {self.name}")
        return self  # 返回值赋给 as 后的变量

    async def __aexit__(self, exc_type, exc, tb):
        print(f"  [DB] 关闭连接 {self.name}...")
        await asyncio.sleep(0.1)  # 模拟异步关闭
        self.connected = False
        print(f"  [DB] 已关闭 {self.name}")
        # 返回 False/None：异常正常传播
        # 返回 True：吞掉异常（一般不要这样做）
        return False

    async def query(self, sql: str):
        if not self.connected:
            raise RuntimeError("未连接")
        await asyncio.sleep(0.1)
        return f"[{self.name}] result of: {sql}"


async def demo_manual_context_manager():
    print("\n=== 1. 手动实现异步上下文管理器 ===")
    async with AsyncDBConnection("db-1") as conn:
        result = await conn.query("SELECT 1")
        print(f"  查询结果: {result}")
    # 退出 with 块时自动调用 __aexit__，即使发生异常


# ---------------------------------------------------------------------------
# 2. 异常时自动清理
# ---------------------------------------------------------------------------
async def demo_exception_cleanup():
    print("\n=== 2. 异常时仍会调用 __aexit__ ===")
    try:
        async with AsyncDBConnection("db-2") as conn:
            await conn.query("SELECT 1")
            raise ValueError("业务逻辑出错")
    except ValueError as e:
        print(f"  捕获到异常: {e}")
    print("  (连接已被正确关闭)")


# ---------------------------------------------------------------------------
# 3. contextlib.asynccontextmanager：装饰器写法（推荐）
# ---------------------------------------------------------------------------
@asynccontextmanager
async def async_db_connection(name: str):
    """用装饰器简化：把 async def + yield 包成上下文管理器。"""
    print(f"  [DB] 连接 {name}...")
    await asyncio.sleep(0.2)
    try:
        yield {"name": name, "connected": True}  # yield 的值 = as 变量
        # yield 之后的代码 = __aexit__ 的逻辑
    finally:
        print(f"  [DB] 关闭 {name}...")
        await asyncio.sleep(0.1)


async def demo_decorator_style():
    print("\n=== 3. asynccontextmanager 装饰器写法 ===")
    async with async_db_connection("db-3") as conn:
        print(f"  使用连接: {conn}")


# ---------------------------------------------------------------------------
# 4. 实战：连接池模式
# ---------------------------------------------------------------------------
class AsyncConnectionPool:
    """简化的异步连接池。"""

    def __init__(self, size: int = 3):
        self.size = size
        self.semaphore = asyncio.Semaphore(size)
        self.in_use = 0

    @asynccontextmanager
    async def acquire(self):
        await self.semaphore.acquire()
        self.in_use += 1
        try:
            await asyncio.sleep(0.05)  # 模拟从池中取连接
            yield f"conn-{self.in_use}"
        finally:
            self.in_use -= 1
            self.semaphore.release()


async def demo_connection_pool():
    print("\n=== 4. 异步连接池 ===")
    pool = AsyncConnectionPool(size=2)

    async def task(n: int):
        async with pool.acquire() as conn:
            print(f"  任务{n} 获取 {conn}")
            await asyncio.sleep(0.2)
            print(f"  任务{n} 释放 {conn}")

    # 5 个任务，但池大小 2，所以最多 2 个并发
    await asyncio.gather(*[task(i) for i in range(5)])


# ---------------------------------------------------------------------------
# 5. 嵌套 async with
# ---------------------------------------------------------------------------
async def demo_nested():
    print("\n=== 5. 嵌套 async with ===")
    async with AsyncDBConnection("db-a") as conn_a, AsyncDBConnection("db-b") as conn_b:
        r1 = await conn_a.query("SELECT * FROM a")
        r2 = await conn_b.query("SELECT * FROM b")
        print(f"  跨库查询: {r1} + {r2}")


# ---------------------------------------------------------------------------
# 6. 模拟 HTTP Client 的会话（类似 aiohttp.ClientSession）
# ---------------------------------------------------------------------------
class FakeHTTPSession:
    """模拟 aiohttp.ClientSession 的生命周期。"""

    def __init__(self):
        self.closed = False

    async def __aenter__(self):
        print("  [HTTP] 创建会话")
        return self

    async def __aexit__(self, *exc):
        print("  [HTTP] 关闭会话")
        self.closed = True

    async def get(self, url: str) -> str:
        if self.closed:
            raise RuntimeError("会话已关闭")
        await asyncio.sleep(0.1)
        return f"200 OK from {url}"


async def demo_http_session():
    print("\n=== 6. HTTP 会话（复用连接）===")
    async with FakeHTTPSession() as session:
        # 一个会话内发多个请求，复用底层连接
        results = await asyncio.gather(
            session.get("https://api.example.com/a"),
            session.get("https://api.example.com/b"),
            session.get("https://api.example.com/c"),
        )
        for r in results:
            print(f"  {r}")


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("05 - 异步上下文管理器")
    print("=" * 60)

    await demo_manual_context_manager()
    await demo_exception_cleanup()
    await demo_decorator_style()
    await demo_connection_pool()
    await demo_nested()
    await demo_http_session()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - async with 调用 __aenter__ / __aexit__，两者都可 await")
    print("  - @asynccontextmanager + yield 是最简洁的写法")
    print("  - 适合资源管理：连接、会话、锁、文件句柄")
    print("  - 异常时 __aexit__ 仍会被调用，保证资源释放")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
