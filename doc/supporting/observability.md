# 可观测性

## 需要记录的内容

- 请求 ID
- 任务 ID
- Agent run ID
- 工具调用参数
- 工具调用结果
- 重试次数
- 失败阶段
- 关键耗时

## 结构化日志字段

- `timestamp`
- `level`
- `service`
- `trace_id`
- `task_id`
- `agent_run_id`
- `event`
- `duration_ms`
- `error_code`
- `message`

## 日志分级

- `INFO`：正常流程
- `WARNING`：可恢复异常
- `ERROR`：任务失败或模块异常

## 重点指标

- 单任务耗时
- 成功率
- 重试率
- 结构化输出修复率
- 爬虫被拦截率
- 报告生成时长

## 最低要求

- 每一步都能定位
- 每次失败都能复现
- 每个任务都能追踪全链路

## 调试视角

如果用户说“任务卡住了”，排查顺序应该是：

1. API 是否创建了任务
2. Celery 是否拿到了任务
3. Worker 是否写入了 task event
4. Agent 是否写入了 step
5. 工具是否开始运行
6. 数据库是否写入结果
7. 前端是否正确读取状态

## Day 20 前端可观测性闭环

Day 20 已把“任务卡住了”的第一层排查入口放到任务详情页：

- 顶部状态卡读取 `GET /api/tasks/{task_id}`。
- 事件时间线读取 `GET /api/tasks/{task_id}/events`。
- Agent steps 表格读取 `GET /api/tasks/{task_id}/steps`。
- 前端轮询默认 5 秒一次，终态自动停止。
- 刷新失败时保留已有数据并展示错误码。
- 任务失败时优先展示 `task.error_code` 和 `task.error_message`。

这不是最终 LLMOps 监控，只是 Day 20 的任务级观测闭环。后续 Day 22 还需要补结构化日志、日志等级、trace 搜索和错误分类统计。

## Day 21 历史复盘入口

Day 21 已补齐历史任务和历史报告真实接口，可观测性开始从“当前任务排查”扩展到“历史任务复盘”：

- `GET /api/tasks` 可以查到成功、失败和运行中的历史任务。
- 历史任务保留 `trace_id`、`error_code`、`error_message`、`created_at`、`updated_at`。
- 失败任务不会从历史列表消失，便于后续统计失败类型。
- `GET /api/reports` 可以按报告维度回看历史分析产物。
- `GET /api/reports/{report_id}` 可以打开旧报告。
- `GET /api/reports/{report_id}/evidence` 可以在报告详情页回看 evidence chain。

这为 Day 22 的日志和错误分类提供了入口：日志不是孤立文本，而应该能和 `task_id`、`trace_id`、`report_id`、`agent_run_id` 关联起来。

## Day 22 结构化错误日志

Day 22 把可观测性从“任务事件可看”推进到“错误原因可查”：

- 新增 `backend/app/observability/logging.py`，统一输出结构化 JSON 日志。
- 新增 `backend/app/observability/sanitization.py`，对 token、secret、authorization、api key 等敏感字段递归脱敏。
- 新增 `backend/app/observability/error_store.py`，提供 `InMemoryErrorLogStore` 和 `SQLAlchemyErrorLogStore`。
- API 请求完成后返回 `X-Request-Duration-Ms`，便于快速判断请求慢还是后台任务慢。
- API 异常处理器会把 `AppError`、`HTTPException` 和 Pydantic validation error 写入 `error_logs`。
- Worker 的 Crawler 失败写入 `layer=crawler`，爬虫结果入库失败写入 `layer=database`。
- 新增 `GET /api/observability/errors`，支持按 `trace_id` 或 `task_id` 查询结构化错误。

### 错误层级

当前 `ErrorLayer` 包含：

| layer | 含义 | 常见错误 |
| --- | --- | --- |
| `api` | FastAPI 参数、路由和统一异常 | `VALIDATION_FAILED`、`QUEUE_UNAVAILABLE` |
| `queue` | Celery / Redis 队列投递 | `QUEUE_UNAVAILABLE` |
| `worker` | 后台任务执行容器 | `WORKER_FAILED` |
| `agent` | ReAct 状态机和工具调度 | `TOOL_EXECUTION_FAILED` |
| `crawler` | Playwright / HTML 采集 | `ACCESS_BLOCKED`、`EMPTY_CONTENT` |
| `rag` | embedding 和语义检索 | `EMBEDDING_FAILED` |
| `report` | 结构化报告生成 | `REPORT_GENERATION_FAILED` |
| `database` | SQLAlchemy / PostgreSQL 写入 | `CRAWL_PERSISTENCE_FAILED` |

### 排查顺序

如果用户说“任务失败了”，Day 22 后的排查顺序是：

1. 在历史任务或任务详情里找到 `task_id` 和 `trace_id`。
2. 调用 `GET /api/tasks/{task_id}/events` 看业务状态停在哪一步。
3. 调用 `GET /api/observability/errors?task_id={task_id}` 看结构化错误。
4. 如果任务跨 API 和 Worker 多段排查，调用 `GET /api/observability/errors?trace_id={trace_id}`。
5. 根据 `layer` 判断是 API、队列、Worker、Crawler、RAG、Report 还是 Database。
6. 根据 `error_code` 决定是用户输入问题、可重试依赖问题，还是代码/数据库问题。

### 为什么错误表不替代日志

`error_logs` 用于保存重要失败，方便前端调试页、历史复盘和面试演示。

结构化应用日志用于保存更细粒度的运行事件，例如请求完成、worker 开始、worker 完成。它可以接入文件、标准输出、Loguru、OpenTelemetry 或集中日志平台。

两者共同构成第一版可观测性：

- 日志负责连续过程。
- 错误表负责可查询的失败事实。

## 与其他文档关系

- 任务状态字段见 `data-model.md`
- 前端展示见 `ui-console-spec.md`
- 发版检查见 `release-checklist.md`
