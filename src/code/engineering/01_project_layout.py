# -*- coding: utf-8 -*-
"""
01_project_layout.py - 工业级项目结构与依赖管理

本文件面向有丰富 Java 经验的开发者，讲解真实项目该怎么组织代码。

最大的心智落差
--------------
Java 有 Maven/Gradle 的 **build lifecycle**（compile -> test -> package -> verify ->
install -> deploy），每个阶段挂插件，`mvn deploy` 一条命令走完全部。

Python **没有构建生命周期**。每个工具是独立命令（ruff / mypy / pytest / build），
串起来靠 pre-commit、Makefile 或 CI 脚本。理解这点是关键。

覆盖
----
1.  单包项目结构（src layout）
2.  分层架构：domain / application / infrastructure
3.  monorepo 与 workspace
4.  pyproject.toml 全量解读
5.  依赖分组与锁定
6.  内部私有包

[注意] 本文件用临时目录生成真实结构并校验，跑完自动清理。
"""

import sys
import textwrap
import tomllib
from pathlib import Path


# =============================================================================
# 1. 单包项目结构
# =============================================================================

SINGLE_PACKAGE = """
my-service/
├── pyproject.toml              # 唯一的项目配置
├── README.md
├── LICENSE
├── .python-version             # 固定 Python 版本（uv/pyenv 读取）
├── uv.lock                     # 锁文件（必须提交）
├── .pre-commit-config.yaml
├── .gitignore
├── src/
│   └── my_service/
│       ├── __init__.py         # 导出公开 API
│       ├── py.typed            # 声明支持类型（PEP 561）
│       ├── config.py
│       ├── cli.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── orders.py
│       └── models/
│           ├── __init__.py
│           └── order.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── scripts/                    # 一次性运维脚本
└── docs/
""".strip()


def demo_single_package():
    """为什么用 src layout。"""
    print("=== 1. 单包项目结构（src layout）===")
    print(textwrap.indent(SINGLE_PACKAGE, "  "))

    print("\n  为什么放 src/ 而不是根目录直接放 my_service/：")
    print("    ❌ 平铺（flat layout）")
    print("       my_service/")
    print("       tests/")
    print("       问题：在项目根跑 pytest 时，当前目录进 sys.path，")
    print("             import my_service 命中【源码目录】而不是【已安装的包】")
    print("             -> 本地通过、打包后失效（漏了文件或 __init__ 逻辑不同）")
    print("    ✅ src layout")
    print("       源码不在 sys.path 里，必须 pip install -e . 才能导入")
    print("       -> 强制验证「安装后是否可用」，暴露打包遗漏")
    print("\n  [Java 对比] 类似 Maven 的 src/main/java——IDE 不会把源码当 classpath 根")


def demo_layered_architecture():
    """分层架构与依赖方向。"""
    print("\n=== 2. 分层架构：依赖只向内 ===")

    print("  推荐的三层（Clean Architecture 简化版）：")
    print("     src/my_service/")
    print("     ├── domain/            # 实体、值对象、领域服务——纯 Python，零外部依赖")
    print("     ├── application/       # 用例编排，依赖 domain 的抽象")
    print("     └── infrastructure/    # 数据库、HTTP、消息队列——实现 application 定义的接口")

    print("\n  依赖方向（必须单向）：")
    print("     infrastructure -> application -> domain")
    print("     ❌ domain 绝不能 import infrastructure")

    print("\n  实现方式：用 Protocol 定义接口（类似 Java interface）")

    code = '''
    # domain/order.py —— 零依赖，可单独测试
    from dataclasses import dataclass
    from decimal import Decimal

    @dataclass(frozen=True)
    class Order:
        id: str
        amount: Decimal

        def with_discount(self, rate: Decimal) -> "Order":
            return Order(self.id, self.amount * (1 - rate))


    # application/ports.py —— 定义仓储接口
    from typing import Protocol
    from domain.order import Order

    class OrderRepository(Protocol):
        def save(self, order: Order) -> None: ...
        def get(self, order_id: str) -> Order | None: ...


    # application/place_order.py —— 用例，只依赖抽象
    class PlaceOrder:
        def __init__(self, repo: OrderRepository):
            self._repo = repo

        def execute(self, order_id: str, amount: Decimal) -> Order:
            order = Order(order_id, amount)
            self._repo.save(order)
            return order


    # infrastructure/sql_repo.py —— 具体实现
    class SqlOrderRepository:
        def __init__(self, session): self._session = session
        def save(self, order): ...
        def get(self, order_id): ...


    # main.py —— 装配（依赖注入）
    repo = SqlOrderRepository(session)
    PlaceOrder(repo).execute("A-1", Decimal("99.9"))
    '''
    print(textwrap.indent(code.strip("\n"), "  "))

    print("\n  [Java 对比]")
    print("     Java: Spring 的 @Service/@Repository + 接口注入")
    print("     Python: Protocol + 构造函数传参，不需要容器")
    print("     [要点] Python 的鸭子类型让依赖注入更轻——只要能对上方法名就行")


