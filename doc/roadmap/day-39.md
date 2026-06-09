# Day 39 - LLMOps 运营指标面板

## 当天目标

Day 39 的目标是把模型调用、结构化输出、自愈、RAG、retry 和恢复数据汇总成一个可解释的 LLMOps 指标面板。前面已经有 metrics 文档、benchmark、provider metrics 和 retry 事件，Day 39 要让这些数据能被前端或 API 统一查看。

这一天解决“项目工程化深度怎么展示”的问题：不是只说用了模型，而是能展示成本统计、失败率、自愈成功率、恢复成功率和耗时分布。

## 前置依赖

- `day-12.md`：guardrails 和 self-heal 指标。
- `day-27.md`：benchmark summary。
- `day-28.md`：retry 和 recovery。
- `day-35.md`：provider_metrics。
- `day-36.md`：真实 LLM prompt 和 fallback。
- `../supporting/llmops-metrics.md`：指标定义。
- `../supporting/observability.md`：错误日志和 trace id。

## 当天交付物

- 新增 LLMOps summary service 或 API：
  - 总任务数。
  - 成功率。
  - 失败率。
  - retry 次数。
  - 恢复成功率。
  - Pydantic parse 失败次数。
  - 自愈成功率。
  - provider 调用次数。
  - provider latency。
  - 成本统计。
- 前端新增或扩展设置/工作台指标区域。
- 指标来源必须标注：
  - fixture。
  - mock。
  - real provider。
  - benchmark。
- 不把 fake provider 指标包装成真实成本。

## 实施步骤

1. 先写测试：
   - `tests/test_llmops_summary.py`。
   - 验证 summary 字段完整。
   - 验证空数据时返回 0 和明确来源。
   - 验证自愈成功率计算。
   - 验证恢复成功率计算。
2. 后端实现：
   - 优先从已有 logs、benchmark summary、provider metrics 汇总。
   - 如果没有持久化数据，先做 fixture summary 和接口契约。
3. 前端展示：
   - 首页或独立 LLMOps 区块显示中文指标。
   - 显示 `数据来源：fixture / mock / real`。
4. 指标解释：
   - `模型调用次数`。
   - `结构化解析失败`。
   - `自愈成功率`。
   - `恢复成功率`。
   - `平均耗时`。
5. 文档同步。

## 测试计划

```powershell
uv run pytest tests\test_llmops_summary.py
uv run pytest tests\test_structured_output_guardrails.py tests\test_day27_benchmarking.py tests\test_day28_recovery.py
uv run pytest tests\test_observability.py
cd frontend
npm run lint
npm run build
```

如果前端新增组件，补前端契约测试：

```powershell
uv run pytest tests\test_frontend_localization_contract.py
```

## 验收标准

- LLMOps 指标字段完整。
- 成本统计、失败率、自愈成功率、恢复成功率都有来源说明。
- 空数据不会报错。
- fake / fixture / real provider 来源不混淆。
- 前端显示中文指标名。
- 文档说明哪些指标能写进简历，哪些只能作为本地 fixture baseline。

## 风险与回退

风险：

- 指标来源混杂导致误导。
- 成本统计没有真实 token 数据。
- 面板看起来很完整，但实际都是 mock。
- 指标计算分母为 0。

回退：

- 如果真实数据不足，明确显示 `暂无真实 provider 数据`。
- 如果成本不可计算，显示调用次数和耗时，不估算成本。
- 如果 UI 范围过大，先做 API summary 和首页小组件。

## 文档同步清单

- `llmops-metrics.md`：更新指标定义、来源和可写入口径。
- `development-log.md`：记录 Day 39 指标结果。
- `interview-defense-dossier.md`：补充“LLMOps 怎么做”的回答。
- `testing-strategy.md`：记录指标计算测试边界。
- `resume-story.md`：如果指标真实可验证，再考虑更新简历素材。

## 面试讲法

可以这样讲：

> Day 39 我把模型相关指标从散落的测试和日志里汇总成 LLMOps summary。里面区分模型调用次数、结构化解析失败、自愈成功率、provider latency、retry 恢复成功率和数据来源。重点是诚实区分 fixture、mock 和 real provider，不把演示数据包装成线上数据。

如果被问“成本统计怎么保证真实”，回答：

> 只有真实 provider 返回 token 或计费信息时才计算成本。fake provider 和 fixture benchmark 只能用于开发基线，不能写成真实成本。我会在面板和文档里标注数据来源。

## 建议提交

```text
feat: 增加 LLMOps 运营指标汇总
```
