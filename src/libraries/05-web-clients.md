# HTTP 客户端与模板

服务端框架之外，Python 项目最常用的两件"周边"是**调用外部 HTTP 服务**和**渲染 HTML 模板**，
再外加一个无处不在的数据校验层。本章覆盖 `requests` / `httpx` / `aiohttp` 三个 HTTP 客户端、
Jinja2 模板引擎，以及 pydantic 数据校验模型。

对 Java 开发者而言，这一章的映射关系异常干净：

| Python 工具 | Java 对应 | 适用场景 |
|-------------|-----------|----------|
| `requests` | OkHttp / Apache HttpClient / `RestTemplate` | 同步调用，脚本与后台任务 |
| `httpx` | Java 11 `HttpClient` + `WebClient` | 同步/异步统一 API，支持 HTTP/2 |
| `aiohttp` | Netty（客户端 + 服务端） | 高并发异步，客户端与服务端同栈 |
| `Jinja2` | Thymeleaf / FreeMarker / Velocity | 服务端渲染、代码生成 |
| `pydantic` | Jackson + Hibernate Validator | 请求体/配置校验、序列化 |

> [示例](../code/libraries/05_web_clients.py)

> [要点] 本节所有 demo **不发真实网络请求**。`requests` 用 `unittest.mock` 打桩，
> `httpx` 用 `MockTransport`，`aiohttp` 用自建本地回环服务器——这是 Python 测试的常规做法，
> 相当于 Java 里用 `MockWebServer` / `MockRestServiceServer`。

## requests：同步 HTTP 客户端的"人类友好"版本

`requests` 是 Python 最流行的同步客户端。它把 Java 里 `HttpRequest.newBuilder()...build()` 的冗长
收敛成一次函数调用——这也是它被称为"human-friendly"的原因。

### 基本用法

```python
import requests

resp = requests.get(
    "https://api.example.com/users/1",
    params={"include": "profile"},        # 自动拼 query string 并做 URL 编码
    headers={"Accept": "application/json"},
    timeout=5,                            # 必须显式设置，否则可能永久挂起
)
print(resp.status_code, resp.json())

resp = requests.post(
    "https://api.example.com/users",
    json={"name": "Bob"},                 # 自动序列化 + 设置 Content-Type: application/json
    timeout=5,
)
```

`params=` 对应 `UriBuilder.queryParam`（自动 URL 编码），`json=` 自动序列化并设置 `Content-Type`，
`resp.json()` 对应 `objectMapper.readTree(...)`（失败时抛 `JSONDecodeError`，不做类型映射）。

> ⚠️ **不设 `timeout` 是 requests 最经典的生产事故**：默认值是 `None`（无限等待）。
> Java 的 `HttpClient` 也有类似坑，但 OkHttp 默认有超时。永远显式传 `timeout`，或给 `Session` 设默认值。

