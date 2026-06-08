# Day 25 - Docker Compose 与环境固化

## 当天目标

Day 25 的目标是把项目从“在当前开发机上能跑”推进到“别人按文档也能启动同一套服务”。

这一天重点不是新增业务能力，而是固化运行环境：

1. 明确 PostgreSQL / pgvector、Redis、API、Worker、前端的服务边界。
2. 用 Docker Compose 描述服务依赖顺序、健康检查、端口和数据卷。
3. 用 Dockerfile 固化后端和前端构建过程。
4. 用 `.env.example` 说明必需环境变量。
5. 用自动化测试约束 compose 文件，防止后续部署配置漂移。

## 前置依赖

- `day-24.md`：主链路集成回归样例已完成。
- `../supporting/deployment.md`：部署策略文档。
- `../supporting/dev-environment.md`：本地开发环境约定。
- `../supporting/testing-strategy.md`：测试分层边界。

## 当天交付物

- `docker-compose.yml`
- `Dockerfile.backend`
- `frontend/Dockerfile`
- `.dockerignore`
- `frontend/.dockerignore`
- `.env.example` compose 变量补充
- `tests/test_day25_compose_contract.py`
- `doc/supporting/docker-compose-runbook.md`
- 部署文档、开发日志和面试文档同步更新

## 实际完成内容

### 1. Docker Compose 服务编排

新增 `docker-compose.yml`，包含 6 个服务：

| 服务 | 作用 | 关键点 |
| --- | --- | --- |
| `postgres` | PostgreSQL + pgvector | 使用 `pgvector/pgvector:pg16`，持久化到 `postgres_data` |
| `redis` | Redis broker/cache | 使用 `redis:7.4-alpine`，持久化到 `redis_data` |
| `migrate` | 数据库迁移 | 等待 PostgreSQL healthy 后执行 `uv run alembic upgrade head` |
| `api` | FastAPI 网关 | 等待 PostgreSQL、Redis 和 migrate 成功后启动 |
| `worker` | Celery Worker | 与 API 使用同一组数据库和 Redis 地址 |
| `frontend` | Next.js 控制台 | 等待 API healthy 后启动 |

服务依赖顺序：

```text
postgres healthy
redis healthy
postgres healthy -> migrate completed
migrate completed + redis healthy -> api / worker
api healthy -> frontend
```

### 2. 后端 Dockerfile

新增 `Dockerfile.backend`：

- 基础镜像：`python:3.12-slim`
- 使用 `uv sync --frozen --no-dev --no-install-project` 固定依赖安装。
- 复制 `backend/`、`migrations/`、`alembic.ini`、`pyproject.toml`、`uv.lock`。
- 设置 `PYTHONPATH=/app/backend`。
- 安装 Playwright Chromium 依赖：`uv run playwright install --with-deps chromium`。
- 默认启动命令：

```text
uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

选择 `--no-install-project` 是因为当前项目还没有作为 Python package 打包，容器内运行依赖 `PYTHONPATH=/app/backend`。这样可以避免 Docker 构建时因为项目 package 元数据不完整而失败。

### 3. 前端 Dockerfile

新增 `frontend/Dockerfile`：

- 基础镜像：`node:22-slim`
- 使用 `npm ci` 固定依赖安装。
- build 阶段注入：
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
  - `NEXT_PUBLIC_USE_MOCKS=false`
- runner 阶段通过 `npm run start` 启动 Next.js。

前端容器暴露 `3000`，浏览器访问前端页面时仍通过宿主机 `http://localhost:8000` 调用 API。

### 4. 环境变量和忽略文件

`.env.example` 新增 compose 相关变量：

```text
POSTGRES_USER=marketmind
POSTGRES_PASSWORD=marketmind
POSTGRES_DB=marketmind
POSTGRES_PORT=5432
REDIS_PORT=6379
API_PORT=8000
FRONTEND_PORT=3000
```

新增 `.dockerignore` 和 `frontend/.dockerignore`，避免把以下内容送入 Docker build context：

- `.env`
- `.venv`
- `node_modules`
- `.next`
- `data`
- `tmp`
- `.git`
- Stitch 原始导出目录

### 5. Compose 契约测试

新增 `tests/test_day25_compose_contract.py`，覆盖：

