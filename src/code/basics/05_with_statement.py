# -*- coding: utf-8 -*-
"""
05_with_statement.py - with 语句与上下文管理器

本文件面向有丰富 Java 经验的开发者，从零讲透 `with` 语句。

核心一句话
----------
`with` 解决的是「**进入时准备、退出时一定清理**」。等价于 try/finally，
但把释放逻辑封装进了对象本身，调用方不可能忘记。

Java 对应：try-with-resources，几乎一一对应，但 Python 多了一个
「__exit__ 返回 True 可以吞掉异常」的能力。

本章覆盖
--------
1. 为什么需要 with       —— try/finally 的痛点
2. with 的展开过程       —— __enter__ / __exit__ 调用时机
3. 常见内置用法          —— 文件、锁、临时目录、重定向输出
4. 自己实现（类）        —— 需要维护状态时
5. 自己实现（装饰器）    —— @contextmanager，99% 场景够用
6. __exit__ 吞异常       —— Python 独有的坑
7. 多资源与嵌套          —— with a, b:  vs  嵌套 with
8. 常见陷阱

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       全部使用标准库。
"""

import sys
import time


# =============================================================================
# 1. 为什么需要 with
# =============================================================================

def demo_why_with():
    """对比「手动关闭」与「with」的写法差异。"""
    print("=== 1. 为什么需要 with ===")

    print("  ❌ 写法一：手动关闭，异常时泄漏资源")
    print("     f = open(path)")
    print("     data = f.read()      # 这里抛异常，f 永远不会关闭")
    print("     f.close()")

    print("\n  ⚠️ 写法二：try/finally，正确但啰嗦")
    print("     f = open(path)")
    print("     try:")
    print("         data = f.read()")
    print("     finally:")
    print("         f.close()       # 必须自己写，且容易写错顺序")

    print("\n  ✅ 写法三：with，释放逻辑封装在对象里")
    print("     with open(path) as f:")
    print("         data = f.read()")
    print("     # 出了 with 块，无论是否异常，文件都已关闭")

    # 真实演示：with 保证关闭
    import tempfile
    import os

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                     encoding="utf-8") as f:
        path = f.name
        f.write("hello")
    try:
        with open(path, encoding="utf-8") as f:
            print(f"\n  实际读取: {f.read()!r}")
            print(f"  with 块内 f.closed = {f.closed}")
        print(f"  with 块外 f.closed = {f.closed}   <- 自动关闭")
    finally:
        os.unlink(path)

    print("  [Java 对比] 与 try-with-resources 完全对应；"
          "Java 的 finally 乱象在 Python 里同样存在，with 是标准解法")


# =============================================================================
# 2. with 的展开过程
# =============================================================================

def demo_expansion():
    """拆解 with 语句底层做了什么。"""
    print("\n=== 2. with 的展开过程 ===")

    class Traced:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            print(f"    [__enter__] {self.name} 进入")
            return f"<资源:{self.name}>"     # 返回值绑定给 as 后面的变量

        def __exit__(self, exc_type, exc_val, exc_tb):
            print(f"    [__exit__]  {self.name} 退出 "
                  f"(exc_type={exc_type.__name__ if exc_type else None})")
            return False                      # 不吞异常

    print("  with Traced('A') as x:")
    with Traced("A") as x:
        print(f"    块内 x = {x}")

    print("\n  等价的手写代码：")
    print("    mgr = Traced('A')")
    print("    x = mgr.__enter__()")
    print("    try:")
    print("        ...块内代码...")
    print("    except Exception as e:")
    print("        if not mgr.__exit__(type(e), e, e.__traceback__):")
    print("            raise")
    print("    else:")
    print("        mgr.__exit__(None, None, None)")

    print("\n  异常时 __exit__ 依然被调用：")
    try:
        with Traced("B"):
            raise ValueError("块内出错了")
    except ValueError:
        print("    异常已向上传播（__exit__ 返回 False）")

    print("  [要点] __exit__ 一定被调用 —— 这是 with 存在的全部理由")


# =============================================================================
# 3. 常见内置用法
# =============================================================================

