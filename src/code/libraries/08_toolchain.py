# -*- coding: utf-8 -*-
"""
08_toolchain.py - Python 工程化工具链

本文件面向有丰富 Java 经验的开发者，讲解 Python 项目的"工程基建"：
    - pytest      ：测试框架（对比 JUnit 5 / AssertJ / Mockito）
    - ruff        ：lint + 格式化（对比 Checkstyle + Spotless，但快 100 倍）
    - mypy        ：静态类型检查（对比 javac，但可选、渐进式）
    - pyproject.toml：统一项目配置（对比 Maven pom.xml / Gradle build.gradle）
    - uv / poetry ：依赖与虚拟环境管理（对比 Maven / Gradle 的依赖管理）
    - pre-commit  ：提交前钩子（对比 Git hooks + Spotless 的 pre-commit）

[说明] 本文件不依赖 pytest 可直接运行：
       - 若安装了 pytest，则真正执行一组测试并打印结果；
       - 若没安装，会打印 pytest 标准写法 + 说明如何安装，exit code 仍为 0。
       - 类型检查 / lint / 依赖管理部分以"配置示例 + 命令"形式展示。

运行：
    python 08_toolchain.py
"""

import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


# =============================================================================
# 第一部分：pytest
# =============================================================================
# [Java 对比]
#   pytest 的 assert           ~ AssertJ（失败信息自动展开，比 JUnit assertEquals 好用）
#   @pytest.fixture            ~ @BeforeEach + 依赖注入（scope 可跨测试复用）
#   @pytest.mark.parametrize   ~ @ParameterizedTest + @CsvSource
#   monkeypatch                ~ Mockito mock，但更轻量
#   pytest.raises              ~ assertThrows

SAMPLE_TESTS = '''
import pytest


# ---- 被测代码 ----
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("b 不能为 0")
    return a / b


def parse_age(s):
    return int(s)


# ---- 1. 基本断言 ----
def test_divide_ok():
    assert divide(10, 2) == 5
    assert divide(1, 3) == pytest.approx(0.3333, rel=1e-3)


# ---- 2. 异常断言 ----
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError, match="不能为 0"):
        divide(1, 0)


# ---- 3. 参数化 ----
@pytest.mark.parametrize("raw, expected", [
    ("18", 18),
    ("0", 0),
    ("100", 100),
])
def test_parse_age(raw, expected):
    assert parse_age(raw) == expected


@pytest.mark.parametrize("bad", ["abc", "", "1.5"])
def test_parse_age_invalid(bad):
    with pytest.raises(ValueError):
        parse_age(bad)


# ---- 4. fixture（依赖注入，scope 可共享） ----
class FakeDB:
    def __init__(self):
        self.rows = []

    def add(self, row):
        self.rows.append(row)

    def count(self):
        return len(self.rows)


@pytest.fixture
def db():
    d = FakeDB()
    yield d          # yield 之前是 setup，之后是 teardown
    d.rows.clear()


def test_db_add(db):
    db.add({"id": 1})
    assert db.count() == 1


def test_db_isolation(db):
    # 每个测试拿到新的 db，互不污染
    assert db.count() == 0


# ---- 5. monkeypatch 打补丁 ----
def current_env():
    import os
    return os.environ.get("APP_ENV", "dev")


def test_env_override(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    assert current_env() == "prod"
'''


def demo_pytest():
    """在临时目录写测试文件并运行 pytest（未安装则打印写法）。"""
    print("=== 1. pytest ===")
    try:
        import pytest  # noqa: F401
        has_pytest = True
    except ImportError:
        has_pytest = False

    if not has_pytest:
        print("  [注意] 未安装 pytest，下面展示标准写法（pip install pytest 后可实际运行）")
        print(textwrap.indent(SAMPLE_TESTS.strip(), "    "))
        print("\n  运行命令: pytest -v            # 详细输出")
        print("           pytest -k \"test_db\"  # 按名字筛选")
        print("           pytest --cov=src     # 覆盖率 (pip install pytest-cov)")
        return

    with tempfile.TemporaryDirectory() as tmp:
        test_file = Path(tmp) / "test_sample.py"
        test_file.write_text(SAMPLE_TESTS, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-q", "--no-header", "-p", "no:cacheprovider"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=tmp,
        )
        tail = (proc.stdout or "").strip().splitlines()[-6:]
        print("  pytest 输出:")
        for line in tail:
            print("    " + line)
    print("  [Java 对比] @BeforeEach/assertThrows/@ParameterizedTest/Mockito 一一对应")
    print("  [要点] 断言直接用 assert，pytest 会把表达式值展开，不需要 assertThat")


