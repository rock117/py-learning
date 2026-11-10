"""
12 - C 扩展与互操作
====================
本节目标：
  1. ctypes 调用 C 共享库（Windows 用 msvcrt.dll，Linux 用 libc）
  2. cffi 简介
  3. Cython 简介
  4. PyO3 (Rust 扩展) 简介
  5. mypyc 简介
  6. 注意：本文件主要用 ctypes 演示，其他在注释中说明

对应 Java 概念：
  - ctypes ≈ JNI（Java Native Interface），但更简单，无需头文件生成
  - cffi ≈ JNA（Java Native Access），运行时绑定
  - Cython ≈ 无直接对应（把 Python 编译成 C）
  - PyO3 ≈ 无直接对应（Rust 写 Python 扩展）

注意：Windows 环境用 ctypes.cdll.msvcrt 调用 C 标准库函数。
"""

import sys
import ctypes
import ctypes.util
import platform


# ---------------------------------------------------------------------------
# 1. 加载 C 共享库
# ---------------------------------------------------------------------------
def load_c_library():
    """根据平台加载 C 标准库。
    Windows: msvcrt.dll (Microsoft C Runtime)
    Linux:   libc.so.6
    macOS:   libSystem.dylib
    """
    print("\n=== 1. 加载 C 共享库 ===")
    system = platform.system()
    print(f"  当前系统: {system}")

    if system == "Windows":
        # Windows 上 msvcrt 是内置的 C 运行时
        # ctypes.cdll.msvcrt 是内置快捷方式
        libc = ctypes.cdll.msvcrt
        print(f"  已加载: msvcrt.dll (ctypes.cdll.msvcrt)")
        return libc, "msvcrt"
    else:
        # Linux/macOS：用 ctypes.util.find_library 查找
        libc_name = ctypes.util.find_library("c")
        if system == "Darwin":
            libc_name = libc_name or "libSystem.dylib"
        libc = ctypes.CDLL(libc_name or "libc.so.6")
        print(f"  已加载: {libc_name}")
        return libc, libc_name


# ---------------------------------------------------------------------------
# 2. 调用 C 标准库函数：printf
# ---------------------------------------------------------------------------
def demo_printf(libc):
    print("\n=== 2. 调用 C 的 printf ===")
    # Java JNI 需要：写 native 方法 → javac → javah 生成头文件 → C 实现编译
    # Python ctypes：直接声明函数签名，调用即可

    # 设置 printf 的参数类型和返回类型（可选但推荐）
    # printf(const char *format, ...) -> int
    libc.printf.argtypes = [ctypes.c_char_p]
    libc.printf.restype = ctypes.c_int

    # 调用 printf，注意传 bytes（C 字符串），不是 str
    # b"..." 是 Python 的 bytes 字面量，对应 C 的 char*
    count = libc.printf(b"  [C printf] Hello from C standard library!\n")
    print(f"  printf 返回打印的字符数: {count}")
    # Java 等价：System.out.print，但这是真正调用 C 函数


# ---------------------------------------------------------------------------
# 3. 调用 C 的数学函数：abs / strlen
# ---------------------------------------------------------------------------
def demo_simple_functions(libc):
    print("\n=== 3. 调用 C 标准库简单函数 ===")

    # abs(int) -> int
    libc.abs.argtypes = [ctypes.c_int]
    libc.abs.restype = ctypes.c_int
    print(f"  C abs(-42) = {libc.abs(-42)}")

    # strlen(const char*) -> size_t
    libc.strlen.argtypes = [ctypes.c_char_p]
    libc.strlen.restype = ctypes.c_size_t
    s = b"Hello, ctypes!"
    print(f"  C strlen({s!r}) = {libc.strlen(s)}")

    # atoi(const char*) -> int
    libc.atoi.argtypes = [ctypes.c_char_p]
    libc.atoi.restype = ctypes.c_int
    print(f"  C atoi('12345') = {libc.atoi(b'12345')}")

    # Java 对比：这些在 Java 里直接用 Math.abs / String.length，
    # 但 ctypes 演示了如何直接调用 C 层实现


# ---------------------------------------------------------------------------
# 4. 传递指针和修改 C 变量
# ---------------------------------------------------------------------------
def demo_pointers(libc):
    print("\n=== 4. 传递指针给 C 函数 ===")
    # C 函数经常通过指针参数返回多个值，ctypes 用 byref 实现

    # 模拟一个场景：C 的 divmod（div 函数返回商，余数通过指针）
    # Windows msvcrt 没有 div 函数暴露给 ctypes，这里用 sprintf 演示指针
    # sprintf(char *str, const char *format, ...) -> int

    try:
        libc.sprintf.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        libc.sprintf.restype = ctypes.c_int
        # 分配 buffer
        buf = ctypes.create_string_buffer(100)
        libc.sprintf(buf, b"Value = %d, Str = %s", 42, b"test")
        print(f"  sprintf 结果: {buf.value!r}")
    except AttributeError:
        print("  (当前平台 C 库无 sprintf，跳过)")

    # 演示 byref：把 Python 变量地址传给 C
    # 假设有个 C 函数 void add_one(int *x)，这里用 ctypes 模拟
    x = ctypes.c_int(10)
    print(f"  ctypes c_int: x.value = {x.value}")
    # byref(x) 得到指向 x 的指针，C 函数可修改它
    ptr = ctypes.byref(x)
    print(f"  byref(x) 的类型: {type(ptr).__name__} (传给需要 int* 的 C 函数)")


