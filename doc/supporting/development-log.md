# 开发实时记录

## 文档定位

这份文档记录项目从 Day 1 到 Day 30 的真实开发过程，以及 30 天之后的持续优化记录。它不是路线图，也不是任务计划。

- `roadmap/day-xx.md`：写“计划今天做什么”
- `development-log.md`：写“今天实际做了什么、验证了什么、留下了什么问题”
- `interview-defense-dossier.md`：写“今天新增了哪些面试可讲的技术选择、开发问题和解决过程”
- `change-management.md`：写“高风险变更和回退策略”
- `bug-log-template.md`：写“可复现 bug 的详细根因”
- `research-log-template.md`：写“外部技术调研结论”

## 记录规则

每次完成一个阶段性开发动作后，都要更新本文件。最小记录单位是“一个可回退 commit”，不是“随手写了几行代码”。

每条记录必须尽量包含：

- 日期
- 分支
- 关联计划文档
- 当天开发选择原因：为什么今天做这个，不先做别的
- 技术方案选择原因：为什么选当前实现方式，替代方案是什么
- 实际完成内容
- 关键文件
- 验证命令和结果
- 提交号
- 遗留问题
- 下一步

如果某一天实际开发内容偏离原计划，必须在当天记录里说明偏离原因，并把影响写入 `open-questions.md`、`future-iterations.md` 或对应设计文档。

`development-log.md` 和 `interview-defense-dossier.md` 必须同步维护：前者记录真实开发事实，后者把这些事实转成面试可讲的项目介绍、技术取舍、问题排查和高频追问回答。每完成一个 Day 或一个可回退提交，都要检查这两份文档是否需要更新。

从 Day 6 开始，每天的开发记录必须新增或保留一个“当天选择思考”小节，回答三个问题：

1. 为什么今天优先开发这个能力？
2. 为什么采用当前技术或实现方式？
3. 为什么暂时不做其他看起来也重要的能力？

这部分内容后续要同步沉淀到 `interview-defense-dossier.md`，用于面试时回答“你为什么这么设计”“你做过哪些取舍”“你不是照着教程堆技术栈吗”等问题。

## 当前项目状态

| 项 | 当前值 |
| --- | --- |
| 稳定分支 | `main` |
| 日常开发分支 | `dev` |
| 当前开发阶段 | Day 23 测试体系加固 |
| 当前主链路 | 文档基线、Next.js 控制台骨架、前端真实 API client、真实任务提交表单、任务详情轮询面板、历史任务列表、历史报告列表、报告详情真实读取、报告 evidence chain 真实读取、FastAPI health、任务创建 API、public_url 安全校验、Celery 入队、Redis 状态快照、Redis 事件流、PostgreSQL 任务与事件持久化、Playwright 最小采集、HTML 证据 artifact、采集结果入库、Agent 工具 schema、工具注册机制、Agent Run / Step 持久化、Agent step 查询 API、最小 ReAct 状态机、结构化输出 Guardrails、自愈统计、短期记忆滑动窗口、上下文摘要压缩、评论清洗、评论切片、fake embedding、review chunk 入库、相似度检索原型、search_reviews_tool、结构化报告生成骨架、报告入库、证据链回查 API、风险机会评分、结构化错误日志、观测错误查询 API、数据库模型、Alembic 迁移 |
| 最新开发提交 | 以 `git log -1 --oneline` 为准 |
| 当前数据库决策 | PostgreSQL + pgvector，review chunk 使用 `vector(1536)` |
| 当前模型决策 | 默认 `gpt-5.4-mini`，报告模型 `gpt-5.5`，embedding `text-embedding-3-small` |

## 定位修正记录

### 2026-05-25

用户提出项目实际市场价值和真实需求问题后，项目定位从较宽泛的“电商竞品调研 Agent”收窄为：

> 面向电商运营场景的评论洞察与证据链报告 Agent。

这次修正明确了三条边界：

- 不替代成熟卖家工具。
- 不做销量预测、广告优化、库存管理等大而全能力。
- 第一版聚焦评论洞察、差评证据、报告可追溯和长任务可追踪。

相关文档：

- `market-positioning.md`
- `project-charter.md`
- `resume-story.md`
- `interview-story.md`
- `demo-script.md`

## Day 1 到 Day 30 总览

| Day | 状态 | 实际主题 | 主要提交 |
| --- | --- | --- | --- |
| Day 01 | Done | 仓库、文档、后端骨架、Next.js 控制台骨架 | `ff5f943` |
| Day 02 | Done | 架构冻结、分支策略、模型和数据源决策 | `d8e5ce2`、`c3fff46` |
| Day 03 | Done | SQLAlchemy 数据模型与 Alembic 初始迁移 | `e258898` |
| Day 04 | Done | API 契约与任务接收层 | `1abe635` |
| Day 05 | Done | Celery + Redis 基础任务队列 | `10c11c1` |
| Day 06 | Done | 任务状态流与事件流 | `e7d361c` |
| Day 07 | Done | 第一周联调、任务事件持久化和基础设施验收 | `a70787a` |
| Day 08 | Done | Playwright 最小采集、字段抽取、失败分类与 HTML 证据 artifact | `f9d43ca` |
| Day 09 | Done | 采集结果入库、artifact 入库、评论入库和幂等策略 | `978d425` |
| Day 10 | Done | Agent 工具 schema、工具注册机制、统一执行 envelope | `cad1671` |
| Day 11 | Done | Agent ReAct 循环与状态落库 | `8e47731` |
| Day 12 | Done | Pydantic Guardrails 与 self-heal | `5b1c0cf` |
| Day 13 | Done | 短期记忆与上下文压缩 | `c552801` |
| Day 14 | Done | 评论切片与 embedding 写入 | `ed4597d` |
| Day 15 | Done | `search_reviews_tool` 语义检索 | `ac23718` |
| Day 16 | Done | 报告 schema 与确定性报告生成骨架 | `193da03` |
| Day 17 | Done | 证据链引用和报告可追溯 | `363dd34` |
| Day 18 | Done | 评论机会点评分与风险分析 | `dfc2117` |
| Day 19 | Done | Next.js 接真实 API | `3fab1b3` |
| Day 20 | Done | 前端任务进度与 Agent step 展示 | `3ff03a8` |
| Day 21 | Done | 历史任务和历史报告真实接入 | `ca09e3a` |
| Day 22 | Done | 日志、trace、错误分类、结构化错误查询 API | `80e372b` |
| Day 23 | Done | 单元测试、校验测试、覆盖率门禁 | 见本提交 |
| Day 24 | Pending | 集成测试与回归样例 | 待记录 |
| Day 25 | Pending | Docker Compose 一键启动 | 待记录 |
| Day 26 | Pending | CI 与版本回退策略 | 待记录 |
| Day 27 | Pending | 性能评估和 benchmark 数据 | 待记录 |
| Day 28 | Pending | 失败重试和续跑机制 | 待记录 |
| Day 29 | Pending | README、demo 和演示素材 | 待记录 |
| Day 30 | Pending | 里程碑发布、tag、指标和复盘 | 待记录 |

## Day 01 记录

### 实际完成

Day 1 原计划是完成仓库、文档入口、版本策略和 GitHub 私有仓库。实际开发中额外推进了后端和前端骨架，形成了可运行的第一版工程基线。

完成内容：

- 创建 30 天 roadmap 和 supporting 横向文档体系。
- 建立 FastAPI 后端骨架：app factory、health endpoint、trace ID middleware、统一响应 envelope。
- 建立 Next.js + TypeScript + Tailwind 控制台骨架。
- 将 Stitch 输出定位为视觉参考，而不是正式生产前端。
- 创建私有 GitHub 仓库并推送 `main`。

### 关键文件

- `README.md`
- `doc/README.md`
- `doc/roadmap/30-day-master-plan.md`
- `backend/app/main.py`
- `backend/app/api/routes/health.py`
- `backend/app/core/config.py`
- `backend/app/core/middleware.py`
- `backend/app/core/responses.py`
- `frontend/src/app/page.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/mock-data.ts`

### 验证记录

- `uv run pytest`：4 passed
- `uv run ruff check backend tests`：通过
- `npm run lint`：通过
- `npm run build`：通过
- `npm audit --audit-level=moderate`：0 vulnerabilities
- 本地 HTTP 验证：`http://127.0.0.1:3000` 返回 200
- 后端健康检查：`http://127.0.0.1:8000/api/health` 返回统一 envelope

### 提交记录

- `8f4109e docs: initialize marketmind agent planning`
- `f36ca3b docs: expand planning docs and cross references`
- `960716d docs: document stitch frontend handoff`
- `d08614f docs: 补充 Stitch 前端生成提示词`
- `ff5f943 feat: 搭建 Next.js 控制台与后端骨架`

### 遗留问题

- Day 1 的实际代码推进超过原计划，后续需要通过 Day 2 文档冻结把边界重新收紧。
- 还没有真实数据库、任务队列和业务接口。
- Stitch 原始目录保留为本地视觉参考，不进入 Git。

### 下一步

进入 Day 2，冻结架构、技术选型、分支策略、模型和数据源决策。

## Day 02 记录

### 实际完成

Day 2 目标是架构总图与技术选型冻结。实际完成了两个层面的冻结：系统架构边界，以及模型/embedding/数据源边界。

完成内容：

- 创建并推送远程 `dev` 分支。
- 明确 `main` 用作稳定演示版本，`dev` 用作日常开发分支。
- 冻结第一版形态为“模块化单体 + Celery worker + PostgreSQL/Redis 基础设施”。
- 明确 API、Worker、Agent、Crawler、RAG、Report、Storage、Observability 的边界。
- 补充部署拓扑和后续可拆分模块列表。
- 冻结默认模型：`gpt-5.4-mini`。
- 冻结报告模型：`gpt-5.5`。
- 冻结 embedding：`text-embedding-3-small`，维度 1536。
- 冻结第一版数据源策略：Demo Dataset + CSV/JSON Upload 优先，Generic URL Crawl 作为能力展示。
- 决定第一版不做真实登录，不做复杂多项目 UI，但数据库保留 `users` 和 `projects`。

### 关键文件

- `doc/supporting/architecture.md`
- `doc/supporting/deployment.md`
- `doc/supporting/tech-stack-decisions.md`
- `doc/supporting/model-and-data-decisions.md`
- `doc/supporting/open-questions.md`
- `doc/supporting/data-model.md`
- `.env.example`
- `backend/app/core/config.py`
- `frontend/.env.example`

### 验证记录

- `uv run pytest`：5 passed
- `uv run ruff check backend tests`：通过
- `npm run build`：通过
- 远程分支：`origin/dev` 已创建

### 提交记录

- `d8e5ce2 docs: 冻结架构与开发分支策略`
- `c3fff46 docs: 明确模型与数据源决策`

### 遗留问题

- 首个定制站点适配器尚未决定。
- 是否加入代理池尚未决定。
- 是否把 planner model 和 report model 暴露给前端配置尚未决定。

### 下一步

进入 Day 3，按冻结的模型和数据源决策设计数据库模型、状态枚举和 Alembic 迁移骨架。

## Day 03 记录

### 实际完成

Day 3 目标是数据库设计与迁移骨架。实际完成了 SQLAlchemy 2.0 ORM 模型、状态枚举、pgvector 字段、Alembic 初始化和测试覆盖。

完成内容：

- 新增 `backend/app/storage/` 包。
- 建立 SQLAlchemy `DeclarativeBase` 和命名约定。
- 定义状态枚举：`TaskStatus`、`AgentRunStatus`、`AgentStepStatus`。
- 定义核心表模型：`users`、`projects`、`tasks`、`task_events`。
- 定义 Agent 状态模型：`agent_runs`、`agent_steps`。
- 定义采集和评论模型：`products`、`crawled_pages`、`reviews`、`review_chunks`。
- 定义报告和辅助模型：`reports`、`artifacts`、`error_logs`。
- 将 `review_chunks.embedding` 固定为 `Vector(1536)`。
- 新增 Alembic 配置、迁移环境和初始迁移 `0001_initial_schema`。
- 初始迁移启用 PostgreSQL `vector` extension。
- 补充迁移计划和数据库变更记录。

