# Day 04 - API 契约与任务接收层

## 当天目标

Day 1 已经提前完成了 FastAPI app factory、health endpoint、配置读取、trace ID middleware 和统一响应 envelope。因此 Day 4 不再重复搭建骨架，而是把后端网关推进到“可以接收分析任务”的阶段。

今天目标是实现 `POST /api/tasks` 的第一版契约：API 只做参数校验、生成 `task_id`、返回统一 envelope，不连接爬虫、不调用模型、不投递 Celery，也暂不依赖真实数据库连接。真实入库和异步队列投递留到 Day 5，避免在一个开发日里同时引入 API、数据库事务、Redis 和 Worker 四类变量。

## 前置依赖

- `day-03.md` 数据模型和初始迁移已完成
- 阅读 `../supporting/api-contract.md`
- 阅读 `../supporting/data-contract-examples.md`
- 阅读 `../supporting/dev-environment.md`

## 当天交付物

- `POST /api/tasks` 任务创建契约
- Pydantic 请求 schema
- 任务接收响应 schema
- 统一 validation error envelope
- API 层与业务接收层的最小分离
- Day 3 可追踪字段补漏检查

## 实施步骤

1. 回看 Day 3 数据模型，确认 `tasks`、`agent_runs`、`agent_steps`、`review_chunks`、`reports` 等核心表没有遗漏。
2. 如发现长任务状态字段缺口，先补齐模型、迁移和测试。
3. 编写 `POST /api/tasks` 的 API 测试，先确认未实现时失败。
4. 新增 `TaskCreateRequest`，约束 `target`、`mode`、`priority`、`source_type`、`options`。
5. 新增 `TaskAcceptedData`，返回 `task_id`、`status`、`trace_id`。
6. 新增任务接收服务，生成 `tsk_` 前缀任务 ID，状态固定为 `received`。
7. 注册 `POST /api/tasks` 路由，返回 HTTP 202 和统一 envelope。
8. 注册 `RequestValidationError` 处理器，让校验错误也返回统一 envelope。
9. 更新 `development-log.md`，记录 Day 4 实际范围与验证结果。

## 验收标准

- `POST /api/tasks` 合法请求返回 202。
- 响应包含 `success=true`、`message=accepted`、`task_id`、`status=received`、`trace_id`。
- 请求头传入 `X-Trace-Id` 时，响应体和响应头保持同一个 trace。
- 空白 `target`、非法 `mode`、非法 `priority` 返回 422，并使用统一错误 envelope。
- API 代码不直接依赖爬虫、模型、Celery 或真实数据库连接。
- Day 3 模型测试继续通过。

## 当天不做

- 不创建真实任务数据库记录。
- 不投递 Celery。
- 不读取 Redis。
- 不做任务状态查询。
- 不接前端真实提交表单。

这些内容进入 Day 5 和 Day 6。

## 风险与回退

- 如果提前接数据库，测试会依赖本地 PostgreSQL 状态，开发节奏会被环境问题拖慢。
- 如果提前接 Celery，接口失败原因会混在 schema、Redis、worker 三层里，不利于定位。
- 如果请求 schema 过窄，后续前端和导入数据源会频繁返工；因此第一版保留 `options` 作为扩展字段。

## 关联文档

- 上一天：`day-03.md`
- 下一天：`day-05.md`
- API 契约：`../supporting/api-contract.md`
- 数据示例：`../supporting/data-contract-examples.md`
- 安全：`../supporting/security-compliance.md`

## 建议提交

`feat: 增加任务创建接口契约`
