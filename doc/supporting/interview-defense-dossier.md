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

Day 8 做 Playwright 最小采集与失败兜底，是因为任务基础设施稳定后，系统需要第一次接入真实外部证据。当天没有追求复杂电商站适配，而是先实现 fixture / public URL 的通用采集、字段抽取、错误分类和 HTML artifact 保存。这个选择的核心是把采集层做成“可解释组件”：成功有标题、价格、评分和证据文件；失败有错误码、原因和失败 HTML，而不是让 worker 静默失败或让任务一直停在 running。

面试时可以这样讲：

> Day 8 我没有把目标定成“稳定爬某个大站”，因为那会把项目拖进站点适配和反爬细节。我的目标是先建立可复用的采集边界：输入是任务和 URL，输出是结构化字段、可追溯 artifact 和明确错误码。这样后续无论接具体站点 adapter、CSV 兜底，还是接 Agent 工具调用，底层契约都是稳定的。

Day 9 做采集结果入库，是因为 Day 8 只把证据放进了任务事件和本地文件，后续 RAG、报告和证据链不能长期依赖事件 payload。当天选择复用 Day 3 的 `products`、`crawled_pages`、`reviews`、`artifacts` 表，而不是重新建表，是为了保持数据模型一致。幂等策略先放在 storage service 层，保证重复采集不会无限新增重复数据。

面试时可以这样讲：

> Day 9 我把采集结果从“过程事件”推进成“数据库资产”。这个阶段的重点不是多爬几个字段，而是让商品、页面、评论和 artifact 都能通过 `task_id` 回溯，并且重复运行不会造成不可控重复数据。这样后续 RAG 和报告才能引用稳定的数据库记录，而不是引用临时变量。

Day 10 做工具 schema 和工具注册机制，是因为 ReAct loop 不是凭空推理，它的核心动作是选择工具、校验参数、执行工具、观察结果。如果没有稳定的工具契约，Agent 代码很容易把模型输出、参数校验、业务函数和错误处理混在一起。当天我选择先实现轻量 `ToolRegistry` 和 `ToolExecutor`，而不是马上引入 LangChain / LangGraph，是为了先掌握输入输出 schema、幂等标记、重试标记和错误 envelope 这些底层边界。

面试时可以这样讲：

> Day 10 我没有急着写 Agent loop，而是先把工具层打稳。因为 Agent 最容易失控的地方不是循环本身，而是模型生成的工具参数不可靠、工具失败不可分类、结果格式不统一。我通过 Pydantic schema、ToolRegistry 和 ToolExecutor 先把工具调用变成一个可验证的后端契约。

Day 11 做 ReAct 状态机和 `agent_steps` 落库，是因为 Day 10 已经把工具契约固定住了，但 Agent 还没有真正进入“可回放的执行链路”。如果只停留在工具注册和执行器层，Agent 仍然只是静态能力清单；只有把 Thought、Action、Observation 记录到数据库里，Agent 才具备调试、恢复和面试展示的价值。今天我选择先做最小单步 ReAct，而不是直接做多轮规划，是为了先验证状态机与数据库落库边界，再逐步接大模型规划器、guardrails 和记忆。

面试时可以这样讲：

> Day 11 我把 Agent 从“工具层”推进到“执行层”。我没有一上来做完整的多轮规划，而是先把 Thought / Action / Observation 三层记录打通，因为这一步决定了这个 Agent 是不是能回放、能恢复、能解释。

Day 12 做结构化输出 guardrails 和 self-heal，是因为 Day 11 只是把执行链路打通，但模型输出仍然可能是坏 JSON、半成品字段或者 schema 不匹配。真正工程化的 Agent 不能让原始模型输出直接进入业务逻辑，必须先过 JSON parse、Pydantic 校验和有限次自愈。当天我把工具选择输出和报告结构输出都抽成了统一守门层，并把 `validation_error_count` 和 `self_heal_count` 纳入 `agent_runs`，这样后续可以直接统计模型失败率和修复率。

面试时可以这样讲：

> Day 12 我没有继续加新功能，而是先把模型输出的边界钉住。因为再聪明的 Agent，只要输出格式不稳定，后面的工具调用和报告生成都会被脏数据拖垮。

Day 13 做短期记忆和上下文压缩，是因为 Agent 后续进入多轮执行、评论检索和报告生成后，不能把所有历史 Thought、Action、Observation 和工具输出无限塞进模型上下文。当天我实现了 `AgentShortTermMemory`，默认保留最近 3 条详细 entry，更早内容进入 summary，并单独保留 `summary_evidence_refs`。Redis 用于短期缓存，PostgreSQL `agent_steps` 仍然是恢复事实来源。

面试时可以这样讲：

> Day 13 我做的是 Agent 的工作记忆，不是长期 RAG。它解决的是“当前任务上下文怎么少而准地交给模型”，所以我用滑动窗口控制最近上下文，用 summary 压缩旧步骤，并且单独保留证据 ID，避免报告后续找不到来源。

Day 14 做评论切片、fake embedding 和 `review_chunks` 入库，是因为短期记忆只解决当前任务上下文，不解决大量评论证据召回。今天我把 Day 9 入库的 reviews 转成 review chunks，并通过 `EmbeddingProvider` 抽象生成向量，写入固定 1536 维的 pgvector 字段。第一版检索用 Python cosine similarity 做原型，后续可以替换为 PostgreSQL pgvector 原生排序。

面试时可以这样讲：

> Day 14 我开始做长期记忆。这里我没有直接接真实 embedding API，而是先用 fake provider 把清洗、切片、维度约束、幂等写入和检索返回格式跑通。因为真实 API 是可替换外部依赖，先把数据链路稳定下来更重要。

Day 15 做 `search_reviews_tool`，是因为 Day 14 的 RAG 检索还只是后端能力，Agent 无法直接通过标准工具调用它。今天我把检索封装成 Pydantic schema 约束的工具：输入包含 query、top_k、min_similarity 和 filters，输出包含 evidence chunks、evidence refs 和 no_results_reason。召回为空时工具明确返回证据不足，不允许模型自己补结论。

