# Day 20 - 任务进度轮询与 Agent Step 展示

## 当天目标

Day 20 解决 Day 19 留下的核心体验缺口：用户提交任务后，不能只看到一个静态详情页，而要能持续观察任务状态、事件时间线和 Agent step 摘要。

当天目标分成两层：

1. 后端补齐 `GET /api/tasks/{task_id}/steps`，把已经持久化的 `agent_steps` 变成前端可消费的脱敏摘要。
2. 前端任务详情页改成客户端进度面板，定时刷新任务状态、事件和 Agent steps，避免用户误以为任务卡死。

## 前置依赖

- `day-19.md` 已完成真实任务提交、状态查询和事件查询。
- `day-06.md` 已完成任务事件流。
- `day-11.md` 已完成 Agent run / step 持久化。
- `../supporting/api-contract.md` 已定义 `GET /api/tasks/{task_id}/steps`。
- `../supporting/observability.md` 已定义“任务卡住了”的排查视角。
- `../supporting/ui-console-spec.md` 已定义任务详情页需要展示状态、事件和 Agent steps。

## 当天交付物

- 后端新增 `GET /api/tasks/{task_id}/steps`。
- 新增 `AgentStepSummaryData` 和 `TaskAgentStepsData` schema。
- `SQLAlchemyAgentRunStore` 新增 `list_steps_for_task()`。
- 任务 steps API 返回脱敏摘要，不暴露完整 thought。
- 前端 `getTaskSteps()` 接真实 API，并把后端 steps 映射成 `AgentStep`。
- 新增 `TaskProgressPanel` 客户端组件。
- 任务详情页使用 `TaskProgressPanel` 做状态、事件、steps 轮询。
- `AgentStepsTable` 和 `TaskTimeline` 增加空态。
- 新增后端 API 测试 `tests/test_task_steps_api.py`。
- 新增前端进度契约测试 `tests/test_frontend_task_progress_contract.py`。

## 实施步骤

### 1. 复查 Day 19

Day 19 已完成：

- `POST /api/tasks` 真实接入。
- `GET /api/tasks/{task_id}` 真实接入。
- `GET /api/tasks/{task_id}/events` 真实接入。
- `GET /api/tasks/{task_id}/steps` 当时仍为空数组 fallback。
- 文档明确把 steps API 和前端进度刷新列为 Day 20 输入。

复查结果：Day 19 没有发现遗漏，可以进入 Day 20。

### 2. 后端 steps API

新增 API：

```text
GET /api/tasks/{task_id}/steps
```

返回结构：

```json
{
  "task_id": "tsk_xxx",
  "steps": [
    {
      "step_id": "stp_xxx",
      "agent_run_id": "run_xxx",
      "task_id": "tsk_xxx",
      "step_index": 1,
      "step_type": "action",
      "tool_name": "search_reviews_tool",
      "status": "success",
      "duration_ms": 2000,
      "input_summary": "search_reviews_tool input keys: query, top_k",
      "observation_summary": "Found 1 review chunk for quality issue.",
      "error_code": null
    }
  ]
}
```

设计约束：

- 先通过任务状态 store 判断任务是否存在，缺失返回 `TASK_NOT_FOUND`。
- 有任务但没有 Agent run / step 时返回空数组，不报错。
- 不返回 `thought` 原文。
- `thought` 类型只返回 `input_summary="Thought recorded"`。
- `tool_input` 只暴露 key 摘要，不暴露完整参数。
- `observation` 做长度截断。
- `tool_output.error.code` 映射为 `error_code`。

### 3. 前端任务进度面板

新增 `frontend/src/components/task-progress-panel.tsx`：

- 使用 `"use client"`。
- 接收服务端首屏加载得到的 `initialTask`、`initialEvents`、`initialSteps`。
- 每 5 秒刷新：
  - `getTask(taskId)`
  - `getTaskEvents(taskId)`
  - `getTaskSteps(taskId)`
- 状态进入 `completed`、`failed`、`cancelled` 后停止轮询。
- 提供手动刷新按钮。
- API 错误显示后端错误码。
- 展示 task error code / message。

为什么第一版选择轮询：

- 后端已经有可查询的状态和事件接口。
- SSE / WebSocket 需要额外连接生命周期、断线重连和部署配置。
- Day 20 的重点是先把观测闭环跑通，不把实时推送复杂度提前引入。

### 4. 前端 API 映射

`frontend/src/lib/api.ts` 新增：

- `BackendTaskSteps`
- `BackendAgentStep`
- `mapBackendAgentStep()`

`getTaskSteps()` 在真实 API 模式下调用：

```ts
request<BackendTaskSteps>(`/api/tasks/${taskId}/steps`)
```

如果后端暂时不可用，仍返回 `[]`，保证任务详情页不会因为 steps 失败而整体不可访问。但成功 API 响应不再使用 mock。

## 验收标准

- `uv run pytest tests\test_task_steps_api.py` 通过。
- `uv run pytest tests\test_frontend_task_progress_contract.py` 通过。
- `cd frontend; npm run build` 通过。
- `cd frontend; npm run lint` 通过。
- `GET /api/tasks/{task_id}/steps` 返回统一 envelope。
- 缺失任务返回 `TASK_NOT_FOUND`。
- 有任务但无 Agent steps 返回空数组。
- 前端任务详情页出现 `TaskProgressPanel`。
- 前端不会展示完整 thought。

## 风险与回退

- 风险：轮询带来额外请求。
  - 回退：当前只在任务未结束时轮询，终态自动停止。
- 风险：Agent thought 泄露。
  - 回退：API schema 不返回 thought 字段，只返回摘要。
- 风险：steps API 失败导致任务详情页不可用。
  - 回退：`getTaskSteps()` catch 后返回空数组；任务状态和事件仍可显示。
- 风险：后续要支持实时推送。
  - 回退：`TaskProgressPanel` 已把刷新逻辑集中封装，后续可把轮询替换成 SSE / WebSocket。

## 关联文档

- 上一天：`day-19.md`
- 下一天：`day-21.md`
- API：`../supporting/api-contract.md`
- 可观测性：`../supporting/observability.md`
- 控制台：`../supporting/ui-console-spec.md`
- Agent 状态机：`../supporting/agent-state-machine.md`
- 开发日志：`../supporting/development-log.md`
- 面试手册：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 实现 Day 20 任务进度与 Agent Step 展示`
