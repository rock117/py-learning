# 其他实用特性

本章讲解 Python 标准库中一些实用的"杂项"特性：pickle 序列化、sqlite3 内置数据库、
logging 日志框架、argparse CLI 解析、配置文件读取、`__future__` 和 weakref 弱引用。

## pickle：序列化

`pickle` 是 Python 的对象序列化模块，类似 Java 的 `Serializable`。

```python
data = pickle.dumps(user)     # 序列化成 bytes
restored = pickle.loads(data) # 反序列化

pickle.dump(user, f)  # 写入文件
user = pickle.load(f) # 从文件读取
```

> [pickle 序列化与安全警告](../code/advanced/13_misc.py#L50-L81)

```python
{{#include ../code/advanced/13_misc.py:50:81}}
```

### 安全警告

**`pickle.loads` 能执行任意代码！** 永远不要 `pickle.loads` 不可信来源的数据。
Java 的 `Serializable` 也有类似风险（`readObject` 漏洞）。替代方案：用 JSON 处理不可信数据。

### Java 对比

| Python pickle | Java Serializable | 说明 |
|---------------|------------------|------|
| `dumps` / `loads` | `ObjectOutputStream` / `ObjectInputStream` | 序列化/反序列化 |
| 能执行任意代码 | `readObject` 漏洞 | 安全风险 |
| 内置，无需实现接口 | 需实现 `Serializable` | 门槛更低 |

## sqlite3：内置数据库

Python 内置 `sqlite3` 模块，零依赖，无需安装驱动。

```python
conn = sqlite3.connect(":memory:")  # 内存数据库

# 参数化查询，防 SQL 注入
conn.executemany(
    "INSERT INTO users (name, age) VALUES (?, ?)",
    [("Alice", 30), ("Bob", 25)],
)

# row_factory 让查询结果像字典
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT * FROM users WHERE name = ?", ("Alice",)).fetchone()
print(row["name"], row["age"])

# with 语句自动 commit/rollback
with conn:
    conn.execute("INSERT INTO users VALUES ('Dave', 40)")
```

> [sqlite3 内置数据库完整示例](../code/advanced/13_misc.py#L82-L134)

```python
{{#include ../code/advanced/13_misc.py:82:134}}
```

### Java 对比

| Python sqlite3 | Java | 说明 |
|----------------|------|------|
| 内置 `sqlite3` 模块 | JDBC + SQLite JDBC 驱动 jar | Python 零依赖 |
| `?` 参数化 | `PreparedStatement` | 防 SQL 注入 |
| `conn.row_factory = Row` | 无直接对应 | 字典式访问 |
| `with conn` 自动事务 | 手动 commit/rollback | 事务管理 |

## logging：日志框架

Python 的 `logging` 模块与 Java `java.util.logging` 结构几乎一致。

```python
logger = logging.getLogger("demo")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))
logger.addHandler(handler)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告")
logger.error("错误")
logger.critical("严重")
```

> [logging 日志框架配置与各级别](../code/advanced/13_misc.py#L135-L171)

```python
{{#include ../code/advanced/13_misc.py:135:171}}
```

### Java 对比

| Python logging | Java java.util.logging | 说明 |
|----------------|------------------------|------|
| `Logger` | `Logger` | 日志记录器 |
| `StreamHandler` | `ConsoleHandler` | 输出处理器 |
| `Formatter` | `Formatter` | 格式化 |
| DEBUG/INFO/WARNING/ERROR/CRITICAL | FINE/FINER/FINEST/INFO/WARNING/SEVERE | 级别 |

## argparse：CLI 参数解析

`argparse` 是 Python 内置的命令行参数解析器，自动生成 `--help`。

```python
parser = argparse.ArgumentParser(prog="mytool", description="示例工具")
parser.add_argument("input", help="输入文件路径")
parser.add_argument("-o", "--output", default="out.txt")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("-n", "--count", type=int, default=1)

group = parser.add_mutually_exclusive_group()
group.add_argument("--fast", action="store_true")
group.add_argument("--safe", action="store_true")
```

> [argparse CLI 参数解析](../code/advanced/13_misc.py#L172-L205)

```python
{{#include ../code/advanced/13_misc.py:172:205}}
```

### Java 对比

| Python argparse | Java | 说明 |
|-----------------|------|------|
| `ArgumentParser` | Commons CLI / picocli | CLI 解析 |
| `add_argument` | `Option` / `@Option` | 定义参数 |
| 互斥组 | picocli 互斥 | 互斥参数 |
| 自动 `--help` | 需手动实现 | 帮助信息 |

## configparser / tomllib：配置文件

### configparser：INI 格式

```python
config = configparser.ConfigParser()
config.read_string("""
[database]
host = localhost
port = 5432
""")
config['database']['host']       # "localhost"
config.getint('database', 'port') # 5432
```

> [configparser 读取 INI 配置](../code/advanced/13_misc.py#L206-L237)

```python
{{#include ../code/advanced/13_misc.py:206:237}}
```

### tomllib：TOML 格式 (3.11+)

```python
import tomllib  # 3.11+ 内置
data = tomllib.loads(toml_text)
data['project']['name']
```

> [tomllib 读取 TOML 配置](../code/advanced/13_misc.py#L238-L265)

```python
{{#include ../code/advanced/13_misc.py:238:265}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `configparser` (INI) | `java.util.Properties` | 但 Properties 不支持分段 |
| `tomllib` (TOML) | 无内置 | TOML 是 pyproject.toml 格式 |

## __future__：提前启用未来特性

`__future__` 让旧版本 Python 提前用上未来版本的行为。

```python
from __future__ import annotations  # 注解延迟求值（变成字符串）
```

> [__future__ 提前启用未来特性](../code/advanced/13_misc.py#L266-L284)

```python
{{#include ../code/advanced/13_misc.py:266:284}}
```

### Java 对比

Java 新特性直接在 JDK 版本启用，没有 `__future__` 机制。Python 的 `from __future__ import annotations`
让所有注解变成字符串（延迟求值），好处是前向引用不用引号，运行时性能更好。

## weakref.finalize：弱引用终结器

`weakref.finalize` 在对象被 GC 时调用注册的回调，比 `__del__` 更灵活可控。

```python
obj = Resource("file-handle")
finalizer = weakref.finalize(obj, cleanup, "file-handle")
# obj 被 GC 时自动调用 cleanup("file-handle")
del obj
```

> [weakref.finalize 弱引用终结器](../code/advanced/13_misc.py#L294-L328)

```python
{{#include ../code/advanced/13_misc.py:294:328}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `weakref.finalize` | `Cleaner` / `PhantomReference` | 对象终结 |
| `__del__` | `Object.finalize()`（已废弃） | 旧方案 |
| 可注册多个、可取消 | Cleaner 可注册多个 | 灵活性 |

## WeakValueDictionary：弱引用字典

```python
wvd = weakref.WeakValueDictionary()
a = Big(1)
wvd["a"] = a
del a  # 删除强引用后，字典条目自动移除
```

> [WeakValueDictionary 弱引用字典](../code/advanced/13_misc.py#L329-L352)

```python
{{#include ../code/advanced/13_misc.py:329:352}}
```

### Java 对比

`WeakHashMap` 是 Java 的对应。用途：缓存，避免内存泄漏（对象不用时自动清理）。

## 实战：带日志和配置的小工具

综合运用 configparser 配置 + logging 日志 + 业务逻辑：

> [带日志和配置的迷你工具](../code/advanced/13_misc.py#L353-L398)

```python
{{#include ../code/advanced/13_misc.py:353:398}}
```

这个小工具组合了配置读取、日志记录和业务逻辑，展示了这些特性的实际协作方式。

## 小结

- `pickle`：序列化，但绝不 `loads` 不可信数据（能执行任意代码）
- `sqlite3`：内置零依赖数据库，JDBC 不用装驱动
- `logging`：与 `java.util.logging` 结构一致的日志框架
- `argparse`：强大的 CLI 解析，自动生成 `--help`
- `configparser` / `tomllib`：INI / TOML 配置文件读取
- `__future__`：提前启用未来版本特性
- `weakref.finalize`：可控的对象终结回调（替代 `__del__`）

> 📁 [查看完整代码](../code/advanced/13_misc.py)
