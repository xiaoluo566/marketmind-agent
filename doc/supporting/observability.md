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

## 与其他文档关系

- 任务状态字段见 `data-model.md`
- 前端展示见 `ui-console-spec.md`
- 发版检查见 `release-checklist.md`
