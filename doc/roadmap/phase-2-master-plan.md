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
| Retry 前端闭环 | failed 任务详情页可点击重试并展示恢复状态 | `../supporting/phase-2-practicality-plan.md` | Day32 |
| 真实 Compose 联调 | Docker daemon 可用后完成真实 build/up 和容器内主链路 | `../supporting/phase-2-acceptance-and-risk.md` | Day33/补验 |
| 真实 embedding provider | 从 deterministic fake provider 过渡到可配置 provider | `../supporting/phase-2-practicality-plan.md` | Day34 |
| 真实 LLM report prompt | 保留 schema/evidence refs 约束，接入真实模型报告生成 | `../supporting/phase-2-practicality-plan.md` | Day35 |
| Playwright E2E | 覆盖任务提交、进度、报告、证据链、retry | `../supporting/phase-2-acceptance-and-risk.md` | Day36 |
| 分支保护 | main/dev required checks 与 PR 合并约束 | `../supporting/phase-2-acceptance-and-risk.md` | Day37 |
| LLMOps 深化 | 成本、耗时、失败率、自愈率、恢复成功率 | `../supporting/llmops-metrics.md` | 后续 |

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

## 第一周建议节奏

| Day | 主题 | 目的 |
| --- | --- | --- |
| Day 31 | 中文界面与术语统一 | 让项目展示不再像英文模板 |
| Day 32 | 前端 retry 按钮 | 打通失败恢复的用户操作闭环 |
| Day 33 | Retry 前端 E2E / 手动验证 | 确认页面、API、事件流一致 |
| Day 34 | 真实 embedding provider 设计和 provider 抽象加固 | 为真实 RAG 做准备 |
| Day 35 | provider 成本和失败指标 | 给 LLMOps 面板提供数据 |
| Day 36 | 真实 LLM report prompt | 从确定性报告过渡到模型报告 |
| Day 37 | Playwright E2E 和分支保护 | 提升协作和回归可靠性 |
