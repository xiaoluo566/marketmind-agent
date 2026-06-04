# Day 14 - 评论切片、Embedding 与向量检索基础

## 当天目标

把 Day 9 已入库的原始评论推进成可检索的长期记忆基础：评论先经过清洗和切片，再生成 embedding，写入 `review_chunks`，最后提供一个 top_k 相似评论检索原型。

Day 14 的重点是打通 RAG 数据链路，不是做最终 Agent 检索工具。最终给 Agent 调用的 `search_reviews_tool` 放到 Day 15。

## 前置依赖

- Day 9：`reviews` 已经能从采集结果入库。
- Day 13：短期记忆已经明确不负责长期评论检索。
- Day 3：`review_chunks.embedding` 已经按 `vector(1536)` 建模。
- 阅读 `../supporting/rag-memory.md`、`../supporting/data-model.md`、`../supporting/model-and-data-decisions.md`。

## 设计边界

### Day 14 做什么

- 评论文本清洗。
- 评论文本切片。
- Embedding provider 抽象。
- 确定性 fake embedding provider，用于本地测试和服务不可用时的流程验证。
- `review_chunks` 幂等写入。
- Python 版 cosine similarity top_k 检索原型。
- 检索结果返回 `chunk_id`、`review_id`、`source_url`、`rating`、`similarity`。

### Day 14 不做什么

- 不直接调用线上 embedding API。
- 不把检索能力包装成 Agent tool。
- 不生成最终报告。
- 不做跨任务长期知识复用。
- 不替换 Day 13 的短期记忆。

真实 embedding API 接入后必须通过 `EmbeddingProvider` 接口，不允许把 provider 调用散落到 storage 层各处。

## 当天交付物

### 代码交付物

- `backend/app/rag/text.py`
  - `clean_review_text`
  - `split_review_text`
  - `ReviewTextChunk`
- `backend/app/rag/embeddings.py`
  - `EmbeddingProvider`
  - `DeterministicEmbeddingProvider`
- `backend/app/rag/review_index.py`
  - `SQLAlchemyReviewChunkStore`
  - `ReviewChunkIndexResult`
  - `ReviewSearchResult`
- `tests/test_review_rag_indexing.py`
  - 清洗测试
  - 切片测试
  - fake embedding 稳定性测试
  - `review_chunks` 幂等入库测试
  - top_k 相似评论检索测试

## 实施步骤

### 1. 评论清洗

清洗规则：

- 去除 HTML 标签。
- 去除 `script` / `style` 内容。
- 处理 HTML entity，例如 `&nbsp;`。
- 合并多余空白。
- 不随意改写用户原始语义。

### 2. 评论切片

第一版规则：

- 短评论直接作为一个 chunk。
- 长评论按句子边界切片。
- 如果单句超过上限，再做强制长度切分。
- 每个 chunk 保留 `review_id`、`task_id`、`chunk_index`。
- 默认 `max_chars=500`，与 `rag-memory.md` 的 300 - 600 字符范围保持一致。

### 3. Embedding Provider 抽象

定义 `EmbeddingProvider`：

```python
class EmbeddingProvider(Protocol):
    dimensions: int
    model_name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
```

第一版使用 `DeterministicEmbeddingProvider`：

- 不依赖网络。
- 输出固定维度向量。
- 同一文本多次生成结果一致。
- 适合自动化测试和本地演示流程。

真实 OpenAI-compatible embedding provider 后续接入时必须保持同一接口。

### 4. 写入 `review_chunks`

`SQLAlchemyReviewChunkStore.index_task_reviews`：

1. 校验 task 是否存在。
2. 查询该任务下所有 reviews。
3. 清洗并切片每条评论。
4. 批量生成 embedding。
5. 按 `review_id + task_id + chunk_index + embedding_model + embedding_dimensions` 做 service 层幂等 upsert。
6. 写入 `review_chunks`。

当前数据库字段已经是 `vector(1536)`，因此测试和 fake provider 入库也必须使用 1536 维。不能因为是 fake provider 就写 16 维向量，否则会违反 Day 3 冻结的字段约束。

### 5. 相似度检索原型

`SQLAlchemyReviewChunkStore.search_similar_reviews`：

1. 对 query 生成 embedding。
2. 读取当前任务下相同模型和维度的 chunks。
3. 第一版在 Python 中计算 cosine similarity。
4. 排序返回 top_k。
5. 每条结果带 `chunk_id`、`review_id`、`review_external_id`、`content`、`source_url`、`rating`、`similarity`。

后续 Day 15 可以把检索封装成 `search_reviews_tool`，再进一步切到 PostgreSQL pgvector 原生排序。

## 验收标准

- `uv run pytest tests\test_review_rag_indexing.py` 通过。
- `uv run pytest` 全量通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 仍为单 head。
- `npm run build` 通过，确认前端未被后端变更影响。

## 风险与回退

### 风险 1：fake embedding 被误认为真实语义能力

回避方式：

- 文档明确 fake provider 只用于流程验证和测试。
- 面试时不能说当前已经接入真实 embedding API。
- Day 15 前不要夸大召回质量。

### 风险 2：不同维度向量混写

回避方式：

- `SQLAlchemyReviewChunkStore` 初始化时固定 `embedding_model` 和 `embedding_dimensions`。
- provider 维度不匹配时直接抛错。
- `review_chunks` 记录 `embedding_model` 和 `embedding_dimensions`。

### 风险 3：切片丢来源

回避方式：

- chunk metadata 保留 `review_external_id`、`source_url`、`rating`、`source_type`。
- 检索结果直接返回 review 来源字段。

## 当天选择思考

今天优先做评论切片和 embedding 入库，是因为 Day 13 已经把当前任务的短期上下文控制住了，下一步必须把“长期评论证据”变成可检索资产。没有 `review_chunks`，后续 `search_reviews_tool` 和证据链报告都只能读取原始 reviews，无法在上千条评论中精准召回。

我选择先做 fake embedding provider，而不是直接接真实模型，是因为 Day 14 的核心是数据链路和持久化边界：清洗、切片、向量维度、幂等写入、检索结果格式。真实模型调用涉及网络、鉴权、成本和限流，适合在这条链路稳定后再接。

我选择第一版用 Python cosine 检索，而不是直接写 pgvector SQL，是因为本地测试使用 SQLite，先把检索输入输出和排序行为固定住。后续在 PostgreSQL 环境下再替换为 pgvector 原生 `<=>` 排序，不改变上层接口。

## 关联文档

- 上一天：`day-13.md`
- 下一天：`day-15.md`
- RAG：`../supporting/rag-memory.md`
- 数据模型：`../supporting/data-model.md`
- 模型决策：`../supporting/model-and-data-decisions.md`
- LLMOps：`../supporting/llmops-metrics.md`

## 建议提交

`feat: 实现 Day 14 评论切片与向量索引`
