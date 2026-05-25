# 面试防守手册：MarketMind Agent 项目深度讲解

## 文档定位

这份文档不是普通项目介绍，而是面试前复习用的“防守手册”。目标是帮助你回答下面几类问题：

- 你这个项目到底解决什么问题？
- 为什么这个项目不是一个套壳大模型 demo？
- 为什么选 FastAPI、Celery、Redis、PostgreSQL、pgvector、Next.js？
- 开发过程中遇到了哪些真实问题？你怎么定位和解决？
- 如果面试官追问架构、数据、异步任务、Agent、RAG、测试、部署、失败恢复，怎么回答？
- 项目还没完全开发完时，怎么诚实但有技术深度地讲当前进度？

这份文档要经常更新。每完成一个 Day，都应该把新的问题、权衡、实现细节、测试结果补进来。

## 实时维护规则

这份文档和 `development-log.md` 是一组配套文档，必须随着开发进度同步更新。

- `development-log.md` 记录事实：做了什么、改了哪些文件、跑了哪些验证、还剩什么问题。
- `interview-defense-dossier.md` 记录面试表达：这个阶段新增了什么可讲的技术选择、工程权衡、问题排查、失败恢复、测试设计和后续规划。

每完成一个 Day 或一个可回退提交时，至少检查下面几件事：

1. 今天有没有新增技术选择？例如为什么引入 Celery、Redis、pgvector、Playwright、Pydantic 或某个测试策略。
2. 今天有没有遇到真实问题？例如配置错误、测试失败、依赖 warning、接口边界变化、文档和代码不一致。
3. 今天有没有新增面试可展示的代码点？例如 API 路由、service 层、worker 任务、schema、测试。
4. 今天有没有新增诚实边界？例如“当前只完成自动化测试，真实端到端联调放到 Day 7”。
5. 今天有没有新增后续计划？例如从 Redis 快照推进到 PostgreSQL 事件流。
6. 今天为什么优先开发这个能力？这个顺序和整个项目主链路有什么关系？
7. 今天为什么选择这个技术方案？有没有考虑过替代方案？为什么暂时没选？

更新原则：

- 不夸大进度，明确“已完成”和“未完成”。
- 只写能被代码、测试、文档或提交记录证明的内容。
- 把失败和修复写清楚，因为面试官往往更关心你怎么定位问题。
- 面试回答要能落到具体文件、具体接口、具体测试，而不是只讲概念。

后续每个开发日建议在本文新增或更新这些区域：

- `当前开发进度怎么讲`
- `每日开发选择思考`
- `开发过程中出现的问题与解决`
- `高频面试问题与回答`
- `目前最适合展示的代码点`
- `后续迭代计划怎么讲`

## 每日开发选择思考

这一节以后按 Day 追加。它专门回答“为什么今天开发这个”和“为什么选择这个方案”。面试时，如果被问到“你是怎么规划项目的”“为什么先做队列再做 Agent”“为什么现在用 Redis 快照而不是直接落库”，就从这里找答案。

### Day 1 到 Day 6 的已有选择

Day 1 先做仓库、文档、后端和前端骨架，是因为项目需要一个可持续迭代的基线。如果一开始就写 Agent 逻辑，后面很容易变成孤立脚本，缺少版本管理、接口边界和展示入口。

Day 2 冻结架构、模型和数据源，是因为项目方向必须先收窄。尤其是从“大而全电商调研”收窄到“评论洞察与证据链报告”，这样后续技术选择才不会发散。

Day 3 做数据库模型和 Alembic，是因为 Agent 项目的核心价值之一是可追踪和可恢复。没有任务表、Agent step、评论、报告和错误日志这些结构，后续很难解释系统如何断点续跑和复盘。

Day 4 做 `POST /api/tasks` 契约，是因为在接 Celery 之前必须先明确 API 输入输出和错误 envelope。否则后面队列、数据库、前端会一起变化，调试成本会很高。

Day 5 接 Celery + Redis，是因为评论采集和 LLM 分析都是长任务，不能让 HTTP 请求一直等待。当天没有直接接真实爬虫或 Agent，是因为异步任务底座还没稳定，先把任务提交、入队、状态查询和队列错误处理跑通更合理。

Day 6 做任务事件流，是因为 Day 5 只能看到“当前状态快照”，但看不到状态是怎么一步步变化的。如果后续要做前端进度条、失败回放、Agent step 调试和断点续跑，就必须先把 `received -> queued -> running -> completed/failed` 这些变化变成结构化事件。当天没有直接做 WebSocket / SSE，是因为实时推送应该建立在稳定事件格式之上，先做可查询事件流更稳。

Day 7 做任务事件持久化和第一周联调，是因为 Day 6 的事件流只在 Redis 实时层里，不能承担长期审计、历史任务回放和断点续跑。当天没有直接进入 Playwright，是因为采集层会引入页面结构、浏览器依赖和网络不稳定性，先把任务状态双写到 PostgreSQL 更利于后续排错。

### Day 8 之后追加模板

```markdown
### Day XX 选择思考

今天优先开发：

- ...

为什么今天做这个：

- ...

为什么选择这个技术或实现方式：

- ...

考虑过但暂时没选的方案：

- ...

这个选择对后续开发的影响：

- ...

面试时可以这样讲：

> ...
```

## 一句话介绍

MarketMind Agent 是一个面向电商运营场景的评论洞察与证据链报告 Agent 系统。用户提交商品链接、Demo Dataset 或评论 CSV/JSON 后，系统通过 FastAPI 接收任务，Celery + Redis 异步执行，后续由采集、清洗、RAG 检索和 Agent 报告生成模块协作，最终输出一份可以追溯到原始评论和工具执行记录的运营分析报告。

更短的版本：

> 这是一个电商评论洞察 Agent，重点不是“让大模型随便写报告”，而是把长任务异步化、把 Agent 执行过程持久化、把报告结论绑定到评论证据链。

## 项目真实价值

### 用户痛点

电商运营或产品分析人员经常要看竞品评论，尤其是差评、退货、质量、物流、售后等信息。人工处理有几个问题：

