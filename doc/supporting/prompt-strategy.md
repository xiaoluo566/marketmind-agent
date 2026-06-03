# Prompt 策略

## 为什么要单独写

Agent 项目最后最容易失控的地方，不是 API，而是 prompt：版本一多，行为就会漂移，最后没人知道是哪一版 prompt 让系统变聪明或者变坏了。

## Prompt 类型

- `system prompt`：定义 Agent 身份、边界和优先级
- `tool prompt`：定义工具如何被调用
- `extraction prompt`：定义如何抽取结构化信息
- `summary prompt`：定义如何压缩长上下文
- `report prompt`：定义如何生成报告
- `self-heal prompt`：定义 JSON 修复和格式恢复

## 模型分层

第一版默认用 `gpt-5.4-mini` 执行高频、结构化、可重试的 Agent 步骤，例如工具参数生成、普通总结和 JSON self-heal。

最终报告生成可以切到 `gpt-5.5`，但必须通过 `REPORT_MODEL_NAME` 配置控制，不能在 prompt 或业务代码里写死。

## 每个 prompt 必须带的元信息

- 名称
- 版本号
- 适用场景
- 输入类型
- 输出 schema
- 失败案例
- 回归样例

## Day 12 self-heal prompt 规则

Day 12 起，结构化输出修复由 `backend/app/agent/guardrails.py` 统一处理。修复 prompt 至少包含：

- prompt 名称
- 目标 schema 名称
- Pydantic 或 JSON parse 错误信息
- 原始模型输出
- “只返回合法 JSON”的约束

当前实现先使用 `build_json_repair_prompt` 生成第一版修复提示词。后续如果 prompt 变复杂，应当把模板迁移到单独 prompt 文件，并记录版本号。

自愈边界：

- self-heal 只能修复格式，不应该改变业务含义。
- 修复失败不能继续进入业务逻辑。
- 修复成功要记录 `self_heal_count`。
- 解析或校验失败要记录 `validation_error_count`。

## Day 13 summary prompt 规则

Day 13 第一版短期记忆摘要先采用确定性摘要，不调用大模型。后续如果接入 LLM summary prompt，必须遵守下面约束：

- 输入必须包含当前 `summary`、待压缩 entries、每条 entry 的 `evidence_refs`。
- 输出必须包含 `summary` 和 `summary_evidence_refs`。
- 不允许删除证据 ID。
- 不允许把没有证据的判断改写成事实。
- 不允许在摘要中新增原始 entry 没有出现过的商品、评论、价格或结论。
- 输出必须经过 Pydantic schema 校验，失败时走 Day 12 self-heal。

推荐 prompt 名称：

- `memory.short_term_summary.v1`

第一版暂时不用 LLM summary 的原因是：短期记忆的核心风险是上下文预算失控和证据 ID 丢失，先用确定性摘要更容易测试和回归。等 Day 14 - Day 17 评论切片、检索和报告证据链稳定后，再考虑把 summary prompt 版本化。

## 版本管理建议

- prompt 不要直接散落在代码里
- 每个阶段只维护少量稳定模板
- prompt 调整必须记录原因和样例

## 与其他文档关系

- `agent-state-machine.md` 决定 prompt 在什么时候被调用
- `data-model.md` 决定 prompt 产出的数据怎么存
- `model-and-data-decisions.md` 决定默认模型和报告模型
- `testing-strategy.md` 决定 prompt 是否回归
