# CI/CD 与运行工作流

这一章把前面所有工具串成一条流水线：**从 git push 到线上运行**。

## CI 阶段划分

> [阶段对照表](../code/engineering/03_ci_and_workflow.py#L50-L67)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:50:67}}
```

| 阶段 | 做什么 | 工具 | Java 对应 |
|------|--------|------|-----------|
| ① 静态检查 | 格式、lint、import 排序 | `ruff check` / `ruff format --check` | Spotless + Checkstyle |
| ② 类型检查 | 静态类型验证 | `mypy` / `pyright` | `javac` |
| ③ 测试 | 单元 + 集成 + 覆盖率 | `pytest --cov` | Surefire + JaCoCo |
| ④ 构建 | 产出 wheel / sdist | `uv build` | `mvn package` |
| ⑤ 镜像 | 构建运行时镜像 | `docker build` | jib / docker |
| ⑥ 发布 | 推 PyPI / 镜像仓库 | `uv publish` / `docker push` | `mvn deploy` |
| ⑦ 部署 | 滚动发布 / 迁移 | k8s / systemd | 同 |

**关键区别**：

```
Java:   ①~③ 在同一个 mvn 生命周期内自动执行
Python: ①~③ 是三个独立命令，必须显式编排
```

依赖关系：① 和 ② 可并行，③ 依赖 ①② 通过，④ 依赖 ③。

## GitHub Actions

> [完整工作流示例与语法校验](../code/engineering/03_ci_and_workflow.py#L149-L186)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:149:186}}
```

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src

  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
      - run: uv sync --frozen --python ${{ matrix.python-version }}
      - run: uv run pytest --cov --cov-report=xml

  build:
    needs: [quality, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - run: uv run --with twine twine check dist/*
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
```

### `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: read
  id-token: write          # PyPI 可信发布

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0    # hatch-vcs 需要完整 git 历史
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - run: uv publish --trusted-publishing always
```

### 要点

| 配置 | 作用 |
|------|------|
| `uv sync --frozen` | 严格按 `uv.lock` 安装，不重新解析 |
| `setup-uv` 自带缓存 | 比手配 `actions/cache` 简单 |
| `matrix` | 覆盖多个 Python 版本（对应多 JDK） |
| `needs:` | 显式声明阶段依赖 |
| `trusted publishing` | 用 OIDC 发 PyPI，**无需长期 API token** |

代码里用 PyYAML 实际校验了两个文件的语法：

```
ci.yml: OK，jobs = ['quality', 'test', 'build']
release.yml: OK，jobs = ['publish']
```

> [Java 对比] Maven 项目 CI 常常就一行 `mvn verify`；Python 需要显式列出 `ruff`/`mypy`/`pytest`——**这正是"没有生命周期"的代价**。

## Makefile：统一本地与 CI

> [Makefile 示例](../code/engineering/03_ci_and_workflow.py#L222-L240)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:222:240}}
```

```makefile
.PHONY: install lint type test cov check build clean

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

type:
	uv run mypy src

test:
	uv run pytest

check: lint type test
	@echo "all checks passed"

build:
	uv build
```

**价值**：本地和 CI 跑同一组命令，避免"CI 和本地不一致"。

```bash
make check      # 提交前跑
# CI 里也调用 make check
```

> [Java 对比] 相当于 Maven goal 别名。也可以用 `nox` / `tox`：
> - `tox` —— 多 Python 版本 × 多套依赖的组合矩阵
> - `nox` —— 用 Python 写任务脚本，比 Makefile 好维护

## Docker 多阶段构建

> [完整 Dockerfile](../code/engineering/03_ci_and_workflow.py#L282-L307)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:282:307}}
```

```dockerfile
# ---- 构建阶段 ----
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 先只拷依赖清单，利用层缓存
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 再拷源码
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- 运行阶段 ----
FROM python:3.12-slim
RUN useradd -m -u 10001 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app
EXPOSE 8000
CMD ["uvicorn", "my_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 关键细节

| 配置 | 原因 |
|------|------|
| `--no-dev` | 不装开发依赖，镜像更小更安全 |
| `--frozen` | 严格用 lock，构建可复现 |
| 先 `COPY` 依赖清单 | 改代码时不用重装依赖（层缓存） |
| `UV_COMPILE_BYTECODE=1` | 预编译 `.pyc`，启动更快 |
| `PYTHONUNBUFFERED=1` | 日志立即输出，容器里别用默认缓冲 |
| `USER app` | 非 root 运行 |
| `HEALTHCHECK` | 编排系统能感知健康状态 |

> [Java 对比] **这就是 Python 版的 fat-jar**：把解释器 + 依赖 + 代码打进一个镜像。jar 方案（jib / spring-boot repackage）在 Python 没有等价物——**wheel 不含解释器，必须靠镜像固定运行时**。

## 配置与环境管理

> [配置示例](../code/engineering/03_ci_and_workflow.py#L309-L345)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:309:345}}
```

三层配置分开管理：

1. **代码中的默认值** —— 可读、可直接跑
2. **环境变量** —— 部署时覆盖（12-factor）
3. **密钥** —— 专用密钥管理，绝不入库

```python
# src/my_service/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    debug: bool = False

settings = Settings()      # 缺 database_url 立刻报错，启动即失败
```

> [要点] **启动时校验（fail fast）**，不要等处理请求才发现配置缺失。

> [Java 对比] Spring 的 `application.yml` + `@ConfigurationProperties`；Python 用 pydantic-settings，**类型即校验**，没有注解魔法。

## 部署策略

> [部署方案对照](../code/engineering/03_ci_and_workflow.py#L347-L392)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:347:392}}
```

| 场景 | 方案 | 要点 |
|------|------|------|
| 容器编排 | K8s Deployment + HPA | liveness/readiness 探针分开配 |
| 长驻服务 | systemd + venv | `Restart=always`，日志走 journald |
| 定时任务 | cron + `python -m` | 加幂等锁，失败要告警 |
| Serverless | Lambda / Cloud Run | 冷启动敏感：精简依赖、延迟导入重库 |
| CLI 工具 | `pipx install` | 隔离环境，不污染系统 Python |

### 优雅停机

```python
import asyncio, signal

async def serve():
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    server = await start_server()
    await stop.wait()           # 阻塞直到收到信号
    server.close()
    await server.wait_closed()  # 等在途请求结束
```

> [Java 对比] Java 靠 shutdown hook；Python 用 `signal` + asyncio 事件。

### 数据库迁移

**Alembic**（SQLAlchemy 生态）—— 对应 Flyway / Liquibase。

> ⚠️ 迁移应在部署流程中**单独一步**，不要放在应用启动里——多副本会竞争，导致重复执行。

## 常见的「本地能跑 CI 挂」

> [原因对照表](../code/engineering/03_ci_and_workflow.py#L394-L415)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:394:415}}
```

| 原因 | 表现 | 解法 |
|------|------|------|
| 依赖未锁定 | CI 装到新版本，行为变了 | 提交 `uv.lock`，CI 用 `--frozen` |
| 大小写敏感 | macOS/Windows 能导入，Linux 挂 | 文件名与 import 大小写严格一致 |
| 路径分隔符 | 写死 `C:\` 或 `/` | 用 `pathlib.Path` |
| 本地未提交文件 | 依赖某个 `.env` / 数据文件 | CI 里显式造测试夹具 |
| `sys.path` 依赖 cwd | 直接跑脚本 vs `python -m` 不同 | 规范用 `python -m` |
| 时区/编码 | 默认 UTF-8 与 GBK 差异 | 显式 `encoding="utf-8"`，用 `zoneinfo` |
| 测试并行问题 | 共享临时文件/端口冲突 | `tmp_path` fixture，端口用 0 |
| 未装可选依赖 | 测试里 import 了但没声明 | dev 依赖组里写全 |

> [实用技巧] CI 上跑一次 `uv sync --frozen` + `uv run pytest`，就能在合并前暴露绝大多数问题。

## Java 对照总表

> [完整对照](../code/engineering/03_ci_and_workflow.py#L418-L435)

```python
{{#include ../code/engineering/03_ci_and_workflow.py:418:435}}
```

| 环节 | Python | Java |
|------|--------|------|
| 本地编排 | Makefile / nox | `mvn` / `gradlew` |
| CI | GitHub Actions 显式编排 | `mvn verify` |
| 多版本矩阵 | `matrix: python-version` | `matrix: java-version` |
| 可运行产物 | **Docker 镜像** | jar / Docker |
| 配置 | pydantic-settings | `application.yml` |
| 迁移 | Alembic | Flyway / Liquibase |
| 优雅停机 | `signal` + asyncio | shutdown hook |
| 发布认证 | trusted publishing (OIDC) | 同 / token |

## 小结

- Python CI 必须**显式编排**三个阶段（lint / type / test），没有生命周期兜底
- `uv sync --frozen` + `setup-uv` 缓存是最简高效的 CI 配置
- Makefile 统一本地与 CI 命令，避免环境不一致
- **Docker 镜像是 Python 版的 fat-jar**——wheel 不含解释器
- 配置用 pydantic-settings 在启动时校验，fail fast
- 优雅停机靠 `signal` + asyncio 事件，迁移单独一步执行
- 锁文件必须提交，这是"本地能跑 CI 挂"的头号原因

> 📁 [完整代码](../code/engineering/03_ci_and_workflow.py)
