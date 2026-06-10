# Day 33 - 重试链路联调与恢复事件验收

## 当天目标

Day 33 的目标是验证 Day 32 的前端重试按钮和 Day 28 的后端 retry API 是否真的形成一致链路。重点不是继续堆 UI，而是确认任务状态、事件时间线、Agent steps、错误提示和浏览器可见行为是否一致。

这一天要把 `waiting_retry`、`task recovery resumed`、队列重新投递、前端刷新和手动浏览器验收连起来，形成一条可演示的失败恢复路径。

## 前置依赖

- `day-28.md`：后端 retry 和 worker recovery resume。
- `day-32.md`：前端 `重试任务` 按钮。
- `../supporting/testing-strategy.md`：E2E 和契约测试边界。
- `../supporting/phase-2-acceptance-and-risk.md`：第二阶段验收与回退策略。
- `../supporting/observability.md`：错误日志和 trace id 查询。
- `../supporting/dev-workflow.md`：本地验证、提交和回退流程。

## SDD 规格

本日按 Spec Kit SDD 思路执行，但规格直接沉淀在本文件，不另开 `specs/` 文档。原因是用户明确要求 Day33 的开发上下文集中在 `doc/roadmap/day-33.md`，避免同时维护两份规格造成后续执行冲突。

### 用户故事 1：证明前端 retry 不是假按钮（P1）

运营用户打开失败任务详情页后，点击 `重试任务`，需要看到任务从失败恢复到重新排队，并在事件时间线看到恢复证据。

独立验收：

- mock 浏览器页面 `/tasks/tsk_6D44` 能显示 `重试任务`。
- 点击后页面出现 `重试任务已提交`。
- 状态从 `失败` 变为 `排队中` 或可解释的恢复中状态。
- 事件时间线出现 `task.retry_submitted` 或中文恢复事件说明。

### 用户故事 2：证明后端 retry 链路和 Worker recovery payload 一致（P1）

开发者或面试官需要确认前端按钮背后确实对应后端 retry API、恢复事件和 Worker resume payload，而不是只改前端状态。

独立验收：

- `POST /api/tasks/{task_id}/retry` 仍返回 202。
- 后端事件顺序包含 `task waiting retry` 和 `task requeued`。
- Worker 重新执行时先记录 `task recovery resumed`。
- recovery payload 包含 `retry_count`、`resume_from_event_id`、`last_error_code`。

### 用户故事 3：真实后端事件进入中文控制台后可读（P2）

真实 API 模式下，后端事件消息仍以稳定英文 message 存储，前端展示层需要把 retry / recovery 常见事件翻译成中文说明，避免中文控制台混入难懂英文流程消息。

独立验收：

- `task waiting retry` 展示为 `任务正在等待重试。`
- `task requeued` 展示为 `任务已重新进入队列。`
- `task recovery resumed` 展示为 `任务恢复执行已开始。`
- `task retry queue unavailable` 展示为 `重试队列不可用。`
- `event_type`、`trace_id`、`task_id` 等技术字段保持英文。

### 功能需求

- **FR-001**：系统必须保留 Day32 的 failed-only `重试任务` 前端入口。
- **FR-002**：系统必须继续调用真实后端路径 `POST /api/tasks/{task_id}/retry`，不得改成 mock-only。
- **FR-003**：系统必须在 retry 成功后刷新任务详情、事件时间线和 Agent steps。
- **FR-004**：系统必须保留后端英文 `event_type` 和 trace 字段，不能为了中文化破坏 API contract。
- **FR-005**：系统必须把真实后端 retry / recovery 常见事件消息映射为中文用户可读说明。
- **FR-006**：系统必须明确区分 mock 浏览器验收、单进程测试验收和真实 Docker/Celery 验收，不得把 mock 结果写成真实容器结果。
- **FR-007**：系统必须为 Day33 增加可回归测试，防止 retry 链路文档、前端事件映射和后端 recovery payload 退化。

### 非目标

- 不重新设计 Day28 后端 retry policy。
- 不在 Day33 引入 Celery countdown 延迟调度。
- 不在 Day33 做完整 Playwright E2E CI job；浏览器验收可先使用 `agent-browser-cli`。
- 如果 Docker daemon 不可用，不声明真实 `docker compose up` 或容器内 worker 消费已通过。

### 接口契约

真实 retry API：

```http
POST /api/tasks/{task_id}/retry
```

成功响应仍使用统一 envelope，`data.status` 可以是 `queued`，事件流中必须能看到 retry / recovery 相关事件。

前端展示契约：