### 关键文件

- `backend/app/storage/base.py`
- `backend/app/storage/database.py`
- `backend/app/storage/models.py`
- `backend/app/storage/statuses.py`
- `alembic.ini`
- `migrations/env.py`
- `migrations/versions/0001_initial_schema.py`
- `tests/test_database_models.py`
- `tests/test_migrations.py`
- `doc/supporting/data-model.md`
- `doc/supporting/change-management.md`

### 验证记录

- `uv run ruff check backend tests migrations`：通过
- `uv run pytest`：13 passed
- `uv run alembic heads`：输出 `0001_initial_schema (head)`
- `uv run alembic upgrade head --sql`：成功生成完整建表 SQL
- `npm run build`：通过，确认前端未受后端依赖变更影响

### 提交记录

- `e258898 feat: 设计初始数据库模型与迁移骨架`

### 遗留问题

- 还没有真实 PostgreSQL 容器和迁移执行环境。
- 还没有 repository 层和 seed 脚本。
- 任务创建 API 还没有写入数据库，Day 4 只做契约和接收层。

### 下一步

进入 Day 4，先做 API 契约和任务接收层，再在 Day 5 接真实数据库与 Celery。

## Day 04 记录

### 实际完成

Day 4 原计划是继续做 FastAPI 骨架，但 Day 1 已经提前把骨架完成了，所以今天实际转为“API 契约与任务接收层”开发。

完成内容：

- 新增 `POST /api/tasks`。
- 新增 `TaskCreateRequest`、`TaskAcceptedData` 请求/响应 schema。
- 为任务输入补上 `mode`、`priority`、`source_type` 和 `options` 的约束。
- 保留 `options` 扩展字段，方便后续接 CSV/JSON 导入和更多前端能力。
- 新增统一 validation error envelope，避免 FastAPI 默认校验错误直接暴露。
- Day 3 再检查时补齐了 `agent_steps.updated_at`，让 Agent step 的状态更新也能回看。

### 关键文件

- `backend/app/api/routes/tasks.py`
- `backend/app/api/schemas/tasks.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/ids.py`
- `backend/app/main.py`
- `backend/app/tasks/service.py`
- `backend/app/storage/models.py`
- `migrations/versions/0001_initial_schema.py`
- `tests/test_tasks_api.py`
- `tests/test_database_models.py`

### 验证记录

- `uv run pytest tests\\test_tasks_api.py`：3 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run pytest`：17 passed
- `uv run alembic heads`：`0001_initial_schema (head)`
- `uv run alembic upgrade head --sql`：通过
- `npm run build`：通过

### 提交记录

- `1abe635 feat: 完成 Day 4 任务接收层与校验统一化`

### 遗留问题

- 任务创建接口目前只返回接收结果，还没有写入 `tasks` 表。
- 还没有接 Celery / Redis。
- 还没有任务状态查询接口。

### 下一步

进入 Day 5，把 `POST /api/tasks` 从“接收层”升级为“任务入队层”，让 API 真正把长任务交给后台执行。

## Day 05 记录

### 实际完成

Day 5 的目标是把任务接收层升级成真正的异步任务入口。今天完成了 Celery + Redis 的基础接入，并把任务状态推进拆成“接收态 -> 排队态 -> 运行态 -> 完成态”的最小闭环。

完成内容：

- 新增 Celery app 配置，使用 Redis 作为 broker 和 result backend。
- 新增任务状态存储抽象，并提供 Redis 实现和内存实现。
- 新增 Celery 任务 `process_research_task`，作为最小后台执行单元。
- 新增任务分发器抽象，把 API 和 Celery 投递解耦。
- 将 `POST /api/tasks` 从 Day 4 的“接收层”升级为“入队层”。
- 新增 `GET /api/tasks/{task_id}`，从状态存储读取任务快照。
- 对 Redis 状态缓存不可用和队列不可用做统一错误 envelope。
- 复查时补充 Worker 单元测试，验证最小任务会把状态推进到 `completed`。
- 补充 Day 5 运行环境变量和开发约定。

### 关键文件

- `backend/app/core/config.py`
- `backend/app/core/exceptions.py`
- `backend/app/api/routes/tasks.py`
- `backend/app/api/schemas/tasks.py`
- `backend/app/tasks/dependencies.py`
- `backend/app/tasks/dispatcher.py`
- `backend/app/tasks/service.py`
- `backend/app/tasks/status_store.py`
- `backend/app/worker/celery_app.py`
- `backend/app/worker/tasks.py`
- `.env.example`
- `doc/supporting/api-contract.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/dev-environment.md`
- `backend/README.md`
- `tests/test_tasks_api.py`
- `tests/test_celery_worker.py`

### 验证记录

- `uv run pytest tests\\test_tasks_api.py tests\\test_celery_worker.py`：10 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run pytest`：25 passed

### 提交记录

- `10c11c1 feat: 接入 Celery Redis 异步任务管线`

### 遗留问题

- 现在的“状态查询”仍然是 Redis 快照，不是数据库持久化。
- Worker 只做了最小的状态推进，还没有真实爬虫或模型调用。
- 还没有事件表写入和时间线查询。

### 下一步

进入 Day 6，把任务状态流和事件表写入补全，让 API 能看到更细的进度和失败原因。

## Day 06 记录

### 实际完成

Day 6 的目标是让任务不再是黑盒。今天把“状态”进一步拆成“状态快照 + 事件流”两层：状态快照保留当前最新结果，事件流保留每次关键变化，前端后续可以直接读事件列表，不需要解析日志。

完成内容：

- 新增 `TaskEventData` 和 `TaskEventsData` schema。
- 新增事件存储抽象，并提供 Redis 实现和内存实现。
- `POST /api/tasks` 在创建、排队、失败时写入结构化事件。
- Worker 最小任务在 running 和 completed 时写入结构化事件。
- 新增 `GET /api/tasks/{task_id}/events`。
- 事件格式统一包含 `event_id`、`task_id`、`status`、`event_type`、`message`、`payload`、`trace_id`、`created_at`。
- 为事件存储不可用增加统一错误 envelope。
- 补充事件流和 worker 状态推进的测试。

### 当天选择思考

今天优先做事件流，不是因为它看起来更“亮眼”，而是因为到 Day 5 为止，系统已经有了任务提交和状态快照，但还缺少“过程可见性”。如果没有事件流，任务虽然能 queued，但用户仍然不知道它什么时候开始执行、有没有失败、卡在哪一步。

我选择用 Redis 列表作为实时事件层，原因是：

- 它天然保持顺序，适合 append-only 的事件时间线。
- 开发成本低，能快速把前端进度展示跑起来。
- 它和 Day 5 的 Redis 状态快照天然可以共存。

我没有在 Day 6 先把 PostgreSQL 的 `task_events` 持久化写入做完，原因是今天的重点是先把“事件流接口”打通，让任务状态不再黑盒。持久化审计层可以放在 Day 7 联调时一起接入，这样更容易验证 API、Worker、前端的时间线展示。

### 关键文件

- `backend/app/api/routes/tasks.py`
- `backend/app/api/schemas/tasks.py`
- `backend/app/tasks/event_store.py`
- `backend/app/tasks/dependencies.py`
- `backend/app/tasks/service.py`
- `backend/app/worker/tasks.py`
- `tests/test_tasks_api.py`
- `tests/test_celery_worker.py`
- `doc/supporting/api-contract.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/data-model.md`
- `doc/supporting/ui-console-spec.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run ruff check backend tests migrations`：通过
- `uv run pytest tests\\test_tasks_api.py tests\\test_celery_worker.py`：12 passed
- `uv run pytest`：29 passed
- `npm run build`：通过

### 提交记录

- `e7d361c feat: 增加任务进度事件流`

### 遗留问题

- 事件流当前以 Redis 为实时层，PostgreSQL `task_events` 持久化还没接上。
- 还没有 WebSocket / SSE。
- 还没有把任务事件展示接到前端。

### 下一步

进入 Day 7，把任务状态流、事件流和基础设施做一次联调，并补上更稳定的持久化层接入方案。

## Day 07 记录

### 实际完成

Day 7 的目标是把 Day 6 的 Redis 实时事件流接到 PostgreSQL 审计层，并把第一周的任务基础设施做一次收束。实际完成了任务状态和任务事件的 SQLAlchemy 持久化实现，同时保留 Redis 作为实时读取层。

完成内容：

- 新增 `SQLAlchemyTaskStatusStore`，把任务快照写入 `tasks` 表。
- 新增 `SQLAlchemyTaskEventStore`，把结构化任务事件写入 `task_events` 表。
- 新增 `MirroredTaskStatusStore` 和 `MirroredTaskEventStore`，实现 Redis + PostgreSQL 双写。
- API 和 Worker 默认依赖从单 Redis store 升级为 mirrored store。
- `GET /api/tasks/{task_id}` 仍优先读取 Redis 状态快照，Redis 缺失时可以回退到 PostgreSQL。
- `GET /api/tasks/{task_id}/events` 仍优先读取 Redis 事件流，Redis 为空或不可用时可以读取 PostgreSQL 历史事件。
- mirrored store 以 PostgreSQL durable write 为准，Redis 实时层写入失败时不再把已落库结果误判为整体失败。
- 新增本地默认用户和默认项目配置，解决 `tasks.user_id`、`tasks.project_id` 外键落库问题。
- 新增 `queue_task_id` 字段和 Alembic 迁移 `0002_task_queue_id`，用于把 Celery 任务 ID 持久化到 `tasks` 表。
- Worker 在进入 running / completed 时补充 `started_at` 和 `finished_at`。
- 补充 SQLAlchemy 持久化测试，覆盖默认工作区创建、任务状态更新和事件顺序查询。

### 当天选择思考

今天优先做持久化和联调边界，而不是直接进入 Playwright，是因为 Day 6 已经把事件格式和事件写入时机稳定下来，但这些事件还只存在 Redis 里。Redis 适合实时进度，但不适合作为长期审计来源；一旦 TTL 到期或 Redis 重启，历史任务时间线就会丢失。

我选择 mirrored store，而不是在 route 和 worker 里直接写两份逻辑，原因是：

- API route 继续只负责接收请求和返回 envelope，不关心底层双写细节。
- Worker 继续只负责推进任务状态，不直接操作 ORM。
- Redis 与 PostgreSQL 的职责通过 store 抽象隔离，后续接 SSE、历史任务页或 Agent step 时更容易复用。
- 测试可以继续用内存 store，不强依赖本地 Redis 或 PostgreSQL。

我没有在 Day 7 做真正的 Playwright 采集，是因为采集本身会带来页面结构、网络、反爬、浏览器依赖等不稳定因素。如果基础设施还没有完成持久化就接采集，后续排错会分不清是任务系统问题还是采集问题。

### 关键文件

