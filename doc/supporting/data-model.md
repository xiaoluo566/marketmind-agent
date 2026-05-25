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
- `created_at`
- `started_at`
- `finished_at`
- `error_code`
- `error_message`
- `trace_id`

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

迁移原则：

- 迁移脚本必须可 downgrade。
- 不在 Day 3 写复杂 repository。
- 不在迁移中写真实业务数据。
- 默认本地用户和默认项目后续通过 seed 脚本或应用初始化创建。

## 数据所有权

- API 创建 `tasks`
- Worker 更新任务状态
- Agent 创建 `agent_runs` 和 `agent_steps`
- Crawler 写入 `products`、`reviews`、`artifacts`
- RAG 写入 `review_chunks` 和向量
- Report 模块写入 `reports`

## 与其他文档关系

- 状态流转见 `agent-state-machine.md`
- API 示例见 `data-contract-examples.md`
- 指标采集见 `llmops-metrics.md`
