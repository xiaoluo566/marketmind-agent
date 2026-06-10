# Day 36 - 真实 LLM 报告生成 Prompt

## 当天目标

Day 36 的目标是把报告生成从确定性模板推进到真实 LLM report prompt，但不能牺牲结构化输出、证据引用和可恢复性。模型可以生成更自然的报告，但必须被 `StructuredReport`、`evidence_refs` 和 Pydantic 校验约束住。

这一天的核心不是“让模型随便写报告”，而是建立 prompt version、结构化输出校验、失败自愈和 fallback 的完整链路。

## SDD 规格

### 用户故事

**P1 - 运营用户获得更自然但仍有证据约束的报告**

作为运营用户，我希望报告可以由 LLM 组织语言，但每个结论仍然必须绑定输入 evidence refs，这样报告更可读，同时不会变成没有来源的 AI 文案。

验收标准：

- prompt 中明确列出 allowed evidence refs。
- prompt 明确要求不要编造证据 ID。
- LLM 输出必须匹配 `StructuredReport(report.v1)`。
- section 引用不存在 evidence ref 时校验失败。

**P1 - 开发者能处理坏 JSON 和模型漂移**

作为开发者，我希望 LLM 输出坏 JSON 时能进入 self-heal，repair 失败时 fallback 到确定性报告生成器。

验收标准：

- bad JSON 会触发 `StructuredOutputGuardrail` repair。
- repair 成功时记录 `validation_error_count` 和 `self_heal_count`。
- repair 失败时 fallback deterministic generator。
- fallback report metadata 记录 `fallback_used` 和 `fallback_reason`。

**P2 - 无证据时不调用 LLM**

作为维护者，我希望没有 evidence snippets 时直接输出 `insufficient_evidence`，避免模型凭空生成结论。

验收标准：

- 无 evidence snippets 时不调用 LLM client。
- 报告状态为 `insufficient_evidence`。
- metadata 记录 `llm_skipped_reason=NO_EVIDENCE_SNIPPETS`。

### 非目标

- 不在单元测试中调用真实 LLM。
- 不把真实模型 token / cost 写成已验证指标。
- 不改变 `StructuredReport` schema。
- 不改变报告入库表结构。
- 不做前端报告详情改造，前端展示放到 Day37 / Day38 / Day40 后续联调。

## 前置依赖

- `day-12.md`：Pydantic guardrails 和 self-heal。
- `day-16.md`：`StructuredReport`、报告 schema、Markdown 渲染和入库。
- `day-17.md`：证据链回查和 evidence refs。
- `day-18.md`：风险/机会评分。
- `day-35.md`：RAG 质量和 provider metrics。
- `../supporting/prompt-strategy.md`：prompt 版本和结构化输出策略。
- `../supporting/llmops-metrics.md`：模型调用和成本指标。

## 当天交付物

- 新增真实报告生成 prompt：
  - system prompt。
  - developer prompt。
  - evidence context。
  - output schema 要求。
  - prompt version。
- 新增 report LLM provider 抽象或复用现有 provider 配置。
- 真实 LLM 输出必须解析成 `StructuredReport`。
- 模型输出 bad JSON 时触发 Pydantic self-correction。
- 失败时 fallback 到确定性报告生成器。
- 报告入库记录：
  - prompt_version。
  - model_name。
  - provider。
  - evidence_ids。
  - fallback_used。
- 不允许生成没有证据引用的结论。
- 新增 `backend/app/reporting/llm_prompt.py`：
  - `REPORT_PROMPT_VERSION`
  - `LLMReportClient`
  - `ReportPromptBundle`
  - `LLMStructuredReportGenerator`
  - `LLMReportGenerationResult`
  - `build_report_prompt_bundle()`
- 新增 `tests/test_llm_report_prompt_contract.py`。

## 实施步骤

1. 先写测试：
   - `tests/test_llm_report_prompt_contract.py`。
   - 验证 prompt 包含 evidence refs 约束。
   - 验证 bad JSON 会进入 repair。
   - 验证无 evidence 时降级。
   - 验证 prompt_version 被记录。
2. Prompt 设计：
   - 输入分为任务目标、评分摘要、RAG evidence、禁止事项。
   - 输出必须匹配 `StructuredReport`。
   - 明确禁止编造证据 ID。
3. Provider 设计：
   - 不在测试里真实调用模型。
   - 使用 fake LLM client 模拟好 JSON、坏 JSON、超时、空响应。
