# 第二阶段实用性深化计划

## 文档定位

第一阶段证明了系统可以工程化运行。第二阶段要提高用户可用性、工程深度和数据可信度。这里的“实用性”不是把项目做成完整商业产品，而是让面试官和未来使用者能看到：这个系统不只是能跑测试，还能更顺畅地处理真实任务、真实失败和真实模型输出。

关联文档：

- `../roadmap/phase-2-master-plan.md`
- `frontend-localization-contract.md`
- `phase-2-acceptance-and-risk.md`
- `day30-bug-summary.md`
- `future-iterations.md`

## 三个深化方向

### 1. 用户可用性

目标：用户能理解页面、能操作失败恢复、能看懂报告证据。

优先任务：

- 中文界面。
- 前端 retry 按钮。
- 任务失败原因和恢复状态展示。
- 报告证据链交互优化。
- Demo 数据入口更明确。

验收方式：

- 页面可见文案中文化。
- failed 任务能在前端点击重试。
- retry 后能看到 `waiting_retry`、`queued`、`recovery event`。
- Playwright E2E 覆盖至少一个操作闭环。

### 2. 工程深度

目标：把第一阶段的稳定测试和配置契约推进到真实运行、真实 provider 和更强 CI。

优先任务：

- 真实 compose build/up 验证。
- Docker daemon 可用后的容器内主链路测试。
- GitHub branch protection required checks。
- Playwright E2E job。
- retry 幂等锁和 Celery countdown。
- Agent step replay。

验收方式：

- 容器内 API health、worker 消费、PostgreSQL 写入和 Redis 状态流可验证。
- CI 仍保持快速稳定，重型 E2E 可以作为独立 job。
- main 只保留稳定版本，dev 用于日常开发。

### 3. 数据可信度

目标：让 RAG 和报告从 deterministic baseline 逐步接近真实模型链路。

优先任务：

- 真实 embedding provider。
- pgvector 原生排序。
- 真实 provider latency / token / cost 统计。
- 真实 LLM report prompt。
- prompt version 写入报告 metadata。
- evidence refs 强制校验。

验收方式：

- fake provider 仍用于单元测试。
- 真实 provider 通过配置打开。
- provider 失败能进入错误分类和 self-heal / retry 路径。
- 报告仍不能引用未知 evidence ref。

## 前端 retry 按钮设计边界

Day28 已有后端 `POST /api/tasks/{task_id}/retry`。第二阶段前端 retry 按钮不重新设计后端逻辑，只消费现有 API。

页面行为：

- 仅 failed 任务展示 `重试任务` 按钮。
- 点击后按钮进入 loading。
- 成功后刷新任务详情、事件流和 Agent steps。
- 如果返回 `TASK_NOT_RETRYABLE`，展示不可重试原因。
- 如果返回 `QUEUE_UNAVAILABLE`，展示队列不可用。

不做：

- 不在前端伪造 retry 成功。
- 不给 completed / running / queued 任务展示 retry。
- 不在 Day32 做完整 Agent step replay。

Day32 当前状态：

- 已实现 `retryTask(taskId)` 前端 API client，真实模式调用 `POST /api/tasks/${task_id}/retry`。
- 已在 `TaskProgressPanel` 中增加 failed-only `重试任务` 按钮。
- 已实现 `正在重新投递`、`重试任务已提交`、`重试失败` 和 trace id 展示。
- 已在 mock 模式下追加 queued 快照和 `task.retry_submitted` 事件，用于无后端 UI 验证。
- 已新增 `tests/test_frontend_retry_contract.py` 和中文化契约补充。
- 已用浏览器 mock 页面验证 `/tasks/tsk_6D44`：点击 `重试任务` 后显示 `重试任务已提交`、`排队中` 和 `api / task.retry_submitted`。

Day33 需要继续确认：

- 真实 API 模式下 `waiting_retry`、恢复事件、Redis/Celery 队列和 Worker recovery payload 是否一致。
- 重复点击之外的后端幂等和 retry limit 是否能被前端错误文案清楚表达。

## 真实 provider 设计边界

真实 provider 接入必须保留测试可控性：

- fake provider 是默认测试 provider。
- 真实 provider 只在配置完整时启用。
- provider 缺少 API key 时 fail fast。
- provider 输出维度必须和 `EMBEDDING_DIMENSIONS` 一致。
- 成本、耗时和失败次数写入 LLMOps 统计入口。

## 真实 LLM report prompt 设计边界

真实 LLM 只能输出候选结构，不能绕过 schema：

1. 模型输出 JSON。
2. JSON parse。
3. Pydantic schema 校验。
4. evidence refs 校验。
5. 失败时进入 self-heal。
6. 多次失败后生成证据不足报告或结构化错误。

## 第二阶段交付判断

一个第二阶段功能只有同时满足下面条件，才算完成：

- 有 roadmap 或 supporting 文档。
- 有测试。
- 有开发日志。
- 有面试手册补充。
- 有回退说明。
- 本地门禁通过。
- 如涉及远程 CI，GitHub Actions 通过。
