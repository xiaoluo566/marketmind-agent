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
- `POST /api/uploads`：上传手工数据
- `WS /ws/tasks/{task_id}`：实时进度推送

## 接口细化

### `POST /api/tasks`

职责：只创建任务和投递异步队列，不直接执行爬虫或模型调用。

输入：

- `target`
- `mode`
- `priority`
- `options`

输出：

- `task_id`
- `status`
- `trace_id`

### `GET /api/tasks/{task_id}/events`

职责：给前端展示任务时间线。事件来源包括 API、worker、crawler、agent、report。

输出建议按时间排序，包含：

- `event_type`
- `message`
- `payload`
- `created_at`

### `GET /api/tasks/{task_id}/steps`

职责：给调试页展示 Agent 执行细节。生产展示时可以隐藏 thought，只展示 tool 和 observation 摘要。

### `POST /api/tasks/{task_id}/retry`

职责：只允许重试失败或可恢复状态的任务。重试时必须记录新的 `agent_run_id`，不能覆盖旧记录。

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

## 错误码建议

- `INVALID_TARGET`
- `TASK_NOT_FOUND`
- `TASK_NOT_RETRYABLE`
- `QUEUE_UNAVAILABLE`
- `VALIDATION_FAILED`
- `INTERNAL_ERROR`

## 与其他文档关系

- 请求响应 JSON 示例见 `data-contract-examples.md`
- 表结构见 `data-model.md`
- 前端消费方式见 `ui-console-spec.md`
- 错误日志见 `observability.md`
