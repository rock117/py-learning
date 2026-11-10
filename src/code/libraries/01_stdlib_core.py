# -*- coding: utf-8 -*-
"""
01_stdlib_core.py - Python 标准库核心模块讲解

本文件面向有丰富 Java 经验的开发者，讲解 Python 标准库中最常用的核心模块：
    - os 与 sys：操作系统接口与解释器相关
    - pathlib：面向对象的路径操作（推荐替代 os.path）
    - collections：高级容器类型
    - itertools：迭代器工具
    - functools：函数式工具

[注意] 本文件在 Windows 控制台（GBK 编码）下可正常运行，不使用 emoji。
       所有 demo 都可通过 `python 01_stdlib_core.py` 运行，exit code 0。

对比 Java：
    Java 开发者通常依赖 java.nio.file / java.util.stream / java.util.function 等包，
    Python 标准库提供了更紧凑、更"Pythonic"的等价实现，无需第三方依赖。
"""

import os
import sys
import collections
import itertools
import functools
from pathlib import Path
from collections import (
    namedtuple,
    Counter,
    defaultdict,
    OrderedDict,
    deque,
    ChainMap,
)
from itertools import (
    chain,
    groupby,
    combinations,
    permutations,
    islice,
    starmap,
    accumulate,
    cycle,
    repeat,
    count,
    product,
    tee,
)
from functools import (
    reduce,
    partial,
    cache,
    lru_cache,
    cached_property,
    singledispatch,
    total_ordering,
    wraps,
)


# =============================================================================
# 第一部分：os 与 sys 模块
# =============================================================================
# [Java 对比] os 模块类似 java.nio.file.Files / java.lang.System 的组合；
#             sys 模块类似 Java 的 System.getProperties() / Runtime。

def demo_os_path():
    """os.path 路径操作演示。

    [Java 对比] Java 中使用 java.nio.file.Path 和 Paths.get() 来操作路径。
    Python 的 os.path 是基于字符串的路径操作，跨平台但不如 pathlib 直观。
    """
    print("=== os.path 路径操作 ===")
    # os.path.join 拼接路径，自动处理分隔符（Windows 用 \，Linux 用 /）
    p = os.path.join("a", "b", "c.txt")
    print("os.path.join('a','b','c.txt') =", p)  # Windows: a\b\c.txt

    # 拆分目录与文件名
    print("dirname =", os.path.dirname(p))   # a\b
    print("basename =", os.path.basename(p))  # c.txt

    # 分割扩展名
    print("splitext =", os.path.splitext(p))  # ('a\\b\\c', '.txt')

    # 绝对路径与规范化
    print("abspath =", os.path.abspath("."))  # 当前目录的绝对路径
    print("normpath =", os.path.normpath("a//b/../c"))  # a\c

    # 判断路径是否存在 / 是否是文件 / 是否是目录
    print("exists('.') =", os.path.exists("."))
    print("isfile('.') =", os.path.isfile("."))
    print("isdir('.') =", os.path.isdir("."))


def demo_os_environ():
    """os.environ 环境变量。

    [Java 对比] Java 用 System.getenv("PATH") 读取环境变量。
    Python 的 os.environ 是一个类似字典的对象，可读可写。
    """
    print("\n=== os.environ 环境变量 ===")
    # 读取环境变量（不存在时返回 None，避免 KeyError）
    path_env = os.environ.get("PATH", "")
    print("PATH 前 80 字符:", path_env[:80])

    # os.getenv 是等价写法，可指定默认值
    home = os.getenv("HOME", os.getenv("USERPROFILE", "<未知>"))
    print("HOME/USERPROFILE =", home)

    # 设置环境变量（仅影响当前进程及其子进程）
    os.environ["MY_TEMP_VAR"] = "hello"
    print("MY_TEMP_VAR =", os.environ["MY_TEMP_VAR"])
    # [注意] 这不会影响父进程（shell），进程退出后消失。


