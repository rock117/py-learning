"""
10 - 内省与反射
================
本节目标：
  1. inspect 模块：获取函数签名、源码、调用栈（对比 Java java.lang.reflect）
  2. __dict__ / __mro__ 对象属性、方法解析顺序
  3. getattr/setattr/hasattr 动态属性访问（对比 Java Field.get/set）
  4. dir() 列出所有属性（对比 Java getMethods()）
  5. __getattr__ vs __getattribute__ 的区别
  6. 实战：实现一个简单的 ORM 映射或插件系统

对应 Java 概念：
  - inspect ≈ java.lang.reflect.Method/Field/Constructor
  - __dict__ ≈ 反射读取字段表
  - getattr/setattr ≈ Field.get()/Field.set()
  - dir() ≈ Class.getMethods() + getFields()
  - __getattr__ ≈ 动态代理 InvocationHandler
"""

import inspect
import importlib
import sys


# ---------------------------------------------------------------------------
# 1. inspect 获取函数签名
# ---------------------------------------------------------------------------
def greet(name: str, *, greeting: str = "Hello", times: int = 1) -> str:
    """带关键字参数和默认值的函数。"""
    return (f"{greeting}, {name}! " * times).strip()


def demo_inspect_signature():
    print("\n=== 1. inspect 获取函数签名 ===")
    # Java: Method.getParameters() 只能拿到参数类型，拿不到名字（编译时 -parameters 才行）
    # Python 的 inspect 能拿到完整的参数名、默认值、注解

    sig = inspect.signature(greet)
    print(f"  signature: {sig}")
    print(f"  参数列表:")
    for name, param in sig.parameters.items():
        print(f"    {name}: kind={param.kind.name}, "
              f"default={param.default}, annotation={param.annotation}")

    # 返回注解
    print(f"  返回注解: {sig.return_annotation}")

    # 用 signature 绑定参数（验证调用是否合法）
    bound = sig.bind("Alice", greeting="Hi", times=2)
    bound.apply_defaults()
    print(f"  绑定参数: {dict(bound.arguments)}")
    print(f"  实际调用: {greet(**bound.arguments)}")


# ---------------------------------------------------------------------------
# 2. inspect 获取源码
# ---------------------------------------------------------------------------
def demo_inspect_source():
    print("\n=== 2. inspect 获取源码 ===")
    # Java 没有等价（运行时拿不到源码，只能反编译字节码）
    source = inspect.getsource(greet)
    print(f"  greet 的源码:\n{source}")

    # 获取定义所在文件和行号
    file, line = inspect.getsourcefile(greet), inspect.getsourcelines(greet)[1]
    print(f"  定义位置: {file}:{line}")


# ---------------------------------------------------------------------------
# 3. inspect 调用栈
# ---------------------------------------------------------------------------
def level3():
    """最深层。"""
    print("\n=== 3. inspect 调用栈 ===")
    # Java: Thread.currentThread().getStackTrace()
    for frame_info in inspect.stack():
        print(f"    {frame_info.function} @ "
              f"{frame_info.filename}:{frame_info.lineno}")


def level2():
    level3()


def level1():
    level2()


def demo_inspect_stack():
    level1()


# ---------------------------------------------------------------------------
# 4. __dict__ 查看对象属性
# ---------------------------------------------------------------------------
class Person:
    class_attr = "我是类属性"  # 类属性，存在类的 __dict__

    def __init__(self, name: str, age: int):
        self.name = name  # 实例属性，存在实例的 __dict__
        self.age = age

    def say_hi(self):
        return f"Hi, I'm {self.name}"


def demo_dict():
    print("\n=== 4. __dict__ 查看对象属性 ===")
    p = Person("Alice", 30)

    # 实例的 __dict__：只有实例属性
    print(f"  实例 __dict__: {p.__dict__}")
    # Java 等价：反射遍历 Field，但 Java 字段是编译期固定的

    # 类的 __dict__：包含类属性、方法等（mappingproxy，只读视图）
    print(f"  类 __dict__ 的 keys: {list(Person.__dict__.keys())}")

    # 动态添加实例属性（Java 做不到，Java 字段固定）
    p.email = "alice@example.com"
    print(f"  动态添加后: {p.__dict__}")

    # 动态添加类属性
    Person.species = "human"
    print(f"  类属性 species: {Person.species}")


# ---------------------------------------------------------------------------
# 5. __mro__ 方法解析顺序
# ---------------------------------------------------------------------------
class A:
    def who(self):
        return "A"


class B(A):
    def who(self):
        return "B"


class C(A):
    def who(self):
        return "C"


class D(B, C):  # 多继承
    pass


def demo_mro():
    print("\n=== 5. __mro__ 方法解析顺序 ===")
    # Java 不支持多继承（类），只有接口多继承，没有 MRO 问题
    # Python 用 C3 线性化算法确定方法查找顺序

    print(f"  D.__mro__: {[cls.__name__ for cls in D.__mro__]}")
    # D → B → C → A → object

    d = D()
    print(f"  d.who() = {d.who()}")  # 找到 B.who 先

    # 用 super() 按 MRO 调用"下一个"
    print(f"  MRO 决定了 super() 的跳转路径")


