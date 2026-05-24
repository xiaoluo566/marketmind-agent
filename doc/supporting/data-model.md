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
- `prompt_version`
- `schema_version`

