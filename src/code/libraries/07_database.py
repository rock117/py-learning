# -*- coding: utf-8 -*-
"""
07_database.py - Python 数据库访问：sqlite3 与 SQLAlchemy ORM

本文件面向有丰富 Java 经验的开发者，讲解 Python 数据持久化：
    - sqlite3           ：标准库内置的嵌入式 SQL 数据库（对比 H2 / SQLite JDBC）
    - DB-API 2.0        ：Python 的"JDBC 等价物"（PEP 249）
    - SQLAlchemy Core   ：SQL 表达式语言（类型安全地拼 SQL）
    - SQLAlchemy ORM    ：对象关系映射（对比 JPA / Hibernate）
    - 事务与连接池
    - N+1 查询问题与 eager loading

[Java 对比 总览]
    DB-API 2.0  ~ JDBC（Connection / Cursor 对应 Statement+ResultSet）
    SQLAlchemy  ~ Hibernate + JPA Criteria API 的合体
       - Engine/Session  ~ EntityManagerFactory / EntityManager
       - decl_base/Base   ~ @Entity + 元数据
       - relationship     ~ @OneToMany / @ManyToOne
       - select().where() ~ Criteria API

[注意] 全部使用内存 SQLite（:memory:），无需安装数据库，运行即销毁。
       若 SQLAlchemy 未安装，相应 demo 打印提示并跳过。
"""

import sqlite3
import sys


# =============================================================================
# 第一部分：DB-API 2.0 与 sqlite3 原生用法
# =============================================================================
# [Java 对比] sqlite3 模块 ~ JDBC 驱动；Cursor ~ Statement/ResultSet。

