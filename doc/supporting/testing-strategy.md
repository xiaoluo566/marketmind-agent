# 测试策略

## 测试层次

1. 单元测试：工具函数、校验器、格式化器
2. 集成测试：API、数据库、任务队列
3. 端到端测试：任务提交到报告生成的完整链路

## 测试映射

| 模块 | 测试类型 | 重点 |
| --- | --- | --- |
| API | 集成测试 | 输入校验、错误码、task_id 返回 |
| Celery | 集成测试 | 任务投递、状态更新、重试 |
| Crawler | 单元 + 集成 | DOM 抽取、失败分类、证据保存 |
| Agent | 单元 + 集成 | 状态转移、工具调用、断点恢复 |
| RAG | 单元 + 集成 | 切片、embedding、召回 |
| Report | 单元 | schema、引用、摘要结构 |
| Frontend | E2E | 提交任务、查看进度、查看报告 |

## 必测内容

- Pydantic schema 校验
- Agent 状态流转
- Celery 任务投递与重试
- 评论切片与向量检索
- 报告生成

## 测试原则

- 失败要可复现
- 关键路径要自动化
- 修 bug 必须补回归测试

## 验收门槛

- 核心模块有测试
- 关键路径能跑通
- 回退版本能快速验证

## 测试数据策略

- 保留少量固定 HTML 样例
- 保留评论 CSV / JSON 样例
- 保留模型输出失败样例
- 保留 Agent step 恢复样例

## Day 14 RAG 测试边界

Day 14 新增 `tests/test_review_rag_indexing.py`，当前覆盖：

- 评论 HTML / script 清洗。
- 按句子边界切片。
- fake embedding 稳定性和维度。
- `review_chunks` 幂等入库。
- top_k 相似评论检索返回 `review_id`、`source_url`、`rating` 和 `similarity`。

当前没有覆盖真实 embedding API 和 PostgreSQL pgvector 原生排序。后续接真实 provider 和 Docker Compose PostgreSQL 后，需要补：

- provider 超时和重试。
- embedding 维度不匹配失败。
- pgvector `<=>` 排序结果。
- 相似度阈值过低时的“证据不足”行为。

## Day 15 工具测试边界

Day 15 新增 `tests/test_search_reviews_tool.py`，当前覆盖：

- 传入 RAG store 和 embedding provider 后，registry 能注册 `search_reviews_tool`。
- query 命中评论时，工具返回 evidence chunk 和 `chunk:{chunk_id}` 格式的 evidence ref。
- `rating_lte` 过滤可以保留低分差评。
- 高 `min_similarity` 导致召回为空时，工具返回空 `results`、空 `evidence_refs` 和 `NO_REVIEW_CHUNKS_ABOVE_THRESHOLD`。

后续 Day 16 - Day 17 报告测试需要验证：

- 报告只能引用 `evidence_refs` 中出现过的 chunk。
- `no_results_reason` 存在时，报告必须标注证据不足。
- 不能把 query 本身写成事实。

## Day 16 报告生成测试边界

Day 16 新增 `tests/test_report_generation.py`，当前覆盖：

- `StructuredReport` 拒绝章节引用未知 evidence ref。
- 没有 evidence snippets 时，生成 `insufficient_evidence` 报告。
- 无证据报告不编造 evidence refs，并在 claim 中明确“证据不足”。
- 有 evidence snippets 时，报告章节能绑定已知 evidence refs。
- `StructuredReport.to_markdown()` 能输出标题、摘要、章节、风险等级和证据引用。
- `SQLAlchemyReportStore` 能把报告 JSON、Markdown、evidence refs 和 schema version 写入 `reports` 表。

Day 16 当前不覆盖：

- 真实 LLM report prompt 输出。
- 多版本报告覆盖策略。
- 报告 API 路由。
- 前端报告详情页。
- PDF / Markdown 文件导出。

这些内容分别放到 Day 17 - Day 21 和第四周处理。Day 16 的测试重点是防止“无证据也生成结论”和“章节引用不存在证据”这两个高风险问题。

