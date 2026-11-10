# -*- coding: utf-8 -*-
"""
06_data_science.py - Python 数据科学类库

本文件面向有丰富 Java 经验的开发者，讲解 Python 数据生态：
    - NumPy    ：多维数组与向量化计算（Java 无标准对应，类似 EJML / ND4J）
    - Pandas   ：表格数据处理（对比 Java 的 Tablesaw / Spark DataFrame / Excel 手工作业）
    - Polars   ：新一代列式 DataFrame（Rust 实现，速度快，API 更一致）
    - Matplotlib：绘图（对比 JFreeChart）

核心差异提醒（Java 开发者最容易误解的点）：
    1. NumPy/Pandas 的计算是"向量化 / 列式"的，不要在行上写 for 循环；
    2. Pandas 有 copy-on-write 语义（2.x 默认），链式赋值会静默失效；
    3. 缺失值 NaN/NaT/None 三者在各库中的行为不完全一致。

[注意] 若未安装某个库，对应 demo 会打印提示并跳过，不影响 exit code 0。
       绘图部分使用非交互后端 Agg，不弹窗，只把图片保存到临时目录。
"""

import sys
import tempfile
from pathlib import Path


# =============================================================================
# 第一部分：NumPy —— 一切的基础
# =============================================================================
# [Java 对比] NumPy ~ 一个支持广播的 double[] + 线性代数库；
#             没有 JVM 生态中那么重的 API，但性能来自 C 层 SIMD。

def demo_numpy_basics():
    """数组创建、dtype、形状、索引与切片。"""
    print("=== 1. NumPy 基础 ===")
    try:
        import numpy as np
    except ImportError:
        print("  [注意] numpy 未安装，跳过。安装: pip install numpy")
        return

    a = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.int64)
    print(f"  a =\n{a}")
    print(f"  shape={a.shape}  ndim={a.ndim}  dtype={a.dtype}  itemsize={a.itemsize}B")
    print(f"  shape=({a.shape[0]}行, {a.shape[1]}列)，即 Java 的 {a.shape[0]} 行 {a.shape[1]} 列二维数组")

    # 切片：视图，不是拷贝（关键差异！）
    row0 = a[0]
    row0[0] = 999
    print(f"  a[0] 是视图还是拷贝? 修改 a[0][0] 后 a[0][0] = {a[0, 0]}（说明是视图）")

    # 常用构造
    print(f"  zeros(2,3):\n{np.zeros((2, 3))}")
    print(f"  arange(0,10,3): {np.arange(0, 10, 3)}")
    print(f"  linspace(0,1,5): {np.linspace(0, 1, 5)}")
    print(f"  random 可复现: {np.random.default_rng(42).integers(0, 100, 5)}")


def demo_numpy_vectorization():
    """向量化 vs for 循环：性能与写法对比。"""
    print("\n=== 2. 向量化计算 ===")
    try:
        import numpy as np
        import time
    except ImportError:
        print("  [注意] numpy 未安装，跳过。")
        return

    n = 1_000_000
    py_list = list(range(n))

    t0 = time.perf_counter()
    total_loop = sum(x * x for x in py_list)
    t_loop = time.perf_counter() - t0

    arr = np.arange(n)
    t0 = time.perf_counter()
    total_vec = int(np.sum(arr * arr))
    t_vec = time.perf_counter() - t0

    print(f"  for 循环: {t_loop * 1000:.1f} ms")
    print(f"  向量化 : {t_vec * 1000:.2f} ms  (约 {t_loop / t_vec:.0f}x 快)")
    print(f"  结果一致: {total_loop == total_vec}")

    print("\n  广播（Broadcasting）—— 不同形状也能运算：")
    m = np.array([[1], [2], [3]])       # 3x1
    v = np.array([10, 20, 30])          # 3
    print(f"  (3x1) + (3,) =\n{m + v}")
    print("  [要点] 能向量化就不要写 for；广播是省内存的扩张，不复制数据")


