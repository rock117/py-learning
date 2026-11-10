# 数据科学

本章覆盖 Python 数据处理四大件：**NumPy**（数组与向量化）、**Pandas**（表格）、**Polars**（新一代列式 DataFrame）、**Matplotlib**（绘图），重点是它们与 Java 生态的对应关系，以及 Java 开发者最容易踩的坑。

## 全景对照：Python 数据栈 vs Java

| Python 工具 | Java 对应 | 用途 / 差异 |
|-------------|-----------|-------------|
| `NumPy` | EJML / Apache Commons Math / ND4J | 多维数组 + 线性代数，底层是 C/（BLAS），不是 JVM 对象数组 |
| `Pandas` | Tablesaw / Spark DataFrame | 单机表格处理，更像"可编程的 Excel" |
| `Polars` | Apache Arrow / DuckDB 生态 | Rust 实现，列式 + 惰性执行，无索引 |
| `Matplotlib` | JFreeChart | 绘图，与 NumPy 无缝配合 |
| `Jupyter` | Apache Zeppelin | 交互式探索 |

> [示例](../code/libraries/06_data_science.py)

> ⚠️ 三类最大的思维转变：
> 1. **列式 / 向量化**：不要在行上写 `for` 循环，这是从"对象集合"到"列数组"的范式切换。
> 2. **视图 vs 拷贝**：切片、筛选出来的往往是视图（或写时复制的浅拷贝），改了不一定"生效"。
> 3. **缺失值**：`NaN` / `NaT` / `None` 三者语义不同，各库行为不一致。

## NumPy：数组与向量化

### 数组基础

`ndarray` 是同构、定长的多维数组，带 `shape` / `dtype` / `itemsize`。可以类比 Java 的 `double[]`，但它知道自己的维度，且计算在 C 层完成：

