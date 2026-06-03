# Day 13 - 短期记忆与上下文压缩

## 当天目标

让 Agent 的当前任务上下文可控增长，避免后续多轮 ReAct / RAG / 报告生成时把所有历史 Thought、Action、Observation、工具输出和评论证据都塞进模型上下文。

Day 13 的重点不是 embedding，也不是长期 RAG，而是“短期工作记忆”：

- 最近几轮详细上下文直接保留。
- 更早的上下文压缩成摘要。
- 摘要必须保留关键证据 ID。
- Redis 作为实时缓存，PostgreSQL `agent_steps` 作为可恢复事实来源。

## 前置依赖

- Day 11：`agent_runs` / `agent_steps` 已经能持久化 Thought、Action、Observation。
- Day 12：结构化输出 guardrails 已经能拦截坏 JSON 和统计自愈次数。
- Redis 已经在 Day 5 - Day 7 用于任务状态和事件实时层。
- 阅读 `../supporting/rag-memory.md`、`../supporting/agent-state-machine.md` 和 `../supporting/prompt-strategy.md`。

## 设计边界

### 短期记忆负责什么

短期记忆只负责当前任务执行过程中的“工作上下文”，例如：

- 最近一次 Thought。
- 最近一次工具调用名称、参数摘要和执行状态。
- 最近一次 Observation。
- 最近工具输出中的 artifact / review / chunk 证据 ID。
- 被压缩后的历史摘要。

### 短期记忆不负责什么

短期记忆不负责：

- 存放全部评论原文。
- 代替 `agent_steps` 数据库表。
- 代替 pgvector 长期记忆。
- 直接生成最终报告。
- 保存不可恢复的唯一业务事实。

Redis 缓存丢失时，系统必须可以从 PostgreSQL 的 `agent_steps` 恢复关键上下文。

## 当天交付物

### 代码交付物

- `backend/app/agent/memory.py`
  - `AgentMemoryEntry`
  - `AgentMemorySnapshot`
  - `AgentPromptContext`
  - `AgentShortTermMemory`
  - `InMemoryAgentMemoryStore`
  - `RedisAgentMemoryStore`
  - `memory_entry_from_step`
  - `extract_evidence_refs`
- `AgentStateMachine` 接入可选 `short_term_memory`
  - 每轮执行前加载 prompt context。
  - Thought / Action / Observation 落库后同步写入短期记忆。
  - 保持默认行为兼容，不强制所有测试依赖 Redis。
- `tests/test_short_term_memory.py`
  - 滑动窗口测试。
  - 历史摘要测试。
  - 证据 ID 保留测试。
  - 从持久化 Agent step 恢复测试。
  - 状态机写入短期记忆测试。

### 文档交付物

- 更新 `rag-memory.md`：补短期记忆和长期 RAG 的边界。
- 更新 `agent-state-machine.md`：补执行前加载记忆、执行后写入记忆。
- 更新 `prompt-strategy.md`：补 summary prompt 的输入输出约束。
- 更新 `data-contract-examples.md`：补短期记忆 snapshot 示例。
- 更新 `development-log.md`：记录 Day 13 实际完成、验证命令和提交号。
- 更新 `interview-defense-dossier.md`：补 Day 13 面试讲法、技术取舍和追问。

## 实施步骤

### 1. 先写测试

覆盖下面行为：

1. 追加 5 条记忆，最近 3 条保留详细内容。
2. 第 1 - 2 条进入 summary。
3. summary 保留 `review_id`、`artifact_id`、`chunk_id` 等证据引用。
4. prompt context 输出稳定，不因历史无限增长而膨胀。
5. Redis / 内存缓存为空时，可以通过 `agent_steps` 重建 snapshot。
6. `AgentStateMachine` 成功执行后，短期记忆中能看到 Thought、Action、Observation。

### 2. 实现记忆数据结构

`AgentMemoryEntry` 字段：

- `sequence`：对应 step index 或记忆序号。
- `step_type`：`thought`、`action`、`observation` 等。
- `content`：给模型看的短文本。
- `evidence_refs`：证据引用，例如 `rev_001`、`chk_001`、`artifact:sha256`。
- `metadata`：内部调试字段，例如 `step_id`、`agent_run_id`、`status`、`tool_name`。

`AgentMemorySnapshot` 字段：

- `task_id`
- `summary`
- `summary_evidence_refs`
- `recent_entries`
- `updated_at`

### 3. 实现滑动窗口

默认窗口大小为 3：

