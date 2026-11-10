# Web 框架（FastAPI / Flask / Django）

Python 生态的三大 Web 框架恰好对应 Spring 的三条技术路线：FastAPI ≈ Spring WebFlux（异步 + 类型驱动），
Flask ≈ Spring MVC 轻量版（同步、中间件式扩展），Django ≈ Spring Boot 全栈（ORM + Admin + 模板一体化）。

本章不重复讲 HTTP 是什么，而是聚焦 **Python 与 Spring 的设计理念差异**，以及 Java 开发者迁移时最容易踩的坑。

> [示例](../code/libraries/04_web_frameworks.py)

## 总览：三个框架与 Spring 的对应关系

| Python 工具 | Java 对应 | 适用场景 |
|-------------|-----------|----------|
| FastAPI | Spring WebFlux（+ Jackson + Bean Validation） | 纯 API 服务，异步 I/O 密集 |
| Flask | Spring MVC（`@RestController` + 少量拦截器） | 中小型站点、微服务、胶水脚本型服务 |
| Django | Spring Boot 全栈（JPA + Thymeleaf + 类 Admin 后台） | 内容管理、后台系统、快速交付整站 |

## FastAPI：类型即契约

FastAPI 建立在 Starlette（ASGI 服务器/路由）+ Pydantic（数据模型）之上。
它把 Java 里分散在注解上的信息（路由、参数绑定、校验、文档）**全部收敛到函数签名和类型注解**里。

> ⚠️ FastAPI 与 Spring 最大的理念差异：Spring 的 `@RequestParam` / `@RequestBody` / `@PathVariable`
> 是显式声明的；FastAPI 是**按签名推断**的——路径里有 `{item_id}` 就是路径参数、类型是 Pydantic 模型就是请求体、
> 其余普通参数就是查询参数。推断规则不懂，就会出现"参数怎么从 body 来的？"这类困惑。

### 最小应用

```python
from fastapi import FastAPI

app = FastAPI(title="MyAPI", version="0.1.0")

@app.get("/")
def root():
    return {"msg": "hello, FastAPI"}
```

`app` 相当于 `@SpringBootApplication` 主类 + 内嵌容器配置。`return` 一个 `dict` 就会被自动 JSON 序列化，
等价于 `@RestController` 返回 POJO。本地起服务用 `uvicorn 04_web_frameworks:app --reload`（≈ `mvn spring-boot:run`）。