# =============================================================================
# 第二部分：ruff —— lint + format
# =============================================================================
# [Java 对比] ruff ~ Checkstyle + PMD + Spotless（可自动修复）
#             由 Rust 编写，毫秒级，规则集涵盖 pycodestyle/pyflakes/isort/bugbear 等。

BAD_CODE = '''
import os, sys,json
from typing import *

def   process( data ,list = [] ):
    if data == None:
        return []
    list.append(data)
    for i in range(0,len(data)):
        if data[i] != None:
            print( "item"+str(data[i]) )
    x=1
    return list

class foo:
  def Bar(self): pass
'''
# 上面故意堆满常见问题：== None、可变默认参数、未使用导入、range(len())、
# 字符串拼接、单行多导入、命名不规范（foo/Bar）、缺少空格。


def demo_ruff():
    """ruff check / ruff format 演示（无网络，仅在本地临时文件上跑）。"""
    print("\n=== 2. ruff（lint + format）===")
    print("  典型问题代码（故意写得很糟）:")
    print(textwrap.indent(BAD_CODE.strip(), "    "))

    if not shutil.which("ruff"):
        print("\n  [注意] 未安装 ruff，跳过实际检查。安装: pip install ruff")
        print("  常用命令:")
        print("    ruff check .            # 检查")
        print("    ruff check --fix .      # 检查并自动修复")
        print("    ruff format .           # 格式化（类似 black）")
        print("    ruff check --select ALL # 开启全部规则")
        return

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "bad_code.py"
        target.write_text(BAD_CODE, encoding="utf-8")
        proc = subprocess.run(
            ["ruff", "check", str(target), "--output-format", "concise"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        lines = (proc.stdout or "").strip().splitlines()
        print(f"\n  ruff check 发现 {len(lines)} 条问题（节选）:")
        for line in lines[:10]:
            print("    " + line.replace(tmp, "<tmp>"))
        if len(lines) > 10:
            print(f"    ... 还有 {len(lines) - 10} 条")
    print("  [Java 对比] 相当于 Checkstyle 但配置极简、速度快一个数量级")


# =============================================================================
# 第三部分：mypy —— 静态类型检查
# =============================================================================
# [Java 对比] mypy ~ javac 的类型检查，但 Python 是"渐进类型"：
#             没标注的地方默认不检查（除非 --strict），因此可以逐步加类型。

TYPE_SAMPLE = '''
from typing import Protocol


class Repo(Protocol):
    def get(self, key: str) -> dict[str, str]: ...


def load_config(repo: Repo, key: str) -> int:
    raw = repo.get(key)
    # 故意返回错误类型：声明 int，实际返回 str
    return raw.get("value", "0")
'''

GOOD_SAMPLE = '''
from typing import Protocol


class Repo(Protocol):
    def get(self, key: str) -> dict[str, str]: ...


def load_config(repo: Repo, key: str) -> int:
    raw = repo.get(key)
    return int(raw.get("value", "0"))
'''


def demo_mypy():
    """mypy 类型检查演示。"""
    print("\n=== 3. mypy（静态类型检查）===")
    if not shutil.which("mypy"):
        print("  [注意] 未安装 mypy，跳过实际检查。安装: pip install mypy")
        print("  错误示例（声明返回 int，实际返回 str）:")
        print(textwrap.indent(TYPE_SAMPLE.strip(), "    "))
        print("\n  常用命令: mypy --strict src/")
        return

    with tempfile.TemporaryDirectory() as tmp:
        for name, code in [("bad.py", TYPE_SAMPLE), ("good.py", GOOD_SAMPLE)]:
            path = Path(tmp) / name
            path.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["mypy", str(path), "--no-incremental", "--cache-dir", str(Path(tmp) / "cache")],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            print(f"  mypy {name} -> exit={proc.returncode}")
            for line in (proc.stdout or "").strip().splitlines()[:3]:
                print("    " + line.replace(tmp, "<tmp>"))
    print("  [Java 对比] 相当于 javac 报错，但可选、渐进；配合 pyright/Pylance 用即时反馈")


# =============================================================================
# 第四部分：pyproject.toml 与依赖管理（uv / poetry）
# =============================================================================

PYPROJECT_SAMPLE = '''
[project]
name = "my-service"
version = "0.1.0"
description = "示例服务"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "pydantic>=2.8",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6", "mypy>=1.11"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# ---------- 工具配置统一放在这里 ----------
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]   # E/F: pycodestyle+pyflakes, I: isort, UP: pyupgrade

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"
'''


def demo_project_config():
    """pyproject.toml 示例与依赖管理命令。"""
    print("\n=== 4. pyproject.toml 与依赖管理 ===")
    print("  现代 Python 项目用 pyproject.toml 统一所有配置:")
    print(textwrap.indent(PYPROJECT_SAMPLE.strip(), "    "))

    print("\n  耗时对比（Maven/Gradle 开发者最有感触的一点）:")
    rows = [
        ("操作", "uv", "pip + venv", "Maven/Gradle"),
        ("创建环境", "uv venv", "python -m venv .venv", "无需"),
        ("安装依赖", "uv sync", "pip install -r req.txt", "mvn install"),
        ("锁定版本", "uv lock (uv.lock)", "pip freeze", "pom.lock / gradle.lockfile"),
        ("新增依赖", "uv add requests", "手改文件再安装", "手改 pom 再 install"),
        ("速度量级", "秒级", "十秒~分钟级", "分钟级（首次）"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    for idx, row in enumerate(rows):
        print("    " + " | ".join(row[i].ljust(widths[i]) for i in range(4)))
        if idx == 0:
            print("    " + "-+-".join("-" * w for w in widths))

    try:
        import importlib.metadata as md
        version = md.version("uv") if _has_dist("uv") else None
    except Exception:
        version = None
    if version:
        print(f"\n  当前环境检测到 uv {version}")
    else:
        print("\n  [注意] uv 是独立可执行程序（pip install uv 或独立安装包），不一定是 Python 包")
    print("  [Java 对比] uv ~ 融合了 Maven 的依赖解析 + NVM 式的多版本管理，速度极快")


def _has_dist(name: str) -> bool:
    try:
        import importlib.metadata as md
        md.distribution(name)
        return True
    except Exception:
        return False


# =============================================================================
# 第五部分：pre-commit
# =============================================================================

PRECOMMIT_SAMPLE = '''
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
        additional_dependencies: [pydantic]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
'''


def demo_pre_commit():
    print("\n=== 5. pre-commit 钩子 ===")
    print("  .pre-commit-config.yaml 示例:")
    print(textwrap.indent(PRECOMMIT_SAMPLE.strip(), "    "))
    print("\n  安装与使用:")
    print("    pip install pre-commit")
    print("    pre-commit install          # 写入 .git/hooks/pre-commit")
    print("    pre-commit run --all-files  # 全量执行一次")
    print("  [Java 对比] 相当于 Spotless/Checkstyle 的 CI 门禁，但提前到本地 commit 阶段")


# =============================================================================
# 第六部分：工具全景速查
# =============================================================================

def print_cheatsheet():
    print("\n=== 6. 工具链速查表 ===")
    rows = [
        ("用途", "Python 工具", "Java 对应"),
        ("测试", "pytest (+ pytest-cov)", "JUnit 5 + JaCoCo"),
        ("断言库", "pytest 内置 assert", "AssertJ"),
        ("Mock", "unittest.mock / pytest-mock", "Mockito"),
        ("Lint / 格式", "ruff", "Checkstyle + Spotless"),
        ("类型检查", "mypy / pyright", "javac"),
        ("依赖管理", "uv / poetry", "Maven / Gradle"),
        ("提交钩子", "pre-commit", "git hooks + CI"),
        ("打包发布", "hatchling / twine", "maven-deploy"),
        ("CI 配置", "GitHub Actions + matrix", "Jenkins / GH Actions"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 60)
    print("Python 工具链演示 (pytest / ruff / mypy / pyproject / pre-commit)")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 60)

    demo_pytest()
    demo_ruff()
    demo_mypy()
    demo_project_config()
    demo_pre_commit()
    print_cheatsheet()

    print("\n" + "=" * 60)
    print("所有 demo 运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
