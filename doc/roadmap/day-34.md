# Day 34 - 真实 embedding provider 接入设计

## 当天目标

Day 34 的目标是把 Day 14 的 `DeterministicEmbeddingProvider` 从“测试用假实现”升级为“可替换、可配置、可验证”的 embedding provider 架构。今天不追求真实跑付费 embedding API，也不把 RAG 质量评估提前做完；重点是先把 provider 边界、配置项、错误分类、维度校验和测试隔离打牢。

这一天完成后，项目应该具备三种能力：

1. 本地测试和 CI 默认走 deterministic fake provider，不访问外部网络。
2. 真实运行时可以通过环境变量启用 OpenAI-compatible embedding provider。
3. 显式启用真实 provider 但缺少 API key、返回维度不一致、限流、超时或响应格式异常时，系统能给出结构化错误，而不是写入半成品向量。

## 前置依赖

- `day-14.md`：评论清洗、切片、fake embedding 和 review chunk 入库。
- `day-15.md`：`search_reviews_tool` 对 `EmbeddingProvider` 的依赖注入。
- `day-24.md`：主链路集成测试仍依赖 deterministic provider 保持稳定。
- `../supporting/model-and-data-decisions.md`：`text-embedding-3-small` 和 1536 维决策。
- `../supporting/rag-memory.md`：RAG 长期记忆、chunk、provider 注入和维度约束。
- `../supporting/security-compliance.md`：API key 只能通过环境变量注入。
- `../supporting/dev-workflow.md`：Day33+ 固定使用 `Spec Kit SDD -> TDD -> implementation -> verification-loop -> 文档回填`。

## SDD 规格

### 用户故事

**P1 - 本地开发者离线验证 RAG 链路**

作为开发者，我希望默认 embedding provider 不依赖外部 API，这样我在没有密钥、没有网络或 CI 环境中仍能稳定运行 RAG、报告和主链路测试。

验收标准：

- 默认 `Settings()` 中 `embedding_provider` 为 `fake`。
- `build_embedding_provider(Settings())` 返回 deterministic provider。
- 默认 provider 不发起网络请求。
- 现有 `tests/test_review_rag_indexing.py` 和 `tests/test_search_reviews_tool.py` 继续通过。

**P1 - 部署者显式启用真实 embedding**

作为部署者，我希望可以通过环境变量切换到 OpenAI-compatible embedding provider，并配置模型、维度、base URL、API key 和超时时间。

验收标准：

- `.env.example` 和 `docker-compose.yml` 声明 `EMBEDDING_PROVIDER`、`EMBEDDING_API_BASE_URL`、`EMBEDDING_API_KEY`、`EMBEDDING_REQUEST_TIMEOUT_SECONDS`、`EMBEDDING_PROVIDER_FALLBACK_ENABLED`。
- provider 请求体包含 `model`、`input` 和 `dimensions`。
- 响应向量数量必须和输入文本数量一致。
- 响应向量维度必须等于 `EMBEDDING_DIMENSIONS`。

**P2 - 外部 provider 失败可分类**

作为排障者，我希望 embedding provider 失败时能看到明确错误码，从而区分配置错误、超时、限流和响应格式异常。

验收标准：

- 缺少 API key 时抛出 `EMBEDDING_PROVIDER_UNCONFIGURED`。
- 超时时抛出 `EMBEDDING_PROVIDER_TIMEOUT`。
- HTTP 429 或显式 rate limit 时抛出 `EMBEDDING_PROVIDER_RATE_LIMITED`。
- 响应结构异常、维度不一致、非数值向量时抛出 `EMBEDDING_PROVIDER_BAD_RESPONSE`。

**P2 - fallback 策略必须显式**

作为维护者，我不希望生产环境悄悄把真实 provider 失败伪装成 fake embedding 成功。

验收标准：

- 默认 `EMBEDDING_PROVIDER_FALLBACK_ENABLED=false`。
- 默认 `EMBEDDING_PROVIDER=fake`，本地测试稳定。
- 如果显式配置 `EMBEDDING_PROVIDER=openai-compatible` 但没有 key，默认 fail-fast。
- 只有显式打开 fallback 时，factory 才允许回退到 deterministic provider，并且文档必须说明这不是可写成真实 RAG 效果的指标；这里的 `provider fallback` 只能是显式降级，不是默认行为。

### 非目标

