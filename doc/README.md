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
