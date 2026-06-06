# Day 16 - 报告 schema 与确定性报告生成骨架

## 当天目标

把 Day 15 的 `search_reviews_tool` evidence chunks 转成可校验、可入库、可展示的结构化报告。

Day 16 不追求“文案漂亮”，也不接真实 LLM 报告生成。今天先把报告边界打牢：报告必须有 schema，章节结论必须绑定 evidence refs，召回为空时必须写“证据不足”，报告 JSON 和 Markdown 必须同时可保存到 `reports` 表。

## 前置依赖

- Day 12：`StructuredOutputGuardrail` 已经能处理结构化输出和 self-heal。
- Day 14：评论清洗、切片、embedding 和 review chunk 入库已完成。
- Day 15：`search_reviews_tool` 已经返回 `results`、`evidence_refs` 和 `no_results_reason`。
- 支撑文档：
  - `../supporting/prompt-strategy.md`
  - `../supporting/data-contract-examples.md`
  - `../supporting/data-model.md`
  - `../supporting/testing-strategy.md`

## 设计边界

### Day 16 做什么

- 新增 `backend/app/reporting/` 报告模块。
- 定义 `StructuredReport` Pydantic schema。
- 定义 `ReportFinding` 章节 schema。
- 定义 `ReportGenerationInput` 和 `EvidenceSnippet`。
- 实现第一版 `StructuredReportGenerator`。
- 实现 `StructuredReport.to_markdown()`。
- 实现 `SQLAlchemyReportStore.save_report()`。
- 使用现有 `reports` 表保存：
  - `title`
  - `status`
  - `summary`
  - `content_json`
  - `content_markdown`
  - `evidence_refs`
  - `schema_version`
- 新增 `tests/test_report_generation.py`。

### Day 16 不做什么

- 不接真实大模型报告 provider。
- 不把报告生成接入完整 worker 流程。
- 不做 PDF 导出。
- 不做机会点评分算法。
- 不新增数据库迁移，因为 Day 3 已经预留 `reports` 表。
- 不把 query 当成事实来源。

## 核心模块

### `backend/app/reporting/schemas.py`

负责报告结构约束。

关键 schema：

- `ReportFinding`
  - `section_id`
  - `heading`
  - `claim`
  - `evidence_refs`
  - `severity`
  - `recommendation`
  - `metadata`
- `StructuredReport`
  - `task_id`
  - `title`
  - `summary`
  - `sections`
  - `evidence_refs`
  - `status`
  - `schema_version`
  - `metadata`

关键校验：

- 每个章节的 `evidence_refs` 必须存在于报告顶层 `evidence_refs`。
- 未召回证据时，章节可以为空 evidence refs，但报告状态必须是 `insufficient_evidence`。
- `schema_version` 当前固定为 `report.v1`。

### `backend/app/reporting/generator.py`

负责第一版确定性报告生成。

输入：

- `task_id`
- `product_name`
- `observations`
- `evidence_snippets`
- `requested_focus`

输出：

- `StructuredReport`

当前生成逻辑：

1. 对 evidence snippets 按 `evidence_ref` 去重。
2. 按 `similarity` 从高到低排序。
3. 如果没有 evidence snippets：
   - `status = insufficient_evidence`
   - 只输出证据状态章节
   - 明确写“证据不足”
   - 不生成任何 evidence ref
4. 如果存在 evidence snippets：
   - `status = draft`
   - 输出用户痛点、风险判断、机会判断三个章节
   - 每个章节必须引用已有 evidence refs
   - 把原始 evidence snippets 放入 metadata，供 Markdown 和后续前端展示

为什么先做确定性生成：

- Day 16 的重点是报告数据结构和证据引用，不是 prompt 创作。
- 确定性生成更容易测试，不会因为模型输出随机导致回归不稳定。
- 后续接 LLM 时，只需要让 LLM 输出同一个 `StructuredReport` schema，并继续通过 Pydantic 校验。

### `backend/app/reporting/stores.py`

负责报告入库。

