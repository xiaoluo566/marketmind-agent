# 第二阶段主计划：从可展示 RC 到更实用的中文产品雏形

## 阶段定位

Day 1-30 已经把 MarketMind Agent 做成了第一阶段 release candidate：主链路、测试、CI、benchmark、retry 后端、报告证据链和演示材料都已经收口。第二阶段不再证明“我能搭一个工程化 Agent”，而是解决两个更贴近真实使用的问题：

1. 使用者能不能顺畅操作它。
2. 分析结果能不能更接近真实业务价值。

所以第二阶段的关键词是：

- 中文界面
- 用户可用性
- 前端 retry 按钮
- 真实 compose build/up
- 真实 embedding provider
- 真实 LLM report prompt
- Playwright E2E
- GitHub branch protection
- 更清晰的 LLMOps 和失败恢复统计

第二阶段仍然坚持“先文档后开发”。每个功能开发前必须先写明目标、契约、测试、回退和与已有文档的关系，避免 Day31 之后互相冲突。

## 为什么第二阶段先做中文界面

当前 Next.js 控制台还有大量英文展示文案，例如 Dashboard、New Research、Tasks、Reports、Evidence、Settings、Recent tasks、System chain 等。对一个面向中文电商运营场景的项目来说，这会带来三个问题：

- 面试演示时，项目定位说中文电商运营，但界面仍像英文 SaaS 模板，可信度下降。
- 后续接 retry、报告解释、证据链和 LLMOps 时，如果中英文混杂，页面含义会变得不稳定。
- 文档已经大量使用中文术语，但前端显示层没有统一术语，容易出现“任务 / job / research / run”混用。

因此 Day31 先做中文界面，不是为了美化，而是为了统一产品语言、降低演示理解成本，并给后续功能提供稳定文案契约。

## 第二阶段模块拆分

| 模块 | 目标 | 关联文档 | 首个交付 |
| --- | --- | --- | --- |
| 前端中文化 | 所有可见核心页面使用中文术语 | `../supporting/frontend-localization-contract.md` | Day31 |
| Retry 前端闭环 | failed 任务详情页可点击重试并展示恢复状态 | `../supporting/phase-2-practicality-plan.md` | `day-32.md` |
| Retry 联调验收 | 校验 `waiting_retry`、恢复事件、事件流和浏览器行为 | `../supporting/phase-2-acceptance-and-risk.md` | `day-33.md` |
| 真实 embedding provider | 从 deterministic fake provider 过渡到可配置 provider | `../supporting/phase-2-practicality-plan.md` | `day-34.md` |
| RAG 质量指标 | 建立 RAG 评估集、召回质量和 provider_metrics | `../supporting/llmops-metrics.md` | `day-35.md` |
| 真实 LLM 报告生成 | 保留 schema/evidence refs 约束，接入真实模型报告生成 | `../supporting/phase-2-practicality-plan.md` | `day-36.md` |
| Playwright E2E | 覆盖任务提交、进度、报告、证据链、retry | `../supporting/phase-2-acceptance-and-risk.md` | `day-37.md` |
| 报告导出 | Markdown 导出和证据包 artifact | `../supporting/reporting`、`../supporting/security-compliance.md` | `day-38.md` |
| LLMOps 深化 | 成本、耗时、失败率、自愈率、恢复成功率 | `../supporting/llmops-metrics.md` | `day-39.md` |
| Phase 2 RC | 阶段验收、release candidate、回归门禁和 main 合并判断 | `../supporting/release-checklist.md` | `day-40.md` |

具体顺序可以按环境调整。比如 Docker daemon 如果仍不可用，真实 compose build/up 不阻塞其他开发，但必须保留为未补验项。

## 第二阶段不做什么

第二阶段暂不做：

- Kubernetes。
- Kafka。
- 多租户复杂权限。
- 全网电商稳定采集。
- 销量预测、广告优化、库存预测。
- 复杂多 Agent 自治。