- `docker-compose.yml` 必须声明 `postgres`、`redis`、`migrate`、`api`、`worker`、`frontend`。
- compose 必须使用 pgvector PostgreSQL 和 Redis 7。
- compose 必须包含健康检查和 `service_completed_successfully` 依赖。
- compose 必须执行 Alembic 迁移。
- compose 必须启动 Celery worker。
- API、Worker 必须使用容器内部的 `postgres` 和 `redis` 地址。
- 后端 Dockerfile 必须使用 Python 3.12、uv、Playwright Chromium 和 Uvicorn。
- 前端 Dockerfile 必须使用 Node 22、`npm ci`、`npm run build`、`npm run start`。
- `.env.example` 和 `.dockerignore` 必须保护本地运行状态和敏感配置。

## 当天为什么这样选

### 为什么 Day 25 先做 Compose，而不是直接 CI？

CI 的前提是启动方式稳定。如果本地还没有一个可描述、可复用、可检查的运行拓扑，CI 里只会复制一堆临时命令。Day 25 先把服务编排固化，Day 26 再把这些命令放进 GitHub Actions，更符合工程顺序。

### 为什么增加 `migrate` 服务？

如果 API 容器启动时自动跑迁移，API 的生命周期会混合“建表”和“提供服务”两件事，失败时不容易判断是迁移失败还是 API 失败。

独立 `migrate` 服务的好处：

- 迁移步骤可单独观察。
- API 和 Worker 可以明确依赖 `migrate` 成功完成。
- 后续 CI 可以复用同一个迁移命令。
- 失败时日志更清楚。

### 为什么没有把真实 API Key 写进 compose？

当前项目的真实模型接入还没有完成，Day 25 只固化基础设施和已有主链路。真实 API Key、Cookie、代理账号都不应该进入 Git。后续真实 LLM / embedding provider 接入时，只通过 `.env` 或 secret manager 注入。

### 为什么 Day 25 没有强行完成真实容器构建？

本机当前 `docker compose config` 可执行，Docker CLI 和 Compose 版本可读取，但 Docker Desktop Linux engine 没有启动。执行 `docker compose build api frontend` 时失败在 daemon 连接：

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

这说明当前阻塞是 Docker Desktop daemon 状态，不是 compose 语法错误。Day 25 已完成静态配置、契约测试和 compose config 校验；真实镜像构建与 `docker compose up` 需要在 Docker Desktop Linux engine 启动后补跑，并记录到后续验证日志。

## 验证记录

已执行：

```powershell
uv run pytest tests\test_day25_compose_contract.py
uv run pytest tests\test_day25_compose_contract.py tests\test_day24_integration_flow.py
docker compose config
docker --version
docker compose version
docker compose build api frontend
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
```

结果：

```text
Day 25 compose contract tests: 4 passed
Day 25 + Day 24 targeted tests: 5 passed
docker compose config: passed
Docker version: 29.3.1
Docker Compose version: v5.1.1
docker compose build api frontend: blocked, Docker Desktop Linux engine is not running
Full pytest: 141 passed
Coverage gate: 141 passed, backend coverage 90.86%, fail-under 80 reached
Ruff: All checks passed
Alembic heads: 0002_task_queue_id (head)
Frontend lint: passed
Frontend build: passed
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

## 验收标准对照

| 标准 | 当前结果 |
| --- | --- |
| 有一键启动拓扑 | 已有 `docker-compose.yml` |
| API 和 Worker 使用同一数据库 | 已通过 compose env 和契约测试约束 |
| Redis 被用于 Celery 和任务状态 | 已配置 `/1`、`/2`、`/3` 三个 logical DB |
| 数据库迁移明确 | 已有 `migrate` 服务 |
| `.env` 不进入 Git | `.gitignore` 已覆盖，`.dockerignore` 也覆盖 |
| `.env.example` 包含必要变量 | 已补齐 compose 端口和数据库变量 |
| compose 语法可解析 | `docker compose config` 通过 |
| 真实镜像可构建 | 待 Docker Desktop daemon 启动后验证 |

## 遗留问题

- 还没有在 Docker Desktop daemon 启动状态下完成真实镜像 build。
- 还没有执行 `docker compose up -d` 的端到端验证。
- 还没有用容器内 API 提交样例任务。
- 后续真实 LLM / embedding provider 还需要 secret 注入策略。
- Playwright Chromium 安装会让后端镜像变大，后续可考虑拆 `crawler-worker` 独立镜像。

## 关联文档

- 上一天：`day-24.md`
- 下一天：`day-26.md`
- 部署：`../supporting/deployment.md`
- Compose 运行手册：`../supporting/docker-compose-runbook.md`
- 安全：`../supporting/security-compliance.md`
- 测试：`../supporting/testing-strategy.md`

## 建议提交

```text
feat: 增加 Day 25 Docker Compose 启动拓扑
```