def demo_os_walk():
    """os.getcwd / os.listdir / os.walk 目录遍历。

    [Java 对比] Java 中遍历目录用 Files.walk() / Files.list()。
    Python 的 os.walk 生成 (dirpath, dirnames, filenames) 三元组，递归遍历。
    """
    print("\n=== os 目录遍历 ===")
    print("当前工作目录 getcwd =", os.getcwd())

    # os.listdir 列出目录下所有条目（不递归）
    entries = os.listdir(".")
    print("listdir('.') 前 5 个:", entries[:5])

    # os.walk 递归遍历，自上而下
    # [技巧] 限制深度避免输出过多
    print("os.walk 限制深度 1 层:")
    for dirpath, dirnames, filenames in os.walk("."):
        depth = dirpath.count(os.sep) - ".".count(os.sep)
        if depth > 1:
            # 修改 dirnames 可阻止向下递归（原地清空即可）
            dirnames.clear()
            continue
        print("  目录:", dirpath, "| 文件数:", len(filenames))


def demo_sys_basics():
    """sys.argv / sys.path / sys.modules / sys.platform。

    [Java 对比] Java 用 args[] (main 方法参数) 获取命令行参数；
    Python 用 sys.argv，其中 argv[0] 是脚本名。
    """
    print("\n=== sys 模块基础 ===")
    # sys.argv: 命令行参数列表
    print("sys.argv =", sys.argv)

    # sys.platform: 平台标识
    # Windows -> 'win32', Linux -> 'linux', macOS -> 'darwin'
    print("sys.platform =", sys.platform)
    if sys.platform == "win32":
        print("[注意] 当前为 Windows 平台")

    # sys.path: 模块搜索路径（类似 Java 的 classpath）
    print("sys.path 前 3 项:", sys.path[:3])

    # sys.modules: 已加载模块的字典
    print("已加载模块数:", len(sys.modules))
    print("os 模块已加载:", "os" in sys.modules)


def demo_sys_stdio():
    """sys.stdin / sys.stdout / sys.stderr 标准流。

    [Java 对比] Java 用 System.in / System.out / System.err。
    Python 的 sys.stdout 默认按控制台编码输出，Windows 下通常是 GBK。
    """
    print("\n=== sys 标准流 ===")
    # sys.stdout 是文本流，可重定向
    print("stdout 编码:", sys.stdout.encoding)

    # stderr 用于错误输出，不会被 stdout 重定向带走
    print("stderr 编码:", sys.stderr.encoding)
    # sys.stderr.write("这条写到 stderr\n")  # 取消注释可测试

    # [技巧] 重新配置 stdout 为 utf-8，解决 Windows 下中文乱码
    # sys.stdout.reconfigure(encoding="utf-8")  # Python 3.7+ 支持


# =============================================================================
# 第二部分：pathlib（推荐替代 os.path）
# =============================================================================
# [Java 对比] pathlib.Path 类似 java.nio.file.Path，但方法更丰富、更直观。
#             官方推荐用 pathlib 替代 os.path 进行新代码开发。

def demo_pathlib_basic():
    """Path 对象创建与路径拼接 / 运算符。"""
    print("\n=== pathlib 基础 ===")
    # 创建 Path 对象
    p = Path("a") / "b" / "c.txt"  # / 运算符拼接路径，非常直观
    print("Path('a')/'b'/'c.txt' =", p)

    # Path.home() 用户主目录，Path.cwd() 当前目录
    print("Path.home() =", Path.home())
    print("Path.cwd() =", Path.cwd())

    # 路径属性
    print("p.name =", p.name)            # c.txt
    print("p.stem =", p.stem)            # c
    print("p.suffix =", p.suffix)        # .txt
    print("p.parent =", p.parent)        # a\b
    print("p.parts =", p.parts)          # ('a', 'b', 'c.txt')


def demo_pathlib_io():
    """读写文件 .read_text() / .write_text()。

    [Java 对比] Java 需要 Files.readString / Files.writeString（Java 11+）。
    Python 的 pathlib 内置便捷方法，一行搞定。
    """
    print("\n=== pathlib 文件读写 ===")
    tmp = Path("pathlib_demo_tmp.txt")
    try:
        # write_text 默认使用系统编码（Windows 为 GBK），可指定 encoding
        tmp.write_text("第一行\n第二行\n", encoding="utf-8")
        # read_text 读取
        content = tmp.read_text(encoding="utf-8")
        print("读取内容:", repr(content))

        # read_bytes / write_bytes 处理二进制
        tmp.write_bytes(b"\x00\x01\x02")
        print("字节数:", len(tmp.read_bytes()))
    finally:
        if tmp.exists():
            tmp.unlink()  # 删除文件
    print("临时文件已清理")


