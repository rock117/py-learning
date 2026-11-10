"""
07 - 实战：HTTP 与文件 I/O
==========================
本节目标：
  1. 用 asyncio.to_thread 桥接阻塞 I/O（无需第三方库）
  2. 用 aiohttp 做异步 HTTP 请求（如已安装）
  3. 用 aiofiles 做异步文件 I/O（如已安装）
  4. 用 Semaphore 限制并发
  5. 批量请求 + 错误重试
  6. 并发下载文件

注意：本文件大部分示例不依赖第三方库，用 asyncio.to_thread 演示。
      aiohttp / aiofiles 部分会在检测到库时自动运行。

对应 Java 概念：
  - aiohttp    ≈ AsyncHttpClient / WebClient
  - aiofiles   ≈ AsynchronousFileChannel
  - to_thread  ≈ CompletableFuture.supplyAsync(blockingFn, executor)
"""

import asyncio
import time
import json
import urllib.request
import urllib.error
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. 用 asyncio.to_thread 桥接阻塞的 urllib
# ---------------------------------------------------------------------------
def blocking_fetch(url: str) -> dict:
    """同步阻塞的 HTTP 请求（urllib）。"""
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read().decode()
            return {"status": resp.status, "length": len(data)}
    except urllib.error.URLError as e:
        return {"status": -1, "error": str(e)}


async def demo_to_thread_http():
    print("\n=== 1. asyncio.to_thread 桥接阻塞 HTTP ===")
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]

    start = time.time()
    # 串行
    # for u in urls:
    #     blocking_fetch(u)  # 耗时 3s

    # 并发：把阻塞调用丢线程池
    results = await asyncio.gather(
        *[asyncio.to_thread(blocking_fetch, u) for u in urls]
    )
    print(f"  3 个延迟 1s 的请求，并发耗时: {time.time()-start:.2f}s (理论 ~1s)")
    print(f"  结果: {results}")


# ---------------------------------------------------------------------------
# 2. aiohttp（如已安装）
# ---------------------------------------------------------------------------
async def demo_aiohttp():
    print("\n=== 2. aiohttp 异步 HTTP（如已安装）===")
    try:
        import aiohttp  # type: ignore
    except ImportError:
        print("  aiohttp 未安装，跳过。安装: pip install aiohttp")
        return

    urls = ["https://httpbin.org/delay/1"] * 3
    start = time.time()

    # 推荐用法：一个 ClientSession 复用连接
    async with aiohttp.ClientSession() as session:
        async def fetch(url):
            async with session.get(url) as resp:
                return await resp.json()

        results = await asyncio.gather(*[fetch(u) for u in urls])

    print(f"  aiohttp 并发 3 个请求: {time.time()-start:.2f}s")
    print(f"  第一个结果 keys: {list(results[0].keys()) if results else None}")


# ---------------------------------------------------------------------------
# 3. 用 Semaphore 限制并发
# ---------------------------------------------------------------------------
async def fetch_with_semaphore(sem, session, url):
    async with sem:
        async with session.get(url) as resp:
            return resp.status


async def demo_concurrency_limit():
    print("\n=== 3. 限制并发数 ===")
    try:
        import aiohttp  # type: ignore
    except ImportError:
        print("  aiohttp 未安装，跳过")
        return

    sem = asyncio.Semaphore(10)  # 最多 10 个并发
    urls = ["https://httpbin.org/get"] * 50

    async with aiohttp.ClientSession() as session:
        start = time.time()
        statuses = await asyncio.gather(
            *[fetch_with_semaphore(sem, session, u) for u in urls]
        )
        print(f"  50 个请求，并发 10，耗时 {time.time()-start:.2f}s")
        print(f"  状态码集合: {set(statuses)}")


