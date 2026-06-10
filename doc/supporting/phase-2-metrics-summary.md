# 第二阶段指标汇总

## 文档定位

这份文档只记录 Phase 2 RC 中已经实际运行或有测试覆盖的指标。没有真实 provider、真实账单、真实线上用户任务的数据，不能在这里写成生产指标。

## 已验证命令

Day40 当前已验证：

```powershell
uv run pytest tests\test_day40_phase2_release_candidate.py
uv run pytest tests\test_frontend_localization_contract.py tests\test_frontend_llmops_contract.py
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config

cd frontend
npm run lint
npm run build
npm run test:e2e
npm audit --audit-level=high

uvx pip-audit
```

最新本地结果：

- `uv run pytest`：222 passed。
- `uv run pytest --cov=backend --cov-report=term-missing`：222 passed，backend coverage 90.58%。
- `uv run ruff check backend tests migrations`：All checks passed。
- `uv run alembic heads`：`0002_task_queue_id (head)`。
- `docker compose config`：passed。
- `npm run lint`：passed。
- `npm run build`：清理 ignored `.next` 后 passed。
- `npm run test:e2e`：1 passed。
- `npm audit --audit-level=high`：found 0 vulnerabilities。
- `uvx pip-audit`：No known vulnerabilities found。
- secret scan：只命中 `.env.example` 占位、compose 本地默认密码、测试假 key 和文档字段，没有发现真实密钥。

Day39 已验证：

```powershell
uv run pytest tests\test_llmops_summary.py tests\test_frontend_llmops_contract.py
uv run pytest tests\test_day27_benchmarking.py tests\test_day28_recovery.py tests\test_rag_quality_metrics.py tests\test_llm_report_prompt_contract.py tests\test_report_export.py tests\test_observability.py
npm run test:e2e
```

## 指标来源说明

| 指标 | 当前来源 | 能否写成真实线上指标 |
| --- | --- | --- |
| Day27 性能 | fixture benchmark | 不能，只能说明本地 fixture 基线 |
| Day35 RAG 质量 | fixture evaluation cases | 不能，只能说明评估方法已建立 |
| Day37 E2E | mock dev server | 不能，只能说明关键浏览器路径可回归 |
| Day39 LLMOps `database_snapshot` | 本地数据库表 `tasks`、`agent_runs`、`task_events` | 只能说明聚合口径，不代表线上生产数据 |
| 前端数据 | mock 或 API fallback | 不能写成真实运营数据 |
| provider metrics | `not_persisted` | 不能写真实 provider 成本或 latency |

## 不写真实线上成本

当前不写真实线上成本。原因：

- 没有真实 provider 账单数据。
- 没有长期持久化 provider latency / token / cost 采样。
- mock、fixture、database_snapshot 只适合演示工程口径，不适合当作生产运营数字。

后续只有在真实 provider 返回 token 或计费信息，并且写入数据库或指标表后，才能把成本指标写成可验证数据。

## 可用于简历的表达

可以写：

- 建立 LLMOps summary API，汇总任务成功率、模型调用、token 字段、guardrails 自愈和 retry/recovery 指标。
- 指标来源区分 database_snapshot、mock、fixture 和 not_persisted，避免把演示数据误写成生产数据。
- 前端提供中文 LLMOps 指标区，能展示数据来源和 warning。

不要写：

- “线上成本降低 xx%”。
- “真实 provider 调用 xx 次”。
- “RAG 真实召回率达到 xx%”。
- “生产环境已完成全链路 E2E”。
