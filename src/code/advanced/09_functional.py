"""
09 - 函数式编程工具
===================
本节目标：
  1. itertools：chain/groupby/combinations/islice/accumulate（对比 Java Stream API）
  2. functools：reduce/partial/cache（对比 Java Function.identity 等）
  3. operator：itemgetter/attrgetter/methodcaller
  4. dataclass(frozen=True) 不可变值对象（对比 Java record）
  5. NamedTuple 带类型元组
  6. 高阶函数：map/filter/reduce
  7. 实战：用生成器管道处理数据流

对应 Java 概念：
  - itertools ≈ java.util.stream.Stream 的中间操作
  - functools.reduce ≈ Stream.reduce(BinaryOperator)
  - functools.partial ≈ lambda 固定部分参数（Java 没有直接对应）
  - operator.itemgetter ≈ Function<Map,K> get = m -> m.get(key)
  - dataclass(frozen=True) ≈ Java 14+ record
  - NamedTuple ≈ 带 getter 的不可变 record
"""

import itertools
import functools
import operator
from collections import namedtuple
from dataclasses import dataclass, field
from typing import NamedTuple


# ---------------------------------------------------------------------------
# 1. itertools.chain：拼接多个可迭代对象
# ---------------------------------------------------------------------------
def demo_chain():
    print("\n=== 1. itertools.chain 拼接迭代器 ===")
    # Java: Stream.concat(s1, s2).concat(s3)
    a = [1, 2, 3]
    b = [4, 5]
    c = [6, 7, 8, 9]
    chained = list(itertools.chain(a, b, c))
    print(f"  chain([1,2,3], [4,5], [6,7,8,9]) = {chained}")

    # chain.from_iterable：当可迭代对象本身在一个容器里
    nested = [[1, 2], [3, 4], [5, 6]]
    flat = list(itertools.chain.from_iterable(nested))
    print(f"  chain.from_iterable([[1,2],[3,4],[5,6]]) = {flat}")
    # Java: nested.stream().flatMap(List::stream)


# ---------------------------------------------------------------------------
# 2. itertools.groupby：分组（注意：需要先排序！）
# ---------------------------------------------------------------------------
def demo_groupby():
    print("\n=== 2. itertools.groupby 分组 ===")
    # Java: Collectors.groupingBy(...)
    # 注意：groupby 只对"连续"的相同 key 分组，所以通常要先排序

    words = ["apple", "ant", "banana", "bear", "cat", "apple", "ant"]
    # 按首字母分组：先排序保证连续
    sorted_words = sorted(words, key=lambda w: w[0])
    grouped = {}
    for key, group in itertools.groupby(sorted_words, key=lambda w: w[0]):
        grouped[key] = list(group)
    print(f"  按首字母分组: {grouped}")

    # 按奇偶分组
    nums = [1, 1, 2, 2, 2, 3, 3, 4]
    for key, group in itertools.groupby(nums, key=lambda x: x % 2):
        print(f"    余数 {key}: {list(group)}")


# ---------------------------------------------------------------------------
# 3. itertools.combinations / permutations / product
# ---------------------------------------------------------------------------
def demo_combinations():
    print("\n=== 3. combinations / permutations / product ===")
    items = ["A", "B", "C"]

    # 组合（无序，不重复）
    comb = list(itertools.combinations(items, 2))
    print(f"  combinations(2): {comb}")  # 3 选 2 = 3 种

    # 排列（有序）
    perm = list(itertools.permutations(items, 2))
    print(f"  permutations(2): {perm}")  # 3 排 2 = 6 种

    # 笛卡尔积（类似嵌套 for）
    prod = list(itertools.product([0, 1], repeat=3))
    print(f"  product([0,1], repeat=3): {prod}")  # 2^3 = 8 种


# ---------------------------------------------------------------------------
# 4. itertools.islice：切片迭代器（惰性）
# ---------------------------------------------------------------------------
def demo_islice():
    print("\n=== 4. itertools.islice 惰性切片 ===")
    # Java: stream.skip(2).limit(3)
    # islice 支持无限迭代器，因为它不预先消费全部

    # 无限自然数
    naturals = itertools.count(1)
    # 取第 5~7 个（索引 4,5,6）
    some = list(itertools.islice(naturals, 4, 7))
    print(f"  count(1) 的第 5~7 个: {some}")

    # 对比 list 切片：list 必须有限，islice 可用于生成器
    gen = (x * x for x in range(100))
    first3 = list(itertools.islice(gen, 3))
    print(f"  生成器前 3 个平方: {first3}")


