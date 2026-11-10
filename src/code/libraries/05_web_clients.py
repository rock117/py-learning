# -*- coding: utf-8 -*-
"""
05_web_clients.py - Python HTTP 客户端、模板引擎与数据校验

本文件面向有丰富 Java 经验的开发者，讲解 Python 生态中"调用外部 HTTP 服务 /
渲染模板 / 数据校验"相关的类库：
    - requests   ：同步 HTTP 客户端（对比 Java HttpClient / OkHttp / RestTemplate）
    - httpx      ：同步 + 异步 HTTP 客户端（对比 Java HttpClient + WebClient）
    - aiohttp    ：异步 HTTP 客户端/服务端（对比 Netty / WebClient）
    - Jinja2     ：模板引擎（对比 Thymeleaf / FreeMarker）
    - pydantic   ：数据校验与序列化（对比 Bean Validation / Jackson + Hibernate Validator）

[注意] 本文件所有 demo 默认都只在本地运行，不发真实网络请求：
       HTTP 客户端部分使用 requests/httpx 的自定义 Adapter/MockTransport，
       或者用 aiohttp 的自建测试服务器 + 本地回环，避免依赖外网。
       如果某个库没有安装，对应 demo 会打印提示并跳过，不影响 exit code 0。

运行：
    python 05_web_clients.py
"""

import json
import sys


# =============================================================================
# 第一部分：requests —— 最流行的同步 HTTP 客户端
# =============================================================================
# [Java 对比] requests ~ OkHttp / Apache HttpClient / Spring RestTemplate
#             Python 版 API 极其简洁，是"人类友好"的典范。

def demo_requests_basic():
    """requests 基本用法。

    演示 GET/POST/参数/JSON，但请求目标被替换成本地 mock，
    这样既能展示 API 形式，又不依赖网络。
    """
    print("=== 1. requests 基本用法 ===")
    try:
        import requests
    except ImportError:
        print("  [注意] requests 未安装，跳过。安装: pip install requests")
        return

    from unittest.mock import Mock, patch

    # 构造一个假的响应对象，模拟服务器返回
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.headers = {"Content-Type": "application/json"}
    fake_response.json.return_value = {"id": 1, "name": "Alice"}
    fake_response.text = '{"id": 1, "name": "Alice"}'
    fake_response.raise_for_status = Mock()  # 200 时不抛异常

    with patch.object(requests, "get", return_value=fake_response) as mock_get:
        # [Java 对比]
        #   HttpResponse<String> resp = client.send(request, BodyHandlers.ofString());
        #   int code = resp.statusCode();
        resp = requests.get(
            "https://api.example.com/users/1",
            params={"include": "profile"},   # 自动拼接到 query string
            headers={"Accept": "application/json"},
            timeout=5,                        # 强烈建议总是设置 timeout
        )
        print(f"  请求 URL: {mock_get.call_args}")
        print(f"  status_code: {resp.status_code}")
        print(f"  json: {resp.json()}")

    # POST JSON 的典型写法
    with patch.object(requests, "post", return_value=fake_response) as mock_post:
        resp = requests.post(
            "https://api.example.com/users",
            json={"name": "Bob", "age": 30},  # 自动序列化 + 设置 Content-Type
            timeout=5,
        )
        print(f"  POST json 参数: {mock_post.call_args.kwargs['json']}")
        print(f"  返回: {resp.json()}")

    print("  [要点] 1) 永远设 timeout  2) 用 params/json 而不是自己拼字符串")
    print("  [要点] 3) 检查 status_code 或用 raise_for_status()")


