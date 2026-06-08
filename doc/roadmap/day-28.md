# Day 28 - 失败恢复与重试策略

## 当天目标

Day 28 的目标是让系统遇到可恢复失败后可以继续推进，而不是只能手工新建任务或从头重跑。今天把 Day 23 已经预留的 `waiting_retry` 状态真正接入业务流程，并基于 Day 27 benchmark 中暴露的 `ACCESS_BLOCKED` 失败分类建立第一版 retry / resume 能力。

今天不做复杂分布式调度，也不声称已经完成完整断点续跑。第一版边界是：

- 同一个 `task_id` 上重试，不新建任务。
- 失败事件和旧事件流全部保留。
- 状态按 `failed -> waiting_retry -> queued -> running -> completed/failed` 推进。
- 重试次数、上限、上次错误和恢复 checkpoint 写入 `options.recovery`。
- Worker 看到 recovery payload 后写入 `task recovery resumed` 事件。
- 只对明确可恢复的错误码允许重试。

## 前置依赖

- `day-23.md`：任务状态转换策略已包含 `failed -> waiting_retry -> queued`。
- `day-27.md`：benchmark 已统计 `ACCESS_BLOCKED` 失败分类，作为 Day28 retry 场景样例。
- `../supporting/agent-state-machine.md`：定义断点续跑必须从稳定步骤恢复，不覆盖旧步骤。
- `../supporting/risk-register.md`：采集失败、任务卡死和输出漂移是主要风险。
- `../supporting/api-contract.md`：已预留 `POST /api/tasks/{task_id}/retry`。

## 当天交付物

- `backend/app/tasks/recovery.py`
- `backend/app/tasks/service.py` retry 逻辑
- `backend/app/api/routes/tasks.py` 的 `POST /api/tasks/{task_id}/retry`
- `backend/app/worker/tasks.py` recovery resume 事件
- `tests/test_day28_recovery.py`
- `doc/supporting/api-contract.md` retry 接口补充
- `doc/supporting/testing-strategy.md` Day 28 测试边界
- `doc/supporting/development-log.md` Day 28 开发记录
- `doc/supporting/interview-defense-dossier.md` Day 28 面试表达补充
- `README.md` 当前阶段同步

## 实际完成内容

### 1. 失败分类与 retry plan

新增 `backend/app/tasks/recovery.py`，定义：

| 名称 | 作用 |
| --- | --- |
| `RetryErrorClassification` | `retryable`、`not_retryable`、`unknown` |
| `RecoveryDecision` | `retry`、`not_retryable`、`limit_reached`、`invalid_state` |
| `RetryPlan` | 记录当前重试次数、下一次次数、上限、退避时间和原因 |
| `ResumeCheckpoint` | 记录可恢复事件点 |
| `classify_retry_error()` | 根据错误码判断是否可重试 |
| `plan_retry()` | 根据错误码、已重试次数和上限生成重试计划 |
| `find_resume_checkpoint()` | 从事件流倒序找到最后一个非失败事件 |
| `build_retry_options()` | 把 recovery metadata 写入 `options.recovery` |

当前可重试错误码：

- `PAGE_TIMEOUT`
- `NETWORK_ERROR`
- `ACCESS_BLOCKED`
- `CRAWL_PERSISTENCE_FAILED`
- `QUEUE_UNAVAILABLE`

当前不可重试错误码：

- `DOM_NOT_FOUND`
- `PARSER_ERROR`
- `VALIDATION_FAILED`
- `TASK_NOT_FOUND`
- `UNKNOWN_SITE`

当前退避策略：

```text
retry_count=0 -> next=1 -> backoff=30s
retry_count=1 -> next=2 -> backoff=60s
retry_count=2 -> next=3 -> backoff=120s
retry_count>=3 -> TASK_RETRY_LIMIT_REACHED
```

### 2. Retry service

在 `backend/app/tasks/service.py` 新增 `retry_task_request()`。

流程：

1. 查询原任务。
2. 只允许 `failed` 任务进入重试。
3. 按 `task.error_code` 和 `options.recovery.retry_count` 生成 retry plan。
4. 从历史事件中找到最后一个非失败事件作为 resume checkpoint。
5. 把任务状态保存为 `waiting_retry`。
6. 写入 `task waiting retry` 事件。
7. 使用原 `task_id` 重新投递队列。
8. 投递成功后保存为 `queued`，清空当前任务状态上的 `error_code` / `error_message`。
9. 写入 `task requeued` 事件。
10. 投递失败时恢复为 `failed` 并写入 `task retry queue unavailable` 事件。

