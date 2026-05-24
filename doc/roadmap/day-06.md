# Day 06 - 任务状态与进度流

## 当天目标

让任务不是一个黑盒。用户和开发者都应该知道任务在排队、运行、失败、重试还是完成。

## 前置依赖

- `day-05.md` Celery 基础链路可运行
- 阅读 `../supporting/data-model.md`
- 阅读 `../supporting/observability.md`

## 当天交付物

- `task_events` 写入逻辑
- 任务状态枚举
- 事件查询接口
- 前端进度数据格式

## 实施步骤

1. 定义状态：`received`、`queued`、`running`、`completed`、`failed`
2. 每次状态变化写入 `task_events`
3. 实现 `GET /api/tasks/{task_id}/events`
4. 为后续 WebSocket / SSE 预留统一事件格式
5. 在失败事件里记录 `error_code` 和 `trace_id`

## 验收标准

- 一个任务至少有 received、queued、running、completed 或 failed
- 失败能看到失败阶段和错误码
- 前端不用解析日志也能展示进度

## 风险与回退

- 不要只依赖 Celery result backend
- 不要把可恢复失败和不可恢复失败混在一起

## 关联文档

- 上一天：`day-05.md`
- 下一天：`day-07.md`
- 数据模型：`../supporting/data-model.md`
- 控制台：`../supporting/ui-console-spec.md`

## 建议提交

`feat: expose task progress events`

