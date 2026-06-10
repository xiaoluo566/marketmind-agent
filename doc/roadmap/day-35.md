# Day 35 - RAG 检索质量与 provider 指标

## 当天目标

Day 35 的目标是让 RAG 不只“能检索”，还要开始能衡量检索质量和 provider 成本。Day 34 解决 provider 接入边界，Day 35 解决“接入后怎么证明效果和成本可控”。

这一天要建立一个小型 RAG 评估集、记录召回质量、provider_metrics，并把这些指标接到 LLMOps 文档和后续面板设计中。

## SDD 规格

### 用户故事

**P1 - 开发者验证 RAG 召回没有退化**

作为开发者，我希望有一组固定的评论检索评估样例，这样后续修改 embedding provider、切片策略或检索逻辑时，可以知道“质量差、退货、物流慢、客服差、续航短”这些业务 query 是否还能召回预期证据。

验收标准：

- 至少 5 个中文业务 query。
- 每个 query 都有 expected review external id。
- 评估结果输出命中数、命中率、top similarity、latency 和 empty recall。
- 评估集使用 fixture，不依赖真实 provider 或外部网络。

**P1 - 工程侧能观测 provider 调用**

作为维护者，我希望 embedding provider 调用能留下结构化指标，这样后续接真实 provider 后能统计调用次数、输入规模、耗时、失败原因和 fallback 使用情况。

验收标准：

- provider metric 包含 provider name、model、operation、input_count、input_characters、latency_ms、success、error_code、fallback_used。
- 成功和失败调用都能记录。
- `EmbeddingProviderError.code` 能进入 metrics。
- 指标聚合能输出 success_count、failure_count、fallback_count、error_counts。

**P2 - 面试和演示中不夸大 fixture baseline**

作为项目作者，我希望文档明确说明 Day35 指标是 fixture baseline，不是线上准确率。

验收标准：

- `llmops-metrics.md`、`rag-memory.md`、`development-log.md`、`interview-defense-dossier.md` 和 `testing-strategy.md` 都说明当前指标边界。
- README 和面试材料不能把 fake provider 命中率写成真实线上效果。

### 非目标

- 不建 `provider_metrics` 数据表。
- 不接真实付费 embedding API。
- 不做 pgvector 原生 `<=>` 排序。
- 不做 Day36 的真实 LLM 报告 prompt。
- 不把 fixture 命中率写成真实业务准确率。

### 数据契约

评估 case：

```text
query
expected_review_external_ids
top_k
min_similarity
reason
```

provider metric：

```text
provider_name
model_name
operation
input_count
input_characters
latency_ms
success
error_code
fallback_used
```

## 前置依赖

- `day-14.md`：review chunk 入库和 top_k 检索。
- `day-15.md`：`search_reviews_tool`。
- `day-34.md`：真实 embedding provider 接入设计。
- `../supporting/llmops-metrics.md`：成本、失败率和自愈统计。
- `../supporting/rag-memory.md`：RAG 检索策略。
- `../supporting/phase-2-practicality-plan.md`：数据可信度提升目标。

## 当天交付物

- 新增 RAG 评估集文档或 fixture：
  - 查询：`质量差`、`退货`、`物流慢`、`客服差`、`续航短`。
  - 期望召回 evidence id / review chunk。
  - top_k、score、命中数量。
- 新增 provider_metrics 结构：
  - provider name。
  - model。
  - token / input 字符数。
  - latency_ms。
  - success / error code。
  - fallback_used。
- 新增指标汇总函数或测试 fixture。
- 更新 `llmops-metrics.md`，说明 embedding 侧指标和 report LLM 侧指标的区别。
- 明确当前指标是 fixture baseline，不包装成真实线上数据。
- 新增 `backend/app/rag/quality.py`：
  - `RAGEvaluationCase`
  - `RAGEvaluationResult`
  - `RAGEvaluationSummary`
  - `ProviderMetric`
  - `ProviderMetricsSummary`
  - `InstrumentedEmbeddingProvider`
  - `evaluate_rag_quality()`
  - `summarize_provider_metrics()`
- 新增 `tests/test_rag_quality_metrics.py`，覆盖 5 个中文 query 和 provider metrics 成功/失败/fallback。

## 实施步骤

1. 先写测试：
   - `tests/test_rag_quality_metrics.py`。
   - 验证评估集可读取。
   - 验证检索返回包含 expected evidence id。
   - 验证 provider_metrics 能记录成功和失败。
2. 建立 fixture：
   - 使用现有 demo reviews，不引入大文件。
   - 每个 query 至少有 1 个期望 evidence。
   - 记录 expected reason，方便面试解释。
3. 指标实现：
   - 如果当前没有持久化表，先用 dataclass / schema 和 summary 函数。
   - 不急着建表，除非 Day39 面板需要。
4. 检索质量输出：
   - 命中率。
   - 平均 top_k latency。
   - fallback 次数。
   - 空召回次数。