def demo_requests_session_and_retry():
    """Session 复用连接 + 重试策略。

    [Java 对比] Session ~ OkHttp 的 OkHttpClient（连接池 + 拦截器 + 默认头）。
    """
    print("\n=== 2. requests.Session 与重试 ===")
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
    except ImportError:
        print("  [注意] requests / urllib3 未安装，跳过。")
        return

    session = requests.Session()
    session.headers.update({"User-Agent": "py-learning/1.0"})

    retry = Retry(
        total=3,                       # 最多重试 3 次
        backoff_factor=0.5,            # 指数退避：0.5s, 1s, 2s
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    print(f"  已为 http/https 挂载重试适配器: total={retry.total}, "
          f"status_forcelist={list(retry.status_forcelist)}")
    print(f"  Session 默认头: {dict(session.headers)}")
    print("  [要点] 同一进程内复用 Session，避免每次新建 TCP 连接")
    session.close()


def demo_requests_error_handling():
    """错误处理：超时 / 连接失败 / HTTP 错误码。"""
    print("\n=== 3. requests 错误处理 ===")
    try:
        import requests
    except ImportError:
        print("  [注意] requests 未安装，跳过。")
        return

    print("  常见异常层级:")
    print("    requests.exceptions.RequestException  (基类)")
    print("      +-- Timeout --------------- 连接/读取超时")
    print("      |     +-- ConnectTimeout")
    print("      |     +-- ReadTimeout")
    print("      +-- ConnectionError ------- DNS 失败 / 拒绝连接")
    print("      +-- HTTPError ------------- raise_for_status() 在 4xx/5xx 时抛出")
    print("      +-- TooManyRedirects")
    # 演示一个一定会失败的请求，捕获并展示异常类型
    try:
        requests.get("http://127.0.0.1:1/", timeout=0.2)
    except requests.exceptions.RequestException as exc:
        print(f"  实际捕获: {type(exc).__name__}")
    print("  [Java 对比] 相当于 IOException / SocketTimeoutException / 手写 4xx 判断")


# =============================================================================
# 第二部分：httpx —— 同步 + 异步统一 API
# =============================================================================
# [Java 对比] httpx 同时支持 sync/async，类似 Java 11 HttpClient，
#             但 Python 的 async 版本 API 与同步版几乎完全一致，迁移成本极低。

def demo_httpx_sync_and_async():
    """httpx 同步与异步用法，使用 MockTransport 避免网络。"""
    print("\n=== 4. httpx 同步 + 异步 ===")
    try:
        import httpx
    except ImportError:
        print("  [注意] httpx 未安装，跳过。安装: pip install httpx")
        return

    def handler(request: "httpx.Request") -> "httpx.Response":
        # 根据路径返回不同内容，模拟一个真实服务
        if request.url.path == "/ping":
            return httpx.Response(200, json={"pong": True})
        return httpx.Response(200, json={"path": request.url.path})

    # --- 同步 ---
    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.test") as client:
        r = client.get("/ping")
        print(f"  [sync] {r.status_code} {r.json()}")

    # --- 异步 ---
    import asyncio

    async def async_main():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="https://api.test"
        ) as client:
            tasks = [client.get(f"/item/{i}") for i in range(3)]
            results = await asyncio.gather(*tasks)   # 真并发
            return [r.json()["path"] for r in results]

    paths = asyncio.run(async_main())
    print(f"  [async] 并发 3 个请求: {paths}")
    print("  [Java 对比] async 版 ~ WebClient / HttpClient.sendAsync")
    print("  [要点] httpx 是 requests 的现代替代品，支持 HTTP/2、同步异步统一 API")


# =============================================================================
# 第三部分：aiohttp —— 异步 HTTP 客户端与服务器
# =============================================================================
# [Java 对比] aiohttp 客户端 ~ Netty HttpClient / WebClient
#             aiohttp 服务端 ~ Netty Server

def demo_aiohttp_client():
    """aiohttp 客户端：用自建的本地服务器做真实回环测试。"""
    print("\n=== 5. aiohttp 客户端 ===")
    try:
        import aiohttp
        from aiohttp import web
    except ImportError:
        print("  [注意] aiohttp 未安装，跳过。安装: pip install aiohttp")
        return

    import asyncio

    async def run():
        # 启动一个临时的本地 HTTP 服务器
        app = web.Application()

        async def hello(request):
            name = request.query.get("name", "world")
            return web.json_response({"hello": name})

        app.router.add_get("/hello", hello)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)   # 端口 0 = 让系统分配
        await site.start()

        # 取出实际监听的端口
        port = site._server.sockets[0].getsockname()[1]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{port}/hello", params={"name": "aiohttp"}) as resp:
                    data = await resp.json()
                    print(f"  GET /hello -> {resp.status} {data}")

                # 并发请求
                urls = [f"http://127.0.0.1:{port}/hello?name=user{i}" for i in range(5)]
                results = []
                for coro in [session.get(u) for u in urls]:
                    async with coro as r:
                        results.append((await r.json())["hello"])
                print(f"  并发 5 个请求的结果: {results}")
        finally:
            await runner.cleanup()

    asyncio.run(run())
    print("  [要点] ClientSession 应在整个应用生命周期复用，不要每次请求新建")