# ---------------------------------------------------------------------------
# 4. 异步文件 I/O：asyncio.to_thread
# ---------------------------------------------------------------------------
def blocking_write(path: str, content: str):
    """同步文件写入。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return len(content)


def blocking_read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def demo_file_io_to_thread():
    print("\n=== 4. 异步文件 I/O（to_thread）===")
    tmpdir = Path("async_tmp_files")
    tmpdir.mkdir(exist_ok=True)

    # 并发写 5 个文件
    start = time.time()
    files = [tmpdir / f"file{i}.txt" for i in range(5)]
    sizes = await asyncio.gather(
        *[
            asyncio.to_thread(blocking_write, str(f), f"content of {f.name}" * 1000)
            for f in files
        ]
    )
    print(f"  并发写 5 个文件: {time.time()-start:.2f}s, 大小 {sizes}")

    # 并发读
    start = time.time()
    contents = await asyncio.gather(
        *[asyncio.to_thread(blocking_read, str(f)) for f in files]
    )
    print(f"  并发读 5 个文件: {time.time()-start:.2f}s, 长度 {[len(c) for c in contents]}")

    # 清理
    for f in files:
        f.unlink()
    tmpdir.rmdir()


# ---------------------------------------------------------------------------
# 5. aiofiles（如已安装）
# ---------------------------------------------------------------------------
async def demo_aiofiles():
    print("\n=== 5. aiofiles 异步文件 I/O（如已安装）===")
    try:
        import aiofiles  # type: ignore
    except ImportError:
        print("  aiofiles 未安装，跳过。安装: pip install aiofiles")
        return

    tmpdir = Path("async_tmp_files2")
    tmpdir.mkdir(exist_ok=True)
    path = tmpdir / "test.txt"

    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write("hello aiofiles\n")
        await f.write("second line\n")

    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()
    print(f"  aiofiles 写入并读取: {content!r}")

    path.unlink()
    tmpdir.rmdir()


# ---------------------------------------------------------------------------
# 6. 错误重试模式
# ---------------------------------------------------------------------------
async def fetch_with_retry(url: str, max_retries: int = 3, delay: float = 0.1):
    """带重试的异步请求（用 to_thread 演示）。"""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            result = await asyncio.to_thread(blocking_fetch, url)
            if result.get("status", -1) > 0:
                return result
            raise RuntimeError(result.get("error", "unknown"))
        except Exception as e:
            last_error = e
            print(f"  第 {attempt} 次失败: {e}")
            if attempt < max_retries:
                await asyncio.sleep(delay * attempt)  # 指数退避
    raise last_error


async def demo_retry():
    print("\n=== 6. 错误重试 ===")
    try:
        result = await fetch_with_retry("https://this-domain-does-not-exist-xxx.com")
        print(f"  成功: {result}")
    except Exception as e:
        print(f"  最终失败: {e}")


# ---------------------------------------------------------------------------
# 7. 并发下载（模拟）
# ---------------------------------------------------------------------------
async def download_file(url: str, save_path: str, sem: asyncio.Semaphore):
    async with sem:
        print(f"  开始下载 {url}")
        # 模拟下载：用 to_thread 写入随机内容
        await asyncio.sleep(0.3)
        await asyncio.to_thread(blocking_write, save_path, f"data from {url}")
        print(f"  完成下载 {url} -> {save_path}")


async def demo_batch_download():
    print("\n=== 7. 并发下载 ===")
    tmpdir = Path("async_dl_tmp")
    tmpdir.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(3)

    urls = [f"https://example.com/file{i}" for i in range(6)]
    paths = [str(tmpdir / f"file{i}.bin") for i in range(6)]

    start = time.time()
    await asyncio.gather(
        *[download_file(u, p, sem) for u, p in zip(urls, paths)]
    )
    print(f"  6 个文件，并发 3，耗时 {time.time()-start:.2f}s")

    # 清理
    for p in paths:
        Path(p).unlink(missing_ok=True)
    tmpdir.rmdir()


# ---------------------------------------------------------------------------
async def main():
    print("=" * 60)
    print("07 - 实战：HTTP 与文件 I/O")
    print("=" * 60)

    await demo_to_thread_http()
    await demo_aiohttp()
    await demo_concurrency_limit()
    await demo_file_io_to_thread()
    await demo_aiofiles()
    await demo_retry()
    await demo_batch_download()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - asyncio.to_thread：桥接阻塞库，无需第三方依赖")
    print("  - aiohttp：异步 HTTP，ClientSession 复用连接")
    print("  - aiofiles：异步文件 I/O")
    print("  - Semaphore：限制并发，保护下游")
    print("  - 重试 + 指数退避：提高健壮性")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
