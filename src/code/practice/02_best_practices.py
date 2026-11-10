# -*- coding: utf-8 -*-
"""
02_best_practices.py - Python 最佳实践
========================================

本文件演示 Python 编程的最佳实践，面向有丰富 Java 经验的开发者。

Java 对比要点：
- Pythonic 写法类似 Java 的 "Effective Java" 最佳实践，但语法更简洁
- Python 用 EAFP（请求宽恕）风格，Java 倾向 LBYL（请求许可）
- Python 异常体系类似 Java，但检查异常不强制（无 checked exception）
- Python 用 pytest 替代 JUnit，用 logging 替代 SLF4J/Logback

运行方式：python 02_best_practices.py
注意：Windows 控制台默认 GBK 编码，本文件避免在 print 中使用 emoji。
"""

import os
import sys
import json
import time
import logging
import unittest
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager


# ============================================================
# 1. Pythonic 写法
# ============================================================

def demo_enumerate():
    """enumerate 替代 range(len())。

    Java 对比：Java 的 for-each 无法同时获取索引和值，需手动维护计数器。
    Python 的 enumerate 优雅地解决这个问题。
    """
    print("=== enumerate 替代 range(len()) ===")

    fruits = ["apple", "banana", "cherry"]

    # 不推荐：Java 式写法
    for i in range(len(fruits)):
        print(f"  [{i}] {fruits[i]}")

    # 推荐：Pythonic 写法
    for index, fruit in enumerate(fruits):
        print(f"  [{index}] {fruit}")

    # enumerate 还支持指定起始索引
    for index, fruit in enumerate(fruits, start=1):
        print(f"  第{index}个: {fruit}")
    print("[提示] enumerate 比手动 range(len()) 更清晰、更安全")


def demo_zip():
    """zip 并行迭代。

    Java 对比：Java 需手动用索引遍历两个列表，或用 Stream 配合 IntStream。
    Python 的 zip 优雅地并行迭代多个序列。
    """
    print("=== zip 并行迭代 ===")

    names = ["Alice", "Bob", "Charlie"]
    ages = [30, 25, 35]
    cities = ["Beijing", "Shanghai", "Guangzhou"]

    # 并行迭代多个列表
    for name, age, city in zip(names, ages, cities):
        print(f"  {name}, {age}岁, {city}")

    # zip 生成的是元组，可转 dict
    name_age = dict(zip(names, ages))
    print(f"  转 dict: {name_age}")

    # zip_longest：不等长时填充（需 from itertools import zip_longest）
    from itertools import zip_longest
    short = [1, 2, 3]
    long = [10, 20, 30, 40, 50]
    for a, b in zip_longest(short, long, fillvalue=0):
        print(f"  zip_longest: {a}, {b}")
    print("[提示] zip 以最短的为准，zip_longest 填充到最长")


def demo_unpacking():
    """解包 unpacking（含 * 和 ** 解包）。

    Java 对比：Java 没有原生解包语法，需手动取数组元素。
    """
    print("=== 解包 unpacking ===")

    # 基本解包
    point = (3, 4, 5)
    x, y, z = point
    print(f"  基本解包: x={x}, y={y}, z={z}")

    # 星号解包：收集剩余元素
    first, *rest = [1, 2, 3, 4, 5]
    print(f"  first={first}, rest={rest}")

    *init, last = [1, 2, 3, 4, 5]
    print(f"  init={init}, last={last}")

    # 函数调用时 * 和 ** 解包
    def greet(name, greeting, punctuation):
        return f"{greeting}, {name}{punctuation}"

    args = ["Alice", "Hello", "!"]
    print(f"  *解包调用: {greet(*args)}")

    kwargs = {"name": "Bob", "greeting": "Hi", "punctuation": "."}
    print(f"  **解包调用: {greet(**kwargs)}")

    # 3.5+ 支持在字面量中解包
    list1 = [1, 2]
    list2 = [3, 4]
    merged_list = [*list1, *list2]
    print(f"  列表合并: {merged_list}")

    dict1 = {"a": 1}
    dict2 = {"b": 2}
    merged_dict = {**dict1, **dict2}
    print(f"  字典合并: {merged_dict}")
    print("[提示] 解包让代码更简洁，* 收集/展开序列，** 展开/合并字典")


