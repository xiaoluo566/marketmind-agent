# 后续迭代清单

## 文档定位

这份文档记录 Day30 release candidate 之后的第二阶段和第三阶段 backlog。它不再是“想到什么写什么”的愿望清单，而是从 Day30 缺口、演示风险、工程闭环和面试表达中反推出来的迭代顺序。

关联文档：

- 当前版本边界：`project-charter.md`
- Day30 发布候选：`day30-release-candidate.md`
- Day30 缺口汇总：`day30-bug-summary.md`
- 指标与 LLMOps：`day30-metrics-summary.md`、`llmops-metrics.md`
- 回退手册：`rollback-runbook.md`
- 里程碑验收：`milestones-and-acceptance.md`

## 第二阶段优先级

第二阶段不继续盲目加技术栈，优先补 Day30 RC 中明确影响演示和工程闭环的缺口：

1. 前端 retry 按钮：Day32 已在 failed 任务详情页接入 `POST /api/tasks/{task_id}/retry`，展示 retry loading、失败提示、恢复事件和 mock 终态刷新；后续补真实多进程 E2E。
2. 真实 compose build/up 验证：Docker Desktop daemon 可用后执行 `docker compose up --build`，验证 postgres、redis、migrate、api、worker、frontend 的 health 和容器内任务提交。
3. 真实 embedding provider：接入 `text-embedding-3-small` 或可配置 provider，补超时、维度不匹配、重试和成本统计。
4. 真实 LLM report prompt：保留 `StructuredReport` schema 校验和 evidence refs 约束，不允许模型输出绕过 guardrails。
5. Playwright E2E：Day37 已覆盖 mock dev server 下的新建任务、查看进度、打开报告、查看 evidence chain 和 retry 入口；后续补真实 API / Docker / provider E2E。
6. GitHub branch protection：把 backend/frontend quality gates 配成 required checks。
7. Agent step replay：从任务级 retry 继续推进到基于最近 Observation 的 step-level resume。

这些优先级和 `day30-bug-summary.md` 对齐。后续开发应该从这里拆 Day31+ 或第二阶段 issue，而不是重新发散需求。

## 第二阶段建议拆分

### 1. Retry 前端闭环

目标：

- failed 任务详情页出现 retry 按钮。
- 点击后调用真实 retry API。
- 页面能显示 `waiting_retry`、重新 queued、recovery event 和最终状态。

新增测试：

- 前端契约测试：failed 状态才展示 retry。
- API client 测试：retry endpoint envelope 解析。
- Playwright E2E：Day37 已覆盖失败任务点击 retry 后的 mock 状态刷新；真实 Redis/Celery 环境仍需单独验收。

### 2. 真实 Compose 联调

目标：

- Docker Desktop daemon 可用后，真实执行 `docker compose up --build`。
- 容器内 PostgreSQL / Redis / migrate / api / worker / frontend 均健康。
- 通过 API 提交一个 fixture 任务，确认 worker 消费并写入数据库。

新增记录：

- `docker-compose-runbook.md` 增加真实运行结果。
- `development-log.md` 增加 Docker daemon 可用后的补验记录。
- `day30-bug-summary.md` 将该项从未解决缺口移到已补验。

### 3. 真实 Embedding Provider

目标：

- 在 `EmbeddingProvider` 抽象下接真实 provider。
- 保留 deterministic fake provider 给测试使用。
- 写入 token / cost / latency 指标入口。

新增测试：

- provider 超时重试。
- embedding 维度不匹配失败。
- provider 配置缺失时 fail fast。
- RAG store 不允许写入错误维度向量。

### 4. 真实 LLM Report Prompt

目标：

- 接真实报告 prompt。
- LLM 输出必须通过 `StructuredReport` schema。
- 所有 section evidence refs 必须来自检索结果。
- parse/validation 失败进入 self-heal，不允许绕过 guardrails。

新增测试：

- 坏 JSON 自愈。
- 引用未知 evidence ref 失败。
- 证据不足时不生成强结论。
- prompt version 写入报告 metadata。

### 5. E2E 与分支保护

目标：

- Playwright 覆盖关键 UI 流程。
- GitHub branch protection 要求 backend/frontend checks 通过。
- PR 模板中的验证记录真正成为合并前检查项。

## 第三阶段方向

- 报告导出 PDF，以及真实浏览器下载文件内容校验。Markdown / JSON evidence package 已在 Day38 完成。
- Prompt 版本回放。
- 更完整的 LLMOps 面板。
- 多数据源适配。
- 独立 crawler worker 池。
- 独立 RAG / embedding worker 池。
- 历史报告对比和趋势图。
- 任务取消、暂停和恢复。

## Day 41-Day50：真实应用闭环优先级

Day 40 Phase 2 RC 后，下一阶段不要继续盲目堆 Agent 能力，而是先补真实应用闭环。目标是让用户可以把真实或半真实评论数据导入系统，得到带证据链的报告，并能回查到原始评论。

| 天数 | 主题 | 交付物 | 关联文档 |
| --- | --- | --- | --- |
| Day 41 | CSV/JSON 评论导入 SDD | 导入 schema、字段映射、错误报告、样例数据 | `data-model.md`、`api-contract.md` |
| Day 42 | 评论导入后端实现 | upload/import API、Pydantic 校验、去重、入库测试 | `testing-strategy.md` |
| Day 43 | 前端导入入口 | 中文上传页、导入预览、错误行展示 | `frontend-localization-contract.md` |
| Day 44 | 低风险真实站点适配器 | Shopify/public demo/Amazon 静态样例适配器之一 | `crawler-strategy.md` |
| Day 45 | 评论分析质量评估集 | query、expected evidence、recall/precision baseline | `rag-memory.md` |
| Day 46 | 真实 LLM evidence-bound 报告联调 | provider 配置、成本记录、JSON repair、evidence refs 校验 | `prompt-strategy.md` |
| Day 47 | 前端证据链报告增强 | 结论 -> 引用证据 -> 原始评论跳转 | `ui-console-spec.md` |
| Day 48 | 导入到报告的端到端回归 | CSV/JSON -> RAG -> report -> evidence chain 测试 | `testing-strategy.md` |
| Day 49 | 真实应用演示脚本 | 面向电商运营的 5-8 分钟演示材料 | `demo-script.md` |
| Day 50 | 第三阶段 RC 审计 | 指标、缺口、面试口径、main 合并判断 | `release-checklist.md` |

这十天的重点是“可用性”和“证据链可信度”，不是新增更多模型名词。任何真实 provider、真实站点或真实数据指标，都必须继续区分 mock、fixture、database_snapshot 和 real。

## 不建议过早做

- Kubernetes。
- Kafka。
- 复杂权限系统。
- 过多站点采集适配。
- 复杂多智能体自治。
- 复杂销量预测或广告优化。

这些能力会明显扩大项目范围，但对当前“评论洞察、证据链报告、长任务可追踪”的核心价值帮助有限。

## 判断是否值得做的标准

新增需求进入 backlog 前，至少回答：

- 是否能改善主链路稳定性？
- 是否能增强报告可信度或证据链可解释性？
- 是否能带来可展示的指标或面试材料？
- 是否能提升工程深度，而不是只增加 UI 或名词？
- 是否会明显拖慢当前阶段交付？