- `backend/app/storage/task_stores.py`
- `backend/app/storage/models.py`
- `backend/app/tasks/dependencies.py`
- `backend/app/worker/tasks.py`
- `backend/app/api/schemas/tasks.py`
- `migrations/versions/0002_task_queue_id.py`
- `tests/test_task_persistence.py`
- `tests/test_database_models.py`
- `tests/test_migrations.py`
- `.env.example`
- `doc/supporting/api-contract.md`
- `doc/supporting/data-model.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\\test_task_persistence.py tests\\test_tasks_api.py tests\\test_celery_worker.py`：19 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run pytest`：36 passed
- `uv run alembic heads`：输出 `0002_task_queue_id (head)`
- `uv run alembic upgrade head --sql`：成功生成 `0001_initial_schema` 到 `0002_task_queue_id` 的 SQL

### 提交记录

- `a70787a feat: 持久化任务状态与事件日志`

### 遗留问题

- 真实 PostgreSQL + Redis + Celery worker 的手工端到端联调还没有执行，当前验证以自动化测试和 Alembic SQL 生成为主。
- 还没有 Docker Compose 一键拉起 PostgreSQL、Redis、API 和 Worker。
- 还没有 WebSocket / SSE。
- 还没有把任务事件展示接到前端。

### 下一步

进入 Day 8，开始 Playwright 最小采集与失败兜底。Day 8 不追求复杂站点适配，优先用本地 HTML fixture 或公开页面跑通采集证据，并继续把采集阶段写入任务事件。

## Day 08 记录

### 实际完成

Day 8 没有直接跳到复杂站点适配，而是把“最小可解释采集链路”先做实。当前实现已经能在 Worker 中对 `public_url` 任务进入采集阶段，先用本地 HTML fixture 跑通，再在具备 Playwright 环境时使用真实页面 best-effort 获取 HTML 内容。

完成内容：

- 新增 `backend/app/crawler/`，拆分为 `errors`、`schemas`、`extractors`、`service` 和 artifact 保存层。
- 接入 `playwright>=1.60.0`，并确认 Chromium 可启动。
- 在 crawler schema 中补充 `task_id`、`artifact_dir`、`save_html_artifact` 等字段，便于后续接入持久化。
- 实现最小 HTML 抽取：标题、价格、评分、可见文本。
- 增加失败分类：`PAGE_TIMEOUT`、`DOM_NOT_FOUND`、`ACCESS_BLOCKED`、`NETWORK_ERROR`、`PARSER_ERROR`、`UNKNOWN_SITE`。
- 支持将成功或失败时的 HTML 证据保存为本地 artifact，并把 artifact 引用写入任务事件。
- Worker 在 `public_url` 任务中补充 crawl 开始 / 成功 / 失败事件，成功事件携带字段摘要和 artifact 引用，失败事件携带错误码和失败原因。
- 新增 fixture 级别测试，覆盖成功抽取、访问拦截、空 DOM、成功 artifact、失败 artifact，以及 Worker 事件写入。

### 当天选择思考

今天的目标不是“把爬虫做得很强”，而是先把“采集链路工程化”建立起来。对这个项目来说，最先需要的不是复杂适配器，而是一个能被任务系统稳定调用、能解释成功和失败、能把证据留下来的采集层。

我把 HTML artifact 保存放在这一天，而不是等到 Day 9 再做，是因为采集成功与否都需要证据出口。没有证据，后续入库、RAG、报告引用和面试复盘都很难说明“结果从哪来”。先把文件型证据链跑通，Day 9 再把它落到 PostgreSQL 的 `crawled_pages` 和 `artifacts` 表，会更顺。

我没有在 Day 8 就做复杂站点适配，是因为复杂适配会把页面结构、网络、浏览器和反爬问题同时引入。先用 fixture 和通用 HTML 提取把边界固定下来，更容易判断后续问题是“采集策略问题”还是“站点适配问题”。

### 关键文件

- `backend/app/crawler/artifacts.py`
- `backend/app/crawler/errors.py`
- `backend/app/crawler/extractors.py`
- `backend/app/crawler/schemas.py`
- `backend/app/crawler/service.py`
- `backend/app/worker/tasks.py`
- `backend/app/core/config.py`
- `.env.example`
- `tests/test_crawler_service.py`
- `tests/test_celery_worker.py`
- `doc/supporting/api-contract.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/crawler-strategy.md`

### 验证记录

- `uv run playwright install chromium`：完成
- `uv run pytest tests\\test_crawler_service.py tests\\test_celery_worker.py`：10 passed
- `uv run ruff check backend tests migrations`：通过

### 提交记录

- `f9d43ca feat: 接入 Day 8 最小采集和证据 artifact`

### 遗留问题

- 目前还没有把 crawler 写入 PostgreSQL 的 `crawled_pages` / `artifacts` 表。
- 目前只保存 HTML artifact，还没有把失败截图也落盘。
- 目前只做了通用 HTML 抽取，还没有接入具体站点 adapter。

### 下一步

进入 Day 9，把 crawler 结果写入 PostgreSQL，同时把 HTML / 截图 / 抽取结果和任务记录真正联起来，让后续 RAG 和报告生成能直接消费结构化采集数据。

## Day 09 记录

### 实际完成

Day 9 的目标是把 Day 8 采集到的证据真正沉淀成数据库资产。今天没有新增迁移，因为 Day 3 已经预留了 `products`、`crawled_pages`、`reviews` 和 `artifacts` 这些实体，所以实现重点放在 storage 封装和幂等写入。

完成内容：

- 新增 `SQLAlchemyCrawlResultStore`，统一负责采集结果持久化。
- 将 `CrawlResult` 映射到 `products`、`crawled_pages`、`reviews`、`artifacts`。
- `Product` 用 `task_id + source_url` 做幂等更新。
- `CrawledPage` 用 `task_id + source_url` 做幂等更新。
- `Artifact` 用 `task_id + artifact_type + checksum` 做幂等更新。
- `Review` 支持页面外部 ID 或稳定 hash 去重。
- Worker 在采集成功后调用持久化 store，把页面证据写入 PostgreSQL。
- 通用 HTML extractor 会顺带抽取简单 review 容器，形成最小评论入库入口。
- 新增采集结果持久化测试，覆盖 product、page、artifact、review 和幂等更新。

### 当天选择思考

Day 8 先做采集、Day 9 再做入库，是为了把“拿到证据”和“沉淀数据资产”拆开。采集层的问题通常是页面结构、浏览器和访问失败；入库层的问题通常是实体关系、幂等和可追踪性。把两件事分开做，调试路径更清楚。

我没有给 `products`、`crawled_pages` 和 `artifacts` 再补一套新表，而是沿用 Day 3 冻结的模型，原因是项目已经有明确的数据分层：任务、页面、评论、报告、证据。如果 Day 9 再重新造表，后续 RAG 和报告引用会乱。

我把幂等策略放在 service 层，而不是先加复杂唯一索引，是因为当前阶段更需要快速跑通“同一任务重复采集不会无限膨胀”这个行为。后面如果真的有高并发冲突，再考虑更强的数据库约束。

### 关键文件

- `backend/app/storage/crawl_stores.py`
- `backend/app/crawler/extractors.py`
- `backend/app/crawler/schemas.py`
- `backend/app/worker/tasks.py`
- `backend/app/tasks/dependencies.py`
- `tests/test_crawl_persistence.py`
- `tests/test_crawler_service.py`
- `tests/test_celery_worker.py`
- `doc/roadmap/day-09.md`
- `doc/supporting/api-contract.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/crawler-strategy.md`
- `doc/supporting/model-and-data-decisions.md`

### 验证记录

- `uv run pytest tests\\test_crawler_service.py tests\\test_crawl_persistence.py tests\\test_celery_worker.py`：14 passed
- `uv run pytest`：47 passed
- `uv run ruff check backend tests migrations`：通过

### 提交记录

- `978d425 feat: 持久化 Day 9 采集结果`

### 遗留问题

- 目前只做了 HTML artifact 入库，没有把截图证据入库。
- 没有给 `artifacts`、`crawled_pages` 加唯一约束，幂等主要依赖 service 层。
- 通用评论抽取只支持简单 review 容器，后续还需要站点适配。

### 下一步

进入 Day 10，把采集、评论和报告相关的工具 schema 固定下来，并开始做工具注册机制，给后面的 ReAct 状态机铺路。

## Day 10 记录

### 实际完成

Day 10 的目标是把后续 Agent 能调用的能力先包装成稳定工具契约，而不是直接开始写 ReAct loop。今天完成了工具 schema、工具注册表和统一执行器的第一版。

完成内容：

- 新增 `backend/app/agent/` 包。
- 新增 `ToolSpec`，描述工具名称、版本、输入 schema、输出 schema、幂等性、重试性和错误码。
- 新增 `ToolManifest`，用于向 Agent 或前端暴露工具清单。
- 新增 `ToolRegistry`，支持注册工具、查询工具、列出工具，并拒绝重复注册。
- 新增 `ToolExecutor`，统一处理输入校验、工具执行、输出校验、错误 envelope、耗时统计和 artifact 汇总。
- 新增 `crawl_product_tool`，把 Day 8/9 的采集能力包装成 Agent 可调用工具。
- 工具失败时不再只返回通用异常，能透传 `ACCESS_BLOCKED` 等 crawler 错误码和失败 artifact。
- 新增工具层测试，覆盖默认工具注册、重复注册、成功执行、输入校验失败、工具不存在和 crawler 分类错误。

### 当天选择思考

今天优先做工具契约，而不是直接做 Agent ReAct 循环，是因为 ReAct 本质上就是“选择工具、组织参数、执行工具、观察结果、决定下一步”。如果工具边界不稳定，后面 Agent loop 会把参数校验、错误处理和业务执行混在一起，调试会非常痛苦。

我选择自己实现轻量 `ToolRegistry` 和 `ToolExecutor`，而不是一开始引入 LangChain / LangGraph，是为了先掌握这个项目最核心的工程边界：工具输入输出 schema、错误分类、幂等标记和统一结果 envelope。后续如果流程复杂，再评估是否迁移到更完整的图执行框架。

`crawl_product_tool` 现在只包装采集能力，不直接写报告，也不让模型操作数据库。这个边界能保证模型只能提出工具调用意图，实际参数校验和执行仍由后端掌控。

### 关键文件

- `backend/app/agent/__init__.py`
- `backend/app/agent/tools/__init__.py`
- `backend/app/agent/tools/schemas.py`
- `backend/app/agent/tools/registry.py`
- `backend/app/agent/tools/executor.py`
- `backend/app/agent/tools/builtin.py`
- `tests/test_agent_tools.py`
- `doc/roadmap/day-10.md`
- `doc/supporting/agent-state-machine.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\\test_agent_tools.py`：6 passed
- `uv run pytest`：53 passed
- `uv run ruff check backend tests migrations`：通过

### 提交记录

- `cad1671 feat: define agent tool contracts`

### 遗留问题

- 工具执行结果还没有写入 `agent_steps`。
- 当前只注册了 `crawl_product_tool`，还没有 `search_reviews_tool` 和报告生成工具。
- 当前工具执行是同步封装，后续如果工具数量和耗时增加，需要评估独立工具队列或异步执行策略。

### 下一步

进入 Day 11，实现最小 ReAct 状态机，让 Agent 能基于任务目标选择工具、校验参数、执行工具，并把 Action / Observation 写入数据库。

## Day 11 记录

### 实际完成

Day 11 的目标是把 Day 10 的工具契约接到真正可持久化的 Agent 执行链路里。今天没有追求完整多轮大模型规划，而是先把最小 ReAct 状态机跑通，让一次 Agent 执行至少能留下 Thought、Action、Observation 三个层次的数据库记录。

完成内容：

- 新增 `backend/app/storage/agent_stores.py`，封装 `agent_runs` 与 `agent_steps` 的 SQLAlchemy 持久化。
- 新增 `SQLAlchemyAgentRunStore`，支持创建 run、标记 running/completed/failed、追加 step、查询最新 step。
- 新增 `AgentStateMachine`，把任务输入映射为最小 ReAct 执行链路。
- 新增 `AgentTaskInput` / `AgentRunResult`，把运行输入与结果从实现细节中抽出来。
- 在状态机中把 Thought、Action、Observation 拆成三条明确的 step 记录，而不是只保留一条模糊日志。
- Tool 调用前后都写入数据库，Action step 先 pending，再 running，结束后再更新为 success / failed。
- 失败时保留旧 step，不覆盖历史记录，并在 observation 中写入结构化失败原因。
- 加入 `max_tool_calls` 限制，避免状态机进入无界循环。
- 新增 Day 11 针对性测试，覆盖 step 顺序、成功链路、失败链路和最大工具调用限制。

### 当天选择思考

今天优先做 ReAct 状态机和 `agent_steps` 持久化，而不是继续扩展工具集合，是因为 Day 10 已经把“工具长什么样、怎么校验、怎么统一返回”固定住了，但 Agent 还没有真正的执行回路。没有执行回路，工具只是静态契约；只有把 Thought / Action / Observation 记下来，Agent 才算进入可回放、可恢复、可面试展示的阶段。

我选择先做“最小单步 ReAct”，而不是直接做完整多轮规划，原因有三个：

- 先验证数据库写入和恢复边界，比先追求大模型聪明更重要。
- 一次完整循环能把状态机、工具执行和结果落库的链路打通，便于后续扩展。
- 这样能把 Day 12 的 guardrails、Day 13 的记忆、Day 15 的检索自然接上，不会在接口上打架。

我没有在今天把 Agent 直接接到 worker 主流程里替代原有采集逻辑，是因为采集结果入库链路已经在 Day 9 验证过，贸然替换会让“任务状态、采集持久化、Agent 持久化”三条线同时变化，排查成本过高。今天更适合把 Agent 自身的状态底座先做扎实。

### 关键文件

- `backend/app/agent/state_machine.py`
- `backend/app/storage/agent_stores.py`
- `backend/app/agent/__init__.py`
- `tests/test_agent_state_machine.py`
- `doc/roadmap/day-11.md`
- `doc/supporting/agent-state-machine.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\\test_agent_state_machine.py`：4 passed
- `uv run pytest`：57 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

### 提交记录

- `8e47731 feat: 实现 Day 11 ReAct 状态机落库`

### 遗留问题

- 现在的状态机还是单步最小版本，还没有接大模型规划器。
- 还没有把 Agent step 的执行结果写到前端控制台。
- 还没有把工具执行结果和未来的 report 生成串起来。

### 下一步

进入 Day 12，给 Agent 输出加 Pydantic guardrails 和 self-heal，让结构化输出失败时能自动重试或纠正。

## Day 12 记录

### 实际完成

Day 12 的目标是把模型输出从“看起来像 JSON”推进到“先校验再进业务”。今天实现的是一个可复用的结构化输出守门层，后续可以给工具选择、报告生成、摘要抽取复用，而不是只给某一处 prompt 写临时修补。

完成内容：

- 新增 `backend/app/agent/guardrails.py`。
- 新增 `AgentToolDecision`，作为工具选择输出 schema。
- 新增 `ReportStructure`，作为报告结构 schema。
- 新增 `StructuredOutputGuardrail`，负责 JSON 解析、Pydantic 校验、self-heal 触发和失败封装。
- 新增 `StructuredOutputParseResult`，记录原始输出、修复后输出、失败次数和自愈次数。
- 新增 `StructuredOutputGuardrailError`，统一携带原始输出、错误详情和统计信息。
- 新增 `build_json_repair_prompt`，把 schema 名称、错误信息和原始输出组织成可修复提示词。
- `AgentRun` 现在可以累计 `validation_error_count` 和 `self_heal_count`，为后续 LLMOps 指标落表留接口。
- 新增 Day 12 针对性测试，覆盖干净 JSON、坏 JSON self-heal、修复调用重试、修复失败和 run 指标累计。

### 当天选择思考

今天优先做 guardrails，而不是继续接新的工具或前端，是因为 Day 11 已经把 Agent 的执行底座打通了，但模型输出本身仍然是不稳定输入。只要输出格式不稳，后面的 planner、报告和证据链都会不断被脏数据扰乱。

我选择把“解析、校验、修复、失败”做成独立模块，而不是散落在各个调用点，原因是：

- 工具选择和报告生成都会遇到结构化输出问题，统一守门更省维护成本。
- `validation_error_count` 和 `self_heal_count` 可以直接沉淀成 LLMOps 指标。
- self-heal prompt 以后可以版本化，便于做回归样例。

我没有在今天接真正的大模型调用，是因为 Day 12 的核心不是模型能力，而是结构化输出边界。先把 JSON 解析、schema 校验、修复提示词和失败封装打牢，后续接任何 LLM provider 都能复用。

### 关键文件

- `backend/app/agent/guardrails.py`
- `backend/app/storage/agent_stores.py`
- `backend/app/agent/__init__.py`
- `tests/test_structured_output_guardrails.py`
- `doc/roadmap/day-12.md`
- `doc/supporting/prompt-strategy.md`
- `doc/supporting/llmops-metrics.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\\test_structured_output_guardrails.py`：6 passed
- `uv run pytest tests\\test_agent_state_machine.py`：4 passed
- `uv run pytest`：63 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

### 提交记录

- `5b1c0cf feat: 实现 Day 12 结构化输出守门`

### 遗留问题

- 现在的 guardrails 还没有接真实 LLM client，只是通用解析和 self-heal 基座。
- 还没有把 guardrails 接到 worker 或 planner 主路径。
- 还没有开始评论切片和 embedding 写入。

### 下一步

进入 Day 13，继续做短期记忆与上下文压缩，把结构化输出和状态机结果接进可复用的记忆层。

## Day 13 记录

### 实际完成

Day 13 的目标是让 Agent 后续多轮执行时不会把所有历史内容无限塞进模型上下文。今天完成了短期记忆模块，并把它以可选依赖接入 Day 11 的状态机。

完成内容：

- 新增 `backend/app/agent/memory.py`。
- 新增 `AgentMemoryEntry`，表示一条可进入上下文的 Thought / Action / Observation 记忆。
- 新增 `AgentMemorySnapshot`，表示当前任务的短期记忆快照。
- 新增 `AgentPromptContext`，把 summary、recent entries 和 evidence refs 组织成 prompt 可读上下文。
- 新增 `AgentShortTermMemory`，实现默认最近 3 条详细保留、更早内容压缩为摘要的滑动窗口策略。
- 新增 `InMemoryAgentMemoryStore`，用于测试和本地无 Redis 场景。
- 新增 `RedisAgentMemoryStore`，用于真实短期上下文缓存。
- 新增 `memory_entry_from_step`，可以把 `AgentStepData` 转成短期记忆。
- 新增 `extract_evidence_refs`，从工具输出中提取 artifact、review、chunk 和 evidence refs。
- `AgentStateMachine` 增加可选 `short_term_memory` 参数。
- 状态机 run 开始前会加载 prompt context。
- Thought、Action、Observation 落库后会同步写入短期记忆。
- 新增 Day 13 测试，覆盖滑动窗口、摘要压缩、证据 ID 保留、从已持久化 step 恢复、状态机写入短期记忆。

### 当天选择思考

今天优先做短期记忆，是因为 Day 11 已经完成 Agent step 落库，Day 12 已经完成结构化输出 guardrails。下一步如果直接进入评论 embedding 或报告生成，Agent 多轮执行时会马上出现上下文无限增长的问题。短期记忆先把“当前任务上下文怎么进入模型”这件事固定住，后续接 RAG 和报告会更顺。

我选择“Redis 短期缓存 + PostgreSQL step 恢复”的组合，而不是只用 Redis，是因为 Redis 适合快速读写当前上下文，但不能作为断点续跑的唯一事实来源。真正可恢复的数据仍然来自 `agent_steps`。

我没有今天就做 LLM summary prompt，是因为 summary prompt 会引入新的模型调用、格式校验和 prompt 漂移。Day 13 先用确定性摘要，让上下文预算和证据 ID 保留变成可测试行为；后续再把 summary prompt 接到 Day 12 的 guardrails。

### 关键文件

- `backend/app/agent/memory.py`
- `backend/app/agent/state_machine.py`
- `tests/test_short_term_memory.py`
- `doc/roadmap/day-13.md`
- `doc/supporting/rag-memory.md`
- `doc/supporting/agent-state-machine.md`
- `doc/supporting/prompt-strategy.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_short_term_memory.py`：4 passed
- `uv run pytest tests\test_agent_state_machine.py tests\test_structured_output_guardrails.py`：10 passed
- `uv run pytest`：67 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

### 提交记录

- `c552801 feat: 实现 Day 13 短期记忆压缩`

### 遗留问题

- 短期记忆已经提供 Redis store，但还没有在 FastAPI / Worker dependency 中默认实例化。
- 当前摘要是确定性摘要，还没有接 LLM summary prompt。
- 当前状态机仍是最小单步 ReAct，短期记忆的价值会在后续多轮 planner、RAG 检索和报告生成中进一步体现。

### 下一步

进入 Day 14，做评论切片与 embedding 写入，把 Day 9 入库的评论转换成可检索的长期记忆。

## Day 14 记录

### 实际完成

Day 14 的目标是把 Day 9 已入库的原始评论变成可检索的长期记忆基础。今天先完成 RAG 数据链路的本地可测版本：清洗、切片、fake embedding、`review_chunks` 幂等入库和 top_k 相似度检索原型。

完成内容：

- 新增 `backend/app/rag/` 包。
- 新增 `clean_review_text`，去除 HTML / script / style 并合并空白。
- 新增 `split_review_text`，按句子边界切片，长句再强制切分。
- 新增 `EmbeddingProvider` 抽象，后续真实 embedding provider 只需要实现同一接口。
- 新增 `DeterministicEmbeddingProvider`，用于本地测试和 embedding 服务不可用时的流程验证。
- 新增 `SQLAlchemyReviewChunkStore.index_task_reviews`，把指定任务下的 reviews 写入 `review_chunks`。
- `review_chunks` 写入时保留 `embedding_model`、`embedding_dimensions`、`source_url`、`rating`、`review_external_id`。
- service 层按 `review_id + task_id + chunk_index + embedding_model + embedding_dimensions` 做幂等 upsert。
- 新增 `search_similar_reviews`，用 Python cosine similarity 做 top_k 检索原型。
- 新增 Day 14 测试，覆盖清洗、切片、fake embedding 稳定性、入库幂等和检索返回来源字段。

### 当天选择思考

今天优先做评论切片和 embedding 入库，是因为 Day 13 已经解决当前任务上下文增长问题，下一步必须把“长期评论证据”变成可检索资产。没有 `review_chunks`，后续 `search_reviews_tool` 只能读原始评论，无法支撑上千评论的精准召回。

我选择先用 fake embedding provider，而不是直接接真实模型，是因为今天的核心风险是数据链路和持久化边界：切片是否稳定、维度是否一致、重复索引是否幂等、检索结果是否带来源。真实 embedding provider 还会引入网络、鉴权、成本和限流，适合在接口稳定后接入。

我选择第一版用 Python cosine 检索，而不是直接写 pgvector SQL，是因为自动化测试使用 SQLite。先固定 `search_similar_reviews` 的输入输出和排序行为，后续在 PostgreSQL 环境中可以替换为 pgvector 原生 `<=>` 排序，不影响上层工具接口。

### 关键文件

- `backend/app/rag/__init__.py`
- `backend/app/rag/text.py`
- `backend/app/rag/embeddings.py`
- `backend/app/rag/review_index.py`
- `tests/test_review_rag_indexing.py`
- `doc/roadmap/day-14.md`
- `doc/supporting/rag-memory.md`
- `doc/supporting/data-model.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/llmops-metrics.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_review_rag_indexing.py`：5 passed
- `uv run pytest tests\test_review_rag_indexing.py tests\test_short_term_memory.py tests\test_agent_state_machine.py`：13 passed
- `uv run pytest`：72 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

### 提交记录

- `ed4597d feat: 实现 Day 14 评论切片与向量索引`

### 遗留问题

- 当前 `DeterministicEmbeddingProvider` 只用于流程验证，不代表真实 embedding 语义质量。
- 当前相似度检索在 Python 中完成，后续 PostgreSQL 环境要切换到 pgvector 原生排序。
- 当前 RAG 检索还没有包装成 Agent tool，Day 15 继续做 `search_reviews_tool`。

### 下一步

进入 Day 15，把 Day 14 的 review chunk 检索能力包装成 Agent 可调用工具，并补充工具 schema、错误分类和 evidence refs。

## Day 15 记录

### 实际完成

Day 15 的目标是把 Day 14 的 RAG 检索能力变成 Agent 可调用工具。今天完成了 `search_reviews_tool` 的输入输出 schema、依赖注入注册、证据片段输出和空召回降级逻辑。

完成内容：

- 新增 `SearchReviewsFilter`，支持评分和来源过滤。
- 新增 `SearchReviewsToolInput`，包含 `query`、`task_id`、`top_k`、`min_similarity` 和 `filters`。
- 新增 `ReviewEvidenceChunk`，规范工具返回的证据片段。
- 新增 `SearchReviewsToolOutput`，包含 `results`、`evidence_refs`、`no_results_reason` 和 metadata。
- 新增 `build_search_reviews_tool_spec`。
- 新增 `run_search_reviews_tool`。
- `build_default_tool_registry` 支持可选注入 `review_chunk_store` 和 `embedding_provider`。
- 默认不传 RAG 依赖时仍只注册 `crawl_product_tool`，避免无数据库场景被 RAG 依赖卡住。
- 工具返回 evidence ref，格式为 `chunk:{chunk_id}`。
- 召回为空时返回 `NO_REVIEW_CHUNKS_ABOVE_THRESHOLD`，不编造证据。
- 新增 `tests/test_search_reviews_tool.py`，覆盖注册、召回和空结果降级。

### 当天选择思考

今天优先做 `search_reviews_tool`，是因为 Day 14 只是完成了 RAG 数据层。Agent 仍然不能主动使用这份评论索引。只有把检索包装成标准工具，后续 ReAct 状态机才能把“需要查退货差评”变成一次可落库、可回放、可失败降级的 Action。

我选择把 `search_reviews_tool` 做成依赖注入注册，而不是默认总是注册，是因为搜索工具需要 `review_chunk_store` 和 `embedding_provider`。如果默认 registry 强依赖数据库，会破坏 Day 10 的工具单元测试和无 RAG 环境下的 crawler 工具使用。

我把 `min_similarity`、评分过滤和 `no_results_reason` 放在工具层，是为了让“证据不足”成为确定性输出，而不是交给模型自由判断。这样后续报告生成可以直接根据 `evidence_refs` 和 `no_results_reason` 决定是否下结论。

### 关键文件

- `backend/app/agent/tools/builtin.py`
- `tests/test_search_reviews_tool.py`
- `doc/roadmap/day-15.md`
- `doc/supporting/rag-memory.md`
- `doc/supporting/agent-state-machine.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/testing-strategy.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_search_reviews_tool.py`：3 passed
- `uv run pytest tests\test_agent_tools.py tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py`：14 passed
- `uv run pytest`：75 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

### 提交记录

- `ac23718 feat: 实现 Day 15 差评语义搜索工具`

### 遗留问题

- 当前工具底层仍使用 Day 14 的 fake embedding 和 Python cosine 检索。
- 还没有把 `search_reviews_tool` 接入真实多轮 planner。
- Day 16 报告生成必须强制只引用 `evidence_refs`，不能引用 query 本身。

### 下一步

进入 Day 16，定义报告 schema 和报告生成输入，把 `search_reviews_tool` 的 evidence chunks 转成可校验的报告结构。

## Day 16 记录

### 实际完成

Day 16 的目标是把 Day 15 的 `search_reviews_tool` evidence chunks 转成可入库、可展示、可校验的报告结构。今天完成了报告 schema、确定性报告生成器、Markdown 渲染和 `reports` 表持久化。

完成内容：

- 新增 `backend/app/reporting/` 模块。
- 新增 `ReportFinding`，定义报告章节、结论、风险等级、建议和 evidence refs。
- 新增 `StructuredReport`，定义报告顶层结构、状态、schema version 和 metadata。
- `StructuredReport` 增加校验：章节引用的 evidence refs 必须存在于报告顶层 `evidence_refs`。
- `StructuredReport.to_markdown()` 输出标题、摘要、章节、风险等级、证据引用和证据摘录。
- 新增 `EvidenceSnippet` 和 `ReportGenerationInput`。
- 新增 `StructuredReportGenerator`。
- 有 evidence snippets 时生成 `draft` 报告，并输出用户痛点、风险判断、机会判断三个章节。
- 无 evidence snippets 时生成 `insufficient_evidence` 报告，明确写“证据不足”，不编造证据。
- 新增 `SQLAlchemyReportStore.save_report()`，把 `content_json`、`content_markdown`、`evidence_refs` 和 `schema_version` 写入 `reports` 表。
- 新增 `tests/test_report_generation.py`，覆盖证据引用校验、无证据降级、Markdown 输出和报告入库。

### 当天选择思考

今天没有直接接真实大模型报告生成，是因为当前最重要的问题不是“报告写得像不像人”，而是“报告能不能被系统证明”。如果 schema、evidence refs 和入库格式不稳定，后续即使模型写得很好，前端和面试讲解也很难解释结论来源。

我选择先做确定性生成器，是为了把报告模块变成可测试的工程组件。它生成的文字不一定是最终版本，但它能固定输入输出、证据约束和无证据降级路径。后续接 LLM 时，只要让模型输出同一个 `StructuredReport` schema，就可以复用 Day 16 的校验和入库逻辑。

我把证据引用校验放在 Pydantic schema 里，而不是只依赖 prompt，是因为 prompt 是软约束，Pydantic 是硬边界。只要章节引用不存在的 `chunk:{chunk_id}`，报告在对象创建阶段就会失败，避免脏报告进入数据库。

我复用 Day 3 的 `reports` 表，没有新增迁移，是因为 `reports` 里已经有 `content_json`、`content_markdown`、`evidence_refs` 和 `schema_version`。这也证明前期数据模型预留是有效的，不需要为了 Day 16 再改数据库结构。

### 关键文件

- `backend/app/reporting/__init__.py`
- `backend/app/reporting/schemas.py`
- `backend/app/reporting/generator.py`
- `backend/app/reporting/stores.py`
- `tests/test_report_generation.py`
- `doc/roadmap/day-16.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/prompt-strategy.md`
- `doc/supporting/data-model.md`
- `doc/supporting/rag-memory.md`
- `doc/supporting/testing-strategy.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_report_generation.py`：4 passed
- `uv run pytest tests\test_report_generation.py tests\test_search_reviews_tool.py tests\test_review_rag_indexing.py`：12 passed
- `uv run pytest`：79 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `cd frontend; npm run build`：通过

### 提交记录

- `193da03 feat: 实现 Day 16 结构化报告生成`

### 遗留问题

- 当前是确定性报告骨架，还没有接真实 LLM report prompt。
- 报告还没有接入 worker 主流程。
- 报告还没有 API 路由和前端详情页。
- Day 17 需要继续做证据链引用强化和报告可追溯展示。

### 下一步

进入 Day 17，把报告 evidence refs 和原始 review chunk / tool output 的追溯关系继续补强，并为后续前端报告详情页准备稳定 API 契约。

## Day 17 记录

### 实际完成

Day 17 的目标是把 Day 16 的报告 evidence refs 变成可回查证据链。今天完成了 evidence ref 解析、数据库回查、报告 citation 绑定、Markdown 证据链渲染和报告证据链 API。

完成内容：

- 新增 `backend/app/reporting/evidence.py`。
- 新增 `EvidenceRef`，定义 evidence ref 解析结果。
- 新增 `EvidenceSource`，定义单条证据来源结构。
- 新增 `EvidenceChain`，定义报告证据链整体输出。
- 新增 `parse_evidence_ref()`，支持 `chunk`、`review`、`artifact`、`step` 四类引用。
- 新增 `SQLAlchemyEvidenceChainStore.resolve()`，根据 `task_id` 和 evidence refs 回查来源。
- `chunk:{chunk_id}` 可以回查到 `review_chunks`，并追溯 parent `review:{review_id}`。
- `review:{review_id}` 可以回查到 `reviews`，并追溯 parent `product:{product_id}`。
- `artifact:{artifact_id}` 可以回查到 `artifacts`。
- `step:{step_id}` 可以回查到 `agent_steps`，并追溯 parent `agent_run:{run_id}`。
- 缺失或跨任务证据返回 `available=false` 和 `missing_reason`。
- 新增 `attach_evidence_chain()`，把 evidence chain 以 JSON 形式放入 `StructuredReport.metadata`。
- `StructuredReport.to_markdown()` 新增“证据链回查”章节。
- 新增 `backend/app/api/routes/reports.py`。
- 新增 `GET /api/reports/{report_id}/evidence`。
- `backend/app/api/router.py` 注册 reports 路由。
- 新增 `tests/test_report_evidence_chain.py`，覆盖 evidence ref 解析、回查、缺失降级、Markdown citation 和 API envelope。

### 当天选择思考

今天优先做证据链回查，是因为 Day 16 只能保证“报告章节引用了合法 evidence ref”，但还不能回答“这个 evidence ref 背后到底是哪条评论、哪个 artifact、哪个 Agent step”。如果报告只停留在 `chunk:xxx` 字符串，前端展示和面试讲解都会缺少说服力。

我选择把证据链设计成结构化 `EvidenceChain`，而不是只在 Markdown 里渲染链接，是因为 Markdown 只是展示层。真正的事实来源应该是 JSON，这样 API、前端、测试和后续 PDF 导出都能复用同一份证据结构。

我暂时没有新增 `report_evidence_links` 表，是因为现有 `reports.evidence_refs` 已经能回查到 `review_chunks`、`reviews`、`artifacts` 和 `agent_steps`。Day 17 先验证引用协议和 API 契约，等 Day 21 做历史报告和版本管理时，再判断是否需要独立关联表。

### 关键文件

- `backend/app/reporting/evidence.py`
- `backend/app/reporting/schemas.py`
- `backend/app/reporting/__init__.py`
- `backend/app/api/routes/reports.py`
- `backend/app/api/router.py`
- `tests/test_report_evidence_chain.py`
- `doc/roadmap/day-17.md`
- `doc/supporting/api-contract.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/data-model.md`
- `doc/supporting/agent-state-machine.md`
- `doc/supporting/testing-strategy.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_report_evidence_chain.py`：7 passed
- `uv run pytest tests\test_report_evidence_chain.py tests\test_report_generation.py tests\test_search_reviews_tool.py tests\test_tasks_api.py`：25 passed
- `uv run pytest`：86 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `cd frontend; npm run build`：通过

### 提交记录

- `363dd34 feat: 实现 Day 17 报告证据链回查`

### 遗留问题

- 前端还没有消费 `GET /api/reports/{report_id}/evidence`。
- 报告详情页还没有点击跳转到证据来源。
- 当前 evidence chain 通过现有表动态解析，尚未独立快照成关联表。
- 报告仍未接入完整 worker 主流程。

### 下一步

进入 Day 18，基于已经可追溯的 evidence chain 做评论机会点评分与风险分析，避免评分结论脱离证据。

## Day 18 记录

### 实际完成

Day 18 的目标是在报告和证据链基础上加入可解释评分，让报告能够区分“轻微问题”和“高风险问题”。今天完成了确定性风险/机会评分模块、评分 schema、样本不足降权、报告 Markdown 评分展示和对应测试。

完成内容：

- 新增 `backend/app/reporting/scoring.py`。
- 新增 `ScorecardInput`。
- 新增 `DimensionScore`。
- 新增 `AnalysisScorecard`。
- 新增 `CompetitiveRiskScorer`。
- 新增 `attach_scorecard_to_report()`。
- 支持质量、物流、售后、价格、包装、功能缺陷六类维度。
- 每个维度按 evidence snippets 的关键词匹配、评论评分、相似度和样本数生成风险分。
- 机会分基于风险分和置信度生成，用于表达“痛点是否值得转成改进机会”。
- 样本数低于 `minimum_samples` 时降权，并写入 `LOW_SAMPLE_SIZE`。
- 无 evidence snippets 时输出 `insufficient_evidence`，不编造分数。
- `StructuredReport.to_markdown()` 新增“维度评分”章节。
- 新增 `tests/test_report_scoring.py`，覆盖分组、绑定 evidence refs、样本不足降权、无证据降级和 Markdown 展示。

### 当天选择思考

今天优先做评分，是因为 Day 17 已经能证明“结论从哪来”，下一步需要回答“哪些问题更严重、哪些痛点更值得处理”。没有评分，报告还是偏摘要；有了评分，报告才更接近运营分析。

我选择确定性规则评分，而不是让 LLM 直接打分，是因为评分最怕黑盒和不可复现。规则虽然简单，但每个分数都能拆成关键词、评分、相似度和样本数，面试时也能清楚解释。

我没有把评分写入新的数据库字段，是因为当前评分属于报告快照内容，放在 `reports.content_json.metadata.analysis_scorecard` 就能满足展示和导出。等后续要做历史报告筛选或跨任务统计，再考虑独立表。

### 关键文件

- `backend/app/reporting/scoring.py`
- `backend/app/reporting/schemas.py`
- `backend/app/reporting/__init__.py`
- `tests/test_report_scoring.py`
- `doc/roadmap/day-18.md`
- `doc/supporting/data-contract-examples.md`
- `doc/supporting/data-model.md`
- `doc/supporting/prompt-strategy.md`
- `doc/supporting/testing-strategy.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_report_scoring.py`：4 passed
- `uv run pytest tests\test_report_scoring.py tests\test_report_generation.py tests\test_report_evidence_chain.py`：15 passed
- `uv run pytest`：90 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `cd frontend; npm run build`：通过

### 提交记录

- `dfc2117 feat: 实现 Day 18 评论风险机会评分`

### 遗留问题

- 当前评分是规则 baseline，不是机器学习模型或真实 LLM 评分。
- 前端还没有展示 scorecard。
- 评分还没有接入完整 worker 主流程。
- 后续如果要按评分筛选历史报告，需要考虑独立字段或表。

### 下一步

进入 Day 19，把 Next.js 前端开始接真实 API，优先接任务状态、事件流、报告详情和证据链接口。

## Day 19 记录

### 实际完成

Day 19 的目标是把 Next.js 控制台从 mock-first 页面推进到真实 FastAPI 接入。今天没有一次性把所有前端页面都改成真实接口，而是优先打通最核心的长任务入口：前端创建任务、拿到 `task_id`、跳转任务详情页，并让任务详情继续读取真实状态和事件。

完成内容：

- 新增 `tests/test_frontend_api_integration_contract.py`，用契约测试锁定前端真实 API 接入边界。
- 扩展 `frontend/src/lib/types.ts`，新增 `TaskCreateInput`、`TaskAccepted`，并补充任务状态页需要的 `source_type`、`updated_at`、`queue_task_id`、错误字段和事件 payload 字段。
- 重构 `frontend/src/lib/api.ts`，从纯 mock client 升级为真实 API client + fallback client。
- 新增 `ApiEnvelope<T>`，让前端显式消费后端统一响应 envelope。
- 新增 `ApiClientError`，保留后端错误码、HTTP status、trace ID 和 details。
- 新增 `createTask()`，调用真实 `POST /api/tasks`。
- `getTask()` 接入真实 `GET /api/tasks/{task_id}`。
- `getTaskEvents()` 接入真实 `GET /api/tasks/{task_id}/events`。
- `getTaskSteps()` 在后端接口未实现时显式 `return []`，避免任务详情页崩溃。
- `listTasks()`、`listReports()`、`getReport()`、`listEvidence()` 暂时保留 mock fallback，因为对应后端接口尚未完成。
- 新增 `frontend/src/components/new-research-form.tsx`，实现客户端任务提交表单。
- 更新 `frontend/src/app/research/new/page.tsx`，用 `NewResearchForm` 替换静态 mock 表单。
- 更新 `frontend/src/components/app-shell.tsx`，显示当前 API 模式和 API base URL。
- 更新 `frontend/.env.example`，把默认示例切换为 `NEXT_PUBLIC_USE_MOCKS=false`。

### 当天选择思考

今天优先做前端真实 API 接入，是因为后端从 Day 4 到 Day 18 已经积累了任务创建、状态查询、事件流、采集、Agent、RAG、报告和评分能力，但如果控制台还停留在静态 mock，项目演示就仍然需要命令行或测试用例支撑。Day 19 的价值是把“后端工程能力”暴露到一个真实可操作入口。

今天没有直接做完整报告详情页，是因为报告详情依赖 `GET /api/reports/{report_id}`、报告列表、历史任务列表等接口，而这些接口尚未完成。强行在前端做完整页面只会制造更多 mock。更合理的顺序是先打通 `POST /api/tasks`、`GET /api/tasks/{task_id}` 和 `GET /api/tasks/{task_id}/events` 这三个已经稳定的接口，再把未实现接口作为 Day 20/Day 21 的明确后续任务。

我选择自己封装轻量 API client，而不是立即引入 React Query / SWR，是因为 Day 19 的主要风险不是缓存策略，而是接口边界是否真实、错误 envelope 是否能被正确处理、mock fallback 是否被限制在未实现接口上。等 Day 20 开始做轮询、进度刷新和 Agent step 展示时，再评估是否引入数据请求库更合适。

我保留 `NEXT_PUBLIC_USE_MOCKS`，是为了让前端具备开发降级能力。真实 API 模式用于联调和演示，mock 模式用于后端未启动时检查页面布局。但默认 `.env.example` 已经切到真实 API，避免项目长期停在 mock 模式。

### 关键文件

- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`
- `frontend/src/components/new-research-form.tsx`
- `frontend/src/app/research/new/page.tsx`
- `frontend/src/components/app-shell.tsx`
- `frontend/.env.example`
- `tests/test_frontend_api_integration_contract.py`
- `doc/roadmap/day-19.md`
- `doc/supporting/ui-console-spec.md`
- `doc/supporting/stitch-frontend-handoff.md`
- `doc/supporting/api-contract.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_frontend_api_integration_contract.py`：4 passed
- `uv run pytest`：94 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `cd frontend; npm run build`：通过
- `cd frontend; npm run lint`：通过
- Playwright 打开 `http://127.0.0.1:3000/research/new`：页面标题正常，表单控件可见，API 模式显示 `Real API`

