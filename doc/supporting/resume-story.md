# 简历表达

## 项目一句话

MarketMind Agent 是一个面向电商运营评论洞察的工程化 Agent 系统，基于 FastAPI、Celery、Redis、PostgreSQL/pgvector、Playwright 和 Next.js，构建异步采集、Agent 状态持久化、评论 RAG 检索、证据链报告和失败任务恢复链路。

## 简历项目描述

建议写法：

> 设计并实现面向电商运营场景的评论洞察 Agent 系统，支持商品评论采集、评论清洗切片、语义检索、结构化报告生成和证据链回查。系统采用 FastAPI + Celery + Redis 解耦长任务，使用 PostgreSQL/pgvector 持久化任务状态、Agent steps、评论 chunk 和报告结果，并通过 Next.js 控制台展示任务进度、历史报告和证据来源。

更短版本：

> 构建电商评论洞察 Agent，重点实现长任务异步队列、Agent 状态持久化、RAG 证据检索、结构化报告和失败任务 retry。

## 可写进简历的 bullet

推荐使用 4-5 条，不要全部堆上去。

### 后端与异步任务

- 基于 FastAPI + Celery + Redis 设计长任务异步调度架构，将评论采集、RAG 检索和报告生成从 HTTP 请求中解耦，API 提交后立即返回 `task_id`，前端通过任务状态与事件流持续追踪进度。

### 状态持久化与可恢复

- 设计 PostgreSQL 任务、事件、Agent run / step 持久化模型，记录 Thought、Action、Observation、工具输出和错误码，实现任务执行可追踪、可回放和失败定位。

### RAG 与证据链

- 构建评论清洗、切片、embedding 和 review chunk 检索链路，将差评片段转化为可引用证据，报告结论通过 evidence refs 回查到原始 review、artifact 或 Agent step，降低 AI 总结幻觉风险。

### Guardrails 与鲁棒性

- 使用 Pydantic Guardrails 校验 Agent 工具调用和报告结构，结合 self-heal repair prompt 处理坏 JSON 和 schema 不匹配，并记录 `validation_error_count`、`self_heal_count` 等 LLMOps 指标入口。

### 工程质量

- 建立 pytest + coverage + ruff + Alembic + Docker Compose config + npm lint/build/audit + pip-audit 的质量门禁；Day28 完整测试为 `157 passed`，Day29 完整测试为 `162 passed`，backend coverage `90.79%`。

### 性能与失败恢复

- 实现 Day27 fixture benchmark，生成 20 个样例任务的 JSON / Markdown artifact，记录成功率 95.00%、平均 338 ms、P95 391 ms，并在 Day28 增加失败任务 retry API 和 Worker recovery resume 事件。

## 已验证数据

当前可以真实写入简历或面试口头说明的数据：

- Day28 `uv run pytest`：157 passed。
- Day29 `uv run pytest`：162 passed。
- backend coverage：90.79%。
- Day27 fixture benchmark：20 个样例任务。
- Day27 fixture benchmark 成功率：95.00%。
- Day27 fixture benchmark 平均端到端耗时：338 ms。
- Day27 fixture benchmark P95：391 ms。
- Day28 失败任务 retry：`tests/test_day28_recovery.py` 7 passed。
- GitHub Actions：backend quality gate 和 frontend quality gate 已通过。

这些数字必须带上限定词：

- Day27 是 fixture benchmark，不是线上压测。
- 当前模型调用次数和 token 成本为 0，因为还没有接真实 provider。
- Day28 是任务级 retry，不是完整 Agent step replay。

## Day27 fixture benchmark 怎么讲

可以这样说：

> 我没有直接把真实网站和真实 LLM 放进第一版 benchmark，因为那样数据会受网络、反爬和模型服务波动影响。Day27 先做 fixture benchmark，固定端到端耗时、阶段耗时、P50/P95、成功率和失败分类这些指标结构。当前 20 个 fixture 样例成功率 95%，平均 338 ms，P95 391 ms，主要瓶颈在 crawler 和 RAG。这些数据不代表线上吞吐，但能作为后续真实 provider 接入后的对比基线。

## Day28 失败任务 retry 怎么讲

可以这样说：

> Day28 我实现的是任务级失败恢复。只有 `PAGE_TIMEOUT`、`NETWORK_ERROR`、`ACCESS_BLOCKED`、`CRAWL_PERSISTENCE_FAILED`、`QUEUE_UNAVAILABLE` 这类可恢复错误可以 retry。retry 复用原 `task_id`，旧事件保留，新事件追加，状态从 `failed -> waiting_retry -> queued -> running` 推进。当前 `backoff_seconds` 先作为 metadata，前端按钮和 Celery countdown 是后续迭代。

## 不建议写

不要写：

- 全网稳定爬取电商平台。
- 使用真实 LLM 完成大规模生产报告。
- 已完成完整线上压测。
- 已完成精确 Agent step 断点续跑。
- 已替代成熟卖家工具。
- 将 Pydantic 解析失败率降低到 1% 以下，除非后续真实统计支持。

原因：

- 这些能力当前没有真实验证。
- 面试官追问时容易被反证。
- 这个项目真正强的地方是工程链路，不是夸大业务覆盖。

## 不同岗位的强调方式

后端实习：

- FastAPI API 设计。
- Celery + Redis 队列。
- PostgreSQL 状态持久化。
- 错误分类和 retry。
- CI / coverage / audit。

AI 应用实习：

- Agent 工具 schema。
- Pydantic Guardrails。
- RAG 证据检索。
- 报告 evidence refs。
- LLMOps 指标入口。

全栈实习：

- Next.js 控制台。
- 真实 API client。
- 任务进度轮询。
- 历史报告和证据链展示。
- 前后端契约测试。

## 关联文档

- 演示脚本：`demo-script.md`
- 面试讲述：`interview-story.md`
- 深度防守：`interview-defense-dossier.md`
- 性能基线：`performance-benchmark.md`
- 指标口径：`llmops-metrics.md`
