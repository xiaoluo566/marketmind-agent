# 数据模型

## 核心表

- `users`：用户和权限
- `projects`：项目或选题
- `tasks`：用户提交的任务
- `task_events`：任务状态流
- `agent_runs`：一次 Agent 完整执行
- `agent_steps`：Thought / Action / Observation 级别记录
- `products`：商品基础信息
- `crawled_pages`：页面抓取结果
- `reviews`：评论原始数据
- `review_chunks`：切片后的评论片段
- `embeddings`：向量索引数据
- `reports`：最终报告
- `artifacts`：导出文件、截图、JSON 等附件
- `error_logs`：结构化错误记录

## 推荐字段

### `tasks`

- `id`
- `user_id`
- `project_id`
- `target`
- `mode`
- `status`
- `priority`
- `source_type`
- `options`
- `queue_task_id`
- `trace_id`
- `created_at`
- `updated_at`
- `started_at`
- `finished_at`
- `error_code`
- `error_message`

### `agent_runs`

- `id`
- `task_id`
- `status`
- `model_name`
- `report_model_name`
- `prompt_version`
- `started_at`
- `finished_at`
- `total_tokens`
- `total_cost`

### `agent_steps`

- `id`
- `agent_run_id`
- `task_id`
- `step_index`
- `step_type`
- `thought`
- `tool_name`
- `tool_input`
- `tool_output`
- `observation`
- `status`
- `error_message`
- `created_at`
- `updated_at`
- `started_at`
- `finished_at`

### `task_events`

- `event_id`
- `task_id`
- `status`
- `event_type`
- `message`
- `payload`
- `trace_id`
- `created_at`

### `error_logs`

- `id`
- `task_id`
- `trace_id`
- `layer`
- `error_code`
- `message`
- `details`
- `created_at`

### `reviews`

- `id`
- `product_id`
- `task_id`
- `source_url`
- `rating`
- `content`
- `author_hash`
- `published_at`
- `raw_payload`

### `review_chunks`

- `id`
- `review_id`
- `task_id`
- `chunk_index`
- `content`
- `embedding`
- `embedding_model`
- `embedding_dimensions`
- `metadata`

## 关键关系

- 一个 `task` 对应多条 `task_events`
- 一个 `task` 可以有多次 `agent_runs`
- 一个 `agent_run` 对应多条 `agent_steps`
- 一个 `product` 可以关联多个 `reviews`
- 一个 `review` 可以拆成多个 `review_chunks`
- 一个 `task` 可以关联多条 `error_logs`

## 设计要求

- 所有记录必须可追溯到任务 ID
- 所有长任务状态必须可恢复
- 所有重要数据都要保留时间戳、来源和版本
- 需要记录失败原因、重试次数和最终结果

## 预留字段

- `trace_id`
- `source_url`
- `source_type`
- `model_name`
- `report_model_name`
- `prompt_version`
- `schema_version`
- `embedding_model`
- `embedding_dimensions`

## 状态枚举建议

### 任务状态

- `received`
- `queued`
- `running`
- `waiting_retry`
- `completed`
- `failed`
- `cancelled`

### Agent 步骤状态

- `pending`
- `running`
- `success`
- `failed`
- `skipped`

## 索引建议

- `tasks(status, created_at)`
- `task_events(task_id, created_at)`
- `agent_steps(agent_run_id, step_index)`
- `reviews(product_id)`
- `review_chunks(task_id)`
- `review_chunks.embedding` 使用 pgvector index，第一版按 `vector(1536)` 设计

## Day 3 建模约束

- 第一版 embedding 固定为 `text-embedding-3-small`。
- 第一版 embedding 维度固定为 1536。
- `review_chunks` 必须记录 `embedding_model` 和 `embedding_dimensions`，避免未来升级模型后混写不同维度向量。
- 第一版不做真实登录，但保留 `users` 表并初始化默认本地用户。
- 第一版保留 `projects` 表并初始化默认项目，前端先不展示复杂项目管理。
- CSV/JSON 导入的原始行数据必须进入 `reviews.raw_payload` 或 `artifacts`，方便回放和排错。

## Alembic 迁移计划

Day 3 初始迁移为 `0001_initial_schema`：