def demo_numpy_linalg_and_stats():
    """线性代数与统计。"""
    print("\n=== 3. 线性代数与统计 ===")
    try:
        import numpy as np
    except ImportError:
        print("  [注意] numpy 未安装，跳过。")
        return

    rng = np.random.default_rng(7)
    x = rng.normal(loc=10, scale=3, size=1000)
    print(f"  mean={x.mean():.3f}  std={x.std():.3f}  median={np.median(x):.3f}")
    print(f"  min={x.min():.3f}  max={x.max():.3f}  quantile(25/50/75)="
          f"{np.quantile(x, [0.25, 0.5, 0.75]).round(2)}")

    A = np.array([[4.0, 1.0], [2.0, 3.0]])
    b = np.array([1.0, 2.0])
    solution = np.linalg.solve(A, b)
    print(f"  解方程 Ax=b: x = {solution}   验证 A@x = {A @ solution}")
    print(f"  逆矩阵:\n{np.linalg.inv(A).round(3)}")
    print(f"  特征值: {np.linalg.eigvals(A).round(3)}")
    print("  [Java 对比] 类似 Apache Commons Math / EJML，但 Python 这些是标配")


# =============================================================================
# 第二部分：Pandas —— 表格处理
# =============================================================================
# [Java 对比] Pandas ~ Tablesaw / Spark DataFrame（单机版）
#             但它更像"可编程的 Excel"，groupby/merge/透视表都是原语。

def demo_pandas_series_dataframe():
    """Series 与 DataFrame 基础。"""
    print("\n=== 4. Pandas Series 与 DataFrame ===")
    try:
        import pandas as pd
    except ImportError:
        print("  [注意] pandas 未安装，跳过。安装: pip install pandas")
        return

    s = pd.Series([10, 20, 30, None], index=["a", "b", "c", "d"], name="score")
    print(f"  Series:\n{s}")
    print(f"  非空值: {s.dropna().tolist()}  mean={s.mean()}")

    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Carol", "Dave", "Eve"],
        "dept": ["RD", "RD", "Sales", "Sales", "RD"],
        "salary": [15000, 18000, 12000, 13000, 22000],
        "years": [1, 3, 2, 4, 6],
    })
    print(f"\n  DataFrame:\n{df}")
    print(f"\n  dtypes:\n{df.dtypes}")
    print(f"  列名: {list(df.columns)}  行数: {len(df)}")
    print("  [Java 对比] DataFrame ≈ List<Map<String,Object>>，但支持列式向量化操作")


def demo_pandas_filter_groupby():
    """筛选、派生列、分组聚合、排序。"""
    print("\n=== 5. 筛选 / 派生列 / 分组聚合 ===")
    try:
        import pandas as pd
    except ImportError:
        print("  [注意] pandas 未安装，跳过。")
        return

    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Carol", "Dave", "Eve"],
        "dept": ["RD", "RD", "Sales", "Sales", "RD"],
        "salary": [15000, 18000, 12000, 13000, 22000],
        "years": [1, 3, 2, 4, 6],
    })

    # 布尔索引（相当于 SQL WHERE）
    high = df[df["salary"] > 14000]
    print(f"  salary > 14000:\n{high[['name', 'salary']]}")

    # 多条件：注意用 & | 并加括号（Python and/or 不适用于 Series）
    filtered = df[(df["dept"] == "RD") & (df["years"] >= 3)]
    print(f"\n  RD 且年限>=3:\n{filtered[['name', 'years']]}")

    # 派生列（向量化，不写循环）
    df2 = df.assign(monthly_bonus=df["salary"] * 0.1,
                    level=df["years"].map(lambda y: "senior" if y >= 4 else "junior"))
    print(f"\n  派生列后:\n{df2[['name', 'monthly_bonus', 'level']]}")

    # 分组聚合（相当于 SQL GROUP BY）
    agg = df.groupby("dept")["salary"].agg(["count", "mean", "max"]).round(1)
    print(f"\n  按部门聚合:\n{agg}")

    # 排序 / 排名
    print(f"\n  按薪水降序前 3:\n{df.sort_values('salary', ascending=False).head(3)[['name', 'salary']]}")


