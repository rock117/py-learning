# 工程化工具链

本章覆盖 Python 项目的"工程基建"：**pytest**（测试）、**ruff**（lint + 格式化）、**mypy**（静态类型检查）、**pyproject.toml + uv**（配置与依赖管理）、**pre-commit**（提交前钩子），每个工具都给出对应的 JVM 生态工具与关键行为差异。

## 全景对照：工具链一览

| 用途 | Python 工具 | Java 对应 | 差异要点 |
|------|-------------|-----------|----------|
| 测试 | pytest | JUnit 5 + JaCoCo | 断言就是 `assert`，无需断言 API |
| 断言库 | pytest 内置 assert | AssertJ | 失败时自动展开表达式 |
| Mock | `unittest.mock` / pytest-mock | Mockito | 更轻量，`monkeypatch` 也可 |
| Lint / 格式 | ruff | Checkstyle + PMD + Spotless | 一个工具、Rust 实现、毫秒级 |
| 类型检查 | mypy / pyright | javac | **可选、渐进**，不阻塞运行 |
| 依赖管理 | uv / poetry | Maven / Gradle | 单文件配置、秒级解析 |
| 提交钩子 | pre-commit | Spotless + CI 门禁 | 提前到本地 commit 阶段 |
| 打包发布 | hatchling / twine | maven-deploy | |

> [示例](../code/libraries/08_toolchain.py)

> ⚠️ 总纲：JVM 生态里这些是**分离的插件**（`pom.xml` 里一段段 `<plugin>`）；Python 生态里是**独立的命令行工具**，通过 `pyproject.toml` 里的 `[tool.xxx]` 段各自读配置。没有"构建生命周期"，你分别调用 `ruff` / `mypy` / `pytest`，再由 `pre-commit` 或 CI 串起来。

## pytest：测试框架

### 断言就是 `assert`

