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

## 与其他文档关系

- 任务状态字段见 `data-model.md`
- 前端展示见 `ui-console-spec.md`
- 发版检查见 `release-checklist.md`
