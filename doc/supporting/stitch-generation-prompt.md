# Stitch 生成提示词

## 用途

这份文档保存给 Stitch 使用的前端生成提示词。目标是一次生成尽量贴近本项目工程边界的控制台 UI，减少后续重构成本。

## 生成目标

生成一个“电商竞品调研与差评洞察 Agent 系统”的前端控制台。这个系统不是营销官网，不需要 landing page，不需要大面积宣传文案。它是一个给开发者、运营分析人员和面试演示使用的工作台。

前端只负责交互和展示，不负责爬虫、Agent 决策、RAG 检索、模型调用或数据库访问。所有业务能力都通过 FastAPI 后端接口完成。正式实现会使用 Next.js，本提示词用于生成或校准视觉参考。

## 直接复制给 Stitch 的主提示词

```text
请为一个名为 MarketMind Agent 的电商竞品调研与差评洞察系统生成一个生产级前端控制台。

这是一个工程化 Agent 项目，不是营销落地页。请不要生成 hero landing page，不要生成大段产品宣传文案，不要使用夸张渐变背景，不要做纯展示型官网。我要的是一个可真实接入后端 API 的 SaaS/数据分析工作台。

项目背景：
用户输入商品链接或上传评论数据后，后端会通过 FastAPI 创建异步任务，Celery Worker 执行爬虫、Agent 推理、评论 RAG 检索和报告生成。前端需要展示任务提交、任务状态、Agent 执行时间线、差评检索结果、报告详情和历史任务。

视觉方向：
- 设计成专业、克制、工程化的数据分析控制台。
- 风格关键词：industrial SaaS、developer operations、market research cockpit、quiet but premium。
- 不要卡片堆满屏幕，不要做营销页，不要紫色渐变风格。
- 使用清晰的信息层级、紧凑但不拥挤的布局。
- 色彩以浅色或中性背景为主，搭配少量蓝绿色/琥珀色用于状态和风险提示。
- 字体要清晰易读，适合长时间查看任务日志、表格和报告。
- 组件圆角控制在 8px 左右，不要过度圆润。

技术要求：
- 生成 Next.js App Router 风格的前端代码，使用 TypeScript。
- 使用可维护的组件结构，而不是把所有内容写在一个大文件里。
- 可以使用 Tailwind CSS 或普通 CSS，但样式要清晰可维护。
- 所有数据先使用 mock data，但代码结构要方便后续替换成真实 API。
- 不要把 API URL 到处硬编码；需要集中放在 api client 或配置位置。
- 页面需要桌面端优先，但也要保证 1366px 宽度和移动端基本可用。

应用结构：
请生成一个应用 shell，包含左侧导航、顶部状态栏和主内容区。

左侧导航包含：
1. Dashboard / 概览
2. New Research / 新建调研
3. Tasks / 任务历史
4. Reports / 报告库
5. Evidence / 证据检索
6. Settings / 设置

顶部状态栏包含：
- 当前环境：Local Dev
- API 状态：Connected / Mock
- Worker 状态：Idle / Running / Delayed
- 当前模型：OpenAI-compatible
- 一个轻量的刷新按钮

页面 1：Dashboard / 概览
需要展示：
- 今日任务数
- 成功率
- 平均耗时
- 待处理任务数
- 模型输出校验失败次数
- 最近任务列表
- 最近生成报告列表
- 一个“系统链路状态”小组件：API、Redis、Celery Worker、PostgreSQL、pgvector、Crawler、Agent。

页面 2：New Research / 新建调研
需要展示：
- 商品链接输入框
- 数据源模式选择：URL Crawl、CSV/JSON Upload、Demo Dataset
- 分析模式选择：竞品差评分析、产品机会点分析、风险扫描、完整报告
- 优先级选择：normal、high
- 可选项：
  - 启用评论 RAG 检索
  - 保存页面截图
  - 生成 Markdown 报告
  - 失败后自动重试
- 提交按钮
- 提交成功后展示 task_id、当前状态和“查看任务详情”按钮

页面 3：Task Detail / 任务详情
需要展示：
- 任务标题、task_id、状态 badge、创建时间、耗时
- 当前阶段进度条：received、queued、running、crawling、reasoning、retrieving、reporting、completed
- 事件时间线：每条事件包含时间、模块、状态、消息
- Agent Steps 面板：展示 step_index、step_type、tool_name、status、duration、observation 摘要
- 错误面板：如果失败，展示 error_code、error_message、retryable、建议动作
- 操作按钮：Retry、Cancel、Open Report、View Raw Events

页面 4：Reports / 报告库与报告详情
报告列表需要展示：
- 报告标题
- 来源任务
- 生成时间
- 风险等级
- 证据数量
- 状态

报告详情需要展示：
- Executive Summary / 摘要
- Product Snapshot / 竞品概况
- Review Pain Points / 差评痛点
- Risk Score / 风险评分
- Opportunity Signals / 机会点
- Evidence References / 证据引用
- Method Trace / 方法追踪

报告详情中的证据引用要设计成可折叠列表。每条证据包含：
- evidence_id
- 来源类型：review、crawler_artifact、agent_step
- 相似度或置信度
- 原文片段
- 来源 URL 或 source label

页面 5：Evidence / 证据检索
需要展示：
- 搜索框，placeholder 为“搜索质量差、物流慢、退货、售后等问题”
- top_k 选择
- 过滤项：评分、来源、时间范围
- 检索结果列表
- 每个结果展示相似度、评论片段、评分、来源、关联任务
- 右侧展示“已选择证据”，用于后续生成报告

页面 6：Settings / 设置
需要展示：
- API Base URL
- Polling interval
- Environment
- Model provider 显示
- Feature toggles：
  - enable_rag
  - enable_crawler_screenshot
  - enable_agent_step_debug
  - enable_retry

重要状态设计：
请定义统一状态颜色：
- received / queued：灰色或蓝灰色
- running / crawling / reasoning：蓝色
- retrieving / reporting：青绿色
- completed：绿色
- waiting_retry：琥珀色
- failed：红色
- cancelled：灰色

Mock 数据要求：
请内置一组真实感 mock data，包括：
- 5 个任务
- 2 个运行中任务
- 1 个失败任务
- 3 份报告
- 10 条 Agent step
- 8 条 evidence 检索结果
mock data 要尽量贴近真实后端字段命名，例如 task_id、status、trace_id、agent_run_id、step_index、tool_name、error_code、report_id、evidence_id。

API 接入预留：
请创建或预留 api client 层，后续将接入这些接口：
- POST /api/tasks
- GET /api/tasks/{task_id}
- GET /api/tasks/{task_id}/events
- GET /api/tasks/{task_id}/steps
- POST /api/tasks/{task_id}/retry
- GET /api/reports/{report_id}

请不要让页面直接访问数据库，不要在前端保存 API key，不要写任何模型调用逻辑，不要生成后端代码。

交互要求：
- 表格支持状态筛选。
- 长文本可折叠。
- Agent step 默认展示摘要，点击后展开详情。
- 失败任务要显示 retry 按钮。
- 报告证据引用可以展开和折叠。
- Dashboard 上的最近任务点击后能进入任务详情。

最终输出要求：
- 代码结构清晰，方便我后续接入真实 API。
- UI 看起来像一个认真做过的工程化控制台。
- 不要生成无意义占位文案。
- 不要生成大面积装饰图。
- 不要生成营销页。
```

