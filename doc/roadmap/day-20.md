# Day 20 - 实时进度展示

## 当天目标

让用户在任务运行中看到清晰的阶段变化、Agent 步骤和失败点。今天解决“任务是不是卡住了”的体验问题。

## 前置依赖

- `day-19.md` 控制台可提交任务
- `day-06.md` 任务事件流可查询
- 阅读 `../supporting/observability.md`

## 当天交付物

- 任务状态条
- 事件时间线
- Agent step 展示
- 失败信息展示

## 实施步骤

1. 前端轮询或订阅任务事件
2. 按时间展示 task events
3. 展示 Agent tool 调用摘要
4. 对失败事件显示 error_code 和建议动作
5. 为后续 WebSocket / SSE 保留接口

## 验收标准

- 用户能看出任务当前阶段
- 开发者能定位卡在哪一步
- 失败信息不是空白或通用报错

## 风险与回退

- 第一版允许轮询，不强制 WebSocket
- 不要把敏感模型输入完整展示给普通用户

## 关联文档

- 上一天：`day-19.md`
- 下一天：`day-21.md`
- 可观测性：`../supporting/observability.md`
- 控制台：`../supporting/ui-console-spec.md`

## 建议提交

`feat: stream task progress`

