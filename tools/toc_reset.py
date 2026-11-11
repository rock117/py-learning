#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
toc_reset.py - 把 md 中的 include 代码块全部剥离，恢复成「纯链接」状态

用途
----
`toc_gen.py` 的转换是可重复的：链接 + include 代码块。
如果 include 内容出了错（行号漂移、重复插入），最干净的修法不是逐个修补，
而是把 include 全部剥掉、让 md 回到只有链接的状态，再重新跑一次 toc_gen。

剥离规则
--------
以下三种形态都会被还原成一条链接：

    > [标题](../code/x.py#L10-L20)

    ```python
    {{#include ../code/x.py:10:20}}
    ```

会变成：

    > [标题](../code/x.py#L10-L20)

如果同一链接后面跟着【多个】include 块（历史上重复插入造成），
只保留根据链接锚点重新计算出来的那一个。

用法
----
    python tools/toc_reset.py --check    # 只统计会剥掉多少个
    python tools/toc_reset.py --fix      # 原地剥离
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"

# 匹配「链接 + 后续一个或多个 include 代码块」
# 捕获：链接整行、链接的 py 路径与行号
PATTERN = re.compile(
    r"^(?P<link>>\s*\[[^\]]+\]\((?P<path>\.\./code/[^)#]+\.py)#L(?P<start>\d+)(?:-L(?P<end>\d+))?\))\s*$"
    r"(?P<blocks>(?:\s*\n\s*\n```[a-zA-Z]*\s*\n\s*\{\{#include [^}]*\}\}\s*\n```)+)",
    re.MULTILINE,
)


def process(md_file: Path, fix: bool) -> tuple[int, int]:
    """返回 (需要剥离的 include 数, 处理的链接数)。"""
    text = md_file.read_text(encoding="utf-8")
    removed = 0
    links = 0

    def repl(m: re.Match) -> str:
        nonlocal removed, links
        blocks = m.group("blocks")
        n = blocks.count("{{#include")
        removed += n
        links += 1
        # 只保留链接本身
        return m.group("link")

    new_text, _ = PATTERN.subn(repl, text)

    if fix and removed:
        md_file.write_text(new_text, encoding="utf-8")
    return removed, links


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--fix", action="store_true")
    args = ap.parse_args()

    total_blocks = total_links = 0
    for md in sorted(SRC_DIR.glob("*/*.md")):
        n, links = process(md, fix=args.fix)
        if n:
            action = "已剥离" if args.fix else "将剥离"
            print(f"{str(md.relative_to(ROOT)):<44} {action} include={n:<4} 涉及链接={links}")
        total_blocks += n
        total_links += links

    print(f"\n合计: {'已剥离' if args.fix else '待剥离'} include {total_blocks} 个，"
          f"涉及链接 {total_links} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
