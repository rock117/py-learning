# 最佳实践

"Pythonic"不是玄学，而是社区沉淀的编码习惯。本章覆盖 Pythonic 写法、代码风格、错误处理、项目结构、测试、日志、配置和文档规范，帮你写出专业级的 Python 代码。

## Java 对比总览

| Python 最佳实践 | Java 对应 | 说明 |
|-----------------|-----------|------|
| PEP 8 + ruff | Google Java Style + Checkstyle | 代码风格 |
| 类型注解 + mypy | Java 类型系统 | 静态检查 |
| pytest | JUnit 5 | 测试框架 |
| logging | SLF4J / Logback | 日志 |
| pydantic-settings | Spring `@ConfigurationProperties` | 配置管理 |
| EAFP（先做再说） | LBYL（先检查再做） | 错误处理风格 |

## Pythonic 写法

Pythonic 的核心：用语言提供的惯用语法，而不是把 Java 写法逐行翻译。

### enumerate / zip / unpacking

> [Pythonic 语法示例](../code/practice/02_best_practices.py#L33-L54)

```python
{{#include ../code/practice/02_best_practices.py:33:54}}
```

| Java 写法 | Pythonic 写法 | 说明 |
|-----------|-------------|------|
| `for (int i=0; i<list.size(); i++)` | `for i, v in enumerate(list)` | 带索引遍历 |
| `for (int i=0; i<a.size(); i++)` + `a.get(i)` + `b.get(i)` | `for x, y in zip(a, b)` | 并行遍历 |
| `Point p = new Point(x, y); int x = p.x;` | `x, y = point` | 解包 |

### 海象运算符（walrus operator `:=`）

Python 3.8+ 的赋值表达式，在条件/循环中同时赋值和判断：

> [海象运算符示例](../code/practice/02_best_practices.py#L128-L169)

```python
{{#include ../code/practice/02_best_practices.py:128:169}}
```

```python
# 传统写法：读取两行
line = f.readline()
while line:
    process(line)
    line = f.readline()

# 海象运算符：一行搞定
while (line := f.readline()):
    process(line)
```

## 代码风格：PEP 8 / ruff / 类型注解

### PEP 8 与 ruff

PEP 8 是 Python 的代码风格指南，对应 Java 的 Google Java Style Guide。

`ruff` 是现代的 linter + formatter（用 Rust 编写），替代 `flake8` + `isort` + `black`：

> [ruff 配置示例](../code/practice/02_best_practices.py#L297-L315)

```python
{{#include ../code/practice/02_best_practices.py:297:315}}
```

| 工具 | Java 对应 | 用途 |
|------|-----------|------|
| `ruff` | Checkstyle / SpotBugs | lint + format |
| `mypy` / `pyright` | Java 编译器类型检查 | 静态类型检查 |
| `black`（已被 ruff format 替代） | google-java-format | 代码格式化 |

### 类型注解

类型注解是 Python 工程化的基石，对应 Java 的静态类型系统。Python 3.9+ 内置泛型（`list[int]` 而非 `List[int]`）：

> [类型注解示例](../code/practice/02_best_practices.py#L264-L294)

```python
{{#include ../code/practice/02_best_practices.py:264:294}}
```

## 错误处理：EAFP vs LBYL

Python 社区推崇 **EAFP**（Easier to Ask Forgiveness than Permission，先做再说），
而 Java 更常用 **LBYL**（Look Before You Leap，先检查再做）：

> [EAFP vs LBYL](../code/practice/02_best_practices.py#L339-L369)

```python
{{#include ../code/practice/02_best_practices.py:339:369}}
```

| 风格 | Java 典型 | Python 典型 | 说明 |
|------|-----------|-------------|------|
| LBYL | `if (map.containsKey(k))` | `if k in d:` | 先检查再操作 |
| EAFP | `try { map.get(k) }` | `try: d[k] except KeyError` | 先操作，捕获异常 |

EAFP 在 Python 中更优的原因：
- 避免 TOCTOU（检查与使用之间的竞态）
- 异常处理在 Python 中开销很小（不像 Java 历史上异常昂贵）

### 精确异常与异常链

> [精确异常处理](../code/practice/02_best_practices.py#L372-L401)

```python
{{#include ../code/practice/02_best_practices.py:372:401}}
```

- 捕获**精确的异常类型**，不要裸 `except:`
- 用 `raise ... from ...` 保留异常链，对应 Java 的 `cause`
- 不要吞异常（`except: pass`）

## 项目结构：src layout

> [项目结构示例](../code/practice/02_best_practices.py#L518-L544)

```python
{{#include ../code/practice/02_best_practices.py:518:544}}
```

Python 推荐用 **src layout**（源码放在 `src/` 下），避免导入测试时的路径污染：

```
my_project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── ...
├── tests/
├── pyproject.toml
└── README.md
```

| Python | Java | 说明 |
|--------|------|------|
| `src/` layout | `src/main/java/` | 源码目录 |
| `__init__.py` | `package-info.java` | 包标识 |
| `pyproject.toml` | `pom.xml` / `build.gradle` | 项目配置 |
| `tests/` | `src/test/java/` | 测试目录 |

## 测试：pytest fixtures / parametrize

`pytest` 是 Python 的事实标准测试框架，对应 Java JUnit 5：

> [pytest 示例](../code/practice/02_best_practices.py#L616-L627)

```python
{{#include ../code/practice/02_best_practices.py:616:627}}
```

| pytest 特性 | JUnit 5 对应 | 说明 |
|-------------|-------------|------|
| `@pytest.fixture` | `@BeforeEach` / `@TestInstance` | 测试夹具 |
| `@pytest.mark.parametrize` | `@ParameterizedTest` | 参数化测试 |
| `assert` | `assertEquals` / `assertTrue` | 断言（无需记忆方法名） |
| `conftest.py` | 无直接对应 | 共享 fixture |

pytest 的 `assert` 是最大优势：直接写 `assert x == y`，失败时自动显示两边值，不需要记 `assertEquals`。

## 日志：logging 配置 / 结构化日志

> [logging 配置示例](../code/practice/02_best_practices.py#L714-L737)

```python
{{#include ../code/practice/02_best_practices.py:714:737}}
```

| Python logging | Java SLF4J/Logback | 说明 |
|----------------|-------------------|------|
| `logging.getLogger(__name__)` | `LoggerFactory.getLogger(...)` | 获取 logger |
| `logging.basicConfig` | `logback.xml` | 基础配置 |
| `dictConfig` | `logback.xml` | 结构化配置 |
| `structlog`（第三方） | 结构化日志库 | JSON/键值对日志 |

关键实践：
- 用 `__name__` 作为 logger 名，自动按模块分级
- 不要用 `print` 做日志，用 `logging`
- 生产环境用结构化日志（JSON），方便 ELK 采集

## 配置管理：环境变量 / .env / pydantic-settings

> [配置管理示例](../code/practice/02_best_practices.py#L800-L821)

```python
{{#include ../code/practice/02_best_practices.py:800:821}}
```

| Python | Java | 说明 |
|--------|------|------|
| `os.environ` | `System.getenv()` | 环境变量 |
| `python-dotenv` | Spring `@PropertySource` | .env 文件加载 |
| `pydantic-settings` | Spring `@ConfigurationProperties` | 类型安全配置 |

`pydantic-settings` 是现代 Python 配置管理的最佳实践：自动从环境变量读取、类型校验、默认值、嵌套配置。

## 文档：docstring 规范

> [docstring 规范示例](../code/practice/02_best_practices.py#L891-L928)

```python
{{#include ../code/practice/02_best_practices.py:891:928}}
```

| 风格 | Java 对应 | 特点 |
|------|-----------|------|
| Google style | Javadoc | 简洁，推荐 |
| NumPy style | 无 | 科学计算社区常用 |
| Sphinx reST | Javadoc | 官方 Sphinx 默认 |

```python
def fetch_data(url: str, timeout: float = 5.0) -> dict:
    """从指定 URL 获取数据。

    Args:
        url: 请求地址。
        timeout: 超时时间（秒），默认 5.0。

    Returns:
        解析后的 JSON 字典。

    Raises:
        TimeoutError: 请求超时。
    """
```

## 小结

- **Pythonic 写法**：`enumerate` / `zip` / unpacking / walrus，不要逐行翻译 Java
- **代码风格**：PEP 8 + `ruff` + 类型注解，`ruff` 一个工具搞定 lint + format
- **错误处理**：EAFP 优先，精确捕获，用 `raise from` 保留异常链
- **项目结构**：src layout，`pyproject.toml` 管理依赖
- **测试**：pytest 是事实标准，`fixture` + `parametrize` + 原生 `assert`
- **日志**：用 `logging` 不用 `print`，生产环境用结构化日志
- **配置**：`pydantic-settings` 做类型安全配置
- **文档**：Google style docstring，配合类型注解

> 📁 [查看完整代码](../code/practice/02_best_practices.py)
