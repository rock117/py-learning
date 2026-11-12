# -*- coding: utf-8 -*-
"""
03_ci_and_workflow.py - CI/CD 与运行工作流

本文件面向有丰富 Java 经验的开发者，展示 Python 项目从提交到上线的完整流水线。

和 Java 的最大差异
------------------
Java 的构建是「编译 + 打包」，产物（jar）自包含。CI 里 mvn 一条命令全搞定。

Python 没有编译步骤，CI 分成两段性质不同的工作：
    1. 质量门禁（lint / type / test）—— 不需要打包
    2. 构建与分发（build / docker / publish）—— 需要显式编排
而且 Python 的「可运行单元」不是 wheel，而是 **Docker 镜像 / 虚拟环境**。

覆盖
----
1.  CI 流水线的标准阶段
2.  GitHub Actions 完整示例
3.  Makefile 统一本地命令
4.  Docker 多阶段构建（对齐 fat-jar 的思路）
5.  配置与环境管理（12-factor）
6.  部署与运行策略
7.  常见的「本地能跑 CI 挂」原因

[注意] 本文件只打印配置示例，不执行 docker/CI。
       会用真实工具校验 GitHub Actions 的 YAML 语法。
"""

import sys
import textwrap


# =============================================================================
# 1. CI 阶段划分
# =============================================================================

STAGES = [
    ("阶段", "做什么", "工具", "Java 对应"),
    ("① 静态检查", "格式、lint、import 排序", "ruff check / ruff format --check", "Spotless + Checkstyle"),
    ("② 类型检查", "静态类型验证", "mypy / pyright", "javac"),
    ("③ 测试", "单元 + 集成测试 + 覆盖率", "pytest --cov", "Surefire + JaCoCo"),
    ("④ 构建", "产出 wheel / sdist", "uv build", "mvn package"),
    ("⑤ 镜像", "构建运行时镜像", "docker build", "jib / docker"),
    ("⑥ 发布", "推 PyPI / 镜像仓库", "uv publish / docker push", "mvn deploy"),
    ("⑦ 部署", "滚动发布 / 迁移", "k8s / systemd / serverless", "同"),
]