面试时可以这样讲：

> Day 15 我把 RAG 检索接进 Agent 工具层。重点不是让模型直接读数据库，而是让模型提出检索意图，后端工具负责过滤、召回和证据引用。这样报告后续只能基于 evidence refs 生成，能减少幻觉。

Day 16 做报告 schema 和确定性报告生成骨架，是因为 Day 15 已经能召回评论证据，但还没有把证据变成可展示、可入库、可校验的报告。今天我没有直接接真实 LLM 报告生成，而是先定义 `StructuredReport`、`ReportFinding`、`EvidenceSnippet` 和 `ReportGenerationInput`，并实现一个确定性 `StructuredReportGenerator`。核心约束是：章节引用的 evidence refs 必须存在于报告顶层 `evidence_refs`；没有 evidence snippets 时只能输出 `insufficient_evidence`，不能编造结论。

面试时可以这样讲：

> Day 16 我先做报告结构，而不是先做文案生成。因为这个项目的价值不是让模型写一篇看起来像报告的文章，而是让每个结论都能追溯到具体评论 chunk。确定性生成器是一个可测试的 baseline，后续接 LLM 时仍然必须输出同一个 schema，并通过 Pydantic 证据引用校验。

Day 17 做证据链回查，是因为 Day 16 只能保证报告引用了合法 `evidence_refs`，但还不能让用户看到这些 ref 背后的原始评论、采集 artifact 或 Agent step。今天我新增 `EvidenceChain`、`EvidenceSource` 和 `SQLAlchemyEvidenceChainStore`，把 `chunk:{id}`、`review:{id}`、`artifact:{id}`、`step:{id}` 解析成可展示来源，并提供 `GET /api/reports/{report_id}/evidence` 给前端后续消费。

面试时可以这样讲：

> Day 17 我把“证据 ID”升级成“证据链”。报告里不只是出现 `chunk:xxx`，而是能通过 API 回查到原始 review chunk、父级 review、artifact 或 Agent step。这样报告可信度不是靠口头解释，而是有结构化数据和测试支撑。

Day 18 做评论机会点评分和风险分析，是因为 Day 17 已经解决“结论能追溯到哪里”，但报告还缺少“哪个问题更严重、哪个痛点更值得处理”的排序能力。今天我新增 `AnalysisScorecard`、`DimensionScore` 和 `CompetitiveRiskScorer`，用确定性规则基于关键词、评分、相似度和样本数生成风险分与机会分，并且样本不足会降权。

面试时可以这样讲：

> Day 18 我没有让模型直接打分，而是先做可解释的规则评分 baseline。每个维度分数都绑定 evidence refs，并说明样本数、平均评分、相似度和降权原因。这样评分不是黑盒，也不会被误解成销量预测。

Day 19 做 Next.js 前端真实 API 接入，是因为后端能力已经积累到可以通过控制台演示的阶段。如果前端仍然只展示 mock 数据，项目虽然有后端工程深度，但面试演示时还需要依赖命令行和测试用例，不利于说明“这是一个可操作系统”。今天我把 `POST /api/tasks`、`GET /api/tasks/{task_id}` 和 `GET /api/tasks/{task_id}/events` 接到真实 FastAPI，同时把尚未实现的任务列表、Agent steps、报告列表和报告详情保留 fallback。

面试时可以这样讲：

> Day 19 我没有把所有页面都强行改成真实 API，而是按后端成熟度分层接入。任务创建、任务状态和事件流已经稳定，所以前端真实调用；列表、steps 和报告详情接口还没完成，所以保留 mock fallback。这样做的好处是演示链路可以先跑起来，同时不会在前端伪造后端尚未具备的能力。

Day 20 做任务进度轮询和 Agent step 展示，是因为 Day 19 只能提交任务和查看一次性详情，用户仍然不知道任务是不是还在运行、卡在哪一步、失败原因是什么。今天我补了 `GET /api/tasks/{task_id}/steps`，把 Day 11 已经落库的 `agent_steps` 变成前端可展示的脱敏摘要，并用 `TaskProgressPanel` 每 5 秒刷新任务状态、事件和 steps。

面试时可以这样讲：

> Day 20 我没有直接上 WebSocket，而是先用轮询打通任务级观测闭环。因为状态、事件和 steps 都已经有查询接口，轮询能先验证页面、API 和数据结构是否稳定。等后续需要更实时的体验时，可以把 `TaskProgressPanel` 里的刷新逻辑替换成 SSE 或 WebSocket。

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

这个项目目前推进到 Day 20，不应该说已经完成完整 Agent 系统。面试时我会明确区分：

- 已完成：后端骨架、数据库模型、任务创建、异步队列、状态快照、任务事件流、PostgreSQL 任务/事件持久化、Playwright 最小采集、HTML 证据 artifact、采集结果入库、工具 schema、工具注册机制、最小 ReAct 状态机、Agent step 落库、Agent step 查询 API、结构化输出 guardrails、短期记忆滑动窗口、上下文摘要压缩、评论清洗、评论切片、fake embedding、review chunk 入库、`search_reviews_tool`、结构化报告生成骨架、报告入库、证据链回查 API、评论风险机会评分、前端真实任务提交、任务状态/事件/steps 轮询读取、错误 envelope、测试。
- 正在做：历史任务和历史报告真实接口。
- 后续做：真实 embedding provider、pgvector 原生检索、真实 LLM report prompt、部署。

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

截至 Day 21，项目已经完成：