def demo_builtin_uses():
    """文件、锁、临时目录、输出重定向。"""
    print("\n=== 3. 常见内置用法 ===")

    # 3.1 文件
    print("  ① 文件")
    print("     with open(p, encoding='utf-8') as f: ...")

    # 3.2 锁
    print("\n  ② 线程锁（with 自动 acquire/release）")
    import threading

    lock = threading.Lock()
    counter = [0]

    def worker():
        for _ in range(1000):
            with lock:
                counter[0] += 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"     4 线程各加 1000 次，最终 counter = {counter[0]}（无锁会小于 4000）")
    print("     [Java 对比] synchronized 块 / lock.lock() + finally unlock()")

    # 3.3 临时目录
    print("\n  ③ 临时目录")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "a.txt"
        p.write_text("data", encoding="utf-8")
        print(f"     临时目录: {tmp}")
        print(f"     写入文件: {p.name} 存在={p.exists()}")
    print(f"     退出后目录存在: {Path(tmp).exists()}   <- 自动递归删除")

    # 3.4 输出重定向
    print("\n  ④ 输出重定向")
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("这句话被捕获了")
    print(f"     捕获到的内容: {buf.getvalue().strip()!r}")
    print("     [场景] 测试时断言被测函数的打印输出")


def demo_decimal_context():
    """with 也用于「临时修改全局状态」。"""
    print("\n=== 4. 临时修改全局状态 ===")
    from decimal import Decimal, localcontext

    print(f"  默认精度: {Decimal(1) / Decimal(3)}")
    with localcontext() as ctx:
        ctx.prec = 4
        print(f"  with 内精度 4: {Decimal(1) / Decimal(3)}")
    print(f"  退出后恢复: {Decimal(1) / Decimal(3)}")
    print("  [要点] localcontext 是「临时改全局配置」的典型模式，"
          "比手动存旧值再还原安全")


# =============================================================================
# 4. 自己实现：类
# =============================================================================

def demo_implement_class():
    """用类实现上下文管理器（需要维护状态时用）。"""
    print("\n=== 5. 自己实现（类）===")

    class Timer:
        """计时器：测量 with 块内代码耗时。"""

        def __init__(self, label: str = "block"):
            self.label = label
            self.elapsed = None

        def __enter__(self):
            self._start = time.perf_counter()
            return self                     # 返回值给 as 变量

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.elapsed = time.perf_counter() - self._start
            status = f"异常 {exc_type.__name__}" if exc_type else "正常"
            print(f"    [{self.label}] {status}，耗时 {self.elapsed * 1000:.1f} ms")
            return False                    # 不吞异常

    with Timer("sleep 20ms") as t:
        time.sleep(0.02)
    print(f"    事后可从对象读取: elapsed={t.elapsed:.4f}s")

    try:
        with Timer("会抛异常"):
            raise RuntimeError("boom")
    except RuntimeError:
        print("    异常照常传播，但计时逻辑已执行")

    print("  [要点] 需要暴露状态（如 elapsed）时，用类更自然；"
          "__enter__ 返回 self 是常见惯例")


# =============================================================================
# 5. 自己实现：@contextmanager
# =============================================================================

def demo_implement_decorator():
    """用 @contextmanager 实现（更简洁）。"""
    print("\n=== 6. 自己实现（@contextmanager）===")
    from contextlib import contextmanager

    @contextmanager
    def timer(label="block"):
        start = time.perf_counter()
        try:
            yield                          # yield 之前 = __enter__
        finally:
            elapsed = time.perf_counter() - start
            print(f"    [{label}] 耗时 {elapsed * 1000:.1f} ms")
        # yield 之后 = __exit__

    with timer("装饰器版"):
        time.sleep(0.02)

    print("\n  yield 的返回值会成为 as 后面的变量：")

    @contextmanager
    def resource(name):
        print(f"    [setup] 打开 {name}")
        try:
            yield {"name": name, "open": True}      # 这个值给 as
        finally:
            print(f"    [teardown] 关闭 {name}")

    with resource("db") as r:
        print(f"    拿到资源: {r}")

    print("\n  ⚠️ 异常时 try/finally 保证清理：")
    try:
        with resource("conn"):
            raise ValueError("中途失败")
    except ValueError:
        print("    异常已传播，但 teardown 已执行")

    print("  [要点] 99% 的场景用 @contextmanager 就够了，"
          "除非需要多次进入同一对象")


# =============================================================================
# 6. __exit__ 吞异常
# =============================================================================