def demo_walrus_operator():
    """walrus := 在循环中的优雅用法。

    Java 对比：Java 没有赋值表达式，无法在条件中赋值。
    海象运算符 := 在表达式内赋值，减少重复代码。
    """
    print("=== walrus := 海象运算符 ===")

    # 场景1：在 while 条件中读取输入
    # 模拟读取数据流
    data_stream = iter(["line1", "line2", "", "line4", None])

    # 不用 walrus：需要重复调用
    # chunk = next(data_stream)
    # while chunk is not None:
    #     process(chunk)
    #     chunk = next(data_stream)

    # 用 walrus：一行搞定
    results = []
    while (chunk := next(data_stream, None)) is not None:
        if chunk:  # 跳过空字符串
            results.append(chunk)
    print(f"  读取结果: {results}")

    # 场景2：在列表推导式中使用
    import math
    raw_values = [4, -1, 9, -4, 16]
    # 只保留非负值，同时计算平方根（先过滤再计算）
    sqrt_pairs = [(x, math.sqrt(x)) for x in raw_values if x >= 0]
    print(f"  平方根对: {sqrt_pairs}")

    # walrus 在推导式中更实用的场景：避免重复调用昂贵的函数
    def expensive_check(x):
        return x * 2 if x > 0 else None

    # 不用 walrus：expensive_check 调用两次
    # result = [y for x in data if (y := expensive_check(x)) is not None]
    data = [1, -2, 3, -4, 5]
    result = [y for x in data if (y := expensive_check(x)) is not None]
    print(f"  walrus 避免重复调用: {result}")
    print("[提示] := 减少重复计算和临时变量，但不要滥用降低可读性")


def demo_conditional_expression():
    """条件表达式（三元运算符）。

    Java 对比：Java 的三元运算符是 cond ? a : b，Python 是 a if cond else b。
    """
    print("=== 条件表达式 ===")

    age = 20
    status = "成年" if age >= 18 else "未成年"
    print(f"  年龄{age}: {status}")

    # 嵌套（不推荐过度嵌套）
    score = 85
    grade = "A" if score >= 90 else ("B" if score >= 80 else "C")
    print(f"  分数{score}: {grade}")
    print("[提示] Python 三元运算符: value_true if condition else value_false")


def demo_multiple_assignment():
    """多重赋值与交换 a, b = b, a。

    Java 对比：Java 交换需要临时变量。
    """
    print("=== 多重赋值与交换 ===")

    # 同时赋值
    a, b, c = 1, 2, 3
    print(f"  同时赋值: a={a}, b={b}, c={c}")

    # 交换：无需临时变量
    a, b = b, a
    print(f"  交换后  : a={a}, b={b}")

    # 函数返回多值解包
    def min_max(lst):
        return min(lst), max(lst)

    lo, hi = min_max([3, 1, 4, 1, 5, 9])
    print(f"  min_max: lo={lo}, hi={hi}")
    print("[提示] Python 多重赋值基于元组解包，交换无需临时变量")


def demo_chained_comparison():
    """链式比较 0 < x < 100。

    Java 对比：Java 不支持链式比较，需写 0 < x && x < 100。
    """
    print("=== 链式比较 ===")

    x = 50
    # Pythonic：链式比较
    in_range = 0 < x < 100
    print(f"  0 < {x} < 100 = {in_range}")

    # 等价于
    in_range2 = 0 < x and x < 100
    print(f"  0 < x and x < 100 = {in_range2}")

    # 链式比较只求值一次 x，更高效
    print("[提示] 链式比较 0 < x < 100 更简洁，且 x 只求值一次")


# ============================================================
# 2. 代码风格与质量
# ============================================================

def demo_pep8():
    """PEP 8 要点（在注释中）。

    PEP 8 是 Python 的代码风格指南，类似 Java 的 Google Java Style Guide。

    要点：
    - 缩进：4 个空格，不用 Tab
    - 行宽：建议 79 字符（PEP 8）/ 88 字符（Black 默认）
    - 命名：函数和变量用 snake_case，类用 PascalCase，常量用 UPPER_CASE
    - 导入：每个导入独占一行，标准库/第三方/本地分组
    - 运算符两侧空格：a = b + c，而非 a=b+c
    - 空行：函数间 2 空行，方法间 1 空行

    Java 对比：
    - Java 用 camelCase 命名方法/变量，Python 用 snake_case
    - Java 类名 PascalCase 两者一致
    """
    print("=== PEP 8 代码风格 ===")
    print("PEP 8 要点：")
    print("  - 缩进 4 空格，不用 Tab")
    print("  - 行宽 79/88 字符")
    print("  - snake_case 命名函数/变量，PascalCase 命名类")
    print("  - 导入分三组：标准库/第三方/本地")
    print("Java 对比：Java 用 camelCase，Python 用 snake_case")