> [requests 基本用法](../code/libraries/05_web_clients.py#L32-L80)

```python
{{#include ../code/libraries/05_web_clients.py:32:80}}
```

### Session 与重试

`Session` ≈ OkHttp 的 `OkHttpClient` 实例：持有连接池、默认请求头、Cookie 和重试策略。

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
session.headers.update({"User-Agent": "py-learning/1.0"})

retry = Retry(
    total=3,
    backoff_factor=0.5,                   # 指数退避：0.5s → 1s → 2s
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

`Session` ≈ `OkHttpClient`，`session.headers.update(...)` ≈ OkHttp 统一加头的 `Interceptor`，
`Retry` ≈ Spring Retry 的 `@Retryable` / Resilience4j，`HTTPAdapter` 的连接池 ≈
`PoolingHttpClientConnectionManager`。

> ⚠️ 两个坑：
> 1. **每次请求都 `requests.get(...)` 会新建连接池并丢弃**，高并发下会耗尽端口（TIME_WAIT）。
>    Java 侧也不会为每次调用 new 一个 `OkHttpClient`，道理一样。
> 2. `Retry` 的 **`allowed_methods` 默认只含幂等 GET**（新版）；示例里加入 `POST` 是有意为之，
>    仅在业务确认幂等（或配合幂等键）时才这样做，否则重试会造成重复下单。

> [Session 与重试](../code/libraries/05_web_clients.py#L83-L113)

```python
{{#include ../code/libraries/05_web_clients.py:83:113}}
```

### 错误处理

```python
try:
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()        # 4xx/5xx 才抛 HTTPError
except requests.exceptions.Timeout:          # 连接/读取超时
    ...
except requests.exceptions.ConnectionError:  # DNS 失败 / 拒绝连接
    ...
except requests.exceptions.HTTPError as e:
    print(e.response.status_code)            # 非 2xx
```

| 异常 | Java 对应 |
|------|-----------|
| `RequestException`（基类） | `IOException` |
| `Timeout` / `ConnectTimeout` / `ReadTimeout` | `SocketTimeoutException` |
| `ConnectionError` | `ConnectException` / `UnknownHostException` |
| `HTTPError` | 无——Java 需自己判断 `statusCode()` |

> ⚠️ 与 Java 最大的差异：**HTTP 状态码默认不抛异常**。`404`、`500` 都只是"正常返回"，
> 必须显式调用 `raise_for_status()` 或检查 `status_code`。Spring 的 `RestTemplate` 默认会抛
> `HttpStatusCodeException`，这是两个生态最容易混淆的行为差异之一。

> [requests 基本用法](../code/libraries/05_web_clients.py#L32-L80) · [Session 与重试](../code/libraries/05_web_clients.py#L83-L113)
 · [错误处理](../code/libraries/05_web_clients.py#L116-L138)

## httpx：同步 + 异步统一 API

`httpx` 是 `requests` 的现代替代品，核心卖点：**同步和异步客户端几乎完全同构**，
且支持 HTTP/2。对应 Java 11 `HttpClient`（`send` / `sendAsync`）。

```python
import httpx

with httpx.Client(base_url="https://api.test") as client:
    r = client.get("/ping")                 # 同步

async with httpx.AsyncClient(base_url="https://api.test") as client:
    tasks = [client.get(f"/item/{i}") for i in range(3)]
    results = await asyncio.gather(*tasks)  # 真并发
```

`Client` 对应 `HttpClient`，`AsyncClient` 对应 `WebClient` / `sendAsync`，
`asyncio.gather(*tasks)` 对应 `Flux.merge` / `CompletableFuture.allOf`（并发发起、等全部完成），
`MockTransport` 对应 `MockWebServer`。

> [要点] 选型上很直接：**项目里已经有 `async` 代码就用 `httpx.AsyncClient`，纯脚本用 `Client`**。
> 比 `requests` + `aiohttp` 混用两个库更省心——一套 API 同时覆盖两个世界。

> [httpx 同步与异步](../code/libraries/05_web_clients.py#L147-L188)

```python
{{#include ../code/libraries/05_web_clients.py:147:188}}
```

## aiohttp：异步客户端 + 服务端

`aiohttp` 除了客户端还自带服务端，定位更接近 Netty：一个库既能当 `HttpClient` 也能当 `HttpServer`。

```python
async with aiohttp.ClientSession() as session:
    async with session.get(url, params={"name": "x"}) as resp:
        data = await resp.json()

app = web.Application()
app.router.add_get("/hello", hello)
web.run_app(app, host="127.0.0.1", port=8080)
```

`ClientSession` 对应 `WebClient` / Netty `HttpClient` 的 Channel 池，`web.Application()` +
`router.add_get` 对应 Netty `ServerBootstrap` + `Router`，`web.json_response` 对应 `ResponseEntity` + Jackson。

> ⚠️ 与 `requests.Session` 同理：**`ClientSession` 要在应用生命周期内复用**，
> 每个请求新建一个会导致连接池反复重建。另外 aiohttp 与其他异步库常常"不共享事件循环"，
> 混用 `httpx.AsyncClient` 和 aiohttp 时要确认在同一个 loop 内。

> [aiohttp 客户端](../code/libraries/05_web_clients.py#L190-L236) · [aiohttp 服务端写法](../code/libraries/05_web_clients.py#L239-L260)

## Jinja2：模板引擎

Jinja2 ≈ Thymeleaf / FreeMarker。它不仅服务于 Flask/Django 之外，还被广泛用于
配置生成（Ansible）、代码脚手架（Cookiecutter）等"非 Web"场景。

### 基本语法

```python
from jinja2 import Environment, DictLoader

templates = {"page.html": """
<h1>Hello {{ name | title }}</h1>
<ul>{% for item in items %}
  <li>{{ loop.index }}. {{ item.name }} - {{ "%.2f" | format(item.price) }}</li>
{% endfor %}</ul>
{% if items %}<p>共 {{ items | length }} 件</p>{% endif %}
"""}
env = Environment(loader=DictLoader(templates), autoescape=True)
html = env.get_template("page.html").render(name="alice", items=[...])
```

`{{ name }}` ≈ Thymeleaf `th:text="${name}"` / FreeMarker `${name}`，`{% for %}` ≈ `th:each`，
`{% if %}` ≈ `th:if`，`| title`、`| length` 这类过滤器 ≈ `#strings` 工具对象，`loop.index` ≈ `iterStat.index`。

> ⚠️ **`autoescape=True` 必须开**。Jinja2 的 `Environment` 默认 `autoescape=False`，
> 而 Thymeleaf 默认是转义的。关掉它等于直接把 XSS 漏洞写进模板里。
> 只有生成非 HTML 文件（纯文本配置、代码）时才应该关闭。

> [Jinja2 基本用法](../code/libraries/05_web_clients.py#L269-L306)

```python
{{#include ../code/libraries/05_web_clients.py:269:306}}
```

### 模板继承与宏

```python
# base.html
# <body>{% block content %}默认内容{% endblock %}</body>
# child.html
# {% extends "base.html" %}
# {% macro badge(text, color) %}<span class="{{ color }}">{{ text }}</span>{% endmacro %}
# {% block content %}{{ badge("NEW", "green") }}{% endblock %}
```

`{% extends %}` + `{% block %}` ≈ `th:replace` + `layout:fragment`，`{% macro %}` ≈ `th:fragment`，
`{% include %}` ≈ `th:insert`。Thymeleaf 是"片段替换"，Jinja2 是 OO 式的"继承 + 覆写块"——
前者更贴近 HTML 原生结构，后者更贴近 Java 的模板方法模式。

> [模板继承示例](../code/libraries/05_web_clients.py#L309-L342)

```python
{{#include ../code/libraries/05_web_clients.py:309:342}}
```

## pydantic：数据校验与序列化

pydantic ≈ Jackson（序列化）+ Hibernate Validator（校验）+ Lombok（少写样板代码）。
它是 FastAPI 的基石，也是 Python 生态里事实上的"数据契约"标准。

### 模型定义与自动转换

```python
from pydantic import BaseModel, Field, ValidationError

class Address(BaseModel):
    city: str
    street: str = ""

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=20)
    age: int = Field(ge=0, le=150)
    email: str | None = None
    tags: list[str] = Field(default_factory=list)   # 可变默认值必须用 factory
    address: Address | None = None

u = User(id="42", name="Alice", age=30)     # "42" 自动转成 int
u.model_dump()                              # → dict
u.model_dump_json()                         # → JSON 字符串
```

| pydantic | Java 对应 |
|----------|-----------|
| `BaseModel` 子类 | DTO `record` / POJO |
| `Field(min_length=1, ge=0)` | `@Size(min=1)` + `@Min(0)` |
| `str \| None = None` | `@Nullable String` / `Optional<String>` |
| `Field(default_factory=list)` | 类字段初始化为 `new ArrayList<>()` |
| `model_dump()` / `model_dump_json()` | Jackson `writeValueAsString` |
| `ValidationError`（聚合所有字段错误） | `MethodArgumentNotValidException` |

> ⚠️ 两个 Java 思维都要调整的点：
> 1. **校验在构造时发生**。`User(id=1, name="", age=-5)` 会**立刻抛 `ValidationError`**，
>    不存在"先构造对象再 `validator.validate()`"的第二步。这也意味着校验不可"跳过"。
> 2. **默认做类型强转**（`"42"` → `42`、`1` → `True`）。要严格类型请用 `model_config = ConfigDict(strict=True)`。

> [pydantic 模型](../code/libraries/05_web_clients.py#L344-L380)

```python
{{#include ../code/libraries/05_web_clients.py:344:380}}
```

### 自定义校验器与模型配置

`@field_validator` ≈ 字段级 `ConstraintValidator`，`@model_validator(mode="after")` ≈ 类级跨字段约束注解，
`extra="forbid"` ≈ Jackson 的 `FAIL_ON_UNKNOWN_PROPERTIES = true`，`str_strip_whitespace` ≈ 自定义
`@JsonDeserialize` / `StringTrimmerEditor`。

> [自定义校验器](../code/libraries/05_web_clients.py#L383-L436)

```python
{{#include ../code/libraries/05_web_clients.py:383:436}}
```

## 综合选型矩阵

| 场景 | 推荐 | Java 对应 |
|------|------|-----------|
| 同步调用少量 API（脚本、定时任务） | `requests` | OkHttp / `RestTemplate` |
| 同步 + 异步统一、要 HTTP/2 | `httpx` | `HttpClient` / `WebClient` |
| 高并发异步客户端 | `httpx.AsyncClient` / `aiohttp` | `WebClient` / Netty |
| 需要客户端和服务端同一套技术栈 | `aiohttp` | Netty |
| HTML 服务端渲染 / 代码生成 | `Jinja2` | Thymeleaf / FreeMarker |
| 请求体、配置文件校验 | `pydantic` / `pydantic-settings` | Bean Validation + Jackson |
| 需要 API 框架（自动文档） | FastAPI（基于 pydantic） | Spring WebFlux / MVC |

> [选型速查表代码](../code/libraries/05_web_clients.py#L438-L455)

```python
{{#include ../code/libraries/05_web_clients.py:438:455}}
```

给 Java 开发者的三条速记：

1. **客户端选型看并发模型**，不看功能列表：`requests` 同步、`httpx` 双模、`aiohttp` 纯异步。
2. **别忘 `timeout` 与 `raise_for_status()`**——Python 客户端的默认值比 Java 更"宽松"，也更危险。
3. **pydantic 同时替代了 Jackson 和 Bean Validation**，别再去找 `@Valid` 等价物，构造函数本身就是校验入口。

服务端框架的用法见上一章 [Web 框架](./04-web-frameworks.md)。

## 小结

- **`requests`**：API 极简，默认连接池需用 `Session` 复用，`timeout` 必须显式设置
- **HTTP 状态码默认不抛异常**：与 `RestTemplate` 相反，要主动 `raise_for_status()`
- **`httpx`**：一套 API 同时覆盖同步与异步，是最省心的现代选择
- **`aiohttp`**：客户端 + 服务端同栈，`ClientSession` 全局复用
- **Jinja2**：`Environment` 默认**不转义**，务必 `autoescape=True`（与 Thymeleaf 默认相反）
- **pydantic**：构造即校验、默认强转类型；`Field` 替代注解、`model_validator` 替代类级约束

> 📁 [查看完整代码](../code/libraries/05_web_clients.py)