- 文档体系、30 天 roadmap、开发日志。
- Next.js 控制台骨架。
- Next.js 真实任务提交表单。
- Next.js 任务详情轮询面板。
- 前端 API client、统一 envelope 解析和错误码展示。
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
- Playwright 最小采集链路。
- 本地 HTML fixture 稳定采集测试入口。
- 通用 HTML 标题、价格、评分和可见文本抽取。
- 采集成功 / 失败事件写入任务事件流。
- 成功 HTML 和失败 HTML artifact 本地保存。
- `ACCESS_BLOCKED`、`DOM_NOT_FOUND`、`PAGE_TIMEOUT` 等采集错误分类。
- 采集成功结果写入 `products`、`crawled_pages`、`reviews` 和 `artifacts`。
- Worker 采集完成事件携带持久化后的 product/page/artifact/review ID。
- 采集结果幂等写入策略，避免同一任务重复运行造成不可控重复数据。
- Agent 工具 schema、工具注册机制和统一工具执行 envelope。
- 第一版 `crawl_product_tool`，可通过 ToolExecutor 调用采集能力。
- `SQLAlchemyAgentRunStore`，用于持久化 `agent_runs` 和 `agent_steps`。
- 最小 `AgentStateMachine`，可以记录 Thought、Action、Observation。
- `StructuredOutputGuardrail`，用于校验和修复 JSON / Pydantic 输出。
- `AgentToolDecision` 和 `ReportStructure` 两个结构化输出 schema。
- `build_json_repair_prompt` 和有限次 self-heal retry。
- `validation_error_count` 与 `self_heal_count` 的 LLMOps 指标入口。
- `AgentShortTermMemory`，用于当前任务短期上下文管理。
- 短期记忆滑动窗口，默认最近 3 条保留详细内容。
- 历史上下文确定性摘要压缩，避免 prompt context 无限增长。
- `summary_evidence_refs` 和 `recent_entries[].evidence_refs`，保证摘要后仍能追溯证据。
- `RedisAgentMemoryStore` 和 `InMemoryAgentMemoryStore`，区分真实缓存和测试实现。
- 从 `AgentStepData` 恢复短期记忆，Redis 丢失时仍能从 PostgreSQL step 重建上下文。
- `clean_review_text` 和 `split_review_text`，用于评论清洗和切片。
- `EmbeddingProvider` 抽象，隔离真实 embedding 服务。
- `DeterministicEmbeddingProvider`，用于本地测试和流程验证。
- `SQLAlchemyReviewChunkStore`，把 reviews 写入 `review_chunks`。
- `ReviewChunkIndexResult`，记录 review_count、chunk_count、embedding_model、embedding_dimensions。
- `search_similar_reviews`，返回 chunk、review 来源、评分和 similarity。
- `search_reviews_tool`，让 Agent 通过标准工具检索评论证据。
- `SearchReviewsToolInput` 和 `SearchReviewsToolOutput`，约束检索输入输出。
- `ReviewEvidenceChunk`，统一证据片段格式。
- `no_results_reason`，让召回为空时明确标注证据不足。
- `StructuredReport` 和 `ReportFinding`，用于约束报告标题、摘要、章节和 evidence refs。
- `EvidenceSnippet` 和 `ReportGenerationInput`，用于把工具召回结果转成报告输入。
- `StructuredReportGenerator`，第一版确定性生成报告骨架。
- 无证据时生成 `insufficient_evidence` 报告，不编造结论。
- `StructuredReport.to_markdown()`，输出前端可展示的 Markdown 草案。
- `SQLAlchemyReportStore`，把报告 JSON、Markdown、evidence refs 和 schema version 写入 `reports` 表。
- `EvidenceRef`、`EvidenceSource` 和 `EvidenceChain`，用于结构化表达证据链。
- `parse_evidence_ref()`，解析 `chunk`、`review`、`artifact`、`step` 四类引用。
- `SQLAlchemyEvidenceChainStore`，根据 `task_id` 回查 review chunk、review、artifact 和 agent step。
- `attach_evidence_chain()`，把 evidence chain 绑定到报告 metadata。
- 报告 Markdown 的“证据链回查”章节。
- `GET /api/reports/{report_id}/evidence`，返回报告 evidence chain。
- `ScorecardInput`、`DimensionScore` 和 `AnalysisScorecard`，用于结构化评分输出。
- `CompetitiveRiskScorer`，基于关键词、评分、相似度和样本数生成风险/机会分。
- 样本不足降权和 `LOW_SAMPLE_SIZE`。
- `attach_scorecard_to_report()`，把 scorecard 绑定到报告 metadata。
- 报告 Markdown 的“维度评分”章节。
- 前端调用真实 `POST /api/tasks` 创建任务，并在成功后跳转 `/tasks/{task_id}`。
- 前端调用真实 `GET /api/tasks/{task_id}` 和 `GET /api/tasks/{task_id}/events` 展示任务状态和事件。
- 前端调用真实 `GET /api/tasks/{task_id}/steps` 展示 Agent step 摘要。
- `TaskProgressPanel` 每 5 秒刷新运行中任务，终态自动停止。
- 前端调用真实 `GET /api/tasks` 展示历史任务列表。
- 前端调用真实 `GET /api/reports` 展示历史报告列表。
- 前端调用真实 `GET /api/reports/{report_id}` 打开报告详情。
- 历史任务 API 支持状态筛选、时间筛选、limit、offset 和 total。
- 历史报告 API 支持报告状态、任务状态、时间筛选、limit、offset 和 total。
- 真实 API 模式下任务列表、报告列表和报告详情成功响应不再回退 mock。
- 工具调用前后状态落库，Action step 能从 pending/running 更新为 success/failed。
- Agent 工具失败时，错误码和失败 observation 会写入数据库，不覆盖旧 step。
- 队列不可用、状态缓存不可用、参数校验失败的统一错误响应。
- pytest + ruff + Next.js build 验证。

还没有完成：

- 具体电商站点 adapter。
- 失败截图 artifact。
- 多轮 LLM planner。
- 任务重试接口。
- 真实 embedding API 接入。
- pgvector 原生相似度 SQL。
- 真实 LLM report prompt。
- 报告详情页前端证据链展示。
- 历史列表筛选控件。
- Docker Compose 全链路一键启动。

