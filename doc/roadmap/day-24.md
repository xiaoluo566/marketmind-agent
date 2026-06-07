# Day 24 - 集成测试与回归样例

## 当天目标

Day 24 的目标不是继续堆新功能，而是验证 Day 1 到 Day 23 已经做出的能力能否作为一条业务主链路稳定运行。

这一天重点回答三个问题：

1. API 提交任务后，任务状态、队列任务 ID 和事件是否能持久化。
2. Worker 使用同一个 `task_id` 执行采集后，商品、页面、评论、artifact 是否能落库。
3. 评论经过 RAG 切片与检索后，报告是否能保存，并通过报告 evidence API 回查到真实评论 chunk。

如果这条链路不成立，前面单点模块再多也只是“功能散件”。所以 Day 24 是从“模块可用”进入“系统可回归”的一天。

## 前置依赖

- `day-23.md`：测试体系加固、coverage fail-under 80、状态转换策略和 schema 契约测试已完成。
- `../supporting/testing-strategy.md`：定义单元、集成、端到端测试边界。
- `backend/app/api/routes/tasks.py`：任务提交、任务状态、事件查询接口。
- `backend/app/worker/tasks.py`：Worker 任务执行入口 `run_research_task()`。
- `backend/app/storage/crawl_stores.py`：采集结果持久化。
- `backend/app/rag/review_index.py`：评论切片、embedding 写入、相似检索。
- `backend/app/reporting/stores.py`：结构化报告持久化。
- `backend/app/api/routes/reports.py`：报告列表、详情和 evidence chain API。

## 当天交付物

- 新增 `tests/test_day24_integration_flow.py`。
- 使用内存 SQLite + `StaticPool` 搭建稳定的集成测试数据库。
- 使用 fake dispatcher 替代真实 Celery broker，但保留 API 的真实任务提交逻辑。
- 使用 fixture HTML 替代真实外部网站，避免测试受网络、反爬、验证码影响。
- 使用 `DeterministicEmbeddingProvider` 替代真实 embedding API，保证本地测试可重复。
- 串联 API、Worker、SQLAlchemy store、Crawler fixture、RAG indexing、Report store、Report API、Evidence API。
- 修正 Day 23 文档中的 coverage 漂移数据：最新复跑为 90.80%。

## 实际完成内容

### 1. 主链路集成测试

新增测试文件：

```text
tests/test_day24_integration_flow.py
```

测试覆盖的链路如下：

```text
POST /api/tasks
  -> SQLAlchemyTaskStatusStore 创建任务
  -> SQLAlchemyTaskEventStore 记录 received / queued
  -> CapturingDispatcher 捕获 payload 和 queue_task_id
  -> run_research_task() 执行 Worker 主体
  -> fixture HTML 解析商品和评论
  -> SQLAlchemyCrawlResultStore 写入 product / crawled_page / review / artifact
  -> SQLAlchemyReviewChunkStore 切片并写入 review_chunks
  -> DeterministicEmbeddingProvider 生成稳定向量
  -> search_similar_reviews() 召回评论 chunk
  -> StructuredReportGenerator 生成 evidence refs 报告
  -> SQLAlchemyReportStore 保存 reports
  -> GET /api/reports 查询报告列表
  -> GET /api/reports/{report_id} 查询报告详情
  -> GET /api/reports/{report_id}/evidence 回查真实 review_chunk 证据
```

这个测试不是单纯 mock API 返回，而是让多个真实 store 和真实路由一起工作。唯一刻意替换的是：

- Celery broker：用 `CapturingDispatcher` 捕获入队请求，避免测试依赖 Redis 和独立 worker 进程。
- 外部网页：用固定 HTML fixture，避免测试依赖真实站点稳定性。
- embedding provider：用确定性 fake provider，避免测试依赖外部模型服务。

### 2. 任务与事件校验

测试断言：

- `POST /api/tasks` 返回 202。
- 返回值包含真实 `task_id`。
- 任务状态先进入 `queued`。
- fake dispatcher 捕获同一个 `task_id` 和 `trace_id`。
- Worker 执行后任务状态变为 `completed`。
- 事件顺序为：

```text
task received
task queued
task running
crawl started
crawl completed
task completed
```

这能防止未来改动破坏任务生命周期的事件顺序。

### 3. 采集、评论和 RAG 校验

fixture HTML 包含：

- 商品标题：`Portable Espresso Maker`
- 价格：`$39.99`
- 总评分：`4.2 out of 5`
- 两条低分评论：
  - `rev-return`：pump failure / return support
  - `rev-shipping`：slow shipping / cracked shell