def demo_suppress_exception():
    """__exit__ 返回 True 会静默吞掉异常——Python 独有。"""
    print("\n=== 7. __exit__ 吞异常 ===")

    class Swallow:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                print(f"    [吞掉] {exc_type.__name__}: {exc_val}")
            return True             # True = 异常不再向外传播

    print("  with Swallow(): raise ValueError('看不见我')")
    with Swallow():
        raise ValueError("看不见我")
    print("    程序继续执行，没有崩溃")

    # 标准库的现成版本
    print("\n  标准库等价物：contextlib.suppress")
    from contextlib import suppress

    with suppress(FileNotFoundError):
        open("不存在的文件.txt", encoding="utf-8")
    print("    suppress(FileNotFoundError) 静默忽略该异常")

    print("\n  ⚠️ 不要滥用：")
    print("    - 吞掉异常会让 bug 变得难以定位")
    print("    - 库作者尤其不要默认吞异常，应在文档里明确说明")
    print("    - 只吞「明确预期且可忽略」的特定异常类型")


# =============================================================================
# 7. 多资源与嵌套
# =============================================================================

def demo_multiple():
    """多资源写法与退出顺序。"""
    print("\n=== 8. 多资源与嵌套 ===")
    import tempfile
    from pathlib import Path

    # 一行管多个（推荐）
    print("  ✅ 一行多个：with a as x, b as y:")
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        print(f"     d1={Path(d1).name}  d2={Path(d2).name}")
        print("     两个资源都可用")

    # 嵌套写法（等价，但缩进更深）
    print("\n  ✅ 嵌套写法（等价）：")
    print("     with a as x:")
    print("         with b as y:")
    print("             ...")

    # 退出顺序：LIFO
    print("\n  退出顺序是 LIFO（后进先出）：")

    class Tag:
        def __init__(self, n):
            self.n = n

        def __enter__(self):
            print(f"      enter {self.n}")
            return self

        def __exit__(self, *a):
            print(f"      exit  {self.n}")
            return False

    with Tag("A"), Tag("B"), Tag("C"):
        print("      --- 块内 ---")

    print("  [要点] B 依赖 A、C 依赖 B 时，顺序很关键；"
          "与 Java try-with-resources 的关闭顺序一致")


# =============================================================================
# 8. 常见陷阱
# =============================================================================

def demo_pitfalls():
    """高频错误。"""
    print("\n=== 9. 常见陷阱 ===")

    print("  坑 1  __exit__ 的异常参数顺序容易写错")
    print("        正确: def __exit__(self, exc_type, exc_val, exc_tb)")
    print("        常见错误: 参数名写反、漏掉 self")

    print("\n  坑 2  @contextmanager 里没用 try/finally")
    print("        @contextmanager")
    print("        def bad():")
    print("            r = acquire()")
    print("            yield r          # ❌ 块内抛异常时不会 release")
    print("            release(r)")
    print("        正确: yield 必须包在 try/finally 里")

    print("\n  坑 3  @contextmanager 函数只能 yield 一次")
    print("        同一个生成器对象不能重复 with；需每次调用 once() 生成新对象")

    from contextlib import contextmanager

    @contextmanager
    def once():
        yield 1

    cm = once()
    with cm:
        pass
    try:
        with cm:
            pass
    except (RuntimeError, AttributeError) as exc:
        print(f"        第二次进入 -> {type(exc).__name__}: {exc}")

    print("\n  坑 4  with 块内 return/break 也会触发 __exit__")
    print("        def f():")
    print("            with open(p) as fh:")
    print("                return fh.read()    # 文件依然会被关闭 ✅")

    print("\n  坑 5  忘记 as 但需要对象")
    print("        with open(p):            # 能用，但拿不到文件对象")
    print("            pass")
    print("        with open(p) as f:       # 需要对象时务必 as")

    print("\n  坑 6  吞异常导致静默失败")
    print("        __exit__ 返回 True 时，块内任何异常都消失")
    print("        只在明确预期时使用，并写清注释")


def print_java_mapping():
    print("\n=== 10. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("资源管理", "with obj as x:", "try (var x = obj)"),
        ("协议", "__enter__ / __exit__", "AutoCloseable.close()"),
        ("多资源", "with a, b:", "try (a; b)"),
        ("退出顺序", "LIFO", "LIFO"),
        ("异常时清理", "一定执行", "一定执行"),
        ("吞异常", "__exit__ 返回 True", "无此能力"),
        ("临时改状态", "localcontext / patch", "无惯用对应"),
        ("异步版", "async with", "无（close 同步）"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 64)
    print("with 语句与上下文管理器")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 64)

    demo_why_with()
    demo_expansion()
    demo_builtin_uses()
    demo_decimal_context()
    demo_implement_class()
    demo_implement_decorator()
    demo_suppress_exception()
    demo_multiple()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 64)
    print("所有 demo 运行完成！")
    print("=" * 64)


if __name__ == "__main__":
    main()
