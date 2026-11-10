# Python 进阶学习（面向 Java 开发者）

> 本教程面向有丰富 Java 经验、熟悉 Python 基本用法的开发者，系统讲解 Python 的高级特性。
>
> 每个章节都配有可运行的代码文件。讲解中的代码片段直接内嵌源码并带语法高亮，
> 点击片段上方的链接可跳转到完整源文件。

## 运行方式

```bash
# 安装 mdbook（如尚未安装）
# https://rust-lang.github.io/mdBook/guide/installation.html

# 本地预览
mdbook serve --open

# 构建静态站点
mdbook build
```

## 维护代码片段

文档里的代码片段不是手工复制的，而是用 `{{#include}}` 从 `src/code/` 下的源码
按行区间自动嵌入。改动源码后运行一次同步脚本即可，不用手工改文档：

```bash
# 检查文档与源码是否同步（CI 可用）
python tools/toc_gen.py --check

# 自动校正所有 include 的行区间
python tools/toc_gen.py --fix
```

脚本按「行号 → 所属顶层函数/类」的规则定位，因此函数内部增删几行后能自动
重新算出行区间；若行号已完全对不上任何函数，会明确报错而不是静默写错内容。

## 代码运行

```bash
# async 部分
python src/code/async/01_basics.py

# 高级部分
python src/code/advanced/01_type_system.py
```

## 环境要求

- Python 3.12+（推荐 3.13，部分特性需要 3.12+）
- 可选第三方库：`pip install numpy pandas polars matplotlib sqlalchemy fastapi flask django requests httpx aiohttp jinja2 pydantic`
  （未安装的库在运行时会被优雅跳过，不影响其他示例）

## 目录

- [第一部分：异步编程 async](./async/README.md)
- [第二部分：高级特性](./advanced/README.md)
