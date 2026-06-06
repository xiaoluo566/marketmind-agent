# API 契约

## 基本原则

- 所有响应统一 envelope
- 成功和失败都要有明确状态
- 长任务必须返回 `task_id`
- 所有输入都要先过 Pydantic 校验

## 建议接口

- `POST /api/tasks`：创建分析任务
- `GET /api/tasks/{task_id}`：查看任务状态
- `GET /api/tasks/{task_id}/events`：查看事件流
- `GET /api/tasks/{task_id}/steps`：查看 Agent 步骤
- `POST /api/tasks/{task_id}/retry`：重试任务
- `GET /api/reports/{report_id}`：查看报告
- `GET /api/reports/{report_id}/evidence`：查看报告证据链
- `POST /api/uploads`：上传手工数据
- `WS /ws/tasks/{task_id}`：实时进度推送

## 当前实现状态

截至 Day 19，后端和前端真实接入状态如下：

| 接口 | 后端状态 | 前端状态 | 备注 |
| --- | --- | --- | --- |
| `POST /api/tasks` | 已实现 | 已真实接入 | 新建任务表单调用，成功后跳转任务详情 |
| `GET /api/tasks/{task_id}` | 已实现 | 已真实接入 | 任务详情页状态快照 |
| `GET /api/tasks/{task_id}/events` | 已实现 | 已真实接入 | 任务详情页事件时间线 |
| `GET /api/reports/{report_id}/evidence` | 已实现 | 待接入详情页 | Day 17 已完成后端证据链 API |
| `GET /api/tasks` | 未实现 | mock fallback | Day 21 历史任务前需要补齐 |
| `GET /api/tasks/{task_id}/steps` | 未实现 | 空数组 fallback | Day 20 任务进度与 Agent step 展示需要补齐 |
| `POST /api/tasks/{task_id}/retry` | 未实现 | 未接入 | 失败恢复能力后续实现 |
| `GET /api/reports` | 未实现 | mock fallback | Day 21 历史报告前需要补齐 |
| `GET /api/reports/{report_id}` | 未实现 | mock fallback | 报告详情页真实化前需要补齐 |
| `GET /api/evidence` | 未实现 | mock fallback | 证据总览页后续实现 |
| `POST /api/uploads` | 未实现 | 未接入 | 手工数据上传后续实现 |
| `WS /ws/tasks/{task_id}` | 未实现 | 未接入 | 第一版继续使用查询/轮询 |

前端 fallback 只用于后端未实现接口，不应掩盖 `POST /api/tasks`、`GET /api/tasks/{task_id}` 和 `GET /api/tasks/{task_id}/events` 的真实错误。

## 接口细化

### `POST /api/tasks`

职责：只创建任务和投递异步队列，不直接执行爬虫或模型调用。

Day 4 的实现范围是“契约先行”：只完成参数校验、生成 `task_id` 和返回统一 envelope。

Day 5 开始接入 Celery + Redis：API 创建任务状态快照，投递 Celery 后返回 `queued`，Worker 负责把状态推进到 `running` / `completed`。

Day 6 开始补任务进度事件流：API 和 Worker 每次关键状态变化都会写入统一事件格式，前端后续可以直接消费事件列表，而不是解析日志。
Day 7 已把关键任务状态和事件同步到 PostgreSQL，形成长期审计和恢复层。Redis 仍然承担实时进度读取职责。
Day 8 开始接入 crawler 最小采集：`public_url` 任务会在 Worker 中进入采集阶段，成功写入 `crawl completed` 事件，失败写入 `crawl failed` 事件并标记任务失败。
Day 9 开始把 crawler 成功结果写入 PostgreSQL：`crawl completed` 事件的 payload 会追加 `persisted` 字段，包含 `product_id`、`page_id`、`artifact_ids` 和 `review_ids`。

输入：

- `target`
- `mode`
- `priority`
- `source_type`
- `options`

输出：

- `task_id`
- `status`
- `trace_id`
- `queue_task_id`

失败：

- 队列或 Redis 状态缓存不可用时返回 `QUEUE_UNAVAILABLE`

### `GET /api/tasks/{task_id}/events`

职责：给前端展示任务时间线。事件来源包括 API、worker、crawler、agent、report。

输出建议按时间排序，包含：

- `task_id`
- `events`
- `event_id`
- `status`
- `event_type`
- `message`
- `payload`
- `trace_id`
- `created_at`

每条事件建议至少包含：

- `event_id`
- `task_id`
- `status`
- `event_type`
- `message`
- `payload`
- `trace_id`
- `created_at`

Day 6 事件来源：

- API 创建任务时写入 `received`
- API 投递成功后写入 `queued`
- API 投递失败时写入 `failed`，`event_type=error`，payload 内包含 `error_code`
- Worker 开始执行时写入 `running`
- Worker 最小任务结束时写入 `completed`

Day 8 事件来源：

- Crawler 开始执行时写入 `event_type=crawler`、`message=crawl started`
- Crawler 成功时写入 `event_type=crawler`、`message=crawl completed`，payload 包含标题、价格、评分、文本预览、评论摘要、HTML artifact 引用和持久化 ID
- Crawler 失败时写入 `event_type=crawler_error`、`message=crawl failed`，payload 包含 `error_code`、失败原因和可选失败 HTML artifact 引用

失败：

- `EVENT_STORE_UNAVAILABLE`：事件缓存或事件写入层不可用

### `GET /api/tasks/{task_id}/steps`

职责：给调试页展示 Agent 执行细节。生产展示时可以隐藏 thought，只展示 tool 和 observation 摘要。

### `POST /api/tasks/{task_id}/retry`

职责：只允许重试失败或可恢复状态的任务。重试时必须记录新的 `agent_run_id`，不能覆盖旧记录。

### `GET /api/reports/{report_id}/evidence`

职责：根据报告记录中的 `evidence_refs` 回查结构化证据链，供前端报告详情页展示“这条结论来自哪里”。

Day 17 实现范围：

- 查询 `reports` 表获取 `task_id` 和 `evidence_refs`。
- 支持 `chunk:{chunk_id}`、`review:{review_id}`、`artifact:{artifact_id}`、`step:{step_id}`。
- 每个 evidence source 都返回 `available`、`source_type`、`content_preview`、`source_url`、`parent_refs` 和 `metadata`。
- 不存在或跨任务的 evidence ref 返回 `available=false`，并写入 `missing_reason`。

输出：

- `report_id`
- `task_id`
- `evidence_refs`
- `sources`
- `missing_refs`

失败：

- `REPORT_NOT_FOUND`：报告不存在。

## 响应建议

- `success`
- `data`
- `error`
- `message`
- `trace_id`

## 约束

- API 不直接执行重任务
- API 不写业务判断
- API 只做参数接入、调度和查询
- `GET /api/tasks/{task_id}` 优先读取 Redis 状态快照，Redis 缺失时可回退到 PostgreSQL 持久化任务记录
- `GET /api/tasks/{task_id}/events` 优先读取 Redis 实时事件层，Redis 为空或不可用时可回退到 PostgreSQL 历史事件

## 错误码建议

- `INVALID_TARGET`
- `TASK_NOT_FOUND`
- `TASK_NOT_RETRYABLE`
- `QUEUE_UNAVAILABLE`
- `EVENT_STORE_UNAVAILABLE`
- `REPORT_NOT_FOUND`
- `VALIDATION_FAILED`
- `INTERNAL_ERROR`

## 与其他文档关系

- 请求响应 JSON 示例见 `data-contract-examples.md`
- 表结构见 `data-model.md`
- 前端消费方式见 `ui-console-spec.md`
- 错误日志见 `observability.md`
