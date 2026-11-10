# 数据库与 ORM

本章覆盖 Python 访问数据库的完整层次：标准库 `sqlite3`（DB-API 2.0）、SQLAlchemy Core（类型安全构造 SQL）、SQLAlchemy ORM（对标 JPA / Hibernate），以及事务、连接池和 N+1 查询的应对方式。

## 全景对照：Java 数据访问栈

| Python 工具 | Java 对应 | 用途 / 差异 |
|-------------|-----------|-------------|
| DB-API 2.0（PEP 249） | JDBC | `Connection` / `Cursor` ≈ `Connection` / `Statement` + `ResultSet` |
| `sqlite3` | SQLite JDBC / H2 | 标准库内置的嵌入式库，零配置 |
| SQLAlchemy Core | jOOQ / JPA Criteria API | 用 Python 表达式拼类型安全的 SQL |
| SQLAlchemy ORM | JPA / Hibernate | 实体映射、关系、Session 管理 |
| `Engine` / `Session` | `EntityManagerFactory` / `EntityManager` | 连接池 / 工作单元 |
| `relationship` | `@OneToMany` / `@ManyToOne` | 关联映射 |
| `select().where()` | Criteria API | 2.0 风格的查询构建 |

> [示例](../code/libraries/07_database.py)

> ⚠️ 本章全部用内存 SQLite（`:memory:`），无需安装数据库，跑完即销毁。若 SQLAlchemy 未安装，对应片段会打印提示并跳过。

## sqlite3 与 DB-API 2.0

### 基础 CRUD 与参数化查询

