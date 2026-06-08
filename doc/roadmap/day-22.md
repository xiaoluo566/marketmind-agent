# Day 22 - 日志、错误分类与可观测性闭环

## 当天目标

Day 22 的目标不是做一个完整监控平台，而是把 Day 1-21 已经形成的任务链路补上“失败后能定位”的工程能力：

- API 层能看到每次请求的 `trace_id` 和请求耗时。
- Worker / Crawler 失败时能写入结构化错误记录。
- 错误能按 `layer`、`error_code`、`task_id`、`trace_id` 查询。
- 日志和错误表都要做敏感字段脱敏，避免 API key、token、authorization 进入调试输出。
- 文档里形成第一版“任务卡住 / 任务失败”排查手册。

这一天承接 Day 20 的任务详情页和 Day 21 的历史任务/报告入口。Day 20 解决“当前任务进展在哪里”，Day 21 解决“历史任务和报告能不能回看”，Day 22 解决“失败后能不能知道是哪一层坏了”。

## 前置依赖

- `day-20.md`：任务详情页已经能读取任务状态、事件和 Agent steps。
- `day-21.md`：历史任务、历史报告和报告详情已经真实接入。
- `../supporting/observability.md`：定义可观测性字段、日志等级、排查顺序。
- `../supporting/api-contract.md`：统一 envelope、错误码和 trace 约束。
- `../supporting/data-model.md`：`error_logs` 表已经在 Day 3 初始迁移中创建。

## 当天交付物

### 1. 结构化日志入口

新增 `backend/app/observability/logging.py`：

- `log_observability_event()` 统一输出 JSON 字符串日志。
- 字段包括 `timestamp`、`level`、`service`、`trace_id`、`task_id`、`agent_run_id`、`event`、`duration_ms`、`error_code`、`layer`、`message`、`details`。
- 不额外引入第三方日志依赖，第一版先基于 Python 标准库 `logging`，降低部署复杂度。
- 后续如果要接 Loguru、OpenTelemetry 或 ELK，只需要替换这一层。

### 2. 敏感字段脱敏

新增 `backend/app/observability/sanitization.py`：

- 对 `api_key`、`apikey`、`authorization`、`access_token`、`refresh_token`、`password`、`secret`、`token` 等 key 做递归脱敏。
- 支持 dict、list、tuple、set 和 Exception。
- `error_logs.details` 和结构化日志 `details` 都复用同一套脱敏逻辑。

这样设计的原因是：可观测性越强，越容易把内部细节打出来。如果没有统一脱敏，后续接入真实模型 API、代理池、登录 cookie 后会很危险。

### 3. `error_logs` 存储层

新增 `backend/app/observability/error_store.py`：

- `ErrorLayer`：`api`、`queue`、`worker`、`agent`、`crawler`、`rag`、`report`、`database`。
- `ErrorLogData`：错误日志数据模型。
- `ErrorLogStore`：存储协议。
- `InMemoryErrorLogStore`：测试和本地注入使用。
- `SQLAlchemyErrorLogStore`：写入 Day 3 已建好的 `error_logs` 表。

当前支持：

- `append(error)`：写入错误。
- `list_for_task(task_id)`：按任务查询。
- `list_for_trace(trace_id)`：按 trace 查询。

`SQLAlchemyErrorLogStore` 不负责创建任务，只记录错误。任务是否存在由调用方和数据库外键约束保证。

### 4. API 请求耗时与错误写入

修改 `backend/app/core/middleware.py`：

- 请求进入时生成或继承 `X-Trace-Id`。
- 请求完成时写回 `X-Trace-Id`。
- 新增 `X-Request-Duration-Ms` 响应头。
- 成功请求写 `api.request.completed` 结构化日志。

修改 `backend/app/core/exceptions.py`：

- `AppError`、`HTTPException`、`RequestValidationError` 进入统一错误 envelope 前，会写 `api.error` 结构化日志。
- 如果 app 上挂了 `error_log_store` 或 `error_log_store_factory`，同步写入 `error_logs`。
- 写错误日志失败不会影响原本 API 响应，只额外输出 `api.error_log_write_failed` 结构化日志。

### 5. Worker / Crawler 错误分类

修改 `backend/app/worker/tasks.py`：

- `process_research_task()` 默认注入 `get_error_log_store()`。
- `run_research_task()` 增加可选 `error_log_store` 参数，保持已有调用兼容。
- Crawler 被拦截、超时、空内容等 `CrawlError` 会写入 `layer=crawler`。
- 爬虫结果持久化失败会写入 `layer=database`。
- 失败事件 payload 增加 `duration_ms`。
- Worker 正常开始和完成会输出 `worker.task.running` / `worker.task.completed` 结构化日志。

### 6. 错误查询 API

新增 `backend/app/api/routes/observability.py`：

```text
GET /api/observability/errors?trace_id=trc_xxx
GET /api/observability/errors?task_id=tsk_xxx
GET /api/observability/errors?trace_id=trc_xxx&task_id=tsk_xxx
```

约束：