def demo_sqlite3_basic():
    """建表、插入、查询、参数化（防 SQL 注入）。"""
    print("=== 1. sqlite3 基础 CRUD ===")
    conn = sqlite3.connect(":memory:")
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE users (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT    NOT NULL,
                email   TEXT    UNIQUE,
                age     INTEGER CHECK (age >= 0)
            )
        """)

        # 参数化查询：永远不要用 f-string 拼 SQL
        users = [("Alice", "alice@example.com", 30),
                 ("Bob", "bob@example.com", 25),
                 ("Carol", "carol@example.com", 35)]
        cur.executemany("INSERT INTO users (name, email, age) VALUES (?, ?, ?)", users)
        conn.commit()
        print(f"  插入 {cur.rowcount} 行")

        cur.execute("SELECT id, name, age FROM users WHERE age >= ? ORDER BY age", (30,))
        rows = cur.fetchall()
        print(f"  age >= 30 的用户: {rows}")
        print(f"  取一行 fetchone(): {cur.fetchone()}  (已被 fetchall 取完，故为 None)")
    finally:
        conn.close()

    print("  [Java 对比]")
    print("    PreparedStatement ps = conn.prepareStatement(\"SELECT ... WHERE age >= ?\");")
    print("    ps.setInt(1, 30); ResultSet rs = ps.executeQuery();")
    print("  Python 中占位符是 ?（sqlite3 也支持 :name 命名参数）")


def demo_sqlite3_row_factory():
    """row_factory：让结果行支持按列名访问。"""
    print("\n=== 2. sqlite3.Row 按列名访问 ===")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row       # 关键：让每行支持 ["colname"]
    try:
        conn.execute("CREATE TABLE t (id INTEGER, name TEXT, score REAL)")
        conn.executemany("INSERT INTO t VALUES (?, ?, ?)",
                         [(1, "a", 90.5), (2, "b", 88.0)])
        for row in conn.execute("SELECT * FROM t"):
            print(f"  row['name'] = {row['name']}, row['score'] = {row['score']}")
            print(f"  转字典: {dict(row)}")
    finally:
        conn.close()
    print("  [Java 对比] rs.getString(\"name\")，但 Python 默认是元组，需要显式设置 row_factory")


def demo_sqlite3_transaction():
    """事务、回滚与上下文管理器。"""
    print("\n=== 3. 事务与回滚 ===")
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE account (id INTEGER PRIMARY KEY, balance INTEGER)")
        conn.execute("INSERT INTO account VALUES (1, 1000)")
        conn.execute("INSERT INTO account VALUES (2, 1000)")
        conn.commit()

        # 转账成功
        with conn:                     # with 块成功 -> 自动 commit；异常 -> 自动 rollback
            conn.execute("UPDATE account SET balance = balance - 100 WHERE id = 1")
            conn.execute("UPDATE account SET balance = balance + 100 WHERE id = 2")
        print(f"  转账成功后: {conn.execute('SELECT * FROM account').fetchall()}")

        # 转账失败（余额不足，业务上抛异常）
        class InsufficientFunds(Exception):
            pass

        try:
            with conn:
                conn.execute("UPDATE account SET balance = balance - 5000 WHERE id = 1")
                balance = conn.execute("SELECT balance FROM account WHERE id = 1").fetchone()[0]
                if balance < 0:
                    raise InsufficientFunds("余额不足")
        except InsufficientFunds as exc:
            print(f"  转账失败回滚: {exc}")

        print(f"  回滚后余额: {conn.execute('SELECT * FROM account').fetchall()}")
    finally:
        conn.close()
    print("  [Java 对比] conn.setAutoCommit(false) + try/commit/catch/rollback，Python 用 with 更简洁")


def demo_sqlite3_join_and_aggregate():
    """多表 JOIN 与聚合。"""
    print("\n=== 4. JOIN 与聚合查询 ===")
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript("""
            CREATE TABLE dept (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE emp  (id INTEGER PRIMARY KEY, name TEXT, dept_id INTEGER, salary REAL);
            INSERT INTO dept VALUES (1, 'RD'), (2, 'Sales'), (3, 'Empty');
            INSERT INTO emp  VALUES (1, 'Alice', 1, 15000),
                                    (2, 'Bob',   1, 18000),
                                    (3, 'Carol', 2, 12000);
        """)
        sql = """
            SELECT d.name AS dept, COUNT(e.id) AS cnt, COALESCE(AVG(e.salary), 0) AS avg_salary
            FROM dept d
            LEFT JOIN emp e ON e.dept_id = d.id
            GROUP BY d.id
            ORDER BY cnt DESC
        """
        for dept, cnt, avg in conn.execute(sql):
            print(f"  {dept:<8} 人数={cnt}  平均薪资={avg:.1f}")
    finally:
        conn.close()
    print("  [要点] COALESCE 处理 NULL；LEFT JOIN 保留没有员工的部门")


# =============================================================================
# 第二部分：SQLAlchemy Core
# =============================================================================
# [Java 对比] SQLAlchemy Core ~ JPA Criteria API / jOOQ（类型安全 SQL 构造器）

def demo_sqlalchemy_core():
    """SQLAlchemy Core：Table + select/insert。"""
    print("\n=== 5. SQLAlchemy Core ===")
    try:
        from sqlalchemy import (create_engine, MetaData, Table, Column,
                                Integer, String, Float, insert, select, func)
    except ImportError:
        print("  [注意] SQLAlchemy 未安装，跳过。安装: pip install sqlalchemy")
        return

    engine = create_engine("sqlite:///:memory:", echo=False)
    metadata = MetaData()
    emp = Table(
        "emp", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50), nullable=False),
        Column("dept", String(20), nullable=False),
        Column("salary", Float, nullable=False),
    )
    metadata.create_all(engine)

    with engine.begin() as conn:      # begin() -> 事务上下文
        conn.execute(insert(emp), [
            {"name": "Alice", "dept": "RD", "salary": 15000},
            {"name": "Bob", "dept": "RD", "salary": 18000},
            {"name": "Carol", "dept": "Sales", "salary": 12000},
        ])

    stmt = (
        select(emp.c.dept, func.count().label("cnt"), func.avg(emp.c.salary).label("avg_salary"))
        .group_by(emp.c.dept)
        .order_by(func.avg(emp.c.salary).desc())
    )
    with engine.connect() as conn:
        for row in conn.execute(stmt):
            print(f"  {row.dept:<8} 人数={row.cnt}  平均薪资={row.avg_salary:.1f}")
    print("  [生成的实际 SQL]", str(stmt).replace("\n", " "))


# =============================================================================
# 第三部分：SQLAlchemy ORM
# =============================================================================
# [Java 对比] SQLAlchemy ORM ~ JPA / Hibernate
#             但 Session 更"显式"：没有脏检查的隐式 flush 边界需要理解清楚。

def demo_sqlalchemy_orm():
    """声明式模型、关系映射、CRUD、查询。"""
    print("\n=== 6. SQLAlchemy ORM 基础 ===")
    try:
        from sqlalchemy import create_engine, ForeignKey, String, Integer, Float, select
        from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                                    relationship, Session)
    except ImportError:
        print("  [注意] SQLAlchemy 未安装，跳过。")
        return

    class Base(DeclarativeBase):
        pass

    class Department(Base):
        __tablename__ = "departments"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(30), unique=True)
        # [Java 对比] @OneToMany(mappedBy = "department", cascade = ALL)
        employees: Mapped[list["Employee"]] = relationship(
            back_populates="department", cascade="all, delete-orphan"
        )

        def __repr__(self) -> str:
            return f"Department(id={self.id}, name={self.name!r})"

    class Employee(Base):
        __tablename__ = "employees"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(50))
        salary: Mapped[float] = mapped_column(Float)
        dept_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
        # [Java 对比] @ManyToOne @JoinColumn(name = "dept_id")
        department: Mapped[Department] = relationship(back_populates="employees")

        def __repr__(self) -> str:
            return f"Employee(id={self.id}, name={self.name!r}, salary={self.salary})"

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        rd = Department(name="RD")
        sales = Department(name="Sales")
        rd.employees = [Employee(name="Alice", salary=15000),
                        Employee(name="Bob", salary=18000)]
        sales.employees = [Employee(name="Carol", salary=12000)]
        session.add_all([rd, sales])
        session.commit()            # [Java 对比] em.flush() + tx.commit()
        print(f"  已插入两个部门，ID: RD={rd.id}, Sales={sales.id}")

        # 查询：用 select(col) 而不是 session.query()（2.0 风格）
        stmt = select(Employee).order_by(Employee.salary.desc())
        for e in session.scalars(stmt):
            print(f"  {e}  部门={e.department.name}")

        # 更新
        alice = session.scalars(select(Employee).where(Employee.name == "Alice")).one()
        alice.salary = 16000
        session.commit()
        print(f"  更新后 Alice: {alice}")

        # 删除（级联）
        session.delete(sales)
        session.commit()
        remaining = session.scalars(select(Department)).all()
        emp_count = len(session.scalars(select(Employee)).all())
        print(f"  删除 Sales 后: 部门={remaining}, 员工数={emp_count}（级联已删 Carol）")


def demo_sqlalchemy_n_plus_one():
    """N+1 查询问题与 eager loading（joinedload / selectinload）。"""
    print("\n=== 7. N+1 查询与 eager loading ===")
    try:
        from sqlalchemy import create_engine, ForeignKey, String, select
        from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                                    relationship, Session, joinedload, selectinload)
    except ImportError:
        print("  [注意] SQLAlchemy 未安装，跳过。")
        return

    class Base(DeclarativeBase):
        pass

    class Author(Base):
        __tablename__ = "authors"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(30))
        books: Mapped[list["Book"]] = relationship(back_populates="author")

    class Book(Base):
        __tablename__ = "books"
        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str] = mapped_column(String(60))
        author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
        author: Mapped[Author] = relationship(back_populates="books")

    engine = create_engine("sqlite:///:memory:", echo=False)  # 关掉 echo 以便统计语句数
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        for i in range(3):
            session.add(Author(name=f"Author{i}", books=[Book(title=f"Book{i}-{j}") for j in range(3)]))
        session.commit()

    # 用 event listener 统计实际执行的 SELECT 次数
    from sqlalchemy import event
    counter = {"n": 0}

    def count_sql(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            counter["n"] += 1

    event.listen(engine, "before_cursor_execute", count_sql)

    with Session(engine) as session:
        counter["n"] = 0
        authors = session.scalars(select(Author)).all()
        _ = [(a.name, len(a.books)) for a in authors]     # 每个 author 触发一次延迟加载
        print(f"  [惰性加载] 查询 {len(authors)} 个作者耗时 SELECT 数: {counter['n']}  (1 + N)")

        counter["n"] = 0
        authors = session.scalars(select(Author).options(selectinload(Author.books))).all()
        _ = [(a.name, len(a.books)) for a in authors]
        print(f"  [selectinload] SELECT 数: {counter['n']}  (固定 2 条)")

        counter["n"] = 0
        authors = session.scalars(select(Author).options(joinedload(Author.books))).unique().all()
        _ = [(a.name, len(a.books)) for a in authors]
        print(f"  [joinedload]   SELECT 数: {counter['n']}  (1 条 JOIN)")

    print("  [Java 对比] JPA 的 fetch = FetchType.LAZY/EAGER + @EntityGraph，同一类问题")


def demo_sqlalchemy_pitfalls():
    """ORM 常见坑速览。"""
    print("\n=== 8. ORM 常见坑 ===")
    print("  1. Session 不是线程安全的 —— 一个线程一个 Session，或用 scoped_session")
    print("  2. 不要在 Session 关闭后访问关系属性（DetachedInstanceError ~ LazyInitializationException）")
    print("  3. session.commit() 后对象默认 expire，再次访问属性会重新查库")
    print("     -> 需要保留数据用 session.refresh(obj) 或 expire_on_commit=False")
    print("  4. 批量插入用 session.add_all() + 单次 commit，而不是循环 commit")
    print("  5. 关系默认是 lazy='select'，列表页展示子集合时极易 N+1")
    print("  [Java 对比] 与 Hibernate 的 LazyInitializationException / N+1 一一对应")


# =============================================================================
# 第四部分：速查表
# =============================================================================

def print_cheatsheet():
    print("\n=== 9. 选型速查表 ===")
    rows = [
        ("场景", "推荐", "Java 对应"),
        ("脚本 / 小工具 / 测试", "sqlite3", "H2 / SQLite JDBC"),
        ("需要类型安全构造 SQL", "SQLAlchemy Core", "jOOQ / Criteria API"),
        ("领域模型复杂 / 要 ORM", "SQLAlchemy ORM", "JPA / Hibernate"),
        ("异步 Web 服务 + DB", "SQLAlchemy 2.0 async / asyncpg", "R2DBC"),
        ("只做数据管道", "DuckDB / Polars", "无直接对应"),
    ]
    widths = [max(len(str(r[i])) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        print("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 60)
    print("Python 数据库访问演示 (sqlite3 / SQLAlchemy)")
    print(f"Python {sys.version.split()[0]}   sqlite3 {sqlite3.sqlite_version}")
    print("=" * 60)

    demo_sqlite3_basic()
    demo_sqlite3_row_factory()
    demo_sqlite3_transaction()
    demo_sqlite3_join_and_aggregate()
    demo_sqlalchemy_core()
    demo_sqlalchemy_orm()
    demo_sqlalchemy_n_plus_one()
    demo_sqlalchemy_pitfalls()
    print_cheatsheet()

    print("\n" + "=" * 60)
    print("所有 demo 运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