def demo_aiohttp_server_style():
    """aiohttp 服务端写法速览（只打印结构，不实际启动）。"""
    print("\n=== 6. aiohttp 服务端写法速览 ===")
    try:
        import aiohttp  # noqa: F401
    except ImportError:
        print("  [注意] aiohttp 未安装，跳过。")
        return

    snippet = '''\
from aiohttp import web

async def handle(request):
    name = request.match_info.get("name", "anonymous")
    return web.json_response({"name": name})

app = web.Application()
app.router.add_get("/users/{name}", handle)
web.run_app(app, host="127.0.0.1", port=8080)
'''
    print(snippet)
    print("  [Java 对比] 相当于一个极简的 Netty + Router，但没有 Spring 全家桶")


# =============================================================================
# 第四部分：Jinja2 —— 模板引擎
# =============================================================================
# [Java 对比] Jinja2 ~ Thymeleaf / FreeMarker / Velocity
#             语法与 Django 模板 / Thymeleaf 很像，但更通用（也用于 Ansible / Cookiecutter）

def demo_jinja2_basic():
    """Jinja2 基本用法：变量、过滤器、循环、条件。"""
    print("\n=== 7. Jinja2 基本用法 ===")
    try:
        from jinja2 import Environment, DictLoader
    except ImportError:
        print("  [注意] Jinja2 未安装，跳过。安装: pip install jinja2")
        return

    templates = {
        "page.html": """\
<h1>Hello {{ name | title }}</h1>
<p>注册时间: {{ created_at | default("未知") }}</p>
<ul>
{% for item in items %}
    <li>{{ loop.index }}. {{ item.name }} - {{ "%.2f" | format(item.price) }} 元</li>
{% else %}
    <li>没有商品</li>
{% endfor %}
</ul>
{% if items %}
<p>共 {{ items | length }} 件，总价 {{ items | sum(attribute="price") }} 元</p>
{% endif %}
""",
    }
    env = Environment(loader=DictLoader(templates), autoescape=True)
    tpl = env.get_template("page.html")

    html = tpl.render(
        name="alice",
        items=[
            {"name": "键盘", "price": 299.0},
            {"name": "鼠标", "price": 99.5},
            {"name": "显示器", "price": 1299.0},
        ],
    )
    print(html)
    print("  [要点] autoescape=True 默认对 HTML 转义，防止 XSS，务必开启")


def demo_jinja2_inheritance():
    """模板继承与宏：{% extends %} / {% block %} / {% macro %}。"""
    print("\n=== 8. Jinja2 模板继承与宏 ===")
    try:
        from jinja2 import Environment, DictLoader
    except ImportError:
        print("  [注意] Jinja2 未安装，跳过。")
        return

    templates = {
        "base.html": """\
<html><head><title>{% block title %}站点{% endblock %}</title></head>
<body>{% block content %}默认内容{% endblock %}</body></html>
""",
        "child.html": """\
{% extends "base.html" %}
{% macro badge(text, color) %}<span class="{{ color }}">{{ text }}</span>{% endmacro %}
{% block title %}用户列表{% endblock %}
{% block content %}
{{ badge("NEW", "green") }}
<ul>{% for u in users %}<li>{{ u }}</li>{% endfor %}</ul>
{% endblock %}
""",
    }
    env = Environment(loader=DictLoader(templates), autoescape=True)
    print(env.get_template("child.html").render(users=["Alice", "Bob", "Carol"]))
    print("  [Java 对比] 等价于 Thymeleaf 的 layout:fragment 或 FreeMarker 的 <#import>")


# =============================================================================
# 第五部分：pydantic —— 数据校验与序列化
# =============================================================================
# [Java 对比] pydantic = Jackson(序列化) + Hibernate Validator(校验) + Lombok(样板代码)
#             FastAPI 的请求/响应模型全部基于它。