def demo_pandas_missing_and_merge():
    """缺失值处理与表连接。"""
    print("\n=== 6. 缺失值处理与 merge ===")
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        print("  [注意] pandas / numpy 未安装，跳过。")
        return

    users = pd.DataFrame({
        "user_id": [1, 2, 3, 4],
        "name": ["Alice", "Bob", "Carol", "Dave"],
        "city": ["Beijing", None, "Shanghai", np.nan],
    })
    orders = pd.DataFrame({
        "order_id": [101, 102, 103, 104],
        "user_id": [1, 1, 3, 9],
        "amount": [100.0, 250.5, None, 80.0],
    })

    print(f"  users 缺失值统计:\n{users.isna().sum()}")
    filled = users.fillna({"city": "Unknown"})
    print(f"\n  fillna 后:\n{filled}")

    # merge = SQL JOIN
    merged = orders.merge(users, on="user_id", how="left")
    print(f"\n  orders LEFT JOIN users:\n{merged}")

    merged["amount"] = merged["amount"].fillna(0.0)
    print(f"\n  按城市汇总金额（缺失城市归为 Unknown）:")
    print(merged.groupby("city", dropna=False)["amount"].sum())
    print("  [Java 对比] 相当于 JOIN + Collectors.groupingBy 的组合，但少写几十行")


def demo_pandas_io():
    """CSV / JSON / Excel 读写。"""
    print("\n=== 7. Pandas 读写 CSV / JSON / Excel ===")
    try:
        import pandas as pd
    except ImportError:
        print("  [注意] pandas 未安装，跳过。")
        return

    df = pd.DataFrame({"id": [1, 2, 3], "value": [1.5, 2.5, 3.5]})
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        csv_path = tmpdir / "data.csv"
        df.to_csv(csv_path, index=False)
        print(f"  CSV 写入 {csv_path.name}，内容:")
        print("    " + csv_path.read_text(encoding="utf-8").replace("\n", "\n    ").rstrip())
        print(f"  读回:\n{pd.read_csv(csv_path)}")

        json_path = tmpdir / "data.json"
        df.to_json(json_path, orient="records", force_ascii=False)
        print(f"  JSON: {json_path.read_text(encoding='utf-8')}")

        try:
            xlsx_path = tmpdir / "data.xlsx"
            df.to_excel(xlsx_path, index=False)
            print(f"  Excel 写入成功，读回:\n{pd.read_excel(xlsx_path)}")
        except ImportError:
            print("  [注意] 写 Excel 需要 openpyxl: pip install openpyxl")
    print("  [Java 对比] 无需 Apache POI / Jackson，一行读写完成")


def demo_pandas_pitfalls():
    """Pandas 常见坑：SettingWithCopyWarning / chained assignment。"""
    print("\n=== 8. Pandas 常见坑 ===")
    try:
        import pandas as pd
    except ImportError:
        print("  [注意] pandas 未安装，跳过。")
        return

    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    # 坑 1：链式赋值，在 copy-on-write 下不会修改原 df
    sub = df[df["a"] > 1]
    sub["b"] = 0
    print(f"  链式赋值后原 df 是否被改? b = {df['b'].tolist()}（未改，说明 sub 是拷贝）")

    # 正确写法 1：显式 copy
    sub2 = df[df["a"] > 1].copy()
    sub2["b"] = 0
    print(f"  显式 .copy() 后修改 sub2，原 df 仍为: {df['b'].tolist()}")

    # 正确写法 2：用 loc 直接在原 df 上改
    df.loc[df["a"] > 1, "b"] = 99
    print(f"  用 df.loc[mask, col] = ... 原地修改后: {df['b'].tolist()}")
    print(f"  copy-on-write 是否开启: {pd.options.mode.copy_on_write}")
    print("  [要点] 想改原表就用 loc/iloc；想改子集就先 .copy()")


# =============================================================================
# 第三部分：Polars —— 新一代 DataFrame
# =============================================================================
# [Java 对比] Polars 无直接对应，思路接近 Apache Arrow + 更强的懒执行（LazyFrame）。

