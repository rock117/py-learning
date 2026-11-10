# 标准库系统工具

本章覆盖 Python 与操作系统打交道的一整套模块：`subprocess`、`logging`、`argparse`、`sqlite3`、`tempfile`、`shutil`，
以及 `pathlib` / `os` 的进阶用法（权限、符号链接、批量重命名）。
它们分别对应 Java 的 `ProcessBuilder`、SLF4J/logback、picocli、JDBC、`Files.createTempFile`、`java.nio.file.Files`。

## 总览：Python ↔ Java 对应表

| Python 模块 | Java 对应 | 用途 / 关键差异 |
|-------------|-----------|-----------------|
| `subprocess` | `ProcessBuilder` | 默认不经 shell，捕获输出一行搞定 |
| `logging` | SLF4J + logback / JUL | 自带实现，`dictConfig` ≈ `logback.xml` |
| `argparse` | picocli / Commons CLI | 命令式 API，自动生成 `--help` |
| `sqlite3` | JDBC + SQLite 驱动 | 驱动内置，`with conn` 自动管理事务 |
| `tempfile` | `Files.createTempFile` | 上下文管理器退出即删 |
| `shutil` | `Files` + 手写递归 | `copytree` / `rmtree` 一行递归 |
| `os` / `pathlib` 进阶 | `PosixFilePermissions`、`createSymbolicLink` | 权限在 Windows 上几乎无效 |

> [示例](../code/libraries/03_stdlib_system.py)

## subprocess：子进程管理

Java 启动进程需要 `ProcessBuilder.start()` → 读 `InputStream` → `waitFor()`，还得注意读流不能阻塞。
Python 的 `subprocess.run` 把这三步合成了一次调用：