def demo_pathlib_glob():
    """遍历 .glob() / .rglob()。"""
    print("\n=== pathlib glob 遍历 ===")
    # glob 只匹配当前层，rglob 递归匹配
    # 这里用当前目录演示，限制输出数量
    py_files = list(Path(".").glob("*.py"))
    print("当前目录 .py 文件:", [str(f) for f in py_files[:5]])

    # rglob 递归所有子目录
    all_py = list(Path(".").rglob("*.py"))
    print("递归 .py 文件总数:", len(all_py))


def demo_pathlib_stat():
    """文件信息 .stat() / .exists() / .is_dir()。"""
    print("\n=== pathlib 文件信息 ===")
    p = Path(".")
    print("exists =", p.exists())
    print("is_dir =", p.is_dir())
    print("is_file =", p.is_file())

    # stat() 返回 os.stat_result，包含大小、时间等
    st = p.stat()
    print("stat.st_size =", st.st_size)
    print("stat.st_mtime =", st.st_mtime)  # 修改时间戳


def demo_pathlib_mkdir():
    """创建/删除 .mkdir() / .unlink() / .rmdir()。"""
    print("\n=== pathlib 创建删除 ===")
    d = Path("pathlib_demo_dir")
    try:
        # mkdir parents=True 类似 mkdir -p，exist_ok=True 避免已存在报错
        d.mkdir(parents=True, exist_ok=True)
        print("目录已创建:", d.exists())

        # 在目录中创建文件
        f = d / "test.txt"
        f.write_text("hello", encoding="utf-8")
        print("文件已创建:", f.exists())

        # unlink 删除文件
        f.unlink()
        print("文件已删除:", not f.exists())
    finally:
        # rmdir 只能删除空目录
        if d.exists():
            d.rmdir()
    print("目录已清理:", not d.exists())


# =============================================================================
# 第三部分：collections 模块
# =============================================================================
# [Java 对比] collections 类似 Apache Commons Collections 或 Java 的增强容器。

def demo_namedtuple():
    """namedtuple 命名元组。

    [Java 对比] 类似 Java 14+ 的 record，是不可变的数据载体。
    namedtuple 比 dataclass 更轻量，基于元组，内存占用小。
    """
    print("\n=== collections.namedtuple ===")
    # 定义一个命名元组类型
    Point = namedtuple("Point", ["x", "y"])
    p = Point(1, 2)
    print("p =", p)
    print("p.x =", p.x, "p.y =", p.y)  # 按名访问
    print("p[0] =", p[0])              # 按索引访问

    # _asdict 转字典，_replace 生成新实例（不可变）
    print("asdict =", p._asdict())
    p2 = p._replace(x=10)
    print("replace 后:", p2, "原对象不变:", p)

    # [技巧] 用 typing.NamedTuple 可加类型注解（更现代的写法）
    # class Point(typing.NamedTuple):
    #     x: int
    #     y: int


def demo_counter():
    """Counter 计数器。

    [Java 对比] Java 中常用 Map<K,Integer> 手动计数，或 Stream.collect(Collectors.groupingBy)。
    Python 的 Counter 提供现成的计数功能。
    """
    print("\n=== collections.Counter ===")
    words = "the quick brown fox jumps over the lazy dog the fox".split()
    c = Counter(words)
    print("计数:", c)
    print("most_common(2) =", c.most_common(2))  # 出现最多的 2 个

    # Counter 支持算术运算
    c2 = Counter({"the": 1, "fox": 2})
    print("相加:", c + c2)
    print("相减:", c - c2)