def demo_polars_basics():
    """Polars：表达式 API + LazyFrame 优化。"""
    print("\n=== 9. Polars DataFrame 与 LazyFrame ===")
    try:
        import polars as pl
    except ImportError:
        print("  [注意] polars 未安装，跳过。安装: pip install polars")
        return

    df = pl.DataFrame({
        "name": ["Alice", "Bob", "Carol", "Dave"],
        "dept": ["RD", "RD", "Sales", "Sales"],
        "salary": [15000, 18000, 12000, 13000],
    })
    print(f"  Polars DataFrame:\n{df}")

    # 表达式 API：列名当变量用（浏览器里拼 SQL 的感觉）
    out = (
        df.lazy()
        .with_columns(
            (pl.col("salary") * 0.1).alias("bonus"),
            pl.when(pl.col("salary") > 14000).then(pl.lit("high")).otherwise(pl.lit("low")).alias("band"),
        )
        .filter(pl.col("dept") == "RD")
        .group_by("dept")
        .agg(pl.col("salary").mean().alias("avg_salary"), pl.len().alias("cnt"))
        .collect()          # 懒执行在这里才真正计算
    )
    print(f"\n  LazyFrame 聚合结果:\n{out}")

    print("\n  Polars vs Pandas 要点:")
    print("    - 没有索引（index），行顺序不隐含语义")
    print("    - 表达式可以并行，LazyFrame 会做谓词下推 + 投影下推")
    print("    - 缺失值是 null 而非 NaN，语义更干净")
    print("    - API 更一致，很少出现 SettingWithCopy 之类的坑")


# =============================================================================
# 第四部分：Matplotlib —— 绘图
# =============================================================================
# [Java 对比] Matplotlib ~ JFreeChart，但更灵活，可与 NumPy 无缝配合。

def demo_matplotlib():
    """绘图并保存为 PNG（不弹窗）。"""
    print("\n=== 10. Matplotlib 绘图 ===")
    try:
        import matplotlib
        matplotlib.use("Agg")             # 非交互后端，服务器/CI 环境友好
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("  [注意] matplotlib / numpy 未安装，跳过。")
        return

    x = np.linspace(0, 2 * np.pi, 200)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))

    axes[0].plot(x, np.sin(x), label="sin")
    axes[0].plot(x, np.cos(x), label="cos", linestyle="--")
    axes[0].set_title("Trig curves")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    rng = np.random.default_rng(1)
    data = [rng.normal(mu, 1.0, 500) for mu in (0, 2, 4)]
    axes[1].boxplot(data, labels=["A", "B", "C"])
    axes[1].set_title("Box plot")

    fig.tight_layout()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "demo.png"
        fig.savefig(path, dpi=100)
        size = path.stat().st_size
        print(f"  已生成图片: {path.name}  ({size} bytes, {path.read_bytes()[:4].hex()} 为 PNG 头)")
    plt.close(fig)
    print("  [要点] 脚本中务必 matplotlib.use('Agg')，否则无显示环境会卡住或报错")


# =============================================================================
# 第五部分：速查表
# =============================================================================

def print_cheatsheet():
    """数据科学类库选型速查。"""
    print("\n=== 11. 选型速查表 ===")
    rows = [
        ("需求", "推荐", "Java 对应"),
        ("数值数组 / 线性代数", "NumPy", "EJML / ND4J"),
        ("表格清洗 / 统计", "Pandas", "Tablesaw / Spark DF"),
        ("大数据量列式计算", "Polars", "Arrow / DuckDB 生态"),
        ("绘图", "Matplotlib / Seaborn", "JFreeChart"),
        ("交互式探索", "Jupyter Notebook", "Zeppelin"),
        ("与 SQL 互通", "pandas.read_sql / Polars SQL", "JPA / JdbcTemplate"),
    ]
    widths = [max(len(str(r[i])) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 60)
    print("Python 数据科学类库演示 (NumPy / Pandas / Polars / Matplotlib)")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 60)

    demo_numpy_basics()
    demo_numpy_vectorization()
    demo_numpy_linalg_and_stats()
    demo_pandas_series_dataframe()
    demo_pandas_filter_groupby()
    demo_pandas_missing_and_merge()
    demo_pandas_io()
    demo_pandas_pitfalls()
    demo_polars_basics()
    demo_matplotlib()
    print_cheatsheet()

    print("\n" + "=" * 60)
    print("所有 demo 运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