## 如果 Stitch 支持分阶段生成

如果 Stitch 不能一次生成完整项目，可以按下面顺序分批生成。

### 第一批

```text
先只生成应用 shell、左侧导航、顶部状态栏、Dashboard、新建调研页。请保留 mock data 和 api client 预留，不要生成后端。
```

### 第二批

```text
在已有应用基础上继续生成任务详情页。重点是任务状态进度条、事件时间线、Agent Steps 表格、失败错误面板和 Retry 操作。
```

### 第三批

```text
在已有应用基础上继续生成报告列表、报告详情和证据引用组件。报告需要展示摘要、竞品概况、差评痛点、风险评分、机会点和证据来源。
```

### 第四批

```text
在已有应用基础上继续生成 Evidence 检索页和 Settings 页。Evidence 页面需要展示评论语义检索结果和证据选择区。Settings 页面只做 API Base URL、轮询间隔、环境和功能开关。
```

## 后续我接入时最需要的代码形态

正式 Next.js 实现最好有这些文件或类似结构：

```text
frontend/
  src/
    app/ or pages/
    components/
      AppShell.tsx
      Sidebar.tsx
      StatusBadge.tsx
      TaskTimeline.tsx
      AgentStepsTable.tsx
      EvidenceList.tsx
      ReportViewer.tsx
    lib/
      api.ts
      mock-data.ts
      types.ts
    styles/
```

## 字段建议

这些字段要尽量在 mock data 中出现，方便后续替换真实接口。

### Task

- `task_id`
- `title`
- `target`
- `mode`
- `status`
- `priority`
- `created_at`
- `started_at`
- `finished_at`
- `duration_ms`
- `trace_id`
- `report_id`

### Task Event

- `event_id`
- `task_id`
- `module`
- `event_type`
- `status`
- `message`
- `created_at`
- `payload`

### Agent Step

- `agent_run_id`
- `step_index`
- `step_type`
- `tool_name`
- `status`
- `duration_ms`
- `input_summary`
- `observation_summary`
- `error_code`

### Report

- `report_id`
- `task_id`
- `title`
- `summary`
- `risk_level`
- `risk_score`
- `evidence_count`
- `created_at`
- `sections`

### Evidence

- `evidence_id`
- `source_type`
- `source_url`
- `similarity`
- `rating`
- `content`
- `task_id`
- `metadata`

## 生成后的检查清单

拿到 Stitch 输出后，先检查：

- 是否生成了营销页，如果有就删掉或改成 Dashboard
- 是否所有 mock data 都集中在一个文件
- 是否 API URL 集中配置
- 是否页面能覆盖任务提交、详情、报告、证据检索、设置
- 是否存在前端直接调用模型或数据库的逻辑
- 是否有明显中文溢出、按钮文字挤压、移动端遮挡
- 是否能在本地启动

## 与其他文档关系

- 前端交接见 `stitch-frontend-handoff.md`
- 页面职责见 `ui-console-spec.md`
- API 字段见 `api-contract.md`
- 数据样例见 `data-contract-examples.md`
