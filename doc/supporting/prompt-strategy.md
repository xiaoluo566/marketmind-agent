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

## Day 16 report prompt 规则

Day 16 第一版报告生成先采用确定性生成器 `deterministic.report.v1`，不调用大模型。

这样做的原因：

- 当前阶段最重要的是报告 schema、证据引用和入库边界。
- LLM 文案质量不是 Day 16 的主要风险，非法 evidence ref 才是主要风险。
- 确定性生成器可以稳定测试“有证据”和“无证据”两条路径。

后续接入真实报告模型时，推荐 prompt 名称：

- `report.evidence_chain.v1`

该 prompt 必须遵守：

- 输入只能使用 `ReportGenerationInput` 中的 observations、requested_focus 和 evidence snippets。
- 输出必须匹配 `StructuredReport`。
- 每个章节的 `evidence_refs` 必须来自输入 evidence snippets。
- 如果输入 evidence snippets 为空，只能输出 `insufficient_evidence`。
- 不允许把 query、requested_focus 或模型常识当作事实证据。
- 不允许生成不存在的 `chunk:{chunk_id}`。
- 输出 JSON 必须先经过 Pydantic 校验，再写入 `reports` 表。

推荐 report prompt 输入摘要结构：

```text
Task: tsk_01HXYZ
Product: Portable Espresso Maker
Requested focus: return support, logistics
Observations:
- Crawler extracted 3 low-rating reviews.
Evidence snippets:
- evidence_ref=chunk:chk_return rating=1.0 similarity=0.86 content="The pump failed after three days..."
```

推荐 report prompt 输出 schema：

```text
StructuredReport(report.v1)
```

Day 16 的确定性生成器可以视为未来 LLM report prompt 的 golden baseline：LLM 可以写得更自然，但不能降低证据引用约束。

## Day 36 LLM report prompt 契约

Day36 新增 `backend/app/reporting/llm_prompt.py`，把真实 LLM 报告 prompt 从文档推进到代码契约。

当前 prompt version：

```text
report.evidence_chain.v1
```

Prompt bundle 分为四段：

- `system_prompt`：限定模型角色，只能根据评论证据生成报告。
- `developer_prompt`：写入 task、product、requested focus、allowed evidence refs。
- `evidence_context`：列出每条 evidence snippet 的 ref、rating、similarity、source 和 content。
- `output_contract`：要求只返回 JSON，并匹配 `StructuredReport(report.v1)`。

Day36 的关键约束：

- Prompt 明确写入“不要编造证据 ID”。
- 每个 section 的 `evidence_refs` 必须来自 allowed evidence refs。
- LLM 输出必须经过 `StructuredOutputGuardrail`。
- bad JSON 可以走 self-heal repair。
- repair 失败后 fallback 到 deterministic report generator。
- 没有 evidence snippets 时不调用 LLM，直接输出 `insufficient_evidence`。

当前仍不在单元测试中调用真实模型。`LLMReportClient` 是协议接口，测试使用 fake client 模拟好 JSON、坏 JSON、repair 和 fallback。

## Day 18 scoring prompt 边界

Day 18 的风险与机会评分先采用确定性规则 `deterministic.scorecard.v1`，不调用大模型。

当前评分只基于：

- evidence snippet 内容关键词
- 评论评分 `rating`
- 检索相似度 `similarity`
- 样本数量
- `minimum_samples` 降权

后续如果让 LLM 参与评分，只能做两类事情：

- 帮助解释 `DimensionScore.explanation`
- 帮助改进维度分类

不能让 LLM 绕过这些约束：

- 每个维度评分必须绑定 evidence refs。
- 样本不足必须标注。
- 无证据不能输出风险分。
- 不能输出“爆款概率”或“销量预测”。
- 输出仍然必须匹配 `AnalysisScorecard(scorecard.v1)`。

推荐 prompt 名称：

- `report.scorecard_explanation.v1`

## 版本管理建议

- prompt 不要直接散落在代码里
- 每个阶段只维护少量稳定模板
- prompt 调整必须记录原因和样例

## 与其他文档关系

- `agent-state-machine.md` 决定 prompt 在什么时候被调用
- `data-model.md` 决定 prompt 产出的数据怎么存
- `model-and-data-decisions.md` 决定默认模型和报告模型
- `testing-strategy.md` 决定 prompt 是否回归