- 启用 PostgreSQL `vector` extension
- 创建 `users`、`projects`、`tasks`、`task_events`
- 创建 `agent_runs`、`agent_steps`
- 创建 `products`、`crawled_pages`、`reviews`、`review_chunks`
- 创建 `reports`、`artifacts`、`error_logs`
- 创建状态流、Agent step、评论归属和 pgvector HNSW 索引

Day 7 增量迁移为 `0002_task_queue_id`：

- 给 `tasks` 增加 `queue_task_id`
- 保存 Celery 返回的后台任务 ID，方便从业务任务追踪到队列任务
- 不改变任务主键，系统内部仍以 `task_id` 作为统一追踪 ID

迁移原则：

- 迁移脚本必须可 downgrade。
- 不在 Day 3 写复杂 repository。
- 不在迁移中写真实业务数据。
- 默认本地用户和默认项目由 Day 7 的 `SQLAlchemyTaskStatusStore` 在本地开发场景中按需创建。

## 数据所有权

- API 创建 `tasks`
- API 和 Worker 通过 mirrored store 同步更新 Redis 实时层与 PostgreSQL 审计层
- Worker 更新任务状态
- Agent 创建 `agent_runs` 和 `agent_steps`
- Crawler 写入 `products`、`crawled_pages`、`reviews`、`artifacts`
- Day 9 起 `SQLAlchemyCrawlResultStore` 负责把采集成功结果映射到这些表，并在 service 层用 `task_id + source_url`、`task_id + artifact_type + checksum` 和评论外部 ID 做第一版幂等控制。
- RAG 写入 `review_chunks` 和向量
- Report 模块写入 `reports`
- Observability 模块写入 `error_logs`

## Day 14 Review Chunk 写入约束

Day 14 新增 `SQLAlchemyReviewChunkStore`，负责把 `reviews` 转成 `review_chunks`：

1. 读取指定 `task_id` 下的评论。
2. 清洗 `reviews.content`。
3. 按句子边界切片，默认每片最多 500 字符。
4. 通过 `EmbeddingProvider` 生成向量。
5. 写入 `review_chunks`。

幂等规则暂时放在 service 层：

- `review_id`
- `task_id`
- `chunk_index`
- `embedding_model`
- `embedding_dimensions`

这五个字段组合一致时，重复索引会更新旧 chunk，而不是新增重复记录。

当前 `review_chunks.embedding` 字段固定为 `vector(1536)`，因此 Day 14 的 fake embedding 也必须输出 1536 维。不要为了单元测试写入短维度向量，否则会和 Day 3 的 pgvector 建模约束冲突。

`review_chunks.metadata` 当前建议写入：

- `review_external_id`
- `source_url`
- `rating`
- `source_type`

## Day 16 Report 写入约束

Day 16 新增 `backend/app/reporting/`，复用 Day 3 已创建的 `reports` 表，不新增迁移。

`reports` 字段使用方式：

| 字段 | Day 16 用途 |
| --- | --- |
| `task_id` | 报告归属任务，必须已存在 |
| `title` | 报告标题，当前由 product name 生成 |
| `status` | `draft`、`insufficient_evidence` 或预留 `failed` |
| `summary` | 结构化报告摘要 |
| `content_json` | 完整 `StructuredReport` JSON |
| `content_markdown` | 前端和导出使用的 Markdown 草案 |
| `evidence_refs` | 报告顶层证据引用列表 |
| `schema_version` | 当前固定为 `report.v1` |

Day 16 的报告入库规则：

1. `SQLAlchemyReportStore.save_report()` 入库前先确认 `task_id` 存在。
2. `StructuredReport` 负责校验章节 evidence refs。
3. `content_json` 保存完整结构，供后续前端详情页和 API 返回。
4. `content_markdown` 保存渲染结果，供前端预览和后续导出。
5. `evidence_refs` 单独冗余一份，方便列表页、证据链检查和后续查询。

当前第一版每次保存创建一条新报告。后续 Day 21 做历史报告时，可以增加报告版本展示策略，但不需要改变 Day 16 的基础字段。

无证据报告必须写入：

- `status = insufficient_evidence`
- `evidence_refs = []`
- `content_json.sections[*].evidence_refs = []`

