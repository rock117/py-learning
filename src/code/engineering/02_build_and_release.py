# -*- coding: utf-8 -*-
"""
02_build_and_release.py - 构建、版本管理与发布

本文件面向有丰富 Java 经验的开发者，讲清楚「从源码到可分发产物」的完整链路。

和 Java 的核心差异
------------------
Java: mvn package 产出 jar，deploy 推到 Maven Central，jar 是自包含的运行时单元。
Python: build 产出 sdist（源码包）+ wheel（预编译包），publish 推到 PyPI，
        wheel 只是「文件集合 + 元数据」，依赖要单独解析安装。

覆盖
----
1.  包管理工具全景（pip / uv / poetry / pipx / conda）
2.  构建产物：sdist vs wheel
3.  版本号管理（semver + 单一来源）
4.  构建与发布的完整命令链
5.  发布前检查清单
6.  私服发布

[注意] 本文件不会真的发布任何东西。
       uv 已安装时会真实执行一次本地 build 演示；否则打印命令。
"""

import sys
import tempfile
import shutil
import subprocess
import textwrap
from pathlib import Path


# =============================================================================
# 1. 包管理工具全景
# =============================================================================

TOOL_MATRIX = [
    ("工具", "定位", "Java 对应", "何时用"),
    ("pip", "最基础的安装器", "无（JDK 自带 jar 工具）", "脚本、CI 里的最小依赖"),
    ("uv", "极快的安装器 + 环境 + 锁 + 构建", "Maven + sdkman 合体", "几乎所有新项目"),
    ("poetry", "依赖管理 + 打包 + 发布一体", "Maven（更接近）", "需要成熟工作流、团队已在用"),
    ("pipx", "把 CLI 工具装到隔离环境", "类似安装全局命令行工具", "装 ruff / black / poetry 本身"),
    ("conda / mamba", "跨语言环境 + 二进制依赖", "无", "数据科学、需要非 Python 二进制依赖"),
    ("hatch", "项目模板 + 构建后端", "Maven archetype + 插件", "用 hatchling 作为 build backend"),
    ("setuptools", "老牌构建后端", "maven-compiler-plugin", "存量项目、兼容性要求"),
    ("twine", "上传到 PyPI 的经典工具", "mvn deploy", "手动校验后发布"),
]