# ---------------------------------------------------------------------------
# 5. itertools.accumulate：前缀累积
# ---------------------------------------------------------------------------
def demo_accumulate():
    print("\n=== 5. itertools.accumulate 前缀累积 ===")
    # Java: 需要自己写 reduce 累积，或用 Stream.iterate
    nums = [1, 2, 3, 4, 5]

    # 默认是累加
    sums = list(itertools.accumulate(nums))
    print(f"  累加: {sums}")  # [1, 3, 6, 10, 15]

    # 用乘法累积
    prods = list(itertools.accumulate(nums, operator.mul))
    print(f"  累乘: {prods}")  # [1, 2, 6, 24, 120]

    # 用 max 累积（运行最大值）
    run_max = list(itertools.accumulate([3, 1, 4, 1, 5, 9, 2], max))
    print(f"  运行最大值: {run_max}")


# ---------------------------------------------------------------------------
# 6. functools.reduce：归约
# ---------------------------------------------------------------------------
def demo_reduce():
    print("\n=== 6. functools.reduce 归约 ===")
    # Java: stream.reduce(0, Integer::sum) 或 .reduce(BinaryOperator)
    nums = [1, 2, 3, 4, 5]

    total = functools.reduce(operator.add, nums, 0)
    print(f"  reduce(add, 1..5) = {total}")

    # 求阶乘
    fact5 = functools.reduce(operator.mul, range(1, 6), 1)
    print(f"  reduce(mul, 1..5) = {fact5}")

    # 带初始值的字符串拼接
    joined = functools.reduce(lambda a, b: f"{a}-{b}", ["a", "b", "c"], "")
    print(f"  reduce 拼接: {joined!r}")


# ---------------------------------------------------------------------------
# 7. functools.partial：偏函数（固定部分参数）
# ---------------------------------------------------------------------------
def demo_partial():
    print("\n=== 7. functools.partial 偏函数 ===")
    # Java 没有直接对应，常见做法是 lambda:
    #   Function<Integer, Integer> add10 = x -> add(x, 10);

    def power(base, exp):
        return base ** exp

    # 固定 exp=2，得到"平方"函数
    square = functools.partial(power, exp=2)
    # 固定 exp=3，得到"立方"函数
    cube = functools.partial(power, exp=3)
    print(f"  square(5) = {square(5)}")
    print(f"  cube(3) = {cube(3)}")

    # 实用场景：固定日志级别
    import logging
    info = functools.partial(logging.log, logging.INFO)
    # info("message") 等价于 logging.log(logging.INFO, "message")


# ---------------------------------------------------------------------------
# 8. functools.cache / lru_cache：自动记忆化
# ---------------------------------------------------------------------------
def demo_cache():
    print("\n=== 8. functools.cache 记忆化 ===")
    # Java 没有内置，需用 Guava Cache 或手写 Map

    call_count = 0

    @functools.lru_cache(maxsize=128)  # lru_cache 支持 maxsize
    def fib(n):
        nonlocal call_count
        call_count += 1
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    print(f"  fib(10) = {fib(10)}, 调用次数(含缓存命中前) = {call_count}")
    call_count = 0
    print(f"  fib(10) 再次 = {fib(10)}, 调用次数 = {call_count} (全命中缓存)")
    print(f"  缓存信息: {fib.cache_info()}")

    # Python 3.9+ 的 @cache = @lru_cache(maxsize=None) 无限缓存
    @functools.cache
    def slow_double(x):
        return x * 2
    print(f"  cache 装饰器: slow_double(5) = {slow_double(5)}")


# ---------------------------------------------------------------------------
# 9. operator 模块
# ---------------------------------------------------------------------------
def demo_operator():
    print("\n=== 9. operator 模块 ===")
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    # itemgetter：等价于 lambda d: d["name"]
    get_name = operator.itemgetter("name")
    print(f"  itemgetter: {get_name(data[0])}")
    # 排序时很方便
    sorted_by_name = sorted(data, key=operator.itemgetter("name"))
    print(f"  按 name 排序: {sorted_by_name}")

    # attrgetter：等价于 lambda obj: obj.attr
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def __repr__(self):
            return f"Point({self.x},{self.y})"

    points = [Point(3, 1), Point(1, 2), Point(2, 3)]
    get_x = operator.attrgetter("x")
    sorted_pts = sorted(points, key=get_x)
    print(f"  attrgetter 按 x 排序: {sorted_pts}")
    # 同时取多个属性
    get_xy = operator.attrgetter("x", "y")
    print(f"  attrgetter('x','y'): {get_xy(points[0])}")

    # methodcaller：等价于 lambda s: s.upper()
    upper = operator.methodcaller("upper")
    print(f"  methodcaller upper: {upper('hello')}")
    # 带参数
    replace_o = operator.methodcaller("replace", "o", "0")
    print(f"  methodcaller replace: {replace_o('hello world')}")


