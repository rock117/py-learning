#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
toc_gen.py - 把 md 中的「代码链接」自动转换成 mdbook 的 {{#include}} 代码块

背景
----
文档里原来用 `../code/xxx.py#L31-L54` 这样的行号锚点链接到源码。
问题有两个：
    1. mdbook 不识别 #L 锚点，浏览器只能打开纯文本，无高亮、无行号；
    2. 行号是手工估算的，代码一改就错位。

本脚本的做法
------------
把「链接里的行号」翻译成「该行所属的顶层函数/类」，再用函数在源码中的
真实起止行生成 {{#include file:start:end}}。

为什么按函数名定位而不是沿用行号
--------------------------------
行号会随代码变动失效，但 `def demo_xxx():` 这个锚点在重构中稳定得多。
脚本每次运行都重新扫描源码，按行号定位归属函数，因此：

    - 在函数里加几行代码，重新跑一次脚本即可自动校正；
    - 行号完全对不上任何函数时，脚本会明确报错，而不是静默生成错误内容。

幂等
----
已转换过的片段会被识别并跳过，因此可以反复运行，不会重复插入。

用法
----
    python tools/toc_gen.py --check      # 只检查，列出待转换项与错误（适合 CI）
    python tools/toc_gen.py --fix        # 原地改写 md 文件
    python tools/toc_gen.py --fix -v     # 显示每处改写的函数名与行区间
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
CODE_DIR = SRC_DIR / "code"

# 匹配形如：> [说明文字](../code/libraries/06_data_science.py#L31-L54)
LINK_WITH_LINES = re.compile(
    r"^(?P<prefix>>\s*\[)(?P<title>[^\]]+)\]"
    r"\((?P<path>\.\./code/[^)#]+\.py)#L(?P<start>\d+)(?:-L(?P<end>\d+))?\)[ \t]*$",
    re.MULTILINE,
)

DEF_LINE = re.compile(r"^(?:async\s+)?def\s+(?P<name>\w+)\s*\(")
CLASS_LINE = re.compile(r"^class\s+(?P<name>\w+)\s*[(:]")
# 模块级常量赋值，如 PYPROJECT_TOML_EXAMPLE = """ ... """
CONST_LINE = re.compile(r"^(?P<name>[A-Z][A-Z0-9_]{2,})\s*=\s*")


@dataclass
class Block:
    """源码中的一个顶层定义（函数或类）的文件行区间。"""

    name: str
    start: int          # 1-based，def/class 所在行
    end: int            # 1-based，含


def scan_blocks(py_file: Path) -> list[Block]:
    """扫描 .py，返回所有顶层函数/类的行区间。"""
    lines = py_file.read_text(encoding="utf-8").splitlines()
    starts: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        m = DEF_LINE.match(line) or CLASS_LINE.match(line) or CONST_LINE.match(line)
        if m:
            starts.append((idx, m.group("name")))

    blocks: list[Block] = []
    for i, (idx, name) in enumerate(starts):
        next_idx = starts[i + 1][0] if i + 1 < len(starts) else len(lines)
        end = next_idx
        # 回退尾部空行，避免把文件尾空行也嵌进正文
        while end > idx + 1 and lines[end - 1].strip() == "":
            end -= 1
        blocks.append(Block(name=name, start=idx + 1, end=end))
    return blocks


def find_block_by_line(blocks: list[Block], line: int, lines: list[str] | None = None,
                       up_to: int = 8) -> Block | None:
    """根据链接里的行号，找到包含该行的那个顶层定义。

    除了直接命中，还允许一种常见情况：链接的起始行落在某个定义紧前方
    的少量行里。典型例子是 `T = TypeVar("T")` 写在 `class Box(Generic[T])`
    前几行，文档想从声明一起展示。

    命中前导区时，返回的 Block 起始行会被前移到那片声明的第一行，
    并跳过空行，避免代码块开头出现空行。
    """
    for b in blocks:
        if b.start <= line <= b.end:
            return b
    for b in blocks:
        if 0 < b.start - line <= up_to:
            start = line
            if lines is not None:
                # 向下跳过空行，落到真正的声明行
                while start < b.start and not lines[start - 1].strip():
                    start += 1
            return Block(name=b.name, start=start, end=b.end)
    return None


def process_md(md_file: Path, fix: bool, verbose: bool) -> tuple[int, int, list[str]]:
    """处理一个 md 文件，返回 (转换数, 跳过数, 错误列表)。"""
    text = md_file.read_text(encoding="utf-8")
    converted = skipped = 0
    errors: list[str] = []
    replacements: list[tuple[int, int, str]] = []

    for m in LINK_WITH_LINES.finditer(text):
        start = int(m.group("start"))
        py_rel = m.group("path").replace("../code/", "")
        py_file = CODE_DIR / py_rel
        lineno = text[: m.start()].count("\n") + 1
        where = f"{md_file.relative_to(ROOT)}:{lineno}"

        if not py_file.exists():
            errors.append(f"{where} 源码不存在: {py_file.name}")
            continue

        block = find_block_by_line(scan_blocks(py_file), start,
                                   lines=py_file.read_text(encoding="utf-8").splitlines())
        if block is None:
            errors.append(f"{where} 行号 L{start} 未落在任何顶层 def/class 内")
            continue

        inc = f"{{{{#include ../code/{py_rel}:{block.start}:{block.end}}}}}"
        # include 展开的是裸文本，必须自己包 fences 才会被渲染成代码块
        fenced = f"```python\n{inc}\n```"

        # 幂等：链接后紧跟的段落里已经有同一条 include 就跳过
        tail = text[m.end(): m.end() + 300]
        if inc in tail:
            skipped += 1
            continue

        new_text = (
            f"{m.group('prefix')}{m.group('title')}]"
            f"({m.group('path')}#L{block.start}-L{block.end})\n\n{fenced}"
        )
        replacements.append((m.start(), m.end(), new_text))
        converted += 1
        if verbose:
            print(f"  {where}  L{start} -> {block.name} [{block.start}-{block.end}]")

    if fix and replacements:
        for s, e, new in reversed(replacements):
            text = text[:s] + new + text[e:]
        md_file.write_text(text, encoding="utf-8")

    return converted, skipped, errors


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="只检查，不写文件")
    g.add_argument("--fix", action="store_true", help="原地改写 md 文件")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    total_c = total_s = 0
    all_errors: list[str] = []

    for md in sorted(SRC_DIR.glob("*/*.md")):
        c, s, errs = process_md(md, fix=args.fix, verbose=args.verbose)
        if c or s or errs:
            flag = "已改写" if args.fix else "待转换"
            print(
                f"{str(md.relative_to(ROOT)):<40} {flag}={c:<4} 已跳过={s:<4} 错误={len(errs)}"
            )
        total_c += c
        total_s += s
        all_errors.extend(errs)

    print(f"\n合计: {'已转换' if args.fix else '待转换'} {total_c} 处，已跳过 {total_s} 处")
    if all_errors:
        print(f"\n发现 {len(all_errors)} 个错误:")
        for e in all_errors:
            print("  - " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
