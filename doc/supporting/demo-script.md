# 演示脚本

## 文档定位

这份文档用于 Day 29 之后的项目展示。目标是把 MarketMind Agent 讲成一个有工程闭环的系统，而不是临时口头解释的 demo。

推荐演示时长：5-8 分钟。

## 演示前检查

演示前先确认：

- 当前分支是 `dev` 或一个已知稳定提交。
- `uv run pytest` 最近一次通过。
- `uv run pytest --cov=backend --cov-report=term-missing` 最近一次通过，coverage 不低于 80%。
- `npm run build` 最近一次通过。
- `doc/supporting/day27-benchmark-summary.md` 存在。
- `POST /api/tasks/{task_id}/retry` 的 Day28 测试已通过。
- 如果 Docker Desktop daemon 没有启动，不演示真实 `docker compose up`，只展示 compose config 和 runbook。

推荐开场口径：

> 这个项目不是要替代成熟卖家工具，而是聚焦电商运营里的评论洞察场景：把大量评论清洗、检索、归因，并生成带证据链的报告，同时让长任务和 Agent 执行过程可追踪、可恢复、可回放。

## 主线演示流程

### 1. 项目定位

打开 README，先讲三句话：

- 场景：电商运营需要快速理解竞品评论里的质量、物流、售后和退货问题。
- 痛点：普通 AI 总结容易没有证据，长任务失败后也难以复盘。
- 方案：FastAPI + Celery + Redis + PostgreSQL/pgvector + Playwright + Agent + Next.js，把任务、证据和报告串成一个工程系统。

不要把项目讲成“全网爬虫”或“卖家工具替代品”。

### 2. 架构图

展示 README 的 Mermaid 架构图，重点讲：

- Next.js 只是控制台，不承载核心业务逻辑。
- FastAPI 是任务入口和查询入口。
- Celery + Redis 负责长任务异步解耦。
- Worker 串联 crawler、Agent、RAG 和 report。
- PostgreSQL 是长期事实来源，Redis 是实时状态和事件缓存。
- pgvector 是后续真实向量检索的落点，当前有 deterministic embedding 流程验证。

### 3. 任务提交

推荐先用 fixture 数据，避免演示被真实网站和网络波动影响。

可以展示：

- 新建任务页面。
- `POST /api/tasks` 返回 `task_id`。
- 任务状态进入 `queued` / `running` / `completed`。
- `trace_id` 如何贯穿请求链路。

讲解重点：

> 长任务不阻塞 HTTP 请求，API 只负责创建任务和入队，Worker 后台执行，前端通过任务详情页轮询状态和事件。

### 4. 任务详情与 Agent steps

打开任务详情页，展示：

- 当前任务状态。
- 任务事件流。
- Agent step 摘要。
- 错误码和 trace 信息。

讲解重点：

> Agent 不是黑盒运行。Thought / Action / Observation 会进入数据库，但前端展示时只展示脱敏摘要，避免把完整中间推理或工具参数暴露出来。

### 5. 报告与证据链

打开历史报告和报告详情页，展示：

- 报告 section。
- 风险/机会评分。
- evidence refs。
- `GET /api/reports/{report_id}/evidence` 返回的证据来源。

讲解重点：

> 报告不是模型凭空写出来的，每个结论都能回查到 review chunk、原始 review、artifact 或 Agent step。证据缺失时系统会显式返回 missing reason，而不是假装有证据。

### 6. Day27 benchmark

展示：

- `doc/supporting/day27-benchmark-summary.md`
- `doc/supporting/day27-benchmark-results.json`
- `backend/app/benchmarking/summary.py`

当前可讲数据：

- Day27 fixture benchmark：20 个样例任务。
- 成功率：95.00%。
- 平均端到端耗时：338 ms。
- P95：391 ms。
- 最慢阶段：crawler。
- 第二瓶颈：RAG。

必须说明：

> 这是 fixture benchmark，不是线上压测，也没有真实 LLM / embedding token 成本。它的价值是固定指标口径和 artifact 形式，后续接真实基础设施后才能做可信对比。

### 7. 失败重试

展示 Day28 失败重试能力：

- `backend/app/tasks/recovery.py`
- `POST /api/tasks/{task_id}/retry`
- `tests/test_day28_recovery.py`
- 任务事件里的 `task recovery resumed`

讲解重点：

> Day28 的 retry 不是简单失败重跑，而是只允许 retryable 错误进入恢复链路。任务复用原 `task_id`，旧事件保留，新事件追加。当前是任务级恢复，还不是 Agent step 级 replay。

### 8. GitHub Actions 与工程化记录

展示：

- `.github/workflows/ci.yml`
- `doc/supporting/testing-strategy.md`
- `doc/supporting/development-log.md`
- 最近一次 CI 成功记录

讲解重点：

> 这个项目不是只靠手工点页面证明可用。后端测试、coverage、ruff、Alembic、compose config、前端 lint/build/audit 和 pip-audit 都进入了质量门禁。

## 备用路线

如果演示现场出问题，按下面降级：

- 前端起不来：改用 README、API 契约和测试输出讲主链路。
- 后端服务没启动：展示 `tests/test_day24_integration_flow.py` 证明主链路契约闭环。
- 真实网站采集失败：切换 fixture HTML，不现场解释反爬细节。
- 模型 API 不可用：说明当前报告生成是 deterministic baseline，真实 LLM provider 是后续项。
- Docker Desktop 不可用：只展示 `docker compose config` 和 `docker-compose-runbook.md`，不要声称真实 compose up 已验证。

## 不要现场声称

不要说：

- 已经完成全网稳定采集。
- 已经完成真实 LLM 成本统计。
- 已经完成真实线上压测。
- 已经完成精确 Agent step replay。
- 已经替代成熟卖家工具。
- Docker Compose 已经完整真实启动验证。

可以说：

- 当前已经完成可测试的异步任务、状态持久化、RAG 原型、证据链报告、benchmark artifact 和任务级 retry。
- 当前仍在补真实 provider、前端 retry 按钮、容器 E2E 和更完整的 LLMOps 统计。

## 结尾总结

推荐结尾：

> 这个项目最核心的价值不是“让大模型写报告”，而是把不稳定的采集、模型输出和长任务执行放进一个可追踪、可恢复、可测试的工程系统里。它的第一阶段已经完成主链路和质量门禁，后续我会继续补真实 provider、前端 retry 入口和容器级 E2E。

## 关联文档

- README：`../../README.md`
- 简历表达：`resume-story.md`
- 面试讲述：`interview-story.md`
- 面试防守：`interview-defense-dossier.md`
- 测试策略：`testing-strategy.md`
- 发布检查：`release-checklist.md`