```text
完整历史：step 1, step 2, step 3, step 4, step 5
压缩后：
  summary: step 1 + step 2 的摘要
  recent_entries: step 3, step 4, step 5
```

窗口大小要可配置，因为不同模型上下文长度和任务类型会不同。

### 4. 实现摘要策略

第一版先用确定性摘要，不调用大模型：

- 每条旧 entry 生成一行摘要。
- 单条内容过长时截断。
- 总摘要超过 `max_summary_chars` 时保留尾部关键内容。
- 证据 ID 不依赖摘要文本保存，而是单独保存在 `summary_evidence_refs`。

后续如果接 LLM summary prompt，必须保证：

- 只压缩语义，不改写事实。
- 不丢证据 ID。
- 输出必须经过 Pydantic schema 校验。

### 5. 实现缓存层

提供两个 store：

- `InMemoryAgentMemoryStore`：测试和本地无 Redis 场景使用。
- `RedisAgentMemoryStore`：真实短期缓存使用，key 格式为 `marketmind:agent:memory:{task_id}`。

Redis 只作为短期缓存，不是唯一事实来源。

### 6. 实现从 Agent step 恢复

从 `AgentStepData` 转成 `AgentMemoryEntry`：

- 优先用 `observation`。
- 其次用 `thought`。
- 如果是工具 step，用 `tool_name` 和 `tool_input` 生成简短描述。
- 从 `tool_output` 中递归提取 `artifact_id`、`review_id`、`chunk_id`、`evidence_refs` 等证据引用。

这一步保证 worker 重启或 Redis 清空后，不会丢失任务的关键上下文。

### 7. 接入状态机

`AgentStateMachine` 增加可选 `short_term_memory`：

- 不传时保持 Day 11 旧行为，方便测试和渐进迁移。
- 传入时：
  - run 开始前加载 `AgentPromptContext`。
  - Thought step 落库后写入记忆。
  - Action step 完成或失败后写入记忆。
  - Observation step 落库后写入记忆。

## 验收标准

- `uv run pytest tests\test_short_term_memory.py` 通过。
- `uv run pytest tests\test_agent_state_machine.py tests\test_structured_output_guardrails.py` 通过。
- `uv run pytest` 全量通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 仍为单 head。
- 前端未改动时至少确认 `npm run build` 没有被后端改动破坏。

## 风险与回退

### 风险 1：摘要丢证据

如果只把旧上下文压缩成纯文本，模型后面可能知道“有质量问题”，但不知道具体证据来自哪条评论。

回避方式：

- `summary_evidence_refs` 单独保存。
- `evidence_refs` 汇总时同时包含 summary 和 recent entries。

### 风险 2：Redis 缓存丢失

Redis 是短期实时层，不能承担唯一事实来源。

回避方式：

- 关键步骤仍然落 PostgreSQL `agent_steps`。
- 提供 `restore_from_steps` 从数据库 step 重建 snapshot。

### 风险 3：摘要策略太早依赖大模型

如果 Day 13 就接 LLM summary，会引入模型成本、格式失败和 prompt 漂移。

回避方式：

- 第一版用确定性摘要。
- 后续再把 `summary prompt` 接入 Day 12 guardrails。

## 当天选择思考

今天优先做短期记忆，是因为 Day 11 已经有 Agent step，Day 12 已经有结构化输出守门。下一步如果直接做 embedding 或报告，Agent 多轮执行时会马上遇到上下文无限增长问题。先把上下文窗口和摘要边界做好，后面的 RAG、报告和前端 step 展示都会更稳。

我选择“Redis 短期缓存 + PostgreSQL step 恢复”的组合，而不是只用 Redis，是因为 Redis 很适合快速读写当前上下文，但不适合承担断点续跑的唯一事实来源。真正可恢复的记录仍然应该来自 `agent_steps`。

我没有今天就做评论 embedding，是因为 embedding 属于长期记忆，依赖评论切片、模型配置、pgvector 写入和检索质量评估。短期记忆解决的是“Agent 当前任务怎么少带上下文”，长期记忆解决的是“海量评论怎么召回证据”，两个问题应该拆开。

## 关联文档

- 上一天：`day-12.md`
- 下一天：`day-14.md`
- 记忆设计：`../supporting/rag-memory.md`
- 状态机：`../supporting/agent-state-machine.md`
- Prompt：`../supporting/prompt-strategy.md`
- 数据模型：`../supporting/data-model.md`

## 建议提交

`feat: 实现 Day 13 短期记忆压缩`
