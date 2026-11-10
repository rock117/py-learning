"""
11 - 包管理与生态
=================
本节目标：
  1. pyproject.toml 结构说明（PEP 517/518，对比 Java pom.xml/build.gradle）
  2. uv 包管理器介绍
  3. poetry 依赖管理
  4. venv/virtualenv 虚拟环境
  5. pipx 安装 CLI 工具
  6. ruff linter + formatter
  7. pytest 测试框架基础（对比 JUnit）
  8. 演示如何创建一个包结构

对应 Java 概念：
  - pyproject.toml ≈ pom.xml (Maven) / build.gradle (Gradle)
  - venv ≈ 不存在直接对应（Java 靠 Maven/Gradle 隔离依赖）
  - pipx ≈ sdkman / brew 安装 CLI
  - ruff ≈ checkstyle + spotless
  - pytest ≈ JUnit 5

注意：本文件主要是说明性代码，演示配置和命令，不实际执行安装。
"""

import sys
import subprocess
import textwrap


# ---------------------------------------------------------------------------
# 1. pyproject.toml 结构说明
# ---------------------------------------------------------------------------
PYPROJECT_TOML_EXAMPLE = """\
[build-system]
# PEP 517/518：声明构建后端
# Java 对比：pom.xml 的 <build><plugins> 或 Gradle 的 plugins{}
requires = ["setuptools>=61.0"]   # 构建依赖（类似 Maven 依赖）
build-backend = "setuptools.build_meta"  # 构建后端

[project]
# 项目元数据（PEP 621）
name = "my-package"          # 类似 Maven groupId+artifactId
version = "1.0.0"            # 类似 Maven <version>
description = "示例包"
readme = "README.md"
requires-python = ">=3.10"   # 类似 Java 的 sourceCompatibility
license = {text = "MIT"}
authors = [{name = "Author", email = "a@b.com"}]

# 运行时依赖，类似 Maven <dependencies>
dependencies = [
    "requests>=2.28",
    "pydantic>=2.0",
]

# 可选依赖（extras），类似 Maven 的 optional / Gradle 的 feature variants
[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1"]
docs = ["sphinx>=7.0"]

# 命令行入口点，类似 Java 的 mainClass
[project.scripts]
my-cli = "my_package.cli:main"

# 工具配置（ruff、pytest 等都集中在这里，类似 .editorconfig + checkstyle.xml）
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""


def demo_pyproject():
    print("\n=== 1. pyproject.toml 结构说明 ===")
    print("  pyproject.toml 是现代 Python 项目的标准配置文件（PEP 517/518/621）")
    print("  完整示例（见源码中的 PYPROJECT_TOML_EXAMPLE 字符串）：")
    # 只打印关键部分
    for line in PYPROJECT_TOML_EXAMPLE.splitlines()[:15]:
        print(f"    {line}")
    print("    ...")
    print("  Java 对比：")
    print("    - [build-system] ≈ pom.xml 的构建插件配置")
    print("    - [project] ≈ pom.xml 的 <groupId>/<artifactId>/<version>")
    print("    - dependencies ≈ <dependencies>")
    print("    - [project.scripts] ≈ Maven 的 mainClass 配置")


# ---------------------------------------------------------------------------
# 2. uv 包管理器介绍
# ---------------------------------------------------------------------------
def demo_uv():
    print("\n=== 2. uv 包管理器 ===")
    print("  uv 是 Astral 用 Rust 写的超快包管理器（替代 pip + venv + pip-tools）")
    print("  常用命令：")
    print("    uv init my-project          # 初始化项目（类似 npm init）")
    print("    uv add requests             # 添加依赖（类似 npm install pkg）")
    print("    uv remove requests           # 移除依赖")
    print("    uv sync                      # 同步依赖到 uv.lock")
    print("    uv run python script.py     # 在项目环境里运行")
    print("    uv pip install pkg           # 兼容 pip 接口")
    print("    uv venv                      # 创建虚拟环境")
    print("  优势：比 pip 快 10-100 倍，全局缓存，自带 venv 管理")
    print("  Java 对比：类似 Gradle 的依赖解析 + 缓存机制")


# ---------------------------------------------------------------------------
# 3. poetry 依赖管理
# ---------------------------------------------------------------------------
def demo_poetry():
    print("\n=== 3. poetry 依赖管理 ===")
    print("  poetry 是流行的依赖管理 + 打包工具（类似 uv 但更早出现）")
    print("  常用命令：")
    print("    poetry init                 # 交互式创建 pyproject.toml")
    print("    poetry add requests          # 添加依赖，写入 pyproject.toml")
    print("    poetry add --group dev pytest  # 添加开发依赖")
    print("    poetry install               # 安装所有依赖")
    print("    poetry run python script.py  # 在虚拟环境运行")
    print("    poetry build                 # 构建 sdist + wheel")
    print("    poetry publish                # 发布到 PyPI")
    print("  poetry.lock 锁定版本，类似 Maven 的 pom.xml 锁定 + Gradle lockfile")


# ---------------------------------------------------------------------------
# 4. venv / virtualenv 虚拟环境
# ---------------------------------------------------------------------------
def demo_venv():
    print("\n=== 4. venv / virtualenv 虚拟环境 ===")
    print("  venv 是 Python 内置的虚拟环境工具（3.3+）")
    print("  virtualenv 是第三方增强版（更快，支持更多 Python 版本）")
    print("  常用命令：")
    print("    python -m venv .venv         # 创建虚拟环境到 .venv 目录")
    print("    .venv\\Scripts\\activate       # Windows 激活")
    print("    source .venv/bin/activate    # Linux/Mac 激活")
    print("    deactivate                   # 退出虚拟环境")
    print("  Java 对比：Java 没有内置虚拟环境概念，靠 Maven/Gradle 隔离")
    print("  当前 Python 解释器路径（说明虚拟环境生效）：")
    print(f"    sys.executable = {sys.executable}")
    print(f"    sys.prefix = {sys.prefix}")


# ---------------------------------------------------------------------------
# 5. pipx 安装 CLI 工具
# ---------------------------------------------------------------------------
def demo_pipx():
    print("\n=== 5. pipx 安装 CLI 工具 ===")
    print("  pipx 专门安装 Python 写的命令行工具，每个工具独立环境，互不污染")
    print("  常用命令：")
    print("    pipx install black           # 安装 black 到独立环境")
    print("    pipx install ruff             # 安装 ruff")
    print("    pipx run cowsay 'hello'        # 临时运行，不安装")
    print("    pipx upgrade black             # 升级")
    print("    pipx list                      # 列出已装工具")
    print("  Java 对比：类似 sdkman 安装 CLI 工具，或 brew install")
    print("  原则：应用用 pipx，库依赖用 uv/poetry，不要全局 pip install")


# ---------------------------------------------------------------------------
# 6. ruff linter + formatter
# ---------------------------------------------------------------------------
def demo_ruff():
    print("\n=== 6. ruff linter + formatter ===")
    print("  ruff 是 Rust 写的超快 linter + formatter（替代 flake8 + black + isort）")
    print("  常用命令：")
    print("    ruff check .                 # 检查代码（lint）")
    print("    ruff check --fix .            # 自动修复")
    print("    ruff format .                 # 格式化代码（替代 black）")
    print("    ruff check --select E,F,W .   # 只检查特定规则")
    print("  配置在 pyproject.toml 的 [tool.ruff] 段：")
    print("    [tool.ruff]")
    print("    line-length = 100")
    print("    [tool.ruff.lint]")
    print('    select = ["E", "F", "I", "UP"]  # 规则集')
    print("  Java 对比：ruff ≈ checkstyle（lint）+ spotless（format）")
    print("  优势：比 flake8 快 50-200 倍，一个工具搞定 lint + format")


# ---------------------------------------------------------------------------
# 7. pytest 测试框架基础
# ---------------------------------------------------------------------------
def demo_pytest():
    print("\n=== 7. pytest 测试框架基础 ===")
    print("  pytest 是 Python 最流行的测试框架，对比 JUnit 5")
    print("  特点：用 assert 语句，无需 self.assertEqual")
    print("  常用命令：")
    print("    pytest                        # 运行所有测试")
    print("    pytest -v                    # 详细输出")
    print("    pytest -k 'test_add'          # 按名字过滤")
    print("    pytest --cov=my_package       # 覆盖率")
    print("    pytest -x                     # 失败即停")

    # 演示一个典型的 pytest 测试文件内容
    test_example = textwrap.dedent("""\
        # test_calc.py —— pytest 测试文件
        import pytest
        from calc import add, divide

        def test_add():
            assert add(1, 2) == 3          # 比 JUnit 的 assertEquals 简洁

        def test_divide_by_zero():
            with pytest.raises(ZeroDivisionError):  # 类似 assertThrows
                divide(1, 0)

        @pytest.mark.parametrize("a,b,expected", [   # 参数化测试
            (1, 2, 3), (0, 0, 0), (-1, 1, 0),
        ])
        def test_add_params(a, b, expected):
            assert add(a, b) == expected

        @pytest.fixture                # 类似 JUnit 的 @BeforeEach
        def sample_data():
            return [1, 2, 3]

        def test_with_fixture(sample_data):
            assert sum(sample_data) == 6
    """)
    print("  典型测试文件示例：")
    for line in test_example.splitlines():
        print(f"    {line}")


# ---------------------------------------------------------------------------
# 8. 演示：创建一个包结构
# ---------------------------------------------------------------------------
PACKAGE_STRUCTURE = """\
my-package/
├── pyproject.toml          # 项目配置（必须）
├── README.md
├── LICENSE
├── .gitignore
├── src/                    # src layout（推荐，避免导入混淆）
│   └── my_package/
│       ├── __init__.py     # 包入口，定义 __version__ 等
│       ├── core.py         # 核心代码
│       ├── cli.py          # 命令行入口
│       └── py.typed        # 空文件，声明支持类型检查（PEP 561）
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── conftest.py         # pytest 共享 fixture
└── docs/
    └── index.md
