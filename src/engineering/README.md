# 工程化实践

本部分讲**真实项目怎么落地**：代码怎么组织、构建发布怎么走、CI/CD 怎么编排。

前几部分讲"Python 语言怎么写"，这部分讲"Python 项目怎么跑起来"。

## Java 开发者最大的心智落差

| | Java | Python |
|---|---|---|
| 构建生命周期 | `compile → test → package → deploy` | **不存在** |
| 一条命令 | `mvn verify` | 需要 Makefile 或 CI 脚本编排 |
| 工具形态 | 插件挂在生命周期阶段 | 独立命令行工具 |
| 可运行产物 | fat jar | **Docker 镜像** |

理解这四点，后面的内容就顺了。

## 章节目录

| 章节 | 主题 | 对应 Java |
|------|------|-----------|
| [01 - 项目结构](01-project-layout.md) | src layout、分层架构、monorepo、`pyproject.toml` 全量、依赖分组 | Maven 目录规范、多模块、`pom.xml` |
| [02 - 构建与发布](02-build-and-release.md) | 包管理工具选型、sdist vs wheel、版本管理、发布检查清单、私服 | `mvn package/deploy`、Nexus |
| [03 - CI/CD 与工作流](03-ci-and-workflow.md) | GitHub Actions、Makefile、Docker 多阶段、配置管理、部署策略 | `mvn verify`、Jenkins、jib |

## 学习路径

1. **项目结构** —— 先有正确的骨架，后面才谈得上工程化
2. **构建与发布** —— 知道产物是什么、怎么验证
3. **CI/CD** —— 把前面所有工具串成流水线

## 配套章节

本部分和前面这些章节关系紧密：

- [`basics/07-modules-and-packages.md`](../basics/07-modules-and-packages.md) —— 导入机制，理解 src layout 的前提
- [`libraries/08-toolchain.md`](../libraries/08-toolchain.md) —— ruff / mypy / pytest 等工具本身
- [`practice/02-best-practices.md`](../practice/02-best-practices.md) —— 编码规范
- [`advanced/11-packaging.md`](../advanced/11-packaging.md) —— 打包基础

> 📁 [本部分代码目录](../code/engineering/)
