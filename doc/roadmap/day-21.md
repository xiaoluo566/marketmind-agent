# Day 21 - 历史任务与历史报告真实接入

## 当天目标

Day 21 解决 Day 20 后仍然存在的“只能看当前任务、不能积累历史资产”的问题。

一个面向电商运营的 Agent 系统不能只像一次性脚本那样跑完就结束。运营人员需要回看过去跑过的任务、失败原因、生成过的报告，以及报告背后的证据链。因此今天的目标不是新增炫技功能，而是把任务和报告从“单次执行页面”升级成“可沉淀、可回放、可继续分析”的历史记录系统。

当天目标分成三层：

1. 后端补齐 `GET /api/tasks`，让历史任务从 PostgreSQL 查询出来，支持状态筛选、时间筛选和分页。
2. 后端补齐 `GET /api/reports` 与 `GET /api/reports/{report_id}`，让报告列表和详情页能消费真实报告数据。
3. 前端 `listTasks()`、`listReports()`、`getReport()` 在真实 API 模式下不再使用 mock fallback，而是映射后端返回的统一 envelope。
4. 阶段审计后补齐报告详情页的 evidence chain 真实接入，避免真实报告正文混用全局 mock evidence。

## 前置依赖

- `day-07.md` 已完成任务和事件 PostgreSQL 持久化。
- `day-16.md` 已完成结构化报告 schema、Markdown 渲染和 `reports` 入库。
- `day-17.md` 已完成报告证据链回查 API。
- `day-19.md` 已完成前端真实任务创建、状态查询和事件读取。
- `day-20.md` 已完成任务详情轮询和 Agent step 展示。
- `../supporting/api-contract.md` 记录当前 API 真实接入状态。
- `../supporting/ui-console-spec.md` 记录前端控制台页面职责。
- `../supporting/data-model.md` 记录 `tasks`、`reports`、`agent_steps` 等核心表结构。

## Day 20 复查结果

进入 Day 21 前先复查 Day 20：

- `GET /api/tasks/{task_id}/steps` 已实现。
- `TaskProgressPanel` 已接入任务状态、事件和 Agent steps 轮询。
- 后端 targeted 测试 `tests/test_task_steps_api.py` 与前端契约测试 `tests/test_frontend_task_progress_contract.py` 通过。
- 文档中发现 `ui-console-spec.md` 的 Day 19 fallback 口径仍写着 steps 未实现，已修正为“Day 19 未实现，Day 20 已补齐”。

复查结论：Day 20 主交付没有代码遗漏，可以进入 Day 21。

## 当天交付物

### 后端

- 新增 `TaskListData` schema。
- `TaskStatusStore` 协议新增 `list()` 历史查询能力。
- `InMemoryTaskStatusStore` 支持测试用历史列表查询。
- `SQLAlchemyTaskStatusStore` 支持按状态、创建时间、分页查询任务。
- `MirroredTaskStatusStore` 的历史查询优先读取 PostgreSQL，避免把 Redis TTL 数据当成长期历史。
- `RedisTaskStatusStore.list()` 明确返回不可用错误，避免误用实时缓存做历史记录。
- 新增 `GET /api/tasks`。
- 新增 `ReportSummaryData`、`ReportDetailData`、`ReportSectionData`、`ReportListData` schema。
- 新增 `GET /api/reports`。
- 新增 `GET /api/reports/{report_id}`。
- 报告详情把 `content_json.sections` 映射成前端 `sections`。
- 报告风险分从 `content_json.metadata.analysis_scorecard.overall_risk_score` 读取。
- 报告风险等级按分数映射为 `low`、`medium`、`high`、`critical`。
- 缺失报告统一返回 `REPORT_NOT_FOUND` envelope。
- 新增 `tests/test_history_api.py`。

### 前端

- `frontend/src/lib/api.ts` 新增 `BackendTaskList`。
- `listTasks()` 在真实 API 模式下调用 `GET /api/tasks`，并映射为 `Task[]`。
- `frontend/src/lib/api.ts` 新增 `BackendReportList`、`BackendReportSummary`、`BackendReportDetail`、`BackendReportSection`。
- `listReports()` 在真实 API 模式下调用 `GET /api/reports`。
- `getReport()` 在真实 API 模式下调用 `GET /api/reports/{report_id}`。
- `getReportEvidence()` 在真实 API 模式下调用 `GET /api/reports/{report_id}/evidence`。
- 新增 `mapBackendReport()` 和 `mapBackendReportDetail()`。
- 新增 `mapBackendEvidenceSource()`，把后端 evidence chain 映射成前端 `Evidence[]`。
- 新增 `normalizeRiskLevel()`，避免后端异常 risk level 破坏页面类型。
- 新增 `tests/test_frontend_history_contract.py`。

## API 设计

### `GET /api/tasks`

