# -*- coding: utf-8 -*-
"""
07_modules_and_packages.py - 模块与包机制

本文件面向有丰富 Java 经验的开发者，讲透 Python 的导入系统。

和 Java 最大的不同
------------------
Java 的包靠 **目录结构 + package 声明** 静态确定，编译期就固定了。
Python 的包是 **运行时按路径搜索** 出来的，`sys.path` 是个可变 list，
可以在运行时增删——这既是 Python 的灵活之处，也是各种诡异的
ImportError 的来源。

覆盖
----
1.  模块 / 包 / 命名空间包
2.  import 的完整查找顺序（sys.modules -> 内置 -> sys.path）
3.  动态设置包路径（sys.path / PYTHONPATH / .pth）
4.  引入其他目录的 5 种场景
5.  包内 import：绝对 vs 相对
6.  __init__.py / __all__ / 循环导入
7.  python -m 与直接运行的差异（相对导入报错的根因）
8.  importlib 动态导入

[注意] 本文件会在临时目录里创建真实的多层包结构来演示导入行为，
       跑完自动清理。不会改动项目自身文件。
"""

import sys
import os
import tempfile
import textwrap
from pathlib import Path


# =============================================================================
# 1. 模块 / 包 / 命名空间包
# =============================================================================

def demo_module_vs_package():
    """三个层次的概念区分。"""
    print("=== 1. 模块 / 包 / 命名空间包 ===")

    import json
    print(f"  模块（单个 .py）:        {type(json).__name__}")
    print(f"    有 __file__:           {hasattr(json, '__file__')}")

    import os.path
    print(f"  包（含 __init__.py）:     {os.path.__name__}")
    print(f"    有 __path__:           {hasattr(os.path, '__path__')}   <- 包的标志")

    print("\n  判断方式：")
    print("    hasattr(obj, '__path__')  -> 是包（可含子模块）")
    print("    hasattr(obj, '__file__')  -> 是普通模块")

    print("\n  命名空间包（PEP 420，3.3+）：")
    print("    没有 __init__.py，也可以被导入")
    print("    同名目录分散在多个 sys.path 位置时，会被合并成一个包")
    print("    [Java 对比] 类似把多个 jar 里同一个 package 合并——Java 做不到，"
          "会 split package 冲突")

    print("\n  [Java 对比]")
    print("    Java: package com.a.b + 目录结构，编译期固定")
    print("    Python: 运行时按 sys.path 顺序查找第一个匹配")


def demo_import_order():
    """import 的查找顺序。"""
    print("\n=== 2. import 的查找顺序 ===")
    import importlib.util

    print("  当一个 import 语句执行时，按顺序尝试：")
    print("    1. sys.modules 缓存      —— 已导入过的直接返回")
    print("    2. 内置模块              —— sys.builtin_module_names")
    print("    3. sys.path 逐个目录    —— 找到第一个匹配")

    print(f"\n  sys.modules 已缓存模块数: {len(sys.modules)}")
    print(f"  重复 import json 是否同一对象: ", end="")

    import json as j1
    import json as j2
    print(f"{j1 is j2}   <- 走缓存，不会重新执行")

    print("\n  内置模块示例:", sorted(sys.builtin_module_names)[:6], "...")

    print("\n  sys.path 的组成（按顺序）：")
    for i, p in enumerate(sys.path[:5]):
        label = p if p else "<空串：表示当前工作目录>"
        print(f"    [{i}] {label}")
    if len(sys.path) > 5:
        print(f"    ... 共 {len(sys.path)} 项")

    print("\n  sys.path 的前几项来源：")
    print("    [0] 脚本所在目录（直接运行脚本时）或 '' （-m 时是 cwd）")
    print("    [1..] PYTHONPATH 环境变量")
    print("    后面  标准库目录 + site-packages")

    print("\n  [Java 对比] 相当于 classpath，但：")
    print("    - sys.path 是可变 list，运行时可 insert/append")
    print("    - 顺序敏感，先找到的胜出（Java classpath 也是）")
    print("    - 没有编译期检查，模块不存在要到运行时才报错")


# =============================================================================
# 2. 动态设置包路径
# =============================================================================

