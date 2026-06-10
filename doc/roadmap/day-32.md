# Day 32 - 前端失败任务重试闭环

## 当天目标

Day 32 的目标是把 Day 28 已经完成的后端 retry 能力接到 Next.js 控制台，让用户在失败任务详情页可以直接点击 `重试任务`，并看到任务从 `failed` 进入 `waiting_retry`、再回到 `queued` / `running` 的过程。

这一天重点解决“后端有能力，但前端用户无法操作”的断点。完成后，失败恢复不再只是 API 层能力，而是一个可演示、可解释、可追踪的用户闭环。

## 前置依赖

- `day-28.md`：后端 retry API、retry policy、`waiting_retry` 状态和 recovery payload。
- `day-31.md`：中文界面与术语统一，所有 retry 文案必须使用中文。
- `../supporting/frontend-localization-contract.md`：重试、恢复、失败、任务状态的中文术语。
- `../supporting/phase-2-practicality-plan.md`：第二阶段用户可用性目标。
- `../supporting/api-contract.md`：统一 API envelope 和错误返回格式。
- `../supporting/testing-strategy.md`：前端契约测试和回归门槛。

## 当天交付物

- 新增或扩展前端 API client：
  - `retryTask(taskId: string)`。
  - 调用 `POST /api/tasks/{task_id}/retry`。
  - 按统一 envelope 解析成功和错误。
- 新增 `RetryTaskButton` 或在 `TaskProgressPanel` 内增加重试按钮。
- 失败任务详情页出现 `重试任务` 按钮。
- 点击后展示：
  - `正在重新投递`。
  - `重试任务已提交`。
  - `重试失败`。
  - API 错误码和 trace id。
- 重试成功后刷新任务详情、事件时间线和 Agent steps。
- 更新 mock 模式下的 retry 行为，方便无后端时验证 UI。
- 新增前端契约测试，确保按钮文案、API 路径和错误处理不退化。

## 实施步骤

1. 先写测试：
   - `tests/test_frontend_retry_contract.py`。
   - 验证 `frontend/src/lib/api.ts` 存在 `retryTask`。
   - 验证 API 路径包含 `/api/tasks/${taskId}/retry` 或等价实现。
   - 验证 `TaskProgressPanel` 或独立按钮组件出现 `重试任务`、`正在重新投递`、`重试失败`。
   - 验证只有 `failed` 任务显示重试入口。
2. 修改 `frontend/src/lib/api.ts`：
   - 增加 `retryTask()`。
   - 保持 `ApiClientError` 错误处理方式一致。
   - mock 模式下返回一个新的任务状态快照，不能直接静默成功。
3. 修改 `TaskProgressPanel`：
   - 判断 `task.status === "failed"` 时显示按钮。
   - 点击按钮时禁用二次点击。
   - 成功后调用现有 `refreshTaskProgress()`。
   - 保留当前 `刷新` 按钮。
4. 错误展示：
   - 后端返回 `TASK_NOT_RETRYABLE` 时显示中文解释。
   - 后端返回队列失败时显示 `重试投递失败，请稍后再试`。
   - trace id 保留英文技术字段。
5. 文案统一：
   - 按钮：`重试任务`。
   - loading：`正在重新投递`。
   - 成功：`重试任务已提交`。
   - 失败：`重试失败`。
6. 运行前端 lint/build。
7. 用 mock 模式打开失败任务详情页，手动确认按钮可见。

## 测试计划

- 新增 `tests/test_frontend_retry_contract.py`。
- 更新 `tests/test_frontend_localization_contract.py`，把 retry 中文文案纳入中文化契约。
- 运行：

```powershell
uv run pytest tests\test_frontend_retry_contract.py tests\test_frontend_localization_contract.py
uv run pytest tests\test_day28_recovery.py
cd frontend
npm run lint
npm run build
```

如果改动触碰 API client，还要运行：

```powershell
uv run pytest tests\test_frontend_api_integration_contract.py tests\test_frontend_task_progress_contract.py
```

## 验收标准

- 失败任务详情页出现 `重试任务`。
- 非失败任务不显示重试按钮。
- 点击重试后按钮进入禁用和 loading 状态。
- 成功后刷新任务状态、事件时间线和 Agent steps。
- 错误状态显示中文提示，并保留后端错误码。
- `POST /api/tasks/{task_id}/retry` 路径没有被误写成前端 mock-only 行为。
- mock 模式可用于页面演示，真实 API 模式可用于后端联调。
- 文档、开发日志、面试文档和测试策略同步。

## 实际完成记录

Day32 已完成前端失败任务重试闭环的首版实现，范围严格控制在“消费 Day28 已有后端 retry API + 让用户可操作失败恢复”，没有重新设计后端恢复策略。

实际代码改动：

