# Day 30 缺口与 Bug 汇总

## 文档定位

这份文档记录 Day 30 release candidate 仍未解决的缺口、当前影响、为什么暂时不在第一阶段完成，以及第二阶段如何处理。它不是失败清单，而是为了让项目边界可解释、可回退、可继续迭代。

关联文档：

- 发布候选说明：`day30-release-candidate.md`
- 指标汇总：`day30-metrics-summary.md`
- 后续迭代：`future-iterations.md`
- 回退手册：`rollback-runbook.md`
- 面试防守手册：`interview-defense-dossier.md`

## 未解决缺口

| 缺口 | 当前状态 | 影响 | 第二阶段处理 |
| --- | --- | --- | --- |
| 前端 retry 按钮 | 后端已有 `POST /api/tasks/{task_id}/retry`，前端未接按钮 | 演示 retry 仍需通过 API 或测试说明 | 在任务详情页的 failed 状态展示 retry 按钮、loading、错误提示和恢复事件 |
| 真实 compose build/up | `docker compose config` 已验证，本机 Docker Desktop daemon 不可用 | 不能声明容器真实启动和服务间联调已完成 | Docker daemon 可用后执行 `docker compose up --build`、容器 health、API 提交和 worker 消费 |
| 真实 embedding provider | 当前使用 deterministic fake provider | RAG 召回只验证结构，不代表真实语义效果 | 接 `text-embedding-3-small` 或可配置 provider，补超时、维度、失败重试测试 |
| 真实 LLM report prompt | 当前报告生成器是确定性 baseline | 报告结构可验证，但没有真实模型文案能力 | 接真实报告 prompt，并强制通过 `StructuredReport` schema 和 evidence refs 校验 |
| Celery countdown | `backoff_seconds` 只写入 metadata | retry 有恢复语义，但没有真实延迟调度 | 在真实 Celery/Redis 环境接 `countdown`，补 E2E 和幂等锁 |
| Agent step replay | 当前是任务级 retry，不是精确 Thought/Action/Observation replay | 无法从某一步工具调用后继续 | 基于 `agent_steps` 和最近 observation 实现 step-level resume |
| Playwright E2E | 前端有契约测试和构建验证，缺少浏览器 E2E | UI 主流程没有真实点击回归 | 用 Playwright 覆盖提交任务、查看进度、打开报告、查看 evidence chain |
| GitHub branch protection | CI 已有，但未配置 required status checks | 远程协作保护不完整 | 在 GitHub 设置 `main`/`dev` required checks 和 PR 合并策略 |
| 真实外部采集稳定性 | 当前有 fixture/public URL 最小采集 | 不能声明稳定爬取所有电商站 | 先做 CSV/JSON 兜底，再选择 1 个站点做 adapter |

## 当前不视为阻塞 RC 的原因

Day30 release candidate 的目标是第一阶段可展示、可复盘、可继续迭代，不是商用 v1.0。下面这些缺口会影响“产品完整度”，但不否定当前工程主链路：

- 核心 API、Worker、存储、Agent、RAG、报告和证据链已有自动化测试。
- CI、本地质量门禁、回退手册和 release checklist 已存在。
- 指标明确标注为 fixture benchmark，没有夸大成线上性能。
- Docker daemon 不可用已经记录为环境限制，没有假装真实 compose build/up 已通过。

## 面试时怎么讲

可以这样讲：

> Day 30 我没有把项目包装成已经商用的 v1.0，而是做成 release candidate。当前最核心的工程链路已经可测试、可演示、可回退，但前端 retry、真实 compose up、真实 provider、Playwright E2E 和 branch protection 还在第二阶段 backlog。这样讲更诚实，也更符合真实工程迭代。

如果被追问“为什么这些没做完还能写简历”，可以回答：

> 简历重点不是说它已经上线，而是展示我如何把 Agent 项目从脚本做成工程系统：有异步任务、状态持久化、证据链、RAG、CI、coverage、benchmark、失败恢复和发布复盘。未完成项我会明确写成后续迭代，不把它们包装成已完成能力。