### 提交记录

- `3fab1b3 feat: 实现 Day 19 前端真实 API 接入`

### 遗留问题

- `GET /api/tasks` 尚未实现，任务列表页仍然 fallback 到 mock data。
- `GET /api/tasks/{task_id}/steps` 尚未实现，任务详情页的 Agent steps 暂时返回空数组。
- `GET /api/reports` 和 `GET /api/reports/{report_id}` 尚未实现，报告列表和报告详情仍然 fallback。
- 前端还没有轮询、SSE 或 WebSocket，任务详情页不会自动刷新。
- 任务创建成功后如果后端 worker 没启动，详情页可能显示 queued 或失败，需要 Day 20 增强状态提示。

### 下一步

进入 Day 20，围绕任务详情页做进度刷新、Agent step 展示和未实现 steps API 的后端补齐，避免前端只会提交任务但不能有效观察执行过程。

## Day 20 记录

### 实际完成

Day 20 的目标是补齐“任务提交后怎么观察运行过程”的缺口。今天完成了后端 Agent step 查询 API、前端任务详情轮询面板、steps 映射和空态展示。任务详情页现在不再是一次性服务端渲染的静态快照，而是可以持续刷新任务状态、事件时间线和 Agent step 摘要。

完成内容：

- 新增 `GET /api/tasks/{task_id}/steps`。
- 新增 `AgentStepSummaryData` 和 `TaskAgentStepsData`。
- `SQLAlchemyAgentRunStore` 新增 `list_steps_for_task()`。
- `get_agent_run_store()` 进入依赖注入层。
- steps API 先检查任务是否存在，缺失返回 `TASK_NOT_FOUND`。
- 有任务但没有 Agent step 时返回空数组。
- steps API 不返回完整 thought，只返回 `Thought recorded` 摘要。
- tool step 只返回工具名、输入 key 摘要、observation 摘要、耗时和错误码。
- 前端 `getTaskSteps()` 接入真实 `GET /api/tasks/{task_id}/steps`。
- 新增 `BackendTaskSteps`、`BackendAgentStep` 和 `mapBackendAgentStep()`。
- `AgentStep` 前端类型补充 `step_id` 和 `task_id`。
- mock agent steps 补齐 `step_id` 和 `task_id`。
- 新增 `TaskProgressPanel` 客户端组件。
- 任务详情页改为首屏服务端加载后交给 `TaskProgressPanel` 轮询。
- 轮询默认 5 秒一次，终态 `completed`、`failed`、`cancelled` 自动停止。
- 任务详情页新增手动刷新按钮、刷新状态、刷新错误展示和任务失败信息展示。
- `AgentStepsTable` 和 `TaskTimeline` 增加空态。
- 新增 `tests/test_task_steps_api.py`。
- 新增 `tests/test_frontend_task_progress_contract.py`。