def demo_sys_path():
    """运行时修改 sys.path。"""
    print("\n=== 3. 动态设置包路径 ===")

    with tempfile.TemporaryDirectory() as tmp:
        # 造一个临时包
        pkg_dir = Path(tmp) / "dynpkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        (pkg_dir / "core.py").write_text(
            "VALUE = 'from dynpkg.core'\n", encoding="utf-8"
        )

        original = list(sys.path)
        try:
            print("  ① 修改前导入尝试：")
            try:
                import dynpkg  # noqa: F401
                print("     意外成功")
            except ImportError:
                print("     ImportError: No module named 'dynpkg'")

            print("\n  ② sys.path.insert(0, tmp) 后：")
            sys.path.insert(0, tmp)
            import dynpkg.core
            print(f"     dynpkg.core.VALUE = {dynpkg.core.VALUE!r}")

            print("\n  ③ sys.path.append(tmp) vs insert(0, tmp)：")
            print("     insert(0) 优先级最高，可能覆盖标准库同名模块")
            print("     append 放最后，更安全")
        finally:
            sys.path[:] = original
            # 清掉已导入的模块，避免污染
            for name in list(sys.modules):
                if name == "dynpkg" or name.startswith("dynpkg."):
                    del sys.modules[name]

        print("\n  ④ 推荐做法对比：")
        print("     ❌ sys.path.append(...) 写在业务代码里 —— 脆弱、污染全局")
        print("     ⚠️  PYTHONPATH 环境变量        —— 适合开发期/容器内")
        print("     ✅ 正确安装包（pip install -e .）—— 生产环境首选")
        print("     ✅ 用 pyproject.toml 声明依赖")
        print("     ✅ 脚本场景用 python -m 而不是直接跑文件")

        print("\n  [Java 对比]")
        print("    Java: -cp / CLASSPATH，启动时指定，运行中基本不动")
        print("    Python: sys.path 是普通 list，随时可改——灵活但危险")
    print()


def demo_pythonpath_and_pth():
    """PYTHONPATH 与 .pth 文件。"""
    print("=== 4. PYTHONPATH 与 .pth 文件 ===")

    print("  PYTHONPATH（环境变量）：")
    print("    作用同 sys.path 追加，但由启动时读取")
    print("    Linux/macOS: export PYTHONPATH=/path/to/lib:$PYTHONPATH")
    print("    Windows:     set PYTHONPATH=C:\\lib;%PYTHONPATH%")
    print(f"    当前 PYTHONPATH: {os.environ.get('PYTHONPATH', '<未设置>')}")
    print("    [Java 对比] 等价于 CLASSPATH")

    print("\n  .pth 文件（site-packages 里的魔法）：")
    print("    在 site-packages 下放一个 xxx.pth，每行一个路径")
    print("    Python 启动时自动把这些路径加进 sys.path")
    print("    [场景] 系统级安装内部包、科学计算环境配置")

    import site
    print(f"\n  当前 site-packages: {site.getsitepackages()[:2]}")
    print(f"  用户级 site: {site.getusersitepackages()}")


# =============================================================================
# 3. 引入其他目录的包
# =============================================================================