- `frontend/src/lib/api.ts`
  - 新增 `retryTask(taskId: string)`。
  - 真实 API 模式调用 `POST /api/tasks/${taskId}/retry`，继续使用统一 `ApiEnvelope` 和 `ApiClientError`。
  - mock 模式新增 `mockRetriedTaskIds`，点击重试后 `getTask()` 返回新的 queued 快照，不修改原始 fixture 对象。
  - mock 模式下 `getTaskEvents()` 会追加 `task.retry_submitted` 事件，消息为 `重试任务已提交，任务已重新进入队列。`，用于无后端演示恢复事件。
- `frontend/src/components/task-progress-panel.tsx`
  - 仅当 `task.status === "failed"` 时显示 `重试任务` 按钮。
  - 点击后进入 `正在重新投递` 状态，并通过 `disabled={retrying || refreshing}` 防止重复点击。
  - 成功后展示 `重试任务已提交`，并调用 `refreshTaskProgress()` 刷新任务详情、事件时间线和 Agent steps。
  - 失败时展示 `重试失败`，保留后端错误码和 `trace id`，便于按请求链路排查。
- `tests/test_frontend_retry_contract.py`
  - 新增前端 retry 契约测试，覆盖 API route、失败态按钮、中文文案、刷新行为和 mock recovery event。
- `tests/test_frontend_localization_contract.py`
  - 将 `重试任务`、`正在重新投递`、`重试失败` 纳入中文化契约。

当前验证：

```powershell
uv run pytest tests\test_frontend_retry_contract.py
# 5 passed

uv run pytest tests\test_frontend_retry_contract.py tests\test_frontend_localization_contract.py tests\test_frontend_api_integration_contract.py tests\test_frontend_task_progress_contract.py tests\test_day28_recovery.py
# 26 passed
```

最终收尾验证：

```powershell
uv run pytest
# 188 passed

uv run pytest --cov=backend --cov-report=term-missing
# 188 passed, backend coverage 90.79%

uv run ruff check backend tests migrations
# All checks passed

uv run alembic heads
# 0002_task_queue_id (head)

docker compose config
# passed

cd frontend
npm run lint
npm run build
npm audit --audit-level=high
# lint/build passed, audit found 0 vulnerabilities

uvx pip-audit
# No known vulnerabilities found
```

浏览器验收：

- 使用 `NEXT_PUBLIC_USE_MOCKS=true npm run dev -- --hostname 127.0.0.1 --port 3002` 启动 mock dev server。
- `GET http://127.0.0.1:3002/tasks/tsk_6D44` 返回 200。
- `agent-browser-cli` 指定 `MarketMind Agent` 标签页扫描确认失败任务详情页显示 `失败`、`刷新`、`重试任务`。
- 点击 `重试任务` 后，页面显示 `重试任务已提交`、状态 `排队中`，事件时间线出现 `api / task.retry_submitted` 和 `重试任务已提交，任务已重新进入队列。`。

待后续 Day33 补验：

- 如果真实后端和 Redis/Celery 可用，补真实 API 模式下 `waiting_retry -> queued/running` 的端到端联调。
- 继续检查重复投递幂等、恢复事件顺序和 worker recovery payload 的真实一致性。

## 风险与回退

风险：

- 重试按钮可能被非 failed 任务误触发。
- 双击按钮可能造成重复投递。
- mock 模式和真实 API 模式行为可能不一致。
- 成功后不刷新事件，用户看不到恢复证据。

回退：

- 如果按钮交互导致构建失败，先只保留 API client 和测试，不上线按钮。
- 如果后端 retry API 行为和前端预期不一致，优先修文档和契约，不临时绕过错误。
- 如果出现重复投递风险，先禁用按钮并记录到 Day33 做幂等联调。

## 文档同步清单

- `development-log.md`：记录 Day 32 实际完成、测试结果、按钮状态和遗留问题。
- `interview-defense-dossier.md`：补充“为什么 retry 要做成前端闭环”的讲法。
- `testing-strategy.md`：新增 Day32 前端 retry 契约测试边界。
- `frontend-localization-contract.md`：补充 retry 相关中文文案。
- `phase-2-practicality-plan.md`：把 Day32 标记为用户可用性提升的第一个闭环。

## 面试讲法

可以这样讲：

> Day 28 我已经把后端 retry API 和 recovery payload 做出来了，但那还不是完整用户能力。Day 32 我把它接到任务详情页：失败任务可以直接点击重试，前端会展示重新投递状态，并刷新事件时间线。这样面试官能看到失败恢复不是文档口号，而是从 API、状态、事件到 UI 的闭环。

如果被问“为什么不先做更复杂的模型能力”，回答：

> 因为长任务系统最怕失败后只能靠开发者手动调接口。先把失败恢复做成用户可操作能力，能明显提升系统实用性，也能为后续 E2E 和 LLMOps 指标打基础。

## 建议提交

```text
feat: 增加前端失败任务重试入口
```
