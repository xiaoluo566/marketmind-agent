# Day 10 - Agent 工具接口设计

## 当天目标

把采集、检索、报告等能力包装成 Agent 可调用的工具。今天重点是工具契约，不急着写复杂推理。

## 前置依赖

- `day-09.md` 采集结果可以入库
- 阅读 `../supporting/agent-state-machine.md`
- 阅读 `../supporting/data-contract-examples.md`

## 当天交付物

- 工具注册机制
- 工具输入 Pydantic schema
- 工具输出 Pydantic schema
- `crawl_product_tool` 草案
- 工具错误分类

## 实施步骤

1. 定义工具基类或统一函数签名
2. 为 `crawl_product_tool` 定义输入输出
3. 设计工具返回结构：`success`、`data`、`error`、`artifacts`
4. 标记工具是否可重试、是否幂等
5. 写一个工具执行器，负责记录调用前后状态

## 验收标准

- 工具参数能被 Pydantic 校验
- 工具结果格式统一
- Agent 不需要知道工具内部实现
- 工具失败能返回可分类错误

## 实际完成记录

Day 10 完成的是 Agent 工具层的第一版契约，不是完整 ReAct 推理。当前实现新增 `backend/app/agent/tools/` 包，核心内容包括：

- `ToolSpec`：工具描述、版本、输入 schema、输出 schema、幂等和重试元信息。
- `ToolManifest`：给 Agent 或前端展示的工具清单。
- `ToolRegistry`：注册、查询、列出工具，并拒绝重复注册。
- `ToolExecutor`：统一做输入校验、执行、输出校验和错误 envelope。
- `crawl_product_tool`：把 Day 8/9 的采集能力包装成 Agent 可调用工具。

工具调用现在统一返回：

- `success`
- `data`
- `error`
- `artifacts`
- `task_id`
- `trace_id`
- `idempotent`
- `retryable`
- `started_at`
- `finished_at`
- `duration_ms`

Day 10 的重要边界：

- 不直接接 LLM。
- 不写 ReAct 循环。
- 不写 Agent step 数据库状态机。
- 不让模型直接操作数据库。

这一天的价值是先把“Agent 可以调用哪些工具、参数怎么校验、失败怎么分类、结果怎么表达”固定下来，避免 Day 11 写 ReAct loop 时工具边界混乱。

## 风险与回退

- 不要让模型直接拼接任意工具参数
- 不要让工具内部吞掉异常

## 关联文档

- 上一天：`day-09.md`
- 下一天：`day-11.md`
- 状态机：`../supporting/agent-state-machine.md`
- Prompt：`../supporting/prompt-strategy.md`

## 建议提交

`feat: define agent tool contracts`