def demo_pydantic_model():
    """BaseModel：类型校验、默认值、序列化。"""
    print("\n=== 9. pydantic 模型与校验 ===")
    try:
        from pydantic import BaseModel, Field, ValidationError
    except ImportError:
        print("  [注意] pydantic 未安装，跳过。安装: pip install pydantic")
        return

    class Address(BaseModel):
        city: str
        street: str = ""

    class User(BaseModel):
        id: int
        name: str = Field(min_length=1, max_length=20)
        age: int = Field(ge=0, le=150)
        email: str | None = None
        tags: list[str] = Field(default_factory=list)   # 可变的默认值要用 factory
        address: Address | None = None

    # 自动类型转换：字符串 "42" 会转成 int 42
    u = User(id="42", name="Alice", age=30, address={"city": "Beijing"})
    print(f"  解析成功: {u}")
    print(f"  id 类型: {type(u.id).__name__} = {u.id}")
    print(f"  age 类型: {type(u.age).__name__} = {u.age}")
    print(f"  序列化为 dict: {u.model_dump()}")
    print(f"  序列化为 JSON: {u.model_dump_json()}")

    # 校验失败：多个字段同时报错，会聚合成 ValidationError
    try:
        User(id=1, name="", age=-5)
    except ValidationError as exc:
        print(f"  校验失败，错误数: {exc.error_count()}")
        for err in exc.errors():
            print(f"    - {'.'.join(map(str, err['loc']))}: {err['msg']}")
    print("  [Java 对比] 相当于 @NotNull/@Size/@Min 等注解 + 统一异常处理")


def demo_pydantic_validator():
    """自定义校验器与模型配置。"""
    print("\n=== 10. pydantic 自定义校验器 ===")
    try:
        from pydantic import BaseModel, field_validator, model_validator, ConfigDict
    except ImportError:
        print("  [注意] pydantic 未安装，跳过。")
        return

    class Order(BaseModel):
        # 禁止额外字段，类似 Jackson 的 FAIL_ON_UNKNOWN_PROPERTIES
        model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

        item: str
        quantity: int
        unit_price: float

        @field_validator("quantity")
        @classmethod
        def quantity_positive(cls, v: int) -> int:
            if v <= 0:
                raise ValueError("数量必须为正数")
            return v

        @model_validator(mode="after")
        def check_total(self):
            # 跨字段校验：总价不能超过阈值
            if self.quantity * self.unit_price > 100000:
                raise ValueError("订单金额超限，需要人工审核")
            return self

        @property
        def total(self) -> float:
            return self.quantity * self.unit_price

    o = Order(item="  显示器  ", quantity=2, unit_price=1299.0)
    print(f"  合法订单: item={o.item!r}, total={o.total}")

    from pydantic import ValidationError

    for bad in [{"item": "x", "quantity": 0, "unit_price": 1.0},
                {"item": "x", "quantity": 1, "unit_price": 200000.0},
                {"item": "x", "quantity": 1, "unit_price": 1.0, "unknown": 1}]:
        try:
            Order(**bad)
            print(f"  意外通过: {bad}")
        except ValidationError as e:
            print(f"  拦截 {bad} -> {e.errors()[0]['msg']}")
    print("  [Java 对比] @Valid + 自定义 ConstraintValidator，但写法紧凑得多")


# =============================================================================
# 第六部分：选型对照表
# =============================================================================

def print_cheatsheet():
    """HTTP 客户端 / 模板 / 校验 选型速查。"""
    print("\n=== 11. 选型速查表 ===")
    rows = [
        ("场景", "推荐", "Java 对应"),
        ("同步调用少量 API", "requests", "OkHttp / RestTemplate"),
        ("同步 + 异步统一", "httpx", "HttpClient / WebClient"),
        ("高并发异步客户端", "aiohttp / httpx.AsyncClient", "WebClient / Netty"),
        ("HTML 模板渲染", "Jinja2", "Thymeleaf / FreeMarker"),
        ("配置 / 请求体校验", "pydantic", "Bean Validation / Jackson"),
        ("Web API 框架", "FastAPI（基于 pydantic）", "Spring WebFlux / MVC"),
    ]
    widths = [max(len(str(r[i])) for r in rows) for i in range(3)]
    for idx, row in enumerate(rows):
        line = "  " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(line)
        if idx == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def main():
    print("=" * 60)
    print("Python HTTP 客户端 / 模板 / 校验 类库演示")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 60)

    demo_requests_basic()
    demo_requests_session_and_retry()
    demo_requests_error_handling()
    demo_httpx_sync_and_async()
    demo_aiohttp_client()
    demo_aiohttp_server_style()
    demo_jinja2_basic()
    demo_jinja2_inheritance()
    demo_pydantic_model()
    demo_pydantic_validator()
    print_cheatsheet()

    print("\n" + "=" * 60)
    print("所有 demo 运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
