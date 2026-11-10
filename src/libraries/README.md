# 第四部分：常用类库

前几个部分讲的是 Python 语言本身；这部分把 Python 生态按领域梳理一遍——标准库、Web、数据、数据库、工具链——每个库都给出 **Java 对应物**和**关键行为差异**，帮助你把 JVM 生态的经验直接迁过来，同时避开"看着像、其实不一样"的陷阱。

## 章节导航

| 章节 | 代码文件 | 覆盖的库 | 适合什么时候看 |
|------|----------|----------|----------------|
| [标准库核心](./01-stdlib-core.md) | [`01_stdlib_core.py`](../code/libraries/01_stdlib_core.py) | `os` / `sys` / `pathlib` / `collections` / `itertools` / `functools` | 刚开始写 Python，想知道"Java 常用的这些东西在 Python 里叫什么" |
| [标准库数据处理](./02-stdlib-data.md) | [`02_stdlib_data.py`](../code/libraries/02_stdlib_data.py) | `re` / `json` / `datetime` / `enum` / `dataclasses` / `typing` | 做数据导入导出、解析文本、处理时间与配置常量 |
| [标准库系统工具](./03-stdlib-system.md) | [`03_stdlib_system.py`](../code/libraries/03_stdlib_system.py) | `subprocess` / `logging` / `argparse` / `sqlite3` / `tempfile` / `shutil` | 写运维脚本、CLI 工具、日志配置 |
| [Web 框架](./04-web-frameworks.md) | [`04_web_frameworks.py`](../code/libraries/04_web_frameworks.py) | FastAPI / Flask / Django | 要起 HTTP 服务，纠结该选哪个框架 |
| [HTTP 客户端与模板](./05-web-clients.md) | [`05_web_clients.py`](../code/libraries/05_web_clients.py) | requests / httpx / aiohttp / Jinja2 / pydantic | 调第三方 API，或需要渲染 HTML、做数据校验 |
| [数据科学](./06-data-science.md) | [`06_data_science.py`](../code/libraries/06_data_science.py) | NumPy / Pandas / Polars / Matplotlib | 做数据分析、报表、清洗表格 |
| [数据库 ORM](./07-database.md) | [`07_database.py`](../code/libraries/07_database.py) | sqlite3 / SQLAlchemy Core / SQLAlchemy ORM | 要持久化数据，或从 Hibernate 迁过来 |
| [工具链](./08-toolchain.md) | [`08_toolchain.py`](../code/libraries/08_toolchain.py) | pytest / ruff / mypy / uv / pre-commit | 给项目搭工程基建 |

## 按需求找库

| 需求 | 首选 | 备选 | Java 对应 |
|------|------|------|-----------|
| HTTP 客户端 | `httpx`（支持 async） | `requests` | HttpClient / OkHttp / RestTemplate |
| Web 框架 | FastAPI | Flask / Django | Spring Boot / Spring MVC |
| 数据校验 | pydantic | —— | Bean Validation + Jackson |
| ORM | SQLAlchemy ORM | SQLModel | JPA / Hibernate |
| 表格处理 | Pandas | Polars | Tablesaw / Spark DataFrame |
| 数值计算 | NumPy | SciPy | EJML / ND4J |
| 绘图 | Matplotlib | Seaborn / Plotly | JFreeChart |
| 测试 | pytest | unittest | JUnit 5 + AssertJ |
| Mock | `unittest.mock` / pytest-mock | —— | Mockito |
| lint + 格式化 | ruff | flake8 + black | Checkstyle + Spotless |
| 类型检查 | mypy | pyright | javac |
| 依赖管理 | uv | poetry | Maven / Gradle |
| 日志 | `logging`（标准库） | structlog / loguru | SLF4J + Logback |
| CLI 参数解析 | `argparse`（标准库） | typer / click | picocli / Commons CLI |
| 子进程 | `subprocess`（标准库） | —— | `ProcessBuilder` |
| 模板 | Jinja2 | —— | Thymeleaf / FreeMarker |
| 配置 | `tomllib` / pydantic-settings | dynaconf | Spring `@ConfigurationProperties` |

> [要点] "首选"偏向现代主流选择。标准库能解决的就用标准库——`subprocess`、`argparse`、`logging` 都是 Java 里对应第三方库才有的能力，Python 自带。

## Java 开发者最该先看的 5 个差异

### 1. pydantic 取代 Bean Validation + Jackson

Java 里校验靠 `@NotNull` / `@Min`，序列化靠 Jackson 注解，两者是**两套系统**。pydantic 用同一个模型类同时完成解析、校验、序列化：

```python
class User(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)
```

`User.model_validate_json(raw)` 一步完成反序列化 + 校验，失败抛 `ValidationError`（含逐字段错误列表）。类型注解就是校验规则——这是 Java 里注解和类型两套机制做不到的。

### 2. pytest 的断言就是 `assert`

Java 的裸 `assert` 默认被 JVM 关闭，所以必须用 AssertJ / `assertEquals`。pytest 反过来：`assert x == y` 失败时会被自动重写展开成 `assert 5.0 == 5`，直接看到两侧实际值。**不要**再去找 `assertEquals` 的对应物。

### 3. SQLAlchemy Session 的语义

- `Session` **非线程安全**，不会像容器里的 `EntityManager` 那样自动绑定到线程
- `commit()` 后对象默认 **expire**，再访问属性会重新查库
- 关系默认 **lazy**，列表页很容易踩 N+1（用 `selectinload` 解决）
- `with conn:` 是**事务**，不是关闭连接

详见 [数据库 ORM](./07-database.md)。

### 4. Pandas 要向量化，切片不是拷贝

- 不要在 `DataFrame` 上 `for` 循环 / `iterrows()`
- 切片返回视图或写时复制的浅拷贝，改子集前先 `.copy()`
- 多条件用 `&` / `|` 并加括号，`and` / `or` 会直接报错

详见 [数据科学](./06-data-science.md)。

### 5. uv / ruff 的速度

Maven 首次 `mvn install` 动辄几分钟，`uv sync` 通常**一秒内**；Checkstyle + Spotless 跑一遍几十秒，ruff 是**毫秒级**。把 ruff 放进 pre-commit 完全不烦人——这是两个生态在"开发者反馈频率"上的根本差距。

## 运行方式

每个章节对应一个可独立运行的脚本：

```bash
python src/code/libraries/06_data_science.py
python src/code/libraries/07_database.py
python src/code/libraries/08_toolchain.py
```

> [要点] 脚本对**未安装的第三方库会优雅跳过**：某段 demo 检测到 `ImportError` 就打印安装提示并返回，其余部分照常运行，`exit code` 仍是 0。所以即使只有标准库，也能把全部示例跑一遍看输出。

安装第三方库以便看到完整输出：

```bash
pip install numpy pandas polars matplotlib sqlalchemy pytest ruff mypy
```

> 📁 [第四部分代码目录](../code/libraries/)
