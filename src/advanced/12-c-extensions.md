# C 扩展与互操作

当纯 Python 性能不够时，可以通过多种方式调用 C 或其他语言编写的高性能代码。
本章讲解 `ctypes`、`cffi`、`Cython`、`PyO3` 和 `mypyc` 等方案。

## Java 对比总览

| Python 方案 | Java 对应 | 说明 |
|-------------|-----------|------|
| ctypes | JNI | 调用 C 共享库，但更简单 |
| cffi | JNA | 运行时绑定，无需编译 |
| Cython | 无直接对应 | Python 超集编译成 C 扩展 |
| PyO3 | 无直接对应 | Rust 写 Python 扩展 |
| mypyc | GraalVM 原生镜像 | 类型注解编译加速 |

## ctypes：调用 C 共享库

`ctypes` 是 Python 内置模块，无需安装，直接调用 C 共享库的函数。

### 加载 C 标准库

根据平台加载不同的 C 运行时：

> [跨平台加载 C 标准库](../code/advanced/12_c_extensions.py#L30-L58)

```python
{{#include ../code/advanced/12_c_extensions.py:30:58}}
```

### 调用 printf

```python
libc.printf.argtypes = [ctypes.c_char_p]
libc.printf.restype = ctypes.c_int
count = libc.printf(b"Hello from C standard library!\n")
```

注意传 `bytes`（C 字符串），不是 `str`。

> [调用 C 的 printf](../code/advanced/12_c_extensions.py#L59-L78)

```python
{{#include ../code/advanced/12_c_extensions.py:59:78}}
```

### 调用简单函数：abs / strlen / atoi

```python
libc.abs.argtypes = [ctypes.c_int]
libc.abs.restype = ctypes.c_int
libc.abs(-42)  # 42

libc.strlen.argtypes = [ctypes.c_char_p]
libc.strlen.restype = ctypes.c_size_t
libc.strlen(b"Hello, ctypes!")  # 14
```

> [调用 C 标准库简单函数](../code/advanced/12_c_extensions.py#L79-L104)

```python
{{#include ../code/advanced/12_c_extensions.py:79:104}}
```

### Java 对比

Java JNI 调用 C 需要：写 native 方法 → javac → javah 生成头文件 → C 实现并编译。
Python ctypes 直接声明函数签名即可调用，**无需编译任何 C 代码**。

## 传递指针与修改 C 变量

C 函数常通过指针参数返回多个值，ctypes 用 `byref` 和 `create_string_buffer` 实现。

```python
buf = ctypes.create_string_buffer(100)
libc.sprintf(buf, b"Value = %d, Str = %s", 42, b"test")

x = ctypes.c_int(10)
ptr = ctypes.byref(x)  # 指向 x 的指针
```

> [传递指针给 C 函数](../code/advanced/12_c_extensions.py#L105-L136)

```python
{{#include ../code/advanced/12_c_extensions.py:105:136}}
```

## 定义 C 结构体

用 `ctypes.Structure` 子类定义 C 结构体，`_fields_` 指定字段。

```python
class CPoint(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
    ]

p = CPoint(3, 4)
ctypes.sizeof(CPoint)  # 结构体大小
points = (CPoint * 3)()  # 结构体数组
```

> [定义 C 结构体与数组](../code/advanced/12_c_extensions.py#L137-L144)

```python
{{#include ../code/advanced/12_c_extensions.py:137:144}}
```

### Java 对比

JNI 中需要手写对应的 Java 类来映射 C 结构体，ctypes 用 `Structure` 子类即可。

## 回调函数：Python 函数作为 C 回调

用 `CFUNCTYPE` 创建函数指针类型，把 Python 函数转成 C 回调。

```python
CMPFUNC = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
)

@CMPFUNC
def compare(a, b):
    va = ctypes.cast(a, ctypes.POINTER(ctypes.c_int))
    vb = ctypes.cast(b, ctypes.POINTER(ctypes.c_int))
    return va[0] - vb[0]

libc.qsort(arr, 5, ctypes.sizeof(ctypes.c_int), compare)
```

> [回调函数：qsort 排序](../code/advanced/12_c_extensions.py#L171-L221)

```python
{{#include ../code/advanced/12_c_extensions.py:171:221}}
```

### Java 对比

Java JNI 回调非常复杂，ctypes 用 `CFUNCTYPE` 装饰器即可，类似 Java 的 `Comparator`。

## cffi：更现代的 C 绑定

`cffi` 可以直接写 C 声明（`cdef`），自动解析，不用手动设 `argtypes`。

```python
from cffi import FFI
ffi = FFI()
ffi.cdef("int abs(int);")
libc = ffi.dlopen("msvcrt")
print(libc.abs(-42))
```

> [cffi 简介](../code/advanced/12_c_extensions.py#L222-L241)

```python
{{#include ../code/advanced/12_c_extensions.py:222:241}}
```

### Java 对比

cffi ≈ JNA（Java Native Access），运行时绑定，无需编译 C 代码。cffi 比 ctypes 类型更安全。

## Cython：Python 超集编译成 C

Cython 是 Python 的超集，可加 C 类型声明，编译成 C 扩展，提速 10-100 倍。

```cython
# fib.pyx
def fib(int n):
    cdef int a = 0, b = 1, i
    for i in range(n):
        a, b = b, a + b
    return a
```

> [Cython 简介](../code/advanced/12_c_extensions.py#L242-L263)

```python
{{#include ../code/advanced/12_c_extensions.py:242:263}}
```

### Java 对比

Java 不能把源码编译成原生 C 扩展。Cython 是 Python 生态独有的加速方案。

## PyO3：Rust 写 Python 扩展

PyO3 是用 Rust 编写 Python 扩展的绑定库，兼具安全与高性能。

```rust
use pyo3::prelude::*;
#[pyfunction]
fn fib(n: u64) -> u64 {
    let (mut a, mut b) = (0, 1);
    for _ in 0..n { let t = a + b; a = b; b = t; }
    a
}
```

> [PyO3 简介](../code/advanced/12_c_extensions.py#L264-L290)

```python
{{#include ../code/advanced/12_c_extensions.py:264:290}}
```

知名项目 pydantic-core、polars、ruff 都用 PyO3。构建工具是 `maturin`。

## mypyc：类型注解零改动加速

`mypyc` 把类型注解的 Python 编译成 C 扩展，不需要改语法，典型加速 2-10 倍。

```bash
pip install mypy
mypyc my_module.py
```

> [mypyc 简介](../code/advanced/12_c_extensions.py#L291-L307)

```python
{{#include ../code/advanced/12_c_extensions.py:291:307}}
```

### Java 对比

类似 GraalVM 的原生镜像，把解释执行编译成原生代码。mypy 自身用 mypyc 编译后提速 4 倍。

## 各方案对比

| 方案 | 易用性 | 性能 | 安全性 | 适用场景 |
|------|--------|------|--------|----------|
| ctypes | 高 | 中 | 低 | 快速调用现有 C 库 |
| cffi | 中 | 中高 | 中 | 类型安全的 C 绑定 |
| Cython | 中 | 高 | 中 | 加速 Python 代码 |
| PyO3 (Rust) | 低 | 高 | 高 | 高性能 + 内存安全 |
| mypyc | 高 | 中高 | 高 | 零改动加速类型化代码 |
| 纯 Python | 最高 | 低 | 高 | 开发优先，性能次要 |

> [各方案对比表](../code/advanced/12_c_extensions.py#L308-L322)

```python
{{#include ../code/advanced/12_c_extensions.py:308:322}}
```

## 小结

- `ctypes`：内置，直接调用 C 共享库，无需编译（类似 JNI 但更简单）
- `cffi`：更现代的 C 绑定，类似 JNA
- `Cython`：Python 超集，编译成 C 扩展，提速 10-100x
- `PyO3`：Rust 写扩展，安全 + 高性能（ruff/polars 用它）
- `mypyc`：用类型注解零改动编译加速
- Windows 用 `ctypes.cdll.msvcrt`，Linux 用 `libc.so.6`

> 📁 [查看完整代码](../code/advanced/12_c_extensions.py)
