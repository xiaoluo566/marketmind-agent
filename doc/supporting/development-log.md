# 开发实时记录

## 文档定位

这份文档记录项目从 Day 1 到 Day 30 的真实开发过程，以及 30 天之后的持续优化记录。它不是路线图，也不是任务计划。

- `roadmap/day-xx.md`：写“计划今天做什么”
- `development-log.md`：写“今天实际做了什么、验证了什么、留下了什么问题”
- `change-management.md`：写“高风险变更和回退策略”
- `bug-log-template.md`：写“可复现 bug 的详细根因”
- `research-log-template.md`：写“外部技术调研结论”

## 记录规则

每次完成一个阶段性开发动作后，都要更新本文件。最小记录单位是“一个可回退 commit”，不是“随手写了几行代码”。

每条记录必须尽量包含：

- 日期
- 分支
- 关联计划文档
- 实际完成内容
- 关键文件
- 验证命令和结果
- 提交号
- 遗留问题
- 下一步

如果某一天实际开发内容偏离原计划，必须在当天记录里说明偏离原因，并把影响写入 `open-questions.md`、`future-iterations.md` 或对应设计文档。

## 当前项目状态

| 项 | 当前值 |
| --- | --- |
| 稳定分支 | `main` |
| 日常开发分支 | `dev` |
| 当前开发阶段 | Day 4 已完成，准备进入 Day 5 |
| 当前主链路 | 文档基线、Next.js 控制台骨架、FastAPI health、任务创建 API 契约、数据库模型、Alembic 初始迁移 |
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
| Day 04 | Pending | API 契约与任务创建接口 | 待记录 |
| Day 05 | Pending | Celery + Redis 基础任务队列 | 待记录 |
| Day 06 | Pending | 任务状态流与事件表写入 | 待记录 |
| Day 07 | Pending | 第一周联调和基础设施验收 | 待记录 |
| Day 08 | Pending | Playwright 采集策略与数据导入兜底 | 待记录 |
| Day 09 | Pending | 爬虫结果入库和证据保存 | 待记录 |
| Day 10 | Pending | 工具 schema 与工具注册机制 | 待记录 |
| Day 11 | Pending | Agent ReAct 循环 | 待记录 |
| Day 12 | Pending | Pydantic Guardrails 与 self-heal | 待记录 |
| Day 13 | Pending | 短期记忆与上下文压缩 | 待记录 |
| Day 14 | Pending | 评论切片与 embedding 写入 | 待记录 |
| Day 15 | Pending | `search_reviews_tool` 语义检索 | 待记录 |
| Day 16 | Pending | 报告 schema 与报告生成 | 待记录 |
| Day 17 | Pending | 证据链引用和报告可追溯 | 待记录 |
| Day 18 | Pending | 评论机会点评分与风险分析 | 待记录 |
| Day 19 | Pending | Next.js 接真实 API | 待记录 |
| Day 20 | Pending | 前端任务进度与 Agent step 展示 | 待记录 |
| Day 21 | Pending | 历史任务和历史报告 | 待记录 |
| Day 22 | Pending | 日志、trace、错误分类 | 待记录 |
| Day 23 | Pending | Docker Compose 一键启动 | 待记录 |
| Day 24 | Pending | 单元测试、集成测试、固定样例 | 待记录 |
| Day 25 | Pending | E2E 与关键用户流验证 | 待记录 |
| Day 26 | Pending | LLMOps 指标统计 | 待记录 |
| Day 27 | Pending | 50 次任务复盘和数据统计 | 待记录 |
| Day 28 | Pending | Demo 脚本、简历素材、截图 | 待记录 |
| Day 29 | Pending | 回归修复和发布准备 | 待记录 |
| Day 30 | Pending | 里程碑封版和总结 | 待记录 |

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

- 本节所在提交即 Day 4 开发提交，具体以 `git log -1 --oneline` 为准。

### 遗留问题

- 任务创建接口目前只返回接收结果，还没有写入 `tasks` 表。
- 还没有接 Celery / Redis。
- 还没有任务状态查询接口。