- 评论数量多，人工翻页成本高。
- 差评内容非结构化，痛点分散在很多评论里。
- 普通 AI 总结容易“看起来有道理”，但没有证据引用。
- 一次完整分析可能包含采集、清洗、检索、总结、报告生成，耗时较长。
- 任务中断后，如果没有状态记录，只能重跑，浪费时间和 token。

### 项目切入点

项目不试图替代成熟卖家工具，也不承诺销量预测、广告投放、库存管理这些大而全能力。第一版只聚焦一个窄但真实的场景：

- 评论洞察
- 差评证据
- 产品缺陷归纳
- 机会点发现
- 长任务状态追踪
- 报告可追溯

这个定位更适合实习项目：范围可控，同时能展示工程化能力。

## 自我思考：我为什么这样设计这个项目

这一节适合在面试中穿插表达。它的重点不是背技术名词，而是让面试官看到：这个项目不是照着教程堆组件，而是有自己的判断、取舍和边界意识。

### 1. 我对 AI Agent 项目的理解

我一开始对 Agent 项目的理解比较直觉：让大模型调用工具，自动完成任务。但真正开始拆这个项目后，我发现一个能写进简历、能被追问的 Agent 项目，重点不应该只是“模型会不会调用工具”，而应该是：

- 模型调用失败怎么办？
- 工具参数不合法怎么办？
- 爬虫或外部服务失败怎么办？
- 长任务跑到一半中断怎么办？
- 用户怎么知道任务进度？
- 报告里的结论怎么证明不是模型编的？
- 后续怎么复盘模型成本、错误率和效果？

所以我对这个项目的定位逐渐从“做一个能自动分析商品的 Agent”变成“做一个可追踪、可恢复、可验证的 Agent 工程系统”。这个变化很重要，因为它决定了后面的技术选择：要有任务队列、状态存储、事件流、结构化校验、RAG 证据链，而不是只写一个 prompt。

面试可以这样说：

> 我后来意识到，AI 应用落地的难点不是让模型输出一段内容，而是把模型这个不稳定组件放进一个稳定的工程系统里。这个项目就是围绕这个思路设计的。

### 2. 我为什么主动收窄项目范围

最初我也考虑过做一个“大而全”的电商调研 Agent：能爬商品、分析销量、看竞品、出报告、给选品建议。但我后来觉得这个方向太容易被质疑。

原因是成熟卖家工具已经覆盖了很多能力，比如：

- 销量估算
- 关键词分析
- 广告投放
- 利润和库存
- Listing 优化
- 市场趋势

一个学生项目如果说要替代这些工具，不现实，也很难讲清楚真实价值。

所以我把范围收窄到“评论洞察与证据链报告”。这个范围更小，但价值更明确：

- 评论数据真实存在。
- 差评和痛点对运营有价值。
- LLM 擅长归纳文本，但需要证据约束。
- RAG 很适合处理大量评论。
- 长任务追踪和报告证据链能体现工程深度。

这个取舍让我觉得项目更可信。它不是一个“万能 AI 运营助手”，而是一个“把评论分析这件事做深”的工程项目。

面试可以这样说：

> 我没有把项目包装成大而全的卖家工具，因为那样很容易变成空泛 demo。我选择收窄到评论洞察，是因为它既有真实业务需求，又能承载异步任务、RAG、Agent 状态机和证据链这些工程点。

### 3. 我对“工程化”的理解

我理解的工程化不是简单地把技术栈写得很多，而是系统具备几个特征：

- 代码有边界：API、service、worker、storage、schema 不混在一起。
- 数据有结构：不是随便存 JSON，而是有任务表、事件表、Agent step、评论表、报告表。
- 任务有生命周期：received、queued、running、completed、failed 这些状态能被观察。
- 失败有分类：不是所有错误都返回 500。
- 变更可回退：有 Git 分支、提交记录和 Alembic 迁移。
- 行为可验证：有 pytest、ruff、build，而不是“我本地跑过”。
- 文档可复盘：开发日志记录实际做了什么，面试文档记录为什么这么做。

所以我不是为了“看起来工业级”才引入 Celery、Redis、PostgreSQL、pgvector，而是因为这个项目的问题本身需要这些能力。

面试可以这样说：

> 我判断一个项目是不是工程化，不看技术名词数量，而看它有没有边界、状态、错误处理、测试、回退和可观测性。

### 4. 我为什么不急着一开始做 Agent 推理

Agent 推理听起来最亮眼，但我没有在 Day 1 就写 Agent loop。原因是：如果没有任务系统、数据模型、状态存储和错误处理，Agent loop 很容易变成一个黑盒脚本。

我选择先做底座：

1. 文档和项目边界。
2. FastAPI 和统一响应。
3. 数据库模型。
4. 任务创建接口。
5. Celery + Redis 异步管线。
6. 事件流和状态追踪。
7. 再接采集、工具、RAG 和 Agent。

这个顺序看起来慢，但它能保证后面的 Agent 不是临时脚本，而是运行在一个可追踪的系统里。

面试可以这样说：

> 我没有急着写 Agent，是因为没有状态系统的 Agent 很难 debug。先把任务和状态底座打稳，后面接 Agent 时每一步才能落库、回放和恢复。

### 5. 我对“文档先行”的思考

这个项目文档比较多，不是为了凑字数，而是因为我想模拟一个真实工程项目的开发方式。

我把文档分成几类：

- `roadmap/day-xx.md`：每天计划做什么。
- `development-log.md`：实际做了什么。
- `architecture.md`：架构边界。
- `data-model.md`：数据对象和关系。
- `api-contract.md`：接口契约。
- `interview-defense-dossier.md`：面试时怎么讲。

这样做有几个好处：

- 防止开发过程中范围失控。
- 当实际开发偏离计划时，有地方记录原因。
- 后续复盘时能看到决策演进，而不只是最终代码。
- 面试时能证明这个项目是持续迭代出来的，不是一天拼出来的 demo。

面试可以这样说：

> 我把开发日志和面试手册都实时维护，是因为我希望每个技术选择都能被解释，每个问题都能被复盘。这也是我训练工程思维的一部分。

### 6. 我对测试策略的思考

Day 5 接 Celery + Redis 时，我没有让测试强依赖真实 Redis。这里有一个取舍：如果测试直接连 Redis，更接近真实环境，但也更容易因为本机服务没启动而失败。

