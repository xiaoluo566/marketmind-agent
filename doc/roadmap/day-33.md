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