面试时可以诚实讲：这个项目正在按 30 天里程碑推进，目前已经完成底层任务入口、异步管线、任务事件流、PostgreSQL 持久化、Playwright 最小采集、采集结果入库、Agent 工具契约、最小 ReAct 状态机、结构化输出 guardrails、短期记忆压缩、评论 RAG 索引基础、`search_reviews_tool`、结构化报告生成骨架、报告证据链回查、可解释评分 baseline、Next.js 真实任务提交、任务详情轮询、历史任务列表、历史报告列表和报告详情真实接入。下一阶段会补日志观测、真实 report prompt、部署和 E2E。重点是展示工程化思路和持续推进能力，而不是假装已经做完所有功能。

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

### 问题 12：Day 11 为什么先做最小 ReAct 状态机，而不是完整多轮规划

现象：

Day 10 已经有工具契约和执行器，下一步很容易直接上完整 LLM planner。但如果这样做，状态机、工具调用、落库和异常处理会一起变复杂。

思考：

完整 planner 不是最先要验证的点。真正先要确认的是：Agent 每一步是不是都能被持久化，失败时旧 step 会不会被覆盖，观察结果能不能回放。只要这层不稳，后面再聪明的 planner 也只是黑盒。

解决：

- 先实现单步最小 ReAct。
- 把 Thought、Action、Observation 拆成独立 step。
- 用 `SQLAlchemyAgentRunStore` 管 run 和 step。
- 工具调用结果直接写入 `tool_output` 和 `observation`。
- 用 `max_tool_calls` 先封住无界循环风险。

面试表达：

> Day 11 我没有急着做完整多轮 Agent，而是先把状态机做成可回放、可恢复的最小版本。因为在工程上，先证明“能记录清楚每一步”比先证明“模型能想很多步”更重要。

### 问题 13：Day 13 为什么先做短期记忆，而不是直接做 embedding

现象：

Day 13 原计划属于“记忆系统”阶段，很容易直接跳到 pgvector、embedding 和语义检索。但如果 Agent 的当前任务上下文没有控制住，后续多轮 planner 会不断把旧 Thought、Action、Observation 和工具输出塞回模型。

思考：

短期记忆和长期 RAG 解决的问题不同。短期记忆解决“当前任务最近发生了什么，怎么少量带给模型”；长期 RAG 解决“海量评论里哪些证据和问题相关”。如果先做 embedding，Agent 仍然可能因为上下文膨胀、重复带旧工具结果而浪费 token。

解决：

- 新增 `AgentShortTermMemory`，先固定上下文窗口。
- 最近 3 条 entry 保留详细内容，更早内容进入 summary。
- 证据 ID 不只写在摘要文本里，而是单独保留在 `summary_evidence_refs`。
- Redis 做短期缓存，PostgreSQL `agent_steps` 做可恢复事实来源。
- 先用确定性摘要，暂时不引入 LLM summary prompt。

面试表达：

> Day 13 我先做短期记忆，是为了控制 Agent 当前任务的 token 增长。embedding 是长期记忆，解决评论召回；短期记忆是工作记忆，解决 Agent 多轮执行时“带多少上下文”的问题。这两个边界拆清楚，后面的 RAG 才不会和状态机混在一起。

### 问题 14：Day 14 为什么先用 fake embedding，而不是直接接真实模型

现象：

Day 14 的路线图包含 embedding 生成流程，但最终实现没有直接调用线上 embedding API，而是先定义 `EmbeddingProvider` 并实现 `DeterministicEmbeddingProvider`。

思考：

真实 embedding API 涉及网络、密钥、限流、成本和失败重试。如果在评论清洗、切片、维度约束、幂等入库和检索结果格式还没稳定时就接真实服务，调试时很难判断问题来自数据链路还是外部模型服务。

解决：

- 先定义 provider 抽象，把外部模型调用隔离在接口后面。
- 用 fake provider 输出 1536 维向量，遵守 `review_chunks.embedding` 的真实维度约束。
- 先把 `reviews -> review_chunks -> top_k results` 跑通。
- 检索结果先包含 `source_url`、`rating`、`review_external_id` 和 `similarity`，为 Day 15 tool 契约做准备。

面试表达：

> Day 14 我没有为了“看起来接了模型”而直接调用 embedding API。我的判断是：先把数据链路做成可测试、可替换，再接真实 provider。这样真实 API 出问题时，边界会很清楚，不会和切片或入库问题混在一起。

### 问题 15：Day 15 为什么把 RAG 检索封装成工具，而不是让模型直接读数据库

现象：

Day 14 已经有 `search_similar_reviews`，理论上可以让 planner 直接调用 store 或把检索结果塞进 prompt。但 Day 15 仍然专门做了 `search_reviews_tool`。

思考：

Agent 不能直接操作数据库或绕过 schema。否则模型输出、数据库查询、过滤规则和证据引用会混在一起，后续很难测试和回放。工具层应该负责把不稳定的模型意图转成确定性的后端行为。

解决：

- 用 `SearchReviewsToolInput` 限制 query、top_k、min_similarity 和 filters。
- 用 `SearchReviewsToolOutput` 统一返回 evidence chunks。
- evidence ref 使用 `chunk:{chunk_id}`。
- 召回为空时返回 `NO_REVIEW_CHUNKS_ABOVE_THRESHOLD`。
- 工具通过依赖注入注册，避免默认 registry 强依赖数据库。

面试表达：

> 我不会让模型直接拼 SQL 或直接读数据库。模型只表达“我要找什么证据”，后端工具负责检索、过滤、证据 ID 和空结果降级。这样 Agent 的每一步都能被状态机记录，也能被测试验证。

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
- 任务状态和任务事件 PostgreSQL 持久化。
- Playwright / HTML fixture 采集成功、失败和 artifact 保存。
- 采集结果写入 product、page、review、artifact。
- Agent 工具注册、参数校验和统一执行 envelope。
- Agent 状态机的 step 顺序、成功链路、失败链路和最大工具调用限制。

