# 部署与版本管理

## 部署方式

第一版采用“本地开发轻量启动，集成环境 Docker Compose”的策略。

- 本地开发：`frontend` 用 `npm run dev`，`api` 用 `uvicorn`，PostgreSQL/Redis 用 Docker 或本机服务。
- 集成开发：用 Docker Compose 拉起 `frontend`、`api`、`worker`、`postgres`、`redis`。
- 未来部署：可以迁移为单机容器组，也可以按瓶颈拆分独立 worker 池。

不建议第一版直接上 Kubernetes。当前项目的主要风险是链路复杂度和状态一致性，不是容器编排规模。

## Docker Compose 服务

第一版建议包含：

| 服务 | 镜像/进程 | 端口 | 说明 |
| --- | --- | --- | --- |
| `frontend` | Next.js | `3000` | 控制台页面 |
| `api` | FastAPI + Uvicorn | `8000` | API 网关和任务查询 |
| `worker` | Celery worker | 无公开端口 | 长任务执行 |
| `postgres` | PostgreSQL + pgvector | `5432` | 业务库和向量库 |
| `redis` | Redis | `6379` | Celery broker 和短期缓存 |

后续可选：

- `crawler-worker`：独立 Playwright worker 池
- `rag-worker`：独立 embedding 和向量写入 worker
- `scheduler`：周期性评论复查和痛点趋势更新
- `monitor`：Flower 或自研队列监控

## 本地启动顺序

1. 启动 PostgreSQL 和 Redis。
2. 执行数据库迁移。
3. 启动 FastAPI：`uv run uvicorn backend.app.main:create_app --factory --reload`。
4. 启动 Celery worker。
5. 启动 Next.js：在 `frontend/` 执行 `npm run dev`。
6. 跑健康检查：`GET /api/health`。
7. 提交样例任务，确认任务能入库、入队、更新状态。

Day 1 阶段只完成了 FastAPI health 与 Next.js mock 控制台；从 Day 3 开始会逐步补齐数据库、Celery 和真实任务流。

## Git 分支策略

| 分支 | 用途 | 规则 |
| --- | --- | --- |
| `main` | 稳定演示版本 | 只合并已验证、可回退的阶段成果 |
| `dev` | 日常集成开发 | Day 2 以后默认开发分支 |
| `feature/*` | 较大功能分支 | 涉及多文件、多天开发时使用 |
| `backup/*` | 高风险回退点 | 数据迁移、架构改造前创建 |

提交信息允许中文，但保留 Conventional Commit 类型，例如：

- `docs: 冻结架构与技术选型`
- `feat: 接入 Celery 任务队列`
- `fix: 修复任务状态查询错误`

## 版本管理要求

- 每天至少一个可回退提交。
- 每个阶段结束后从 `dev` 合并到 `main`。
- 里程碑节点打 tag，例如 `v0.1-day07-infra`。
- 重大架构变更先写文档，再改代码。
- 提交前必须至少运行对应层的 lint/test/build。

## 回退策略

回退不是只退代码，还要检查数据和任务状态：

- 保留数据库迁移脚本和回滚说明。
- 保留上一个可用镜像或分支。
- 出现高风险变更时先创建 `backup/*` 分支。
- 数据库迁移必须说明是否向后兼容。
- Worker 必须能处理旧任务，或者显式标记旧任务不可恢复。
- 前端必须能读取旧报告，或者提供报告版本兼容层。

## 环境变量

第一版 `.env.example` 至少覆盖：

- `APP_ENV`
- `APP_NAME`
- `API_PREFIX`
- `LOG_LEVEL`
- `BACKEND_CORS_ORIGINS`
- `DATABASE_URL`
- `REDIS_URL`
- `MODEL_PROVIDER`
- `MODEL_NAME`
- `REPORT_MODEL_NAME`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_USE_MOCKS`

不要把真实 API Key、Cookie、代理账号、数据库密码提交到仓库。

## 回退检查清单

- 当前分支是否干净
- 是否知道要回退到哪个 commit/tag
- `.env.example` 是否变化
- 数据库迁移是否兼容
- Worker 是否仍能消费旧任务
- 前端是否能读取旧报告
- GitHub 上是否已有远程备份

## 与其他文档关系

- 环境细节见 `dev-environment.md`
- 发布清单见 `release-checklist.md`
- 测试门槛见 `testing-strategy.md`
- 架构拓扑见 `architecture.md`
