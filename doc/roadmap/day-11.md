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

## 实施步骤

1. 创建 `agent_runs`
2. 每轮循环先写 Thought
3. 选择工具后写 Action，状态为 `pending`
4. 工具执行中更新为 `running`
5. 工具返回后写 Observation，状态为 `success` 或 `failed`
6. 当信息足够时进入报告阶段

## 验收标准

- 数据库能完整还原一次 Agent 执行
- 工具失败不会覆盖旧 step
- 每一步都有 `task_id` 和 `agent_run_id`
- 循环有最大步数限制，避免无限执行

## 风险与回退

- 不要把思考链只保存在内存
- 如果模型接口暂不可用，可以先用 fake planner 测状态机

## 关联文档

- 上一天：`day-10.md`
- 下一天：`day-12.md`
- 状态机：`../supporting/agent-state-machine.md`
- 可观测性：`../supporting/observability.md`

## 建议提交

`feat: persist agent reasoning steps`