测试断言：

- Worker 能把评论写入数据库。
- RAG index 能读取同一个 `task_id` 下的评论。
- `index_task_reviews()` 返回 `review_count == 2`。
- `index_task_reviews()` 返回 `chunk_count == 2`。
- `search_similar_reviews()` 能返回两条带 `review_external_id` 的评论证据。

### 4. 报告和证据链校验

测试使用 RAG 检索结果构造 `EvidenceSnippet`，再生成 `StructuredReport` 并保存。

测试断言：

- `GET /api/reports?task_status=completed` 能查到刚生成的报告。
- 报告列表中的 `risk_score` 来自报告 metadata 的 `analysis_scorecard.overall_risk_score`。
- `GET /api/reports/{report_id}` 能返回同一个 `task_id` 和同一组 `evidence_refs`。
- `GET /api/reports/{report_id}/evidence` 返回：
  - `missing_refs == []`
  - 所有 source 都 `available == true`
  - source type 为 `review_chunk`
  - 每个 chunk 都能追溯到 `review:{review_id}`

这能证明报告不是“凭空生成文本”，而是有可回查的数据证据。

## 当天为什么这样选

### 为什么不直接跑真实 Redis + Celery + PostgreSQL？

Day 24 的目标是“主链路回归样例”，不是“部署验收”。真实 Redis、Celery worker 和 PostgreSQL 会放到 Day 25 的 Docker Compose 和后续 CI 阶段。

今天如果直接把测试绑定到真实服务，缺点很明显：

- 本地环境稍有差异就会失败。
- 失败原因可能是 Redis 没启动，而不是业务链路真的坏了。
- 测试速度变慢，不适合作为日常回归。

所以今天选择“真实业务模块 + 可控基础设施替身”的策略：业务代码尽量真实，外部依赖用稳定替身。

### 为什么不用真实 LLM 和真实 embedding？

集成测试要验证的是系统契约，不是模型质量。真实 LLM / embedding 的输出会受网络、费用、限流、模型版本影响，不适合做稳定回归。

这里继续使用 `DeterministicEmbeddingProvider`，是为了确保：

- 向量维度固定。
- 相同文本输出稳定。
- 检索结果可重复。
- CI 或本地无模型密钥时仍可跑测试。

真实 embedding provider 后续应该接入同一个接口，并增加 provider 超时、重试、维度不匹配和 pgvector 原生排序测试。

### 为什么 Day 24 更像测试开发，而不是功能开发？

因为项目已经进入第四周。这个阶段继续加功能会让系统看起来更丰富，但如果没有跨模块回归样例，后续改动很容易破坏已有链路。

Day 24 的工程价值在于把“我觉得它能跑”变成“有一条自动化测试证明它能跑”。

## 验证记录

当前已执行：

```powershell
uv run pytest tests\test_day24_integration_flow.py
uv run pytest tests\test_quality_gate_config.py tests\test_task_status_policy.py tests\test_schema_validation_contracts.py
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
```

结果：

```text
Day 24 targeted test: 1 passed
Day 23 quality gate targeted tests: 22 passed
Full pytest: 137 passed
Coverage gate: 137 passed, backend coverage 90.86%, fail-under 80 reached
Ruff: All checks passed
Alembic heads: 0002_task_queue_id (head)
Frontend lint: passed
Frontend build: passed
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

## 遗留问题

- Day 24 的集成测试没有启动真实 Redis broker。
- Day 24 的集成测试没有启动独立 Celery worker 进程。
- Day 24 的集成测试没有连接真实 PostgreSQL / pgvector 原生查询。
- 报告仍由确定性生成器生成，真实 LLM prompt 尚未接入。
- 前端 E2E 尚未覆盖这条完整链路。

这些不是 Day 24 的失败，而是测试分层边界。后续对应安排：

- Day 25：Docker Compose 一键启动。
- Day 26：CI 与回退策略。
- Day 27：性能与 benchmark。
- Day 28：失败重试与续跑。
- Day 29：Demo、README 和演示材料。

## 关联文档

- 上一天：`day-23.md`
- 下一天：`day-25.md`
- 测试策略：`../supporting/testing-strategy.md`
- 开发日志：`../supporting/development-log.md`
- 面试文档：`../supporting/interview-defense-dossier.md`
- 部署计划：`../supporting/deployment.md`
- 发布门禁：`../supporting/release-checklist.md`

## 建议提交

```text
test: 增强 Day 24 主链路集成测试
```