## Day 17 证据链测试边界

Day 17 新增 `tests/test_report_evidence_chain.py`，当前覆盖：

- `parse_evidence_ref()` 能解析 `chunk:{id}`。
- malformed ref 和不支持类型会抛错。
- `SQLAlchemyEvidenceChainStore` 能回查 review chunk、artifact 和 agent step。
- `chunk:{chunk_id}` 能追溯到 parent `review:{review_id}`。
- 缺失证据返回 `available=false` 和 `missing_reason=EVIDENCE_NOT_FOUND`。
- `attach_evidence_chain()` 返回新报告，不原地修改旧报告。
- `StructuredReport.to_markdown()` 能渲染“证据链回查”章节。
- `GET /api/reports/{report_id}/evidence` 能返回统一 envelope。
- 缺失 report 返回 `REPORT_NOT_FOUND`。
- 阶段审计补充：`agent_step` evidence metadata 不暴露完整 `tool_input` 和 `tool_output`。

Day 17 当前不覆盖：

- 前端点击跳转到具体来源详情。
- 报告详情页真实 UI。
- PDF 导出中的 citation 格式。
- 多任务并发下的报告证据链性能。

Day 17 的测试重点是保证证据缺失不会被伪装成可用证据，以及 API 返回结构和底层 evidence chain 模型一致。

## 阶段审计补充测试

推主分支前的阶段审计补了三个回归方向：

- `tests/test_tasks_api.py::test_create_task_rejects_unsafe_public_url_targets`：确认 `source_type=public_url` 时拒绝 `file://` 和 localhost / loopback 目标。
- `tests/test_report_evidence_chain.py::test_report_evidence_api_sanitizes_agent_step_metadata`：确认报告证据链不会把完整 Agent tool input/output 暴露到 API。
- `tests/test_frontend_history_contract.py::test_report_detail_uses_real_report_evidence_chain`：确认报告详情页使用 `GET /api/reports/{report_id}/evidence`，不再用全局 mock evidence 拼报告证据。

## Day 18 评分测试边界

Day 18 新增 `tests/test_report_scoring.py`，当前覆盖：

- evidence snippets 能按关键词分组到质量、售后、物流、包装等维度。
- 每个 `DimensionScore` 必须携带 `evidence_refs`。
- 高风险低评分评论能得到较高风险分和机会分。
- 样本数低于 `minimum_samples` 时会降权。
- 样本不足时写入 `sample_warning=LOW_SAMPLE_SIZE`。
- 无 evidence snippets 时输出 `insufficient_evidence`，不编造维度分。
- `attach_scorecard_to_report()` 返回新报告，不原地修改旧报告。
- `StructuredReport.to_markdown()` 能渲染“维度评分”章节。

Day 18 当前不覆盖：

- 真实 LLM 评分。
- 机器学习分类器。
- 前端图表展示。
- 跨任务评分统计。

Day 18 的测试重点是防止评分脱离证据、防止小样本被过度解读，以及保证评分规则可复现。

## Day 23 测试体系加固

Day 23 不再重复“建立 tests 目录”，而是把已经积累的测试体系固化成质量门禁。

新增内容：

- `tests/test_quality_gate_config.py`
- `tests/test_task_status_policy.py`
- `tests/test_schema_validation_contracts.py`
- `backend/app/storage/status_policy.py`

### Coverage 门禁

`pyproject.toml` 当前策略：

