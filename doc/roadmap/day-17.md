# Day 17 - 证据链引用与来源回查

## 当天目标

在 Day 16 结构化报告基础上，把报告里的 `evidence_refs` 变成可回查的证据链。报告不只显示 `chunk:chk_xxx`，还要能追溯到原始 review chunk、评论、采集 artifact 或 Agent step。

Day 17 的核心不是重新生成报告，而是把“证据 ID”升级为“证据来源对象”：前端和面试展示时可以回答“这条结论来自哪条评论、哪个工具输出、哪个采集文件”。

## 前置依赖

- Day 15：`search_reviews_tool` 返回 `chunk:{chunk_id}`。
- Day 16：`StructuredReport` 已经约束章节只能引用顶层 `evidence_refs`。
- Day 16：`reports` 表已经保存 `content_json`、`content_markdown`、`evidence_refs` 和 `schema_version`。
- 支撑文档：
  - `../supporting/data-contract-examples.md`
  - `../supporting/api-contract.md`
  - `../supporting/data-model.md`
  - `../supporting/agent-state-machine.md`
  - `../supporting/testing-strategy.md`

## 设计边界

### Day 17 做什么

- 新增 `backend/app/reporting/evidence.py`。
- 定义 `EvidenceRef`、`EvidenceSource`、`EvidenceChain`。
- 实现 `parse_evidence_ref()`。
- 实现 `SQLAlchemyEvidenceChainStore.resolve()`。
- 支持回查：
  - `chunk:{chunk_id}` -> `review_chunks` + parent `review:{review_id}`
  - `review:{review_id}` -> `reviews` + parent `product:{product_id}`
  - `artifact:{artifact_id}` -> `artifacts`
  - `step:{step_id}` -> `agent_steps` + parent `agent_run:{run_id}`
- 实现 `attach_evidence_chain()`，把 evidence chain 放进 `StructuredReport.metadata`。
- `StructuredReport.to_markdown()` 增加“证据链回查”章节。
- 新增 `GET /api/reports/{report_id}/evidence`。
- 新增 `tests/test_report_evidence_chain.py`。

### Day 17 不做什么

- 不做前端真实报告详情页。
- 不做点击跳转 UI。
- 不做 report list API。
- 不做报告版本管理。
- 不新增关联表，因为 Day 17 的证据引用仍可通过 `reports.evidence_refs` 和现有业务表解析。
- 不把 evidence ref 和数据库主键强绑定到无法迁移的格式；当前格式是应用层引用协议。

## Evidence Ref 格式

第一版格式：

```text
{type}:{source_id}
```

支持类型：

| 类型 | 示例 | 回查表 | 说明 |
| --- | --- | --- | --- |
| `chunk` | `chunk:chk_return` | `review_chunks` | RAG 召回的评论切片 |
| `review` | `review:rev_return` | `reviews` | 原始评论 |
| `artifact` | `artifact:art_html` | `artifacts` | HTML、截图、上传文件等证据文件 |
| `step` | `step:stp_search` | `agent_steps` | 工具调用或 Agent 执行步骤 |

不支持的格式必须报错或返回 missing source，不能静默忽略。

## Evidence Source 输出

`EvidenceSource` 字段：

- `evidence_ref`
- `source_type`
- `source_id`
- `task_id`
- `available`
- `title`
- `content_preview`
- `source_url`
- `parent_refs`
- `missing_reason`
- `metadata`

设计重点：

- `available=false` 用于表达证据缺失。
- `missing_reason` 用于表达缺失原因，例如 `EVIDENCE_NOT_FOUND`。
- `parent_refs` 用于向上追溯，例如 `chunk:chk_return` 的 parent 是 `review:rev_return`。
- `content_preview` 用于前端先展示摘要，不把整段长评论塞进列表。

## API 契约

### `GET /api/reports/{report_id}/evidence`

职责：根据 `reports.evidence_refs` 回查结构化证据链。

成功响应：