### 当天选择思考

今天优先做任务进度和 Agent step 展示，是因为 Day 19 虽然已经能创建任务并进入详情页，但用户仍然无法判断任务是否真的在运行、卡在哪一步、失败原因是什么。对于一个长任务 Agent 系统来说，进度可见性不是装饰，而是最基本的可用性和可调试能力。

我选择先补 `GET /api/tasks/{task_id}/steps`，而不是只在前端继续 mock Agent steps，是因为 `agent_steps` 从 Day 11 起已经进入数据库。如果前端继续显示 mock steps，就会破坏项目一直强调的“状态可追踪”和“证据链可回放”。Day 20 把数据库里的 step 通过 API 暴露出来，才算真正打通 Agent 执行过程展示。

我没有直接做 SSE / WebSocket，是因为当前后端已经有状态、事件和 steps 的查询接口，轮询可以低成本把观测闭环跑通。SSE / WebSocket 会引入连接管理、断线重连、部署代理配置和消息一致性问题，应该等页面和 API 契约稳定后再升级。

我刻意不暴露完整 thought，是因为 Agent 内部推理可能包含 prompt、临时判断、工具参数细节或后续敏感信息。前端第一版只需要展示 step 类型、工具名、状态、耗时、输入摘要、observation 摘要和错误码。这样既能定位问题，又避免把内部推理当成用户可见内容。