# ---------------------------------------------------------------------------
# 5. 定义 C 结构体
# ---------------------------------------------------------------------------
# C 结构体对应：
#   struct Point { int x; int y; };
class CPoint(ctypes.Structure):
    """对应 C 的 struct Point { int x; int y; }。
    Java JNI 中需要手写对应 Java 类，ctypes 用 Structure 子类即可。
    """
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
    ]


def demo_struct():
    print("\n=== 5. 定义 C 结构体 ===")
    p = CPoint(3, 4)
    print(f"  CPoint(3, 4): x={p.x}, y={p.y}")

    # 修改字段
    p.x = 10
    print(f"  修改后: x={p.x}, y={p.y}")

    # 结构体大小（C 的 sizeof）
    size = ctypes.sizeof(CPoint)
    print(f"  sizeof(CPoint) = {size} 字节")

    # 结构体数组
    points = (CPoint * 3)()  # CPoint[3]
    for i, pt in enumerate(points):
        pt.x = i
        pt.y = i * i
    print(f"  结构体数组: {[(p.x, p.y) for p in points]}")


# ---------------------------------------------------------------------------
# 6. 回调函数：把 Python 函数传给 C
# ---------------------------------------------------------------------------
def demo_callback(libc):
    print("\n=== 6. 回调函数：Python 函数作为 C 回调 ===")
    # Java JNI 回调很复杂，ctypes 用 CFUNCTYPE 创建函数指针

    # qsort(void *base, size_t nmemb, size_t size,
    #       int (*compar)(const void *, const void *))
    try:
        libc.qsort.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t,
            ctypes.CFUNCTYPE(ctypes.c_int,
                             ctypes.c_void_p, ctypes.c_void_p),
        ]
        libc.qsort.restype = None
    except AttributeError:
        print("  (当前平台 C 库无 qsort，用模拟演示)")
        # 即使没有 qsort，也演示 CFUNCTYPE 的用法
        pass

    # 定义比较函数类型：int cmp(const void*, const void*)
    CMPFUNC = ctypes.CFUNCTYPE(
        ctypes.c_int,        # 返回 int
        ctypes.c_void_p,     # const void*
        ctypes.c_void_p,     # const void*
    )

    # Python 比较函数（转成 C 函数指针）
    @CMPFUNC
    def compare(a, b):
        # a, b 是 void 指针，转成 int 指针再取值
        va = ctypes.cast(a, ctypes.POINTER(ctypes.c_int))
        vb = ctypes.cast(b, ctypes.POINTER(ctypes.c_int))
        # 返回负/零/正，类似 Java Comparator
        return va[0] - vb[0]

    # 准备 C 数组
    arr = (ctypes.c_int * 5)(5, 3, 1, 4, 2)
    print(f"  排序前: {[arr[i] for i in range(5)]}")

    try:
        libc.qsort(arr, 5, ctypes.sizeof(ctypes.c_int), compare)
        print(f"  qsort 后: {[arr[i] for i in range(5)]}")
    except (AttributeError, OSError):
        # 没有 qsort 就用 Python sorted 模拟结果展示
        sorted_arr = sorted([arr[i] for i in range(5)])
        print(f"  (模拟) 排序后: {sorted_arr}")
        print("  回调函数 compare 已定义，演示了 CFUNCTYPE 用法")


# ---------------------------------------------------------------------------
# 7. cffi 简介
# ---------------------------------------------------------------------------
def demo_cffi_intro():
    print("\n=== 7. cffi 简介 ===")
    print("  cffi（C Foreign Function Interface）是 ctypes 的替代/增强")
    print("  特点：")
    print("    - 可以直接写 C 声明（cdef），自动解析，不用手动设 argtypes")
    print("    - ABI 模式（运行时）和 API 模式（编译时，更快）")
    print("    - PyPy 上性能比 ctypes 好很多")
    print("  Java 对比：cffi ≈ JNA（Java Native Access），运行时绑定，无需编译")
    print("  示例代码（需 pip install cffi）：")
    print('    from cffi import FFI')
    print('    ffi = FFI()')
    print('    ffi.cdef("int abs(int);")  # 直接写 C 声明')
    print('    libc = ffi.dlopen("msvcrt")  # 或 libc.so.6')
    print('    print(libc.abs(-42))')
    print("  cffi vs ctypes：cffi 更现代，类型更安全，但 ctypes 是内置无需安装")