```toml
[tool.pytest.ini_options]
addopts = "-q"

[tool.coverage.run]
source = ["backend"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

设计取舍：

- 默认 `uv run pytest` 保持轻量，方便日常定向测试。
- 提交前使用 `uv run pytest --cov=backend --cov-report=term-missing` 执行 coverage 门禁。
- coverage fail-under 固定为 80，当前 Day 23 实测 backend coverage 为 90.80%。

不要把 `--cov=backend --cov-fail-under=80` 直接写入默认 `addopts`。这样会让只跑纯配置测试或前端契约测试时 coverage 变成 0，反而破坏开发效率。

### 状态转换测试边界

`tests/test_task_status_policy.py` 覆盖：

- received -> queued
- queued -> running
- running -> completed / failed
- failed -> waiting_retry
- waiting_retry -> queued
- completed / cancelled 终态不能回到 running / queued

当前状态策略先作为独立模块存在，不直接接入 store。后续 Day 28 做 retry / resume 时，再把 `ensure_task_status_transition()` 接入具体业务入口。

### Schema 契约测试边界

`tests/test_schema_validation_contracts.py` 覆盖：

- `TaskCreateRequest` 的 target trim 和默认值。
- `public_url` 的危险目标拒绝。
- 合法 HTTPS public URL 放行。
- `StructuredReport` 的 evidence refs 一致性。
- `TaskStatus` 和 `AgentStepStatus` 枚举值和文档保持一致。

这组测试和已有 API 测试有意重叠一部分。原因是 API 测试验证路由行为，schema 测试验证边界模型本身；当未来路由重构时，schema 约束仍然应该独立成立。

## Day 24 主链路集成测试边界

Day 24 新增 `tests/test_day24_integration_flow.py`，用于验证 Day 1 到 Day 23 已完成能力是否能组成一条稳定主链路。

这条测试链路覆盖：

- `POST /api/tasks` 创建任务，并通过依赖覆盖使用真实 `SQLAlchemyTaskStatusStore` 和 `SQLAlchemyTaskEventStore`。
- fake dispatcher 捕获入队 payload，验证 API 层确实生成 `task_id`、`trace_id` 和 `queue_task_id`。
- `run_research_task()` 使用同一个 `task_id` 执行 Worker 主体。
- fixture HTML 被 crawler 解析为商品、页面、评论和 artifact。
- `SQLAlchemyCrawlResultStore` 将采集结果写入数据库。
- `SQLAlchemyReviewChunkStore` 对评论切片并写入 `review_chunks`。
- `DeterministicEmbeddingProvider` 生成稳定 embedding，用于本地回归。
- `search_similar_reviews()` 召回评论 chunk，并构造 `chunk:{id}` evidence ref。
- `StructuredReportGenerator` 和 `SQLAlchemyReportStore` 生成并保存报告。
- `GET /api/reports`、`GET /api/reports/{report_id}` 和 `GET /api/reports/{report_id}/evidence` 通过真实 API 回查报告和证据链。

Day 24 有意不覆盖：

- 真实 Redis broker。
- 独立 Celery worker 进程。
- 真实 PostgreSQL / pgvector 原生 `<=>` 排序。
- 真实外部电商网站。
- 真实 LLM / embedding API。
- 浏览器端 E2E。

这些能力分别放到 Day 25 之后的 Docker Compose、CI、benchmark、E2E 和真实 provider 接入阶段。Day 24 的重点是“业务模块之间的契约是否闭环”，而不是“所有基础设施是否在本机同时启动”。

当前验证命令：

```powershell
uv run pytest tests\test_day24_integration_flow.py
```

当前结果：

```text
1 passed
```

提交前完整门禁结果：

```text
uv run pytest: 137 passed
uv run pytest --cov=backend --cov-report=term-missing: 137 passed, backend coverage 90.86%
uv run ruff check backend tests migrations: passed
uv run alembic heads: 0002_task_queue_id (head)
frontend npm run lint: passed
frontend npm run build: passed
npm audit --audit-level=high: 0 vulnerabilities
uvx pip-audit: No known vulnerabilities found
```

## Day 25 Docker Compose 契约测试边界

Day 25 新增 `tests/test_day25_compose_contract.py`，用于把容器化运行拓扑纳入自动化测试。

这组测试覆盖：

- `docker-compose.yml` 必须声明 `postgres`、`redis`、`migrate`、`api`、`worker`、`frontend`。
- PostgreSQL 必须使用 pgvector 镜像。
- Redis 必须使用 Redis 7 系列镜像。
- API 和 Worker 必须依赖 PostgreSQL / Redis healthy 和 `migrate` 成功完成。
- `migrate` 必须执行 `uv run alembic upgrade head`。
- Worker 必须执行 Celery worker 启动命令。
- API / Worker 必须使用容器内部 `postgres` 和 `redis` 地址，而不是 `localhost`。
- 后端 Dockerfile 必须包含 Python 3.12、uv sync、Playwright Chromium 和 Uvicorn。
- 前端 Dockerfile 必须包含 Node 22、`npm ci`、`npm run build` 和 `npm run start`。
- `.env.example` 和 `.dockerignore` 必须覆盖必要变量和本地运行状态。

Day 25 契约测试不等于真实容器 E2E。它验证的是配置结构和关键约束，真实镜像构建、`docker compose up -d`、容器健康检查和容器内任务提交，需要在 Docker Desktop Linux engine 启动后单独执行。

当前验证命令：

```powershell
uv run pytest tests\test_day25_compose_contract.py
docker compose config
```

当前结果：

```text
compose contract tests: 4 passed
docker compose config: passed
full pytest: 141 passed
coverage gate: 141 passed, backend coverage 90.86%
ruff: passed
frontend lint/build: passed
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