def demo_tool_matrix():
    """包管理工具对比。"""
    print("=== 1. 包管理工具全景 ===")
    widths = [max(len(str(r[i])) for r in TOOL_MATRIX) for i in range(4)]
    for idx, row in enumerate(TOOL_MATRIX):
        print("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))

    print("\n  uv 为什么成为默认选择：")
    print("    - 安装速度比 pip 快 10~100 倍（Rust 实现 + 全局缓存硬链接）")
    print("    - 一个工具覆盖：venv + pip + pip-tools + pipx + build + publish")
    print("    - 兼容 pyproject.toml 与现有 requirements.txt")
    print("    - 跨平台一致的解析与锁定")

    print("\n  poetry vs uv 的取舍：")
    print("    poetry: 生态成熟、lock 稳定、内置 publish；但解析较慢、历史上与 PEP 标准有偏差")
    print("    uv:     更快、更贴近标准、可当 pip 替代；生态还在快速演进")

    print("\n  [Java 对比]")
    print("    Maven 一个工具搞定生命周期；Python 是「一堆单职责工具 + 一个编排器」")
    print("    pip  ≈ 只做 dependency resolution + install（无生命周期概念）")
    print("    uv   ≈ 最接近 Maven 的一站式体验，但仍不做「编译」")


# =============================================================================
# 2. 构建产物
# =============================================================================

def demo_artifacts():
    """sdist vs wheel。"""
    print("\n=== 2. 构建产物：sdist vs wheel ===")

    rows = [
        ("产物", "内容", "安装时", "平台相关"),
        ("sdist (.tar.gz)", "源码 + pyproject.toml", "现场构建，可能需编译器", "否"),
        ("wheel (.whl)", "预构建的文件集合 + 元数据", "直接解压复制", "可选（纯 Python 时通用）"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(4)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))

    print("\n  wheel 文件名编码了关键信息：")
    print("     my_service-0.1.0-py3-none-any.whl")
    print("       ^name  ^ver   ^py  ^abi ^platform")
    print("     - py3-none-any      纯 Python，任何平台通用")
    print("     - cp312-cp312-win_amd64   CPython 3.12 + Windows x64")
    print("     - cp312-abi3-manylinux   ABI3 稳定接口，Linux 通用")

    print("\n  [Java 对比]")
    print("     jar ≈ wheel（分发单元），但 jar 含编译后 class，可跨平台")
    print("     sdist ≈ 源码 jar（更接近 sources jar，但要现场构建）")
    print("     [关键] Python 没有「字节码 + 依赖打包成唯一产物」的默认习惯；")
    print("            Docker 镜像才是真正对齐 fat-jar 的方案")

    print("\n  为什么优先 wheel：")
    print("     - 无构建步骤，CI/生产安装快一个数量级")
    print("     - 避免用户机器缺编译器/头文件导致的失败")
    print("     - 纯 Python 项目也建议同时发布两种")


# =============================================================================
# 3. 版本管理
# =============================================================================

def demo_versioning():
    """版本号单一来源。"""
    print("\n=== 3. 版本号管理 ===")

    print("  语义化版本（semver）：MAJOR.MINOR.PATCH")
    print("     MAJOR  不兼容的 API 变更")
    print("     MINOR  向后兼容的新功能")
    print("     PATCH  向后兼容的 bug 修复")
    print("     预发布: 1.0.0a1 / 1.0.0rc1   （PEP 440 后缀）")

    print("\n  ⚠️ 版本号只能有一个来源，不要在多处手写：")

    print("\n  ✅ 方式一：pyproject.toml 里写死，运行时读取元数据")
    code = '''
    # pyproject.toml
    [project]
    version = "0.1.0"

    # src/my_service/__init__.py
    from importlib.metadata import version
    __version__ = version("my-service")     # 不要手写字符串
    '''
    print(textwrap.indent(code.strip("\n"), "  "))

    print("\n  ✅ 方式二：动态版本（从 git tag 推导）")
    code2 = '''
    [project]
    dynamic = ["version"]

    [tool.hatch.version]
    source = "vcs"          # hatch-vcs：从 git tag 生成版本

    [tool.hatch.build.hooks.vcs]
    version-file = "src/my_service/_version.py"
    '''
    print(textwrap.indent(code2.strip("\n"), "  "))

    # 真实读取当前环境里已安装包的版本
    from importlib.metadata import version as pkg_version, PackageNotFoundError
    print("\n  真实演示 importlib.metadata.version：")
    for name in ("pip", "setuptools", "pydantic", "nonexistent-pkg-xyz"):
        try:
            print(f"     {name:<18} -> {pkg_version(name)}")
        except PackageNotFoundError:
            print(f"     {name:<18} -> PackageNotFoundError（未安装时这样处理）")

    print("\n  [Java 对比]")
    print("     Maven: <version> 在 pom 里，${project.version} 引用")
    print("     Python: pyproject 或 git tag，运行时用 importlib.metadata 读")
    print("     [差异] Python 包安装后的目录名不含版本号，靠 *.dist-info 目录记录")


# =============================================================================
# 4. 构建与发布命令链
# =============================================================================

def demo_build_commands():
    """完整命令链，并真实跑一次 uv build。"""
    print("\n=== 4. 构建命令链 ===")

    print("  uv（推荐）：")
    print("     uv build              # 同时产出 sdist + wheel 到 dist/")
    print("     uv build --wheel      # 只构建 wheel")
    print("     uv publish            # 发布到 PyPI（需 PYPI_TOKEN）")
    print("     uv publish --index-url https://pypi.corp/simple   # 发私服")

    print("\n  poetry：")
    print("     poetry build")
    print("     poetry publish")

    print("\n  传统方式（twine）：")
    print("     python -m build                 # 需 pip install build")
    print("     twine check dist/*              # 校验元数据与 README 渲染")
    print("     twine upload dist/*")

    print("\n  ⚠️ 发布是不可逆的：")
    print("     PyPI 上同名版本【不能覆盖】，只能换版本号或 yank")
    print("     发布前务必在 TestPyPI 演练：")
    print("     uv publish --publish-url https://test.pypi.org/legacy/")

    # 真实执行一次本地 build（不发布）
    print("\n  ---- 真实构建演示 ----")
    if not shutil.which("uv"):
        print("  [跳过] 未安装 uv。安装后可实际执行 uv build")
        return

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg = root / "src" / "demo_build_pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")

        (root / "pyproject.toml").write_text(
            '[build-system]\n'
            'requires = ["hatchling"]\n'
            'build-backend = "hatchling.build"\n\n'
            '[project]\n'
            'name = "demo-build-pkg"\n'
            'version = "0.1.0"\n'
            'description = "build demo"\n'
            'requires-python = ">=3.10"\n',
            encoding="utf-8",
        )
        (root / "README.md").write_text("# demo\n", encoding="utf-8")

        r = subprocess.run(["uv", "build"], cwd=root,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        out = (r.stdout + r.stderr).strip().splitlines()
        for line in out[-6:]:
            print(f"     {line}")

        dist = root / "dist"
        if dist.exists():
            print("\n     产出:")
            for f in sorted(dist.iterdir()):
                print(f"       {f.name}  ({f.stat().st_size} bytes)")


# =============================================================================
# 5. 发布前检查清单
# =============================================================================

CHECKLIST = [
    ("项目", "检查项", "命令 / 说明"),
    ("元数据", "name/version/description/license 齐全", "见 pyproject.toml"),
    ("元数据", "README 能在 PyPI 正常渲染", "twine check dist/*"),
    ("构建", "sdist 与 wheel 都能构建", "uv build"),
    ("构建", "wheel 里有 py.typed（如需类型）", "unzip -l dist/*.whl"),
    ("测试", "全部测试通过", "pytest"),
    ("测试", "在「干净环境」装 wheel 后能导入", "pip install dist/*.whl 后 python -c 'import x'"),
    ("质量", "lint 与类型检查通过", "ruff check . && mypy src"),
    ("兼容", "声明并测试最低 Python 版本", "tox / CI matrix"),
    ("安全", "依赖无已知漏洞", "uv audit / pip-audit"),
    ("版本", "git tag 与版本号一致", "git tag v0.1.0"),
    ("演练", "先发 TestPyPI 验证", "uv publish --publish-url <testpypi>"),
]


def demo_checklist():
    """发布前检查清单。"""
    print("\n=== 5. 发布前检查清单 ===")
    widths = [max(len(str(r[i])) for r in CHECKLIST) for i in range(3)]
    for idx, row in enumerate(CHECKLIST):
        print("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))

    print("\n  [要点] 「在干净环境装 wheel 后能导入」是最容易漏的一步——")
    print("         src layout 能帮你避免「本地能跑、装完缺文件」")


def demo_private_registry():
    """私服发布。"""
    print("\n=== 6. 私服发布 ===")

    print("  配置私有索引（uv）：")
    cfg = '''
    [[tool.uv.index]]
    name = "corp"
    url = "https://pypi.corp.example.com/simple"
    publish-url = "https://pypi.corp.example.com/legacy/"
    explicit = true          # 只有显式指定时才从这个源找
    '''
    print(textwrap.indent(cfg.strip("\n"), "  "))

    print("\n  认证方式（不要写进仓库）：")
    print("     UV_INDEX_CORP_USERNAME / UV_INDEX_CORP_PASSWORD 环境变量")
    print("     ~/.netrc 或 keyring")

    print("\n  [Java 对比]")
    print("     Maven: <repositories> + <distributionManagement> + settings.xml")
    print("     Python: tool.uv.index + 环境变量认证")

    print("\n  ⚠️ explicit = true 很重要：否则 pip 会把公有 PyPI 和私服混合解析，")
    print("     容易造成「依赖混淆攻击」（dependency confusion）")


def print_java_mapping():
    print("\n=== 7. Java 对照总表 ===")
    rows = [
        ("环节", "Python", "Java"),
        ("依赖解析", "uv lock", "mvn dependency:resolve"),
        ("构建", "uv build", "mvn package"),
        ("产物", "sdist + wheel", "jar"),
        ("校验", "twine check", "mvn verify"),
        ("发布", "uv publish", "mvn deploy"),
        ("仓库", "PyPI / 私服", "Maven Central / Nexus"),
        ("不可覆盖", "同名版本禁止重发", "同样禁止（release 仓库）"),
        ("可执行分发", "Docker 镜像", "fat jar / Docker"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 66)
    print("构建、版本管理与发布")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 66)

    demo_tool_matrix()
    demo_artifacts()
    demo_versioning()
    demo_build_commands()
    demo_checklist()
    demo_private_registry()
    print_java_mapping()

    print("\n" + "=" * 66)
    print("所有 demo 运行完成！")
    print("=" * 66)


if __name__ == "__main__":
    main()
