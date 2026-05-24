# Day 05 - Celery 与 Redis 基础接入

## 当天目标

让 API 能把任务交给后台执行，避免长任务阻塞 HTTP 请求。今天要跑通“提交任务 -> 返回 task_id -> Worker 执行”的最小闭环。

## 前置依赖

- `day-04.md` API 骨架可启动
- Redis 可用
- 阅读 `../supporting/architecture.md`

## 当天交付物

- Celery app
- Redis broker 配置
- 最小后台任务
- `POST /api/tasks`
- `GET /api/tasks/{task_id}` 原型

## 实施步骤

1. 配置 Celery broker 和 result backend
2. 写一个最小任务，例如打印或记录 URL
3. API 接收到请求后创建任务记录
4. API 投递 Celery 后立即返回 `task_id`
5. Worker 更新任务状态

## 验收标准

- API 请求不会等待 Worker 完成
- Worker 能消费任务
- 数据库或缓存能查到任务状态
- Worker 未启动时 API 能明确报错或保留 queued 状态

## 风险与回退

- 不要在 API 中直接调用耗时函数
- 如果 Celery 配置失败，先用最小任务验证 Redis 连通性

## 关联文档

- 上一天：`day-04.md`
- 下一天：`day-06.md`
- API：`../supporting/api-contract.md`
- 可观测性：`../supporting/observability.md`

## 建议提交

`feat: add celery task pipeline`

