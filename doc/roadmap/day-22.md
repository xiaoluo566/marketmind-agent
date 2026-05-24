# Day 22 - 日志与可观测性

## 当天目标

让系统出错时能定位到具体层：API、队列、Worker、Agent、Crawler、RAG、Report 或 Database。

## 前置依赖

- `day-21.md` 历史记录已可查看
- 阅读 `../supporting/observability.md`
- 阅读 `../supporting/risk-register.md`

## 当天交付物

- 结构化日志
- trace_id 贯穿
- 关键耗时记录
- 错误分类
- 调试手册雏形

## 实施步骤

1. 引入日志库
2. API 请求生成 trace_id
3. Worker、Agent、Crawler 继承 trace_id
4. 每个关键阶段记录 duration_ms
5. 失败时记录 error_code 和 error_message

## 验收标准

- 一个任务能通过 trace_id 串起来
- 日志能区分模块和阶段
- 失败定位不依赖猜测

## 风险与回退

- 不要在日志中打印 API key
- 不要只写自然语言错误，要有 error_code

## 关联文档

- 上一天：`day-21.md`
- 下一天：`day-23.md`
- 可观测性：`../supporting/observability.md`
- 安全：`../supporting/security-compliance.md`

## 建议提交

`feat: improve observability`