> [FastAPI 最小应用](../code/libraries/04_web_frameworks.py#L46-L82)

```python
{{#include ../code/libraries/04_web_frameworks.py:46:82}}
```

### 路径参数与查询参数

```python
@app.get("/items/{item_id}")
def get_item(item_id: int):        # 路径参数：名字匹配 + 类型注解自动转换校验
    return {"item_id": item_id}

@app.get("/search")
def search(q: str, limit: int = 10):   # 不在路径中的参数 = 查询参数；有默认值 = 可选
    return {"q": q, "limit": limit}
```

`item_id: int` 对应 `@PathVariable Long itemId`；`q: str, limit: int = 10` 对应
`@RequestParam(required=false, defaultValue="10")`（`None` 默认值即表示可选，无注解则一律是字符串）。

> ⚠️ 类型转换失败时 FastAPI 返回 **422 Unprocessable Entity**，而不是 Spring 的 400
> （`MethodArgumentTypeMismatchException`）。如果前端/网关按 400 做了特殊处理，迁移时会出问题。

> [路径与查询参数](../code/libraries/04_web_frameworks.py#L85-L125)

```python
{{#include ../code/libraries/04_web_frameworks.py:85:125}}
```

### 请求体：Pydantic 模型

FastAPI 不写 `@RequestBody`，参数类型是 `BaseModel` 子类即代表"从 JSON 请求体解析"：

```python
@app.post("/items")
def create_item(item: Item): ...      # 参数类型是 BaseModel 子类 -> 自动从 JSON 请求体解析
```

> ⚠️ Pydantic 默认开启**宽松类型转换**：传 `"42"` 会变成 `42`、传 `"1"` 会变成 `True`。
> 这是 Java 开发者最不习惯的地方——Jackson 默认同样宽松，但 Bean Validation 不做转换。
> 需要严格模式时在 `model_config` 中设置 `strict=True`。

> [请求体示例](../code/libraries/04_web_frameworks.py#L128-L166)

```python
{{#include ../code/libraries/04_web_frameworks.py:128:166}}
```

### 响应模型 response_model

`response_model` 控制"输出层的视图"，既能过滤敏感字段，也能生成准确的 OpenAPI schema：

```python
class UserInDB(BaseModel):
    id: int
    name: str
    password: str          # 敏感字段

class UserOut(BaseModel):
    id: int
    name: str

@app.get("/users/{uid}", response_model=UserOut)
def get_user(uid: int):
    return UserInDB(id=uid, name="Alice", password="secret123")   # password 被自动剔除
```

对应关系：`response_model` ≈ **DTO + `@JsonView` + `@JsonIgnore`** 三合一。
Spring 通常要维护两套 DTO 或加 `@JsonView(UserOut.class)`；FastAPI 只需声明一个返回类型，
框架在序列化时按 `UserOut` 字段白名单筛选。

> ⚠️ `response_model` 是"白名单过滤"，不是"深拷贝校验"。它作用于输出，不会阻止 handler 内部拿到完整对象。
> 另外它也会把不一致的类型（如 `"1"` → `1`）按模型重新转换一遍。

> [response_model 示例](../code/libraries/04_web_frameworks.py#L169-L204)

```python
{{#include ../code/libraries/04_web_frameworks.py:169:204}}
```

### `async def` vs `def`：最容易误解的一点

这是本章**最重要**的一节。同一个框架里两种路由，底层执行模型完全不同：

```python
import asyncio

@app.get("/async-data")
async def async_data():
    await asyncio.sleep(0.01)          # 在事件循环中挂起，期间可处理其他请求
    return {"data": "fetched asynchronously"}

@app.get("/sync-data")
def sync_data():                       # 普通 def：FastAPI 自动丢进线程池执行
    return {"data": "fetched synchronously"}
```

| 路由写法 | 执行位置 | 并发方式 | Spring 对应 |
|----------|----------|----------|-------------|
| `async def` + `await` | 事件循环（单线程）内 | 协程切换，非阻塞 | **WebFlux**（Netty EventLoop + `Mono`/`Flux`） |
| `def`（普通函数） | 外部 threadpool（默认 Starlette 约 40 线程） | 线程池阻塞 | **Spring MVC**（Tomcat 工作线程） |

> ⚠️ 两个经典坑：
> 1. **在 `async def` 里调用阻塞库**（`requests.get`、`psycopg2`、`time.sleep`）会**卡死整个事件循环**，
>    所有并发请求一起停摆——等价于在 WebFlux 的 EventLoop 上做阻塞调用。
> 2. **在 `def` 里写 CPU 密集计算**会占满线程池，请求排队；Python 有 GIL，线程池也解决不了 CPU 瓶颈，
>    这类任务应该丢给进程池（`run_in_executor` 或 Celery）。
>
> 一句话选型：**I/O 密集且有异步驱动（asyncpg / httpx.AsyncClient / aioredis）→ `async def`；
> 只有同步库（requests / 同步 ORM）→ 老实写 `def`，让框架帮你放线程池。**

> [async / sync 路由对比](../code/libraries/04_web_frameworks.py#L207-L238)

```python
{{#include ../code/libraries/04_web_frameworks.py:207:238}}
```

### 依赖注入 Depends

FastAPI 的 `Depends` 处理的是**请求级依赖**（依据当前 HTTP 请求参数构造对象），
而 Spring 的 `@Autowired` 处理的是**应用级单例 Bean**——这是两者最本质的区别。

```python
from fastapi import Depends, Header, HTTPException

def get_token(authorization: str = Header(...)):     # 从请求头读取
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的 token")
    return authorization[len("Bearer "):]

def get_current_user(token: str = Depends(get_token)):   # 依赖可以嵌套
    return {"name": "Alice", "token": token}

@app.get("/me")
def me(user: dict = Depends(get_current_user)):      # 整条依赖链自动解析
    return user
```

`Depends(func)` 注入的是**函数调用结果**而非受管 Bean；依赖可以嵌套（自动解析依赖图，同一请求内默认只调用
一次），也可以用 `yield` 依赖做 setup/teardown（≈ `try/finally` 的 `@Around` 切面）。`Header(...)` / `Query(...)`
则对应 `@RequestHeader` / `@RequestParam`。

> [要点] 想让依赖"全局生效"（如鉴权），Spring 用拦截器/过滤器；FastAPI 用
> `FastAPI(dependencies=[Depends(...)])` 挂在应用或路由组上，同样不需要写注解。

> [依赖注入示例](../code/libraries/04_web_frameworks.py#L241-L294)

```python
{{#include ../code/libraries/04_web_frameworks.py:241:294}}
```

### 中间件

```python
import time

@app.middleware("http")
async def timing_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)          # 交棒给下一个中间件 / 路由
    response.headers["X-Process-Time"] = f"{time.time() - start:.4f}"
    return response
```

`@app.middleware("http")` ≈ `HandlerInterceptor` / `OncePerRequestFilter`，`call_next(request)` ≈
`chain.doFilter(req, resp)`。

> ⚠️ 中间件必须是 `async def`（因为 `call_next` 本身是协程），且这里**没有**"自动线程池"保护：
> 在中间件里做阻塞调用同样会卡死事件循环。

> [中间件示例](../code/libraries/04_web_frameworks.py#L297-L329)

```python
{{#include ../code/libraries/04_web_frameworks.py:297:329}}
```

### 异常处理

`raise HTTPException(404, ...)` ≈ `throw new ResponseStatusException(HttpStatus.NOT_FOUND)`；
`@app.exception_handler(MyError)` ≈ `@ControllerAdvice` + `@ExceptionHandler(MyError.class)`。

> ⚠️ `@app.exception_handler` 按 `isinstance` 匹配异常类，没有 Spring 的 `@Order`/`@Primary` 那套优先级控制。

> [异常处理示例](../code/libraries/04_web_frameworks.py#L332-L378)

```python
{{#include ../code/libraries/04_web_frameworks.py:332:378}}
```

### 自动文档与 CORS

`/openapi.json`、`/docs`、`/redoc` ≈ springdoc-openapi 的 `/swagger-ui.html`，路由上的 `summary=` ≈
`@Operation(summary=...)`；`app.add_middleware(CORSMiddleware, ...)` ≈ `WebMvcConfigurer#addCorsMappings`。

> [要点] 文档"零配置"的前提是**你用了类型注解**。写着 `def f(x)` 的函数在文档里就是个匿名参数——
> 这也是 FastAPI 把"类型提示当作核心"的根本原因。

> [自动文档](../code/libraries/04_web_frameworks.py#L381-L411) · [CORS](../code/libraries/04_web_frameworks.py#L414-L462)

### 完整 CRUD 示例

```python
@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(todo: TodoCreate): ...

@app.get("/todos", response_model=list[TodoOut])
def list_todos(): ...

@app.put("/todos/{tid}", response_model=TodoOut)
def update_todo(tid: int, todo: TodoCreate): ...
```

`@app.post` + `status_code=201` ≈ `@PostMapping` + `@ResponseStatus(CREATED)`，
`response_model=list[TodoOut]` ≈ `List<TodoOut>`，示例里的 `dict` 只是 JPA Repository 的内存替身。

> [CRUD 完整示例](../code/libraries/04_web_frameworks.py#L465-L580)

```python
{{#include ../code/libraries/04_web_frameworks.py:465:580}}
```

## Flask：极简同步框架

Flask 是"微框架"：核心只有路由 + 请求对象 + 模板，其余能力全靠扩展。
它对应的是一个**没有 Spring 容器依赖注入、没有注解驱动**的 Spring MVC——或者更准确说，
接近 Java 里的 Javalin / Spark 风格。

### 最小应用与路由

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, Flask!"          # 直接返回字符串 = text/html

@app.route("/items/<int:item_id>")  # <int:...> 是路径转换器
def get_item(item_id):
    return f"item_id={item_id}"
```

`@app.route("/x")` ≈ `@RequestMapping("/x")`，`<int:item_id>` ≈ `@PathVariable Integer itemId`，
`app.test_client()` ≈ `MockMvc`，返回 `str` ≈ `@ResponseBody String`。

> ⚠️ Flask 的转换器让"类型校验"发生在**路由匹配阶段**：`/items/abc` 会直接 404（根本匹配不上），
> 而不是 400。这点和 FastAPI 的 422、Spring 的 400 都不同。

> [Flask 最小应用](../code/libraries/04_web_frameworks.py#L583-L610) · [路由参数](../code/libraries/04_web_frameworks.py#L613-L637)
 · [模板渲染](../code/libraries/04_web_frameworks.py#L640-L662)

### 模板渲染：render_template

`render_template("hello.html", name=name)` + Jinja2 ≈ `ModelAndView` + Thymeleaf。
Jinja2 的语法见下一章 [HTTP 客户端与模板](./05-web-clients.md)。

### request / jsonify

```python
from flask import request, jsonify

@app.route("/search")
def search():
    q = request.args.get("q", "")
    page = request.args.get("page", "1", type=int)
    return jsonify(q=q, page=page)

@app.route("/echo", methods=["POST"])
def echo():
    return jsonify(received=request.get_json())
```

`request.args.get("q")` ≈ `@RequestParam`，`request.get_json()` ≈ `@RequestBody Map<String,Object>`，
`jsonify(...)` ≈ `@ResponseBody` + Jackson，返回 `(jsonify(...), 404)` ≈ `ResponseEntity.notFound()`。

> ⚠️ Flask 是**全局请求上下文**（`request` 是个代理对象，靠线程/协程局部变量绑定），
> 不是方法参数注入。它能工作，但静态分析器和类型检查器都看不到它的来源——这是典型的 Python "魔法"。

> [request / jsonify 示例](../code/libraries/04_web_frameworks.py#L665-L697)

```python
{{#include ../code/libraries/04_web_frameworks.py:665:697}}
```

### 重定向与 url_for、Blueprint

```python
from flask import redirect, url_for

@app.route("/old")
def old():
    return redirect(url_for("new"))   # 按函数名反查 URL，而非硬编码

user_bp = Blueprint("users", __name__, url_prefix="/api/users")
@user_bp.route("/")
def list_users():
    return jsonify(users=["Alice", "Bob"])
app.register_blueprint(user_bp)
```

`url_for("new")` ≈ `MvcUriComponentsBuilder.fromMappingName(...)`，`redirect(...)` ≈ `return "redirect:/new"`，
`Blueprint(url_prefix=...)` ≈ Controller 类上的 `@RequestMapping("/api/users")` 前缀，
`register_blueprint` ≈ 组件扫描。

> [要点] Blueprint 只是**路由分组 + 前缀**，不提供 DI、AOP、事务——想"模块化"得更像 Spring，
> 需要自己组装扩展（如 Flask-SQLAlchemy、Flask-Injector）。

> [重定向示例](../code/libraries/04_web_frameworks.py#L700-L724) · [Blueprint 示例](../code/libraries/04_web_frameworks.py#L727-L757)
 · [Flask 博客 API](../code/libraries/04_web_frameworks.py#L760-L827)

### 完整博客 API 的启示

Flask 版 CRUD 里**没有校验层**：所有 `title 必须存在` 这类判断都是手写 `if`，状态码用
`return obj, 201` 元组表达。缺的正是 pydantic ≈ Bean Validation 那一层——这正是 FastAPI 相对 Flask 的最大增量。

## Django：全栈 "Batteries Included"

Django 是唯一开箱即包含 ORM、迁移、Admin、模板、认证的框架，定位最接近 Spring Boot 全家桶。
示例以注释形式展示结构（Django 项目是多文件布局，不适合单文件运行）。

```python
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

| Django | Spring 对应 |
|--------|-------------|
| `models.Model` + `CharField` | `@Entity` + JPA 字段（`@Column`） |
| `auto_now_add=True` | `@CreationTimestamp` / `@PrePersist` |
| `get_object_or_404` | `orElseThrow(...)` → `@ControllerAdvice` 转 404 |
| `ListView` 类视图 | 基于继承的 `@Controller`（比注解式更"重"） |
| `urls.py` 的 `path()` | `@RequestMapping` / 路由表 |
| `@admin.register` | **无直接等价物**（JHipster 生成的 CRUD 页面最接近） |
| `makemigrations` / `migrate` | **Flyway / Liquibase**（但由模型自动生成脚本） |
| 模板 `{{ post.title }}` | Thymeleaf `th:text="${post.title}"` |

> ⚠️ Django 的两个 Java 思维冲突点：
> 1. **ORM 默认不自动迁移到生产**——`makemigrations` 自动生成迁移脚本，看似省事，
>    但团队协作时迁移文件要进版本库，等价于 Flyway 脚本，别当成"数据库自己变了"。
> 2. **MTV ≠ MVC 的命名**：Django 的 "View"（`views.py`）实际是 Spring 的 Controller，
>    Django 的 "Template" 才是 View。跟 Java 同事沟通时直接说 Controller/Template 更准确。

> [Django 概览](../code/libraries/04_web_frameworks.py#L868-L969)

```python
{{#include ../code/libraries/04_web_frameworks.py:868:969}}
```

## 综合选型矩阵

| 维度 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| 异步模型 | 原生 ASGI，`async def` 路由 | WSGI 同步（需 Quart/gevent） | 3.0+ 支持 async 视图 |
| 依赖注入 | `Depends`（请求级） | 无内置（扩展） | 无（自实现/扩展） |
| 数据校验 | pydantic 强依赖 | 无（手写/第三方） | Form / DRF Serializer |
| ORM | 无（自选 SQLAlchemy） | 无（自选 SQLAlchemy） | 内置 Django ORM |
| 数据库迁移 | Alembic（配 SQLAlchemy） | Alembic / Flask-Migrate | 内置 migrations |
| 自动 API 文档 | Swagger / ReDoc 内置 | 需扩展（flasgger） | 需 DRF + drf-spectacular |
| 模板引擎 | 无（纯 API） | Jinja2 | Django Templates |
| Admin 后台 | 无 | 无 | 内置 |
| 学习曲线 | 低（类型驱动，反馈快） | 最低 | 中（概念多、约定多） |
| Java 对应 | Spring WebFlux | Spring MVC 轻量版 | Spring Boot 全栈 |
| 适合场景 | 现代 API 服务、微服务 | 小站点、脚本型服务、原型 | 内容管理、后台系统、整站交付 |

> [框架对比代码](../code/libraries/04_web_frameworks.py#L971-L1001)

```python
{{#include ../code/libraries/04_web_frameworks.py:971:1001}}
```

给 Java 团队的落地建议：

- **对外 API / 微服务**：选 FastAPI。类型注解 + OpenAPI 一体化最接近 Spring 开发者的心智，
  且 `TestClient` 可以直接当集成测试用。
- **要"接管"的存量业务系统、后台管理**：选 Django。Admin 能省掉大量 CRUD 页面，
  相当于白送你一个简易版的管理后台。
- **少量接口 / 内嵌脚本服务**：选 Flask。依赖最少，几行代码就能跑，
  不要让框架替你决定项目结构。

无论选哪个，**HTTP 客户端、模板引擎、数据校验**这三件"周边"几乎一定还会用到，
见下一章 [HTTP 客户端与模板](./05-web-clients.md)。

## 小结

- **FastAPI 用类型注解驱动一切**：路由参数、校验、文档都来自签名，等价 Spring WebFlux + Jackson + Bean Validation
- **`async def` 跑事件循环，`def` 跑线程池**：对应 WebFlux vs Spring MVC；在 `async def` 里做阻塞调用会卡死所有请求
- **`Depends` 是请求级依赖**，`@Autowired` 是应用级单例，两者解决的问题不同
- **`response_model` 是输出白名单**，替代 DTO + `@JsonView`/`@JsonIgnore`
- **Flask 没有校验层和 DI**，像无容器的 Spring MVC，适合小而快
- **Django 是全家桶**，ORM + Admin + 迁移最接近 Spring Boot，但约定多、学习曲线最陡
- 三个框架的失败状态码细节不同（422 / 404 / 400），迁移时注意前后端契约

> 📁 [查看完整代码](../code/libraries/04_web_frameworks.py)
