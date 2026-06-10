# Day 39 - LLMOps 运营指标面板

## 当天目标

Day39 的目标是把模型调用、结构化输出、Guardrails 自愈、RAG provider、retry/recovery 和任务耗时数据汇总成一个可解释的 LLMOps 指标面板。

这一天解决的问题不是“项目用了大模型”，而是“项目能不能说明大模型链路是否稳定、成本是否可信、失败是否可恢复、指标来源是否诚实”。因此 Day39 的重点是统一指标口径、明确数据来源，并在前端用中文展示关键运营指标。

## SDD 规格

用户故事：

- 作为项目开发者，我希望在控制台看到 LLMOps 指标汇总，这样我可以快速判断当前系统的任务成功率、模型调用量、结构化解析失败次数、自愈成功率和 retry 恢复效果。
- 作为面试讲述者，我希望每个指标都带有数据来源，这样我不会把 mock、fixture 或未持久化 provider 指标包装成真实生产数据。
- 作为后续优化者，我希望 LLMOps summary 有稳定 API 契约，这样 Day40 阶段验收和 Day41+ 真实应用闭环可以继续复用同一套指标口径。

功能需求：

- 新增 `GET /api/observability/llmops-summary`。
- API 返回统一 success envelope。
- API 至少返回 `summary_version`、`generated_at`、`data_freshness`、`data_sources`。
- API 从 `tasks` 汇总 `task_metrics`。
- API 从 `agent_runs` 汇总 `model_usage` 和 `guardrail_metrics`。
- API 从 `task_events` 和 `tasks.options.recovery` 汇总 `recovery_metrics`。
- provider metrics 当前必须明确返回 `not_persisted`。
- 前端首页必须展示中文 LLMOps 指标区域。
- 前端 mock 模式必须有 `llmopsSummary`，真实 API 模式请求 `/api/observability/llmops-summary`。

非目标：

- 不新增 metrics 表。
- 不估算真实 provider 成本。
- 不把 Day35 in-memory provider metrics 写成生产指标。
- 不做趋势图、日报聚合、时间窗口筛选。
- 不在 Day39 做 50 次真实任务复盘。

接口契约：

`GET /api/observability/llmops-summary`

核心字段：

- `task_metrics`：任务总数、完成数、失败数、成功率、失败率、平均耗时、数据来源。
- `model_usage`：Agent run 数、模型调用数、input/output/total tokens、已记录成本、成本来源、成本可信度。
- `guardrail_metrics`：结构化解析失败次数、自愈次数、自愈成功率。
- `recovery_metrics`：retry 请求、重新入队、recovery resumed、队列不可用、恢复成功数、恢复成功率。
- `provider_metrics`：当前只返回 `not_persisted` 和说明。
- `warnings`：必须包含“暂无真实 provider 成本数据”。

## 前置依赖

- `day-12.md`：Guardrails 和 self-heal 指标。
- `day-27.md`：fixture benchmark summary。
- `day-28.md`：retry 和 recovery。
- `day-35.md`：provider metrics baseline。
- `day-36.md`：真实 LLM prompt 和 fallback 指标口径。
- `../supporting/llmops-metrics.md`：指标定义。
- `../supporting/observability.md`：错误日志和 trace id。
- `../supporting/api-contract.md`：API 契约。

## 当天交付物

- LLMOps summary service。
- `GET /api/observability/llmops-summary` API。
- 前端 `LLMOpsSummary` 类型。
- 前端 mock `llmopsSummary`。
- 前端 `getLLMOpsSummary()` helper。
- 首页中文 LLMOps 指标区域。
- 后端 API 聚合测试。
- 前端源码契约测试。
- supporting 文档和面试文档回填。

## 实施步骤

1. 按 SDD 检查指标来源和非目标。
2. 先写 RED 测试：
   - `tests/test_llmops_summary.py`
   - `tests/test_frontend_llmops_contract.py`
3. 后端实现：
   - 查询 `tasks`。
   - 查询 `agent_runs`。
   - 查询 `task_events`。
   - 汇总 task/model/guardrail/recovery/provider 指标。
4. API 接入：
   - 在 observability router 新增 `/llmops-summary`。
   - 使用统一 `success_response`。
5. 前端实现：
   - 增加 `LLMOpsSummary` 类型。
   - mock 模式增加 `llmopsSummary`。
   - API client 增加 `getLLMOpsSummary()`。
   - 首页展示中文 LLMOps 指标和数据来源。
6. 文档回填：
   - `development-log.md`
   - `interview-defense-dossier.md`
   - `testing-strategy.md`
   - `llmops-metrics.md`
   - `api-contract.md`

## 测试计划

```powershell
uv run pytest tests\test_llmops_summary.py tests\test_frontend_llmops_contract.py
uv run pytest tests\test_day27_benchmarking.py tests\test_day28_recovery.py tests\test_rag_quality_metrics.py tests\test_llm_report_prompt_contract.py tests\test_report_export.py tests\test_observability.py
uv run pytest tests\test_phase2_day32_40_docs.py
uv run ruff check backend tests migrations
cd frontend
npm run lint
npm run build
npm run test:e2e
npm audit --audit-level=high
```

## 验收标准

