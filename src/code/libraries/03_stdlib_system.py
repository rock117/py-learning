# -*- coding: utf-8 -*-
"""
03_stdlib_system.py - Python 标准库系统工具讲解

本文件面向有丰富 Java 经验的开发者，讲解 Python 标准库中与"系统/进程/日志/
命令行/数据库/文件系统"相关的模块：
    - subprocess：子进程管理（对比 Java ProcessBuilder / Runtime.exec）
    - logging：日志框架（对比 java.util.logging / SLF4J）
    - argparse：命令行参数解析（对比 picocli / Apache Commons CLI）
    - sqlite3：嵌入式 SQL 数据库（对比 Java JDBC + SQLite JDBC）
    - tempfile：临时文件/目录
    - shutil：高级文件操作（对比 java.nio.file.Files）
    - pathlib + os 进阶：权限 / 符号链接 / 批量重命名

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       所有 demo 都可通过 `python 03_stdlib_system.py` 运行，exit code 0。
       第三方库（本文件全部使用标准库，无需额外安装）。

对比 Java：
    Java 开发者通常依赖 java.lang.ProcessBuilder / java.util.logging /
    Apache Commons CLI / JDBC 等，Python 标准库开箱即用，无需第三方依赖。
"""

import os
import sys
import subprocess
import logging
import logging.config
import argparse
import sqlite3
import tempfile
import shutil
import json
import stat
from pathlib import Path


# =============================================================================
# 第一部分：subprocess 模块
# =============================================================================
# [Java 对比] subprocess 类似 java.lang.ProcessBuilder / Runtime.exec()，
#             但 API 更简洁，且默认更安全（不依赖 shell 解释器）。

def demo_subprocess_run_basic():
    """subprocess.run 基本用法：执行命令并等待完成。

    [Java 对比]
        ProcessBuilder pb = new ProcessBuilder("git", "--version");
        Process p = pb.start();
        String out = new String(p.getInputStream().readAllBytes());
        int code = p.waitFor();
    Python 一行 subprocess.run 即可完成。
    """
    print("=== subprocess.run 基本用法 ===")
    # run 返回 CompletedProcess 对象，包含 args / returncode / stdout / stderr
    # [注意] Windows 下用 where，Linux/macOS 下用 which。这里用通用命令。
    result = subprocess.run(
        ["python", "--version"],  # 命令与参数列表（推荐写法，不经 shell）
        capture_output=True,      # 捕获 stdout/stderr 到 result.stdout/stderr
        text=True,                # 以文本（str）而非 bytes 返回输出
    )
    print("命令:", result.args)
    print("返回码:", result.returncode)
    print("stdout:", result.stdout.strip())
    print("stderr:", result.stderr.strip())


def demo_subprocess_capture():
    """capture_output 捕获输出，stdout 与 stderr 分开。

    [Java 对比] Java 需要手动开线程读取 InputStream，否则可能死锁；
                Python 的 capture_output=True 自动处理，避免管道阻塞。
    """
    print("\n=== capture_output 捕获输出 ===")
    # 执行一个会输出到 stderr 的命令（python -c "import sys; sys.stderr.write('err')")
    result = subprocess.run(
        [sys.executable, "-c", "import sys; print('to stdout'); sys.stderr.write('to stderr\\n')"],
        capture_output=True,
        text=True,
    )
    print("stdout 内容:", repr(result.stdout))
    print("stderr 内容:", repr(result.stderr))
    # [技巧] 也可用 stdout=subprocess.PIPE, stderr=subprocess.PIPE 等价 capture_output=True


def demo_subprocess_shell_warning():
    """shell=True 的用法与安全警告。

    [安全警告] shell=True 会把命令交给系统 shell 解释，存在命令注入风险！
        - 永远不要用 shell=True 拼接来自用户输入的字符串
        - 优先使用列表形式（shell=False，默认），由 OS 直接 exec
    [Java 对比] Java 的 Runtime.exec(String) 也会经过 shell 解析（在某些平台上），
                同样有注入风险，推荐用 ProcessBuilder(String[])。
    """
    print("\n=== shell=True 用法与安全警告 ===")
    # 安全写法：列表形式，不经 shell
    safe = subprocess.run(["echo", "hello"], capture_output=True, text=True, shell=False)
    print("安全写法(列表):", safe.stdout.strip())

    # 危险写法（仅演示，不要在生产代码用用户输入拼接）
    # shell=True 时整个字符串交给 shell，可使用管道、通配符等 shell 特性
    dangerous = subprocess.run("echo hello & echo world", capture_output=True, text=True, shell=True)
    print("shell=True 输出:", dangerous.stdout.strip())
    print("[警告] shell=True 配合用户输入 = 命令注入漏洞，务必避免！")


def demo_subprocess_popen_pipe():
    """Popen 与管道：连接多个进程的 stdin/stdout。

    [Java 对比] Java 中连接进程管道非常繁琐，需要手动管理线程读取流；
                Python 的 Popen 支持 stdout=另一个Popen.stdin 直接管道。
    """
    print("\n=== Popen 管道连接 ===")
    # 经典示例：ls 输出 | findstr / grep 过滤
    # 这里用 Python 自身模拟：第一个进程输出数字，第二个进程过滤偶数
    p1 = subprocess.Popen(
        [sys.executable, "-c", "print('\\n'.join(str(i) for i in range(10)))"],
        stdout=subprocess.PIPE,
        text=True,
    )
    p2 = subprocess.Popen(
        [sys.executable, "-c", "import sys; [print(l.strip()) for l in sys.stdin if int(l.strip())%2==0]"],
        stdin=p1.stdout,   # 把 p1 的 stdout 接到 p2 的 stdin
        stdout=subprocess.PIPE,
        text=True,
    )
    # 关闭 p1.stdout 避免管道死锁（p1 写完后 fd 应由 p2 接管）
    p1.stdout.close()
    out, _ = p2.communicate()  # 等待 p2 完成，读取输出
    print("过滤后的偶数:", out.strip().replace("\n", ", "))


