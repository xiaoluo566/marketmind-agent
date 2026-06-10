# 部署与版本管理

## 部署策略

第一版采用“两层启动方式”：

- 本地开发：前端、API、Worker 可以直接用 `npm` / `uv` 启动，PostgreSQL 和 Redis 可以用 Docker 或本机服务。
- 集成环境：使用 Docker Compose 拉起 `frontend`、`api`、`worker`、`migrate`、`postgres`、`redis`。

当前不直接上 Kubernetes。项目现阶段的核心风险是长任务、状态、证据链和配置一致性，不是集群规模。

## Docker Compose 服务

| 服务 | 镜像/进程 | 端口 | 说明 |
| --- | --- | --- | --- |
| `frontend` | Next.js | `3000` | 控制台页面 |
| `api` | FastAPI + Uvicorn | `8000` | API 网关和任务查询 |
| `worker` | Celery worker | 无公开端口 | 长任务执行 |
| `migrate` | Alembic | 无公开端口 | 数据库迁移 |
| `postgres` | PostgreSQL + pgvector | `5432` | 业务库和向量库 |
| `redis` | Redis | `6379` | Celery broker、result backend 和任务状态缓存 |

依赖顺序：

```text
postgres healthy
redis healthy
postgres healthy -> migrate completed
migrate completed + redis healthy -> api / worker
api healthy -> frontend
```

## 一键启动命令

从仓库根目录执行：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

后台启动：

```powershell
docker compose up --build -d
```

查看服务状态：

```powershell
docker compose ps
docker compose logs -f api
docker compose logs -f worker
```

健康检查：

```powershell
curl http://localhost:8000/api/health
```

前端地址：

```text
http://localhost:3000
```

API 地址：

```text
http://localhost:8000
```

## 数据卷与清理

Compose 会创建三个命名卷：

- `postgres_data`
- `redis_data`
- `crawler_artifacts`

停止容器但保留数据：

```powershell
docker compose down
```

停止容器并清理数据卷：

```powershell
docker compose down -v
```

清理数据卷会删除数据库、Redis 数据和采集 artifact，只能在确认不需要回滚数据时执行。

## 环境变量

`.env.example` 至少包含：

- `APP_ENV`
- `APP_NAME`
- `API_PREFIX`
- `LOG_LEVEL`
- `BACKEND_CORS_ORIGINS`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`
- `REDIS_PORT`
- `API_PORT`
- `FRONTEND_PORT`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `TASK_STATUS_REDIS_URL`
- `TASK_STATUS_TTL_SECONDS`
- `CRAWLER_ARTIFACT_DIR`
- `CRAWLER_SAVE_HTML_ARTIFACT`
- `CRAWLER_CAPTURE_SCREENSHOT`
- `MODEL_PROVIDER`
- `MODEL_NAME`
- `REPORT_MODEL_NAME`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS`
- `EMBEDDING_API_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_REQUEST_TIMEOUT_SECONDS`
- `EMBEDDING_PROVIDER_FALLBACK_ENABLED`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_USE_MOCKS`

不要把真实 API Key、Cookie、代理账号或生产数据库密码提交到仓库。真实部署时通过 `.env`、GitHub Actions secrets 或 secret manager 注入。

Day34 以后，Compose 默认仍使用 `EMBEDDING_PROVIDER=fake`，用于无密钥环境下验证服务拓扑。真实部署时如果要启用 embedding API，需要显式配置：

```env
EMBEDDING_PROVIDER=openai-compatible
EMBEDDING_API_KEY=...
EMBEDDING_API_BASE_URL=https://api.openai.com/v1
```

显式启用真实 provider 但缺少 `EMBEDDING_API_KEY` 时，后端会 fail-fast。不要在生产环境默认打开 `EMBEDDING_PROVIDER_FALLBACK_ENABLED`，否则会掩盖真实 provider 配置错误。

## 当前验证边界

Day 25 已验证：

- `tests/test_day25_compose_contract.py`：4 passed。
- `docker compose config`：通过。
- Docker CLI：`Docker version 29.3.1`。
- Docker Compose：`Docker Compose version v5.1.1`。

Day 25 未完成真实 build / up，原因是当前 Docker Desktop Linux engine 未运行：

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

后续 Docker Desktop 启动后，需要补跑：

```powershell
docker compose build api frontend
docker compose up -d
curl http://localhost:8000/api/health
docker compose ps
```

## 回滚策略

回滚不是只退代码，还要检查数据和任务状态：

- 保留数据库迁移脚本和回滚说明。
- 保留上一阶段可用 commit/tag。
- 高风险变更前创建 `backup/*` 分支。
- 数据库迁移必须说明是否向后兼容。
- Worker 必须能处理旧任务，或者显式标记旧任务不可恢复。
- 前端必须能读取旧报告，或者提供报告版本兼容层。

## 与其他文档关系

- 环境细节见 `dev-environment.md`
- Compose 操作见 `docker-compose-runbook.md`
- 发布清单见 `release-checklist.md`
- 测试门槛见 `testing-strategy.md`
- 架构拓扑见 `architecture.md`