- LLMOps 指标字段完整。
- `GET /api/observability/llmops-summary` 返回统一 success envelope。
- 空数据库返回 0 baseline，不抛异常。
- 任务成功率、失败率、平均耗时来自 `tasks`。
- 模型调用、token、已记录成本、结构化解析失败、自愈次数来自 `agent_runs`。
- retry/recovery 指标来自 `task_events` 和 `tasks.options.recovery`。
- 成本统计、失败率、自愈成功率、恢复成功率都有来源说明。
- provider metrics 当前明确标记 `not_persisted`。
- 前端显示中文指标名：`LLMOps 指标`、`数据来源`、`模型调用`、`Token 总量`、`自愈成功率`、`恢复成功率`。
- fake / fixture / mock / real provider 来源不混淆。
- 文档说明哪些指标能作为已验证工程能力，哪些还只是本地 baseline。

## 实际完成

后端完成：

- 新增 `backend/app/observability/llmops_summary.py`。
- 新增 `GET /api/observability/llmops-summary`。
- 从 `tasks` 汇总任务数量、完成数、失败数、成功率、失败率和平均耗时。
- 从 `agent_runs` 汇总模型调用数、input/output/total tokens、已记录成本、结构化解析失败次数和 self-heal 次数。
- 从 `task_events` 和 `tasks.options.recovery` 汇总 retry/recovery 指标。
- provider metrics 当前明确返回 `not_persisted`，不伪装成真实 provider 运营数据。
- 空数据库返回 0 baseline。

前端完成：

- `frontend/src/lib/types.ts` 新增 `LLMOpsSummary`。
- `frontend/src/lib/mock-data.ts` 新增 `llmopsSummary`。
- `frontend/src/lib/api.ts` 新增 `getLLMOpsSummary()`。
- `frontend/src/app/page.tsx` 首页新增中文 `LLMOps 指标` 区域。

测试完成：

- 新增 `tests/test_llmops_summary.py`。
- 新增 `tests/test_frontend_llmops_contract.py`。
- RED 阶段确认 API 404、前端类型/helper/mock/中文文案缺失。
- GREEN 阶段 Day39 目标测试通过。

## 当前验证结果

```powershell
uv run pytest tests\test_llmops_summary.py tests\test_frontend_llmops_contract.py
# 5 passed

uv run pytest tests\test_llmops_summary.py tests\test_frontend_llmops_contract.py tests\test_phase2_day32_40_docs.py tests\test_frontend_localization_contract.py
# 16 passed

uv run pytest tests\test_day27_benchmarking.py tests\test_day28_recovery.py tests\test_rag_quality_metrics.py tests\test_llm_report_prompt_contract.py tests\test_report_export.py tests\test_observability.py
# 27 passed

uv run ruff check backend tests migrations
# All checks passed

cd frontend
npm run lint
# passed

npm run build
# passed

npm run test:e2e
# 1 passed

npm audit --audit-level=high
# found 0 vulnerabilities
```

## 风险与回退

风险：

- 指标来源混杂导致误导。
- 成本统计没有真实 provider token 或账单数据。
- 面板看起来完整，但实际部分指标来自 mock。
- 指标计算分母为 0。
- 未来 provider metrics 持久化后字段可能需要扩展。

回退：

- 保留 `not_persisted` 和 warning。
- 没有真实成本时显示调用次数和 token 记录，不估算金额。
- 如果指标字段有争议，先保留 summary API，不进入简历数字。
- provider metrics 后续独立设计表结构，不破坏 Day39 summary。

## 文档同步清单

- `llmops-metrics.md`：更新指标定义、来源和可写入口径。
- `development-log.md`：记录 Day39 实际开发、RED/GREEN 和验证结果。
- `interview-defense-dossier.md`：补充“LLMOps 怎么做”和“如何避免假指标”的回答。
- `testing-strategy.md`：记录指标计算测试边界。
- `api-contract.md`：补充 `/api/observability/llmops-summary`。
- `resume-story.md`：只补工程能力，不写未验证真实运营数字。

## 面试讲法

可以这样讲：

> Day39 我把模型相关指标从散落的测试、日志和表字段里汇总成 LLMOps summary。它区分任务成功率、模型调用次数、结构化解析失败、自愈成功率、retry 恢复成功率和数据来源。重点不是把面板做得花，而是诚实区分 database、mock、fixture 和 real provider，避免把演示数据包装成线上数据。

如果被问“成本统计怎么保证真实”，回答：

> 只有真实 provider 返回 token 或计费信息并被持久化时，才能把它计为真实成本。fake provider、mock summary 和 fixture benchmark 只能作为开发 baseline，不能写成线上成本。我在 API 和前端都保留 `cost_source`、`cost_confidence` 和 warnings，用来避免指标误读。

如果被问“为什么不新增 metrics 表”，回答：

> Day39 是第一版指标汇总，现有 `tasks`、`agent_runs`、`task_events` 已经能支持核心口径。先做查询汇总可以降低 schema 变更风险。后续当真实 provider 调用和长期趋势分析稳定后，再把 provider metrics 和日报聚合拆成独立表。

## 建议提交

```text
feat: 增加 LLMOps 运营指标汇总
```