def demo_stages():
    print("=== 1. CI 流水线的标准阶段 ===")
    widths = [max(len(str(r[i])) for r in STAGES) for i in range(4)]
    for idx, row in enumerate(STAGES):
        print("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))

    print("\n  关键区别：")
    print("     Java:  ①~③ 在同一个 mvn 生命周期内自动执行")
    print("     Python: ①~③ 是三个独立命令，必须显式编排顺序")
    print("\n  推荐并行：① 和 ② 可并行；③ 依赖 ①② 通过；④ 依赖 ③")
    print("  覆盖率、类型检查可以「不阻塞合并」但记录趋势，团队自行决策")


# =============================================================================
# 2. GitHub Actions
# =============================================================================

GHA_CI = '''
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
      - uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.13'

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
'''.strip()

GHA_RELEASE = '''
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: read
  id-token: write          # PyPI 可信发布（trusted publishing）

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
'''.strip()


def demo_github_actions():
    print("\n=== 2. GitHub Actions ===")
    print("  ---- .github/workflows/ci.yml ----")
    print(textwrap.indent(GHA_CI, "  "))

    print("\n  ---- .github/workflows/release.yml ----")
    print(textwrap.indent(GHA_RELEASE, "  "))

    print("\n  要点：")
    print("    uv sync --frozen    保证严格按 uv.lock 安装，不重新解析")
    print("    setup-uv 自带缓存   比 actions/cache 手配更简单")
    print("    matrix              覆盖多个 Python 版本（对应 Java 的多个 JDK）")
    print("    needs:              显式声明阶段依赖")
    print("    trusted publishing  用 OIDC 发 PyPI，无需长期 API token ✅")

    # 校验 YAML 语法
    print("\n  ---- 语法校验 ----")
    try:
        import yaml
    except ImportError:
        print("  [跳过] PyYAML 未安装，无法校验 YAML 语法")
        return
    for name, text in (("ci.yml", GHA_CI), ("release.yml", GHA_RELEASE)):
        try:
            doc = yaml.safe_load(text)
            jobs = list(doc.get("jobs", {}))
            print(f"     {name}: OK，jobs = {jobs}")
        except Exception as exc:
            print(f"     {name}: 解析失败 {exc}")

    print("\n  [Java 对比]")
    print("     Maven 项目 CI 往往就一行 mvn verify；")
    print("     Python 需要显式列出 ruff/mypy/pytest，这正是「没有生命周期」的代价")


# =============================================================================
# 3. Makefile
# =============================================================================

MAKEFILE = '''
.PHONY: install lint type test cov check build docker clean

install:
\tuv sync

lint:
\tuv run ruff check .
\tuv run ruff format --check .

type:
\tuv run mypy src

test:
\tuv run pytest

cov:
\tuv run pytest --cov --cov-report=term-missing

check: lint type test
\t@echo "all checks passed"

build:
\tuv build

docker:
\tdocker build -t my-service:$(shell git rev-parse --short HEAD) .

clean:
\trm -rf dist build .pytest_cache .ruff_cache .mypy_cache
\tfind . -name __pycache__ -type d -prune -exec rm -rf {} +
'''.strip()


def demo_makefile():
    print("\n=== 3. Makefile：统一本地与 CI 命令 ===")
    print(textwrap.indent(MAKEFILE, "  "))

    print("\n  价值：本地和 CI 跑的是同一组命令，避免「CI 和本地不一致」")
    print("     make check     # 本地提交前跑")
    print("     CI 里也调用 make check")

    print("\n  [Java 对比] 相当于 Maven 的 goal 别名；")
    print("              Gradle 用户可用 ./gradlew 类比，但 Python 没有内置编排器")

    print("\n  也可以用 taskfile / just / nox / tox：")
    print("     tox       多个 Python 版本 × 多套依赖的组合矩阵")
    print("     nox       用 Python 写任务脚本，比 Makefile 更好维护")


# =============================================================================
# 4. Docker
# =============================================================================

DOCKERFILE = '''
# ---- 构建阶段 ----
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 先只拷依赖清单，利用层缓存
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \\
    uv sync --frozen --no-install-project --no-dev

# 再拷源码并安装项目本身
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \\
    uv sync --frozen --no-dev

# ---- 运行阶段 ----
FROM python:3.12-slim

RUN useradd -m -u 10001 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "my_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
'''.strip()


def demo_docker():
    print("\n=== 4. Docker 多阶段构建 ===")
    print(textwrap.indent(DOCKERFILE, "  "))

    print("\n  为什么两阶段：")
    print("     builder 里需要 uv 和构建工具；运行镜像只保留 .venv + 源码")
    print("     最终镜像通常 150~250MB（slim 基础镜像）")

    print("\n  关键细节：")
    print("     --no-dev                 不装开发依赖，镜像更小更安全")
    print("     --frozen                 严格用 lock，构建可复现")
    print("     先 COPY 依赖清单         改代码时不用重装依赖（层缓存）")
    print("     ENV UV_COMPILE_BYTECODE  预编译 .pyc，启动更快")
    print("     PYTHONUNBUFFERED=1       日志立即输出，容器里别用默认缓冲")
    print("     USER app                 非 root 运行")
    print("     HEALTHCHECK              编排系统能感知健康状态")

    print("\n  [Java 对比]")
    print("     这就是 Python 版的 fat-jar：把解释器 + 依赖 + 代码打进一个镜像")
    print("     jar 方案（jib / spring-boot repackage）在 Python 没有等价物——")
    print("     wheel 不包含解释器，必须靠镜像固定运行时")


# =============================================================================
# 5. 配置与环境
# =============================================================================

def demo_config():
    print("\n=== 5. 配置与环境管理（12-factor） ===")

    print("  三层配置，分开管理：")
    print("     ① 代码中的默认值      可读、可直接跑")
    print("     ② 环境变量            部署时覆盖（12-factor）")
    print("     ③ 密钥               专用密钥管理系统，绝不入库")

    code = '''
    # src/my_service/config.py
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        database_url: str
        redis_url: str = "redis://localhost:6379/0"
        log_level: str = "INFO"
        debug: bool = False

    settings = Settings()        # 缺 database_url 会立刻报错，启动即失败
    '''
    print(textwrap.indent(code.strip("\n"), "  "))

    print("\n  要点：")
    print("     启动时校验（fail fast），不要等到处理请求才发现配置缺失")
    print("     .env 只用于本地开发，加进 .gitignore")
    print("     生产用编排系统的 secret（k8s Secret / AWS Secrets Manager）")

    print("\n  [Java 对比]")
    print("     Spring: application.yml + @ConfigurationProperties + @Value")
    print("     Python: pydantic-settings，类型即校验，无注解魔法")


# =============================================================================
# 6. 部署策略
# =============================================================================

def demo_deploy():
    print("\n=== 6. 部署与运行 ===")

    rows = [
        ("场景", "方案", "要点"),
        ("容器编排", "K8s Deployment + HPA", "liveness/readiness 探针分开配"),
        ("长驻服务", "systemd + venv", "Restart=always，日志走 journald"),
        ("定时任务", "cron + python -m", "加幂等锁，失败要有告警"),
        ("Serverless", "Lambda / Cloud Run", "冷启动敏感：精简依赖、延迟导入重库"),
        ("CLI 工具", "pipx install", "隔离环境，不污染系统 Python"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))

    print("\n  滚动发布注意：")
    print("     优雅停机：处理 SIGTERM，停止接新请求，等待在途请求完成")
    print("     ← Java 里靠 shutdown hook，Python 用 signal + asyncio 事件")

    code = '''
    # 优雅停机（asyncio 服务）
    import asyncio, signal

    async def serve():
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop.set)

        server = await start_server()
        await stop.wait()          # 阻塞直到收到信号
        server.close()
        await server.wait_closed() # 等在途请求结束
    '''
    print(textwrap.indent(code.strip("\n"), "  "))

    print("\n  数据库迁移：")
    print("     Alembic（SQLAlchemy 生态）—— 对应 Flyway / Liquibase")
    print("     迁移应在部署流程中单独一步，不要放在应用启动里（多副本会竞争）")


# =============================================================================
# 7. 本地能跑 CI 挂
# =============================================================================

def demo_ci_failures():
    print("\n=== 7. 常见的「本地能跑 CI 挂」 ===")

    rows = [
        ("原因", "表现", "解法"),
        ("依赖未锁定", "CI 装到新版本，行为变了", "提交 uv.lock，CI 用 --frozen"),
        ("大小写敏感", "macOS/Windows 能导入，Linux 挂", "文件名与 import 大小写严格一致"),
        ("路径分隔符", "写死 C:\\\\ 或 /", "用 pathlib.Path"),
        ("本地未提交文件", "依赖某个 .env / 数据文件", "CI 里显式造测试夹具"),
        ("sys.path 依赖 cwd", "直接跑脚本 vs python -m 不同", "规范用 python -m 或安装包"),
        ("时区/编码", "默认 UTF-8 与 GBK 差异", "显式 encoding='utf-8'，用 zoneinfo"),
        ("测试并行问题", "共享临时文件/端口冲突", "tmp_path fixture，端口用 0"),
        ("未装可选依赖", "测试里 import 了但没声明", "dev 依赖组里写全"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))

    print("\n  [实用技巧] CI 上跑一次 `uv sync --frozen` + `uv run pytest`，")
    print("             就能在合并前暴露绝大多数问题")


def print_java_mapping():
    print("\n=== 8. Java 对照总表 ===")
    rows = [
        ("环节", "Python", "Java"),
        ("本地编排", "Makefile / nox", "mvn / gradlew"),
        ("CI", "GitHub Actions 显式编排", "mvn verify"),
        ("多版本矩阵", "matrix: python-version", "matrix: java-version"),
        ("可运行产物", "Docker 镜像", "jar / Docker"),
        ("配置", "pydantic-settings", "application.yml"),
        ("迁移", "Alembic", "Flyway / Liquibase"),
        ("优雅停机", "signal + asyncio", "shutdown hook"),
        ("发布认证", "trusted publishing (OIDC)", "同 / token"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 66)
    print("CI/CD 与运行工作流")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 66)

    demo_stages()
    demo_github_actions()
    demo_makefile()
    demo_docker()
    demo_config()
    demo_deploy()
    demo_ci_failures()
    print_java_mapping()

    print("\n" + "=" * 66)
    print("所有 demo 运行完成！")
    print("=" * 66)


if __name__ == "__main__":
    main()