所以我做了两层测试：

- API 和 service 层用 `InMemoryTaskStatusStore` 和 fake dispatcher，验证业务行为。
- Celery 层测试配置和 worker 任务体，验证任务注册和状态推进。

这样可以先保证自动化测试稳定，再把真实 Redis/Worker 联调放到 Day 7。这个策略不是逃避真实联调，而是把“单元行为验证”和“基础设施联调”分开。

面试可以这样说：

> 我不希望单元测试依赖本机 Redis 是否启动，所以通过接口抽象隔离基础设施。真实 Redis 联调会做，但它应该是集成测试或联调步骤，而不是所有测试的前置条件。

### 7. 我对“不要夸大进度”的思考

这个项目目前还在 Day 7，不应该说已经完成完整 Agent 系统。面试时我会明确区分：

- 已完成：后端骨架、数据库模型、任务创建、异步队列、状态快照、任务事件流、PostgreSQL 任务/事件持久化、错误 envelope、测试。
- 正在做：采集层接入和失败兜底。
- 后续做：Agent、RAG、报告、前端真实接入、部署。

我认为这反而是加分项。因为真实开发中，清楚知道自己完成了什么、没完成什么，比把项目包装得过满更可信。

面试可以这样说：

> 我会诚实说明当前进度，但也能讲清楚后续路径。对我来说，可信的迭代计划比夸大完成度更重要。

### 8. 我认为这个项目最能体现我的什么能力

这个项目最能体现的不是“我会调用某个大模型 API”，而是下面几种能力：

- 把一个模糊想法收窄成可落地需求。
- 把需求拆成 30 天可执行计划。
- 设计 API、数据模型、任务队列和状态流。
- 用测试保护关键行为。
- 在开发过程中持续修正文档和架构。
- 能解释每个技术选择背后的原因。

面试可以这样说：

> 这个项目对我来说不只是 AI 项目，也是一次完整的软件工程训练：需求收窄、架构设计、任务拆解、状态建模、错误处理、测试验证和持续复盘。

### 9. 我对后续难点的预判

我认为后续最难的不是继续加页面，而是这些问题：

- 采集不稳定：页面结构变化、反爬、网络失败。
- Agent 工具调用不稳定：参数错、输出格式错、工具失败。
- RAG 召回质量：召回不到关键评论，或者召回太多噪声。
- 报告可信度：结论必须和证据片段绑定。
- 状态一致性：API、Redis、PostgreSQL、Worker 之间的状态不能乱。
- 成本控制：embedding 和 LLM token 不能无限增长。

我后续会优先解决状态一致性和证据链，因为这两个点决定项目是不是可靠。

面试可以这样说：

> 我已经预判后续最大风险是状态一致性和证据可信度，所以前期先做任务状态、事件、Agent step 和 evidence refs，而不是先追求页面效果。

## 当前开发进度怎么讲

截至 Day 7，项目已经完成：

- 文档体系、30 天 roadmap、开发日志。
- Next.js 控制台骨架。
- FastAPI 后端骨架。
- 统一 API envelope 和 trace ID middleware。
- SQLAlchemy 2.0 数据模型和 Alembic 初始迁移。
- PostgreSQL + pgvector 的数据结构设计。
- `POST /api/tasks` 任务创建接口。
- Celery + Redis 异步任务管线。
- Redis 状态快照和 `GET /api/tasks/{task_id}` 查询。
- `GET /api/tasks/{task_id}/events` 任务事件流查询。
- API 和 Worker 在状态变化时写入结构化事件。
- Redis + PostgreSQL mirrored store，任务状态和任务事件可以双写。
- `tasks.queue_task_id` 迁移，用于持久化 Celery 后台任务 ID。
- 本地默认用户和默认项目的按需初始化，解决任务落库外键问题。
- 队列不可用、状态缓存不可用、参数校验失败的统一错误响应。
- pytest + ruff + Next.js build 验证。

还没有完成：

- 真正的 Playwright 数据采集。
- Agent ReAct 状态机。
- 评论 embedding 写入和语义检索。
- 报告生成。
- 前端接真实 API。
- Docker Compose 全链路一键启动。

面试时可以诚实讲：这个项目正在按 30 天里程碑推进，目前已经完成底层任务入口、异步管线、任务事件流和 PostgreSQL 持久化，下一阶段会接 Playwright 采集和 Agent 状态机。重点是展示工程化思路和持续推进能力，而不是假装已经做完所有功能。

## 2 分钟项目介绍话术

这个项目叫 MarketMind Agent，是一个面向电商运营的评论洞察与证据链报告系统。它解决的问题是：运营人员分析竞品时，需要阅读大量评论，尤其是差评，但人工整理很慢，普通大模型总结又缺少证据链。

我的设计不是写一个单体脚本直接爬取再总结，而是把它做成一个工程化的长任务系统。前端提交任务后，FastAPI 立即返回 `task_id`，任务交给 Celery + Redis 后台执行。任务状态会被记录下来，后续 Agent 的 Thought、Action、Observation 也会进入数据库，这样失败后可以定位原因，也可以做断点续跑。

评论数据会经过清洗、切片和 embedding，存入 pgvector。生成报告时，Agent 不直接凭空总结，而是通过语义检索找出相关差评片段，再把结论和证据引用绑定起来。这个项目的重点是异步任务、状态可追踪、RAG 证据链和结构化输出校验，目标是做一个有工程深度的 Agent 项目。

## 5 分钟项目介绍结构

### 1. 背景

电商运营做竞品分析时，常见任务是看评论、找差评、找质量问题、找用户抱怨点。这个工作真实存在，但非常耗时。

### 2. 问题

只用大模型有三个风险：

- 上下文塞不下大量评论。
- 输出可能没有证据。
- 长任务失败后无法恢复。

只用爬虫脚本也有问题：

- HTTP 请求容易超时。
- 任务状态不可追踪。
- 后续很难扩展 Agent、RAG、报告和前端。

### 3. 方案

系统分成几个层次：