后续会加：

- 真实 Redis + Celery worker 联调测试。
- RAG 检索召回测试。
- Playwright E2E。

### Q15：如果面试官说这个项目太复杂，你怎么回答？

可以承认复杂，但解释分阶段策略：

- Day 1 到 Day 6 先做基础设施和任务可观测性。
- Day 7 到 Day 12 做联调、采集、状态机和工具。
- Day 13 到 Day 18 做 RAG 和报告。
- Day 19 做前端真实任务提交、状态查询和事件读取。
- Day 20 做前端任务进度轮询和 Agent step 展示。
- Day 21 做历史任务、历史报告和报告详情真实接入。
- Day 22 之后做日志、部署、E2E 和 LLMOps 统计。

复杂度不是一次性堆上去，而是按依赖逐步增加。

### Q16：如果面试官问你最有技术含量的部分是什么？

可以选三个：

1. 长任务异步解耦：FastAPI + Celery + Redis。
2. Agent 状态可追踪：Agent step 落库和断点续跑。
3. 评论 RAG 证据链：pgvector 检索 + 报告 evidence refs。

截至 Day 21，这三个方向都已经有可展示的工程骨架：异步任务链路已经跑通，Agent step 已落库并能在前端展示摘要，评论 RAG 和报告 evidence refs 已经能生成并回查。后续重点是扩大真实数据源、真实模型接入和观测指标。

### Q17：如果问你为什么不用 LangChain / LangGraph？

可以这样回答：

LangChain 和 LangGraph 能加快 Agent 构建，但我第一版更想掌握底层状态机、工具 schema、落库和错误处理。所以先手写轻量状态机，后续如果流程变复杂，可以评估 LangGraph。

这样讲更有主动思考：

> 我不是排斥框架，而是不想一开始被框架屏蔽掉核心工程问题。

### Q18：如果问你怎么处理模型输出 JSON 不合法？

当前实现是：

- 用 Pydantic 定义输出 schema，例如 `AgentToolDecision` 和 `ReportStructure`。
- 第一次 JSON parse 或 schema 校验失败后，通过 `build_json_repair_prompt` 组织修复提示词。
- 使用有限次 self-heal 和 Tenacity repair retry，避免无限修复。
- 统计 `validation_error_count` 和 `self_heal_count`。
- 多次失败后抛出 `StructuredOutputGuardrailError`，保留原始输出和 attempts，后续可以写入 `error_logs`。

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

### Q21：短期记忆、长期记忆和 RAG 的区别是什么？

短期记忆是当前任务的工作上下文，保存最近几轮 Thought、Action、Observation 和压缩后的历史摘要。它主要服务于 Agent planner，目的是控制 token 增长。

长期记忆是可跨任务复用的数据资产，例如评论切片、报告结论、证据 metadata 和 embedding。它主要服务于语义检索和证据召回。

RAG 是使用长期记忆的一种检索增强流程：先根据问题召回相关评论 chunk，再把这些 evidence refs 交给模型生成报告。

这个项目里 Day 13 做的是短期记忆，Day 14 - Day 15 才会进入评论切片、embedding 和 `search_reviews_tool`。

### Q22：Day 14 的 fake embedding 会不会让项目显得不真实？

不会，但必须讲清楚边界。fake embedding 不是为了假装已经有真实语义能力，而是为了在没有外部服务依赖的情况下验证工程链路：

- 评论能否被清洗和切片。
- 维度是否严格保持 1536。
- 重复索引是否幂等。
- 检索结果是否带来源、评分和相似度。
- 后续真实 provider 能否无缝替换。

面试时要诚实说：当前 fake provider 只保证流程和接口，真实召回质量要等接入 `text-embedding-3-small` 或兼容 embedding 服务后评估。

### Q23：`search_reviews_tool` 如何避免模型幻觉？

它本身不让模型直接下结论，而是返回结构化证据：

- 每条结果有 `chunk_id`、`review_id`、`source_url`、`rating`。
- 每条结果有 `evidence_ref`。
- 工具输出有 `evidence_refs` 汇总。
- 召回为空时有 `no_results_reason`。

后续报告生成时，prompt 和 schema 必须要求结论绑定 `evidence_refs`。如果 `evidence_refs` 为空，就只能写证据不足，不能把 query 或模型常识写成事实。

### Q24：Day 16 为什么先用确定性报告生成器，而不是直接让 LLM 写报告？

因为 Day 16 要解决的是报告可信度和工程边界，不是文案质量。

如果直接让 LLM 写报告，短期看起来更像成品，但会引入几个风险：

- 模型可能引用不存在的证据。
- 前端不知道稳定字段在哪里。
- 报告入库后难以区分结构字段和自然语言。
- 召回为空时模型可能凭常识补结论。
- 测试会受模型随机性影响，不适合做第一版回归基线。

所以我先实现 `StructuredReportGenerator`：

- 输入是 `ReportGenerationInput`。
- 证据是 `EvidenceSnippet`。
- 输出是 `StructuredReport`。
- 章节是 `ReportFinding`。
- 入库前由 Pydantic 校验证据引用。

面试时可以这样回答：

> 我不是不接 LLM，而是先把 LLM 将来必须遵守的报告契约定下来。确定性生成器保证这个契约可测试、可入库、可展示。后续接真实 report prompt 时，模型只负责提升表达质量，不能绕过 evidence refs 和 schema 校验。

### Q25：报告如何防止引用不存在的证据？

Day 16 在 `StructuredReport` 里做了 schema 级校验：每个章节的 `evidence_refs` 必须是报告顶层 `evidence_refs` 的子集。

如果某个章节引用了 `chunk:missing`，但顶层只有 `chunk:known`，Pydantic 会直接抛 `ValidationError`，报告对象无法创建，也就不会进入 `reports` 表。

这比只在 prompt 里写“请引用证据”更可靠，因为 prompt 是软约束，schema 校验是硬边界。