def demo_subprocess_timeout():
    """timeout 超时控制：防止子进程挂起。

    [Java 对比] Java 的 Process.waitFor(timeout, unit) 也可设超时，
                但超时后需手动 destroyForcibly()。
    Python 超时会抛 TimeoutExpired，并自动 kill 子进程。
    """
    print("\n=== timeout 超时控制 ===")
    try:
        # 这个命令会 sleep 10 秒，但 timeout=1 秒就超时
        subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=1,
        )
    except subprocess.TimeoutExpired as e:
        print("捕获超时:", e)
        print("超时后子进程已被自动终止")


def demo_subprocess_input():
    """input 参数：向子进程 stdin 传入数据。

    [Java 对比] Java 需要获取 Process.getOutputStream() 并手动 write + flush + close。
    Python 的 input= 参数自动完成写入与关闭。
    """
    print("\n=== input 参数 ===")
    # 子进程从 stdin 读取一行并大写化输出
    result = subprocess.run(
        [sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"],
        input="hello from parent\n",  # 自动写入 stdin 并关闭
        capture_output=True,
        text=True,
    )
    print("子进程输出:", result.stdout.strip())


def demo_subprocess_env():
    """env 参数：自定义子进程环境变量。

    [Java 对比] Java 的 ProcessBuilder.environment() 返回可修改的 Map。
    Python 的 env= 完全替换环境变量（不是追加），需手动继承父进程变量。
    """
    print("\n=== env 环境变量 ===")
    # 继承父进程环境，再添加自定义变量
    my_env = os.environ.copy()
    my_env["MY_CUSTOM_VAR"] = "secret_value"

    result = subprocess.run(
        [sys.executable, "-c", "import os; print(os.environ.get('MY_CUSTOM_VAR', 'NOT SET'))"],
        capture_output=True,
        text=True,
        env=my_env,  # 传入自定义环境
    )
    print("子进程读取自定义变量:", result.stdout.strip())

    # [注意] 如果不传 env，子进程继承父进程全部环境变量


def demo_subprocess_git():
    """实战：调用 git 命令获取仓库信息。

    [Java 对比] Java 中调用外部命令同样繁琐，且需处理编码、超时、异常。
    """
    print("\n=== 实战：调用 git 命令 ===")
    # 检查 git 是否可用
    if shutil.which("git") is None:
        print("  [注意] 系统未安装 git，跳过此 demo")
        return

    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        print("git 版本:", result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print("调用 git 失败:", e)


# =============================================================================
# 第二部分：logging 模块（进阶）
# =============================================================================
# [Java 对比] logging 模块类似 java.util.logging（JUL）的架构：
#   - Logger（记录器）  ≈ java.util.logging.Logger
#   - Handler（处理器）  ≈ java.util.logging.Handler / ConsoleHandler / FileHandler
#   - Formatter（格式器）≈ java.util.logging.Formatter
#   - Level（级别）     ≈ java.util.logging.Level
#   Python 的 logging 比 JUL 更灵活，且通过 dictConfig 支持复杂配置。
#   对比 SLF4J：SLF4J 是门面，需绑定后端（logback 等）；Python logging 自带实现。

def demo_logging_basic():
    """basicConfig 基础配置：最简单的日志方式。

    [Java 对比] 类似在代码里直接 Logger.getLogger().setLevel() + ConsoleHandler。
    basicConfig 是一次性配置，只对 root logger 生效，且只在第一次调用时有效。
    """
    print("\n=== logging basicConfig ===")
    # [注意] basicConfig 默认只对 root logger 配置，且只在 root 没有 handler 时生效。
    #        多次调用 basicConfig 默认无效（除非 force=True）。
    logging.basicConfig(
        level=logging.DEBUG,                    # 最低级别，低于此级别不输出
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",  # 格式
        datefmt="%H:%M:%S",                      # 时间格式
        force=True,                             # 强制重新配置（覆盖之前的配置）
    )
    logger = logging.getLogger("demo")  # 获取命名 logger
    logger.debug("这是 DEBUG 级别日志")
    logger.info("这是 INFO 级别日志")
    logger.warning("这是 WARNING 级别日志")
    logger.error("这是 ERROR 级别日志")
    logger.critical("这是 CRITICAL 级别日志")


def demo_logging_architecture():
    """Logger / Handler / Formatter 三层架构。

    [Java 对比] 与 JUL 完全一致的三层架构：
        Logger -> Handler -> Formatter
        记录器   处理器     格式器
    一个 Logger 可挂多个 Handler，每个 Handler 可有自己的 Formatter 和 Level。
    """
    print("\n=== Logger/Handler/Formatter 三层架构 ===")
    # 创建自定义 logger（不用 root，避免被 basicConfig 污染）
    logger = logging.getLogger("arch.demo")
    logger.setLevel(logging.DEBUG)

    # 清除可能存在的 handlers（避免重复输出）
    logger.handlers.clear()
    logger.propagate = False  # 不向 root logger 传播，避免重复打印

    # Handler 1：控制台输出，级别 INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("[控制台] %(levelname)s: %(message)s"))

    # Handler 2：文件输出，级别 DEBUG（注意 Windows 路径用 / 或 \\）
    log_file = Path(tempfile.gettempdir()) / "py_learning_demo.log"
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("[文件] %(asctime)s %(levelname)s: %(message)s"))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.debug("debug 信息只进文件")   # 控制台不显示（INFO 级别过滤）
    logger.info("info 信息进控制台和文件")
    logger.warning("warning 信息进控制台和文件")
    print(f"日志文件路径: {log_file}")


def demo_logging_levels():
    """日志级别 DEBUG/INFO/WARNING/ERROR/CRITICAL。

    [Java 对比] JUL 的级别：SEVERE / WARNING / INFO / CONFIG / FINE / FINER / FINEST
    Python 的级别：CRITICAL(50) / ERROR(40) / WARNING(30) / INFO(20) / DEBUG(10)
    数值越大优先级越高，setLevel(N) 表示只输出 >= N 的日志。
    """
    print("\n=== 日志级别 ===")
    print("级别数值:", logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
    # 输出: 10 20 30 40 50
    logger = logging.getLogger("levels.demo")
    logger.handlers.clear()
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)

    # 设置不同级别观察过滤效果
    for level_name, level in [("DEBUG", logging.DEBUG), ("WARNING", logging.WARNING)]:
        logger.setLevel(level)
        print(f"\n  -- logger.setLevel({level_name}) --")
        logger.debug("  debug 消息")
        logger.info("  info 消息")
        logger.warning("  warning 消息")


def demo_logging_rotating():
    """RotatingFileHandler / TimedRotatingFileHandler 滚动日志。

    [Java 对比] Java 中通常用 logback 的 RollingFileAppender 实现滚动；
    Python 标准库自带 RotatingFileHandler（按大小）和 TimedRotatingFileHandler（按时间）。
    """
    print("\n=== RotatingFileHandler 滚动日志 ===")
    from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

    log_dir = Path(tempfile.gettempdir()) / "py_learning_logs"
    log_dir.mkdir(exist_ok=True)

    # 按大小滚动：每个文件最大 1KB，保留 3 个备份
    rotating = RotatingFileHandler(
        str(log_dir / "app.log"),
        maxBytes=1024,       # 1KB 后滚动
        backupCount=3,       # 保留 3 个历史文件
        encoding="utf-8",
    )
    rotating.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

    logger = logging.getLogger("rotating.demo")
    logger.handlers.clear()
    logger.propagate = False
    logger.addHandler(rotating)
    logger.setLevel(logging.DEBUG)

    # 写入多条日志触发滚动
    for i in range(50):
        logger.info(f"日志条目 {i} " + "x" * 30)
    print(f"滚动日志目录: {log_dir}")
    print("文件列表:", [p.name for p in log_dir.iterdir()])

    # [说明] TimedRotatingFileHandler 按时间滚动（每天/每小时）
    # timed = TimedRotatingFileHandler("app.log", when="midnight", backupCount=7)


def demo_logging_custom_formatter():
    """自定义 Formatter：控制日志输出格式。

    [Java 对比] 类似继承 java.util.logging.Formatter 重写 format(LogRecord)。
    """
    print("\n=== 自定义 Formatter ===")

    class ColorlessFormatter(logging.Formatter):
        """自定义格式器：添加进程 ID 和模块信息。"""

        def format(self, record):
            # record 包含：levelname, name, message, module, lineno, process 等
            record.pid = os.getpid()  # 动态添加属性
            return super().format(record)

    fmt = ColorlessFormatter("[PID:%(pid)s] %(name)s %(levelname)s %(message)s")
    logger = logging.getLogger("custom.fmt")
    logger.handlers.clear()
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.info("带进程 ID 的日志")


def demo_logging_hierarchy():
    """getLogger 层级命名：点分命名形成父子关系。

    [Java 对比] JUL 也有 logger 层级（如 "com.example.service"），
    Python 同样用点分命名，子 logger 未设置级别时继承父 logger 级别。
    """
    print("\n=== Logger 层级命名 ===")
    # root -> "app" -> "app.db" -> "app.db.mysql"
    root = logging.getLogger()
    app = logging.getLogger("app")
    app_db = logging.getLogger("app.db")
    app_db_mysql = logging.getLogger("app.db.mysql")

    # 设置父 logger 级别，子 logger 继承
    app.setLevel(logging.WARNING)
    print("app 级别:", app.getEffectiveLevel(), "(WARNING)")
    print("app.db 继承级别:", app_db.getEffectiveLevel())
    print("app.db.mysql 继承级别:", app_db_mysql.getEffectiveLevel())

    # app.db 单独设置级别后不再继承
    app_db.setLevel(logging.DEBUG)
    print("app.db 设置后级别:", app_db.getEffectiveLevel(), "(DEBUG)")
    print("app.db.mysql 现在继承 app.db:", app_db_mysql.getEffectiveLevel())


def demo_logging_dict_config():
    """dictConfig 字典配置：声明式日志配置。

    [Java 对比] 类似 logback.xml / log4j2.xml 的声明式配置。
    Python 用 dictConfig 传入一个字典（通常从 YAML/JSON 加载）。
    """
    print("\n=== dictConfig 字典配置 ===")
    log_file = Path(tempfile.gettempdir()) / "py_learning_dictconfig.log"
    config = {
        "version": 1,                  # 必须为 1（schema 版本）
        "disable_existing_loggers": False,  # 不禁用已有 logger
        "formatters": {
            "simple": {"format": "%(asctime)s %(levelname)s %(message)s"},
            "detailed": {
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s:%(lineno)d %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_file),
                "encoding": "utf-8",
            },
        },
        "root": {                       # root logger 配置
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
    }
    logging.config.dictConfig(config)
    logger = logging.getLogger("dictconfig.demo")
    logger.debug("debug 进文件")
    logger.info("info 进控制台和文件")
    print(f"配置文件日志: {log_file}")


def demo_logging_json():
    """结构化日志（JSON 格式）：便于日志收集系统（ELK 等）解析。

    [Java 对比] Java 中常用 logstash-logback-encoder 输出 JSON 日志。
    Python 可自定义 Formatter 输出 JSON。
    """
    print("\n=== 结构化日志（JSON 格式） ===")

    class JsonFormatter(logging.Formatter):
        """将 LogRecord 序列化为 JSON 字符串。"""

        def format(self, record):
            log_dict = {
                "time": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno,
            }
            if record.exc_info:
                log_dict["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_dict, ensure_ascii=False)

    logger = logging.getLogger("json.demo")
    logger.handlers.clear()
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.info("这是一条 JSON 格式日志")
    logger.warning("带中文的警告日志")


# =============================================================================
# 第三部分：argparse 模块
# =============================================================================
# [Java 对比] argparse 类似 picocli / Apache Commons CLI，但内置于标准库。
#   - picocli 用 @Command / @Option 注解
#   - argparse 用 add_argument() 方法调用
#   argparse 自动生成 --help，支持子命令，功能非常强大。

def demo_argparse_basic():
    """基础参数：add_argument 基本用法。

    [Java 对比] picocli:
        @Option(names = "-n", description = "name") String name;
    argparse:
        parser.add_argument("-n", help="name")
    """
    print("\n=== argparse 基础参数 ===")
    parser = argparse.ArgumentParser(
        prog="mytool",               # 程序名（显示在 help 中）
        description="一个示例 CLI 工具",  # 描述（显示在 help 顶部）
        epilog="更多信息请查阅文档",     # 结尾文字
    )
    # 可选参数：-n / --name，类型 str，默认 "World"
    parser.add_argument("-n", "--name", type=str, default="World", help="问候的名字")
    # 位置参数：直接写名字，无 - 前缀
    parser.add_argument("action", help="要执行的动作")

    # 模拟命令行参数（实际使用时由 sys.argv 传入）
    args = parser.parse_args(["greet", "-n", "Python"])
    print("解析结果:", args)
    print("name =", args.name)
    print("action =", args.action)


def demo_argparse_positional_vs_optional():
    """位置参数 vs 可选参数。

    [Java 对比] picocli 中位置参数用 @Parameters，可选参数用 @Option。
    argparse 中：带 - 前缀的是可选参数，不带的是位置参数。
    """
    print("\n=== 位置参数 vs 可选参数 ===")
    parser = argparse.ArgumentParser()
    # 位置参数：必填，按顺序传入
    parser.add_argument("source", help="源文件路径")
    parser.add_argument("dest", help="目标文件路径")
    # 可选参数：可省略，用 - 或 -- 指定
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-c", "--count", type=int, default=1, help="重复次数")

    args = parser.parse_args(["input.txt", "output.txt", "-v", "-c", "3"])
    print("source =", args.source)
    print("dest =", args.dest)
    print("verbose =", args.verbose)  # store_true -> 布尔开关
    print("count =", args.count)


def demo_argparse_type_default_required():
    """类型转换 type= / 默认值 default= / 必选 required=。

    [Java 对比] picocli 用 type=Class 指定类型，defaultValue= 指定默认值。
    """
    print("\n=== type / default / required ===")
    parser = argparse.ArgumentParser()
    # required=True 表示该可选参数必须提供
    parser.add_argument("--port", type=int, required=True, help="端口号（必填）")
    parser.add_argument("--host", type=str, default="localhost", help="主机（默认 localhost）")
    # type 也可以是自定义函数
    parser.add_argument("--level", type=int, choices=[1, 2, 3], default=1, help="日志级别 1-3")

    args = parser.parse_args(["--port", "8080", "--level", "2"])
    print("port =", args.port, type(args.port))   # int 类型
    print("host =", args.host)
    print("level =", args.level)


def demo_argparse_mutually_exclusive():
    """互斥参数组：add_mutually_exclusive_group。

    [Java 对比] picocli 用 @ArgGroup(exclusive = true) 实现互斥。
    argparse 用 add_mutually_exclusive_group。
    """
    print("\n=== 互斥参数组 ===")
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verbose", action="store_true", help="详细输出")
    group.add_argument("--quiet", action="store_true", help="安静输出")
    parser.add_argument("file", help="目标文件")

    # 只能选 --verbose 或 --quiet 之一，不能同时用
    args = parser.parse_args(["test.txt", "--verbose"])
    print("verbose =", args.verbose, "| quiet =", args.quiet)

    # 以下会报错（取消注释测试）：
    # parser.parse_args(["test.txt", "--verbose", "--quiet"])


def demo_argparse_subparsers():
    """子命令 subparsers：类似 git add / git commit 的结构。

    [Java 对比] picocli 支持子命令（@Command(subcommands = {...})）。
    argparse 用 add_subparsers 实现类似结构。
    """
    print("\n=== 子命令 subparsers ===")
    parser = argparse.ArgumentParser(prog="gitlike")
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # 子命令 add
    parser_add = subparsers.add_parser("add", help="添加文件")
    parser_add.add_argument("files", nargs="+", help="要添加的文件")  # nargs='+' 至少一个

    # 子命令 commit
    parser_commit = subparsers.add_parser("commit", help="提交")
    parser_commit.add_argument("-m", "--message", required=True, help="提交信息")

    args = parser.parse_args(["add", "file1.txt", "file2.txt"])
    print("add 子命令:", args)

    args = parser.parse_args(["commit", "-m", "initial commit"])
    print("commit 子命令:", args)


def demo_argparse_help():
    """自动生成 --help：argparse 自动生成格式化的帮助信息。

    [Java 对比] picocli 也自动生成 usage help，格式更丰富（彩色等）。
    """
    print("\n=== 自动生成 --help ===")
    parser = argparse.ArgumentParser(prog="mytool", description="示例工具")
    parser.add_argument("-n", "--name", default="World", help="名字")
    parser.add_argument("--verbose", action="store_true", help="详细模式")
    parser.add_argument("path", help="目标路径")

    # 打印 help 文本（不退出程序）
    help_text = parser.format_help()
    print(help_text)


def demo_argparse_cli_tool():
    """实战：构建一个完整的 CLI 工具（文件统计）。

    [Java 对比] 完整对应一个 picocli 的 @Command 类。
    """
    print("\n=== 实战：文件统计 CLI 工具 ===")
    parser = argparse.ArgumentParser(
        prog="filestat",
        description="统计指定目录下的文件信息",
    )
    parser.add_argument("directory", help="要统计的目录")
    parser.add_argument("-e", "--extension", default=None, help="按扩展名过滤")
    parser.add_argument("-s", "--sort", choices=["name", "size"], default="name", help="排序方式")
    parser.add_argument("--limit", type=int, default=10, help="显示前 N 个")

    # 模拟参数：统计当前目录
    args = parser.parse_args([".", "--limit", "5"])
    print(f"目录: {args.directory}, 扩展名过滤: {args.extension}, 排序: {args.sort}, 限制: {args.limit}")

    # 实际统计逻辑
    path = Path(args.directory)
    if not path.is_dir():
        print(f"[注意] {path} 不是目录")
        return
    files = [f for f in path.iterdir() if f.is_file()]
    if args.extension:
        files = [f for f in files if f.suffix == f".{args.extension}"]
    if args.sort == "size":
        files.sort(key=lambda f: f.stat().st_size, reverse=True)
    else:
        files.sort(key=lambda f: f.name)
    for f in files[: args.limit]:
        print(f"  {f.name:30s} {f.stat().st_size:>10d} bytes")


# =============================================================================
# 第四部分：sqlite3 模块（进阶）
# =============================================================================
# [Java 对比] sqlite3 类似 Java JDBC + SQLite JDBC 驱动：
#   - connect()      ≈ DriverManager.getConnection()
#   - cursor()       ≈ Statement / PreparedStatement
#   - execute()       ≈ stmt.execute() / executeQuery()
#   - commit/rollback ≈ connection.commit() / rollback()
#   Python 标准库自带 sqlite3，无需额外驱动。

def demo_sqlite_connect():
    """连接数据库 connect 与游标 cursor。"""
    print("\n=== sqlite3 连接与游标 ===")
    # 连接内存数据库（:memory:），进程结束即销毁，适合测试
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 执行 DDL
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER
        )
    """)
    print("表 users 创建成功")
    conn.close()


def demo_sqlite_param_query():
    """参数化查询（防 SQL 注入）。

    [安全警告] 永远不要用字符串拼接构造 SQL！
        错误：cursor.execute(f"SELECT * FROM users WHERE name='{user_input}'")
        正确：cursor.execute("SELECT * FROM users WHERE name=?", (user_input,))
    [Java 对比] JDBC 的 PreparedStatement.setString() 同理。
    """
    print("\n=== 参数化查询（防注入） ===")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    conn.executemany("INSERT INTO users VALUES (?, ?, ?)", [
        (1, "Alice", 30),
        (2, "Bob", 25),
        (3, "Charlie", 35),
    ])
    conn.commit()

    # 参数化查询（? 占位符）
    name = "Alice"
    for row in conn.execute("SELECT * FROM users WHERE name = ?", (name,)):
        print("查询结果:", row)

    # [注意] 即使只有一个参数，也要传 tuple: (name,) 而非 name
    conn.close()


def demo_sqlite_transaction():
    """事务管理 commit / rollback。

    [Java 对比] JDBC 默认 autoCommit=true，需 conn.setAutoCommit(false) 开启事务。
    Python sqlite3 默认在 DML 语句前隐式开启事务，需手动 commit。
    """
    print("\n=== 事务管理 ===")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER)")
    conn.executemany("INSERT INTO accounts VALUES (?, ?)", [(1, 100), (2, 50)])
    conn.commit()

    try:
        # 转账：从账户 1 转 30 到账户 2
        conn.execute("UPDATE accounts SET balance = balance - 30 WHERE id = 1")
        conn.execute("UPDATE accounts SET balance = balance + 30 WHERE id = 2")
        # 检查余额是否为负
        balance = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
        if balance < 0:
            raise ValueError("余额不足")
        conn.commit()
        print("转账成功")
    except Exception as e:
        conn.rollback()
        print("转账失败，已回滚:", e)

    for row in conn.execute("SELECT * FROM accounts"):
        print("  账户:", row)
    conn.close()


def demo_sqlite_context():
    """上下文管理器 with conn：自动 commit 或 rollback。

    [Java 对比] Java 7+ 的 try-with-resources 自动关闭连接，
                但事务的 commit/rollback 仍需手动。Python 的 with conn 自动处理。
    """
    print("\n=== 上下文管理器 with conn ===")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")

    # with conn 退出时：无异常则 commit，有异常则 rollback
    with conn:
        conn.execute("INSERT INTO items VALUES (1, 'item1')")
        conn.execute("INSERT INTO items VALUES (2, 'item2')")
    print("with 块正常退出，已自动 commit")
    print("记录数:", conn.execute("SELECT COUNT(*) FROM items").fetchone()[0])

    # 模拟异常时自动回滚
    try:
        with conn:
            conn.execute("INSERT INTO items VALUES (3, 'item3')")
            raise RuntimeError("故意出错")
    except RuntimeError as e:
        print("with 块异常退出，已自动 rollback:", e)
    print("回滚后记录数:", conn.execute("SELECT COUNT(*) FROM items").fetchone()[0])
    conn.close()


def demo_sqlite_row_factory():
    """Row 工厂 row_factory：按列名访问结果。

    [Java 对比] JDBC 的 ResultSet 用 rs.getString("column") 按名访问。
    Python 默认返回 tuple，设置 row_factory=sqlite3.Row 后可按列名访问。
    """
    print("\n=== Row 工厂 row_factory ===")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row  # 关键：设置 Row 工厂
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice', 30)")
    conn.commit()

    row = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
    print("按索引访问:", row[0], row[1], row[2])        # tuple 风格
    print("按列名访问:", row["id"], row["name"], row["age"])  # 字典风格
    print("keys():", row.keys())                        # 列名列表
    conn.close()


def demo_sqlite_table_index():
    """创建表 / 索引。"""
    print("\n=== 创建表与索引 ===")
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL
        )
    """)
    # 创建索引加速查询
    conn.execute("CREATE INDEX idx_category ON products(category)")
    conn.execute("CREATE UNIQUE INDEX idx_name ON products(name)")
    print("表和索引创建成功")

    # 查看表结构
    for row in conn.execute("PRAGMA table_info(products)"):
        print("  列信息:", row)
    conn.close()


