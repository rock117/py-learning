"""
08 - 上下文管理器进阶
=====================
本节目标：
  1. 回顾 async with（简要）
  2. ExitStack 动态管理多个上下文（对比 Java try-with-resources 多资源）
  3. AsyncExitStack 异步版本
  4. contextlib.suppress 忽略指定异常（对比 Java catch{} 空捕获）
  5. contextlib.redirect_stdout 重定向输出（对比 Java System.setOut）
  6. contextlib.closing 给只有 close() 的对象加 with 支持
  7. contextlib.contextmanager 装饰器
  8. 实战：数据库事务管理器

对应 Java 概念：
  - with 语句 ≈ try-with-resources（AutoCloseable）
  - ExitStack ≈ 动态数量的 try-with-resources（Java 不支持动态）
  - contextlib.suppress ≈ catch (IOException e) { /* 忽略 */ }
  - redirect_stdout ≈ System.setOut(new PrintStream(...))
  - @contextmanager ≈ 用 try-finally 模拟 AutoCloseable
"""

import asyncio
import io
import sys
from contextlib import (
    ExitStack,
    AsyncExitStack,
    suppress,
    redirect_stdout,
    redirect_stderr,
    closing,
    contextmanager,
    asynccontextmanager,
)


# ---------------------------------------------------------------------------
# 1. 回顾 async with（简要）
# ---------------------------------------------------------------------------
class AsyncResource:
    """异步资源：进入时打开，退出时关闭。"""

    def __init__(self, name: str):
        self.name = name

    async def __aenter__(self):
        print(f"  [async] 打开 {self.name}")
        await asyncio.sleep(0.05)  # 模拟异步初始化
        return self

    async def __aexit__(self, exc_type, exc, tb):
        print(f"  [async] 关闭 {self.name}")
        await asyncio.sleep(0.05)
        return False  # 不吞异常


async def demo_async_with_review():
    print("\n=== 1. 回顾 async with ===")
    async with AsyncResource("R1") as r:
        print(f"  使用 {r.name}")
    # Java 等价：try (var r = new AsyncResource("R1")) { ... }
    # 但 Java 的 close() 是同步的，Python 的 __aexit__ 可以 await


# ---------------------------------------------------------------------------
# 2. ExitStack 动态管理多个上下文
# ---------------------------------------------------------------------------
class ManagedFile:
    """模拟一个需要 with 管理的文件句柄。"""

    def __init__(self, path: str):
        self.path = path
        self.opened = False

    def __enter__(self):
        print(f"  [file] 打开 {self.path}")
        self.opened = True
        return self

    def __exit__(self, exc_type, exc, tb):
        print(f"  [file] 关闭 {self.path}")
        self.opened = False
        return False


def demo_exit_stack():
    print("\n=== 2. ExitStack 动态管理多个上下文 ===")
    # Java try-with-resources 可以写多个资源：
    #   try (var a = ...; var b = ...; var c = ...) { ... }
    # 但资源数量在编译期就固定。Python 的 ExitStack 可以动态添加！

    files = [f"file_{i}.txt" for i in range(3)]

    with ExitStack() as stack:  # 创建一个"上下文栈"
        # 动态地把每个文件加入栈，进入其 __enter__
        handles = [stack.enter_context(ManagedFile(f)) for f in files]
        print(f"  已打开 {len(handles)} 个文件")
        for h in handles:
            print(f"    - {h.path} opened={h.opened}")
    # 退出时按 LIFO 顺序自动调用每个 __exit__（与 Java try-with-resources 一致）


# ---------------------------------------------------------------------------
# 3. ExitStack 的 callback：注册清理回调
# ---------------------------------------------------------------------------
def demo_exit_stack_callback():
    print("\n=== 3. ExitStack.callback 注册清理回调 ===")
    with ExitStack() as stack:
        # callback 不需要对象实现 __enter__/__exit__，任意函数都行
        stack.callback(lambda: print("  清理回调 1"))
        stack.callback(lambda: print("  清理回调 2"))
        print("  主体逻辑执行中...")
    # 退出时按 LIFO 调用：先 2 后 1
    # Java 等价：没有直接对应，类似 finally 块里手动调用多个清理方法