- 必须提供 `trace_id` 或 `task_id`，否则返回 `OBSERVABILITY_FILTER_REQUIRED`。
- 默认最多返回 50 条，最大 100 条。
- 返回统一 envelope。
- 每条 item 包含 `error_id`、`task_id`、`trace_id`、`layer`、`error_code`、`message`、`details`、`created_at`。

这个接口是后续前端 LLMOps / 调试页的基础，不在 Day 22 做复杂 UI。

## 实施步骤

1. 写 `tests/test_observability.py`，先约束错误日志存储、脱敏、Worker 失败写入和 API 查询接口。
2. 新增 `app.observability` 包，集中放日志、脱敏和错误存储。
3. 在 FastAPI app 上挂 `error_log_store_factory`。
4. 改造异常处理器，把统一错误 envelope 和错误日志写入串起来。
5. 改造 Worker，让 Crawler 和 Database 失败进入 `error_logs`。
6. 新增 `/api/observability/errors` 查询接口。
7. 更新 `observability.md`、`api-contract.md`、`data-model.md`、开发日志和面试文档。

## 当天选择思考

### 为什么没有一上来接 OpenTelemetry？

OpenTelemetry 更标准，但 Day 22 的主要目标是让当前系统可排查。现在系统还没有容器化部署、没有集中日志平台，也没有多服务指标采集后端。直接引入 OTel 会让配置复杂度超过收益。

当前选择是：

- 先定义统一结构化日志字段。
- 先把错误写入 PostgreSQL 的 `error_logs`。
- 先提供按 trace/task 查询的 API。
- 后续再把 `log_observability_event()` 换成 OTel exporter 或 Loguru sink。

### 为什么错误表和任务事件都要保留？

`task_events` 记录业务生命周期，比如 received、queued、running、crawl started、crawl failed。

`error_logs` 记录排障维度，比如 layer、error_code、duration_ms、path、method、阶段和脱敏 details。

两者不是重复：

- 前端任务详情页优先看 `task_events`，知道任务走到了哪一步。
- 排障和复盘优先看 `error_logs`，知道是哪一层失败、失败码是什么、耗时多少。

### 为什么查询错误日志必须带筛选条件？

错误日志属于运维排查数据，不能默认无边界列出。第一版要求 `trace_id` 或 `task_id` 至少有一个，避免：

- 前端误调用导致全表扫描。
- 本地开发日志太多时页面卡顿。
- 未来多用户场景下误暴露其他任务的错误。

## 验收标准

- `error_logs` 可以持久化 `api`、`crawler`、`database` 等层级错误。
- API 失败响应仍保持统一 envelope，并且写入错误表。
- 成功和失败请求都带 `X-Trace-Id`，请求完成时带 `X-Request-Duration-Ms`。
- Worker 爬虫失败写入 `layer=crawler`、`error_code=ACCESS_BLOCKED` 等分类错误。
- `GET /api/observability/errors` 可按 `trace_id` 或 `task_id` 查询错误。
- 敏感字段在错误日志 details 中被替换成 `[REDACTED]`。

## 验证记录

- `uv run pytest tests\test_observability.py`：6 passed。
- `uv run pytest tests\test_tasks_api.py tests\test_celery_worker.py tests\test_task_persistence.py tests\test_health.py`：25 passed。
- `uv run pytest tests\test_observability.py tests\test_tasks_api.py tests\test_celery_worker.py tests\test_task_persistence.py tests\test_health.py`：29 passed。
- `uv run ruff check backend tests\test_observability.py`：通过。
- `uv run pytest`：114 passed。
- `uv run ruff check backend tests migrations`：通过。
- `uv run alembic heads`：`0002_task_queue_id (head)`。
- `cd frontend; npm run lint`：通过。
- `cd frontend; npm run build`：通过。

## 风险与回退

风险：

- 如果日志 details 继续扩展，仍可能引入新的敏感字段 key。
- API 错误日志写入依赖数据库，数据库完全不可用时只能输出结构化日志，无法持久化。
- 当前错误查询 API 没有鉴权，仍只适合本地开发和简历项目阶段。

回退：

- 如果 `error_logs` 写入影响 API 响应，可以临时移除 `app.state.error_log_store_factory`，保留 envelope。
- 如果查询接口暂时不展示给前端，可以不接 UI，但保留接口和测试。
- 如果后续接入 OpenTelemetry，优先替换 `log_observability_event()`，不要改业务代码。

## 遗留问题

- 当时未提供 `POST /api/tasks/{task_id}/retry`，错误分类暂时只能用于复盘，不能自动恢复；Day 28 已完成后端 retry API，前端入口、Celery countdown 和 Agent step replay 仍未实现。
- `GET /api/observability/errors` 还没有前端页面。
- 还没有跨任务错误统计，例如按 `error_code` 聚合失败次数。
- 还没有 LLM token / cost 维度的指标面板。
- 还没有集中日志平台，当前结构化日志仍输出到应用日志流。

## 关联文档

- 上一天：`day-21.md`
- 下一天：`day-23.md`
- 可观测性：`../supporting/observability.md`
- API 契约：`../supporting/api-contract.md`
- 数据模型：`../supporting/data-model.md`
- 安全：`../supporting/security-compliance.md`
- 面试文档：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 实现 Day 22 结构化错误日志和观测接口`