| 后端 message | 前端展示 |
| --- | --- |
| `task waiting retry` | `任务正在等待重试。` |
| `task requeued` | `任务已重新进入队列。` |
| `task recovery resumed` | `任务恢复执行已开始。` |
| `task retry queue unavailable` | `重试队列不可用。` |

### 成功标准

- Day32 复核无遗漏。
- Day33 新增测试先失败再通过。
- retry / recovery 真实后端事件能在中文控制台显示为中文说明。
- `tests/test_day28_recovery.py`、Day32 retry 契约测试和 Day33 新测试通过。
- 浏览器 mock 验收至少确认一次 `重试任务 -> 重试任务已提交 -> task.retry_submitted`。
- 文档同步到 `development-log.md`、`interview-defense-dossier.md`、`testing-strategy.md`、`phase-2-acceptance-and-risk.md`、`llmops-metrics.md`。

## 当天交付物

- 新增 retry 链路联调测试。
- mock 模式下补充一个失败任务重试样例。
- 真实 API 模式下验证：
  - failed 任务点击重试。
  - 状态进入 `waiting_retry` 或 `queued`。
  - 事件流出现恢复事件。
  - Worker 接收 recovery payload。
- 浏览器验收脚本或手动验收记录。
- 明确记录 Docker / Redis / Celery 不可用时的降级验证边界。

## 实施步骤

1. 先写测试：
   - `tests/test_frontend_retry_flow_docs.py` 或扩展 Day32 测试。
   - 验证文档和前端都包含 `waiting_retry`、`task recovery resumed`、`恢复事件`。
2. 后端目标测试：
   - 复跑 `tests/test_day28_recovery.py`。
   - 如果发现前端需要额外字段，先补 API schema 测试。
3. 前端目标测试：
   - 重试按钮点击后刷新任务状态。
   - 错误状态下显示后端错误码。
4. 浏览器验收：
   - 优先用 `agent-browser-cli` 打开失败任务详情页。
   - 如果 Edge 扩展不可用，再用 Playwright。
   - 记录页面是否出现 `重试任务`、`正在重新投递`、`恢复事件`。
5. 日志验收：
   - 确认错误日志不泄露 payload 中的敏感字段。
   - trace id 能关联前端错误和后端事件。
6. 如果 Docker daemon 不可用：
   - 明确只完成 mock / 单进程 / 测试层验证。
   - 不声明真实 Celery 容器链路已通过。

## 测试计划

```powershell
uv run pytest tests\test_day28_recovery.py
uv run pytest tests\test_frontend_retry_contract.py
uv run pytest tests\test_frontend_task_progress_contract.py
uv run pytest tests\test_observability.py
cd frontend
npm run lint
npm run build
```

浏览器验收建议：

```powershell
$env:NEXT_PUBLIC_USE_MOCKS="true"
cd frontend
npm run dev -- --hostname 127.0.0.1 --port 3002
agent-browser-cli open http://127.0.0.1:3002/tasks/tsk_6D44
agent-browser-cli scan --tab <tab_id> --text-only
```

## 验收标准

- 前端失败任务详情页能触发 retry。
- API 真实路径仍是 `POST /api/tasks/{task_id}/retry`。
- 状态链路包含 `failed -> waiting_retry -> queued/running` 的可观测证据。
- 事件时间线出现 `task recovery resumed` 或中文恢复事件说明。
- 错误场景有中文错误提示。
- `agent-browser-cli` 或 Playwright 至少完成一次页面文本验证。
- 不把 mock 验证包装成真实 Docker Compose 验证。

## 实际完成记录

Day33 已完成重试链路联调验收的第一轮收口。当天重点不是继续新增 UI，而是把 Day28 后端 retry / recovery 和 Day32 前端按钮之间的证据链补齐，并明确真实容器链路仍未补验。

### SDD 执行记录

- 按 Day33+ 新流程先做 SDD，但根据用户要求，规格直接写入本文件的 `SDD 规格`，未保留额外 `specs/` 文档。
- 规格明确了三个用户故事：
  - 证明前端 retry 不是假按钮。
  - 证明后端 retry 链路和 Worker recovery payload 一致。
  - 真实后端事件进入中文控制台后可读。
- 规格明确了接口契约：`POST /api/tasks/{task_id}/retry` 不变，真实后端 message 通过前端展示层翻译为中文，不改后端 event_type 和 trace 字段。

### TDD 执行记录

新增 `tests/test_day33_retry_linkage_contract.py`，先运行得到 RED：

