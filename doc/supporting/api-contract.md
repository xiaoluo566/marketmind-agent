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
- `GET /api/tasks`：查看历史任务
- `POST /api/tasks/{task_id}/retry`：重试任务
- `GET /api/reports`：查看历史报告
- `GET /api/reports/{report_id}`：查看报告
- `GET /api/reports/{report_id}/evidence`：查看报告证据链
- `GET /api/observability/errors`：按 `trace_id` 或 `task_id` 查询结构化错误
- `POST /api/uploads`：上传手工数据
- `WS /ws/tasks/{task_id}`：实时进度推送

## 当前实现状态

截至 Day 22，后端和前端真实接入状态如下：

| 接口 | 后端状态 | 前端状态 | 备注 |
| --- | --- | --- | --- |
| `POST /api/tasks` | 已实现 | 已真实接入 | 新建任务表单调用，成功后跳转任务详情 |
| `GET /api/tasks/{task_id}` | 已实现 | 已真实接入 | 任务详情页状态快照 |
| `GET /api/tasks/{task_id}/events` | 已实现 | 已真实接入 | 任务详情页事件时间线 |
| `GET /api/tasks/{task_id}/steps` | 已实现 | 已真实接入 | 返回脱敏 Agent step 摘要，任务详情页轮询刷新 |
| `GET /api/reports/{report_id}/evidence` | 已实现 | 已真实接入报告详情页 | 返回结构化证据链，Agent step metadata 已脱敏 |
| `GET /api/tasks` | 已实现 | 已真实接入 | 历史任务列表，支持状态、时间、分页 |
| `GET /api/reports` | 已实现 | 已真实接入 | 历史报告列表，返回 task_status、risk_score、evidence_count |
| `GET /api/reports/{report_id}` | 已实现 | 已真实接入 | 报告详情，返回 sections、Markdown 和 evidence refs |
| `GET /api/observability/errors` | 已实现 | 未接入 UI | Day 22 调试接口，支持按 trace_id 或 task_id 查询结构化错误 |
| `POST /api/tasks/{task_id}/retry` | 未实现 | 未接入 | 失败恢复能力后续实现 |
| `GET /api/evidence` | 未实现 | mock fallback | 证据总览页后续实现 |
| `POST /api/uploads` | 未实现 | 未接入 | 手工数据上传后续实现 |
| `WS /ws/tasks/{task_id}` | 未实现 | 未接入 | 第一版继续使用查询/轮询 |

前端 fallback 只用于后端未实现接口或非核心辅助数据，不应掩盖 `POST /api/tasks`、`GET /api/tasks/{task_id}`、`GET /api/tasks/{task_id}/events`、`GET /api/tasks`、`GET /api/reports`、`GET /api/reports/{report_id}` 和 `GET /api/reports/{report_id}/evidence` 的真实错误。`GET /api/tasks/{task_id}/steps` 失败时前端可降级为空数组，避免进度详情页整体不可用。

## 接口细化

### `POST /api/tasks`

职责：只创建任务和投递异步队列，不直接执行爬虫或模型调用。

Day 4 的实现范围是“契约先行”：只完成参数校验、生成 `task_id` 和返回统一 envelope。

Day 5 开始接入 Celery + Redis：API 创建任务状态快照，投递 Celery 后返回 `queued`，Worker 负责把状态推进到 `running` / `completed`。

Day 6 开始补任务进度事件流：API 和 Worker 每次关键状态变化都会写入统一事件格式，前端后续可以直接消费事件列表，而不是解析日志。
Day 7 已把关键任务状态和事件同步到 PostgreSQL，形成长期审计和恢复层。Redis 仍然承担实时进度读取职责。
Day 8 开始接入 crawler 最小采集：`public_url` 任务会在 Worker 中进入采集阶段，成功写入 `crawl completed` 事件，失败写入 `crawl failed` 事件并标记任务失败。
Day 9 开始把 crawler 成功结果写入 PostgreSQL：`crawl completed` 事件的 payload 会追加 `persisted` 字段，包含 `product_id`、`page_id`、`artifact_ids` 和 `review_ids`。

阶段审计补充：

- `source_type=public_url` 时，`target` 必须是 `http` 或 `https`。
- `public_url` 禁止 localhost、`.local`、loopback、private、link-local、reserved、multicast、unspecified 地址。
- 这条校验用于降低把后端 crawler 变成内网探测工具的 SSRF 风险。

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

### `GET /api/tasks`

职责：给历史任务页展示过去创建过的任务，包括成功、失败、运行中和取消的任务。

Day 21 实现范围：

- 历史查询以 PostgreSQL 为事实来源。
- 支持 `status` 重复查询参数。
- 支持 `created_after` 和 `created_before`。
- 支持 `limit` 和 `offset`。
- 返回 `items`、`limit`、`offset`、`total`。
- 按 `created_at desc`、`task_id desc` 排序。
- 失败任务不会从列表中消失。

输出：

- `items`
- `limit`
- `offset`
- `total`

每个 item 使用 `TaskStatusData`，包含：