### Q26：Day 17 为什么没有新建 `report_evidence_links` 表？

因为 Day 17 的目标是先打通 evidence ref 协议和回查能力，而不是过早固定更多表结构。

当前已有：

- `reports.evidence_refs`
- `review_chunks`
- `reviews`
- `artifacts`
- `agent_steps`

这些表已经足够解析 `chunk:{id}`、`review:{id}`、`artifact:{id}`、`step:{id}`。如果现在立刻加关联表，会增加迁移和同步成本，但还没有历史报告版本、报告列表筛选、证据快照冻结这些明确需求。

面试时可以这样讲：

> 我没有为了“看起来复杂”而加表。Day 17 先用应用层 evidence ref 协议把回查跑通，并通过 API 和测试验证。如果后续 Day 21 做历史报告版本，需要冻结每次报告的证据快照，那时再引入 `report_evidence_links` 或 evidence snapshot 表更合理。

### Q27：证据缺失怎么办？

证据缺失不能静默忽略，也不能伪造 content。

Day 17 的处理是：

- 返回 `available=false`。
- 写入 `missing_reason`。
- 在 `EvidenceChain.missing_refs` 里汇总缺失 ID。
- Markdown 的“证据链回查”章节也会显示缺失原因。

这样前端可以提示“报告证据链不完整”，Agent 后续也可以决定重新检索或重新采集。

### Q28：Day 18 的评分是不是在预测商业成功？

不是。Day 18 的评分是解释型排序，不是销量预测，也不是爆款概率。

评分输入只来自：

- evidence snippet 内容。
- 评论 rating。
- 检索 similarity。
- 样本数。
- `minimum_samples` 降权。

它的作用是帮助用户判断“哪个维度更值得关注”，比如质量问题比物流问题更高风险，而不是判断“这个商品一定会不会卖爆”。

面试时可以这样讲：

> 我没有把评分包装成商业预测，因为那需要销量、价格、广告、市场规模等更多数据。当前评分只对评论证据本身负责，是一个可解释的风险排序 baseline。

### Q29：为什么不用 LLM 直接给风险分？

因为 LLM 直接打分很容易出现三个问题：

- 不可复现：同样输入多次分数可能不同。
- 难解释：面试官追问 82 分怎么来的，很难拆解。
- 容易脱离证据：模型可能凭常识给分。

Day 18 用确定性规则先建立 baseline：关键词决定维度，rating 和 similarity 影响风险，样本数不足就降权。后续即使用 LLM，也只能辅助解释或分类，不能绕过 evidence refs 和 schema。

### Q30：Day 19 为什么没有一次性删除所有 mock？

因为前端真实接入不等于“所有页面都必须立刻真实化”。Day 19 的后端稳定接口是：

- `POST /api/tasks`
- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/events`
- `GET /api/reports/{report_id}/evidence`

但这些接口还没有完成：

- `GET /api/tasks`
- `GET /api/tasks/{task_id}/steps`
- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `GET /api/evidence`

所以 Day 19 的策略是：核心链路真实接入，未实现接口显式 fallback。这样做比“全删 mock 然后页面大片报错”更适合工程迭代，也比“前端伪造不存在的后端能力”更诚实。

面试时可以这样讲：

> 我把 mock 当成开发兜底，不当成产品能力。任务创建、状态和事件已经有真实后端，所以前端真实调用；列表、steps 和报告详情还没后端接口，所以保留 fallback，并在文档里标记为 Day 20/Day 21 的工作。这个选择体现的是接口成熟度驱动前端接入，而不是为了演示效果硬拼假数据。

### Q31：Day 20 为什么先用轮询，而不是 WebSocket / SSE？

因为 Day 20 要解决的首要问题是“用户能不能看到任务进度和 Agent steps”，不是“实时推送链路是否足够高级”。

当前系统已经有三个查询接口：

- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/events`
- `GET /api/tasks/{task_id}/steps`

轮询可以直接复用这些接口，用较低复杂度先验证任务详情页的信息结构。如果一开始就上 WebSocket / SSE，会新增连接管理、断线重连、反向代理配置、消息顺序和鉴权等问题，反而可能掩盖 API 契约和页面信息架构是否正确。

面试时可以这样讲：

> 我不是不会做 WebSocket，而是认为 Day 20 的正确顺序是先稳定数据契约和页面观测闭环。轮询是一个可替换实现，后续如果任务运行时间更长、状态变化更频繁，可以把 `TaskProgressPanel` 的刷新逻辑换成 SSE 或 WebSocket。

### Q32：为什么不把 Agent thought 完整展示给前端？

因为 thought 属于内部推理过程，不适合直接作为用户可见内容。它可能包含 prompt 片段、临时判断、工具参数、错误尝试或后续敏感信息。

Day 20 的处理方式是：

- thought step 只返回 `input_summary=Thought recorded`。
- action step 返回 tool name 和输入 key 摘要，不返回完整输入。
- observation 做长度截断。
- 失败时优先展示 `error_code`。

这保证了前端能定位执行过程，但不会把内部推理和完整模型上下文暴露出去。

### Q33：Day 21 为什么要做历史任务和历史报告？

因为这个项目的定位不是“一次性生成报告脚本”，而是“面向电商运营场景的评论洞察与证据链工作台”。如果用户只能看当前正在跑的任务，系统价值会停留在 Demo；如果用户能回看历史任务、失败原因、旧报告和证据链，系统才有复盘和持续使用的价值。

Day 21 做完后，项目从单次链路变成了可积累链路：

- 任务可以回看。
- 失败任务不会消失。
- 报告可以从列表重新打开。
- 报告详情可以继续接证据链。
- 后续 LLMOps 可以按历史任务统计耗时、失败率和成本。

面试时可以这样讲：