# ---------------------------------------------------------------------------
# 4. AsyncExitStack 异步版本
# ---------------------------------------------------------------------------
async def demo_async_exit_stack():
    print("\n=== 4. AsyncExitStack 异步版本 ===")
    async with AsyncExitStack() as stack:
        # 动态添加多个异步上下文
        resources = [
            await stack.enter_async_context(AsyncResource(f"A{i}"))
            for i in range(3)
        ]
        print(f"  已获取 {len(resources)} 个异步资源")
    # 退出时按 LIFO 调用 __aexit__


# ---------------------------------------------------------------------------
# 5. contextlib.suppress 忽略指定异常
# ---------------------------------------------------------------------------
def demo_suppress():
    print("\n=== 5. contextlib.suppress 忽略指定异常 ===")
    # Java 等价：catch (FileNotFoundException e) { /* 空捕获，故意忽略 */ }

    # 不用 suppress 的写法：
    try:
        raise FileNotFoundError("test.txt")
    except FileNotFoundError:
        print("  传统写法：捕获后什么都不做")

    # 用 suppress：更明确地表达"我故意忽略这个异常"
    with suppress(FileNotFoundError, PermissionError):
        raise FileNotFoundError("test.txt")
    print("  suppress 写法：异常被静默忽略，继续执行")

    # 注意：只忽略指定的异常，其他异常仍会抛出
    # suppress() 不传参数 = 忽略所有异常（不推荐，会掩盖 bug）


# ---------------------------------------------------------------------------
# 6. contextlib.redirect_stdout 重定向输出
# ---------------------------------------------------------------------------
def demo_redirect_stdout():
    print("\n=== 6. redirect_stdout 重定向标准输出 ===")
    # Java 等价：System.setOut(new PrintStream(baos));
    # 但 Python 的版本是上下文管理器，退出后自动恢复

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        # 这段代码的 print 不会到屏幕，而是进 buffer
        print("这条消息被重定向到 buffer")
        print("第二条消息")
    # 退出 with 后，stdout 自动恢复
    print(f"  buffer 内容: {buffer.getvalue()!r}")

    # 同理有 redirect_stderr
    err_buffer = io.StringIO()
    with redirect_stderr(err_buffer):
        print("错误信息", file=sys.stderr)
    print(f"  stderr 内容: {err_buffer.getvalue()!r}")


# ---------------------------------------------------------------------------
# 7. contextlib.closing 给只有 close() 的对象加 with 支持
# ---------------------------------------------------------------------------
class OnlyHasClose:
    """有些对象（如 urllib 的 response）只有 close() 方法，
    没有实现 __enter__/__exit__，无法直接用 with。"""

    def __init__(self, name: str):
        self.name = name
        self.closed = False

    def close(self):
        print(f"  [close] 关闭 {self.name}")
        self.closed = True


def demo_closing():
    print("\n=== 7. contextlib.closing ===")
    obj = OnlyHasClose("socket")
    # 直接 with obj 会报错（没有 __enter__）
    # with obj:  # AttributeError
    #     pass

    # 用 closing 包装：退出时自动调用 obj.close()
    with closing(obj) as o:
        print(f"  使用 {o.name}, closed={o.closed}")
    print(f"  退出后 closed={obj.closed}")
    # Java 等价：try { ... } finally { obj.close(); }


# ---------------------------------------------------------------------------
# 8. contextlib.contextmanager 装饰器（同步版）
# ---------------------------------------------------------------------------
@contextmanager
def indented_block(label: str):
    """用生成器函数实现上下文管理器：
    - yield 之前 = __enter__
    - yield 的值 = as 变量
    - yield 之后 = __exit__
    """
    print(f"  [{label}] 进入")
    try:
        yield f"value-of-{label}"  # 交给 as 变量
    finally:
        print(f"  [{label}] 退出")


def demo_contextmanager_decorator():
    print("\n=== 8. @contextmanager 装饰器 ===")
    with indented_block("demo") as val:
        print(f"  拿到值: {val}")
    # 这是实现上下文管理器最简洁的方式，比写 __enter__/__exit__ 省事


