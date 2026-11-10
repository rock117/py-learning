"""
13 - 其他实用特性
==================
本节目标：
  1. pickle 序列化（对比 Java Serializable，注意安全警告）
  2. sqlite3 内置数据库
  3. logging 日志框架（对比 Java java.util.logging）
  4. argparse CLI 参数解析
  5. configparser/tomllib 配置文件
  6. __future__ 提前启用未来特性
  7. weakref.finalize 弱引用终结器
  8. 实战：一个带日志和配置的小工具

对应 Java 概念：
  - pickle ≈ Java Serializable（但 pickle 不安全，能执行任意代码）
  - sqlite3 ≈ JDBC + SQLite JDBC 驱动（但 Python 内置无需驱动）
  - logging ≈ java.util.logging（API 设计几乎一致）
  - argparse ≈ Apache Commons CLI / picocli
  - configparser ≈ java.util.Properties
"""

from __future__ import annotations

import pickle
import sqlite3
import logging
import argparse
import configparser
import weakref
import sys
import os
import io
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. pickle 序列化
# ---------------------------------------------------------------------------
class User:
    """可 pickle 的简单类。"""
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"User(name={self.name!r}, age={self.age})"


def demo_pickle():
    print("\n=== 1. pickle 序列化 ===")
    user = User("Alice", 30)

    # 序列化成 bytes
    data = pickle.dumps(user)
    print(f"  pickle.dumps: {data[:40]}... (共 {len(data)} 字节)")

    # 反序列化
    restored = pickle.loads(data)
    print(f"  pickle.loads: {restored}")

    # 写入文件
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
        pickle.dump(user, f)
    with open(path, "rb") as f:
        from_file = pickle.load(f)
    print(f"  从文件读取: {from_file}")
    os.unlink(path)

    # 安全警告：pickle.loads 能执行任意代码！
    print("  [警告] 安全警告：")
    print("    pickle.loads(恶意数据) 会执行任意 Python 代码")
    print("    Java Serializable 也有类似风险（readObject 漏洞）")
    print("    原则：永远不要 pickle.loads 不可信来源的数据")
    print("    替代：用 JSON（json 模块）处理不可信数据")


# ---------------------------------------------------------------------------
# 2. sqlite3 内置数据库
# ---------------------------------------------------------------------------
def demo_sqlite():
    print("\n=== 2. sqlite3 内置数据库 ===")
    # Java 需要 SQLite JDBC 驱动，Python 内置 sqlite3 模块

    # 用内存数据库（:memory:）演示，不落盘
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=WAL")  # 部分高级特性

    # 建表
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER
        )
    """)

    # 插入（参数化查询，防 SQL 注入）
    conn.executemany(
        "INSERT INTO users (name, age) VALUES (?, ?)",
        [("Alice", 30), ("Bob", 25), ("Carol", 35)],
    )
    conn.commit()

    # 查询
    cursor = conn.execute("SELECT id, name, age FROM users WHERE age > ?", (26,))
    for row in cursor:
        print(f"    {row}")

    # row_factory 让查询结果像字典
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE name = ?", ("Alice",)).fetchone()
    print(f"  Row 字典式访问: name={row['name']}, age={row['age']}")

    # 事务（with 语句自动 commit/rollback）
    print("  事务演示:")
    try:
        with conn:  # 成功 commit，异常 rollback
            conn.execute("INSERT INTO users (name, age) VALUES ('Dave', 40)")
            conn.execute("INSERT INTO users (name, age) VALUES ('Eve', 28)")
    except Exception as e:
        print(f"    事务回滚: {e}")

    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print(f"  当前用户数: {count}")

    conn.close()
    print("  Java 对比：需要 JDBC + 驱动 jar，Python 内置零依赖")


# ---------------------------------------------------------------------------
# 3. logging 日志框架
# ---------------------------------------------------------------------------
def demo_logging():
    print("\n=== 3. logging 日志框架 ===")
    # Java java.util.logging 的 Logger/Handler/Formatter 几乎一一对应

    # 配置 logger
    logger = logging.getLogger("demo")
    logger.setLevel(logging.DEBUG)  # 设置最低级别

    # 添加控制台 handler
    handler = logging.StreamHandler(io.StringIO())  # 重定向到 buffer 演示
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 各级别日志
    logger.debug("调试信息（详细诊断）")
    logger.info("普通信息（正常运行）")
    logger.warning("警告（潜在问题）")
    logger.error("错误（已发生问题）")
    logger.critical("严重（系统级故障）")

    # 读取 handler 输出
    output = handler.stream.getvalue()
    for line in output.strip().splitlines():
        print(f"    {line}")

    logger.removeHandler(handler)
    print("  级别对照：DEBUG < INFO < WARNING < ERROR < CRITICAL")
    print("  Java 对比：Level.FINE/FINER/FINEST ≈ DEBUG/INFO/... 结构一致")


# ---------------------------------------------------------------------------
# 4. argparse CLI 参数解析
# ---------------------------------------------------------------------------
def demo_argparse():
    print("\n=== 4. argparse CLI 参数解析 ===")
    # Java 对比：Apache Commons CLI 或 picocli

    parser = argparse.ArgumentParser(
        prog="mytool",
        description="示例命令行工具",
    )
    # 位置参数
    parser.add_argument("input", help="输入文件路径")
    # 可选参数
    parser.add_argument("-o", "--output", default="out.txt", help="输出路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细模式")
    parser.add_argument("-n", "--count", type=int, default=1, help="重复次数")
    # 互斥参数
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fast", action="store_true", help="快速模式")
    group.add_argument("--safe", action="store_true", help="安全模式")

    # 模拟命令行参数（实际从 sys.argv 取）
    test_args = ["data.csv", "-o", "result.txt", "-v", "-n", "3", "--fast"]
    args = parser.parse_args(test_args)

    print(f"  输入: {args.input}")
    print(f"  输出: {args.output}")
    print(f"  详细: {args.verbose}")
    print(f"  次数: {args.count}")
    print(f"  模式: fast={args.fast}, safe={args.safe}")
    print("  argparse 自动生成 --help，参数类型转换，互斥校验")


# ---------------------------------------------------------------------------
# 5. configparser 配置文件
# ---------------------------------------------------------------------------
def demo_configparser():
    print("\n=== 5. configparser 配置文件 ===")
    # Java 对比：java.util.Properties（但 Properties 不支持分段）

    config_text = """
