"""
04 - Web 框架（FastAPI / Flask / Django）
========================================
本节目标：
  1. FastAPI：现代异步 Web 框架（重点讲解）
  2. Flask：经典轻量同步 Web 框架
  3. Django：全栈 MTV 框架（概览，注释为主）

面向有丰富 Java 经验的开发者，每个概念都给出 Java 对比说明。

对应 Java 概念：
  - FastAPI   ≈ Spring Boot + Spring WebFlux（异步 + 注解路由）
  - Flask     ≈ Spring MVC（同步 + 轻量）
  - Django    ≈ Spring Boot 全栈（ORM + Admin + 模板一体化）

注意：
  - FastAPI / Flask 需要安装才能运行示例（pip install fastapi uvicorn / pip install flask）
  - Django 部分以注释展示（项目结构复杂，不适合单文件演示）
  - uvicorn 启动部分用注释说明，不在代码中实际启动服务器（会阻塞）
  - Windows 控制台默认 GBK 编码，避免在 print 中使用 emoji
"""

import sys
import json
from typing import Any


# ===========================================================================
# 第一部分：FastAPI（重点）
# ===========================================================================
# FastAPI 是基于 Starlette + Pydantic 的现代异步 Web 框架。
#
# [Java 对比] Spring Boot
#   - Spring Boot 用 @RestController + @GetMapping 注解定义路由
#   - FastAPI 用 @app.get("/path") 装饰器定义路由
#   - Spring Boot 用 @RequestBody / @PathVariable / @RequestParam 接收参数
#   - FastAPI 直接在函数签名中声明参数类型，自动解析与验证
#   - Spring Boot 用 Jackson 序列化/反序列化 JSON
#   - FastAPI 用 Pydantic 自动完成（且带类型验证）
#   - Spring Boot 用 @Async / WebFlux 支持异步
#   - FastAPI 原生 async def 支持异步
#
# 安装：pip install fastapi uvicorn


def demo_fastapi_minimal():
    """FastAPI 最小应用：创建实例 + 定义路由。"""
    print("\n=== 1. FastAPI 最小应用 ===")
    try:
        from fastapi import FastAPI
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    # 创建应用实例（类似 Spring Boot 的 @SpringBootApplication 主类）
    app = FastAPI(
        title="MyAPI",                # 显示在 Swagger 文档标题
        description="学习用示例 API",  # 文档描述
        version="0.1.0",
    )

    # 定义根路由
    # [Java 对比]
    #   @GetMapping("/")
    #   public Map<String, String> root() { return Map.of("msg", "hello"); }
    @app.get("/")
    def root():
        return {"msg": "hello, FastAPI"}

    # 用 TestClient 在进程内测试（不启动真实服务器，不会阻塞）
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/")
    print(f"  GET / -> {resp.status_code}: {resp.json()}")
    # 验证路由生效
    assert resp.json() == {"msg": "hello, FastAPI"}

    # [说明] 真实部署时用 uvicorn 启动（不要在脚本里调用，会阻塞）：
    #   命令行：uvicorn 04_web_frameworks:app --reload --port 8000
    #   或代码：uvicorn.run(app, host="127.0.0.1", port=8000)
    print("  [说明] 部署命令: uvicorn 04_web_frameworks:app --reload --port 8000")


def demo_fastapi_path_query():
    """FastAPI 路径参数与查询参数。"""
    print("\n=== 2. FastAPI 路径参数 / 查询参数 ===")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # 路径参数：{item_id} 自动绑定到函数参数 item_id
    # [Java 对比] @GetMapping("/items/{itemId}") public Item get(@PathVariable Long itemId)
    @app.get("/items/{item_id}")
    def get_item(item_id: int):  # 类型注解 int -> 自动校验并转换
        return {"item_id": item_id, "type": type(item_id).__name__}

    # 查询参数：函数参数不在路径中 -> 视为查询参数
    # [Java 对比] @RequestParam(required=false, defaultValue="") String q
    @app.get("/search")
    def search(q: str, limit: int = 10):  # limit 有默认值 -> 可选
        return {"q": q, "limit": limit}

    client = TestClient(app)

    # 路径参数自动类型转换
    r1 = client.get("/items/42")
    print(f"  GET /items/42 -> {r1.json()}")

    # 路径参数类型错误时自动返回 422（类似 Spring 的 MethodArgumentTypeMismatch）
    r2 = client.get("/items/abc")
    print(f"  GET /items/abc -> {r2.status_code} (类型校验失败)")

    # 查询参数
    r3 = client.get("/search?q=python&limit=5")
    print(f"  GET /search?q=python&limit=5 -> {r3.json()}")

    # 可选查询参数使用默认值
    r4 = client.get("/search?q=java")
    print(f"  GET /search?q=java -> {r4.json()} (limit 用默认值)")