def demo_defaultdict():
    """defaultdict 默认字典。

    [Java 对比] Java 中常用 computeIfAbsent 实现类似功能。
    Python 的 defaultdict 在缺失键时自动调用工厂函数生成默认值。
    """
    print("\n=== collections.defaultdict ===")
    # 按 key 分组
    dd = defaultdict(list)
    for word in ["apple", "banana", "avocado", "blueberry"]:
        dd[word[0]].append(word)
    print("按首字母分组:", dict(dd))

    # 计数场景
    counts = defaultdict(int)  # int() 默认返回 0
    for ch in "aabbbcccc":
        counts[ch] += 1
    print("字符计数:", dict(counts))


def demo_ordereddict():
    """OrderedDict 有序字典。

    [注意] Python 3.7+ 普通 dict 已保证插入顺序，OrderedDict 仍有独特功能：
           move_to_end / popitem(last=False) 等。
    """
    print("\n=== collections.OrderedDict ===")
    od = OrderedDict()
    od["a"] = 1
    od["b"] = 2
    od["c"] = 3
    print("OrderedDict:", od)

    # move_to_end 调整顺序
    od.move_to_end("a")
    print("move_to_end('a') 后:", od)

    # popitem 弹出
    print("popitem(last=False) =", od.popitem(last=False))  # 弹出最旧的
    print("剩余:", od)


def demo_deque():
    """deque 双端队列。

    [Java 对比] 类似 Java 的 ArrayDeque，两端 O(1) 增删。
    比 list 在头部插入高效（list 头部插入是 O(n)）。
    """
    print("\n=== collections.deque ===")
    dq = deque([1, 2, 3], maxlen=5)  # maxlen 限制长度，超出自动丢弃
    dq.append(4)        # 右侧添加
    dq.appendleft(0)    # 左侧添加
    print("deque:", dq)

    print("pop() =", dq.pop())          # 右侧弹出
    print("popleft() =", dq.popleft())  # 左侧弹出
    print("deque:", dq)

    # rotate 旋转
    dq.rotate(1)  # 右旋
    print("rotate(1) 后:", dq)


def demo_chainmap():
    """ChainMap 链接多个映射。

    [Java 对比] Java 没有直接等价物，需手动合并 Map。
    ChainMap 不复制，按顺序查找，修改只影响第一个映射。
    """
    print("\n=== collections.ChainMap ===")
    defaults = {"theme": "light", "lang": "en"}
    user_prefs = {"theme": "dark"}
    # 用户设置优先，回退到默认值
    cm = ChainMap(user_prefs, defaults)
    print("theme =", cm["theme"])  # dark（来自 user_prefs）
    print("lang =", cm["lang"])    # en（来自 defaults）

    # 修改只影响第一个映射
    cm["theme"] = "blue"
    print("user_prefs =", user_prefs)  # {'theme': 'blue'}


# =============================================================================
# 第四部分：itertools 模块（进阶用法）
# =============================================================================
# [Java 对比] 类似 Java Stream API，但 itertools 操作的是迭代器，
#             惰性求值，内存友好。Java Stream 是一次性消费，Python 迭代器也是。

def demo_itertools_chain():
    """chain 连接多个迭代器。"""
    print("\n=== itertools.chain ===")
    # 把多个可迭代对象串联
    result = list(chain([1, 2], [3, 4], [5]))
    print("chain([1,2],[3,4],[5]) =", result)

    # chain.from_iterable 接收一个嵌套可迭代对象
    nested = [[1, 2], [3, 4]]
    print("from_iterable =", list(chain.from_iterable(nested)))


def demo_itertools_groupby():
    """groupby 分组。

    [注意] groupby 只对"连续"相同元素分组，需先排序。
    """
    print("\n=== itertools.groupby ===")
    data = [("a", 1), ("a", 2), ("b", 3), ("a", 4)]
    # 先按 key 排序，否则相同 key 会被分到不同组
    data_sorted = sorted(data, key=lambda x: x[0])
    for key, group in groupby(data_sorted, key=lambda x: x[0]):
        print(f"  key={key}: {list(group)}")


def demo_itertools_combinations():
    """combinations / permutations 排列组合。"""
    print("\n=== itertools 排列组合 ===")
    items = ["A", "B", "C"]
    # combinations 组合（无序，不重复）
    print("combinations(2):", list(combinations(items, 2)))
    # permutations 排列（有序）
    print("permutations(2):", list(permutations(items, 2)))
    # product 笛卡尔积
    print("product([1,2],[3,4]):", list(product([1, 2], [3, 4])))