> [sqlite3 基础 CRUD](../code/libraries/07_database.py#L34-L67)

```python
{{#include ../code/libraries/07_database.py:34:67}}
```

```python
cur.executemany(
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    [("Alice", "a@x.com", 30), ("Bob", "b@x.com", 25)],
)
cur.execute("SELECT id, name FROM users WHERE age >= ?", (30,))
rows = cur.fetchall()      # list[tuple]，默认按位置取值
```

对应 JDBC 的 `PreparedStatement`：

| Python | JDBC |
|--------|------|
| `cur.execute(sql, (arg,))` | `ps.setInt(1, arg); ps.executeQuery()` |
| `?` 占位符 | `?` 占位符（一致） |
| `:name` 命名参数 | `?name` → `setXxx("name", ...)` |
| `cur.fetchone()` / `fetchall()` | `rs.next()` / 遍历 `ResultSet` |
| `cur.rowcount` | `ps.getUpdateCount()` |

> ⚠️ **永远用 `?` 占位符，绝不用 f-string 拼 SQL**：

```python
# 危险：SQL 注入，等价于 Java 字符串拼接 JDBC（而 JDBC 至少有 PreparedStatement 可推荐）
name = input()
cur.execute(f"SELECT * FROM users WHERE name = '{name}'")

# 正确：参数化，驱动负责转义
cur.execute("SELECT * FROM users WHERE name = ?", (name,))
```

注意元组单元素要写成 `(name,)`——少写逗号会变成普通值，`sqlite3` 会把它当成字符序列逐字符绑定。

### row_factory：按列名取值

默认每行是 `tuple`，只能用下标；设置 `row_factory` 后才能像 JDBC 的 `rs.getString("name")` 一样取值：

> [row_factory 示例](../code/libraries/07_database.py#L70-L84)

```python
{{#include ../code/libraries/07_database.py:70:84}}
```

```python
conn.row_factory = sqlite3.Row     # 关键的一行
for row in conn.execute("SELECT * FROM t"):
    print(row["name"], dict(row))
```

> ⚠️ 这是 Java 开发者最容易"以为自动就有"的能力——`rs.getString("col")` 是 JDBC 默认行为，而 Python 默认是**位置元组**，改列顺序或加列就会静默错位。

### 事务：`with conn:` 不是关闭连接

> [事务与回滚示例](../code/libraries/07_database.py#L87-L119)

```python
{{#include ../code/libraries/07_database.py:87:119}}
```

```python
with conn:            # 进入时无操作；正常退出 → commit；抛异常 → rollback
    conn.execute("UPDATE account SET balance = balance - 100 WHERE id = 1")
    conn.execute("UPDATE account SET balance = balance + 100 WHERE id = 2")
```

> ⚠️ **`with conn:` 是事务上下文，不是 `close()`**。它对应的是：

```java
conn.setAutoCommit(false);
try {
    ...;
    conn.commit();
} catch (Exception e) {
    conn.rollback();
    throw e;
}
```

要关闭连接，仍然需要 `conn.close()`，推荐写成 `try/finally` 或嵌套使用。SQLAlchemy 里同理：`engine.begin()` 是事务，`engine.connect()` 才需要自己管。

### JOIN 与聚合

多表 JOIN、`COALESCE`、`LEFT JOIN` 保留空分组，全部走原生 SQL：

> [JOIN 与聚合示例](../code/libraries/07_database.py#L122-L152)

```python
{{#include ../code/libraries/07_database.py:122:152}}
```

```sql
SELECT d.name AS dept, COUNT(e.id) AS cnt, COALESCE(AVG(e.salary), 0) AS avg
FROM dept d LEFT JOIN emp e ON e.dept_id = d.id
GROUP BY d.id ORDER BY cnt DESC
```

> [要点] SQLite 对 `COUNT(e.id)`（忽略 NULL）与 `COUNT(*)` 的区分、`COALESCE` 处理 NULL，语义与 MySQL / PG 一致，可直接迁移。

## SQLAlchemy Core：类型安全的 SQL

Core 层不涉及对象映射，用 Python 表达式描述表结构和查询，最接近 **jOOQ**（也像 JPA Criteria API）：

> [SQLAlchemy Core 示例](../code/libraries/07_database.py#L154-L197)

```python
{{#include ../code/libraries/07_database.py:154:197}}
```

```python
stmt = (
    select(emp.c.dept, func.count().label("cnt"), func.avg(emp.c.salary).label("avg_salary"))
    .group_by(emp.c.dept)
    .order_by(func.avg(emp.c.salary).desc())
)
with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(row.dept, row.cnt, row.avg_salary)
```

与 jOOQ 的对应：`Table` ≈ `DSL.table`，`emp.c.dept` ≈ `EMP.DEPT`，`func.avg` ≈ `DSL.avg`。与 jOOQ 一样，它生成**平台无关**的 SQL（`str(stmt)` 可以看到实际 SQL），换数据库不用重写查询。

| 模式 | 事务 | 需手动 commit |
|------|------|---------------|
| `engine.begin()` | 自动开事务 | 退出时自动提交 / 回滚 |
| `engine.connect()` | 不自动开 | 需要显式 `conn.commit()` |

## SQLAlchemy ORM：对标 JPA / Hibernate

### 声明式模型

> [ORM 基础示例](../code/libraries/07_database.py#L199-L266)

```python
{{#include ../code/libraries/07_database.py:199:266}}
```

```python
class Base(DeclarativeBase):
    pass

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department", cascade="all, delete-orphan"
    )

class Employee(Base):
    __tablename__ = "employees"
    dept_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    department: Mapped[Department] = relationship(back_populates="employees")
```

映射关系：

| SQLAlchemy | JPA |
|------------|-----|
| `Base` + `Mapped[...]` | `@Entity` + 字段 |
| `mapped_column(...)` | `@Column` / `@Id` |
| `relationship(back_populates=...)` | `@OneToMany(mappedBy=...)` / `@ManyToOne` |
| `cascade="all, delete-orphan"` | `cascade = CascadeType.ALL, orphanRemoval = true` |
| `Session(engine)` | `EntityManager` |
| `session.commit()` | `em.flush() + tx.commit()` |
| `select(Employee)` | `em.createQuery(...)` / Criteria |

### Session 的四个语义差异

Java 开发者习惯 Spring 事务下的 `EntityManager` 托管，转过来最容易在这几处翻车：

> [ORM 常见坑](../code/libraries/07_database.py#L333-L347)

```python
{{#include ../code/libraries/07_database.py:333:347}}
```

**1. `Session` 不是线程安全的。** 一个线程一个 Session，或者用 `scoped_session` / `sessionmaker`。JPA 的 `EntityManager` 通常由容器绑定到线程，Python 没有容器，必须自己管。

**2. `commit()` 后对象默认 expire（≈ `LazyInitializationException` 的孪生兄弟）。**

```python
alice.salary = 16000
session.commit()
print(alice.salary)   # 触发一次 SELECT 重新加载
```

`expire_on_commit=True`（默认）会让所有对象在提交后失效，下次访问属性重新查库。如果要提交后继续使用对象数据（比如序列化返回给前端），用 `session.refresh(obj)` 或建 session 时设 `expire_on_commit=False`。

**3. Session 关闭后访问关系属性 → `DetachedInstanceError`**（对应 Hibernate 的 `LazyInitializationException`，根因相同：惰性加载需要活跃 Session）。

**4. 批量插入用 `add_all()` + 单次 `commit()`**，别在循环里 `commit()`——那是 N 次事务往返。

### ORM 的 CRUD 流程

> [ORM CRUD 片段](../code/libraries/07_database.py#L199-L266)

```python
{{#include ../code/libraries/07_database.py:199:266}}
```
```python
with Session(engine) as session:
    rd = Department(name="RD")
    rd.employees = [Employee(name="Alice", salary=15000), Employee(name="Bob", salary=18000)]
    session.add_all([rd, sales])
    session.commit()                    # 级联插入

    stmt = select(Employee).order_by(Employee.salary.desc())
    for e in session.scalars(stmt):
        print(e, e.department.name)     # 惰性加载 department

    session.delete(sales)               # 级联删除子对象
    session.commit()
```

> [要点] 2.0 风格用 `select(...)` + `session.scalars()`，而不是老式的 `session.query(...)`。新代码统一用前者。

### N+1 查询与 eager loading

这是 ORM 世界的头号性能杀手，代码里用事件监听器**实测**了三种写法的 SELECT 次数：

> [N+1 查询实测](../code/libraries/07_database.py#L269-L330)

```python
{{#include ../code/libraries/07_database.py:269:330}}
```

```python
# 默认（lazy="select"）：1 次查作者 + 每作者 1 次查书
authors = session.scalars(select(Author)).all()
_ = [(a.name, len(a.books)) for a in authors]          # SELECT 数 = 1 + N

# selectinload：2 条固定 SQL（IN 查询）
authors = session.scalars(select(Author).options(selectinload(Author.books))).all()

# joinedload：1 条 JOIN
authors = session.scalars(select(Author).options(joinedload(Author.books))).unique().all()
```

| 加载方式 | SELECT 数 | 适用场景 | JPA 对应 |
|----------|-----------|----------|----------|
| 默认 `lazy="select"` | 1 + N | 只访问少量父对象 | `FetchType.LAZY` |
| `selectinload` | 2 | 一对多集合（推荐默认） | `@BatchSize` / `@EntityGraph` |
| `joinedload` | 1 | 多对一 / 一对一 | `JOIN FETCH` |

> ⚠️ 3 个作者时是 4 vs 2 vs 1。生产环境 1000 行列表就是 **1001 次查询**——和 Hibernate 的 N+1 一模一样的问题，提前声明抓取策略即可。`joinedload` 必须加 `.unique()`，因为 JOIN 会展开重复行。

## 选型速查

> [选型速查表](../code/libraries/07_database.py#L349-L363)

```python
{{#include ../code/libraries/07_database.py:349:363}}
```
| 场景 | 首选 | 备选 | Java 对应 |
|------|------|------|-----------|
| 脚本 / 小工具 / 测试 | `sqlite3` | — | H2 / SQLite JDBC |
| 类型安全构造 SQL | SQLAlchemy Core | — | jOOQ / Criteria API |
| 复杂领域模型 / ORM | SQLAlchemy ORM | — | JPA / Hibernate |
| 异步服务 + DB | SQLAlchemy async / asyncpg | — | R2DBC |
| 纯数据管道 | DuckDB / Polars | — | 无直接对应 |

## 小结

- **永远参数化**：`?` 占位符，元组单元素记着加逗号
- **`with conn:` 是事务不是关闭**：commit / rollback 自动，close 仍要自己做
- **默认结果是元组**：要按列名取值必须设 `row_factory = sqlite3.Row`
- **Session 非线程安全**：commit 后默认 expire，detach 后访问关系报 `DetachedInstanceError`
- **关系默认惰性**：列表页一律 `selectinload`，实测能看到 1+N → 2 → 1 的差别
- **Core ∽ jOOQ、ORM ∽ Hibernate**：SQL 思维和抓取策略可以整套迁移

> 📁 [查看完整代码](../code/libraries/07_database.py)