`SQLAlchemyReportStore.save_report()` 做三件事：

1. 确认 `task_id` 存在。
2. 把 `StructuredReport` 写入 `reports.content_json`。
3. 把 `StructuredReport.to_markdown()` 写入 `reports.content_markdown`。

当前第一版每次保存生成一条新报告记录。后续如果要支持“同一任务报告重生成”，可以在 Day 21 历史报告模块里加版本号和 latest 标记。

## 报告状态

| 状态 | 含义 |
| --- | --- |
| `draft` | 已有可引用证据，报告可供前端预览 |
| `insufficient_evidence` | 没有足够 evidence refs，不能下确定结论 |
| `failed` | 预留给后续 LLM 生成或入库失败 |

## 证据引用规则

报告必须遵守：

- 章节结论只能引用顶层 `evidence_refs` 中存在的 ID。
- `evidence_ref` 第一版格式为 `chunk:{chunk_id}`。
- 不能引用没有被 `search_reviews_tool` 召回的评论。
- 不能把 `query`、`requested_focus` 或模型常识写成事实证据。
- 召回为空时，必须输出“证据不足”，不能输出风险结论。

## TDD 测试设计

新增 `tests/test_report_generation.py`，覆盖：

1. `StructuredReport` 拒绝未知 evidence ref。
2. 没有 evidence snippets 时，生成 `insufficient_evidence` 报告。
3. 有 evidence snippets 时，报告章节绑定已有 evidence refs，并能渲染 Markdown。
4. `SQLAlchemyReportStore` 能把 JSON、Markdown、evidence refs 和 schema version 写入 `reports` 表。

## 验收标准

- `uv run pytest tests\test_report_generation.py` 通过。
- `uv run pytest tests\test_report_generation.py tests\test_search_reviews_tool.py tests\test_review_rag_indexing.py` 通过。
- `uv run pytest` 全量通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 仍然只有 `0002_task_queue_id (head)`。
- `cd frontend; npm run build` 通过。
- `doc/supporting/development-log.md` 和 `doc/supporting/interview-defense-dossier.md` 已更新。

## 风险与回退

### 风险 1：报告看起来像最终商业结论

规避方式：

- Day 16 报告状态仍是 `draft`。
- 文档明确当前是“确定性报告骨架”，不是完整 LLM 报告。
- Opportunity 章节只写“后续需要评分”，不直接给爆款结论。

### 风险 2：证据引用漂移

规避方式：

- `StructuredReport` 做 schema 级校验。
- 章节引用未知 evidence ref 直接 `ValidationError`。
- 测试覆盖未知 evidence ref。

### 风险 3：无证据时模型编造

规避方式：

- 生成器无 evidence snippets 时只生成 `insufficient_evidence`。
- Markdown 中也写证据不足。
- Day 17 继续补证据链引用和前端展示。

## 当天选择思考

今天我没有直接把报告生成接到 LLM，是因为项目现在最需要的是“可信报告结构”，不是更会写文案的模型。只要报告 schema 不稳定，后面无论接什么模型都会有两个问题：第一，前端不知道怎么展示；第二，面试时无法解释报告结论怎么追溯证据。

我选择把证据引用校验放在 Pydantic schema 里，而不是只写在 prompt 里，是因为 prompt 约束不能保证每次都生效。程序级校验可以让非法报告在入库前失败，这比事后人工检查更符合工程化要求。

我选择复用 Day 3 预留的 `reports` 表，而不是新增迁移，是因为现有字段已经覆盖 Day 16 的需要。今天新增的是报告业务模块，不是数据库形态变化。这样也能验证前期建模不是“为了画架构图”，而是真的能承接后续功能。

## 关联文档

- 上一天：`day-15.md`
- 下一天：`day-17.md`
- 数据契约：`../supporting/data-contract-examples.md`
- Prompt：`../supporting/prompt-strategy.md`
- 数据模型：`../supporting/data-model.md`
- 测试策略：`../supporting/testing-strategy.md`
- 面试文档：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 实现 Day 16 结构化报告生成`