> 我把历史任务和历史报告放在 Day 21，是因为前面已经完成任务提交、进度观察、报告生成和证据链回查。这个时候最重要的不是继续加模型能力，而是把这些结果沉淀下来，形成可复盘的工作台。否则项目会像一次性脚本，不像工程系统。

### Q34：为什么历史任务查询优先读取 PostgreSQL，而不是 Redis？

Redis 在当前系统里的职责是实时状态缓存和事件流缓存，它有 TTL，也可能因为缓存清理丢失历史状态。历史任务列表需要长期可查、可排序、可筛选，所以应该从 PostgreSQL 读取。

Day 21 的处理方式是：

- `GET /api/tasks/{task_id}` 仍可以优先读 Redis，再回退 PostgreSQL。
- `GET /api/tasks` 作为历史列表，优先读取 PostgreSQL。
- `RedisTaskStatusStore.list()` 明确返回不可用，不让历史页误用 TTL 数据。
- `MirroredTaskStatusStore.list()` 通过 secondary PostgreSQL store 查询历史。

面试时可以这样讲：

> 我把 Redis 和 PostgreSQL 的职责分开：Redis 负责当前任务的快速状态读取，PostgreSQL 负责长期历史和审计。这样任务详情页可以快，历史页也不会因为缓存过期而丢数据。

### Q35：为什么真实 API 模式下不再对任务列表和报告列表做 mock fallback？

Day 19 时保留 fallback 是因为对应后端接口还没有实现。如果后端没有接口，前端为了页面可预览可以先回退 mock。但 Day 21 已经补齐 `GET /api/tasks`、`GET /api/reports` 和 `GET /api/reports/{report_id}`，真实模式下再 fallback 会掩盖后端错误。

这类 fallback 的风险是：

- 后端挂了，页面仍显示假数据，开发者误以为链路正常。
- 接口字段变了，mock 数据无法暴露契约错误。
- 面试展示时容易被追问“这到底是不是假数据”。

Day 21 的处理方式是：

- `NEXT_PUBLIC_USE_MOCKS=true` 时显式使用 mock。
- 真实 API 模式下成功响应直接映射后端数据。
- 真实 API 失败时抛出 `ApiClientError`，不吞掉错误。
- 用 `tests/test_frontend_history_contract.py` 防止以后把成功路径又改回 fallback。

面试时可以这样讲：

> 我保留 mock 作为显式开发模式，但真实 API 模式不能悄悄回退 mock。否则系统看起来可用，实际后端已经坏了。Day 21 后，任务列表、报告列表和报告详情都必须消费真实接口。

### Q36：为什么 Day 21 没有直接做复杂权限和筛选 UI？

当前项目仍是本地单用户简历项目，Day 21 的核心目标是打通历史数据查询和真实前端映射。复杂权限需要用户体系、项目空间、鉴权中间件和数据隔离策略，如果在历史 API 还没稳定时引入，会让主线过早膨胀。

Day 21 的保留扩展口：

- `tasks` 本身已经有 `user_id`、`project_id`。
- `reports` 可以通过 `task_id` 关联任务，再做项目过滤。
- `GET /api/tasks` 已有状态、时间、分页参数。
- `GET /api/reports` 已有报告状态、任务状态、时间、分页参数。

面试时可以这样讲：

> 我不是忽略权限，而是按阶段控制复杂度。Day 21 先稳定历史查询契约和数据来源，后续加用户/项目过滤时只需要在 store 查询层增加 where 条件，不需要重写前端页面和 API 形状。

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

截至 Day 21，最适合展示：