- Next.js 前端：提交任务、查看进度、查看报告。
- FastAPI 网关：接收请求、校验参数、返回统一响应。
- Celery + Redis：负责异步任务队列。
- PostgreSQL：存任务、Agent step、评论、报告、错误日志。
- pgvector：存评论向量，支持语义检索。
- Agent 状态机：按照 ReAct 模式调用采集、检索、报告工具。

### 4. 工程亮点

- API 与长任务解耦。
- Agent 状态可回放。
- 报告结论带证据链。
- Pydantic 做输入输出校验。
- 测试覆盖关键接口、队列配置和错误分支。

### 5. 当前进展和后续

目前已完成 Day 1 到 Day 6：后端骨架、数据库模型、任务创建接口、Celery + Redis 异步管线、任务事件流。下一步是第一周基础设施联调和任务事件持久化，然后接 Playwright 采集、Agent 工具、RAG 和报告。

## 为什么选择这些技术

### 为什么用 FastAPI

选择 FastAPI 的原因：

- Python 生态适合 Agent、爬虫、RAG、LLM SDK。
- Pydantic 是 FastAPI 的一等公民，适合做结构化输入输出校验。
- 异步接口和 OpenAPI 文档支持好。
- 对学生项目来说，上手快但足够工程化。

为什么不用 Flask：

- Flask 更轻，但 schema、类型提示、OpenAPI、依赖注入需要更多手动拼装。
- 本项目的 API 契约和校验很重要，FastAPI 更合适。

为什么不用 Django：

- Django 更完整，但项目当前不需要完整后台管理、模板、ORM 全家桶。
- 本项目后端重点是任务网关、Agent、队列、RAG，FastAPI 更轻。

面试回答重点：

> 我不是因为 FastAPI 流行才用，而是因为这个项目对 typed schema、API 契约、Pydantic 校验和 Python AI 生态依赖比较强，FastAPI 的边界最贴合。

### 为什么用 Celery + Redis

电商评论分析是长任务，可能包含采集、清洗、embedding、模型推理和报告生成，持续时间可能从几十秒到数分钟。如果 API 直接执行，会有几个问题：

- HTTP 请求容易超时。
- 前端体验差。
- 任务失败后难以重试。
- 并发任务会阻塞 Web 进程。

Celery + Redis 的价值：

- FastAPI 只负责接收任务并返回 `task_id`。
- Worker 后台执行耗时逻辑。
- Redis 作为 broker 简单、快、部署成本低。
- 后续可以扩展多个 worker。

为什么 Day 5 没直接上更复杂的 Temporal：

- Temporal 很强，适合复杂工作流和 saga，但学习和部署成本更高。
- 当前项目第一版需要先跑通异步任务最小闭环。
- 等任务依赖、补偿、重试策略复杂后，可以评估迁移到 Temporal。

面试回答重点：

> Celery 解决的是生产者-消费者解耦。我的 API 不直接跑爬虫或模型，只创建任务状态并投递队列，这样系统不会被单个长任务拖住。

### 为什么 Redis 既做 broker 又做状态快照

Day 5 里 Redis 有三个用途：

- `redis://localhost:6379/1`：Celery broker。
- `redis://localhost:6379/2`：Celery result backend。
- `redis://localhost:6379/3`：任务状态快照。

这么分库的原因：

- 避免 broker、result、业务状态 key 混在一起。
- 方便后续清理和排查。
- 开发阶段不需要一开始就把任务状态全部写数据库。

为什么任务状态最终还是要进 PostgreSQL：

- Redis 快照适合实时状态和临时查询。
- PostgreSQL 适合长期审计、历史报告、断点续跑和数据分析。
- Day 7 已经通过 mirrored store 把关键任务状态和事件同步写入 PostgreSQL，形成长期审计记录。

面试回答重点：

> Redis 快照是实时层，不是最终事实来源。最终的任务、事件、Agent step 还是要进入 PostgreSQL，这样才有可追溯性。

### 为什么用 PostgreSQL + pgvector

PostgreSQL 用来存结构化状态和业务数据：

- `tasks`
- `task_events`
- `agent_runs`
- `agent_steps`
- `products`
- `reviews`
- `review_chunks`
- `reports`
- `artifacts`
- `error_logs`

pgvector 用来存评论切片向量：

- 评论数量多，不能全部塞进 LLM 上下文。
- 用户痛点往往不是简单关键词，比如“质量差”可能对应“用了两天坏了”“泵不工作”“铰链断了”。
- 向量检索可以按语义召回相关评论。

为什么不用单独向量数据库：

- 第一版规模不大，PostgreSQL + pgvector 能减少系统数量。
- 数据关系和向量在同一个数据库里，开发和部署更简单。
- 后续如果数据量很大，可以再迁移到 Milvus、Qdrant 或 Weaviate。

面试回答重点：

> 我优先选择 pgvector 是为了降低第一版系统复杂度，同时保留向量检索能力。等规模上来后，再把向量检索拆出去更稳。

### 为什么用 SQLAlchemy + Alembic

项目要展示数据库设计能力，所以不能只用内存字典或临时 JSON 文件。

SQLAlchemy 的价值：

- 明确 ORM 模型。
- 方便和 PostgreSQL 对接。
- 能表达表关系、索引、外键。

Alembic 的价值：

- 数据库结构可版本化。
- 每次 schema 改动可回退。
- 符合团队开发习惯。

面试回答重点：

> Agent 项目不应该只有 prompt 和脚本。状态表、迁移、索引和数据关系能体现工程化深度。

### 为什么用 Next.js

前端不是项目核心，但需要一个足够完整的控制台：

- 提交任务。
- 查看任务进度。
- 查看 Agent step。
- 查看报告。
- 查看证据链。

选择 Next.js 的原因：

- React 生态成熟。
- TypeScript 能约束前端数据结构。
- 后续接 API、动态路由、报告详情页都方便。
- 对实习面试来说，Next.js 比临时 HTML 更像真实项目。

为什么不用 Streamlit：

- Streamlit 快，但更像内部 demo。
- 本项目要展示全栈工程结构，Next.js 更适合。

面试回答重点：

> 我用 Next.js 不是为了做炫酷页面，而是为了做一个真实控制台，让长任务状态、报告和证据链能被产品化展示。

### 为什么第一版不做登录