# ---------------------------------------------------------------------------
# 10. dataclass(frozen=True) 不可变值对象
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Point3D:
    """不可变的三维点。
    Java 等价（Java 14+ record）：
        public record Point3D(double x, double y, double z) {}
    frozen=True 让实例不可变，且可哈希（能放进 set / 当 dict key）。
    """
    x: float
    y: float
    z: float = 0.0  # 默认值

    def distance_to(self, other: "Point3D") -> float:
        return ((self.x - other.x) ** 2 +
                (self.y - other.y) ** 2 +
                (self.z - other.z) ** 2) ** 0.5


@dataclass
class MutablePoint:
    """可变版本（默认），对比展示。"""
    x: float
    y: float


def demo_frozen_dataclass():
    print("\n=== 10. dataclass(frozen=True) 不可变值对象 ===")
    p1 = Point3D(1, 2, 3)
    p2 = Point3D(1, 2, 3)
    print(f"  p1 = {p1}")
    print(f"  p1 == p2: {p1 == p2}")  # frozen dataclass 自动生成 __eq__
    print(f"  hash(p1) = {hash(p1)}")  # frozen=True 才能哈希
    print(f"  distance = {p1.distance_to(Point3D(4, 6, 3)):.2f}")

    # 不可变：修改会报错
    try:
        p1.x = 10  # FrozenInstanceError
    except Exception as e:
        print(f"  修改 frozen 实例报错: {type(e).__name__}")

    # 可哈希 → 可放入 set
    point_set = {p1, p2, Point3D(0, 0)}
    print(f"  放入 set: {point_set} (去重了)")

    # 可变版本对比
    mp = MutablePoint(1, 2)
    mp.x = 10  # 正常修改
    print(f"  可变 dataclass: {mp}")
    try:
        hash(mp)  # 默认不可哈希
    except TypeError as e:
        print(f"  可变 dataclass 不可哈希: {e}")


# ---------------------------------------------------------------------------
# 11. NamedTuple：带类型注解的元组
# ---------------------------------------------------------------------------
class Employee(NamedTuple):
    """类型安全的命名元组。
    Java 等价：record Employee(String name, int age, String dept)
    NamedTuple 是 tuple 子类，所以兼容所有 tuple 操作，且内存比 dataclass 小。
    """
    name: str
    age: int
    dept: str = "engineering"


# 旧式写法（仍可用）
Person = namedtuple("Person", ["name", "age"])


def demo_namedtuple():
    print("\n=== 11. NamedTuple 带类型元组 ===")
    emp = Employee("Alice", 30, "sales")
    print(f"  emp = {emp}")
    print(f"  emp.name = {emp.name}, emp[0] = {emp[0]}")  # 两种访问方式
    print(f"  emp._fields = {emp._fields}")
    print(f"  emp._asdict() = {emp._asdict()}")

    # 解包（和普通 tuple 一样）
    name, age, dept = emp
    print(f"  解包: name={name}, age={age}, dept={dept}")

    # 不可变
    try:
        emp.age = 31
    except AttributeError as e:
        print(f"  不可变: {e}")

    # 替换字段（返回新实例）
    emp2 = emp._replace(age=31)
    print(f"  _replace: {emp2} (原 emp 不变: {emp})")

    # 旧式 namedtuple
    p = Person("Bob", 25)
    print(f"  旧式 namedtuple: {p}, p.name={p.name}")


