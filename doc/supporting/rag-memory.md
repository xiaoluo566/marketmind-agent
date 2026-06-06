# 记忆与 RAG

## 目标

解决长评论、长上下文、长任务无法直接塞进模型上下文的问题。

## 分层

- 短期记忆：当前任务最近几轮上下文
- 中期记忆：当前项目的历史任务摘要
- 长期记忆：评论切片、报告、结论和证据向量

## Day 13 短期记忆实现

Day 13 已经新增 `backend/app/agent/memory.py`，把短期记忆从概念推进到代码。当前短期记忆由三部分组成：

- `AgentMemoryEntry`：一条可放进上下文的记忆，通常由 `agent_steps` 转换而来。
- `AgentMemorySnapshot`：当前任务的记忆快照，包含历史摘要、摘要证据 ID 和最近详细 entry。
- `AgentPromptContext`：真正交给 planner / prompt 使用的上下文视图。

当前默认策略：

- 最近 3 条 entry 保留详细内容。
- 更早 entry 压缩到 `summary`。
- 证据引用单独保存在 `summary_evidence_refs` 和 `recent_entries[].evidence_refs`。
- Redis key 使用 `marketmind:agent:memory:{task_id}`。
- Redis 只做短期缓存，PostgreSQL `agent_steps` 仍是断点恢复的事实来源。

第一版摘要是确定性摘要，不调用大模型。这样可以先保证上下文预算稳定，避免把 summary prompt、模型调用失败和业务记忆机制同时引入。后续如果把摘要改成 LLM summary，必须接 Day 12 的 Pydantic Guardrails，并继续保留证据 ID。

### 短期记忆和长期 RAG 的区别

| 项 | 短期记忆 | 长期 RAG |
| --- | --- | --- |
| 作用 | 控制当前任务上下文增长 | 从大量评论中召回证据 |
| 存储 | Redis snapshot + PostgreSQL step 恢复 | PostgreSQL + pgvector |
| 内容 | Thought、Action、Observation 摘要 | review chunk、embedding、metadata |
| 生命周期 | 当前任务执行期间为主 | 可跨任务复用 |
| 关键风险 | 摘要丢证据 ID | 召回不准或样本偏差 |

## 处理链路

1. 清洗原始评论
2. 切片
3. 生成 embedding
4. 存入 pgvector
5. 按语义检索召回
6. 再做摘要和归纳

## Embedding 冻结

第一版使用：

- 模型：`text-embedding-3-small`
- 维度：1536
- pgvector 字段：`vector(1536)`

不要在同一张向量表里混写不同模型或不同维度的向量。后续如果升级到 `text-embedding-3-large`，需要通过 `embedding_model`、`embedding_dimensions` 或新的索引版本区分。

## 清洗规则

- 去除 HTML 标签、脚本和无意义空白
- 保留用户原始语义，不随意改写
- 保留评分、时间、来源等 metadata
- 对重复评论做简单去重

## 切片策略

评论通常较短，可以按单条评论作为基本 chunk。长评论按 300 到 600 中文字符切片，保留 `review_id`、`chunk_index`、`rating`、`source_url`。

切片不能打断关键上下文，例如“刚买回来很好，但是用了三天就坏了”不能只保留前半句。

## Day 14 评论索引实现

Day 14 新增 `backend/app/rag/`，把评论长期记忆链路从文档推进到代码：

- `text.py`：评论清洗和切片。
- `embeddings.py`：embedding provider 抽象和确定性 fake provider。
- `review_index.py`：`review_chunks` 入库和相似度检索原型。

当前流程：

```text
reviews.content
  -> clean_review_text
  -> split_review_text
  -> EmbeddingProvider.embed_texts
  -> review_chunks
  -> search_similar_reviews top_k
```

第一版 `DeterministicEmbeddingProvider` 只用于本地测试和流程验证，不代表真实语义召回质量。真实 embedding provider 后续必须实现同一个接口。

### Day 14 入库约束

- `review_chunks.embedding` 仍然固定 `vector(1536)`。
- 即使是 fake embedding，写库时也必须输出 1536 维。
- `embedding_model` 和 `embedding_dimensions` 必须写入每条 chunk。
- provider 维度和 store 维度不一致时直接失败。
- service 层按 `review_id + task_id + chunk_index + embedding_model + embedding_dimensions` 做幂等 upsert。

### Day 14 检索原型

当前 `search_similar_reviews` 在 Python 中计算 cosine similarity，返回：

- `chunk_id`
- `review_id`
- `review_external_id`
- `content`
- `similarity`
- `source_url`
- `rating`
- `metadata`

Day 15 做 `search_reviews_tool` 时，可以复用这个 store 的输出契约。后续接真实 PostgreSQL 时，可以把 Python cosine 替换成 pgvector 原生排序，但不要改变工具返回字段。

## Day 15 Agent 检索工具

Day 15 新增 `search_reviews_tool`，把 Day 14 的检索能力包装成 Agent 工具。

工具输入：

- `query`
- `task_id`
- `top_k`
- `min_similarity`
- `filters.rating_lte`
- `filters.rating_gte`
- `filters.source_type`

工具输出：

- `results`
- `evidence_refs`
- `no_results_reason`
- `metadata`

每条 result 都必须携带：

- `chunk_id`
- `review_id`
- `review_external_id`
- `content`
- `similarity`
- `source_url`
- `rating`
- `evidence_ref`

`evidence_ref` 当前格式为 `chunk:{chunk_id}`。后续报告生成时只能引用这些 evidence refs，不能引用没有召回到的评论。

如果没有结果，工具必须返回：

```json
{
  "results": [],
  "evidence_refs": [],
  "no_results_reason": "NO_REVIEW_CHUNKS_ABOVE_THRESHOLD"
}
```

这条约束的目的不是让工具“看起来成功”，而是给 Agent 一个明确降级信号：证据不足时不要编造结论。

## 检索流程

1. Agent 提出检索意图
2. `search_reviews_tool` 把问题转成检索 query
3. pgvector 返回 top_k chunk
4. 系统按评分、时间、相似度做二次排序
5. 把结果摘要交给 Agent
6. 报告生成时引用 chunk ID

## 检索维度

- 质量问题
- 物流问题
- 包装问题
- 售后问题
- 价格问题
- 退货问题

## 约束

- 检索结果必须带来源
- 摘要必须保留证据链
- 不允许把没有证据的判断写成事实

## 召回质量检查

- 如果召回结果相似度太低，报告要标注“证据不足”
- 如果召回结果集中在少量用户，报告要标注样本偏差
- 如果正负评论冲突，报告要展示冲突而不是强行下结论

## 与其他文档关系

- 评论来源见 `crawler-strategy.md`
- 向量字段见 `data-model.md`
- 模型和数据源决策见 `model-and-data-decisions.md`
- 报告引用见 `demo-script.md` 和 `resume-story.md`