### 关键文件

- `backend/app/api/routes/tasks.py`
- `backend/app/api/schemas/tasks.py`
- `backend/app/storage/agent_stores.py`
- `backend/app/tasks/dependencies.py`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/types.ts`
- `frontend/src/lib/mock-data.ts`
- `frontend/src/app/tasks/[taskId]/page.tsx`
- `frontend/src/components/task-progress-panel.tsx`
- `frontend/src/components/agent-steps-table.tsx`
- `frontend/src/components/task-timeline.tsx`
- `tests/test_task_steps_api.py`
- `tests/test_frontend_task_progress_contract.py`
- `doc/roadmap/day-20.md`
- `doc/supporting/api-contract.md`
- `doc/supporting/ui-console-spec.md`
- `doc/supporting/observability.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_task_steps_api.py tests\test_frontend_task_progress_contract.py`：5 passed
- `uv run pytest`：99 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `cd frontend; npm run lint`：通过
- `cd frontend; npm run build`：通过
- Playwright 打开 `http://127.0.0.1:3000/tasks/tsk_9A21`：mock 模式下任务详情页显示 Polling、Refresh、事件时间线和 Agent steps 表格

### 提交记录

- `3ff03a8 feat: 实现 Day 20 任务进度与 Agent Step 展示`

### 遗留问题