def demo_fastapi_request_body():
    """FastAPI 请求体：用 Pydantic 模型接收 JSON。"""
    print("\n=== 3. FastAPI 请求体（Pydantic 模型）===")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel, Field
    except ImportError:
        print("  [注意] fastapi/pydantic 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # Pydantic 模型定义请求体结构
    # [Java 对比] class ItemDTO { @NotNull String name; @Min(0) int price; }
    #             配合 @RequestBody ItemDTO item 自动反序列化 + 校验
    class Item(BaseModel):
        name: str = Field(..., min_length=1, max_length=50, description="商品名称")
        price: float = Field(..., gt=0, description="价格，必须大于 0")
        tags: list[str] = Field(default_factory=list, description="标签列表")

    # 声明 Item 类型 -> FastAPI 自动从请求体解析 JSON 并校验
    @app.post("/items")
    def create_item(item: Item):
        return {"created": item.model_dump()}

    client = TestClient(app)

    # 正常请求
    r1 = client.post("/items", json={"name": "Book", "price": 29.9, "tags": ["it", "book"]})
    print(f"  POST 正常 -> {r1.status_code}: {r1.json()}")

    # 校验失败：price 为负数 -> 422
    r2 = client.post("/items", json={"name": "X", "price": -1})
    print(f"  POST price=-1 -> {r2.status_code} (校验失败)")

    # 校验失败：缺少必填字段 name -> 422
    r3 = client.post("/items", json={"price": 10})
    print(f"  POST 缺少 name -> {r3.status_code} (校验失败)")


def demo_fastapi_response_model():
    """FastAPI 响应模型 response_model：过滤输出字段。"""
    print("\n=== 4. FastAPI 响应模型 response_model ===")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
    except ImportError:
        print("  [注意] fastapi/pydantic 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # 内部模型（含敏感字段）
    class UserInDB(BaseModel):
        id: int
        name: str
        password: str  # 敏感字段，不应返回给客户端

    # 对外响应模型（不含 password）
    class UserOut(BaseModel):
        id: int
        name: str

    # response_model=UserOut 会自动过滤掉 password 字段
    # [Java 对比] 用 @JsonIgnore 在序列化时排除字段，或用不同 DTO
    @app.get("/users/{uid}", response_model=UserOut)
    def get_user(uid: int):
        # 内部返回完整数据，FastAPI 按 UserOut 过滤
        return UserInDB(id=uid, name="Alice", password="secret123")

    client = TestClient(app)
    r = client.get("/users/1")
    print(f"  GET /users/1 -> {r.json()}")
    assert "password" not in r.json(), "password 应被过滤"
    print("  [验证] password 字段已被 response_model 过滤")


def demo_fastapi_async():
    """FastAPI 异步路由处理函数。"""
    print("\n=== 5. FastAPI 异步路由 ===")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # async def 定义异步路由，内部可 await 其他协程
    # [Java 对比] WebFlux 的 @GetMapping 配合 Mono/Flux 返回响应式类型
    import asyncio

    @app.get("/async-data")
    async def async_data():
        await asyncio.sleep(0.01)  # 模拟异步 I/O（如数据库查询）
        return {"data": "fetched asynchronously"}

    # 同步路由也支持（普通 def），FastAPI 会放到线程池执行
    @app.get("/sync-data")
    def sync_data():
        return {"data": "fetched synchronously"}

    client = TestClient(app)
    r1 = client.get("/async-data")
    r2 = client.get("/sync-data")
    print(f"  异步路由: {r1.json()}")
    print(f"  同步路由: {r2.json()}")
    print("  [说明] async def 适合 I/O 密集；def 适合 CPU 密集（自动线程池）")


def demo_fastapi_dependency_injection():
    """FastAPI 依赖注入 Depends。"""
    print("\n=== 6. FastAPI 依赖注入 Depends ===")
    try:
        from fastapi import FastAPI, Depends, Header
        from fastapi.testclient import TestClient
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # 依赖函数：从请求头提取 token
    # [Java 对比] 类似 Spring 的 @RequestHeader 或自定义 HandlerInterceptor
    def get_token(authorization: str = Header(...)):
        # Header(...) 表示从请求头读取 Authorization，必填
        if not authorization.startswith("Bearer "):
            # 抛出 HTTPException 会被 FastAPI 转成错误响应
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="无效的 token")
        return authorization[len("Bearer "):]

    # 通过 Depends(get_token) 注入依赖
    # [Java 对比] 类似 @Autowired 注入 Bean，或参数解析器
    @app.get("/secure")
    def secure_endpoint(token: str = Depends(get_token)):
        return {"token": token, "msg": "已认证"}

    # 依赖可嵌套：依赖 A 依赖 B，FastAPI 自动解析依赖图
    def get_current_user(token: str = Depends(get_token)):
        # 模拟根据 token 查用户
        return {"name": "Alice", "token": token}

    @app.get("/me")
    def me(user: dict = Depends(get_current_user)):
        return user

    client = TestClient(app)

    # 无 token -> 422（Header 必填缺失）
    r1 = client.get("/secure")
    print(f"  无 Authorization -> {r1.status_code}")

    # 有效 token
    r2 = client.get("/secure", headers={"Authorization": "Bearer abc123"})
    print(f"  有效 token -> {r2.status_code}: {r2.json()}")

    # 无效 token 格式 -> 401
    r3 = client.get("/secure", headers={"Authorization": "Basic xxx"})
    print(f"  无效格式 -> {r3.status_code}: {r3.json()['detail']}")

    # 嵌套依赖
    r4 = client.get("/me", headers={"Authorization": "Bearer xyz"})
    print(f"  嵌套依赖 /me -> {r4.json()}")


def demo_fastapi_middleware():
    """FastAPI 中间件：在请求前后执行逻辑。"""
    print("\n=== 7. FastAPI 中间件 ===")
    try:
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()
    import time

    # 中间件：记录请求耗时
    # [Java 对比] Spring 的 Filter / HandlerInterceptor
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start = time.time()
        # call_next 把请求传递给下一个中间件/路由
        response = await call_next(request)
        duration = time.time() - start
        # 在响应头添加自定义字段
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

    @app.get("/ping")
    def ping():
        return {"pong": True}

    client = TestClient(app)
    r = client.get("/ping")
    print(f"  GET /ping -> {r.status_code}: {r.json()}")
    print(f"  响应头 X-Process-Time: {r.headers.get('X-Process-Time')}")


def demo_fastapi_exception_handler():
    """FastAPI 异常处理 HTTPException 与自定义异常。"""
    print("\n=== 8. FastAPI 异常处理 ===")
    try:
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.testclient import TestClient
        from fastapi.responses import JSONResponse
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # 自定义业务异常
    class BusinessError(Exception):
        def __init__(self, code: int, message: str):
            self.code = code
            self.message = message

    # 注册自定义异常处理器
    # [Java 对比] @ControllerAdvice + @ExceptionHandler(BusinessError.class)
    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        return JSONResponse(
            status_code=400,
            content={"error_code": exc.code, "error_msg": exc.message},
        )

    # 使用 HTTPException 抛出标准 HTTP 错误
    @app.get("/items/{item_id}")
    def get_item(item_id: int):
        if item_id < 0:
            # [Java 对比] throw new ResponseStatusException(HttpStatus.NOT_FOUND, "...")
            raise HTTPException(status_code=404, detail="item 不存在")
        return {"item_id": item_id}

    @app.get("/pay")
    def pay():
        raise BusinessError(code=5001, message="余额不足")

    client = TestClient(app)

    r1 = client.get("/items/-1")
    print(f"  HTTPException 404 -> {r1.status_code}: {r1.json()['detail']}")

    r2 = client.get("/pay")
    print(f"  自定义异常 -> {r2.status_code}: {r2.json()}")


def demo_fastapi_docs():
    """FastAPI 自动文档：Swagger UI / ReDoc。"""
    print("\n=== 9. FastAPI 自动文档 ===")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI(title="Demo API", version="1.0.0")

    @app.get("/hello", summary="打招呼", description="返回问候语")
    def hello(name: str = "world"):
        """GET /hello - 一个简单的问候接口。"""
        return {"hello": name}

    client = TestClient(app)

    # FastAPI 自动生成 OpenAPI schema
    # [Java 对比] springdoc-openapi / springfox 生成 Swagger 文档
    r = client.get("/openapi.json")
    schema = r.json()
    print(f"  OpenAPI 版本: {schema.get('openapi')}")
    print(f"  API 标题: {schema['info']['title']}")
    print(f"  已注册路径: {list(schema['paths'].keys())}")

    # [说明] 启动服务后访问：
    #   Swagger UI: http://127.0.0.1:8000/docs
    #   ReDoc:     http://127.0.0.1:8000/redoc
    print("  [说明] Swagger UI: /docs, ReDoc: /redoc")


def demo_fastapi_cors():
    """FastAPI CORS 配置。"""
    print("\n=== 10. FastAPI CORS 配置 ===")
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.testclient import TestClient
    except ImportError:
        print("  [注意] fastapi 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI()

    # 添加 CORS 中间件
    # [Java 对比] Spring 中配置 CorsRegistry 或 WebMvcConfigurer.addCorsMappings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://example.com"],  # 允许的源
        allow_credentials=True,                   # 允许携带 Cookie
        allow_methods=["*"],                       # 允许所有方法
        allow_headers=["*"],                       # 允许所有头
    )

    @app.get("/data")
    def data():
        return {"data": "ok"}

    client = TestClient(app)

    # 模拟跨域预检请求 OPTIONS
    r = client.options(
        "/data",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    print(f"  预检请求状态: {r.status_code}")
    print(f"  允许的源: {r.headers.get('access-control-allow-origin')}")

    # 不在白名单的源
    r2 = client.options(
        "/data",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    print(f"  非白名单源预检: {r2.status_code} (无 allow-origin 头)")


def demo_fastapi_crud():
    """FastAPI 完整示例：内存存储的 CRUD API。"""
    print("\n=== 11. FastAPI 完整 CRUD 示例（内存存储）===")
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from pydantic import BaseModel, Field
    except ImportError:
        print("  [注意] fastapi/pydantic 未安装，跳过。安装: pip install fastapi uvicorn")
        return

    app = FastAPI(title="Todo API", version="1.0.0")

    # --- 模型定义 ---
    class TodoCreate(BaseModel):
        """创建 Todo 的请求体。"""
        title: str = Field(..., min_length=1, max_length=100)
        done: bool = False

    class TodoOut(BaseModel):
        """返回给客户端的 Todo 模型。"""
        id: int
        title: str
        done: bool

    # --- 内存存储 ---
    # [Java 对比] 实际项目用 JPA Repository，这里用 dict 模拟
    _store: dict[int, dict] = {}
    _next_id = 1

    def get_next_id() -> int:
        nonlocal _next_id
        _next_id += 1
        return _next_id - 1

    # --- 路由 ---
    # [Java 对比]
    #   @PostMapping("/todos")        -> create
    #   @GetMapping("/todos")          -> list
    #   @GetMapping("/todos/{id}")    -> get one
    #   @PutMapping("/todos/{id}")    -> update
    #   @DeleteMapping("/todos/{id}") -> delete

    @app.post("/todos", response_model=TodoOut, status_code=201)
    def create_todo(todo: TodoCreate):
        tid = get_next_id()
        item = {"id": tid, **todo.model_dump()}
        _store[tid] = item
        return item

    @app.get("/todos", response_model=list[TodoOut])
    def list_todos():
        return list(_store.values())

    @app.get("/todos/{tid}", response_model=TodoOut)
    def get_todo(tid: int):
        if tid not in _store:
            raise HTTPException(status_code=404, detail="todo 不存在")
        return _store[tid]

    @app.put("/todos/{tid}", response_model=TodoOut)
    def update_todo(tid: int, todo: TodoCreate):
        if tid not in _store:
            raise HTTPException(status_code=404, detail="todo 不存在")
        _store[tid].update(todo.model_dump())
        return _store[tid]

    @app.delete("/todos/{tid}", status_code=204)
    def delete_todo(tid: int):
        if tid not in _store:
            raise HTTPException(status_code=404, detail="todo 不存在")
        del _store[tid]

    # --- 测试 CRUD 流程 ---
    client = TestClient(app)

    # Create
    r = client.post("/todos", json={"title": "学习 FastAPI", "done": False})
    print(f"  Create -> {r.status_code}: {r.json()}")
    tid = r.json()["id"]

    # List
    r = client.get("/todos")
    print(f"  List  -> {r.status_code}: {r.json()}")

    # Get one
    r = client.get(f"/todos/{tid}")
    print(f"  Get   -> {r.status_code}: {r.json()}")

    # Update
    r = client.put(f"/todos/{tid}", json={"title": "学习 FastAPI（已更新）", "done": True})
    print(f"  Update-> {r.status_code}: {r.json()}")

    # Delete
    r = client.delete(f"/todos/{tid}")
    print(f"  Delete-> {r.status_code} (204 No Content)")

    # 确认已删除
    r = client.get(f"/todos/{tid}")
    print(f"  Get(删除后) -> {r.status_code} (404)")


# ===========================================================================
# 第二部分：Flask
# ===========================================================================
# Flask 是一个轻量级同步 Web 框架，适合中小型项目或 API 服务。
#
# [Java 对比] Spring MVC
#   - Spring MVC 用 @Controller / @RestController + @RequestMapping
#   - Flask 用 @app.route("/path") 装饰器
#   - Spring MVC 用 Model / ModelAndView 传递数据到视图
#   - Flask 用 render_template("xx.html", key=value)
#   - Spring MVC 用 @Autowired 注入依赖
#   - Flask 用 Blueprint 模块化、扩展注册
#
# 安装：pip install flask


def demo_flask_minimal():
    """Flask 最小应用。"""
    print("\n=== 12. Flask 最小应用 ===")
    try:
        from flask import Flask
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    app = Flask(__name__)

    # [Java 对比]
    #   @RestController
    #   public class HelloController {
    #       @GetMapping("/")
    #       public String hello() { return "Hello, Flask!"; }
    #   }
    @app.route("/")
    def hello():
        return "Hello, Flask!"

    # 用 test_client 在进程内测试（不启动真实服务器）
    client = app.test_client()
    r = client.get("/")
    print(f"  GET / -> {r.status_code}: {r.get_data(as_text=True)}")

    # [说明] 真实部署：flask run --port 5000，或用 gunicorn/waitress 生产部署
    print("  [说明] 部署命令: flask run --port 5000（开发）或 gunicorn（生产）")


def demo_flask_route_params():
    """Flask 路由参数与转换器。"""
    print("\n=== 13. Flask 路由参数 ===")
    try:
        from flask import Flask
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    app = Flask(__name__)

    # <int:item_id> 是类型转换器：int / float / path / uuid
    # [Java 对比] @PathVariable Integer itemId
    @app.route("/items/<int:item_id>")
    def get_item(item_id):
        return f"item_id={item_id} (类型: {type(item_id).__name__})"

    # 字符串参数（默认类型 string）
    @app.route("/users/<username>")
    def get_user(username):
        return f"username={username}"

    client = app.test_client()
    print(f"  /items/42 -> {client.get('/items/42').get_data(as_text=True)}")
    print(f"  /users/alice -> {client.get('/users/alice').get_data(as_text=True)}")


def demo_flask_template():
    """Flask 模板渲染 render_template（用内联模板演示）。"""
    print("\n=== 14. Flask 模板渲染 ===")
    try:
        from flask import Flask, render_template_string
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    app = Flask(__name__)

    # 实际项目用 render_template("index.html", ...) 从 templates/ 目录加载
    # 这里用 render_template_string 内联演示（避免依赖文件系统）
    # [Java 对比] Thymeleaf: model.addAttribute("name", "World"); return "index";
    TEMPLATE = "<h1>Hello, {{ name }}!</h1><p>Items: {{ items|join(', ') }}</p>"

    @app.route("/hello/<name>")
    def hello(name):
        return render_template_string(TEMPLATE, name=name, items=["a", "b", "c"])

    client = app.test_client()
    r = client.get("/hello/World")
    print(f"  /hello/World -> {r.get_data(as_text=True).strip()}")


def demo_flask_request_jsonify():
    """Flask 请求对象 request 与 JSON 响应 jsonify。"""
    print("\n=== 15. Flask request 与 jsonify ===")
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    app = Flask(__name__)

    # GET：读取查询参数
    # [Java 对比] @RequestParam String q / HttpServletRequest.getParameter("q")
    @app.route("/search")
    def search():
        q = request.args.get("q", "")     # 查询参数
        page = request.args.get("page", "1", type=int)  # 带类型转换
        return jsonify(q=q, page=page)

    # POST：读取 JSON 请求体
    # [Java 对比] @RequestBody Map<String, Object> body
    @app.route("/echo", methods=["POST"])
    def echo():
        data = request.get_json()  # 解析 JSON 请求体
        return jsonify(received=data)

    client = app.test_client()

    r1 = client.get("/search?q=python&page=3")
    print(f"  GET /search -> {r1.get_json()}")

    r2 = client.post("/echo", json={"msg": "hi"})
    print(f"  POST /echo  -> {r2.get_json()}")


def demo_flask_redirect_url_for():
    """Flask 重定向 redirect 与 url_for。"""
    print("\n=== 16. Flask redirect / url_for ===")
    try:
        from flask import Flask, redirect, url_for
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    app = Flask(__name__)

    @app.route("/old")
    def old():
        # url_for 根据函数名生成 URL（类似 Spring 的 MvcUriComponentsBuilder）
        return redirect(url_for("new"))

    @app.route("/new")
    def new():
        return "这是新页面"

    client = app.test_client()
    # follow_redirects=True 自动跟随重定向
    r = client.get("/old", follow_redirects=True)
    print(f"  /old -> 重定向到 /new -> {r.get_data(as_text=True)}")
    print(f"  最终状态码: {r.status_code}")


def demo_flask_blueprint():
    """Flask 蓝图 Blueprint：模块化路由组织。"""
    print("\n=== 17. Flask Blueprint ===")
    try:
        from flask import Flask, Blueprint, jsonify
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    # 创建蓝图（类似 Spring 的 @RestController 分组）
    # [Java 对比] 把不同 Controller 放不同包，用 @RequestMapping("/api/v1/users") 前缀
    user_bp = Blueprint("users", __name__, url_prefix="/api/users")

    @user_bp.route("/")
    def list_users():
        return jsonify(users=["Alice", "Bob"])

    @user_bp.route("/<int:uid>")
    def get_user(uid):
        return jsonify(id=uid, name="Alice")

    app = Flask(__name__)
    # 注册蓝图到应用
    app.register_blueprint(user_bp)

    client = app.test_client()
    r1 = client.get("/api/users/")
    print(f"  GET /api/users/ -> {r1.get_json()}")
    r2 = client.get("/api/users/1")
    print(f"  GET /api/users/1 -> {r2.get_json()}")
    print("  [说明] Blueprint 用于大型项目模块化，类似 Spring 的多 Controller 分组")


def demo_flask_blog_api():
    """Flask 完整示例：简单博客 API（内存存储）。"""
    print("\n=== 18. Flask 完整博客 API ===")
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("  [注意] flask 未安装，跳过。安装: pip install flask")
        return

    app = Flask(__name__)
    _posts: dict[int, dict] = {}
    _next_id = 1

    # 列出所有文章
    @app.get("/posts")
    def list_posts():
        return jsonify(list(_posts.values()))

    # 获取单篇文章
    @app.get("/posts/<int:pid>")
    def get_post(pid):
        post = _posts.get(pid)
        if not post:
            return jsonify(error="not found"), 404
        return jsonify(post)

    # 创建文章
    @app.post("/posts")
    def create_post():
        nonlocal _next_id
        data = request.get_json()
        if not data or "title" not in data:
            return jsonify(error="title is required"), 400
        post = {"id": _next_id, "title": data["title"], "content": data.get("content", "")}
        _posts[_next_id] = post
        _next_id += 1
        return jsonify(post), 201

    # 删除文章
    @app.delete("/posts/<int:pid>")
    def delete_post(pid):
        if pid not in _posts:
            return jsonify(error="not found"), 404
        del _posts[pid]
        return "", 204

    client = app.test_client()

    # 创建
    r = client.post("/posts", json={"title": "Hello", "content": "First post"})
    print(f"  Create -> {r.status_code}: {r.get_json()}")
    pid = r.get_json()["id"]

    # 列表
    r = client.get("/posts")
    print(f"  List   -> {r.get_json()}")

    # 获取
    r = client.get(f"/posts/{pid}")
    print(f"  Get    -> {r.get_json()}")

    # 删除
    r = client.delete(f"/posts/{pid}")
    print(f"  Delete -> {r.status_code}")

    # 删除后获取 -> 404
    r = client.get(f"/posts/{pid}")
    print(f"  Get(删除后) -> {r.status_code}")


# ===========================================================================
# 第三部分：Django（概览，注释为主）
# ===========================================================================
# Django 是一个"自带电池"的全栈 Web 框架，包含 ORM、模板、Admin、表单、认证等。
#
# [Java 对比] Spring Boot 全栈
#   - Spring Boot: Spring MVC + Spring Data JPA + Spring Security + Thymeleaf
#   - Django:     Views + Django ORM + django.contrib.auth + Django Templates
#
# Django 设计哲学：MTV 架构
#   - M (Model):       数据模型，定义在 models.py，对应数据库表
#   - T (Template):    模板，渲染 HTML，对应 templates/ 目录
#   - V (View):        视图，处理请求逻辑，定义在 views.py
#
# [Java 对比] Spring MVC 是 MVC：
#   - M (Model):       数据模型
#   - V (View):        视图（Thymeleaf/JSP）
#   - C (Controller):  控制器
#   Django 的 View 相当于 Spring 的 Controller，Django 的 Template 相当于 View。
#
# Django 项目结构（典型）：
#   myproject/
#     manage.py          # 管理脚本（类似 Spring Boot 的 mvn spring-boot:run）
#     myproject/
#       settings.py      # 配置（类似 application.yml）
#       urls.py          # 根 URL 路由配置
#       wsgi.py / asgi.py# 部署入口
#     blog/              # 应用（类似 Spring 中的一个模块）
#       models.py        # ORM 模型定义
#       views.py         # 视图函数 / 类视图
#       urls.py          # 应用级 URL 路由
#       admin.py         # Admin 后台注册
#       templates/       # 模板文件
#       migrations/      # 数据库迁移脚本（类似 Flyway/Liquibase）
#
# 安装：pip install django


def demo_django_overview():
    """Django 概览：用注释展示核心概念（不实际运行 Django 项目）。"""
    print("\n=== 19. Django 概览（注释展示）===")
    print("  Django 是全栈框架，项目结构复杂，此处仅用注释展示核心概念。")
    print()
    print("  --- Django MTV 架构 ---")
    print("  Model      -> models.py 中定义，继承 models.Model")
    print("  Template   -> templates/ 目录下的 .html 文件")
    print("  View       -> views.py 中定义，处理 HTTP 请求")
    print()
    print("  --- 创建项目命令 ---")
    print("  django-admin startproject myproject    # 创建项目")
    print("  cd myproject")
    print("  python manage.py startapp blog         # 创建应用")
    print("  python manage.py makemigrations         # 生成迁移（类似 Flyway）")
    print("  python manage.py migrate               # 执行迁移")
    print("  python manage.py runserver             # 启动开发服务器")
    print()
    print("  --- ORM 模型定义 (models.py) ---")
    print("""
    # [Java 对比] JPA Entity
    #   @Entity @Table(name="blog_post")
    #   public class Post {
    #       @Id @GeneratedValue
    #       private Long id;
    #       @Column(nullable=false, max_length=200)
    #       private String title;
    #       @Column(columnDefinition="TEXT")
    #       private String content;
    #       @Temporal(TemporalType.TIMESTAMP)
    #       private Date createdAt;
    #   }

    from django.db import models

    class Post(models.Model):
        title = models.CharField(max_length=200)       # VARCHAR(200)
        content = models.TextField()                    # TEXT
        created_at = models.DateTimeField(auto_now_add=True)  # 创建时自动设时间

        def __str__(self):
            return self.title
    """)
    print("  --- 视图函数 (views.py) ---")
    print("""
    # [Java 对比] @GetMapping("/posts/{id}")
    #   public ResponseEntity<Post> getPost(@PathVariable Long id) { ... }

    from django.shortcuts import get_object_or_404, render
    from .models import Post

    # 函数视图
    def post_detail(request, post_id):
        post = get_object_or_404(Post, pk=post_id)  # 找不到自动返回 404
        return render(request, "blog/detail.html", {"post": post})

    # 类视图（类似 Spring 的 @Controller 继承基类）
    from django.views.generic import ListView
    class PostListView(ListView):
        model = Post
        template_name = "blog/list.html"
        context_object_name = "posts"
    """)
    print("  --- URL 路由 (urls.py) ---")
    print("""
    # [Java 对比] @RequestMapping("/posts/{id}") 路径映射
    from django.urls import path
    from . import views

    urlpatterns = [
        path("posts/", views.PostListView.as_view(), name="post_list"),
        path("posts/<int:post_id>/", views.post_detail, name="post_detail"),
    ]
    """)
    print("  --- Admin 后台 ---")
    print("""
    # Django 自带 Admin 后台（类似 Spring Boot Admin 但更强大）
    # [Java 对比] 无直接等价物，类似用 JHipster 生成的管理界面
    # 注册模型后访问 /admin/ 即可进行 CRUD
    from django.contrib import admin
    from .models import Post

    @admin.register(Post)
    class PostAdmin(admin.ModelAdmin):
        list_display = ("id", "title", "created_at")
        search_fields = ("title", "content")
    """)
    print("  --- 模板系统 ---")
    print("""
    {# templates/blog/detail.html #}
    {# [Java 对比] Thymeleaf: <h1 th:text="${post.title}">标题</h1> #}
    <h1>{{ post.title }}</h1>
    <p>{{ post.content }}</p>
    <small>{{ post.created_at|date:"Y-m-d" }}</small>
    """)
    print("  [说明] Django 适合内容管理、后台系统等全栈场景。")
    print("         API 开发可配合 Django REST Framework (DRF)。")


# ===========================================================================
# 第四部分：框架对比总结
# ===========================================================================

def demo_framework_comparison():
    """三大框架横向对比总结。"""
    print("\n=== 20. 框架对比总结 ===")
    comparison = [
        ("特性", "FastAPI", "Flask", "Django"),
        ("异步支持", "原生 async", "需 async 扩展", "3.0+ 支持 async"),
        ("类型提示", "强依赖（核心）", "可选", "可选"),
        ("自动文档", "Swagger/ReDoc 内置", "需扩展", "需 DRF + drf-spectacular"),
        ("ORM", "无（自选 SQLAlchemy）", "无", "内置 Django ORM"),
        ("模板", "无（纯 API）", "Jinja2", "Django Templates"),
        ("Admin 后台", "无", "无", "内置"),
        ("学习曲线", "低（类型友好）", "低", "中（全栈概念多）"),
        ("适合场景", "API 服务", "轻量 Web/API", "全栈/内容管理"),
        ("Java 对应", "Spring WebFlux", "Spring MVC", "Spring Boot 全栈"),
    ]
    # 手动对齐打印（避免依赖第三方库）
    col_widths = [10, 22, 22, 22]
    for row in comparison:
        cells = []
        for i, cell in enumerate(row):
            # 中文按 2 个宽度计算，简单补齐
            text = str(cell)
            width = sum(2 if ord(c) > 127 else 1 for c in text)
            pad = col_widths[i] - width
            cells.append(text + " " * max(0, pad))
        print("  " + " | ".join(cells))


# ===========================================================================
# 主入口
# ===========================================================================

def main():
    print("=" * 60)
    print("04 - Web 框架（FastAPI / Flask / Django）")
    print("=" * 60)

    # FastAPI 部分
    demo_fastapi_minimal()
    demo_fastapi_path_query()
    demo_fastapi_request_body()
    demo_fastapi_response_model()
    demo_fastapi_async()
    demo_fastapi_dependency_injection()
    demo_fastapi_middleware()
    demo_fastapi_exception_handler()
    demo_fastapi_docs()
    demo_fastapi_cors()
    demo_fastapi_crud()

    # Flask 部分
    demo_flask_minimal()
    demo_flask_route_params()
    demo_flask_template()
    demo_flask_request_jsonify()
    demo_flask_redirect_url_for()
    demo_flask_blueprint()
    demo_flask_blog_api()

    # Django 部分
    demo_django_overview()

    # 对比总结
    demo_framework_comparison()

    print("\n" + "=" * 60)
    print("小结：")
    print("  - FastAPI：异步优先，类型驱动，自动文档，适合现代 API 服务")
    print("  - Flask：轻量灵活，同步为主，适合中小型项目或微服务")
    print("  - Django：全栈一体，ORM+Admin+模板，适合内容管理与后台系统")
    print("  - Java 对应：FastAPI~WebFlux, Flask~SpringMVC, Django~SpringBoot全栈")
    print("=" * 60)


if __name__ == "__main__":
    main()
    sys.exit(0)