def demo_sqlite_executemany():
    """批量插入 executemany：比循环 execute 高效得多。

    [Java 对比] JDBC 的 PreparedStatement.addBatch() + executeBatch()。
    """
    print("\n=== 批量插入 executemany ===")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE logs (id INTEGER, msg TEXT)")

    # 准备批量数据
    data = [(i, f"message {i}") for i in range(1000)]
    # executemany 一次性插入，比 for 循环 execute 快很多
    conn.executemany("INSERT INTO logs VALUES (?, ?)", data)
    conn.commit()
    print("批量插入 1000 条，总数:", conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0])
    conn.close()


# =============================================================================
# 第五部分：tempfile 模块
# =============================================================================
# [Java 对比] Java 用 java.io.File.createTempFile() / java.nio.file.Files.createTempDirectory()
#   Python 的 tempfile 模块更安全，且支持上下文管理器自动清理。

def demo_tempfile_named():
    """NamedTemporaryFile：带名字的临时文件，可自动删除。"""
    print("\n=== NamedTemporaryFile ===")
    # delete=True（默认）退出 with 块时自动删除文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="demo_", delete=True, encoding="utf-8") as f:
        f.write("临时文件内容")
        f.flush()  # 确保写入磁盘
        print("临时文件名:", f.name)
        print("文件存在:", Path(f.name).exists())
    print("with 退出后文件存在:", Path(f.name).exists())  # False，已自动删除