def demo_type_hints():
    """类型注解最佳实践。

    Java 对比：Java 是静态类型，编译期检查；Python 类型注解是可选的，运行时不强制。
    用 mypy 做静态类型检查。
    """
    print("=== 类型注解 ===")

    # 基本类型注解
    def greet(name: str, times: int = 1) -> str:
        """带类型注解的函数。"""
        return (f"Hello, {name}! " * times).strip()

    print(f"  greet('Alice', 2) = {greet('Alice', 2)}")

    # 复杂类型：List, Dict, Optional
    def find_user(user_id: int) -> Optional[Dict[str, Any]]:
        """返回用户字典或 None。"""
        users = {1: {"name": "Alice", "age": 30}}
        return users.get(user_id)

    user = find_user(1)
    print(f"  find_user(1) = {user}")
    print(f"  find_user(99) = {find_user(99)}")

    # 3.9+ 可直接用 list/dict 泛型（无需 typing.List）
    def process(items: list[int]) -> dict[str, int]:
        return {str(x): x for x in items}

    print(f"  process([1,2,3]) = {process([1, 2, 3])}")
    print("[提示] 类型注解提升可读性，配合 mypy 静态检查")


def demo_ruff_note():
    """ruff lint + format 示例（在注释中说明）。

    ruff 是用 Rust 编写的极速 linter + formatter，替代 flake8 + isort + black：
        pip install ruff

    常用命令：
        ruff check .          # 检查代码
        ruff check --fix .    # 自动修复
        ruff format .         # 格式化代码（类似 black）

    Java 对比：类似 Checkstyle / SpotBugs / google-java-format，但速度快几十倍。
    """
    print("=== ruff lint + format ===")
    print("ruff 是极速 linter + formatter：pip install ruff")
    print("  ruff check .        # 检查")
    print("  ruff check --fix .  # 自动修复")
    print("  ruff format .       # 格式化")
    print("Java 对比：Checkstyle + SpotBugs + google-java-format 的合体，但快几十倍")


def demo_mypy_note():
    """mypy 类型检查示例。

    mypy 是 Python 的静态类型检查器：
        pip install mypy
        mypy your_script.py

    Java 对比：Java 编译器自带类型检查，Python 需要 mypy 做额外检查。
    """
    print("=== mypy 类型检查 ===")
    print("mypy 静态类型检查器：pip install mypy")
    print("  mypy your_script.py")
    print("  mypy --strict your_package/")
    print("Java 对比：Java 编译器自带类型检查，Python 需 mypy 额外检查")
    print("[提示] 在 CI 中集成 mypy 可提前发现类型错误")


# ============================================================
# 3. 错误处理最佳实践
# ============================================================

def demo_eafp_vs_lbyl():
    """EAFP vs LBYL。

    EAFP = Easier to Ask Forgiveness than Permission（请求宽恕比许可容易）
    LBYL = Look Before You Leap（三思而后行）

    Java 对比：Java 倾向 LBYL（先检查再操作），Python 推荐 EAFP（直接操作，捕获异常）。
    Python 异常处理开销小，EAFP 更 Pythonic。
    """
    print("=== EAFP vs LBYL ===")

    data = {"name": "Alice", "age": 30}

    # LBYL：先检查再访问
    if "email" in data:
        email = data["email"]
    else:
        email = "unknown"
    print(f"  LBYL: email = {email}")

    # EAFP：直接访问，捕获异常（Pythonic 推荐）
    try:
        email = data["email"]
    except KeyError:
        email = "unknown"
    print(f"  EAFP: email = {email}")

    # 更 Pythonic：用 dict.get
    email = data.get("email", "unknown")
    print(f"  get : email = {email}")
    print("[提示] Python 推荐 EAFP 风格，异常开销小，代码更直接")


