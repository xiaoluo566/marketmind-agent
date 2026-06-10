# 开发环境

## 本机假设

- Windows 为主
- PowerShell 可用
- Git 已安装
- GitHub CLI 已登录
- Python 和 Node 只在需要时启用

## 推荐工具链

- Python 3.11 或 3.12
- `uv` 或 `venv` 管理 Python 环境
- Docker Desktop 负责本地服务
- GitHub CLI 负责仓库创建、推送和版本查看
- Playwright 负责浏览器自动化

## 本地目录约定

- 仓库根目录：项目代码和文档
- `doc/`：规划和规范
- `src/`：后续实现代码
- `tests/`：测试
- `data/`：本地样例数据和临时输出

## 环境变量约定

- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `TASK_STATUS_REDIS_URL`
- `TASK_STATUS_TTL_SECONDS`
- `CRAWLER_ARTIFACT_DIR`
- `CRAWLER_SAVE_HTML_ARTIFACT`
- `CRAWLER_CAPTURE_SCREENSHOT`
- `DEFAULT_LOCAL_USER_ID`
- `DEFAULT_LOCAL_USER_EMAIL`
- `DEFAULT_LOCAL_PROJECT_ID`
- `DEFAULT_LOCAL_PROJECT_NAME`
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
- `APP_ENV`
- `LOG_LEVEL`

默认开发配置：

- `MODEL_NAME=gpt-5.4-mini`
- `REPORT_MODEL_NAME=gpt-5.5`
- `EMBEDDING_PROVIDER=fake`
- `EMBEDDING_MODEL=text-embedding-3-small`
- `EMBEDDING_DIMENSIONS=1536`
- `EMBEDDING_API_BASE_URL=https://api.openai.com/v1`
- `EMBEDDING_API_KEY=`，本地默认留空，不提交真实密钥
- `EMBEDDING_REQUEST_TIMEOUT_SECONDS=15`
- `EMBEDDING_PROVIDER_FALLBACK_ENABLED=false`
- `CELERY_BROKER_URL=redis://localhost:6379/1`
- `CELERY_RESULT_BACKEND=redis://localhost:6379/2`
- `TASK_STATUS_REDIS_URL=redis://localhost:6379/3`
- `CRAWLER_ARTIFACT_DIR=data/artifacts/crawler`
- `CRAWLER_SAVE_HTML_ARTIFACT=true`
- `CRAWLER_CAPTURE_SCREENSHOT=false`
- `DEFAULT_LOCAL_USER_ID=usr_local`
- `DEFAULT_LOCAL_PROJECT_ID=prj_default`

## 本地启动约定

Day 5 开始后端依赖 Redis 才能投递真实后台任务。Windows 本机开发时，Celery worker 建议使用 `solo` pool，避免默认 prefork 在 Windows 下不稳定。

Day 7 开始任务状态和事件会同步写入 PostgreSQL，所以本地真实联调还需要 `DATABASE_URL` 指向可用的 PostgreSQL 数据库，并先执行 Alembic 迁移。

Day 8 开始接入 Playwright 最小采集。首次运行真实浏览器采集前，需要安装 Chromium：

```powershell
uv run playwright install chromium
```

当前 HTML artifact 默认写入 `data/artifacts/crawler`，该目录属于本地运行产物，不进入 Git。

Day34 以后，本地默认 embedding provider 是 `fake`。如果要验证真实 provider，需要在本机 `.env` 中显式配置：

```env
EMBEDDING_PROVIDER=openai-compatible
EMBEDDING_API_KEY=你的本地密钥
```

不要把 `.env` 提交到 Git。真实 provider 开启后仍要确认 `EMBEDDING_DIMENSIONS=1536` 和数据库 `review_chunks.embedding vector(1536)` 一致。

```powershell
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir backend --reload
uv run celery -A app.worker.celery_app.celery_app worker -Q marketmind --loglevel=INFO --pool=solo
```

## 依赖关系

这个文档与 `deployment.md`、`testing-strategy.md`、`release-checklist.md` 共同决定项目能不能被别人复制起来。

## 开发纪律

- 环境配置先文档化再写代码
- 任何新依赖都要说明用途和可替代方案
- 本机可以跑通后再考虑容器化