def demo_itertools_islice():
    """islice 切片迭代器，不消耗内存加载全部。"""
    print("\n=== itertools.islice ===")
    # 对无限迭代器取前 N 个
    result = list(islice(count(10, 2), 5))  # 从 10 开始步长 2，取 5 个
    print("islice(count(10,2), 5) =", result)

    # 也可指定 start, stop, step
    print("islice(range(10), 2, 8, 2) =", list(islice(range(10), 2, 8, 2)))


def demo_itertools_starmap():
    """starmap / accumulate。"""
    print("\n=== itertools.starmap / accumulate ===")
    # starmap: 把每个元素作为参数解包传给函数
    pairs = [(2, 3), (4, 5)]
    print("starmap(pow):", list(starmap(pow, pairs)))  # [8, 1024]

    # accumulate: 累积运算（默认求和）
    print("accumulate([1,2,3,4]):", list(accumulate([1, 3, 5, 7])))
    # 自定义函数：累积最大值
    print("accumulate(max):", list(accumulate([3, 1, 4, 1, 5], max)))


def demo_itertools_infinite():
    """cycle / repeat / count 无限迭代器。"""
    print("\n=== itertools 无限迭代器 ===")
    # cycle 无限循环
    print("cycle(ABC) 取 7 个:", list(islice(cycle("ABC"), 7)))

    # repeat 重复元素
    print("repeat(5, 3):", list(repeat(5, 3)))  # [5, 5, 5]

    # count 无限计数
    print("count(10) 取 3 个:", list(islice(count(10), 3)))


def demo_itertools_tee():
    """tee 复制迭代器。

    [注意] tee 后的原迭代器不应再使用，否则复制结果会异常。
    """
    print("\n=== itertools.tee ===")
    it = iter(range(5))
    it1, it2 = tee(it, 2)
    print("tee 副本 1:", list(it1))
    print("tee 副本 2:", list(it2))


# =============================================================================
# 第五部分：functools 模块（进阶用法）
# =============================================================================
# [Java 对比] functools 类似 Java 的 Function/Supplier/Function 接口与 Stream.reduce。

def demo_functools_reduce():
    """reduce 归约。

    [Java 对比] 类似 Java Stream.reduce(accumulator)。
    Python3 中 reduce 已移到 functools，不再内置。
    """
    print("\n=== functools.reduce ===")
    nums = [1, 2, 3, 4]
    # 累加
    print("reduce(+):", reduce(lambda x, y: x + y, nums))  # 10
    # 带初始值
    print("reduce(+, init=100):", reduce(lambda x, y: x + y, nums, 100))  # 110
    # 求最大值
    print("reduce(max):", reduce(lambda a, b: a if a > b else b, nums))


def demo_functools_partial():
    """partial 偏函数：固定部分参数。

    [Java 对比] Java 中常用 lambda 或方法引用实现类似效果。
    """
    print("\n=== functools.partial ===")
    # 固定 base 参数
    def power(base, exponent):
        return base ** exponent

    square = partial(power, exponent=2)
    cube = partial(power, exponent=3)
    print("square(5) =", square(5))  # 25
    print("cube(3) =", cube(3))      # 27

    # 实用：简化 int(x, base) 调用
    b2int = partial(int, base=2)
    print("int('1010', base=2) =", b2int("1010"))  # 10


def demo_functools_cache():
    """cache / lru_cache 缓存。

    [Java 对比] Java 中常用 Guava Cache 或 Caffeine。
    Python 的 cache（3.9+）是无界缓存，lru_cache 有上限。
    """
    print("\n=== functools.cache / lru_cache ===")

    @cache  # 3.9+ 无界缓存，等价于 lru_cache(maxsize=None)
    def fib(n):
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    print("fib(30) =", fib(30))

    @lru_cache(maxsize=128)  # 有界 LRU 缓存
    def slow_func(x):
        return x * x

    print("slow_func(5) =", slow_func(5))
    print("cache_info:", slow_func.cache_info())