职责：历史任务列表。

Query 参数：

- `status`：可重复传入，例如 `?status=failed&status=completed`。
- `created_after`：只返回该时间之后创建的任务。
- `created_before`：只返回该时间之前创建的任务。
- `limit`：默认 50，最大 100。
- `offset`：默认 0。

返回数据：

```json
{
  "items": [],
  "limit": 50,
  "offset": 0,
  "total": 0
}
```

排序规则：

- 按 `created_at desc`。
- 同一时间按 `task_id desc` 做稳定排序。

设计选择：

- 历史查询以 PostgreSQL 为事实来源。
- Redis 继续承担实时状态缓存，不承担历史分页查询。
- 失败任务必须保留在列表里，不能因为失败而消失。

### `GET /api/reports`

职责：历史报告列表。

Query 参数：

- `status`：报告状态筛选，例如 `draft`、`insufficient_evidence`、`failed`。
- `task_status`：关联任务状态筛选，例如 `completed`、`failed`。
- `created_after`：报告创建时间下界。
- `created_before`：报告创建时间上界。
- `limit`：默认 50，最大 100。
- `offset`：默认 0。

返回数据：

```json
{
  "items": [
    {
      "report_id": "rpt_xxx",
      "task_id": "tsk_xxx",
      "task_status": "completed",
      "title": "Portable Espresso Maker Report",
      "summary": "Quality and support issues dominate negative reviews.",
      "status": "draft",
      "risk_level": "high",
      "risk_score": 76,
      "evidence_count": 2,
      "created_at": "2026-05-26T10:00:00Z",
      "updated_at": "2026-05-26T10:00:00Z",
      "schema_version": "report.v1"
    }
  ],
  "limit": 50,
  "offset": 0,
  "total": 1
}
```

### `GET /api/reports/{report_id}`

职责：报告详情。

返回内容在列表字段基础上增加：

- `sections`
- `content_markdown`
- `evidence_refs`

`sections` 映射规则：

- 后端优先读取 `content_json.sections[*].heading` 作为 `title`。
- 后端优先读取 `content_json.sections[*].claim` 作为 `body`。
- 后端优先读取 `content_json.sections[*].evidence_refs` 作为 `evidence_ids`。

注意：前端字段暂名仍为 `evidence_ids`，但当前真实后端返回的是 `chunk:xxx`、`step:xxx` 这类 evidence refs。后续接入证据详情页时需要把 `evidence_ids` 命名进一步统一为 `evidence_refs`。

## 实施步骤

### 1. 先写测试

新增 `tests/test_history_api.py`：

- 历史任务按创建时间倒序返回。
- 失败任务保留在历史列表中。
- 任务列表支持状态筛选。
- 任务列表支持时间筛选。
- 任务列表支持 `limit` 和 `offset`。
- 报告列表返回前端可消费的摘要字段。
- 报告详情返回 sections。
- 缺失报告返回 `REPORT_NOT_FOUND`。

新增 `tests/test_frontend_history_contract.py`：

- `listTasks()` 真实模式下使用 `request<BackendTaskList>("/api/tasks")`。
- `listReports()` 真实模式下使用 `request<BackendReportList>("/api/reports")`。
- `getReport()` 真实模式下使用 `request<BackendReportDetail>(...)`。
- 成功响应不再走 `safeRequest(..., mock)` fallback。

### 2. 补任务历史查询

实现位置：

- `backend/app/api/schemas/tasks.py`
- `backend/app/tasks/status_store.py`
- `backend/app/storage/task_stores.py`
- `backend/app/tasks/service.py`
- `backend/app/api/routes/tasks.py`

关键点：

- store 返回 `(items, total)`，route 组装 `TaskListData`。
- SQLAlchemy 查询先计算 total，再应用 limit/offset。
- mirrored store 历史查询优先使用 PostgreSQL。
- Redis list 明确不可用，不做含糊的 scan 实现。

### 3. 补报告列表和详情

实现位置：

- `backend/app/api/schemas/reports.py`
- `backend/app/api/routes/reports.py`

关键点：

- 报告列表 join `tasks`，返回 `task_status`。
- `evidence_count` 从 `reports.evidence_refs` 计算。
- `risk_score` 从 scorecard metadata 读取。
- `risk_level` 由分数确定。
- 详情页 sections 从 `content_json.sections` 映射，不重新解析 Markdown。

### 4. 前端真实接入

实现位置：

- `frontend/src/lib/api.ts`
- `frontend/src/app/reports/[reportId]/page.tsx`

关键点：

- mock 模式仍然可以用于离线看页面。
- 真实模式成功时不再吞掉错误后回退 mock。
- 报告详情接口失败时应暴露 `ApiClientError`，避免用户误以为报告存在。
- 报告详情页读取报告正文时，也读取该报告自己的 evidence chain。
- 报告详情页不再用全局 `/api/evidence` mock 数据拼接证据列表。