登录不是第一版核心价值。第一版重点是：

- 异步任务链路。
- Agent 状态记录。
- 评论检索。
- 证据链报告。

但数据库保留了 `users` 和 `projects`，原因是：

- 未来扩展多用户、多项目时不需要推翻数据模型。
- 当前可以用默认本地用户和默认项目。

面试回答重点：

> 我没有一开始做登录，是为了避免偏离核心链路。但数据模型预留了用户和项目边界，说明后续扩展路径已经考虑过。

## 开发过程中出现的问题与解决

### 问题 1：最初方案范围过大，像“大而全卖家工具”

现象：

最开始的设想包含竞品调研、爬虫、Agent、RAG、前端、监控，看起来很完整，但市场定位容易被质疑：你凭什么替代 Helium 10、Jungle Scout、卖家精灵？

思考：

成熟卖家工具覆盖关键词、销量估算、广告、库存、利润、Listing 优化等能力，一个学生项目不可能完整替代。强行说替代会显得不可信。

解决：

把项目定位收窄为“电商评论洞察与证据链报告 Agent”。

保留：

- 评论洞察
- 差评分析
- 证据链报告
- 长任务追踪

放弃或延后：

- 销量预测
- 广告优化
- 库存管理
- 全站点稳定采集

面试表达：

> 我中途主动收窄了项目定位，因为我意识到大而全卖家工具不现实。收窄后项目更可信，也更能突出工程深度。

### 问题 2：Day 1 提前做了 FastAPI 骨架，Day 4 文档滞后

现象：

Day 4 原计划写的是 FastAPI 骨架、health、配置读取。但 Day 1 已经提前完成了这些内容。如果 Day 4 继续按旧文档执行，会重复劳动。

解决：

把 Day 4 调整为“API 契约与任务接收层”：

- 新增 `POST /api/tasks`。
- 新增 Pydantic schema。
- 新增统一 validation error。
- 不接数据库、Celery、爬虫和模型。

面试表达：

> 我没有机械执行文档，而是根据实际进度调整 Day 4 范围。这个过程也记录进了开发日志，避免后续文档和代码脱节。

### 问题 3：Day 3 复查时发现 Agent step 缺少 `updated_at`

现象：

Day 3 已经设计了 `agent_steps` 表，但复查“长任务状态可追踪”要求时发现，`agent_steps` 有 `created_at`、`started_at`、`finished_at`，但没有 `updated_at`。

风险：

Agent step 会从 pending 变成 running、success 或 failed。如果没有 `updated_at`，后续做断点续跑、失败定位和时间线分析会不完整。

解决：

- 给 ORM 模型补 `updated_at`。
- 给 Alembic 初始迁移补字段。
- 给测试补断言。
- 给数据模型文档补字段。

面试表达：

> 这是一个小字段，但体现了我对状态可追踪的重视。Agent 项目最怕黑盒运行，所以状态变化时间要尽量完整。

### 问题 4：Git push 出现 `credential-manager-core` warning

现象：

push 时出现：

```text
git: 'credential-manager-core' is not a git command
```

定位：

检查 Git credential helper 发现：

- 系统级配置是新版 `manager`。
- 用户级配置残留旧版 `manager-core`。

解决：

删除用户级旧配置：

```powershell
git config --global --unset credential.helper manager-core
```

结果：

后续 push 不再出现该 warning。

面试表达：

> 这个问题不是代码问题，而是本机 Git 凭据管理器配置残留。我通过 `git config --show-origin --get-all credential.helper` 定位到了配置来源。

### 问题 5：Day 5 测试不能依赖真实 Redis

现象：

Day 5 要接 Celery + Redis，但如果测试必须依赖本机 Redis 启动，CI 和本地开发都会不稳定。

解决：

做了抽象层：

- `TaskStatusStore` 协议。
- `RedisTaskStatusStore` 真实实现。
- `InMemoryTaskStatusStore` 测试实现。
- `TaskQueueDispatcher` 协议。
- `CeleryTaskDispatcher` 真实实现。
- 测试里用 fake dispatcher 和 memory store。

效果：

- 单元测试不依赖 Redis。
- 真实运行仍然走 Celery + Redis。
- API 层和基础设施层解耦。

面试表达：

> 我没有为了测试方便把业务写死成内存实现，而是抽象了状态存储和队列分发器。测试用 fake，生产用 Redis 和 Celery，这是典型的依赖倒置。

### 问题 6：Ruff 报 `Depends()` 默认参数问题

现象：

Ruff 报：

```text
B008 Do not perform function call Depends in argument defaults
```

原因：

FastAPI 常见写法是：

```python
def route(dep = Depends(get_dep)):
    ...
```

但 Ruff 的 bugbear 规则认为函数调用不应该放在默认参数里。

解决：

改成 `Annotated` 写法：

```python
status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)]
```

效果：

- 满足 FastAPI 依赖注入。
- 通过 Ruff。
- 类型表达更清晰。

面试表达：

> 我保留了 FastAPI 的依赖注入能力，同时让代码符合静态检查规则。这个细节能减少团队协作时的风格争议。

### 问题 7：队列不可用和状态存储不可用不能直接 500

现象：

Day 5 接入队列后，如果 Redis broker 或状态缓存不可用，接口可能抛异常变成 500。

风险：

前端不知道是参数错、队列挂了，还是服务内部 bug。

解决：

- 定义 `QueueUnavailableError`。
- 定义 `TaskStatusStoreUnavailableError`。
- 在 API 层捕获并转换成统一 envelope。
- 错误码统一为 `QUEUE_UNAVAILABLE`。