当前未完成：

```text
docker compose build api frontend
```

未完成原因是本机 Docker Desktop Linux engine 未运行，错误为：

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

## Day 26 CI 契约测试边界

Day 26 新增 `tests/test_day26_ci_contract.py`，用于把 CI workflow、PR 模板、发布清单和回退手册纳入自动化测试。

这组测试覆盖：

- `.github/workflows/ci.yml` 必须同时覆盖 `pull_request` 和 `push`。
- CI 触发分支必须包含 `main` 和 `dev`。
- backend job 必须使用 Python 3.12 和 uv。
- backend job 必须执行 `uv run ruff check backend tests migrations`。
- backend job 必须执行 `uv run pytest --cov=backend --cov-report=term-missing`，继续使用 80% coverage 门槛。
- backend job 必须执行 `uv run alembic heads`，避免迁移 head 漂移。
- backend job 必须执行 `docker compose config`，验证 compose 配置解析和服务拓扑。
- backend job 必须执行 `uvx pip-audit`，把 Python 依赖漏洞扫描纳入门禁。
- frontend job 必须使用 Node 22、`npm ci`、`npm run lint`、`npm run build` 和 `npm audit --audit-level=high`。
- CI workflow 不能包含 `docker compose up` 或 `docker compose build`。
- `.github/pull_request_template.md` 必须要求验证记录和回退方案。
- `release-checklist.md` 必须包含 tag、backup、revert、compose 和 coverage 关键项。
- `rollback-runbook.md` 必须覆盖 Git、数据库迁移和 Docker Compose 回退。

Day 26 的测试重点是把“开发流程”也当成工程契约。CI 配置、PR 模板和回退手册不是附属材料，它们会直接影响项目是否可协作、可合入、可回退。

Day 26 当前不覆盖：

- GitHub Actions 远程实际运行结果。
- 真实容器镜像构建。
- `docker compose up -d` 后的容器健康检查。
- 容器内 API 提交样例任务和 Worker 消费。
- GitHub branch protection rule。

这些能力分别放到后续远程 CI 观察、Docker Desktop daemon 可用后的补验、Day 27 benchmark、Day 28 retry/resume 和 Day 30 里程碑发布处理。

当前验证命令：

```powershell
uv run pytest tests\test_day26_ci_contract.py
```

当前结果：

```text
Day 26 CI contract tests: 4 passed
Day 24 - Day 26 targeted tests: 9 passed
Full pytest: 145 passed
Coverage gate: 145 passed, backend coverage 90.86%
```

## 回归要求

任何 bug 修复都要留下一个能复现旧问题的测试。没有测试的修复，后续很容易被重构再次破坏。

## 与其他文档关系

- 数据样例见 `data-contract-examples.md`
- 状态机见 `agent-state-machine.md`
- 发版门槛见 `release-checklist.md`