- 今天不统计真实 embedding token 和成本。
- 今天不做真实 provider 质量评估集。
- 今天不改 `review_chunks.embedding` 的 `vector(1536)` 建模。
- 今天不替换 pgvector 原生排序，也不调整 `search_reviews_tool` 输出契约。
- 今天不把 API key 写入测试、文档示例或 Docker Compose 默认值。

### 接口契约

环境变量：

```env
EMBEDDING_PROVIDER=fake
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
EMBEDDING_API_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=
EMBEDDING_REQUEST_TIMEOUT_SECONDS=15
EMBEDDING_PROVIDER_FALLBACK_ENABLED=false
```

Python provider factory：

```python
provider = build_embedding_provider(settings)
vectors = provider.embed_texts(["质量差", "物流慢"])
```

错误码：

```text
EMBEDDING_PROVIDER_UNCONFIGURED
EMBEDDING_PROVIDER_TIMEOUT
EMBEDDING_PROVIDER_RATE_LIMITED
EMBEDDING_PROVIDER_BAD_RESPONSE
```

## 当天交付物

- `backend/app/core/config.py` 新增真实 provider 配置项。
- `backend/app/rag/embeddings.py` 新增：
  - `EmbeddingProviderError`
  - `OpenAICompatibleEmbeddingProvider`
  - `build_embedding_provider()`
  - provider 错误码常量
- `backend/app/rag/__init__.py` 导出 provider factory、真实 provider 和错误码。
- `.env.example` 和 `docker-compose.yml` 补齐 provider 环境变量。
- `tests/test_embedding_provider_config.py` 覆盖 Day34 provider 配置、解析和错误分类。
- `tests/test_config.py` 补充默认 provider 配置断言。
- supporting 文档同步更新模型决策、RAG、部署、安全、LLMOps、测试策略、开发日志和面试讲法。

## 实施步骤

1. 先写 `tests/test_embedding_provider_config.py`，让测试在缺少 provider 常量、factory 和真实 provider 类时失败。
2. 在 `Settings` 中增加 embedding provider 配置。
3. 在 `embeddings.py` 中实现真实 provider 和错误分类。
4. 保持 `DeterministicEmbeddingProvider` 不变，保证 Day14 / Day15 / Day24 回归稳定。
5. 更新 `.env.example` 和 `docker-compose.yml`，只写变量占位，不写真实密钥。
6. 更新文档并明确今天没有真实调用外部 embedding API。
7. 运行 targeted tests、full tests、lint、compose config、frontend build/audit 和安全扫描。

## 实际完成

Day34 按 SDD + TDD 完成。

实现选择：

- 默认 provider 设为 `fake`，因为本地测试、CI 和演示不能依赖外部模型服务。
- 显式选择 `openai-compatible` 但没有 API key 时 fail-fast，而不是静默 fallback。这样能避免生产环境误以为真实 embedding 生效。
- `OpenAICompatibleEmbeddingProvider` 使用标准库 `urllib` 实现真实 HTTP 请求，避免为了一个 provider 架构引入新的运行时依赖。
- provider 支持注入 `client`，测试中用 fake client 验证请求体、header、timeout 和响应解析，不触发真实网络。
- response 解析时强制校验数量、维度和数值类型，避免把坏向量写入 `review_chunks`。
- fallback 开关保留，但默认关闭。fallback 只适合本地演示或临时降级，不能作为真实 RAG 指标来源。

关键文件：

- `backend/app/rag/embeddings.py`
- `backend/app/rag/__init__.py`
- `backend/app/core/config.py`
- `tests/test_embedding_provider_config.py`
- `tests/test_config.py`
- `.env.example`
- `docker-compose.yml`

## 测试计划

```powershell
uv run pytest tests\test_embedding_provider_config.py
uv run pytest tests\test_embedding_provider_config.py tests\test_config.py tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
git diff --check
```

## 当前验证结果

已完成：

- `uv run pytest tests\test_embedding_provider_config.py`：6 passed。
- `uv run pytest tests\test_embedding_provider_config.py tests\test_config.py tests\test_review_rag_indexing.py tests\test_search_reviews_tool.py`：16 passed。
- `uv run pytest`：198 passed。
- `uv run pytest --cov=backend --cov-report=term-missing`：198 passed，backend coverage 90.13%。
- `uv run ruff check backend tests migrations`：All checks passed。
- `uv run alembic heads`：`0002_task_queue_id (head)`。
- `docker compose config`：通过。
- `cd frontend; npm run lint`：通过。
- `cd frontend; npm run build`：通过。
- `cd frontend; npm audit --audit-level=high`：found 0 vulnerabilities。
- `uvx pip-audit`：No known vulnerabilities found。
- `git diff --check`：无输出。