# ---------------------------------------------------------------------------
# 6. getattr / setattr / hasattr 动态属性访问
# ---------------------------------------------------------------------------
def demo_dynamic_attr():
    print("\n=== 6. getattr/setattr/hasattr 动态属性访问 ===")
    p = Person("Bob", 25)

    # getattr：等价于 p.name，但属性名是字符串（运行时决定）
    # Java: Field field = cls.getDeclaredField("name"); field.get(obj)
    name = getattr(p, "name")
    print(f"  getattr(p, 'name') = {name}")

    # 带默认值（属性不存在时不报错）
    email = getattr(p, "email", "N/A")
    print(f"  getattr(p, 'email', 'N/A') = {email}")

    # hasattr：检查属性是否存在
    print(f"  hasattr(p, 'age'): {hasattr(p, 'age')}")
    print(f"  hasattr(p, 'salary'): {hasattr(p, 'salary')}")

    # setattr：动态设置属性
    setattr(p, "salary", 50000)
    print(f"  setattr 后 p.salary = {p.salary}")

    # 动态方法调用
    method = getattr(p, "say_hi")
    print(f"  动态调用方法: {method()}")

    # delattr：删除属性
    delattr(p, "salary")
    print(f"  delattr 后 hasattr salary: {hasattr(p, 'salary')}")


# ---------------------------------------------------------------------------
# 7. dir() 列出所有属性
# ---------------------------------------------------------------------------
def demo_dir():
    print("\n=== 7. dir() 列出所有属性 ===")
    # Java: cls.getMethods() + cls.getFields()
    p = Person("Carol", 40)
    all_attrs = dir(p)
    print(f"  dir(p) 共 {len(all_attrs)} 个属性")
    # 过滤掉 dunder 方法，只看"用户可见"的
    user_attrs = [a for a in all_attrs if not a.startswith("__")]
    print(f"  非 dunder 属性: {user_attrs}")

    # dir() 模块：列出模块的所有名字
    import math
    math_names = [n for n in dir(math) if not n.startswith("_")]
    print(f"  dir(math) 前 5 个: {math_names[:5]}...")


# ---------------------------------------------------------------------------
# 8. __getattr__ vs __getattribute__ 的区别
# ---------------------------------------------------------------------------
class LazyObject:
    """演示 __getattr__：只有属性不存在时才调用（用于惰性加载/代理）。"""

    def __init__(self):
        self.real = "real_value"

    def __getattr__(self, name):
        """只有当正常属性查找失败时才调用。
        Java 等价：动态代理 InvocationHandler.invoke()
        常用于：代理模式、惰性属性、__getattr__ 链。
        """
        print(f"  [__getattr__] 访问不存在的属性: {name}")
        if name.startswith("lazy_"):
            value = f"computed-{name}"
            setattr(self, name, value)  # 缓存起来
            return value
        raise AttributeError(f"'{type(self).__name__}' 没有属性 '{name}'")


class TracingObject:
    """演示 __getattribute__：每次属性访问都调用（慎用，易递归）。"""

    def __init__(self):
        self.data = "tracing_value"

    def __getattribute__(self, name):
        """对"所有"属性访问生效，包括已存在的。
        注意：内部访问 self.xxx 会再次触发 __getattribute__，容易无限递归。
        必须用 object.__getattribute__ 来避免递归。
        """
        # 拿真实值（绕过自身，避免递归）
        value = object.__getattribute__(self, name)
        print(f"  [__getattribute__] 读取 {name} = {value!r}")
        return value


def demo_getattr_vs_getattribute():
    print("\n=== 8. __getattr__ vs __getattribute__ ===")
    print("  --- __getattr__（仅属性不存在时触发）---")
    obj = LazyObject()
    print(f"  obj.real = {obj.real}")  # 存在，不触发 __getattr__
    print(f"  obj.lazy_x = {obj.lazy_x}")  # 不存在，触发 __getattr__
    print(f"  obj.lazy_x 再次 = {obj.lazy_x}")  # 已缓存，不触发

    print("\n  --- __getattribute__（每次访问都触发）---")
    tobj = TracingObject()
    tobj.data  # 触发
    print("  总结: __getattr__ 用于「兜底」，__getattribute__ 用于「拦截所有」")


# ---------------------------------------------------------------------------
# 9. 实战：简易 ORM 映射
# ---------------------------------------------------------------------------
class Model:
    """简易 ORM 基类：把类属性的字段定义映射到数据库列。
    Java 等价：JPA @Entity + @Column 注解 + 反射。
    这里用 __init_subclass__ + 类属性实现类似效果。
    """

    # 子类定义后，自动收集带 Column 标记的字段
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._columns = {}  # 存储列名 -> 类型
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, Column):
                cls._columns[name] = value
                # 把类属性替换为描述符，实现实例级存储
                setattr(cls, name, value)

    def __init__(self, **kwargs):
        for col_name in self._columns:
            setattr(self, f"_col_{col_name}", kwargs.get(col_name, None))

    def to_dict(self):
        return {name: getattr(self, f"_col_{name}")
                for name in self._columns}

    @classmethod
    def columns(cls):
        return list(cls._columns.keys())