# ---------------------------------------------------------------------------
# 8. Cython 简介
# ---------------------------------------------------------------------------
def demo_cython_intro():
    print("\n=== 8. Cython 简介 ===")
    print("  Cython 是 Python 的超集，可编译成 C 扩展，大幅提速")
    print("  特点：")
    print("    - .pyx 文件：Python 语法 + C 类型声明")
    print("    - 编译成 .c 再编译成 .pyd/.so，性能接近 C")
    print("    - 可直接调用 C 库，比 ctypes 快（编译时绑定）")
    print("  Java 对比：无直接对应（Java 不能把源码编译成原生 C 扩展）")
    print("  示例 .pyx 代码：")
    print("    # fib.pyx")
    print("    def fib(int n):       # 加 C 类型声明")
    print("        cdef int a = 0, b = 1, i")
    print("        for i in range(n):")
    print("            a, b = b, a + b")
    print("        return a")
    print("  编译：在 setup.py 里用 cythonize，或用 cythonize CLI")
    print("  典型加速：10-100 倍（数值密集型）")


# ---------------------------------------------------------------------------
# 9. PyO3 (Rust 扩展) 简介
# ---------------------------------------------------------------------------
def demo_pyo3_intro():
    print("\n=== 9. PyO3 (Rust 扩展) 简介 ===")
    print("  PyO3 是用 Rust 编写 Python 扩展的绑定库")
    print("  特点：")
    print("    - Rust 的安全 + 性能，自动生成 Python 可调用的模块")
    print("    - 用 maturin 构建（类似 setuptools）")
    print("    - 性能与 C 扩展相当，但内存安全")
    print("  Java 对比：无直接对应（Java 生态没有 Rust 绑定的主流方案）")
    print("  示例 Rust 代码（lib.rs）：")
    print("    use pyo3::prelude::*;")
    print("    #[pyfunction]")
    print("    fn fib(n: u64) -> u64 {")
    print("        let (mut a, mut b) = (0, 1);")
    print("        for _ in 0..n { let t = a + b; a = b; b = t; }")
    print("        a")
    print("    }")
    print("    #[pymodule]")
    print("    fn my_ext(_py: Python, m: &PyModule) -> PyResult<()> {")
    print("        m.add_function(wrap_pyfunction!(fib, m)?)?; Ok(())")
    print("    }")
    print("  构建：maturin develop（开发）/ maturin build（发布）")
    print("  知名项目：pydantic-core、polars、ruff 都用 PyO3")


# ---------------------------------------------------------------------------
# 10. mypyc 简介
# ---------------------------------------------------------------------------
def demo_mypyc_intro():
    print("\n=== 10. mypyc 简介 ===")
    print("  mypyc 是 mypy 项目的一部分，把类型注解的 Python 编译成 C 扩展")
    print("  特点：")
    print("    - 不需要改语法，只用现有类型注解")
    print("    - 编译后保持 Python 语义，但静态类型部分提速")
    print("    - 典型加速 2-10 倍（不如 Cython 激进，但零改动成本）")
    print("  Java 对比：类似 GraalVM 的原生镜像，把解释执行编译成原生")
    print("  用法：")
    print("    pip install mypy           # 装 mypy（含 mypyc）")
    print("    mypyc my_module.py         # 编译成扩展")
    print("  知名项目：mypy 自身用 mypyc 编译，提速 4 倍")


# ---------------------------------------------------------------------------
# 11. 性能对比说明
# ---------------------------------------------------------------------------
def demo_performance_notes():
    print("\n=== 11. 各方案对比 ===")
    print("  方案       | 易用性 | 性能   | 安全性 | 适用场景")
    print("  -----------|--------|--------|--------|------------------")
    print("  ctypes     | 高     | 中     | 低     | 快速调用现有 C 库")
    print("  cffi       | 中     | 中高   | 中     | 需要类型安全的 C 绑定")
    print("  Cython     | 中     | 高     | 中     | 加速 Python 代码")
    print("  PyO3(Rust) | 低     | 高     | 高     | 高性能 + 内存安全")
    print("  mypyc      | 高     | 中高   | 高     | 零改动加速类型化代码")
    print("  纯 Python  | 最高   | 低     | 高     | 开发优先，性能次要")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("12 - C 扩展与互操作")
    print("=" * 60)

    # 加载 C 库（跨平台）
    libc, lib_name = load_c_library()

    try:
        demo_printf(libc)
        demo_simple_functions(libc)
        demo_pointers(libc)
        demo_struct()
        demo_callback(libc)
    except Exception as e:
        print(f"  C 库调用出错（部分平台函数可能不可用）: {e}")

    demo_cffi_intro()
    demo_cython_intro()
    demo_pyo3_intro()
    demo_mypyc_intro()
    demo_performance_notes()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - ctypes：内置，直接调用 C 共享库，无需编译（类似 JNI 但更简单）")
    print("  - cffi：更现代的 C 绑定，类似 JNA")
    print("  - Cython：Python 超集，编译成 C 扩展，提速 10-100x")
    print("  - PyO3：Rust 写扩展，安全 + 高性能（ruff/polars 用它）")
    print("  - mypyc：用类型注解零改动编译加速")
    print("  - Windows 用 ctypes.cdll.msvcrt，Linux 用 libc.so.6")
    print("=" * 60)


if __name__ == "__main__":
    main()