def demo_import_other_dirs():
    """五种常见场景。"""
    print("\n=== 5. 引入其他目录的包 ===")

    print("  场景 A：同项目内的兄弟包（推荐结构）")
    print("     myproject/")
    print("     ├── pyproject.toml")
    print("     └── src/")
    print("         ├── mypkg/")
    print("         └── otherpkg/")
    print("     ✅ pip install -e . 后，mypkg 和 otherpkg 都是顶层包")
    print("        from otherpkg import xxx")

    print("\n  场景 B：脚本要引用上级目录的包")
    print("     scripts/")
    print("     └── run.py        <- 想 import ../src/mypkg")
    print("     ❌ 不要 sys.path.append('..')")
    print("     ✅ 用 python -m 从项目根运行:")
    print("        python -m scripts.run")
    print("     ✅ 或先 pip install -e .")

    print("\n  场景 C：monorepo 多个独立包")
    print("     repo/")
    print("     ├── packages/core/      (package: core)")
    print("     └── packages/web/       (package: web)")
    print("     ✅ 各包自己的 pyproject.toml，用 uv workspace / poetry path 依赖:")
    print("        [tool.uv.sources]")
    print("        core = { workspace = true }")

    print("\n  场景 D：插件目录（运行时才发现）")
    print("     plugins/")
    print("     ├── plugin_a.py")
    print("     └── plugin_b.py")
    print("     ✅ importlib 动态加载，见第 8 节")

    print("\n  场景 E：单文件脚本想复用工具函数")
    print("     ❌ 不要复制粘贴")
    print("     ✅ 抽成包 + pip install -e .")
    print("     ✅ 或放同目录直接 import（仅限临时脚本）")

    # 真实演示 B 场景
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "mypkg").mkdir()
        (root / "src" / "mypkg" / "__init__.py").write_text("", encoding="utf-8")
        (root / "src" / "mypkg" / "util.py").write_text(
            "def hello(): return 'hello from mypkg.util'\n", encoding="utf-8"
        )
        (root / "scripts").mkdir()
        (root / "scripts" / "run.py").write_text(
            "import sys\nfrom pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))\n"
            "from mypkg.util import hello\n"
            "print('   ', hello())\n",
            encoding="utf-8",
        )
        import subprocess
        print("\n  实际验证场景 B（sys.path 注入 src）：")
        r = subprocess.run([sys.executable, str(root / "scripts" / "run.py")],
                           capture_output=True, text=True, encoding="utf-8")
        print(r.stdout.rstrip() or f"    失败: {r.stderr.strip().splitlines()[-1]}")

    print()


# =============================================================================
# 4. 包内 import
# =============================================================================

def demo_internal_import():
    """绝对导入 vs 相对导入。"""
    print("=== 6. 包内 import：绝对 vs 相对 ===")

    print("  目录结构：")
    print("     mypkg/")
    print("     ├── __init__.py")
    print("     ├── core.py")
    print("     └── utils/")
    print("         ├── __init__.py")
    print("         └── text.py")

    print("\n  ✅ 绝对导入（推荐）：")
    print("     from mypkg.utils import text")
    print("     from mypkg.utils.text import slugify")
    print("     优点：清晰、可搜索、重构友好、Python 官方推荐")

    print("\n  ⚠️ 相对导入（包内部使用）：")
    print("     from . import core              # 同级模块")
    print("     from .utils import text         # 子包")
    print("     from ..core import foo          # 上上级")
    print("     优点：包改名时不用改 import")
    print("     缺点：不能用于顶层脚本；相对层级容易看晕")

    print("\n  ❌ 绝对不要用的写法：")
    print("     from mypkg import *             # 污染命名空间")
    print("     import mypkg.core as c          # 在包内部（可以但啰嗦）")

    print("\n  [Java 对比]")
    print("     Java 只有一种 import：全限定名（相当于绝对导入）")
    print("     Python 多出的相对导入是为「包可改名/可重定位」服务")

    # 真实演示相对导入在「直接运行」时失败
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg = root / "relpkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "a.py").write_text("VALUE = 'a'\n", encoding="utf-8")
        (pkg / "b.py").write_text(
            "from .a import VALUE\ndef get(): return VALUE\n", encoding="utf-8"
        )
        (pkg / "main.py").write_text(
            "from .b import get\nprint(get())\n", encoding="utf-8"
        )

        import subprocess
        print("\n  ⚠️ 直接运行 python relpkg/main.py：")
        r = subprocess.run([sys.executable, str(pkg / "main.py")],
                           capture_output=True, text=True, encoding="utf-8",
                           cwd=str(root))
        err = r.stderr.strip().splitlines()
        print(f"     {err[-1] if err else r.stdout.strip()}")

        print("\n  ✅ 改用 python -m relpkg.main（从父目录运行）：")
        r2 = subprocess.run([sys.executable, "-m", "relpkg.main"],
                            capture_output=True, text=True, encoding="utf-8",
                            cwd=str(root))
        out = r2.stdout.strip() or r2.stderr.strip().splitlines()[-1]
        print(f"     {out}")

        print("\n  [根因] 直接跑文件时，该文件是「顶层模块 __main__」，")
        print("         没有所属包，相对导入无参照点")
        print("         用 -m 时，Python 先把父目录加进 sys.path，模块知道自己属于 relpkg")
    print()


# =============================================================================
# 5. __init__.py 与 __all__
# =============================================================================

