# Docker Compose 运行手册

## 适用场景

这份文档用于 Day 25 之后的本地集成启动。它解决的是“从空环境拉起同一套服务”的问题，不替代日常开发时的 `uvicorn`、`celery`、`npm run dev`。

## 服务拓扑

```text
frontend -> api -> postgres
                 -> redis
worker   -> postgres
worker   -> redis
migrate  -> postgres
```

## 首次启动

```powershell
Copy-Item .env.example .env
docker compose up --build
```

后台启动：

```powershell
docker compose up --build -d
```

## 常用验证

```powershell
docker compose config
docker compose ps
curl http://localhost:8000/api/health
docker compose logs -f api
docker compose logs -f worker
```

## 提交样例任务

后续可以用下面命令验证 API 是否能入队。注意：如果 Docker Desktop 未启动，先不要执行。

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/tasks `
  -ContentType application/json `
  -Headers @{ "X-Trace-Id" = "trc_compose_smoke" } `
  -Body '{
    "target": "https://example.com/products/portable-espresso-maker",
    "mode": "competitive_research",
    "priority": "normal",
    "source_type": "public_url",
    "options": {
      "fixture_html": "<html><body><h1>Portable Espresso Maker</h1><article class=\"review\" data-review-id=\"rev-1\">Pump failed. 1 out of 5</article></body></html>"
    }
  }'
```

## 停止与清理

保留数据：

```powershell
docker compose down
```

删除数据卷：

```powershell
docker compose down -v
```

`down -v` 会删除 PostgreSQL、Redis 和 crawler artifact 数据，只应在确认不需要保留演示数据时执行。

## 当前已验证

- `uv run pytest tests\test_day25_compose_contract.py`：4 passed。
- `docker compose config`：通过。
- `docker --version`：Docker version 29.3.1。
- `docker compose version`：Docker Compose version v5.1.1。

## 当前未验证

真实镜像构建尚未完成，因为本机 Docker Desktop Linux engine 未运行：

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Docker Desktop 启动后，需要补跑：

```powershell
docker compose build api frontend
docker compose up -d
curl http://localhost:8000/api/health
docker compose ps
```

## 排错入口

| 现象 | 优先检查 |
| --- | --- |
| `docker compose config` 失败 | YAML 缩进、变量插值、服务名 |
| API 起不来 | `migrate` 是否成功、`DATABASE_URL` 是否指向 `postgres` |
| Worker 不消费任务 | `CELERY_BROKER_URL` 是否指向 `redis://redis:6379/1` |
| 前端访问不到 API | 浏览器侧 `NEXT_PUBLIC_API_BASE_URL` 是否为 `http://localhost:8000` |
| 采集 artifact 丢失 | `crawler_artifacts` volume 是否被 `down -v` 删除 |
