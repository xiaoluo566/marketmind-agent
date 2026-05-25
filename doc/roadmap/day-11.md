# Day 11 - ReAct 循环与状态落库

## 当天目标

实现 Agent 的核心循环，让系统真正具备“计划 -> 调用工具 -> 观察结果 -> 再计划”的能力。今天的关键不是让模型多聪明，而是每一步都可追踪。

## 前置依赖

- `day-10.md` 工具契约已定义
- 阅读 `../supporting/agent-state-machine.md`
- 阅读 `../supporting/data-model.md`

## 当天交付物

- Agent run 创建逻辑
- step_index 顺序记录
- Thought / Action / Observation 数据结构
- 工具调用前后状态写入
- 最小 ReAct loop

## Day 11 实际实现记录

Day 11 采用“最小可运行 ReAct”方案，而不是直接接完整大模型 planner。当前实现先证明四件事：

1. Agent run 可以创建并持久化。
2. Agent step 可以按 `step_index` 顺序追加。
3. 工具调用前后的状态变化可以写入数据库。
4. 成功和失败都能留下 Observation，后续可以回放。

新增核心代码：

- `backend/app/storage/agent_stores.py`
  - `SQLAlchemyAgentRunStore`
  - `AgentRunData`
  - `AgentStepData`
- `backend/app/agent/state_machine.py`
  - `AgentTaskInput`
  - `AgentRunResult`
  - `AgentStateMachine`
- `tests/test_agent_state_machine.py`

最小状态机当前会生成三类 step：

| step_type | 作用 | 当前状态变化 |
| --- | --- | --- |
| `thought` | 记录为什么选择下一步工具 | 直接写入 `success` |
| `action` | 记录工具名、工具参数和工具执行结果 | `pending -> running -> success/failed` |
| `observation` | 记录工具返回后的可读观察结果 | `success` 或 `failed` |

成功链路：

```text
create agent_run(pending)
mark run running
append thought(success)
append action(pending)
mark action running
ToolExecutor.execute(crawl_product_tool)
mark action success, write tool_output
append observation(success)
mark run completed
```

失败链路：

```text
create agent_run(pending)
mark run running
append thought(success)
append action(pending)
mark action running
ToolExecutor.execute(crawl_product_tool)
mark action failed, write structured error
append observation(failed)
mark run failed
```

当前实现保留一个重要边界：Day 11 没有把 worker 主流程替换成 Agent 状态机。原因是 Day 9 的采集结果入库链路已经稳定，贸然替换会让“采集持久化”和“Agent 持久化”同时变化，风险较高。Day 11 先把 Agent 自身的状态落库能力做扎实，后续再做 worker 路由整合。

## 实施步骤

1. 创建 `agent_runs`
2. 每轮循环先写 Thought
3. 选择工具后写 Action，状态为 `pending`
4. 工具执行中更新为 `running`
5. 工具返回后写 Observation，状态为 `success` 或 `failed`
6. 当信息足够时进入报告阶段

## 验收标准

- 数据库能完整还原一次 Agent 执行：已通过 `tests/test_agent_state_machine.py` 验证
- 工具失败不会覆盖旧 step：已通过失败链路测试验证
- 每一步都有 `task_id` 和 `agent_run_id`：已通过 `SQLAlchemyAgentRunStore.append_step` 强制写入
- 循环有最大步数限制，避免无限执行：已加入 `max_tool_calls` 并覆盖测试

## 风险与回退

- 不要把思考链只保存在内存
- 如果模型接口暂不可用，可以先用 fake planner 测状态机

## Day 11 后遗留问题

- 当前 planner 仍是确定性规则，不是大模型 Function Calling。
- 当前只执行 `crawl_product_tool`，还没有 `search_reviews_tool` 和报告工具。
- 当前状态机还没有接入 worker 主路径和前端 Agent step 展示。
- 当前没有真正做断点续跑，只是具备 `get_latest_step` 和 step 持久化基础。

## Day 11 验证记录

- `uv run pytest tests\\test_agent_state_machine.py`：4 passed
- `uv run pytest`：57 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

## 关联文档

- 上一天：`day-10.md`
- 下一天：`day-12.md`
- 状态机：`../supporting/agent-state-machine.md`
- 可观测性：`../supporting/observability.md`

## 建议提交

`feat: persist agent reasoning steps`
