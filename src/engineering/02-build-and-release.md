# 构建与发布

这一章讲「从源码到可分发产物」的完整链路，以及包管理工具怎么选。

## 包管理工具全景

> [工具对比表](../code/engineering/02_build_and_release.py#L51-L78)

```python
{{#include ../code/engineering/02_build_and_release.py:51:78}}
```

| 工具 | 定位 | Java 对应 | 何时用 |
|------|------|-----------|--------|
| `pip` | 最基础的安装器 | 无 | 脚本、CI 的最小依赖 |
| **`uv`** | 安装器 + 环境 + 锁 + 构建 + 发布 | Maven + sdkman 合体 | **几乎所有新项目** |
| `poetry` | 依赖管理 + 打包 + 发布一体 | 最接近 Maven | 团队已在用 |
| `pipx` | 把 CLI 工具装到隔离环境 | 装全局命令行工具 | 装 `ruff` / `poetry` 本身 |
| `conda` | 跨语言环境 + 二进制依赖 | 无 | 数据科学 |
| `hatch` | 模板 + 构建后端 | archetype + 插件 | 用 `hatchling` 作 backend |
| `setuptools` | 老牌构建后端 | `maven-compiler-plugin` | 存量项目 |
| `twine` | 上传 PyPI 的经典工具 | `mvn deploy` | 手动校验后发布 |

### uv 为什么成为默认选择

- 安装速度比 pip 快 **10~100 倍**（Rust 实现 + 全局缓存硬链接）
- 一个工具覆盖：`venv` + `pip` + `pip-tools` + `pipx` + `build` + `publish`
- 兼容 `pyproject.toml` 和现有 `requirements.txt`
- 跨平台一致的解析与锁定

### poetry vs uv

| | poetry | uv |
|---|---|---|
| 成熟度 | 生态成熟、lock 稳定 | 快速演进 |
| 速度 | 较慢 | 极快 |
| 标准贴合 | 历史上有偏差 | 更贴近 PEP |
| 定位 | 全流程工具 | 可当 pip 替代 |

> [Java 对比] Maven 一个工具搞定生命周期；Python 是"一堆单职责工具 + 一个编排器"。

## 构建产物：sdist vs wheel

> [产物对比](../code/engineering/02_build_and_release.py#L80-L116)

```python
{{#include ../code/engineering/02_build_and_release.py:80:116}}
```

| 产物 | 内容 | 安装时 | 平台相关 |
|------|------|--------|---------|
| **sdist** (`.tar.gz`) | 源码 + `pyproject.toml` | 现场构建，可能要编译器 | 否 |
| **wheel** (`.whl`) | 预构建的文件集合 + 元数据 | 直接解压复制 | 纯 Python 时通用 |

wheel 文件名编码了关键信息：

```
my_service-0.1.0-py3-none-any.whl
  ^name   ^ver   ^py  ^abi ^platform
```

| 后缀 | 含义 |
|------|------|
| `py3-none-any` | 纯 Python，任何平台通用 |
| `cp312-cp312-win_amd64` | CPython 3.12 + Windows x64 |
| `cp312-abi3-manylinux` | ABI3 稳定接口，Linux 通用 |

**为什么优先 wheel**：

- 无构建步骤，安装快一个数量级
- 避免用户机器缺编译器/头文件导致失败
- 纯 Python 项目也建议两种都发

> [Java 对比] `jar` ≈ wheel（分发单元），但 jar 含编译后 class 且可跨平台；`sdist` 更像 sources jar。**Python 没有"字节码 + 依赖打成唯一产物"的默认习惯**——Docker 镜像才是真正对齐 fat-jar 的方案。

## 版本号管理

> [版本管理示例](../code/engineering/02_build_and_release.py#L118-L172)

```python
{{#include ../code/engineering/02_build_and_release.py:118:172}}
```

语义化版本 `MAJOR.MINOR.PATCH`，预发布用 PEP 440 后缀（`1.0.0a1` / `1.0.0rc1`）。

⚠️ **版本号只能有一个来源**，不要多处手写。

### 方式一：`pyproject.toml` 写死，运行时读元数据

```toml
[project]
version = "0.1.0"
```

```python
# src/my_service/__init__.py
from importlib.metadata import version
__version__ = version("my-service")      # 不要手写字符串
```

### 方式二：从 git tag 动态生成

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
```

代码里真实演示了 `importlib.metadata.version`：

```
pip                -> 25.1.1
pydantic           -> 2.11.7
nonexistent-pkg    -> PackageNotFoundError（未安装时这样处理）
```

> [Java 对比] Maven 用 `${project.version}` 引用。Python 包安装后目录名**不含版本号**，版本记录在 `*.dist-info/` 目录里。

## 构建命令链

> [构建演示](../code/engineering/02_build_and_release.py#L174-L239)

```python
{{#include ../code/engineering/02_build_and_release.py:174:239}}
```

### uv（推荐）

```bash
uv build                # 同时产出 sdist + wheel 到 dist/
uv build --wheel        # 只构建 wheel
uv publish              # 发布到 PyPI
uv publish --index-url https://pypi.corp/simple    # 发私服
```

### poetry

```bash
poetry build && poetry publish
```

### 传统方式（twine）

```bash
python -m build         # 需要 pip install build
twine check dist/*      # 校验元数据与 README 渲染
twine upload dist/*
```

### 真实构建结果

代码里实际执行了一次 `uv build`：

```
Building source distribution...
Building wheel from source distribution...
Successfully built dist\demo_build_pkg-0.1.0.tar.gz
Successfully built dist\demo_build_pkg-0.1.0-py3-none-any.whl

产出:
  demo_build_pkg-0.1.0-py3-none-any.whl  (1010 bytes)
  demo_build_pkg-0.1.0.tar.gz            (406 bytes)
```

> ⚠️ **发布不可逆**：PyPI 上同名版本**不能覆盖**，只能换版本号或 yank。发布前先在 TestPyPI 演练：

```bash
uv publish --publish-url https://test.pypi.org/legacy/
```

## 发布前检查清单

> [检查清单](../code/engineering/02_build_and_release.py#L257-L267)

```python
{{#include ../code/engineering/02_build_and_release.py:257:267}}
```

| 类别 | 检查项 |
|------|--------|
| 元数据 | `name`/`version`/`description`/`license` 齐全 |
| 元数据 | README 能在 PyPI 正常渲染（`twine check`） |
| 构建 | sdist 与 wheel 都能构建 |
| 构建 | wheel 里含 `py.typed`（如需类型支持） |
| 测试 | 全部测试通过 |
| **测试** | **在干净环境装 wheel 后能导入** |
| 质量 | `ruff check` + `mypy` 通过 |
| 兼容 | 测试最低 Python 版本 |
| 安全 | `pip-audit` 无已知漏洞 |
| 版本 | git tag 与版本号一致 |
| 演练 | 先发 TestPyPI |

> [要点] "在干净环境装 wheel 后能导入"是最容易漏的一步。**src layout 能帮你避免"本地能跑、装完缺文件"**。

## 私服发布

> [私服配置](../code/engineering/02_build_and_release.py#L270-L293)

```python
{{#include ../code/engineering/02_build_and_release.py:270:293}}
```

```toml
[[tool.uv.index]]
name = "corp"
url = "https://pypi.corp.example.com/simple"
publish-url = "https://pypi.corp.example.com/legacy/"
explicit = true          # 只在显式指定时用这个源
```

认证通过环境变量，**不要写进仓库**：

```bash
UV_INDEX_CORP_USERNAME / UV_INDEX_CORP_PASSWORD
```

> ⚠️ `explicit = true` 很重要。否则 pip 会把公有 PyPI 和私服混合解析，容易被**依赖混淆攻击**（dependency confusion）利用——攻击者在你私服上抢注一个同名的公有包。

> [Java 对比] `<repositories>` + `<distributionManagement>` + `settings.xml`。

## Java 对照总表

> [完整对照](../code/engineering/02_build_and_release.py#L296-L313)

```python
{{#include ../code/engineering/02_build_and_release.py:296:313}}
```

| 环节 | Python | Java |
|------|--------|------|
| 依赖解析 | `uv lock` | `mvn dependency:resolve` |
| 构建 | `uv build` | `mvn package` |
| 产物 | sdist + wheel | jar |
| 校验 | `twine check` | `mvn verify` |
| 发布 | `uv publish` | `mvn deploy` |
| 仓库 | PyPI / 私服 | Maven Central / Nexus |
| 可执行分发 | **Docker 镜像** | fat jar / Docker |

## 小结

- **uv** 是当前首选：一个工具覆盖环境、依赖、构建、发布
- **sdist 是源码包，wheel 是预构建包**——优先发 wheel
- 版本号单一来源：`pyproject.toml` 或 git tag，运行时用 `importlib.metadata`
- 发布不可逆，**先在 TestPyPI 演练**
- 发布前务必在干净环境装 wheel 验证
- 私服配置 `explicit = true` 防依赖混淆

> 下一步：[CI/CD 与工作流](03-ci-and-workflow.md)

> 📁 [完整代码](../code/engineering/02_build_and_release.py)