- `backend/app/api/routes/tasks.py`：`GET /api/tasks` 如何支持历史任务查询、状态筛选、时间筛选和分页。
- `backend/app/api/routes/reports.py`：`GET /api/reports`、`GET /api/reports/{report_id}` 和报告证据链 API。
- `backend/app/api/schemas/reports.py`：报告列表、报告详情和 section 的前端契约。
- `backend/app/storage/task_stores.py`：历史任务查询为什么优先走 PostgreSQL，而不是 Redis。
- `tests/test_history_api.py`：历史任务、失败任务保留、报告列表、报告详情和 404 envelope 测试。
- `tests/test_frontend_history_contract.py`：前端历史页真实 API 契约测试。
- `frontend/src/lib/api.ts`：任务列表、报告列表和报告详情的真实 API 映射。
- `frontend/src/components/task-progress-panel.tsx`：任务详情轮询、手动刷新、终态停止和刷新错误展示。
- `backend/app/api/routes/tasks.py`：`GET /api/tasks/{task_id}/steps` 如何返回脱敏 Agent step 摘要。
- `backend/app/api/schemas/tasks.py`：`AgentStepSummaryData` 和 `TaskAgentStepsData`。
- `backend/app/storage/agent_stores.py`：按 `task_id` 查询 Agent steps 的持久化入口。
- `tests/test_task_steps_api.py`：steps API 的任务存在性、脱敏输出和空 steps 测试。
- `tests/test_frontend_task_progress_contract.py`：任务详情轮询面板和真实 steps 映射的契约测试。
- `frontend/src/lib/api.ts`：前端真实 API client、统一 envelope 解析、`ApiClientError` 和 fallback 边界。
- `frontend/src/components/new-research-form.tsx`：真实任务提交表单，成功后跳转任务详情。
- `frontend/src/app/research/new/page.tsx`：新建任务页面从静态 mock 表单切换为客户端提交组件。
- `frontend/src/components/app-shell.tsx`：控制台显示真实 API / mock 模式，降低联调误判。
- `tests/test_frontend_api_integration_contract.py`：前端真实接入的契约测试。
- `backend/app/api/routes/tasks.py`：API 如何接收任务、投递队列、统一错误。
- `backend/app/tasks/service.py`：任务状态创建和入队流程。
- `backend/app/tasks/dispatcher.py`：Celery 分发器抽象。
- `backend/app/tasks/status_store.py`：Redis 状态存储和内存测试实现。
- `backend/app/tasks/event_store.py`：Redis 事件流存储和内存测试实现。
- `backend/app/storage/task_stores.py`：SQLAlchemy 持久化 store 和 Redis/PostgreSQL mirrored store。
- `backend/app/worker/tasks.py`：最小 worker 状态推进。
- `backend/app/crawler/service.py`：Playwright 最小采集和 HTML artifact 保存。
- `backend/app/crawler/extractors.py`：通用 HTML 字段抽取和失败分类。
- `backend/app/storage/crawl_stores.py`：采集结果写入 product、page、review、artifact 的持久化和幂等策略。
- `backend/app/agent/tools/schemas.py`：工具输入输出、错误和执行结果 schema。
- `backend/app/agent/tools/registry.py`：工具注册和发现机制。
- `backend/app/agent/tools/executor.py`：统一工具执行 envelope 和错误分类。
- `backend/app/agent/tools/builtin.py`：`crawl_product_tool` 内置工具。
- `backend/app/storage/agent_stores.py`：Agent run / step 持久化 store。
- `backend/app/agent/state_machine.py`：最小 ReAct 状态机，记录 Thought / Action / Observation。
- `backend/app/agent/guardrails.py`：结构化输出校验、自愈提示词和失败封装。
- `backend/app/agent/memory.py`：短期记忆滑动窗口、摘要压缩、证据 ID 保留和 Redis 缓存 store。
- `backend/app/rag/text.py`：评论清洗和按句子边界切片。
- `backend/app/rag/embeddings.py`：embedding provider 抽象和确定性 fake provider。
- `backend/app/rag/review_index.py`：review chunk 入库、幂等更新和 top_k 检索原型。
- `backend/app/agent/tools/builtin.py`：`search_reviews_tool` schema、依赖注入注册和证据输出。
- `backend/app/reporting/schemas.py`：`StructuredReport`、`ReportFinding` 和证据引用校验。
- `backend/app/reporting/generator.py`：确定性报告生成骨架和无证据降级。
- `backend/app/reporting/stores.py`：报告 JSON、Markdown、evidence refs 和 schema version 入库。
- `backend/app/reporting/evidence.py`：evidence ref 解析、EvidenceChain、缺失证据降级和来源回查。
- `backend/app/reporting/scoring.py`：维度评分、样本不足降权、风险/机会解释。
- `backend/app/api/routes/reports.py`：报告证据链 API。
- `backend/app/storage/models.py`：数据库模型设计。
- `migrations/versions/0002_task_queue_id.py`：任务队列 ID 持久化迁移。
- `tests/test_task_persistence.py`：任务和事件持久化测试。
- `tests/test_tasks_api.py`：API 成功、失败、队列不可用测试。
- `tests/test_celery_worker.py`：Celery 配置、worker 状态推进和事件写入测试。
- `tests/test_crawler_service.py`：采集成功、拦截、空 DOM 和 artifact 保存测试。
- `tests/test_crawl_persistence.py`：采集结果入库和幂等测试。
- `tests/test_agent_tools.py`：工具注册、参数校验、统一执行结果和分类错误测试。
- `tests/test_agent_state_machine.py`：Agent step 顺序、成功链路、失败链路和最大工具调用限制测试。
- `tests/test_structured_output_guardrails.py`：坏 JSON 修复、修复失败、repair retry 和指标累计测试。
- `tests/test_short_term_memory.py`：短期记忆窗口、摘要压缩、证据引用、从 step 恢复和状态机接入测试。
- `tests/test_review_rag_indexing.py`：评论清洗、切片、fake embedding、入库幂等和相似检索测试。
- `tests/test_search_reviews_tool.py`：RAG 工具注册、证据返回和空召回降级测试。
- `tests/test_report_generation.py`：报告 evidence refs 校验、证据不足降级、Markdown 渲染和报告入库测试。
- `tests/test_report_evidence_chain.py`：证据链解析、回查、缺失降级、Markdown citation 和 API envelope 测试。
- `tests/test_report_scoring.py`：维度分组、风险机会评分、样本不足降权和 Markdown 评分展示测试。

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

- Day 10：Agent 工具 schema 和工具注册机制已完成。
- Day 11：ReAct 状态机和 Agent step 持久化已完成。
- Day 12：Pydantic guardrails 和 self-heal 已完成。
- Day 13：短期记忆滑动窗口和上下文压缩已完成。
- Day 14：评论切片、fake embedding、review chunk 入库和相似检索原型已完成。
- Day 15：`search_reviews_tool` 和 evidence chunk 输出已完成。
- Day 16：结构化报告 schema、确定性报告生成、Markdown 渲染和 `reports` 入库已完成。
- Day 17：证据链回查、Markdown citation 和 `GET /api/reports/{report_id}/evidence` 已完成。
- Day 18：可解释风险/机会评分、样本不足降权和 Markdown 评分展示已完成。
- Day 19：Next.js 真实任务提交、任务状态查询、任务事件读取和前端错误 envelope 展示已完成。
- Day 20：任务详情轮询、`GET /api/tasks/{task_id}/steps` 和 Agent step 脱敏摘要展示已完成。
- Day 21：历史任务、历史报告列表和报告详情真实 API 接入已完成。

中期：

- 真实 embedding provider。
- pgvector 原生向量排序。
- 真实 LLM report prompt。
- 报告详情页和前端证据链展示。

后期：

- 前端历史报告和证据链详情完善。
- Docker Compose。
- LLMOps 指标和 50 次任务复盘。

## 面试结尾总结

如果面试官让你用一句话总结项目，可以说：

> 这个项目的核心价值是把“LLM 生成报告”升级成一个可追踪、可恢复、带证据链的异步 Agent 系统。

如果让你说最难点：

> 最难的不是单个模型调用，而是长任务状态、工具调用、证据检索和失败恢复之间的一致性设计。

如果让你说下一步：

> 下一步我会补日志、trace、错误分类和更完整的报告证据链前端展示，让历史任务不仅能查到，还能更快定位失败原因和报告证据来源。