def demo_precise_exception():
    """精确捕获异常，不要裸 except。"""
    print("=== 精确捕获异常 ===")

    # 错误：裸 except 会吞掉所有异常（包括 KeyboardInterrupt）
    # try:
    #     ...
    # except:          # [警告] 不要这样写！
    #     pass

    # 错误：except Exception 会吞掉大部分异常
    # try:
    #     ...
    # except Exception:  # [警告] 太宽泛
    #     pass

    # 正确：精确捕获特定异常
    def safe_divide(a, b):
        try:
            return a / b
        except ZeroDivisionError as e:
            print(f"  [捕获] 除零错误: {e}")
            return None
        except TypeError as e:
            print(f"  [捕获] 类型错误: {e}")
            return None

    print(f"  safe_divide(10, 0) = {safe_divide(10, 0)}")
    print(f"  safe_divide('a', 2) = {safe_divide('a', 2)}")
    print("[提示] 精确捕获具体异常类型，避免吞掉意外错误")


def demo_custom_exception():
    """自定义异常层次（对比 Java 异常体系）。

    Java 对比：
    - Java: Throwable -> Exception -> RuntimeException(非检查) / 其他(检查异常)
    - Python: BaseException -> Exception -> 自定义异常
    - Python 没有检查异常概念，所有异常都是非检查的
    """
    print("=== 自定义异常层次 ===")

    class AppError(Exception):
        """应用异常基类。"""
        pass

    class ValidationError(AppError):
        """数据验证错误。"""
        def __init__(self, field, message):
            self.field = field
            self.message = message
            super().__init__(f"{field}: {message}")

    class NotFoundError(AppError):
        """资源未找到错误。"""
        pass

    def get_user(user_id):
        if user_id < 0:
            raise ValidationError("user_id", "不能为负数")
        if user_id > 100:
            raise NotFoundError(f"用户 {user_id} 不存在")
        return {"id": user_id}

    # 捕获基类异常
    try:
        get_user(-1)
    except AppError as e:
        print(f"  [捕获] {type(e).__name__}: {e}")

    # 捕获特定子类
    try:
        get_user(999)
    except NotFoundError as e:
        print(f"  [捕获] NotFound: {e}")

    print("[提示] 自定义异常继承 Exception，建立层次结构便于统一处理")


def demo_exception_chain():
    """异常链 raise from。

    Java 对比：Java 用异常的 cause（Throwable.initCause），Python 用 raise ... from ...。
    """
    print("=== 异常链 raise from ===")

    def parse_config(raw):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            # 用 raise from 保留原始异常链
            raise ValueError("配置文件格式错误") from e

    try:
        parse_config("{invalid json}")
    except ValueError as e:
        print(f"  [捕获] {e}")
        print(f"  [原因] {e.__cause__}")
    print("[提示] raise ... from ... 保留异常因果链，便于调试")


def demo_context_manager():
    """上下文管理器管理资源。

    Java 对比：类似 Java 的 try-with-resources（Java 7+）。
    Python 用 with 语句，自动调用 __enter__ 和 __exit__。
    """
    print("=== 上下文管理器 ===")

    # 用类实现
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            print("  [Timer] 开始计时")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.elapsed = time.perf_counter() - self.start
            print(f"  [Timer] 耗时 {self.elapsed * 1e3:.2f} ms")
            # 返回 False（默认）不吞异常，返回 True 吞掉异常
            return False

    with Timer() as t:
        _ = sum(range(100000))

    # 用 contextlib.contextmanager 装饰器实现（更简洁）

    @contextmanager
    def timer_context():
        start = time.perf_counter()
        try:
            yield  # with 块内的代码在这里执行
        finally:
            elapsed = time.perf_counter() - start
            print(f"  [contextmanager] 耗时 {elapsed * 1e3:.2f} ms")

    with timer_context():
        _ = sum(range(100000))

    print("[提示] with 语句自动管理资源，contextmanager 装饰器简化实现")


# ============================================================
# 4. 项目结构最佳实践
# ============================================================

def demo_project_structure():
    """项目结构最佳实践（在注释/字符串中展示）。

    Python 推荐使用 src layout：

    my_project/
    |-- pyproject.toml
    |-- src/
    |   |-- my_package/
    |   |   |-- __init__.py
    |   |   |-- module_a.py
    |   |   |-- module_b.py
    |   |-- tests/
    |       |-- test_module_a.py
    |-- docs/
    |-- README.md

    Java 对比：Java 用 Maven/Gradle 的 src/main/java + src/test/java 结构。
    Python 的 src layout 避免意外导入未安装的包。
    """
    print("=== 项目结构最佳实践 ===")
    print("推荐 src layout：")
    print("  my_project/")
    print("  |-- pyproject.toml")
    print("  |-- src/my_package/__init__.py")
    print("  |-- tests/test_xxx.py")
    print("Java 对比：Maven 的 src/main/java + src/test/java")