- `task_id`
- `status`
- `trace_id`
- `target`
- `mode`
- `priority`
- `source_type`
- `queue_task_id`
- `error_code`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`
- `updated_at`

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

Day 20 实现范围：

- 先确认任务存在，不存在返回 `TASK_NOT_FOUND`。
- 根据 `task_id` 查询所有 `agent_steps`。
- 按 Agent run 创建时间和 `step_index` 升序返回。
- 不暴露完整 `thought`。
- `thought` 类型只返回 `input_summary=Thought recorded`。
- tool step 只返回 tool 名称、输入 key 摘要、observation 摘要、耗时和错误码。

输出：

- `task_id`
- `steps`
- `step_id`
- `agent_run_id`
- `step_index`
- `step_type`
- `tool_name`
- `status`
- `duration_ms`
- `input_summary`
- `observation_summary`
- `error_code`

### `POST /api/tasks/{task_id}/retry`

职责：只允许重试失败或可恢复状态的任务。重试时必须记录新的 `agent_run_id`，不能覆盖旧记录。

### `GET /api/reports`

职责：给报告列表页展示已经生成的结构化报告。

Day 21 实现范围：

- 查询 `reports` 并关联 `tasks` 取 `task_status`。
- 支持 `status`、`task_status`、`created_after`、`created_before`、`limit`、`offset`。
- 返回 `items`、`limit`、`offset`、`total`。
- 从 `reports.evidence_refs` 计算 `evidence_count`。
- 从 `content_json.metadata.analysis_scorecard.overall_risk_score` 读取 `risk_score`。
- 将风险分映射为 `low`、`medium`、`high`、`critical`。

输出 item：

- `report_id`
- `task_id`
- `task_status`
- `title`
- `summary`
- `status`
- `risk_level`
- `risk_score`
- `evidence_count`
- `created_at`
- `updated_at`
- `schema_version`

### `GET /api/reports/{report_id}`

职责：给报告详情页返回可渲染的报告结构。

Day 21 实现范围：

- 缺失报告返回 `REPORT_NOT_FOUND`。
- 返回报告列表字段。
- 额外返回 `sections`、`content_markdown`、`evidence_refs`。
- `sections` 从 `content_json.sections` 映射，不从 Markdown 反解析。

`sections` 字段：

- `title`
- `body`
- `evidence_ids`

注意：当前前端历史命名仍为 `evidence_ids`，但真实后端值是 `chunk:xxx`、`step:xxx` 这样的 evidence refs。报告详情页已经通过 `GET /api/reports/{report_id}/evidence` 回查证据链，后续还需要把字段名统一为 `evidence_refs`。

### `GET /api/reports/{report_id}/evidence`

职责：根据报告记录中的 `evidence_refs` 回查结构化证据链，供前端报告详情页展示“这条结论来自哪里”。

Day 17 实现范围：

- 查询 `reports` 表获取 `task_id` 和 `evidence_refs`。
- 支持 `chunk:{chunk_id}`、`review:{review_id}`、`artifact:{artifact_id}`、`step:{step_id}`。
- 每个 evidence source 都返回 `available`、`source_type`、`content_preview`、`source_url`、`parent_refs` 和 `metadata`。
- 不存在或跨任务的 evidence ref 返回 `available=false`，并写入 `missing_reason`。

阶段审计补充：

- 报告详情页已经调用该接口，不再用全局 `/api/evidence` mock 数据拼报告证据。
- `agent_step` 类型证据只返回 `tool_input_keys`、`tool_output_keys`、`error_code` 等摘要元数据。
- `agent_step` 类型证据不返回完整 `tool_input` 和 `tool_output`，避免把内部工具参数或模型中间产物直接暴露到前端。

输出：

- `report_id`
- `task_id`
- `evidence_refs`
- `sources`
- `missing_refs`

失败：

- `REPORT_NOT_FOUND`：报告不存在。

### `GET /api/observability/errors`

职责：给调试页和本地排障提供结构化错误查询入口。该接口查询 `error_logs`，不替代任务事件流；任务生命周期仍通过 `GET /api/tasks/{task_id}/events` 查看。

Day 22 实现范围：

- 支持按 `trace_id` 查询同一请求链路的错误。
- 支持按 `task_id` 查询同一业务任务的错误。
- 支持 `trace_id + task_id` 组合过滤。
- 缺少筛选条件时返回 `OBSERVABILITY_FILTER_REQUIRED`。
- 返回统一 envelope。

查询参数：

- `trace_id`：可选。
- `task_id`：可选。
- `limit`：默认 50，范围 1-100。

输出：

- `items`
- `limit`
- `total`

每个 item：

- `error_id`
- `task_id`
- `trace_id`
- `layer`
- `error_code`
- `message`
- `details`
- `created_at`

失败：

- `OBSERVABILITY_FILTER_REQUIRED`：缺少 `trace_id` 和 `task_id`。

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
- `OBSERVABILITY_FILTER_REQUIRED`
- `VALIDATION_FAILED`
- `INTERNAL_ERROR`

## 与其他文档关系

- 请求响应 JSON 示例见 `data-contract-examples.md`
- 表结构见 `data-model.md`
- 前端消费方式见 `ui-console-spec.md`
- 错误日志见 `observability.md`
