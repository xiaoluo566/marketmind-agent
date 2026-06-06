# Day 15 - `search_reviews_tool` 差评语义搜索工具

## 当天目标

为 Agent 提供 `search_reviews_tool`，让它能围绕“退货”“质量差”“物流慢”“售后差”等问题主动检索 Day 14 已索引的评论证据，而不是让模型凭空总结。

Day 15 的核心是工具契约：输入要可控，输出要能直接进入报告证据链，召回为空时必须明确告诉 Agent “证据不足”，不能编造结论。

## 前置依赖

- Day 14：`reviews -> review_chunks -> top_k search` 已跑通。
- Day 10：`ToolRegistry` / `ToolExecutor` 已存在。
- Day 11：Agent step 可以记录工具调用。
- 阅读 `../supporting/rag-memory.md`、`../supporting/agent-state-machine.md`、`../supporting/data-contract-examples.md`。

## 设计边界

### Day 15 做什么

- 新增 `search_reviews_tool`。
- 定义检索输入 schema。
- 定义证据 chunk 输出 schema。
- 支持 `top_k`、`min_similarity` 和基础 filter。
- 返回 `chunk_id`、`review_id`、`review_external_id`、`content`、`rating`、`source_url`、`similarity`。
- 返回 `evidence_refs`，格式为 `chunk:{chunk_id}`。
- 召回为空时返回 `no_results_reason`，而不是让 Agent 自己脑补。
- 工具通过依赖注入注册到 `ToolRegistry`，避免默认 registry 强依赖数据库。

### Day 15 不做什么

- 不接真实 embedding API。
- 不直接写最终报告。
- 不做 pgvector 原生 SQL 排序。
- 不把所有 review chunks 塞给模型。
- 不把低相似度结果强行当证据。

## 当天交付物

### 代码交付物

- `backend/app/agent/tools/builtin.py`
  - `SearchReviewsFilter`
  - `SearchReviewsToolInput`
  - `ReviewEvidenceChunk`
  - `SearchReviewsToolOutput`
  - `build_search_reviews_tool_spec`
  - `run_search_reviews_tool`
- `tests/test_search_reviews_tool.py`
  - 工具依赖注入注册测试。
  - 召回证据 chunk 测试。
  - 召回为空不编造证据测试。

## 输入 schema

```json
{
  "task_id": "tsk_01HXYZ",
  "query": "return support",
  "top_k": 5,
  "min_similarity": 0.2,
  "filters": {
    "rating_lte": 2.0,
    "rating_gte": null,
    "source_type": "crawler"
  }
}
```

字段说明：

- `task_id`：可选；不传时使用工具上下文中的 `context.task_id`。
- `query`：必填，至少 1 个字符。
- `top_k`：默认 5，范围 1 - 20，避免撑爆上下文。
- `min_similarity`：默认 0，范围 0 - 1。
- `filters.rating_lte`：只保留低于等于该评分的评论。
- `filters.rating_gte`：只保留高于等于该评分的评论。
- `filters.source_type`：按评论来源过滤。

## 输出 schema

```json
{
  "query": "return support",
  "task_id": "tsk_01HXYZ",
  "results": [
    {
      "chunk_id": "chk_01HXYZ",
      "review_id": "rev_01HREVIEW",
      "review_external_id": "rev-return",
      "content": "The pump failed after three days. Return request and support were ignored.",
      "similarity": 0.82,
      "source_url": "https://example.com/product/espresso#rev-return",
      "rating": 1.0,
      "evidence_ref": "chunk:chk_01HXYZ",
      "metadata": {
        "source_type": "crawler"
      }
    }
  ],
  "evidence_refs": ["chunk:chk_01HXYZ"],
  "no_results_reason": null,
  "metadata": {
    "top_k": 5,
    "min_similarity": 0.2,
    "embedding_model": "fake-embedding-v1",
    "embedding_dimensions": 1536
  }
}
```

召回为空时：

```json
{
  "results": [],
  "evidence_refs": [],
  "no_results_reason": "NO_REVIEW_CHUNKS_ABOVE_THRESHOLD"
}
```

## 实施步骤

### 1. 先写测试

覆盖：

1. 传入 review chunk store 和 embedding provider 后，registry 能注册 `search_reviews_tool`。
2. query 命中评论时，工具返回 evidence chunk。
3. `rating_lte` 过滤能保留差评。
4. 高 `min_similarity` 导致无结果时，返回空数组和 `no_results_reason`。

### 2. 增加工具 schema

工具输入输出必须用 Pydantic schema，不能直接返回裸 dict。

### 3. 依赖注入注册

`build_default_tool_registry` 增加可选参数：

- `review_chunk_store`
- `embedding_provider`

只有两者都传入时才注册 `search_reviews_tool`。这样默认 registry 仍然能在无数据库场景下用于 crawler 工具测试。

### 4. 调用 Day 14 检索

工具内部调用：

```text
SQLAlchemyReviewChunkStore.search_similar_reviews
```

然后在工具层做：

- `min_similarity` 过滤。
- rating filter。
- source_type filter。
- evidence ref 生成。
- 空结果降级。

### 5. 交给 Agent 的约束

Agent 后续拿到工具结果后：

- 如果 `results` 非空，可以基于 evidence chunk 生成分析。
- 如果 `results` 为空，必须输出“证据不足”或继续选择其他工具。
- 不允许把 `query` 当成事实。
- 不允许把低相似度结果强行写成结论。

## 验收标准

- `uv run pytest tests\test_search_reviews_tool.py` 通过。
- `uv run pytest tests\test_agent_tools.py tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py` 通过。
- `uv run pytest` 全量通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 仍为单 head。
- `npm run build` 通过。

## 风险与回退

### 风险 1：召回为空时模型编造

回避方式：

- 工具输出明确 `no_results_reason`。
- `evidence_refs` 为空。
- 后续报告 prompt 必须要求无 evidence refs 时标注证据不足。

### 风险 2：top_k 过大撑爆上下文

回避方式：

- schema 限制 `top_k <= 20`。
- 默认值为 5。
- Day 16 报告生成时只取最相关 evidence refs。

### 风险 3：默认 registry 依赖数据库

回避方式：

- `search_reviews_tool` 通过依赖注入注册。
- 默认不传 store/provider 时，只注册 `crawl_product_tool`。

## 当天选择思考

今天优先做 `search_reviews_tool`，是因为 Day 14 只是完成了 RAG 数据层。Agent 还不能主动使用这个能力。只有把检索封装成工具，ReAct 状态机后续才能把“我需要找退货证据”变成一次可追踪的 Action。

我选择把过滤、空结果降级和 evidence ref 生成放在工具层，而不是直接让模型处理 Day 14 的原始检索结果，是因为工具层更适合做确定性规则：top_k 限制、相似度阈值、评分过滤和证据引用格式。

我没有今天接 pgvector 原生 SQL，是因为 Day 15 的重点是 Agent 工具契约。只要工具输入输出稳定，后续把底层检索从 Python cosine 换成 pgvector SQL 不会影响 Agent。

## 关联文档

- 上一天：`day-14.md`
- 下一天：`day-16.md`
- 数据模型：`../supporting/data-model.md`
- RAG：`../supporting/rag-memory.md`
- 状态机：`../supporting/agent-state-machine.md`
- 报告演示：`../supporting/demo-script.md`

## 建议提交

`feat: 实现 Day 15 差评语义搜索工具`