def demo_init_and_all():
    """__init__.py 的用法与 __all__。

    __init__.py 标记目录为 Python 包。
    __all__ 控制 from package import * 时导出的名称。
    """
    print("=== __init__.py 与 __all__ ===")

    # 模拟一个包的 __init__.py 内容
    init_content = '''
# my_package/__init__.py
__all__ = ["public_func", "PublicClass"]

def public_func():
    """公开 API。"""
    pass

def _private_func():
    """私有函数，下划线前缀表示内部使用。"""
    pass

class PublicClass:
    pass
'''
    print(init_content)
    print("[提示] __all__ 控制 `from package import *` 的导出范围")
    print("  下划线前缀 _name 表示内部使用（约定，非强制）")


def demo_pyproject_toml():
    """pyproject.toml 关键配置。"""
    print("=== pyproject.toml 关键配置 ===")
    toml_example = '''
# pyproject.toml - Python 项目的标准配置文件
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "my-package"
version = "1.0.0"
description = "A sample package"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.28",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "mypy>=1.0", "ruff>=0.1"]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
'''
    print(toml_example)
    print("Java 对比：pyproject.toml 类似 pom.xml / build.gradle")


# ============================================================
# 5. 测试最佳实践
# ============================================================

def demo_pytest_fixtures():
    """pytest fixtures 基础（对比 JUnit @BeforeEach）。

    Java 对比：pytest fixture 类似 JUnit 的 @BeforeEach / @BeforeAll。
    fixture 通过依赖注入，比 JUnit 注解更灵活。
    """
    print("=== pytest fixtures ===")
    test_code = '''
import pytest

# fixture：测试前的准备工作（类似 @BeforeEach）
@pytest.fixture
def sample_list():
    """每个测试函数前创建新列表。"""
    return [1, 2, 3, 4, 5]

# scope="session" 全会话只创建一次（类似 @BeforeAll）
@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection()
    yield conn  # yield 之后的代码在测试结束后执行（teardown）
    conn.close()

def test_sum(sample_list):
    assert sum(sample_list) == 15

def test_len(sample_list):
    assert len(sample_list) == 5
'''
    print(test_code)
    print("[提示] fixture 通过参数名注入，scope 控制生命周期")


def demo_pytest_parametrize():
    """parametrize 参数化测试（对比 JUnit @ParameterizedTest）。"""
    print("=== pytest parametrize ===")
    test_code = '''
import pytest

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (10, 20, 30),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add(a, b, expected):
    assert a + b == expected

# Java 对比：类似 @ParameterizedTest + @CsvSource
'''
    print(test_code)
    print("[提示] parametrize 一次测试多组数据，避免重复代码")


def demo_pytest_assert():
    """assert 的用法与 pytest 断言重写。"""
    print("=== pytest assert ===")
    test_code = '''
def test_example():
    # pytest 会重写 assert 语句，提供详细错误信息
    x = 10
    y = 20
    assert x == y, f"期望 {x} 等于 {y}"  # 失败时显示变量值

    # 对比 Java：assertEquals(expected, actual)
    assert sum([1, 2, 3]) == 6

    # 集合断言
    assert set([1, 2]) == {1, 2}

    # 异常断言
    import pytest
    with pytest.raises(ZeroDivisionError):
        1 / 0
'''
    print(test_code)
    print("[提示] pytest 重写 assert，失败时显示表达式各部分值")


def demo_test_organization():
    """测试命名与组织。"""
    print("=== 测试命名与组织 ===")
    print("命名规范：")
    print("  - 文件：test_<模块名>.py 或 <模块名>_test.py")
    print("  - 函数：test_<行为>_<条件>()，如 test_login_with_valid_credentials")
    print("  - 类：Test<功能>，如 TestUserService")
    print("组织结构：")
    print("  tests/")
    print("    |-- unit/          # 单元测试")
    print("    |-- integration/   # 集成测试")
    print("    |-- conftest.py    # 共享 fixture")
    print("Java 对比：类似 Maven Surefire 的 test 命名约定")


# ============================================================
# 6. 日志最佳实践
# ============================================================