# ---------------------------------------------------------------------------
# 12. 高阶函数 map / filter / reduce
# ---------------------------------------------------------------------------
def demo_higher_order():
    print("\n=== 12. map / filter 高阶函数 ===")
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # map：映射。Java: stream.map(x -> x * 2)
    doubled = list(map(lambda x: x * 2, nums))
    print(f"  map x2: {doubled}")

    # filter：过滤。Java: stream.filter(x -> x % 2 == 0)
    evens = list(filter(lambda x: x % 2 == 0, nums))
    print(f"  filter 偶数: {evens}")

    # map + filter 链式
    result = list(filter(lambda x: x > 10, map(lambda x: x * x, nums)))
    print(f"  平方后 >10: {result}")

    # Python 更推荐用生成器表达式（更 Pythonic）
    result2 = [x for x in (n * n for n in nums) if x > 10]
    print(f"  生成器表达式等价: {result2}")


# ---------------------------------------------------------------------------
# 13. 实战：生成器管道处理数据流
# ---------------------------------------------------------------------------
def demo_pipeline():
    print("\n=== 13. 实战：生成器管道处理数据流 ===")
    # 模拟日志流，用生成器管道逐步处理（惰性，省内存）
    # Java 等价：Stream.of(logs).filter(...).map(...).collect(...)

    logs = [
        "2024-01-01 INFO  start server",
        "2024-01-01 ERROR db connection failed",
        "2024-01-01 WARN  retry 1",
        "2024-01-01 ERROR timeout",
        "2024-01-02 INFO  server recovered",
        "2024-01-02 ERROR disk full",
    ]

    def read_lines(lines):
        """阶段1：产出每一行（模拟流式读取）。"""
        for line in lines:
            yield line

    def parse_errors(lines):
        """阶段2：只保留 ERROR 行。"""
        for line in lines:
            if "ERROR" in line:
                yield line

    def extract_messages(lines):
        """阶段3：提取日期和消息。"""
        for line in lines:
            date = line[:10]
            msg = line.split("ERROR")[1].strip()
            yield (date, msg)

    def annotate(lines):
        """阶段4：加上序号。"""
        for i, (date, msg) in enumerate(lines, 1):
            yield f"#{i} [{date}] {msg}"

    # 组装管道：每个阶段都是生成器，数据逐条流过，内存占用 O(1)
    pipeline = annotate(extract_messages(parse_errors(read_lines(logs))))
    for item in pipeline:
        print(f"  {item}")

    print("  (管道是惰性的，可以处理超大文件而不占内存)")


# ---------------------------------------------------------------------------
# 14. itertools 更多实用工具
# ---------------------------------------------------------------------------
def demo_more_itertools():
    print("\n=== 14. 更多 itertools 工具 ===")
    # takewhile / dropwhile：Java Stream.takeWhile / dropWhile
    nums = [1, 2, 3, 4, 1, 2]
    take = list(itertools.takewhile(lambda x: x < 4, nums))
    drop = list(itertools.dropwhile(lambda x: x < 4, nums))
    print(f"  takewhile(<4): {take}")  # [1,2,3] 遇到 4 停
    print(f"  dropwhile(<4): {drop}")  # [4,1,2] 跳过开头 <4 的

    # starmap：把每组的元素解包后传给函数
    pairs = [(1, 2), (3, 4), (5, 6)]
    sums = list(itertools.starmap(lambda a, b: a + b, pairs))
    print(f"  starmap(+): {sums}")

    # zip_longest：不等长 zip，短的填默认值
    zipped = list(itertools.zip_longest([1, 2, 3], ["a", "b"], fillvalue="?"))
    print(f"  zip_longest: {zipped}")

    # cycle：无限循环
    cycler = itertools.cycle(["A", "B", "C"])
    picked = [next(cycler) for _ in range(7)]
    print(f"  cycle 取7个: {picked}")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("09 - 函数式编程工具")
    print("=" * 60)

    demo_chain()
    demo_groupby()
    demo_combinations()
    demo_islice()
    demo_accumulate()
    demo_reduce()
    demo_partial()
    demo_cache()
    demo_operator()
    demo_frozen_dataclass()
    demo_namedtuple()
    demo_higher_order()
    demo_pipeline()
    demo_more_itertools()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - itertools 提供惰性迭代器工具，对应 Java Stream 中间操作")
    print("  - functools.reduce 归约，partial 偏函数，cache 记忆化")
    print("  - operator 模块避免写 lambda，代码更清晰")
    print("  - dataclass(frozen=True) ≈ Java record，不可变值对象")
    print("  - NamedTuple 兼具 tuple 轻量与类型注解")
    print("  - 生成器管道：惰性、省内存的数据流处理方式")
    print("=" * 60)


if __name__ == "__main__":
    main()
