# 模块与包机制

这一章讲 Python 的导入系统。它和 Java 的包机制看似相似，实则根本不同——**Java 的包在编译期固定，Python 的包在运行时按路径搜索**。

这个差异既是 Python 灵活性的来源，也是各种 `ImportError` 的根源。

## 三个层次的概念

> [概念区分](../code/basics/07_modules_and_packages.py#L40-L64)

```python
{{#include ../code/basics/07_modules_and_packages.py:40:64}}
```

| 概念 | 形态 | 判断方式 |
|------|------|---------|
| **模块** | 单个 `.py` 文件 | 有 `__file__` |
| **包** | 含 `__init__.py` 的目录 | 有 `__path__` |
| **命名空间包** | 无 `__init__.py` 的目录（PEP 420） | 有 `__path__`，可能跨多个位置 |

```python
import json
hasattr(json, "__file__")      # True  —— 模块

import os.path
hasattr(os.path, "__path__")   # True  —— 包
```

**命名空间包**值得特别注意：Python 3.3+ 允许多个物理位置的同名目录**合并成一个包**。Java 里这是 `split package` 冲突，Python 里是合法特性。

> [Java 对比] Java 的包由 `package` 声明 + 目录结构在**编译期**确定；Python 全在**运行时**解析。

## `import` 的查找顺序

> [查找顺序演示](../code/basics/07_modules_and_packages.py#L67-L106)

```python
{{#include ../code/basics/07_modules_and_packages.py:67:106}}
```

当一个 `import` 执行时，按顺序尝试：

```
1. sys.modules 缓存      —— 已导入的直接返回，不会重新执行
2. 内置模块              —— sys.builtin_module_names
3. sys.path 逐个目录    —— 找到第一个匹配就停
```

```python
import json as j1
import json as j2
j1 is j2        # True —— 走缓存
```

`sys.path` 是**普通 list**，顺序敏感：

```
[0] 脚本所在目录（直接运行）或 '' （-m 时是 cwd）
[1..] PYTHONPATH 环境变量
[..] 标准库目录 + site-packages
```

> [Java 对比] 相当于 `classpath`，但 `sys.path` 运行时可变、顺序敏感、没有编译期检查。

## 动态设置包路径

> [sys.path 演示](../code/basics/07_modules_and_packages.py#L108-L155)

```python
{{#include ../code/basics/07_modules_and_packages.py:108:155}}
```

```python
import sys
sys.path.insert(0, "/path/to/libs")    # 优先级最高
import mylib                            # 现在能找到

sys.path.append("/path/to/libs")       # 优先级最低，更安全
```

⚠️ **`insert(0, ...)` 会覆盖标准库同名模块**。如果你注入的目录里有 `json.py`，整个项目的 `import json` 都会错。

### 四种方式对比

| 方式 | 适用场景 | 风险 |
|------|---------|------|
| `sys.path.append(...)` 写在业务代码 | ❌ 不推荐 | 污染全局、依赖 cwd、难调试 |
| `PYTHONPATH` 环境变量 | 开发期、容器内 | 部署环境需一致配置 |
| `.pth` 文件 | 系统级安装内部包 | 隐式、难发现 |
| **`pip install -e .`** | ✅ 生产首选 | 无 |
| **`python -m`** | ✅ 脚本场景 | 无 |

### `PYTHONPATH` 与 `.pth`

> [环境变量与 pth](../code/basics/07_modules_and_packages.py#L158-L181)

```python
{{#include ../code/basics/07_modules_and_packages.py:158:181}}
```

```bash
# Linux/macOS
export PYTHONPATH=/opt/mylib:$PYTHONPATH

# Windows
set PYTHONPATH=C:\mylib;%PYTHONPATH%
```

`.pth` 文件是 site-packages 下的魔法：放一个 `xxx.pth`，每行一个路径，Python 启动时自动加入 `sys.path`。

> [Java 对比] `PYTHONPATH` ≈ `CLASSPATH`。但 `.pth` 没有 Java 对应物。

## 引入其他目录的包：5 种场景

> [完整场景演示](../code/basics/07_modules_and_packages.py#L183-L251)

```python
{{#include ../code/basics/07_modules_and_packages.py:183:251}}
```

### A. 同项目内的兄弟包（推荐）

```
myproject/
├── pyproject.toml
└── src/
    ├── mypkg/
    └── otherpkg/
```

`pip install -e .` 后两者都是顶层包，直接 `from otherpkg import xxx`。

### B. 脚本引用上级目录的包

```
scripts/
└── run.py          ← 想 import ../src/mypkg
```

❌ 不要 `sys.path.append("..")`（依赖 cwd）
✅ 从项目根运行 `python -m scripts.run`
✅ 或先 `pip install -e .`

### C. monorepo 多个独立包

```
repo/
└── packages/
    ├── core/
    └── web/
```

用 workspace 声明，见[工程化 - 项目结构](../engineering/01-project-layout.md)。

### D. 插件目录（运行时发现）

用 `importlib` 动态加载，见后文。

### E. 单文件脚本复用工具函数

✅ 抽成包 + `pip install -e .`，不要复制粘贴。

### 真实验证

代码里实际生成了这套结构并运行，输出：

```
实际验证场景 B（sys.path 注入 src）：
    hello from mypkg.util
```

## 包内 import：绝对 vs 相对

> [绝对/相对导入](../code/basics/07_modules_and_packages.py#L253-L322)

```python
{{#include ../code/basics/07_modules_and_packages.py:253:322}}
```

```
mypkg/
├── __init__.py
├── core.py
└── utils/
    ├── __init__.py
    └── text.py
```

### ✅ 绝对导入（官方推荐）

```python
from mypkg.utils import text
from mypkg.utils.text import slugify
```

清晰、可搜索、重构友好。

### ⚠️ 相对导入（包内部）

```python
from . import core          # 同级模块
from .utils import text     # 子包
from ..core import foo      # 上上级
```

好处是包改名时不用改 import；坏处是层级多了容易看晕，且**不能用于顶层脚本**。

### 一个必踩的坑：`python pkg/main.py`

代码里真实跑了一遍两种方式：

```
⚠️ 直接运行 python relpkg/main.py：
   ImportError: attempted relative import with no known parent package

✅ 改用 python -m relpkg.main：
   a
```

**根因**：直接跑文件时，该文件是「顶层模块 `__main__`」，没有所属包，相对导入无参照点。用 `-m` 时 Python 先把父目录加进 `sys.path`，模块知道自己的包名。

> [要点] 记住这条：**包内的相对导入，只能用 `python -m pkg.module` 运行，不能直接跑文件。**

## `__init__.py` 与 `__all__`

> [`__init__.py` 与 `__all__`](../code/basics/07_modules_and_packages.py#L324-L376)

```python
{{#include ../code/basics/07_modules_and_packages.py:324:376}}
```

`__init__.py` 的三件事：

1. 标记目录为常规包（PEP 420 后非必需，但推荐保留）
2. 包首次导入时执行
3. 定义 `__all__` 控制 `from pkg import *`

### 推荐用法：导出公开 API

```python
# mypkg/__init__.py
from .core import Client, Config
from .errors import MyError

__all__ = ["Client", "Config", "MyError"]
__version__ = "1.0.0"
```

调用方只需：

```python
from mypkg import Client        # 不需要知道内部文件结构
```

> [要点] 这是**最重要的工程实践之一**：`__init__.py` 决定了包的公开 API，重构内部文件时不会破坏调用方。

### ⚠️ `__init__.py` 里不要做重活

- 不要 import 大量模块（拖慢首次导入）
- 不要放副作用代码（写文件、连网络）
- 不要在里面改 `sys.path`

## 循环导入

> [循环导入说明](../code/basics/07_modules_and_packages.py#L379-L406)

```python
{{#include ../code/basics/07_modules_and_packages.py:379:406}}
```

症状：

```
ImportError: cannot import name 'X' from partially initialized module
```

三种解法：

| 解法 | 说明 |
|------|------|
| 延迟导入 | 把 `import` 移到函数内部 |
| **抽取公共模块**（首选） | a 和 b 都依赖 common，而不是互相依赖 |
| `TYPE_CHECKING` | 只用于类型标注，运行时不执行 |

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .other import OtherType
```

> [要点] 出现循环导入往往说明**模块职责划分有问题**。优先想"该拆出什么"，而不是急着用延迟导入糊过去。

## `importlib` 动态导入

> [动态导入演示](../code/basics/07_modules_and_packages.py#L408-L441)

```python
{{#include ../code/basics/07_modules_and_packages.py:408:441}}
```

```python
import importlib

# ① 按名称
math_mod = importlib.import_module("math")

# ② 按字符串变量（插件场景）
for name in ["json", "csv", "base64"]:
    importlib.import_module(name)

# ③ 按文件路径
spec = importlib.util.spec_from_file_location("my_plugin", "/path/my_plugin.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
```

### 自动发现子模块

> [pkgutil 发现](../code/basics/07_modules_and_packages.py#L444-L467)

```python
{{#include ../code/basics/07_modules_and_packages.py:444:467}}
```

```python
import pkgutil, importlib

for m in pkgutil.iter_modules(pkg.__path__):
    if not m.name.startswith("_"):
        importlib.import_module(f"{pkg.__name__}.{m.name}")
```

> [Java 对比] 类似 `ServiceLoader` / SPI。但 Python 按目录约定发现，Java 靠 `META-INF/services` 声明。

## 常见陷阱

> [完整陷阱演示](../code/basics/07_modules_and_packages.py#L469-L501)

```python
{{#include ../code/basics/07_modules_and_packages.py:469:501}}
```

| 坑 | 现象 | 解法 |
|---|---|---|
| **直接运行含相对导入的文件** | `ImportError: attempted relative import` | `python -m pkg.main` |
| **`sys.path` 里写相对路径** | 换个工作目录就失效 | 用 `Path(__file__).resolve().parent` |
| **模块名撞标准库** | 自己写 `json.py` / `random.py` | 起名避开标准库 |
| **import 时执行重活** | 启动慢、测试慢 | 延迟到函数内 |
| **变量名覆盖模块名** | `json = {...}` 后 `json.dumps` 失败 | 换个变量名 |
| **`sys.path[0]` 行为差异** | 本地能跑、CI 挂了 | 统一用 `python -m` |

## Java 对照总表

| 场景 | Python | Java |
|------|--------|------|
| 包的标识 | `__init__.py`（可选） | `package` 声明 |
| 搜索路径 | `sys.path`（可变 list） | `classpath`（启动时固定） |
| 路径环境变量 | `PYTHONPATH` | `CLASSPATH` |
| 导入语法 | `import x` / `from x import y` | `import a.b.C` |
| 相对导入 | `from . import x` | 无 |
| 动态导入 | `importlib.import_module` | `Class.forName` |
| 插件发现 | `pkgutil.iter_modules` | `ServiceLoader` |
| 导入时机 | 运行时，可延迟 | 类加载时 |

## 小结

- Python 的包是**运行时按 `sys.path` 搜索**出来的，不是编译期固定的
- `sys.path` 是可变 list，顺序敏感——`insert(0)` 可能覆盖标准库
- **`python -m pkg.module`** 是解决相对导入报错的标准答案
- `__init__.py` 里导出公开 API，让调用方不依赖内部结构
- 跨目录引用优先用 `pip install -e .`，不要到处改 `sys.path`
- 循环导入往往暴露了模块划分问题，先想拆分

> 📁 [完整代码](../code/basics/07_modules_and_packages.py)