def demo_monorepo():
    """monorepo 与 workspace。"""
    print("\n=== 3. monorepo 与 workspace ===")

    print("  结构：")
    print("     repo/")
    print("     ├── pyproject.toml          # workspace 根，无源码")
    print("     ├── uv.lock                 # 全仓共享锁文件")
    print("     ├── packages/")
    print("     │   ├── core/               # package: acme-core")
    print("     │   │   ├── pyproject.toml")
    print("     │   │   └── src/acme/core/")
    print("     │   └── web/                # package: acme-web")
    print("     │       ├── pyproject.toml")
    print("     │       └── src/acme/web/")
    print("     └── tools/")

    print("\n  uv workspace 配置（根 pyproject.toml）：")
    cfg = '''
    [tool.uv.workspace]
    members = ["packages/*"]

    # packages/web/pyproject.toml 里引用本地包
    [project]
    dependencies = ["acme-core"]

    [tool.uv.sources]
    acme-core = { workspace = true }
    '''
    print(textwrap.indent(cfg.strip("\n"), "  "))

    print("\n  [Java 对比]")
    print("     Maven multi-module: <modules> + <dependency> 指向兄弟模块")
    print("     Gradle: include ':core', ':web' + implementation project(':core')")
    print("     Python: uv workspace / poetry path dependency")

    print("\n  何时用 monorepo：")
    print("     ✅ 多个包需要原子性变更（改 core 同时改 web）")
    print("     ✅ 共享锁文件，版本一致")
    print("     ❌ 团队独立发布、独立 CI 时，多仓库更简单")


# =============================================================================
# 2. pyproject.toml 全量
# =============================================================================

FULL_PYPROJECT = '''
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-service"
version = "0.1.0"
description = "订单服务"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [{ name = "Rock", email = "rock@example.com" }]
keywords = ["orders", "service"]
classifiers = [
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]

# 运行时依赖：带版本约束
dependencies = [
    "fastapi>=0.115,<1.0",
    "pydantic>=2.8",
    "httpx>=0.27",
]

# 可选依赖：按用途分组，pip install my-service[dev]
[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov", "ruff>=0.6", "mypy>=1.11", "pre-commit"]
docs = ["mkdocs-material"]

# CLI 入口点：安装后可直接调用的命令
[project.scripts]
my-service = "my_service.cli:main"

# 插件入口点（供其他包发现）
[project.entry-points."myapp.plugins"]
csv_exporter = "my_service.exporters.csv:Exporter"

[project.urls]
Homepage = "https://github.com/rock117/my-service"
Issues = "https://github.com/rock117/my-service/issues"

# ---------------- 工具配置 ----------------
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.11"
strict = true
files = ["src", "tests"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers --cov=src --cov-report=term-missing"
markers = ["integration: 需要外部服务"]

[tool.coverage.run]
branch = true
source = ["src"]

[tool.hatch.build.targets.wheel]
packages = ["src/my_service"]
'''.strip()


def demo_pyproject():
    """逐段解读 pyproject.toml。"""
    print("\n=== 4. pyproject.toml 全量解读 ===")
    print(textwrap.indent(FULL_PYPROJECT, "  "))

    # 真实解析验证：确认这段 TOML 语法正确
    try:
        data = tomllib.loads(FULL_PYPROJECT)
        print(f"\n  ✅ TOML 语法校验通过")
        print(f"     project.name = {data['project']['name']!r}")
        print(f"     依赖数 = {len(data['project']['dependencies'])}")
        print(f"     CLI 入口 = {list(data['project']['scripts'])}")
        print(f"     可选依赖组 = {list(data['project']['optional-dependencies'])}")
    except Exception as exc:
        print(f"  ❌ TOML 解析失败: {exc}")

    print("\n  各段作用：")
    print("     [build-system]          告诉 pip 用什么后端构建（setuptools/hatchling/poetry）")
    print("     [project]               项目元数据 + 依赖（PEP 621 标准）")
    print("     [project.scripts]       定义命令行入口，安装后生成可执行文件")
    print("     [project.entry-points]  插件发现机制，等价于 Java ServiceLoader")
    print("     [tool.*]                各工具自己的配置，统一放这里")

    print("\n  [Java 对比]")
    print("     [project]        ~ <groupId>/<artifactId>/<version>/<dependencies>")
    print("     [build-system]   ~ <build><plugins><plugin>maven-compiler")
    print("     [project.scripts]~ maven-shade 的 Main-Class + 启动脚本")
    print("     多个 [tool.*]    ~ 多个 <plugin> 各自的 <configuration>")
    print("     [关键差异] 没有 <plugins> 执行阶段的概念，工具都是独立命令")


