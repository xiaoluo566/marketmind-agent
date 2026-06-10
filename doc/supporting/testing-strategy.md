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

状态策略先作为独立模块存在，不直接接入 store。Day 28 已经把 `waiting_retry` 接入 retry 业务入口，但底层 store 仍保持轻量，后续如果加入 cancel / pause / resume，需要继续把状态策略往写入层下沉。

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

## Day 27 Benchmark 测试边界

Day 27 新增 `tests/test_day27_benchmarking.py`，用于验证 benchmark 统计逻辑和性能 artifact 生成。

这组测试覆盖：

- `summarize_benchmark_results()` 能统计总样本数、成功数、失败数、成功率、平均端到端耗时、阶段均值和失败分类。
- 20 个 fixture 样例任务可稳定生成。
- `crawler` 和 `rag` 的瓶颈排序可复现。
- benchmark artifact 能写出 JSON、summary JSON 和 Markdown。
- Day27 roadmap、development log、interview dossier、performance benchmark 和 LLMOps 文档必须记录 benchmark 边界。

Day 27 benchmark 测试不覆盖：

- 真实 Redis / Celery broker 排队耗时。
- 真实 Playwright 浏览器访问外部网站。
- 真实 PostgreSQL / pgvector 原生排序耗时。
- 真实 LLM / embedding provider 调用耗时和 token 成本。
- 并发任务吞吐。

当前验证命令：

```powershell
uv run pytest tests\test_day27_benchmarking.py
```

当前结果：

```text
Day 27 benchmark tests: 5 passed
```

## Day 28 Retry / Resume 测试边界

Day 28 新增 `tests/test_day28_recovery.py`，用于验证失败重试和恢复策略。

这组测试覆盖：

- `classify_retry_error()` 能区分可重试、不可重试和 unknown 错误码。
- `plan_retry()` 能按 `retry_count` 生成下一次重试次数和指数退避。
- 达到最大重试次数后返回 `TASK_RETRY_LIMIT_REACHED`。
- `POST /api/tasks/{task_id}/retry` 能把失败任务推进为 `waiting_retry`，再重新投递为 `queued`。
- retry payload 复用原 `task_id`，并携带 `options.recovery`。
- 不可重试错误返回 `TASK_NOT_RETRYABLE`。
- 队列投递失败时任务回到 `failed`，并写入 `task retry queue unavailable` 事件。
- Worker 看到 recovery payload 后写入 `task recovery resumed` 事件。
- Day28 roadmap、development log 和 interview dossier 必须记录 retry / resume 边界。

Day 28 当前不覆盖：

- 前端 retry 按钮。
- 真实 Celery countdown 延迟重试。
- 并发双击 retry 的幂等锁。
- 独立 `task_retries` 表。
- 完整 Agent step replay。

当前验证命令：

```powershell
uv run pytest tests\test_day28_recovery.py
```

当前结果：