原因是这些能力会扩大范围，但不能直接改善当前核心价值。当前核心价值仍然是评论洞察、证据链报告、长任务可追踪和失败可恢复。

## 文档依赖关系

第二阶段文档关系如下：

- `phase-2-master-plan.md`：阶段总计划和开发顺序。
- `day-31.md`：中文界面执行手册。
- `../supporting/frontend-localization-contract.md`：中文术语、页面范围、非目标和测试契约。
- `../supporting/phase-2-practicality-plan.md`：实用性深化路线，包括 retry、provider、prompt、LLMOps。
- `../supporting/phase-2-acceptance-and-risk.md`：验收门槛、风险和回退策略。
- `../supporting/future-iterations.md`：第二阶段 backlog 来源。
- `../supporting/day30-bug-summary.md`：第二阶段优先级从 Day30 缺口反推。

任何第二阶段开发如果改变 API、状态机、报告 schema 或 UI 术语，必须同步这些文档。

## 第二阶段验收总标准

第二阶段阶段性验收至少满足：

- 中文界面覆盖核心页面。
- failed 任务能从前端发起 retry。
- 真实 provider 接入前后都有测试和回退。
- 真实 compose build/up 一旦环境可用必须补验并记录。
- Playwright E2E 覆盖至少一个完整主流程。
- main 只保留稳定版本，dev 用于日常开发。
- 所有新能力都有测试、文档和开发日志。

## Day32-Day40 执行路线

Day32-Day40 是第二阶段第一轮深化开发。它不是继续增加新名词，而是沿着 Day30 缺口和 Day31 中文界面基线，把项目从“可展示 RC”推进到“更实用的中文产品雏形”。

| Day | 文档 | 主题 | 目的 | 主要依赖 |
| --- | --- | --- | --- | --- |
| Day 32 | `day-32.md` | 前端失败任务重试闭环 | 把后端 retry API 变成用户可点击的恢复能力 | Day28、Day31 |
| Day 33 | `day-33.md` | 重试链路联调与恢复事件验收 | 校验 `waiting_retry`、恢复事件、前端刷新和浏览器行为 | Day28、Day32 |
| Day 34 | `day-34.md` | 真实 embedding provider 接入设计 | 加固 `EmbeddingProvider`、真实 provider 配置和 provider fallback | Day14、Day15、模型决策 |
| Day 35 | `day-35.md` | RAG 检索质量与 provider 指标 | 建立 RAG 评估集、召回质量和 provider_metrics | Day34、LLMOps |
| Day 36 | `day-36.md` | 真实 LLM 报告生成 Prompt | 用 `StructuredReport`、`evidence_refs`、Pydantic 约束真实模型报告 | Day12、Day16、Day17 |
| Day 37 | `day-37.md` | Playwright E2E 主链路 | 用真实浏览器覆盖新建调研、任务、报告、证据链和 retry 入口 | Day31、Day32 |
| Day 38 | `day-38.md` | 报告导出与证据包 | 让报告具备 Markdown 导出、证据包和 artifact 交付能力 | Day16、Day17 |
| Day 39 | `day-39.md` | LLMOps 运营指标面板 | 展示成本统计、失败率、自愈成功率和恢复成功率 | Day35、Day36 |
| Day 40 | `day-40.md` | 第二阶段阶段验收与发布候选 | 建立 Phase 2 RC、阶段验收、release candidate 和回归门禁 | Day31-Day39 |

这 9 个执行日必须继续遵守：

- 每天先跑前一天验收，确认没有遗漏。
- 每天开发前先更新或确认当天文档。
- 每天开发后更新 `development-log.md`、`interview-defense-dossier.md` 和 `testing-strategy.md`。
- 任何真实 provider、真实 compose build/up、真实 LLM 调用，都必须把 mock / fixture / real 的边界写清楚。
