# Day 12 - 结构化输出与自愈

## 当天目标

降低模型输出不符合 schema 的失败率。所有 Agent 输出都必须先校验，再进入业务流程。

## 前置依赖

- `day-11.md` ReAct loop 可运行
- 阅读 `../supporting/prompt-strategy.md`
- 阅读 `../supporting/security-compliance.md`

## 当天交付物

- Pydantic 输出模型
- Tenacity 重试策略
- JSON 修复 prompt
- 校验失败日志
- 自修复结果统计字段

## Day 12 实际实现记录

当前 Day 12 没有接真实大模型 API，而是先实现结构化输出守门层。原因是模型供应商可以后换，但“输出必须先校验再进业务”的边界必须先固定。

新增核心代码：

- `backend/app/agent/guardrails.py`
  - `AgentToolDecision`
  - `ReportStructure`
  - `StructuredOutputGuardrail`
  - `StructuredOutputParseResult`
  - `StructuredOutputGuardrailError`
  - `build_json_repair_prompt`
- `backend/app/storage/agent_stores.py`
  - `record_guardrail_metrics`
- `tests/test_structured_output_guardrails.py`

实际链路：

```text
raw_model_output
  -> JSON parse
  -> Pydantic schema validate
  -> success: return structured output
  -> fail: build_json_repair_prompt
  -> repair function with Tenacity retry
  -> validate repaired JSON
  -> success: record self_heal_count
  -> fail: raise StructuredOutputGuardrailError with raw output and attempts
```

当前覆盖两个输出面：

| Schema | 用途 |
| --- | --- |
| `AgentToolDecision` | 后续 planner 生成工具选择时使用 |
| `ReportStructure` | 后续报告生成前校验章节结构 |

统计字段：

- `validation_error_count`：结构化输出解析或 Pydantic 校验失败次数。
- `self_heal_count`：self-heal 成功次数。

这两个字段已经存在于 `agent_runs`，Day 12 增加了 store 层累计方法。

## 实施步骤

1. 定义工具选择输出 schema
2. 定义报告结构 schema
3. 对模型返回先做 JSON parse
4. parse 失败时触发 self-heal prompt
5. self-heal 仍失败时写入结构化错误
6. 把失败样例保存为后续测试数据

## 验收标准

- 非标准 JSON 不会直接进入业务逻辑：已由 `StructuredOutputGuardrail` 拦截
- 自修复次数被记录：已通过 `record_guardrail_metrics` 和测试验证
- 失败时能看到原始输出和错误原因：`StructuredOutputGuardrailError` 携带 `original_output` 与 attempts
- 至少有一个回归测试覆盖坏 JSON：已新增坏 JSON self-heal 和失败测试

## 风险与回退

- 不要无限重试模型
- 不要让自修复 prompt 改变业务含义
- 如果模型不稳定，先降低输出复杂度

## Day 12 后遗留问题

- 当前还没有真实 LLM client。
- 当前 guardrails 还没有接入 worker 主路径。
- 当前 self-heal prompt 还是代码内生成，后续需要做 prompt 版本管理。

## Day 12 验证记录

- `uv run pytest tests\\test_structured_output_guardrails.py`：6 passed
- `uv run pytest`：63 passed
- `uv run ruff check backend tests migrations`：通过
- `uv run alembic heads`：`0002_task_queue_id (head)`
- `npm run build`：通过

## 关联文档

- 上一天：`day-11.md`
- 下一天：`day-13.md`
- Prompt：`../supporting/prompt-strategy.md`
- LLMOps：`../supporting/llmops-metrics.md`

## 建议提交

`feat: add structured output guardrails`