> [pytest 示例](../code/libraries/08_toolchain.py#L124-L160)

```python
{{#include ../code/libraries/08_toolchain.py:124:160}}
```

```python
def test_divide_ok():
    assert divide(10, 2) == 5
    assert divide(1, 3) == pytest.approx(0.3333, rel=1e-3)

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError, match="不能为 0"):
        divide(1, 0)
```

与 Java 的对应：

| pytest | Java |
|--------|------|
| `assert x == y` | `assertEquals(y, x)` / `assertThat(x).isEqualTo(y)` |
| `assert a in b` | `assertThat(b).contains(a)` |
| `pytest.approx(x)` | `assertEquals(x, y, delta)` |
| `pytest.raises(E, match=...)` | `assertThrows(E.class, ...)` |
| `@pytest.mark.parametrize` | `@ParameterizedTest` + `@CsvSource` |
| `@pytest.fixture` | `@BeforeEach` + 依赖注入 |

> [要点] 失败时 pytest 会**重写字节码**，把 `assert divide(10, 2) == 5` 展开成 `assert 5.0 == 5` 并展示两侧实际值——这就是不需要 AssertJ 的原因。Java 的裸 `assert` 被 JVM 默认关闭，这是两门语言最容易被误解的差异之一。

### 参数化测试

```python
@pytest.mark.parametrize("raw, expected", [("18", 18), ("0", 0), ("100", 100)])
def test_parse_age(raw, expected):
    assert parse_age(raw) == expected

@pytest.mark.parametrize("bad", ["abc", "", "1.5"])
def test_parse_age_invalid(bad):
    with pytest.raises(ValueError):
        parse_age(bad)
```

一个用例函数 × 一组参数 = 多个独立测试，报告里各自有名字，与 `@ParameterizedTest` + `@MethodSource` 等价。

### fixture：依赖注入 + yield teardown

```python
@pytest.fixture
def db():
    d = FakeDB()
    yield d          # yield 之前是 setup
    d.rows.clear()   # yield 之后是 teardown
```

关键差异：

- **依赖注入**：测试函数把 fixture 名写在参数里，pytest 自动传入。JUnit 里没有这个机制，`@BeforeEach` 只能给字段赋值。
- **`yield` 完成 setup/teardown**：等价于 `@BeforeEach` + `@AfterEach` 合体，但无需额外注解。
- **`scope`**：`function`（默认）/ `class` / `module` / `session`，可让昂贵资源跨测试复用——JUnit 5 里对应 `@TestInstance` 或 `@ExtendWith` 手写。

### monkeypatch：轻量 Mock

```python
def test_env_override(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    assert current_env() == "prod"
```

`monkeypatch` 提供 `setenv` / `setattr` / `chdir` / `syspath_prepend`，测试结束**自动还原**。

### unittest.mock：对照 Mockito

> [unittest.mock 示例](../code/libraries/08_toolchain.py#L183-L281)

```python
{{#include ../code/libraries/08_toolchain.py:183:281}}
```

当需要**验证调用**（`verify`）、**控制返回值**（`thenReturn`）或 **captor** 时，用 `unittest.mock`。完整的 Mockito 映射：

| Mockito | unittest.mock |
|---------|---------------|
| `mock(Svc.class)` | `Mock(spec=Svc)` |
| `when(x).thenReturn(v)` | `x.return_value = v` |
| `thenThrow(e)` | `x.side_effect = e` |
| `thenReturn(a, b)` | `x.side_effect = [a, b]` |
| `thenAnswer(f)` | `x.side_effect = f`（用函数） |
| `verify(x).m(1)` | `x.m.assert_called_with(1)` |
| `verify(x, times(2)).m()` | `assert x.m.call_count == 2` |
| `any()` | `mock.ANY` |
| `ArgumentCaptor` | `x.m.call_args_list` |
| `@Mock` / `@InjectMocks` | `@patch("module.attr")` / `patch.dict` |

三个关键差异：

**1. `Mock` vs `MagicMock`**

| | `Mock` | `MagicMock` |
|---|---|---|
| `len(m)` | ❌ `TypeError` | ✅ 可配置 |
| `iter(m)` / `with m` / `m[0]` | ❌ | ✅ |
| 适用场景 | 极少 | **默认选它** |

**2. 必须显式传 `spec=` 才有类型安全**

```python
strict = Mock(spec=RealService)
strict.nonexistent_method()      # ❌ AttributeError

loose = Mock()
loose.nonexistent_method()       # ✅ 静默通过，拼写错也不报
```

> ⚠️ Mockito 的 `mock(Svc.class)` **默认就是类型安全的**，而 Python 的 `Mock()` 接受任何调用。忘传 `spec=` 会让测试形同虚设——拼错方法名照样通过。

**3. `side_effect` 一个参数干三件事**

```python
repo.find.side_effect = [{"id": 2}, {"id": 3}]   # 依次返回
repo.find.side_effect = lambda x: x * 10          # 用函数计算
repo.find.side_effect = KeyError("not found")     # 抛异常
```

> [要点] 优先级：能用 `monkeypatch` 就用（更轻）；需要验证调用或复杂返回值时上 `unittest.mock`。

> [Java 对比] 与 JUnit 不同，pytest 的 Mock **不需要任何框架注解**，纯标准库；`pytest-mock` 只是把 `patch` 包装成了 fixture。

## ruff：lint + 格式化

> [ruff 示例](../code/libraries/08_toolchain.py#L183-L281)

```python
{{#include ../code/libraries/08_toolchain.py:183:281}}
```

ruff 用一个 Rust 二进制替代了**一整套**工具：

| ruff 规则 / 子命令 | 被替代的 Java 工具 |
|--------------------|--------------------|
| `E` / `F`（pycodestyle / pyflakes） | Checkstyle + 部分 PMD |
| `I`（isort） | 无对应（Java 有 IDE 整理 import） |
| `UP`（pyupgrade） | 无对应 |
| `B`（bugbear，常见 bug 模式） | SpotBugs / PMD |
| `SIM`（简化建议） | IntelliJ 检查 |
| `ruff format` | Spotless / google-java-format |

```bash
ruff check .              # 检查
ruff check --fix .        # 检查并自动修复
ruff format .             # 格式化（兼容 black 风格）
```

> [要点] 速度差距是量级的：几千文件的项目 ruff 通常**几百毫秒**，Checkstyle + Spotless 往往要几秒到几十秒。这直接决定了能否放进 pre-commit 钩子里而不烦人。

## mypy：静态类型检查

> [mypy 示例](../code/libraries/08_toolchain.py#L183-L281)

```python
{{#include ../code/libraries/08_toolchain.py:183:281}}
```

```python
def load_config(repo: Repo, key: str) -> int:
    raw = repo.get(key)
    return raw.get("value", "0")    # 声明 int，实际返回 str → mypy 报错
```

> [要点] **Python 的类型检查是可选、渐进的，这是和 javac 最根本的差异。**

| 维度 | javac | mypy |
|------|-------|------|
| 是否必须通过才能运行 | 是 | 否，代码照跑 |
| 覆盖范围 | 全部代码强制 | 只检查有注解的部分 |
| `--strict` | 无此概念 | 连未注解的函数也要求/检查 |
| 何时反馈 | 编译期（IDE + mvn compile） | 命令行 / IDE 插件 / pre-commit |
| 运行期强制 | 是 | 否，注解只是元数据 |

这意味着你可以**先不写类型**，在核心模块逐步加注解，把 `disallow_untyped_defs` 之类的开关一点点打开——这在 Java 项目里不可想象，但在从动态脚本长大的 Python 项目里非常实用。

- **mypy** vs **pyright**：二者都实现 PEP 484 系列规范。mypy 历史更久、配置项更毒舌（`--strict`）；pyright 由微软维护，是 VS Code Pylance 的引擎，IDE 即时反馈更顺畅。CI 里常两者都跑。

## pyproject.toml 与依赖管理

### 一个文件统一所有配置

> [pyproject.toml 示例](../code/libraries/08_toolchain.py#L284-L319)

```python
{{#include ../code/libraries/08_toolchain.py:284:319}}
```

```toml
[project]
name = "my-service"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115", "pydantic>=2.8"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6", "mypy>=1.11"]

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

对照 `pom.xml`：

| pyproject.toml 段 | pom.xml 中对应的部分 |
|-------------------|---------------------|
| `[project]` | `<groupId>` / `<artifactId>` / `<version>` / `<dependencies>` |
| `[project.optional-dependencies]` | `<profiles>` / `<scope>test</scope>` |
| `[build-system]` | `<build><plugins>` 中的 maven-compiler / jar |
| `[tool.ruff]` | maven-checkstyle-plugin `<configuration>` |
| `[tool.mypy]` | 无（javac 配置在 compiler plugin 里） |
| `[tool.pytest.ini_options]` | surefire `<configuration>` |

> ⚠️ **依赖版本原则相反**：Maven 习惯锁版本（`1.2.3`），Python 库通常声明**下限**（`>=0.115`），实际锁定交给 `uv.lock` / `poetry.lock`。库（给别人用）不锁，应用（自己部署）锁。

### uv：秒级依赖管理

> [工具链速查表](../code/libraries/08_toolchain.py#L377-L412)

```python
{{#include ../code/libraries/08_toolchain.py:377:412}}
```

| 操作 | uv | pip + venv | Maven / Gradle |
|------|----|-----------|----------------|
| 创建环境 | `uv venv` | `python -m venv .venv` | 无需（JVM 全局） |
| 安装依赖 | `uv sync` | `pip install -r req.txt` | `mvn install` |
| 锁定版本 | `uv lock` → `uv.lock` | `pip freeze` | `gradle.lockfile` |
| 新增依赖 | `uv add requests` | 手改文件再 `pip install` | 手改 pom 再 `mvn install` |
| Python 版本 | `uv python install 3.12` | pyenv / 系统包 | SDKMAN 管 JDK |
| 速度量级 | **秒级** | 十秒~分钟级 | 分钟级（首次） |

> [要点] uv 用 Rust 写的解析器 + 全局缓存 + 硬链接，冷启动也比 pip 快一个数量级，热缓存下几乎是瞬时的。它同时管"装 Python 版本 + 虚拟环境 + 依赖 + 锁文件"，角色上更接近 **Maven + SDKMAN** 的组合。

## pre-commit：提交前钩子

> [pre-commit 配置示例](../code/libraries/08_toolchain.py#L377-L412)

```python
{{#include ../code/libraries/08_toolchain.py:377:412}}
```

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
```

```bash
pre-commit install            # 写入 .git/hooks/pre-commit
pre-commit run --all-files    # 全量跑一次
```

> [要点] 对应 Java 里"CI 阶段才跑的 Spotless / Checkstyle 门禁"。差异在于：pre-commit **把检查提前到本地每次 commit**，失败就阻止提交；每个 hook 的依赖在隔离环境里自动安装，不需要复制脚本。

## 选型速查

> [速查表](../code/libraries/08_toolchain.py#L415-L445)

```python
{{#include ../code/libraries/08_toolchain.py:415:445}}
```

| 需求 | 首选 | 备选 | Java 对应 |
|------|------|------|-----------|
| 测试 | pytest | unittest | JUnit 5 |
| 覆盖率 | pytest-cov | coverage.py | JaCoCo |
| Lint / 格式 | ruff | flake8 + black | Checkstyle + Spotless |
| 类型检查 | mypy | pyright | javac |
| 依赖管理 | uv | poetry | Maven / Gradle |
| 提交钩子 | pre-commit | — | Git hooks + CI |

## 小结

- **`assert` 就是断言**：pytest 自动展开失败信息，不需要 AssertJ；断言参数顺序 `expected == actual` 也不再需要纠结
- **fixture 是依赖注入**：`yield` 划分 setup / teardown，写法比 `@BeforeEach` + `@AfterEach` 简洁
- **类型检查可选且渐进**：mypy 不通过代码照样运行，可以从零注解开始逐步收紧
- **`pyproject.toml` 一统配置**：项目元数据 + 所有工具配置，比 `pom.xml` + 一堆插件直观
- **uv 快一个数量级**：`uv sync` 秒级完成，`uv lock` 替代 `pip freeze`
- **pre-commit 把门禁前移**：CI 能做的事提前到本地 commit 阶段

> 📁 [查看完整代码](../code/libraries/08_toolchain.py)