> [run 基本用法](../code/libraries/03_stdlib_system.py#L44-L65)

```python
{{#include ../code/libraries/03_stdlib_system.py:44:65}}
```

```python
result = subprocess.run(
    [sys.executable, "--version"],   # 列表形式：参数逐个传递，不经 shell
    capture_output=True, text=True,  # 同时捕获 stdout/stderr，以 str 而非 bytes 返回
)
result.returncode, result.stdout, result.stderr
```

| 参数 | 等价 Java | 说明 |
|------|-----------|------|
| `capture_output=True` | 手动读 `getInputStream()` | 自动读取，**不会死锁** |
| `text=True` | `new String(bytes, charset)` | 默认 `False`，拿到的是 `bytes` |
| `check=True` | 判断 `exitValue()` | 非 0 返回码直接抛 `CalledProcessError` |
| `input="..."` | `getOutputStream().write(...)` | 自动写入并关闭 stdin |
| `timeout=5` | `waitFor(5, SECONDS)` | 超时抛 `TimeoutExpired` |

> ⚠️ `text=True` 默认用**系统编码**解码输出，Windows 上子进程输出 UTF-8 中文时可能抛 `UnicodeDecodeError`，
> 需要显式传 `encoding="utf-8"`。不传 `check=True` 时，**命令失败不会抛异常**，只是 `returncode != 0`。

### 管道、shell 注入与 env

> [capture 演示](../code/libraries/03_stdlib_system.py#L68-L83) ·
> [shell 警告演示](../code/libraries/03_stdlib_system.py#L86-L104) ·
> [Popen 管道演示](../code/libraries/03_stdlib_system.py#L107-L130) ·
> [timeout 演示](../code/libraries/03_stdlib_system.py#L133-L149) ·
> [input 演示](../code/libraries/03_stdlib_system.py#L152-L166) ·
> [env 演示](../code/libraries/03_stdlib_system.py#L169-L188) ·
> [git 实战](../code/libraries/03_stdlib_system.py#L191-L223)

```python
{{#include ../code/libraries/03_stdlib_system.py:191:223}}
```

```python
subprocess.run("echo hello & echo world", shell=True)     # 危险：交给 shell 解释
subprocess.run(["echo", "hello"])                        # 安全：OS 直接 exec
subprocess.run([...], input="hello\n", capture_output=True, text=True)   # 自动写 stdin 并关闭

p1 = subprocess.Popen([...], stdout=subprocess.PIPE, text=True)
p2 = subprocess.Popen([...], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
p1.stdout.close()               # 关键：不关闭会导致 p2 永远等不到 EOF
out, _ = p2.communicate()

my_env = os.environ.copy()      # env= 是【替换】而非追加，必须先 copy
my_env["MY_CUSTOM_VAR"] = "secret"
subprocess.run([...], env=my_env, timeout=5)   # 超时抛 TimeoutExpired，也会自动 kill
```

> ⚠️ 三个 Java 开发者必踩的坑：
> 1. **管道死锁**：Java 里「等子进程结束再读流」是经典 bug（缓冲区写满，子进程阻塞）。`run` 内部用
>    `communicate()` 规避了，但手动 `Popen` + `stdout=PIPE` 又忘了 `communicate()` 时**同样会死锁**。
>    连接两个进程的管道在 Java 要开两个线程搬运字节，Python 只需 `p1.stdout` 塞给 `p2.stdin` +
>    `p1.stdout.close()`（否则两个进程互等对方的 EOF）。
> 2. **`shell=True` 就是 `Runtime.exec(String)`**：有命令注入风险。安全做法只有一条——用列表形式，
>    永远不要把用户输入拼进字符串。
> 3. **`env=` 是替换**：Java 的 `ProcessBuilder.environment()` 返回的 Map 是继承来的，改一个 key 就够；
>    Python 里必须自己 `os.environ.copy()` 再改，否则子进程连 `PATH` 都没有。

## logging：日志

架构与 Java 高度对应，但**没有门面/实现分离**：`logging` 既是门面又是实现，不需要 SLF4J 那样的绑定。

| Python | Java 对应 |
|--------|-----------|
| `Logger` / `Handler` / `Formatter` | `Logger` / `Appender` / `Layout`（logback） |
| `dictConfig` / `RotatingFileHandler` | `logback.xml` / `RollingFileAppender` |
| `getLogger(__name__)` | `LoggerFactory.getLogger(Foo.class)` |

### basicConfig 与级别

> [basicConfig 演示](../code/libraries/03_stdlib_system.py#L225-L245) ·
> [级别演示](../code/libraries/03_stdlib_system.py#L285-L308)

```python
{{#include ../code/libraries/03_stdlib_system.py:285:308}}
```

```python
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", force=True)
logger = logging.getLogger("demo")    # 慎用 root logger
```

| Python | 数值 | JUL 对应 |
|--------|------|----------|
| `CRITICAL` / `ERROR` | 50 / 40 | `SEVERE` |
| `WARNING` / `INFO` / `DEBUG` | 30 / 20 / 10 | `WARNING` / `INFO` / `FINE` |
| `NOTSET` | 0 | —— |

> ⚠️ `basicConfig()` **只在 root 没有任何 handler 时生效**，第二次调用被静默忽略（这就是「为什么我改了 level 没反应」）。
> 3.8+ 用 `force=True` 强制覆盖。格式符是 `%s` 风格（`logger.info("x=%s", x)`）而**不是 f-string**：
> f-string 会在调用前就完成拼接，即使该日志最终被过滤掉也要付出代价。日志**默认走 stderr**。

### Logger / Handler / Formatter 三层

> [架构演示](../code/libraries/03_stdlib_system.py#L248-L282) ·
> [层级演示](../code/libraries/03_stdlib_system.py#L374-L396)

```python
{{#include ../code/libraries/03_stdlib_system.py:374:396}}
```

```python
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
logger.propagate = False              # 不向父 logger 冒泡
console = logging.StreamHandler()
console.setLevel(logging.INFO)        # handler 也有自己的级别（第二个过滤层）
console.setFormatter(logging.Formatter("[控制台] %(levelname)s: %(message)s"))
file = logging.FileHandler(path, encoding="utf-8")
logger.addHandler(console); logger.addHandler(file)
```

> ⚠️ **`propagate` 是 Python 独有的概念**（log4j2 的 additivity 与之类似）。日志会沿点分命名向父 logger
> 冒泡，而每个 handler 都各自输出一次——于是「控制台出现两遍日志」。排查顺序永远是：
> `handlers` 有没有重复、`propagate` 是不是该关。另外 `getLogger()` 是**全局单例**，重复 `addHandler` 会累积。

### 滚动日志、Formatter 与 dictConfig

> [滚动日志演示](../code/libraries/03_stdlib_system.py#L311-L345) ·
> [自定义 Formatter 演示](../code/libraries/03_stdlib_system.py#L348-L371) ·
> [dictConfig 演示](../code/libraries/03_stdlib_system.py#L399-L439) ·
> [JSON 日志演示](../code/libraries/03_stdlib_system.py#L442-L483)

```python
{{#include ../code/libraries/03_stdlib_system.py:442:483}}
```

```python
from logging.handlers import RotatingFileHandler
RotatingFileHandler(path, maxBytes=1024, backupCount=3, encoding="utf-8")
class JsonFormatter(logging.Formatter):   # 对应 logstash-logback-encoder，便于 ELK 采集
    def format(self, record):
        return json.dumps({...}, ensure_ascii=False)
```

> ⚠️ `RotatingFileHandler` 在多进程下**不安全**（多进程会同时滚动同一文件），logback 有 `prudent` 模式，
> Python 需要第三方库或改 `WatchedFileHandler` + 外部 logrotate。
> `dictConfig` 默认 `disable_existing_loggers=True`，会把 import 阶段建好的库 logger 静默禁用，**务必写 `False`**。

## argparse：命令行解析

对应 picocli，但风格是**命令式**的：picocli 用注解声明字段，argparse 用 `add_argument()` 调用。

| argparse | picocli | 说明 |
|----------|---------|------|
| `add_argument("path")` | `@Parameters` | 位置参数，必填 |
| `add_argument("-n", "--name")` | `@Option` | 可选参数 |
| `action="store_true"` | `boolean` 标志 | 出现即为 `True` |
| `type=int` / `choices=[1,2,3]` | `type=Integer.class` | 转换函数，失败会报错 |
| `nargs="+"` | `arity = "1..*"` | 至少一个 |
| `add_subparsers()` | `@Command(subcommands=...)` | 子命令 |
| `add_mutually_exclusive_group()` | `@ArgGroup(exclusive=true)` | 互斥 |

### 基础参数、互斥组与子命令

> [基础参数演示](../code/libraries/03_stdlib_system.py#L485-L508) ·
> [位置 vs 可选](../code/libraries/03_stdlib_system.py#L511-L530) ·
> [type / default / required 演示](../code/libraries/03_stdlib_system.py#L533-L549) ·
> [互斥组演示](../code/libraries/03_stdlib_system.py#L552-L570) ·
> [子命令演示](../code/libraries/03_stdlib_system.py#L573-L595) ·
> [help 演示](../code/libraries/03_stdlib_system.py#L598-L611) ·
> [CLI 工具实战](../code/libraries/03_stdlib_system.py#L614-L657)

```python
{{#include ../code/libraries/03_stdlib_system.py:614:657}}
```

```python
parser.add_argument("-n", "--name", type=str, default="World")
parser.add_argument("action")                          # 位置参数
parser.add_argument("--port", type=int, required=True) # 可选参数但必填
args = parser.parse_args([...])   # 传 None 则读 sys.argv[1:]

group = parser.add_mutually_exclusive_group()
group.add_argument("--verbose", action="store_true")
group.add_argument("--quiet", action="store_true")

subparsers = parser.add_subparsers(dest="command")
subparsers.add_parser("add", help="添加文件").add_argument("files", nargs="+")
parser.format_help()      # 拿到 help 文本而不退出（便于截图 / 测试）
```

> ⚠️ 「带 `-` 的是可选参数」并不意味着「可以省略」——`required=True` 能让可选参数变必填；反过来，
> 位置参数也不能靠 `required=` 控制。`parse_args()` 失败时**直接 `sys.exit(2)`**，不是可捕获的业务异常，
> 单测里要传参而不是去 catch。
>
> `dest="command"` 是子命令的关键：它把选中的子命令名存进 `args.command`；不写 `dest` 就无法知道选了哪个，
> 写了但用户没选子命令时 `args.command` 是 `None` 而非报错。`--help` / `-h` 与 `usage` 都是自动生成的，
> 这点和 picocli 一样；实战里通常把 `main()` 写成 `args = parser.parse_args(); return handle(args)`，
> 让解析与业务完全分离，方便测试。

## sqlite3：嵌入式数据库

Python 自带 SQLite 驱动，等价于「JDBC + sqlite-jdbc 依赖」，但无需任何 Maven 坐标。

| sqlite3 | JDBC |
|---------|------|
| `connect(":memory:")` | `DriverManager.getConnection(...)` |
| `conn.execute(sql, params)` / `cursor()` | `PreparedStatement.execute()` / `Statement` |
| `executemany(sql, rows)` / `commit()` | `addBatch()` + `executeBatch()` / `commit()` |
| `row_factory = sqlite3.Row` | `ResultSet.getString("col")` |

### 连接、参数化查询与事务

> [连接演示](../code/libraries/03_stdlib_system.py#L659-L675) ·
> [参数化查询演示](../code/libraries/03_stdlib_system.py#L678-L702) ·
> [事务演示](../code/libraries/03_stdlib_system.py#L705-L733) ·
> [上下文管理器演示](../code/libraries/03_stdlib_system.py#L736-L761) ·
> [Row 工厂演示](../code/libraries/03_stdlib_system.py#L764-L781) ·
> [表与索引演示](../code/libraries/03_stdlib_system.py#L784-L804) ·
> [executemany 演示](../code/libraries/03_stdlib_system.py#L807-L829)

```python
{{#include ../code/libraries/03_stdlib_system.py:807:829}}
```

```python
conn = sqlite3.connect(":memory:")
conn.execute("SELECT * FROM users WHERE name = ?", (name,))   # ⚠️ 单参数也要用 tuple
conn.executemany("INSERT INTO logs VALUES (?, ?)", [(i, f"msg {i}") for i in range(1000)])
with conn:                      # 正常退出 → commit；异常退出 → rollback（但不 close！）
    conn.execute("INSERT INTO items VALUES (1, 'item1')")
conn.row_factory = sqlite3.Row
row["name"]                     # 按列名取值，等价 rs.getString("name")
```

> ⚠️ **永远不要用 f-string 拼 SQL**，请用 `?` 占位符——这是 Python 版的 `PreparedStatement`；
> 只传一个参数时必须写 `(name,)`，写成 `(name)` 会被当成普通括号。`executemany` 比循环 `execute` 快得多，
> 但**仍然在同一个事务里**，不 `commit()` 就丢。占位符只有 `?` 和 `:name`，**不支持** MySQL 的 `%s`。
>
> 事务语义与 JDBC 相反：**JDBC 默认 `autoCommit=true`，sqlite3 默认 `isolation_level=""`**，
> 即 DML 前会**隐式开启事务**，不 `commit()` 就不落盘，而 DDL / SELECT 并不总是自动提交。
>
> `with conn` **只管理事务，不关闭连接**！Java 的 try-with-resources 是「关闭资源」，
> 这里退出 with 后 `conn` 仍然可用，必须自己 `conn.close()`。`cursor` 并不是上下文管理器。

## tempfile：临时文件

| tempfile | Java |
|----------|------|
| `NamedTemporaryFile()` | `Files.createTempFile()`（不自动删） |
| `TemporaryDirectory()` | `Files.createTempDirectory()` 需自己 `delete` |
| `mkstemp()` / `mkdtemp()` | 返回 fd+path / path，需手动清理 |

> [NamedTemporaryFile 演示](../code/libraries/03_stdlib_system.py#L831-L840) ·
> [TemporaryDirectory 演示](../code/libraries/03_stdlib_system.py#L843-L852) ·
> [mkstemp 演示](../code/libraries/03_stdlib_system.py#L855-L875) ·
> [实战演示](../code/libraries/03_stdlib_system.py#L878-L900)

```python
{{#include ../code/libraries/03_stdlib_system.py:878:900}}
```

```python
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=True, encoding="utf-8") as f:
    f.write("内容"); f.flush()      # flush 后才能从另一个句柄读到
# 退出 with：文件自动删除
```

> ⚠️ `delete=True` 的 `NamedTemporaryFile` 在 **Windows 上文件被打开期间无法被再次打开**（文件锁），
> 所以「写完后用 `open(f.name)` 再读一遍」在 Linux 能跑通、Windows 会 `PermissionError`。
> 需要跨平台就 `delete=False` 后自己删，或在 with 内部用 `f.seek(0)` 读。

## shutil：高级文件操作

> [copy / copy2 / copytree 演示](../code/libraries/03_stdlib_system.py#L902-L932) ·
> [move / rmtree 演示](../code/libraries/03_stdlib_system.py#L935-L952) ·
> [disk_usage 演示](../code/libraries/03_stdlib_system.py#L955-L963) ·
> [which 演示](../code/libraries/03_stdlib_system.py#L966-L982)

```python
{{#include ../code/libraries/03_stdlib_system.py:966:982}}
```

```python
shutil.copy(src, dst)         # 内容 + 权限位，不保留时间戳
shutil.copy2(src, dst)        # 额外保留元数据（mtime 等）≈ Files.copy + COPY_ATTRIBUTES
shutil.copytree(src_dir, dst_dir)    # 递归，一行搞定
shutil.move(src, dst)         # 同分区 rename，跨分区 copy+delete
shutil.rmtree(tree)           # 递归删除；无对应 Java API，需手写递归
```

> ⚠️ `copytree` 目标目录**必须不存在**，否则抛 `FileExistsError`；`rmtree` 删除不存在的路径会抛
> `FileNotFoundError`。作为脚本工具时要自己加 `ignore_errors=True` 或 `exist_ok=True`。

## os / pathlib 进阶

> [chmod 演示](../code/libraries/03_stdlib_system.py#L984-L1008) ·
> [路径展开演示](../code/libraries/03_stdlib_system.py#L1011-L1023) ·
> [符号链接演示](../code/libraries/03_stdlib_system.py#L1026-L1046) ·
> [批量重命名演示](../code/libraries/03_stdlib_system.py#L1049-L1069)

```python
{{#include ../code/libraries/03_stdlib_system.py:1049:1069}}
```

```python
os.chmod(path, stat.S_IREAD)                  # 只读；stat.filemode() 显示为 '-r--r--r--'
os.path.expanduser("~")                       # 展开主目录，等价 Path.home()
os.symlink(target, link)                      # Windows 需管理员或开发者模式
for f in tmp.glob("img_*.png"):               # 批量重命名：目标名不能与已有文件冲突
    f.rename(f.parent / f"IMG_{num:04d}.png")
```

| 操作 | Python | Java |
|------|--------|------|
| 改权限 | `os.chmod(p, 0o644)` | `Files.setPosixFilePermissions(...)` |
| 用户主目录 | `Path.home()` | `System.getProperty("user.home")` |
| 符号链接 | `os.symlink(t, l)` / `os.readlink(l)` | `Files.createSymbolicLink` / `readSymbolicLink` |
| 批量重命名 | `Path.rename()` 循环 | `Files.move()` 循环 |

> ⚠️ Windows 上 `os.chmod` **只支持切换只读位**，传入 `0o644` 基本无效；创建符号链接需要管理员权限或
> 开发者模式，否则抛 `OSError`——所以跨平台脚本必须 `try/except OSError` 兜底，而不是「代码写得不够稳」。

## 小结

- **`subprocess` 默认不经 shell**：用列表传参；`text=True`、`check=True` 是必备项；`env=` 是**替换**不是追加
- **不让子进程死锁**：用 `run`/`communicate()`，手动 `Popen` 时要 `p1.stdout.close()`
- **`logging.basicConfig` 只生效一次**、默认走 stderr、`propagate` 会造成重复输出；
  logger 和 handler 的 level 是**两个独立过滤层**
- **argparse 的「可选参数」不等于「可省略」**；解析失败会 `sys.exit(2)`；`dest` 决定子命令落到哪个属性
- **sqlite3 事务语义与 JDBC 相反**：DML 前隐式开启事务；`with conn` 只管事务，不管关闭；单参数也要写 `(x,)`
- **`NamedTemporaryFile(delete=True)` 在 Windows 上有文件锁**，别在 with 内二次打开同名文件
- **`copytree` 目标不能已存在**；`chmod` / `symlink` 在 Windows 上能力有限，务必 try/except

> 📁 [查看完整代码](../code/libraries/03_stdlib_system.py)