### 下一步

进入 Day 5，把 `POST /api/tasks` 从“接收层”升级为“任务入队层”，让 API 真正把长任务交给后台执行。

## Day 05 记录模板

计划主题：Celery + Redis 基础任务队列。

实际完成：待记录。

验证记录：待记录。

提交记录：待记录。

遗留问题：待记录。

下一步：待记录。

## Day 06 记录模板

计划主题：任务状态流与事件记录。

实际完成：待记录。

验证记录：待记录。

提交记录：待记录。

遗留问题：待记录。

下一步：待记录。

## Day 07 记录模板

计划主题：第一周联调和基础设施验收。

实际完成：待记录。

验证记录：待记录。

提交记录：待记录。

遗留问题：待记录。

下一步：待记录。

## Day 08 到 Day 14 记录模板

第二周重点从数据采集进入 Agent 工具和状态机。每天开发后按下面格式补充。

| Day | 计划主题 | 实际完成 | 验证 | 提交 |
| --- | --- | --- | --- | --- |
| Day 08 | Playwright 采集策略与数据导入兜底 | 待记录 | 待记录 | 待记录 |
| Day 09 | 爬虫结果入库和证据保存 | 待记录 | 待记录 | 待记录 |
| Day 10 | 工具 schema 与工具注册机制 | 待记录 | 待记录 | 待记录 |
| Day 11 | Agent ReAct 循环 | 待记录 | 待记录 | 待记录 |
| Day 12 | Pydantic Guardrails 与 self-heal | 待记录 | 待记录 | 待记录 |
| Day 13 | 短期记忆与上下文压缩 | 待记录 | 待记录 | 待记录 |
| Day 14 | 评论切片与 embedding 写入 | 待记录 | 待记录 | 待记录 |

## Day 15 到 Day 21 记录模板

第三周重点是 RAG、报告、证据链和前端真实接入。每天开发后按下面格式补充。

| Day | 计划主题 | 实际完成 | 验证 | 提交 |
| --- | --- | --- | --- | --- |
| Day 15 | `search_reviews_tool` 语义检索 | 待记录 | 待记录 | 待记录 |
| Day 16 | 报告 schema 与报告生成 | 待记录 | 待记录 | 待记录 |
| Day 17 | 证据链引用和报告可追溯 | 待记录 | 待记录 | 待记录 |
| Day 18 | 评论机会点评分与风险分析 | 待记录 | 待记录 | 待记录 |
| Day 19 | Next.js 接真实 API | 待记录 | 待记录 | 待记录 |
| Day 20 | 前端任务进度与 Agent step 展示 | 待记录 | 待记录 | 待记录 |
| Day 21 | 历史任务和历史报告 | 待记录 | 待记录 | 待记录 |

## Day 22 到 Day 30 记录模板

第四周重点是可观测性、部署、测试、复盘、演示和封版。每天开发后按下面格式补充。

| Day | 计划主题 | 实际完成 | 验证 | 提交 |
| --- | --- | --- | --- | --- |
| Day 22 | 日志、trace、错误分类 | 待记录 | 待记录 | 待记录 |
| Day 23 | Docker Compose 一键启动 | 待记录 | 待记录 | 待记录 |
| Day 24 | 单元测试、集成测试、固定样例 | 待记录 | 待记录 | 待记录 |
| Day 25 | E2E 与关键用户流验证 | 待记录 | 待记录 | 待记录 |
| Day 26 | LLMOps 指标统计 | 待记录 | 待记录 | 待记录 |
| Day 27 | 50 次任务复盘和数据统计 | 待记录 | 待记录 | 待记录 |
| Day 28 | Demo 脚本、简历素材、截图 | 待记录 | 待记录 | 待记录 |
| Day 29 | 回归修复和发布准备 | 待记录 | 待记录 | 待记录 |
| Day 30 | 里程碑封版和总结 | 待记录 | 待记录 | 待记录 |

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