```json
{
  "success": true,
  "data": {
    "report_id": "rpt_01HXYZ",
    "task_id": "tsk_01HXYZ",
    "evidence_refs": ["chunk:chk_return"],
    "missing_refs": [],
    "sources": [
      {
        "evidence_ref": "chunk:chk_return",
        "source_type": "review_chunk",
        "source_id": "chk_return",
        "task_id": "tsk_01HXYZ",
        "available": true,
        "title": "Review chunk #0",
        "content_preview": "The pump failed after three days...",
        "source_url": "https://example.com/product/espresso#return-001",
        "parent_refs": ["review:rev_return"],
        "missing_reason": null,
        "metadata": {
          "rating": 1.0,
          "source_type": "crawler"
        }
      }
    ]
  },
  "error": null,
  "message": "ok",
  "trace_id": "trc_01HXYZ"
}
```

报告不存在：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "REPORT_NOT_FOUND"
  }
}
```

## TDD 测试设计

新增 `tests/test_report_evidence_chain.py`，覆盖：

1. `parse_evidence_ref()` 支持已知类型。
2. malformed ref 和不支持类型会失败。
3. `SQLAlchemyEvidenceChainStore` 能回查 review chunk、artifact 和 agent step。
4. 缺失证据返回 `available=false` 和 `missing_reason`，不编造内容。
5. `attach_evidence_chain()` 返回新报告，不原地修改旧报告。
6. Markdown 输出包含“证据链回查”。
7. `GET /api/reports/{report_id}/evidence` 返回结构化 evidence chain。
8. 缺失 report 返回 `REPORT_NOT_FOUND`。

## 验收标准

- `uv run pytest tests\test_report_evidence_chain.py` 通过。
- `uv run pytest tests\test_report_evidence_chain.py tests\test_report_generation.py tests\test_search_reviews_tool.py tests\test_tasks_api.py` 通过。
- `uv run pytest` 全量通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 仍然只有 `0002_task_queue_id (head)`。
- `cd frontend; npm run build` 通过。
- `doc/supporting/development-log.md` 和 `doc/supporting/interview-defense-dossier.md` 已更新。

## 风险与回退

### 风险 1：证据引用只存在 Markdown 文本里

规避方式：

- Evidence chain 以 JSON 形式放入 `StructuredReport.metadata.evidence_chain`。
- API 直接返回结构化 sources。
- Markdown 只是展示层，不作为唯一事实来源。

### 风险 2：证据缺失被误认为可用

规避方式：

- 缺失 ref 返回 `available=false`。
- 同时写入 `missing_reason`。
- `missing_refs` 汇总缺失 ID。

### 风险 3：API 查询直接拼 SQL 或泄漏其他任务数据

规避方式：

- 回查统一走 SQLAlchemy model。
- 每种 evidence ref 都检查 `task_id`。
- 跨任务或不存在的记录统一视为 `EVIDENCE_NOT_FOUND`。

## 当天选择思考

今天优先做证据链回查，是因为 Day 16 只能保证“章节引用了合法 evidence ref”，但还不能让前端或面试官看到这个 evidence ref 背后到底是什么。报告可信度不只来自 schema，还来自“能不能回到原始评论和工具执行记录”。

我选择把证据链做成 `EvidenceChain` JSON，而不是只在 Markdown 里拼链接，是因为 Markdown 是展示格式，不能承担系统事实来源。结构化 JSON 可以给前端、API、测试和后续导出复用。

我选择暂时不新增 report_evidence_links 表，是因为现有 `reports.evidence_refs`、`review_chunks`、`reviews`、`artifacts`、`agent_steps` 已经能支撑第一版回查。等 Day 21 做历史报告、报告版本和列表查询时，再判断是否需要单独关联表。

## 关联文档

- 上一天：`day-16.md`
- 下一天：`day-18.md`
- API 契约：`../supporting/api-contract.md`
- 数据契约：`../supporting/data-contract-examples.md`
- 数据模型：`../supporting/data-model.md`
- 状态机：`../supporting/agent-state-machine.md`
- 测试策略：`../supporting/testing-strategy.md`
- 面试文档：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 实现 Day 17 报告证据链回查`