旧失败记录不会被覆盖，因为失败原因仍保留在历史 `task_events` 和 `options.recovery.last_error_code` 中。

### 3. Retry API

新增接口：

```text
POST /api/tasks/{task_id}/retry
```

成功响应：

```json
{
  "task_id": "tsk_xxx",
  "status": "queued",
  "trace_id": "trc_xxx",
  "queue_task_id": "retry_1"
}
```

失败错误码：

- `TASK_NOT_FOUND`
- `TASK_NOT_RETRYABLE`
- `TASK_RETRY_LIMIT_REACHED`
- `QUEUE_UNAVAILABLE`
- `RECOVERY_STORE_UNAVAILABLE`

### 4. Worker resume event

`backend/app/worker/tasks.py` 现在会识别 `payload.options.recovery`。如果存在 recovery metadata，Worker 会在进入普通 running 事件前写入：

```text
event_type=recovery
message=task recovery resumed
```

payload 包含：

- `retry_count`
- `resume_from_event_id`
- `resume_from_event_type`
- `last_error_code`

这样任务详情页后续可以区分“首次执行”和“失败后恢复执行”。

### 5. 测试覆盖

新增 `tests/test_day28_recovery.py`，覆盖：

- 可重试 / 不可重试 / unknown 错误分类。
- 最大重试次数和指数退避。
- `POST /api/tasks/{task_id}/retry` 成功把 failed 任务推进到 waiting_retry 再 queued。
- retry payload 保留原 `task_id`，并携带 `options.recovery`。
- 不可重试错误和达到上限返回 409。
- 重试投递队列失败时任务回到 failed，并写入 retry error 事件。
- Worker 看到 recovery payload 后写入 `task recovery resumed`。
- Day28 文档必须记录 recovery scope 和边界。

## 当天为什么这样选

### 为什么复用同一个 task_id？

Day28 的目标是“恢复同一个失败任务”，不是“复制一个新任务”。复用同一个 `task_id` 可以保留完整事件流，让前端和面试演示看到一次任务从失败、等待重试、重新排队到恢复执行的全过程。

如果新建任务，虽然实现更简单，但会导致旧任务和新任务之间的关系需要额外映射，历史报告、错误日志、Agent steps 和 evidence chain 都会变复杂。

### 为什么把 retry metadata 放进 `options.recovery`？

当前不新增数据库迁移，是为了降低 Day28 的 blast radius。`tasks.options` 已经是 JSON 字段，适合保存第一版恢复元数据：

- `retry_count`
- `max_attempts`
- `backoff_seconds`
- `last_error_code`
- `last_error_message`
- `resume_from_event_id`

后续如果 retry / resume 指标变复杂，再拆出独立 `task_retries` 表更合理。

### 为什么不做无限自动重试？

无限重试会放大外部站点反爬、队列故障和数据库故障。Day28 先固定 `max_attempts=3`，并把不可恢复错误直接拒绝重试。这样系统不会在错误输入或坏页面上不断消耗资源。

## 验证命令

```powershell
uv run pytest tests\test_day28_recovery.py
```

当前结果：

```text
Day 28 recovery tests: 7 passed
```

收尾完整门禁：

```powershell
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
```

当前结果：

```text
uv run pytest: 157 passed
uv run pytest --cov=backend --cov-report=term-missing: 157 passed, backend coverage 90.79%
uv run ruff check backend tests migrations: All checks passed
uv run alembic heads: 0002_task_queue_id (head)
docker compose config: passed
frontend npm run lint: passed
frontend npm run build: passed
npm audit --audit-level=high: found 0 vulnerabilities
uvx pip-audit: No known vulnerabilities found
```

## 遗留问题

- 当前 retry API 还没有接入前端按钮。
- 当前没有真正延迟执行 backoff，只把 `backoff_seconds` 写入 metadata；真实 Celery countdown 可在后续接入。
- 当前 resume checkpoint 基于事件流，不是完整 Agent step replay。
- 当前没有独立 `task_retries` 表。
- 当前没有并发重试锁，后续需要防止多次点击 retry 造成重复投递。

## 关联文档

- 上一天：`day-27.md`
- 下一天：`day-29.md`
- API 契约：`../supporting/api-contract.md`
- 状态机：`../supporting/agent-state-machine.md`
- 风险：`../supporting/risk-register.md`
- 测试策略：`../supporting/testing-strategy.md`

## 建议提交

```text
feat: 增加 Day 28 失败重试和恢复策略
```