> [NumPy 基础示例](../code/libraries/06_data_science.py#L31-L54)

```python
{{#include ../code/libraries/06_data_science.py:31:54}}
```

最关键的差异是**切片返回视图**：

```python
a = np.array([[1, 2, 3], [4, 5, 6]])
row0 = a[0]     # 视图，不是拷贝
row0[0] = 999   # a[0, 0] 也变成 999
```

Java 里 `int[] b = a.clone()` 才是拷贝，否则两个引用指向同一数组——NumPy 的切片行为和 Java 的引用语义类似，但**常常被误以为是 `Arrays.copyOf`**。

> [要点] 想要独立副本，显式调用 `a[0].copy()`。

### 向量化 vs 行循环

这是数据类库存在的**全部理由**。同样的平方和，一个走 Python 解释器逐元素循环，一个走 C 层 SIMD：

> [向量化示例](../code/libraries/06_data_science.py#L57-L87)

```python
{{#include ../code/libraries/06_data_science.py:57:87}}
```

```python
# 慢：100 万次解释器循环
total_loop = sum(x * x for x in py_list)

# 快：一次 C 层调用
total_vec = int(np.sum(arr * arr))
```

在百万级数据上通常有 **几十倍到上百倍**差异。对应到 Java：你**不会**用 `for (i...)` 手写矩阵乘法，而是调 BLAS；Python 里同理，能写成数组表达式就别写循环。

**广播（Broadcasting）**是配套的省内存机制：形状 `(3, 1)` 与 `(3,)` 相加时，不会真复制出 `3×3` 的中间数组。

> ⚠️ 在 Pandas 里用 `df.iterrows()` 遍历行，相当于在 Java 里对每个 `List` 元素反射调用——**每行都是一次 Python 对象装箱**，慢 10~100 倍。看到 `for _, row in df.iterrows()` 就该停下来想能不能向量化。

### 线性代数与统计

`np.linalg.solve` / `inv` / `eigvals` 直接映射到 LAPACK，统计函数（`mean` / `std` / `quantile`）也都是向量化实现：

> [线性代数与统计示例](../code/libraries/06_data_science.py#L90-L118)

```python
{{#include ../code/libraries/06_data_science.py:90:118}}
```

Java 里这些往往要引第三方库（EJML），而 Python 里是 NumPy 的标配。

## Pandas：表格处理

### Series 与 DataFrame

`Series` 是带标签的一维数组，`DataFrame` 是共享索引的二维表。心智模型不是 `List<POJO>`，而是**一组对齐的列数组**：

> [Series 与 DataFrame 示例](../code/libraries/06_data_science.py#L120-L142)

```python
{{#include ../code/libraries/06_data_science.py:120:142}}
```

- `DataFrame` ≈ `List<Map<String, Object>>` 的便利性 + 列式向量化的性能
- 每列有独立的 `dtype`，`object` 列就是 Python 对象（通常是字符串）

### 筛选、派生列、分组

四类操作几乎一一对应 SQL：

| Pandas | SQL | Java Stream |
|--------|-----|-------------|
| `df[df.salary > 14000]` | `WHERE salary > 14000` | `stream().filter(...)` |
| `df.assign(x=...)` | `SELECT salary * 0.1 AS x` | `stream().map(...)` |
| `df.groupby("dept")["salary"].agg(...)` | `GROUP BY dept` | `Collectors.groupingBy` |
| `df.sort_values(...).head(3)` | `ORDER BY ... LIMIT 3` | `sorted().limit()` |

> [筛选与分组示例](../code/libraries/06_data_science.py#L145-L179)

```python
{{#include ../code/libraries/06_data_science.py:145:179}}
```

```python
# 多条件：必须用 & | 并给每个条件加括号
filtered = df[(df["dept"] == "RD") & (df["years"] >= 3)]

# 派生列：向量化，不要 map 到循环
df2 = df.assign(monthly_bonus=df["salary"] * 0.1)
```

> ⚠️ **`and` / `or` 不能用于 Series**。它们会把整个 Series 当成布尔值求值，直接抛 `ValueError: The truth value of a Series is ambiguous`。必须用 `&` / `|` / `~`，且优先级低于比较运算符，**括号不能省**：`df[(a) & (b)]` 而不是 `df[a & b]`。

`groupby(...).agg([...])` 对应 `Collectors.groupingBy` + downstream collector，但一行就写完了——Java 里这通常要 20~30 行样板代码。

### 缺失值与 merge

`NaN` 是浮点缺失值，`None` 是对象缺失值，Pandas 会尽量统一成 `NaN` / `NaT`。`merge` 就是 SQL JOIN：

> [缺失值与 merge 示例](../code/libraries/06_data_science.py#L182-L214)

```python
{{#include ../code/libraries/06_data_science.py:182:214}}
```

```python
merged = orders.merge(users, on="user_id", how="left")   # LEFT JOIN
merged["amount"] = merged["amount"].fillna(0.0)
merged.groupby("city", dropna=False)["amount"].sum()
```

- `how=` 取值 `left` / `right` / `inner` / `outer`，与 SQL 一致
- `dropna=False` 才能把 `NaN` 分组当作独立一组（否则被静默丢弃）
- `isna().sum()` 按列统计缺失数，等价于逐列 `COUNT(*) - COUNT(col)`

> [要点] `merge` + `groupby` ≈ `JOIN` + `Collectors.groupingBy`，但你的 Java 版本可能需要一堆 `Collector.of` 才能表达同样语义。

### IO：一行读读写写

`read_csv` / `to_csv` / `read_excel` / `to_json` 直接覆盖了 POI + Jackson 的工作：

> [IO 示例](../code/libraries/06_data_science.py#L217-L246)

```python
{{#include ../code/libraries/06_data_science.py:217:246}}
```

> ⚠️ `to_excel` / `read_excel` 依赖 `openpyxl`，没装会抛 `ImportError`，不是内置能力。

### 五个必踩的坑

> [Pandas 常见坑示例](../code/libraries/06_data_science.py#L249-L280)

```python
{{#include ../code/libraries/06_data_science.py:249:280}}
```

这是全章最值得反复读的一段。逐条展开：

**1. 切片（`df[...]` / `df.iloc[...]`）通常是视图或浅拷贝，不是深拷贝。**

```python
sub = df["a"]            # 列视图
sub2 = df[df["a"] > 1]   # 布尔筛选：可能是拷贝，也可能是视图，取决于版本
```

**2. Copy-on-Write（2.x 起默认开启）让链式赋值静默失效。**

```python
sub = df[df["a"] > 1]
sub["b"] = 0             # 不报错、不警告，但 df 没变
print(df["b"])           # b 保持原值
```

Java 里 `x.setB(0)` 一定改到对象上（除非你显式 `new` 了一个），Pandas 的"静默不生效"是最难排查的一类 bug。

**正确写法只有两种**：

```python
# 想改子集：先 copy
sub = df[df["a"] > 1].copy()
sub["b"] = 0

# 想改原表：用 loc
df.loc[df["a"] > 1, "b"] = 99
```

> ⚠️ 判断标准：**`df.loc[mask, col] = ...`** 是原地修改，**`sub = ...; sub[col] = ...`** 是改副本。拿不准就先 `.copy()`，代价只是多一份数据。

**3. 多条件必须括号**：见上节。

**4. `SettingWithCopyWarning` 在 CoW 下变成了"什么都不提示"**：CoW 关闭时会警告，开启后连警告都没有，纯粹静默——更危险。

**5. 索引陷阱**：筛选后原索引保留，`merged.loc[0]` 可能对应不到你以为的那一行；必要时 `reset_index(drop=True)`。

> [要点] 一句话记住：**"要么 `.copy()`，要么 `.loc`"**，中间路线在 CoW 下不可靠。

## Polars：新一代列式 DataFrame

Polars 用 Rust 实现，采用 Arrow 内存格式、表达式 API 和惰性执行。Java 世界里最接近的类比是"Arrow + 一个能优化的关系代数引擎"（类似 DuckDB）：

> [Polars 示例](../code/libraries/06_data_science.py#L282-L322)

```python
{{#include ../code/libraries/06_data_science.py:282:322}}
```

```python
out = (
    df.lazy()
    .with_columns((pl.col("salary") * 0.1).alias("bonus"))
    .filter(pl.col("dept") == "RD")
    .group_by("dept")
    .agg(pl.col("salary").mean().alias("avg_salary"), pl.len().alias("cnt"))
    .collect()      # 到这里才真正计算
)
```

与 Pandas 的关键差异：

| 维度 | Pandas | Polars |
|------|--------|--------|
| 索引 | 有，行顺序隐含语义 | 无索引，行顺序无语义 |
| 执行 | 立即（eager） | `LazyFrame` 惰性，可做谓词下推 |
| 缺失值 | `NaN` / `None` 混用 | 统一 `null` |
| 并发 | 多为单线程 | 自动多线程 |
| 链式赋值坑 | 有 | 基本没有（表达式 API 天然不可变） |

> [要点] 新项目、尤其是大数据量或需要并行时优先 Polars；但 Pandas 生态最大（`sklearn` / `matplotlib` / 各种 IO 都吃它），两者可以互转（`pl.from_pandas` / `df.to_pandas()`）。

## Matplotlib：绘图

> [Matplotlib 示例](../code/libraries/06_data_science.py#L324-L362)

```python
{{#include ../code/libraries/06_data_science.py:324:362}}
```

```python
import matplotlib
matplotlib.use("Agg")                # 必须在 import pyplot 之前
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
axes[0].plot(x, np.sin(x), label="sin")
fig.savefig("demo.png", dpi=100)
```

> ⚠️ **脚本 / 服务器 / CI 里必须 `matplotlib.use("Agg")`**。默认后端需要显示器或 GUI 事件循环；在没有显示环境（headless）的机器上，`plt.show()` 会卡住或直接报错。对应 Java：JFreeChart 纯内存绘图不会有这问题，这是 Matplotlib 特有的坑。

- 对应 Java 的 JFreeChart：`Figure` ≈ `ChartPanel`，`Axes` ≈ `Plot`
- 多子图用 `subplots` 返回的 `axes` 数组，而不是全局状态
- 结束务必 `plt.close(fig)`，否则长驻进程会泄漏 figure

## 选型速查

> [选型速查表](../code/libraries/06_data_science.py#L364-L380)

```python
{{#include ../code/libraries/06_data_science.py:364:380}}
```

| 需求 | 首选 | 备选 | Java 对应 |
|------|------|------|-----------|
| 数值数组 / 线性代数 | NumPy | SciPy | EJML / ND4J |
| 表格清洗 / 统计 | Pandas | Polars | Tablesaw / Spark DataFrame |
| 大数据量列式计算 | Polars | DuckDB | Arrow / DuckDB |
| 绘图 | Matplotlib | Seaborn / Plotly | JFreeChart |
| 交互式探索 | Jupyter | VS Code Notebook | Zeppelin |
| 读 SQL 到表 | `pd.read_sql` | Polars SQL | JdbcTemplate / JPA |

## 小结

- **不要写行循环**：`iterrows` 是反模式，优先向量化 + 广播
- **切片不是拷贝**：修改原表用 `.loc[mask, col] = ...`，修改子集先 `.copy()`
- **多条件用 `&` / `|` 并加括号**：`and` / `or` 对 Series 直接报错
- **merge ∽ JOIN、groupby ∽ groupingBy**：SQL 心智直接迁移
- **Polars 更干净但生态较小**：无索引、惰性执行、`null` 统一
- **headless 环境必须 `Agg` 后端**

> 📁 [查看完整代码](../code/libraries/06_data_science.py)