```powershell
uv run pytest tests\test_day33_retry_linkage_contract.py
# 2 failed, 2 passed
```

失败点：

- `frontend/src/lib/api.ts` 尚无 `translateBackendTaskEventMessage()`。
- `inferEventModule()` 尚未显式识别 `recovery` 和 `retry` 事件。

实现后变为 GREEN：

```powershell
uv run pytest tests\test_day33_retry_linkage_contract.py
# 4 passed

uv run pytest tests\test_frontend_retry_contract.py tests\test_frontend_localization_contract.py tests\test_day28_recovery.py
# 20 passed
```

### 实际代码改动

- `frontend/src/lib/api.ts`
  - 新增 `translateBackendTaskEventMessage(event)`。
  - 将真实后端事件消息映射为中文展示：
    - `task waiting retry` -> `任务正在等待重试。`
    - `task requeued` -> `任务已重新进入队列。`
    - `task recovery resumed` -> `任务恢复执行已开始。`
    - `task retry queue unavailable` -> `重试队列不可用。`
  - `mapBackendTaskEvent()` 使用翻译后的 message，但保留 `event_type`、`trace_id`、`payload` 原始技术字段。
  - `inferEventModule()` 显式把 `recovery` 归为 `worker`，把 `retry` 归为 `api`，让事件时间线模块来源更清晰。

### 浏览器验收

使用 mock dev server：

```powershell
$env:NEXT_PUBLIC_USE_MOCKS="true"
cd frontend
npm run dev -- --hostname 127.0.0.1 --port 3002
```

验收结果：

- `GET http://127.0.0.1:3002/tasks/tsk_6D44` 返回 200。
- `agent-browser-cli` 打开并扫描任务详情页，初始页面显示 `失败`、`刷新`、`重试任务`。
- 点击 `重试任务` 后，页面显示：
  - `重试任务已提交`
  - `排队中`
  - `api / task.retry_submitted`
  - `重试任务已提交，任务已重新进入队列。`

### Docker / 真实容器边界

本日检查 Docker daemon：

```powershell
docker info --format '{{.ServerVersion}}'
```

结果：

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

因此 Day33 只声明以下能力已通过：

- 源码契约测试。
- 后端 retry / recovery 单进程测试。
- 前端 lint/build。
- mock 浏览器点击验收。

不声明：

- 真实 `docker compose up` 已通过。
- 真实 Redis/Celery 容器链路已消费 recovery payload。
- 真实容器内 worker 恢复成功率。

### 最终验证

```powershell
uv run pytest
# 192 passed

uv run pytest --cov=backend --cov-report=term-missing
# 192 passed, backend coverage 90.77%

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

git diff --check
# passed
```

安全扫描：

- `rg -n "sk-|OPENAI_API_KEY|API_KEY|SECRET|PASSWORD|TOKEN|TOKEN=" ...` 只有测试假 key、环境变量占位、package-lock URL 和文档字段命中。
- 未发现真实密钥。

## 风险与回退

风险：

- 浏览器可见状态和后端状态不同步。
- retry 后事件流延迟，用户以为没有成功。
- 真实 Celery 和测试内存实现行为有差异。
- 双击按钮造成重复恢复事件。

回退：

- 如果真实联调不稳定，先保留按钮但加明确 loading 和错误提示。
- 如果重复投递不可控，Day34 前先增加按钮冷却或前端禁用。
- 如果容器联调失败，记录到 `phase-2-acceptance-and-risk.md`，不阻塞 Day34 provider 设计。

## 文档同步清单

- `development-log.md`：记录 Day 33 联调结果、浏览器验收方式和未补验边界。
- `interview-defense-dossier.md`：补充“如何证明 retry 不是假按钮”的回答。
- `testing-strategy.md`：记录 retry 链路测试和浏览器验收边界。
- `phase-2-acceptance-and-risk.md`：同步真实联调中的失败点。
- `llmops-metrics.md`：预留恢复成功率统计字段。

## 面试讲法

可以这样讲：

> Day 33 我不是继续写新功能，而是验证失败恢复链路是否真实。我的验收标准不是按钮能点，而是状态、事件、Worker recovery payload 和前端展示都能对应上。这样 retry 才能算工程闭环，而不是一个 UI 操作。

如果被问“怎么处理 Docker 不可用”，回答：

> 我会明确区分测试层、mock 浏览器层和真实容器层。Docker daemon 不可用时，只声明前两者通过，真实 compose build/up 会留在补验清单里，不会夸大项目状态。

## 建议提交

```text
test: 补齐重试链路联调验收
```
