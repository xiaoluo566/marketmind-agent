# Agent 状态机

## 状态链

1. `received`
2. `classified`
3. `planned`
4. `tool_selected`
5. `tool_running`
6. `observation_saved`
7. `self_checked`
8. `reporting`
9. `completed`
10. `failed`

## 状态转移表

| 当前状态 | 触发条件 | 下一状态 | 写入内容 |
| --- | --- | --- | --- |
| `received` | 任务被 worker 拿到 | `classified` | 任务目标和输入摘要 |
| `classified` | Agent 判断任务类型 | `planned` | 任务类型、需要的工具 |
| `planned` | 选择下一步工具 | `tool_selected` | 工具名和参数草案 |
| `tool_selected` | 参数校验通过 | `tool_running` | Pending action |
| `tool_running` | 工具成功返回 | `observation_saved` | Observation 和 artifact |
| `tool_running` | 工具失败 | `failed` 或 `planned` | 错误原因和重试决策 |
| `observation_saved` | 结构化检查通过 | `self_checked` | schema 校验结果 |
| `self_checked` | 需要更多信息 | `planned` | 下一轮计划 |
| `self_checked` | 信息足够 | `reporting` | 报告生成输入 |
| `reporting` | 报告成功入库 | `completed` | report_id |

## 关键动作

- 接收用户目标并做任务分类
- 选择工具而不是直接输出结论
- 每次工具调用前写 Pending
- 每次工具调用后写 Success / Failed
- 每次 Observation 都持久化
- 在结构化输出失败时自动重试或纠错

## 记录要求

- Thought：记录决策依据
- Action：记录调用的工具和参数
- Observation：记录工具结果和关键事实
- Error：记录异常、重试和回退策略

## 断点续跑

- 必须从数据库恢复最后一个稳定步骤
- 不允许只依赖内存中的上下文
- 恢复时必须检查 schema 版本和工具版本

## 工具调用契约

每个工具必须具备：

- 输入 Pydantic schema
- 输出 Pydantic schema
- 超时设置
- 可重试标记
- 错误分类
- 结果摘要函数

Day 10 起工具契约由 `backend/app/agent/tools/` 维护：

- `ToolSpec` 负责描述工具元信息和 schema。
- `ToolRegistry` 负责工具注册和发现。
- `ToolExecutor` 负责输入校验、执行、输出校验和统一错误 envelope。
- `crawl_product_tool` 是第一版内置工具，用于把采集能力暴露给 Agent。

工具执行结果必须统一包含：

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

Agent 后续只能通过 registry 和 executor 调用工具，不允许直接绕过 schema 调用具体业务函数。

## Day 15 `search_reviews_tool`

Day 15 将评论检索能力接入工具注册表。当前工具注册策略：

- 默认 `build_default_tool_registry()` 只注册 `crawl_product_tool`。
- 传入 `review_chunk_store` 和 `embedding_provider` 时，额外注册 `search_reviews_tool`。

这样做是为了避免默认工具注册表在测试或无数据库场景下强依赖 RAG 存储。

`search_reviews_tool` 的 Action 语义：

```text
Thought: 需要确认是否存在退货和售后差评证据
Action: search_reviews_tool(query="return support", top_k=5, filters.rating_lte=2)
Observation: 返回相关 review chunks 和 evidence refs
```

Agent 看到工具结果时必须遵守：

- `results` 非空：只能基于返回 chunk 形成结论。
- `results` 为空：必须记录证据不足，不能继续编造。
- 报告后续引用必须使用 `evidence_refs`。

## Day 16 报告生成接入边界

Day 16 新增 `backend/app/reporting/`，但还没有把 worker 主流程替换成“采集 -> 检索 -> 报告”的完整 Agent runner。当前报告模块是独立可测试组件，后续状态机接入时建议按下面边界推进：

```text
search_reviews_tool output
  -> EvidenceSnippet[]
  -> ReportGenerationInput
  -> StructuredReportGenerator / report prompt
  -> StructuredReport
  -> SQLAlchemyReportStore
```

状态机接入报告时必须记录：

- 生成报告前的 Thought：为什么现在证据足够或不足。
- 报告生成 Action：输入的 `task_id`、`requested_focus` 和 evidence refs。
- 报告生成 Observation：`report_id`、`status`、`schema_version` 和 evidence refs。

Day 16 已经完成的硬边界：

- `StructuredReport` 校验章节 evidence refs。
- 无证据时输出 `insufficient_evidence`。
- 报告 JSON 和 Markdown 可写入 `reports` 表。

Day 17 继续补的是 evidence refs 到 review chunk / tool output 的可追溯展示，而不是重新设计报告 schema。

## Day 11 最小实现

Day 11 已经把状态机从文档推进到代码。当前实现位置：

- `backend/app/storage/agent_stores.py`
- `backend/app/agent/state_machine.py`
- `tests/test_agent_state_machine.py`

当前不是完整多轮 LLM planner，而是最小可运行 ReAct 状态机。它的目标是先把“每一步可追踪”打通：