5. 文档同步：
   - 把指标解释写进 `llmops-metrics.md`。
   - 把当前 baseline 写进 `development-log.md`。

## 测试计划

```powershell
uv run pytest tests\test_rag_quality_metrics.py
uv run pytest tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py
uv run pytest tests\test_day27_benchmarking.py
uv run ruff check backend tests migrations
```

如果 Day34 已新增 provider 配置测试，也一起跑：

```powershell
uv run pytest tests\test_embedding_provider_config.py
```

## 实际完成

Day35 按 SDD + TDD 完成第一版 RAG 评估和 provider metrics 基线。

实现选择：

- 新增 `backend/app/rag/quality.py`，不修改 `search_reviews_tool` 输出契约。
- 使用 `InstrumentedEmbeddingProvider` 包装任何 `EmbeddingProvider`，把成功、失败、fallback、输入字符数和耗时记录为 metrics。
- 使用 dataclass/schema 风格的内存结构，不新增数据库表，避免 Day35 过早引入迁移负担。
- 评估集放在测试 fixture 内，用 5 条中文评论覆盖质量、退货、物流、客服、续航。
- `evaluate_rag_quality()` 统计每个 query 的 expected evidence 命中情况，输出 micro hit rate、case hit rate、empty recall 和 latency。
- `summarize_provider_metrics()` 聚合 provider metrics，作为 Day39 LLMOps 面板的输入雏形。

关键文件：

- `backend/app/rag/quality.py`
- `backend/app/rag/__init__.py`
- `tests/test_rag_quality_metrics.py`

## 当前验证结果

- RED：`uv run pytest tests\test_rag_quality_metrics.py` 最初失败，原因是 `app.rag.quality` 不存在。
- GREEN：`uv run pytest tests\test_rag_quality_metrics.py`：2 passed。
- RAG/provider 回归：`uv run pytest tests\test_rag_quality_metrics.py tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py tests\test_embedding_provider_config.py`：16 passed。
- `uv run pytest`：200 passed。
- `uv run pytest --cov=backend --cov-report=term-missing`：200 passed，backend coverage 90.31%。
- `uv run ruff check backend tests migrations`：All checks passed。
- `uv run alembic heads`：`0002_task_queue_id (head)`。
- `docker compose config`：通过。
- `cd frontend; npm run lint`：通过。
- `cd frontend; npm run build`：通过。
- `cd frontend; npm audit --audit-level=high`：found 0 vulnerabilities。
- `uvx pip-audit`：No known vulnerabilities found。
- `git diff --check`：无输出。

安全扫描说明：`rg` 只命中 `.env.example` 示例密码、文档占位 key、测试假 key 和源码路径名，没有发现真实密钥。
- Day35 + Phase2 文档契约回归：`uv run pytest tests\test_rag_quality_metrics.py tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py tests\test_embedding_provider_config.py tests\test_phase2_day32_40_docs.py`：19 passed。
- `uv run pytest`：200 passed。
- `uv run ruff check backend tests migrations`：All checks passed。
- `git diff --check`：无输出。

## 验收标准

- 至少 5 个中文业务查询有评估样例。
- 每个查询有 expected evidence 或 expected cluster。
- provider_metrics 能记录成功、失败、fallback 和 latency。
- RAG 质量指标输出不依赖真实外部 provider。
- 文档清楚标注这是 fixture baseline。
- 不把 fixture 命中率包装成线上准确率。

## 风险与回退

风险：

- 评估集太小，指标被误解为真实效果。
- fake provider 的相似度不代表真实 embedding 效果。
- 过早建表造成迁移负担。
- 指标字段和 Day39 LLMOps 面板需求不一致。

回退：

- 如果真实 provider 结果不稳定，先只记录 fake baseline 和真实 provider smoke。
- 如果指标字段设计不确定，先保留 schema 和 JSON summary，不急着建表。
- 如果召回质量差，记录原因，不临时调高分数。

## 文档同步清单

- `llmops-metrics.md`：新增 RAG/provider 指标章节。
- `rag-memory.md`：补充 RAG 评估集和召回质量说明。
- `development-log.md`：记录 Day 35 指标和 fixture baseline。
- `interview-defense-dossier.md`：补充“如何评估 RAG 效果”的回答。
- `testing-strategy.md`：记录 RAG 质量测试边界。

## 面试讲法

可以这样讲：

> Day 35 我没有只停留在“向量检索能跑”，而是加了一个小型 RAG 评估集和 provider_metrics。这样我可以说明每个查询期待召回哪些证据，provider 调用耗时多少、是否 fallback、有没有空召回。它不是线上准确率，但能证明我知道 RAG 需要评估和观测。

如果被问“为什么评估集这么小”，回答：

> 这是开发阶段 fixture baseline，用来防止回归和展示评估方法。真正上线前需要更大样本和人工标注，但在简历项目里，先建立评估框架比声称一个不可靠准确率更重要。

## 建议提交

```text
feat: 增加 RAG 检索质量与 provider 指标基线
```
