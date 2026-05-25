# Day 07 - 第一周联调与任务事件持久化

## 当天目标

把 Day 4 到 Day 6 做出的任务入口、Celery 入队、Redis 状态快照、Redis 事件流和 Day 3 预留的 PostgreSQL `tasks` / `task_events` 表接成一条可验收链路。

Day 7 的重点不是继续堆新能力，而是把第一周的地基做扎实：确认真实 Redis + Worker 能跑通，确认任务状态能从短期实时层同步到长期审计层，并明确后续 Playwright、Agent step、报告生成都应该写入同一套状态轨迹。

## 前置依赖

- `day-03.md` 数据库模型和 Alembic 初始迁移已完成
- `day-05.md` Celery + Redis 异步任务管线已完成
- `day-06.md` Redis 事件流和 `GET /api/tasks/{task_id}/events` 已完成
- 阅读 `../supporting/api-contract.md`
- 阅读 `../supporting/data-model.md`
- 本地可启动 PostgreSQL、Redis、FastAPI 和 Celery worker

## 当天交付物

- PostgreSQL 任务 repository 雏形
- `tasks` 表写入或更新任务状态
- `task_events` 表持久化关键事件
- Redis 实时事件层与 PostgreSQL 审计层的职责说明
- 真实 Redis + Celery worker 的本地联调记录
- Day 1 到 Day 7 第一周验收清单
- 更新开发日志和面试防御手册

## 为什么持久化放在 Day 7

Day 6 已经完成了事件格式和事件写入时机：`received -> queued -> running -> completed/failed`。如果 Day 6 同时把 Redis、PostgreSQL、repository、事务边界全部接上，范围会膨胀，而且不利于先稳定事件契约。

所以 Day 6 只解决“过程可见性”，Day 7 再解决“长期可追溯性”。这个拆分更适合工程推进：

- 先固定事件格式，再决定落库策略。
- 先让 API / Worker 都能写事件，再统一接持久化。
- 先用 Redis 支撑前端实时进度，再用 PostgreSQL 支撑历史审计、回放和断点续跑。
- 先完成第一周联调，再进入 Playwright 采集，避免采集失败和基础设施问题混在一起。

## 实施步骤

1. 检查 Alembic 初始迁移中的 `tasks` 和 `task_events` 字段是否满足 Day 6 事件结构。
2. 新增 storage/repository 层，不让 API route 和 Celery worker 直接写 ORM。
3. 在 `POST /api/tasks` 创建任务时写入 `tasks` 主记录。
4. 在事件写入服务中增加 PostgreSQL 持久化分支，把关键事件写入 `task_events`。
5. 设计失败策略：Redis 写入失败、PostgreSQL 写入失败、双写部分成功时分别如何返回和记录。
6. 用真实 Redis + Celery worker 跑一次本地端到端联调。
7. 补测试：repository 单元测试、API 行为测试、worker 事件持久化测试。
8. 更新 `development-log.md`、`interview-defense-dossier.md`、`api-contract.md`。

## 验收标准

- `POST /api/tasks` 后，数据库 `tasks` 中存在对应任务。
- `GET /api/tasks/{task_id}` 仍能读取最新状态快照。
- `GET /api/tasks/{task_id}/events` 返回的事件和 `task_events` 表中的关键事件一致。
- Worker 执行后，`running` 和 `completed` 或 `failed` 事件能写入 PostgreSQL。
- Redis 不再被描述为唯一状态来源，而是实时层。
- PostgreSQL 被描述为审计和恢复层。
- 自动化测试通过，真实 Redis/Worker 联调步骤被记录。

## 风险与回退

- 如果本地 PostgreSQL 环境阻塞，当天先完成 repository 和测试替身，真实容器联调延后到 Docker 日。
- 如果双写逻辑让 API 变复杂，先把写事件封装成 service，route 只调用一个接口。
- 如果 Redis 和 PostgreSQL 状态短暂不一致，优先保证 PostgreSQL 最终可审计，Redis 作为实时展示缓存。
- 不在 Day 7 接 Playwright，避免把网页采集不稳定性引入第一周基础设施验收。

## 关联文档

- 上一天：`day-06.md`
- 下一天：`day-08.md`
- API 契约：`../supporting/api-contract.md`
- 数据模型：`../supporting/data-model.md`
- 开发日志：`../supporting/development-log.md`
- 面试手册：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 持久化任务状态与事件日志`