# ---------------------------------------------------------------------------
# 9. contextmanager 处理异常
# ---------------------------------------------------------------------------
@contextmanager
def tolerant_block():
    """演示 contextmanager 中捕获异常。"""
    print("  进入 tolerant_block")
    try:
        yield
    except ValueError as e:
        print(f"  在上下文内捕获 ValueError: {e}")
        # 不 re-raise = 吞掉异常（类似 __exit__ 返回 True）


def demo_contextmanager_exception():
    print("\n=== 9. @contextmanager 中处理异常 ===")
    with tolerant_block():
        raise ValueError("故意抛出")
    print("  异常被上下文管理器吞掉，继续执行")


# ---------------------------------------------------------------------------
# 10. 实战：数据库事务管理器
# ---------------------------------------------------------------------------
class FakeDB:
    """模拟数据库连接，支持事务。"""

    def __init__(self, name: str):
        self.name = name
        self.committed = False
        self.rolled_back = False

    def begin(self):
        print(f"  [DB:{self.name}] BEGIN TRANSACTION")

    def commit(self):
        self.committed = True
        print(f"  [DB:{self.name}] COMMIT")

    def rollback(self):
        self.rolled_back = True
        print(f"  [DB:{self.name}] ROLLBACK")

    def execute(self, sql: str):
        print(f"  [DB:{self.name}] EXEC: {sql}")
        return f"result of {sql}"


@contextmanager
def transaction(db: FakeDB):
    """事务管理器：正常退出 commit，异常退出 rollback。
    Java 等价（JDBC）：
        conn.setAutoCommit(false);
        try { ...; conn.commit(); }
        catch (Exception e) { conn.rollback(); throw e; }
    """
    db.begin()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise  # 重新抛出，让调用方知道


def demo_transaction_success():
    print("\n=== 10a. 事务成功提交 ===")
    db = FakeDB("orders")
    with transaction(db) as conn:
        conn.execute("INSERT INTO orders VALUES (1)")
        conn.execute("INSERT INTO orders VALUES (2)")
    print(f"  committed={db.committed}, rolled_back={db.rolled_back}")


def demo_transaction_failure():
    print("\n=== 10b. 事务异常回滚 ===")
    db = FakeDB("users")
    try:
        with transaction(db) as conn:
            conn.execute("INSERT INTO users VALUES (1)")
            raise RuntimeError("唯一键冲突")
    except RuntimeError as e:
        print(f"  外部捕获: {e}")
    print(f"  committed={db.committed}, rolled_back={db.rolled_back}")


# ---------------------------------------------------------------------------
# 11. 嵌套上下文 + ExitStack 组合
# ---------------------------------------------------------------------------
def demo_nested_exit_stack():
    print("\n=== 11. ExitStack 组合事务与文件 ===")
    db = FakeDB("logs")
    with ExitStack() as stack:
        # 把事务也压入栈
        txn = stack.enter_context(transaction(db))
        # 再打开一个文件
        f = stack.enter_context(ManagedFile("export.txt"))
        txn.execute("SELECT * FROM logs")
        print(f"  写入 {f.path}")
    # 退出顺序：文件先关（后进先出），事务再 commit


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
async def async_main():
    await demo_async_with_review()
    await demo_async_exit_stack()


def sync_main():
    demo_exit_stack()
    demo_exit_stack_callback()
    demo_suppress()
    demo_redirect_stdout()
    demo_closing()
    demo_contextmanager_decorator()
    demo_contextmanager_exception()
    demo_transaction_success()
    demo_transaction_failure()
    demo_nested_exit_stack()


def main():
    print("=" * 60)
    print("08 - 上下文管理器进阶")
    print("=" * 60)
    sync_main()
    asyncio.run(async_main())
    print("\n" + "=" * 60)
    print("小结：")
    print("  - ExitStack：动态管理数量不定的上下文（Java 做不到）")
    print("  - AsyncExitStack：异步版，配合 async with")
    print("  - suppress：明确地忽略指定异常，比空 catch 更清晰")
    print("  - redirect_stdout/stderr：临时重定向输出，自动恢复")
    print("  - closing：给只有 close() 的对象加 with 支持")
    print("  - @contextmanager：用 yield 优雅实现 __enter__/__exit__")
    print("  - 实战：transaction 管理器 = commit/rollback 模式")
    print("=" * 60)


if __name__ == "__main__":
    main()
