# Python 进阶学习（面向 Java 开发者）

一套用 [mdbook](https://rust-lang.github.io/mdBook/) 构建的 Python 进阶教程。面向**有丰富 Java 经验、熟悉 Python 基本用法**的开发者，重点是"Java 有而 Python 不一样"的地方，而不是通用编程入门。

每个主题都给出 **Java 对应物**（如 `asyncio` ↔ CompletableFuture、`pydantic` ↔ Bean Validation、SQLAlchemy ↔ Hibernate），并标注 Python 特有的坑。

## 快速开始

```bash
# 安装 mdbook
cargo install mdbook          # 或下载预编译包：
                              # https://rust-lang.github.io/mdBook/guide/installation.html

# 本地预览（浏览器自动打开 http://localhost:3000）
mdbook serve --open

# 构建静态站点到 book/
mdbook build
```

不想装 mdbook 也可以直接读 Markdown 源文件，从 [`src/README.md`](src/README.md) 开始。

## 内容结构

全书共 **6 部分 44 章**，含 **44 个可直接运行的示例文件**。

| 部分 | 章节 | 内容 |
|------|------|------|
| **零、语言基础补遗** | 8 章 | 星号解包、类方法与 property、推导式、迭代协议与切片、`with` 语句、易误解关键字、模块与包机制、装饰器入门 |
| **一、异步编程** | 9 章 | 协程、事件循环、任务管理、异步迭代器、异步上下文管理器、同步原语、HTTP/文件 I/O、取消与超时、与 Java 对比 |
| **二、高级特性** | 13 章 | 类型系统、元编程、装饰器、生成器进阶、并发与并行、内存与性能、现代语法、上下文管理器、函数式工具、内省反射、包管理、C 扩展、其他 |
| **三、实战经验** | 3 章 | 性能优化深入、最佳实践、16 个常见陷阱 |
| **四、常用类库** | 8 章 | 标准库核心/数据/系统、Web 框架、HTTP 客户端、数据科学、数据库 ORM、工程化工具链 |
| **五、工程化实践** | 3 章 | 工业级项目结构、构建与发布（包管理工具选型/版本管理/私服）、CI/CD 与运行工作流（Actions/Docker/部署） |

完整目录见 [`src/SUMMARY.md`](src/SUMMARY.md)。

### 适合谁

- 熟悉 Java，Python 能写但不够"地道"
- 想搞清楚 `async/await` 与 JVM 并发模型的异同
- 需要把 Java 生态经验（Spring、JPA、JUnit、Maven）迁移到 Python

## 项目结构

```
.
├── book.toml              # mdbook 配置
├── src/
│   ├── SUMMARY.md         # 全书目录（mdbook 导航由它驱动）
│   ├── README.md          # 书籍首页
│   ├── basics/            # 第零部分：8 章（语言基础补遗）
│   ├── async/             # 第一部分：9 章
│   ├── advanced/          # 第二部分：13 章
│   ├── practice/          # 第三部分：3 章
│   ├── libraries/         # 第四部分：8 章
│   ├── engineering/       # 第五部分：3 章（工程化）
│   └── code/              # 全部可运行示例（44 个 .py）
│       ├── basics/        ├── async/         ├── advanced/
│       ├── practice/      ├── libraries/     └── engineering/
└── tools/
    ├── toc_gen.py         # 文档与源码的同步工具
    └── toc_reset.py       # 剥离 include，回到纯链接状态
```

## 运行示例

```bash
python src/code/async/01_basics.py
python src/code/libraries/06_data_science.py
```

单个脚本都会跑完所有 demo 后打印 `所有 demo 运行完成！`，退出码 0。

**环境要求**：Python 3.12+（推荐 3.13）。第三方库可选安装：

```bash
pip install numpy pandas polars matplotlib sqlalchemy \
            fastapi flask django requests httpx aiohttp jinja2 pydantic
```

未安装某个库时，对应 demo 会打印提示并跳过，**不影响其余示例运行**。

## 文档与代码如何保持同步

讲解中的代码片段不是手工复制的，而是用 mdbook 的 `{{#include}}` 从 `src/code/` 按行区间自动嵌入，因此源码改动后文档不会默默过期：

```bash
python tools/toc_gen.py --check   # 检查是否同步（适合挂 CI）
python tools/toc_gen.py --fix     # 自动校正所有 include 的行区间
python tools/toc_reset.py --fix   # 出问题时：剥离全部 include，回到纯链接
```

脚本按「行号 → 所属顶层函数/类」定位，函数内部增删几行后能自动重算区间；若行号已完全对不上任何函数，会**明确报错**而非静默生成错误内容。

> 如果 include 内容出现错乱，先跑 `toc_reset.py --fix` 把文档退回“只有链接”的状态，再跑 `toc_gen.py --fix` 重建，比逐处修补可靠。

## 贡献

欢迎提 issue 或 PR 补充主题、修正示例。修改 `src/code/` 下的源码后，请运行 `python tools/toc_gen.py --fix` 并确认 `mdbook build` 通过。