这样前端和面试展示时可以明确说明：系统宁愿输出证据不足，也不会生成没有来源的结论。

## Day 17 Evidence Chain 回查约束

Day 17 新增 `backend/app/reporting/evidence.py`，不新增数据库表。第一版证据链通过已有表和 `reports.evidence_refs` 解析：

| evidence ref | 回查表 | 返回 source_type | parent_refs |
| --- | --- | --- | --- |
| `chunk:{chunk_id}` | `review_chunks` | `review_chunk` | `review:{review_id}` |
| `review:{review_id}` | `reviews` | `review` | `product:{product_id}` |
| `artifact:{artifact_id}` | `artifacts` | `artifact` | 空 |
| `step:{step_id}` | `agent_steps` | `agent_step` | `agent_run:{run_id}` |

回查规则：

1. 每个 evidence ref 必须先通过 `parse_evidence_ref()` 校验格式。
2. 只支持 `chunk`、`review`、`artifact`、`step` 四种类型。
3. 所有回查必须检查 `task_id`，不存在或跨任务引用统一返回 `available=false`。
4. 缺失证据必须返回 `missing_reason`，不能编造 `content_preview`。
5. `EvidenceChain.missing_refs` 汇总所有不可用引用，方便前端提示报告证据不完整。

为什么暂时不新增 `report_evidence_links` 表：

- Day 16 已经把报告顶层 `evidence_refs` 冗余到 `reports`。
- 当前四类证据都能通过现有表直接解析。
- Day 17 的目标是先打通回查协议和 API，不急着引入新关联表。
- 后续 Day 21 做历史报告、报告版本和列表查询时，再评估是否需要把 evidence chain 快照独立成表。

## Day 18 Analysis Scorecard 存储约束

Day 18 新增 `AnalysisScorecard`，当前不新增数据库表或迁移。

存储位置：

```text
reports.content_json.metadata.analysis_scorecard
```

Markdown 展示位置：

```text
reports.content_markdown -> ## 维度评分
```

这样设计的原因：

- Day 18 的评分是报告内容的一部分，不是跨任务统计指标。
- 评分必须和报告当时使用的 evidence snippets 一起快照保存。
- 当前前端只需要展示报告详情，不需要按评分排序报告列表。
- 后续如果要做“按风险分筛选历史报告”或“跨任务评分趋势”，再把 scorecard 拆到独立表。

约束：

- `AnalysisScorecard.evidence_refs` 必须来自输入 evidence snippets。
- 每个 `DimensionScore.evidence_refs` 必须能回到 Day 17 的 evidence chain。
- 样本不足必须写入 `LOW_SAMPLE_SIZE`。
- 无证据时 `status=insufficient_evidence`，整体分数为 0。

## Day 22 Error Log 写入约束

Day 22 开始正式使用 Day 3 已创建的 `error_logs` 表，不新增迁移。

字段使用方式：

| 字段 | Day 22 用途 |
| --- | --- |
| `id` | 错误日志 ID，前缀 `err_` |
| `task_id` | 可选，能归属到任务时必须写入 |
| `trace_id` | 可选，API 和 Worker 链路优先写入 |
| `layer` | 错误所在层，例如 `api`、`crawler`、`database` |
| `error_code` | 机器可读错误码 |
| `message` | 人类可读摘要 |
| `details` | 脱敏后的结构化细节 |
| `created_at` | 错误发生时间 |

当前写入来源：

- API 统一异常处理器：写入 `layer=api`。
- Worker Crawler 失败：写入 `layer=crawler`。
- Crawler 结果持久化失败：写入 `layer=database`。

查询入口：

```text
GET /api/observability/errors?trace_id=trc_xxx
GET /api/observability/errors?task_id=tsk_xxx
```

约束：

- `details` 必须经过 `sanitize_details()` 递归脱敏。
- 不允许无筛选条件查询全部错误。
- `task_events` 继续记录业务生命周期，`error_logs` 记录排障事实，两者不要混用。

## 与其他文档关系

- 状态流转见 `agent-state-machine.md`
- API 示例见 `data-contract-examples.md`
- 指标采集见 `llmops-metrics.md`
