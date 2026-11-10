# -*- coding: utf-8 -*-
"""
03_decorators.py - 装饰器进阶
============================

本文件演示 Python 装饰器的各种用法和 functools 工具。
面向有丰富 Java 经验的开发者。

Java 对比：
- Java 没有直接的装饰器语法，类似功能靠注解 + AOP（如 Spring AOP）实现。
- Python 装饰器是语言级特性，本质是高阶函数（接收函数返回函数）。
- @decorator 语法是 `func = decorator(func)` 的语法糖。
"""

import functools
import time
import logging
from typing import Any, Callable, TypeVar
from functools import lru_cache, singledispatch, cached_property

F = TypeVar("F", bound=Callable[..., Any])


# ============================================================================
# 1. 基础装饰器回顾
# ============================================================================

def simple_logger(func: Callable) -> Callable:
    """最简单的装饰器：打印调用日志。

    Java 对比：类似 Spring AOP 的 @Before 切面。
    """
    def wrapper(*args, **kwargs):
        print(f"  [LOG] 调用 {func.__name__}({args}, {kwargs})")
        result = func(*args, **kwargs)
        print(f"  [LOG] {func.__name__} 返回 {result}")
        return result
    return wrapper


@simple_logger
def add(a: int, b: int) -> int:
    return a + b


def demo_basic_decorator() -> None:
    """演示基础装饰器。"""
    print("=== 基础装饰器 ===")
    print(f"add(2, 3) = {add(2, 3)}")


# ============================================================================
# 2. 带参数装饰器（三层嵌套）
# ============================================================================

def repeat(times: int) -> Callable:
    """带参数的装饰器：重复执行 N 次。

    三层嵌套结构：
    - 最外层接收参数（times）
    - 中间层接收被装饰函数（func）
    - 最内层是实际执行的 wrapper

    Java 对比：类似带参数的注解 @Repeat(3)。
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = None
            for i in range(times):
                print(f"  第 {i+1}/{times} 次执行 {func.__name__}")
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


@repeat(3)
def say_hello(name: str) -> str:
    return f"hello {name}"


def demo_param_decorator() -> None:
    """演示带参数装饰器。"""
    print("\n=== 带参数装饰器 ===")
    print(say_hello("Alice"))


# ============================================================================
# 3. 类装饰器（用 __call__ 实现）
# ============================================================================

class CountCalls:
    """类装饰器：统计函数调用次数。

    类装饰器利用 __call__ 让实例可调用。
    优点：可以保存状态（比闭包更清晰）。

    Java 对比：类似一个实现了 InvocationHandler 的代理类。
    """

    def __init__(self, func: Callable) -> None:
        self.func = func
        self.count = 0
        functools.update_wrapper(self, func)  # 保留元信息

    def __call__(self, *args, **kwargs) -> Any:
        self.count += 1
        print(f"  {self.func.__name__} 第 {self.count} 次调用")
        return self.func(*args, **kwargs)


@CountCalls
def greet(name: str) -> str:
    return f"hi {name}"


def demo_class_decorator() -> None:
    """演示类装饰器。"""
    print("\n=== 类装饰器 ===")
    greet("A")
    greet("B")
    greet("C")
    print(f"总调用次数: {greet.count}")


# ============================================================================
# 4. functools.wraps 保留元信息
# ============================================================================

def without_wraps(func: Callable) -> Callable:
    """不使用 wraps，元信息丢失。"""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def with_wraps(func: Callable) -> Callable:
    """使用 wraps，保留原函数元信息。"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@without_wraps
def func_a() -> None:
    """func_a 文档"""
    pass


@with_wraps
def func_b() -> None:
    """func_b 文档"""
    pass


def demo_wraps() -> None:
    """演示 functools.wraps。"""
    print("\n=== functools.wraps ===")
    print(f"func_a.__name__ = {func_a.__name__}")  # wrapper
    print(f"func_a.__doc__ = {func_a.__doc__}")    # None
    print(f"func_b.__name__ = {func_b.__name__}")  # func_b
    print(f"func_b.__doc__ = {func_b.__doc__}")    # func_b 文档


# ============================================================================
# 5. functools.lru_cache 自动缓存（对比 Guava Cache）
# ============================================================================

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    """带缓存的斐波那契。

    Java 对比：类似 Guava CacheBuilder.newBuilder().maximumSize(128)
    或 Caffeine cache。Python 内置 functools.lru_cache 一行搞定。

    LRU = Least Recently Used，最近最少使用淘汰策略。
    """
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def demo_lru_cache() -> None:
    """演示 lru_cache。"""
    print("\n=== functools.lru_cache ===")
    start = time.perf_counter()
    result = fibonacci(35)
    elapsed = time.perf_counter() - start
    print(f"fibonacci(35) = {result}, 耗时 {elapsed:.6f}s")

    # 第二次调用，命中缓存
    start = time.perf_counter()
    result = fibonacci(35)
    elapsed = time.perf_counter() - start
    print(f"fibonacci(35) 再次调用 = {result}, 耗时 {elapsed:.6f}s（缓存命中）")

    # 查看缓存信息
    print(f"缓存信息: {fibonacci.cache_info()}")