def demo_init_and_all():
    """__init__.py 的作用与 __all__。"""
    print("=== 7. __init__.py 与 __all__ ===")

    print("  __init__.py 的三件事：")
    print("    1. 标记目录为常规包（PEP 420 后非必需，但推荐保留）")
    print("    2. 包首次导入时执行——可做初始化、导出 API")
    print("    3. 定义 __all__ 控制 from pkg import * 的行为")

    print("\n  ✅ 推荐：在 __init__.py 里导出公开 API")
    print("     # mypkg/__init__.py")
    print("     from .core import Client, Config")
    print("     from .errors import MyError")
    print("     __all__ = ['Client', 'Config', 'MyError']")
    print("     __version__ = '1.0.0'")
    print("\n     使用方：from mypkg import Client    （不用知道内部文件结构）")

    print("\n  __all__ 的两个作用：")
    print("    1. from pkg import * 只导入列表里的名字")
    print("    2. 类型检查器/IDE 据此判断公开 API，下划线开头视为私有")

    print("\n  ⚠️ __init__.py 不要做重活：")
    print("     - 不要在里面 import 大量模块（拖慢首次导入）")
    print("     - 不要放副作用代码（写文件、连网络）")
    print("     - 不要在里面改 sys.path（污染全局）")

    # 演示 __all__
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "allpkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text(
            "from .pub import public_func\n"
            "__all__ = ['public_func']\n",
            encoding="utf-8",
        )
        (pkg / "pub.py").write_text(
            "def public_func(): return 'public'\n"
            "def _private(): return 'private'\n",
            encoding="utf-8",
        )
        (pkg / "internal.py").write_text("X = 1\n", encoding="utf-8")

        code = (
            "import sys\n"
            f"sys.path.insert(0, {tmp!r})\n"
            "from allpkg import *\n"
            "print('  import * 得到的名字:', sorted(n for n in dir() if not n.startswith('_')))\n"
        )
        import subprocess
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, encoding="utf-8")
        print(f"\n  实际验证: {r.stdout.strip() or r.stderr.strip()}")
    print()


def demo_circular_import():
    """循环导入的原因与解法。"""
    print("=== 8. 循环导入 ===")

    print("  症状：ImportError: cannot import name 'X' from partially initialized module")
    print("\n  Java 里循环依赖是编译期问题，IDE 会警告；")
    print("  Python 里是运行时问题，有时甚至「碰巧能跑」，更隐蔽。")

    print("\n  三种解法：")
    print("    ① 把 import 移到函数内部（延迟导入）")
    print("       def handle():")
    print("           from .other import helper   # 用到时才导入")
    print("           helper()")
    print("\n    ② 抽取公共依赖到第三个模块（首选）")
    print("       a.py 和 b.py 都依赖 common.py，而不是互相依赖")
    print("\n    ③ 用 TYPE_CHECKING 只做类型标注")
    print("       from typing import TYPE_CHECKING")
    print("       if TYPE_CHECKING:")
    print("           from .other import OtherType   # 运行时不执行")

    print("\n  [要点] 出现循环导入往往说明模块职责划分有问题，")
    print("         优先想「该拆出什么」，而不是急着用延迟导入糊过去")
    print()


# =============================================================================
# 6. importlib 动态导入
# =============================================================================