def demo_tempfile_directory():
    """TemporaryDirectory：临时目录，退出时自动递归删除。"""
    print("\n=== TemporaryDirectory ===")
    with tempfile.TemporaryDirectory(prefix="demo_dir_") as tmpdir:
        print("临时目录:", tmpdir)
        # 在临时目录中创建文件
        (Path(tmpdir) / "a.txt").write_text("hello", encoding="utf-8")
        (Path(tmpdir) / "b.txt").write_text("world", encoding="utf-8")
        print("目录内容:", os.listdir(tmpdir))
    print("with 退出后目录存在:", Path(tmpdir).exists())  # False，已自动删除


def demo_tempfile_mkstemp_mkdtemp():
    """mkstemp / mkdtemp：手动管理的临时文件/目录（不自动删除）。

    [注意] mkstemp 返回的 fd 是 OS 级别的文件描述符，需 os.close(fd) 关闭。
    """
    print("\n=== mkstemp / mkdtemp ===")
    # mkstemp：返回 (fd, path)，需手动关闭 fd 和删除文件
    fd, path = tempfile.mkstemp(suffix=".tmp", prefix="manual_")
    try:
        os.write(fd, b"manual temp file")
        print("mkstemp 文件:", path)
    finally:
        os.close(fd)          # 关闭文件描述符
        os.unlink(path)       # 删除文件
    print("mkstemp 文件已删除:", not Path(path).exists())

    # mkdtemp：返回目录路径，需手动删除
    dirpath = tempfile.mkdtemp(prefix="manual_dir_")
    print("mkdtemp 目录:", dirpath)
    shutil.rmtree(dirpath)  # 手动删除
    print("mkdtemp 目录已删除:", not Path(dirpath).exists())