# ============================================================================
# 6. functools.singledispatch 按类型分派（对比 Java 方法重载）
# ============================================================================

@singledispatch
def to_json(value: Any) -> str:
    """根据类型分派到不同实现。

    Java 对比：Java 有编译期方法重载，Python 运行期用 singledispatch 模拟。
    singledispatch 按第一个参数的类型选择实现。
    """
    raise TypeError(f"不支持类型 {type(value)}")


@to_json.register
def _(value: int) -> str:
    return str(value)


@to_json.register
def _(value: str) -> str:
    return f'"{value}"'


@to_json.register
def _(value: list) -> str:
    items = ", ".join(to_json(item) for item in value)
    return f"[{items}]"


@to_json.register
def _(value: dict) -> str:
    items = ", ".join(f'"{k}": {to_json(v)}' for k, v in value.items())
    return f"{{{items}}}"


def demo_singledispatch() -> None:
    """演示 singledispatch。"""
    print("\n=== functools.singledispatch ===")
    print(to_json(42))
    print(to_json("hello"))
    print(to_json([1, "two", 3]))
    print(to_json({"name": "Alice", "age": 30}))


# ============================================================================
# 7. functools.cached_property
# ============================================================================

class DataFetcher:
    """cached_property: 首次访问计算并缓存，后续直接返回。

    Java 对比：类似 Spring @Cacheable 或手写的 lazy init getter。
    cached_property 是 3.8+ 特性。
    """

    def __init__(self, source: str) -> None:
        self.source = source

    @cached_property
    def expensive_data(self) -> str:
        """模拟耗时计算。"""
        print("  执行耗时计算...")
        time.sleep(0.1)
        return f"data from {self.source}"


def demo_cached_property() -> None:
    """演示 cached_property。"""
    print("\n=== functools.cached_property ===")
    fetcher = DataFetcher("db")
    print(f"第一次访问: {fetcher.expensive_data}")
    print(f"第二次访问: {fetcher.expensive_data}")  # 直接返回缓存


# ============================================================================
# 8. 装饰器叠加顺序
# ============================================================================

def decorator_a(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("  A - before")
        result = func(*args, **kwargs)
        print("  A - after")
        return result
    return wrapper


def decorator_b(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("  B - before")
        result = func(*args, **kwargs)
        print("  B - after")
        return result
    return wrapper


@decorator_a
@decorator_b
def stacked() -> None:
    print("  函数执行")


def demo_stacked() -> None:
    """演示装饰器叠加顺序。

    装饰器从下往上应用，从上往下执行。
    @A @B def f 等价于 f = A(B(f))
    执行顺序：A before -> B before -> f -> B after -> A after
    """
    print("\n=== 装饰器叠加顺序 ===")
    stacked()


# ============================================================================
# 9. 实战：计时 / 重试 / 日志装饰器
# ============================================================================

def timer(func: Callable) -> Callable:
    """计时装饰器。"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [TIMER] {func.__name__} 耗时 {elapsed:.6f}s")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 0.1) -> Callable:
    """重试装饰器。

    Java 对比：类似 Spring Retry 的 @Retryable。
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    print(f"  [RETRY] 第 {attempt} 次失败: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


def setup_logger() -> logging.Logger:
    """配置日志。"""
    logger = logging.getLogger("demo")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = setup_logger()


def log_call(func: Callable) -> Callable:
    """日志装饰器。"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"调用 {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} 成功")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} 失败: {e}")
            raise
    return wrapper


@timer
@log_call
def slow_task() -> str:
    time.sleep(0.05)
    return "done"


_fail_count = 0


@retry(max_attempts=3)
def flaky_task() -> str:
    """模拟前两次失败，第三次成功。"""
    global _fail_count
    _fail_count += 1
    if _fail_count < 3:
        raise RuntimeError(f"第 {_fail_count} 次失败")
    return "success"


def demo_practical() -> None:
    """演示实战装饰器。"""
    print("\n=== 实战装饰器 ===")
    print(f"slow_task 结果: {slow_task()}")
    print(f"flaky_task 结果: {flaky_task()}")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    demo_basic_decorator()
    demo_param_decorator()
    demo_class_decorator()
    demo_wraps()
    demo_lru_cache()
    demo_singledispatch()
    demo_cached_property()
    demo_stacked()
    demo_practical()
    print("\n所有装饰器示例运行完毕。")