### 5. 阶段审计补充

Day 1-21 阶段审计时发现三个和 Day 21 强相关的问题，并已补齐：

- 报告详情页没有消费 `GET /api/reports/{report_id}/evidence`，已新增 `getReportEvidence(reportId)`。
- `public_url` 任务缺少协议和内网地址校验，已在 `TaskCreateRequest` 增加 SSRF 基础防护。
- `agent_step` evidence metadata 暴露完整 `tool_input` / `tool_output`，已改成只暴露 `tool_input_keys`、`tool_output_keys`、`error_code` 等摘要字段。

对应测试：

- `tests/test_frontend_history_contract.py::test_report_detail_uses_real_report_evidence_chain`
- `tests/test_tasks_api.py::test_create_task_rejects_unsafe_public_url_targets`
- `tests/test_report_evidence_chain.py::test_report_evidence_api_sanitizes_agent_step_metadata`

## 当天选择思考

今天优先做历史任务和历史报告，是因为前面几天已经打通了“创建任务、看进度、生成报告、回查证据”的单次链路。但真正的运营系统需要积累：用户要对比多次任务、回看失败原因、打开旧报告、复盘哪些品类风险更高。如果没有历史层，这个系统仍然像 demo；有了历史层，系统才开始像一个可以持续使用的工作台。

我选择让历史任务读取 PostgreSQL，而不是 Redis，是因为 Redis 在当前系统里是实时状态层，并且有 TTL。它适合任务详情页快速读当前状态，不适合做长期历史分页。如果历史列表依赖 Redis，任务过期后用户会看不到过去结果，直接违背“可追踪、可复盘”的项目定位。

我没有今天就做复杂权限，是因为当前项目仍处于本地单用户和简历 Demo 阶段，过早加入用户空间、项目空间、权限过滤会让 Day 21 的主线变得混乱。更合理的做法是先固定接口形状，后续在 `SQLAlchemyTaskStatusStore.list()` 和报告查询里追加 `user_id/project_id` 过滤。

我选择保留 `limit/offset/total`，而不是只返回数组，是因为历史页天然会增长。即使第一版页面还没有分页控件，API 也应该提前具备分页扩展口，避免后续前端和后端一起重构。

## 验收标准

- `uv run pytest tests\test_history_api.py` 通过。
- `uv run pytest tests\test_frontend_history_contract.py` 通过。
- `uv run pytest` 通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 正常。
- `cd frontend; npm run lint` 通过。
- `cd frontend; npm run build` 通过。
- `GET /api/tasks` 返回统一 envelope。
- `GET /api/tasks` 可查到失败任务。
- `GET /api/tasks` 支持状态筛选、时间筛选、分页。
- `GET /api/reports` 返回报告列表。
- `GET /api/reports/{report_id}` 返回可渲染 sections。
- `GET /api/reports/{report_id}/evidence` 已在报告详情页真实接入。
- `public_url` 拒绝 `file://`、localhost、内网、loopback、link-local 等不安全目标。
- Agent step evidence metadata 不暴露完整 tool input/output。
- 前端真实 API 模式下任务列表、报告列表、报告详情不再使用 mock fallback。

## 风险与回退

- 风险：历史查询误用 Redis TTL 数据。
  - 回退：mirrored store 历史查询优先 PostgreSQL，Redis list 明确不可用。
- 风险：报告 `content_json` 结构不完整，详情页 sections 为空。
  - 回退：接口返回空 sections，前端仍可展示标题、摘要、风险分和 Markdown；后续补报告生成质量。
- 风险：offset 分页在大量数据时性能不足。
  - 回退：当前 Day 21 数据量小，先保留 offset；后续可升级 cursor pagination。
- 风险：前端取消 success fallback 后，后端未启动时页面会报错。
  - 回退：本地开发可显式设置 `NEXT_PUBLIC_USE_MOCKS=true`，真实模式下不应该掩盖 API 错误。

## 遗留问题

- `POST /api/tasks/{task_id}/retry` 尚未实现。
- `GET /api/evidence` 仍未实现，证据总览页继续 mock fallback。
- 前端报告 section 字段仍叫 `evidence_ids`，真实后端实际返回 evidence refs，后续需要统一命名。
- 历史列表页面还没有 UI 筛选控件，目前筛选能力先落在 API 层。

## 关联文档

- 上一天：`day-20.md`
- 下一天：`day-22.md`
- 控制台：`../supporting/ui-console-spec.md`
- API：`../supporting/api-contract.md`
- 数据模型：`../supporting/data-model.md`
- 可观测性：`../supporting/observability.md`
- 开发日志：`../supporting/development-log.md`
- 面试手册：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 实现 Day 21 历史任务与报告真实接入`
