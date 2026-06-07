# Day 23 - 测试体系加固与覆盖率门禁

## 当天目标

Day 23 原始计划是“建立 pytest 基础配置、补 schema、状态机、RAG、报告测试”。由于 Day 4 到 Day 22 的开发一直遵循 TDD，项目当前已经有较完整的测试体系。因此 Day 23 不再重复创建 `tests/` 目录，而是把测试体系从“很多测试能跑”升级为“质量门禁可执行、覆盖率可量化、关键契约可防回归”。

当天目标：

- 保留 `uv run pytest` 的快速定向测试能力。
- 配置 backend coverage fail-under 80%。
- 用测试锁住 pytest / coverage 配置，避免后续误删质量门禁。
- 把任务状态转换规则独立成可测试策略。
- 补核心 Pydantic schema 校验契约测试。

## 前置依赖

- `day-22.md`：结构化错误日志和观测接口已经完成。
- `../supporting/testing-strategy.md`：定义测试层次和当前覆盖边界。
- `../supporting/data-contract-examples.md`：作为 API 契约样例参考。
- `pyproject.toml`：已有 pytest 基础配置和 `pytest-cov` 依赖。

## 当天交付物

### 1. Coverage 门禁配置

修改 `pyproject.toml`：

- 保留 pytest 默认 `addopts = "-q"`，让定向测试仍然轻量。
- 新增 `[tool.coverage.run] source = ["backend"]`。
- 新增 `[tool.coverage.report] fail_under = 80`。
- 新增 `show_missing = true`，方便定位未覆盖文件。

为什么不把 `--cov=backend --cov-fail-under=80` 放进默认 `addopts`：

- 定向运行纯配置测试时，不会 import backend，coverage 会变成 0。
- 如果默认 pytest 强制 coverage，开发中快速跑单文件测试会经常被覆盖率门禁误伤。
- 更合理的方式是：日常定向用 `uv run pytest tests\xxx.py`，提交前门禁用 `uv run pytest --cov=backend --cov-report=term-missing`。

### 2. 质量门禁配置测试

新增 `tests/test_quality_gate_config.py`：

- 确认 pytest 默认命令保持 `-q`。
- 确认 coverage source 指向 `backend`。
- 确认 coverage fail-under 为 80。
- 确认 coverage 报告显示 missing lines。

这类测试不是测试业务逻辑，而是测试工程规则，防止未来重构配置时把质量门槛删掉。

### 3. 任务状态转换策略

新增 `backend/app/storage/status_policy.py`：

- `TERMINAL_TASK_STATUSES`
- `ALLOWED_TASK_STATUS_TRANSITIONS`
- `can_transition_task_status(current, next_status)`
- `ensure_task_status_transition(current, next_status)`

新增 `tests/test_task_status_policy.py`：

- 允许 received -> queued。
- 允许 queued -> running。
- 允许 running -> completed / failed。
- 允许 failed -> waiting_retry。
- 允许 waiting_retry -> queued。
- 拒绝 completed -> running。
- 拒绝 cancelled -> queued。

当前 Day 23 只新增策略模块，不强行改造持久化 store。原因是 Day 1-22 主链路已经稳定，直接把 store 写入全部改成强校验会影响历史测试和任务恢复策略。后续 Day 28 做失败重试和续跑时，再把策略接入 retry / cancel API。

### 4. 核心 schema 校验契约

新增 `tests/test_schema_validation_contracts.py`：

- `TaskCreateRequest` 会 trim target 并应用默认 mode / priority / source_type / options。
- `source_type=public_url` 拒绝 `file://`、localhost、loopback、private IP、`.local`。
- 合法 HTTPS public URL 可以通过。
- `StructuredReport` 拒绝章节引用不在报告顶层 `evidence_refs` 中的证据。
- `StructuredReport` 接受 evidence-backed sections。
- `TaskStatus` 和 `AgentStepStatus` 枚举值与文档保持一致。

## 实施步骤

