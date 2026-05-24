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

