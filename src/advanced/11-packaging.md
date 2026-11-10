# 包管理与生态

本章介绍现代 Python 的包管理工具链：`pyproject.toml` 配置、`uv`/`poetry` 依赖管理、
`venv` 虚拟环境、`ruff` 代码检查、`pytest` 测试框架，以及标准包结构。

## pyproject.toml：项目标准配置

`pyproject.toml` 是现代 Python 项目的标准配置文件（PEP 517/518/621），替代了旧的
`setup.py` / `setup.cfg`。

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = ["requests>=2.28", "pydantic>=2.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1"]

[project.scripts]
my-cli = "my_package.cli:main"
```

> [pyproject.toml 完整示例](../code/advanced/11_packaging.py#L32-L71)

```python
{{#include ../code/advanced/11_packaging.py:32:71}}
```

### Java 对比

| Python pyproject.toml | Java | 说明 |
|----------------------|------|------|
| `[build-system]` | pom.xml `<build><plugins>` | 构建后端 |
| `[project]` 元数据 | pom.xml groupId/artifactId/version | 项目元数据 |
| `dependencies` | `<dependencies>` | 运行时依赖 |
| `optional-dependencies` | Maven optional / Gradle feature variants | 可选依赖 |
| `[project.scripts]` | Maven mainClass | CLI 入口点 |
| `[tool.ruff]` 等 | checkstyle.xml + .editorconfig | 工具配置 |

## uv：超快包管理器

`uv` 是 Astral 用 Rust 写的超快包管理器，替代 `pip` + `venv` + `pip-tools`。

```bash
uv init my-project          # 初始化项目
uv add requests             # 添加依赖
uv sync                     # 同步依赖到 uv.lock
uv run python script.py     # 在项目环境里运行
```

> [uv 包管理器常用命令](../code/advanced/11_packaging.py#L92-L109)

```python
{{#include ../code/advanced/11_packaging.py:92:109}}
```

### Java 对比

`uv` 类似 Gradle 的依赖解析 + 缓存机制，但比 pip 快 10-100 倍。

## poetry：依赖管理 + 打包

`poetry` 是成熟的全流程工具，从初始化到发布一条龙。

```bash
poetry init                 # 交互式创建 pyproject.toml
poetry add requests         # 添加依赖
poetry add --group dev pytest  # 添加开发依赖
poetry install              # 安装所有依赖
poetry build                # 构建 sdist + wheel
poetry publish              # 发布到 PyPI
```

> [poetry 依赖管理](../code/advanced/11_packaging.py#L110-L126)

```python
{{#include ../code/advanced/11_packaging.py:110:126}}
```

`poetry.lock` 锁定版本，类似 Maven 的 pom.xml 锁定 + Gradle lockfile。

## venv：虚拟环境

`venv` 是 Python 内置的虚拟环境工具（3.3+），隔离项目依赖。

```bash
python -m venv .venv         # 创建虚拟环境
.venv\Scripts\activate       # Windows 激活
source .venv/bin/activate    # Linux/Mac 激活
deactivate                   # 退出
```

> [venv 虚拟环境](../code/advanced/11_packaging.py#L127-L144)

```python
{{#include ../code/advanced/11_packaging.py:127:144}}
```

### Java 对比

Java 没有内置虚拟环境概念，靠 Maven/Gradle 隔离依赖。Python 的 venv 是进程级隔离，
每个项目有独立的 site-packages。

## pipx：安装 CLI 工具

`pipx` 专门安装 Python 写的命令行工具，每个工具独立环境，互不污染。

```bash
pipx install black           # 安装到独立环境
pipx run cowsay 'hello'      # 临时运行，不安装
pipx list                    # 列出已装工具
```

> [pipx 安装 CLI 工具](../code/advanced/11_packaging.py#L145-L160)

```python
{{#include ../code/advanced/11_packaging.py:145:160}}
```

原则：**应用用 pipx，库依赖用 uv/poetry，不要全局 pip install**。

## ruff：linter + formatter

`ruff` 是 Rust 写的超快 linter + formatter，一个工具替代 flake8 + black + isort。

```bash
ruff check .                 # 检查代码
ruff check --fix .           # 自动修复
ruff format .                # 格式化代码
```

> [ruff linter + formatter](../code/advanced/11_packaging.py#L161-L180)

```python
{{#include ../code/advanced/11_packaging.py:161:180}}
```

### Java 对比

`ruff` ≈ checkstyle（lint）+ spotless（format），但比 flake8 快 50-200 倍。

## pytest：测试框架

`pytest` 用 `assert` 语句，无需 `self.assertEqual`，比 JUnit 简洁。

```python
def test_add():
    assert add(1, 2) == 3

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

@pytest.mark.parametrize("a,b,expected", [(1,2,3), (0,0,0)])
def test_add_params(a, b, expected):
    assert add(a, b) == expected

@pytest.fixture                # 类似 @BeforeEach
def sample_data():
    return [1, 2, 3]
```

> [pytest 测试文件示例](../code/advanced/11_packaging.py#L181-L225)

```python
{{#include ../code/advanced/11_packaging.py:181:225}}
```

### Java 对比

| Python pytest | Java JUnit 5 | 说明 |
|---------------|--------------|------|
| `assert x == y` | `assertEquals(y, x)` | 断言 |
| `pytest.raises(Exc)` | `assertThrows(Exc.class, ...)` | 异常测试 |
| `@pytest.mark.parametrize` | `@ParameterizedTest` + `@CsvSource` | 参数化 |
| `@pytest.fixture` | `@BeforeEach` | 测试夹具 |
| `conftest.py` | 无直接对应 | 共享 fixture |

## 标准包结构

推荐的 **src layout** 结构：

```
my-package/
├── pyproject.toml
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── core.py
│       └── py.typed        # 声明支持类型检查
├── tests/
│   ├── test_core.py
│   └── conftest.py          # pytest 共享 fixture
└── docs/
```

> [标准包结构详解](../code/advanced/11_packaging.py#L226-L244)

```python
{{#include ../code/advanced/11_packaging.py:226:244}}
```

关键文件：
- `__init__.py`：标记目录为包，可定义 `__all__`、`__version__`
- `py.typed`：空文件，告诉类型检查器本包支持 type hints（PEP 561）
- `conftest.py`：pytest 的共享 fixture，自动发现

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| `src/my_package/` | `src/main/java/...` | 源码 |
| `tests/` | `src/test/java/...` | 测试 |
| `pyproject.toml` | `pom.xml` / `build.gradle` | 配置 |

## 构建与发布

```bash
uv build            # 构建 sdist + wheel
uv publish          # 发布到 PyPI
# 或
poetry build && poetry publish
```

> [构建与发布流程](../code/advanced/11_packaging.py#L279-L297)

```python
{{#include ../code/advanced/11_packaging.py:279:297}}
```

### Java 对比

| Python | Java | 说明 |
|--------|------|------|
| 构建 wheel | `mvn package` 生成 jar | 打包 |
| 发布 PyPI | `mvn deploy` 到 Maven Central | 发布 |
| PyPI 全局唯一 | Maven Central + 私服 | 仓库 |

## 小结

- `pyproject.toml` 是现代 Python 项目标准配置（PEP 517/518/621）
- `uv` 是最快的包管理器，`poetry` 是成熟的全流程工具
- `venv` 隔离环境，`pipx` 装 CLI 工具
- `ruff` 一个工具搞定 lint + format
- `pytest` 用 assert 语句，比 JUnit 简洁
- src layout 是推荐的项目结构

> 📁 [查看完整代码](../code/advanced/11_packaging.py)