- 当前任务进度刷新是轮询，不是 SSE / WebSocket。
- `GET /api/tasks` 尚未实现，任务列表页仍然 fallback 到 mock data。
- `GET /api/reports` 和 `GET /api/reports/{report_id}` 尚未实现，报告列表和报告详情仍然 fallback。
- steps API 当前展示摘要，不支持按 run 过滤或展开单步详情。
- 失败任务重试 `POST /api/tasks/{task_id}/retry` 尚未实现。

### 下一步

进入 Day 21，补历史任务和历史报告相关接口，让任务列表和报告列表从 mock fallback 进入真实数据查询，并为报告详情接入真实报告数据做准备。

## Day 21 记录

### Day 20 复查

开始 Day 21 前先复查 Day 20：

- `uv run pytest tests\test_task_steps_api.py tests\test_frontend_task_progress_contract.py`：5 passed。
- `GET /api/tasks/{task_id}/steps` 已实现，并且返回脱敏 Agent step 摘要。
- `TaskProgressPanel` 已接入任务状态、事件和 steps 轮询。
- 文档检查发现 `ui-console-spec.md` 的 Day 19 fallback 说明仍写着 Agent steps 尚未实现，已经改成“Day 19 未实现，Day 20 已补齐”。

复查结论：Day 20 主功能没有代码遗漏，只有一处文档口径需要修正，已在 Day 21 开始前补齐。

### 实际完成

Day 21 的目标是补齐历史任务和历史报告，让系统从“能跑一次任务”变成“能沉淀任务资产和报告资产”。今天完成了 `GET /api/tasks`、`GET /api/reports`、`GET /api/reports/{report_id}`，并让 Next.js 的任务列表、报告列表和报告详情在真实 API 模式下不再使用 mock fallback。

完成内容：

- 新增 `TaskListData`。
- `TaskStatusStore` 协议新增 `list()`。
- `InMemoryTaskStatusStore` 支持历史列表查询，服务于测试。
- `SQLAlchemyTaskStatusStore` 支持按状态、创建时间、limit、offset 查询历史任务。
- `MirroredTaskStatusStore.list()` 优先读取 PostgreSQL 历史数据。
- `RedisTaskStatusStore.list()` 明确返回不可用错误，避免误把 Redis TTL 数据当成历史事实来源。
- 新增 `GET /api/tasks`。
- 新增 `ReportSectionData`、`ReportSummaryData`、`ReportDetailData`、`ReportListData`。
- 新增 `GET /api/reports`。
- 新增 `GET /api/reports/{report_id}`。
- 报告列表关联 `tasks` 表返回 `task_status`。
- 报告列表从 `evidence_refs` 计算 `evidence_count`。
- 报告列表从 `content_json.metadata.analysis_scorecard.overall_risk_score` 读取 `risk_score`。
- 报告详情把 `content_json.sections` 映射为前端 `sections`。
- 缺失报告返回 `REPORT_NOT_FOUND` envelope。
- 前端 `listTasks()` 在真实 API 模式下调用 `GET /api/tasks`。
- 前端 `listReports()` 在真实 API 模式下调用 `GET /api/reports`。
- 前端 `getReport()` 在真实 API 模式下调用 `GET /api/reports/{report_id}`。
- 前端新增 `BackendTaskList`、`BackendReportList`、`BackendReportSummary`、`BackendReportDetail`。
- 新增 `tests/test_history_api.py`。
- 新增 `tests/test_frontend_history_contract.py`。

### 当天选择思考

今天优先做历史任务和历史报告，是因为 Day 19 和 Day 20 已经打通了任务提交和任务详情观察，但用户还不能回看过去的任务、失败记录和报告。如果系统只能看当前任务，它仍然更像一次性 Demo；能积累历史记录后，才开始具备“工作台”的形态。

我选择让历史任务查询优先读取 PostgreSQL，而不是 Redis，是因为 Redis 在当前架构里承担实时状态缓存，有 TTL，不适合作为长期历史事实来源。PostgreSQL 里有任务、事件、Agent step、报告和证据链，历史页应该从这里查，才能保证可追踪和可复盘。

我选择先做 `limit/offset/total`，而不是直接上 cursor pagination，是因为当前数据规模还小，offset 更容易测试和理解。但 API 已经保留分页结构，后续如果历史记录变多，可以把内部实现升级为 cursor，而前端只需要适配分页控件。

我没有今天做复杂筛选 UI，是因为 Day 21 的核心风险在 API 是否真实、历史数据是否可查、前端是否还在成功时回退 mock。筛选能力已经先落在后端 query 参数里，前端控件可以在后续 UI polish 或 Day 25 E2E 前补。

### 关键文件

- `backend/app/api/routes/tasks.py`
- `backend/app/api/routes/reports.py`
- `backend/app/api/schemas/tasks.py`
- `backend/app/api/schemas/reports.py`
- `backend/app/tasks/status_store.py`
- `backend/app/tasks/service.py`
- `backend/app/storage/task_stores.py`
- `frontend/src/lib/api.ts`
- `tests/test_history_api.py`
- `tests/test_frontend_history_contract.py`
- `doc/roadmap/day-21.md`
- `doc/supporting/api-contract.md`
- `doc/supporting/ui-console-spec.md`
- `doc/supporting/interview-defense-dossier.md`

### 验证记录

- `uv run pytest tests\test_history_api.py`：4 passed。
- `uv run pytest tests\test_frontend_history_contract.py`：2 passed。
- `uv run pytest tests\test_history_api.py tests\test_frontend_history_contract.py tests\test_tasks_api.py tests\test_report_evidence_chain.py`：24 passed。
- `uv run pytest`：105 passed。
- `uv run ruff check backend tests migrations`：通过。
- `uv run alembic heads`：`0002_task_queue_id (head)`。
- `cd frontend; npm run lint`：通过。
- `cd frontend; npm run build`：通过。

### 提交记录

- `ca09e3a feat: 实现 Day 21 历史任务与报告真实接入`

### 遗留问题

- `POST /api/tasks/{task_id}/retry` 尚未实现。
- `GET /api/evidence` 仍未实现，证据总览页继续 mock fallback。
- 报告详情前端字段仍叫 `evidence_ids`，但真实后端值是 evidence refs，后续需要统一命名。
- 历史列表筛选能力已经在 API 层实现，但前端还没有筛选控件。

### 下一步

进入 Day 22，围绕日志、trace、错误分类和可观测性做增强。Day 21 已经让历史任务、报告列表和报告详情进入真实数据链路，Day 22 可以开始把这些链路中的错误和耗时记录得更清楚。

## Day 1-21 阶段审计记录

### 审计背景

在继续 Day 22 之前，先按“能否推到 main 作为稳定演示版本”的标准复查 Day 1-21。审计重点不是继续加新功能，而是检查：

- 是否有后端已完成但前端没有真实接入的断层。
- 是否有文档状态明显落后于代码。
- 是否有安全边界和工程化文档不一致。
- 是否有测试绿了但产品链路仍然混用 mock 的情况。

### 发现并修复的问题

问题 1：报告详情页没有消费报告证据链 API。

- 现象：Day 17 已实现 `GET /api/reports/{report_id}/evidence`，Day 21 已实现报告详情真实读取，但报告详情页仍通过 `listEvidence()` 读取全局 evidence fallback。
- 风险：报告正文是真实数据，证据列表却可能来自 mock 或其他任务，破坏“证据链报告”的核心可信度。
- 修复：新增 `getReportEvidence(reportId)`，报告详情页改为调用 `GET /api/reports/{report_id}/evidence`。
- 测试：新增 `tests/test_frontend_history_contract.py::test_report_detail_uses_real_report_evidence_chain`。

问题 2：`public_url` 任务缺少 URL 安全校验。

- 现象：安全文档要求 URL 校验协议和域名，但 `TaskCreateRequest` 之前只校验非空字符串。
- 风险：后续 crawler 接入真实外部 URL 时，可能被提交 `file://`、localhost、内网地址等目标，形成 SSRF 或本机探测风险。
- 修复：`source_type=public_url` 时只允许 `http` / `https`，并拒绝 localhost、`.local`、loopback、private、link-local、reserved、multicast、unspecified 地址。
- 测试：新增 `tests/test_tasks_api.py::test_create_task_rejects_unsafe_public_url_targets`。

问题 3：报告 evidence chain 的 Agent step metadata 暴露过多内部工具数据。

- 现象：Day 20 已经对任务详情的 Agent step 做脱敏，但 Day 17 的 evidence chain 对 `agent_step` 证据返回完整 `tool_input` 和 `tool_output`。
- 风险：报告详情页接入 evidence chain 后，内部工具参数、模型中间产物或后续敏感字段可能进入前端。
- 修复：`agent_step` evidence metadata 只返回 `tool_input_keys`、`tool_output_keys`、`error_code`、step 基础状态，不返回完整 `tool_input` / `tool_output`。
- 测试：新增 `tests/test_report_evidence_chain.py::test_report_evidence_api_sanitizes_agent_step_metadata`。

问题 4：README 当前阶段过期。

- 现象：README 仍写着“架构冻结 + 基础骨架阶段”，不符合 Day 21 后的真实状态。
- 风险：面试官或未来自己从仓库入口阅读时，会误以为项目只做到 Day 2。
- 修复：更新 README 当前状态、当前阶段和验证命令。

### 审计后仍然保留的计划项

这些不是本次推 main 前必须修复的问题，而是 Day 22 之后的计划项：

- `POST /api/tasks/{task_id}/retry`：失败任务重试。
- `GET /api/evidence`：全局证据检索 / 总览页真实接口。
- 历史任务和历史报告的前端筛选控件。
- 报告详情字段 `evidence_ids` 与真实 evidence refs 的命名统一。
- 真实 embedding provider。
- pgvector 原生 SQL 排序。
- 真实 LLM report prompt。
- Docker Compose 全链路一键启动。
- Playwright E2E。

### 阶段审计验证记录

- `uv run pytest tests\test_tasks_api.py tests\test_report_evidence_chain.py tests\test_frontend_history_contract.py`：23 passed。
- `uv run ruff check backend tests migrations`：通过。
- `npm audit --audit-level=high`：0 vulnerabilities。
- `uvx pip-audit`：No known vulnerabilities found。
- `uv run pytest --cov=backend --cov-report=term-missing`：108 passed，backend coverage 91%。
- `git diff --check`：通过。
- 最终完整门禁：
  - `uv run pytest`：108 passed。
  - `uv run ruff check backend tests migrations`：通过。
  - `uv run alembic heads`：`0002_task_queue_id (head)`。
  - `cd frontend; npm run lint`：通过。
  - `cd frontend; npm run build`：通过。

## Day 08 到 Day 14 记录模板

第二周重点从数据采集进入 Agent 工具和状态机。每天开发后按下面格式补充。

