# Supporting 文档说明

这一组文档负责定义项目的长期约束，避免开发过程中只靠临时记忆做决定。

## 建议优先级

- 先看 `project-charter.md`，明确项目目标和非目标
- 再看 `market-positioning.md`，明确真实市场价值和不替代成熟卖家工具的边界
- 再看 `dependency-map.md`，知道哪些文档是前置，哪些是后置
- 再看 `architecture.md`、`data-model.md`、`api-contract.md`
- 再看 `model-and-data-decisions.md`，确认模型、embedding、数据源和用户边界
- 接着看 `agent-state-machine.md`、`prompt-strategy.md`、`crawler-strategy.md`、`rag-memory.md`
- 最后参考 `deployment.md`、`testing-strategy.md`、`risk-register.md`、`release-checklist.md`

## 交付和复盘

- `milestones-and-acceptance.md` 用来判断每周是否真的完成
- `market-positioning.md` 用来约束项目市场定位、用户价值和简历口径
- `llmops-metrics.md` 用来收集可写进简历的数据
- `demo-script.md` 用来准备最终展示
- `development-log.md` 用来实时记录 Day 1 到 Day 30 的实际开发过程和后续优化
- `stage-audit-day-01-21.md` 用来记录 Day 1-21 推主分支前的阶段审计、发现问题和修复结果
- `interview-defense-dossier.md` 用来准备面试讲述、技术选择、问题排查和高频追问
- `future-iterations.md` 用来管理 30 天之后的增强点
- `dev-environment.md` 用来约束本机开发环境
- `ui-console-spec.md` 用来约束前端控制台行为
- `stitch-frontend-handoff.md` 用来约束 Stitch 生成前端的交接方式
- `stitch-generation-prompt.md` 用来保存可直接复制给 Stitch 的详细提示词
- `stitch-export-review.md` 用来记录 Stitch 导出内容的评审和 Next.js 重构方向
- `model-and-data-decisions.md` 用来集中记录模型、embedding、首发数据源、CSV/JSON schema、用户和项目隔离策略

## 第二阶段 supporting 文档

Day 30 release candidate 之后，新增这些第二阶段文档：

- `frontend-localization-contract.md`：前端中文界面术语、范围、非目标和测试契约。
- `phase-2-practicality-plan.md`：用户可用性、工程深度和数据可信度的深化路线。
- `phase-2-acceptance-and-risk.md`：第二阶段验收门槛、风险、Docker daemon 不可用时的处理和回退策略。

这些文档和 `future-iterations.md`、`day30-bug-summary.md`、`testing-strategy.md`、`development-log.md` 共同决定第二阶段的开发顺序。后续不能绕开它们直接写功能。

## Day32-Day40 关联要求

Day32-Day40 的每日开发文档已经提前写好：

- `../roadmap/day-32.md`：前端失败任务重试闭环。
- `../roadmap/day-33.md`：重试链路联调与恢复事件验收。
- `../roadmap/day-34.md`：真实 embedding provider 接入设计。
- `../roadmap/day-35.md`：RAG 检索质量与 provider 指标。
- `../roadmap/day-36.md`：真实 LLM 报告生成 Prompt。
- `../roadmap/day-37.md`：Playwright E2E 主链路。
- `../roadmap/day-38.md`：报告导出与证据包。
- `../roadmap/day-39.md`：LLMOps 运营指标面板。
- `../roadmap/day-40.md`：第二阶段阶段验收与发布候选。

每天开发后必须同步：

- `development-log.md`
- `interview-defense-dossier.md`
- `testing-strategy.md`
- 如果改 API、模型、RAG、报告、部署或安全边界，还要同步对应 supporting 文档。