def demo_importlib():
    """运行时按名字/路径导入。"""
    print("=== 9. importlib 动态导入 ===")
    import importlib

    # ① 按名称导入
    math_mod = importlib.import_module("math")
    print(f"  import_module('math') -> {math_mod.sqrt(16)}")

    # ② 按字符串变量导入（插件场景）
    module_names = ["json", "csv", "base64"]
    loaded = {n: importlib.import_module(n) for n in module_names}
    print(f"  批量按名导入: {list(loaded)}")

    # ③ 按文件路径导入
    with tempfile.TemporaryDirectory() as tmp:
        plugin = Path(tmp) / "my_plugin.py"
        plugin.write_text(
            "NAME = 'demo-plugin'\ndef run(): return 'plugin executed'\n",
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("my_plugin", plugin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(f"\n  按路径加载: NAME={mod.NAME!r}")
        print(f"               run()={mod.run()!r}")

    # ④ 热重载（开发期）
    print("\n  reload（开发期热重载，生产慎用）：")
    print("     importlib.reload(module)")

    print("\n  [常见场景] 插件系统、配置文件指定 handler、测试 mock 替换")
    print("  [Java 对比] 类似 Class.forName() + 反射，但没有 ClassLoader 那套层级")
    print()


def demo_pkgutil_discover():
    """发现子模块（插件自动注册）。"""
    print("=== 10. pkgutil 自动发现 ===")
    import pkgutil

    print("  iter_modules 可列出包里所有子模块：")
    found = [m.name for m in pkgutil.iter_modules(["json"] if False else [])
             if False]  # 占位，避免依赖具体路径
    print("     for m in pkgutil.iter_modules(pkg.__path__):")
    print("         if not m.name.startswith('_'):")
    print("             importlib.import_module(f'{pkg.__name__}.{m.name}')")

    # 用真实包演示
    import xml
    subs = [m.name for m in pkgutil.iter_modules(xml.__path__)]
    print(f"\n  实际: xml 包的子模块 = {subs}")
    print("\n  [场景] 插件目录自动注册、按约定命名批量加载")
    print("  [Java 对比] 类似 ServiceLoader / SPI")
    print()


# =============================================================================
# 7. 陷阱汇总
# =============================================================================

def demo_pitfalls():
    """高频错误。"""
    print("=== 11. 常见陷阱 ===")

    print("  坑 1  直接运行包含相对导入的文件")
    print("        python pkg/main.py  -> ImportError: attempted relative import")
    print("        解法: python -m pkg.main")

    print("\n  坑 2  sys.path 里写相对路径")
    print("        sys.path.append('../lib')  # ❌ 相对于当前工作目录，不稳定")
    print("        解法: 用 Path(__file__).resolve().parent / 'lib'")

    print("\n  坑 3  模块名和标准库冲突")
    print("        自己写个 json.py / random.py / types.py")
    print("        -> 整个项目导入错乱（sys.path[0] 优先）")
    print("        解法: 起名避开标准库，或放进包里")

    print("\n  坑 4  import 时就执行重活")
    print("        module-level 的数据库连接、大文件读取")
    print("        -> 拖慢启动，测试时也变慢")
    print("        解法: 延迟到函数内，或用 __getattr__ 懒加载")

    print("\n  坑 5  混淆模块名和变量名")
    print("        import json")
    print("        json = {'a': 1}   # 覆盖了模块！")

    print("\n  坑 6  依赖 sys.path[0] 的行为差异")
    print("        直接运行脚本: sys.path[0] = 脚本所在目录")
    print("        python -m:    sys.path[0] = 当前工作目录")
    print("        两者不同，导致「本地能跑 CI 挂了」")

    print("\n  [Java 对比] Java 的这些坑大多被编译期消灭（package 声明必须和路径一致），")
    print("             Python 全靠运行时约定，所以更需要规范的工程结构")


def print_java_mapping():
    print("\n=== 12. Java 对照总表 ===")
    rows = [
        ("场景", "Python", "Java"),
        ("包的标识", "__init__.py（可选）", "package 声明"),
        ("搜索路径", "sys.path（可变 list）", "classpath（启动时固定）"),
        ("路径环境变量", "PYTHONPATH", "CLASSPATH"),
        ("导入语法", "import x / from x import y", "import a.b.C"),
        ("相对导入", "from . import x", "无（只有全限定名）"),
        ("动态导入", "importlib.import_module", "Class.forName"),
        ("插件发现", "pkgutil.iter_modules", "ServiceLoader"),
        ("导入时机", "运行时，可能延迟", "类加载时"),
        ("同名冲突", "先找到的胜出，静默", "classpath 顺序，也很难查"),
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(row[i].ljust(widths[i]) for i in range(3)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 64)
    print("Python 模块与包机制")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 64)

    demo_module_vs_package()
    demo_import_order()
    demo_sys_path()
    demo_pythonpath_and_pth()
    demo_import_other_dirs()
    demo_internal_import()
    demo_init_and_all()
    demo_circular_import()
    demo_importlib()
    demo_pkgutil_discover()
    demo_pitfalls()
    print_java_mapping()

    print("\n" + "=" * 64)
    print("所有 demo 运行完成！")
    print("=" * 64)


if __name__ == "__main__":
    main()