1. 创建 `agent_runs`，初始状态为 `pending`。
2. 将 run 标记为 `running`。
3. 写入 `thought` step，说明为什么下一步要调用工具。
4. 写入 `action` step，记录工具名和工具参数，初始状态为 `pending`。
5. 工具执行前把 action step 标记为 `running`。
6. 通过 `ToolExecutor` 调用 `crawl_product_tool`。
7. 工具成功时，写入完整 `tool_output`，把 action step 标记为 `success`。
8. 工具失败时，写入结构化错误，把 action step 标记为 `failed`。
9. 追加 `observation` step，保存可读观察结果。
10. 根据工具结果把 run 标记为 `completed` 或 `failed`。

当前 step 粒度：

| step_type | 记录内容 | 说明 |
| --- | --- | --- |
| `thought` | `thought` | 记录本轮为什么选择某个动作 |
| `action` | `tool_name`、`tool_input`、`tool_output`、`status` | 记录具体工具调用和执行结果 |
| `observation` | `observation`、`tool_output` | 记录工具结果对 Agent 来说意味着什么 |

这里故意把 Thought、Action、Observation 拆成多条 step，而不是压进一条日志，是为了方便前端后续展示时间线，也方便失败后定位卡在“决策、执行、观察”的哪一层。

当前没有把 worker 主流程替换为 Agent 状态机。原因是 Day 9 的采集结果入库已经稳定，如果 Day 11 同时替换 worker 和引入 Agent step，会扩大回归范围。后续更合理的做法是先让 state machine 独立稳定，再把 worker route 中的 public URL 任务逐步切到 Agent runner。

## Day 12 结构化输出守门

Day 12 新增 `backend/app/agent/guardrails.py`，用于拦截模型输出：

- `AgentToolDecision`：工具选择输出 schema。
- `ReportStructure`：报告结构输出 schema。
- `StructuredOutputGuardrail`：统一做 JSON parse、Pydantic 校验、self-heal 和失败封装。
- `StructuredOutputGuardrailError`：保留原始输出、错误详情和 attempts。

状态机后续接大模型 planner 时，模型输出必须先经过 guardrail：

```text
LLM raw output
  -> StructuredOutputGuardrail.parse
  -> AgentToolDecision
  -> ToolExecutor
  -> agent_steps
```

不允许把 raw LLM output 直接当作工具参数进入 `ToolExecutor`。如果 guardrail 修复成功，需要累计 `agent_runs.self_heal_count`；如果解析或 schema 校验失败，需要累计 `agent_runs.validation_error_count`。

## Day 13 短期记忆接入

Day 13 新增 `backend/app/agent/memory.py`，用于控制 Agent 每轮执行前看到的上下文。状态机现在支持可选 `short_term_memory`：

```text
agent_steps / Redis snapshot
  -> AgentShortTermMemory.build_prompt_context
  -> planner / thought builder
  -> ToolExecutor
  -> agent_steps
  -> AgentShortTermMemory.remember_step
```

当前接入点：

1. run 开始前调用 `build_prompt_context(task_id)`，读取历史摘要和最近上下文。
2. `thought` step 落库后，写入短期记忆。
3. `action` step 完成或失败后，写入短期记忆。
4. `observation` step 落库后，写入短期记忆。

短期记忆默认最近 3 条保留详细内容，更早内容进入 summary。这里的 summary 不是长期业务结论，而是帮助后续 planner 避免重复塞入完整上下文的工作摘要。

### 恢复策略

Redis 短期记忆不是唯一事实来源。如果 worker 重启或 Redis key 过期，可以用 `AgentShortTermMemory.restore_from_steps(task_id, steps)` 从 PostgreSQL `agent_steps` 重建：

- `observation` 优先转为记忆内容。
- 其次使用 `thought`。
- 工具 step 使用 `tool_name` 和 `tool_input` 生成简短描述。
- 从 `tool_output` 中提取 `artifact_id`、`review_id`、`chunk_id`、`evidence_refs` 等证据引用。

这让 Day 13 的记忆机制和 Day 11 的状态落库形成互补：Redis 提供快速上下文读取，PostgreSQL 提供可恢复执行历史。

## 断点续跑算法

1. 从 `agent_runs` 找到最近一次未完成 run
2. 读取最后一条 `agent_steps`
3. 如果最后一步是 `success`，从下一步继续
4. 如果最后一步是 `pending` 或 `running`，检查工具是否幂等
5. 如果工具幂等，标记旧步骤为 `failed`，并在 `tool_output` 或错误 payload 里记录 recovery 原因后重试
6. 如果工具不幂等，创建人工确认事件

## 不要做的事

- 不要把 Agent 的全部上下文只存在 Python 变量里
- 不要直接让模型自由输出报告
- 不要让模型自己决定数据库写入
- 不要在失败后覆盖旧步骤

## 与其他文档关系

- prompt 管理见 `prompt-strategy.md`
- 数据表见 `data-model.md`
- 测试策略见 `testing-strategy.md`