```text
Day 28 recovery tests: 7 passed
Day26-Day28 targeted tests: 16 passed
Full pytest: 157 passed
Coverage gate: 157 passed, backend coverage 90.79%
ruff: passed
alembic heads: 0002_task_queue_id (head)
docker compose config: passed
frontend lint/build: passed
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

## Day 29 Demo 文档测试边界

Day 29 新增 `tests/test_day29_demo_docs.py`，用于把 README、演示脚本、简历表达和面试讲述稿纳入自动化契约。

这组测试覆盖：

- `README.md` 必须包含 Day 29、快速启动、架构图、演示路径、已知边界，以及 demo / resume / interview 材料链接。
- `doc/supporting/demo-script.md` 必须包含 5-8 分钟、演示前检查、主线演示流程、失败重试、备用路线和不要现场声称。
- `doc/supporting/resume-story.md` 必须包含 Day27 fixture benchmark、Day28 失败任务 retry、90.79%、157 passed 和不建议写。
- `doc/supporting/interview-story.md` 必须包含 2 分钟版本、不是套壳、Day 28、Day 29 和追问回答。
- `doc/supporting/development-log.md` 必须记录 Day 29 开发记录。
- `doc/supporting/testing-strategy.md` 必须记录 Day 29 Demo 文档测试边界。

Day 29 当前不覆盖：

- 截图是否真实生成。
- 演示录屏是否真实录制。
- Docker Compose 是否真实 build/up。
- 面试官是否认可表达质量。

当前验证命令：

```powershell
uv run pytest tests\test_day29_demo_docs.py
```

当前结果：

```text
Day29 demo docs tests: 5 passed
Day27-Day29 targeted tests: 17 passed
Full pytest: 162 passed
Coverage gate: 162 passed, backend coverage 90.79%
ruff: passed
alembic heads: 0002_task_queue_id (head)
docker compose config: passed
frontend lint/build: passed
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
```

## Day 30 Release Candidate 测试边界

Day 30 新增 `tests/test_day30_release_candidate.py`，用于验证第一阶段收口材料是否完整，而不是新增业务主链路。

这组测试覆盖：

- `doc/supporting/day30-release-candidate.md` 必须存在，并记录 `v0.1-day30-rc1`、release candidate、Docker Desktop daemon 状态、GitHub Actions 和“不声明 v1.0”的边界。
- `doc/supporting/day30-metrics-summary.md` 必须只使用已验证数字，例如 `168 passed`、coverage `90.77%`、Day27 fixture benchmark 的 `20` 个样例、`95.00%` 成功率、`338 ms` 平均耗时、`391 ms` P95，以及模型调用次数：0。
- `doc/supporting/day30-bug-summary.md` 必须明确未解决缺口，包括前端 retry 按钮、真实 compose build/up、真实 embedding provider 等。
- `doc/supporting/future-iterations.md` 必须把第二阶段优先级具体化，避免 Day30 之后继续发散。
- `doc/supporting/release-checklist.md`、`README.md`、`development-log.md` 和 `interview-defense-dossier.md` 必须同步 Day30 RC 状态。

Day 30 当前不覆盖：

- 真实 Docker Compose build/up。
- 真实 LLM / embedding provider 调用。
- 前端 retry 按钮点击流程。
- Playwright E2E。
- GitHub branch protection required checks。
- Tag 推送后的 release 页面。

当前验证命令：

```powershell
uv run pytest tests\test_day30_release_candidate.py
```

当前结果会在 Day30 提交前更新到 `development-log.md`。Day30 的测试重点是防止发布材料夸大项目状态，确保 RC 边界、指标和缺口能被自动化检查。

## Day 31 前端中文化测试边界

Day 31 新增并扩展 `tests/test_frontend_localization_contract.py`，用于防止第二阶段控制台继续残留英文模板文案。

这组测试覆盖：

- AppShell 导航必须使用 工作台、新建调研、任务、报告、证据链、设置。
- Dashboard 必须使用中文运营文案，例如 Agent 调研工作台、今日任务、成功率、最近任务、系统链路、最近报告。
- NewResearchForm 必须使用中文 label、placeholder、按钮和错误提示。
- status badge 必须使用中文状态映射，不能依赖 `status.replace` 生成英文 fallback。
- mock service 中用户可见文案必须中文化。
- 任务、报告、证据链、设置页面必须使用中文标题和中文核心字段名。
- TaskProgressPanel、TaskTimeline、AgentStepsTable 必须使用中文进度和空状态文案。
- `formatDateTime()` 必须使用 `zh-CN` 日期格式。
- 根布局必须使用 `lang="zh-CN"` 和中文 metadata description。
- API 字段名和技术 key 仍必须保留，例如 `source_type`、`use_rag`、`enable_rag`、`task_id`。

Day 31 当前不覆盖：

- Playwright 视觉回归。
- 中文文本在所有移动端宽度下的布局截图。
- 多语言切换。
- 前端 retry 按钮点击流程。

当前验证命令：

```powershell
uv run pytest tests\test_frontend_localization_contract.py tests\test_phase2_planning_docs.py
```

当前结果：

```text
12 passed
Full pytest: 180 passed
Coverage gate: 180 passed, backend coverage 90.77%
ruff: passed
alembic heads: 0002_task_queue_id (head)
docker compose config: passed
frontend lint/build: passed
npm audit: 0 vulnerabilities
HTTP smoke: /, /research/new, /tasks, /reports, /evidence, /settings all 200 in mock dev mode
agent-browser-cli: Chinese page titles verified for dashboard, tasks, reports, evidence and settings
```

## Day32-Day40 文档契约测试边界

Day32-Day40 在正式开发前先新增 `tests/test_phase2_day32_40_docs.py`，用于锁定第二阶段后续 9 天的文档完整性。这个测试不验证业务功能已经实现，只验证开发前置文档、索引、开发日志、测试策略和面试材料已经准备好。

这组测试覆盖：

- `doc/roadmap/day-32.md` 必须存在，并记录 Day 32：前端失败任务重试闭环。
- `doc/roadmap/day-33.md` 必须存在，并记录 Day 33：重试链路联调与恢复事件验收。
- `doc/roadmap/day-34.md` 必须存在，并记录 Day 34：真实 embedding provider 接入设计。
- `doc/roadmap/day-35.md` 必须存在，并记录 Day 35：RAG 检索质量与 provider 指标。
- `doc/roadmap/day-36.md` 必须存在，并记录 Day 36：真实 LLM 报告生成 Prompt。
- `doc/roadmap/day-37.md` 必须存在，并记录 Day 37：Playwright E2E 主链路。
- `doc/roadmap/day-38.md` 必须存在，并记录 Day 38：报告导出与证据包。
- `doc/roadmap/day-39.md` 必须存在，并记录 Day 39：LLMOps 运营指标面板。
- `doc/roadmap/day-40.md` 必须存在，并记录 Day 40：第二阶段阶段验收与发布候选。
- 每个每日文档必须包含：当天目标、前置依赖、当天交付物、实施步骤、测试计划、验收标准、风险与回退、文档同步清单、面试讲法、建议提交。
- `phase-2-master-plan.md`、`doc/README.md`、`roadmap/README.md` 必须索引 Day32-Day40。
- `development-log.md` 必须包含 Day32-Day40 开发前置记录。
- `interview-defense-dossier.md` 必须包含 Day32-Day40 面试讲述准备。
- `testing-strategy.md` 必须包含 Day32-Day40 文档契约测试边界。

当前不覆盖：

- Day32-Day40 的实际业务功能是否已经实现。
- Playwright E2E 是否已接入。
- 真实 provider 是否已经可用。
- Phase 2 RC 是否已经发布。

这些内容会在对应开发日写独立测试验证。这个测试的作用是防止后续开发跳过文档、索引和面试材料。

当前验证：

```text
tests/test_phase2_day32_40_docs.py: 3 passed
Phase 2 + Day30 documentation contract tests: 21 passed
Full pytest: 183 passed
ruff: passed
git diff --check: passed
```

## Day 32 前端 Retry 契约测试边界

Day32 新增 `tests/test_frontend_retry_contract.py`，用于验证 Day28 后端 retry 能力已经被前端正确消费。这个测试不是浏览器 E2E，而是源码级契约测试，目标是防止后续重构误删 API route、按钮状态、中文文案或 mock recovery 行为。

这组测试覆盖：

- `frontend/src/lib/api.ts` 必须导出 `retryTask(taskId: string)`。
- `retryTask()` 必须调用真实后端路径 `POST /api/tasks/${taskId}/retry`，不能只做 mock-only 行为。
- `TaskProgressPanel` 必须导入并调用 `retryTask()`。
- 只有 `task.status === "failed"` 时展示 `重试任务` 入口。
- 重试过程中按钮必须显示 `正在重新投递`，并通过 `disabled={retrying || refreshing}` 禁用重复点击。
- 成功后必须展示 `重试任务已提交`，并调用 `refreshTaskProgress()` 刷新任务详情、事件时间线和 Agent steps。
- 失败时必须展示 `重试失败`，保留 `trace id` 作为排障字段。
- mock 模式必须更新任务快照和追加 `task.retry_submitted` 事件，方便无后端时验证 UI。

这组测试不覆盖：

- 真实浏览器点击。
- Redis / Celery 是否真的重新消费任务。
- `waiting_retry -> queued/running` 的真实端到端状态迁移。
- 后端幂等锁和 retry limit 的全部组合，这些仍由 `tests/test_day28_recovery.py` 和 Day33 联调覆盖。

当前验证：

```text
tests/test_frontend_retry_contract.py: 5 passed
Day32 targeted retry regression: 29 passed
Full pytest: 188 passed
Coverage gate: 188 passed, backend coverage 90.79%
ruff: passed
frontend lint/build: passed
npm audit: 0 vulnerabilities
pip-audit: No known vulnerabilities found
Browser mock click: /tasks/tsk_6D44 retry submitted and task.retry_submitted event visible
```

## 回归要求

任何 bug 修复都要留下一个能复现旧问题的测试。没有测试的修复，后续很容易被重构再次破坏。

## Spec Kit 接入验证边界

Spec Kit 接入属于开发流程和仓库结构变更，不改变业务代码、API、数据库 schema 或前端页面行为。因此本次验证重点不是跑新的业务测试，而是确认工具链、生成目录和文档流程没有破坏现有 Day1-Day32 结构。

本次验证覆盖：

- `specify version` 可以正常执行。
- `.specify/integration.json` 记录 Codex integration。
- `.specify/init-options.json` 记录 `ai_skills: true`、`script: ps` 和当前 Spec Kit 版本。
- `.agents/skills/` 存在 `speckit-specify`、`speckit-plan`、`speckit-tasks`、`speckit-implement`、`speckit-analyze`、`speckit-checklist`、`speckit-clarify` 等 skills。
- `AGENTS.md` 已补充 Day33+ 固定开发流程。
- `doc/supporting/dev-workflow.md` 已记录：
  `Spec Kit SDD -> tdd-workflow -> 代码实现 -> verification-loop -> 开发日志/面试文档/测试文档回填`。
- `.specify/memory/constitution.md` 不再保留模板占位，而是写入本项目的 SDD 原则。

本次不覆盖：

- Day33 retry 真实联调功能。
- 新 `specs/` 功能目录，因为本次只接入工具和流程，不创建具体功能规格。
- Spec Kit 每个 skill 的完整端到端执行，这会在 Day33+ 的具体功能开发中验证。

## Day 33 Retry 链路联调测试边界

Day33 新增 `tests/test_day33_retry_linkage_contract.py`，用于验证 Day28 后端 retry/recovery 和 Day32 前端 retry 按钮之间的链路证据。它不是完整真实容器 E2E，而是把当前可自动化的合同固定下来。

这组测试覆盖：

- `doc/roadmap/day-33.md` 必须内嵌 SDD 规格，并明确不另开 `specs/` 文档。
- `frontend/src/lib/api.ts` 必须存在 `translateBackendTaskEventMessage()`。
- 真实后端 retry/recovery message 必须在前端展示层映射为中文：
  - `task waiting retry`
  - `task requeued`
  - `task recovery resumed`
  - `task retry queue unavailable`
- `inferEventModule()` 必须显式识别 `recovery` 和 `retry`。
- 后端仍必须保留可审计 message 和 recovery payload keys：
  - `retry_count`
  - `resume_from_event_id`
  - `resume_from_event_type`
  - `last_error_code`

这组测试不覆盖：

- 真实 Docker Compose 启动。
- Redis/Celery 容器内消费。
- 真实浏览器 E2E CI job。
- 未来新增后端事件 message 的全部中文映射。

当前验证：

```text
tests/test_day33_retry_linkage_contract.py: 4 passed
Day28 + Day32 + Day33 retry regression: 20 passed
frontend lint/build: passed
Browser mock click: /tasks/tsk_6D44 retry submitted and task.retry_submitted event visible
Docker daemon: unavailable, real compose retry validation not claimed
```

## Day 34 Embedding Provider 契约测试边界

Day34 新增 `tests/test_embedding_provider_config.py`，用于验证真实 embedding provider 接入架构，而不是验证真实语义召回质量。

这组测试覆盖：

- `Settings()` 默认使用 `EMBEDDING_PROVIDER=fake`，保证本地测试和 CI 不触发外部 API。
- `build_embedding_provider(Settings(embedding_provider="fake"))` 返回 `DeterministicEmbeddingProvider`。
- 显式配置 `EMBEDDING_PROVIDER=openai-compatible` 但缺少 API key 时抛出 `EMBEDDING_PROVIDER_UNCONFIGURED`。
- `OpenAICompatibleEmbeddingProvider` 会把 `model`、`input`、`dimensions`、`Authorization` 和 timeout 传给 client。
- 合法 provider 响应能解析为向量列表。
- 响应维度不匹配时抛出 `EMBEDDING_PROVIDER_BAD_RESPONSE`。
- rate limit 错误保持为 `EMBEDDING_PROVIDER_RATE_LIMITED`。
- Day14 / Day15 RAG 回归继续通过，说明 provider 扩展没有破坏现有注入链路。

这组测试不覆盖：

- 真实 OpenAI 或兼容 provider 网络请求。
- 真实 token、成本和 latency。
- 真实 RAG 召回质量。
- pgvector 原生向量排序。
- provider metrics 面板。

当前验证：

```text
tests/test_embedding_provider_config.py: 6 passed
Day34 targeted RAG provider regression: 16 passed
Full pytest: 198 passed
Coverage gate: backend coverage 90.13%
ruff / alembic heads / docker compose config: passed
frontend lint / build / audit: passed
pip-audit: No known vulnerabilities found
```

Day35 需要在这个基础上补 RAG 评估集和 provider 指标测试，不能把 Day34 的架构测试误写成真实召回质量验证。

## Day 35 RAG 质量与 Provider Metrics 测试边界

Day35 新增 `tests/test_rag_quality_metrics.py`，用于验证 RAG 评估和 provider metrics baseline。

这组测试覆盖：

- 5 个中文业务 query：
  - `质量差`
  - `退货`
  - `物流慢`
  - `客服差`
  - `续航短`
- 每个 query 都有 expected review external id。
- `evaluate_rag_quality()` 能输出 total cases、passed cases、empty recall、micro hit rate 和 per-case result。
- `InstrumentedEmbeddingProvider` 能记录 provider name、model、输入字符数、latency、success、error code 和 fallback。
- `summarize_provider_metrics()` 能聚合成功、失败、fallback 和错误码。
- 模拟 timeout provider 失败时，metrics 保留 `EMBEDDING_PROVIDER_TIMEOUT`。

这组测试不覆盖：

- 真实 embedding provider 网络请求。
- 真实 token / cost。
- 大规模人工标注评估集。
- pgvector 原生排序。
- provider metrics 持久化。

当前验证：

```text
tests/test_rag_quality_metrics.py: 2 passed
Day35 RAG/provider targeted regression: 16 passed
Day35 + Phase2 docs targeted regression: 19 passed
Full pytest: 200 passed
Coverage gate: backend coverage 90.31%
ruff / alembic heads / docker compose config: passed
frontend lint / build / audit: passed
pip-audit: No known vulnerabilities found
```

这组测试的定位是防回归和证明评估方法，不是证明线上 RAG 准确率。

## Day 36 LLM Report Prompt 测试边界

Day36 新增 `tests/test_llm_report_prompt_contract.py`，用于验证真实 LLM 报告生成 prompt 的工程契约。

这组测试覆盖：

- `build_report_prompt_bundle()` 必须包含 prompt version、StructuredReport、allowed evidence refs 和“不要编造证据 ID”。
- bad JSON 输出会触发 self-heal repair。
- repair 成功后 report metadata 记录 `prompt_version`、`model_name`、`model_provider` 和 `fallback_used=false`。
- repair 失败或 evidence ref 校验失败时 fallback deterministic generator。
- fallback report metadata 记录 `fallback_used=true` 和 `fallback_reason=structured_output_guardrail_failed`。
- 无 evidence snippets 时跳过 LLM，输出 `insufficient_evidence`，并记录 `llm_skipped_reason=NO_EVIDENCE_SNIPPETS`。

这组测试不覆盖：

- 真实 LLM 网络请求。
- 真实 token / cost / latency。
- 多 prompt version 文件管理。
- 前端报告详情展示。

当前验证：

```text
tests/test_llm_report_prompt_contract.py: 4 passed
Day36 report chain targeted regression: 26 passed
ruff: passed
```

## Day 37 Playwright E2E 测试边界

Day37 新增 `tests/test_day37_playwright_e2e_contract.py`，用于验证 Playwright E2E 的工程契约，而不是去模拟真实浏览器行为。

这组测试覆盖：

- `frontend/package.json` 必须包含 `test:e2e` 脚本。
- `frontend/package.json` 必须声明 `@playwright/test`。
- `frontend/playwright.config.ts` 必须把 `testDir` 指向 `./e2e`。
- Playwright 必须使用 mock dev server：
  - `baseURL` 固定到 `http://127.0.0.1:3100`
  - `NEXT_PUBLIC_USE_MOCKS=true`
  - `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- E2E 必须打开失败截图、trace 和 video。
- 主链路 spec 必须使用中文 locator，并覆盖工作台、新建调研、任务详情、任务列表、retry、报告详情和证据链。
- mock 提交流程必须允许 E2E 独立于后端运行。
- `playwright-report/**` 和 `test-results/**` 必须从 ESLint 和 Git 提交中排除，避免测试产物污染质量门禁。

这组测试不覆盖：

- 真实 Docker Compose / FastAPI / Redis / Celery 联调。
- 真实浏览器访问外网。
- 移动端 viewport。
- 真实 LLM provider。

当前验证：

```text
tests/test_day37_playwright_e2e_contract.py: 4 passed
frontend npm run test:e2e: 1 passed
frontend npm run lint: passed
frontend npm run build: passed
frontend npm audit --audit-level=high: passed
```

## 与其他文档关系

- 数据样例见 `data-contract-examples.md`
- 状态机见 `agent-state-machine.md`
- 发版门槛见 `release-checklist.md`

## Day 38 报告导出与证据包测试边界

Day38 新增 `tests/test_report_export.py`，用于验证报告导出和证据包导出的后端契约。

这组测试覆盖：

- `GET /api/reports/{report_id}/export/markdown` 返回 `text/markdown`
- Markdown 导出包含正确 `Content-Disposition` 文件名
- Markdown 内容包含报告标题和 evidence ref
- `GET /api/reports/{report_id}/evidence-package` 返回统一 success envelope
- evidence package 包含 `package_version`、`report_id`、`task_id`、`evidence_refs` 和 sources
- 缺失 evidence ref 保留 `available=false` 和 `missing_reason=EVIDENCE_NOT_FOUND`
- 导出内容不会包含 `api_key`、`authorization`、`provider_token` 等敏感 metadata
- 缺失报告返回 `REPORT_NOT_FOUND` envelope

Day38 同时更新 `tests/test_frontend_history_contract.py`：

- 前端 API client 必须提供 Markdown 和 evidence package 下载 URL helper
- 真实 API 模式必须指向 `/export/markdown` 和 `/evidence-package`
- mock 模式必须能生成 data URL
- 报告详情组件必须展示 `导出 Markdown` 和 `下载证据包`

当前验证：

```text
tests/test_report_export.py + frontend/report regression: 19 passed
ruff: passed
frontend lint/build: passed
frontend Playwright E2E: 1 passed
```

## Day 39 LLMOps Summary 测试边界

Day39 新增 `tests/test_llmops_summary.py`，用于验证 LLMOps 运营指标汇总的后端 API 契约和前端展示契约。

这组测试覆盖：

- `GET /api/observability/llmops-summary` 返回统一 success envelope。
- API 从 `tasks` 表统计：
  - `total_tasks`
  - `completed_tasks`
  - `failed_tasks`
  - `success_rate`
  - `failure_rate`
  - `average_duration_ms`
- API 从 `agent_runs` 表统计：
  - `agent_run_count`
  - `model_call_count`
  - `input_tokens`
  - `output_tokens`
  - `total_tokens`
  - `reported_cost`
  - `validation_error_count`
  - `self_heal_count`
  - `self_heal_success_rate`
- API 从 `task_events` 和 `tasks.options.recovery` 统计：
  - `retry_requested_count`
  - `retry_requeued_count`
  - `recovery_resumed_count`
  - `retry_queue_unavailable_count`
  - `recovery_success_count`
  - `recovery_success_rate`
- 空数据库返回 0 baseline，不抛异常。
- provider metrics 当前标记为 `not_persisted`。
- warnings 必须包含“暂无真实 provider 成本数据”。
- 前端必须存在 `LLMOpsSummary` 类型、`getLLMOpsSummary()` helper、mock `llmopsSummary` 和首页中文 LLMOps 文案。

这组测试不覆盖：

- 真实 provider token / cost / latency。
- provider metrics 持久化。
- 趋势图、日报聚合和跨时间窗口查询。
- 真实 Docker Compose 下的多 Worker 运营数据。

当前验证：

```text
tests/test_llmops_summary.py: 3 passed
Day39 targeted regression: 38 passed
ruff: passed
frontend lint: passed
frontend build: passed
frontend audit: found 0 vulnerabilities
frontend Playwright E2E: 1 passed
```

这组指标可以用于演示工程化观测口径，但不能直接写成真实生产 LLMOps 数据，除非后续接入真实 provider 并完成持久化采样。

## Day 40 Phase 2 RC 测试边界

Day40 新增 `tests/test_day40_phase2_release_candidate.py`，用于验证第二阶段发布候选文档、缺口汇总、指标汇总和后续真实应用闭环规划是否同步。

这组测试覆盖：

- `doc/roadmap/day-40.md` 必须包含内嵌 SDD 规格、`v0.2-phase2-rc1`、不声明 v1.0、Day31-Day39 和真实应用闭环。
- `doc/supporting/phase-2-release-candidate.md` 必须记录 Phase 2 RC 范围、main 合并判断、Docker Compose 真实 build/up 边界和真实 provider 成本边界。
- `doc/supporting/phase-2-bug-summary.md` 必须记录未完成项，包括真实多容器 E2E、branch protection、CSV/JSON 评论导入和低风险真实站点适配器。
- `doc/supporting/phase-2-metrics-summary.md` 必须只写已验证命令和真实来源边界，不写真实线上成本。
- README、release checklist、future iterations、interview dossier 和 development log 必须引用 Day40 Phase 2 RC。

Day40 同时更新 `tests/test_frontend_localization_contract.py`，禁止根布局继续使用 `next/font/google`。这是因为生产构建依赖外网字体会让 `npm run build` 在受限网络下失败，属于发布门禁问题。

这组测试不覆盖：

- Docker daemon 下真实 `docker compose up --build`。
- 真实 provider 调用和真实账单成本。
- 真实业务数据上的召回质量。
- 真实 provider 调用和真实业务数据上的完整召回质量。

## 真实应用闭环测试边界

本次不再新增日程式文档契约测试，改为直接用功能测试锁定闭环能力。

新增测试：

- `tests/test_review_import_contract.py`：覆盖 CSV/JSON 导入、错误行报告、去重、`manual_upload` task、`products` / `reviews` 入库，以及导入后 RAG chunk 索引。
- `tests/test_crawler_service.py::test_crawl_product_page_extracts_low_risk_json_ld_reviews`：覆盖低风险 JSON-LD Product.review 页面适配。
- `tests/test_frontend_review_import_contract.py`：覆盖 `/imports` 前端页面、中文导入文案、`importReviews()` API client 和导入结果字段展示。

仍需继续保留的回归测试：

- `tests/test_rag_quality_metrics.py`
- `tests/test_llm_report_prompt_contract.py`
- `tests/test_report_evidence_chain.py`
- `tests/test_day24_integration_flow.py`