| Day | 计划主题 | 实际完成 | 验证 | 提交 |
| --- | --- | --- | --- | --- |
| Day 08 | Playwright 最小采集与失败兜底 | crawler service、字段抽取、失败分类、HTML artifact、Worker crawl 事件 | crawler/service + worker 测试通过，ruff 通过 | `f9d43ca` |
| Day 09 | 爬虫结果入库和证据保存 | 采集结果入库、artifact 入库、评论入库和幂等策略 | pytest + ruff 通过 | `978d425` |
| Day 10 | 工具 schema 与工具注册机制 | Agent 工具 schema、ToolRegistry、ToolExecutor、`crawl_product_tool` | pytest + ruff 通过 | `cad1671` |
| Day 11 | Agent ReAct 循环 | Agent Run / Step 持久化、最小 ReAct 状态机 | pytest + ruff + build 通过 | `8e47731` |
| Day 12 | Pydantic Guardrails 与 self-heal | 结构化输出守门、JSON repair prompt、run 指标累计 | pytest + ruff + build 通过 | `5b1c0cf` |
| Day 13 | 短期记忆与上下文压缩 | 短期记忆 snapshot、滑动窗口摘要、证据 ID 保留、从 Agent step 恢复、状态机接入记忆 | pytest 67 passed，ruff 通过，alembic head 正常，npm build 通过 | `c552801` |
| Day 14 | 评论切片与 embedding 写入 | 评论清洗、切片、fake embedding、review chunk 幂等入库、相似度检索原型 | pytest 72 passed，ruff 通过，alembic head 正常，npm build 通过 | `ed4597d` |
| Day 15 | `search_reviews_tool` 语义检索 | 工具 schema、依赖注入注册、evidence chunk、空召回降级 | pytest 75 passed，ruff 通过，alembic head 正常，npm build 通过 | `ac23718` |

## Day 15 到 Day 21 记录模板

第三周重点是 RAG、报告、证据链和前端真实接入。每天开发后按下面格式补充。

| Day | 计划主题 | 实际完成 | 验证 | 提交 |
| --- | --- | --- | --- | --- |
| Day 15 | `search_reviews_tool` 语义检索 | 工具 schema、依赖注入注册、evidence chunk、空召回降级 | pytest 75 passed，ruff 通过，alembic head 正常，npm build 通过 | `ac23718` |
| Day 16 | 报告 schema 与确定性报告生成骨架 | `StructuredReport`、证据引用校验、Markdown 渲染、`reports` 入库 | pytest 79 passed，ruff 通过，alembic head 正常，frontend build 通过 | `193da03` |
| Day 17 | 证据链引用和报告可追溯 | evidence ref 解析、EvidenceChain、Markdown citation、报告证据链 API | pytest 86 passed，ruff 通过，alembic head 正常，frontend build 通过 | `363dd34` |
| Day 18 | 评论机会点评分与风险分析 | `AnalysisScorecard`、维度风险分、机会分、样本不足降权、Markdown 评分展示 | pytest 90 passed，ruff 通过，alembic head 正常，frontend build 通过 | `dfc2117` |
| Day 19 | Next.js 接真实 API | `POST /api/tasks` 真实提交、任务状态/事件真实读取、API envelope/error 封装、未实现接口 fallback、新建任务表单 | pytest 94 passed，ruff 通过，alembic head 正常，frontend build/lint 通过 | `3fab1b3` |
| Day 20 | 前端任务进度与 Agent step 展示 | `GET /api/tasks/{task_id}/steps`、脱敏 step 摘要、任务详情轮询面板、空态和刷新错误展示 | pytest 99 passed，ruff 通过，alembic head 正常，frontend build/lint 通过 | `3ff03a8` |
| Day 21 | 历史任务和历史报告 | `GET /api/tasks`、`GET /api/reports`、`GET /api/reports/{report_id}`、真实前端列表和详情映射、历史查询契约测试 | pytest 105 passed，ruff 通过，alembic head 正常，frontend build/lint 通过 | `ca09e3a` |

## Day 22 到 Day 30 记录模板

第四周重点是可观测性、部署、测试、复盘、演示和封版。每天开发后按下面格式补充。

| Day | 计划主题 | 实际完成 | 验证 | 提交 |
| --- | --- | --- | --- | --- |
| Day 22 | 日志、trace、错误分类 | 结构化 JSON 日志入口、敏感字段脱敏、`ErrorLogStore`、API 错误写入、Worker/Crawler 分类错误、`GET /api/observability/errors` | `uv run pytest` 114 passed，ruff 通过，alembic head 正常，frontend lint/build 通过 | `80e372b` |
| Day 23 | 测试体系加固与覆盖率门禁 | quality gate 配置测试、coverage fail-under 80、任务状态转换策略、核心 schema 契约测试 | targeted tests 22 passed，coverage full gate 136 passed，coverage 90.83% | 见本提交 |
| Day 24 | 集成测试与回归样例 | 待记录 | 待记录 | 待记录 |
| Day 25 | Docker Compose 一键启动 | 待记录 | 待记录 | 待记录 |
| Day 26 | CI 与版本回退策略 | 待记录 | 待记录 | 待记录 |
| Day 27 | 性能评估和 benchmark 数据 | 待记录 | 待记录 | 待记录 |
| Day 28 | 失败重试和续跑机制 | 待记录 | 待记录 | 待记录 |
| Day 29 | README、demo 和演示素材 | 待记录 | 待记录 | 待记录 |
| Day 30 | 里程碑发布、tag、指标和复盘 | 待记录 | 待记录 | 待记录 |

## Day 22 开发记录

### 背景

Day 20 和 Day 21 已经让任务详情、历史任务、历史报告进入真实数据链路，但仍有一个工程化缺口：任务失败后只能看业务事件和错误 envelope，缺少一个能按 `trace_id` / `task_id` 查询的结构化错误记录。

Day 22 因此选择先做“可排障闭环”，而不是直接做复杂 LLMOps 面板。

### 实际完成

- 新增 `backend/app/observability/logging.py`，统一结构化日志字段。
- 新增 `backend/app/observability/sanitization.py`，递归脱敏敏感 key。
- 新增 `backend/app/observability/error_store.py`，提供 `ErrorLayer`、`ErrorLogData`、`InMemoryErrorLogStore` 和 `SQLAlchemyErrorLogStore`。
- 修改 `backend/app/core/middleware.py`，保留 `X-Trace-Id` 并新增 `X-Request-Duration-Ms`。
- 修改 `backend/app/core/exceptions.py`，将 API 统一异常写入 `error_logs`。
- 修改 `backend/app/worker/tasks.py`，将 Crawler 失败写入 `layer=crawler`，持久化失败写入 `layer=database`。
- 新增 `backend/app/api/routes/observability.py`，提供 `GET /api/observability/errors`。
- 更新 `doc/roadmap/day-22.md`、`observability.md`、`api-contract.md`、`data-model.md` 和面试文档。

### 当天为什么这样选

可观测性有很多层：日志、指标、trace、告警、dashboard。当前项目最缺的是“失败后能复盘”，所以第一步优先做三件事：

1. 日志字段统一，后续好接 Loguru / OTel。
2. 关键失败入库，方便历史任务复盘。
3. 查询接口成型，后续前端可以直接接调试页。

暂时不接完整 OpenTelemetry，是为了控制复杂度。没有部署、没有集中日志平台、没有服务网格时，OTel 的配置成本会大于收益。

### 当前验证

- `uv run pytest tests\test_observability.py`：6 passed。
- `uv run pytest tests\test_tasks_api.py tests\test_celery_worker.py tests\test_task_persistence.py tests\test_health.py`：25 passed。
- `uv run pytest tests\test_observability.py tests\test_tasks_api.py tests\test_celery_worker.py tests\test_task_persistence.py tests\test_health.py`：29 passed。
- `uv run ruff check backend tests\test_observability.py`：通过。
- `uv run pytest`：114 passed。
- `uv run ruff check backend tests migrations`：通过。
- `uv run alembic heads`：`0002_task_queue_id (head)`。
- `cd frontend; npm run lint`：通过。
- `cd frontend; npm run build`：通过。

### 遗留问题

- 错误日志查询接口还没有前端 UI。
- 错误日志还没有按 `error_code` 聚合统计。
- `POST /api/tasks/{task_id}/retry` 尚未实现，错误分类还没有和自动恢复策略打通。
- 当前结构化日志仍输出到应用日志流，后续可以接 Loguru、OpenTelemetry、ELK 或 Grafana Loki。

## Day 23 开发记录

### 背景

Day 23 原计划是补单元测试和校验测试。但项目从 Day 4 起一直按 TDD 推进，截至 Day 22 已有 API、任务队列、Crawler、Agent、RAG、Report、前端契约和 Observability 测试。因此今天不再机械地“建立 tests 目录”，而是把测试体系升级成可执行的质量门禁。

### 实际完成

- 修改 `pyproject.toml`：
  - 保持 pytest 默认 `addopts = "-q"`。
  - 新增 `[tool.coverage.run] source = ["backend"]`。
  - 新增 `[tool.coverage.report] fail_under = 80` 和 `show_missing = true`。
- 新增 `tests/test_quality_gate_config.py`，防止 coverage 门禁配置被误删。
- 新增 `backend/app/storage/status_policy.py`，沉淀任务状态转换策略。
- 新增 `tests/test_task_status_policy.py`，覆盖合法和非法状态转换。
- 新增 `tests/test_schema_validation_contracts.py`，覆盖任务创建 schema、public URL 安全校验、报告 evidence refs 和状态枚举。
- 更新 `doc/roadmap/day-23.md` 和 `doc/supporting/testing-strategy.md`。

### 当天为什么这样选

今天最重要的取舍是：不把 coverage 强塞进 pytest 默认 `addopts`。

原因是定向测试经常只跑一个小文件。如果这个文件不 import backend 代码，coverage 会是 0，然后 fail-under 直接失败。这会让“快速定位问题”的测试体验变差。最终选择是：

- 日常快速测试：`uv run pytest tests\some_test.py`
- 提交前 coverage 门禁：`uv run pytest --cov=backend --cov-report=term-missing`

这样既保留开发效率，又有可量化的质量线。

状态转换策略也选择先独立，不立即接入 store。原因是状态策略会影响所有任务写入，Day 23 的目标是测试体系加固，不应引入大范围行为变化。后续 Day 28 做 retry / resume 时，再把策略接入业务入口。

### 当前验证

- `uv run pytest tests\test_quality_gate_config.py`：1 passed。
- `uv run pytest tests\test_task_status_policy.py`：11 passed。
- `uv run pytest tests\test_schema_validation_contracts.py tests\test_task_status_policy.py tests\test_quality_gate_config.py`：22 passed。
- `uv run pytest --cov=backend --cov-report=term-missing`：136 passed，backend coverage 90.83%，达到 80% 门槛。

### 遗留问题

- `status_policy.py` 还没有接入 `SQLAlchemyTaskStatusStore` 或 retry / cancel API。
- 还没有 Playwright E2E。
- 还没有真实 PostgreSQL / Redis / Celery 的 Docker 集成测试。
- 还没有 CI workflow。

## 30 天后优化记录

30 天之后不再按 Day 编号推进，改用优化主题记录。

### 优化记录模板

```text
日期：
分支：
优化主题：
背景问题：
实际改动：
影响范围：
验证命令：
指标变化：
提交号：
是否进入简历素材：
后续动作：
```

### 优化方向池

| 方向 | 触发条件 | 记录位置 |
| --- | --- | --- |
| 任务取消和重试 | 用户需要控制长任务 | `future-iterations.md`、本文件 |
| 报告导出 PDF / Markdown | 演示和实际使用需要交付物 | `future-iterations.md`、本文件 |
| 多数据源适配 | Demo Dataset 不足以展示采集能力 | `crawler-strategy.md`、本文件 |
| Prompt 版本回放 | 报告质量波动，需要可复现 | `prompt-strategy.md`、本文件 |
| Agent 运行回放 | 面试展示需要解释推理过程 | `agent-state-machine.md`、本文件 |
| 独立 crawler worker 池 | Playwright 并发成为瓶颈 | `architecture.md`、本文件 |
| 独立 rag worker 池 | embedding 写入成为瓶颈 | `architecture.md`、本文件 |
| LLMOps 面板 | 需要展示成本、失败率和自愈率 | `llmops-metrics.md`、本文件 |

## 每日收尾检查

每天收尾前至少确认：

- 工作区是否干净
- 是否已经提交到 `dev`
- 是否记录了验证命令和结果
- 是否有未解决问题进入 `open-questions.md`
- 是否有高风险变更进入 `change-management.md`
- 是否需要更新 `README.md` 或 supporting 索引