4. 生成器改造：
   - 真实 provider 可用时调用 LLM。
   - 解析失败时 self-heal。
   - repair 失败后 fallback deterministic generator。
5. LLMOps 指标：
   - 记录 parse_failed、repair_success、fallback_used。
   - 记录模型名和 prompt_version。
6. 文档同步。

## 测试计划

```powershell
uv run pytest tests\test_llm_report_prompt_contract.py
uv run pytest tests\test_report_generation.py tests\test_structured_output_guardrails.py
uv run pytest tests\test_report_evidence_chain.py tests\test_report_scoring.py
uv run ruff check backend tests migrations
```

如果改动触碰前端报告详情：

```powershell
cd frontend
npm run lint
npm run build
```

## 实际完成

Day36 按 SDD + TDD 完成 LLM report prompt 契约层。

实现选择：

- 新增 `backend/app/reporting/llm_prompt.py`，把真实 LLM 报告能力作为可注入 client，而不是在报告生成器里硬编码外部 SDK。
- `build_report_prompt_bundle()` 生成 system / developer / evidence / output contract 四段 prompt。
- prompt version 固定为 `report.evidence_chain.v1`。
- `LLMStructuredReportGenerator` 使用 `StructuredOutputGuardrail` 解析 LLM 输出为 `StructuredReport`。
- bad JSON 会调用 client repair；repair 成功记录 self-heal。
- repair 失败或 evidence ref 校验失败后 fallback 到 `StructuredReportGenerator`。
- 无 evidence snippets 时跳过 LLM，直接输出 deterministic `insufficient_evidence`。
- report metadata 记录 `prompt_version`、`model_provider`、`model_name`、`fallback_used`、`fallback_reason` 或 `llm_skipped_reason`。

关键文件：

- `backend/app/reporting/llm_prompt.py`
- `backend/app/reporting/__init__.py`
- `tests/test_llm_report_prompt_contract.py`

## 当前验证结果

- RED：`uv run pytest tests\test_llm_report_prompt_contract.py` 最初失败，原因是 `app.reporting.llm_prompt` 不存在。
- GREEN：`uv run pytest tests\test_llm_report_prompt_contract.py`：4 passed。
- 报告链路回归：`uv run pytest tests\test_llm_report_prompt_contract.py tests\test_report_generation.py tests\test_structured_output_guardrails.py tests\test_report_evidence_chain.py tests\test_report_scoring.py`：26 passed。
- `uv run ruff check backend tests migrations`：All checks passed。

## 验收标准

- 真实 LLM report prompt 有版本号。
- 输出必须经过 `StructuredReport` 校验。
- evidence_refs 必须来自输入证据。
- bad JSON 有 repair 路径。
- repair 失败有 deterministic fallback。
- LLM 调用不进入单元测试真实网络。
- 文档明确当前真实 provider 是否已经配置和验证。

## 风险与回退

风险：

- 模型编造证据。
- 输出 JSON 不稳定。
- prompt 变更导致报告 schema 回归。
- 真实 provider 成本不可控。

回退：

- 如果真实 provider 不稳定，默认仍走 deterministic generator。
- 如果证据引用校验失败，报告生成失败，不写入无证据报告。
- 如果 repair 次数过多，记录到 LLMOps，不无限重试。

## 文档同步清单

- `prompt-strategy.md`：记录 report prompt version 和禁止事项。
- `llmops-metrics.md`：记录 parse / repair / fallback 指标。
- `development-log.md`：记录 Day 36 实际验证和 provider 状态。
- `interview-defense-dossier.md`：补充“如何防止模型胡编报告”的回答。
- `testing-strategy.md`：记录真实 LLM prompt 测试边界。

## 面试讲法

可以这样讲：

> Day 36 我把报告生成从确定性模板推进到真实 LLM prompt，但没有让模型自由发挥。模型输出必须过 `StructuredReport`，证据引用必须来自输入 evidence_refs，坏 JSON 会触发 self-correction，repair 失败会 fallback 到确定性报告。这样既有真实模型能力，也保留工程可控性。

如果被问“你怎么防止模型幻觉”，回答：

> 我不让报告直接相信模型文本。报告 section 必须引用已有 evidence id，引用不存在就校验失败。模型只能在证据范围内组织语言，不能凭空生成结论。

## 建议提交

```text
feat: 增加真实 LLM 报告生成 prompt 契约
```