def demo_dependency_groups():
    """依赖分组与锁定策略。"""
    print("\n=== 5. 依赖分组与锁定 ===")

    print("  三类依赖，务必分开：")
    print("     dependencies                运行时必需，会传给下游用户")
    print("     optional-dependencies.dev   开发工具，不进生产镜像")
    print("     dependency-groups           PEP 735 新标准（uv 支持）")

    print("\n  uv 的写法：")
    print("     uv add fastapi              # 运行时依赖")
    print("     uv add --dev pytest         # 开发依赖")
    print("     uv add --group docs mkdocs  # 自定义分组")
    print("     uv sync --no-dev            # 生产环境装依赖")

    print("\n  锁文件：")
    print("     uv.lock / poetry.lock / requirements.txt（带 hash）")
    print("     ⚠️ 必须提交到 git —— 保证所有环境装到完全相同的版本")
    print("     ⚠️ 生产镜像用 lock --frozen，不要每次解析")

    print("\n  版本约束写法：")
    print("     >=1.2         最低版本，无上限（库常用，但风险高）")
    print("     >=1.2,<2.0    兼容 semver 的常见写法 ✅")
    print("     ~=1.2.3       等价于 >=1.2.3,<1.3.0")
    print("     ==1.2.3       精确锁定（应用层可用，库不要用）")

    print("\n  [Java 对比]")
    print("     Maven: <scope>compile/test/provided</scope>")
    print("     Python: dependencies / optional-dependencies / dependency-groups")
    print("     [差异] Python 的「开发依赖」不会自动隔离，需要显式分组")


# =============================================================================
# 3. 真实结构校验
# =============================================================================

def demo_verify_layout():
    """在临时目录生成真实 src layout 并验证可导入。"""
    print("\n=== 6. 真实结构验证 ===")
    import tempfile
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg = root / "src" / "demo_service"
        (pkg / "api").mkdir(parents=True)
        (pkg / "services").mkdir()

        (pkg / "__init__.py").write_text(
            'from .services.orders import place_order\n'
            '__all__ = ["place_order"]\n'
            '__version__ = "0.1.0"\n',
            encoding="utf-8",
        )
        (pkg / "py.typed").write_text("", encoding="utf-8")
        (pkg / "api" / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "api" / "routes.py").write_text(
            "from demo_service import place_order\n"
            "def handle(): return place_order()\n",
            encoding="utf-8",
        )
        (pkg / "services" / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "services" / "orders.py").write_text(
            "def place_order(): return 'order placed'\n",
            encoding="utf-8",
        )

        # 用 PYTHONPATH 模拟安装后状态
        code = (
            "import demo_service\n"
            "from demo_service.api.routes import handle\n"
            "print('version:', demo_service.__version__)\n"
            "print('__all__:', demo_service.__all__)\n"
            "print('call:', handle())\n"
        )
        env = {"PYTHONPATH": str(root / "src"), "PATH": "/usr/bin:/bin"}
        import os
        full_env = {**os.environ, **env}
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, encoding="utf-8",
                           env=full_env)

        print("  生成的目录树:")
        for p in sorted(root.rglob("*")):
            rel = p.relative_to(root)
            if p.is_file() and "__pycache__" not in rel.parts:
                print(f"     {rel}")
        print("\n  导入验证:")
        for line in (r.stdout or r.stderr).strip().splitlines()[:6]:
            print(f"     {line}")

    print("\n  [要点] __init__.py 导出 place_order 后，")
    print("         下游只需 from demo_service import place_order，")
    print("         不依赖内部文件结构——重构时不会破坏调用方")


def demo_private_packages():
    """内部私有包。"""
    print("\n=== 7. 内部私有包分发 ===")

    print("  三种方式：")
    print("    ① git 依赖（最简单）")
    print("       dependencies = [\"acme-core @ git+https://git.corp/acme/core.git@v1.2.0\"]")
    print("    ② 私有 PyPI（devpi / Artifactory / AWS CodeArtifact）")
    print("       [tool.uv.index]")
    print("       url = \"https://pypi.corp/simple\"")
    print("    ③ 共享目录 + pip install -e（仅开发期）")

    print("\n  [Java 对比] 对应 Maven 私服 Nexus/Artifactory + <repositories>")

    print("\n  ⚠️ 安全提醒：")
    print("     pip 默认会执行 setup.py（老式包），装未审计的包等于执行代码")
    print("     私有源请配认证，不要把 token 写进 pyproject.toml")


def print_java_mapping():
    print("\n=== 8. Java 对照总表 ===")
    rows = [
        ("概念", "Python", "Java"),
        ("项目配置", "pyproject.toml", "pom.xml / build.gradle"),
        ("源码目录", "src/<pkg>/", "src/main/java"),
        ("测试目录", "tests/", "src/test/java"),
        ("构建生命周期", "无（工具各自为政）", "compile→test→package→deploy"),
        ("依赖锁定", "uv.lock / poetry.lock", "pom 版本 + dependencyManagement"),
        ("多模块", "uv workspace", "multi-module / Gradle subprojects"),
        ("接口抽象", "Protocol + 构造注入", "@Autowired + interface"),
        ("插件机制", "entry-points", "ServiceLoader / SPI"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 66)
    print("工业级项目结构与依赖管理")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 66)

    demo_single_package()
    demo_layered_architecture()
    demo_monorepo()
    demo_pyproject()
    demo_dependency_groups()
    demo_verify_layout()
    demo_private_packages()
    print_java_mapping()

    print("\n" + "=" * 66)
    print("所有 demo 运行完成！")
    print("=" * 66)


if __name__ == "__main__":
    main()
