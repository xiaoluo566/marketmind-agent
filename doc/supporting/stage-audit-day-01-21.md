# Day 1-21 阶段审计报告

## 审计目的

本次审计发生在准备把 `dev` 合并到 `main` 之前。目标不是继续推进 Day 22，而是确认 Day 1-21 的阶段产物是否已经达到“可以作为稳定演示版本”的最低标准。

审计重点：

- 工程化链路是否闭合。
- 后端已完成能力是否真实接入前端。
- 文档是否跟上代码状态。
- 安全边界是否和文档一致。
- 哪些欠缺属于当前必须修，哪些属于 Day 22 之后计划项。

## 总体结论

Day 1-21 的主体工程链路是成立的：

- FastAPI、Celery、Redis、PostgreSQL、SQLAlchemy、Playwright、Next.js 已经形成分层结构。
- 任务创建、状态查询、事件查询、Agent step 查询、历史任务、历史报告、报告详情、报告 evidence chain 都有真实接口或真实前端接入。
- RAG、报告和评分目前使用 deterministic / local baseline，适合作为工程骨架和测试基线。
- 全量测试、ruff、Alembic head、前端 lint/build 可以作为推主分支前的质量门禁。

推主分支前发现 4 个问题，其中 3 个属于必须修复，1 个属于文档入口过期。均已处理。

## 已修复问题

### 1. 报告详情页未接入 evidence chain

问题：

- 后端 Day 17 已实现 `GET /api/reports/{report_id}/evidence`。
- 前端 Day 21 已实现报告详情真实读取。
- 但报告详情页仍通过 `listEvidence()` 读取全局 evidence fallback。

影响：

- 报告正文是真实报告，证据列表却可能是 mock 或其他任务的证据。
- 这会破坏项目最核心的“证据链报告”可信度。

修复：

- 新增 `getReportEvidence(reportId)`。
- 报告详情页改为并行读取 `getReport(reportId)` 和 `getReportEvidence(reportId)`。
- 新增 `BackendReportEvidence`、`BackendEvidenceSource` 和 `mapBackendEvidenceSource()`。

验证：

- `tests/test_frontend_history_contract.py::test_report_detail_uses_real_report_evidence_chain`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`

### 2. `public_url` 缺少 SSRF 基础防护

问题：

- 安全文档要求 URL 必须校验协议和域名。
- `TaskCreateRequest` 之前只校验 `target` 非空，没有针对 `source_type=public_url` 做安全约束。

影响：

- 后续 crawler 可能被提交 `file://`、localhost、内网 IP、link-local 等目标。
- 这会让后端采集能力变成内网探测入口。

修复：

- `public_url` 只允许 `http` 和 `https`。
- 拒绝 localhost、`.local`、loopback、private、link-local、reserved、multicast、unspecified 地址。

验证：

- `tests/test_tasks_api.py::test_create_task_rejects_unsafe_public_url_targets`

### 3. Agent step evidence metadata 暴露完整工具输入输出

问题：

- Day 20 的任务详情 steps API 已经对 Agent step 做脱敏。
- 但 Day 17 的 evidence chain 对 `agent_step` source 返回完整 `tool_input` 和 `tool_output`。

影响：

- 报告详情接入 evidence chain 后，前端可能看到内部工具参数或后续敏感中间结果。
- 这和“只展示摘要，不暴露完整 thought / prompt / tool input”的边界不一致。

修复：

- `agent_step` evidence metadata 只返回：
  - `step_index`
  - `step_type`
  - `status`
  - `tool_name`
  - `tool_input_keys`
  - `tool_output_keys`
  - `error_code`
- 不再返回完整 `tool_input` 和 `tool_output`。

验证：

- `tests/test_report_evidence_chain.py::test_report_evidence_api_sanitizes_agent_step_metadata`

### 4. README 当前阶段过期

问题：

- README 仍写着项目处于“架构冻结 + 基础骨架”阶段。
- 这和 Day 21 后的实际工程状态不一致。

影响：

- 仓库入口会误导面试官或未来维护者。
- 主分支稳定版本的说明不可信。

修复：

- 更新 README 当前状态。
- 补充 Day 1-21 已完成能力。
- 补充验证命令。
- 明确尚未完成的后续能力。

## 当前仍保留的欠缺

以下欠缺不阻止推主分支，因为它们属于 Day 22 之后计划范围，且文档已明确标注：

- `POST /api/tasks/{task_id}/retry`：失败任务重试。
- `GET /api/evidence`：全局 evidence 检索 / 证据总览真实接口。
- 历史任务和历史报告前端筛选控件。
- 报告详情字段 `evidence_ids` 与真实 evidence refs 的命名统一。
- 真实 embedding provider。
- pgvector 原生相似度 SQL。
- 真实 LLM report prompt。
- Docker Compose 全链路一键启动。
- Playwright E2E。
- LLMOps 指标统计和 50 次任务复盘。

## 推 main 前质量门禁

本次审计已通过：

- `uv run pytest tests\test_tasks_api.py tests\test_report_evidence_chain.py tests\test_frontend_history_contract.py`：23 passed。
- `uv run ruff check backend tests migrations`：通过。
- `npm audit --audit-level=high`：0 vulnerabilities。
- `uvx pip-audit`：No known vulnerabilities found。
- `uv run pytest --cov=backend --cov-report=term-missing`：108 passed，backend coverage 91%。
- `git diff --check`：通过。

推 main 前最终完整门禁已通过：

```powershell
uv run pytest                                      # 108 passed
uv run ruff check backend tests migrations         # passed
uv run alembic heads                               # 0002_task_queue_id (head)
cd frontend
npm run lint                                      # passed
npm run build                                     # passed
```

建议推 main 前再检查：

```powershell
git status --short --branch
git log --oneline -5
git diff --check
```

## 面试表达

可以这样解释这次阶段审计：

> 我没有在 Day 21 后直接继续堆 Day 22，而是先做了一次阶段审计。审计发现报告详情证据链还没有真实联调、public URL 缺少基础 SSRF 防护、Agent step evidence metadata 暴露过多内部数据，以及 README 入口文档过期。修完这些再推 main，比继续加日志功能更符合工程化项目的节奏。

## 关联文档

- `development-log.md`
- `api-contract.md`
- `ui-console-spec.md`
- `security-compliance.md`
- `testing-strategy.md`
- `release-checklist.md`
