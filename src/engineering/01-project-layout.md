# 工业级项目结构

这一章讲真实项目该怎么组织。核心提醒：**Python 没有 Maven 那样的构建生命周期**，所以结构必须靠人为约定，比 Java 更需要纪律。

## 最大的心智落差

| | Java | Python |
|---|---|---|
| 构建生命周期 | `compile → test → package → verify → deploy` | **不存在** |
| 一条命令跑完 | `mvn verify` | 需要 `make check` 或 CI 脚本编排 |
| 工具关系 | 插件挂在生命周期阶段上 | 各自独立的命令行工具 |
| 配置位置 | `pom.xml` 里的 `<plugin>` | `pyproject.toml` 里的 `[tool.xxx]` |

`libraries/08-toolchain.md` 也强调过这点：`ruff`、`mypy`、`pytest` 是三个独立命令，靠 `pre-commit` 或 CI 串起来。

## 单包项目结构

> [完整结构](../code/engineering/01_project_layout.py#L70-L85)

```python
{{#include ../code/engineering/01_project_layout.py:70:85}}
```

```
my-service/
├── pyproject.toml              # 唯一配置
├── uv.lock                     # 锁文件（必须提交）
├── .python-version             # 固定解释器版本
├── src/
│   └── my_service/
│       ├── __init__.py
│       ├── py.typed            # 声明支持类型（PEP 561）
│       ├── api/
│       ├── services/
│       └── models/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
└── docs/
```

### 为什么用 `src/` layout

这是最容易忽略但影响最大的决定：

| | flat layout（平铺） | src layout |
|---|---|---|
| 结构 | `my_service/` 直接在根目录 | `src/my_service/` |
| 根目录跑 pytest | `import my_service` 命中**源码目录** | 必须 `pip install -e .` 才能导入 |
| 能发现打包遗漏吗 | ❌ 经常漏文件也能"跑通" | ✅ 强制验证安装后是否完整 |

> ⚠️ flat layout 最典型的坑：本地测试全绿，打包发布后用户 `import` 失败——因为某个 `__init__.py` 没被包含进 wheel。

> [Java 对比] 类似 Maven 强制 `src/main/java`——IDE 不会把源码目录当 classpath 根。

## 分层架构：依赖只向内

> [分层示例](../code/engineering/01_project_layout.py#L88-L154)

```python
{{#include ../code/engineering/01_project_layout.py:88:154}}
```

```
src/my_service/
├── domain/            # 实体、值对象 —— 纯 Python，零外部依赖
├── application/       # 用例编排，依赖 domain 的抽象
└── infrastructure/    # 数据库、HTTP、消息队列
```

**依赖方向必须单向**：

```
infrastructure → application → domain
```

❌ `domain` 绝不能 import `infrastructure`。

### 用 Protocol 做依赖倒置

```python
# application/ports.py —— 定义接口
from typing import Protocol

class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def get(self, order_id: str) -> Order | None: ...


# application/place_order.py —— 用例只依赖抽象
class PlaceOrder:
    def __init__(self, repo: OrderRepository):
        self._repo = repo
```

> [Java 对比] Java 需要 `interface` + Spring 的 `@Autowired`；Python 用 `Protocol` + 构造参数注入，**不需要容器**。鸭子类型让依赖注入轻得多——方法名对上就行。

### 这样做的好处

- `domain` 层可以脱离数据库、网络单独测试，速度快
- 换数据库只需改 `infrastructure`，业务代码不动
- 与 Java 的六边形架构/洋葱架构完全对应

## monorepo 与 workspace

> [monorepo 配置](../code/engineering/01_project_layout.py#L157-L201)

```python
{{#include ../code/engineering/01_project_layout.py:157:201}}
```

```
repo/
├── pyproject.toml          # workspace 根，无源码
├── uv.lock                 # 全仓共享锁文件
└── packages/
    ├── core/
    │   ├── pyproject.toml
    │   └── src/acme/core/
    └── web/
        ├── pyproject.toml
        └── src/acme/web/
```

根 `pyproject.toml`：

```toml
[tool.uv.workspace]
members = ["packages/*"]
```

`packages/web/pyproject.toml` 里引用本地包：

```toml
[project]
dependencies = ["acme-core"]

[tool.uv.sources]
acme-core = { workspace = true }
```

> [Java 对比] Maven multi-module 的 `<modules>` + 兄弟模块依赖；Gradle 的 `include` + `implementation project(':core')`。

**何时用 monorepo**：

- ✅ 多个包需要原子性变更（改 core 同时改 web）
- ✅ 共享锁文件，版本一致
- ❌ 团队独立发布、独立 CI 时，多仓库更简单

## `pyproject.toml` 全量

> [完整示例与语法校验](../code/engineering/01_project_layout.py#L273-L301)

```python
{{#include ../code/engineering/01_project_layout.py:273:301}}
```

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-service"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115,<1.0", "pydantic>=2.8"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6", "mypy>=1.11"]

[project.scripts]
my-service = "my_service.cli:main"

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

| 段 | 作用 | Java 对应 |
|---|---|---|
| `[build-system]` | 用什么后端构建 | `maven-compiler-plugin` |
| `[project]` | 元数据 + 依赖 | `groupId/artifactId/version/dependencies` |
| `[project.scripts]` | CLI 入口 | `Main-Class` + 启动脚本 |
| `[project.entry-points]` | 插件发现 | `ServiceLoader` / SPI |
| `[tool.*]` | 各工具配置 | 各 `<plugin><configuration>` |

## 依赖分组

> [依赖管理](../code/engineering/01_project_layout.py#L304-L338)

```python
{{#include ../code/engineering/01_project_layout.py:304:338}}
```

三类依赖，**务必分开**：

| 分组 | 内容 | 生产环境是否安装 |
|------|------|----------------|
| `dependencies` | 运行时必需 | ✅ |
| `optional-dependencies.dev` | 测试、lint、类型检查 | ❌ |
| `dependency-groups` | PEP 735 新标准分组 | 按需 |

```bash
uv add fastapi               # 运行时
uv add --dev pytest          # 开发
uv sync --no-dev             # 生产安装
```

**版本约束写法**：

| 写法 | 含义 | 适用 |
|------|------|------|
| `>=1.2` | 最低版本，无上限 | ⚠️ 库常用但风险高 |
| `>=1.2,<2.0` | 兼容 semver | ✅ 推荐 |
| `~=1.2.3` | `>=1.2.3,<1.3.0` | patch 级兼容 |
| `==1.2.3` | 精确锁定 | 应用层，库不要用 |

> ⚠️ **锁文件必须提交**：`uv.lock` / `poetry.lock`。生产镜像用 `--frozen`，不要每次重新解析。

## 真实结构验证

> [结构验证](../code/engineering/01_project_layout.py#L340-L397)

```python
{{#include ../code/engineering/01_project_layout.py:340:397}}
```

代码里生成了一套完整 src layout 并实际导入验证：

```
version: 0.1.0
__all__: ['place_order']
call: order placed
```

关键是 `__init__.py` 里导出 `place_order` 后，下游只需：

```python
from demo_service import place_order      # 不依赖内部文件结构
```

## 内部私有包

> [私有包分发](../code/engineering/01_project_layout.py#L400-L416)

```python
{{#include ../code/engineering/01_project_layout.py:400:416}}
```

| 方式 | 写法 |
|------|------|
| git 依赖 | `"acme-core @ git+https://git.corp/core.git@v1.2.0"` |
| 私有 PyPI | `[[tool.uv.index]]` + `url = "https://pypi.corp/simple"` |
| 共享目录 | `pip install -e`（仅开发期） |

> [Java 对比] 对应 Nexus / Artifactory 私服 + `<repositories>`。

> ⚠️ pip 安装老式包会执行 `setup.py`，等于执行任意代码。私有源要求认证，**token 不要写进 `pyproject.toml`**。

## Java 对照总表

> [完整对照](../code/engineering/01_project_layout.py#L419-L436)

```python
{{#include ../code/engineering/01_project_layout.py:419:436}}
```

| 概念 | Python | Java |
|------|--------|------|
| 项目配置 | `pyproject.toml` | `pom.xml` / `build.gradle` |
| 源码目录 | `src/<pkg>/` | `src/main/java` |
| 测试目录 | `tests/` | `src/test/java` |
| 构建生命周期 | **无** | `compile→test→package→deploy` |
| 依赖锁定 | `uv.lock` | `dependencyManagement` |
| 多模块 | `uv workspace` | multi-module |
| 接口抽象 | `Protocol` + 构造注入 | `interface` + `@Autowired` |
| 插件机制 | `entry-points` | `ServiceLoader` |

## 小结

- Python **没有构建生命周期**，结构纪律全靠约定
- **优先 src layout**：能暴露"打包后缺文件"的问题
- 分层架构靠 `Protocol` 做依赖倒置，依赖只向内
- `pyproject.toml` 一个文件管元数据、依赖和所有工具配置
- 锁文件必须提交，生产用 `--frozen`
- `__init__.py` 导出公开 API，让调用方不依赖内部结构

> 下一步：[构建与发布](02-build-and-release.md)、[CI/CD 与工作流](03-ci-and-workflow.md)

> 📁 [完整代码](../code/engineering/01_project_layout.py)