1. 写 `tests/test_quality_gate_config.py`，先让测试暴露当前 coverage 门禁缺失。
2. 修改 `pyproject.toml`，配置 coverage source 和 fail-under。
3. 写 `tests/test_task_status_policy.py`，先让测试暴露缺少状态策略模块。
4. 新增 `backend/app/storage/status_policy.py`。
5. 写 `tests/test_schema_validation_contracts.py`，补核心 schema 防回归测试。
6. 运行 Day 23 targeted tests。
7. 运行 coverage full gate。
8. 更新 `testing-strategy.md`、`development-log.md` 和面试文档。

## 当天选择思考

### 为什么 Day 23 不再“建立 tests 目录”？

因为项目在 Day 4 之后已经持续使用 TDD，目前测试已经覆盖 API、任务队列、Crawler、Agent、RAG、Report、前端契约和 Observability。继续按早期文档写“建立 tests 目录”会和真实项目状态不一致。

Day 23 的真正价值是把测试体系变成工程门禁：

- 有 coverage 配置。
- 有 fail-under 目标。
- 有配置测试防止门禁被误删。
- 有状态策略测试支撑后续 retry/cancel。

### 为什么 coverage 门禁设置为 80%？

80% 是工程上常见的最低质量线，适合简历项目展示“有质量门槛”。但不追求 100%，因为：

- 有些基础设施封装只在真实 Redis / PostgreSQL / Celery 环境下覆盖。
- 真实 Playwright 和外部网络采集不适合每次单元测试都跑。
- 测试价值不等于覆盖率数字本身，关键是核心风险路径有明确回归。

当前全量 coverage 结果为 90.83%，已经超过门槛。

### 为什么状态策略先独立，不立即接入 store？

状态策略会影响所有任务写入。当前已有代码中存在一些幂等写入、测试替身和恢复场景，如果当天直接强制所有 store save 都走状态策略，可能把“测试体系加固”变成大范围行为变更。

所以 Day 23 先做可测试策略模块，形成后续 Day 28 retry / resume 的基础。等恢复机制开发时，再把策略接到具体命令入口。

## 验收标准

- `uv run pytest tests\test_quality_gate_config.py` 通过。
- `uv run pytest tests\test_task_status_policy.py` 通过。
- `uv run pytest tests\test_schema_validation_contracts.py` 通过。
- `uv run pytest tests\test_schema_validation_contracts.py tests\test_task_status_policy.py tests\test_quality_gate_config.py` 通过。
- `uv run pytest --cov=backend --cov-report=term-missing` 通过，coverage >= 80%。

## 验证记录

- `uv run pytest tests\test_quality_gate_config.py`：1 passed。
- `uv run pytest tests\test_task_status_policy.py`：11 passed。
- `uv run pytest tests\test_schema_validation_contracts.py tests\test_task_status_policy.py tests\test_quality_gate_config.py`：22 passed。
- `uv run pytest --cov=backend --cov-report=term-missing`：136 passed，backend coverage 90.83%，达到 80% 门槛。

最终完整验证以本次提交前完整门禁为准。

## 风险与回退

风险：

- Coverage 配置可能让 full gate 变慢，但不会影响默认 targeted pytest。
- 状态策略模块暂未接入 store，因此当前更多是“规则沉淀”，不是运行时强制保护。
- schema 测试和已有 API 测试有部分重叠，但这是有意的：schema 测试更靠近边界模型，API 测试更靠近路由行为。

回退：

- 如果 coverage 门禁在 CI 中因环境导致不稳定，可以保留 coverage 配置，先让 CI 跑普通 pytest，再单独拆 coverage job。
- 如果后续发现状态策略和恢复机制冲突，优先调整 `ALLOWED_TASK_STATUS_TRANSITIONS`，不要散落修改各个 store。

## 遗留问题

- `status_policy.py` 还没有接入 `SQLAlchemyTaskStatusStore` 或 retry API。
- 还没有 Playwright E2E 测试。
- 还没有真实 PostgreSQL / Redis / Celery 的 Docker 集成测试。
- 还没有 CI workflow。

## 关联文档

- 上一天：`day-22.md`
- 下一天：`day-24.md`
- 测试策略：`../supporting/testing-strategy.md`
- 数据契约：`../supporting/data-contract-examples.md`
- 状态机：`../supporting/agent-state-machine.md`
- 发布门禁：`../supporting/release-checklist.md`

## 建议提交

`test: 加固 Day 23 测试体系和覆盖率门禁`
