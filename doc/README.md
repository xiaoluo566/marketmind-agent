# 文档总索引

这里是项目的文档入口。建议开发顺序先看 `supporting/`，再按 `roadmap/` 的 30 天节奏执行。

## 目录结构

- `supporting/`：项目总览、架构、数据库、API、Agent、RAG、部署、测试、风险等横向文档
- `roadmap/`：Day 01 到 Day 30 的每日开发文档
- `roadmap/30-day-master-plan.md`：总览式里程碑表，适合每周复盘

## 这套文档怎么配合使用

这套文档不是平铺的说明书，而是“先定义能力，再拆任务，再按天执行，再做复盘”的链式结构：

- `project-charter.md` 和 `market-positioning.md` 负责说清楚为什么做、做给谁、真实市场边界在哪里
- `architecture.md`、`model-and-data-decisions.md` 和 `data-model.md` 负责说清楚系统怎么分层、模型和数据源怎么选、数据怎么流转
- `api-contract.md`、`agent-state-machine.md`、`prompt-strategy.md` 负责说清楚代码层怎么对接
- `crawler-strategy.md`、`rag-memory.md`、`ui-console-spec.md` 负责说清楚核心功能怎么实现
- `testing-strategy.md`、`deployment.md`、`release-checklist.md` 负责说清楚怎么验证、怎么发版、怎么回退
- `stitch-frontend-handoff.md` 负责说清楚 Stitch 前端的交接方式
- `stitch-generation-prompt.md` 负责保存可直接复制给 Stitch 的详细提示词
- `stitch-export-review.md` 负责记录 Stitch 导出内容的评审和 Next.js 重构方向
- `development-log.md` 负责记录 Day 1 到 Day 30 以及后续优化的真实开发过程
- `interview-defense-dossier.md` 负责沉淀面试讲述、技术选择、开发问题和高频追问回答
- `roadmap/day-xx.md` 负责把这些内容拆成可执行日程

## 阅读顺序

1. `supporting/project-charter.md`
2. `supporting/market-positioning.md`
3. `supporting/dependency-map.md`
4. `supporting/architecture.md`
5. `supporting/model-and-data-decisions.md`
6. `supporting/data-model.md`
7. `supporting/api-contract.md`
8. `supporting/agent-state-machine.md`
9. `supporting/prompt-strategy.md`
10. `supporting/crawler-strategy.md`
11. `supporting/rag-memory.md`
12. `supporting/stitch-frontend-handoff.md`
13. `supporting/stitch-generation-prompt.md`
14. `supporting/stitch-export-review.md`
15. `roadmap/day-01.md` 起按天推进

## 横向重点文档

- `supporting/milestones-and-acceptance.md`：每周交付物和验收门槛
- `supporting/market-positioning.md`：市场定位、真实价值和非替代边界
- `supporting/model-and-data-decisions.md`：模型、embedding、数据源、CSV/JSON、用户和项目隔离决策
- `supporting/dev-workflow.md`：日常开发、分支、提交、回退流程
- `supporting/llmops-metrics.md`：模型调用、成本、失败率和自愈统计
- `supporting/security-compliance.md`：安全、隐私和采集合规边界
- `supporting/demo-script.md`：最终演示脚本
- `supporting/interview-defense-dossier.md`：面试防守手册，包含项目介绍、技术选择、开发问题和高频问答
- `supporting/development-log.md`：开发过程实时记录和后续优化日志
- `supporting/future-iterations.md`：30 天之后的迭代方向
- `supporting/dependency-map.md`：文档之间的前后依赖
- `supporting/release-checklist.md`：发版前检查项
- `supporting/stitch-frontend-handoff.md`：Stitch 前端生成和交接规范
- `supporting/stitch-generation-prompt.md`：Stitch 生成提示词
- `supporting/stitch-export-review.md`：Stitch 导出评审和 Next.js 重构方向

## 使用方式

- 每天只认当天文档和前置依赖文档
- 每个文档都写清楚目标、任务、验收、风险和回退
- 任何超出文档范围的想法先写入 `supporting/open-questions.md`

## 第二阶段入口

Day 1-30 完成后，第二阶段从“可展示 RC”推进到“更实用的中文产品雏形”。后续开发先读：

1. `roadmap/phase-2-master-plan.md`
2. `roadmap/day-31.md`
3. `supporting/frontend-localization-contract.md`
4. `supporting/phase-2-practicality-plan.md`
5. `supporting/phase-2-acceptance-and-risk.md`

第二阶段继续保持先文档后开发。中文界面、前端 retry 按钮、真实 provider、真实 compose build/up、Playwright E2E 和 branch protection 都必须在这些文档约束下推进。

## Day32-Day40 执行文档

第二阶段第一轮深化开发已经拆成这些执行文档：

| Day | 文档 | 主题 |
| --- | --- | --- |
| Day 32 | `roadmap/day-32.md` | 前端失败任务重试闭环 |
| Day 33 | `roadmap/day-33.md` | 重试链路联调与恢复事件验收 |
| Day 34 | `roadmap/day-34.md` | 真实 embedding provider 接入设计 |
| Day 35 | `roadmap/day-35.md` | RAG 检索质量与 provider 指标 |
| Day 36 | `roadmap/day-36.md` | 真实 LLM 报告生成 Prompt |
| Day 37 | `roadmap/day-37.md` | Playwright E2E 主链路 |
| Day 38 | `roadmap/day-38.md` | 报告导出与证据包 |
| Day 39 | `roadmap/day-39.md` | LLMOps 运营指标面板 |
| Day 40 | `roadmap/day-40.md` | 第二阶段阶段验收与发布候选 |

这些文档和 `supporting/development-log.md`、`supporting/interview-defense-dossier.md`、`supporting/testing-strategy.md` 绑定使用。每天开发完成后必须同步实际完成、验证结果、问题处理和面试讲法。