安全扫描说明：`rg` 只命中 `.env.example` 示例密码、文档占位 key、测试假 key 和源码路径名，没有发现真实密钥。

回归修复说明：全量测试暴露出 `SQLAlchemyTaskEventStore.list_for_task()` 在多条事件时间戳相同时可能按随机 event id 打乱顺序。Day34 顺手修复为“只有同一任务同一 `created_at` 时推进 1 微秒作为 tie-break”，不改变已有按事件时间排序的语义。

如 Docker daemon 不可用，只声明 `docker compose config`，不声明真实容器 build/up。

## 验收标准

- `EmbeddingProvider` 接口保持稳定。
- fake provider 仍可用于测试和离线演示。
- 真实 provider 配置完整，但没有硬编码 secret。
- 未配置 API key 时不发真实请求。
- 显式真实 provider 缺 key 默认 fail-fast。
- provider bad response、rate limit 和 timeout 有结构化错误码。
- RAG 入库和 `search_reviews_tool` 不因 provider 抽象变化而破坏。
- 文档清楚说明当前是 provider 架构完成，不等于真实 embedding 质量已经验证。

## 风险与回退

风险：

- 真实 provider 输出维度和 `review_chunks.embedding vector(1536)` 不一致。
- 测试误触发真实模型调用，产生费用。
- fallback 掩盖生产配置错误。
- 真实 provider 响应格式和 OpenAI-compatible 假设不完全一致。

回退：

- 关闭 `EMBEDDING_PROVIDER=openai-compatible`，改回 `EMBEDDING_PROVIDER=fake`。
- 保留 `DeterministicEmbeddingProvider`，保证本地回归不受外部服务影响。
- 维度不一致时 fail-fast，不自动截断或 padding。
- 真实 provider 错误不写入半成品 embedding。

## 文档同步清单

- `model-and-data-decisions.md`：记录 Day34 provider 切换、默认 fake 和真实 provider 启用方式。
- `rag-memory.md`：记录 `build_embedding_provider()`、错误分类和 provider 维度约束。
- `security-compliance.md`：记录 API key 环境变量和日志安全边界。
- `dev-environment.md` / `deployment.md`：补充 Day34 环境变量。
- `llmops-metrics.md`：说明 provider 错误码和真实 token/cost 仍未统计。
- `development-log.md`：记录 Day34 实际开发、验证和取舍。
- `interview-defense-dossier.md`：补充“为什么保留 fake provider”和“为什么缺 key fail-fast”。
- `testing-strategy.md`：记录 Day34 provider 契约测试边界。
- `README.md`：更新已完成/未完成边界。

## 面试讲法

可以这样说：

> Day34 我把 embedding 从 deterministic fake provider 升级成可配置 provider 架构。默认 fake 是为了本地测试和 CI 稳定，不代表真实语义效果；真实运行可以通过 `EMBEDDING_PROVIDER=openai-compatible`、API base URL、API key 和维度配置切换。显式启用真实 provider 但缺 key 时会 fail-fast，避免生产环境把 fake 结果误当成真实 RAG 效果。

如果被问“fake provider 会不会太玩具”，回答：

> fake provider 是测试隔离手段，不是产品能力。真正的工程点是 provider 抽象、配置边界、维度校验、错误分类和测试不触网。没有这些，直接把真实 API 写进 RAG 代码会让 CI 不稳定，也很难复现问题。

如果被问“为什么不默认 fallback”，回答：

> 因为 fallback 会掩盖生产配置错误。默认 fake 适合开发；一旦显式选择真实 provider，缺 key 或 provider 异常就应该暴露。只有在本地演示或临时降级场景，才显式打开 fallback，并且指标里必须标注它不是真实 provider。

## Day35 交接

Day35 可以在 Day34 provider 架构上继续做 RAG 检索质量与 provider 指标：

- 小型 RAG 评估集。
- query -> expected evidence 的命中检查。
- provider latency / error / fallback 统计口径。
- 空召回和低相似度的可解释输出。

Day35 不需要重新设计 provider 配置，只需要复用 Day34 的 factory 和错误码。

## 建议提交

```text
feat: 增加可配置 embedding provider 架构
```