"""


def demo_package_structure():
    print("\n=== 8. 标准包结构 ===")
    print("  推荐的 src layout 结构：")
    for line in PACKAGE_STRUCTURE.splitlines():
        print(f"    {line}")
    print("  关键文件说明：")
    print("    - __init__.py：标记目录为包，可定义 __all__、__version__")
    print("    - py.typed：空文件，告诉类型检查器本包支持 type hints")
    print("    - conftest.py：pytest 的共享 fixture，自动发现")
    print("  Java 对比：src/main/java/... 对应 src/my_package/，")
    print("            src/test/java/... 对应 tests/")


# ---------------------------------------------------------------------------
# 9. 实际演示：检查当前环境
# ---------------------------------------------------------------------------
def demo_check_environment():
    print("\n=== 9. 检查当前环境 ===")
    print(f"  Python 版本: {sys.version}")
    print(f"  平台: {sys.platform}")
    print(f"  可执行文件: {sys.executable}")

    # 检查是否安装了常用工具（不实际运行，只说明）
    print("  常用工具检查（仅说明，不实际运行）：")
    tools = ["uv", "poetry", "ruff", "pytest", "pipx"]
    for tool in tools:
        print(f"    - {tool}: 用 '{tool} --version' 检查是否安装")


# ---------------------------------------------------------------------------
# 10. 构建与发布流程
# ---------------------------------------------------------------------------
def demo_build_publish():
    print("\n=== 10. 构建与发布流程 ===")
    print("  构建包：")
    print("    uv build            # uv 构建 sdist + wheel")
    print("    poetry build        # poetry 构建")
    print("    python -m build     # 标准 PEP 517 构建（需装 build 包）")
    print("  发布到 PyPI：")
    print("    uv publish          # uv 发布")
    print("    poetry publish      # poetry 发布")
    print("    twine upload dist/* # 传统方式")
    print("  Java 对比：")
    print("    - 构建 wheel ≈ mvn package 生成 jar")
    print("    - 发布 PyPI ≈ mvn deploy 到 Maven Central")
    print("    - PyPI 是全局唯一仓库，Maven 有 Central + 私服")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("11 - 包管理与生态")
    print("=" * 60)

    demo_pyproject()
    demo_uv()
    demo_poetry()
    demo_venv()
    demo_pipx()
    demo_ruff()
    demo_pytest()
    demo_package_structure()
    demo_check_environment()
    demo_build_publish()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - pyproject.toml 是现代 Python 项目标准配置（PEP 517/518/621）")
    print("  - uv 是最快的包管理器，poetry 是成熟的全流程工具")
    print("  - venv 隔离环境，pipx 装 CLI 工具")
    print("  - ruff 一个工具搞定 lint + format（替代 flake8+black+isort）")
    print("  - pytest 用 assert 语句，比 JUnit 简洁")
    print("  - src layout 是推荐的项目结构")
    print("=" * 60)


if __name__ == "__main__":
    main()