def demo_tempfile_practical():
    """实战：安全处理临时文件（处理完即删）。"""
    print("\n=== 实战：安全处理临时文件 ===")
    # 典型场景：下载文件 -> 处理 -> 删除
    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        # 模拟下载多个文件
        for i in range(3):
            (work / f"data_{i}.csv").write_text(f"id,value\n{i},{i*10}\n", encoding="utf-8")
        # 处理文件
        total = 0
        for f in work.glob("*.csv"):
            for line in f.read_text(encoding="utf-8").splitlines()[1:]:  # 跳过表头
                total += int(line.split(",")[1])
        print("处理完成，总和:", total)
    # 退出 with 后所有临时文件和目录自动清理


# =============================================================================
# 第六部分：shutil 模块
# =============================================================================
# [Java 对比] shutil 类似 java.nio.file.Files 的文件操作工具集，
#   但提供了更高级的 copytree / rmtree 等递归操作。

def demo_shutil_copy():
    """copy / copy2 / copytree：文件与目录复制。

    [Java 对比] Java 用 Files.copy(src, dest, REPLACE_EXISTING) 复制单文件，
                复制目录需自己递归遍历。Python 的 copytree 一行搞定。
    """
    print("\n=== shutil copy / copy2 / copytree ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "src.txt"
        src.write_text("hello", encoding="utf-8")

        # copy：复制文件内容 + 权限（不含元数据）
        dst1 = tmp / "dst_copy.txt"
        shutil.copy(str(src), str(dst1))
        print("copy:", dst1.read_text(encoding="utf-8"))

        # copy2：复制文件内容 + 权限 + 元数据（修改时间等）
        dst2 = tmp / "dst_copy2.txt"
        shutil.copy2(str(src), str(dst2))
        print("copy2 元数据 mtime:", dst2.stat().st_mtime == src.stat().st_mtime)

        # copytree：递归复制整个目录
        src_dir = tmp / "src_dir"
        src_dir.mkdir()
        (src_dir / "a.txt").write_text("a", encoding="utf-8")
        (src_dir / "sub").mkdir()
        (src_dir / "sub" / "b.txt").write_text("b", encoding="utf-8")
        dst_dir = tmp / "dst_dir"
        shutil.copytree(str(src_dir), str(dst_dir))
        print("copytree 结果:", sorted(p.name for p in dst_dir.rglob("*")))


def demo_shutil_move_rmtree():
    """move / rmtree：移动与删除目录。"""
    print("\n=== shutil move / rmtree ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "src.txt"
        src.write_text("move me", encoding="utf-8")
        # move：移动文件（同分区下是重命名，跨分区是复制+删除）
        dst = tmp / "dst.txt"
        shutil.move(str(src), str(dst))
        print("move 后 src 存在:", src.exists(), "| dst 存在:", dst.exists())

        # rmtree：递归删除目录树
        tree = tmp / "tree"
        tree.mkdir()
        (tree / "a.txt").write_text("a", encoding="utf-8")
        shutil.rmtree(str(tree))
        print("rmtree 后 tree 存在:", tree.exists())


def demo_shutil_disk_usage():
    """disk_usage：磁盘使用情况。"""
    print("\n=== shutil disk_usage ===")
    # 返回 (total, used, free)，单位字节
    usage = shutil.disk_usage("/")
    print(f"总空间: {usage.total / 1024**3:.1f} GB")
    print(f"已用: {usage.used / 1024**3:.1f} GB")
    print(f"可用: {usage.free / 1024**3:.1f} GB")
    print(f"使用率: {usage.used / usage.total * 100:.1f}%")


def demo_shutil_which():
    """which：查找命令路径（类似 Linux which 命令）。"""
    print("\n=== shutil which ===")
    # 查找 python 命令的完整路径
    python_path = shutil.which("python")
    print("python 路径:", python_path)
    # 查找 git（可能不存在）
    git_path = shutil.which("git")
    print("git 路径:", git_path if git_path else "[未找到]")
    # [Java 对比] Java 没有直接等价，需自己遍历 PATH 环境变量


# =============================================================================
# 第七部分：pathlib + os 进阶
# =============================================================================
# [Java 对比] 文件权限类似 java.nio.file.attribute.PosixFilePermissions；
#   符号链接类似 java.nio.file.Files.createSymbolicLink() / readSymbolicLink()

def demo_os_chmod():
    """文件权限 os.chmod。

    [注意] Windows 对 chmod 支持有限，主要只读标志生效；
            Linux/macOS 完整支持 rwx 权限。
    [Java 对比] Java 用 Files.setPosixFilePermissions(path, PosixFilePermissions.fromString("rwxr-xr-x"))
    """
    print("\n=== os.chmod 文件权限 ===")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    try:
        # 获取当前权限
        mode = os.stat(path).st_mode
        print(f"当前权限: {stat.filemode(mode)} ({oct(mode & 0o777)})")

        # 设置为只读
        os.chmod(path, stat.S_IREAD)
        new_mode = os.stat(path).st_mode
        print(f"只读后权限: {stat.filemode(new_mode)} ({oct(new_mode & 0o777)})")

        # 恢复读写
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    finally:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)  # 确保可删
        os.unlink(path)


def demo_path_expand():
    """路径展开 ~ 展开（用户主目录）。"""
    print("\n=== 路径展开 ~ ===")
    # os.path.expanduser 把 ~ 展开为用户主目录
    home = os.path.expanduser("~")
    print("expanduser('~') =", home)

    # pathlib 的 Path.home() 等价
    print("Path.home() =", Path.home())

    # 展开环境变量 $HOME / %USERPROFILE%
    expanded = os.path.expandvars("$HOME/tmp" if os.name != "nt" else "%USERPROFILE%\\tmp")
    print("expandvars:", expanded)


def demo_os_symlink():
    """符号链接 os.symlink / os.readlink。

    [注意] Windows 创建符号链接需要管理员权限或开发者模式，可能失败。
    [Java 对比] Files.createSymbolicLink(target, link)
    """
    print("\n=== os.symlink 符号链接 ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        target = tmp / "target.txt"
        target.write_text("I am the target", encoding="utf-8")
        link = tmp / "link.txt"
        try:
            os.symlink(str(target), str(link))
            print("符号链接创建成功:", link)
            print("readlink:", os.readlink(str(link)))
            print("通过链接读取:", link.read_text(encoding="utf-8"))
            print("is_symlink:", link.is_symlink())
        except OSError as e:
            # Windows 普通用户可能无权限创建符号链接
            print(f"[注意] 创建符号链接失败（Windows 需管理员/开发者模式）: {e}")


def demo_pathlib_batch_rename():
    """实战：批量重命名文件。"""
    print("\n=== 实战：批量重命名文件 ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # 创建测试文件
        for i in range(5):
            (tmp / f"img_{i}.png").write_bytes(b"fake image")
        print("重命名前:", sorted(p.name for p in tmp.iterdir()))

        # 批量重命名：img_0.png -> IMG_0001.png
        for f in tmp.glob("img_*.png"):
            num = int(f.stem.split("_")[1])
            new_name = f"IMG_{num:04d}.png"
            f.rename(f.parent / new_name)
        print("重命名后:", sorted(p.name for p in tmp.iterdir()))


# =============================================================================
# 第八部分：hashlib / secrets / base64 / uuid
# =============================================================================
# [Java 对比] hashlib   ~ java.security.MessageDigest
#             secrets   ~ java.security.SecureRandom + UUID.randomUUID
#             base64    ~ java.util.Base64
#             uuid      ~ java.util.UUID
#
# 这四个模块是工具类开发的刚需，且经常一起出现。


def demo_hashlib():
    """hashlib：摘要算法（对应 MessageDigest）。"""
    print("\n=== 21. hashlib 摘要算法 ===")
    import hashlib

    data = "hello world".encode("utf-8")

    # 常用算法
    print(f"  md5    = {hashlib.md5(data).hexdigest()}")
    print(f"  sha1   = {hashlib.sha1(data).hexdigest()}")
    print(f"  sha256 = {hashlib.sha256(data).hexdigest()}")
    print(f"  sha256(前 16) = {hashlib.sha256(data).hexdigest()[:16]}")

    # 统一入口 + 可用算法
    h = hashlib.new("sha256")
    h.update(data)
    print(f"  hashlib.new('sha256') = {h.hexdigest()}")
    print(f"  常用算法: {sorted(hashlib.algorithms_guaranteed)[:6]} ...")

    # 流式处理大文件（不要一次性读入内存）
    print("\n  文件摘要（流式）:")
    print("    h = hashlib.sha256()")
    print("    with open(path, 'rb') as f:")
    print("        for chunk in iter(lambda: f.read(8192), b''):")
    print("            h.update(chunk)")
    print("    h.hexdigest()")
    print("  [Java 对比] MessageDigest.getInstance(\"SHA-256\")")

    # 重要：普通 hash 不能存密码
    print("\n  [安全] 存密码不能用 sha256！需用 pbkdf2_hmac / bcrypt / argon2")
    salt = b"random_salt_16b"
    pwd_hash = hashlib.pbkdf2_hmac("sha256", b"my-password", salt, 200_000)
    print(f"  pbkdf2_hmac(迭代 20 万次) = {pwd_hash.hex()[:32]}...")
    print("  [Java 对比] PBKDF2WithHmacSHA256 或 BCryptPasswordEncoder")


def demo_secrets():
    """secrets：密码学安全的随机数（不能用 random）。"""
    print("\n=== 22. secrets 安全随机 ===")
    import secrets
    import string
    import random

    # 令牌与密码学随机值
    print(f"  token_hex(16)  = {secrets.token_hex(16)}")
    print(f"  token_urlsafe   = {secrets.token_urlsafe(16)}")
    print(f"  token_bytes     = {secrets.token_bytes(8).hex()}")
    print(f"  randbelow(100)  = {secrets.randbelow(100)}")

    # 生成安全密码
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(16))
    print(f"  安全密码        = {password}")

    # 常量时间比较（防时序攻击）
    print(f"  compare_digest  = {secrets.compare_digest('abc', 'abc')}")
    print("  [要点] secrets.compare_digest 在比较 token/签名时必用")

    print("\n  ⚠️ random 模块【不能】用于安全场景:")
    print("    random 基于 Mersenne Twister，种子可被推算，适合仿真/游戏")
    print("    secrets 基于 os.urandom（内核 CSPRNG）")
    print(f"    random 示例   = {random.random()}")
    print("  [Java 对比] secrets ~ java.security.SecureRandom（random ~ java.util.Random）")


def demo_base64():
    """base64：编码（不是加密）。"""
    print("\n=== 23. base64 编码 ===")
    import base64

    raw = b"hello world\x00\xff"
    print(f"  原始字节:        {raw!r}")
    print(f"  b64encode:       {base64.b64encode(raw).decode()}")
    print(f"  b64decode:       {base64.b64decode(base64.b64encode(raw))!r}")

    # URL 安全变体（替换 +/ 为 -_，去除填充）
    raw2 = b"\xfb\xff\xbf"
    print(f"\n  URL 安全变体:")
    print(f"    b64encode = {base64.b64encode(raw2).decode()}")
    print(f"    urlsafe   = {base64.urlsafe_b64encode(raw2).decode()}")

    # 常用场景：把二进制塞进 JSON / URL
    print("\n  [常见用途] 小图片写成 data URI、JWT payload、短信/邮件签名")
    print("  [误用] base64 是【编码】不是【加密】，任何人都能解码")
    print("        需要保密请用加密（cryptography 库的 Fernet/AES）")
    print("  [Java 对比] java.util.Base64.getEncoder() / getUrlEncoder()")


def demo_uuid():
    """uuid：通用唯一标识。"""
    print("\n=== 24. uuid ===")
    import uuid

    # uuid4：随机生成（最常用）
    u4 = uuid.uuid4()
    print(f"  uuid4()          = {u4}   (随机，最常用)")
    print(f"  str(u)           = {str(u4)}")
    print(f"  u.hex            = {u4.hex}")
    print(f"  u.int            = {str(u4.int)[:20]}...")

    # uuid1：基于时间 + MAC（可能泄露机器信息，不建议）
    u1 = uuid.uuid1()
    print(f"\n  uuid1()          = {u1}")
    print("  ⚠️ uuid1 包含 MAC 地址和时间戳，可能泄露隐私，一般不用")

    # uuid5：基于名字的确定性 UUID（同一名字总是同一 UUID）
    ns = uuid.NAMESPACE_DNS
    u5 = uuid.uuid5(ns, "example.com")
    print(f"\n  uuid5(NS_DNS, 'example.com') = {u5}")
    print("  同名字再次生成结果相同，可用于确定性 ID")

    # 解析与校验
    print(f"\n  解析: uuid.UUID('{u4}') == u4 -> {uuid.UUID(str(u4)) == u4}")
    print("  [Java 对比] java.util.UUID.randomUUID() 对应 uuid4()")


# =============================================================================
# 主入口
# =============================================================================
def main():
    """运行所有 demo。"""
    print("=" * 70)
    print("Python 标准库系统工具演示 - 面向 Java 开发者")
    print("=" * 70)

    # subprocess
    demo_subprocess_run_basic()
    demo_subprocess_capture()
    demo_subprocess_shell_warning()
    demo_subprocess_popen_pipe()
    demo_subprocess_timeout()
    demo_subprocess_input()
    demo_subprocess_env()
    demo_subprocess_git()

    # logging
    demo_logging_basic()
    demo_logging_architecture()
    demo_logging_levels()
    demo_logging_rotating()
    demo_logging_custom_formatter()
    demo_logging_hierarchy()
    demo_logging_dict_config()
    demo_logging_json()

    # argparse
    demo_argparse_basic()
    demo_argparse_positional_vs_optional()
    demo_argparse_type_default_required()
    demo_argparse_mutually_exclusive()
    demo_argparse_subparsers()
    demo_argparse_help()
    demo_argparse_cli_tool()

    # sqlite3
    demo_sqlite_connect()
    demo_sqlite_param_query()
    demo_sqlite_transaction()
    demo_sqlite_context()
    demo_sqlite_row_factory()
    demo_sqlite_table_index()
    demo_sqlite_executemany()

    # tempfile
    demo_tempfile_named()
    demo_tempfile_directory()
    demo_tempfile_mkstemp_mkdtemp()
    demo_tempfile_practical()

    # shutil
    demo_shutil_copy()
    demo_shutil_move_rmtree()
    demo_shutil_disk_usage()
    demo_shutil_which()

    # pathlib + os 进阶
    demo_os_chmod()
    demo_path_expand()
    demo_os_symlink()
    demo_pathlib_batch_rename()

    # hashlib / secrets / base64 / uuid
    demo_hashlib()
    demo_secrets()
    demo_base64()
    demo_uuid()

    print("\n" + "=" * 70)
    print("所有 demo 运行完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
