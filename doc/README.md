# 项目文档索引

这里是 MarketMind Agent 的文档入口。文档按“项目定位 -> 架构与数据 -> API 与功能契约 -> 工程流程 -> 测试发布 -> 面试表达”的顺序组织。

## 推荐阅读顺序

1. [项目章程](supporting/project-charter.md)
2. [市场定位](supporting/market-positioning.md)
3. [系统架构](supporting/architecture.md)
4. [技术栈决策](supporting/tech-stack-decisions.md)
5. [模型与数据决策](supporting/model-and-data-decisions.md)
6. [数据模型](supporting/data-model.md)
7. [API 契约](supporting/api-contract.md)
8. [Agent 状态机](supporting/agent-state-machine.md)
9. [RAG 与记忆系统](supporting/rag-memory.md)
10. [Prompt 策略](supporting/prompt-strategy.md)
11. [爬虫策略](supporting/crawler-strategy.md)
12. [真实应用闭环说明](supporting/real-application-loop.md)
13. [前端控制台规格](supporting/ui-console-spec.md)
14. [测试策略](supporting/testing-strategy.md)
15. [部署说明](supporting/deployment.md)
16. [发布检查清单](supporting/release-checklist.md)

## 核心文档

- [development-log.md](supporting/development-log.md)：真实开发过程、问题修复、验证记录和后续优化日志。
- [interview-defense-dossier.md](supporting/interview-defense-dossier.md)：面试讲法、技术选择、问题处理和高频追问。
- [demo-script.md](supporting/demo-script.md)：项目演示流程和备用展示路线。
- [resume-story.md](supporting/resume-story.md)：简历表达素材。
- [interview-story.md](supporting/interview-story.md)：短版项目介绍和关键讲述路径。
- [future-iterations.md](supporting/future-iterations.md)：后续 backlog，不作为夸大已完成能力的依据。
- [security-compliance.md](supporting/security-compliance.md)：安全、隐私和采集合规边界。
- [rollback-runbook.md](supporting/rollback-runbook.md)：回退策略。
- [docker-compose-runbook.md](supporting/docker-compose-runbook.md)：Docker Compose 运行手册。

## 真实应用闭环相关文档

当前项目的应用价值围绕评论洞察和证据链报告展开：

- [real-application-loop.md](supporting/real-application-loop.md)
- [api-contract.md](supporting/api-contract.md)
- [crawler-strategy.md](supporting/crawler-strategy.md)
- [rag-memory.md](supporting/rag-memory.md)
- [prompt-strategy.md](supporting/prompt-strategy.md)
- [ui-console-spec.md](supporting/ui-console-spec.md)

## 前端与 Stitch 交接

- [stitch-frontend-handoff.md](supporting/stitch-frontend-handoff.md)
- [stitch-generation-prompt.md](supporting/stitch-generation-prompt.md)
- [stitch-export-review.md](supporting/stitch-export-review.md)
- [frontend-localization-contract.md](supporting/frontend-localization-contract.md)

## 历史路线归档

`roadmap/` 目录保存阶段性执行文档和历史开发记录。它用于复盘和追溯，不再作为 README 的主叙事入口。后续新功能以 Spec Kit 规格、TDD 测试和 supporting 文档为准。