def demo_logging_basic():
    """logging 基础配置。

    Java 对比：Python logging 类似 SLF4J + Logback。
    logging 是标准库，无需额外依赖。
    """
    print("=== logging 基础配置 ===")

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("my_app")

    logger.debug("调试信息（默认不显示）")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")

    print("[提示] logging 比 print 更灵活：支持级别、格式、文件输出")
    print("Java 对比：SLF4J + Logback 的 Python 版")


def demo_structured_logging():
    """结构化日志（JSON 格式）。

    Java 对比：类似 Logstash JSON encoder，便于 ELK 采集。
    """
    print("=== 结构化日志（JSON） ===")

    import json as json_module

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json_module.dumps(log_data, ensure_ascii=False)

    # 创建专用 logger
    json_logger = logging.getLogger("json_logger")
    json_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    json_logger.addHandler(handler)
    json_logger.setLevel(logging.INFO)

    json_logger.info("用户登录成功")
    json_logger.warning("登录失败次数过多", extra={"user": "alice", "attempts": 5})
    print("[提示] JSON 日志便于机器解析，适合 ELK/Loki 等日志系统")


def demo_logging_levels():
    """日志级别使用规范。"""
    print("=== 日志级别规范 ===")
    print("DEBUG   : 调试细节，生产环境关闭")
    print("INFO    : 关键业务流程（用户登录、订单创建）")
    print("WARNING : 可预期的问题，不影响功能（如重试、降级）")
    print("ERROR   : 错误，影响部分功能，需关注")
    print("CRITICAL: 严重错误，系统不可用")
    print("Java 对比：与 SLF4J 的 trace/debug/info/warn/error 对应")


def demo_avoid_print_as_log():
    """避免 print 作为日志。"""
    print("=== 避免 print 作为日志 ===")
    print("[警告] 不要用 print 替代 logging：")
    print("  - print 无法控制级别")
    print("  - print 无法输出到文件")
    print("  - print 无法添加时间戳和格式")
    print("  - print 无法按模块过滤")
    print("[提示] 生产代码用 logging，print 仅用于调试")


# ============================================================
# 7. 配置管理
# ============================================================

def demo_env_var():
    """环境变量 + os.environ。

    Java 对比：Java 也用 System.getenv()，Python 用 os.environ。
    """
    print("=== 环境变量 ===")

    # 设置环境变量（演示用）
    os.environ["APP_DEBUG"] = "true"
    os.environ["APP_PORT"] = "8080"

    # 读取环境变量
    debug = os.environ.get("APP_DEBUG", "false")  # 带默认值
    port = int(os.environ.get("APP_PORT", "8000"))

    print(f"  APP_DEBUG = {debug}")
    print(f"  APP_PORT  = {port}")

    # 不存在时返回 None 或默认值
    missing = os.environ.get("NOT_SET", "default_value")
    print(f"  NOT_SET   = {missing}")
    print("[提示] os.environ.get(key, default) 避免 KeyError")


def demo_dotenv_note():
    """.env 文件 + python-dotenv（注释说明）。

    python-dotenv 从 .env 文件加载环境变量：
        pip install python-dotenv

    .env 文件示例：
        APP_DEBUG=true
        DATABASE_URL=postgresql://user:pass@localhost/db

    代码：
        from dotenv import load_dotenv
        load_dotenv()  # 加载 .env 文件
        debug = os.getenv("APP_DEBUG")

    Java 对比：类似 Spring Boot 的 application.properties / .env 配置。
    """
    print("=== .env 文件 + python-dotenv ===")
    print("python-dotenv 从 .env 文件加载环境变量：pip install python-dotenv")
    print("  .env: APP_DEBUG=true")
    print("  代码: load_dotenv(); os.getenv('APP_DEBUG')")
    print("Java 对比：Spring Boot 的 application.properties")


def demo_pydantic_settings_note():
    """pydantic-settings 类型安全配置（注释说明）。

    pydantic-settings 提供类型安全的配置管理：
        pip install pydantic-settings

    示例：
        from pydantic_settings import BaseSettings

        class Settings(BaseSettings):
            app_name: str = "MyApp"
            debug: bool = False
            port: int = 8000

            class Config:
                env_prefix = "APP_"  # 环境变量前缀

        settings = Settings()  # 自动从环境变量加载并验证类型

    Java 对比：类似 Spring Boot 的 @ConfigurationProperties，类型安全。
    """
    print("=== pydantic-settings 类型安全配置 ===")
    print("pydantic-settings：pip install pydantic-settings")
    print("  class Settings(BaseSettings):")
    print("      port: int = 8000  # 自动类型转换和验证")
    print("Java 对比：Spring Boot 的 @ConfigurationProperties")