[database]
host = localhost
port = 5432
name = mydb

[logging]
level = INFO
file = app.log
"""
    config = configparser.ConfigParser()
    config.read_string(config_text)

    print(f"  [database] host = {config['database']['host']}")
    print(f"  [database] port = {config.getint('database', 'port')}")
    print(f"  [logging] level = {config['logging']['level']}")

    # 写入文件
    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False, mode="w") as f:
        path = f.name
        config.write(f)
    print(f"  已写入配置文件: {Path(path).name}")
    os.unlink(path)


# ---------------------------------------------------------------------------
# 6. tomllib 读取 TOML 配置（Python 3.11+）
# ---------------------------------------------------------------------------
def demo_tomllib():
    print("\n=== 6. tomllib 读取 TOML（Python 3.11+）===")
    try:
        import tomllib  # 3.11+ 内置
    except ImportError:
        print("  tomllib 需要 Python 3.11+，当前版本不支持，跳过")
        print("  3.10 及以下可用 pip install tomli（API 一致）")
        return

    toml_text = """
[project]
name = "demo"
version = "1.0.0"

[tool.demo]
debug = true
max_workers = 4
"""
    data = tomllib.loads(toml_text)
    print(f"  project.name = {data['project']['name']}")
    print(f"  tool.demo.debug = {data['tool']['demo']['debug']}")
    print(f"  tool.demo.max_workers = {data['tool']['demo']['max_workers']}")
    print("  TOML 比 INI 更现代，支持嵌套表、数组、类型，是 pyproject.toml 格式")


# ---------------------------------------------------------------------------
# 7. __future__ 提前启用未来特性
# ---------------------------------------------------------------------------
def demo_future():
    print("\n=== 7. __future__ 提前启用未来特性 ===")
    # __future__ 让旧版本 Python 提前用上未来版本的行为
    # Java 对比：无直接对应（Java 新特性直接在 JDK 版本启用）

    print("  常用 __future__ 导入：")
    print("    from __future__ import annotations  # 3.7+，注解延迟求值")
    print("    from __future__ import generator_stop  # 3.7+ 默认启用")
    print("    from __future__ import barry_as_FLUFL  # 彩蛋：!= 改成 <>")

    # annotations 延迟求值示例（3.10+ 默认行为，但显式导入更明确）
    # 注：from __future__ import annotations 必须在文件顶部，已在文件开头导入

    # 现在可以写前向引用注解而不报错
    def get_tree() -> "TreeNode":
        return TreeNode()

    print("  from __future__ import annotations 让所有注解变成字符串")
    print("  好处：前向引用不用引号，运行时不求值，性能更好")


class TreeNode:
    pass


# ---------------------------------------------------------------------------
# 8. weakref.finalize 弱引用终结器
# ---------------------------------------------------------------------------
def demo_weakref_finalize():
    print("\n=== 8. weakref.finalize 弱引用终结器 ===")
    # Java 对比：Object.finalize()（已废弃）或 Cleaner/PhantomReference
    # Python 的 finalize 更可控：对象被 GC 时调用注册的回调

    cleanup_log = []

    class Resource:
        def __init__(self, name):
            self.name = name

    def cleanup(name):
        cleanup_log.append(f"清理 {name}")
        print(f"  [finalize] 清理 {name}")

    obj = Resource("file-handle")
    # 注册终结器：obj 被 GC 时调用 cleanup("file-handle")
    finalizer = weakref.finalize(obj, cleanup, "file-handle")
    print(f"  已注册终结器: alive={finalizer.alive}")

    # 主动调用并注销（类似 try-finally 的 finally）
    # finalizer()  # 取消注释会立即触发清理

    # 删除对象，触发 GC（CPython 引用计数立即回收）
    del obj
    print(f"  del 后 finalizer.alive={finalizer.alive}")
    print(f"  cleanup_log: {cleanup_log}")

    # 对比 __del__：finalize 更灵活，可注册多个，可取消
    print("  对比 __del__：finalize 可注册多个回调，可主动取消，更可控")


# ---------------------------------------------------------------------------
# 9. weakref 弱引用字典
# ---------------------------------------------------------------------------
def demo_weakref_dict():
    print("\n=== 9. weakref.WeakValueDictionary ===")
    # Java 对比：WeakHashMap
    # 键或值是弱引用，对象无其他引用时自动移除条目

    class Big:
        def __init__(self, n):
            self.n = n

    wvd = weakref.WeakValueDictionary()
    a = Big(1)
    wvd["a"] = a
    print(f"  添加后 keys: {list(wvd.keys())}")

    del a  # 删除强引用
    import gc
    gc.collect()
    print(f"  del a + gc 后 keys: {list(wvd.keys())} (自动移除)")
    print("  用途：缓存，避免内存泄漏（对象不用时自动清理）")


# ---------------------------------------------------------------------------
# 10. 实战：带日志和配置的小工具
# ---------------------------------------------------------------------------
def build_mini_tool():
    """构建一个带日志和配置的迷你工具，演示综合运用。"""
    print("\n=== 10. 实战：带日志和配置的小工具 ===")

    # 1. 配置（用 configparser）
    config = configparser.ConfigParser()
    config.read_string("""