示例响应：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "QUEUE_UNAVAILABLE",
    "message": "task queue is unavailable",
    "details": {
      "reason": "redis broker is unavailable"
    }
  },
  "message": "task queue is unavailable",
  "trace_id": "trc_xxx"
}
```

面试表达：

> 我没有让底层异常直接泄露给前端，而是转换成业务错误码。这样前端可以做明确提示，日志里也能根据 trace ID 定位。

### 问题 8：`uv add` 出现第三方包版本 warning

现象：

安装 Celery 时 `uv` 输出了很多 “Fixing invalid version specifier” warning。

判断：

这些 warning 来自第三方依赖包元数据里不规范的版本描述，`uv` 自动修正后依赖安装成功。

处理：

- 没有把它当成项目代码问题。
- 继续执行测试验证依赖是否可用。
- pytest、ruff 均通过后认为可接受。

面试表达：

> 我区分了依赖解析 warning 和代码错误。最终以 lockfile、import、测试结果作为判断标准。

### 问题 9：Day 5 还没有做真实 Redis/Worker 手工联调

现象：

Day 5 已完成代码、单元测试和配置，但没有启动真实 Redis + Celery worker 做端到端手工联调。

原因：

本阶段优先保证代码结构、抽象边界和自动化测试。真实联调更适合 Day 7 和第一周验收一起做。

补救：

- 文档写清楚本地启动命令。
- 测试覆盖 Celery app 注册和 worker 状态推进逻辑。
- 后续 Day 7 再补 Redis/Worker 实机联调记录。

面试表达：

> 我会诚实说目前自动化测试已经覆盖队列入口和 worker 任务体，但真实 Redis/Worker 端到端联调是后续联调日的任务，不会夸大已完成范围。

### 问题 10：Day 6 为什么先做事件查询，而不是直接做 WebSocket / SSE

现象：

Day 6 的目标是任务状态与进度流。直觉上可以直接做 WebSocket 或 SSE，让前端实时收到进度。

思考：

实时推送只是传输方式，真正核心的是事件格式和事件来源。如果没有稳定的结构化事件，WebSocket 推送的也只是临时日志字符串，后续前端、调试、失败回放都会很难维护。

解决：

- 先定义 `TaskEventData`。
- API 和 Worker 状态变化时写事件。
- 新增 `GET /api/tasks/{task_id}/events`。
- 前端先通过轮询或手动刷新消费事件流。
- 后续再把同一套事件格式接到 SSE / WebSocket。

面试表达：

> 我没有急着做实时推送，因为 WebSocket 解决的是传输问题，不解决事件建模问题。先把事件格式和写入时机稳定下来，后续接 SSE 或 WebSocket 会更自然。

### 问题 11：为什么 PostgreSQL 事件持久化放到 Day 7

现象：

Day 6 已经有 `task_events` 数据表，也已经有 `GET /api/tasks/{task_id}/events` 接口，但当时事件流还只写入 Redis，没有写入 PostgreSQL。

思考：

这不是遗漏，而是有意拆分。Day 6 的核心目标是先稳定事件模型：什么时候写事件、事件字段有哪些、API 和 Worker 如何共同推进状态。如果当天同时做 Redis 事件流、PostgreSQL repository、事务边界、真实 worker 联调，范围会变大，问题也会混在一起。

解决：

- Day 6 先完成 Redis 实时事件流，让任务过程可见。
- Day 7 完成第一周联调，把关键事件写入 PostgreSQL `task_events`。
- Redis 定位为实时展示层，PostgreSQL 定位为审计、历史查询和断点续跑层。
- 双写时以 PostgreSQL 持久化成功为准，Redis 实时层失败时不覆盖 durable write 的成功结果。
- Playwright 采集顺延到 Day 8，避免基础设施联调和采集不稳定性同时出现。

面试表达：

> 我把事件系统拆成两步：Day 6 先把事件格式和写入时机稳定下来，Day 7 再接 PostgreSQL 持久化。这样 Redis 负责实时进度，PostgreSQL 负责长期审计和恢复，边界更清楚。

## 高频面试问题与回答

### Q1：你这个项目和普通“调用大模型生成报告”的项目有什么区别？

普通 demo 通常是输入一段文字，调用 LLM，输出报告。我的项目重点不是 prompt，而是工程链路：

- 长任务异步化。
- 任务状态可追踪。
- Agent 执行步骤可落库。
- 评论数据可向量检索。
- 报告结论能关联证据。
- 失败能分类、重试和恢复。

所以它更接近一个可迭代的业务系统，而不是一次性脚本。

### Q2：为什么不直接把所有评论塞给大模型？

原因有三个：

- token 成本高。
- 评论太多时上下文塞不下。
- 大模型容易忽略细节或编造归纳。

RAG 的作用是先把评论切片向量化，按问题召回最相关的片段，再让模型基于证据生成报告。

### Q3：为什么需要 Agent？普通 pipeline 不行吗？

普通 pipeline 适合固定流程，比如固定采集、固定清洗、固定报告。但运营分析任务可能是动态的：

- 有时需要先找质量问题。
- 有时需要看物流差评。
- 有时需要比较多个竞品。
- 有时爬虫失败要转用上传数据。

Agent 的价值是根据任务目标选择工具和下一步动作。但我不会让 Agent 完全黑盒自治，而是用状态机和工具 schema 约束它。

### Q4：Agent 的风险是什么？你怎么控制？

风险：

- 输出不稳定。
- 工具调用参数不合法。
- 幻觉。
- 长任务中断。

控制方式：

- Pydantic schema 校验工具输入输出。
- Thought / Action / Observation 记录。
- 工具失败分类。
- 自愈重试。
- 报告必须引用证据。
- 状态落库支持恢复。

### Q5：为什么要记录 Thought？生产环境不是可能有隐私风险吗？

开发和调试阶段记录 Thought 可以帮助理解 Agent 为什么调用某个工具。但生产环境可以做两种处理：

- 内部调试环境完整保留。
- 用户可见层只展示 tool、observation summary 和证据，不展示完整 thought。

这样既保留可观测性，又避免暴露不必要的推理内容。

### Q6：如果爬虫被反爬怎么办？

第一版不做违法绕过，也不绕验证码、登录、付费墙。策略是：

- 公共页面 best-effort 采集。
- 限速、重试、失败截图。
- 分类记录错误原因。
- 提供 CSV/JSON 上传作为兜底。

重点是保证评论分析主链路不被某一个站点卡死。

### Q7：为什么不一开始就接真实电商网站？

因为如果第一阶段依赖真实站点，开发会被反爬、页面变化、网络和代理问题拖慢。更合理的顺序是：

1. Demo Dataset 和 CSV/JSON 先保证主链路。
2. 再接通用 URL 采集。
3. 最后做站点适配器。

这样能先验证系统架构，而不是陷入爬虫细节。

### Q8：你怎么设计数据库表？

核心思想是按业务实体和执行过程拆：

- `tasks`：任务主表。
- `task_events`：任务时间线。
- `agent_runs`：一次 Agent 执行。
- `agent_steps`：Thought / Action / Observation。
- `products`：商品信息。
- `reviews`：原始评论。
- `review_chunks`：切片和向量。
- `reports`：报告。
- `artifacts`：截图、HTML、导出文件等证据。
- `error_logs`：结构化错误。

这样既能支持业务查询，也能支持调试和回溯。

### Q9：为什么 Day 5 用 Redis 状态快照，而不是直接写 PostgreSQL？

Day 5 的目标是异步队列最小闭环。Redis 快照足够支持快速查询任务状态，也能减少当天引入数据库事务、repository 和 worker 事务一致性问题。

但长期设计不是只靠 Redis。Day 6 先把状态变化写成 Redis 事件流，Day 7 再把关键任务状态和事件同步写入 PostgreSQL，这样才能支持历史任务、审计和断点续跑。

### Q10：Celery 投递成功但 Worker 没启动怎么办？

API 只负责投递任务。只要 Redis broker 可用，任务会处于 queued。Worker 启动后再消费。

如果 broker 不可用，API 返回 `QUEUE_UNAVAILABLE`。

如果 worker 长时间不消费，后续可以通过：

- queued 超时检测。
- worker heartbeat。
- 任务重试。
- 告警。

### Q11：如何保证报告可信？

报告必须满足几个约束：

- 结论来自检索到的评论片段或采集证据。
- 报告结构由 Pydantic schema 校验。
- 每个风险点或机会点要有 evidence refs。
- 不能把没有证据的数据写进结论。

面试时可以强调：可信不是靠模型“更聪明”，而是靠证据链和结构化约束。

### Q12：如何做失败恢复？

计划中的恢复方式：

- 任务状态写入 `tasks` 和 `task_events`。
- Agent 每一步写入 `agent_steps`。
- 工具调用前先记录 pending。
- 工具成功后写 observation。
- 中断后从最后一条成功 observation 继续。

这样可以减少重复爬取和重复 token 消耗。

### Q13：如何评价这个项目的工程化程度？

可以从几个角度讲：

- 有明确文档体系。
- 有 30 天 roadmap 和开发日志。
- 有 Git 分支策略。
- 有类型和 schema。
- 有 Alembic 迁移。
- 有 pytest 和 ruff。
- 有异步任务队列。
- 有错误码和 trace ID。
- 有后续部署计划。

这比单文件脚本更接近真实团队项目。

### Q14：你怎么做测试？

当前测试包括：

- health endpoint envelope。
- trace ID 保留。
- 配置默认值。
- 数据模型注册。
- pgvector 维度。
- Alembic 迁移。
- `POST /api/tasks` 成功、默认值、校验失败。
- `GET /api/tasks/{task_id}` 成功和 404。
- 队列不可用、状态存储不可用。
- Celery 配置和 worker 任务状态推进。

后续会加：

- repository 集成测试。
- crawler 固定页面测试。
- Agent 工具 schema 测试。
- RAG 检索召回测试。
- Playwright E2E。

### Q15：如果面试官说这个项目太复杂，你怎么回答？

可以承认复杂，但解释分阶段策略：

- Day 1 到 Day 6 先做基础设施和任务可观测性。
- Day 7 到 Day 12 做联调、采集、状态机和工具。
- Day 13 到 Day 18 做 RAG 和报告。
- Day 19 之后做前端真实接入和部署。

复杂度不是一次性堆上去，而是按依赖逐步增加。

### Q16：如果面试官问你最有技术含量的部分是什么？

可以选三个：

1. 长任务异步解耦：FastAPI + Celery + Redis。
2. Agent 状态可追踪：Agent step 落库和断点续跑。
3. 评论 RAG 证据链：pgvector 检索 + 报告 evidence refs。

当前已完成第一个，第二个和第三个在后续里程碑。

### Q17：如果问你为什么不用 LangChain / LangGraph？

可以这样回答：

LangChain 和 LangGraph 能加快 Agent 构建，但我第一版更想掌握底层状态机、工具 schema、落库和错误处理。所以先手写轻量状态机，后续如果流程变复杂，可以评估 LangGraph。

这样讲更有主动思考：

> 我不是排斥框架，而是不想一开始被框架屏蔽掉核心工程问题。

### Q18：如果问你怎么处理模型输出 JSON 不合法？

计划是：

- 用 Pydantic 定义输出 schema。
- 第一次解析失败后，把错误信息反馈给模型做 self-correction。
- 限制修复次数。
- 统计解析失败率和自愈成功率。
- 多次失败后记录 `error_logs` 并中止或降级。

### Q19：如果问你如何控制成本？

成本来自：

- LLM token。
- embedding。
- 爬虫代理或浏览器资源。
- 数据库存储。

控制方式：

- 评论先切片和检索，不全量塞给模型。
- 短期记忆滑动窗口。
- 老上下文 summary。
- 失败后从断点恢复，减少重跑。
- 记录 token 和 cost。

### Q20：如果问你如何部署？

计划是 Docker Compose：

- FastAPI。
- Celery worker。
- Redis。
- PostgreSQL + pgvector。
- Next.js。

第一版本地开发先用 uv + npm，等 Day 23 做容器化一键启动。

## 面试官可能深挖的技术点

### 异步任务一致性

可能追问：

- 如果 API 创建状态成功，但 Celery 投递失败怎么办？
- 如果 Celery 投递成功，但状态更新失败怎么办？

当前 Day 6 处理：

- 先创建 received 状态。
- 投递成功后更新 queued。
- 投递成功后写 received 和 queued 事件。
- 投递失败返回 `QUEUE_UNAVAILABLE`，状态更新为 failed，并写入 error 事件。
- Worker 执行时继续写 running 和 completed 事件。

后续增强：

- PostgreSQL 事务内创建任务。
- outbox pattern 记录待投递事件。
- worker 消费后幂等更新状态。
- 定时扫描 received 但未 queued 的任务。

### 幂等性

可能追问：

- 用户重复提交怎么办？
- Worker 重复执行怎么办？

后续方案：

- 给请求加 client_request_id。
- 同一用户同一 target 可选择去重。
- Worker 更新状态时检查当前状态。
- 工具输出写入 artifacts，重复执行可复用。

### 状态机

当前任务状态：

- received
- queued
- running
- waiting_retry
- completed
- failed
- cancelled

Agent step 状态：

- pending
- running
- success
- failed
- skipped

面试表达：

> 任务状态描述宏观生命周期，Agent step 描述每一个工具调用或推理步骤，两者粒度不同。

### 错误分类

错误不应该只有 500。项目里会逐步区分：

- `VALIDATION_FAILED`
- `QUEUE_UNAVAILABLE`
- `TASK_NOT_FOUND`
- `TASK_NOT_RETRYABLE`
- `CRAWLER_BLOCKED`
- `MODEL_TIMEOUT`
- `SCHEMA_PARSE_FAILED`
- `EMBEDDING_FAILED`

分类越清楚，越容易重试、告警和复盘。

### 可观测性

当前已有：

- trace ID middleware。
- 统一 response envelope。
- 错误 envelope。

后续会补：

- Loguru。
- structured logging。
- task events。
- agent steps。
- LLMOps metrics。

## 项目亮点怎么写进简历

可以写：

> MarketMind Agent：电商评论洞察与证据链报告系统。基于 FastAPI、Celery、Redis、PostgreSQL、pgvector 和 Next.js 构建长任务 Agent 工作台，实现任务异步调度、状态追踪、评论语义检索和证据链报告生成。负责后端架构设计、数据模型设计、任务队列接入、Agent 状态机和 RAG 检索链路。

更工程化版本：

> 设计并实现 FastAPI + Celery + Redis 的长任务异步管线，API 接收任务后返回 task_id，Worker 后台执行采集和分析任务；通过 PostgreSQL 持久化任务、Agent step、评论和报告数据，使用 pgvector 对评论切片做语义检索，生成带 evidence refs 的运营洞察报告；引入 Pydantic schema、trace ID、统一错误码和 pytest/ruff 验证，提高系统可追踪性和可维护性。

## 面试时不要夸大的地方

不要说：

- 已经能稳定爬所有电商网站。
- 已经替代成熟卖家工具。
- 已经完成完整商用系统。
- Agent 已经完全自治。
- RAG 已经大规模验证。

应该说：

- 第一版聚焦评论洞察和证据链报告。
- 采集采用 best-effort，CSV/JSON 是兜底路径。
- 当前按 30 天计划推进，已完成基础设施和异步管线。
- 后续会继续补采集、RAG、Agent 和部署。

诚实比夸大更能赢得信任。

## 自我介绍时如何引出项目

可以这样说：

> 我最近在做一个偏工程化的 Agent 项目，叫 MarketMind Agent。它不是简单调用大模型生成文本，而是围绕电商评论分析这个场景，把任务队列、状态追踪、RAG 检索和证据链报告串起来。我希望通过这个项目系统性训练后端工程、异步任务、数据库设计和 AI 应用落地能力。

如果对方是后端岗位：

> 我可以重点讲它的 FastAPI、Celery、Redis、PostgreSQL、状态机和错误处理。

如果对方是 AI 应用岗位：

> 我可以重点讲它的 Agent 工具调用、Pydantic guardrails、评论 RAG 和证据链报告。

如果对方是全栈岗位：

> 我可以重点讲 Next.js 控制台如何展示任务进度、Agent step 和报告证据。

## 目前最适合展示的代码点

截至 Day 7，最适合展示：

- `backend/app/api/routes/tasks.py`：API 如何接收任务、投递队列、统一错误。
- `backend/app/tasks/service.py`：任务状态创建和入队流程。
- `backend/app/tasks/dispatcher.py`：Celery 分发器抽象。
- `backend/app/tasks/status_store.py`：Redis 状态存储和内存测试实现。
- `backend/app/tasks/event_store.py`：Redis 事件流存储和内存测试实现。
- `backend/app/storage/task_stores.py`：SQLAlchemy 持久化 store 和 Redis/PostgreSQL mirrored store。
- `backend/app/worker/tasks.py`：最小 worker 状态推进。
- `backend/app/storage/models.py`：数据库模型设计。
- `migrations/versions/0002_task_queue_id.py`：任务队列 ID 持久化迁移。
- `tests/test_task_persistence.py`：任务和事件持久化测试。
- `tests/test_tasks_api.py`：API 成功、失败、队列不可用测试。
- `tests/test_celery_worker.py`：Celery 配置、worker 状态推进和事件写入测试。

## 如果被问“你在项目中学到了什么”

可以回答：

我最大的收获是：AI 项目的难点不只是 prompt，而是如何把不稳定的模型调用放进一个可追踪、可恢复、可测试的工程系统里。

具体包括：

- 长任务不能阻塞 HTTP。
- Agent 不能黑盒运行。
- 报告不能没有证据。
- 状态必须可回放。
- 外部依赖必须有错误分类。
- 测试不能强依赖本地基础设施。

## 后续迭代计划怎么讲

短期：

- Day 7：基础设施联调和任务事件持久化。
- Day 8：Playwright 最小采集与失败兜底。
- Day 9：爬虫结果入库和证据保存。

中期：

- Agent 工具 schema。
- ReAct 状态机。
- Pydantic guardrails。
- 评论切片和 embedding。
- `search_reviews_tool`。

后期：

- 报告生成。
- 证据链引用。
- 前端真实 API 接入。
- Docker Compose。
- LLMOps 指标和 50 次任务复盘。

## 面试结尾总结

如果面试官让你用一句话总结项目，可以说：

> 这个项目的核心价值是把“LLM 生成报告”升级成一个可追踪、可恢复、带证据链的异步 Agent 系统。

如果让你说最难点：

> 最难的不是单个模型调用，而是长任务状态、工具调用、证据检索和失败恢复之间的一致性设计。

如果让你说下一步：

> 下一步我会把 Redis 快照推进到 PostgreSQL 事件流，并接入采集和 Agent step，这样任务就不仅能返回 queued，还能看到完整执行时间线。