def demo_12factor_config():
    """12-factor app 配置原则。"""
    print("=== 12-factor app 配置原则 ===")
    print("原则：配置存储在环境变量中，而非代码中")
    print("好处：")
    print("  - 同一代码可在不同环境（dev/staging/prod）运行")
    print("  - 敏感信息（密码、密钥）不进版本控制")
    print("  - 部署时通过环境变量注入配置")
    print("Java 对比：Spring Boot 的外部化配置理念一致")


# ============================================================
# 8. 文档最佳实践
# ============================================================

def demo_docstring_google():
    """docstring 规范（Google/Sphinx/reST 风格）。"""
    print("=== docstring 规范 ===")

    def example_google_style(param1, param2=None):
        """一句话简述。

        详细描述，可以多行。

        Args:
            param1: 第一个参数说明。
            param2: 第二个参数，可选，默认 None。

        Returns:
            返回值说明。

        Raises:
            ValueError: 当 param1 为负数时。

        Examples:
            >>> example_google_style(1)
            2
        """
        if param1 < 0:
            raise ValueError("param1 不能为负数")
        return param1 + (param2 or 1)

    print("Google 风格（推荐）：")
    print("  Args: / Returns: / Raises: / Examples:")
    print()
    print("reST 风格（Sphinx 默认）：")
    print("  :param param1: 说明")
    print("  :returns: 说明")
    print("  :raises ValueError: 说明")
    print()
    print("NumPy 风格：")
    print("  Parameters / Returns / Raises（带下划线分隔）")
    print("Java 对比：类似 Javadoc 的 @param @return @throws")


def demo_type_hints_and_docs():
    """type hints 与文档的关系。"""
    print("=== type hints 与文档 ===")
    print("type hints 补充 docstring，两者配合：")
    print("  - type hints：机器可读，mypy 检查，IDE 提示")
    print("  - docstring：人可读，说明语义和用法")
    print("  - 两者不冲突，type hints 描述类型，docstring 描述含义")
    print("Java 对比：Javadoc 中 @param 的类型是冗余的（编译器已知），")
    print("  Python 的 type hints 和 docstring 各有侧重")


def demo_module_docstring():
    """模块级文档字符串。"""
    print("=== 模块级文档字符串 ===")
    print("模块/文件开头的三引号字符串是模块文档：")
    print('  """模块功能简述。')
    print('  详细说明、使用示例。')
    print('  """')
    print("可通过 help(module) 或 module.__doc__ 访问")
    print("Java 对比：类似 package-info.java 的作用")


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print("Python 最佳实践 - 面向 Java 开发者")
    print("=" * 60)
    print()

    sections = [
        ("Pythonic 写法", [
            demo_enumerate, demo_zip, demo_unpacking,
            demo_walrus_operator, demo_conditional_expression,
            demo_multiple_assignment, demo_chained_comparison,
        ]),
        ("代码风格与质量", [
            demo_pep8, demo_type_hints, demo_ruff_note, demo_mypy_note,
        ]),
        ("错误处理最佳实践", [
            demo_eafp_vs_lbyl, demo_precise_exception, demo_custom_exception,
            demo_exception_chain, demo_context_manager,
        ]),
        ("项目结构最佳实践", [
            demo_project_structure, demo_init_and_all, demo_pyproject_toml,
        ]),
        ("测试最佳实践", [
            demo_pytest_fixtures, demo_pytest_parametrize,
            demo_pytest_assert, demo_test_organization,
        ]),
        ("日志最佳实践", [
            demo_logging_basic, demo_structured_logging,
            demo_logging_levels, demo_avoid_print_as_log,
        ]),
        ("配置管理", [
            demo_env_var, demo_dotenv_note,
            demo_pydantic_settings_note, demo_12factor_config,
        ]),
        ("文档最佳实践", [
            demo_docstring_google, demo_type_hints_and_docs,
            demo_module_docstring,
        ]),
    ]

    for title, funcs in sections:
        print()
        print("# " + "=" * 56)
        print(f"# {title}")
        print("# " + "=" * 56)
        for func in funcs:
            print()
            func()

    print()
    print("=" * 60)
    print("全部演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