[tool]
name = greeter
greeting = Hello

[logging]
level = INFO
""")

    # 2. 日志
    logger = logging.getLogger(config["tool"]["name"])
    logger.setLevel(getattr(logging, config["logging"]["level"]))
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(h)

    # 3. 业务逻辑
    def greet(name: str) -> str:
        greeting = config["tool"]["greeting"]
        msg = f"{greeting}, {name}!"
        logger.info(f"生成问候: {msg}")
        return msg

    # 4. 运行
    results = [greet(n) for n in ["Alice", "Bob", "Carol"]]
    for r in results:
        print(f"    {r}")

    print("  日志输出:")
    for line in buf.getvalue().strip().splitlines():
        print(f"    {line}")

    print("  这个小工具组合了：configparser 配置 + logging 日志 + 业务逻辑")
    print("  Java 对比：Properties + java.util.logging + 主逻辑，结构类似")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("13 - 其他实用特性")
    print("=" * 60)

    demo_pickle()
    demo_sqlite()
    demo_logging()
    demo_argparse()
    demo_configparser()
    demo_tomllib()
    demo_future()
    demo_weakref_finalize()
    demo_weakref_dict()
    build_mini_tool()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - pickle：序列化，但绝不 loads 不可信数据（能执行任意代码）")
    print("  - sqlite3：内置零依赖数据库，JDBC 不用装驱动")
    print("  - logging：与 java.util.logging 结构一致的日志框架")
    print("  - argparse：强大的 CLI 解析，自动生成 --help")
    print("  - configparser/tomllib：INI/TOML 配置文件读取")
    print("  - __future__：提前启用未来版本特性")
    print("  - weakref.finalize：可控的对象终结回调（替代 __del__）")
    print("=" * 60)


if __name__ == "__main__":
    main()
