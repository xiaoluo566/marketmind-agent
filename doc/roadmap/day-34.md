# Day 34 - 真实 embedding provider 接入设计

## 当天目标

Day 34 的目标是把当前 deterministic fake embedding provider 升级为可配置的真实 embedding provider 架构。重点是先把 provider 边界、配置、失败分类、fallback 和测试写清楚，再接真实模型。

这一天不追求一次性把所有 provider 做完，而是让 `EmbeddingProvider` 具备生产化接入能力：可以使用真实 OpenAI-compatible embedding，也可以在测试和离线演示时回退到 fake provider。

## 前置依赖

- `day-14.md`：评论切片、fake embedding、review chunk 入库和相似检索原型。
- `day-15.md`：`search_reviews_tool` 和 evidence chunk 输出。
- `../supporting/model-and-data-decisions.md`：基础模型和 embedding 模型选择。
- `../supporting/rag-memory.md`：RAG、短期记忆和评论检索策略。
- `../supporting/security-compliance.md`：API key 和外部模型调用安全边界。
- `../supporting/phase-2-practicality-plan.md`：真实 provider 是第二阶段数据可信度目标。

## 当天交付物

- 新增或重构 `EmbeddingProvider` 抽象。
- 新增真实 provider 配置项：
  - `EMBEDDING_PROVIDER`。
  - `EMBEDDING_MODEL`，默认建议继续使用 `text-embedding-3-small`，除非模型决策文档更新。
  - `EMBEDDING_DIMENSIONS`。
  - `EMBEDDING_API_BASE_URL`。
  - `EMBEDDING_API_KEY`。
- 保留 deterministic fake provider，作为测试和本地演示 fallback。
- provider fallback 策略：
  - 测试默认 fake provider。
  - 未配置 API key 时不调用真实 provider。
  - 真实 provider 失败时按配置决定 fail-fast 或 fallback。
- 新增错误分类：
  - `EMBEDDING_PROVIDER_UNCONFIGURED`。
  - `EMBEDDING_PROVIDER_TIMEOUT`。
  - `EMBEDDING_PROVIDER_RATE_LIMITED`。
  - `EMBEDDING_PROVIDER_BAD_RESPONSE`。
- 更新 RAG 入库流程，使 provider 可注入、可替换、可测试。

## 实施步骤

1. 先写测试：
   - `tests/test_embedding_provider_config.py`。
   - `tests/test_review_rag_indexing.py` 扩展 provider 注入场景。
   - 验证 fake provider 仍确定性输出。
   - 验证未配置真实 provider 时不会偷偷发网络请求。
2. 配置设计：
   - 在 `backend/app/core/config.py` 增加 provider 配置。
   - `.env.example` 补充变量，但不填真实 secret。
   - Docker Compose 只保留变量占位，不硬编码密钥。
3. Provider 抽象：
   - 保持 `EmbeddingProvider` 接口稳定。
   - 真实 provider 返回维度必须与配置一致。
   - bad response 要转成结构化错误。
4. RAG 入库接入：
   - review chunk 入库时使用 provider 注入。
   - fake provider 用于测试。
   - 真实 provider 留开关，不强制本地必须可用。
5. 文档同步：
   - 更新模型决策文档。
   - 更新安全文档，明确 API key 管理。

## 测试计划

```powershell
uv run pytest tests\test_review_rag_indexing.py
uv run pytest tests\test_search_reviews_tool.py
uv run pytest tests\test_config.py
uv run pytest tests\test_schema_validation_contracts.py
uv run ruff check backend tests migrations
```

如果新增真实 provider 的 HTTP client，需要 mock 外部请求，不允许测试真实扣费。

## 验收标准

- `EmbeddingProvider` 接口清晰。
- fake provider 仍然可用于测试和离线演示。
- 真实 provider 配置齐全，但不硬编码 secret。
- 未配置 API key 时不发真实请求。
- provider fallback 行为有测试覆盖。
- RAG 入库和 `search_reviews_tool` 不因 provider 抽象变化而破坏。
- 文档清楚说明当前默认 provider 和真实 provider 切换方式。
- `text-embedding-3-small` 的维度、成本和替换边界必须写入模型决策文档。

## 风险与回退

风险：

- 真实 provider 维度与 pgvector / 配置维度不一致。
- 测试误触发真实模型调用导致费用。
- provider fallback 掩盖真实生产错误。
- 不同 provider 的返回格式不一致。

回退：

- 如果真实 provider 不稳定，保持 fake provider 为默认测试路径。
- 如果维度不一致，先 fail-fast，不自动截断向量。
- 如果外部 provider 报错，先记录错误分类，不写入半成品 embedding。

## 文档同步清单

- `model-and-data-decisions.md`：记录真实 embedding 模型选择和默认 fake provider 边界。
- `rag-memory.md`：记录 provider 注入和 fallback 策略。
- `security-compliance.md`：记录 API key 管理和不提交密钥。
- `development-log.md`：记录 Day 34 实际接入和验证结果。
- `interview-defense-dossier.md`：补充“为什么保留 fake provider”的讲法。
- `testing-strategy.md`：记录真实 provider mock 测试边界。

## 面试讲法

可以这样讲：

> Day 34 我把 embedding 从一个 deterministic fake provider，升级成可替换的 provider 架构。测试和本地演示仍走 fake provider，真实运行可以配置 OpenAI-compatible embedding。这样既避免测试依赖外部模型和费用，也让 RAG 链路具备真实接入路径。

如果被问“fake provider 会不会太玩具”，回答：

> fake provider 不是产品能力，而是测试隔离手段。真正的工程点是 provider 抽象、配置、失败分类、维度校验和 fallback 策略。有了这些，真实 provider 接入才不会污染测试和 CI。

## 建议提交

```text
feat: 增加可配置 embedding provider 架构
```