class Column:
    """字段描述符：模拟数据库列定义。"""
    def __init__(self, col_type=str, primary_key=False):
        self.col_type = col_type
        self.primary_key = primary_key
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # 类访问返回描述符本身
        return getattr(obj, f"_col_{self.name}", None)

    def __set__(self, obj, value):
        setattr(obj, f"_col_{self.name}", value)


class User(Model):
    """ORM 实体定义，类似 JPA 的 @Entity。"""
    id = Column(int, primary_key=True)
    username = Column(str)
    email = Column(str)
    age = Column(int)


def demo_orm():
    print("\n=== 9. 实战：简易 ORM 映射 ===")
    print(f"  User 表的列: {User.columns()}")

    user = User(id=1, username="alice", email="alice@x.com", age=30)
    print(f"  user.username = {user.username}")
    print(f"  user.to_dict() = {user.to_dict()}")

    # 模拟生成 SQL
    cols = ", ".join(User.columns())
    placeholders = ", ".join(["?"] * len(User.columns()))
    print(f"  INSERT SQL: INSERT INTO user ({cols}) VALUES ({placeholders})")

    # 模拟从数据库行构造对象
    db_row = (2, "bob", "bob@x.com", 25)
    row_dict = dict(zip(User.columns(), db_row))
    user2 = User(**row_dict)
    print(f"  从行构造: {user2.to_dict()}")


# ---------------------------------------------------------------------------
# 10. 实战：插件系统
# ---------------------------------------------------------------------------
def demo_plugin_system():
    print("\n=== 10. 实战：插件系统 ===")
    # 通过 importlib 动态导入模块，inspect 发现其中的类/函数
    # Java 等价：ServiceLoader / SPI 机制

    # 这里用内置模块做演示（实际可扫描目录动态加载）
    # 模拟：发现某个模块里所有以 "plugin_" 开头的函数
    fake_plugin_module = type("FakePlugin", (), {
        "plugin_greet": lambda self: "Hello from plugin",
        "plugin_bye": lambda self: "Bye from plugin",
        "internal_helper": lambda self: "not a plugin",
    })()

    plugins = {}
    for name in dir(fake_plugin_module):
        if name.startswith("plugin_"):
            plugins[name] = getattr(fake_plugin_module, name)

    print(f"  发现的插件: {list(plugins.keys())}")
    for pname, pfunc in plugins.items():
        print(f"    {pname}() -> {pfunc()}")

    # 真实场景：用 importlib 动态加载
    # module = importlib.import_module("my_plugins.email_plugin")
    # for name in dir(module):
    #     if name.startswith("plugin_"):
    #         plugin_cls = getattr(module, name)
    print("  (实际项目用 importlib.import_module 动态加载插件模块)")


# ---------------------------------------------------------------------------
# 11. type() 和 isinstance() 的内省
# ---------------------------------------------------------------------------
def demo_type_introspection():
    print("\n=== 11. type() / isinstance() / issubclass() ===")
    p = Person("Dave", 50)

    print(f"  type(p) = {type(p)}")
    print(f"  type(p).__name__ = {type(p).__name__}")
    print(f"  type(p).__bases__ = {type(p).__bases__}")  # 父类元组

    print(f"  isinstance(p, Person): {isinstance(p, Person)}")
    print(f"  isinstance(p, object): {isinstance(p, object)}")
    print(f"  issubclass(Person, object): {issubclass(Person, object)}")

    # 动态创建类（Java 用字节码生成，Python 用 type() 三参数形式）
    DynamicClass = type("DynamicClass", (object,), {"greet": lambda self: "hi"})
    obj = DynamicClass()
    print(f"  动态创建的类: {type(obj).__name__}, obj.greet() = {obj.greet()}")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("10 - 内省与反射")
    print("=" * 60)

    demo_inspect_signature()
    demo_inspect_source()
    demo_inspect_stack()
    demo_dict()
    demo_mro()
    demo_dynamic_attr()
    demo_dir()
    demo_getattr_vs_getattribute()
    demo_orm()
    demo_plugin_system()
    demo_type_introspection()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - inspect：函数签名、源码、调用栈，比 Java 反射信息更丰富")
    print("  - __dict__：实例/类的属性表，可动态增删")
    print("  - __mro__：多继承的方法查找顺序（C3 线性化）")
    print("  - getattr/setattr/hasattr：动态属性访问")
    print("  - __getattr__ 兜底，__getattribute__ 全拦截")
    print("  - 实战：ORM 用描述符 + __init_subclass__，插件用 importlib")
    print("=" * 60)


if __name__ == "__main__":
    main()
