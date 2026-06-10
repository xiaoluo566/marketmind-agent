# 第二阶段缺口与修复汇总

## 文档定位

这份文档记录 Phase 2 RC 仍然存在的缺口，以及 Day40 已修复的问题。它的目标是防止项目把未验证能力写成已完成能力。

## 已修复问题

| 问题 | 影响 | 处理结果 | 是否阻塞 Phase 2 RC |
| --- | --- | --- | --- |
| `next/font/google` 依赖外网字体 | `npm run build` 在受限网络下会因为无法访问 Google Fonts 失败 | 已修复：移除 `next/font/google`，改用系统字体栈，并增加前端本地化契约测试 | 不阻塞 Phase 2 RC |
| Windows ignored 产物短暂文件锁 | `.next` 或 `test-results/.last-run.json` 可能让 build / E2E 在清理阶段报 EPERM | 已处理：路径校验后清理 ignored 生成目录，顺序重跑 `npm run build` 和 `npm run test:e2e` 通过 | 不阻塞 Phase 2 RC |

## 仍未完成或未补验

| 缺口 | 当前状态 | 影响 | 下一步 |
| --- | --- | --- | --- |
| Docker Compose 真实 build/up | 已有 compose config、Dockerfile 和 runbook；未完成真实 daemon 下 `docker compose up --build` | 不能声明多容器真实联调完成 | Docker Desktop daemon 可用后补验 health、API 提交和 worker 消费 |
| 真实 provider 成本 | 只有配置边界和 `agent_runs.total_cost` 字段；没有真实账单采样 | 不能写真实线上成本 | 接真实 provider 后持久化 token、latency、cost |
| 真实多容器 E2E | Day37 是 mock dev server E2E | 不能证明 Docker/API/Redis/Celery/provider 全链路 | 真实 compose 可用后新增 Playwright + API E2E |
| branch protection | 已有 CI 和 PR 模板；未自动配置 required checks | main 保护仍依赖人工纪律 | 在 GitHub 仓库手动开启 required checks，并截图或记录配置 |
| CSV/JSON 评论导入 | 尚未实现 | 用户无法直接导入店铺后台或第三方工具导出的评论 | Day41 优先设计导入 schema、校验、去重和入库链路 |
| 低风险真实站点适配器 | 尚未实现 | 项目仍偏 fixture/demo，真实应用说服力不足 | 选择公开 demo / Shopify / Amazon 静态样例等低风险来源 |
| 真实业务样本 RAG 质量评估 | 当前是 fixture 评估集 | 不能证明真实评论召回质量 | 建立小型人工标注集，记录 query、expected evidence 和 recall |
| 真实 LLM evidence-bound 报告 | Prompt 契约已完成，但未跑真实 provider | 不能声明真实模型报告质量 | 接 provider 后继续强制 evidence refs 校验和 JSON repair |
| 前端证据链报告闭环 | 已有报告详情和 evidence chain；缺少导入样本到报告的完整演示 | 用户还不能从导入数据一路看到结论和原始评论 | Day41-Day50 打通导入 -> 分析 -> 报告 -> 证据回查 |

## 不作为 Phase 2 RC 阻塞项的原因

Phase 2 RC 的目标是证明第二阶段深化能力：中文界面、retry、provider 边界、RAG 评估方法、真实 LLM prompt 契约、E2E、导出和 LLMOps summary。它不是最终商用版本。

因此，上表未完成项必须记录为 backlog，但不阻塞 `v0.2-phase2-rc1`，前提是 README、面试文档和 release 文档都不夸大。

## 面试讲法

如果被问“这些缺口是不是说明项目没做完”，可以回答：

> 是的，它还不是生产 v1.0。我把它标成 Phase 2 RC，就是为了区分已验证工程能力和下一阶段真实应用闭环。当前最有价值的不是说所有外部场景都已覆盖，而是系统已经有任务、状态、证据链、报告、导出、LLMOps 和测试门禁，下一阶段可以围绕 CSV/JSON 导入和真实样本分析继续深化。