def demo_functools_cached_property():
    """cached_property 缓存属性：首次访问后缓存。

    [Java 对比] Java 中常手写 lazy getter + volatile 字段。
    """
    print("\n=== functools.cached_property ===")

    class DataProvider:
        def __init__(self):
            self._calls = 0

        @cached_property
        def expensive(self):
            self._calls += 1
            print("  [计算中...]")
            return [1, 2, 3]

    dp = DataProvider()
    print("第一次访问:", dp.expensive)
    print("第二次访问:", dp.expensive)  # 不再计算
    print("调用次数:", dp._calls)


def demo_functools_singledispatch():
    """singledispatch 单分派：根据第一个参数类型分发。

    [Java 对比] Java 通过方法重载实现，Python 动态类型需 singledispatch。
    """
    print("\n=== functools.singledispatch ===")

    @singledispatch
    def process(obj):
        return f"未知类型: {type(obj)}"

    @process.register(str)
    def _(obj):
        return f"字符串: {obj!r}"

    @process.register(int)
    def _(obj):
        return f"整数: {obj}"

    @process.register(list)
    def _(obj):
        return f"列表长度: {len(obj)}"

    print(process("hello"))
    print(process(42))
    print(process([1, 2, 3]))
    print(process(3.14))


def demo_functools_total_ordering():
    """total_ordering 自动补全比较方法。

    [Java 对比] Java 实现 Comparable 接口只需 compareTo；
    Python 需实现多个 __eq__ __lt__ 等，total_ordering 帮忙补全。
    """
    print("\n=== functools.total_ordering ===")

    @total_ordering
    class Student:
        def __init__(self, name, score):
            self.name = name
            self.score = score

        def __eq__(self, other):
            return self.score == other.score

        def __lt__(self, other):  # 只需定义 < 和 ==，其余自动生成
            return self.score < other.score

    s1 = Student("Alice", 90)
    s2 = Student("Bob", 85)
    print("s1 > s2:", s1 > s2)   # 自动生成
    print("s1 >= s2:", s1 >= s2)
    print("s1 <= s2:", s1 <= s2)


def demo_functools_wraps():
    """wraps 保留被装饰函数的元信息。

    [Java 对比] Java 注解处理器一般不涉及此问题。
    Python 装饰器会改变函数 __name__，wraps 用于修复。
    """
    print("\n=== functools.wraps ===")

    def my_decorator(func):
        @wraps(func)  # 保留原函数名、文档等
        def wrapper(*args, **kwargs):
            print(f"  [调用 {func.__name__}]")
            return func(*args, **kwargs)
        return wrapper

    @my_decorator
    def greet(name):
        """打招呼"""
        return f"Hello, {name}"

    print("函数名:", greet.__name__)  # greet（若不用 wraps 则是 wrapper）
    print("文档:", greet.__doc__)
    print(greet("World"))


# =============================================================================
# 主入口
# =============================================================================
def main():
    """运行所有 demo。"""
    print("=" * 70)
    print("Python 标准库核心模块演示 - 面向 Java 开发者")
    print("=" * 70)

    # os 与 sys
    demo_os_path()
    demo_os_environ()
    demo_os_walk()
    demo_sys_basics()
    demo_sys_stdio()

    # pathlib
    demo_pathlib_basic()
    demo_pathlib_io()
    demo_pathlib_glob()
    demo_pathlib_stat()
    demo_pathlib_mkdir()

    # collections
    demo_namedtuple()
    demo_counter()
    demo_defaultdict()
    demo_ordereddict()
    demo_deque()
    demo_chainmap()

    # itertools
    demo_itertools_chain()
    demo_itertools_groupby()
    demo_itertools_combinations()
    demo_itertools_islice()
    demo_itertools_starmap()
    demo_itertools_infinite()
    demo_itertools_tee()

    # functools
    demo_functools_reduce()
    demo_functools_partial()
    demo_functools_cache()
    demo_functools_cached_property()
    demo_functools_singledispatch()
    demo_functools_total_ordering()
    demo_functools_wraps()

    print("\n" + "=" * 70)
    print("所有 demo 运行完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
