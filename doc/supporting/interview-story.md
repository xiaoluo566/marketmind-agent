# 面试讲述稿

## 推荐开场

> 我最近做了一个工程化 Agent 项目，叫 MarketMind Agent。它面向电商运营里的评论洞察场景，重点不是让大模型随便生成一篇报告，而是把评论采集、RAG 检索、Agent 状态追踪、证据链报告和失败恢复串成一个可测试、可复盘的系统。

## 2 分钟版本

这个项目解决的是电商运营里“评论太多、痛点难归纳、AI 报告缺少证据、长任务容易中断”的问题。

用户提交商品链接或评论数据后，FastAPI 创建任务并交给 Celery + Redis 异步执行，避免 HTTP 请求长时间阻塞。Worker 会调用采集、评论检索和报告生成模块。评论数据会进入 PostgreSQL，切片后生成 review chunks，后续通过 embedding / pgvector 方向做语义检索。Agent 执行时，Thought、Action、Observation 会进入数据库，前端可以看到脱敏后的 step 摘要。报告生成时，每个结论都绑定 evidence refs，可以通过 API 回查到原始 review、artifact 或 Agent step。

这个项目不是套壳大模型 demo。它的重点是工程稳定性：任务状态、事件流、错误分类、Pydantic Guardrails、测试覆盖、CI、benchmark artifact 和失败任务 retry。当前已经完成 Day28 的任务级失败恢复，Day29 主要把 README、演示脚本和简历表达整理成可展示材料。

## 30 秒版本

> MarketMind Agent 是一个电商评论洞察 Agent 系统。它用 FastAPI + Celery + Redis 处理长任务，用 PostgreSQL/pgvector 管理任务状态、评论证据和报告结果，用 Agent 工具调用和 Pydantic Guardrails 控制模型输出，最终生成可回查证据链的评论分析报告。

## 为什么不是套壳

如果面试官问“这是不是套壳”，回答重点是：

- 套壳通常只有 prompt 和一次模型调用，这个项目有任务队列、状态持久化、事件流、Agent steps、RAG index、报告 schema 和证据链 API。
- 报告不是凭空生成，结论必须绑定 evidence refs。
- 长任务失败不是静默失败，系统有错误分类、结构化日志和 Day28 retry。
- 项目有测试和 CI，不只靠手工演示。

可以这样说：

> 我判断一个 Agent 项目是不是工程化，主要看它能不能处理失败、能不能追踪执行过程、能不能证明输出依据。这个项目就是围绕这三点做的。

## 技术选择怎么讲

FastAPI：

- 适合 Python AI / 数据处理栈。
- Pydantic schema 和 API 输入校验天然贴合。
- 适合快速做清晰的后端 API。

Celery + Redis：

- 评论采集和报告分析是长任务。
- API 不应该等几分钟再返回。
- Celery 负责任务分发，Redis 负责 broker 和实时状态缓存。

PostgreSQL + pgvector：

- PostgreSQL 负责长期事实来源。
- 任务、事件、Agent steps、评论和报告都需要可追溯。
- pgvector 是评论语义检索的长期方向。

Playwright：

- 需要处理网页采集和动态页面。
- 当前只做最小采集和 fixture 流程，不承诺全网稳定反爬。

Next.js：

- 用于构建控制台，展示任务提交、进度、历史报告和证据链。
- 前端不承载核心业务逻辑，业务事实来自 API。

## 如果被追问：Day 28 做了什么

回答：

> Day 28 做的是失败任务 retry 和恢复策略。只有可恢复错误码能 retry，比如 `PAGE_TIMEOUT`、`NETWORK_ERROR`、`ACCESS_BLOCKED`。retry 复用原 `task_id`，旧事件保留，新事件追加。状态会从 `failed -> waiting_retry -> queued -> running` 推进。Worker 收到 recovery payload 后会写入 `task recovery resumed` 事件。当前它是任务级恢复，还不是 Agent step 级 replay。

继续补一句边界：

> 我没有马上加 `task_retries` 表和 Celery countdown，是为了控制 Day28 的改动范围。当前 retry metadata 暂存在 `options.recovery`，后续如果要做恢复成功率和更细审计，再拆表更合理。

## 如果被追问：Day 29 做了什么

回答：

> Day 29 不是继续堆功能，而是把项目整理成可展示作品。我重写了 README、演示脚本、简历表达和面试讲述稿，并用 `tests/test_day29_demo_docs.py` 锁住这些文档必须包含快速启动、架构图、演示路径、已知边界、verified metrics 和 Day28 retry 边界。这样后续展示时不靠临场口头解释，也不会把未验证能力写进简历。

这个回答的重点是：文档也当作工程交付物，而不是附属品。

## 高频问题

### 为什么不用一个 Python 脚本直接跑？

因为真实任务可能持续数分钟，HTTP 请求容易超时，而且失败后无法恢复。FastAPI + Celery 把任务提交和任务执行解耦，用户能拿到 `task_id`，系统能持续记录状态和事件。

### 为什么 Agent 状态要落库？

因为 Agent 失败时要知道卡在 Thought、Action 还是 Observation。落库后可以复盘工具参数、工具结果和错误码，也能给前端展示脱敏执行摘要。

### RAG 在项目里解决什么？

评论数量多，不能全部塞进模型。RAG 把评论清洗、切片、向量化，Agent 只召回与“质量差”“物流慢”“售后差”等问题相关的片段，报告再引用这些 evidence refs。

### 爬虫被拦怎么办？

第一版不做违法绕过。系统会做错误分类、保存失败 artifact、记录事件，并支持 CSV/JSON 或 fixture 数据兜底。Day28 增加了可恢复错误 retry，但不可恢复错误不会无限重试。

### 如何证明报告可信？

报告 section 引用 evidence refs，后端提供 `GET /api/reports/{report_id}/evidence` 回查来源。缺失证据会显式返回 missing reason，而不是让模型编造。

### 项目最大的不足是什么？

当前已经补齐可配置 embedding provider 架构、真实 LLM 报告 prompt 契约和 mock 模式 Playwright E2E，但还没有真实 provider 调用、真实 compose up 验证和真实多容器 E2E。Day27 benchmark 是 fixture benchmark，不代表真实线上吞吐。这个边界需要诚实说明。

## 结尾总结

> 我做这个项目最大的收获是：AI 应用落地不是写一个 prompt，而是把不稳定的模型、采集和外部依赖放进一个稳定的工程系统里。这个系统要有任务队列、状态持久化、结构化校验、证据链、失败恢复和质量门禁。

## 关联文档

- 简历表达：`resume-story.md`
- 演示脚本：`demo-script.md`
- 深度防守：`interview-defense-dossier.md`
- 架构细节：`architecture.md`
- 数据模型：`data-model.md`
- Agent 状态机：`agent-state-machine.md`
